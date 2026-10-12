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
APPROVED='480c102a5f3119fd8b645d3cf2f3e2ad793e2b9a'
PIN='fd0d1be4ce0f25bcd632c49b209557bb910053866f8df8a28e062256f98fc02e'
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


def version_tokens(text):
 """Numeric recognition only: positions, arbitrary-width core, optional v/V."""
 tokens=[]
 def digits(start):
  end=start
  while end<len(text) and '0'<=text[end]<='9': end+=1
  return end
 for start,char in enumerate(text):
  prefixed=char in ('v','V')
  if not prefixed and not ('0'<=char<='9'): continue
  if start and (text[start-1].isalnum() or text[start-1] in ('_','.')): continue
  position=start+1 if prefixed else start; parts=[]
  for component in range(3):
   end=digits(position)
   if end==position: break
   parts.append(int(text[position:end])); position=end
   if component<2:
    if position>=len(text) or text[position]!='.': break
    position+=1
  if len(parts)!=3: continue
  tokens.append((start,position,tuple(parts),prefixed))
 return tokens

def framework_version_cores(text):
 """Classify each declaration locally, separate from token recognition.

 Context cannot cross an earlier numeric token, sentence/clause boundary or
 coordinating conjunction. Only an explicit named toolchain subject joined
 to this value by declaration words exempts this token. Unknown prefixed
 values and bare release/version declarations are framework values. This
 bounded syntax guard still requires independent personal source review.
 """
 cores=[]; previous_end=0
 tools={'sbcl','asdf','python'}
 bridge={'version','release','tag','number','candidate','value','is','was',
         'remains','at','will','be','next','current','recorded','installed'}
 for start,end,core,prefixed in version_tokens(text):
  left=text[previous_end:start]; previous_end=end
  left=re.split(r'[\n;,!?]|(?<![0-9])\.|\.(?![0-9])|\b(?:and|but|while|whereas|however)\b',left,flags=re.I)[-1]
  words=[word.lower() for word in re.findall(r'[A-Za-z]+',left)]
  named=[i for i,word in enumerate(words) if word in tools]
  toolchain=bool(named and all(word in bridge for word in words[named[-1]+1:]))
  declared=any(word in {'release','version','tag','minor','candidate'} for word in words)
  if not toolchain and (prefixed or declared): cores.append(core)
 return cores

def dossier(text):
 head,b=body(text); need(head.get('version')=='0.1.0' and head.get('status')=='active' and head.get('authoritative_source')==SOURCE[0] and head.get('change_log'),'DOSSIER_HEADER')
 span=section(b,'## Human release boundary'); direct=re.split(r'(?m)^#{1,6} ',span,maxsplit=1)[0]
 need(re.search(r'(?<![\w-])H-FRAMEWORK-RELEASE(?![\w-])',direct) and 'H-CONSUMER-UPGRADE' in span,'HUMAN_BOUNDARY_SECTION')
 for token in ('v1.5.0','phase016','PLAN-WA','PLAN-016','C12',E+'current-source-inputs.json','.agent/qa/113.json','.agent/evidence/113/evidence-gate.txt'):
  need(token in b,'DOSSIER_EXTERNAL_ANCHOR:'+token)
 need(re.search(r'next\s*MINOR',b,re.I),'GENERIC_MINOR')
 versions=framework_version_cores(b)
 need(all(version<=(1,5,0) for version in versions),'FIXED_FUTURE_VERSION')
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
 state_data(data['state'],closed)
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

def recovery_state(): return obj(PRIVATE/'recovery-base',CANON[2])

