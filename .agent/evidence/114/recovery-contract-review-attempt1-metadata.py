#!/usr/bin/env python3
"""Recovery pre-code metadata only: schema/hash/diff/archive checks, no acceptance."""
from pathlib import Path
import hashlib,json,stat,subprocess
import jsonschema,yaml
r=Path.cwd(); e='.agent/evidence/114/'; pin='e92511922f2689e2a400990d6765a5a570bc26374c94d5b1fc934f889c19e3c9'
def obj(p): return json.loads((r/p).read_bytes())
c=obj('.agent/contracts/114.json'); original=obj(e+'recovery-original/.agent/contracts/114.json')
assert hashlib.sha256((r/'.agent/contracts/114.json').read_bytes()).hexdigest()==pin
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='ea41afd196dddaef02f6be86217c84deaf47d238'
jsonschema.validate(c,obj('.nizam/schema/contract.schema.json'))
assert c['status']=='proposed' and c['approvals']['validator_mode_a'] is False and c['approvals']['evaluator_contract_review'] is False
assert c['verification']==original['verification'] and len(c['verification'])==12 and c['estimated_lines']==original['estimated_lines']==1150
assert c['scope']['files_create']==original['scope']['files_create'] and c['scope']['files_modify'][:-1]==original['scope']['files_modify'] and c['scope']['files_modify'][-1]['path']=='docs/planning/DEBT.md'
f=obj('.agent/feature_list_015.json'); feature=next(x for x in f['features'] if x['id']=='114'); assert [v['command'] for v in c['verification'][:6]]==feature['acceptance_tests']
assert feature['status']=='blocked' and feature['passes'] is False and next(x for x in f['features'] if x['id']=='113')['status']=='complete'
print('Actual proposed pin/schema/false pre-code flags/12commands/1150 and original sixSource scope preserved; sole added path is Parent-only051 debt mask. Canonical114 blocked,113complete.')
auth=obj(e+'recovery-authorization.json'); assert auth['gate']=='H-CHECKER-114-RECOVERY' and auth['decision']=='approved' and auth['epoch']==c['recovery']['epoch']=='114-recovery-1'
state=obj('.agent/run_state.json'); assert state['scope_budget']['total_lines_changed']==6779 and state['scope_budget']['original_estimate_lines']==7200 and state['scope_budget']['ceiling_130pct']==9360
for key,count in [('114-contract',1),('114-checker-development',3),('114-checker-review',3)]: assert state['circuit_breaker'][key]=={'attempts':count,'limit':3}
for key in ['114-recovery-contract','114-recovery-checker-development','114-recovery-checker-review']: assert state['circuit_breaker'][key]['limit']==3 and 0<=state['circuit_breaker'][key]['attempts']<=3
print('Explicit human recovery auth and bounded freshkeys verified; old exhausted3/3 and completed6779 budget preserved.')
inventory=obj(e+'recovery-halt-inventory.json'); assert len(inventory['files'])==485 and inventory['immutable_halt_base']==c['recovery']['halt_base']
for key,meta in inventory['files'].items():
 p=r/meta['path']; assert p.is_file() and not p.is_symlink(),key
 assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256'] and stat.S_IMODE(p.stat().st_mode)==meta['permissions'],key
oldhistory=[meta['path'] for key,meta in inventory['files'].items() if key.endswith('/private/history.json') and meta['sha256']=='764cd7d54f31158c375cb4ce69bac3e0ff711f0f61058bbc48bef546e106df30']; assert oldhistory
history=obj(oldhistory[0]); assert len(history)==4800 and '.agent/contracts/114.json' not in history and len([p for p in history if p.startswith('.nizam/')])==239
for path,meta in history.items():
 if path=='docs/planning/DEBT.md': continue
 p=r/path; assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256'] and stat.S_IMODE(p.stat().st_mode)==meta['permissions'],path
for meta in obj(e+'recovery-original/inventory.json').values():
 p=r/meta['archive']; assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256'] and stat.S_IMODE(p.stat().st_mode)==meta['permissions']
assert hashlib.sha256((r/(e+'recovery-original-debt.md')).read_bytes()).hexdigest()=='efaf7f488c42302f82661b51090fabc9f19f842c3814ab2390e255cb6fd5d3f2'
assert (r/(e+'recovery-halt-debt.md')).read_bytes()==subprocess.check_output(['git','show','ea41afd196dddaef02f6be86217c84deaf47d238:docs/planning/DEBT.md'])
assert stat.S_IMODE((r/(e+'recovery-original-debt.md')).stat().st_mode)==436
print('Actual485 supplementary bytes/fullmodes and canonical-original archive maps verified; original4800 seal found in immutable snapshots,4799current original members plus239installed preserved, originaldebt0.65/halt0.66 actualpins verified.')
print('PRE-CODE METADATA PASS ONLY. No acceptance/dev/helper/test/source/canonical/debt/counter edits or old verifier runs; renewed ModeA and Evaluator verdicts still actual distinct gates.')
