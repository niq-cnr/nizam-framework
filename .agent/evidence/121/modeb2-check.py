"""Frozen independent repair review and one unchanged original probe invocation."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import jsonschema

ROOT = Path(__file__).resolve().parents[3]
OLD = '12466809d26e5cb3891c2db0f57e4fbf7bbebade'
REVIEW = '09b7237dd9764def149b43a532c5d1e11f9b486d'
BASE = 'f270bbbe511dc4ec47ed416bc0cefbae60e2c5cb'
E = ROOT / '.agent/evidence/121'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    revision = git('rev-parse', 'HEAD').decode().strip()
    data = lambda rev, path: git('show', rev + ':' + path)
    previous = data(OLD, 'tools/workflow_assurance.py')
    needle = b'except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:'
    replacement = needle.replace(b'RecursionError', b'RuntimeError')
    # Exactly the three new API handlers changed; pre121 source is untouched.
    prefix, suffix = previous.split(b'def _lane_path(value):', 1)
    assert suffix.count(needle) == 3
    assert prefix + b'def _lane_path(value):' + suffix.replace(needle, replacement) == data(REVIEW, 'tools/workflow_assurance.py')
    for path in ('tools/test_workflow_assurance.py', 'tools/README.md', 'CHANGELOG.md', '.agent/contracts/121.json', '.agent/evidence/121/modeb1-probe.py'):
        assert data(OLD, path) == data(REVIEW, path), path
    assert issubclass(RecursionError, RuntimeError)
    symbols = lambda raw: {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(raw).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    inherited = symbols(data(BASE, 'tools/workflow_assurance.py')); current = symbols(data(REVIEW, 'tools/workflow_assurance.py'))
    assert all(current[k] == v for k, v in inherited.items())
    gatepath = '.agent/qa/121-executable-bundle-review-rev1.json'
    gate = json.loads(data(REVIEW, gatepath))
    for schema in ('schema/contract_review.schema.json', '.nizam/schema/contract_review.schema.json'):
        jsonschema.Draft202012Validator(json.loads((ROOT / schema).read_text())).validate(gate)
    assert gate['final_verdict']['approved'] is True and all(gate[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'))
    binding = json.loads((E / 'executable-review3-root-binding.json').read_text())
    seal = json.loads((E / 'executable-review3-seal.json').read_text())
    assert binding['passed'] is True and binding['actual_reviewer_captures'] == 27
    assert seal['approved'] is True and seal['actual_wrapper_exit'] == seal['actual_verifier_exit'] == 0
    runtime = json.loads((E / 'controls3-reviewer-result.json').read_text())
    assert runtime['protected_before'] == runtime['protected_after']
    captures = runtime['captures']; assert len(captures) == 27
    for capture in captures:
        assert capture['actual_exit'] == capture['expected_exit'] and capture['protected_unchanged'] is True
        for stream in ('stdout', 'stderr'):
            assert hashlib.sha256((ROOT / capture[stream]).read_bytes()).hexdigest() == capture[stream + '_sha256']
    for name, path in [('source', 'tools/workflow_assurance.py'), ('tests', 'tools/test_workflow_assurance.py'), ('contract', '.agent/contracts/121.json')]:
        assert hashlib.sha256(data(REVIEW, path)).hexdigest() == seal['inputs'][name]['sha256']
    protected = git('diff', '--name-only', OLD + '..' + REVIEW, '--', '.nizam', 'schema', '.github').decode()
    assert not protected
    facts = dict(reviewed_revision=REVIEW, exercised_revision=revision, exact_three_new_api_handler_replacements=True, recursion_subclass_still_caught=True, inherited_source_symbols_unchanged=len(inherited), frozen_test_docs_contract_probe_unchanged=True, protected_schema_installed_workflows_unchanged=True, strict_new_executable_gate=True, independently_checked_raw_captures=len(captures), root_binding=binding, procedural_recoveries_preserved=True)
    argv = [sys.executable, '.agent/evidence/121/modeb1-probe.py']
    result = subprocess.run(argv, cwd=ROOT, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True)
    for stream in ('stdout', 'stderr'):
        (E / ('modeb2-probe.' + stream + '.txt')).write_bytes(getattr(result, stream))
    facts['probe'] = dict(argv=argv, cwd=str(ROOT), environment={'PYTHONDONTWRITEBYTECODE': '1'}, actual_exit=result.returncode, exercised_revision=revision)
    (E / 'modeb2-review.json').write_text(json.dumps(facts, indent=2) + '\n')
    assert result.returncode == 0, 'actual unchanged original probe failed; STOP'
    argv = [sys.executable, '.agent/evidence/scope-budget-014/measure.py', '--range', '121=' + BASE + '..' + REVIEW, '--files']
    measured = subprocess.run(argv, cwd=ROOT, capture_output=True)
    for stream in ('stdout', 'stderr'):
        (E / ('modeb2-budget.' + stream + '.txt')).write_bytes(getattr(measured, stream))
    facts['budget'] = dict(argv=argv, cwd=str(ROOT), environment={'PYTHONDONTWRITEBYTECODE': '1'}, actual_exit=measured.returncode, exercised_revision=revision, measured_revision=REVIEW)
    (E / 'modeb2-review.json').write_text(json.dumps(facts, indent=2) + '\n')
    assert measured.returncode == 0, 'actual scope measurement failed; STOP'
    print(json.dumps(facts, indent=2)); print(result.stdout.decode()); print(measured.stdout.decode())


if __name__ == '__main__':
    main()
