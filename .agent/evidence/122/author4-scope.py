"""Zero-API proof: only one new fixture commit hook changes; pin official housekeeping semantics."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[3]
BASE = 'd96cc8295f79bccd990041375b92e4e03a71012d'
old = ast.parse(subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':tools/test_workflow_assurance.py']))
new = ast.parse((ROOT/'tools/test_workflow_assurance.py').read_bytes()); reduced = copy.deepcopy(new)
fixture = next(n for n in reduced.body if isinstance(n,ast.ClassDef) and n.name == 'FailureFixture')
hook = next(n for n in fixture.body if isinstance(n,ast.FunctionDef) and n.name == 'commit'); fixture.body.remove(hook)
assert ast.dump(old) == ast.dump(reduced), 'Anything beyond the additive new122 hook changed'
expected = ast.parse("""def commit(self, message):
    if not getattr(self, '_fixture_housekeeping_disabled', False):
        for key, value in (('gc.auto', '0'), ('maintenance.auto', 'false')):
            git(self.root, 'config', '--local', key, value)
        self._fixture_housekeeping_disabled = True
    return super().commit(message)
""").body[0]
assert ast.dump(hook) == ast.dump(expected), 'Only fixture-local once-before-super configuration is authorized'
receipt = next(n for n in old.body if isinstance(n,ast.ClassDef) and n.name == 'ReceiptFixture')
init = next(n for n in receipt.body if isinstance(n,ast.FunctionDef) and n.name == '__init__')
commits = [n.lineno for n in ast.walk(init) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr == 'commit' and isinstance(n.func.value,ast.Name) and n.func.value.id == 'self']
git_init = [n.lineno for n in ast.walk(init) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id == 'git' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value == 'init']
assert git_init and min(git_init) < min(commits), 'Root exists before dynamically dispatched first commit'
worker = lambda generation: ast.parse((ROOT/('.agent/evidence/122/controls'+generation+'-worker.py')).read_bytes())
body = lambda tree: next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name == 'worker')
assert ast.dump(body(worker('2'))) == ast.dump(body(worker('3'))), 'Worker semantic body changed'
official = Path('/home/cnross/.tmp/nizam-feature122-ci-git255-build1/source')
commit = 'e9019fcafe0040228b8631c30f97ae1adb61bcdc'
source_pins = {}
for path in ('Documentation/config/maintenance.adoc','Documentation/config/gc.adoc','run-command.c'):
    raw = subprocess.check_output(['git','-C',str(official),'show',commit+':'+path])
    source_pins[path] = dict(source_commit=commit,git_blob=subprocess.check_output(['git','-C',str(official),'rev-parse',commit+':'+path]).decode().strip(),sha256=hashlib.sha256(raw).hexdigest())
binary = Path('/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/bin/git')
assert hashlib.sha256(binary.read_bytes()).hexdigest() == '81ba53616316440d4afc8a99107301b32790eb1a9157bdd97274017fbd4d0e4b'
print(json.dumps(dict(scope='Only additive FailureFixture.commit hook; inherited42/all semantic assertions/inventories/full .git snapshots unchanged',worker_semantic_body_unchanged=True,api_calls=0,official_source=source_pins,git_binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest()),sort_keys=True))
