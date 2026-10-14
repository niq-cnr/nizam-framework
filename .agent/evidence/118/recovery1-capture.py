"""Root capture of actual independent receipts; no test outcome generation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
E = '.agent/evidence/118/'
spec = importlib.util.spec_from_file_location('capture118guard', ROOT / E / 'scope-guard.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
c = g.approved()
assert c['status'] == 'approved'
g.successors(c, True)
g.seal_check(True)
closeout_review = g.read(E + 'recovery1-closeout-review.json')
g.gate(closeout_review)
assert closeout_review['actor'] == '/root/wa_validator118'
assert closeout_review['adapter_sha256'] == g.sha(g.safe(E+'recovery1-closeout-guard.py').read_bytes())
assert closeout_review['original_guard_sha256'] == g.sha(g.safe(E+'scope-guard.py').read_bytes())
assert closeout_review['authorization_sha256'] == g.sha(g.safe(E+'recovery1-closeout-override.json').read_bytes())
candidate = g.read(E + 'source-candidate.json')
prereq = g.read(E + 'prerequisite20.json')
mode = g.read(g.MODE_B)
qa = g.read(g.QA)
assert set(candidate) == {'revision', 'tree', 'source_sha256', 'runtime_sha256', 'historical_sha256'}
assert g.git('rev-parse', candidate['revision'] + '^{tree}') == candidate['tree']
assert prereq['actor'] == prereq['session_id'] == '/root/wa_prerequisite118_recovery1'
assert mode['actor'] == '/root/wa_validator118'
assert qa['actor'] == '/root/wa_acceptance118'
for family in ('source_sha256', 'runtime_sha256', 'historical_sha256'):
    for path, digest in candidate[family].items():
        assert g.sha(g.safe(path).read_bytes()) == digest == g.sha(g.at(path, candidate['revision'])), path
        g.exact(path, g.entries(candidate['revision'])[path])
assert g.load(ROOT / 'tools/workflow_assurance.py').verify_foundation_ready(ROOT, prereq) is True
Draft202012Validator(g.read('.nizam/schema/qa_verdict.schema.json')).validate(qa)
assert qa['adversarial_check']['result'] == 'pass'
assert qa['adversarial_check']['evidence'] == qa['adversarial']['evidence']
proofs = [row['evidence'] for row in prereq['checks']] + [row['evidence'] for row in qa['checks']] + [qa['adversarial']['evidence']]
assert len(proofs) == len(set(proofs)) == 24
receipt = dict(candidate, feature='118', owner='/root', passed=True,
    prerequisite_sha256=g.sha(g.safe(E + 'prerequisite20.json').read_bytes()),
    qa_ref=g.QA, mode_b_ref=g.MODE_B,
    qa_sha256=g.sha(g.safe(g.QA).read_bytes()), mode_b_sha256=g.sha(g.safe(g.MODE_B).read_bytes()),
    checks_captured=3, adversarial_captured=True,
    evidence_sha256={p: g.sha(g.safe(p).read_bytes()) for p in proofs},
    closeout_override_ref=E+'recovery1-closeout-override.json',
    closeout_review_ref=E+'recovery1-closeout-review.json',
    closeout_review_sha256=g.sha(g.safe(E+'recovery1-closeout-review.json').read_bytes()),
    closeout_checker_sha256=g.sha(g.safe(E+'recovery1-closeout-guard.py').read_bytes()))
g._closure(c, (candidate, prereq, mode, qa, receipt), lambda p: g.safe(p).read_bytes())
print('PASS independent actors, approved B2, actual Source/tree/core/runtime/history bytes and modes')
print('PASS actual ordered20 prerequisite, exact3 QA commands and independent ownspot; all24 proof hashes')
target = ROOT / g.CAPTURE
assert not target.exists()
target.write_text(json.dumps(receipt, indent=2) + '\n')
g.closure(c)
print('PASS Root capture committed only after actual receipt validation; lifecycle still in_progress')
