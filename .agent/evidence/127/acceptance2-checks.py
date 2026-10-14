"""Focused metadata correction checks; no production execution or semantic-red claim."""
import ast, copy, hashlib, json, pathlib, subprocess
import jsonschema
R = pathlib.Path(__file__).resolve().parents[3]
OLD = '3040ff032d2e5a0f1b0a5669447ce3268402e5fc'
def blob(rev, path): return subprocess.check_output(['git','show',f'{rev}:{path}'],cwd=R)
def read(path): return json.loads((R/path).read_text())
p = '.agent/evidence/127/acceptance1-obligations.json'
prior = json.loads(blob(OLD,p)); current = read(p)
expected = copy.deepcopy(prior)
expected['fourteen_commands'][6:9] = [prior['fourteen_commands'][7],prior['fourteen_commands'][8],prior['fourteen_commands'][6]]
assert current == expected, 'only approved positions7-9 may change'
tree = ast.parse((R/'tools/test_runtime_session.py').read_text())
checks = ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHECKS' for t in n.targets)))
fn = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fixture_claim')
select = [n for n in fn.body if (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='expected' for t in n.targets)) or (isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='expected')]
ns = {'CHECKS':checks}; exec(compile(ast.fix_missing_locations(ast.Module(body=select,type_ignores=[])),'sealed-fixture-claim-expectation','exec'),ns)
assert current['fourteen_commands'] == ['PYTHONDONTWRITEBYTECODE=1 python3 '+' '.join(x) for x in ns['expected']]
assert len(ns['expected']) == 14
print('PASS exact projection-only positions7-9 correction and equality to all14 unchanged runner scheduling expectations')
for path,sha in [('tools/test_runtime_session.py','3628f1b2b833a0f504cced79252391ff213bd75197dd2d5261494fbb646eb12e'),('.agent/evidence/127/runtime-api127.json','f8052878dc2566dde5ec35911b485a874e187df57df8f10ade508505afd544b6')]:
 data=(R/path).read_bytes(); assert data==blob(OLD,path); assert hashlib.sha256(data).hexdigest()==sha
print('PASS exact original runner and API bytes/SHA256')
seal = read('.agent/evidence/127/acceptance1-test-seal.json'); count=0
def verify(obj):
 global count
 if isinstance(obj,dict):
  if {'path','revision','git_blob','sha256'} <= obj.keys():
   data=blob(obj['revision'],obj['path']); assert hashlib.sha256(data).hexdigest()==obj['sha256']; assert subprocess.check_output(['git','rev-parse',obj['revision']+':'+obj['path']],cwd=R,text=True).strip()==obj['git_blob']; count+=1
  for v in obj.values(): verify(v)
 elif isinstance(obj,list):
  for v in obj: verify(v)
verify(seal)
for path in ['.agent/evidence/127/acceptance1-test-seal.json','.agent/evidence/127/acceptance1-handoff.json']:
 assert (R/path).read_bytes()==blob(OLD,path)
print(f'PASS all{count} original immutable pins, prior seal/handoff and reused actual control receipts remain verifiable')
contract=read('.agent/contracts/127.json'); assert contract['status']=='approved'
assert hashlib.sha256((R/'.agent/contracts/127.json').read_bytes()).hexdigest()=='b221434834b68dd0273a0bdd0f6f8c0988bee0165f9c31255f4e33b150191cb7'
schema=read('schema/contract.schema.json'); jsonschema.Draft202012Validator.check_schema(schema); jsonschema.validate(contract,schema)
print('PASS approved contract SHA and actual shipped contract-schema validation')
changed=subprocess.check_output(['git','diff','--name-only',OLD,'HEAD'],cwd=R,text=True).splitlines()
# Root review/dispatch ancestors are retained; the correction commit itself owns only the projection.
assert subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r','HEAD'],cwd=R,text=True).splitlines()==[p]
print('PASS correction commit changes only owned projection; no source/test/API/coordination edit')
