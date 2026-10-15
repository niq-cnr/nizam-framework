import hashlib,json,os,subprocess,concurrent.futures
from pathlib import Path
out=Path('/home/cnross/.tmp/nizam-feature123-fresh-qa1-run');contexts=json.loads((out/'remaining-contexts.json').read_bytes());driver=Path('/home/cnross/workspace02/nizam-framework/.agent/evidence/123/fresh-qa-capture1.py')
assert hashlib.sha256(driver.read_bytes()).hexdigest()=='e9e9417c39548919b892f0b7436b885b72a26b781d15455e62daebe9367c5ac0'
extra=(out/'adversarial.py').read_bytes();(out/'adversarial.frozen-sha256').write_text(hashlib.sha256(extra).hexdigest()+'\n')
def run(lane,name,argv,expected=0,stdin=None):
 repo,directory,sentinel=map(Path,contexts[lane]);args=['python3',str(driver),'--repo',str(repo),'--output',str(directory),'--name',name,'--sentinel',str(sentinel),'--expected-exit',str(expected)]
 if stdin:args+=['--stdin',str(stdin)]
 args+=['--',*argv]
 with (directory/(name+'.wrapper.stdout.txt')).open('xb') as stdout,(directory/(name+'.wrapper.stderr.txt')).open('xb') as stderr:
  child=subprocess.Popen(args,cwd=repo,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=stdout,stderr=stderr)
  with (directory/(name+'.wrapper-started.json')).open('x') as f:json.dump(dict(argv=args,wrapper_pid=child.pid),f,indent=2)
  rc=child.wait()
 print(lane,name,'wrapper_actual_exit',rc,flush=True)
 assert rc==0,(lane,name,rc)
 return json.loads((directory/(name+'.capture-summary.json')).read_bytes())
def core():
 for name,argv in [('blocker',['python3','tools/test_workflow_assurance.py','--case','ci-blocker-rejected']),('readiness',['python3','tools/test_workflow_assurance.py','--check','controls-ready']),('validate',['bash','tools/validate.sh']),('payload',['bash','tools/validate.sh','--payload'])]:run('core',name,argv)
 stale=run('core','current-stale118',['python3','tools/test_workflow_assurance.py','--check','foundation-ready'],1)
 diagnostic=(out/'core/current-stale118.stderr.txt').read_text();assert diagnostic=='AssuranceError: pinned entry bytes/mode changed: tools/workflow_assurance.py\n',diagnostic
 run('core','adversarial',['python3','-'],stdin=out/'adversarial.py')
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 first=pool.submit(core);second=pool.submit(run,'historical118','historical118',['python3','tools/test_workflow_assurance.py','--check','foundation-ready'])
 first.result();second.result()
print('All core/history commands and exactly one own extra completed with expected exits and physical preservation.',flush=True)
