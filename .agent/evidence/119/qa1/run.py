"""Fresh119 QA attempt1 command capture; never edits product or lifecycle state."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
E = ROOT/'.agent/evidence/119/qa1'
HIST = Path('/home/cnross/.tmp/nizam-feature119-qa1-historical118')
ANCHOR = '8ac94f6808e8197111197c9acbf59b2aa92efc7c'
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', LC_ALL='C.UTF-8')
RESULTS = []
def write(name, value):
    (E/name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')
def git(*args, root=ROOT):
    return subprocess.check_output(['git', '-C', str(root), *args]).decode().strip()
def digest(data): return hashlib.sha256(data).hexdigest()
def identity(root):
    installed = git('ls-files', '-z', '.nizam', root=root).split('\0')
    paths = ['tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', 'tools/convergent_review.py', 'tools/README.md', 'CHANGELOG.md'] + [p for p in installed if p]
    if (root/'.agent/contracts/119.json').exists(): paths += ['.agent/contracts/119.json']
    files = {p: {'sha256': digest((root/p).read_bytes()), 'git_blob': git('rev-parse', 'HEAD:'+p, root=root)} for p in paths}
    return {'revision': git('rev-parse', 'HEAD', root=root), 'tree': git('rev-parse', 'HEAD^{tree}', root=root), 'installed_count': len([p for p in installed if p]), 'files': files}
def capture(name, argv, cwd=ROOT, expected=0, marker=None, expected_lines=None):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(); t = time.monotonic()
    p = subprocess.run(argv, cwd=cwd, env=ENV, capture_output=True, timeout=600)
    (E/(name+'.stdout.txt')).write_bytes(p.stdout); (E/(name+'.stderr.txt')).write_bytes(p.stderr)
    result = {'name': name, 'argv': argv, 'cwd': str(cwd), 'environment_overrides': {'PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C.UTF-8'}, 'revision': git('rev-parse','HEAD',root=cwd), 'started_at': started, 'elapsed_seconds': time.monotonic()-t, 'exit_code': p.returncode, 'expected_exit_code': expected, 'stdout': '.agent/evidence/119/qa1/'+name+'.stdout.txt', 'stderr': '.agent/evidence/119/qa1/'+name+'.stderr.txt'}
    result['passed'] = p.returncode == expected and (marker is None or marker in (p.stdout+p.stderr).decode()) and (expected_lines is None or p.stdout.decode().splitlines() == expected_lines)
    write(name+'.result.json', result); RESULTS.append(result)
    print(name+': exit='+str(p.returncode)+' expected='+str(expected)+' passed='+str(result['passed']), flush=True)
    return result

os.chdir(ROOT)
assert git('rev-parse','HEAD') == '8c50ec1e8a8bd44eb7e484929551f5c633fd7f58'
state = json.loads((ROOT/'.agent/run_state.json').read_bytes())
assert state['circuit_breaker']['119-QA']['attempts'] == 1
contract = json.loads((ROOT/'.agent/contracts/119.json').read_bytes())
gate = json.loads((ROOT/'.agent/validator/119-mode-b.json').read_bytes())
assert contract['status'] == 'approved' and gate['final_verdict']['approved'] is True
assert all(gate[k] == [] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
before = identity(ROOT); write('identity-before.json', before)
assert before['installed_count'] == 239
assert before['files']['tools/workflow_assurance.py']['sha256'] == 'cb28b6f793d11c7d42770421be1f110599c7956f3d0b243d70501d6f6f995e1e'
assert before['files']['tools/test_workflow_assurance.py']['sha256'] == '6e7c4e9df367bbe1173997525c3d7ad6dbfa29912574173f18403876e14cb480'
write('environment.json', {'python': sys.version, 'platform':platform.platform(), 'selected_environment': {k:ENV.get(k) for k in ('PYTHONDONTWRITEBYTECODE','LC_ALL','LANG')}, 'actor':'/root/qa119', 'root':str(ROOT), 'immutable_historical_root':str(HIST), 'current_approved_contract_sha256':before['files']['.agent/contracts/119.json']['sha256']})
assert not HIST.exists(), 'historical owned snapshot already exists'
capture('historical-snapshot-setup', ['git','worktree','add','--detach',str(HIST),ANCHOR])
if not RESULTS[-1]['passed']: raise SystemExit(1)
write('historical-identity.json', identity(HIST))
for check in contract['verification']:
    args = check['command'].split(); assert args.pop(0) == 'PYTHONDONTWRITEBYTECODE=1'
    capture('case-'+args[-1], args, expected_lines=['PASS '+args[-1]])
cases = ['identity-positive','invalidate-source','invalidate-contract','invalidate-tests','invalidate-tool','invalidate-environment','invalidate-unknown','record-continuity','reject-unowned-field','reject-history-edit','allow-owned-append','reject-self-review','reject-seal-change','reject-missing-red','reject-setup-as-red','independent-handoff','accepted-entry','reject-foreign-repo','reject-stale-pin','reject-role-write']
new = ['approve-empty','advisory-visible','block-carried','reject-issues','reject-missing-coverage','reject-unsupported']
capture('default26', ['python3','tools/test_workflow_assurance.py'], expected_lines=['PASS '+c for c in cases+new])
capture('preservation', ['python3','.agent/evidence/119/qa1/preserve.py'], marker='PASS inherited source module')
capture('historical-foundation', ['python3','tools/test_workflow_assurance.py','--check','foundation-ready'], cwd=HIST, marker='PASS foundation-ready:')
capture('live-stale-foundation', ['python3','tools/test_workflow_assurance.py','--check','foundation-ready'], expected=1, marker='pinned entry bytes/mode changed: tools/workflow_assurance.py')
capture('compliance-default', ['bash','tools/validate.sh'], marker='0 failed')
capture('compliance-payload', ['bash','tools/validate.sh','--payload'], marker='0 failed')
extra = capture('adversarial', ['python3','.agent/evidence/119/qa1/adversarial.py'], marker='PASS one independent purity check:')
(ROOT/'.agent/evidence/119-qa-adversarial.txt').write_text(json.dumps({'description':'Single evaluator-originated purity spot-check with actual write-attempt control and side-effect-denying audit hook over real carried-ledger mapping', **extra}, indent=2)+'\n')
after = identity(ROOT); write('identity-after.json', after)
assert before == after, 'protected identity changed'
write('execution-summary.json', {'actor':'/root/qa119','attempt':1,'revision':before['revision'],'protected_identities_unchanged':True,'contract_verifications':6,'current_default_cases':26,'exactly_one_adversarial':True,'all_commands_passed':all(r['passed'] for r in RESULTS),'results':RESULTS})
raise SystemExit(0 if all(r['passed'] for r in RESULTS) else 1)
