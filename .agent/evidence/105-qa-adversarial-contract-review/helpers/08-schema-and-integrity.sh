# The verdict validates against schema/contract_review.schema.json; the contract and every tracked file are unchanged; only allowlisted paths are new.
python3 - <<'PY'
import json, hashlib, subprocess, jsonschema
v = json.load(open('.agent/qa/105-contract-review.json'))
jsonschema.validate(v, json.load(open('schema/contract_review.schema.json')))
print('verdict schema-valid; approved =', v['final_verdict']['approved'], '; issues/missing/unsupported =', len(v['issues']), len(v['missing_acceptance_coverage']), len(v['unsupported_claims']))
print('contract sha256 =', hashlib.sha256(open('.agent/contracts/105.json','rb').read()).hexdigest(), '(expected bf8247c0339075dc9a65d5719102be3a4c5feac8f10a27ed238a36c11b54b14b)')
tracked = subprocess.run(['git','diff','--name-only','HEAD'],capture_output=True,text=True,check=True).stdout.split()
print('tracked files modified vs HEAD:', tracked, '(only the Orchestrator-owned .agent/run_state.json is expected)')
new = subprocess.run(['git','ls-files','--others','--exclude-standard','-z'],capture_output=True,text=True,check=True).stdout.split('\0')
new = sorted(p for p in new if p)
bad = [p for p in new if not (p == '.agent/contracts/105.json' or p.startswith(('.agent/qa/105','.agent/evidence/105-qa-')))]
print('untracked paths:', len(new), 'outside allowlist and the contract itself:', bad)
PY
