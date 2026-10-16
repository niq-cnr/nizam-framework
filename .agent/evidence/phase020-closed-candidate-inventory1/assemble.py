"""Apply reviewed attribution to adapter-shaped metadata. Never imports a count engine."""
import argparse,ast,copy,gzip,hashlib,json,re,subprocess
from pathlib import Path
AREA=Path('.agent/evidence/phase020-closed-candidate-inventory1')
ROOT='a9e5a25a2b0d150c4300b58c4f0aa2fab690de8c'
OLD='ce872ff7c5486badd43004f5257f087d21eb0bb3'
OLD_AREA='.agent/evidence/phase020-candidate-accounting-preparation1/'
DELTA_AREA='.agent/evidence/phase020-candidate-accounting-preparation2/'
FLOOR='a63cf0c513ad645a9771a69af00dca5d0a45474d'
EXTRA=['0ae08da6a153e589a7dbcac65223d1fa9d2449a4','7724438dd1fe429811997f4e195ba166f877620e','50f12726fc748a7fe40aab6a9a5cc7864657276b','00cddc71fffca59fbc4c70a6a5e4cc47e81bf660','777a801921fa565e4d0c2c224f7b5dec6a21b381']
BLOBS={}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(*a):return subprocess.check_output(['git',*a])
def blob(rev,path):
 key=(rev,path)
 if key not in BLOBS:
  p=subprocess.run(['git','show',rev+':'+path],capture_output=True);assert p.returncode in (0,128);BLOBS[key]=p.stdout if p.returncode==0 else None
 return BLOBS[key]
def ref(rev,path,pointer=None):
 raw=blob(rev,path);assert raw is not None
 r={'revision':rev,'path':path,'sha256':sha(raw)}
 if pointer is not None:r['pointer']=pointer
 return r
def load(rev,path):
 raw=blob(rev,path);return json.loads(gzip.decompress(raw) if raw[:2]==b'\x1f\x8b' else raw)
def patch(parent,rev,path):return git('-c','color.ui=false','diff','--no-ext-diff','--no-textconv','--no-renames','--unified=0',parent,rev,'--',path).decode()
def signed(text):return [s for s in text.splitlines() if s[:1] in ('+','-') and not s.startswith(('+++ ','--- '))]
def split(text,owners):
 lines=signed(text);assert len(lines)==len(owners)
 return [{'signed_line_sha256':sha(line.encode()),'owner':owner} for line,owner in zip(lines,owners)]
def own(path):
 return path.startswith(('.agent/evidence/129/','.agent/evidence/phase020-','.agent/evidence/handover-2026-10-16/')) or bool(re.fullmatch(r'\.agent/(?:contracts|qa|validator)/(?:129|020-|phase020)[^/]*\.json',path)) or path in ('.agent/product_spec_020.md','.agent/feature_list_020.json','docs/planning/phase_020.yaml','docs/planning/HANDOVER-2026-10-16.md')
def category(path):
 return 'independent_tests' if path.endswith('/probe.py') else 'process'
def object_hashes(oids,known):
 missing=sorted(set(oids)-set(known));p=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 for start in range(0,len(missing),32):
  batch=missing[start:start+32];p.stdin.write(('\n'.join(batch)+'\n').encode());p.stdin.flush()
  for oid in batch:
   header=p.stdout.readline().split();assert header[:2]==[oid.encode(),b'blob'];remaining=int(header[2]);digest=hashlib.sha256()
   while remaining:
    raw=p.stdout.read(min(remaining,65536));assert raw;digest.update(raw);remaining-=len(raw)
   assert p.stdout.read(1)==b'\n';known[oid]=digest.hexdigest()
 p.stdin.close();assert p.wait()==0 and not p.stderr.read();return known
