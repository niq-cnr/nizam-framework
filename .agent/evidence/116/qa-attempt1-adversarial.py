"""Fresh QA transport and proof-binding boundary; only temporary fixtures mutate."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

api = load('qa_source116', ROOT / 'tools/workflow_assurance.py')
runner = load('qa_frozen_fixture', ROOT / 'tools/test_workflow_assurance.py')
bundle = api.parse_json((ROOT / '.agent/evidence/116/acceptance-bundle.json').read_bytes())
review = api.parse_json((ROOT / '.agent/validator/116-test-bundle-review.json').read_bytes())
assert api.verify_acceptance_bundle(ROOT, bundle, review) is True

with tempfile.TemporaryDirectory(prefix='nizam116-fresh-qa-transport-') as scratch:
    temp = Path(scratch)
    bp, rp = temp / 'bundle.json', temp / 'review.json'
    def cli(root, bbytes, rbytes, label, accepted):
        bp.write_bytes(bbytes); rp.write_bytes(rbytes)
        args = [sys.executable, str(ROOT / 'tools/workflow_assurance.py'), 'bundle',
                '--repo', str(root), '--bundle', str(bp), '--review', str(rp)]
        result = subprocess.run(args, capture_output=True, text=True)
        print('CLI_CONTROL:', label, 'ARGS:', json.dumps(args), 'ACTUAL_EXIT:', result.returncode)
        print('CLI_STDOUT:', repr(result.stdout), 'CLI_STDERR:', repr(result.stderr))
        if accepted:
            assert result.returncode == 0 and result.stdout == 'PASS bundle\n' and not result.stderr
        else:
            assert result.returncode == 1 and 'PASS' not in result.stdout and result.stderr.startswith('AssuranceError: ')
    bbytes, rbytes = api.canonical(bundle), api.canonical(review)
    cli(ROOT, bbytes, rbytes, 'genuine full project positive', True)
    malformed = []
    altered = copy.deepcopy(review); altered['reviewer_session_id'] = review['actor'] + '/different-session'
    malformed.append(('correct actor but different reviewer session', bbytes, api.canonical(altered)))
    altered = copy.deepcopy(review); altered['final_verdict']['approved'] = 1
    malformed.append(('integer approval cannot impersonate boolean true', bbytes, api.canonical(altered)))
    altered = copy.deepcopy(review); altered['caller_override'] = True
    malformed.append(('unrecognized review authority field', bbytes, api.canonical(altered)))
    malformed.append(('duplicate equal feature keys remain invalid JSON', b'{"feature_id":"116",' + bbytes[1:], rbytes))
    malformed.append(('nonfinite token cannot masquerade as empty blocker list', bbytes,
                      rbytes.replace(b'"issues":[]', b'"issues":NaN')))
    for label, invalid_bundle, invalid_review in malformed:
        cli(ROOT, invalid_bundle, invalid_review, label, False)
        cli(ROOT, bbytes, rbytes, 'restored full project positive after ' + label, True)
    fixture_parent = temp / 'proof-fixture'; fixture_parent.mkdir()
    fixture = runner.BundleFixture(fixture_parent)
    fixture.transition()
    row = fixture.row('reject-missing-red'); proof = row['red']; path = proof['path']
    original = (fixture.root / path).read_bytes()
    mutations = [
        ('duplicate equal EXIT header', original.replace(b'EXIT: 1\n', b'EXIT: 1\nEXIT: 1\n')),
        ('positive digest substituted into red input binding', original.replace(
            row['operation']['case_input']['sha256'].encode(), row['operation']['positive_input']['sha256'].encode())),
        ('contradictory observed result beside intended policy assertion', original.replace(
            b'OBSERVED_RESULT: accept\n', b'OBSERVED_RESULT: accept\nOBSERVED_RESULT: reject\n')),
    ]
    cli(fixture.root, api.canonical(fixture.bundle), api.canonical(fixture.review), 'genuine complete transitioned proof fixture', True)
    for label, invalid_proof in mutations:
        fixture.write(path, invalid_proof); proof['sha256'] = api.sha(invalid_proof); fixture.refresh()
        cli(fixture.root, api.canonical(fixture.bundle), api.canonical(fixture.review), label, False)
        fixture.write(path, original); proof['sha256'] = api.sha(original); fixture.refresh()
        cli(fixture.root, api.canonical(fixture.bundle), api.canonical(fixture.review), 'restored transitioned fixture after ' + label, True)
assert api.verify_acceptance_bundle(ROOT, bundle, review) is True
print('PASS one fresh QA adversarial boundary: 8 negatives, 10 positive/restored CLI controls, unchanged actual project bundle')
