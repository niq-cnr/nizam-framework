"""Fresh Evaluator final static evidence admission; never reexecutes acceptance."""
import ast,collections,gzip,hashlib,json,re,shutil,stat,subprocess
from pathlib import Path
import jsonschema
import yaml
ROOT=Path.cwd();OUT=Path('/home/cnross/.tmp/nizam-feature123-fresh-qa1-run');TARGET=ROOT/'.agent/evidence/123/fresh-qa1';BASE='d94c880b825f3f5893941f91fea46e2564903a4f';SOURCE='9886e5fadad31845349e54235820edac71c7b7fb';HIST='f8965efbfe1323b7cd6c342f87cb9cb8102f4e76'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a])
def blob(rev,p):return git('show',rev+':'+p)
def read(p):return json.loads(p.read_bytes())
def write(p,v):
 assert not p.exists();p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def refvalue(r):
 b=blob(r['revision'],r['path']);assert sha(b)==r['sha256'];return json.loads(b)
expected=[('candidate','candidate',['python3','tools/test_workflow_assurance.py','--case','ci-candidate-bound'],0),('core','blocker',['python3','tools/test_workflow_assurance.py','--case','ci-blocker-rejected'],0),('core','readiness',['python3','tools/test_workflow_assurance.py','--check','controls-ready'],0),('core','validate',['bash','tools/validate.sh'],0),('core','payload',['bash','tools/validate.sh','--payload'],0),('default48','default48',['python3','tools/test_workflow_assurance.py'],0),('fixture','fixture',['bash','tools/fixtures_self_test.sh'],0),('historical118','historical118',['python3','tools/test_workflow_assurance.py','--check','foundation-ready'],0),('core','current-stale118',['python3','tools/test_workflow_assurance.py','--check','foundation-ready'],1)]
# Do not start this admission until all original long execution frames exist.
assert all((OUT/lane/(name+'.capture-summary.json')).exists() for lane,name,argv,code in expected)
frames=[]
for lane,name,argv,code in expected+[('extra2','adversarial2',['python3','-'],0),('core','adversarial',['python3','-'],1)]:
 directory=OUT/lane;frame=read(directory/(name+'.execution.json'));summary=read(directory/(name+'.capture-summary.json'))
 assert frame['argv']==argv and type(frame['actual_exit']) is int and frame['actual_exit']==code and not frame['timed_out']
 assert frame['exercised_revision']==('8ac94f6808e8197111197c9acbf59b2aa92efc7c' if lane=='historical118' else BASE)
 assert frame['started_at']>'2026-10-15T19:10:21.516185+00:00'
 assert summary['capture_driver_sha256']=='e9e9417c39548919b892f0b7436b885b72a26b781d15455e62daebe9367c5ac0'
 for stream in ('stdout','stderr'):
  raw=Path(frame[stream]['path']).read_bytes();assert sha(raw)==frame[stream]['sha256'] and len(raw)==frame[stream]['bytes']
 inventories=[]
 for side in ('before','after'):
  r=summary[side];raw=Path(r['path']).read_bytes();decoded=gzip.decompress(raw);assert sha(raw)==r['sha256'] and sha(decoded)==r['inventory_sha256'];value=json.loads(decoded);assert len(value['rows'])==r['rows'] and sum(p['path'].startswith('.nizam/') for p in value['rows'])==r['installed']==239;inventories.append(value)
 assert inventories[0]==inventories[1] and summary['preservation_equal']
 frames.append(dict(lane=lane,name=name,command=argv,actual_exit=code,expected_exit=code,frame='.agent/evidence/123/fresh-qa1/'+lane+'/'+name+'.execution.json',pid=frame['child_pid'],elapsed_seconds=frame['elapsed_seconds'],physical_rows=len(inventories[0]['rows']),installed_rows=239,preservation_equal=True))
# Derive the exact default inventory from immutable syntax, never import tests.
def inventory_ast(raw):
 tree=ast.parse(raw);values={}
 names={'CASES','BASE_CASES','BUNDLE_CASES','PRE_ENTRY_CASES','ENTRY_CASES','AGF_CASES','RECEIPT_CASES','LANE_CASES','FAILURE_CASES','CONTROL_CASES'}
 def value(node):
  if isinstance(node,ast.Name):return values[node.id]
  if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):return value(node.left)+value(node.right)
  return ast.literal_eval(node)
 for n in tree.body:
  if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in names:values[n.targets[0].id]=value(n.value)
 main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');loop=[n for n in main.body if isinstance(n,ast.For)][-1];expression=loop.iter
 while isinstance(expression,ast.IfExp):expression=expression.orelse
 return list(value(expression))
