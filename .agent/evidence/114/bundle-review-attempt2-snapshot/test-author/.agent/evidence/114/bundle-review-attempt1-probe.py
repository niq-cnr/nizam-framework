#!/usr/bin/env python3
"""Preregistered independent reviewer scratch probes; evidence only, no gates."""
import pathlib,importlib.util,tempfile,shutil,json,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('review_controls',ROOT/'.agent/evidence/114/private/controls.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);C=M.C
PLAN=[{'name':'future-version-multidigit','scope':'private dossier predicate CONTROL; actual semantic gate not fabricated','expected_exit':1,'expected_diagnostic':'FIXED_FUTURE_VERSION','classification':'evidence','mutation':'append Next release v1.10.0 to otherwise valid CONTROL dossier'}, {'name':'ignored-installed-extra-file','scope':'private history predicate CONTROL; no old gate execution','expected_exit':1,'expected_diagnostic':'INSTALLED_INVENTORY','classification':'unclassified/installed immutable','mutation':'add .nizam/tools/__pycache__/reviewer_extra.pyc, leaving all239 known installed and4800 historical bytes/fullmodes unchanged'}]
for x in PLAN: print('PREREGISTERED',json.dumps(x,sort_keys=True),flush=True)
def call(name,fn,expected,diagnostic):
 try: fn();rc=0;message='PASS'
 except C.Failure as e: rc=1;message=str(e)
 print('ACTUAL',name,'EXIT'+str(rc),message,'EXPECTED_EXIT'+str(expected),'EXPECTED_DIAGNOSTIC',diagnostic,flush=True)
 return rc==expected and (not expected or message==diagnostic)
text=M.dossier_fixture();call('dossier-positive',lambda:C.dossier(text),0,'PASS')
version_ok=call('future-version-multidigit',lambda:C.dossier(text+'\nNext release v1.10.0\n'),1,'FIXED_FUTURE_VERSION')
call('dossier-restored',lambda:C.dossier(text),0,'PASS')
with tempfile.TemporaryDirectory(prefix='nizam114-review-inventory-',dir='/home/cnross/.tmp') as td:
 scratch=pathlib.Path(td)/'repo';shutil.copytree(ROOT,scratch,ignore=shutil.ignore_patterns('.git','__pycache__'))
 call('history-positive',lambda:C.history(scratch),0,'PASS')
 rel='.nizam/tools/__pycache__/reviewer_extra.pyc';p=scratch/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'REVIEWER CONTROL ONLY; not bytecode\n')
 ignored=subprocess.run(['git','-C',str(ROOT),'check-ignore','--no-index',rel],capture_output=True,text=True)
 print('READONLY_IGNORE_COMMAND',json.dumps(['git','-C',str(ROOT),'check-ignore','--no-index',rel]),'ACTUAL_EXIT',ignored.returncode,'OUTPUT',ignored.stdout.strip(),flush=True)
 before=[x for x in C.obj(ROOT,C.E+'private/history.json') if x.startswith('.nizam/')]
 actual=[str(x.relative_to(scratch)) for x in (scratch/'.nizam').rglob('*') if x.is_file() or x.is_symlink()]
 print('EXPECTED_INSTALLED_COUNT',len(before),'ACTUAL_SCRATCH_INSTALLED_COUNT',len(actual),'EXTRA',sorted(set(actual)-set(before)),flush=True)
 assert ignored.returncode==0 and len(actual)==len(before)+1
 inventory_ok=call('ignored-installed-extra-file',lambda:C.history(scratch),1,'INSTALLED_INVENTORY')
 p.unlink();call('history-restored',lambda:C.history(scratch),0,'PASS')
print('PROBE_RESULTS',json.dumps({'version_expected_rejection':version_ok,'inventory_expected_rejection':inventory_ok}),flush=True)
if not version_ok or not inventory_ok:sys.exit(1)
