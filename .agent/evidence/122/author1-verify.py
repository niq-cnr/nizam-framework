"""Fixture/schema and immutable inherited AST checks only; never exercise122 behavior."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
BASE = 'd9dd92db6ae7b4b6aaa5fc7c99060e6bfbb2752a'
path = ROOT / 'tools/test_workflow_assurance.py'
old = ast.parse(subprocess.check_output(['git', '-C', str(ROOT), 'show', BASE + ':tools/test_workflow_assurance.py']))
new = ast.parse(path.read_bytes())
index = {n.name: n for n in new.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
for node in old.body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name != 'main':
        assert ast.dump(node, include_attributes=False) == ast.dump(index[node.name], include_attributes=False), node.name
    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
        assert any(ast.dump(node, include_attributes=False) == ast.dump(n, include_attributes=False) for n in new.body), 'inherited inventory'
spec = importlib.util.spec_from_file_location('independent_author_bank', path)
bank = importlib.util.module_from_spec(spec); spec.loader.exec_module(bank)
assert len(bank.CASES + bank.AGF_CASES + bank.RECEIPT_CASES + bank.LANE_CASES) == 42
assert len(bank.CASES + bank.AGF_CASES + bank.RECEIPT_CASES + bank.LANE_CASES + bank.FAILURE_CASES) == 46
api = bank.load_api(); assert not hasattr(api, 'route_failed_attempt'), 'unexpected Source availability'
os.environ['NIZAM_WA120_FIXTURE'] = 'observed'
for cause in ('infrastructure', 'semantic'):
    for attempt in (1, 2, 3):
        with tempfile.TemporaryDirectory(prefix='nizam122-author-setup-') as parent:
            f = bank.FailureFixture(api, parent, cause, attempt, [{'operation_id':'other-a'}, {'operation_id':'other-b'}] if attempt == 2 else None)
            for name, value in (('run_state', f.state), ('contract', json.loads((f.root/'contract.json').read_bytes()))):
                jsonschema.Draft202012Validator(json.loads((ROOT/'schema'/(name+'.schema.json')).read_bytes())).validate(value)
            assert f.capture['exit_code'] == 7 and f.capture['executed'] is True
            assert f.capture['candidate_sha256'] == bank.sha(bank.canonical(f.candidate))
            for reference in (f.anchor, f.policy['coordination_ref'], f.policy['authority_ref'], f.authority['contract_ref'], f.authority['capture_ref'], f.authority['evidence_ref'], f.capture['stdout'], f.capture['stderr']):
                raw = subprocess.check_output(['git','-C',str(f.root),'show',reference['revision']+':'+reference['path']])
                assert bank.sha(raw) == reference['sha256']
                assert (f.root/reference['path']).read_bytes() == raw
                assert subprocess.check_output(['git','-C',str(f.root),'ls-tree',reference['revision'],'--',reference['path']]).startswith(b'100644 blob ')
            if cause == 'semantic':
                raw = (f.root/f.evidence['verdict_ref']['path']).read_bytes()
                jsonschema.Draft202012Validator(json.loads((ROOT/'schema/contract_review.schema.json').read_bytes())).validate(json.loads(raw))
            for name in ('122-mode-a', '122-review'):
                jsonschema.Draft202012Validator(json.loads((ROOT/'schema/contract_review.schema.json').read_bytes())).validate(json.loads((f.root/'proof'/(name+'.json')).read_bytes())) if name == '122-review' else None
            print('FIXTURE_SETUP_OK', cause, attempt, 'actual_outer_exit=7', 'candidate='+f.candidate['source_commit'])
print('AUTHOR_STATIC_OK inherited42 preserved; default46; Source behavior unexecuted')
