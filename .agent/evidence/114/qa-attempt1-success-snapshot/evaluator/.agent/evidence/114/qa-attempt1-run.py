#!/usr/bin/env python3
"""Serial personally executed formal QA114 capture, no source/coordination writes."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / '.agent/evidence/114'
PLAN = json.loads((E / 'qa-attempt1-plan.json').read_bytes())
C = PLAN['candidate_commit']
CONTRACT = json.loads((ROOT / '.agent/contracts/114.json').read_bytes())
FIXED = json.loads((E / 'fixed-inputs.json').read_bytes())
SOURCE = json.loads((E / 'current-source-inputs.json').read_bytes())
RESULTS = []

def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

def stability():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                   text=True).strip() == C
    assert digest('.agent/run_state.json') == PLAN['received_run_state_sha256']
    assert digest('.agent/evidence/114/fixed-inputs.json') == PLAN['fixed_inputs_sha256']
    assert digest('.agent/evidence/114/current-source-inputs.json') == PLAN['source_manifest_sha256']
    assert digest('.agent/contracts/114.json') == SOURCE['contract_sha256']
    for path, meta in {**FIXED['files'], **SOURCE['source_paths']}.items():
        assert digest(path) == meta['sha256'], path

def capture(command, name):
    stability()
    raw_path = E / (name + '-output.txt')
    evidence = E / (name + '.txt')
    assert not raw_path.exists() and not evidence.exists()
    print('START:', name, command, flush=True)
    with raw_path.open('wb') as output:
        done = subprocess.run(command, shell=True, executable='/bin/bash', cwd=ROOT,
                              stdout=output, stderr=subprocess.STDOUT,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    original = raw_path.read_bytes()
    normalized = re.sub(rb'(?m)^(COMMAND:|CANDIDATE_SHA:|EXIT:)', rb'OUTPUT: \1', original)
    evidence.write_bytes(('COMMAND: ' + command + '\nCANDIDATE_SHA: ' + C + '\n').encode()
                         + normalized + (b'\n' if normalized and not normalized.endswith(b'\n') else b'')
                         + ('EXIT: %d\n' % done.returncode).encode())
    entry = {'command': command, 'exit_code': done.returncode,
             'evidence': '.agent/evidence/114/' + name + '.txt'}
    RESULTS.append(entry)
    result_path = E / 'qa-attempt1-progress.json'
    if result_path.exists():
        old = json.loads(result_path.read_bytes())
        assert old['candidate_commit'] == C and old['checks'] == RESULTS[:-1]
    result_path.write_text(json.dumps({'stage': 'actual-fresh-qa-progress',
                          'candidate_commit': C, 'checks': RESULTS,
                          'at': datetime.datetime.now(datetime.timezone.utc).isoformat()},
                          indent=2) + '\n')
    print('RESULT:', name, 'EXIT', done.returncode, flush=True)
    if done.returncode != 0:
        print('Genuine failure: stopped without source/contract/state repair or rerun.', flush=True)
        return False
    stability()
    return True

def main():
    assert [test['command'] for test in CONTRACT['verification']] == PLAN['checks']
    for number, test in enumerate(CONTRACT['verification'], 1):
        if not capture(test['command'], 'qa-%02d' % number):
            return 1
    if not capture(PLAN['ownspot']['command'], '114-qa-adversarial'):
        return 1
    print('FORMAL QA execution complete:12 canonical checks and1 own spot; '
          'all actual EXIT0; source/fixed/coordination stability preserved.', flush=True)
    return 0

if __name__ == '__main__':
    sys.exit(main())
