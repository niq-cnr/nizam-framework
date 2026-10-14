"""Independent feature127 pre-code review controls; not feature127 acceptance."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import jsonschema

ROOT = Path.cwd()
OUT = ROOT / '.agent/evidence/127'
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'LC_ALL': 'C'}

def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def record(name, argv, expected=0):
    started = time.monotonic()
    p = subprocess.run(argv, cwd=ROOT, env=ENV, capture_output=True, timeout=60)
    stem = 'contract-review-' + name
    stdout, stderr = OUT / (stem + '.stdout.txt'), OUT / (stem + '.stderr.txt')
    stdout.write_bytes(p.stdout)
    stderr.write_bytes(p.stderr)
    result = dict(argv=argv, cwd=str(ROOT), environment={'PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C'},
                  source_revision=git('rev-parse','HEAD'), actual_exit=p.returncode,
                  expected_exit=expected, elapsed_seconds=time.monotonic()-started,
                  stdout=str(stdout.relative_to(ROOT)), stderr=str(stderr.relative_to(ROOT)),
                  stdout_sha256=sha(p.stdout), stderr_sha256=sha(p.stderr))
    (OUT / (stem + '.json')).write_text(json.dumps(result, indent=2)+'\n')
    assert p.returncode == expected, result
    print(name + ': actual_exit=' + str(p.returncode), flush=True)
    return result

contract = json.loads((ROOT / '.agent/contracts/127.json').read_text())
dispatch = json.loads((OUT / 'precode-dispatch.json').read_text())
assert sha((ROOT / '.agent/contracts/127.json').read_bytes()) == dispatch['proposal_sha256']
assert git('rev-parse', dispatch['proposal_commit']+':.agent/contracts/127.json') == git('hash-object','.agent/contracts/127.json')
jsonschema.Draft202012Validator(json.loads((ROOT / '.nizam/schema/contract.schema.json').read_text())).validate(contract)
features = json.loads((ROOT / '.agent/feature_list_016.json').read_text())['features']
feature = next(x for x in features if x['id']=='127')
assert [x['command'] for x in contract['verification']] == feature['acceptance_tests']
assert len(contract['verification']) == 5
assert contract['status'] == 'proposed'
assert contract['estimated_lines'] == feature['estimated_lines'] == 1950
assert contract['budget']['already_counted'] == 3003 and contract['budget']['phase_ceiling'] == 7345
inputs = ['AGENTS.md', '.nizam/NIZAM.json', '.nizam/tools/SKILL.md',
          '.nizam/methodology/01_execution.md', '.nizam/methodology/02_adversarial_tdd.md',
          '.nizam/standard/AGF.md', '.nizam/schema/contract_review.schema.json',
          '.agent/contracts/127.json', '.agent/product_spec_016.md', '.agent/feature_list_016.json',
          'methodology/10_live_runtime_sessions.md', 'methodology/11_sbcl_runtime_binding.md',
          'tools/interface.md', 'docs/nips/NIP-0003-live-runtime-sessions.md',
          'schema/runtime_session.schema.json', 'schema/runtime_operation.schema.json',
          'tools/verify_lib.sh', 'tools/runtime_session.py', 'tools/test_runtime_session.py',
          'tools/fixtures/runtime_session/stub_runtime.py', 'tools/fixtures_self_test.sh',
          '.agent/evidence/126/runtime-api.json', '.agent/evidence/126/test-seal-b3.json',
          '.agent/evidence/126/evidence-capture.json', '.agent/evidence/126/pr97-main-ci.json',
          '.agent/evidence/127/precode-dispatch.json']
identity = dict(reviewer='/root/contract_review127', role='independent Evaluator contract review',
                exercised_revision=git('rev-parse','HEAD'), proposal_commit=dispatch['proposal_commit'],
                proposal_sha256=dispatch['proposal_sha256'], platform=platform.platform(),
                python=sys.version, no_feature127_acceptance_run=True,
                files={p:dict(sha256=sha((ROOT/p).read_bytes()), git_blob=git('hash-object',p)) for p in inputs})
for p in ['tools/runtime_session.py','tools/test_runtime_session.py','tools/fixtures/runtime_session/stub_runtime.py','tools/fixtures_self_test.sh']:
    assert git('rev-parse',contract['base_revision']+':'+p) == identity['files'][p]['git_blob']
(OUT/'contract-review-identities.json').write_text(json.dumps(identity,indent=2)+'\n')
results = []
for check in ('lifecycle-no-evaluation','record-schema','fixture-claim-registered'):
    results.append(record(check,['python3','tools/test_runtime_session.py','--check',check]))
for fixture, expected in [('runtime_operation_valid_running_stopped_waiting.json',0),
                          ('runtime_operation_neg_timeout_cancelled.json',1),
                          ('runtime_session_valid_reattach_pending.json',0),
                          ('runtime_session_valid_replayable_handoff.json',0)]:
    results.append(record(fixture.removesuffix('.json'),['bash','tools/validate.sh','--target','tools/fixtures/'+fixture],expected))
(OUT/'contract-review-results.json').write_text(json.dumps(dict(actual_checks=results,
    qualification='Baseline semantic and C12 controls only; future unsupported selectors are not semantic red.'),indent=2)+'\n')
