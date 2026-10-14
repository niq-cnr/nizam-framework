import json, yaml, jsonschema
from pathlib import Path
checks=[('.agent/run_state.json','run_state'),('.agent/feature_list_017.json','feature_list'),('.agent/contracts/116.json','contract'),('.agent/qa/116.json','qa_verdict'),('.agent/validator/116-mode-b.json','contract_review')]
for record,schema in checks:
    jsonschema.Draft202012Validator(json.loads(Path('.nizam/schema/'+schema+'.schema.json').read_text())).validate(json.loads(Path(record).read_text()))
    print('PASS installed schema',record)
jsonschema.Draft202012Validator(json.loads(Path('.nizam/schema/phase.schema.json').read_text())).validate(yaml.safe_load(Path('docs/planning/phase_017.yaml').read_text()))
print('PASS installed canonical phase schema')
