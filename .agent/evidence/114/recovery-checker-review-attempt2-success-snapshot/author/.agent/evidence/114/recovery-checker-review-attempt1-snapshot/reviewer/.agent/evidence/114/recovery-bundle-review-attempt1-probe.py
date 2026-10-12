"""Preregistered independent reviewer SCRATCH probes; first mismatch stops."""
from pathlib import Path
import copy,importlib.util,json,shutil,stat,tempfile
ROOT=Path.cwd().resolve();E=ROOT/'.agent/evidence/114'
s=importlib.util.spec_from_file_location('own_controls',E/'private/controls.py');K=importlib.util.module_from_spec(s);s.loader.exec_module(K);C=K.C
cases=[
 ('original-actual-SBCL-context',0,'PASS','Recorded SBCL version 2.2.9.debian is a toolchain input; framework release remains v1.5.0.'),
 ('ASDF-Python-punctuation-positive',0,'PASS','Recorded ASDF version: 3.3.5; Python version (V3.14.0) is a toolchain input; current framework version 1.5.0.'),
 ('same-sentence-framework-negative',1,'FIXED_FUTURE_VERSION','SBCL version 2.2.9.debian is recorded but the next framework release will be V1.10.0.'),
 ('wide-bare-framework-negative',1,'FIXED_FUTURE_VERSION','Python version 3.14.0 is recorded; next framework version will be 123.456.789!'),
 ('ASDF-framework-conjunction-negative',1,'FIXED_FUTURE_VERSION','ASDF version 3.3.5 is installed and framework release candidate 1.10.0.'),
]
def result(action):
 try:action();return 0,'PASS'
 except C.Failure as error:return 1,str(error)
def check(name,expected,diagnostic,action,restore):
 print('PREREGISTERED',name,'expected EXIT'+str(expected),'diagnostic='+diagnostic,flush=True)
 exitcode,actual=result(action);print('ACTUAL',name,'EXIT'+str(exitcode),'diagnostic='+actual,flush=True)
 restored,rd=result(restore);print('RESTORED',name,'EXIT'+str(restored),'diagnostic='+rd,flush=True)
 if exitcode!=expected or (expected and actual!=diagnostic) or restored!=0:
  print('FIRST_ACTUAL_BOUNDARY_FAILURE:'+name,flush=True);raise SystemExit(1)
base=K.dossier_fixture()
for name,expected,diagnostic,text in cases:
 check(name,expected,diagnostic,lambda t=text:C.dossier(base+'\n'+t+'\n'),lambda:C.dossier(base))
with tempfile.TemporaryDirectory(prefix='nizam114-reviewer-boundary-',dir='/home/cnross/.tmp') as td:
 scratch=Path(td);assert scratch.parent==Path('/home/cnross/.tmp')
 original='.agent/contracts/114.json';meta=C.obj(ROOT,C.E+'recovery-halt-inventory.json')['files'][original]
 p=scratch/meta['path'];p.parent.mkdir(parents=True);shutil.copy2(ROOT/meta['path'],p)
 before=stat.S_IMODE(p.stat().st_mode)
 def corrupt_mode():p.chmod(before^0o020);C.supplemental_members(scratch,{original:meta})
 def restore_mode():p.chmod(before);C.supplemental_members(scratch,{original:meta})
 check('archive-fullpermission-change',1,'ARCHIVE_MEMBER:'+original,corrupt_mode,restore_mode)
texts=[C.raw(ROOT,p).decode() for p in (C.E+'private/original-debt.md',C.E+'recovery-halt-debt.md',C.E+'recovery-authorized-debt.md')]
check('unowned-debt-log-change',1,'DEBT051_CURRENT_BYTES',lambda:C.debt_data(*texts,texts[-1].replace('Resolve only NDEBT-050','Alter only NDEBT-050',1),False),lambda:C.debt_data(*texts,texts[-1],False))
data=C.recovery_state()
def reset_contract():
 d=copy.deepcopy(data);d['circuit_breaker']['114-contract']['attempts']=0;C.state_data(d,False)
check('original114-contract-counter-reset',1,'OLD_COUNTER:114-contract',reset_contract,lambda:C.state_data(copy.deepcopy(data),False))
check('explicit-SBCL-runtime-subject-positive',0,'PASS',lambda:C.dossier(base+'\nRecorded SBCL runtime version 2.2.9.debian is a toolchain input; framework release remains v1.5.0.\n'),lambda:C.dossier(base))
print('OWN SCRATCH BOUNDARIES PASS; CONTROL ONLY, no production gates or acceptance.')
