import hashlib,json,subprocess
from pathlib import Path
import jsonschema,yaml
root=Path.cwd();proposal='385f376fb8360db94242df2c33acdeaf1ab5f2df'
git=lambda *args:subprocess.check_output(['git',*args])
read=lambda rev,path:git('show',rev+':'+path)
old=git('rev-parse',proposal+'^').decode().strip()
paths={'.agent/product_spec_020.md','.agent/feature_list_020.json','docs/planning/phase_020.yaml','docs/planning/manifest.json'}
assert set(git('diff','--name-only',old,proposal).decode().splitlines())==paths
spec=read(proposal,'.agent/product_spec_020.md').decode()
front=json.loads(json.dumps(yaml.safe_load(spec.split('---',2)[1]),default=str))
fl=json.loads(read(proposal,'.agent/feature_list_020.json')); prior=json.loads(read(old,'.agent/feature_list_020.json'))
phase=yaml.safe_load(read(proposal,'docs/planning/phase_020.yaml')); manifest=json.loads(read(proposal,'docs/planning/manifest.json'))
for name,value in [('frontmatter',front),('feature_list',fl),('phase',phase),('manifest',manifest)]:
    jsonschema.Draft202012Validator(json.loads((root/('.nizam/schema/'+name+'.schema.json')).read_bytes())).validate(value)
assert front['version']==fl['spec_version']=='0.2.0' and front['status']=='active'
assert fl['phase_status']==phase['status']=='in_progress'
excluded={'spec_version','phase_status','activation_prerequisites'}
assert {k:v for k,v in fl.items() if k not in excluded}=={k:v for k,v in prior.items() if k not in excluded}
assert fl['activation_prerequisites'][1:]==prior['activation_prerequisites'][1:]
features={f['id']:f for f in fl['features']};order=[]
def visit(key,active):
    assert key in features and key not in active
    if key in order:return
    for dep in features[key]['dependencies']:visit(dep,active|{key})
    order.append(key)
for key in features:visit(key,set())
assert order==['129','130','131','132'] and all(f['status']=='pending' and f['passes'] is False for f in features.values())
assert fl['original_estimate_lines']==7350 and fl['ceiling_130pct']==9555 and fl['budget_categories']=={'product':1850,'tests':1750,'process':3750}
assert phase['steps']==yaml.safe_load(read(old,'docs/planning/phase_020.yaml'))['steps']
old_manifest=json.loads(read(old,'docs/planning/manifest.json'))
assert manifest['current_phase']=='020-sbcl-fresh-acceptance' and len(manifest['phases'])==len(old_manifest['phases'])
for before,after in zip(old_manifest['phases'],manifest['phases']):
    assert before['id']==after['id']
    if before['id']!='020-sbcl-fresh-acceptance':assert before==after
refs=[]
def inspect(value):
    if isinstance(value,dict):
        if {'path','revision','sha256'}<=value.keys():
            assert hashlib.sha256(read(value['revision'],value['path'])).hexdigest()==value['sha256'];refs.append(value)
        for child in value.values():inspect(child)
    elif isinstance(value,list):
        for child in value:inspect(child)
inspect(fl);assert len(refs)==9
contract=(root/'.agent/contracts/129.json').read_bytes();assert hashlib.sha256(contract).hexdigest()=='71c6374a6bd88a1110de3fceb612a1392f0b203736e13843caace9fec52c26e6'
assert json.loads(contract)['status']=='approved'
assert 'This activation delta takes effect only after' in spec and 'New integration waits PR 105 main all five' in spec
assert 'its frozen PR 105 still awaits capable CI,\nnormal merge and main delivery.' in spec
print('STATIC_PASS exactfourfile delta;schemas4;wholefeatureobjects/DAG/lanes/matrix/prerequisites unchanged;immutable refs9;otherphases unchanged;7350/9555 preserved;approved129pin;conditionalgates retained')
print('CURRENT_CONTEXT_FINDING spec020 present-tense frozenPR105 awaitsnormalmerge conflicts with proposal application only after normalmerge; qualify original intake snapshot without rewriting historical refs or claiming future success')
