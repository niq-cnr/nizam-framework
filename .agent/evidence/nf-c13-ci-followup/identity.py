#!/usr/bin/env python3
"""Compare C13 scoped source bytes and consumed index fields across candidates."""
import hashlib
import json
import subprocess

old='d4c39fcb6852f7d2bc71940745f0594b8af59c83'
new='46b2aeb691b9692c371b4e6bc51e8dddd125a17e'
paths=['schema/governance_skill.schema.json','tools/test_governance_skill.py','tools/validate.sh',
       'tools/fixtures/skill_index_neg_dangling_module.json',
       'tools/fixtures/skill_index_neg_unindexed_capability.json','tools/fixtures_self_test.sh',
       'schema/README.md','NIZAM.json']
def blob(sha,path): return subprocess.check_output(['git','show',f'{sha}:{path}'])
result={}
for path in paths:
 a,b=blob(old,path),blob(new,path)
 result[path]={'previous_sha256':hashlib.sha256(a).hexdigest(), 'candidate_sha256':hashlib.sha256(b).hexdigest(), 'byte_identical':a==b}
 if path != 'NIZAM.json' and a!=b: raise SystemExit('C13 source identity changed: '+path)
 if path=='NIZAM.json':
  x,y=json.loads(a),json.loads(b)
  old_caps=x['capabilities'];new_caps=y['capabilities']
  if old_caps!=new_caps: raise SystemExit('C13 authoritative-source inputs changed')
  x['framework']['version']=y['framework']['version']
  if x!=y: raise SystemExit('NIZAM changes beyond framework version')
  result[path]['c13_index_projection_identical']=True
  result[path]['framework_version_change']='2.0.0 to 3.0.0'
print(json.dumps({'previous':old,'candidate':new,'inputs':result},sort_keys=True,indent=2))
