#!/usr/bin/env python3
"""Final reviewer-owned focused scratch probes; no production approvals or repairs."""
import pathlib,tempfile,shutil,importlib.util,json,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('finalreview114',ROOT/'.agent/evidence/114/private/controls.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);C=M.C
PLAN=[('installed-root-symlink',1,'INSTALLED_INVENTORY'),('installed-fullmode-changed',1,'HISTORY:.nizam/NIZAM.json'),('release-candidate-bare-punctuation',1,'FIXED_FUTURE_VERSION'),('version-will-be-bare',1,'FIXED_FUTURE_VERSION'),('uppercase-sentence-core',1,'FIXED_FUTURE_VERSION'),('historical-current-toolchain-date',0,'PASS'),('named-toolchain-version-word',0,'PASS')]
for name,exit_code,diagnostic in PLAN:print('PREREGISTERED',json.dumps({'name':name,'expected_exit':exit_code,'expected_diagnostic':diagnostic,'classification':'privateCONTROL evidence/installedimmutable','scope':'scratch predicate only; no actualsource/SourceReview/QA/capture/gate claim'}),flush=True)
def run(name,call,expected,diagnostic):
 try:call();rc=0;message='PASS'
 except C.Failure as e:rc=1;message=str(e)
 print('ACTUAL',name,'EXIT'+str(rc),message,'EXPECTED_EXIT'+str(expected),'EXPECTED_DIAGNOSTIC',diagnostic,flush=True)
 return rc==expected and message==diagnostic
with tempfile.TemporaryDirectory(prefix='nizam114-final-review-boundary-',dir='/home/cnross/.tmp') as td:
 scratch=pathlib.Path(td)/'repo';shutil.copytree(ROOT,scratch,ignore=shutil.ignore_patterns('.git','__pycache__'))
 assert run('history-baseline',lambda:C.history(scratch),0,'PASS')
 installed=scratch/'.nizam';backup=pathlib.Path(td)/'original-installed';installed.rename(backup);installed.symlink_to(backup,target_is_directory=True)
 try:ok=run('installed-root-symlink',lambda:C.history(scratch),1,'INSTALLED_INVENTORY')
 finally:installed.unlink();backup.rename(installed)
 assert run('root-symlink-restored',lambda:C.history(scratch),0,'PASS')
 if not ok:sys.exit(1)
 p=scratch/'.nizam/NIZAM.json';mode=p.stat().st_mode&0o7777;p.chmod(mode^0o100)
 try:ok=run('installed-fullmode-changed',lambda:C.history(scratch),1,'HISTORY:.nizam/NIZAM.json')
 finally:p.chmod(mode)
 assert run('fullmode-restored',lambda:C.history(scratch),0,'PASS')
 if not ok:sys.exit(1)
text=M.dossier_fixture()
CASES=[('release-candidate-bare-punctuation','Next release candidate: 1.10.0;',1),('version-will-be-bare','Framework version will be 1.10.0.',1),('uppercase-sentence-core','The next MINOR is V12.34.567!',1),('historical-current-toolchain-date','Historical framework version 0.99.123; current V1.5.0. Recorded SBCL 2.2.9.debian, ASDF 3.3.5, Python 3.13.1; assessed 2026-10-12.',0),('named-toolchain-version-word','Recorded SBCL version 2.2.9.debian is a toolchain input; framework release remains v1.5.0.',0)]
for name,addition,expected in CASES:
 print('ACTUAL_INPUT',name,json.dumps(addition),flush=True)
 diagnostic='FIXED_FUTURE_VERSION' if expected else 'PASS'
 ok=run(name,lambda:C.dossier(text+'\n'+addition+'\n'),expected,diagnostic)
 assert run(name+'-restored',lambda:C.dossier(text),0,'PASS')
 if not ok:sys.exit(1)
print('FINAL_REVIEWER_FOCUSED_PROBES:PASS; scratch only')
