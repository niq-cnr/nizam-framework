"""One independent spot-check: valid mapping under a side-effect-denying audit hook."""
import copy
import json
import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root/'tools'))
import workflow_assurance as api
import convergent_review as review

fixture = root/'tools/fixtures/convergent_review/05-prior-persisting'
read = lambda name: json.loads((fixture/name).read_bytes())
packet = read('packet.json'); trials = [read('trial-%d.json' % i) for i in (1, 2, 3)]
prior = read('prior-ledger.json')
digest = lambda value: review.sha256(review.canonical_json_bytes(value))
ledger = review.converge_documents(packet, digest(packet), trials, {i: digest(trials[i-1]) for i in (1, 2, 3)}, prior, digest(prior), [])
assert all(t['observations'] == [] for t in trials) and ledger['findings'][0]['lifecycle'] == 'persisting'
report = {'final_verdict': {'approved': True}, 'issues': [], 'missing_acceptance_coverage': [], 'unsupported_claims': []}
before = copy.deepcopy((ledger, report)); seen = []
class ForbiddenSideEffect(RuntimeError): pass
def audit(event, args):
    write = event == 'open' and ((isinstance(args[1], str) and any(c in args[1] for c in 'wax+')) or (isinstance(args[2], int) and bool(args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))))
    if write or event in ('subprocess.Popen', 'os.system', 'os.remove', 'os.rename', 'os.mkdir', 'socket.connect', 'socket.bind'):
        seen.append(event); raise ForbiddenSideEffect(event)
sys.addaudithook(audit)
try:
    open(root/'.agent/evidence/119/qa1/forbidden-write-sentinel', 'w')
except ForbiddenSideEffect as exc:
    assert str(exc) == 'open'
else:
    raise AssertionError('audit guard failed its real write-attempt control')
assert seen == ['open']; seen.clear()
out = api.convergent_agf_verdict(ledger, report, expected_repository=ledger['repository'], expected_head_sha=ledger['head_sha'])
assert out['final_verdict']['approved'] is False and out['issues'] == ledger['findings']
assert out['required_fixes'] and (ledger, report) == before and not seen
assert not (root/'.agent/evidence/119/qa1/forbidden-write-sentinel').exists()
print('PASS one independent purity check: genuine write attempt denied by audit guard; actual carried-blocker mapping succeeds with zero write/process/network events and inputs intact')
