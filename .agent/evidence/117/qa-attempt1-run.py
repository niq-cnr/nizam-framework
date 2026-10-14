import hashlib, json, os, stat, subprocess
from pathlib import Path
ROOT=Path.cwd().resolve()
E=Path('.agent/evidence/117')
def load(p): return json.loads(Path(p).read_bytes())
def sha(b): return hashlib.sha256(b).hexdigest()
def git(*a): return subprocess.check_output(['git',*a])
c=load(E/'source-candidate.json'); b=load(E/'acceptance-bundle.json'); contract=load('.agent/contracts/117.json')
assert ROOT == Path('/home/cnross/.tmp/nizam-117-qa-attempt1-spyqvr9j')
assert load(E/'qa-attempt1.json')['owner']=='/root/wa_acceptance117'
assert contract['status']=='approved'
assert len(contract['verification'])==12
assert c['revision']=='2ab311bde4e104ec4a2b1b739fe8fa91b48fe5b7'
assert git('rev-parse',c['revision']+'^{tree}').decode().strip()==c['tree']
m=load('.agent/validator/117-mode-b.json')
assert m['final_verdict']['approved'] is True
assert all(type(m[k]) is list and m[k]==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
for k in ('revision','source_sha256','sealed_dependencies_sha256'): assert m[k]==c[k]
def bindings(label):
    rows=[]
    assert len(b['inputs'])==27
    assert c['sealed_dependencies_sha256']=={r['path']:r['sha256'] for r in b['inputs']}
    for revision,inputs in [(c['revision'],[{'path':p,'sha256':h} for p,h in c['source_sha256'].items()]),(b['baseline']['commit'],b['inputs'])]:
        for row in inputs:
            p=Path(row['path'])
            assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents))
            blob=git('show',revision+':'+str(p)); mode=git('ls-tree',revision,'--',str(p)).decode().split()[0]
            assert sha(p.read_bytes())==sha(blob)==row['sha256'],str(p)
            assert bool(p.stat().st_mode & 0o111)==(mode=='100755')
            rows.append({'path':str(p),'git_revision':revision,'sha256':sha(blob),'mode':mode})
    path=E/('qa-attempt1-bindings-'+label+'.json'); assert not path.exists()
    path.write_text(json.dumps({'source_revision':c['revision'],'checkout_revision':git('rev-parse','HEAD').decode().strip(),'core_count':4,'sealed_count':27,'verified':rows},indent=2)+'\n')
bindings('before')
checks=[]
for i,row in enumerate(contract['verification'],1):
    result=subprocess.run(row['command'],shell=True,executable='/bin/bash',capture_output=True,text=True)
    p=E/f'qa-attempt1-check-{i:02}.txt'; assert not p.exists()
    p.write_text(f"COMMAND: {row['command']}\nREVISION: {c['revision']}\nEXIT: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    checks.append(dict(row,exit_code=result.returncode,evidence=str(p),sha256=sha(p.read_bytes())))
    (E/'qa-attempt1-results.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(f"CHECK {i}/12: exit {result.returncode}: {row['acceptance_test']}",flush=True)
    if result.returncode: raise SystemExit(result.returncode)
bindings('after')
