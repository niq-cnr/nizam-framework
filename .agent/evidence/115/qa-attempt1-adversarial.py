"""Independent fresh-QA spot: staging attacks hidden by restored working bytes."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

PRODUCT = Path('/home/cnross/.tmp/nizam-115-qa-attempt1-0438usyf/tools/workflow_assurance.py')
spec = importlib.util.spec_from_file_location('fresh_qa_product', PRODUCT)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True)
    return result.stdout


def reject(operation, fragment, label):
    try:
        operation()
    except api.AssuranceError as error:
        assert fragment in str(error), (label, str(error))
        print('INTENDED_REJECTION', label, str(error))
    else:
        raise AssertionError('FALSE_PASS: ' + label)


with tempfile.TemporaryDirectory(prefix='nizam-115-fresh-qa-index-') as scratch:
    root = Path(scratch) / 'fixture'
    root.mkdir()
    git(root, 'init', '-q')
    git(root, 'config', 'user.name', 'Fresh Independent QA')
    git(root, 'config', 'user.email', 'fresh-qa@example.invalid')
    git(root, 'remote', 'add', 'origin', 'https://example.invalid/fresh-index-fixture.git')
    baseline_record = {'status': 'running', 'budget': 5400, 'history': [{'gate': 'approved'}]}
    seeded = {'source.py': b'value = 1\n', 'contract.json': b'{"approved":true}\n',
              'test.py': b'assert 1 == 1\n', 'tool.py': b'print("fixture")\n',
              'record.json': json.dumps(baseline_record).encode()}
    for name, data in seeded.items():
        (root / name).write_bytes(data)
        (root / name).chmod(0o644)
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'fresh QA immutable fixture')
    anchor = git(root, 'rev-parse', 'HEAD').decode().strip()
    inputs = {'source': ['source.py'], 'contracts': ['contract.json'],
              'tests': ['test.py'], 'tools': ['tool.py'], 'unknown_dependencies': []}
    ownership = {'record.json': ['/history', '/status']}

    def assess():
        return api.assess_repository(root, anchor, inputs, [], ownership)

    def restored(label):
        assert api.compare_identity(initial, assess()) is True
        print('POSITIVE_CONTROL', label)

    initial = assess()
    assert initial['source_commit'] == anchor
    print('POSITIVE_CONTROL pristine actual assessment', anchor)

    # Only the Git index contains changed source; all workspace bytes match anchor.
    (root / 'source.py').write_bytes(b'value = 2\n')
    git(root, 'add', 'source.py')
    (root / 'source.py').write_bytes(seeded['source.py'])
    assert (root / 'source.py').read_bytes() == git(root, 'show', anchor + ':source.py')
    assert git(root, 'show', ':source.py') != seeded['source.py']
    reject(assess, 'unknown/assessed bytes changed: source.py', 'staged source drift with pristine workspace')
    git(root, 'add', 'source.py')
    restored('restored source index')

    # Git index can change executable mode independently of filesystem bytes/mode.
    git(root, 'update-index', '--chmod=+x', 'tool.py')
    assert not ((root / 'tool.py').stat().st_mode & 0o111)
    assert git(root, 'ls-files', '--stage', 'tool.py').startswith(b'100755 ')
    reject(assess, 'executable mode changed: tool.py', 'staged-only executable mode drift')
    git(root, 'update-index', '--chmod=-x', 'tool.py')
    restored('restored executable index mode')

    # An unowned budget change must fail even if the actual record file is restored.
    bad_record = copy.deepcopy(baseline_record)
    bad_record['budget'] = 7020
    (root / 'record.json').write_text(json.dumps(bad_record))
    git(root, 'add', 'record.json')
    (root / 'record.json').write_bytes(seeded['record.json'])
    assert json.loads(git(root, 'show', ':record.json'))['budget'] == 7020
    reject(assess, "unowned record value changed: ('budget',)", 'staged unowned budget with pristine workspace')
    git(root, 'add', 'record.json')
    restored('restored unowned record index')

    # Legitimate staged-only scalar update and append remain valid against anchor.
    good_record = copy.deepcopy(baseline_record)
    good_record['status'] = 'finished'
    good_record['history'].append({'gate': 'captured'})
    (root / 'record.json').write_text(json.dumps(good_record))
    git(root, 'add', 'record.json')
    (root / 'record.json').write_bytes(seeded['record.json'])
    assert json.loads(git(root, 'show', ':record.json'))['status'] == 'finished'
    restored('legitimate staged owned scalar and history append accepted')
    git(root, 'add', 'record.json')
    restored('final complete restoration')
    assert git(root, 'status', '--porcelain') == b''
print('PASS independent staged-only drift adversary: 3 intended rejections and 6 positive controls')
