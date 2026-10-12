#!/usr/bin/env python3
"""Feature114 independent checks; controls are scratch models, never acceptance."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import yaml

HERE=Path(__file__).resolve().parent
PRIVATE=HERE/'private'
BASE=PRIVATE/'base'
ORIGIN='45ceeb80eabc823400f2bb6044edcb4fa3aa9b2f'
APPROVED='4e230c43693660c2b5d1d6a5bef79d4502cfc566'
PIN='7fbd7d107bc8dcd3165339d4c2df1381d50ba1499d68d90d17de0228588de44f'
E='.agent/evidence/114/'
SOURCE=(E+'release-readiness.md','CHANGELOG.md','docs/planning/ROADMAP.md','docs/planning/manifest.json','docs/planning/backlog_dag.json','docs/planning/backlog_reconciliation.md')
CANON=('.agent/feature_list_015.json','docs/planning/phase_015.yaml','.agent/run_state.json')
GATES=('.agent/validator/114-mode-a.json','.agent/qa/114-contract-review.json','.agent/validator/114-test-bundle-review.json','.agent/validator/114-mode-b.json','.agent/qa/114.json')
ACTORS={'generator':'/root/adapter_generator_113','test_author':'/root/adapter_acceptance_recovery_113','bundle_reviewer':'/root/adapter_validator_113','final_qa':'/root/readiness_acceptance_114'}
class Failure(Exception): pass
def need(ok,msg):
 if not ok: raise Failure(msg)
def raw(root,p):
 f=root/p; need(f.is_file() and not f.is_symlink(),'REGULAR_FILE:'+p); return f.read_bytes()
def obj(root,p): return json.loads(raw(root,p))
def sha(root,p): return hashlib.sha256(raw(root,p)).hexdigest()
def git(root,*args): return subprocess.check_output(['git','-C',str(root),*args])
def mode(root,p): return '100755' if stat.S_IMODE((root/p).stat().st_mode)&0o111 else '100644'
def approval(d): return d.get('final_verdict',{}).get('approved') is True and all(d.get(k)==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
def body(text):
 need(text.startswith('---\n'),'DOC_FRONTMATTER'); parts=text.split('---\n',2); need(len(parts)==3,'DOC_FRONTMATTER'); return yaml.safe_load(parts[1]),parts[2]
def old(p): return (BASE/p).read_text()
def clone(d): return copy.deepcopy(d)
def section(s,heading):
 m=re.search(r'(?m)^'+re.escape(heading)+r'\n',s); need(m is not None,'SECTION:'+heading)
 end=re.search(r'(?m)^## ',s[m.end():]); return s[m.end():m.end()+end.start()] if end else s[m.end():]
def header(path,text,version):
 before,_=body(old(path)); current,b=body(text); a=clone(current); a['version']=before['version']; a['change_log']=before['change_log']
 need(a==before and current['version']==version,'DOC_HEADER_DELTA:'+path)
 need(len(current['change_log'])==len(before['change_log'])+1 and current['change_log'][1:]==before['change_log'] and current['change_log'][0]['version']==version,'OLD_LOG_PRESERVED:'+path)
 return b

def predecessor_data(contract,qa,mode_b,pre,merged,features,phase):
 need(contract['status']=='approved' and approval(qa) and approval(mode_b) and qa['qa_pass'] is True and qa['checks_run']==qa['checks_passed']==len(qa['checks'])==16,'PREDECESSOR_GATE')
 need(next(x for x in features['features'] if x['id']=='113')['status']=='complete' and next(x for x in phase['steps'] if x['id']=='113')['status']=='COMPLETED','PREDECESSOR_LIFECYCLE')
 p=pre['pr']; need(p['number']==88 and p['headRefOid']=='7e2c26de846ba53ac409e5276bbb5c1690883099' and p['isDraft'] is False and p['mergeStateStatus']=='CLEAN' and p['mergeable']=='MERGEABLE','PREDECESSOR_PR')
 need(len(p['statusCheckRollup'])==6 and all(x.get('conclusion')=='SUCCESS' for x in p['statusCheckRollup']),'PREDECESSOR_PR_CHECKS')
 need(merged['pr']['state']=='MERGED' and merged['pr']['headRefOid']==p['headRefOid'] and merged['pr']['mergeCommit']['oid']==ORIGIN,'PREDECESSOR_MERGE')
 need(merged['main']['headSha']==ORIGIN and merged['main']['conclusion']=='success' and len(merged['main']['jobs'])==5 and all(x['conclusion']=='success' for x in merged['main']['jobs']),'PREDECESSOR_MAIN')
def predecessor(root):
 qa=obj(root,'.agent/qa/113.json'); features=obj(BASE,CANON[0]); phase=yaml.safe_load(raw(BASE,CANON[1]))
 predecessor_data(obj(root,'.agent/contracts/113.json'),qa,obj(root,'.agent/validator/113-mode-b.json'),obj(root,E+'predecessor113-pr-premerge.json'),obj(root,E+'predecessor113-merge-main.json'),features,phase)
 for p in qa['evidence_files']+[next(x for x in features['features'] if x['id']=='113')['evidence']]: need(bool(raw(root,p).strip()),'PREDECESSOR_EVIDENCE:'+p)
 need(subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',qa['candidate_commit'],ORIGIN],capture_output=True).returncode==0,'PREDECESSOR_ANCESTRY')


def dossier(text):
 head,b=body(text); need(head.get('version')=='0.1.0' and head.get('status')=='active' and head.get('authoritative_source')==SOURCE[0] and head.get('change_log'),'DOSSIER_HEADER')
 span=section(b,'## Human release boundary'); direct=re.split(r'(?m)^#{1,6} ',span,maxsplit=1)[0]
 need(re.search(r'(?<![\w-])H-FRAMEWORK-RELEASE(?![\w-])',direct) and 'H-CONSUMER-UPGRADE' in span,'HUMAN_BOUNDARY_SECTION')
 for token in ('v1.5.0','phase016','PLAN-WA','PLAN-016','C12',E+'current-source-inputs.json','.agent/qa/113.json','.agent/evidence/113/evidence-gate.txt'):
  need(token in b,'DOSSIER_EXTERNAL_ANCHOR:'+token)
 need(re.search(r'next\s*MINOR',b,re.I),'GENERIC_MINOR')
 need(not re.search(r'v1\.[6-9]\.[0-9]+|v[2-9]\.[0-9]+\.[0-9]+',b),'FIXED_FUTURE_VERSION')
 for phrase in (r'live(?:\s|-)conformance\s+(?:passed|complete|verified)',r'(?:all\s+)?thirteen\s+live\s+proofs\s+(?:passed|complete|verified)',r'WA\s+(?:implemented|activated|allocated)',r'phase016\s+(?:activated|allocated|complete)',r'(?:release|tag)\s+(?:published|created)\s+v(?!1\.5\.0)',r'114\s+QA\s+(?:passed|complete)'):
  need(not re.search(phrase,b,re.I),'FALSE_DELIVERY_CLAIM')
 need(re.search(r'(?:pending|outstanding)',span,re.I) and re.search(r'(?:unallocated|pending)',b,re.I),'PENDING_BOUNDARIES')
 need(re.search(r'(?:capture|evidence.gate)',b,re.I) and re.search(r'(?:fresh|independent)',b,re.I),'GATE_SEQUENCE')
 return b

def doc_deltas(root):
 change=raw(root,'CHANGELOG.md').decode(); prior=old('CHANGELOG.md'); anchor='### Changed\n\n'; before,tail=prior.split(anchor,1)
 need(change.startswith(before+anchor) and change.endswith(tail),'CHANGELOG_HISTORY')
 addition=change[len(before+anchor):-len(tail)]
 need(addition.startswith('- ') and len(re.findall(r'(?m)^- ',addition))==1 and len(addition.split())<=160 and '114' in addition,'CHANGELOG_SINGLE_BULLET')
 path='docs/planning/ROADMAP.md'; current=header(path,raw(root,path).decode(),'0.60.0'); prior=body(old(path))[1]
 # Remove only the terminal Selected-NIP overlay and first CurrentPosition bullet.
 heading='## Selected NIP-0003 — Authorized Phase015 Normative Plan'
 a=section(prior,heading); b=section(current,heading)
 need(b.startswith(a),'ROADMAP_SELECTED_HISTORY'); overlay=b[len(a):]; need(overlay.strip() and len(overlay.split())<=260 and '114' in overlay,'ROADMAP_OVERLAY')
 normalized=current.replace(heading+'\n'+b,heading+'\n'+a,1)
 normalized=re.sub(r'(?m)^## Current Position \([^\n]+\)$',lambda _:re.search(r'(?m)^## Current Position \([^\n]+\)$',prior).group(),normalized,count=1)
 pos=normalized.index('## Current Position '); oldpos=prior.index('## Current Position ')
 n=re.search(r'(?ms)^- .*?(?=^- |^## |\Z)',normalized[pos:]); o=re.search(r'(?ms)^- .*?(?=^- |^## |\Z)',prior[oldpos:])
 need(n is not None and o is not None and '015' in n.group(),'ROADMAP_CURRENT_BULLET')
 start=pos+n.start(); normalized=normalized[:start]+o.group()+normalized[pos+n.end():]
 need(normalized==prior,'ROADMAP_OTHER_BODY')
 path='docs/planning/backlog_reconciliation.md'; current=header(path,raw(root,path).decode(),'0.1.14'); prior=body(old(path))[1]
 current=re.sub(r'(?m)^## Current planning view — [^\n]+$',lambda _:re.search(r'(?m)^## Current planning view — [^\n]+$',prior).group(),current,count=1)
 marker='## Prior reconciliation history'; left,right=prior.split(marker,1); nl,nr=current.split(marker,1)
 need(nr==right and nl.startswith(left),'RECON_HISTORY'); extra=nl[len(left):]
 need(extra.strip() and len(extra.split())<=180 and '114' in extra,'RECON_BOUNDED_ADDITION')


def baseline_models():
 return {'features':obj(BASE,CANON[0]),'phase':yaml.safe_load(raw(BASE,CANON[1])),'state':obj(BASE,CANON[2]),'manifest':obj(BASE,SOURCE[3]),'dag':obj(BASE,SOURCE[4])}
def models(root):
 return {'features':obj(root,CANON[0]),'phase':yaml.safe_load(raw(root,CANON[1])),'state':obj(root,CANON[2]),'manifest':obj(root,SOURCE[3]),'dag':obj(root,SOURCE[4])}
def planning_data(data,closed):
 olddata=baseline_models(); features=clone(data['features']); f=next(x for x in features['features'] if x['id']=='114'); original=next(x for x in olddata['features']['features'] if x['id']=='114')
 expected='complete' if closed else 'in_progress'; need(f['status']==expected and f.get('passes') is closed,'FEATURE_STATE')
 if closed: need(f.get('qa')=='.agent/qa/114.json' and f.get('evidence')==E+'evidence-gate.txt' and f.get('completed_at'),'FEATURE_COMPLETION_REFERENCE')
 else: need('qa' not in f and 'completed_at' not in f,'PREMATURE_QA')
 need(f.get('contract_ref')=='.agent/contracts/114.json','FEATURE_CONTRACT')
 for k in ('status','passes','contract_ref','evidence','qa','completed_at'): f.pop(k,None)
 of=clone(original)
 for k in ('status','passes','contract_ref','evidence','qa','completed_at'): of.pop(k,None)
 need(f==of,'FEATURE_UNOWNED'); features['features']=[original if x['id']=='114' else x for x in features['features']]; features['phase_status']=olddata['features']['phase_status']
 need(features==olddata['features'],'OTHER_FEATURES')
 need(data['features']['phase_status']==expected,'FEATURE_PHASE')
 phase=clone(data['phase']); s=next(x for x in phase['steps'] if x['id']=='114'); original=next(x for x in olddata['phase']['steps'] if x['id']=='114')
 need(s['status']==('COMPLETED' if closed else 'IN_PROGRESS'),'PHASE_STEP')
 if closed: need(s.get('evidence')==E+'evidence-gate.txt' and s.get('docs_updated') and s.get('changelog_entry'),'PHASE_COMPLETION_REFERENCE')
 for k in ('status','evidence','docs_updated','changelog_entry'): s.pop(k,None)
 os_=clone(original)
 for k in ('status','evidence','docs_updated','changelog_entry'): os_.pop(k,None)
 need(s==os_,'PHASE_STEP_UNOWNED'); phase['steps']=[original if x['id']=='114' else x for x in phase['steps']]; phase['status']=olddata['phase']['status']; need(phase==olddata['phase'],'OTHER_PHASE_STEPS')
 need(data['phase']['status']==expected,'PHASE_STATE')
 state=clone(data['state']); base=olddata['state']; need(state['current_phase']=='015-live-runtime-normative' and state['status']==expected,'RUN_POSITION')
 need(state['current_feature']==(None if closed else '114') and state['active_contract_id']==(None if closed else '114'),'RUN_ACTIVE')
 need(state['history'][:len(base['history'])]==base['history'],'HISTORY_PREFIX')
 need(set(state['circuit_breaker'])==set(base['circuit_breaker']),'COUNTER_KEYS')
 for key,val in base['circuit_breaker'].items():
  actual=state['circuit_breaker'][key]
  if key.startswith('114-'): need(actual['limit']==3 and val['attempts']<=actual['attempts']<=3 and set(actual)==set(val),'COUNTER_LIMIT')
  else: need(actual==val,'OLD_COUNTER:'+key)
 budget=state['scope_budget']; b=base['scope_budget']; need(budget['original_estimate_lines']==7200 and budget['ceiling_130pct']==9360 and budget['total_lines_changed']<=9360,'BUDGET_CEILING')
 need(budget['per_feature'][:len(b['per_feature'])]==b['per_feature'],'OLD_BUDGET_RECORDS')
 suffix=budget['per_feature'][len(b['per_feature']):]; need(not suffix or closed and len(suffix)==1 and suffix[0]['id']=='114','BUDGET_APPEND')
 need(state['completed_contract_ids'][:len(base['completed_contract_ids'])]==base['completed_contract_ids'] and state['completed_contract_ids'][len(base['completed_contract_ids']):] in ([],['114']),'COMPLETED_IDS')
 for key in ('current_phase','current_feature','active_contract_id','status','updated_at','history','circuit_breaker','scope_budget','last_action','completed_contract_ids','pending_operator_gate'): state[key]=base[key]
 need(state==base,'STATE_UNOWNED')
 manifest=clone(data['manifest']); original=olddata['manifest']; rows=manifest['phases']; row=next(x for x in rows if x['id']=='015-live-runtime-normative'); orow=next(x for x in original['phases'] if x['id']=='015-live-runtime-normative')
 need(row['status']==expected and row.get('activation_state')=='active' and '114' in row.get('note',''),'MANIFEST_015')
 row['status']=orow['status']; row['note']=orow['note']; manifest['updated_at']=original['updated_at']; need(manifest==original,'MANIFEST_OTHER')
 dag=clone(data['dag']); original=olddata['dag']; need(dag['activated_phase']['current_status']==expected and '114' in dag['activated_phase']['run_state_position'],'DAG_ACTIVATED')
 for key in ('current_status','run_state_position'): dag['activated_phase'][key]=original['activated_phase'][key]
 dag['generated_at']=original['generated_at']; oldpack={p['id']:p for p in original['packets']}
 for p in dag['packets']:
  name=p['id']; o=oldpack.get(name); need(o is not None,'DAG_PACKET_SET')
  if name not in ('NIP3-113','NIP3-114','PLAN-WA','PLAN-016'): need(p==o,'DAG_OTHER_PACKET:'+name); continue
  target='complete' if name=='NIP3-113' else expected if name=='NIP3-114' else 'pending'
  need(p['status']==target and p['authority_status']=='authorized','DAG_PACKET_STATE:'+name)
  for kind in ('technical','evidence'):
   desired=True if name=='NIP3-113' else (True if kind=='technical' else closed) if name=='NIP3-114' else closed if name=='PLAN-WA' else False
   need(p['prerequisites'][kind]['satisfied'] is desired and bool(p['prerequisites'][kind]['reason']),'DAG_PREREQUISITE:'+name+':'+kind)
  if name=='PLAN-016': need('PLAN-WA' in p['prerequisites']['technical']['reason'],'PLAN016_SERIALIZATION')
  if name.startswith('NIP3-'):
   need(p['prerequisites']['authority']['satisfied'] is True,'DAG_AUTHORITY:'+name)
   need(p['evidence'][:len(o['evidence'])]==o['evidence'],'DAG_EVIDENCE_PREFIX:'+name)
   p['status']=o['status']; p['authority_status']=o['authority_status']; p['evidence']=o['evidence']; allowed=('technical','authority','evidence')
  else: allowed=('technical','evidence')
  for kind in allowed:
   a=p['prerequisites'][kind]; b=o['prerequisites'][kind]; need(set(a)==set(b),'DAG_PREREQUISITE_SHAPE'); p['prerequisites'][kind]=b
  need(p==o,'DAG_UNOWNED:'+name)
 need(dag==original,'DAG_OTHER')


def completion(root):
 qa=obj(root,'.agent/qa/114.json'); need(approval(qa) and qa['qa_pass'] is True and qa['checks_run']==qa['checks_passed']==len(qa['checks'])==12 and qa['adversarial']['performed'] is True,'REAL_COMPLETION_QA')
 source=obj(root,E+'current-source-inputs.json'); command='PYTHONDONTWRITEBYTECODE=1 python3 '+E+'evidence_gate.py'
 gate=raw(root,E+'evidence-gate.txt').decode(); need(gate.startswith('COMMAND: '+command+'\n') and 'CANDIDATE_SHA: '+source['candidate']['commit']+'\n' in gate and re.findall(r'^EXIT:\s*(-?\d+)\s*$',gate,re.M)==['0'] and gate.rstrip().endswith('EXIT: 0'),'REAL_CAPTURE_GATE')
 need('EVIDENCE GATE PASS: feature114' in gate,'REAL_CAPTURE_RESULT')
 return True

def planning(root):
 data=models(root); closed=data['phase']['status']=='complete'
 planning_data(data,closed); doc_deltas(root)
 if closed: completion(root)

def check_members(root,files,label):
 for p,meta in files.items():
  need(not Path(p).is_absolute() and '..' not in Path(p).parts,'INPUT_PATH')
  need(sha(root,p)==meta['sha256'] and mode(root,p)==meta['mode'],label+':'+p)
  if 'permissions' in meta: need(stat.S_IMODE((root/p).stat().st_mode)==meta['permissions'],label+'_FULLMODE:'+p)

def source_shape(source):
 need(set(source)=={'format','candidate','fixed_inputs_sha256','contract_sha256','source_paths','canonical_precompletion'} and source['format']==1,'SOURCE_SHAPE_CIRCULAR')
 need(set(source['candidate'])=={'commit','tree'},'SOURCE_SHAPE_CIRCULAR')

def candidate_tree(root,candidate,tree):
 p=subprocess.run(['git','-C',str(root),'rev-parse',candidate+'^{tree}'],capture_output=True,text=True)
 need(re.fullmatch('[0-9a-f]{40}',candidate) and p.returncode==0 and p.stdout.strip()==tree,'CANDIDATE_TREE')

def history_members(root,original):
 for p,meta in original.items(): need(sha(root,p)==meta['sha256'] and stat.S_IMODE((root/p).stat().st_mode)==meta['permissions'],'HISTORY:'+p)

def integrity(root,source,fixed):
 source_shape(source)
 need(fixed['actors']==ACTORS and len(set(ACTORS.values()))==4,'ACTOR_INDEPENDENCE')
 need(fixed['base_revision']==ORIGIN and fixed['approved_base']==APPROVED and fixed['contract_sha256']==PIN and sha(root,'.agent/contracts/114.json')==PIN,'APPROVED_CONTRACT_PIN')
 need(sha(root,E+'fixed-inputs.json')==obj(root,E+'fixed-inputs-seal.json')['manifest_sha256'],'FIXED_SEAL')
 check_members(root,fixed['files'],'FIXED_MEMBER')
 need(source['fixed_inputs_sha256']==sha(root,E+'fixed-inputs.json') and source['contract_sha256']==PIN,'SOURCE_FIXED_BINDING')
 need(sha(root,E+'current-source-inputs.json')==obj(root,E+'current-source-seal.json')['manifest_sha256'],'SOURCE_SEAL')
 c=source['candidate']['commit']; candidate_tree(root,c,source['candidate']['tree'])
 need(obj(root,E+'current-source-seal.json')['candidate_commit']==c,'SOURCE_CANDIDATE')
 closed=yaml.safe_load(raw(root,CANON[1]))['status']=='complete'
 need(git(root,'rev-parse','HEAD').decode().strip()==c if not closed else subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',c,'HEAD'],capture_output=True).returncode==0,'CANDIDATE_POSITION')
 need(set(source['source_paths'])==set(SOURCE),'SOURCE_SET')
 for p,meta in source['source_paths'].items():
  need(hashlib.sha256(git(root,'show',c+':'+p)).hexdigest()==meta['sha256'] and git(root,'ls-tree',c,'--',p).decode().split()[0]==meta['mode'],'CANDIDATE_SOURCE:'+p)
  if not closed or p in (SOURCE[0],SOURCE[1]): need(sha(root,p)==meta['sha256'] and mode(root,p)==meta['mode'],'SOURCE_CHANGED:'+p)
 need(set(source['canonical_precompletion'])==set(CANON),'CANONICAL_SIDECAR_SET')
 for p,meta in source['canonical_precompletion'].items(): need(hashlib.sha256(git(root,'show',c+':'+p)).hexdigest()==meta['sha256'] and git(root,'ls-tree',c,'--',p).decode().split()[0]==meta['mode'],'CANONICAL_SIDECAR:'+p)
 for p,meta in fixed['files'].items(): need(hashlib.sha256(git(root,'show',c+':'+p)).hexdigest()==meta['sha256'] and git(root,'ls-tree',c,'--',p).decode().split()[0]==meta['mode'],'CANDIDATE_FIXED:'+p)
 return c

def readiness(root):
 dossier(raw(root,SOURCE[0]).decode()); fixed=obj(root,E+'fixed-inputs.json'); source=obj(root,E+'current-source-inputs.json'); c=integrity(root,source,fixed)
 need(c not in raw(root,SOURCE[0]).decode(),'DOSSIER_CIRCULAR_CANDIDATE')
 bundle=obj(root,GATES[2]); need(approval(bundle) and bundle['actor']==ACTORS['bundle_reviewer'] and bundle['fixed_inputs_sha256']==sha(root,E+'fixed-inputs.json'),'BUNDLE_GATE')
 review=obj(root,E+'source-review.json'); need(approval(review) and review['actor']==ACTORS['final_qa'] and review['candidate_commit']==c and review['source_manifest_sha256']==sha(root,E+'current-source-inputs.json') and review['fixed_inputs_sha256']==sha(root,E+'fixed-inputs.json'),'SEMANTIC_REVIEW')
 need(review.get('evidence') and all(raw(root,p).strip() for p in review['evidence']),'SEMANTIC_REVIEW_EVIDENCE')
 if yaml.safe_load(raw(root,CANON[1]))['status']=='complete': planning(root)

def history(root):
 original=obj(root,E+'private/history.json')
 need(len([p for p in original if p.startswith('.nizam/')])==239,'INSTALLED_INVENTORY')
 history_members(root,original)

def allowed(path): return path in SOURCE+CANON or path=='.agent/contracts/114.json' or path in GATES or path.startswith(E)
def scope_paths(paths):
 for p in paths: need(allowed(p),'OUT_OF_SCOPE:'+p)
def scope_history(root):
 history(root); planning(root)
 paths=set(git(root,'diff','--name-only',ORIGIN,'--').decode().splitlines())|set(git(root,'ls-files','--others','--exclude-standard').decode().splitlines()); scope_paths(paths)
 p=subprocess.run([sys.executable,'.agent/evidence/scope-budget-014/measure.py','--range','114='+ORIGIN+'..'],cwd=root,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True)
 need(p.returncode==0,'BUDGET_CLASSIFIER'); counts=re.findall(r'^\s*BUDGET_COUNTED_LINES=(\d+)\s*$',p.stdout,re.M); need(len(counts)==1 and 6779+int(counts[0])<=9360,'ACTUAL_BUDGET_CEILING')
 print('ACTUAL FROZEN114 BUDGET_COUNTED_LINES='+counts[0])

def negative_controls(root):
 p=subprocess.run([sys.executable,str(PRIVATE/'controls.py'),'--root',str(root)],cwd=root,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 need(p.returncode==0,'NEGATIVE_CONTROLS')

def main():
 modes={'predecessor':predecessor,'readiness':readiness,'planning':planning,'scope-history':scope_history,'negative-controls':negative_controls}
 need(len(sys.argv)==2 and sys.argv[1] in modes,'MODE')
 modes[sys.argv[1]](Path.cwd().resolve()); print('PASS feature114 '+sys.argv[1])
if __name__=='__main__':
 try: main()
 except (Failure,KeyError,ValueError,AssertionError,FileNotFoundError) as error:
  print('FAIL feature114 '+str(error)); raise SystemExit(1)
