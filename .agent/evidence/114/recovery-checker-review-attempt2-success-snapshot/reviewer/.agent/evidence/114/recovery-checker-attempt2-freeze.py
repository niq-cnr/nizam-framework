"""Seal only actual existing inputs after the single passing checkpoint."""
from pathlib import Path
import hashlib
import json
import stat

E=Path('.agent/evidence/114'); H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert json.loads((E/'recovery-checker-attempt2-development-result.json').read_text())['passed'] is True
seed=E/'recovery-checker-attempt2-seed-inputs/fixed-inputs.json'
assert H(seed)=='85197e8832f66e90eb1ce58144a47ebf4c25f6c9f0a89121f86b7f550d904a9a'
old=json.loads(seed.read_text())
changed={str(E/'check_114.py'),str(E/'private/controls.py'),str(E/'private/negative-plan.json')}
for p,m in old['files'].items():
 if p not in changed:
  assert H(p)==m['sha256'] and stat.S_IMODE(Path(p).stat().st_mode)==m['permissions'],('Old fixed input changed',p)
paths=set(old['files'])
prior=E/'private/recovery1-history.json'
assert H(prior)=='48042108c329d977f27cfe6608cc8973150b0d73bbb04282a67956e38903df78'
for m in json.loads(prior.read_text())['files'].values():
 assert H(m['path'])==m['sha256'] and stat.S_IMODE(Path(m['path']).stat().st_mode)==m['permissions'];paths.add(m['path'])
paths.add(str(prior))
for p in ('.agent/validator/114-mode-a.json','.agent/qa/114-contract-review.json'):
 paths.update(json.loads(Path(p).read_text())['evidence'])
manifest=json.loads((E/'recovery-halt-inventory.json').read_text())
assert H(E/'recovery-halt-inventory.json')=='cdb359913b7663be29ec3a1317ecf3b1ee55a2a31a0620edcfac1da5b746a41b'
for m in manifest['files'].values():
 p=m['path'];assert H(p)==m['sha256'] and stat.S_IMODE(Path(p).stat().st_mode)==m['permissions'];paths.add(p)
paths.update(str(p) for p in E.glob('recovery-checker-attempt2-*') if p.is_file())
paths.update(str(p) for p in (E/'recovery-checker-attempt2-seed-inputs').iterdir())
paths.update([str(E/'private/original-debt.md'),str(E/'private/recovery-base/.agent/run_state.json'),str(E/'recovery-approved-contract.json'),str(E/'recovery-contract-approval.json'),str(E/'recovery-authorization.json'),str(E/'recovery-halt-inventory.json'),str(E/'recovery-halt-debt.md'),str(E/'recovery-authorized-debt.md')])
files={}
for p in sorted(paths):
 f=Path(p);assert f.is_file() and not f.is_symlink()
 permissions=stat.S_IMODE(f.stat().st_mode)
 files[p]={'sha256':H(p),'mode':'100755' if permissions&0o111 else '100644','permissions':permissions}
fixed={k:v for k,v in old.items() if k!='files'}
fixed.update(approved_base='480c102a5f3119fd8b645d3cf2f3e2ad793e2b9a',contract_sha256='fd0d1be4ce0f25bcd632c49b209557bb910053866f8df8a28e062256f98fc02e',files=files)
assert H(E/'fixed-inputs.json')==H(seed), 'Unexpected old active map before reseal'
assert H(E/'fixed-inputs-seal.json')==H(E/'recovery-checker-attempt2-seed-inputs/fixed-inputs-seal.json')
(E/'fixed-inputs.json').write_text(json.dumps(fixed,indent=2)+'\n')
digest=H(E/'fixed-inputs.json')
(E/'fixed-inputs-seal.json').write_text(json.dumps({'manifest_sha256':digest},indent=2)+'\n')
print('ACTUAL_FIXED_FILES:',len(files));print('FIXED_INPUTS_SHA256:',digest)
print('Future bundleReview/ModeB/source/QA/capture/handoff excluded; old maps/full modes archived, original4800 unchanged.')
