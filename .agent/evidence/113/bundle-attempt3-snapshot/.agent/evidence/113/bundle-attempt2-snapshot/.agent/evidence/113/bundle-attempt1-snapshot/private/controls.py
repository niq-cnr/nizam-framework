#!/usr/bin/env python3
"""Preregistered scratch mutations with exact diagnostics, exits and restoration.

Synthetic source is a private test fixture, not the delivered product. Its local
Git candidate is real and contains no future QA/source-review verdicts or hashes.
Each restored positive must pass the same component after its targeted negative.
"""
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

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('feature113', HERE.parent / 'check_113.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def dump(root, path, value):
    (root/path).write_text(json.dumps(value, indent=2)+'\n')


def document(root, path, version, body, enforcement=None):
    front, _ = c.doc(c.BASE, path)
    front['version'] = version
    front['change_log'].insert(0, {'version':version,'date':'2026-10-12','summary':'PRIVATE CONTROL FIXTURE ONLY'})
    if enforcement:
        front['enforcement'] = enforcement
    (root/path).write_text('---\n'+yaml.safe_dump(front,sort_keys=False)+'---'+body)


def fixture(root):
    _, old = c.doc(c.BASE, 'tools/interface.md')
    operations = c.contract()['implementation_requirements']['operations']
    operations_text = '\n'.join('| `'+op+'` | '+('Executes project code.' if op=='submit-operation' else 'Lifecycle or observation control only.')+' |' for op in operations)
    rules = [
        'Records validate against schemas; declared record validity proves no live behavior.',
        'Reject stale generation and lease before execution; identity must match current owner.',
        'At most one operation in flight; lifecycle/reattach preserves outstanding work.',
        'A timeout stops waiting only, never reports execution stopped.',
        'Capture before unwind; failed load or compile never claims image consistency.',
        'Review trials receive no endpoint or permission and requests are rejected.',
        'Lifecycle operations never evaluate project code.',
        'Session results are never acceptance evidence; acceptance uses fresh process/build/hermetic resources.',
        'Attempt counters survive a new generation or process; contract step attempt never resets.'
    ]
    optional = '''## 6. Optional Capability: Live Runtime Sessions

Only `submit-operation` executes project code, including `observe`.
Nonclaiming adapters remain conformant; these calls and S1-S9 apply only to claiming adapters.
There is no separate status call; existing `read-state` reads durable records.
`runtime.session.lifecycle` cannot operate/accept; `runtime.session.operate` is Generator development,
and `runtime.session.accept` is Evaluator fresh acceptance.

| Operation | Purpose |
| --- | --- |
'''+operations_text+'''

Kinds: `load_source`, `compile_source`, `evaluate`, `run_tests`, `observe`.
Request: `operation_id`, `session_id`, `expected_generation` {`counter`, `nonce`},
`expected_lease_epoch`, `requester` {`principal_kind`, `role`, `agent_id`},
`contract_id`, `step_key`, `attempt`, `kind`, `payload`, `context` {`working_dir`, `namespace`, reader/test config refs}, `limits`.
Statuses: `completed`, `condition_signalled`, `cancelled`, `terminated`, `rejected`,
`running`, `cancel_requested`, `unknown`. `debugger_paused` is optional, not emitted in v1.
`wait_outcome`: `stopped_waiting` retains outstanding execution and busy lane.

| Check | Requirement |
| --- | --- |
'''+ '\n'.join('| S'+str(i)+' | '+text+' |' for i,text in enumerate(rules,1))+'\n\n'
    refs = old[old.index('## 6. References'):].replace('## 6.', '## 7.',1)
    refs += '\n- `methodology/10_live_runtime_sessions.md` and `methodology/11_sbcl_runtime_binding.md`.\n- `schema/runtime_session.schema.json` and `schema/runtime_operation.schema.json`.\n'
    document(root,'tools/interface.md','0.4.0',old[:old.index('## 6. References')]+optional+refs)
    m = c.js(c.BASE,'tools/skill.json'); m['version']='0.6.0'
    m['runtime_requirements']['live_runtime_session']={'required':False,'description':'Optional for claiming adapters only.'}
    m['capabilities'] += [{'name':'live_runtime_session','module':'tools/interface.md','description':'Optional adapter.'}, {'name':'sbcl_runtime_binding','module':'methodology/11_sbcl_runtime_binding.md','description':'Normative binding.'}]
    dump(root,'tools/skill.json',m)
    index = c.js(c.BASE,'NIZAM.json');index['capabilities'].append({'id':'nizam-live-runtime-adapter','summary':'Optional adapter.','authoritative_source':'tools/interface.md'});dump(root,'NIZAM.json',index)
    _,old=c.doc(c.BASE,'tools/SKILL.md');refs=old[old.index('## 10. References'):].replace('## 10.','## 11.',1)
    refs += '\n- `methodology/10_live_runtime_sessions.md` and `methodology/11_sbcl_runtime_binding.md`.\n'
    inserted='''## 10. Live Runtime Sessions

For claiming adapters, read `tools/interface.md`, `methodology/10_live_runtime_sessions.md`
and `methodology/11_sbcl_runtime_binding.md`; capability remains optional.

'''
    document(root,'tools/SKILL.md','0.6.0',old[:old.index('## 10. References')]+inserted+refs)
    _,old=c.doc(c.BASE,'tools/README.md')
    extra='Optional runtime adapters follow [sessions](../methodology/10_live_runtime_sessions.md), [SBCL binding](../methodology/11_sbcl_runtime_binding.md) and [interface](interface.md). Nonclaiming consumers remain conformant.'
    document(root,'tools/README.md','0.20.0',old.replace('## Design Decision',extra+'\n\n## Design Decision',1))
    _,old=c.doc(c.BASE,c.PRODUCT[5]); start=old.index('A runtime session')
    intro='''

# Live Runtime Sessions

This protocol is **partially-enforced** through existing schema and C12 record validation only;
these declared-record checks cannot prove live runtime behavior. The optional
[adapter interface](../tools/interface.md) is normatively delivered, as is the
[SBCL binding](11_sbcl_runtime_binding.md). Executable controller/adapter/SBCL
enforcement and all thirteen live conformance proofs remain pending phase016.

'''
    body=intro+old[start:]
    marker='The normative\nSBCL reference binding is delivered.'
    begin=body.index(marker);end=body.index('\n\n| requirement-id',begin)
    body=body[:begin]+marker+' The optional [adapter interface](../tools/interface.md) is delivered; executable controller/SBCL enforcement and all live proofs remain pending phase016.'+body[end:]
    document(root,c.PRODUCT[5],'0.2.0',body,'partially-enforced')
    _,old=c.doc(c.BASE,c.PRODUCT[6]);heading='## 1. Binding scope and evidence boundary\n\n'
    body=old.replace(heading,heading+'The optional [adapter interface](../tools/interface.md) routes claiming consumers.\n\n',1)
    document(root,c.PRODUCT[6],'0.1.1',body)
    old=c.read(c.BASE,'CHANGELOG.md');(root/'CHANGELOG.md').write_text(old.replace('### Changed\n\n','### Changed\n\n- **Optional live-runtime adapter (feature113).** Normative optional routing only; controller and live proofs pending.\n\n',1))


def invoke(root, component):
    p=subprocess.run([sys.executable,str(HERE/'control_worker.py'),str(root),component],text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    return p.returncode,p.stdout+p.stderr


def preregister(name, component, path, diagnostic, budget_class):
    return {'name':name,'component':component,'path':path,'expected_exit':1,
            'expected_diagnostic':diagnostic,'budget_class':budget_class,'restored_exit':0}


# Every target is declared before the scratch candidate or mutations execute.
PLAN = [
    preregister('optional-required-true','routing','tools/skill.json','OPTIONAL_REQUIRED_FALSE','budget/product'),
    preregister('optional-absent-default-disabled','routing','tools/skill.json','OPTIONAL_REQUIRED_FALSE','budget/product'),
    preregister('mandatory-requirement-removed','compatibility','tools/skill.json','MANIFEST_BASE_PRESERVED','budget/product'),
    preregister('old-ten-item-body-altered','compatibility','tools/interface.md','INTERFACE_BASE_BODY','budget/product'),
    preregister('eleventh-base-item','compatibility','tools/interface.md','INTERFACE_BASE_BODY','budget/product'),
    preregister('missing-operation','surface','tools/interface.md','OPERATIONS_EXACT','budget/product'),
    preregister('duplicate-operation','surface','tools/interface.md','OPERATIONS_EXACT','budget/product'),
    preregister('extra-status-call','surface','tools/interface.md','OPERATIONS_EXACT','budget/product'),
    preregister('missing-s9','surface','tools/interface.md','S_RULES_EXACT','budget/product'),
    preregister('duplicate-s1','surface','tools/interface.md','S_RULES_EXACT','budget/product'),
    preregister('misplaced-s5-keyword','surface','tools/interface.md','S_RULE_CONTENT:5','budget/product'),
    preregister('misplaced-router-marker','routing','tools/SKILL.md','ROUTER_PATH:methodology/10_live_runtime_sessions.md','budget/product'),
    preregister('duplicate-manifest-route','routing','tools/skill.json','DUPLICATE_MANIFEST_ROUTE','budget/product'),
    preregister('index-route-misdirected','routing','NIZAM.json','INDEX_ROUTE','budget/product'),
    preregister('missing-schema-crosslink','routing','tools/interface.md','SCHEMA_LINK:schema/runtime_operation.schema.json','budget/product'),
    preregister('version-not-increased','delta','tools/interface.md','VERSION:tools/interface.md','budget/product'),
    preregister('changed-old-r1','delta','methodology/10_live_runtime_sessions.md','RUNTIME_SECTION_PRESERVED:1','budget/product'),
    preregister('record-boundary-erased','claim','methodology/10_live_runtime_sessions.md','RECORD_ONLY_ENFORCEMENT','budget/product'),
    preregister('false-live13-proof','claim','tools/interface.md','FALSE_DELIVERY_CLAIM:tools/interface.md','budget/product'),
    preregister('foreign-ecosystem-scope','claim','tools/interface.md','FALSE_DELIVERY_CLAIM:tools/interface.md','budget/product'),
    preregister('false-release','claim','tools/interface.md','FALSE_DELIVERY_CLAIM:tools/interface.md','budget/product'),
    preregister('installed-content-changed','history','.nizam/NIZAM.json','HISTORY_OR_INSTALLED:.nizam/NIZAM.json','UNCLASSIFIED'),
    preregister('installed-mode-changed','history','.nizam/NIZAM.json','HISTORY_OR_INSTALLED:.nizam/NIZAM.json','UNCLASSIFIED'),
    preregister('historical-proof-changed','history','.agent/qa/112.json','HISTORY_OR_INSTALLED:.agent/qa/112.json','budget/verdict'),
    preregister('out-of-scope-tracked','history','README.md','HISTORY_OR_INSTALLED:README.md','budget/product-ext'),
    preregister('out-of-scope-untracked','history','alien113.txt','OUT_OF_SCOPE:alien113.txt','UNCLASSIFIED'),
    preregister('successor-promoted','lifecycle','.agent/feature_list_015.json','PREDECESSOR_SUCCESSOR:114','budget/planning'),
    preregister('predecessor-rewritten','lifecycle','.agent/feature_list_015.json','PREDECESSOR_SUCCESSOR:112','budget/planning'),
    preregister('phase-prematurely-complete','lifecycle','docs/planning/phase_015.yaml','PHASE_CONTINUITY','budget/planning'),
    preregister('attempt-counter-reset','lifecycle','.agent/run_state.json','COUNTER_CONTINUITY:113-contract','excluded/run_state'),
    preregister('budget-ceiling-rebased','lifecycle','.agent/run_state.json','BUDGET_CONTINUITY','excluded/run_state'),
    preregister('budget-overrun','lifecycle','.agent/run_state.json','BUDGET_CONTINUITY','excluded/run_state'),
    preregister('fixed-seal-corrupt','integrity','.agent/evidence/113/fixed-inputs-seal.json','FIXED_SEAL','evidence'),
    preregister('fixed-member-corrupt','integrity','.agent/evidence/113/evidence_gate.py','FIXED_MEMBER:.agent/evidence/113/evidence_gate.py','evidence'),
    preregister('source-seal-corrupt','integrity','.agent/evidence/113/current-source-seal.json','SOURCE_SEAL','evidence'),
    preregister('candidate-tree-corrupt','integrity','.agent/evidence/113/current-source-inputs.json','CANDIDATE_TREE','evidence'),
    preregister('actual-counted-budget-overrun','budget','.agent/contracts/113-budget-overrun-control.json','BUDGET_ACTUAL_CEILING','budget/contract'),
]


def mutate(root, item):
    name,path=item['name'],item['path'];p=root/path
    if name=='installed-mode-changed':
        p.chmod(stat.S_IMODE(p.stat().st_mode)^0o100);return
    if name=='out-of-scope-untracked':p.write_text('CONTROL_ONLY\n');return
    if name=='actual-counted-budget-overrun':p.write_text('CONTROL_ONLY\n'*3300);return
    text=p.read_text()
    if path.endswith('.json') and name not in ('installed-content-changed','historical-proof-changed'):
        data=json.loads(text)
        if name=='optional-required-true':data['runtime_requirements']['live_runtime_session']['required']=True
        elif name=='optional-absent-default-disabled':data['runtime_requirements'].pop('live_runtime_session')
        elif name=='mandatory-requirement-removed':data['runtime_requirements'].pop('shell_execution')
        elif name=='duplicate-manifest-route':data['capabilities'].append(copy.deepcopy(data['capabilities'][-1]))
        elif name=='index-route-misdirected':data['capabilities'][-1]['authoritative_source']='tools/SKILL.md'
        elif name in ('successor-promoted','predecessor-rewritten'):
            target='114' if name=='successor-promoted' else '112';next(x for x in data['features'] if x['id']==target)['status']='in_progress'
        elif name=='attempt-counter-reset':data['circuit_breaker']['113-contract']['attempts']=0
        elif name=='budget-ceiling-rebased':data['scope_budget']['ceiling_130pct']=9999
        elif name=='budget-overrun':data['scope_budget']['total_lines_changed']=9361
        elif name in ('fixed-seal-corrupt','source-seal-corrupt'):data['manifest_sha256']='0'*64
        elif name=='candidate-tree-corrupt':
            data['candidate']['tree']='0'*40;dump(root,path,data)
            seal=c.js(root,'.agent/evidence/113/current-source-seal.json');seal['manifest_sha256']=c.sha(p);dump(root,'.agent/evidence/113/current-source-seal.json',seal);return
        else:raise AssertionError(name)
        dump(root,path,data);return
    if name=='old-ten-item-body-altered':text=text.replace('The adapter locates','The adapter ignores',1)
    elif name=='eleventh-base-item':text=text.replace('## 6. Optional','11. A new mandatory runtime requirement.\n\n## 6. Optional',1)
    elif name=='missing-operation':text=text.replace('| `open-session` | Lifecycle or observation control only. |\n','',1)
    elif name=='duplicate-operation':text=text.replace('| `open-session` |','| `open-session` | duplicate |\n| `open-session` |',1)
    elif name=='extra-status-call':text=text.replace('| Operation |','| `status-call` | extra |\n| Operation |',1)
    elif name=='missing-s9':text=text.replace('| S9 |','| X9 |',1)
    elif name=='duplicate-s1':text=text.replace('| S2 |','| S1 |',1)
    elif name=='misplaced-s5-keyword':text=text.replace('Capture before unwind;','Capture before handler;',1)+'\nunwind\n'
    elif name=='misplaced-router-marker':
        start=text.index('## 10. Live Runtime Sessions');end=text.index('## 11. References',start)
        text=text[:start]+text[start:end].replace('methodology/10_live_runtime_sessions.md','methodology/missing.md')+text[end:]
    elif name=='missing-schema-crosslink':text=text.replace('schema/runtime_operation.schema.json','schema/missing.schema.json')
    elif name=='version-not-increased':text=text.replace('version: 0.4.0','version: 0.3.1',1)
    elif name=='changed-old-r1':text=text.replace('| R1 |','| R0 |',1)
    elif name=='record-boundary-erased':text=text.replace('cannot prove live runtime behavior','proves live runtime behavior',1)
    elif name=='false-live13-proof':text+='\nAll thirteen live cases passed.\n'
    elif name=='foreign-ecosystem-scope':text+='\nThis repository is governed by NizamIQ.\n'
    elif name=='false-release':text+='\nReleased framework v1.6.0.\n'
    elif name=='phase-prematurely-complete':text=text.replace('status: in_progress','status: complete',1)
    else:text+='\nCONTROL_CORRUPTION\n'
    p.chmod(p.stat().st_mode|0o200);p.write_text(text)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--print-plan',action='store_true');args=parser.parse_args()
    if args.print_plan:print(json.dumps(PLAN,indent=2));return
    source=args.root.resolve();assert source.is_dir() and (source/'.git').exists()
    with tempfile.TemporaryDirectory(prefix='nizam113-controls-') as temp:
        scratch=Path(temp)/'repo'
        p=subprocess.run(['git','clone','--quiet','--shared','--no-checkout',str(source),str(scratch)],text=True,capture_output=True);assert p.returncode==0,p.stderr
        shutil.copytree(source,scratch,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git','__pycache__'))
        fixture(scratch)
        for args_git in (('read-tree','HEAD'),('config','user.name','Private Controls'),('config','user.email','controls@example.invalid'),('add','--',*c.PRODUCT),('commit','--quiet','-m','PRIVATE synthetic controls candidate')):
            c.git(scratch,*args_git)
        candidate=c.git(scratch,'rev-parse','HEAD');tree=c.git(scratch,'rev-parse','HEAD^{tree}')
        fixed={'format':1,'base_revision':c.contract()['base_revision'],'approved_base':c.git(source,'rev-parse','HEAD'),'contract_sha256':c.sha(scratch/'.agent/contracts/113.json'),
               'actors':{'test_author':'/root/adapter_test_author_113','generator':'/root/adapter_generator_113','bundle_reviewer':'/root/adapter_validator_113','final_qa':'/root/adapter_acceptance_113'},
               'files':{'.agent/evidence/113/evidence_gate.py':{'sha256':c.sha(scratch/'.agent/evidence/113/evidence_gate.py'),'mode':c.mode(scratch/'.agent/evidence/113/evidence_gate.py')}}}
        dump(scratch,'.agent/evidence/113/fixed-inputs.json',fixed);dump(scratch,'.agent/evidence/113/fixed-inputs-seal.json',{'manifest_sha256':c.sha(scratch/'.agent/evidence/113/fixed-inputs.json')})
        current={'format':1,'candidate':{'commit':candidate,'tree':tree},'fixed_inputs_sha256':c.sha(scratch/'.agent/evidence/113/fixed-inputs.json'),'contract_sha256':fixed['contract_sha256'],
                 'source_paths':{path:{'sha256':c.sha(scratch/path),'mode':c.mode(scratch/path)} for path in c.PRODUCT}}
        dump(scratch,'.agent/evidence/113/current-source-inputs.json',current);dump(scratch,'.agent/evidence/113/current-source-seal.json',{'manifest_sha256':c.sha(scratch/'.agent/evidence/113/current-source-inputs.json'),'candidate_commit':candidate})
        for component in ('surface','routing','compatibility','delta','history','lifecycle','claim','integrity','budget'):
            rc,out=invoke(scratch,component);print('POSITIVE',component,'EXIT',rc,out.strip());assert rc==0,component
        for item in PLAN:
            path=scratch/item['path'];existed=path.exists();original=path.read_bytes() if existed else None;permissions=stat.S_IMODE(path.stat().st_mode) if existed else None
            # A candidate-tree mutation also updates its source seal to reach its target.
            seal=scratch/'.agent/evidence/113/current-source-seal.json';seal_original=seal.read_bytes()
            print('PREREGISTERED',json.dumps(item,sort_keys=True))
            try:
                mutate(scratch,item);rc,out=invoke(scratch,item['component']);print('NEGATIVE',item['name'],'EXIT',rc,out.strip());assert rc==item['expected_exit'] and item['expected_diagnostic'] in out,item['name']
            finally:
                if existed:path.chmod(permissions|0o200);path.write_bytes(original);path.chmod(permissions)
                else:path.unlink(missing_ok=True)
                seal.write_bytes(seal_original)
            rc,out=invoke(scratch,item['component']);print('RESTORED',item['name'],'EXIT',rc,out.strip());assert rc==0,item['name']
        measure=[sys.executable,str(scratch/'.agent/evidence/scope-budget-014/measure.py'),'--range','113='+c.contract()['base_revision']+'..','--files']
        p=subprocess.run(measure,cwd=scratch,text=True,capture_output=True);print('FROZEN_BUDGET_POSITIVE_EXIT',p.returncode);assert p.returncode==0,p.stderr
        alien=scratch/'unclassified113.txt';alien.write_text('CONTROL_ONLY\n')
        try:
            p=subprocess.run(measure,cwd=scratch,text=True,capture_output=True);print('FROZEN_BUDGET_UNCLASSIFIED_EXIT',p.returncode);assert p.returncode==3 and 'UNCLASSIFIED' in p.stdout and 'unclassified113.txt' in p.stdout
        finally:alien.unlink()
        p=subprocess.run(measure,cwd=scratch,text=True,capture_output=True);print('FROZEN_BUDGET_RESTORED_EXIT',p.returncode);assert p.returncode==0
        print('CONTROL_SUITE:PASS; cases='+str(len(PLAN))+'; synthetic component proof only; no source-review/QA verdict authored')


if __name__=='__main__':main()
