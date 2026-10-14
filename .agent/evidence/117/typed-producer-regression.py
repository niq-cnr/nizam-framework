"""Reviewer-origin Boolean-actor regression plus declared producer type controls.

All receipts below are expressly private parser fixtures. Public mock rejection
precedes every mutation family; no fixture is a production approval or QA run.
"""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[3]


def main():
    e=ROOT/'.agent/evidence/117'
    spec=importlib.util.spec_from_file_location('typed_producer_guard',e/'scope-guard.py')
    g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    b=json.loads((e/'acceptance-bundle.json').read_text())
    with tempfile.TemporaryDirectory(prefix='nizam117-typed-producer-') as parent:
        scratch=Path(parent)/'repo'
        subprocess.run(['git','clone','-q','--shared','--no-checkout',str(ROOT),str(scratch)],check=True)
        subprocess.run(['git','-C',str(scratch),'checkout','-q',g.APPROVED],check=True)
        paths={v['path'] for v in b['inputs']}|{g.BUNDLE}
        for row in b['baseline_evidence']: paths.update(row[k]['path'] for k in ('setup','positive','red'))
        for path in paths:
            target=scratch/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,target)
        g.ROOT=scratch;reviewer=b['roles']['acceptance_reviewer']
        g.write(g.REVIEW,{'review':'validator-test-bundle-review','feature':'117','actor':reviewer['agent_id'],
                'reviewer_session_id':reviewer['session_id'],'seal_sha256':b['seal_sha256'],
                'issues':[],'missing_acceptance_coverage':[],'unsupported_claims':[],
                'final_verdict':{'approved':True,'summary':'PRIVATE structural parser fixture'}})
        g._private_complete_fixture()
        g.expected_rejection(lambda:g.scope(g.BASE),'mock receipts confined')
        print('PASS public scope rejects private completion receipts',flush=True)
        g._CONTROL_FIXTURE=scratch.resolve()
        with contextlib.redirect_stdout(io.StringIO()):g._scope(g.BASE)
        print('PASS genuine valid private completion with string actors',flush=True)
        contract=g.current('.agent/contracts/117.json')
        def exercise(path,location,value,diagnostic,full=False,missing=False):
            original=(scratch/path).read_bytes();capture=(scratch/g.CAPTURE).read_bytes()
            obj=g.current(path);target=obj
            for key in location[:-1]:target=target[key]
            if missing:target.pop(location[-1])
            else:target[location[-1]]=value
            g.write(path,obj)
            if path in (g.MODE_B,g.QA):
                cap=g.current(g.CAPTURE)
                cap['mode_b_sha256' if path==g.MODE_B else 'qa_sha256']=g.sha(g.safe(path).read_bytes())
                g.write(g.CAPTURE,cap)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    g.expected_rejection(lambda:g._scope(g.BASE) if full else g.completed_receipts(contract),diagnostic)
            finally:
                (scratch/path).write_bytes(original);(scratch/g.CAPTURE).write_bytes(capture)
            g.completed_receipts(contract)
            print('PASS typed producer '+path+' '+str(location)+' '+('missing' if missing else repr(value)),flush=True)
        # Exact reviewer false-pass: change actor to true, update actual capture hash,
        # then require full canonical completion to reject after the valid baseline.
        exercise(g.MODE_B,['actor'],True,'ModeB actor nonempty string',full=True)
        print('PASS exact reviewer Boolean ModeB actor regression with current capture hash',flush=True)
        for path,label in ((g.MODE_B,'ModeB'),(g.QA,'QA')):
            for value in (False,1,1.0,None,[],{},''):
                exercise(path,['actor'],value,label+' actor nonempty string')
            exercise(path,['actor'],None,label+' actor nonempty string',missing=True)
        exercise(g.QA,['actor'],True,'QA actor nonempty string')
        roles=b['roles']
        for role in ('test_author','developer'):
            exercise(g.MODE_B,['actor'],roles[role]['agent_id'],'independent ModeB actor')
            exercise(g.QA,['actor'],roles[role]['agent_id'],'distinct fresh QA actor')
        exercise(g.QA,['actor'],g.current(g.MODE_B)['actor'],'distinct fresh QA actor')
        exercise(g.QA,['actor'],roles['acceptance_reviewer']['agent_id'],'distinct fresh QA actor')
        for path,location,value,diagnostic in [
            (g.CANDIDATE,['revision'],True,'actual SourceC revision'),
            (g.CANDIDATE,['source_sha256'],[],'exact four SourceC hashes'),
            (g.MODE_B,['sealed_dependencies_sha256'],{},'all sealed runtime dependency hashes'),
            (g.MODE_B,['feature'],True,'117-only closure'),
            (g.MODE_B,['final_verdict','approved'],1,'receipt strict approved boolean'),
            (g.QA,['qa_pass'],1,'all twelve exact checks passed'),
            (g.QA,['checks_run'],True,'all twelve exact checks passed'),
            (g.QA,['checks_passed'],12.0,'all twelve exact checks passed'),
            (g.CAPTURE,['passed'],1,'distinct Root capture'),
            (g.CAPTURE,['checks_captured'],True,'distinct Root capture'),
            (g.CAPTURE,['owner'],True,'distinct Root capture')]:
            exercise(path,location,value,diagnostic)
        print('PASS all typed producer controls; private fixtures only',flush=True)


if __name__=='__main__': main()
