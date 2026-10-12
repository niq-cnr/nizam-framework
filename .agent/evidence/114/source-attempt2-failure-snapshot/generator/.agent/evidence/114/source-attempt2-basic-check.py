from pathlib import Path
import json,copy,hashlib,stat,subprocess,importlib.util
import yaml,jsonschema
p=Path('.').resolve(); B='33fd885115981e7ae479dfff7ad7d5a623d8014c'
S=('.agent/evidence/114/release-readiness.md','CHANGELOG.md','docs/planning/ROADMAP.md','docs/planning/manifest.json','docs/planning/backlog_dag.json','docs/planning/backlog_reconciliation.md')
def prior(path): return subprocess.check_output(['git','show',B+':'+path],cwd=p)
def j(path): return json.loads((p/path).read_bytes())
assert hashlib.sha256((p/'.agent/run_state.json').read_bytes()).hexdigest()=='5819ef53bae5be1ea07abde4beb9715288594b29f56c48c4d7a8e1aed962f239'
assert stat.S_IMODE((p/'.agent/run_state.json').stat().st_mode)==436
schema=j('.nizam/schema/frontmatter.schema.json')
for path in (S[0],S[2],S[5]):
 text=(p/path).read_text();assert text.startswith('---\n')
 front=yaml.safe_load(text.split('---\n',2)[1]);jsonschema.Draft202012Validator(schema).validate(front)
jsonschema.Draft202012Validator(j('.nizam/schema/manifest.schema.json')).validate(j(S[3]))
# The independently reviewed predicate grades only Markdown section masks.
spec=importlib.util.spec_from_file_location('reviewed114metadata',p/'.agent/evidence/114/check_114.py')
reviewed=importlib.util.module_from_spec(spec);spec.loader.exec_module(reviewed);reviewed.doc_deltas(p)
manifest=j(S[3]); old=json.loads(prior(S[3])); m=copy.deepcopy(manifest)
row=next(x for x in m['phases'] if x['id']=='015-live-runtime-normative');o=next(x for x in old['phases'] if x['id']==row['id'])
assert row['status']=='in_progress' and row['activation_state']=='active' and '114' in row['note']
row['status']=o['status'];row['note']=o['note'];m['updated_at']=old['updated_at'];assert m==old
original=json.loads(prior(S[4]));d=copy.deepcopy(j(S[4]));oldpacks={x['id']:x for x in original['packets']}
assert d['activated_phase']['current_status']=='in_progress' and '114' in d['activated_phase']['run_state_position']
for key in ('current_status','run_state_position'):d['activated_phase'][key]=original['activated_phase'][key]
d['generated_at']=original['generated_at']
for packet in d['packets']:
 name=packet['id'];o=oldpacks[name]
 if name not in ('NIP3-113','NIP3-114','PLAN-WA','PLAN-016'):
  assert packet==o;continue
 assert packet['status']==('complete' if name=='NIP3-113' else 'in_progress' if name=='NIP3-114' else 'pending')
 assert packet['authority_status']=='authorized'
 if name.startswith('NIP3-'):
  assert packet['evidence'][:len(o['evidence'])]==o['evidence']
  assert packet['prerequisites']['technical']['satisfied'] is True
  assert packet['prerequisites']['authority']['satisfied'] is True
  assert packet['prerequisites']['evidence']['satisfied'] is (name=='NIP3-113')
  for key in ('status','authority_status','evidence'):packet[key]=o[key]
  allowed=('technical','authority','evidence')
 else:
  assert packet['prerequisites']['technical']['satisfied'] is False and packet['prerequisites']['evidence']['satisfied'] is False
  allowed=('technical','evidence')
 for kind in allowed:
  assert set(packet['prerequisites'][kind])==set(o['prerequisites'][kind])
  packet['prerequisites'][kind]=o['prerequisites'][kind]
 assert packet==o
assert d==original
changes=set(subprocess.check_output(['git','diff','--name-only'],cwd=p,text=True).splitlines())
assert changes==set(S[1:])|{'.agent/run_state.json'}
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip()==B
assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=p,text=True).strip()==''
subprocess.run(['git','diff','--check'],cwd=p,check=True)
print('BASIC SOURCE CHECKPOINT: syntax, exact document/JSON masks, Parent state preservation and Git whitespace; no acceptance claim.')
