import concurrent.futures,datetime,hashlib,json,os,stat,subprocess,time
from pathlib import Path
ROOT=Path('/home/cnross/workspace02/nizam-framework');OUT=Path('/home/cnross/.tmp/nizam-feature123-fresh-qa1-run');REV='d94c880b825f3f5893941f91fea46e2564903a4f';SOURCE='9886e5fadad31845349e54235820edac71c7b7fb'
DRIVER=ROOT/'.agent/evidence/123/fresh-qa-capture1.py'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(root,*a):return subprocess.check_output(['git','-C',str(root),*a])
def write(p,b):
 with p.open('xb') as f:f.write(b)
def jwrite(p,v):write(p,json.dumps(v,indent=2,sort_keys=True).encode()+b'\n')
def rawref(r):
 b=git(ROOT,'show',r['revision']+':'+r['path']);assert sha(b)==r['sha256'];return b
release=json.loads(git(ROOT,'show',REV+':.agent/evidence/123/root-fresh-qa1-release.json'))
assert release['owner']=='/root/fresh_qa123 independent Evaluator' and release['attempt']==1 and release['limit']==3
modeb=json.loads(rawref(release['mode_b_ref']));assert modeb['final_verdict']['approved'] is True and all(modeb[k]==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
for key in ('plan_ref','capture_driver_ref','policy_ref','evidence_ref','hosted_review_ref','final_seal_ref','approved_contract_ref'):rawref(release[key])
assert sha(DRIVER.read_bytes())==release['capture_driver_ref']['sha256']
evidence=json.loads(rawref(release['evidence_ref']));selection=json.loads(rawref(evidence['capture_selection_ref']))
capturepack=json.loads(rawref(evidence['verify_selection_ref']))['capture_pack_ref'];packs=[capturepack,evidence['pack_ref']]
jwrite(OUT/'entry-admission.json',dict(release_revision=REV,release_sha256=sha(git(ROOT,'show',REV+':.agent/evidence/123/root-fresh-qa1-release.json')),mode_b_ref=release['mode_b_ref'],source=SOURCE,driver_sha256=sha(DRIVER.read_bytes()),packs=packs,at=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='actual released inputs independently read; not QA verdict'))
def setup(lane,historical=False):
 target=Path('/home/cnross/.tmp/nizam-feature123-fresh-qa1-'+lane);assert not target.exists()
 directory=OUT/lane;directory.mkdir();captures=directory/'setup';captures.mkdir();serial=0
 def command(argv,cwd,input_bytes=None):
  nonlocal serial
  serial+=1;name='%02d'%serial;start=datetime.datetime.now(datetime.timezone.utc).isoformat();tick=time.monotonic()
  if input_bytes is not None:write(captures/(name+'.stdin'),input_bytes)
  child=subprocess.Popen(argv,cwd=cwd,stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  stdout,stderr=child.communicate(input_bytes);write(captures/(name+'.stdout.txt'),stdout);write(captures/(name+'.stderr.txt'),stderr)
  record=dict(argv=argv,cwd=str(cwd),child_pid=child.pid,started_at=start,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-tick,actual_exit=child.returncode,stdout=dict(path=name+'.stdout.txt',bytes=len(stdout),sha256=sha(stdout)),stderr=dict(path=name+'.stderr.txt',bytes=len(stderr),sha256=sha(stderr)),stdin_sha256=None if input_bytes is None else sha(input_bytes))
  jwrite(captures/(name+'.execution.json'),record);assert child.returncode==0,record
 command(['git','clone','--no-hardlinks','--no-checkout',str(ROOT),str(target)],ROOT)
 command(['git','switch','--detach','8ac94f6808e8197111197c9acbf59b2aa92efc7c' if historical else REV],target)
 command(['git','remote','set-url','origin','https://github.com/niq-cnr/nizam-framework.git'],target)
 assert not (target/'.git/objects/info/alternates').exists()
 assert git(target,'remote','get-url','origin').decode().strip()=='https://github.com/niq-cnr/nizam-framework.git'
 assert git(target,'rev-parse','v1.5.0^{commit}').decode().strip()=='f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852'
 if not historical:
  for number,reference in enumerate(packs,1):
   payload=rawref(reference);assert payload.startswith(b'# v2 git bundle\n') and b'\n\n' in payload
   bundle=captures/('selected-%s.bundle'%number);write(bundle,payload)
   command(['git','index-pack','--strict','--fix-thin','--stdin'],target,payload.split(b'\n\n',1)[1])
   command(['git','bundle','verify',str(bundle)],target)
   command(['git','fetch','--no-tags','--no-write-fetch-head',str(bundle),'refs/wa123/proof:refs/nizam/123/fresh-qa1-'+str(number)],target)
  for group,rows in evidence['candidate']['assessed_inputs'].items():
   for row in rows:
    path=target/row['path'];s=path.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and sha(path.read_bytes())==row['sha256'] and bool(s.st_mode&0o111)==row['executable'],row
  assert not (target/'.agent/evidence/123/experiment').exists()
 sentinel=directory/'outside-sentinel.txt';write(sentinel,('fresh-QA1 '+lane+' outside preservation sentinel\n').encode())
 jwrite(directory/'setup-summary.json',dict(lane=lane,repo=str(target),head=git(target,'rev-parse','HEAD').decode().strip(),origin=git(target,'remote','get-url','origin').decode().strip(),separate_git_metadata=str(target/'.git'),no_alternates=True,setup_commands=serial,selected_source=SOURCE,protected_rows=None if historical else 537,installed_rows=len(git(target,'ls-files','--','.nizam').splitlines()),sentinel=str(sentinel)))
 return target,directory,sentinel
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 futures={lane:pool.submit(setup,lane) for lane in ('candidate','default48','fixture')}
 contexts={lane:f.result() for lane,f in futures.items()}
commands={'candidate':['python3','tools/test_workflow_assurance.py','--case','ci-candidate-bound'],'default48':['python3','tools/test_workflow_assurance.py'],'fixture':['bash','tools/fixtures_self_test.sh']}
started={}
for lane,(repo,directory,sentinel) in contexts.items():
 argv=['python3',str(DRIVER),'--repo',str(repo),'--output',str(directory),'--name',lane,'--sentinel',str(sentinel),'--',*commands[lane]]
 stdout=(directory/'wrapper.stdout.txt').open('xb');stderr=(directory/'wrapper.stderr.txt').open('xb')
 child=subprocess.Popen(argv,cwd=repo,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=stdout,stderr=stderr,start_new_session=True);stdout.close();stderr.close()
 started[lane]=dict(wrapper_pid=child.pid,wrapper_argv=argv,repo=str(repo),output=str(directory));jwrite(directory/'wrapper-launch.json',started[lane])
jwrite(OUT/'long-lanes-started.json',started)
print(json.dumps(started,indent=2),flush=True)
core=setup('core');historical=setup('historical118',True)
jwrite(OUT/'remaining-contexts.json',dict(core=[str(v) for v in core],historical118=[str(v) for v in historical]))
print('Core and historical contexts prepared; three long lanes running.',flush=True)
