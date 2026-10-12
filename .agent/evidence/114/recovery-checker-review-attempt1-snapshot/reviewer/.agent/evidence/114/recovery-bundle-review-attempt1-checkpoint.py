"""Independent reviewer CONTROL checkpoint; does not author production gates."""
from pathlib import Path
import ast, hashlib, importlib.util, json, os, stat, subprocess, sys
ROOT=Path.cwd().resolve(); E=ROOT/'.agent/evidence/114'
expected='480c102a5f3119fd8b645d3cf2f3e2ad793e2b9a'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==expected
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H(E/'fixed-inputs.json')=='85197e8832f66e90eb1ce58144a47ebf4c25f6c9f0a89121f86b7f550d904a9a'
assert H(ROOT/'.agent/contracts/114.json')=='fd0d1be4ce0f25bcd632c49b209557bb910053866f8df8a28e062256f98fc02e'
for p in [E/'check_114.py',E/'private/controls.py',E/'evidence_gate.py']: ast.parse(p.read_text())
fixed=json.loads((E/'fixed-inputs.json').read_text())
for p,m in fixed['files'].items():
 f=ROOT/p;assert f.is_file() and not f.is_symlink() and H(f)==m['sha256'] and stat.S_IMODE(f.stat().st_mode)==m['permissions'],p
assert len(fixed['files'])==552
handoff=json.loads((E/'recovery-checker-attempt1-handoff.json').read_text())
for p,h in handoff['files'].items():assert H(ROOT/p)==h,p
assert len(handoff['files'])==17
old=E/'checker-review-attempt3-snapshot/test-author/.agent/evidence/114/private'
for f in (old/'base').rglob('*'):
 if f.is_file():
  current=E/'private/base'/f.relative_to(old/'base')
  assert current.read_bytes()==f.read_bytes() and stat.S_IMODE(current.stat().st_mode)==stat.S_IMODE(f.stat().st_mode),str(current)
oldplan=json.loads((old/'negative-plan.json').read_text())['controls'];newplan=json.loads((E/'private/negative-plan.json').read_text())['controls']
assert newplan[:len(oldplan)]==oldplan and len(oldplan)==29 and len(newplan)==43
assert H(E/'evidence_gate.py')=='6ee76ff402671138fee6731f49bb2c9082dc6788038302ccecbeb224fc7b9532'
s=importlib.util.spec_from_file_location('review114',E/'check_114.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
C.history(ROOT);C.state_data(C.obj(ROOT,C.CANON[2]),False)
print('REVIEWER metadata CONTROL PASS:552 fixed SHA/fullpermissions;17 handoff hashes; original privatebase/29 intents retained;4800 history/4799 nonDEBT/install239/supplement485;actual authorized051.67/currentstate;capture unchanged.',flush=True)
command=[sys.executable,str(E/'private/controls.py'),'--root','.']
print('INNER COMMAND: PYTHONDONTWRITEBYTECODE=1 python3 .agent/evidence/114/private/controls.py --root .',flush=True)
r=subprocess.run(command,cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
print('ACTUAL_CHILD_EXIT:',r.returncode,flush=True)
if r.returncode:raise SystemExit(r.returncode)
print('REVIEWER CONTROL CHECKPOINT PASS; no source/readiness/formalQA/production completion claim.')
