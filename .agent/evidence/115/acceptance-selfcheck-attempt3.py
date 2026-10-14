"""Private, independently authored baseline and scope controls; not a public test switch."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / '.agent/evidence/115'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    runner = load('independent_acceptance', ROOT / 'tools/test_workflow_assurance.py')
    baseline = load('naive_valid_api', E / 'naive-baseline-attempt3.py')
    revision = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    logs = ['COMMAND: PYTHONDONTWRITEBYTECODE=1 python3 .agent/evidence/115/acceptance-selfcheck-attempt3.py', 'REVISION: ' + revision]
    cases = []
    try:
        os.environ['NIZAM_WA_TEST_VALUE'] = 'initial-observed-value'
        with tempfile.TemporaryDirectory(prefix='nizam-wa115-baseline-positive-') as temp:
            f = runner.Fixture(temp); identity = f.assess(baseline)
            assert identity['source_commit'] == f.commit
            assert identity['repository'] == runner.git(f.root, 'remote', 'get-url', 'origin')
            assert identity['assessed_inputs']['source'][0]['sha256'] == runner.sha((f.root / 'src/code.py').read_bytes())
            assert baseline.compare_identity(identity, identity) is True
            allowed = runner.record(); allowed['history'].append({'kind':'positive-control'})
            assert baseline.verify_record_update(runner.record(), allowed, ['/history']) is True
            try:
                runner.cli_controls(baseline, f, identity)
            except AssertionError as exc:
                assert 'CLI duplicate manifest key rejected after successful setup' in str(exc), 'CLI baseline failure must be intended strict JSON assertion'
                logs.append('PASS valid baseline CLI positive assess; intended strict-JSON duplicate-key red: '+str(exc))
            else: raise AssertionError('baseline CLI duplicate-key false-pass not detected')
            del os.environ['NIZAM_WA_TEST_VALUE']
            try: f.assess(baseline)
            except baseline.AssuranceError: pass
            else: raise AssertionError('missing observed environment must be typed incomplete input')
        logs.append('PASS baseline positive controls: real committed fixture/setup, origin/commit/bytes, self comparison, allowed append, typed incomplete-input rejection')
        for case in runner.CASES:
            try:
                runner.run_case(case, baseline)
            except AssertionError as exc:
                assert str(exc).startswith('POLICY_ASSERTION: '), 'non-policy baseline assertion: ' + str(exc)
                row = {'case':case, 'exit':1, 'classification':'intended-policy-red', 'assertion':str(exc)}
                cases.append(row); logs.append(json.dumps(row))
            else:
                raise AssertionError('naive baseline false-pass: ' + case)
        command = [sys.executable, str(ROOT / 'tools/test_workflow_assurance.py'), '--scope', '--base', runner.BASE]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        logs += ['COMMAND: ' + ' '.join(command), 'STDOUT: ' + result.stdout, 'STDERR: ' + result.stderr, 'EXIT: ' + str(result.returncode)]
        assert result.returncode == 0, 'scope positive self-check failed'
        for args in (['--case','unknown'], ['--case'], ['--check','foundation-ready'], ['--scope']):
            result = subprocess.run([sys.executable, str(ROOT / 'tools/test_workflow_assurance.py'), *args], cwd=ROOT, capture_output=True, text=True)
            assert result.returncode == 2 and 'error:' in result.stderr, 'CLI fails closed with intended argparse diagnostic'
            logs.append('PASS runner argument rejection ' + repr(args) + ': actual EXIT 2')
        with tempfile.TemporaryDirectory(prefix='nizam-wa115-scope-controls-') as temp:
            scratch = Path(temp) / 'repo'
            subprocess.run(['git','clone','-q','--shared','--no-checkout',str(ROOT),str(scratch)],check=True)
            subprocess.run(['git','-C',str(scratch),'checkout','-q',runner.APPROVED],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            shutil.copyfile(ROOT / 'tools/test_workflow_assurance.py', scratch / 'tools/test_workflow_assurance.py')
            runner.ROOT = scratch
            with contextlib.redirect_stdout(io.StringIO()): runner.scope(runner.BASE)
            logs.append('PASS independent scratch scope positive')
            for name, path, mutate in [
                ('old-proof-byte', '.agent/evidence/115/api-interface.json', lambda p: p.write_bytes(p.read_bytes()+b'\n')),
                ('old-proof-executable-mode', '.agent/evidence/115/api-interface.json', lambda p:p.chmod(0o755)),
                ('archived015-budget', '.agent/run_state.json', lambda p: mutate_json(p,'phase_015_scope_budget_final','total_lines_changed',0)),
                ('phase017-terminal-spoof', 'docs/planning/manifest.json', mutate_manifest),
                ('foreign-current-feature', '.agent/run_state.json', lambda p: mutate_json(p,None,'current_feature','116')),
            ]:
                target=scratch/path; saved=target.read_bytes(); mode=target.stat().st_mode
                try:
                    mutate(target)
                    try: runner.scope(runner.BASE)
                    except AssertionError as exc:
                        assert str(exc).startswith('POLICY_ASSERTION: ')
                        logs.append('PASS targeted scope reject '+name+': '+str(exc))
                    else: raise AssertionError('scope false-pass '+name)
                finally:
                    target.write_bytes(saved); target.chmod(mode)
            with contextlib.redirect_stdout(io.StringIO()): runner.scope(runner.BASE)
            logs.append('PASS scratch restored positive after five specific rejects')
        runner.ROOT=ROOT
        assert not (ROOT/'tools/workflow_assurance.py').exists(), 'source must remain absent before independent bundle approval'
        logs.append('EXIT: 0')
        raw=E/'acceptance-selfcheck-attempt3.txt'; assert not raw.exists(); raw.write_text('\n'.join(logs)+'\n')
        handoff={'feature':'115','author':'/root/wa_test_author','developer':'/root/wa_generator','independent_reviewer':'/root/wa_validator','approved_base':revision,
                 'test_path':'tools/test_workflow_assurance.py','test_sha256':digest(ROOT/'tools/test_workflow_assurance.py'),'test_lines':len((ROOT/'tools/test_workflow_assurance.py').read_text().splitlines()),
                 'baseline_path':'.agent/evidence/115/naive-baseline-attempt3.py','baseline_sha256':digest(E/'naive-baseline-attempt3.py'),
                 'api_sha256':digest(E/'api-interface.json'),'selfcheck_path':'.agent/evidence/115/acceptance-selfcheck-attempt3.py','selfcheck_sha256':digest(Path(__file__)),
                 'raw':'.agent/evidence/115/acceptance-selfcheck-attempt3.txt','raw_sha256':digest(raw),'actual_exit':0,'cases':cases,'source_exists':False,'review_status':'pending-independent-review'}
        path=E/'acceptance-author-handoff-attempt3.json';assert not path.exists();path.write_text(json.dumps(handoff,indent=2)+'\n');print(json.dumps(handoff,indent=2))
    except Exception as exc:
        logs += ['FAIL: '+type(exc).__name__+': '+str(exc),'EXIT: 1']
        raw=E/'acceptance-selfcheck-attempt3-failed.txt'; assert not raw.exists();raw.write_text('\n'.join(logs)+'\n')
        raise

def mutate_json(path,parent,key,value):
    obj=json.loads(path.read_text());target=obj[parent] if parent else obj;target[key]=value;path.write_text(json.dumps(obj))

def mutate_manifest(path):
    obj=json.loads(path.read_text())
    for row in obj['phases']:
        if row['id']=='017-workflow-assurance-foundation':row['status']='complete'
    path.write_text(json.dumps(obj))

if __name__=='__main__': main()
