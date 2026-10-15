import ast,fnmatch,gzip,hashlib,json,os,pathlib,stat,subprocess,sys,time
R=pathlib.Path('/home/cnross/.tmp/nizam-feature123-modeb1'); O=pathlib.Path('/home/cnross/.tmp/modeb123-capture1'); O.mkdir(exist_ok=True)
CTX='fb6971f4b77fae37fbbeb8c08cf8b0b42d73d40b'; S='9886e5fadad31845349e54235820edac71c7b7fb'; B='79811ef76df950b8151e2af62637ab7d1df34305'; OLD='f8965efbfe1323b7cd6c342f87cb9cb8102f4e76'
def git(*args):return subprocess.check_output(['git','-C',str(R),*args])
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads((R/p).read_bytes())
def req(ok,label,**facts):
 if not ok:raise AssertionError(label)
 print(json.dumps(dict(check=label,**facts),sort_keys=True))
def snap():
 rows={}
 for d,ds,fs in os.walk(R):
  ds[:]=[x for x in ds if x!='.git']
  for n in ds+fs:
   p=pathlib.Path(d)/n;st=p.lstat();row=dict(mode=st.st_mode,nlink=st.st_nlink)
   if stat.S_ISREG(st.st_mode):row['sha256']=sha(p.read_bytes())
   elif stat.S_ISLNK(st.st_mode):row['target']=os.readlink(p)
   rows[str(p.relative_to(R))]=row
 return dict(physical=rows,head=git('rev-parse','HEAD').decode().strip(),origin=git('remote','get-url','origin').decode().strip(),refs=git('show-ref').decode(),status=git('status','--porcelain=v1','--untracked-files=all').decode())
before=snap(); (O/'preservation-before.json.gz').write_bytes(gzip.compress(json.dumps(before,sort_keys=True).encode(),mtime=0))
req(before['head']==CTX and not before['status'],'isolated assessed context clean',context=CTX,gitdir=str(R/'.git'),alternates_present=(R/'.git/objects/info/alternates').exists())
contract=read('.agent/contracts/123.json'); release=read('.agent/evidence/123/root-modeb1-release.json'); policy=read('.agent/evidence/123/controls-policy.json'); E=read(policy['evidence_ref']['path']); seal=read('.agent/evidence/123/final-executable-seal1-report.json'); H=read(policy['hosted_review_ref']['path']); HF=read('.agent/evidence/123/hosted-review1-facts.json')
req(contract['status']=='approved' and contract['approvals']['validator_mode_a'] is True and contract['approvals']['evaluator_contract_review'] is True,'approved contract and independent gates')
for p in ['tools/workflow_assurance.py','tools/test_workflow_assurance.py','tools/workflow_assurance_ci.py','.github/workflows/compliance.yml','tools/fixtures_self_test.sh','tools/README.md','CHANGELOG.md','.agent/contracts/123.json']:
 req(git('show',S+':'+p)==(R/p).read_bytes(),'protected source-current bytes '+p,sha256=sha((R/p).read_bytes()))
paths=git('diff','--name-only',B,CTX).decode().splitlines();allowed=[x['path'] for k in ['files_create','files_modify'] for x in contract['scope'][k]];adj=read('.agent/evidence/123/source-prerequisite.json')['adjacent_prior_feature_evidence'];adjpaths={x['path'] for x in adj}
unknown=[p for p in paths if not any(fnmatch.fnmatchcase(p,a) for a in allowed) and p not in adjpaths]
req(not unknown,'whole contracted file scope',changed_paths=len(paths),uncontracted=unknown,base=B)
for row in adj:
 p=row['path'];actual=git('show',row['revision']+':'+p);entry=git('ls-tree',row['revision'],'--',p).decode().split()
 req(sha(actual)==row['sha256'] and entry[:3]==[row['git_mode'],'blob',row['git_blob']] and git('show',CTX+':'+p)==actual,'exact adjacent evidence '+p)
req(not git('diff','--name-only',B,CTX,'--','.nizam'),'installed payload tree unchanged',installed_paths=len(git('ls-tree','-r','--name-only',CTX,'--','.nizam').splitlines()))
for p in ['tools/workflow_assurance.py','tools/test_workflow_assurance.py']:
 old=ast.parse(git('show',OLD+':'+p));new=ast.parse((R/p).read_bytes());nmap={n.name:n for n in new.body if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))};changed=[];count=0
 for n in old.body:
  if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef)) and not(p.endswith('test_workflow_assurance.py') and n.name=='main'):
   count+=1
   if n.name not in nmap or ast.dump(n,include_attributes=False)!=ast.dump(nmap[n.name],include_attributes=False):changed.append(n.name)
 req(not changed,'inherited AST preserved '+p,definitions=count,changed=changed)
 if p.endswith('/workflow_assurance.py'):
  old_assign=[ast.dump(n,include_attributes=False) for n in old.body if isinstance(n,(ast.Assign,ast.AnnAssign,ast.Import,ast.ImportFrom))];new_assign=[ast.dump(n,include_attributes=False) for n in new.body if isinstance(n,(ast.Assign,ast.AnnAssign,ast.Import,ast.ImportFrom))]
  req(new_assign[:len(old_assign)]==old_assign,'inherited Source imports assignments CLI preserved')
