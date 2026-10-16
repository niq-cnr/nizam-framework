"""Read-only final PR integration admission; no product import or acceptance run."""
import ast, hashlib, json, subprocess
from pathlib import Path
O=Path('/home/cnross/.tmp/nizam-feature123-final-integration1')
R=Path('/home/cnross/.tmp/nizam-performance-attribution1')
HEAD='599d7c5aa0c0c80ce8da596c7aeae2924d7dca04'
BASE='79811ef76df950b8151e2af62637ab7d1df34305'
def read(name): return json.loads((O/(name+'.stdout.txt')).read_bytes())
def git(*a): return subprocess.check_output(['git','-C',str(R),*a])
def sha(b): return hashlib.sha256(b).hexdigest()
run=read('terminal-run'); jobs=read('terminal-jobs')['jobs']; checks=read('terminal-checks')
assert run['id']==38802791707 and run['run_attempt']==1 and run['head_sha']==HEAD
assert run['status']=='completed' and run['conclusion']=='success'
expected={'validate','e2e_bootstrap','fixtures_self_test','convergent_review','self_governance'}
assert {j['name'] for j in jobs}==expected and all(j['status']=='completed' and j['conclusion']=='success' for j in jobs)
assert checks['headRefOid']==HEAD and checks['baseRefOid']==BASE and checks['mergeable']=='MERGEABLE' and checks['mergeStateStatus']=='CLEAN'
assert {c['name'] for c in checks['statusCheckRollup']}==expected|{'closeout'}
assert all(c['status']=='COMPLETED' and c['conclusion']=='SUCCESS' for c in checks['statusCheckRollup'])
feedback=read('terminal-feedback'); assert not feedback.get('errors')
pr=feedback['data']['repository']['pullRequest'];assert pr['headRefOid']==HEAD and pr['baseRefOid']==BASE and pr['state']=='OPEN'
for key in ('reviews','comments','reviewThreads'): assert pr[key]['nodes']==[] and not pr[key]['pageInfo']['hasNextPage']
cap=next(j for j in jobs if j['name']=='convergent_review')
for name in ('WA123 capture','WA123 verify','Preserve actual WA123 proof'): assert next(s for s in cap['steps'] if s['name']==name)['conclusion']=='skipped'
rows=[]
for line in (O/'terminal-logs.stdout.txt').read_text().splitlines():
 parts=line.split('\t',2);assert len(parts)==3;rows.append((parts[0],parts[1],parts[2].lstrip('\ufeff').partition(' ')[2]))
assert {j for j,step,text in rows if step=='Complete job'}==expected
helper=git('show',HEAD+':.agent/evidence/123/fresh-qa1/finalize2.py')
assert sha(helper)=='55128e72b14e620f7b35b8e0d68293af39c53236d61de4c88eb1cf469fda1872'
function=next(n for n in ast.parse(helper).body if isinstance(n,ast.FunctionDef) and n.name=='inventory_ast')
ns={'ast':ast};exec(compile(ast.Module(body=[function],type_ignores=[]),'frozen inventory_ast','exec'),ns)
source=git('show',HEAD+':tools/test_workflow_assurance.py');cases=ns['inventory_ast'](source);assert len(cases)==len(set(cases))==48
passes=[text[5:] for job,step,text in rows if job=='fixtures_self_test' and step=='Run PYTHONDONTWRITEBYTECODE=1 python3 tools/test_workflow_assurance.py' and text.startswith('PASS ')]
assert [p for p in passes if p in cases]==cases
observer=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='controls_foreign_observer')
aux=[n.args[0].value[5:] for n in ast.walk(observer) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='print' and n.args and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str) and n.args[0].value.startswith('PASS ')]
assert len(aux)==1 and [p for p in passes if p not in cases]==aux
for job,step in (('fixtures_self_test','Run bash tools/fixtures_self_test.sh'),('convergent_review','Run fixture self-test')):
 assert sum(j==job and s==step and text=='SELF-TEST OK: 166/166 fixtures accounted for, 0 failed' for j,s,text in rows)==1
receipts=[(job,json.loads(text.split('=',1)[1])) for job,step,text in rows if step=='Record maintenance checkout source identity' and text.startswith('MAINTENANCE_CHECKOUT_RECEIPT={')]
assert len(receipts)==2 and {j for j,r in receipts}=={'fixtures_self_test','convergent_review'}
checkout=git('rev-parse','refs/wa123/final-integration-pr').decode().strip()
assert checkout=='b3833b699c5f2d18b1b8f8096ab1139bda33abe7'
assert git('rev-parse',checkout+'^{tree}')==git('rev-parse',HEAD+'^{tree}')
assert git('show','-s','--format=%P',checkout).decode().strip().split()==[BASE,HEAD]
for job,receipt in receipts:
 assert receipt['checkout_sha']==checkout
 for path,digest in receipt['source_sha256'].items(): assert sha(git('show',HEAD+':'+path))==digest
frames=[]
for path in sorted(O.glob('*.execution.json')):
 f=json.loads(path.read_bytes());expected_exit=1 if path.name=='capable-job-log.execution.json' else 0
 assert f['actual_exit']==expected_exit and not f['timed_out'],path.name
 for stream in ('stdout','stderr'):
  b=Path(f[stream]['path']).read_bytes();assert sha(b)==f[stream]['sha256'] and len(b)==f[stream]['bytes']
 frames.append({'path':path.name,'actual_exit':f['actual_exit']})
facts={'role':'Root Orchestrator','scope':'Final PR CI and feedback admission only; no merge/main CI claim','head':HEAD,'base':BASE,'run':38802791707,'attempt':1,'required_checks_passed':6,'workflow_jobs_passed':5,'actual_checkout':checkout,'checkout_tree_matches_head':True,'source_identity_receipts':2,'ordered_default_cases':cases,'auxiliary_pass_literals':aux,'fixture_file_inventory_per_job':'166/166','wa123_operations_skipped':True,'feedback_clear':True,'verified_frames':frames,'known_original_log_observation':'Premature capable-job-log returned1 because whole run was still in progress; original retained. Terminal collection0 is a changed-precondition observation, not a workflow rerun.','collector_sha256':'5eb17f67b155d2595267b6aa8c030ca8def95c6f4fb4216570708b44eef06075','log_sha256':sha((O/'terminal-logs.stdout.txt').read_bytes()),'log_bytes':(O/'terminal-logs.stdout.txt').stat().st_size}
p=O/'terminal-admission.json';assert not p.exists();p.write_text(json.dumps(facts,indent=2)+'\n')
print(json.dumps({'actual_exit':0,'checks_passed':6,'default_cases':len(cases),'fixture_inventory':'166/166','checkout':checkout,'feedback_clear':True}))
