"""Read-only recovery verifier; no acceptance or mutation processes are run."""
import hashlib
import json
import pathlib
import subprocess

import jsonschema

ROOT = pathlib.Path(__file__).resolve().parents[3]
EVIDENCE = '.agent/evidence/121/'
AUTHOR = '6178b7ed5798ecb752ea7c01b70798ab3e36a1b7'
OWN = 'b3d416a57fd9ec7b273ca776f2b625c035751faf'
DISPATCH = '849e29c7fa8ca1d711acfb58bd953ce3e200fbe2'
CASES = ('independent-lanes', 'shared-state-serialized', 'reject-terminal-spoof', 'reject-fourth', 'owned-rollback')


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob_identity(data):
    return dict(git_oid=hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
                sha256=sha(data), size_bytes=len(data), type='blob')


def load(path, revision=None):
    data = git('show', revision + ':' + path) if revision else (ROOT / path).read_bytes()
    return json.loads(data)


def check(value, label):
    if not value:
        raise AssertionError(label)


def tree(revision):
    result = {}
    for row in git('ls-tree', '-rz', revision).split(b'\0'):
        if row:
            metadata, path = row.split(b'\t', 1)
            mode, kind, oid = metadata.decode().split()
            result[path.decode()] = dict(mode=mode, type=kind, git_oid=oid)
    return result


def verify_snapshots(result, revision, label):
    check(result['protected_before'] == result['protected_after'], label + ' full filesystem before/after equality')
    entries = tree(revision)
    for path, row in result['protected_before'].items():
        data = git('show', revision + ':' + path)
        check(sha(data) == row['sha256'], label + ' historical blob ' + path)
        check(bool(int(entries[path]['mode'], 8) & 0o111) == bool(row['mode'] & 0o111),
              label + ' normalized executable bit ' + path)
    return len(result['protected_before'])


def verify_captures(result, artifact_revision, exercised_revision, label):
    check(result['complete'] is True and len(result['captures']) == 27, label + ' complete27')
    check(result['release_revision'] == exercised_revision and result['helper_revision'] == exercised_revision,
          label + ' exercised binding')
    expected_labels = ['archive-init', 'archive-empty', 'archive-import', 'archive-restored']
    expected_labels += ['archive-blob-' + name for name in result['inputs']['objects']]
    expected_labels += [case + '-' + stage for case in CASES for stage in ('positive', 'semantic-red', 'restored')]
    check([row['label'] for row in result['captures']] == expected_labels, label + ' exact capture order')
    summaries = []
    for row in result['captures']:
        check(row['revision'] == exercised_revision and row['release_revision'] == exercised_revision,
              label + ' capture revision ' + row['label'])
        check(row['actual_exit'] == row['expected_exit'] and row['protected_unchanged'] is True,
              label + ' actual exit/preservation ' + row['label'])
        raw = {key: git('show', artifact_revision + ':' + row[key]) for key in ('stdout', 'stderr')}
        for key, data in raw.items():
            check(sha(data) == row[key + '_sha256'] and data == (ROOT / row[key]).read_bytes(),
                  label + ' raw identity ' + row['label'] + ':' + key)
        if row['expected_assertion']:
            check(row['actual_exit'] == 1 and [line for line in raw['stderr'].decode().splitlines()
                  if line.startswith('AssertionError: POLICY_ASSERTION:')] == [row['expected_assertion']],
                  label + ' exact intended assertion ' + row['label'])
            traces = [json.loads(line[len('API_TRACE '):]) for line in raw['stdout'].decode().splitlines()
                      if line.startswith('API_TRACE ')]
            fixtures = [json.loads(line[len('FIXTURE_TRACE '):]) for line in raw['stdout'].decode().splitlines()
                        if line.startswith('FIXTURE_TRACE ')]
            check(traces and traces[-1] == row['intended_api_trace'] and traces[-1]['returned'] is True
                  and fixtures and 'detached' in fixtures[0]['registration'] and b'PASS ' not in raw['stdout'],
                  label + ' actual API/fixture trace ' + row['label'])
            last = traces[-1]
            case = row['label'].removesuffix('-semantic-red')
            predicates = {
                'independent-lanes': lambda: last['result']['eligible'] is False and last['result']['conflicts'] == [],
                'shared-state-serialized': lambda: last['result']['eligible'] is True and last['result']['conflicts'] == [],
                'reject-terminal-spoof': lambda: type(last['authority_approved']) is int and last['authority_approved'] == 1,
                'reject-fourth': lambda: type(last['attempt']) is int and last['attempt'] == 4,
                'owned-rollback': lambda: last['method'] == 'rollback_owned_attempt' and last['result']['removed'] is False,
            }
            check(predicates[case](), label + ' semantic target ' + case)
        elif any(row['label'] == case + '-' + stage for case in CASES for stage in ('positive', 'restored')):
            case = row['label'].rsplit('-', 1)[0]
            check(row['actual_exit'] == 0 and raw['stdout'].decode().splitlines() == ['PASS ' + case],
                  label + ' positive/restored marker ' + row['label'])
        else:
            check(row['actual_exit'] == 0, label + ' archive exit ' + row['label'])
        summaries.append({key: row[key] for key in ('label', 'argv', 'cwd', 'environment', 'revision',
                         'actual_exit', 'expected_exit', 'expected_assertion', 'stdout', 'stderr',
                         'stdout_sha256', 'stderr_sha256')})
    return summaries


