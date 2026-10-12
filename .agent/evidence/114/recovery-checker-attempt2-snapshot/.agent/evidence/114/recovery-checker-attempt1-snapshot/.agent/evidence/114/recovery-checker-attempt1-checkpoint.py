"""One bounded development checkpoint; no Source/future QA acceptance."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

ROOT=Path.cwd().resolve(); E=Path('.agent/evidence/114')
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
result_path=E/'recovery-checker-attempt1-development-result.json'
assert not result_path.exists(), 'Checkpoint already recorded; rerun forbidden'
result={'stage':'testauthor-development-only','attempt':1,'epoch':'114-recovery-1','actor':'/root/adapter_acceptance_recovery_113','approved_base':'480c102a5f3119fd8b645d3cf2f3e2ad793e2b9a','checks':[],'passed':False}
try:
 w=json.loads((E/'recovery-checker-attempt1-workspace.json').read_text())
 assert Path(w['root']).resolve()==ROOT and w['actor']==result['actor']
 assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==result['approved_base']
 assert H('.agent/contracts/114.json')==w['approved_contract_sha256']=='fd0d1be4ce0f25bcd632c49b209557bb910053866f8df8a28e062256f98fc02e'
 for p in [E/'check_114.py',E/'private/controls.py',E/'evidence_gate.py']: ast.parse(p.read_text())
 assert H(E/'evidence_gate.py')=='6ee76ff402671138fee6731f49bb2c9082dc6788038302ccecbeb224fc7b9532'
 s=importlib.util.spec_from_file_location('development114',E/'check_114.py'); C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
 C.history(ROOT); C.state_data(C.obj(ROOT,C.CANON[2]),False)
 print('DEVELOPMENT metadata PASS: ASTs/actualapprovedpin/original4800+4799/fullmodes/installed239/supplemental485/authorized051/currentrecoverystate/capture6ee.')
 result['checks'].append({'kind':'actual-input-preservation-metadata','exit_code':0})
 for command,output in [
  (['python3',str(E/'check_114.py'),'predecessor'],E/'recovery-checker-attempt1-predecessor-output.txt'),
  (['python3',str(E/'private/controls.py'),'--root','.'],E/'recovery-checker-attempt1-controls-output.txt')]:
  assert not output.exists()
  print('INNER COMMAND: PYTHONDONTWRITEBYTECODE=1 '+' '.join(command),flush=True)
  run=subprocess.run(command,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  output.write_bytes(b'STDOUT:\n'+run.stdout+b'\nSTDERR:\n'+run.stderr+('\nACTUAL_CHILD_EXIT: '+str(run.returncode)+'\n').encode())
  sys.stdout.buffer.write(run.stdout);sys.stderr.buffer.write(run.stderr);sys.stdout.flush();sys.stderr.flush()
  result['checks'].append({'command':'PYTHONDONTWRITEBYTECODE=1 '+' '.join(command),'exit_code':run.returncode,'evidence':str(output)})
  if run.returncode: raise RuntimeError('Actual child checkpoint failure; STOP no inline repair: '+str(output))
 result['passed']=True
 print('DEVELOPMENT ONLY CHECKPOINT PASS:43 targeted negative1/positive0/restored0 and13 declared version positives; source/ModeB/freshQA/capture remain future actual gates.')
except Exception as error:
 result['failure']=str(error)
 print('DEVELOPMENT CHECKPOINT FAILED; STOP: '+str(error),file=sys.stderr)
finally:
 result['helper_sha256']=H(E/'check_114.py');result['controls_sha256']=H(E/'private/controls.py')
 result_path.write_text(json.dumps(result,indent=2)+'\n')
if not result['passed']: raise SystemExit(1)
