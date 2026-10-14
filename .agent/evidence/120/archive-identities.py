"""Root evidence transport: archive existing sealed blobs; execute no fixture or Source."""
import datetime
import hashlib
import json
import pathlib
import struct
import subprocess

E = pathlib.Path('.agent/evidence/120')
MERGE = 'f270bbbe511dc4ec47ed416bc0cefbae60e2c5cb'
SEAL_REVISION = '0edf4c64496e145d4b936292d72e6f14827ce845'
SEAL_PATH = str(E / 'executable-review1-seal.json')
RESTORE = pathlib.Path('/home/cnross/.tmp/nizam-feature120-identity-restore1.git')
assert not RESTORE.exists()
records = []
def capture(name, argv, *, data=None, expected=0):
    run = subprocess.run(argv, input=data, capture_output=True)
    out, err = E / ('identity-archive1-' + name + '.stdout'), E / ('identity-archive1-' + name + '.stderr')
    out.write_bytes(run.stdout)
    err.write_bytes(run.stderr)
    records.append({'name': name, 'argv': argv, 'cwd': str(pathlib.Path.cwd()), 'actual_exit': run.returncode, 'expected_exit': expected, 'stdout': str(out), 'stderr': str(err)})
    (E / 'identity-archive1-commands.json').write_text(json.dumps(records, indent=2) + '\n')
    assert run.returncode == expected, name
    return run.stdout
seal_bytes = subprocess.check_output(['git', 'show', SEAL_REVISION + ':' + SEAL_PATH])
objects = json.loads(seal_bytes)['identity_objects']
assert len(objects) == 17
reachable = {line.split(b' ', 1)[0].decode() for line in capture('reachable', ['git', 'rev-list', '--objects', MERGE]).splitlines()}
missing = sorted(set(objects) - reachable)
assert len(missing) == 11
for oid, pin in objects.items():
    assert subprocess.check_output(['git', 'cat-file', '-t', oid]).strip() == b'blob'
    raw = subprocess.check_output(['git', 'cat-file', 'blob', oid])
    assert len(raw) == pin['size_bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256']
pack = capture('pack', ['git', 'pack-objects', '--stdout', '--window=17', '--depth=17'], data=('\n'.join(sorted(objects)) + '\n').encode())
assert pack[:4] == b'PACK' and struct.unpack('>II', pack[4:12]) == (2, 17)
assert len(pack) <= 262144
archive = E / 'retained-identities.pack'
archive.write_bytes(pack)
capture('init', ['git', 'init', '--bare', '--quiet', str(RESTORE)])
capture('absent-before', ['git', '-C', str(RESTORE), 'cat-file', '-e', missing[0]], expected=1)
capture('restore', ['git', '-C', str(RESTORE), 'index-pack', '--stdin'], data=archive.read_bytes())
verified = []
for oid, pin in objects.items():
    kind = subprocess.check_output(['git', '-C', str(RESTORE), 'cat-file', '-t', oid]).strip()
    raw = subprocess.check_output(['git', '-C', str(RESTORE), 'cat-file', 'blob', oid])
    assert kind == b'blob' and len(raw) == pin['size_bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256']
    verified.append(oid)
result = {'role': 'Root', 'passed': True, 'actual_exit': 0, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(), 'seal_revision': SEAL_REVISION, 'seal_path': SEAL_PATH, 'seal_sha256': hashlib.sha256(seal_bytes).hexdigest(), 'merge': MERGE, 'not_reachable_from_merge': missing, 'archive': str(archive), 'archive_sha256': hashlib.sha256(pack).hexdigest(), 'archive_bytes': len(pack), 'archive_objects': 17, 'empty_restore_root': str(RESTORE), 'restored_verified_objects': verified, 'commands': str(E / 'identity-archive1-commands.json'), 'boundary': 'Append-only evidence portability repair. Original seals, fixtures, Source, tests, contracts and runtime results unchanged. No behavior rerun or new approval claim.'}
(E / 'identity-archive1-receipt.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS portable sealed17-blob archive and empty-database recovery; eleven previously unreachable identities preserved')
