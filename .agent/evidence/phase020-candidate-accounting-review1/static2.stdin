"""Read-only JSON/hash/AST/Git metadata review; no accounting or product main."""
import ast,collections,functools,gzip,hashlib,json,subprocess
from pathlib import Path
A=Path('.agent/evidence/phase020-candidate-accounting-preparation1')
sha=lambda b:hashlib.sha256(b).hexdigest()
@functools.lru_cache(None)
def blob(r,p):return subprocess.check_output(['git','show',r+':'+p])
def ref(r):
 b=blob(r['revision'],r['path']);assert sha(b)==r['sha256'],r;return b
def decoded(b):return json.loads(gzip.decompress(b) if b[:2]==b'\x1f\x8b' else b)
def ptr(v,p):
 for k in p.strip('/').split('/') if p else []:v=v[int(k)] if isinstance(v,list) else v[k]
 return v
c=json.loads((A/'closure.json').read_bytes());ds=json.loads((A/'derivations.json').read_bytes());events=decoded((A/'events.json.gz').read_bytes());merges=decoded((A/'merges.json.gz').read_bytes());shared=decoded((A/'shared.json.gz').read_bytes())
for p,h in json.loads((A/'index.json').read_bytes()).items():assert sha(Path(p).read_bytes())==h,p
for row in c['generated_metadata']['generated_outputs']:
 b=Path(row['path']).read_bytes();assert sha(b)==row['sha256'] and sha(gzip.decompress(b))==row['decoded_sha256']
refs={}
def collect(v):
 if isinstance(v,dict):
  if {'revision','path','sha256'}<=v.keys():refs[(v['revision'],v['path'],v['sha256'])]=v
  for z in v.values():collect(z)
 elif isinstance(v,list):
  for z in v:collect(z)
collect(c);collect(ds)
for r in refs.values():ref(r)
for name in ('prepare.py','derive.py','adapter.py'):ast.parse((A/name).read_bytes())
f=json.loads((A/'static2.execution.json').read_bytes());assert f['actual_exit']==0 and f['child_pid']==193015
for s in ('stdin','stdout','stderr'):assert sha((A/Path(f[s]['path']).name).read_bytes())==f[s]['sha256']
assert json.loads(Path('.agent/validator/020-accounting-method2.json').read_bytes())['final_verdict']['approved']
assert c['endpoint'] is None and c['heads'] is None
assert set(c['preparation_heads'])==set(events['preparation_heads'])
actual=set(subprocess.check_output(['git','rev-list',*c['preparation_heads'],'^'+c['history_floor']]).decode().split())
assert actual=={r['commit'] for r in events['ancestry']}
assert {'d8415499577f9f23ff93a9475ffa409b1028379e','93f8d98df5315f595f72529af866b003b2a81f30','a3dffed6e895ae6a3e039f36d5d2f95e6bbcfe24'}<=actual
for r in events['ancestry']:
 assert subprocess.check_output(['git','show','-s','--format=%P',r['commit']]).decode().split()==r['parents']
for m in merges:
 if 'reuse_existing_capture' in m:
  original=ptr(decoded(ref(m['reuse_existing_capture'])),m['reuse_existing_capture']['decoded_pointer']);assert all(m[k]==v for k,v in original.items())
 if 'canonical' in m:
  original=ptr(decoded(ref(m['canonical'])),m['canonical']['pointer']);assert original['actual_exit']==0 and original['child_pid']==m['original_actual_child_pid'] and original['stdout']['bytes']==original['stderr']['bytes']==0
 else:
  assert m['actual_exit']==0 and m['child_pid']>0
  for s in ('stdout','stderr'):assert sha(m[s]['text'].encode())==m[s]['sha256'] and len(m[s]['text'].encode())==m[s]['bytes']
  if m['commit']!='69e1903da50487cf09d27022bb3450329aa685be':assert not m['stdout']['bytes'] and not m['stderr']['bytes']
