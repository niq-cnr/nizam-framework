"""Capture final whole-feature budget including the committed Mode B verdict."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import jsonschema
ROOT = Path(__file__).resolve().parents[3]
E = ROOT / '.agent/evidence/122'
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
argv = [sys.executable, '.agent/evidence/scope-budget-014/measure.py', '--range', '122=3ee2b39b75fa5e2bc645e52c7b02f185d5d84e03..' + revision, '--files']
p = subprocess.run(argv, cwd=ROOT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), capture_output=True)
prefix = 'modeb2-verdict-scope'
(E / (prefix + '.stdout')).write_bytes(p.stdout); (E / (prefix + '.stderr')).write_bytes(p.stderr)
result = dict(argv=argv, cwd=str(ROOT), PYTHONDONTWRITEBYTECODE='1', actual_exit=p.returncode, exercised_revision=revision, stdout='.agent/evidence/122/' + prefix + '.stdout', stderr='.agent/evidence/122/' + prefix + '.stderr', stdout_sha256=hashlib.sha256(p.stdout).hexdigest(), stderr_sha256=hashlib.sha256(p.stderr).hexdigest())
(E / (prefix + '.execution.json')).write_text(json.dumps(result, indent=2) + '\n')
if p.returncode: raise SystemExit(p.returncode)
verdict_path = ROOT / '.agent/validator/122-mode-b.json'; verdict = json.loads(verdict_path.read_bytes())
for schema in ('schema/contract_review.schema.json', '.nizam/schema/contract_review.schema.json'):
    jsonschema.Draft202012Validator(json.loads((ROOT / schema).read_bytes())).validate(verdict)
assert len(verdict_path.read_text().splitlines()) <= 30
assert verdict['final_verdict']['approved'] is True and all(verdict[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'))
count = int(re.search(rb'BUDGET_COUNTED_LINES=(\d+)', p.stdout)[1])
assert count == 720 + len(verdict_path.read_text().splitlines()) and count <= 950 and 3364 + count <= 9360
assert b'UNCLASSIFIED_LINES=0' in p.stdout and b'evidence                       42    1108' in p.stdout
print(json.dumps(dict(actual_measure_exit=p.returncode, schema_valid_root_and_installed=True, verdict_lines=len(verdict_path.read_text().splitlines()), whole122=count, phase_total=3364+count, phase_ceiling=9360, api_calls=0)))
