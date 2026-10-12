#!/usr/bin/env python3
"""Pre-code read-only metadata inspection, never feature acceptance execution."""
from pathlib import Path
import hashlib,json,subprocess
import jsonschema,yaml
r=Path.cwd(); base='45ceeb80eabc823400f2bb6044edcb4fa3aa9b2f'
def obj(p): return json.loads((r/p).read_bytes())
c=obj('.agent/contracts/114.json')
assert hashlib.sha256((r/'.agent/contracts/114.json').read_bytes()).hexdigest()=='6a5e4ac0ceb35ace0c3ed676c373dfd564aef47024b790fb7c648e91f79afa36'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==base
assert c['status']=='proposed' and c['base_revision']==base
jsonschema.validate(c,obj('.nizam/schema/contract.schema.json'))
f=obj('.agent/feature_list_015.json'); rows={x['id']:x for x in f['features']}
assert rows['114']['status']=='pending' and rows['114']['dependencies']==['113']
assert rows['113']['status']=='complete' and rows['113']['passes'] is True
assert [x['command'] for x in c['verification'][:6]]==rows['114']['acceptance_tests']
assert len(c['verification'])==12
for check in c['verification']:
 p=subprocess.run(['bash','-n','-c',check['command']],capture_output=True,text=True)
 assert p.returncode==0,p.stderr
print('PROPOSAL pin/current immutable base/status/schema and all12 command syntax verified; first6 canonical commands byte-exact. No acceptance command executed.')
phase=yaml.safe_load((r/'docs/planning/phase_015.yaml').read_text()); steps={x['id']:x for x in phase['steps']}
assert phase['status']=='in_progress' and steps['113']['status']=='COMPLETED' and steps['114']['status']=='PENDING'
for p in ['.agent/contracts/113.json','.agent/validator/113-mode-b.json','.agent/qa/113.json']:
 d=obj(p)
 if p.endswith('contracts/113.json'): assert d['status']=='approved'
 else: assert d['final_verdict']['approved'] is True and all(d[k]==[] for k in ['issues','missing_acceptance_coverage','unsupported_claims'])
qa=obj('.agent/qa/113.json'); assert qa['qa_pass'] is True and qa['checks_run']==qa['checks_passed']==len(qa['checks'])==16
for p in qa['evidence_files']+[rows['113']['evidence']]: assert (r/p).is_file() and (r/p).stat().st_size>0,p
assert subprocess.run(['git','merge-base','--is-ancestor',qa['candidate_commit'],base],capture_output=True).returncode==0
print('Actual completed113 contract/ModeB/fresh16QA/ownspot/capture files and source-candidate ancestry inspected; historical checkers not executed.')
pre=obj('.agent/evidence/114/predecessor113-pr-premerge.json')['pr']; merged=obj('.agent/evidence/114/predecessor113-merge-main.json')
assert pre['number']==88 and pre['headRefOid']=='7e2c26de846ba53ac409e5276bbb5c1690883099'
assert pre['mergeStateStatus']=='CLEAN' and pre['mergeable']=='MERGEABLE' and pre['isDraft'] is False
assert len(pre['statusCheckRollup'])==6 and all(x['conclusion']=='SUCCESS' for x in pre['statusCheckRollup'])
assert merged['pr']['state']=='MERGED' and merged['pr']['headRefOid']==pre['headRefOid'] and merged['pr']['mergeCommit']['oid']==base
assert merged['main']['headSha']==base and merged['main']['conclusion']=='success'
assert len(merged['main']['jobs'])==5 and all(x['conclusion']=='success' for x in merged['main']['jobs'])
print('Actual prerequisite PR88 sixSUCCESS/CLEAN and merged post113Main fiveSUCCESS proof bound to45ceeb; not inherited as114 acceptance.')
state=obj('.agent/run_state.json'); assert state['scope_budget']['total_lines_changed']==6779 and state['scope_budget']['original_estimate_lines']==7200 and state['scope_budget']['ceiling_130pct']==9360
assert 9360-6779==2581
assert all(v['limit']==3 and v['attempts']==0 for k,v in state['circuit_breaker'].items() if k.startswith('114-'))
packets={p['id']:p for p in obj('docs/planning/backlog_dag.json')['packets']}
for name in ['NIP3-113','NIP3-114','PLAN-WA','PLAN-016']: assert name in packets
for name in ['PLAN-WA','PLAN-016']:
 p=packets[name]; assert p['status']=='pending' and p['authority_status']=='authorized' and p['prerequisites']['technical']['satisfied'] is False and p['prerequisites']['evidence']['satisfied'] is False
assert all(not x['claim_working'] for x in f['case_matrix'])
print('Actual budget6779/9360, remaining2581 and untouched114 zero/3 counters; WA/016 pending and livecase claimsfalse externally anchored.')
print('METADATA REVIEW PASS; no product/helper/test implementation, acceptance execution, source/canonical writes or future gate assumptions.')
