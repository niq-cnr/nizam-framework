"""Static event/object provenance and actual read-only merge proof; never counts lines."""
import gzip,hashlib,json,re,subprocess
from pathlib import Path
BASE='7278cd902ec0209766e9e06f1f72587ff2a1a45c'
FLOOR='a63cf0c513ad645a9771a69af00dca5d0a45474d'
HEADS=[BASE,'73961d78b9b3eba221e1bd0951befc1a8aa08dfd','0697bfe5e121543b2aa8ed8c8607d0c50e99b413','a3dffed6e895ae6a3e039f36d5d2f95e6bbcfe24','205b5152dfc18cbab2c42ea25cd39ce92a295038']
AREA=Path('.agent/evidence/phase020-candidate-accounting-preparation1')
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args])
def packed(path,value):
 raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode();path.write_bytes(gzip.compress(raw,mtime=0));return {'path':str(path),'sha256':sha(path.read_bytes()),'decoded_sha256':sha(raw)}
def main():
 assert git('rev-parse','HEAD').decode().strip()==BASE
 previous=json.loads(Path('.agent/evidence/phase020-accounting-preparation2/ledger.json').read_bytes())
 overrides={(e['commit'],e['path']):e for e in previous['events']}
 test_events=set(git('rev-list','--no-merges','d66ff730248dec4f086365be55eb4ad060a350c5..abc822f1cca7d246c82557e9181f051fb40f6cfc','--','tools/test_runtime_session.py').decode().split())|{'a3dffed6e895ae6a3e039f36d5d2f95e6bbcfe24'}
 product_events={'ee1ce1dfb6b0f235c23eae439e00328645098c42','2e8c92d11c36525c3b73b8cfb23822c4507835cb','a9114bcbe16fba76dbdba1147ea76db8a5a6b39d'}
 commits=git('rev-list','--reverse','--topo-order','--parents',*HEADS,'^'+FLOOR).decode().splitlines()
 foreign_merge_report=Path('.agent/evidence/133/delivery-supplement1/measurement1/supplement-report.json')
 prior_merges={m['commit']:(i,m) for i,m in enumerate(json.loads(foreign_merge_report.read_bytes())['merges'])}
 events=[];ancestry=[];merges=[];shared=[];objects=set();pending=[]
 version=git('--version').decode().strip()
 for line in commits:
  rev,*parents=line.split();tree=git('rev-parse',rev+'^{tree}').decode().strip();ancestry.append({'commit':rev,'parents':parents,'tree':tree})
  if len(parents)!=1:
   if rev in prior_merges:
    i,p=prior_merges[rev];assert p['parents']==parents and p['tree']==tree and p['actual_exit']==0 and p['stdout']['bytes']==p['stderr']['bytes']==0
    assert p['parent_trees']==[git('rev-parse',v+'^{tree}').decode().strip() for v in parents]
    merges.append({'commit':rev,'parents':parents,'tree':tree,'disposition':'verified-automatic-by-reference','canonical':{'revision':BASE,'path':str(foreign_merge_report),'sha256':sha(foreign_merge_report.read_bytes()),'pointer':'/merges/'+str(i)},'original_actual_child_pid':p['child_pid'],'original_actual_exit':p['actual_exit'],'original_argv':p['argv']})
   else:
    argv=['git','-c','color.ui=false','show','--remerge-diff','--format=','--no-ext-diff','--no-textconv',rev]
    child=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out,err=child.communicate()
    disposition='verified-automatic' if len(parents)==2 and child.returncode==0 and not out and not err else 'PENDING-authored-or-unsupported-merge'
    proof={'commit':rev,'parents':parents,'tree':tree,'parent_trees':[git('rev-parse',v+'^{tree}').decode().strip() for v in parents],'argv':argv,'cwd':str(Path.cwd()),'git_version':version,'child_pid':child.pid,'actual_exit':child.returncode,'stdout':{'sha256':sha(out),'bytes':len(out),'text':out.decode()},'stderr':{'sha256':sha(err),'bytes':len(err),'text':err.decode()},'disposition':disposition};merges.append(proof)
    if disposition.startswith('PENDING'):pending.append({'kind':'merge','commit':rev,'reason':disposition})
   continue
  parent=parents[0]
  raw=git('diff-tree','--raw','--no-abbrev','--no-renames','-r','-z',parent,rev);parts=raw.split(b'\0');i=0
  while i<len(parts)-1:
   info=parts[i].decode();path=parts[i+1].decode();i+=2
   oldmode,newmode,oldoid,newoid,status=info.split();oldmode=oldmode[1:]
   e={'commit':rev,'parent':parent,'path':path,'before_oid':None if set(oldoid)=={'0'} else oldoid,'after_oid':None if set(newoid)=={'0'} else newoid,'before_mode':oldmode,'after_mode':newmode,'status':status}
   if path=='.agent/run_state.json':e.update(owner='excluded-state',feature=None,category='excluded',disposition='exact-approved-state-exclusion',rule='approved spec020 lines129-130')
   elif (rev,path) in overrides:
    v=overrides[(rev,path)];e.update(owner='020',feature=v['feature'],category=v['category'],disposition=v['disposition'],rule='approved-method2-event-override',prior_ledger_event={'commit':rev,'path':path,'block':v['block']})
   elif path.startswith(('.agent/evidence/129/',)) or re.fullmatch(r'\.agent/(?:contracts|qa|validator)/129[^/]*\.json',path):
    cat='independent_tests' if path.endswith('/probe.py') else 'process';e.update(owner='020',feature='129',category=cat,disposition='PENDING-provenance-classification',rule='129-purpose-default')
   elif path.startswith(('.agent/evidence/phase020-','.agent/evidence/phase020/')) or re.fullmatch(r'\.agent/(?:qa|validator)/(?:phase020|020-accounting)[^/]*\.json',path) or path in ('.agent/product_spec_020.md','.agent/feature_list_020.json','docs/planning/phase_020.yaml'):
    e.update(owner='020',feature=None,category='process',disposition='PENDING-provenance-classification',rule='020-planning-and-accounting')
   elif rev in product_events and path in ('tools/runtime_session.py','tools/sbcl_session_loop.lisp'):e.update(owner='020',feature='129',category='product',disposition='charge-authored',rule='actual-Source1/2/3-product-event')
   elif rev in test_events and path=='tools/test_runtime_session.py':e.update(owner='020',feature='129',category='independent_tests',disposition='charge-authored',rule='actual-independent-acceptance-event')
   else:e.update(owner='foreign',feature=None,category='separate-unmeasured',disposition='foreign-retained',rule='outside explicit020scope; shared paths inspected below')
   isshared=path in ('docs/planning/manifest.json','docs/planning/ROADMAP.md','docs/planning/HANDOVER.md','docs/planning/DEBT.md','CHANGELOG.md','tools/README.md','AGENTS.md','docs/planning/agentic-excellence.md')
   if isshared:
    patch=git('-c','color.ui=false','diff','--no-ext-diff','--no-textconv','--no-renames','--unified=0',parent,rev,'--',path).decode()
    shared.append({'commit':rev,'parent':parent,'path':path,'patch_sha256':sha(patch.encode()),'patch':patch,'state':'PENDING-shared-split' if re.search(r'020|\b129\b|SBCL|sbcl',patch) else 'foreign-context-no020change-marker'})
   if e['owner']=='020' or isshared:
    for k in ('before_oid','after_oid'):
     if e[k]:objects.add(e[k])
   events.append(e)
 # Hash exact relevant bytes in one Git batch, not a line-count engine.
 child=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);raw,err=child.communicate(('\n'.join(sorted(objects))+'\n').encode());assert child.returncode==0 and not err
 hashes={};data={};pos=0
 for oid in sorted(objects):
  end=raw.index(b'\n',pos);head=raw[pos:end].split();pos=end+1;assert head[0].decode()==oid and head[1]==b'blob';size=int(head[2]);value=raw[pos:pos+size];pos+=size+1;hashes[oid]=sha(value);data[oid]=value
 assert pos==len(raw)
 for e in events:
  if e['owner']=='020' or e['path'] in {s['path'] for s in shared}:
   e['before_sha256']=hashes.get(e['before_oid']);e['after_sha256']=hashes.get(e['after_oid'])
  if e['disposition']=='PENDING-provenance-classification':
   raw=data[e['after_oid'] or e['before_oid']];name=Path(e['path']).name
   # Raw observations are NOT admitted by filename: match actual paired physical frame/stream hashes below.
   if Path(name).suffix in ('.py','.lisp','.md') or '.stdin' in name:e['disposition']='charge-authored'
   elif Path(name).suffix=='.json' and not any(t in name for t in ('.execution.','.started.','.capture-summary.')):e['disposition']='charge-maintained-report'
   else:pending.append({'kind':'raw-or-authored-provenance','commit':e['commit'],'path':e['path'],'sha256':sha(raw)})
 meta={'kind':'Static full union event provenance; no accounting totals','base':BASE,'history_floor':FLOOR,'preparation_heads':HEADS,'final_Root_endpoint':None,'final_Root_heads':None,'ancestry':ancestry,'events':events,'pending':pending,'limitation':'Foreign history retained by commit/path/Git-OID metadata; no foreign numeric costs. Relevant020/shared bytes hashbound. Final Root endpoint and own preparation commits not bound here.'}
 outputs=[packed(AREA/'events.json.gz',meta),packed(AREA/'merges.json.gz',merges),packed(AREA/'shared.json.gz',shared)]
 (AREA/'preparation-output.json').write_text(json.dumps({'generated_outputs':outputs,'generator_sha256':sha(Path(__file__).read_bytes()),'base':BASE,'scope':'Metadata/hash/events and read-only actual remerge proof only; no line measurement or engine main'},indent=2)+'\n')
 print('Static event/object inventory and actual merge proofs retained. No numeric accounting performed.')
if __name__=='__main__':main()
