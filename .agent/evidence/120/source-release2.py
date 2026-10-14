"""Root-only release capture; independently reviewed Source gate, no Source edits."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import jsonschema

review = '2fd107511998916a270e3fe2febda32040fe6118'
contract_sha = '3238ad1b0732007801769e086a2cd96a6832bb686847ecd4c23e33c532e93bb9'
test_sha = '4914b7c60215b001ab822f47997fbebf15805660ca0c605cf0713de43e123006'
def git(*args):
    return subprocess.check_output(['git', *args])
def data(path):
    return git('show', review + ':' + path)
verdict = json.loads(data('.agent/qa/120-provisional-bundle-review-rev1.json'))
assert verdict['final_verdict']['approved'] is True
assert all(verdict[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'))
assert verdict['test_sha256'] == test_sha and verdict['approved_contract_sha256'] == contract_sha
seal = json.loads(data('.agent/evidence/120/provisional-review2-seal.json'))
assert len(seal['protected_inputs']) == 9 and len(seal['files']) == 8
for path, pin in seal['protected_inputs'].items():
    assert type(pin) is dict and set(pin) == {'sha256', 'git_blob'}
    assert hashlib.sha256(data(path)).hexdigest() == pin['sha256'], path
    assert git('rev-parse', review + ':' + path).decode().strip() == pin['git_blob'], path
for path, digest in seal['files'].items():
    assert type(digest) is str and hashlib.sha256(data(path)).hexdigest() == digest, path
paths = git('diff', '--name-only', 'ea6a84e', review).decode().splitlines()
assert all(p == '.agent/qa/120-provisional-bundle-review-rev1.json' or
           p.startswith('.agent/evidence/120/provisional-review2-') for p in paths)
subprocess.run(['git', 'merge', '--no-ff', '--no-stat', '--quiet', review, '-m',
                'chore: integrate120 provisional approval after corrected seal capture'], check=True)
assert hashlib.sha256(Path('tools/test_workflow_assurance.py').read_bytes()).hexdigest() == test_sha
assert hashlib.sha256(Path('.agent/contracts/120.json').read_bytes()).hexdigest() == contract_sha
assert json.load(open('.agent/evidence/120/source-prerequisite.json'))['passed'] is True
p = Path('.agent/run_state.json'); state = json.loads(p.read_text())
assert state['current_feature'] == state['active_contract_id'] == '120'
assert state['circuit_breaker']['120-source-release-capture'] == {'attempts': 2, 'limit': 3}
assert '120-implementation' not in state['circuit_breaker']
now = datetime.now(timezone.utc).isoformat()
state['circuit_breaker']['120-implementation'] = {'attempts': 1, 'limit': 3}
state['updated_at'] = now
state['history'].append({'at': now, 'event': '120-initial-source-release',
 'detail': 'Strict dualprecode and provisional-review2 approval; corrected release capture2 verified9 protectedGit/SHA and8 reviewSHA pins. Source1 released; initialcandidate commit precedes allbehavioralcommands, no completion claim.'})
jsonschema.validate(state, json.load(open('.nizam/schema/run_state.schema.json')))
dispatch = {'role': 'Root', 'at': now, 'attempt': 1, 'generator': '/root/generator119',
 'root': '/home/cnross/.tmp/nizam-feature120-source1',
 'approved_contract_sha256': contract_sha, 'test_sha256': test_sha,
 'provisional_approval': '.agent/qa/120-provisional-bundle-review-rev1.json',
 'provisional_review_commit': review, 'author_commit': '945d37a69af3dc371bd277f50697846e8d507eae',
 'readiness': '.agent/evidence/120/source-readiness1.json',
 'main_ci_prerequisite': '.agent/evidence/120/source-prerequisite.json',
 'write_scope': ['tools/workflow_assurance.py', 'tools/README.md', 'CHANGELOG.md', '.agent/evidence/120/source1-*'],
 'initial_commit_rule': 'Commit initial Source/docs before any behavioral development command; record actualcandidateSHA. MissingAPIs permit initialaddition without absentAPIsemanticred. Preserve allold115-119AST/CLI/test/schema/installed/proofs.',
 'on_failure': 'Preserve actual command/revision/stdout/stderr/exit and intendedassertion diagnosis; no behavioralrepair before genuine intendedred and Rootisolatedretry allocation. No test/contract weakening.',
 'next': 'Independent author11positive/privateintendedred/restored controls, distinct finalbundle, ModeB, freshQA, actual hosted37, Rootcapture andcanonicalfirstclosure.'}
result = {'role': 'Root', 'at': now, 'attempt': 2, 'actual_exit': 0, 'passed': True,
 'protected_git_sha_pins': 9, 'review_sha_pins': 8, 'review_commit': review,
 'approved_contract_sha256': contract_sha, 'test_sha256': test_sha,
 'initial_source_released': True, 'source_or_test_edits': False,
 'prior_failure': '.agent/evidence/120/source-release1-failure.json'}
p.write_text(json.dumps(state, indent=2) + '\n')
Path('.agent/evidence/120/source1-dispatch.json').write_text(json.dumps(dispatch, indent=2) + '\n')
Path('.agent/evidence/120/source-release2-result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