def tail_events(commits):
 result=[]
 for rev,parents in commits:
  if len(parents)!=1:continue
  parent=parents[0];parts=git('diff-tree','--raw','--no-abbrev','--no-renames','-r','-z',parent,rev).split(b'\0');i=0
  while i<len(parts)-1:
   om,nm,bo,ao,status=parts[i].decode().split();path=parts[i+1].decode();i+=2
   result.append({'commit':rev,'parent':parent,'path':path,'before_oid':None if set(bo)=={'0'} else bo,'after_oid':None if set(ao)=={'0'} else ao,'status':status})
 return result

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--binding',type=Path);args=ap.parse_args()
 closure=load(OLD,OLD_AREA+'closure.json');oldmeta=load(OLD,OLD_AREA+'events.json.gz');delta=load(ROOT,DELTA_AREA+'delta.json');reviews=[ref(ROOT,'.agent/validator/020-accounting-method2.json'),ref(ROOT,'.agent/validator/020-candidate-accounting-closure1.json'),ref(ROOT,'.agent/validator/020-candidate-accounting-closure2.json')]
 assert sha(blob(OLD,OLD_AREA+'closure.json'))=='1299b2275f2f7479d31615bb7abbbc9b1c5457d33c6bcf8c6cfa910f487ed290'
 assert sha(blob(ROOT,DELTA_AREA+'delta.json'))=='dfe9108e61ac50ec5fd1d776cb3fd199c37fc91d014db10dd5ac96d4af475dc9'
 checkpoint=ROOT;heads=list(dict.fromkeys(closure['preparation_heads']+EXTRA+[ROOT]));endpoint=None;binding=None;extra_product=set()
 if args.binding:
  binding=json.loads(args.binding.read_bytes());release=load(binding['revision'],binding['path']);assert ref(binding['revision'],binding['path'])['sha256']==binding['sha256']
  checkpoint=release['endpoint'];heads=list(dict.fromkeys(release['heads']+[checkpoint]));endpoint=checkpoint;extra_product=set(release.get('retained_product_commits',[]))
  assert set(closure['preparation_heads']+EXTRA)<=set(heads),'Root binding must explicitly preserve minimum retained heads'
 parents_tail=[line.split() for line in git('rev-list','--reverse','--topo-order','--parents',*heads,*['^'+h for h in closure['preparation_heads']]).decode().splitlines()]
 tail=[(p[0],p[1:]) for p in parents_tail];ancestry=oldmeta['ancestry']+[{'commit':r,'parents':p,'tree':git('rev-parse',r+'^{tree}').decode().strip()} for r,p in tail]
 events=copy.deepcopy(oldmeta['events'])+tail_events(tail);bykey={e['commit']+':'+e['path']:e for e in events};assert len(bykey)==len(events)
 known={}
 for e in oldmeta['events']:
  for which in ('before','after'):
   if e.get(which+'_oid') and e.get(which+'_sha256'):known[e[which+'_oid']]=e[which+'_sha256']
 alloids={e[k] for e in events for k in ('before_oid','after_oid') if e.get(k)};known=object_hashes(alloids,known)
 for e in events:
  e['before_sha256']=known.get(e['before_oid']);e['after_sha256']=known.get(e['after_oid'])
 old_dec={e['key']:(i,e) for i,e in enumerate(closure['event_decisions'])};overrides={d['commit']+':'+d['path']:d for d in delta['joint_doc_overrides']};interfaces={d['commit']+':'+d['path']:d for d in delta['interface_overrides']};pending=[];rows=[]
 def bare(e):return {'key':e['commit']+':'+e['path'],'commit':e['commit'],'parent':e['parent'],'path':e['path'],'before_sha256':e['before_sha256'],'after_sha256':e['after_sha256']}
 for e in events:
  key=e['commit']+':'+e['path'];row=bare(e);path=e['path'];row.update(owner='foreign',feature=None,category='separate-unmeasured',disposition='foreign',proof={'old_union':ref(OLD,OLD_AREA+'events.json.gz'),'scope':'Retained otherphase or historicaljoint work; not a free global cost claim.'})
  if path=='.agent/run_state.json':row.update(owner='coordination',category='excluded',disposition='excluded-state',proof={'authority':ref(ROOT,'.agent/product_spec_020.md'),'rule':'Exact canonical state path excluded including narrative.'})
  elif key in overrides:row['proof']={'delta':ref(ROOT,DELTA_AREA+'delta.json'),'scope':'Exact original joint event/block; historicaljoint translates to foreign under approvedR1.'}
  elif key in old_dec:
   i,d=old_dec[key];row.update({k:d[k] for k in ('owner','feature','category','disposition')});row['proof']={'accepted_closure':ref(OLD,OLD_AREA+'closure.json','/event_decisions/'+str(i)),'approval':reviews[1]}
   if 'canonical_event' in d:row['canonical_event']=d['canonical_event']
   if 'split_lines' in d:row['split_lines']=d['split_lines']
   if row['disposition'].startswith('PENDING'):pending.append({'event':key,'reason':row['disposition']})
  elif own(path):row.update(owner='020',feature='129' if path.startswith('.agent/evidence/129/') or re.fullmatch(r'\.agent/(contracts|qa|validator)/129[^/]*\.json',path) else None,category=category(path),disposition='charge-authored',proof={'method':ref(ROOT,'.agent/evidence/phase020-accounting-preparation2/method.json'),'purpose':'Completed129 recovery/review/qualification or020accounting/handover authoring; physical raw proof handled below.'})
  elif e['commit'] in extra_product and path in ('tools/runtime_session.py','tools/sbcl_session_loop.lisp'):row.update(owner='020',feature='129',category='product',disposition='charge-authored',proof={'Root_binding':binding,'purpose':'Retained product draft; execution/approval not inferred.'})
  elif e['commit'] in ('719e91f68bd800cdae4a91c5ff739b24e4f2605c','1d37ac4785b59857572b120d82554a1b60fa404e') and path in ('docs/planning/HANDOVER.md','docs/planning/ROADMAP.md','docs/planning/manifest.json'):
   row.update(owner='020',feature=None,category='process',disposition='charge-authored',proof={'handover':ref(checkpoint,'.agent/evidence/handover-2026-10-16/receipt.json'),'purpose':'Actual current020handover authoring; cited historical work not transferred.'})
   if path=='docs/planning/manifest.json':
    before=json.loads(blob(e['parent'],path));after=json.loads(blob(e['commit'],path));oldnote=next(p['note'] for p in before['phases'] if p['id']=='021-receipt-input-maintenance');newnote=next(p['note'] for p in after['phases'] if p['id']=='021-receipt-input-maintenance')
    foreign={sign+'      "note": '+json.dumps(value)+',' for sign,value in (('-',oldnote),('+',newnote))};text=patch(e['parent'],e['commit'],path);row['split_lines']=split(text,['foreign' if s in foreign else '020' for s in signed(text)]);row['proof']['021_note']='Exact021note values remain133administration; timestamp/020note belongs020handover.'
  elif e['commit'] not in {a['commit'] for a in oldmeta['ancestry']}:
   row.update(disposition='PENDING-unknown-tail-ownership',proof={'event':key});pending.append({'event':key,'reason':row['disposition']})
  if key in interfaces:row.update(owner='020',feature='129',category='process',disposition='charge-authored',proof={'delta':ref(ROOT,DELTA_AREA+'delta.json'),'decision':'R3/A8 both actual interface events; no authorship or copy deduction inference.'})
  if row['disposition']=='charge-authored':row['reviewed_authored_override']={'method':ref(ROOT,'.agent/evidence/phase020-accounting-preparation2/method.json'),'scope':'Invalid/nonPython source and maintained evidence reports are charged by purpose; final inventory review binds this row.'}
  rows.append(row)
 # A5: copied semantic body once, new pin substitution process once at0697; Root retention is a copy.
 mixed_path='.agent/evidence/129/implementation3-close-probe1/probe.py';original=blob(checkpoint,'.agent/evidence/129/source2-close-diagnostic1/probe.py');derived=blob('0697bfe5e121543b2aa8ed8c8607d0c50e99b413',mixed_path);binding_data=load('0697bfe5e121543b2aa8ed8c8607d0c50e99b413','.agent/evidence/129/implementation3-close-probe1/binding.json');newpin=binding_data['bindings']['tools/runtime_session.py']['new'];oldpin=binding_data['bindings']['tools/runtime_session.py']['old'];assert original.replace(oldpin.encode(),newpin.encode())==derived
 for row in rows:
  if row['path']==mixed_path:
   row.update(proof={'A5':ref(ROOT,'.agent/validator/020-candidate-accounting-closure1.json','/approved_decisions/4'),'canonical_semantic_event':'93f8d98df5315f595f72529af866b003b2a81f30:.agent/evidence/129/source2-close-diagnostic1/probe.py'})
   if row['commit']=='0697bfe5e121543b2aa8ed8c8607d0c50e99b413':row.update(disposition='charge-authored',category='process',split_lines=split(patch(row['parent'],row['commit'],mixed_path),['020' if newpin in s else 'foreign' for s in signed(patch(row['parent'],row['commit'],mixed_path))]))
   else:row.update(disposition='proven-copy',canonical_event='0697bfe5e121543b2aa8ed8c8607d0c50e99b413:'+mixed_path)
 pending=[p for p in pending if not p['event'].endswith(':'+mixed_path) and p['event'] not in overrides]
 # Bind physical tail streams/frames and strict indexes by actual bytes, never evidence-directory exemption.
 owned=[r for r in rows if r['owner']=='020'];versions={};raw_proofs={}
 for row in owned:
  for rev,digest in ((row['commit'],row['after_sha256']),(row['parent'],row['before_sha256'])):
   if digest:versions.setdefault((row['path'],digest),(rev,blob(rev,row['path'])))
 for (path,digest),(rev,data) in versions.items():
  if not path.endswith('.execution.json'):continue
  value=json.loads(data)
  if 'argv' not in value or 'actual_exit' not in value:continue
  proof={'frame':ref(rev,path),'actual_exit':value['actual_exit'],'pid':value.get('child_pid',value.get('pid')),'limitation':'Missing historical PID remains missing.'};raw_proofs[(path,digest)]=proof;parent=str(Path(path).parent);stem=Path(path).name.removesuffix('.execution.json')
  for name,item in {**value.get('streams',{}),**{k:value[k] for k in ('stdin','stdout','stderr') if isinstance(value.get(k),dict)}}.items():
   if item.get('sha256'):
    p=parent+'/'+Path(item.get('path',stem+'.'+name+'.txt')).name
    if (p,item['sha256']) in versions and name!='stdin':raw_proofs[(p,item['sha256'])]=proof|{'stream':name}
  p=parent+'/'+stem+'.started.json'
  for (candidate,d),(r,b) in versions.items():
   if candidate==p:
    start=json.loads(b)
    if start.get('argv')==value['argv'] and start.get('child_pid',start.get('pid'))==value.get('child_pid',value.get('pid')):raw_proofs[(p,d)]=proof|{'kind':'start'}
 for (path,digest),(rev,data) in versions.items():
  if path.endswith('.capture-summary.json'):
   v=json.loads(data);parent=str(Path(path).parent);frame=parent+'/'+Path(path).name.replace('.capture-summary.json','.execution.json')
   if any(p==frame for p,d in raw_proofs):
    raw_proofs[(path,digest)]={'summary':ref(rev,path),'generator':ref(ROOT,'.agent/evidence/123/fresh-qa-capture1.py')}
    for side in ('before','after'):
     value=v.get(side,{})
     if 'path' in value and 'sha256' in value:
      p=parent+'/'+Path(value['path']).name
      if (p,value['sha256']) in versions:
       raw_proofs[(p,value['sha256'])]={'summary':ref(rev,path),'pointer':'/'+side};inv=json.loads(gzip.decompress(versions[(p,value['sha256'])][1]));sentinel=inv.get('sentinel',{})
       for (candidate,d),(r,b) in versions.items():
        if d==sentinel.get('sha256') and Path(candidate).name==Path(sentinel.get('path','')).name:raw_proofs[(candidate,d)]={'inventory':ref(rev,p),'pointer':'/sentinel'}
  if path.endswith('.json') and 'index' in Path(path).name:
   value=json.loads(data);table=value.get('files',value) if isinstance(value,dict) else None
   if isinstance(table,dict) and table:
    entries=[]
    for p,item in table.items():
     d=item if isinstance(item,str) else item.get('sha256') if isinstance(item,dict) and set(item)<=set(('sha256','bytes')) else None;p=p if p.startswith('.agent/') else str(Path(path).parent/p)
     if not isinstance(d,str) or not re.fullmatch('[0-9a-f]{64}',d) or (p,d) not in versions:break
     entries.append({'path':p,'sha256':d})
    else:raw_proofs[(path,digest)]={'kind':'strict mechanical index','index':ref(rev,path),'sources':entries}
 for row in rows:
  # Preserve reviewed old decisions exactly; newly bound raw tail is a current inventory proposal for exact review.
  if row['key'] not in old_dec and row['disposition']=='charge-authored':
   proof=raw_proofs.get((row['path'],row['after_sha256'] or row['before_sha256']))
   if proof:row.update(disposition='derived-observation',proof=proof)
 # Source-role retained captures copied into Root: canonical same-path event remains once.
 for source,prefix in [('0ae08da6a153e589a7dbcac65223d1fa9d2449a4','.agent/evidence/129/implementation3/environment-continuation1/'),('7724438dd1fe429811997f4e195ba166f877620e','.agent/evidence/129/source3-B2-diagnostic1/'),('bccaef268ef2f385a8b14acac47f5d61a0e41216','.agent/evidence/129/source3-semantic-diagnostics1/'),('00cddc71fffca59fbc4c70a6a5e4cc47e81bf660','.agent/evidence/129/source2-partial-frame-red1/'),('777a801921fa565e4d0c2c224f7b5dec6a21b381','.agent/evidence/129/source2-close-diagnostic1/')]:
  for row in rows:
   canonical=source+':'+row['path']
   if row['commit']!=source and row['path'].startswith(prefix) and canonical in bykey and row['after_sha256']==bykey[canonical]['after_sha256'] and row['before_sha256'] is None and row['disposition']=='charge-authored':row.update(disposition='proven-copy',canonical_event=canonical,proof={'canonical':ref(source,row['path']),'copy':ref(row['commit'],row['path']),'Root_retention':ref(checkpoint,'.agent/run_state.json'),'rule':'Exact independently captured source event and Root retention of same path/bytes; no general equality deduction.'})
 rowmap={r['key']:r for r in rows};oldmerges=load(OLD,OLD_AREA+'merges.json.gz');merge_proofs={m['commit']:{'reviewed':True,'proof':ref(OLD,OLD_AREA+'merges.json.gz','/'+str(i)),'approval':ref(ROOT,'.agent/validator/020-candidate-accounting-closure1.json','/approved_decisions/5'),'disposition':'foreign018-resolution' if m['commit']=='69e1903da50487cf09d27022bb3450329aa685be' else 'verified-automatic-or-exact-reuse'} for i,m in enumerate(oldmerges)}
 for rev,parents in tail:
  if len(parents)>1:merge_proofs[rev]={'reviewed':False,'commit':rev,'parents':parents,'tree':git('rev-parse',rev+'^{tree}').decode().strip(),'state':'PENDING-one-final-immutable-union-merge-proof-pass'}
 # Exact inherited baselines, no runtime/test import or execution.
 product_parent='3622fe0fc384a9d3292917e3f07b64aa2f4b2caa';runner_parent='d66ff730248dec4f086365be55eb4ad060a350c5';runner_path='tools/test_runtime_session.py';oldtree=ast.parse(blob(runner_parent,runner_path));newtree=ast.parse(blob(checkpoint,runner_path));get=lambda t:next(n.value for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='CORE_LEAVES' for x in n.targets));assert ast.dump(get(oldtree))==ast.dump(get(newtree));baselines={'tools/runtime_session.py':ref(product_parent,'tools/runtime_session.py'),'tools/sbcl_session_loop.lisp':{'revision':product_parent,'path':'tools/sbcl_session_loop.lisp','sha256':None,'absence_verified':blob(product_parent,'tools/sbcl_session_loop.lisp') is None},runner_path:ref(runner_parent,runner_path),'inherited_core14':{'baseline':ref(runner_parent,runner_path),'checkpoint':ref(checkpoint,runner_path),'selector_ast_sha256':sha(ast.dump(get(oldtree)).encode()),'unchanged':True}}
 # Snapshot assembly uses exact checkpoint bytes now; final Root END rebind/tail extension remains mandatory.
 snapshots=[];snapshot_pending=[];changed_paths=git('diff','--name-only','--no-renames','-z',FLOOR,checkpoint).split(b'\0')
 for name in changed_paths:
  if not name:continue
  path=name.decode();parent=FLOOR;before=blob(parent,path);after=blob(checkpoint,path);digest=sha(after) if after is not None else None;eligible=[r for r in rows if r['path']==path and r['after_sha256']==digest and r['disposition'] not in ('PENDING-unknown-tail-ownership',)];preferred=next((r for r in reversed(eligible) if r['commit']==checkpoint),eligible[-1] if eligible else None)
  snap={'key':'snapshot:'+path,'commit':checkpoint,'parent':parent,'path':path,'before_sha256':sha(before) if before is not None else None,'after_sha256':digest,'owner':'foreign','feature':None,'category':'separate-unmeasured','disposition':'foreign','proof':{'scope':'Retained inherited/otherphase or historicaljoint snapshot; explicit020event evidence required.'}}
  if preferred:
   snap.update({k:preferred[k] for k in ('owner','feature','category','disposition','proof')});snap['proof']={'checkpoint':checkpoint,'decision_event':preferred['key'],'decision_proof':preferred['proof']}
   if preferred.get('canonical_event'):
    canonical=rowmap[preferred['canonical_event']]
    if canonical['path']==path:snap.update(disposition=canonical['disposition'],category=canonical['category'],owner=canonical['owner'],feature=canonical['feature'],proof=snap['proof']|{'same_path_single_snapshot':'Canonical body represented once in this path; Root copy deduction applies to chronology, not an absent duplicate snapshot row.'})
    else:snap['canonical_event']=preferred['canonical_event']
   if snap['disposition']=='charge-authored':snap['reviewed_authored_override']=preferred.get('reviewed_authored_override',{'method':'Approved purpose-backed evidence source/report overlay'})
  if path in ('tools/runtime_session.py',runner_path):
   parent=product_parent if path=='tools/runtime_session.py' else runner_parent;before=blob(parent,path);snap.update(parent=parent,before_sha256=sha(before),owner='020',feature='129',category='product' if path=='tools/runtime_session.py' else 'independent_tests',disposition='charge-authored',proof={'inherited_baseline':baselines[path],'purpose':'Only129 delta after explicit inherited baseline; no pre129 controller/core14 charge.'})
   if before==after:snap.update(owner='foreign',category='inherited',disposition='foreign',proof={'inherited_baseline':baselines[path],'exact_bytes_equal':True})
  if path=='.agent/run_state.json':snap.update(owner='coordination',category='excluded',disposition='excluded-state',proof={'authority':ref(ROOT,'.agent/product_spec_020.md'),'exact_path':True})
  if path==mixed_path:
   snap.update(owner='020',feature='129',category='process',disposition='charge-authored',reviewed_authored_override={'A5':reviews[1]},proof={'A5':reviews[1],'canonical_semantic_body':'93f8d98df5315f595f72529af866b003b2a81f30:.agent/evidence/129/source2-close-diagnostic1/probe.py'},split_lines=split(patch(FLOOR,checkpoint,path),['020' if newpin in s else 'foreign' for s in signed(patch(FLOOR,checkpoint,path))]))
  if path in ('docs/planning/manifest.json','docs/planning/HANDOVER.md','docs/planning/ROADMAP.md'):
   snap.update(owner='020',feature=None,category='process',disposition='PENDING-shared-snapshot-line-provenance',proof={'required':'Bind actual020registration/handover blocks and retained joint/otherphase lines; no whole shared-file020assignment.'});snapshot_pending.append({'path':path,'reason':snap['disposition']})
  snapshots.append(snap)
 cfg={'kind':'Effective adapter-shaped current inventory; no numeric accounting','status':'PREPARATION-unbound-not-measurable','endpoint':endpoint,'heads':heads if endpoint else None,'known_preparation_heads':heads,'history_floor':FLOOR,'snapshot_checkpoint':checkpoint,'root_binding':binding,'commits':[a['commit'] for a in ancestry],'event_keys':list(bykey),'merge_proofs':merge_proofs,'chronological':rows,'snapshot':snapshots,'inherited_product_test_baseline_proofs':baselines,'inputs':{'method':ref(ROOT,'.agent/evidence/phase020-accounting-preparation2/method.json'),'original_closure':ref(OLD,OLD_AREA+'closure.json'),'delta':ref(ROOT,DELTA_AREA+'delta.json'),'strict_scoped_reviews':reviews,'adapter':ref(OLD,OLD_AREA+'adapter.py'),'Root_release':ref(ROOT,'.agent/evidence/phase020-closed-candidate-inventory-release1.json')},'pending':pending+snapshot_pending+[{'reason':'Final Root END/complete heads and Source4 immutable qualification/product/result checkpoint remain pending'},{'reason':'Exact final inventory hash review and later separate Root measurement release required'},{'reason':'New tail merge proof pass waits one final immutable union; original proofs reused by reference'},{'reason':'Own assembler/config/capture/review commits must enter final accounting tail once'}],'later_work':'Source4 final checkpoint and later replacement architecture/freshQA/docs/admin are unbound; no absent-as-zero claim. Snapshot is explicit current checkpoint preview, not final candidate seal.','own_accounting':'All authored helper/config/report/static input charged020process once within original3750; no allowance. Generated mechanical metadata remains tied to source/frame/output hashes; no blanket evidence exemption.'}
 output=AREA/'inventory.json.gz';raw=json.dumps(cfg,sort_keys=True,separators=(',',':')).encode();output.write_bytes(gzip.compress(raw,mtime=0));report={'kind':'Inventory assembly provenance, not cost result','source_sha256':sha(Path(__file__).read_bytes()),'inventory_sha256':sha(output.read_bytes()),'decoded_sha256':sha(raw),'base':ROOT,'checkpoint':checkpoint,'binding':binding,'status':cfg['status'],'pending':cfg['pending'],'adapter_sha256':cfg['inputs']['adapter']['sha256'],'counts_or_adapter_main_executed':False};(AREA/'assembly.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS adapter-shaped metadata assembled; no counting/main/runtime/test execution. Final binding and exact review remain required.')
if __name__=='__main__':main()
