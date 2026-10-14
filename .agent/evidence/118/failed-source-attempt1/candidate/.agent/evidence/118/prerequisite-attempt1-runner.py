import hashlib
import json
import re
import stat
import subprocess
import traceback
from pathlib import Path

ROOT = Path.cwd()
E = Path('.agent/evidence/118')
ACTOR = '/root/wa_prerequisite118'
SOURCE = '3dfedd208dc0f260857d2a615d92d31d2a3d8ebc'
TREE = '1e8b3be5189c5d285b1846559ef7054956d9a488'
BASE = '0cc0d1fdb12633d72a65442738470492bf56ada2'
EXPECTED_CANDIDATE = 'fd95cfa41e7a7583c5c539130360714e3445f640f366a758ae47a25aa3abda72'
observations = []
checks = []

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(Path(path).read_bytes())

def write_new(path, data):
    with Path(path).open('x') as out:
        out.write(json.dumps(data, indent=2) + '\n')

def git(*args):
    command = ['git', *args]
    result = subprocess.run(command, capture_output=True)
    observations.append({'command': command, 'exit_code': result.returncode,
                         'stdout_sha256': digest(result.stdout),
                         'stderr': result.stderr.decode()})
    if result.returncode:
        raise RuntimeError(f'Git observation failed: {command}: {result.stderr!r}')
    return result.stdout

def safe(path):
    p = Path(path)
    assert not p.is_absolute() and p.as_posix() == path and '..' not in p.parts
    for part in [p, *p.parents]:
        assert not part.is_symlink(), f'symlink: {part}'
    assert stat.S_ISREG(p.stat().st_mode), f'not regular: {p}'
    return p

def git_file(revision, path):
    record = git('ls-tree', revision, '--', path).decode().strip()
    meta, found_path = record.split('\t')
    mode, kind, blob = meta.split()
    assert found_path == path and kind == 'blob' and mode in ('100644', '100755')
    data = git('show', revision + ':' + path)
    return data, mode, blob

def verify_inputs(candidate, api, manifest, historical):
    assert digest((E / 'source-candidate.json').read_bytes()) == EXPECTED_CANDIDATE
    assert set(candidate) == {'revision','tree','source_sha256','runtime_sha256','historical_sha256'}
    assert candidate['revision'] == SOURCE and candidate['tree'] == TREE
    assert git('rev-parse', SOURCE + '^{commit}').decode().strip() == SOURCE
    assert git('rev-parse', SOURCE + '^{tree}').decode().strip() == TREE
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    assert set(manifest) == {'core_paths','runtime_paths','roles_ref'}
    assert manifest['core_paths'] == api['core_paths']
    assert len(manifest['core_paths']) == 4 and len(set(manifest['runtime_paths'])) == 27
    assert not set(manifest['core_paths']) & set(manifest['runtime_paths'])
    assert manifest['roles_ref'] == str(E / 'role-sessions.json')
    roles = read(manifest['roles_ref'])
    assert set(roles) == {'test_author','developer','acceptance_reviewer'}
    for role in roles.values():
        assert set(role) == {'agent_id','session_id'}
        assert all(type(v) is str and v and v != ACTOR for v in role.values())
    assert len({r['agent_id'] for r in roles.values()}) == 3
    assert len({r['session_id'] for r in roles.values()}) == 3
    rows = []
    groups = [('source_sha256', api['core_paths'], SOURCE, 4),
              ('runtime_sha256', manifest['runtime_paths'], SOURCE, 27),
              ('historical_sha256', api['historical_paths'], api['historical_base'], 12)]
    for group, paths, revision, count in groups:
        assert len(paths) == count and set(candidate[group]) == set(paths)
        for path in paths:
            expected = candidate[group][path]
            assert re.fullmatch('[0-9a-f]{64}', expected)
            p = safe(path)
            current = p.read_bytes()
            data, mode, blob = git_file(revision, path)
            current_mode = '100755' if p.stat().st_mode & 0o111 else '100644'
            assert digest(current) == expected == digest(data), f'digest mismatch: {path}'
            assert current_mode == mode, f'mode mismatch: {path}'
            rows.append({'group':group,'path':path,'revision':revision,'sha256':expected,
                         'git_blob':blob,'git_mode':mode,'current_mode':current_mode})
    assert len(historical['inputs']) == 23
    assert len({(r['revision'],r['path']) for r in historical['inputs']}) == 23
    historical_rows = []
    for entry in historical['inputs']:
        data, mode, blob = git_file(entry['revision'], entry['path'])
        assert digest(data) == entry['sha256']
        assert type(entry['executable']) is bool
        assert (mode == '100755') == entry['executable']
        historical_rows.append(dict(entry, git_blob=blob, git_mode=mode))
    assert git('rev-parse', historical['tag'] + '^{commit}').decode().strip() == historical['tag_revision']
    return {'candidate_sha256':EXPECTED_CANDIDATE, 'candidate':candidate,
            'current_and_git_inputs':rows,'transitive_historical_git_inputs':historical_rows,
            'roles':roles,'passed':True}

