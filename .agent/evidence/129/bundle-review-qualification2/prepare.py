import ast, hashlib, importlib.util, json
from pathlib import Path
root = Path.cwd(); runner = root/'tools/test_runtime_session.py'
assert hashlib.sha256(runner.read_bytes()).hexdigest() == '3a9bc25eb29c5368be51aa47728d5c7ad4a4f4829716bfbd7c1f1a1dda4969bb'
spec = importlib.util.spec_from_file_location('proposed129',runner)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
out = root/'.agent/evidence/129/bundle-review-qualification2'
s = module.LiveSession(out/'fixtures')
s.record = {'owner':module.OWNER,'generation':{'counter':1,'nonce':'0'*32},'lease_epoch':0}
tree = ast.parse(runner.read_bytes())
reports = ast.literal_eval(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='live_printing').body[0].value)
selections = [(kind,kind,None,None,{},True,False) for kind in ('evaluate','load_source','compile_source')]
selections += [(f'report{n}','evaluate',report,None,limits,n==1,n==1) for n,(report,limits) in enumerate(reports)]
selections += [(f'finite{n}','evaluate','(sleep 0.3) (write-string "finite-report-complete" stream)',None,{'output_bytes':2048,'timeout_seconds':seconds},True,True) for n,seconds in enumerate((.1,0))]
selections += [('restart','evaluate',None,'(lambda (out) (declare (ignore out)) (loop (sleep 0.01)))',{'output_bytes':2048,'timeout_seconds':.1},False,False)]
rows=[]
for label,kind,report,restart_report,limits,active,render in selections:
    fixture,callback,ended=module.capture_fixture(s,kind,report,restart_report,limits)
    request,progress,cleanup,invoked,witness,names=fixture
    path=out/'fixtures'/(label+'.lisp');path.write_text(request['payload']['expression'])
    rows.append(dict(label=label,path=str(path),kind=kind,active=active,render=render,condition=names[0],frame=names[1],restart=names[2],progress=str(progress),cleanup=str(cleanup),invoked=str(invoked),witness=witness,callback=str(callback),ended=str(ended),limits=limits,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
def lisp(value):return 't' if value is True else 'nil' if value is False else json.dumps(value)
manifest='(\n'+'\n'.join(' ('+' '.join(':'+k+' '+lisp(v) for k,v in row.items() if k not in ('limits','sha256'))+')' for row in rows)+'\n)\n'
(out/'manifest.lisp').write_text(manifest)
(out/'manifest.json').write_text(json.dumps({'candidate':'063a44f8dc326e7a8bb5667e660eb88e5ef2b4fc','sources':rows},indent=2)+'\n')
print('PREPARED changed14 sources;6 active including cycle and2 finite reporters; no native/controller execution')
