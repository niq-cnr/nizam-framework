"""Independent ModeB1 candidate metadata/components only; no formalQA/readiness8."""
from pathlib import Path
import hashlib,importlib.util,json,stat,subprocess,re
ROOT=Path.cwd().resolve();E=ROOT/'.agent/evidence/114'
CANDIDATE='32114a706ff95bcb8e90e371168159a8957a3628';BASE='33fd885115981e7ae479dfff7ad7d5a623d8014c'
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
git=lambda *a:subprocess.check_output(['git',*a])
assert git('rev-parse','HEAD').decode().strip()==CANDIDATE
assert git('rev-parse',CANDIDATE+'^').decode().strip()==BASE
assert git('rev-parse',CANDIDATE+'^{tree}').decode().strip()=='b5f4fcf629d3856c163fb31756894f40f237839f'
s=importlib.util.spec_from_file_location('mode_b114_checker',E/'check_114.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
paths=set(git('diff','--name-only',BASE,CANDIDATE,'--').decode().splitlines());assert paths==set(C.SOURCE)
assert git('diff','--name-only',BASE,CANDIDATE,'--',*C.CANON).strip()==b''
print('MODEB C direct-parentB; exact pure six Source diff; canonical three Git snapshots equalB: PASS',flush=True)
source=C.obj(ROOT,C.E+'current-source-inputs.json');fixed=C.obj(ROOT,C.E+'fixed-inputs.json')
assert H(E/'current-source-inputs.json')=='fb8c287e555892f749d7e0afa6218847bfa7fc969b05dbf17be816c0c880ec88'
assert H(E/'fixed-inputs.json')=='d5ffdc6fcbdef8c292de8d4b06e4a570386b1021f9201df8a0e9dee3b2ccfccc' and len(fixed['files'])==768
assert H(ROOT/'.agent/contracts/114.json')==C.PIN=='fd0d1be4ce0f25bcd632c49b209557bb910053866f8df8a28e062256f98fc02e'
assert C.integrity(ROOT,source,fixed)==CANDIDATE
print('MODEB exact source/CANON3 Git map/seals and768 actualfixed files, C Git replay and root fullpermissions: PASS',flush=True)
handoff=C.obj(ROOT,C.E+'source-attempt3-handoff.json')
assert handoff['candidate_commit']==CANDIDATE and handoff['candidate_parent']==BASE and handoff['development_checkpoint_runs']==1 and handoff['development_checkpoint_exit']==0
for path,m in handoff['source_paths'].items():
 assert H(ROOT/path)==m['sha256'] and stat.S_IMODE((ROOT/path).stat().st_mode)==m['permissions'],path
for path,m in handoff['proofs'].items():
 assert H(ROOT/path)==m['sha256'] and stat.S_IMODE((ROOT/path).stat().st_mode)==m['permissions'],path
receipt=(E/'source-attempt3-basic-check.txt').read_text()
assert receipt.startswith('COMMAND: PYTHONDONTWRITEBYTECODE=1 python3 .agent/evidence/114/source-attempt3-basic-check.py\nEXERCISED_HEAD: '+BASE+'\n')
assert re.findall(r'^EXIT: (-?\d+)$',receipt,re.M)==['0'] and receipt.rstrip().endswith('EXIT: 0')
assert H(ROOT/'.agent/validator/114-test-bundle-review.json')==handoff['approved_bundle_sha256']=='db907eef5128ab160a3e2ab5c1296c745225d79f7ffd298597f5d80c92f29a46'
print('MODEB Source3 actual one basic checkpoint atB EXIT0; frozen proofs/source SHA-fullmodes; genuine reviewedbundle pin: PASS',flush=True)
C.dossier(C.raw(ROOT,C.SOURCE[0]).decode());C.planning(ROOT);C.history(ROOT)
C.scope_paths(set(git('diff','--name-only',C.ORIGIN,CANDIDATE,'--').decode().splitlines())|set(git('ls-files','--others','--exclude-standard').decode().splitlines()))
r=subprocess.run(['git','diff','--check',BASE,CANDIDATE],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
state=C.obj(ROOT,C.CANON[2]);assert state['scope_budget']['total_lines_changed']==6779 and state['scope_budget']['original_estimate_lines']==7200 and state['scope_budget']['ceiling_130pct']==9360
assert state['circuit_breaker']['114-generator-development']['attempts']==3
assert not (ROOT/'.agent/qa/114.json').exists() and not (E/'source-review.json').exists() and not (E/'evidence-gate.txt').exists()
print('MODEB bounded dossier/doc/JSON masks, exact oldhistory4800/4799nonDEBT/install239/485+203 archives, authorizedOpen051.67/fullmodes/liveRootcounters/budget and untracked-aware scope/whitespace: PASS',flush=True)
print('NUMSTAT ONLY product diff:\n'+git('diff','--numstat',BASE,CANDIDATE,'--').decode(),flush=True)
print('MODEB CHECKPOINT PASS. No readiness8/formal12QA/capture/oldchecker or future approval stand-in; actual budget classifier remains required in freshQA.')
