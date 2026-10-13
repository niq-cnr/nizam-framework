"""Fresh independent recovery baseline/control execution; not actual feature QA."""
import hashlib
import importlib.util
import json
from pathlib import Path
import os
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[3]
E=ROOT/'.agent/evidence/115'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main():
    runner=load('recovery_acceptance',ROOT/'tools/test_workflow_assurance.py')
    baseline=load('independent_naive_baseline',E/'recovery-naive-baseline-attempt1.py')
    revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    lines=['COMMAND: PYTHONDONTWRITEBYTECODE=1 python3 .agent/evidence/115/recovery-selfcheck-attempt1.py','REVISION: '+revision];rows=[]
    try:
        os.environ['NIZAM_WA_TEST_VALUE']='initial-observed-value'
        with tempfile.TemporaryDirectory(prefix='nizam-recovery-baseline-positive-') as temp:
            fixture=runner.Fixture(temp);identity=fixture.assess(baseline)
            assert identity['source_commit']==fixture.commit and identity['repository']==runner.git(fixture.root,'remote','get-url','origin')
            assert identity['assessed_inputs']['source'][0]['sha256']==runner.sha((fixture.root/'src/code.py').read_bytes())
            assert baseline.compare_identity(identity,identity) is True
            append=runner.record();append['history'].append({'kind':'explicit-positive-control'})
            assert baseline.verify_record_update(runner.record(),append,['/history']) is True
            try:runner.cli_controls(baseline,fixture,identity)
            except AssertionError as exc:
                assert 'CLI duplicate manifest key rejected after successful setup' in str(exc)
                lines.append('PASS baseline actual CLI positive/setup then intended duplicate-key policy red: '+str(exc))
            else:raise AssertionError('expected naive duplicate-key defect not detected')
        lines.append('PASS valid Git fixture/origin/commit/bytes and unchanged/owned-append positives')
        for case in runner.CASES:
            try:runner.run_case(case,baseline)
            except AssertionError as exc:
                assert str(exc).startswith('POLICY_ASSERTION: ')
                row={'case':case,'exit':1,'classification':'intended-policy-red','assertion':str(exc)};rows.append(row);lines.append(json.dumps(row))
            else:raise AssertionError('naive baseline case false-pass '+case)
        for mode in ('--scope','--scope-controls'):
            command=['python3','tools/test_workflow_assurance.py',mode,'--base',runner.BASE]
            result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
            lines += ['COMMAND: PYTHONDONTWRITEBYTECODE=1 '+' '.join(command),'STDOUT: '+result.stdout,'STDERR: '+result.stderr,'EXIT: '+str(result.returncode)]
            assert result.returncode==0,'recovery '+mode+' actual failed'
        assert not (ROOT/'tools/workflow_assurance.py').exists(),'no product Source before independent bundle approval'
        lines.append('EXIT: 0')
        raw=E/'recovery-selfcheck-attempt1.txt';assert not raw.exists();raw.write_text('\n'.join(lines)+'\n')
        files=['tools/test_workflow_assurance.py','.agent/evidence/115/recovery-scope-guard.py','.agent/evidence/115/recovery-naive-baseline-attempt1.py','.agent/evidence/115/api-interface.json','.agent/evidence/115/recovery-selfcheck-attempt1.py',str(raw.relative_to(ROOT))]
        handoff={'feature':'115','epoch':'115-recovery-1','author':'/root/wa_test_author','developer':'/root/wa_generator','independent_reviewer':'/root/wa_validator','approved_base':revision,'test_lines':len((ROOT/files[0]).read_text().splitlines()),'files_sha256':{path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in files},'actual_exit':0,'cases':rows,'source_exists':False,'controls':'exact contract116/runcomplete regressions, previous five rejects, valid pre-source/delivered/private-mock captured states, public mock rejection and missing capture rejection','review_status':'pending-independent-corrected-bundle-review'}
        p=E/'recovery-author-handoff-attempt1.json';assert not p.exists();p.write_text(json.dumps(handoff,indent=2)+'\n');print(json.dumps(handoff,indent=2))
    except Exception as exc:
        lines += ['FAIL: '+type(exc).__name__+': '+str(exc),'EXIT: 1'];p=E/'recovery-selfcheck-attempt1-failed.txt';assert not p.exists();p.write_text('\n'.join(lines)+'\n');raise

if __name__=='__main__':main()
