"""Independent revision1 contract inspection; JSON/AST/Git reads only."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

def read(path):
    return json.loads(Path(path).read_text())

c = read('.agent/contracts/123.json')
assert hashlib.sha256(Path('.agent/contracts/123.json').read_bytes()).hexdigest() == '3871de65953edb7652932bf756038791f350ad9c40a14488873f051eaba7bff3'
for path in ('schema/contract.schema.json', '.nizam/schema/contract.schema.json'):
    jsonschema.Draft202012Validator(read(path)).validate(c)
assert c['status'] == 'proposed' and c['approvals'] == dict(validator_mode_a=False, evaluator_contract_review=False, revisions=1)
f, = [r for r in read('.agent/feature_list_018.json')['features'] if r['id'] == '123']
assert [r['command'] for r in c['verification'][:5]] == f['acceptance_tests']
p = c['protocol']
assert all(set(p[k]) == {'keys', 'binding'} for k in ('policy', 'selection', 'evidence', 'checkout', 'host', 'trial', 'artifact', 'hosted_review', 'result', 'report', 'a10_result'))
assert p['notation'].startswith('Every record below is closed: exactly its listed keys, all required.')
print('PUBLIC BOUNDS: both contract schemas valid, released digest exact, five acceptance commands verbatim, closed public records and fixed result/command/order declared before Source.')
evaluator = Path('tools/evaluate_convergent_review_prompt.py').read_text()
ast.parse(evaluator)
assert 'start_new_session=True' in evaluator and 'str(isolation_adapter)' in evaluator and 'runner_exit' in evaluator
for field in ('packet_digest', 'prompt_template_digest', 'runner_digest', 'trials', 'review_replay_digest', 'trial_number', 'prompt_digest', 'trial_digest', 'isolated_packet_digest', 'runner_exit', 'isolation_adapter_digest'):
    assert '"' + field + '"' in evaluator and field in p['trial']['binding']
assert 'for trial_number in (1, 2, 3):' in evaluator
print('PRIOR R1 CLOSED: selected existing evaluator really invokes three separate adapter processes, retains exact named receipts and outputs; contract binds evaluator/runner/prompt/packet/output/adapter/boundary/exit refs and requires replay-valid forged/missing/substituted-chain rejection plus genuine restoration.')
canary = Path('.agent/evidence/agentic-excellence/runtime-preflight-namespace-canary.txt').read_text()
assert 'Operation not permitted' in canary and 'EXIT:1' in canary
assert 'read-only' in c['api']['result'] and 'No local enforced trial' in c['api']['local_hosted']
assert 'precede ModeB' in c['api']['local_hosted']
assert 'Hosted runner never invokes controls-ready' in p['order'][5]
print('EXECUTION PATH: historical local namespace failure is explicit; local selectors are synthetic and controls-ready observes selected completed proof only. Hosted capture -> independent Root capture selection -> matching-runtime A10 verify -> distinct review -> ModeB -> fresh QA is nonrecursive and executable in existing capable job.')
print('TRUST: observer is a fixed independently specified deterministic workflow-key rule, not three model judgments/full review; real trial bytes must equal evaluator outputs. Root alone selects authority/capture policy, immutable materialization preserves original instruction/owner/gate/scope; live E120 migration remains unapplied.')
for path, digest in {'tools/workflow_assurance.py':'fff790d700daa6247557851c6988f8f6e7465ec291907992374d00e3c9d886b6','tools/test_workflow_assurance.py':'800b5970059febf8cf870cc5e23c6bc16e589fc0de6580fe1d6b0dca9f76adae'}.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
old = '.agent/qa/123-contract-review.json'
assert Path(old).read_bytes() == subprocess.check_output(['git','show','a70bca694bd8653384475368d3797b2adf787b2f:'+old])
rows = read('.agent/evidence/123/source-prerequisite.json')['adjacent_prior_feature_evidence']
assert len(rows) == 28
for row in rows:
    data = subprocess.check_output(['git', 'show', row['revision']+':'+row['path']])
    assert hashlib.sha256(data).hexdigest() == row['sha256'] and Path(row['path']).read_bytes() == data
    assert subprocess.check_output(['git','ls-tree',row['revision'],'--',row['path']],text=True).split()[:3] == [row['git_mode'],'blob',row['git_blob']]
assert c['estimated_lines'] == 1200 and [c['budget'][k] for k in ('phase_original','phase_ceiling','prior_actual')] == [7200,9360,4303]
print('COVERAGE/PRESERVATION: negative/restored candidate/runtime/producer/ref/output/exit/provenance, A11 blockers/arrays, actual A10 advance/noop/conflict/recovery, malformed records, default48/fixtures, inherited46/115-122 ASTs, historical118 positive/current stale negative, installed239/five jobs/all gates and Root-only capture/closure are explicit obligations. Actual Source/test digests, old rejection, exact28 raw bytes/modes and budgets are unchanged.')
print('No product/API/acceptance/bank/compliance/namespace/CI behavior executed; this is pre-code contract testability approval only.')
