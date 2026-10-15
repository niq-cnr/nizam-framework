"""Static preparation proof; no product/API imports or behavior runs."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

cpath=Path('.agent/contracts/123.json');c=json.loads(cpath.read_text())
assert hashlib.sha256(cpath.read_bytes()).hexdigest()=='0eb09db2d8758a7762e1b9ac9fb1a7de9b2db9882be343235aea88c2a6c29838'
assert c['status']=='approved' and c['approvals']['validator_mode_a'] is True and c['approvals']['evaluator_contract_review'] is True
for path in ['.agent/validator/123-mode-a-rev1.json','.agent/qa/123-contract-review-rev1.json']:
 v=json.loads(Path(path).read_text());assert v['final_verdict']['approved'] is True
 assert all(v[k]==[] for k in ['issues','missing_acceptance_coverage','unsupported_claims'])
 print('STATIC passed pre-code gate: '+path)
for path in ['tools/workflow_assurance.py','tools/test_workflow_assurance.py','tools/evaluate_convergent_review_prompt.py','tools/isolated_trial_adapter.py']:
 raw=Path(path).read_bytes();tree=ast.parse(raw,filename=path)
 print('STATIC syntax/input '+path+' sha256='+hashlib.sha256(raw).hexdigest()+' definitions='+str(sum(isinstance(n,(ast.FunctionDef,ast.ClassDef)) for n in ast.walk(tree))))
assert 'approval_evidence' not in c
print('STATIC Root input requirement: existing A10 engine requires currently absent contract.approval_evidence; no edit made')
for path in ['tools/linux_trial_sandbox.sh','.github/workflows/compliance.yml','tools/fixtures_self_test.sh','templates/convergent-review-prompt.md']:
 assert Path(path).is_file()
assert subprocess.check_output(['git','diff','HEAD','--name-only'])==b''
print('STATIC tracked Source/tests/contracts/workflow/state/installed paths unchanged')
print('No API, acceptance, bank, CI, compliance, namespace, model or behavioral command executed')
