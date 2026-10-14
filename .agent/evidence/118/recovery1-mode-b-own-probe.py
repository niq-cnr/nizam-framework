"""Independent private Mode B probes; scratch only, not a product switch."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
E = '.agent/evidence/118/'
def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod
candidate = json.loads((ROOT / (E+'source-candidate.json')).read_text())
revision = candidate['revision']
assert git(ROOT, 'rev-parse', revision+'^{tree}').decode().strip() == candidate['tree']
for group, count in [('source_sha256',4),('runtime_sha256',28),('historical_sha256',12)]:
    assert len(candidate[group]) == count
    for name, digest in candidate[group].items():
        current = ROOT/name
        assert not current.is_symlink() and current.is_file()
        blob = git(ROOT, 'show', revision+':'+name)
        mode, kind = git(ROOT, 'ls-tree', revision, '--', name).decode().split()[:2]
        assert kind == 'blob' and mode in ('100644','100755')
        assert bool(current.stat().st_mode & 0o111) == (mode == '100755')
        assert current.read_bytes() == blob and hashlib.sha256(blob).hexdigest() == digest
print('PASS actual SourceC2 tree/current/Git bytes and modes: 4 core, 28 runtime, 12 historical')
base = 'dfba397ad712d6731c612355001fb7885bb8116c'
old = git(ROOT, 'show', base+':tools/workflow_assurance.py').decode()
new = (ROOT/'tools/workflow_assurance.py').read_text()
old_nodes = {x.name: ast.get_source_segment(old,x) for x in ast.parse(old).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
new_nodes = {x.name: ast.get_source_segment(new,x) for x in ast.parse(new).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
assert all(new_nodes[k] == v for k,v in old_nodes.items())
assert set(new_nodes)-set(old_nodes) == {'verify_foundation_ready'}
print('PASS all previous function/class bodies exact; sole new function verify_foundation_ready')
api = load('reviewed_source', ROOT/'tools/workflow_assurance.py')
prereq = json.loads((ROOT/(E+'prerequisite20.json')).read_text())
with tempfile.TemporaryDirectory(prefix='nizam118-modeb-own-') as temp:
    scratch = Path(temp)/'repo'
    subprocess.run(['git','clone','-q','--shared',str(ROOT),str(scratch)],check=True)
    assert api.verify_foundation_ready(scratch,prereq) is True
    print('PASS original actual prerequisite positive in disposable Git clone')
    original = git(scratch,'rev-parse','refs/tags/v1.5.0').decode().strip()
    subprocess.run(['git','-C',str(scratch),'update-ref','refs/tags/v1.5.0',revision],check=True)
    try:
        api.verify_foundation_ready(scratch,prereq)
    except api.AssuranceError as exc:
        assert str(exc) == 'historical runtime tag changed', str(exc)
        print('PASS own adversary: unchanged file maps with redirected actual installed tag rejected: '+str(exc))
    else:
        raise AssertionError('redirected historical Git tag accepted')
    subprocess.run(['git','-C',str(scratch),'update-ref','refs/tags/v1.5.0',original],check=True)
    assert api.verify_foundation_ready(scratch,prereq) is True
    print('PASS restored actual tag positive')
    adapter = load('reviewed_adapter', ROOT/(E+'recovery1-closeout-guard.py'))
    before, valid, row = adapter.fixture()
    oldrow = next(x for x in before.splitlines() if x.startswith('| NDEBT-054 |'))
    malformed = '|'.join(oldrow.split('|')[:6])+'| RESOLVED '+adapter.g.QA+' '+adapter.g.CAPTURE+' '+E+'recovery-authorization.json |'
    assert len(row.split('|')) == 7 and len(malformed.split('|')) == 8
    adapter.g.ROOT = scratch
    target = scratch/'docs/planning/DEBT.md'
    target.write_text(valid)
    try:
        adapter.ORIGINAL_DEBT(True)
    except AssertionError as exc:
        assert '054 identity/date/severity/description' in str(exc), str(exc)
        print('REPRODUCED original false failure: valid five-column Notes replacement rejected: '+str(exc))
    else:
        raise AssertionError('original valid-row defect not reproduced')
    adapter.debt(True)
    print('PASS adapter valid five-column private fixture')
    target.write_text(valid.replace(row,malformed))
    adapter.ORIGINAL_DEBT(True)
    print('REPRODUCED original false pass: malformed six-column row accepted')
    try:
        adapter.debt(True)
    except AssertionError as exc:
        assert 'exact five debt columns' in str(exc), str(exc)
        print('PASS adapter rejects original malformed positive: '+str(exc))
    else:
        raise AssertionError('adapter accepted malformed sixth column')
print('LIMIT: debt fixtures are private parser probes, not actual capture or terminal scope success')
