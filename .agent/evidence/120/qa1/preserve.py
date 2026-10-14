"""Independent120 preservation check anchored to merged feature119."""
import ast
import importlib.util
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[4]
base='92fecd8d376964f5e3dd7e34bc201035acfe8bc6'
def old(p): return subprocess.check_output(['git','show',base+':'+p],cwd=root).decode()
def nodes(text): return ast.parse(text)
def funcs(tree): return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
p='tools/workflow_assurance.py'; a=nodes(old(p)); b=nodes((root/p).read_text()); old_functions=funcs(a); now=funcs(b)
assert all(now[k]==v for k,v in old_functions.items()),'inherited source/API/CLI AST changed'
b.body=[n for n in b.body if not(isinstance(n,ast.FunctionDef) and n.name not in old_functions)]
assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),'inherited module changed'
p='tools/test_workflow_assurance.py'; a=funcs(nodes(old(p))); b=funcs(nodes((root/p).read_text()))
assert all(b[k]==v for k,v in a.items() if k!='main'),'inherited test function changed'
spec=importlib.util.spec_from_file_location('qa120_inventory',root/p); module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert len(module.CASES)==20 and len(module.AGF_CASES)==6 and len(module.RECEIPT_CASES)==11
assert not set(module.RECEIPT_CASES)&set(module.CASES+module.AGF_CASES)
assert not subprocess.check_output(['git','diff','--name-only',base,'HEAD','--','schema','.nizam','.github'],cwd=root).strip(),'schema/payload/workflow change'
print('PASS inherited source module/API/CLI AST and old acceptance functions preserved; disjoint20+6+11 inventory; schemas/installed payload/workflows unchanged')
