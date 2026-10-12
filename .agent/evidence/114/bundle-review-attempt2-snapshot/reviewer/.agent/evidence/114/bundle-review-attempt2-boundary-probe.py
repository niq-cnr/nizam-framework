#!/usr/bin/env python3
"""Reviewer2 preregistered scratch-only boundary challenges; never future gates."""
import pathlib,tempfile,shutil,importlib.util,json,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('review114controls',ROOT/'.agent/evidence/114/private/controls.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);C=M.C
PLAN=[('missing-installed-entry',1,'INSTALLED_INVENTORY'),('replacement-installed-bytes',1,'HISTORY:.nizam/NIZAM.json'),('known-installed-file-symlink',1,'INSTALLED_REGULAR_FILES'),('installed-directory-symlink',1,'INSTALLED_INVENTORY'),('historical-current-version',0,'PASS'),('next-patch-version',1,'FIXED_FUTURE_VERSION'),('wide-major-version',1,'FIXED_FUTURE_VERSION'),('sentence-terminal-future-version',1,'FIXED_FUTURE_VERSION')]
for name,exit_code,diagnostic in PLAN: print('PREREGISTERED',json.dumps({'name':name,'expected_exit':exit_code,'expected_diagnostic':diagnostic,'classification':'CONTROL evidence/installed immutable','proof_scope':'scratch predicate only; no SourceReview/QA/capture/gate fabrication'}),flush=True)
def exercise(name,call,expected,diagnostic):
 try:call();rc=0;message='PASS'
 except C.Failure as e:rc=1;message=str(e)
 print('ACTUAL',name,'EXIT'+str(rc),message,'EXPECTED_EXIT'+str(expected),'EXPECTED_DIAGNOSTIC',diagnostic,flush=True)
 return rc==expected and message==diagnostic
with tempfile.TemporaryDirectory(prefix='nizam114-review2-boundary-',dir='/home/cnross/.tmp') as td:
 scratch=pathlib.Path(td)/'repo';shutil.copytree(ROOT,scratch,ignore=shutil.ignore_patterns('.git','__pycache__'))
 assert exercise('history-baseline',lambda:C.history(scratch),0,'PASS')
 p=scratch/'.nizam/NIZAM.json';saved=p.read_bytes();permissions=p.stat().st_mode&0o7777
 for name,mutation,diagnostic in [('missing-installed-entry','missing','INSTALLED_INVENTORY'),('replacement-installed-bytes','bytes','HISTORY:.nizam/NIZAM.json'),('known-installed-file-symlink','symlink','INSTALLED_REGULAR_FILES')]:
  backup=pathlib.Path(td)/'original.json';backup.write_bytes(saved)
  try:
   if mutation=='missing':p.unlink()
   elif mutation=='bytes':p.write_bytes(saved+b'\nREVIEWER CONTROL CORRUPTION\n')
   else:p.unlink();p.symlink_to(backup)
   ok=exercise(name,lambda:C.history(scratch),1,diagnostic)
  finally:
   if p.is_symlink():p.unlink()
   p.write_bytes(saved);p.chmod(permissions)
  assert exercise(name+'-restored',lambda:C.history(scratch),0,'PASS')
  if not ok:sys.exit(1)
 directory=scratch/'.nizam/tools';backup=pathlib.Path(td)/'tools-original';directory.rename(backup);directory.symlink_to(backup,target_is_directory=True)
 try:ok=exercise('installed-directory-symlink',lambda:C.history(scratch),1,'INSTALLED_INVENTORY')
 finally:directory.unlink();backup.rename(directory)
 assert exercise('directory-symlink-restored',lambda:C.history(scratch),0,'PASS')
 if not ok:sys.exit(1)
text=M.dossier_fixture()
for name,addition,expected in [('historical-current-version','Historical versions v0.14.3 and current v1.5.0',0),('next-patch-version','Next release v1.5.1',1),('wide-major-version','Next release v12.34.567',1),('sentence-terminal-future-version','Next release v1.10.0.',1)]:
 diagnostic='PASS' if not expected else 'FIXED_FUTURE_VERSION'
 ok=exercise(name,lambda:C.dossier(text+'\n'+addition+'\n'),expected,diagnostic)
 assert exercise(name+'-restored',lambda:C.dossier(text),0,'PASS')
 if not ok:sys.exit(1)
print('REVIEWER_BOUNDARY_PROBES:PASS; scratch component only')