def main():
    seal = load(EVIDENCE + 'controls2-author-seal.json', AUTHOR)
    manifest = load(EVIDENCE + 'controls2-identities.json', AUTHOR)
    author_result = load(EVIDENCE + 'controls2-author-result.json', AUTHOR)
    own_result = load(EVIDENCE + 'controls2-reviewer-result.json', OWN)
    static = load(EVIDENCE + 'executable-review1-static-proof.json', OWN)
    failure = load(EVIDENCE + 'executable-review1-postrun-failure.json', OWN)
    author_tree = tree(AUTHOR)
    check(len(seal['immutable_artifact_pins']) == 65, 'author65')
    for row in seal['immutable_artifact_pins']:
        data = git('show', AUTHOR + ':' + row['path'])
        check(blob_identity(data) == {key: row[key] for key in ('git_oid', 'sha256', 'size_bytes', 'type')}
              and author_tree[row['path']]['mode'] == row['mode'] and data == (ROOT / row['path']).read_bytes(),
              'author immutable pin ' + row['path'])
    for name, revision, result in [('author', AUTHOR, author_result), ('reviewer', OWN, own_result)]:
        wrapper = load(EVIDENCE + 'controls2-' + name + '-wrapper.json', revision)
        check(wrapper['actual_exit'] == 0, name + ' successful runtime wrapper')
        for row in wrapper['outputs'].values():
            data = git('show', revision + ':' + row['path'])
            check(sha(data) == row['sha256'] and len(data) == row['size_bytes'], name + ' wrapper raw')
    check(load(EVIDENCE + 'controls2-reviewer-wrapper.json', OWN)['executor'] == '/root/review_controls121',
          'independent executor attribution')
    author_count = verify_snapshots(author_result, seal['exercised_revision'], 'author')
    own_count = verify_snapshots(own_result, own_result['release_revision'], 'reviewer')
    author_captures = verify_captures(author_result, AUTHOR, seal['exercised_revision'], 'author')
    own_captures = verify_captures(own_result, OWN, own_result['release_revision'], 'reviewer')
    check(len(manifest['objects']) == 8 and manifest['objects'] == seal['identity_objects']
          and own_result['inputs'] == manifest, 'eight exact identity manifest')
    source = (ROOT / 'tools/workflow_assurance.py').read_bytes()
    identities = {}
    for name, expected in manifest['objects'].items():
        for result, revision in [(author_result, AUTHOR), (own_result, OWN)]:
            row = next(row for row in result['captures'] if row['label'] == 'archive-blob-' + name)
            data = git('show', revision + ':' + row['stdout'])
            check(blob_identity(data) == expected, 'restored exact identity ' + name)
        identities[name] = expected
        if name in CASES:
            mutation = next(row for row in static['private_source_mutations'] if row['case'] == name)
            expected_source = source.decode()
            for change in mutation['changes']:
                check(expected_source.count(change['before']) == 1, 'single mutation target ' + name)
                expected_source = expected_source.replace(change['before'], change['after'])
            check(data == expected_source.encode(), 'exact public Source mutation ' + name)
        else:
            path = {'source': 'tools/workflow_assurance.py', 'tests': 'tools/test_workflow_assurance.py',
                    'helper': EVIDENCE + 'controls2-run.py'}[name]
            check(data == (ROOT / path).read_bytes(), 'unchanged frozen input ' + name)
    pack = (ROOT / (EVIDENCE + 'controls2-identities.pack')).read_bytes()
    check(sha(pack) == manifest['pack_sha256'] and len(pack) == manifest['pack_bytes'], 'frozen pack')
    prior_tree = tree(static['reviewed_revision'])
    current_tree = tree(DISPATCH)
    inherited_paths = ['tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/contracts/121.json']
    inherited_paths += [path for path in prior_tree if path.startswith(('schema/', '.nizam/'))]
    for path in inherited_paths:
        check(prior_tree[path] == current_tree[path] and
              blob_identity((ROOT / path).read_bytes())['git_oid'] == current_tree[path]['git_oid'],
              'protected Source/test/schema/installed unchanged ' + path)
    check(sum(path.startswith('.nizam/') for path in current_tree) == 239, 'installed239')
    check(failure['actual_exit'] == 1 and failure['stdin_provenance_limitation'], 'original failed utility preserved')
    for key in ('stdout', 'stderr'):
        check(sha(git('show', OWN + ':' + failure[key])) == failure[key + '_sha256'], 'original failure raw ' + key)
    candidate = load(EVIDENCE + 'executable-review2-candidate-verdict.json')
    check(candidate['feature'] == candidate['feature_id'] == '121' and
          candidate['final_verdict']['approved'] is True and
          all(candidate[key] == [] for key in ('issues', 'missing_acceptance_coverage', 'unsupported_claims')),
          'strict AGF envelope')
    schema_paths = ['schema/contract_review.schema.json', '.nizam/schema/contract_review.schema.json']
    for path in schema_paths:
        jsonschema.validate(candidate, load(path))
    print(json.dumps(dict(result='pass',reviewer='/root/review_controls121',attempt=2,
        verifier_revision=git('rev-parse', 'HEAD').decode().strip(),author_revision=AUTHOR,
        own_artifact_revision=OWN,own_exercised_revision=own_result['release_revision'],
        author_immutable_pins_verified=65,author_protected_snapshot_files=author_count,
        reviewer_protected_snapshot_files=own_count,mode_profile='Historical blob SHA256 and Git executable boolean only; full filesystem mode equality checked within each recorded before/after pair. Git does not attest all permission bits.',
        identity_objects=identities,author_captures=author_captures,reviewer_captures=own_captures,
        inherited_static_inventory_reused=EVIDENCE+'executable-review1-static-proof.json',
        protected_paths_checked=len(inherited_paths),installed_count=239,schema_validation=schema_paths,
        original_failed_utility=EVIDENCE+'executable-review1-postrun-failure.json',
        inline_body_provenance_limitation=failure['stdin_provenance_limitation'],
        no_prior_gate_approval=True,no_acceptance_runtime_rerun=True),indent=2))


if __name__ == '__main__':
    main()
