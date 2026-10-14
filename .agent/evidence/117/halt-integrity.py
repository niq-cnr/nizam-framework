"""Orchestrator halt-state integrity observation; no gate verdict."""
import hashlib,json,subprocess,stat
from pathlib import Path
import jsonschema,yaml
r=Path.cwd()
def read(p): return json.loads((r/p).read_text())
def old(p): return json.loads(subprocess.check_output(['git','show','374cb04:'+p]))
def typed(x): return json.dumps(x,sort_keys=True,separators=(',',':'))
s=read('.agent/run_state.json');b=old('.agent/run_state.json')
assert typed(s['history'][:len(b['history'])])==typed(b['history'])
assert typed(s['scope_budget']['per_feature'])==typed(b['scope_budget']['per_feature'])
assert s['scope_budget']['total_lines_changed']==3009
assert typed(s['completed_contract_ids'])==typed(b['completed_contract_ids'])
assert typed(s['phase_015_scope_budget_final'])==typed(b['phase_015_scope_budget_final'])
for k,v in b['circuit_breaker'].items():
 if k not in {'117-contract-review','117-mode-a'}:assert typed(s['circuit_breaker'][k])==typed(v)
assert s['circuit_breaker']['117-contract-review']['attempts']==3
assert s['status']=='blocked'and s['current_feature']=='117'and s['active_contract_id']is None
assert s['blocked_features']==b['blocked_features']+['117']
f=read('.agent/feature_list_017.json');bf=old('.agent/feature_list_017.json')
assert typed(f['features'][:2])==typed(bf['features'][:2]);assert typed(f['features'][3])==typed(bf['features'][3])
assert f['phase_status']=='blocked'and f['features'][2]['status']=='blocked'and f['features'][2]['passes']is False
p=yaml.safe_load((r/'docs/planning/phase_017.yaml').read_text());assert p['status']=='blocked'and [x['status']for x in p['steps']]==['COMPLETED','COMPLETED','BLOCKED','PENDING']
for obj,name in [(s,'run_state'),(f,'feature_list'),(p,'phase'),(read('.agent/contracts/117.json'),'contract')]:jsonschema.validate(obj,read('.nizam/schema/'+name+'.schema.json'))
assert read('.agent/contracts/117.json')['status']=='proposed'
assert typed(read('.agent/contracts/117.json'))==typed(old('.agent/contracts/117.json'))
assert not(r/'.agent/qa/117.json').exists()and not(r/'.agent/qa/117-contract-review.json').exists()
assert not(r/'.agent/validator/117-mode-a-rev1.json').exists()
assert not(r/'.agent/evidence/117/source-candidate.json').exists()
c=read('.agent/evidence/116/source-candidate.json')
for path,h in c['source_sha256'].items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==h
changed=subprocess.check_output(['git','diff','--name-only','374cb04'],text=True).splitlines()
allowed={'.agent/run_state.json','.agent/feature_list_017.json','docs/planning/phase_017.yaml','docs/planning/manifest.json','docs/planning/backlog_dag.json','docs/planning/DEBT.md'}
assert set(changed)<=allowed
# All old evidence/gates and installed files retain their original regular-file modes.
rows=subprocess.check_output(['git','ls-tree','-r','374cb04','.agent/evidence','.agent/qa','.agent/validator','.nizam'],text=True).splitlines()
for line in rows:
 meta,path=line.split('\t');mode=meta.split()[0];a=r/path
 assert a.is_file()and not a.is_symlink()
 assert bool(a.stat().st_mode&0o111)==(mode=='100755')
print('PASS canonical/derivedBLOCKED; fourinstalledschemas; 115/116 measured/history/counter prefixes, SourceC hashes, oldproof bytes/modes and installedpaths preserved; no117approval/Source/QA inferred')
