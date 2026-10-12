#!/usr/bin/env python3
"""Small preregistered scratch component/model controls, never QA or live proof."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import yaml

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('controls114_checker',HERE.parent/'check_114.py')
C=importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

CASES=[
 ('failed-predecessor','PREDECESSOR_GATE','evidence'),
 ('failed-pr-check','PREDECESSOR_PR_CHECKS','evidence'),
 ('candidate-tree-changed','CANDIDATE_TREE','evidence'),
 ('circular-sidecar-field','SOURCE_SHAPE_CIRCULAR','evidence'),
 ('premature-phasecomplete','PHASE_STATE','planning'),
 ('unreferenced-qa','FEATURE_COMPLETION_REFERENCE','planning'),
 ('historical-proof-changed','HISTORY:.agent/qa/113.json','evidence'),
 ('untracked-stray','OUT_OF_SCOPE:unapproved-114.txt','unclassified'),
 ('fixed-future-release','FIXED_FUTURE_VERSION','evidence'),
 ('false-liveproof','FALSE_DELIVERY_CLAIM','evidence'),
 ('wa-allocation','FALSE_DELIVERY_CLAIM','evidence'),
 ('dag-edge-changed','DAG_UNOWNED:NIP3-114','planning'),
 ('plan016-premature','DAG_PREREQUISITE:PLAN-016:technical','planning'),
 ('old-counter-reset','OLD_COUNTER:113-checker-review','excluded'),
 ('budget-rebaseline','BUDGET_CEILING','planning'),
 ('old-roadmap-prose','ROADMAP_OTHER_BODY','planning'),
 ('altered-released-changelog','CHANGELOG_HISTORY','product'),
 ('installed-ignored-extra-file','INSTALLED_INVENTORY','unclassified/installed'),
 ('installed-extra-symlink','INSTALLED_INVENTORY','unclassified/installed'),
 ('future-version-multidigit','FIXED_FUTURE_VERSION','evidence'),
 ('future-version-sentence-period', 'FIXED_FUTURE_VERSION', 'evidence'),
 ('future-version-comma', 'FIXED_FUTURE_VERSION', 'evidence'),
 ('future-version-semicolon', 'FIXED_FUTURE_VERSION', 'evidence'),
 ('future-version-colon', 'FIXED_FUTURE_VERSION', 'evidence'),
 ('future-version-parentheses', 'FIXED_FUTURE_VERSION', 'evidence'),
 ('future-version-markdown-closing', 'FIXED_FUTURE_VERSION', 'evidence'),
 ('future-version-square-closing', 'FIXED_FUTURE_VERSION', 'evidence'),
 ('future-version-uppercase', 'FIXED_FUTURE_VERSION', 'evidence'),
 ('future-version-bare', 'FIXED_FUTURE_VERSION', 'evidence'),
 ('toolchain-mixed-clause','FIXED_FUTURE_VERSION','evidence'),
 ('toolchain-mixed-conjunction','FIXED_FUTURE_VERSION','evidence'),
 ('toolchain-mixed-comma-bare','FIXED_FUTURE_VERSION','evidence'),
 ('toolchain-does-not-exempt-widemajor','FIXED_FUTURE_VERSION','evidence'),
 ('missing-original-archive','ARCHIVE_MEMBER:.agent/contracts/114.json','evidence'),
 ('corrupt-original-archive','ARCHIVE_MEMBER:.agent/contracts/114.json','evidence'),
 ('altered-non051-debt','DEBT051_CURRENT_BYTES','planning'),
 ('premature051-resolution','DEBT051_PREMATURE_RESOLUTION','planning'),
 ('exhausted114-counter-reset','OLD_COUNTER:114-checker-review','excluded'),
 ('extra-recovery-counter','COUNTER_KEYS','excluded'),
 ('recovery-counter-limit','COUNTER_LIMIT','excluded'),
 ('recovery-history-changed','HISTORY_PREFIX','excluded'),
 ('historical114-budget-rebased','BUDGET_PRESERVATION','planning'),
 ('recovery-authorization-changed','RECOVERY_GATE_AUTHORIZATION','excluded'),
 ('runtime-mixed-framework-forecast','FIXED_FUTURE_VERSION','evidence'),
 ('system-mixed-framework-forecast','FIXED_FUTURE_VERSION','evidence'),
 ('interpreter-mixed-framework-forecast','FIXED_FUTURE_VERSION','evidence'),
 ('toolchain-predicate-does-not-exempt-release','FIXED_FUTURE_VERSION','evidence'),
 ('past-recovery1-proof-corrupt','ARCHIVE_MEMBER:recovery-author1:.agent/evidence/114/check_114.py','evidence')]

def model(closed=False):
 data=C.baseline_models(); status='complete' if closed else 'in_progress'
 f=next(x for x in data['features']['features'] if x['id']=='114')
 data['features']['phase_status']=status; f['status']=status; f['passes']=closed
 s=next(x for x in data['phase']['steps'] if x['id']=='114'); data['phase']['status']=status; s['status']='COMPLETED' if closed else 'IN_PROGRESS'
 data['state']=C.recovery_state(); state=data['state']; state['status']=status
 if closed:
  f.update(qa='.agent/qa/114.json',evidence=C.E+'evidence-gate.txt',completed_at='CONTROL_ONLY')
  s.update(evidence=C.E+'evidence-gate.txt',docs_updated='CONTROL_ONLY',changelog_entry='CONTROL_ONLY')
  state['current_feature']=None; state['active_contract_id']=None; state['completed_contract_ids'].append('114')
  state['scope_budget']['per_feature'].append({'id':'114','estimated':1150,'actual':0,'note':'CONTROL ONLY structural closed model, not production acceptance'})
  state['pending_operator_gate']=None
 row=next(x for x in data['manifest']['phases'] if x['id']=='015-live-runtime-normative'); row['status']=status; row['note']='CONTROL_ONLY114 projected status; no actual QA or capture approval.'
 dag=data['dag']; dag['activated_phase']['current_status']=status; dag['activated_phase']['run_state_position']='CONTROL_ONLY113 complete;114 '+status
 for p in dag['packets']:
  name=p['id']
  if name in ('NIP3-113','NIP3-114'):
   p['status']='complete' if name=='NIP3-113' else status; p['authority_status']='authorized'
   for kind in ('technical','authority','evidence'):
    p['prerequisites'][kind]={'satisfied':True if name=='NIP3-113' or kind!='evidence' else closed,'reason':'CONTROL_ONLY structural model, never production proof.'}
  if name in ('PLAN-WA','PLAN-016'):
   for kind in ('technical','evidence'):
    p['prerequisites'][kind]={'satisfied':closed if name=='PLAN-WA' else False,'reason':'CONTROL_ONLY114 '+status+'; PLAN-WA planning remains pending.'}
 return data

def dossier_fixture():
 return '''---
id: nizam-114-readiness
title: "CONTROL readiness"
description: "CONTROL ONLY, never acceptance or completed gate"
version: 0.1.0
status: active
authoritative_source: .agent/evidence/114/release-readiness.md
change_log:
  - version: "0.1.0"
    date: "2026-10-12"
    summary: "CONTROL ONLY"
---
# CONTROL ONLY next MINOR readiness

Published and installed v1.5.0 unchanged. Existing C12 records prove no live behavior;
phase016 remains pending and unallocated. PLAN-WA pending; PLAN-016 pending after PLAN-WA.
Actual113 inputs: .agent/qa/113.json and .agent/evidence/113/evidence-gate.txt.
Assessed actual candidate sidecar: .agent/evidence/114/current-source-inputs.json.
Fresh independent QA and capture must precede canonical closure; this fixture creates neither.

## Human release boundary

Next-candidate H-FRAMEWORK-RELEASE remains outstanding; distinct later
H-CONSUMER-UPGRADE remains outstanding. Historical v1.5.0 acts remain executed.
'''

def header(path,version):
 h,b=C.body(C.old(path)); h['version']=version; h['change_log'].insert(0,{'version':version,'date':'2026-10-12','summary':'CONTROL ONLY114'})
 return h,b

def closed_debt_fixture(authorized):
 """A structural scratch model; referenced paths are not fabricated gates."""
 text=authorized.replace('version: 0.67.0\n','version: 0.68.0\n',1)
 text=text.replace('change_log:\n','change_log:\n  - version: "0.68.0"\n    date: "2026-10-12"\n    summary: "CONTROL ONLY structural051 resolution model; no production acceptance."\n',1)
 oldrow,cells=C.debt_row(text)
 cells[-1]=cells[-1].rstrip()+' CONTROL ONLY modeled references: '+C.GATES[3]+' '+C.GATES[4]+' '+C.E+'evidence-gate.txt '
 row='|'+'|'.join(cells)+'|\n'; text=text.replace(oldrow,'',1)
 start=text.index('## Resolved\n'); marker='|----|------|----------|-------------|------------|\n'; where=text.index(marker,start)+len(marker)
 return text[:where]+row+text[where:]

def source_fixture(scratch):
 for p in C.SOURCE[1:]:
  dest=scratch/p; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes((C.BASE/p).read_bytes())
 p=scratch/C.SOURCE[0]; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(dossier_fixture())
 p=scratch/'CHANGELOG.md'; p.write_text(p.read_text().replace('### Changed\n\n','### Changed\n\n- CONTROL ONLY114 readiness; no production QA.\n\n',1))
 path='docs/planning/ROADMAP.md'; h,b=header(path,'0.60.0'); heading='## Selected NIP-0003 — Authorized Phase015 Normative Plan'; oldspan=C.section(b,heading)
 b=b.replace(heading+'\n'+oldspan,heading+'\n'+oldspan+'CONTROL ONLY114 readiness overlay; canonical gates determine actual closure.\n\n',1)
 start=b.index('## Current Position '); n=__import__('re').search(r'(?ms)^- .*?(?=^- |^## |\Z)',b[start:]); b=b[:start+n.start()]+'- CONTROL ONLY phase015 feature114 readiness; no closure claim.\n'+b[start+n.end():]
 (scratch/path).write_text('---\n'+yaml.safe_dump(h,sort_keys=False)+'---\n'+b)
 path='docs/planning/backlog_reconciliation.md'; h,b=header(path,'0.1.14'); b=b.replace('## Prior reconciliation history','CONTROL ONLY114 readiness projection; no actual QA/capture/close claim.\n\n## Prior reconciliation history',1)
 (scratch/path).write_text('---\n'+yaml.safe_dump(h,sort_keys=False)+'---\n'+b)


def exercise(root,name,negative,scratch):
 if name in ('runtime-mixed-framework-forecast','system-mixed-framework-forecast','interpreter-mixed-framework-forecast','toolchain-predicate-does-not-exempt-release'):
  text=dossier_fixture()
  if negative: text+='\n'+{
   'runtime-mixed-framework-forecast':'Recorded SBCL runtime version 2.2.9.debian is input; next framework release V1.10.0.',
   'system-mixed-framework-forecast':'ASDF build system version 3.3.5 is recorded and next framework release candidate 1.10.0.',
   'interpreter-mixed-framework-forecast':'Python interpreter version 3.14.0 is recorded but framework version will be v123.456.789!',
   'toolchain-predicate-does-not-exempt-release':'Recorded SBCL runtime is a toolchain input next release v1.10.0.'}[name]+'\n'
  C.dossier(text); return
 if name=='past-recovery1-proof-corrupt':
  original='recovery-author1:.agent/evidence/114/check_114.py';meta=C.obj(root,C.E+'private/recovery1-history.json')['files'][original]
  destination=scratch/meta['path'];destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/meta['path'],destination)
  if negative:destination.write_bytes(destination.read_bytes()+b'CONTROL CORRUPTION\n')
  C.supplemental_members(scratch,{original:meta});return
 if name.startswith('toolchain-'):
  text=dossier_fixture()
  if negative: text+='\n'+{
   'toolchain-mixed-clause':'Recorded SBCL version 2.2.9.debian is a toolchain input; next framework release v1.10.0.',
   'toolchain-mixed-conjunction':'SBCL version 2.2.9.debian is recorded and next framework release V1.10.0.',
   'toolchain-mixed-comma-bare':'Recorded ASDF version 3.3.5, next framework version will be 1.10.0.',
   'toolchain-does-not-exempt-widemajor':'Python version 3.14.0 is a toolchain input but next release (v123.456.789).'}[name]+'\n'
  C.dossier(text); return
 if name in ('missing-original-archive','corrupt-original-archive'):
  original='.agent/contracts/114.json'; meta=C.obj(root,C.E+'recovery-halt-inventory.json')['files'][original]
  destination=scratch/meta['path']; destination.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/meta['path'],destination)
  if negative:
   if name=='missing-original-archive': destination.unlink()
   else: destination.write_bytes(destination.read_bytes()+b'CONTROL CORRUPTION\n')
  C.supplemental_members(scratch,{original:meta}); return
 if name in ('altered-non051-debt','premature051-resolution'):
  texts=[C.raw(root,p).decode() for p in (C.E+'private/original-debt.md',C.E+'recovery-halt-debt.md',C.E+'recovery-authorized-debt.md')]
  current=texts[-1]
  if negative:
   if name=='altered-non051-debt': current=current.replace('| NDEBT-040 |','| NDEBT-999 |',1)
   else: current=current.replace('version: 0.67.0\n','version: 0.68.0\n',1)
  C.debt_data(*texts,current,False); return
 if name.startswith('failed-'):
  contract=C.obj(root,'.agent/contracts/113.json'); qa=C.obj(root,'.agent/qa/113.json'); mb=C.obj(root,'.agent/validator/113-mode-b.json'); pre=C.obj(root,C.E+'predecessor113-pr-premerge.json'); merged=C.obj(root,C.E+'predecessor113-merge-main.json'); data=C.baseline_models()
  if negative and name=='failed-predecessor': qa['final_verdict']['approved']=False
  if negative and name=='failed-pr-check': pre['pr']['statusCheckRollup'][0]['conclusion']='FAILURE'
  C.predecessor_data(contract,qa,mb,pre,merged,data['features'],data['phase']); return
 if name=='candidate-tree-changed':
  tree=C.git(root,'rev-parse',C.APPROVED+'^{tree}').decode().strip(); C.candidate_tree(root,C.APPROVED,'0'*40 if negative else tree); return
 if name=='circular-sidecar-field':
  data={'format':1,'candidate':{'commit':C.APPROVED,'tree':'CONTROL_ONLY'},'fixed_inputs_sha256':'CONTROL_ONLY','contract_sha256':C.PIN,'source_paths':{},'canonical_precompletion':{}}
  if negative: data['future_qa_sha256']='CONTROL_ONLY'
  C.source_shape(data); return
 if name=='historical-proof-changed':
  path='.agent/qa/113.json'; dest=scratch/path; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/path,dest)
  meta=C.obj(root,C.E+'private/history.json')[path]
  if negative: dest.write_bytes(dest.read_bytes()+b'\nCONTROL CORRUPTION\n')
  C.history_members(scratch,{path:meta}); return
 if name in ('installed-ignored-extra-file','installed-extra-symlink'):
  original=C.obj(root,C.E+'private/history.json'); expected={p:meta for p,meta in original.items() if p.startswith('.nizam/')}
  # Copy only actual known installed files; no installed writes in real root.
  for path in expected:
   destination=scratch/path; destination.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/path,destination)
  if negative:
   extra=scratch/'.nizam/tools/__pycache__/testauthor_extra.pyc'; extra.parent.mkdir(parents=True,exist_ok=True)
   if name=='installed-extra-symlink': extra.symlink_to('../SKILL.md')
   else: extra.write_bytes(b'CONTROL ONLY ignored extra installed file\n')
  C.installed_inventory(scratch,original); C.history_members(scratch,expected); return
 if name=='untracked-stray': C.scope_paths([C.E+'control-only.txt']+(['unapproved-114.txt'] if negative else [])); return
 if name in ('future-version-sentence-period', 'future-version-comma', 'future-version-semicolon', 'future-version-colon', 'future-version-parentheses', 'future-version-markdown-closing', 'future-version-square-closing', 'future-version-uppercase', 'future-version-bare'):
  text=dossier_fixture()
  if negative: text+='\n'+{'future-version-sentence-period': 'Next release v1.10.0.', 'future-version-comma': 'Next release v1.10.0,', 'future-version-semicolon': 'Next release v1.10.0;', 'future-version-colon': 'Next release v1.10.0:', 'future-version-parentheses': 'Next release (v1.10.0).', 'future-version-markdown-closing': 'Next release `v1.10.0`.', 'future-version-square-closing': 'Next release [v1.10.0].', 'future-version-uppercase': 'Next release V1.10.0.', 'future-version-bare': 'Next release 1.10.0.'}[name]+'\n'
  C.dossier(text); return
 if name in ('fixed-future-release','false-liveproof','wa-allocation','future-version-multidigit'):
  text=dossier_fixture()
  if negative: text+='\n'+{'fixed-future-release':'Next release v1.6.0','false-liveproof':'All thirteen live proofs passed','wa-allocation':'WA allocated','future-version-multidigit':'Next release v1.10.0'}[name]+'\n'
  C.dossier(text); return
 if name in ('old-roadmap-prose','altered-released-changelog'):
  source_fixture(scratch)
  if negative:
   path='docs/planning/ROADMAP.md' if name=='old-roadmap-prose' else 'CHANGELOG.md'; p=scratch/path
   text=p.read_text(); text=text.replace('## Purpose and Authority','## Changed historical authority',1) if name=='old-roadmap-prose' else text.replace('## [1.5.0]','## [9.9.9]',1)
   C.need(text!=p.read_text(),'CONTROL_MUTATION_SETUP'); p.write_text(text)
  C.doc_deltas(scratch); return
 data=model(name=='unreferenced-qa')
 if negative:
  if name=='premature-phasecomplete': data['phase']['status']='complete'
  if name=='unreferenced-qa': next(x for x in data['features']['features'] if x['id']=='114').pop('qa')
  if name=='dag-edge-changed': next(x for x in data['dag']['packets'] if x['id']=='NIP3-114')['dependency_edges']['depends_on'].append('PLAN-016')
  if name=='plan016-premature': next(x for x in data['dag']['packets'] if x['id']=='PLAN-016')['prerequisites']['technical']['satisfied']=True
  if name=='old-counter-reset': data['state']['circuit_breaker']['113-checker-review']['attempts']=0
  if name=='budget-rebaseline': data['state']['scope_budget']['ceiling_130pct']=99999
  if name=='exhausted114-counter-reset': data['state']['circuit_breaker']['114-checker-review']['attempts']=0
  if name=='extra-recovery-counter': data['state']['circuit_breaker']['114-recovery-extra']={'attempts':0,'limit':3}
  if name=='recovery-counter-limit': data['state']['circuit_breaker']['114-recovery-checker-development']['limit']=4
  if name=='recovery-history-changed': data['state']['history'][-1]['event']='CONTROL CORRUPTION'
  if name=='historical114-budget-rebased': data['state']['scope_budget']['historical_inflight_measurements'][-1]['actual']=0
  if name=='recovery-authorization-changed': data['state']['pending_operator_gate']['decision']='denied'
 C.planning_data(data,name=='unreferenced-qa')


def main():
 parser=argparse.ArgumentParser(); parser.add_argument('--root',type=Path,required=True); parser.add_argument('--case'); parser.add_argument('--negative',action='store_true'); args=parser.parse_args(); root=args.root.resolve()
 if args.case:
  with tempfile.TemporaryDirectory(prefix='nizam114-control-',dir='/home/cnross/.tmp') as td:
   scratch=Path(td).resolve(); C.need(scratch.parent==Path('/home/cnross/.tmp') and scratch.name.startswith('nizam114-control-'),'OWNED_SCRATCH')
   exercise(root,args.case,args.negative,scratch)
  print('CONTROL COMPONENT PASS '+args.case); return
 print('CONTROL ONLY:'+str(len(CASES))+' preregistered negatives and restored positives; data models are not future approved gates, source acceptance or live runtime proof.')
 C.planning_data(model(False),False); C.planning_data(model(True),True); print('CONTROL structural precompletion/closed projections PASS; productionclosure still requires actual QA/capture.')
 texts=[C.raw(root,p).decode() for p in (C.E+'private/original-debt.md',C.E+'recovery-halt-debt.md',C.E+'recovery-authorized-debt.md')]
 C.debt_data(*texts,texts[-1],False); C.debt_data(*texts,closed_debt_fixture(texts[-1]),True)
 print('CONTROL structural051 authorized-open/resolved masks PASS; modeled references are not actual approvals or production completion.')
 for addition in ['Historical v0.14.3. Current v1.5.0.', 'Historical v1.4.0, current v1.5.0;', 'Historical (v1.4.0): current `v1.5.0`.', 'Historical [v0.99.123] and current <v1.5.0>.', 'Historical framework version 1.4.0. Current framework version 1.5.0.', 'Current V1.5.0; historical V0.14.3.', 'Recorded SBCL 2.2.9 and ASDF 3.3.5; date 2026-10-12.', 'Recorded SBCL v2.2.9; existing framework v1.5.0.']:
  C.dossier(dossier_fixture()+'\n'+addition+'\n'); print('CONTROL punctuation current/historical positive PASS '+addition)
 for addition in [
  'Recorded SBCL version 2.2.9.debian is a toolchain input; framework release remains v1.5.0.',
  'Recorded ASDF version 3.3.5 and Python version 3.14.0 are toolchain inputs; current framework v1.5.0.',
  'SBCL release V2.2.9 is recorded, while framework release remains 1.5.0.',
  'Python version will be 3.14.0; next MINOR framework version remains undecided.',
  'SBCL version 2.2.9.debian and historical framework version 0.99.123; current framework version 1.5.0.']:
  C.dossier(dossier_fixture()+'\n'+addition+'\n'); print('CONTROL named-subject positive PASS '+addition)
 for addition in [
  'Recorded SBCL runtime version 2.2.9.debian is a toolchain input; framework release remains v1.5.0.',
  'Recorded ASDF system version 3.3.5 is a toolchain input; current framework v1.5.0.',
  'Recorded Python interpreter version 3.14.0 is a toolchain input; framework release remains v1.5.0.',
  'Recorded SBCL optimized native Lisp runtime version 2.2.9.debian is input; framework remains v1.5.0.']:
  C.dossier(dossier_fixture()+'\n'+addition+'\n');print('CONTROL nominal-declaration positive PASS '+addition)
 for name,diagnostic,classification in CASES:
  print('PREREGISTERED '+name+' negative EXIT1 diagnostic='+diagnostic+' class='+classification+'; positive/restored EXIT0')
  for label,bad,expected in [('POSITIVE',False,0),('NEGATIVE',True,1),('RESTORED',False,0)]:
   command=[sys.executable,str(Path(__file__).resolve()),'--root',str(root),'--case',name]+(['--negative'] if bad else [])
   p=subprocess.run(command,cwd=root,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True)
   print('CONTROL '+name+' '+label+' actual EXIT'+str(p.returncode)); print(p.stdout,end=''); print(p.stderr,end='')
   C.need(p.returncode==expected,'CONTROL_EXIT:'+name+':'+label)
   if bad: C.need('TARGET DIAGNOSTIC: '+diagnostic+'\n' in p.stdout,'CONTROL_DIAGNOSTIC:'+name)
 print('CONTROL ALL'+str(len(CASES))+' targeted negatives plus restored positives PASS; no acceptance or production completion claim.')
if __name__=='__main__':
 try: main()
 except C.Failure as error:
  print('TARGET DIAGNOSTIC: '+str(error)); raise SystemExit(1)