# No product module is imported: immutable Ref validation uses Git bytes/modes only.
refs={}
def walk(v):
 if type(v) is dict:
  if all(k in v for k in ['path','revision','sha256']) and isinstance(v['path'],str) and len(str(v['revision']))==40 and len(str(v['sha256']))==64:refs[(v['revision'],v['path'],v['sha256'])]=v
  for x in v.values():walk(x)
 elif type(v) is list:
  for x in v:walk(x)
for v in [release,policy,E,seal,H,HF,read('.agent/evidence/123/author4-freeze.json')]:walk(v)
for rev,p,digest in sorted(refs):
 raw=git('show',rev+':'+p);entry=git('ls-tree',rev,'--',p).decode().split();req(sha(raw)==digest and entry[0] in ['100644','100755'] and entry[1]=='blob','immutable Ref '+p,revision=rev,sha256=digest)
for label,index_path in [('final-seal','.agent/evidence/123/final-seal1/capture-index.json'),('hosted-review',HF['raw_index']['path'])]:
 idx=read(index_path);rows=idx['files'];total=0
 for row in rows:
  raw=(R/row['path']).read_bytes();req(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'raw indexed '+label+' '+row['path']);total+=len(raw)
 req(True,'raw index complete '+label,files=len(rows),bytes=total)
# Bind all protected candidate inputs to Source and assessed context without exercising APIs.
protected=[]
for cat,rows in E['candidate']['assessed_inputs'].items():
 for row in rows:
  p=row['path'];raw=(R/p).read_bytes();entry=git('ls-tree',S,'--',p).decode().split();st=(R/p).lstat()
  req(sha(raw)==row['sha256'] and sha(git('show',S+':'+p))==row['sha256'] and (entry[0]=='100755') is row['executable'] and bool(st.st_mode&0o111) is row['executable'] and st.st_nlink==1,'protected candidate '+p);protected.append(p)
req(len(protected)==537,'all candidate inputs checked',count=len(protected))
for p in ['.agent/validator/123-mode-a-rev2.json','.agent/qa/123-contract-review-rev2.json','.agent/qa/123-provisional-bundle-review-rev3.json','.agent/evidence/123/hosted-review1.json','.agent/qa/123-final-executable-seal1.json']:
 v=read(p);req(v['final_verdict']['approved'] is True and all(v[k]==[] for k in ['issues','missing_acceptance_coverage','unsupported_claims']),'strict prerequisite gate '+p)
req(H['reviewer']=='/root/overlap_review123' and seal['reviewer']=='/root/final_seal123' and H['reviewer']!=seal['reviewer'],'role separation preserved')
req([x['actual_exit'] for x in seal['readiness']]==[0,1,0] and all(x['preservation_equal'] for x in seal['readiness']),'actual readiness controls and preservation',exits=[x['actual_exit'] for x in seal['readiness']])
req(set(x['group'] for x in seal['payload_catalog'])==set(contract['protocol']['payload_catalog']),'all31 payload obligations mapped',groups=len(seal['payload_catalog']))
for mode,runid in [('capture',38736608742),('verify',38754141468)]:
 host=E[mode+'_host'];meta=read(host['metadata_ref']['path']);fetches={x['kind']:x for x in meta['fetches']};run=json.loads(git('show',fetches['run']['stdout']['revision']+':'+fetches['run']['stdout']['path']));jobs=json.loads(git('show',fetches['jobs']['stdout']['revision']+':'+fetches['jobs']['stdout']['path']))
 req(host['run_id']==runid==run['id'] and run['status']=='completed' and run['conclusion']=='success' and len(jobs['jobs'])==5 and all(j['conclusion']=='success' for j in jobs['jobs']),'actual hosted run '+mode,run_id=runid,attempt=host['attempt'])
req(contract['budget']['phase_original']==7200 and contract['budget']['phase_ceiling']==9360 and contract['budget']['prior_actual']==4303 and contract['budget']['measurement_base']==B,'budget rules bound without interim measurement')
after=snap();(O/'preservation-after.json.gz').write_bytes(gzip.compress(json.dumps(after,sort_keys=True).encode(),mtime=0));req(before==after,'full physical Git state and coordination preserved',physical_paths=len(before['physical']),tracked_paths=len(git('ls-files','-z').split(b'\0'))-1,installed_regular_files=sum(1 for p,v in before['physical'].items() if p.startswith('.nizam/') and stat.S_ISREG(v['mode'])))
print('STATIC_MODEB_INSPECTION_COMPLETE; no product import, API, test, network, CI, scope measure or namespace execution')
