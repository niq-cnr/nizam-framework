import hashlib,json,re,subprocess
from pathlib import Path
import jsonschema
E=Path('.agent/evidence/117')
def load(p): return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a])
q=load('.agent/qa/117.json');c=load(E/'source-candidate.json');contract=load('.agent/contracts/117.json');b=load(E/'acceptance-bundle.json');producer=load(E/'producer-interface.json')
jsonschema.validate(q,load('.nizam/schema/qa_verdict.schema.json'))
assert set(producer['qa']['required'])<=set(q)
assert q['feature_id']=='117' and type(q['actor']) is str and q['actor']=='/root/wa_acceptance117'
roles=load(E/'role-sessions.json');m=load('.agent/validator/117-mode-b.json')
assert q['actor'] not in {m['actor'],*(roles[x]['agent_id'] for x in ['test_author','developer','acceptance_reviewer'])}
for k in ['revision','source_sha256','sealed_dependencies_sha256']:assert q[k]==c[k]==m[k]
assert q['qa_pass'] is True
for k in ['checks_run','checks_passed']:assert type(q[k]) is int and q[k]==12
assert q['final_verdict']['approved'] is True
for k in ['issues','missing_acceptance_coverage','unsupported_claims','required_fixes']:assert type(q[k]) is list and q[k]==[]
assert len(q['checks'])==12 and len(q['evidence_files'])==13==len(set(q['evidence_files']))
def raw(path,command):
    text=Path(path).read_text()
    for key,value in [('COMMAND',command),('REVISION',c['revision']),('EXIT','0')]:
        assert re.findall('^'+key+': (.*)$',text,re.M)==[value]
    for h in ['STDOUT:','STDERR:']:assert text.splitlines().count(h)==1
for expected,row in zip(contract['verification'],q['checks']):
    assert {k:row[k] for k in expected}==expected
    assert type(row['exit_code']) is int and row['exit_code']==0
    assert row['evidence'] in q['evidence_files'] and row['sha256']==sha(row['evidence'])
    raw(row['evidence'],row['command'])
a=q['adversarial'];assert a['performed'] is True and a['evidence'] in q['evidence_files']
assert a['command'] not in [r['command'] for r in q['checks']]
assert a['evidence'] not in [r['evidence'] for r in q['checks']]
assert q['adversarial_check']['evidence']==a['evidence'] and q['adversarial_check']['result']=='pass'
raw(a['evidence'],a['command'])
assert len(c['source_sha256'])==4 and len(b['inputs'])==27
assert c['sealed_dependencies_sha256']=={r['path']:r['sha256'] for r in b['inputs']}
for revision,rows in [(c['revision'],[{'path':p,'sha256':h} for p,h in c['source_sha256'].items()]),(b['baseline']['commit'],b['inputs'])]:
    for row in rows:
        p=Path(row['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents))
        assert sha(p)==row['sha256']==hashlib.sha256(git('show',revision+':'+str(p))).hexdigest()
        assert bool(p.stat().st_mode & 0o111)==(git('ls-tree',revision,'--',str(p)).decode().split()[0]=='100755')
for label in ['before','after']:
    r=load(E/('qa-attempt1-bindings-'+label+'.json'));assert r['core_count']==4 and r['sealed_count']==27 and len(r['verified'])==31
assert git('rev-parse',c['revision']+'^{tree}').decode().strip()==c['tree']
print('PASS: installed QA schema, strict producer fields/types/independence, exact ordered12 commands,13 unique proof paths, actual proof digests and raw headers')
print('PASS: four current/GitSourceC core inputs and all27 current/GitB sealed inputs; bytes and executable modes unchanged after ownspot')
print('QA_SHA256: '+sha('.agent/qa/117.json'))
