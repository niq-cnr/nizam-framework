import ast,gzip,hashlib,json,subprocess
from collections import Counter
from pathlib import Path
root=Path.cwd();candidate='abc822f1cca7d246c82557e9181f051fb40f6cfc';evidence='e72705879bce518623d51f9de88ea85f1557f759'
git=lambda *args:subprocess.check_output(['git',*args]);read=lambda rev,path:git('show',rev+':'+path)
sha=lambda raw:hashlib.sha256(raw).hexdigest();path='tools/test_runtime_session.py'
old=(root/path).read_bytes();new=read(candidate,path)
assert sha(old)=='a61a2ec17e729a6c6ea0b9090a639beb0903db49c4d9869b948d908d568bdf1e'
assert sha(new)=='d186e915424040b32ee9c232d952a170ec0a806cf415126abf34a8a81eda0431'
assert git('rev-parse',candidate+':'+path).decode().strip()=='5af7a9f5683886dff6b607ec39f87490b9cddbd9'
a,b=map(ast.parse,(old,new));definition=lambda tree:{n.name:ast.dump(n) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
da,db=map(definition,(a,b));changed={n for n in da if da[n]!=db[n]};added=set(db)-set(da)
assert changed=={'live_rendered_overflow_control','live_scenario','live_terminate','live_unresolved_capture'}
assert added=={'group_descendant_fixture','live_group_descendant','live_partial_frame_deadline'} and not set(da)-set(db)
assert [ast.dump(n) for n in a.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))]==[ast.dump(n) for n in b.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))]
requires=lambda tree:Counter(ast.dump(n) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require')
adjusted=ast.parse(old.replace(b"before['outstanding_operation_ref'] == request['operation_id'] and",b"before['outstanding_operation_ref'] == str(s.operation(request['operation_id']).resolve()) and",1))
assert not requires(adjusted)-requires(b);compile(new,path,'exec')
for protected in ('tools/runtime_session.py','.agent/contracts/129.json','.agent/evidence/129/interface-intent1.json'):
    assert read(candidate,protected)==(root/protected).read_bytes()
assert len(json.loads((root/'.agent/contracts/129.json').read_bytes())['verification'])==11
assert git('rev-parse',candidate+':.nizam')==git('rev-parse','HEAD:.nizam')
assert len(git('ls-tree','-r','--name-only',candidate,'.nizam').splitlines())==239
prefix='.agent/evidence/129/fixture-correction2/'
index=json.loads(read(evidence,prefix+'raw-index.json'));assert len(index)==15
for name,entry in index.items():
    data=read(evidence,prefix+name);assert len(data)==entry['bytes'] and sha(data)==entry['sha256'],name
for name,pid in [('static1',3941310),('native1',3944220)]:
    frame=json.loads(read(evidence,prefix+name+'.execution.json'))
    assert frame['actual_exit']==0 and frame['child_pid']==pid and not frame['timed_out'] and frame['exercised_revision']==candidate
    for stream in ('stdin','stdout','stderr'):
        meta=frame.get(stream)
        if meta:
            data=read(evidence,prefix+Path(meta['path']).name);assert len(data)==meta['bytes'] and sha(data)==meta['sha256']
before=gzip.decompress(read(evidence,prefix+'native1.preservation-before.json.gz'))
assert before==gzip.decompress(read(evidence,prefix+'native1.preservation-after.json.gz'))
rows=json.loads(before)['rows'];assert len(rows)==15960 and sum(r['path'].startswith('.nizam/') for r in rows)==239
events={line.split(' ',1)[0]:json.loads(line.split(' ',1)[1]) for line in read(evidence,prefix+'native1.stdout.txt').decode().splitlines()}
start,ready,term,result,cleanup=[events[n] for n in ('NATIVE_START','NATIVE_READY','NATIVE_AFTER_GROUP_TERM','NATIVE_RESULT','NATIVE_CLEANUP')]
expression=read(evidence,prefix+'native-expression.lisp');assert expression.endswith(b'\n') and sha(expression[:-1])==start['spawn_form_sha256']
assert start['argv'][start['argv'].index('--eval')+1].encode()==expression[:-1]
assert ready['pid']==result['descendant_pid']==3944225 and ready['ppid']==ready['pgid']==start['pid']==3944223
assert ready['actual_TERM_ignored_with_progress'] and term['leader_live_token'] is None and term['descendant_still_live_token']==ready['child_token']
assert result['observed_descendant_dead_after_group_KILL'] and result['unrelated_survived'] and result['actual_elapsed_seconds']<15 and not result['runtime_controller_or_selector_executed']
assert cleanup['remaining_owned']=={} and cleanup['unrelated_exit']==-15
archive=subprocess.check_output(['git','-C','/home/cnross/.tmp/nizam-129-postsource-fixture-author2','rev-parse','refs/heads/archive/129-fixture-author2-prequalification-a3dffed6']).decode().strip()
assert archive=='a3dffed6e895ae6a3e039f36d5d2f95e6bbcfe24'
print('STATIC_PASS complete bundle allowed4function delta/3helpers; all old assertions except justified canonicalref retained;11commands/protected/installed239;15indexed author files/2actual0 frames/15960 preservation rows; native S1 exactexpression/PIDgroup/TERMignore/KILLdeath/sentinel/cleanup; superseded archive retained. No reviewer runtime/controller/selector execution.')
