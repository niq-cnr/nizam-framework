"""Reviewer2 preregistered SCRATCH boundaries, stop first mismatch."""
from pathlib import Path
import copy,importlib.util,json,shutil,stat,tempfile
ROOT=Path.cwd().resolve();E=ROOT/'.agent/evidence/114'
s=importlib.util.spec_from_file_location('own2_controls',E/'private/controls.py');K=importlib.util.module_from_spec(s);s.loader.exec_module(K);C=K.C
cases=[
 ('exact-prior-review1-runtime-positive',0,'PASS','Recorded SBCL runtime version 2.2.9.debian is a toolchain input; framework release remains v1.5.0.'),
 ('fresh-nominal-modifiers-positive',0,'PASS','Recorded ASDF dependency resolution build system version is 3.3.5; Python bytecode interpreter version is currently V3.14.0; current framework version 1.5.0.'),
 ('fresh-toolchain-historical-date-positive',0,'PASS','Recorded SBCL native runtime version 2.2.9.debian; archived framework version 0.99.123; current v1.5.0. Build date 2026-10-12.'),
 ('nearest-framework-subject-negative',1,'FIXED_FUTURE_VERSION','Recorded SBCL runtime input establishes next framework release version V1.10.0.'),
 ('finite-predicate-generic-release-negative',1,'FIXED_FUTURE_VERSION','SBCL runtime has next release v1.10.0.'),
 ('same-sentence-width-punctuation-negative',1,'FIXED_FUTURE_VERSION','Python interpreter version 3.14.0 is recorded but framework release candidate (123.456.789)!'),
 ('three-declarations-last-framework-negative',1,'FIXED_FUTURE_VERSION','SBCL runtime version 2.2.9.debian; ASDF system version 3.3.5 and next framework version will be 1.10.0.')]
base=K.dossier_fixture()
def result(action):
 try:action();return 0,'PASS'
 except C.Failure as error:return 1,str(error)
def check(name,expected,diagnostic,action,restore):
 print('PREREGISTERED',name,'expected EXIT'+str(expected),'diagnostic='+diagnostic,flush=True)
 code,actual=result(action);print('ACTUAL',name,'EXIT'+str(code),'diagnostic='+actual,flush=True)
 restored,rd=result(restore);print('RESTORED',name,'EXIT'+str(restored),'diagnostic='+rd,flush=True)
 if code!=expected or expected and actual!=diagnostic or restored!=0:
  print('FIRST_ACTUAL_BOUNDARY_FAILURE:'+name,flush=True);raise SystemExit(1)
for name,code,diagnostic,text in cases:check(name,code,diagnostic,lambda t=text:C.dossier(base+'\n'+t+'\n'),lambda:C.dossier(base))
with tempfile.TemporaryDirectory(prefix='nizam114-review2-boundary-',dir='/home/cnross/.tmp') as td:
 scratch=Path(td);assert scratch.parent==Path('/home/cnross/.tmp')
 name='recovery-reviewer1:.agent/evidence/114/recovery-bundle-review-attempt1-probe.py'
 meta=C.obj(ROOT,C.E+'private/recovery1-history.json')['files'][name]
 p=scratch/meta['path'];p.parent.mkdir(parents=True);shutil.copy2(ROOT/meta['path'],p);saved=p.read_bytes();permissions=stat.S_IMODE(p.stat().st_mode)
 def symlink_past():p.unlink();p.symlink_to(ROOT/meta['path']);C.supplemental_members(scratch,{name:meta})
 def restore_past():
  p.unlink();p.write_bytes(saved);p.chmod(permissions);C.supplemental_members(scratch,{name:meta})
 check('prior-first-probe-symlink-substitution',1,'ARCHIVE_MEMBER:'+name,symlink_past,restore_past)
texts=[C.raw(ROOT,p).decode() for p in (C.E+'private/original-debt.md',C.E+'recovery-halt-debt.md',C.E+'recovery-authorized-debt.md')]
altered=texts[-1].replace('| NDEBT-051 | 2026-10-12 | Medium |','| NDEBT-051 | 2026-10-12 | Low |',1)
assert altered!=texts[-1]
check('authorized051-unowned-severity-change',1,'DEBT051_FIELDS',lambda:C.debt_data(texts[0],texts[1],altered,altered,False),lambda:C.debt_data(*texts,texts[-1],False))
data=C.recovery_state()
def reset():
 d=copy.deepcopy(data);d['circuit_breaker']['114-recovery-contract']['attempts']=0;C.state_data(d,False)
check('renewed-precode-counter-reset',1,'OLD_COUNTER:114-recovery-contract',reset,lambda:C.state_data(copy.deepcopy(data),False))
print('OWN REVIEW2 SCRATCH ALL10 BOUNDARIES PASS; CONTROL ONLY, no Source or production gates.')