def state_data(data,closed):
 state=clone(data); base=recovery_state(); expected='complete' if closed else 'in_progress'
 need(state['current_phase']=='015-live-runtime-normative' and state['status']==expected,'RUN_POSITION')
 need(state['current_feature']==(None if closed else '114') and state['active_contract_id']==(None if closed else '114'),'RUN_ACTIVE')
 need(state['history'][:len(base['history'])]==base['history'],'HISTORY_PREFIX')
 need(state['blocked_features']==base['blocked_features'],'RECOVERY_BLOCKED_FEATURES')
 need(set(state['circuit_breaker'])==set(base['circuit_breaker']),'COUNTER_KEYS')
 immutable={'114-contract','114-checker-development','114-checker-review','114-recovery-contract'}
 for key,val in base['circuit_breaker'].items():
  actual=state['circuit_breaker'][key]
  if key.startswith('114-') and key not in immutable:
   need(set(actual)==set(val) and actual['limit']==3 and type(actual['attempts']) is int and val['attempts']<=actual['attempts']<=3,'COUNTER_LIMIT')
  else: need(actual==val,'OLD_COUNTER:'+key)
 budget=state['scope_budget']; b=base['scope_budget']
 need(budget['original_estimate_lines']==7200 and budget['ceiling_130pct']==9360 and 6779<=budget['total_lines_changed']<=9360,'BUDGET_CEILING')
 need(budget['per_feature'][:len(b['per_feature'])]==b['per_feature'],'OLD_BUDGET_RECORDS')
 suffix=budget['per_feature'][len(b['per_feature']):]
 need(not suffix if not closed else len(suffix)==1 and suffix[0]['id']=='114' and suffix[0]['estimated']==1150,'BUDGET_APPEND')
 need(budget['total_lines_changed']==(6779 if not closed else 6779+suffix[0]['actual']),'BUDGET_TOTAL')
 normalized=clone(budget)
 for key in ('total_lines_changed','evidence_lines_total','excluded_lines_total','per_feature','last_measured_at'): normalized[key]=b[key]
 need(normalized==b,'BUDGET_PRESERVATION')
 need(state['completed_contract_ids']==base['completed_contract_ids']+(['114'] if closed else []),'COMPLETED_IDS')
 pending=state['pending_operator_gate']; previous=base['pending_operator_gate']
 if pending is None:
  need(any(x.get('event')=='114-recovery-contract-approved-resume' and x.get('evidence')==E+'recovery-contract-approval.json' for x in state['history']),'RECOVERY_GATE_CLEAR_RECEIPT')
 else:
  gate=clone(pending); need(isinstance(gate.get('stage'),str) and gate['stage'],'RECOVERY_GATE_STAGE'); gate['stage']=previous['stage']
  need(gate==previous,'RECOVERY_GATE_AUTHORIZATION')
 for key in ('current_phase','current_feature','active_contract_id','status','updated_at','history','circuit_breaker','scope_budget','last_action','completed_contract_ids','pending_operator_gate'): state[key]=base[key]
 need(state==base,'STATE_UNOWNED')


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

def supplemental_members(root,members):
 for original,meta in members.items():
  path=meta['path']; target=root/path
  need(not Path(path).is_absolute() and '..' not in Path(path).parts,'ARCHIVE_PATH')
  need(target.is_file() and not target.is_symlink(),'ARCHIVE_MEMBER:'+original)
  need(sha(root,path)==meta['sha256'] and mode(root,path)==meta['mode'] and stat.S_IMODE(target.stat().st_mode)==meta['permissions'],'ARCHIVE_MEMBER:'+original)

def debt_row(text):
 rows=re.findall(r'(?m)^\| NDEBT-051 \|.*\n',text)
 need(len(rows)==1,'DEBT051_ROW')
 return rows[0],rows[0].strip().split('|')[1:-1]

def debt_header(before,after,version):
 oldhead,_=body(before); current,_=body(after); normalized=clone(current)
 normalized['version']=oldhead['version']; normalized['change_log']=oldhead['change_log']
 need(normalized==oldhead and current['version']==version,'DEBT051_HEADER')
 need(len(current['change_log'])==len(oldhead['change_log'])+1 and current['change_log'][1:]==oldhead['change_log'],'DEBT051_LOG_HISTORY')
 entry=current['change_log'][0]
 need(set(entry)=={'version','date','summary'} and entry['version']==version and '051' in entry['summary'],'DEBT051_NEW_LOG')
 oldraw=before.split('---\n',2)[1]; newraw=after.split('---\n',2)[1]
 # Preserve the actual old YAML log bytes, rather than only parsed values.
 start=newraw.index('change_log:\n')+len('change_log:\n')
 next_entry=re.search(r'(?m)^  - ',newraw[start+1:]); need(next_entry is not None,'DEBT051_LOG_HISTORY')
 newraw=newraw[:start]+newraw[start+1+next_entry.start():]
 newraw=newraw.replace('version: '+version+'\n','version: '+oldhead['version']+'\n',1)
 need(newraw==oldraw,'DEBT051_HEADER_BYTES')

def debt_transition(before,after,version,closed=False):
 debt_header(before,after,version)
 oldrow,oldcells=debt_row(before); newrow,newcells=debt_row(after)
 need(newcells[:-1]==oldcells[:-1],'DEBT051_FIELDS')
 prior=oldcells[-1].strip(); actual=newcells[-1].strip()
 need(actual.startswith(prior) and 0<len(actual[len(prior):].split())<=160,'DEBT051_NOTES_MASK')
 _,a=body(before); _,b=body(after)
 need(a.replace(oldrow,'',1)==b.replace(newrow,'',1),'DEBT051_OTHER_BODY')
 need(newrow in section(b,'## Resolved' if closed else '## Open'),'DEBT051_LOCATION')

def debt_data(original,halt,authorized,current,closed):
 debt_header(original,halt,'0.66.0')
 row,_=debt_row(halt); _,a=body(original); _,b=body(halt)
 need(row in section(b,'## Open') and b.replace(row,'',1)==a,'DEBT051_HALT_MASK')
 debt_transition(halt,authorized,'0.67.0')
 need('H-CHECKER-114-RECOVERY' in debt_row(authorized)[0] and E+'recovery-contract-approval.json' in debt_row(authorized)[0],'DEBT051_AUTHORIZATION')
 if closed:
  debt_transition(authorized,current,'0.68.0',True)
  notes=debt_row(current)[1][-1]
  for path in (GATES[3],GATES[4],E+'evidence-gate.txt'): need(path in notes,'DEBT051_RESOLUTION_REFERENCE')
 else:
  need(body(current)[0]['version']!='0.68.0','DEBT051_PREMATURE_RESOLUTION')
  need(current==authorized,'DEBT051_CURRENT_BYTES')

