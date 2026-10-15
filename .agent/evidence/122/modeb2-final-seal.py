"""Read-only current final seal binding audit; never executes controls or API."""
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import jsonschema
ROOT = Path(__file__).resolve().parents[3]
SEAL_REV = '2ff08b54636cbb0afd89fb8e59393e59e9d96b77'
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)
def raw(path):
    return (ROOT / path).read_bytes()
def load(path):
    return json.loads(raw(path))
def sha(data):
    return hashlib.sha256(data).hexdigest()
def snapshot():
    records = []
    for path in git('ls-files', '-z').decode().split('\0'):
        if not path: continue
        p = ROOT / path
        records.append([path, stat.S_IMODE(p.lstat().st_mode), sha(raw(path))])
    return dict(count=len(records), sha256=sha(json.dumps(records, separators=(',', ':')).encode()))
before = snapshot()
seal_path = '.agent/evidence/122/executable1-current-seal.json'
verdict_path = '.agent/qa/122-executable-bundle-review.json'
seal = load(seal_path); verdict = load(verdict_path)
assert git('show', SEAL_REV + ':' + seal_path) == raw(seal_path)
assert git('show', SEAL_REV + ':' + verdict_path) == raw(verdict_path)
jsonschema.Draft202012Validator(load('schema/qa_verdict.schema.json')).validate(verdict)
assert seal['approved'] is True and verdict['final_verdict']['approved'] is True
assert all(verdict[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims', 'required_fixes'))
assert verdict['checks_run'] == verdict['checks_passed'] == 24
assert len(seal['refs']) == 17 and len(seal['portable_objects']) == 8
for entry in seal['refs']:
    data = git('show', entry['revision'] + ':' + entry['path'])
    observed = git('ls-tree', entry['revision'], '--', entry['path']).decode().split()
    assert sha(data) == entry['sha256'] and data == raw(entry['path'])
    assert observed[0] == entry['git_mode'] and observed[2] == entry['git_blob']
    assert bool((ROOT / entry['path']).stat().st_mode & 0o111) == (entry['git_mode'] == '100755')
for identity in seal['portable_objects'].values():
    data = git('cat-file', 'blob', identity['git_oid'])
    assert sha(data) == identity['sha256'] and len(data) == identity['size_bytes']
for entry in seal['historical_state_anchors']:
    pin = entry['snapshot_pin']; data = git('show', entry['revision'] + ':' + entry['path'])
    observed = git('ls-tree', entry['revision'], '--', entry['path']).decode().split()
    assert sha(data) == pin['sha256'] and observed[2] == pin['git_blob']
    assert (observed[0] == '100755') is pin['executable']
for result_path in ('.agent/evidence/122/controls3-runtime2-result.json', '.agent/evidence/122/controls3-executable-review1-result.json'):
    result = load(result_path)
    assert result['complete'] is True and result['preparation_only'] is False
    assert result['inputs']['objects'] == seal['portable_objects']
    assert result['protected_before'] == result['protected_after'] and len(result['captures']) == 24
    captures = result['captures']; assert [c['actual_exit'] for c in captures[:12]] == [0] * 12
    assert [c['actual_exit'] for c in captures[12:]] == [0, 1, 0] * 4
    for capture in captures:
        assert capture['actual_exit'] == capture['expected_exit'] and capture['protected_unchanged'] is True
        data = raw(capture['stdout'])
        if capture['stdout_storage'] == 'portable-pack-object':
            ref = json.loads(data); assert ref['pack'] == '.agent/evidence/122/controls3-identities.pack'
            identity = ref['identity']; assert identity in seal['portable_objects'].values()
            data = git('cat-file', 'blob', identity['git_oid'])
        assert sha(data) == capture['stdout_sha256'] and len(data) == capture['stdout_size_bytes']
        assert sha(raw(capture['stderr'])) == capture['stderr_sha256']
for label in ('replay', 'own-audit', 'author-audit', 'scope-receipt'):
    result = load('.agent/evidence/122/executable1-current-' + label + '.execution.json')
    assert result['actual_exit'] == 0
    assert (ROOT / result['stdout']).is_file() and (ROOT / result['stderr']).is_file()
after = snapshot(); assert before == after
print(json.dumps(dict(seal_revision=SEAL_REV, verified_refs=17, verified_portable_blobs=8, historical_state_anchors=2, author_and_replay_commands=[24,24], each_case_actual_exits=[0,1,0], each_archive_actual_exits=[0]*12, complete_raw_hashes=True, protected_before=before, protected_after=after, api_calls=0), sort_keys=True))
