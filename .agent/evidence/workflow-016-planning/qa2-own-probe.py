import copy, hashlib, json, pathlib, subprocess
import jsonschema, yaml
root = pathlib.Path.cwd()
phase_path = root / 'docs/planning/phase_017.yaml'
original = phase_path.read_bytes()
valid = yaml.safe_load(original)
schema = json.loads((root / '.nizam/schema/phase.schema.json').read_text())
v = jsonschema.Draft202012Validator(schema)
assert list(v.iter_errors(valid)) == []
bad = copy.deepcopy(valid)
bad['steps'][0]['stdout'] = 'PASS: all runtime acceptance succeeded'
errors = list(v.iter_errors(bad))
matching = [e for e in errors if e.validator == 'additionalProperties' and list(e.absolute_path) == ['steps', 0] and 'stdout' in e.message]
assert matching, 'Expected installed closed-step schema rejection missing'
print('VALID_BASELINE: accepted')
for e in matching: print('TARGETED_REJECTION:', e.validator, json.dumps(list(e.absolute_path)), e.message)
del bad['steps'][0]['stdout']
assert bad == valid and list(v.iter_errors(bad)) == []
assert phase_path.read_bytes() == original
print('RESTORED_VALID_MODEL: accepted')
print('SOURCE_PHASE_BYTES_UNCHANGED_SHA256:', hashlib.sha256(original).hexdigest())
print('PROBE_RESULT: PASS')
