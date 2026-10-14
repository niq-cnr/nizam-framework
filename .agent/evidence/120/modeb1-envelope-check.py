import json,hashlib,subprocess
from pathlib import Path
import jsonschema
show=lambda p:subprocess.check_output(['git','show','67f8c81c51e2deef8c8855fc7a7af90dab49f734:'+p]);proof=json.loads(show('.agent/evidence/120/review-envelope1-proof.json'))
assert len(proof['files'])==4 and proof['validation_count']==8
for row in proof['files']:
 p=row['path'];raw=show(p);old=Path(p).read_bytes();assert old==subprocess.check_output(['git','show',row['original']['revision']+':'+p])
 assert raw.count(b'  "feature": "120",\n')==1 and raw.replace(b'  "feature": "120",\n',b'',1)==old
 for key,data in [('original',old),('new',raw)]:assert hashlib.sha256(data).hexdigest()==row[key]['sha256'] and subprocess.check_output(['git','cat-file','blob',row[key]['git_blob']])==data
 for schema in ('schema/contract_review.schema.json','.nizam/schema/contract_review.schema.json'):jsonschema.validate(json.loads(raw),json.loads(show(schema)))
assert not subprocess.check_output(['git','diff','--name-only','b50320b','67f8c81','--','tools/workflow_assurance.py','tools/test_workflow_assurance.py','tools/README.md','CHANGELOG.md','.agent/contracts/120.json','.agent/evidence/120/executable-review1-seal.json'])
print('PASS immutable67f8c81 supplement: exact4 feature aliases, eight schema checks, original bytes/digests/Git objects preserved; Source/test/contract/docs/seal unchanged. Original230seal pins remain historical references, never rebound.')
