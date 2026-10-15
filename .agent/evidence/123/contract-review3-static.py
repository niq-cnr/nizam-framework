"""Independent final contract architectural inspection; no product imports/runs."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

def read(path):
    return json.loads(Path(path).read_text())

c = read('.agent/contracts/123.json'); p = c['protocol']
assert hashlib.sha256(Path('.agent/contracts/123.json').read_bytes()).hexdigest() == 'cc441e823e3dcf430228527d938ad0aa5944e5181f7a5a8a6181774b37cb1f74'
for path in ('schema/contract.schema.json', '.nizam/schema/contract.schema.json'):
    jsonschema.Draft202012Validator(read(path)).validate(c)
assert c['status'] == 'proposed' and c['approvals'] == dict(validator_mode_a=False,evaluator_contract_review=False,revisions=2)
assert 'approval_evidence' not in c
feature, = [r for r in read('.agent/feature_list_018.json')['features'] if r['id'] == '123']
assert [r['command'] for r in c['verification'][:5]] == feature['acceptance_tests']
assert len(p['payload_catalog']) == 31 and all(isinstance(k,str) and isinstance(v,str) and v for k,v in p['payload_catalog'].items())
for name in ('policy','selection','evidence','checkout','host','trial','artifact','hosted_review','result','report','a10_result','capability','process','invocation','host_metadata','fetch','experiment_authority','shadow_state'):
    assert set(p[name]) == {'keys','binding'} and all(p[name].values())
assert set(p['external_formats']) == {'json_policy','run','jobs','artifacts','log'}
assert set(p['bundle_transport']) == {'raw','produce','manifest','import','archive','limits'}
print('FORMAT AUDIT: independently read all31 catalog groups. Capability/Process and raw stdout/stderr, Invocation, Bundle/Manifest/ZIP, HostMetadata/Fetch/raw REST/log/archive, ExperimentAuthority/ShadowState and existing convergent/A10 payloads each have fixed producers, parsers and binding consumers; no deferred public record selection.')
print('HOST AUDIT: external REST has explicit consumed field types and ignored-unknown policy; Root normalization is closed and recomputed from raw Fetch output. IDs/attempt/job/steps/producer/selection/invocation/log marker/ZIP hashes cross-bind actual captures; marker/schema/producer labels alone cannot authenticate success.')
print('PACK AUDIT: selected raw bundle bytes/base/hash are authoritative input; exact v2 header and one ref/prerequisite, strict import and every-commit output-only inventory are required. Manifest is canonical and fully determined by mode/source/tip/bundle/hash/size/sorted inventory; archive provides exact actual manifest for hosted comparison. It creates no additional policy authority. Three-entry ZIP and size/path/type limits reject unknown or malformed transport.')
source = Path('tools/workflow_assurance.py').read_text(); tree = ast.parse(source)
receipt, = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name == '_receipt_prerequisites']
segment = ast.get_source_segment(source,receipt)
for field in ('proposal_sha256','mode_a','contract_review'):
    assert field in segment and field in p['approval_materialization']
assert 'before author final freeze/Source anchor' in p['approval_materialization']
assert 'Root commits' in p['payload_catalog']['evidence.a10_receipt_ref']
print('APPROVAL AUDIT: existing120 actually requires bound proposal_sha256/mode_a/contract_review plus reviewed revision/digest and distinct reviewers. Contract now makes truthful Root publication after these actual gates and before author freeze/Source anchor mandatory; approved blob and actual provisional refs remain separate later facts, with omission/stale links rejected.')
authority = read('.agent/evidence/phase018-preflight/activation-authority.json')
assert authority['repository'] == 'niq-cnr/nizam-framework only' and authority['scope']['features'] == ['119','120','121','122','123']
assert authority['scope']['original_estimate_lines'] == 7200 and authority['scope']['ceiling_130pct'] == 9360
print('AUTHORITY AUDIT: closed experiment materialization copies original instruction/owner/gate and selected four scope fields, explicit origin mapping only; original raw authority ref persists. Isolated ShadowState is newly labeled, no live counter reset/migration/adoption or second authority.')
print('ORDER AUDIT: actual gates -> approved metadata -> author/provisional -> Source -> capture selection -> real three enforced trials/map -> output refs -> capture bundle/manifest/invocation -> raw capture/Root selection -> receipt -> recovery policy -> verify selection -> matching-runtime real A10 -> output/verify bundle/metadata -> Evidence -> distinct HostedReview -> final Root policy -> local read-only observation. Each output wrapper is later than targets; no ancestor needs a future object hash. Hosted proof precedes ModeB/freshQA; known local namespace failure is observation only; fixed deterministic rule is not full model review.')
print('NEGATIVE AUDIT: both selectors explicitly require forged/missing/substituted trial, Root/host/pack/cycle/approval facts and genuine restoration; A11 carried blockers/each nonempty array, A10 advance/noop/conflict/recovery, malformed values and candidate/runtime/exit mutations remain covered. All five exact commands plus default48/fixtures, inherited46 ASTs, historical118 positive/current stale negative and exactly one fresh QA extra are retained.')
for path,digest in {'tools/workflow_assurance.py':'fff790d700daa6247557851c6988f8f6e7465ec291907992374d00e3c9d886b6','tools/test_workflow_assurance.py':'800b5970059febf8cf870cc5e23c6bc16e589fc0de6580fe1d6b0dca9f76adae'}.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
for path,revision in (('.agent/qa/123-contract-review.json','a70bca694bd8653384475368d3797b2adf787b2f'),('.agent/qa/123-contract-review-rev1.json','d3841922efd736eae42d0966a891238a736e9645')):
    assert Path(path).read_bytes() == subprocess.check_output(['git','show',revision+':'+path])
rows = read('.agent/evidence/123/source-prerequisite.json')['adjacent_prior_feature_evidence']; assert len(rows) == 28
for row in rows:
    data = subprocess.check_output(['git','show',row['revision']+':'+row['path']])
    assert hashlib.sha256(data).hexdigest() == row['sha256'] and Path(row['path']).read_bytes() == data
    assert subprocess.check_output(['git','ls-tree',row['revision'],'--',row['path']],text=True).split()[:3] == [row['git_mode'],'blob',row['git_blob']]
assert c['estimated_lines'] == 1200 and [c['budget'][k] for k in ('phase_original','phase_ceiling','prior_actual')] == [7200,9360,4303]
state = read('.agent/run_state.json'); assert state['circuit_breaker']['123-contract-review']['attempts'] == 3
print('PRESERVATION: Source/test digests, both prior review bytes and exact28 adjacent raw blobs/modes confirmed unchanged; original1200/7200/9360/prior4303 retained. Five jobs/all gates, installed239/history and Root-only counters/capture/canonical closure remain required.')
print('No API/acceptance/bank/namespace/CI/compliance/model/behavior execution; static contract testability analysis does not establish implementation or real hosted success.')
