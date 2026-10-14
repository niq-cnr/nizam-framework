#!/usr/bin/env python3
"""Fresh independent QA128 command capture; no product or lifecycle writes."""
import datetime, hashlib, json, os, pathlib, platform, shutil, subprocess, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = ROOT / '.agent/evidence/128/qa1'
ADVERSARIAL = ROOT / '.agent/evidence/128-qa-adversarial.txt'
def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, obj):
    assert not path.exists(), str(path)
    path.write_text(json.dumps(obj, indent=2) + '\n')
def snapshot():
    tracked = git('ls-files').splitlines()
    paths = [p for p in tracked if not p.startswith(('.agent/evidence/', '.agent/qa/', '.agent/validator/'))]
    paths += [str(p.relative_to(ROOT)) for p in (ROOT / '.nizam').rglob('*') if p.is_file()]
    pins = {p:sha(ROOT/p) for p in sorted(set(paths))}
    return {'revision':git('rev-parse','HEAD'), 'tree':git('rev-parse','HEAD^{tree}'),
            'branch':git('branch','--show-current'), 'protected_sha256':pins,
            'status':git('status','--porcelain','--untracked-files=all'),
            'installed_inventory_count':sum(p.startswith('.nizam/') for p in pins)}
assert ROOT == pathlib.Path('/home/cnross/.tmp/nizam-feature128-qa1')
assert git('rev-parse','HEAD') == '32984eb88627ace080574d70143fb7ff11df8763'
contract = json.loads((ROOT/'.agent/contracts/128.json').read_text())
assert sha(ROOT/'.agent/contracts/128.json') == '8a9cb74fa0b10e8beb312a950d976697aca227c061f7ed03ced44fa7b031be89'
modeb=json.loads((ROOT/'.agent/validator/128-mode-b.json').read_text())
assert modeb['final_verdict']['approved'] and all(not modeb[k] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
before = snapshot(); write(OUT/'identity-before.json',before)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
environment = {'os':platform.platform(), 'python':sys.version, 'python_executable':shutil.which('python3'),
    'bash_executable':shutil.which('bash'), 'effective':{k:env.get(k) for k in ('PYTHONDONTWRITEBYTECODE','PATH','LANG','LC_ALL','TMPDIR')},
    'inherited_environment':'Other existing environment values inherited; credentials not serialized.'}
write(OUT/'environment.json',environment)
records=[]
for label, item in zip(('core-ready','validate','payload'), contract['verification']):
    command=item['command']; started=datetime.datetime.now(datetime.timezone.utc).isoformat(); start=time.monotonic()
    argv=['bash','-c',command]
    print('START',label,flush=True)
    p=subprocess.run(argv,cwd=ROOT,env=env,text=True,capture_output=True,timeout=1400)
    (OUT/(label+'.stdout.txt')).write_text(p.stdout); (OUT/(label+'.stderr.txt')).write_text(p.stderr)
    record={'owner':'/root/qa128','command':command,'argv':argv,'cwd':str(ROOT),'actual_exit':p.returncode,
      'started_at':started,'elapsed_seconds':time.monotonic()-start,'exercised_revision':before['revision'],
      'source_test_identity':'.agent/evidence/128/qa1/identity-before.json','environment':'.agent/evidence/128/qa1/environment.json',
      'stdout':str((OUT/(label+'.stdout.txt')).relative_to(ROOT)), 'stderr':str((OUT/(label+'.stderr.txt')).relative_to(ROOT))}
    if label=='core-ready':
        leaves=[json.loads(line.split(' ',1)[1]) for line in p.stdout.splitlines() if line.startswith('CORE_LEAF ')]
        record['leaf_count']=len(leaves)
        record['leaf_inventory_exact']= [x['argv'][2:] for x in leaves] == contract['leaf_argv']
        record['all_leaf_exit0_and_finalproof']=all(x['exit']==0 and x['proof'] and x['cleanup'] and x['event'] is None for x in leaves)
        record['aggregate_final_marker']=bool(p.stdout.splitlines()) and p.stdout.splitlines()[-1]=='PASS core-ready'
    write(OUT/(label+'.result.json'),record); records.append(record)
    print('DONE',label,'exit',p.returncode,round(record['elapsed_seconds'],2),'seconds',flush=True)
# Exactly one QA-origin extra: unavailable capability must fail before aggregate dispatch.
argv=['python3','tools/test_runtime_session.py','--check','core-ready','--require-sbcl']
start=time.monotonic(); p=subprocess.run(argv,cwd=ROOT,env=env,text=True,capture_output=True,timeout=15)
extra={'owner':'/root/qa128','description':'Unavailable SBCL request cannot acquire a partial stub core-ready success.',
    'command':'PYTHONDONTWRITEBYTECODE=1 python3 tools/test_runtime_session.py --check core-ready --require-sbcl',
    'argv':argv,'cwd':str(ROOT),'actual_exit':p.returncode,'elapsed_seconds':time.monotonic()-start,
    'exercised_revision':before['revision'],'source_test_identity':'.agent/evidence/128/qa1/identity-before.json',
    'environment':'.agent/evidence/128/qa1/environment.json','stdout':p.stdout,'stderr':p.stderr,
    'expected_exit':2,'expected_reason':'requested capability proof is unavailable in this partial stub suite; no skip permitted',
    'passed':p.returncode==2 and 'requested capability proof is unavailable in this partial stub suite; no skip permitted' in p.stderr and not p.stdout}
write(ADVERSARIAL,extra); print('DONE adversarial exit',p.returncode,'passed',extra['passed'],flush=True)
after=snapshot(); write(OUT/'identity-after.json',after)
unchanged=before['protected_sha256']==after['protected_sha256'] and before['revision']==after['revision']
checks={'contract_commands_run':3,'contract_commands_passed':sum(x['actual_exit']==0 for x in records),
        'exactly_one_extra':True,'adversarial_passed':extra['passed'],'protected_identities_unchanged':unchanged,
        'all_receipt_markers_valid':records[0].get('leaf_inventory_exact') and records[0].get('all_leaf_exit0_and_finalproof') and records[0].get('aggregate_final_marker') and records[0].get('leaf_count')==14}
write(OUT/'execution-summary.json',checks)
print(json.dumps(checks),flush=True)
sys.exit(0 if all((checks['contract_commands_passed']==3,extra['passed'],unchanged,checks['all_receipt_markers_valid'])) else 1)
