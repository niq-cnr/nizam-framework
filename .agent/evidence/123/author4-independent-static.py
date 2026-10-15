"""Independent static4 only: AST/compile-in-memory/Git/bytes/modes; never import product/tests."""
import ast
import collections
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[3]
CODE = 'd1fd767bca33f7e54486ebc8542811315fe48bde'
BASE = '40285cd344ed92bfed5345185c7d46b8c41c007b'
PREPARATION = '299e5ac29422a34510502c0c2d5e2365cac47563'
PRESERVED = 'f8965efbfe1323b7cd6c342f87cb9cb8102f4e76'
SOURCE55 = '3e824cbc7b18b458edc82e8f63d900b510c68d2c'
TEST = 'tools/test_workflow_assurance.py'
PINS = {TEST: '06eba273dbfd615df7f0ea3b6b52592ed208f9ec267b52a1e06996488b850f13',
    'tools/workflow_assurance.py': '2579b0d94598621acccc6e257408e80a0657834393a6f30be878da94967e70b8',
    'tools/workflow_assurance_ci.py': '7ab3b092188383897900b7f84af2c22156d662ebe355e25b837b250123b49905',
    '.agent/contracts/123.json': '64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5',
    '.agent/evidence/123/author3-controls.py': '79352536f9db966c73d7552dc5112db08a4fa356d507bf9c6482aef27f06e8bd'}


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=20)


