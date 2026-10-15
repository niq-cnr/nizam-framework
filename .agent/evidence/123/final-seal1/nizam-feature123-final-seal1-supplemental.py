import ast,datetime,gzip,hashlib,json,os,re,stat,subprocess,sys,time
from pathlib import Path
R=Path('/home/cnross/.tmp/nizam-feature123-final-seal1');O=Path('/home/cnross/.tmp/nizam-feature123-final-seal1-captures')
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()+b'\n'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R)
def read(p):return json.loads((R/p).read_bytes())
def gate(v):assert v['final_verdict']['approved'] is True and all(v[k]==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
def snap():
 rows=[]
 for name in git('ls-files','-z').decode().split('\0'):
  if not name:continue
  p=R/name;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1,name
  rows.append([name,s.st_mode,s.st_nlink,sha(p.read_bytes())])
 return dict(rows=rows,head=git('rev-parse','HEAD').decode().strip(),origin=git('remote','get-url','origin').decode().strip(),refs=git('show-ref').decode(),status=git('status','--porcelain','--untracked-files=all').decode())
start=time.monotonic();at=datetime.datetime.now(datetime.timezone.utc).isoformat();before=snap();(O/'seal-supplemental.before.json.gz').write_bytes(gzip.compress(enc(before),mtime=0))
refs={}
def ref(r):
 key=(r['revision'],r['path'],r['sha256'])
 if key in refs:return refs[key][1]
 assert re.fullmatch('[0-9a-f]{40}',key[0]) and re.fullmatch('[0-9a-f]{64}',key[2])
 line=git('--literal-pathspecs','ls-tree','-z',key[0],'--',key[1]);assert line.count(b'\0')==1
 meta,path=line[:-1].split(b'\t');mode,kind,blob=meta.decode().split();assert kind=='blob' and mode in ('100644','100755') and path.decode()==key[1]
 raw=git('cat-file','blob',blob);assert sha(raw)==key[2],key
 refs[key]=(dict(path=key[1],revision=key[0],sha256=key[2],git_mode=mode,git_blob=blob,bytes=len(raw)),raw)
 return raw
def walk(x):
 if isinstance(x,dict):
  if {'path','revision','sha256'}<=x.keys():ref(x)
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
contract=read('.agent/contracts/123.json');policy=read('.agent/evidence/123/controls-policy.json');evidence=read('.agent/evidence/123/controls-evidence.json');freeze=read('.agent/evidence/123/author4-freeze.json');hosted=json.loads(ref(policy['hosted_review_ref']));gate(hosted)
assert len(contract['protocol']['payload_catalog'])==31 and freeze['payload_catalog_count']==31
walk(policy);walk(evidence);walk(freeze)
for k in ('capture_selection_ref','verify_selection_ref'):
 selection=json.loads(ref(evidence[k]));walk(selection)
 for field in ('authority_ref','shadow_state_ref','report_ref','a10_policy_ref'):
  if selection[field] is not None:walk(json.loads(ref(selection[field])))
 assert selection['contract_ref']['sha256']=='64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5'
for k in ('capture_host','verify_host'):
 metadata=json.loads(ref(evidence[k]['metadata_ref']));walk(metadata)
 invocation=json.loads(ref(metadata['invocation_ref']));walk(invocation)
 assert invocation['actual_exit']==0
for k in ('evaluation_ref','replay_ref','a11_capture_ref','a10_capture_ref','a10_result_ref','capability_ref'):
 walk(json.loads(ref(evidence[k])))
walk(hosted)
index=read('.agent/evidence/123/hosted-review1/capture-index.json')
for row in index['files']:
 raw=(R/row['path']).read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
assert len(index['files'])==98
def dump(x):return ast.dump(x,include_attributes=False)
ast_counts={'tools/workflow_assurance.py':{'basis':'Original static1 passed all inherited functions/classes/main/assignments before its later CASES count failure; not rerun'},'tools/test_workflow_assurance.py':{'basis':'Original static1 passed inherited functions/classes before its assignmentcount failure; not rerun'}}
path='tools/test_workflow_assurance.py'
base=ast.parse(git('show','f8965efbfe1323b7cd6c342f87cb9cb8102f4e76:'+path));current=ast.parse((R/path).read_bytes())
assignment_counts={}
for name in dict.fromkeys(dump(n.targets[0]) for n in base.body if isinstance(n,ast.Assign)):
 old=[dump(n) for n in base.body if isinstance(n,ast.Assign) and dump(n.targets[0])==name]
 new=[dump(n) for n in current.body if isinstance(n,ast.Assign) and dump(n.targets[0])==name]
 assert old==new,(path,name)
 assignment_counts[name]=len(old)
ast_counts[path]['ordered_assignments_reconciled']=assignment_counts
assert git('rev-parse','9886e5fadad31845349e54235820edac71c7b7fb^').decode().strip()=='d1fd767bca33f7e54486ebc8542811315fe48bde'
assert git('rev-parse','9886e5fadad31845349e54235820edac71c7b7fb^{tree}')==git('rev-parse','d1fd767bca33f7e54486ebc8542811315fe48bde^{tree}')
provisional=read('.agent/qa/123-provisional-bundle-review-rev3.json');gate(provisional);walk(provisional)
for r in freeze['current_program_refs']:
 assert ref(r)==(R/r['path']).read_bytes()==git('show','9886e5fadad31845349e54235820edac71c7b7fb:'+r['path'])
controls=[]
for lane in ('candidate','blocker'):
 for stage,expected in [('positive',0),('semantic-negative',1)]:
  path=f'.agent/evidence/123/renewed-controls-{lane}2.{stage}.execution.json';v=read(path);walk(v)
  assert v['actual_exit']==expected and v['expected_observation_observed'] and v['stop_reason'] is None and v['preservation']['equal']
  assert all(v['stream_complete'].values()) and v['exercised_revision']=='9886e5fadad31845349e54235820edac71c7b7fb'
  for stream in ('stdout','stderr'):
   raw=(R/v[stream]).read_bytes();assert sha(raw)==v[stream+'_sha256'] and len(raw)==v['retained_bytes'][stream]==v['observed_bytes'][stream]
  raw=(R/v['preservation']['before_inventory_path']).read_bytes();assert sha(raw)==v['preservation']['before_inventory_gzip_sha256'];snapshot=json.loads(gzip.decompress(raw));assert len(snapshot['rows'])==13104 and all(row[2]==1 for row in snapshot['rows'])
  if expected==1:assert 'POLICY_ASSERTION: synthetic invalid controls proof accepted: '+('replay-valid-missing-trials' if lane=='candidate' else 'incoming-issues') in (R/v['stderr']).read_text()
  controls.append(dict(path=path,sha256=sha((R/path).read_bytes()),actual_exit=expected,finished_at=v['finished_at'],stdout_sha256=v['stdout_sha256'],stderr_sha256=v['stderr_sha256']))
witness=read('.agent/evidence/123/restored-default-witness-capture2-review.json');gate(witness);walk(witness)
assert witness['actual_execution']['started_at']=='2026-10-15T13:31:39Z' and witness['observed_outcomes']['ordered_selector_count']==48
when=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
assert all(when(witness['actual_execution']['started_at'])>when(x['finished_at']) for x in controls if x['actual_exit']==1)
log=ref(witness['raw_log_ref']).decode();names=[]
for line in log.splitlines():
 m=re.search(r'PASS ([a-z][a-z0-9-]+)\s*$',line)
 if m:names.append(m[1])
assert names==witness['observed_outcomes']['ordered_selector_names']
jobs=json.loads(ref(witness['external_result_binding']['job_metadata_ref']));job=next(j for j in jobs['jobs'] if j['id']==116427391522);assert job['conclusion']=='success'
ready=[]
for stage,expected in [('positive',0),('semantic-negative',1),('restored',0)]:
 f=json.loads((O/(stage+'.execution.json')).read_bytes());assert f['actual_exit']==expected and f['accepted'] and f['preservation_equal'] and f['installed_count']==239
 b=json.loads(gzip.decompress((O/f['before']['path']).read_bytes()));a=json.loads(gzip.decompress((O/f['after']['path']).read_bytes()));assert b==a
 for key in ('before','after'):
  raw=(O/f[key]['path']).read_bytes();assert sha(raw)==f[key]['sha256']
 for stream,v in f['streams'].items():assert sha((O/v['path']).read_bytes())==v['sha256'] and v['bytes']==v['observed_bytes'] and v['complete']
 ready.append(dict(stage=stage,actual_exit=expected,exercised_revision=f['exercised_revision'],elapsed_seconds=f['elapsed_seconds'],tracked_count=f['tracked_count'],installed_count=f['installed_count']))
methods={n.name:n.lineno for c in ast.parse((R/'tools/workflow_assurance.py').read_bytes()).body if isinstance(c,ast.ClassDef) and c.name=='_ControlsProof' for n in c.body if isinstance(n,ast.FunctionDef)}
grammar=[]
for key,obligation in contract['protocol']['payload_catalog'].items():
 if any(s in key for s in ('Metadata','job_log','manifest / invocation')):consumer='host';producer='Root actual five Fetch captures and normalization / run_capture+run_verify bundle_outputs'
 elif any(s in key for s in ('trial','Trial','evaluation_ref','replay_ref','prompt_ref','prior_ledger','report_ref','a11_result')):consumer='replay';producer='existing enforced evaluator/convergence and independent Report4 / run_map'
 elif any(s in key for s in ('a10','a11_capture')):consumer='a10' if 'a10' in key else 'capture';producer='run_verify unchanged A10 APIs / run_capture capture_record'
 elif 'capability' in key or 'Process.' in key:consumer='capability';producer='run_capture actual boundary/isolation captures'
 elif 'pack_ref' in key:consumer='pack';producer='bundle_outputs output-only actual Git bundle'
 elif 'authority' in key or 'Authority' in key:consumer='authority';producer='Root experiment authority from immutable original standing instruction'
 elif 'shadow' in key:consumer='shadow';producer='Root experiment-only ShadowState before capture'
 elif 'contract' in key or 'prerequisites' in key:consumer='prerequisites';producer='actual dual pre-code gates / Root approved metadata / provisional4'
 elif 'candidate' in key:consumer='identity';producer='run_capture unchanged assess_repository against clean Source'
 elif 'runner_ref' in key:consumer='selection';producer='protected immutable Source code selected by Root'
 elif key=='experiment copied inputs':consumer='host';producer='prepare/run_capture/run_verify exact earlier Root input copies'
 else:consumer='verify';producer='Root post-HostedReview policy or independent HostedReviewer after actual Evidence'
 grammar.append(dict(group=key,contract_obligation=obligation,producer=producer,consumer='tools/workflow_assurance.py:'+str(methods[consumer])+' _ControlsProof.'+consumer,actual_chain='policy P -> actual Evidence E -> capture2/verify1; current immutable code/selected refs and original synthetic controls/raw captures',validation='closed canonical/ref/protected/object relations in pinned parser; current selectors retained in exact frozen code and independently captured 0/1/restored witnesses'))
after=snap();assert before==after;(O/'seal-supplemental.after.json.gz').write_bytes(gzip.compress(enc(after),mtime=0))
facts=dict(role='Independent final executable acceptance Evaluator',reviewer='/root/final_seal123',feature_id='123',release_revision=before['head'],source_commit='9886e5fadad31845349e54235820edac71c7b7fb',readiness=ready,original_synthetic_controls=controls,restoration=dict(review_sha256=sha((R/'.agent/evidence/123/restored-default-witness-capture2-review.json').read_bytes()),started_at=witness['actual_execution']['started_at'],ordered_selectors=names,scope='Both synthetic lanes semantic restoration only; no literal restored wrapper, same-runtime or full hosted filesystem claim'),inherited_ast=ast_counts,payload_catalog=grammar,verified_ref_objects=[v[0] for v in refs.values()],hosted_raw_files_verified=len(index['files']),preservation=dict(equal=True,tracked_count=len(before['rows']),installed_count=sum(x[0].startswith('.nizam/') for x in before['rows']),scope='own full physical bytes/full modes/nlinks/HEAD/origin/allrefs/coordination; Root shared refs may advance'),no_source_or_tests_modified=True,limitations=['No final QA/ModeB/feature closure verdict','No local namespace/model/historical A10 execution; final API only through three frozen readiness helper commands','No interim scope measurement'],incidental_readonly_observations=['Original static1 remains exit1: mistaken one-assignment-per-target assumption despite baseline/current three identical CASES assignments; Root narrowly authorized ordered sequence reconciliation within open seal1; original timing limitation retained','jq projection of nonexistent grammar key failed before corrected narrow read; no behavior','transported commit absent in separate ODB before strict authorized import; no proof failure'],actual_exit=0,argv=[sys.executable,str(Path(__file__).resolve())],cwd=str(R),environment={'PYTHONDONTWRITEBYTECODE':'1'},started_at=at,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start)
(O/'seal-supplemental.facts.json').write_bytes(enc(facts));print(json.dumps(dict(status='PASS independent final static reconciliation',verified_refs=len(refs),catalog_groups=len(grammar),inherited_ast=ast_counts,readiness=[x['actual_exit'] for x in ready])),flush=True)
