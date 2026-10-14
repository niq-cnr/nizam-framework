import hashlib,json,pathlib,subprocess,jsonschema
P=pathlib.Path
contract=P('.agent/contracts/128.json'); c=json.loads(contract.read_text())
assert hashlib.sha256(contract.read_bytes()).hexdigest()=='bf5b536112cb58b8f605b46db931f0edc3ae140af761d0742007ca5ea98c8443'
jsonschema.validate(c,json.loads(P('.nizam/schema/contract.schema.json').read_text()))
assert c['status']=='proposed' and len(c['leaf_argv'])==14 and len({tuple(x) for x in c['leaf_argv']})==14
f=next(x for x in json.loads(P('.agent/feature_list_016.json').read_text())['features'] if x['id']=='128')
assert [x['command'] for x in c['verification']]==f['acceptance_tests']
assert c['estimated_lines']==f['estimated_lines']==800
assert sum(c['budget'][k] for k in ('product','independent_tests','process'))==800
assert (c['budget']['phase_original'],c['budget']['phase_ceiling'],c['budget']['already_counted'],c['budget']['remaining_ceiling'])==(5650,7345,4765,2580)
s=json.loads(P('.agent/run_state.json').read_text()); assert s['circuit_breaker']['128-mode-a']=={'attempts':1,'limit':3}
selection=json.loads(P('.agent/evidence/128/selection.json').read_text())
assert selection['dependency_gate']['127']=='complete'
r=json.loads(P('.agent/evidence/127/pr98-main-ci.json').read_text())
assert r['actual_api_exit']==0 and r['run']['databaseId']==38565810273 and r['run']['conclusion']=='success'
assert r['run']['headSha']==selection['base_revision']
for x in ('tools/runtime_session.py','tools/test_runtime_session.py','tools/fixtures_self_test.sh'):
 assert subprocess.check_output(['git','show',selection['base_revision']+':'+x])==P(x).read_bytes()
 print(x,hashlib.sha256(P(x).read_bytes()).hexdigest())
print('PASS contract schema/hash; exact AT1-AT3; 14 unique leaves; budget; recorded attempt; dependency and actual CI receipt; no implementation delta')