def recovery_inputs(root):
 need(sha(root,E+'private/recovery-base/.agent/run_state.json')==hashlib.sha256(git(root,'show',APPROVED+':'+CANON[2])).hexdigest(),'RECOVERY_BASE_SNAPSHOT')
 need(sha(root,E+'recovery-approved-contract.json')==sha(root,'.agent/contracts/114.json')==PIN,'APPROVED_CONTRACT_PIN')
 receipt=obj(root,E+'recovery-contract-approval.json')
 need(receipt['approved_contract_sha256']==PIN and receipt['actors']==ACTORS and receipt['epoch']=='114-recovery-1','RECOVERY_APPROVAL_RECEIPT')
 for path,key in ((GATES[0],'validator_sha256'),(GATES[1],'evaluator_sha256')):
  gate=obj(root,path); need(approval(gate) and sha(root,path)==receipt[key],'RECOVERY_PRECODE_GATE')
  need(gate['proposal_sha256']==receipt['proposal_sha256'] and gate['actor']==ACTORS['bundle_reviewer' if path==GATES[0] else 'test_author'],'RECOVERY_PRECODE_IDENTITY')
  need(gate.get('evidence') and all(raw(root,p).strip() for p in gate['evidence']),'RECOVERY_PRECODE_EVIDENCE')
 auth=obj(root,E+'recovery-authorization.json')
 need(auth['decision']=='approved' and auth['authorized_by']=='operator' and auth['epoch']=='114-recovery-1' and auth['immutable_halt_base']=='ea41afd196dddaef02f6be86217c84deaf47d238','RECOVERY_AUTHORIZATION')
 need(auth['halt_record_sha256']==sha(root,E+'circuit-breaker-halt.json'),'RECOVERY_HALT_RECORD')
 manifest=obj(root,E+'recovery-halt-inventory.json')
 need(sha(root,E+'recovery-halt-inventory.json')==receipt['halt_inventory_sha256']=='cdb359913b7663be29ec3a1317ecf3b1ee55a2a31a0620edcfac1da5b746a41b' and len(manifest['files'])==485,'RECOVERY_ARCHIVE_MAP')
 supplemental_members(root,manifest['files'])

def integrity(root,source,fixed):
 source_shape(source)
 recovery_inputs(root)
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

def installed_inventory(root,original):
 expected={p for p in original if p.startswith('.nizam/')}
 need(len(expected)==239,'INSTALLED_INVENTORY')
 installed=root/'.nizam'
 need(installed.is_dir() and not installed.is_symlink(),'INSTALLED_INVENTORY')
 actual={}
 # os.walk sees ignored/dot files; lstat and no-follow expose directory symlinks.
 for folder,dirs,files in os.walk(installed,followlinks=False):
  directory=Path(folder)
  for name in dirs+files:
   entry=directory/name; metadata=entry.lstat(); relative=entry.relative_to(root).as_posix()
   if stat.S_ISDIR(metadata.st_mode): continue
   actual[relative]=metadata.st_mode
 need(set(actual)==expected,'INSTALLED_INVENTORY')
 need(all(stat.S_ISREG(metadata) for metadata in actual.values()),'INSTALLED_REGULAR_FILES')

def history(root):
 original=obj(root,E+'private/history.json')
 need(sha(root,E+'private/history.json')=='764cd7d54f31158c375cb4ce69bac3e0ff711f0f61058bbc48bef546e106df30' and len(original)==4800,'ORIGINAL_HISTORY_SEAL')
 installed_inventory(root,original)
 history_members(root,{p:m for p,m in original.items() if p!='docs/planning/DEBT.md'})
 debtmeta=original['docs/planning/DEBT.md']; path=E+'private/original-debt.md'
 need(sha(root,path)==debtmeta['sha256'] and stat.S_IMODE((root/path).stat().st_mode)==debtmeta['permissions'],'ORIGINAL_DEBT_SNAPSHOT')
 recovery_inputs(root)
 closed=yaml.safe_load(raw(root,CANON[1]))['status']=='complete'
 debt_data(raw(root,path).decode(),raw(root,E+'recovery-halt-debt.md').decode(),raw(root,E+'recovery-authorized-debt.md').decode(),raw(root,'docs/planning/DEBT.md').decode(),closed)
 need(stat.S_IMODE((root/'docs/planning/DEBT.md').stat().st_mode)==debtmeta['permissions'],'DEBT_FULLMODE')
 if closed: completion(root)

def allowed(path): return path in SOURCE+CANON or path in ('.agent/contracts/114.json','docs/planning/DEBT.md') or path in GATES or path.startswith(E)
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