cases=inventory_ast(blob(SOURCE,'tools/test_workflow_assurance.py'));assert len(cases)==len(set(cases))==48
terminal=[line[5:] for line in (OUT/'default48/default48.stdout.txt').read_text().splitlines() if line.startswith('PASS ')]
assert terminal==cases,(terminal,cases)
fixture=(OUT/'fixture/fixture.stdout.txt').read_text();matches=re.findall(r'^SELF-TEST OK: (\d+)/(\d+) fixtures accounted for, 0 failed$',fixture,re.M);assert len(matches)==1 and matches[0][0]==matches[0][1]
for case in ('ci-candidate-bound','ci-blocker-rejected'):assert fixture.splitlines().count('OK   workflow-assurance '+case)==1
assert (OUT/'core/current-stale118.stderr.txt').read_text()=='AssuranceError: pinned entry bytes/mode changed: tools/workflow_assurance.py\n'
assert (OUT/'historical118/historical118.stdout.txt').read_text()=='PASS foundation-ready: valid current20 receipt and independent typed/proof/identity/continuity attacks\n'
assert (OUT/'core/readiness.stdout.txt').read_text().splitlines()[-1]=='PASS controls-ready observed independently selected actual hosted proof'
for name,diagnostic in [('validate','SUMMARY: 16 passed, 0 failed'),('payload','SUMMARY (payload mode): 12 passed, 0 failed')]:assert (OUT/('core/'+name+'.stdout.txt')).read_text().splitlines()[-1]==diagnostic
assert 'EXPECTED_REJECTION same warmed parser: capture metadata current artifact regular mode/hardlink\n' in (OUT/'extra2/adversarial2.stdout.txt').read_text()
assert (OUT/'extra2/adversarial2.stdin').read_bytes()==(OUT/'adversarial2.py').read_bytes()
assert (OUT/'core/adversarial.stdin').read_bytes()==(OUT/'adversarial.py').read_bytes()
# Existing definitions and assignment sequences are anchored outside the result.
preserved={}
for path in ('tools/workflow_assurance.py','tools/test_workflow_assurance.py'):
 old=ast.parse(blob(HIST,path));new=ast.parse(blob(SOURCE,path));count=0
 for kind in ((ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef),):
  for n in old.body:
   if isinstance(n,kind):
    if path.endswith('test_workflow_assurance.py') and n.name=='main':continue
    candidates=[v for v in new.body if isinstance(v,kind) and v.name==n.name];assert len(candidates)==1 and ast.dump(n,include_attributes=False)==ast.dump(candidates[0],include_attributes=False),(path,n.name);count+=1
 def assignments(tree):
  answer=collections.defaultdict(list)
  for n in tree.body:
   if isinstance(n,ast.Assign):
    for t in n.targets:
     if isinstance(t,ast.Name):answer[t.id].append(ast.dump(n.value,include_attributes=False))
  return answer
 prior,current=assignments(old),assignments(new)
 for key,sequence in prior.items():assert current[key]==sequence,(path,key)
 preserved[path]=dict(inherited_definitions_unchanged=count,inherited_assignment_sequences_unchanged=len(prior),test_main_exception='Approved additive dispatch only; independently ModeB reviewed; actual default48 and literal selectors executed' if path.endswith('test_workflow_assurance.py') else None)
workflow=yaml.safe_load(blob(SOURCE,'.github/workflows/compliance.yml'));assert set(workflow['jobs'])=={'validate','e2e_bootstrap','fixtures_self_test','convergent_review','self_governance'}
assert all(not step.get('continue-on-error',False) for job in workflow['jobs'].values() for step in job['steps'])
# Container is at actual release, embedded predecessor artifact rows at019398.
container=json.loads(blob(BASE,'.agent/evidence/123/source-prerequisite.json'));rows=container['adjacent_prior_feature_evidence'];assert len(rows)==28
for row in rows:
 assert row['revision']==container['integration_anchor']=='019398f7c652fe7b5718b3adc140a8dc515fb029'
 entry=git('ls-tree',row['revision'],'--',row['path']).decode().split();assert entry[0]==row['git_mode'] and entry[2]==row['git_blob'];raw=blob(row['revision'],row['path']);assert sha(raw)==row['sha256'];assert (ROOT/row['path']).read_bytes()==raw
release=json.loads(blob(BASE,'.agent/evidence/123/root-fresh-qa1-release.json'));policy=refvalue(release['policy_ref']);evidence=refvalue(release['evidence_ref'])
for group,items in evidence['candidate']['assessed_inputs'].items():
 for row in items:
  p=ROOT/row['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and sha(p.read_bytes())==row['sha256'] and bool(s.st_mode&0o111)==row['executable']
# Publish only finished bytes. Existing earlier captures must remain identical.
for p in OUT.rglob('*'):
 if p.is_file():
  destination=TARGET/p.relative_to(OUT)
  if destination.exists():assert destination.read_bytes()==p.read_bytes();continue
  destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,destination)