try:
    owner = read(E / 'prerequisite-attempt1.json')
    assert owner['owner'] == ACTOR and owner['root'] == str(ROOT)
    assert owner['attempt'] == 1 and owner['base'] == BASE and owner['source_revision'] == SOURCE
    contract = read('.agent/contracts/118.json')
    assert contract['status'] == 'approved'
    assert contract['approvals']['validator_mode_a'] is True
    assert contract['approvals']['evaluator_contract_review'] is True
    state = read('.agent/run_state.json')
    assert state['current_feature'] == '118' and state['status'] == 'in_progress'
    counter = state['circuit_breaker'].get('118-prerequisite')
    assert counter is None or counter['attempts'] < 3
    assert not (E / 'prerequisite20.json').exists()
    candidate = read(E / 'source-candidate.json')
    api = read(E / 'api-interface.json')
    manifest = read(E / 'runtime-inputs.json')
    historical = read(E / 'historical-runtime-inputs.json')
    producer = read(E / 'producer-interface.json')
    before = verify_inputs(candidate, api, manifest, historical)
    before['attempt_owner'] = owner
    before['counter_at_overlay_base'] = counter
    before['counter_ownership'] = '/root'
    write_new(E / 'prerequisite-attempt1-inputs-before.json', before)
    assert len(api['current_cases']) == 20
    assert len({r['case'] for r in api['current_cases']}) == 20
    for index, case in enumerate(api['current_cases'], 1):
        command = case['command']
        assert command == 'PYTHONDONTWRITEBYTECODE=1 python3 tools/test_workflow_assurance.py --case ' + case['case']
        assert re.fullmatch('[a-z-]+', case['case'])
        proof = E / f"prerequisite-attempt1-case-{index:02d}-{case['case']}.txt"
        assert not proof.exists()
        result = subprocess.run(command, shell=True, executable='/bin/bash', capture_output=True)
        raw = (f'COMMAND: {command}\nREVISION: {SOURCE}\nEXIT: {result.returncode}\nSTDOUT:\n'.encode()
               + result.stdout + b'\nSTDERR:\n' + result.stderr)
        with proof.open('xb') as out:
            out.write(raw)
        row = dict(case, exit_code=result.returncode, evidence=str(proof), sha256=digest(raw))
        checks.append(row)
        print(f"{index:02d}/20 {case['case']}: exit {result.returncode}", flush=True)
        if result.returncode != 0:
            raise RuntimeError(f"Case failed: {case['case']}; see {proof}")
        assert result.stdout.strip(), f"Empty stdout: {case['case']}"
        for header in (b'COMMAND:', b'REVISION:', b'EXIT:'):
            assert sum(line.startswith(header) for line in raw.splitlines()) == 1
    after = verify_inputs(candidate, api, manifest, historical)
    assert after == {k:v for k,v in before.items() if k not in ('attempt_owner','counter_at_overlay_base','counter_ownership')}
    write_new(E / 'prerequisite-attempt1-inputs-after.json', after)
    receipt = dict(feature='118', actor=ACTOR, session_id=ACTOR, passed=True,
                   checks_run=20, checks_passed=20, **candidate, checks=checks)
    assert set(receipt) == set(producer['prerequisite']['closed_keys'])
    assert all(set(row) == {'case','command','exit_code','evidence','sha256'} for row in checks)
    write_new(E / 'prerequisite20.json', receipt)
    write_new(E / 'prerequisite-attempt1-summary.json', {
        'actor':ACTOR,'attempt':1,'passed':True,'checks_run':len(checks),
        'checks_passed':20,'receipt':str(E / 'prerequisite20.json'),
        'receipt_sha256':digest((E / 'prerequisite20.json').read_bytes()),
        'input_verification_before':str(E / 'prerequisite-attempt1-inputs-before.json'),
        'input_verification_after':str(E / 'prerequisite-attempt1-inputs-after.json'),
        'checks':checks})
    print('receipt_sha256=' + digest((E / 'prerequisite20.json').read_bytes()), flush=True)
except BaseException:
    write_new(E / 'prerequisite-attempt1-failure.json', {
        'actor':ACTOR,'attempt':1,'passed':False,'checks_run':len(checks),
        'checks_passed':sum(r['exit_code'] == 0 for r in checks),
        'checks':checks,'diagnostic':traceback.format_exc()})
    raise
finally:
    write_new(E / 'prerequisite-attempt1-git-observations.json', observations)
