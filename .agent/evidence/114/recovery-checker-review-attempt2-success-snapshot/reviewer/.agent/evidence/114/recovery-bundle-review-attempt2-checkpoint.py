"""Independent reviewer2 CONTROL checkpoint; no source/QA/capture execution."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,stat,subprocess,sys
ROOT=Path.cwd().resolve();E=ROOT/'.agent/evidence/114';H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='480c102a5f3119fd8b645d3cf2f3e2ad793e2b9a'
assert H(E/'fixed-inputs.json')=='d5ffdc6fcbdef8c292de8d4b06e4a570386b1021f9201df8a0e9dee3b2ccfccc'
assert H(ROOT/'.agent/contracts/114.json')=='fd0d1be4ce0f25bcd632c49b209557bb910053866f8df8a28e062256f98fc02e'
fixed=json.loads((E/'fixed-inputs.json').read_text())
assert len(fixed['files'])==768
for p,m in fixed['files'].items():
 f=ROOT/p;assert f.is_file() and not f.is_symlink() and H(f)==m['sha256'] and stat.S_IMODE(f.stat().st_mode)==m['permissions'],p
handoff=json.loads((E/'recovery-checker-attempt2-handoff.json').read_text())
for p,h in handoff['files'].items():assert H(ROOT/p)==h,p
for p in [E/'check_114.py',E/'private/controls.py',E/'evidence_gate.py']:ast.parse(p.read_text())
prior=json.loads((E/'private/recovery1-history.json').read_text())['files'];assert len(prior)==203
authorbase=ROOT/prior['recovery-author1:.agent/evidence/114/private/base/.agent/run_state.json']['path']
oldbase=authorbase.parents[1]
for f in (E/'checker-review-attempt3-snapshot/test-author/.agent/evidence/114/private/base').rglob('*'):
 if f.is_file():
  relative=f.relative_to(E/'checker-review-attempt3-snapshot/test-author/.agent/evidence/114/private/base')
  current=E/'private/base'/relative
  assert f.read_bytes()==current.read_bytes() and stat.S_IMODE(f.stat().st_mode)==stat.S_IMODE(current.stat().st_mode),str(current)
oldplan=ROOT/prior['recovery-author1:.agent/evidence/114/private/negative-plan.json']['path']
assert json.loads((E/'private/negative-plan.json').read_text())['controls'][:43]==json.loads(oldplan.read_text())['controls']
assert len(json.loads((E/'private/negative-plan.json').read_text())['controls'])==48
oldcontrols=ROOT/prior['recovery-author1:.agent/evidence/114/private/controls.py']['path']
def positives(p):
 tree=ast.parse(p.read_text());results=[]
 for node in ast.walk(tree):
  if isinstance(node,ast.For) and isinstance(node.target,ast.Name) and node.target.id=='addition':results.extend(ast.literal_eval(node.iter))
 return results
assert positives(oldcontrols)==positives(E/'private/controls.py')[:13] and len(positives(E/'private/controls.py'))==17
assert H(E/'evidence_gate.py')=='6ee76ff402671138fee6731f49bb2c9082dc6788038302ccecbeb224fc7b9532'
s=importlib.util.spec_from_file_location('review2_checker',E/'check_114.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
C.history(ROOT);C.state_data(C.obj(ROOT,C.CANON[2]),False)
print('REVIEW2 metadata CONTROL PASS:768 fixed/fullpermissions/handoff hashes;original privatebase/4800/4799nonDEBT/install239/supplement485/separate203 past-recovery map;43 prior negatives/13positives exact retained;live authorized051.67 and actualstate;capture6ee.',flush=True)
print('INNER COMMAND: PYTHONDONTWRITEBYTECODE=1 python3 .agent/evidence/114/private/controls.py --root .',flush=True)
r=subprocess.run([sys.executable,str(E/'private/controls.py'),'--root','.'],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
print('ACTUAL_CHILD_EXIT:',r.returncode,flush=True)
if r.returncode:raise SystemExit(r.returncode)
print('REVIEW2 CONTROL CHECKPOINT PASS; no source/formalQA/production completion.')
