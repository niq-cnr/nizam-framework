import json, hashlib, subprocess
from pathlib import Path
import jsonschema
r=Path.cwd()
rev='757b0c61c1f586307d8fd7adfc5160718ce7a374'
p=subprocess.check_output(['git','show',rev+':.agent/contracts/122.json'])
assert hashlib.sha256(p).hexdigest()=='829aab4a4ba65966c3fa1e01e0bc689f60d2ae718f70192f448c7456e8b0c160'
c=json.loads(p); old=json.loads(subprocess.check_output(['git','show','ca3f3917c1d6caf28748877cb47514d0302a4534:.agent/contracts/122.json']))
print('Contract delta:'); print(subprocess.check_output(['git','diff','ca3f3917c1d6caf28748877cb47514d0302a4534',rev,'--','.agent/contracts/122.json'],text=True))
for k in c['api']:
 if k!='continuity': assert c['api'][k]==old['api'][k]
for path,lo,hi in [('tools/workflow_assurance.py',90,120),('.agent/feature_list_018.json',115,137),('.agent/product_spec_018.md',36,41)]:
 print(path+' lines '+str(lo)+'-'+str(hi)+':')
 print('\n'.join(f'{i+1}: {line}' for i,line in enumerate((r/path).read_text().splitlines()) if lo<=i+1<=hi))
for prefix in ('schema/','.nizam/schema/'):
 for name,path in [('contract','.agent/contracts/122.json'),('contract_review','.agent/qa/122-contract-review-rev1.json')]:
  jsonschema.Draft202012Validator(json.loads((r/(prefix+name+'.schema.json')).read_text())).validate(json.loads((r/path).read_text()))
print('Both contract and review schemas passed; static inspection only, no API/acceptance behavior.')
