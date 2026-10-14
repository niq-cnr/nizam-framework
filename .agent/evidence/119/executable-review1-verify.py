import hashlib,json,pathlib,subprocess
R=pathlib.Path.cwd(); E=R/'.agent/evidence/119'
def sha(b): return hashlib.sha256(b).hexdigest()
def obj(blob): return subprocess.check_output(['git','cat-file','blob',blob])
def read(p): return json.loads((R/p).read_text())
def pinned(p,pin):
    data=(R/p).read_bytes(); assert sha(data)==pin['sha256']; assert obj(pin['git_blob'])==data
seal=read('.agent/evidence/119/author1-executable-seal.json')
for p,pin in seal['files'].items(): pinned(p,pin)
provisional=read('.agent/evidence/119/author1-provisional-seal.json')
for p,pin in provisional['files'].items():
    data=subprocess.check_output(['git','show','833b97b2116d630c4af937e23b7ad89eb442ee77:'+p]); assert sha(data)==pin['sha256'] and obj(pin['git_blob'])==data
for p in ('.agent/evidence/119/author1-controls.py','.agent/evidence/119/author1-captures.json','.agent/evidence/119/author1-provisional-seal.json'):
    assert (R/p).read_bytes()==subprocess.check_output(['git','show','833b97b2116d630c4af937e23b7ad89eb442ee77:'+p])
controls=read('.agent/evidence/119/author1-executable-controls-captures.json'); preservation=read('.agent/evidence/119/author1-executable-preservation-captures.json'); historical=read('.agent/evidence/119/author1-executable-historical2-captures.json')
for rows in (controls,preservation,historical):
    for row in rows:
        for key in ('stdout','stderr'): assert sha((R/row[key]).read_bytes())==row[key+'_sha256']
        for p,pin in row.get('inputs',{}).items(): assert sha(obj(pin['git_blob']))==pin['sha256']
assert len(controls)==18
names=('approve-empty','advisory-visible','block-carried','reject-issues','reject-missing-coverage','reject-unsupported')
for i,name in enumerate(names):
    a,b,c=controls[3*i:3*i+3]; assert [r['exit'] for r in (a,b,c)]==[0,1,0]
    assert [r['label'] for r in (a,b,c)]==[name+'-positive',name+'-semantic-red',name+'-restored']
    assert (R/a['stdout']).read_text().strip()=='PASS '+name and (R/c['stdout']).read_text().strip()=='PASS '+name
    assert not (R/b['stdout']).read_bytes() and 'POLICY_ASSERTION: ' in b['expected_diagnostic'] and b['expected_diagnostic'] in (R/b['stderr']).read_text()
assert len([r for r in preservation if r['label'].startswith('legacy-') and r['exit']==0])==20
live=next(r for r in preservation if r['label']=='live-stale118'); assert live['exit']==1 and 'pinned entry bytes/mode changed: tools/workflow_assurance.py' in (R/live['stderr']).read_text()
assert len(historical)==3 and all(r['exit']==0 for r in historical) and 'PASS foundation-ready:' in (R/historical[-1]['stdout']).read_text()
assert read('.agent/evidence/119/author1-executable-preservation-run.json')['exit']==1
ids=read('.agent/evidence/119/author1-executable-historical2-identities.json'); assert ids['revision']=='8ac94f6808e8197111197c9acbf59b2aa92efc7c'
for path,pin in ids['inputs'].items():
    data=obj(pin['git_blob']); assert sha(data)==pin['sha256']
    suffix=next(p for p in ('tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/119.json') if path.endswith(p))
    revision='8ac94f6808e8197111197c9acbf59b2aa92efc7c' if suffix.startswith('tools/') else '9a999591d64d05458d8dc650b00f05361516203f'
    assert data==subprocess.check_output(['git','show',revision+':'+suffix])
own=read('.agent/evidence/119/executable-review1-captures.json'); assert len(own)==20
for row in own:
    for key in ('stdout','stderr'): assert sha((R/row[key]).read_bytes())==row[key+'_sha256']
    for p,pin in row['inputs'].items(): pinned(p,pin)
h=read('.agent/evidence/119/executable-review1-historical-foundation.json'); assert h['actual_exit']==0 and h['revision']==ids['revision']
for key in ('stdout','stderr'): assert sha((R/h[key]).read_bytes())==h[key+'_sha256']
print('PASS14 author finalseal pins; immutable provisional pins; author18 semantic controls,20 current positives, retained helper failure, repaired historical positive; own20 captures and own historical positive; Source/test/approval unchanged')
