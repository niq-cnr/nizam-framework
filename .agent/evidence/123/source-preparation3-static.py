"""Read-only preparation declarations and syntax checks, no API imports."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
p=Path('.agent/contracts/123.json');c=json.loads(p.read_text())
assert hashlib.sha256(p.read_bytes()).hexdigest()=='64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5'
assert c['status']=='approved' and c['approvals']['validator_mode_a'] is True and c['approvals']['evaluator_contract_review'] is True
assert c['approval_evidence']['proposal_sha256']=='cc441e823e3dcf430228527d938ad0aa5944e5181f7a5a8a6181774b37cb1f74'
assert len(c['protocol']['payload_catalog'])==31
for name in [c['approval_evidence']['mode_a'],c['approval_evidence']['contract_review']]:
 v=json.loads(Path(name).read_text());assert v['final_verdict']['approved'] is True
 assert all(v[k]==[] for k in ['issues','missing_acceptance_coverage','unsupported_claims'])
 print('STATIC actual strict gate and current metadata: '+name)
for name in ['tools/workflow_assurance.py','tools/test_workflow_assurance.py','tools/evaluate_convergent_review_prompt.py','tools/isolated_trial_adapter.py']:
 raw=Path(name).read_bytes();ast.parse(raw,filename=name)
 print('STATIC unchanged input '+name+' sha256='+hashlib.sha256(raw).hexdigest())
assert subprocess.check_output(['git','diff','HEAD','--name-only'])==b''
print('STATIC tracked contract/Source/tests/workflow/state/installed files unchanged; only own preparation evidence untracked')
print('No API import or acceptance/bank/namespace/CI/compliance/model/behavior/transport run')