def sha(raw): return hashlib.sha256(raw).hexdigest()
def dump(node): return ast.dump(node, include_attributes=False)
def historical(revision, path): return git('show', revision + ':' + path)
def definitions(tree): return {n.name: dump(n) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
def constructor(tree):
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ControlsFixture')
    return cls, next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')


def snapshot():
    rows = []
    for path in filter(None, git('ls-files', '-z').split(b'\0')):
        name = os.fsdecode(path); target = ROOT / name; info = target.lstat()
        if stat.S_ISLNK(info.st_mode): value = os.readlink(target)
        else:
            h = hashlib.sha256()
            with target.open('rb') as stream:
                for block in iter(lambda: stream.read(65536), b''): h.update(block)
            value = h.hexdigest()
        rows.append((name, info.st_mode, info.st_nlink, value))
    return rows


def inventories(tree):
    result = {}
    def value(node):
        if isinstance(node, ast.Name): return result[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add): return value(node.left) + value(node.right)
        return ast.literal_eval(node)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id.endswith('CASES'):
            result[node.targets[0].id] = value(node.value)
    return result


class InheritedMain(ast.NodeTransformer):
    def visit_BinOp(self, node):
        node = self.generic_visit(node)
        return node.left if isinstance(node.op, ast.Add) and isinstance(node.right, ast.Name) and node.right.id == 'CONTROL_CASES' else node
    def visit_IfExp(self, node):
        node = self.generic_visit(node)
        return node.orelse if any(isinstance(n, ast.Name) and n.id == 'CONTROL_CASES' for n in ast.walk(node.test)) else node
    def visit_If(self, node):
        if any(isinstance(n, ast.Constant) and n.value == 'controls-ready' for n in ast.walk(node.test)): return None
        return self.generic_visit(node)
    def visit_Tuple(self, node):
        node = self.generic_visit(node)
        node.elts = [n for n in node.elts if not isinstance(n, ast.Constant) or n.value != 'controls-ready']
        return node


def inspect():
    revision = git('rev-parse', 'HEAD').decode().strip()
    git('merge-base', '--is-ancestor', CODE, revision)
    assert git('rev-parse', CODE + '^').decode().strip() == BASE
    assert sorted(git('diff', '--name-only', BASE, CODE).decode().splitlines()) == sorted([TEST, '.agent/evidence/123/author4-checkpoint-preparation.json'])
    refs = []
    for path, digest in PINS.items():
        raw = (ROOT / path).read_bytes()
        assert sha(raw) == digest and raw == historical(CODE, path)
        if path != TEST: assert raw == historical(BASE, path)
        metadata = git('ls-tree', CODE, '--', path).split(b'\t')[0].decode().split()
        assert metadata[0] in ('100644', '100755') and metadata[1] == 'blob'
        assert bool((ROOT / path).lstat().st_mode & 0o111) == (metadata[0] == '100755')
        refs.append(dict(path=path, revision=CODE, sha256=digest, git_mode=metadata[0], git_blob=metadata[2]))
        if path.endswith('.py'): compile(raw, str(ROOT / path), 'exec')
    prior_raw = historical(BASE, TEST); new_raw = (ROOT / TEST).read_bytes()
    assert sha(prior_raw) == '9bafd83bb18933bf103930d461fe681e42804f45ec7cdd065d74a7ffb5c75d00'
    old = ast.parse(prior_raw); new = ast.parse(new_raw)
    old_cls, old_init = constructor(old); new_cls, new_init = constructor(new)
    normalized = copy.deepcopy(new); normalized_cls, normalized_init = constructor(normalized)
    normalized_cls.body[normalized_cls.body.index(normalized_init)] = copy.deepcopy(old_init)
    assert dump(normalized) == dump(old), 'Only ControlsFixture.__init__ may change anywhere in module AST'
    def requirements(node):
        return [dump(n) for n in sorted(ast.walk(node), key=lambda x: getattr(x, 'lineno', 0))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'require']
    old_require, new_require = requirements(old_init), requirements(new_init)
    assert len(old_require) == 7 and len(new_require) == 16
    assert not (collections.Counter(old_require) - collections.Counter(new_require))
    assert [n for n in new_require if n in old_require] == old_require, 'All original assertion ASTs/order remain exact'
    init_text = ast.get_source_segment(new_raw.decode(), new_init)
    for snippet in ("self.ambient_source=seed.ambient_source", "self.packet_base=seed.packet_base", "self.fixture_source_path=seed.fixture_source_path",
        "target.open('xb')", "target.chmod(0o644)", "self.packet_base=self.commit('SYNTHETIC private UTF8 source baseline F0')",
        "self.source=self.commit('SYNTHETIC private meaningful UTF8 source candidate F1')", "self.fixture_source_path='tools/zz_wa123_synthetic_candidate.txt'"):
        assert snippet in init_text
    inputs = next(n.value for n in ast.walk(new_init) if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Attribute) and t.attr == 'inputs' for t in n.targets))
    assert isinstance(inputs, ast.IfExp) and dump(inputs.body) == dump(ast.parse('copy.deepcopy(seed.inputs)', mode='eval').body)
    sources = next(k.value for k in inputs.orelse.keywords if k.arg == 'source')
    assert dump(sources) == dump(ast.parse("['tools/workflow_assurance.py',self.fixture_source_path]", mode='eval').body)
    fresh = next(n for n in new_init.body if isinstance(n, ast.If) and isinstance(n.test, ast.BoolOp))
    profile = next(n for n in fresh.orelse if isinstance(n, ast.If) and isinstance(n.test, ast.Name) and n.test.id == 'source_profile')
    f0 = next(n for n in fresh.orelse if isinstance(n, ast.Assign) and any(isinstance(t, ast.Attribute) and t.attr == 'packet_base' for t in n.targets))
    f1 = next(n for n in fresh.orelse if isinstance(n, ast.Assign) and any(isinstance(t, ast.Attribute) and t.attr == 'source' for t in n.targets) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == 'commit')
    assert f0.lineno < profile.lineno < f1.lineno
    original = ast.parse(historical(PRESERVED, TEST)); inherited = definitions(original); current = definitions(new)
    assert len(inherited) == 74 and all(current[k] == v for k, v in inherited.items() if k != 'main')
    main = next(n for n in new.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    assert dump(InheritedMain().visit(copy.deepcopy(main))) == inherited['main']
    old_inv, new_inv = inventories(original), inventories(new)
    assert all(new_inv[k] == v for k, v in old_inv.items())
    labels = sum((old_inv[k] for k in ('CASES', 'AGF_CASES', 'RECEIPT_CASES', 'LANE_CASES', 'FAILURE_CASES')), ())
    assert len(labels) == len(set(labels)) == 46 and new_inv['CONTROL_CASES'] == ('ci-candidate-bound', 'ci-blocker-rejected')
    source_original = definitions(ast.parse(historical(SOURCE55, 'tools/workflow_assurance.py')))
    source_current = definitions(ast.parse((ROOT / 'tools/workflow_assurance.py').read_bytes()))
    assert len(source_original) == 55 and all(source_current[k] == v for k, v in source_original.items())
    installed = [r for r in git('ls-tree', '-rz', CODE, '--', '.nizam').split(b'\0') if r]
    modes = []
    assert len(installed) == 239 and git('ls-tree', '-rz', BASE, '--', '.nizam') == git('ls-tree', '-rz', CODE, '--', '.nizam')
    for row in installed:
        header, name = row.split(b'\t'); mode, kind, blob = header.decode().split(); path = ROOT / os.fsdecode(name)
        assert kind == 'blob' and mode in ('100644', '100755') and path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1
        assert path.read_bytes() == git('cat-file', 'blob', blob) and bool(path.stat().st_mode & 0o111) == (mode == '100755')
        modes.append((os.fsdecode(name), path.lstat().st_mode))
    authority = json.loads(historical(BASE, '.agent/evidence/123/root-fixture-recovery4-authority.json'))
    assert authority['decision'].startswith('Authorize ONE additional constructor-only acceptance author revision4')
    state = json.loads((ROOT / '.agent/run_state.json').read_bytes())
    return dict(static_only=True, formal_gate=False, behavior_executed=False, exercised_revision=revision,
        target_checkpoint=CODE, parent_packet_base=BASE, preparation_release=PREPARATION, exact_input_refs=refs,
        constructor_original_require_calls_preserved=7, constructor_additional_require_calls=9,
        outside_constructor_module_AST_exact=True, C_V_and_defects_and_observer_AST_exact=True,
        inherited_test_definitions=74, inherited_source_definitions=55, inherited_cases=46, default_cases=48,
        installed_regular_files=239, installed_full_modes_sha256=sha(json.dumps(modes,separators=(',', ':')).encode()),
        observed_counters={k:{field:state['circuit_breaker'][k][field] for field in ('attempts','limit','status') if field in state['circuit_breaker'][k]}
            for k in ('123-author','123-author-static','123-provisional-review','123-source')},
        limitation='Static structural proof only; actual F0/F1 construction, source-contract/seed/carried controls and binary two-parent engineering matrix remain unexecuted by this helper.')


def alarm(_signum, _frame): raise TimeoutError('Static4 whole-operation bound120s exceeded')


def main():
    assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
    signal.signal(signal.SIGALRM, alarm); signal.alarm(120)
    before = snapshot()
    try: result = inspect()
    finally:
        after = snapshot()
        print(json.dumps(dict(preservation_equal=after==before, tracked_inputs=len(before),
            snapshot_sha256=sha(json.dumps(before,separators=(',', ':')).encode()),
            full_modes_and_links_and_bytes=True, owned_coordination_unchanged=after==before),sort_keys=True))
        assert after == before, 'Current full tracked inputs including installed/coordination/history changed'
        signal.alarm(0)
    result['actual_exit'] = 0
    print(json.dumps(result,sort_keys=True))


if __name__ == '__main__': main()