notes=['Original one-extra setup1 actual1 is retained, not semantic rejection. Root72605b4a authorized only tools import-path/new outside directory correction; setup2 same check actual0 with original assertions unchanged.','Incidental read-only preparation git show of source-prerequisite container at019398 returned128 (container absent there); actual d94 container records28 embedded rows anchored019398. Correct location read; no acceptance rerun, contract edit or wider exception.','Core orchestration process stopped actual1 after original own-extra setup failure; original selected child has complete PID/time/argv/rawstreams/fullpreservation. Exact outer controller PID/times were not retained and are not invented.','No fresh namespace/model/historical-runtime A10 execution; local readiness independently observes actual completed hosted proof. No benchmark/comparative or lifecycle closure claim.']
report=dict(role='Evaluator',reviewer='/root/fresh_qa123',feature_id='123',release_revision=BASE,source_revision=SOURCE,mode_b_ref=release['mode_b_ref'],policy_ref=release['policy_ref'],evidence_ref=release['evidence_ref'],source_tree=evidence['candidate']['source_tree'],logical_planned_checks=10,mandatory_commands=9,acceptance_process_attempts=11,mandatory_expected_outcomes_satisfied=9,mandatory_actual_exit_zero=8,exactly_one_additional_adversarial_check=True,original_setup_failure_preserved=True,results=frames,default48_order=cases,fixture_accounting=matches[0],preservation_ast=preserved,adjacent_prior_rows_verified=28,protected_rows_verified=sum(map(len,evidence['candidate']['assessed_inputs'].values())),notes=notes)
write(TARGET/'results.json',report)
qa=dict(feature_id='123',qa_pass=True,checks_run=9,checks_passed=8,checks_passed_scope='Literal exit0 count; all9 mandatory expected outcomes satisfied including intended current-stale118 exit1.',adversarial=dict(performed=True,logical_checks=1,setup_attempts=2),adversarial_check=dict(description='One independently selected same-instance warmed immutable-cache metadata hardlink rejection/restoration',result='pass',evidence='.agent/evidence/123-qa-adversarial.txt'),checks=[dict(command='PYTHONDONTWRITEBYTECODE=1 '+' '.join(v['command']) if v['command'][0]=='python3' else ' '.join(v['command']),exit_code=v['actual_exit'],expected_exit=v['expected_exit'],evidence=v['frame']) for v in frames[:9]],evidence_files=['.agent/evidence/123/fresh-qa1/results.json','.agent/evidence/123/fresh-qa1/capture-index.json','.agent/evidence/123-qa-adversarial.txt']+[v['frame'] for v in frames],issues=[],missing_acceptance_coverage=[],unsupported_claims=[],required_fixes=[],final_verdict=dict(approved=True,summary='Independent freshQA: all9 mandatory expected outcomes, exact default48/fixture coverage, preserved physical/installed/history/source bounds, and exactly one own extra verified. Original operational setup1 failure retained and bounded setup2 correction proved.'),reviewer='/root/fresh_qa123',assessed_revision=BASE,source_revision=SOURCE,approved_contract_ref=release['approved_contract_ref'],mode_b_ref=release['mode_b_ref'],notes=notes)
for path in ('schema/qa_verdict.schema.json','.nizam/schema/qa_verdict.schema.json'):jsonschema.Draft202012Validator(json.loads((ROOT/path).read_bytes())).validate(qa)
write(ROOT/'.agent/qa/123.json',qa)
authored=['setup.py','core.py','adversarial.py','adversarial2.py','extra2-setup.py','finalize.py']
index=dict(files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in sorted(TARGET.rglob('*')) if p.is_file()],canonical_authored_sources=[dict(path='.agent/evidence/123/fresh-qa1/'+p,sha256=sha((TARGET/p).read_bytes())) for p in authored],duplicate_retained_sources=[dict(canonical='adversarial.py',duplicate='core/adversarial.stdin'),dict(canonical='adversarial2.py',duplicate='extra2/adversarial2.stdin')],classification='Raw execution frames/streams/inventories/setup bundles and binary index-pack stdin distinct from authored code; existing preparation1 and capture1 remain canonical prior artifacts. No scope measurement performed.')
write(TARGET/'capture-index.json',index)
print(json.dumps(dict(strict_qa_approved=True,mandatory_expected=9,extra=1,acceptance_attempts=11,raw_index_files=len(index['files']),default_order=48,qa_path='.agent/qa/123.json'),sort_keys=True))
