"""Metadata-only finalization of the personally performed pre-code review."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import stat
import subprocess
import jsonschema

E = Path('.agent/evidence/114')
H = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
proposal = 'e92511922f2689e2a400990d6765a5a570bc26374c94d5b1fc934f889c19e3c9'
mode_a_sha = 'd3e649ad47ff4cf90ce2d64ff66248f976bd0aa152d600d124c52c259a55ecde'
base = 'ea41afd196dddaef02f6be86217c84deaf47d238'
actor = '/root/adapter_acceptance_recovery_113'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == base
w = json.loads((E/'recovery-contract-review-attempt1-workspace.json').read_text())
assert w['actor'] == actor and Path(w['root']).resolve() == Path.cwd()
assert w['proposal_sha256'] == proposal
assert H('.agent/contracts/114.json') == proposal
c = json.loads(Path('.agent/contracts/114.json').read_text())
assert c['status'] == 'proposed' and c['approvals']['validator_mode_a'] is False
assert c['approvals']['evaluator_contract_review'] is False
assert H('.agent/validator/114-mode-a.json') == mode_a_sha
m = json.loads(Path('.agent/validator/114-mode-a.json').read_text())
assert m['proposal_sha256'] == proposal and m['epoch'] == '114-recovery-1'
assert m['actor'] != actor and m['final_verdict']['approved'] is True
assert all(m[k] == [] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
assert all(Path(p).is_file() for p in m['evidence'])
target = Path('.agent/qa/114-contract-review.json')
old = json.loads((E/'recovery-original/inventory.json').read_text())[str(target)]
assert H(target) == old['sha256'] and H(old['archive']) == old['sha256']
assert stat.S_IMODE(Path(old['archive']).stat().st_mode) == old['permissions']
assert stat.S_IMODE(target.stat().st_mode) == old['permissions']
assert (E/'recovery-contract-review-attempt1-raw.txt').read_text().rstrip().endswith('EXIT: 0')
v = {
 'review':'contract-testability', 'feature':'114', 'revision_reviewed':1,
 'stage':'independent-pre-code-contract-review', 'epoch':'114-recovery-1',
 'actor':actor, 'reviewed_at':datetime.now(timezone.utc).isoformat(),
 'proposal_sha256':proposal, 'approved_base':base, 'mode_a_sha256':mode_a_sha,
 'evidence':[
  '.agent/evidence/114/recovery-contract-review-attempt1-raw.txt',
  '.agent/evidence/114/recovery-contract-review-attempt1-reasoning.txt',
  '.agent/evidence/114/recovery-contract-review-attempt1-finalization-raw.txt'],
 'issues':[], 'missing_acceptance_coverage':[], 'unsupported_claims':[],
 'final_verdict':{'approved':True, 'feature':'114',
  'summary':'Independent renewed pre-code review approves unchanged six-Source/12-command scope and 1150 budget, precise archived-history/debt051/epoch-counter masks, contextual release guards and separate actual bundle/ModeB/freshQA/capture gates. No feature acceptance or implementation executed.'}
}
schema = json.loads(Path('.nizam/schema/contract_review.schema.json').read_text())
jsonschema.Draft202012Validator(schema).validate(v)
target.write_text(json.dumps(v, indent=2)+'\n')
actual = json.loads(target.read_text())
jsonschema.Draft202012Validator(schema).validate(actual)
assert actual['final_verdict']['approved'] is True
assert all(actual[k] == [] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
assert H(old['archive']) == old['sha256']
print('Actual renewed ModeA/proposal/owned workspace bindings and original review archive verified.')
print('Typed independent pre-code review written and installed contract_review schema valid.')
print('REVIEW_SHA256:',H(target))
print('PRE-CODE METADATA ONLY: no acceptance commands, implementation or lifecycle state edits.')
