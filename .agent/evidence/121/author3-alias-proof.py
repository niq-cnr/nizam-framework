"""Bounded fixture ownership proof; no full suite or acceptance gate verdict."""
import ast
import copy
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
FROZEN = 'a8ba0c53ac5f646d50df2ae58e622f4b231aafc6'
TEST = 'tools/test_workflow_assurance.py'


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args]).decode().strip()


def load(text):
    namespace = {'__file__': str(ROOT / TEST), '__name__': 'fixture_snapshot_probe'}
    exec(compile(text, str(ROOT / TEST), 'exec'), namespace)
    return namespace


def policy_restore(source):
    function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'lane_spoof')
    assignment = next(n for n in function.body if isinstance(n, ast.Assign) and
        any(isinstance(t, ast.Attribute) and ast.unparse(t) == 'f.policy' for t in n.targets))
    return compile(ast.Module(body=[assignment], type_ignores=[]), '<actual-policy-restore>', 'exec')


def prove(label, source):
    module = load(source)
    with tempfile.TemporaryDirectory(prefix='author3-alias-') as parent:
        f = module['LaneFixture'](parent)
        try:
            for name, value in [('contract', json.loads((f.root / 'contract.json').read_text())),
                                ('run_state', f.state), ('feature_list', f.features)]:
                jsonschema.validate(value, json.loads((f.root / ('schema/' + name + '.schema.json')).read_text()))
            registration = module['git'](f.root, 'worktree', 'list', '--porcelain')
            assert ('worktree ' + str(f.attempt) + '\nHEAD ' + f.base + '\ndetached') in registration
            saved = copy.deepcopy(f.request)
            saved_bytes = module['canonical'](saved)
            f.request = saved
            attached = f.worktree('attached', True)
            f.authorize(attempt_root=str(attached))
            request_alias = module['canonical'](saved) != saved_bytes
            # Exercise the actual saved-policy restoration AST before and after bad authority.
            policy = copy.deepcopy(f.policy)
            policy_bytes = module['canonical'](policy)
            scope = dict(f=f, policy=policy, copy=copy)
            restore = policy_restore(source)
            exec(restore, scope)
            f.policy['authority_ref'] = f.pin('proof/bad-authority.json', {'approved': 1})
            exec(restore, scope)
            policy_alias = module['canonical'](policy) != policy_bytes
            assert request_alias == policy_alias == (label == 'frozen')
            print(json.dumps(dict(label=label, fixture_root=str(f.root), base=f.base,
                schemas=['contract', 'run_state', 'feature_list'], registration=registration,
                request_saved_snapshot_mutated=request_alias, policy_saved_snapshot_mutated=policy_alias,
                saved_request_root=saved['attempt_root'], actual_probe_root=str(attached)), sort_keys=True), flush=True)
        finally:
            f.close()


old = subprocess.check_output(['git', '-C', str(ROOT), 'show', FROZEN + ':' + TEST]).decode()
current = (ROOT / TEST).read_text()
assert hashlib.sha256(old.encode()).hexdigest() == 'c7273078ababd7aef1f9f72601fa93d8b5698baf608e7a86128b2502f3d456bc'
provenance = dict(revision=git('rev-parse', 'HEAD'), frozen_revision=FROZEN,
    test_sha256=hashlib.sha256(current.encode()).hexdigest(), source_sha256=hashlib.sha256((ROOT / 'tools/workflow_assurance.py').read_bytes()).hexdigest())
print(json.dumps(provenance, sort_keys=True), flush=True)
provecount = 0
for label, source in [('frozen', old), ('corrected', current)]:
    prove(label, source)
    provecount += 1
assert provecount == 2
print('PASS bounded real fixture/schema and request/policy snapshot ownership proof', flush=True)
