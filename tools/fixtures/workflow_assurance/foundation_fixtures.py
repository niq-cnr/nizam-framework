"""Independent mutation fixtures; never a product readiness implementation."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
E = '.agent/evidence/118/'

def canonical(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def require(ok, msg):
    if not ok: raise AssertionError('POLICY_ASSERTION: ' + msg)
def load(path):
    spec=importlib.util.spec_from_file_location('fixture_module', path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def git(root,*args): return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.PIPE).decode().strip()
def read(root,path): return json.loads((Path(root)/path).read_bytes())
def write(root,path,v):
    p=Path(root)/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v if isinstance(v,bytes) else canonical(v))

def capture(root,command,revision,path):
    r=subprocess.run(command,shell=True,cwd=root,capture_output=True,text=True)
    raw='COMMAND: '+command+'\nREVISION: '+revision+'\nEXIT: '+str(r.returncode)+'\nSTDOUT:\n'+r.stdout+'\nSTDERR:\n'+r.stderr
    write(root,path,raw.encode());return r

def binding(root,revision):
    manifest=read(root,E+'runtime-inputs.json');api=read(root,E+'api-interface.json')
    maps={name:{p:sha((Path(root)/p).read_bytes()) for p in paths} for name,paths in [('source_sha256',manifest['core_paths']),('runtime_sha256',manifest['runtime_paths']),('historical_sha256',api['historical_paths'])]}
    return dict(revision=revision,tree=git(root,'rev-parse',revision+'^{tree}'),**maps)

def baseline_setup(destination):
    root=Path(destination); require(not root.exists(),'new owned baseline scratch root')
    subprocess.run(['git','clone','-q','--shared',str(ROOT),str(root)],check=True)
    revision=git(ROOT,'rev-parse','HEAD');git(root,'checkout','--detach','-q',revision)
    cases=read(root,E+'api-interface.json')['current_cases'];checks=[]
    for i,item in enumerate(cases):
        path=E+'fixture-current20-'+str(i)+'.txt';r=capture(root,item['command'],revision,path)
        require(r.returncode==0,'current20 setup '+item['case']);checks.append(dict(item,exit_code=r.returncode,evidence=path,sha256=sha((root/path).read_bytes())))
    candidate=binding(root,revision)
    # These explicitly synthetic actor/session labels belong only to baseline parser fixtures.
    receipt=dict(candidate,feature='118',actor='fixture-only-prerequisite',session_id='fixture-only-prerequisite-session',passed=True,checks_run=20,checks_passed=20,checks=checks)
    write(root,E+'source-candidate.json',candidate);write(root,E+'prerequisite20.json',receipt)
    write(root,E+'FIXTURE-NOT-SOURCEC.json',{'purpose':'Independent naive baseline fixture, never actual SourceC prerequisite evidence','actual_executor':'/root/wa_review118','revision':revision})
    print('CURRENT20_SETUP: 20 actual commands PASS');return root

def reject(api,root,value,label):
    try: api.verify_foundation_ready(root,value)
    except api.AssuranceError as exc:
        require(bool(str(exc)),'nonempty rejection '+label);return
    require(False,label+' invalid receipt accepted')

def run_foundation(api):
    require(callable(getattr(api,'verify_foundation_ready',None)),'foundation API callable')
    good=read(ROOT,E+'prerequisite20.json'); require(api.verify_foundation_ready(ROOT,good) is True,'actual independent prerequisite positive')
    mutations=[('missing-case',lambda v:v['checks'].pop()),('duplicate-case',lambda v:v['checks'].__setitem__(1,copy.deepcopy(v['checks'][0]))),('foreign-case',lambda v:v['checks'][0].update(case='foreign')),('wrong-command',lambda v:v['checks'][0].update(command='true')),('nonzero-exit',lambda v:v['checks'][0].update(exit_code=1)),('bool-exit',lambda v:v['checks'][0].update(exit_code=False)),('bool-count',lambda v:v.update(checks_run=True)),('bool-passed',lambda v:v.update(passed=1)),('actor-type',lambda v:v.update(actor=[])),('session-type',lambda v:v.update(session_id={})),('unsafe-path',lambda v:v['checks'][0].update(evidence='../escape')),('stale-revision',lambda v:v.update(revision='0'*40)),('extra-key',lambda v:v.update(unknown=True)),('missing-runtime',lambda v:v['runtime_sha256'].pop(next(iter(v['runtime_sha256'])))),('unknown-runtime',lambda v:v['runtime_sha256'].update({'unknown.py':'0'*64}))]
    roles=read(ROOT,E+'role-sessions.json')
    for role,row in roles.items():
        mutations.extend([(role+'-actor',lambda v,row=row:v.update(actor=row['agent_id'])),(role+'-session',lambda v,row=row:v.update(session_id=row['session_id']))])
    for name,change in mutations:
        value=copy.deepcopy(good);change(value);reject(api,ROOT,value,name)
    # All filesystem attacks use separate scratch state. Git objects remain real.
    with tempfile.TemporaryDirectory(prefix='nizam118-acceptance-') as parent:
        root=Path(parent)/'repo';subprocess.run(['git','clone','-q','--shared','--no-checkout',str(ROOT),str(root)],check=True)
        paths=set(good['source_sha256'])|set(good['runtime_sha256'])|set(good['historical_sha256'])|{E+'source-candidate.json',E+'prerequisite20.json'}|{r['evidence'] for r in good['checks']}
        for p in paths:
            target=root/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
        require(api.verify_foundation_ready(root,good) is True,'copied candidate positive')
        candidate=read(root,E+'source-candidate.json')
        for key,value in [('tree','0'*40),('revision','0'*40),('source_sha256',{p:'0'*64 for p in good['source_sha256']}),('runtime_sha256',{})]:
            bad=copy.deepcopy(candidate);bad[key]=value;write(root,E+'source-candidate.json',bad);receipt=copy.deepcopy(good);receipt[key]=value;reject(api,root,receipt,'matched false candidate '+key)
        write(root,E+'source-candidate.json',candidate)
        first=good['checks'][0];target=root/first['evidence'];saved=target.read_bytes()
        for raw in (saved+b'EXIT: 0\n',saved.replace(b'STDOUT:\n',b'NO_STDOUT:\n',1),saved.replace(good['revision'].encode(),b'0'*40,1)):
            target.write_bytes(raw);value=copy.deepcopy(good);value['checks'][0]['sha256']=sha(raw);reject(api,root,value,'malformed raw proof after rehash')
        target.write_bytes(saved);target.unlink();reject(api,root,good,'missing raw proof');target.write_bytes(saved)
        for p in (list(good['source_sha256'])[0],E+'foundation-fixtures.py',list(good['historical_sha256'])[0]):
            target=root/p;saved=target.read_bytes();mode=target.stat().st_mode
            target.write_bytes(saved+b'\n');reject(api,root,good,'changed input '+p);target.write_bytes(saved)
            target.chmod(mode ^ 0o111);reject(api,root,good,'changed executable '+p);target.chmod(mode)
            target.unlink();target.symlink_to(root / (E + 'api-interface.json'));reject(api,root,good,'symlink input '+p);target.unlink();target.write_bytes(saved);target.chmod(mode)
        git(root,'read-tree',good['revision']);git(root,'config','user.name','Independent continuity fixture');git(root,'config','user.email','fixture@example.invalid');write(root,E+'record-only.json',{'record_only':True});git(root,'add',E+'record-only.json');git(root,'commit','-qm','record-only HEAD advance')
        require(git(root,'rev-parse','HEAD')!=good['revision'] and api.verify_foundation_ready(root,good) is True,'record-only HEAD continuity')
    print('PASS foundation-ready: valid current20 receipt and independent typed/proof/identity/continuity attacks')
