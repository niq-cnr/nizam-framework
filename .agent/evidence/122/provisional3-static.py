"""Narrow frozen regression review only; never calls the routing API."""
import ast, hashlib, json, subprocess
from pathlib import Path
from types import SimpleNamespace
import jsonschema
root=Path.cwd(); E=root/'.agent/evidence/122'
git=lambda *a:subprocess.check_output(['git',*a])
freeze=json.loads((E/'author3-freeze.json').read_bytes())
for ref in freeze['refs']:
    raw=git('show',ref['revision']+':'+ref['path'])
    assert hashlib.sha256(raw).hexdigest()==ref['sha256'] and (root/ref['path']).read_bytes()==raw
    assert git('ls-tree',ref['revision'],'--',ref['path']).decode().split()[:3]==[ref['git_mode'],'blob',ref['git_blob']]
diff=git('diff','a774da9c9ce16039ea4605cb22e538ee96237abd','b04b165584e3a2253b2d9010a2326a8c6e03165a','--','tools/test_workflow_assurance.py'); (E/'provisional3-test-diff.txt').write_bytes(diff)
assert git('diff','--numstat','a774da9c9ce16039ea4605cb22e538ee96237abd','b04b165584e3a2253b2d9010a2326a8c6e03165a','--','tools/test_workflow_assurance.py').decode().strip()=='26\t0\ttools/test_workflow_assurance.py'
assert not git('diff','--name-only','412b7e027b93386b7a1017a07cadad8392e8d217','HEAD','--','tools/workflow_assurance.py','.agent/contracts/122.json','.agent/evidence/122/compatibility1-*')
tree=ast.parse((root/'tools/test_workflow_assurance.py').read_bytes()); node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='failure_legacy_verdicts')
ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'<frozen-legacy-fixture>','exec'),ns)
rows=ns['failure_legacy_verdicts'](SimpleNamespace(capture={'argv':['synthetic'],'stdout':{'path':'proof/failed.stdout'}}))
schema=json.loads((root/'schema/qa_verdict.schema.json').read_bytes())
for label,verdict,deny in rows:
    jsonschema.Draft202012Validator(schema).validate(verdict);jsonschema.Draft202012Validator(schema['anyOf'][0]).validate(verdict)
assert len(rows)==24 and sum(not r[2] for r in rows)==4
for label,expected in (('static',0),('semantic-regression',1)):
    p=json.loads((E/('author3-'+label+'.execution.json')).read_bytes())
    assert p['actual_exit']==expected and p['exercised_revision']==freeze['frozen_revision'] and p['protected_before']==p['protected_after']
assert 'SEMANTIC_SCHEMA_CONTEXT legacy-final-false: failure routing invalid: failure semantic verdict shape' in (E/'author3-semantic-regression.stderr').read_text()
review=json.loads((root/'.agent/qa/122-provisional-bundle-review-rev2.json').read_bytes())
for path in ('schema/qa_verdict.schema.json','.nizam/schema/qa_verdict.schema.json'):jsonschema.Draft202012Validator(json.loads((root/path).read_bytes())).validate(review)
print('STATIC_OK 12 frozen refs; additive26 lines; legacy24 schema-valid rows=4 positives+20 malformed/passing negatives; Source/contract/compatibility proof preserved at412b7e')
print('AUTHOR_PROOF static0; actualsemantic1 at legacy-final-false with protectedbefore==after; no API/selector rerun; provisional acceptance-bundle approval only')
