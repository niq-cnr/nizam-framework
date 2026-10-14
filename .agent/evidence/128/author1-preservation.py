#!/usr/bin/env python3
"""External historical AST and contract inventory anchors for feature128."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE = '88996ee9405f9467ff2debd6e3115b34d064019a'
CANDIDATE = '441567ef05c3eb68558c6aeb679aa94b0a1a3baa'
path = 'tools/test_runtime_session.py'
old = ast.parse(subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':'+path]))
raw = (ROOT/path).read_bytes(); new = ast.parse(raw)
dump = lambda node: ast.dump(node,include_attributes=False)
find = lambda tree: {node.name:node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
before, after = find(old), find(new)
preserved = []
for name,node in before.items():
    if name != 'main':
        assert dump(node) == dump(after[name]), name
        preserved.append(name)
main = copy.deepcopy(after['main'])
for node in ast.walk(main):
    if isinstance(node,ast.Call) and any(isinstance(arg,ast.Constant) and arg.value=='--check' for arg in node.args):
        choice=next(k for k in node.keywords if k.arg=='choices')
        assert ast.unparse(choice.value)=="(*CHECKS, 'core-ready')"
        choice.value=ast.Name(id='CHECKS',ctx=ast.Load())
main.body=[node for node in main.body if not (isinstance(node,ast.If) and ast.unparse(node.test)=="args.check == 'core-ready'")]
assert dump(main)==dump(before['main']), 'inherited dispatch after removing exact approved extension'
for key in ('CHECKS','CASES'):
    values=lambda tree:next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==key for t in n.targets))
    assert dump(values(old))==dump(values(new)), key
inventory=ast.literal_eval(next(n.value for n in new.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CORE_LEAVES' for t in n.targets)))
contract=json.loads((ROOT/'.agent/contracts/128.json').read_text())
assert [list(x) for x in inventory]==contract['leaf_argv'] and len(inventory)==14
for p in ('tools/runtime_session.py','tools/fixtures/runtime_session/stub_runtime.py','tools/fixtures_self_test.sh'):
    assert (ROOT/p).read_bytes()==subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':'+p]),p
print('PASS all',len(preserved),'inherited functions/classes AST unchanged; inherited main differs only choice and earlydispatch; CHECKS/CASES unchanged')
print('PASS exact14 externally anchored inventory; controller/stub/harness historical bytes unchanged')
print('RUNNER_SHA256',hashlib.sha256(raw).hexdigest())
print('RUNNER_GIT_OBJECT',subprocess.check_output(['git','-C',str(ROOT),'rev-parse',CANDIDATE+':'+path],text=True).strip())