nonempty=next(m for m in merges if m['commit']=='69e1903da50487cf09d27022bb3450329aa685be');assert nonempty['stdout']['bytes']>0
assert all(p.startswith('.agent/evidence/123/') for p in next(x for x in c['merge_decisions'] if x['commit']==nonempty['commit'])['paths'])
# Raw exclusion checks use observed JSON shapes, never filename alone.
raw_issues=[];kinds=collections.Counter()
for e in c['event_decisions']:
 if e['disposition']!='derived-observation':continue
 r,p=e['key'].split(':',1);b=blob(r,p);assert sha(b)==e['after_sha256'];proof=e['proof'];kind=proof.get('kind','outer-capture-stream');kinds[kind]+=1
 try:
  if kind=='actual-machine-execution-frame':
   v=decoded(b);assert isinstance(v['argv'],list) and v.get('child_pid',v.get('pid',0))>0 and isinstance(v['actual_exit'],int)
  elif kind=='actual-start-frame':
   v=decoded(b);f=decoded(ref(proof['execution']));assert v.get('child_pid',v.get('pid'))==f.get('child_pid',f.get('pid')) and v['argv']==f['argv'] and v['exercised_revision']==f['exercised_revision']
  elif kind.startswith('actual-frame-bound-'):
   f=decoded(ref(proof['frame']));s=ptr(f,proof['source_pointer']);assert sha(b)==s['sha256'] and len(b)==s['bytes'];assert f.get('child_pid',f.get('pid'))==proof['pid']
  elif kind=='exact-uniform-hash-index':
   v=decoded(b);v=v.get('files',v);assert isinstance(v,dict) and v
   sources={x['path']:x for x in proof['sources']}
   for path,h in v.items():
    source=sources.get(path) or sources.get(str(Path(p).parent/path));assert source;data=ref(source);assert sha(data)==(h if isinstance(h,str) else h['sha256'])
    if isinstance(h,dict):assert len(data)==h['bytes']
  elif kind=='actual-preservation-bytes':
   s=ptr(decoded(ref(proof['summary'])),proof['source_pointer']);assert sha(b)==s['sha256'] and sha(gzip.decompress(b))==s['inventory_sha256']
  elif kind=='actual-capture-sentinel':assert sha(b)==ptr(decoded(ref(proof['inventory'])),proof['source_pointer'])['sha256']
  elif kind=='capture-preservation-summary':
   v=decoded(b);f=decoded(ref(proof['execution']));assert v['actual_exit']==f['actual_exit'] and v['capture_driver_sha256']==proof['generator']['sha256']
  elif kind=='outer-capture-stream':
   if 'output_sha256' in proof:assert sha(b)==proof['output_sha256']
   else:
    stream=ptr(decoded(ref(proof['frame'])),proof['pointer']);assert sha(b)==stream['sha256'] and len(b)==stream['bytes']
 except (AssertionError,KeyError,TypeError) as ex:raw_issues.append({'event':e['key'],'kind':kind,'error':type(ex).__name__})
# Copy proposals have exact source identity plus recorded retention/input lineage.
copy_issues=[]
for e in c['event_decisions']:
 if e['disposition']!='proven-copy':continue
 r,p=e['key'].split(':',1);cr,cp=e['canonical_event'].split(':',1);assert blob(r,p)==blob(cr,cp)
 proof=e['proof']
 if 'actual_input_identity' in proof:
  f=decoded(ref(proof['frame']));identity=proof['actual_input_identity'];assert f['stdin']['path']==identity[0] and f['stdin']['sha256']==identity[1] and f['child_pid']==identity[2]
 elif 'actual_frame' in proof:
  f=decoded(ref(proof['actual_frame']));assert f['stdin']['sha256']==e['after_sha256']
 else:
  state=decoded(ref(proof['Root_state']));assert state['history']
# Mixed probe is sealed canonical source with one authorized metadata replacement.
m=c['mixed_close_probe_copy'];old=ref(m['canonical']);new=ref(m['derived']);binding=decoded(ref(m['binding']));expected=old
for v in binding['bindings'].values():assert expected.count(v['old'].encode())==1;expected=expected.replace(v['old'].encode(),v['new'].encode())
assert expected==new
release=json.loads(Path('.agent/evidence/129/source-release3.json').read_bytes());assert release['sealed_close_probe']['sha256']==sha(old) and 'ONLY derive' in release['sealed_close_probe']['candidate_binding']
print(json.dumps({'metadata_check':'PASS','reviewed_closure_sha256':sha((A/'closure.json').read_bytes()),'method_approval_preserved':True,'raw_relational_issues':raw_issues,'copy_relational_issues':copy_issues,'mixed_probe_exact_authorized_substitution':True,'merge69_nonempty_foreign018_preserved':True,'raw_proof_kinds':dict(kinds),'measurement_or_product_main_executed':False},sort_keys=True))
