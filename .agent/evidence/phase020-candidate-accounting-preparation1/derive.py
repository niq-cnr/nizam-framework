"""Static string-template byte proof only; never imports or runs runtime/test code."""
import ast,gzip,hashlib,json,subprocess
from pathlib import Path
AREA=Path('.agent/evidence/phase020-candidate-accounting-preparation1')
BASE='7278cd902ec0209766e9e06f1f72587ff2a1a45c'
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(r,p):return subprocess.check_output(['git','show',r+':'+p])
def pin(r,p):return {'revision':r,'path':p,'sha256':sha(blob(r,p))}
def expr(node,env):
 if isinstance(node,ast.Constant):return node.value
 if isinstance(node,ast.Name):return env[node.id]
 if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):return expr(node.left,env)+expr(node.right,env)
 if isinstance(node,ast.BoolOp) and isinstance(node.op,ast.Or):
  for v in node.values:
   result=expr(v,env)
   if result:return result
  return result
 if isinstance(node,ast.IfExp):return expr(node.body if expr(node.test,env) else node.orelse,env)
 if isinstance(node,ast.Compare) and len(node.ops)==1 and isinstance(node.ops[0],ast.IsNot):return expr(node.left,env) is not expr(node.comparators[0],env)
 if isinstance(node,ast.Call):
  args=[expr(v,env) for v in node.args];assert not node.keywords
  if isinstance(node.func,ast.Name) and node.func.id=='str':return str(*args)
  if isinstance(node.func,ast.Name) and node.func.id=='lisp_write':return write_literal(*args)
  if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='json' and node.func.attr=='dumps':return json.dumps(*args)
 raise ValueError('Unsupported static template expression: '+ast.dump(node))
def assignment(fn,name):
 return next(n.value for n in ast.walk(fn) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
WRITE=None
def write_literal(path,value):return expr(WRITE,{'path':path,'value':value})
def main():
 global WRITE
 old=json.loads(Path('.agent/evidence/phase020-accounting-preparation2/ledger.json').read_bytes());proofs=[]
 for d in old['derivations']:
  if not d['id'].startswith('qualified-fixtures'):proofs.append(dict(d,resolution='Exact actual logged argument/input SHA chain independently observed in method2 review; pinned full chain retained by reference.'));continue
  template=d['template_source'];raw=blob(template['revision'],template['path']);assert sha(raw)==template['sha256'];tree=ast.parse(raw)
  functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)};WRITE=functions['lisp_write'].body[0].value
  body=assignment(functions['condition_fixture'],'body');reports=ast.literal_eval(functions['live_printing'].body[0].value)
  manifest=json.loads(blob(BASE,d['manifest']['path']));n=1 if d['id'].endswith('1') else 2;prefix=d['manifest']['path'].rsplit('/',1)[0]+'/'
  rendered=[]
  for output in d['outputs']:
   i=int(output['manifest_pointer'].rsplit('/',1)[1]);row=manifest['sources'][i];assert row==output['exact_parameters']
   label=Path(row['path']).stem;report=reports[int(label[6:])][0] if label.startswith('report') else ('(sleep 0.3) (write-string "finite-report-complete" stream)' if label.startswith('finite') else None)
   restart_report='(lambda (out) (declare (ignore out)) (loop (sleep 0.01)))' if label=='restart' else None
   env={**row,'report':report,'restart_report':restart_report}
   if n==2:
    cap=functions['capture_fixture'];env['prefix']=expr(assignment(cap,'prefix'),env);env['rendering']=expr(assignment(cap,'rendering'),env)
    env['report']=expr(assignment(cap,'wrapped_report'),env)
    env['restart_report']=None if restart_report is None else expr(next(z.value for z in ast.walk(cap) if isinstance(z,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='wrapped_restart' for t in z.targets) and not isinstance(z.value,ast.Constant)),{**env,'restart_report':restart_report})
   expected=expr(body,env)
   if row['kind']=='compile_source':expected='(eval-when (:compile-toplevel :load-toplevel :execute) '+expected+')'
   if n==2:
    original=write_literal(row['cleanup'],row['witness']);assert expected.count(original)==1
    env['original']=original;ending=expr(assignment(functions['capture_fixture'],'ending'),env);expected=expected.replace(original,ending)
   actual=blob(BASE,output['path']);assert expected.encode()==actual,output['path']
   rendered.append({'path':output['path'],'sha256':sha(actual),'parameters_pointer':output['manifest_pointer'],'method':'Static evaluation of pinned AST string concatenation/JSON literals only; no test function import/call','nonce':row['condition'].rsplit('-',1)[1],'callback_nonce':row.get('callback','').rsplit('-',1)[-1] if n==2 else None})
  rows=manifest['sources']
  def scalar(v):return 't' if v is True else 'nil' if v is False else json.dumps(v,ensure_ascii=True)
  excluded={'sha256'} if n==1 else {'limits','sha256'}
  expected='(\n'+'\n'.join(' ('+' '.join(':'+k+' '+scalar(v) for k,v in row.items() if k not in excluded)+')' for row in rows)+'\n)\n'
  assert expected.encode()==blob(BASE,prefix+'manifest.lisp')
  constructor=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='LiveSession')
  state_dict=next(c.args[0] for c in ast.walk(constructor) if isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and isinstance(c.func.value,ast.Name) and c.func.value.id=='json' and c.func.attr=='dumps')
  state=json.dumps(ast.literal_eval(state_dict)).encode();assert state==blob(BASE,prefix+'fixtures/run_state.json')
  observations=[]
  for row in rows:
   for key in ('progress','cleanup','callback','ended'):
    if key not in row:continue
    path=prefix+'fixtures/'+Path(row[key]).name
    found=subprocess.run(['git','show',BASE+':'+path],capture_output=True)
    if found.returncode:continue
    data=found.stdout
    if key in ('progress','cleanup'):assert data==(row['witness']+'\n').encode()
    else:
     text=data.decode().splitlines();assert text and all(v.lstrip('-').isdigit() for v in text[0].split())
     if key=='callback':assert text[1] in ('6/32/T','6/32/NIL')
    observations.append({'path':path,'sha256':sha(data),'source_output':key,'manifest_pointer':'/sources/'+str(rows.index(row)),'disposition':'derived runtime observation; actual native qualification frame and canonical generator semantics retained'})
  proofs.append({'id':d['id'],'generator':d['generator'],'template_source':template,'manifest':d['manifest'],'actual_native_frame':d['actual_native_frame'],'actual_native_pid':d['actual_native_pid'],'actual_native_exit':d['actual_native_exit'],'outputs':rendered,'manifest_lisp':pin(BASE,prefix+'manifest.lisp'),'fixture_state':pin(BASE,prefix+'fixtures/run_state.json'),'runtime_observations':observations,'resolution':'Exact static byte derivation verified; no preparation PID invented; actual native frame binds the qualified bytes and original stream hashes. Canonical runner/prepare controls charged once; output copies proposed derived observation for independent closure review.'})
 (AREA/'derivations.json').write_text(json.dumps({'kind':'Exact static derived-copy byte provenance; independent closure review still required','base':BASE,'proofs':proofs},indent=2)+'\n')
 print('PASS exact static fixture/template byte derivation; no runtime, test, controller or line measurement.')
if __name__=='__main__':main()
