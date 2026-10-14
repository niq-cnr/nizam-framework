"""Independent, one-shot SourceC2 prerequisite evidence capture; no product imports."""
import hashlib
import json
from pathlib import Path
import stat
import subprocess

E = Path('.agent/evidence/118')
ACTOR = '/root/wa_prerequisite118_recovery1'
REV = '60cf91d1e2f0781382c20a5a18bb1673a381c0d8'
TREE = 'b64616bc09108ecc7a329f286a84dfd6e60889b4'
CANDIDATE_SHA = '95d29360b7919b768024ae10c2a072430b0b3003822f5b2611eaf868df846171'
BASE = '642e85d5f63c50f2a62e0c92896b73cbe978c192'
sha = lambda data: hashlib.sha256(data).hexdigest()
def git(*args):
    return subprocess.check_output(['git', *args])
def read(path):
    return json.loads(Path(path).read_text())
def write_new(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')

candidate = read(E / 'source-candidate.json')
api = read(E / 'api-interface.json')
producer = read(E / 'producer-interface.json')
manifest = read(E / 'runtime-inputs.json')
roles = read(E / 'role-sessions.json')
assert read('.agent/contracts/118.json')['status'] == 'approved'
assert set(candidate) == set(producer['candidate']['closed_keys'])
assert candidate['revision'] == REV and candidate['tree'] == TREE
assert sha((E / 'source-candidate.json').read_bytes()) == CANDIDATE_SHA
assert git('rev-parse', 'HEAD').decode().strip() == BASE
assert git('rev-parse', REV + '^{tree}').decode().strip() == TREE
assert all(ACTOR not in role.values() for role in roles.values())
assert set(candidate['source_sha256']) == set(api['core_paths']) == set(manifest['core_paths'])
assert set(candidate['runtime_sha256']) == set(manifest['runtime_paths'])
assert set(candidate['historical_sha256']) == set(api['historical_paths'])
assert [len(candidate[k]) for k in ['source_sha256','runtime_sha256','historical_sha256']] == [4,28,12]
assert len(api['current_cases']) == 20
assert len({r['case'] for r in api['current_cases']}) == 20
assert not (E / 'prerequisite20.json').exists()
assert not list(E.glob('recovery1-prerequisite-case-*.txt'))

def snapshot():
    rows = []
    for group in ['source_sha256', 'runtime_sha256', 'historical_sha256']:
        for name, expected in candidate[group].items():
            path = Path(name)
            info = path.lstat()
            assert stat.S_ISREG(info.st_mode), name
            current = path.read_bytes()
            blob = git('show', REV + ':' + name)
            mode = git('ls-tree', REV, '--', name).decode().split()[0]
            current_mode = '100755' if info.st_mode & 0o111 else '100644'
            assert sha(current) == sha(blob) == expected, name
            assert mode == current_mode, name
            row = {'path': name, 'group': group, 'sha256': expected, 'git_mode': mode, 'current_mode': current_mode}
            if group == 'historical_sha256':
                historical_blob = git('show', api['historical_base'] + ':' + name)
                historical_mode = git('ls-tree', api['historical_base'], '--', name).decode().split()[0]
                assert sha(historical_blob) == expected and historical_mode == mode, name
                row['historical_revision'] = api['historical_base']
                row['historical_mode'] = historical_mode
            rows.append(row)
    assert sha((E / 'source-candidate.json').read_bytes()) == CANDIDATE_SHA
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    assert not git('diff', '--name-only', 'HEAD').strip()
    return {'actor': ACTOR, 'revision': REV, 'tree': TREE, 'overlay_revision': BASE, 'candidate_sha256': CANDIDATE_SHA, 'rows': rows}

before = snapshot()
write_new(E / 'recovery1-prerequisite-identity-before.json', before)
checks = []
for index, row in enumerate(api['current_cases'], 1):
    command = row['command']
    result = subprocess.run(command, shell=True, executable='/bin/bash', capture_output=True)
    path = E / ('recovery1-prerequisite-case-%02d-%s.txt' % (index, row['case']))
    raw = ('COMMAND: ' + command + '\nREVISION: ' + REV + '\nEXIT: ' + str(result.returncode) + '\nSTDOUT:\n').encode() + result.stdout + b'\nSTDERR:\n' + result.stderr
    with path.open('xb') as f:
        f.write(raw)
    checks.append({'case': row['case'], 'command': command, 'exit_code': result.returncode, 'evidence': str(path), 'sha256': sha(raw)})
    print('%02d %s exit=%d' % (index, row['case'], result.returncode), flush=True)
after = snapshot()
write_new(E / 'recovery1-prerequisite-identity-after.json', after)
assert before == after
passed = sum(r['exit_code'] == 0 for r in checks)
receipt = {'feature': '118', 'actor': ACTOR, 'session_id': ACTOR, 'passed': passed == 20, 'checks_run': len(checks), 'checks_passed': passed, **candidate, 'checks': checks}
assert set(receipt) == set(producer['prerequisite']['closed_keys'])
write_new(E / 'prerequisite20.json', receipt)
print('receipt_sha256=' + sha((E / 'prerequisite20.json').read_bytes()), flush=True)
print('checks_passed=%d/20 identity_unchanged=true' % passed, flush=True)
