import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
from test_governance_skill import GovernanceSkillTests
from jsonschema import Draft202012Validator
schema=json.loads(Path('schema/governance_skill.schema.json').read_text())
version=json.loads(Path('tools/skill.json').read_text())['version']
indexed={c['authoritative_source'] for c in json.loads(Path('NIZAM.json').read_text())['capabilities']}
for name in ['skill_index_neg_dangling_module.json','skill_index_neg_unindexed_capability.json']:
 fixture=json.loads((Path('tools/fixtures')/name).read_text())
 Draft202012Validator(schema).validate(fixture)
 assert fixture['version']==version
 case=GovernanceSkillTests();case.setUp()
 try:
  case.check(fixture,False)
  for capability in fixture['capabilities']:
   if capability['module'] not in indexed:capability['module']='methodology/00_planning.md'
  case.check(fixture,True)
 finally:case.doCleanups()
 print(name,': complete shape/parity valid; targeted bad pointer rejects; repaired pointer passes')
