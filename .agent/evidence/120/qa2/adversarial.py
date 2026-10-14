"""One QA-originated spot-check: no replay of receipt argv or mutating Git commands."""
import copy
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
root=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('qa120_fixture',root/'tools/test_workflow_assurance.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
api=m.load_api()
os.environ['NIZAM_WA120_FIXTURE']='observed'
with tempfile.TemporaryDirectory(prefix='nizam120-qa-ownspot-') as parent:
    f=m.ReceiptFixture(api,parent,alternate=True)
    assert f.capture['exit_code']==0 and f.capture['executed'] is True
    files=f.snapshot(); inputs=copy.deepcopy((f.policy,f.receipt,f.state)); seen=[]; forbidden=[]
    original=subprocess.Popen
    class GuardDenied(RuntimeError): pass
    def guarded(argv,*args,**kwargs):
        command=argv[3:] if type(argv) is list else []
        if command[:2]==['--literal-pathspecs','ls-tree']: command=command[1:]
        allowed=(type(argv) is list and len(argv)>=4 and argv[:3]==['git','-C',str(f.root)] and bool(command) and command[0] in ('rev-parse','ls-tree','cat-file','merge-base','remote') and (command[0]!='remote' or command[1:3]==['get-url','origin']))
        if not allowed:
            forbidden.append(argv);raise GuardDenied('unapproved command execution')
        seen.append(argv);return original(argv,*args,**kwargs)
    subprocess.Popen=guarded
    try:
        try: subprocess.run([sys.executable,'-c','raise SystemExit(99)'])
        except GuardDenied: pass
        else: raise AssertionError('process guard control did not reject')
        assert len(forbidden)==1;forbidden.clear()
        actual=api.verify_stage_receipt(f.root,f.receipt,policy=f.policy)
        proposal=api.plan_receipt_transition(f.root,f.state,f.receipt,policy=f.policy)
        assert actual==f.receipt and proposal['action']=='advance'
        assert api.plan_receipt_transition(f.root,proposal['state'],f.receipt,policy=f.policy)['action']=='noop'
        assert not forbidden and seen,'no observed readonly Git calls'
    finally: subprocess.Popen=original
    assert (f.policy,f.receipt,f.state)==inputs and f.snapshot()==files
    print('PASS exactly one independent command-nonexecution spot: real fixture capture precedes guard; injected nonGit command blocked; verify/advance/noop use only observed readonly Git commands; no receipt argv replay, file/input mutation')
