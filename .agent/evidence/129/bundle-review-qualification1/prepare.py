import ast, hashlib, importlib.util, json
from pathlib import Path

root = Path.cwd()
runner = root / 'tools/test_runtime_session.py'
raw = runner.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '1cb7c33f15454fe6c8babf2541b7c24fdfa794c39b2f8ce70a34569c9ba12f27'
spec = importlib.util.spec_from_file_location('proposed129', runner)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
out = root / '.agent/evidence/129/bundle-review-qualification1'
session = module.LiveSession(out / 'fixtures')
session.record = {'owner': module.OWNER, 'generation': {'counter': 1, 'nonce': '0'*32}, 'lease_epoch': 0}
tree = ast.parse(raw)
reports = ast.literal_eval(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'live_printing').body[0].value)
rows = []
selections = [(f'report{n}', 'evaluate', report, False) for n, (report, limits) in enumerate(reports)]
selections += [(kind, kind, None, True) for kind in ('evaluate', 'load_source', 'compile_source')]
for label, kind, report, active in selections:
    request, progress, cleanup, invoked, witness, names = module.condition_fixture(session, kind, report)
    path = out / 'fixtures' / (label + '.lisp')
    path.write_text(request['payload']['expression'])
    rows.append(dict(path=str(path), kind=kind, active=active, condition=names[0], frame=names[1], restart=names[2], progress=str(progress), cleanup=str(cleanup), invoked=str(invoked), witness=witness, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
def string(value): return json.dumps(value, ensure_ascii=True)
manifest = '(\n' + '\n'.join(' (' + ' '.join(':'+key+' '+ ('t' if value is True else 'nil' if value is False else string(value)) for key,value in row.items() if key != 'sha256') + ')' for row in rows) + '\n)\n'
(out/'manifest.lisp').write_text(manifest)
(out/'manifest.json').write_text(json.dumps({'runner_sha256':hashlib.sha256(raw).hexdigest(),'source_revision':'c573e2c6327a53160e8cb07d9a527b2e08de81b5','sources':rows},indent=2)+'\n')
print('PREPARED exact11 generated fixture sources; no native or controller execution')
