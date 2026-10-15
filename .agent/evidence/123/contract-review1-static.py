"""Independent read-only contract inspection; no product/API/acceptance imports."""
import ast
import hashlib
import json
from pathlib import Path
import jsonschema

root = Path.cwd()
path = Path('.agent/contracts/123.json')
raw = path.read_bytes()
contract = json.loads(raw)
assert hashlib.sha256(raw).hexdigest() == '00e2b4ec4e6d5e7de35dd977545b57fc477f827ee93c378ce0d4625d1ee0db3f'
for schema_path in ('schema/contract.schema.json', '.nizam/schema/contract.schema.json'):
    jsonschema.Draft202012Validator(json.loads(Path(schema_path).read_text())).validate(contract)
print('Contract immutable digest and both contract schemas confirmed; schema validity is not semantic approval.')
feature, = [row for row in json.loads(Path('.agent/feature_list_018.json').read_text())['features'] if row['id'] == '123']
assert [row['command'] for row in contract['verification'][:5]] == feature['acceptance_tests']
print('All five feature acceptance commands are present verbatim; default48/fixture integration and preservation remain additional obligations.')
source = Path('tools/convergent_review.py').read_text()
tree = ast.parse(source)
replay, = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'verify_replay_directory']
segment = ast.get_source_segment(source, replay)
assert 'converge_documents' in segment and 'validate_trial' in segment
assert 'sandbox' not in segment and 'subprocess' not in segment
print('R1 static anchor: tools/convergent_review.py:1596-1657 verifies retained bytes/relations/recomputation; it does not attest trial execution or sandbox provenance.')
print('R1 contract anchor: api.a11 requires independently supplied real observations/replay; api.local_hosted retains generic isolation capability output, with no per-trial adapter/runner/input/output/exit provenance requirement or corresponding negative acceptance.')
standard = Path('.nizam/standard/convergent_code_review.md').read_text()
assert 'Each trial MUST run through a trusted sandbox adapter' in standard
print('R1 authority: installed standard/convergent_code_review.md section5 requires each trial to run through an enforced adapter; replay integrity alone does not establish that fact.')
sequence = contract['gate_sequence']
mode_index, = [i for i, text in enumerate(sequence) if text.startswith('Independent Mode B')]
hosted_index, = [i for i, text in enumerate(sequence) if text.startswith('Existing capable')]
assert mode_index < hosted_index
assert 'mandatory before capture' in contract['api']['local_hosted']
print('Nonblocking sequencing observation: contract retains ModeB before freshQA and actual hosted proof plus independent review before capture; provisional Root DAG is subject to approved contract and will be reconciled by Root.')
print('No acceptance, API, bank, compliance, CI or behavior command was executed.')
