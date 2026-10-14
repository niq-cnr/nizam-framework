#!/usr/bin/env python3
"""Replayable private executable controls for the feature128 aggregate candidate."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[3]
RUNNER = REPO / 'tools/test_runtime_session.py'
SPEC = importlib.util.spec_from_file_location('sealed_runner', RUNNER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
EXPECTED = '005ed223ab121c3a1eda7f806ac6acc1e7076e795bf9b8ee75a394ca37d5e534'
assert hashlib.sha256(RUNNER.read_bytes()).hexdigest() == EXPECTED
LEAF = r'''import importlib.util,json,os,sys,time
from pathlib import Path
args=sys.argv[1:]; name=args[1] if args[0]=='--check' else 'case'+args[1]+'/stub'
first=args==['--check','lifecycle-no-evaluation']; mode=os.environ['AUTHOR_MODE']
if first and mode=='failure':
 print('PASS '+name); print('BEHAVIOR_ASSERTION: intended child failure',file=sys.stderr);sys.exit(23)
if first and mode=='missing-marker':
 print('PASS '+name);print('unrelated trailing output');sys.exit(0)
if first and mode in ('timeout','SIGINT','SIGTERM'):
 spec=importlib.util.spec_from_file_location('real_leaf',os.environ['AUTHOR_REAL_RUNNER'])
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 s=m.Session(Path(os.environ['TMPDIR']),candidate=Path(os.environ['AUTHOR_REPO']))
 s.open();meta=s.remember()
 Path(os.environ['AUTHOR_WITNESS']).write_text(json.dumps({'meta':meta,'tokens':s.processes,
  'marker':os.environ['NIZAM_CORE_OWNER'],'leaf_pid':os.getpid()}))
 time.sleep(60)
print('PASS '+name)
'''
WRAPPER = r'''import importlib.util,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('candidate_aggregate',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=Path(sys.argv[2]);sys.exit(m.core_ready(seconds=3))
'''
results = []
with tempfile.TemporaryDirectory(prefix='nizam128-controls-') as scratch:
    base = Path(scratch)
    sentinel = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
    try:
        for mode in ('failure', 'missing-marker', 'setup', 'timeout', 'SIGINT', 'SIGTERM'):
            private = base / mode; (private / 'tools').mkdir(parents=True)
            if mode != 'setup':
                (private / 'tools/test_runtime_session.py').write_text(LEAF)
            witness = private / 'witness.json'
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', AUTHOR_MODE=mode,
                       AUTHOR_REPO=str(REPO), AUTHOR_REAL_RUNNER=str(RUNNER), AUTHOR_WITNESS=str(witness))
            argv = [sys.executable, '-c', WRAPPER, str(RUNNER), str(private)]
            start = time.monotonic(); p = subprocess.Popen(argv, env=env, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                if mode in ('SIGINT', 'SIGTERM'):
                    deadline = time.monotonic() + 8
                    while not witness.exists() and p.poll() is None and time.monotonic() < deadline:
                        time.sleep(.02)
                    assert witness.exists(), 'real detached controller witness required before interrupt'
                    p.send_signal(getattr(signal, mode))
                out, err = p.communicate(timeout=30)
            except BaseException:
                p.kill(); p.communicate(); raise
            receipt = {'mode': mode, 'argv': argv, 'cwd': str(REPO), 'environment':
                {k:env[k] for k in ('PYTHONDONTWRITEBYTECODE','AUTHOR_MODE','AUTHOR_REPO','AUTHOR_REAL_RUNNER','AUTHOR_WITNESS')},
                'stdout': out, 'stderr': err, 'actual_exit': p.returncode, 'seconds': time.monotonic()-start}
            results.append(receipt)
            leaves = [json.loads(line.split(' ',1)[1]) for line in out.splitlines() if line.startswith('CORE_LEAF ')]
            assert p.returncode == (130 if mode in ('SIGINT','SIGTERM') else 1), receipt
            assert len(leaves) == (1 if mode in ('SIGINT','SIGTERM') else 14), 'safe later diagnostics must execute'
            assert 'PASS core-ready' not in out.splitlines()
            if mode == 'failure':
                assert leaves[0]['exit'] == 23 and leaves[0]['proof'] and 'intended child failure' in leaves[0]['stderr']
            if mode == 'missing-marker':
                assert leaves[0]['exit'] == 0 and not leaves[0]['proof']
            if mode == 'setup':
                assert all(x['exit'] == 2 and not x['proof'] and "can't open file" in x['stderr'] for x in leaves)
            if mode in ('timeout','SIGINT','SIGTERM'):
                value = json.loads(witness.read_text()); receipt['real_detached_witness'] = value
                receipt['after_tokens'] = {pid:MODULE.process_token(int(pid)) for pid in value['tokens']}
                assert all(receipt['after_tokens'][pid] != token for pid,token in value['tokens'].items())
                assert not MODULE.core_owned(value['marker']), 'no owned descendants remain'
                assert leaves[0]['event'] == ('timeout' if mode == 'timeout' else 'interrupted')
                assert leaves[0]['cleanup'] is True and leaves[0]['exit'] != 0
                cleanup = [json.loads(line.split(' ',1)[1]) for line in out.splitlines() if line.startswith('CORE_CLEANUP ')][0]
                assert set(value['tokens']) <= set(cleanup['owned_tokens']) and not cleanup['remaining']
            assert sentinel.poll() is None, 'unowned sentinel remains alive'
            receipt['unowned_sentinel_survived'] = True
            print('PASS',mode,'actual_exit',p.returncode,'leaf_count',len(leaves),flush=True)
    finally:
        sentinel.terminate(); sentinel.wait(timeout=5)
receipt = {'owner':'/root/evaluator128','kind':'author private aggregate sensitivity controls, not finalQA',
           'candidate':'441567ef05c3eb68558c6aeb679aa94b0a1a3baa','runner_sha256':EXPECTED,
           'exercised_revision':subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),
           'private_leaf_source':LEAF,'controls':results,'actual_exit':0}
path = REPO / '.agent/evidence/128/author1-controls.json'
assert not path.exists(); path.write_text(json.dumps(receipt,indent=2)+'\n')
