"""Frozen read-only scope/preservation inspection, not a product acceptance rerun."""
import ast
import fnmatch
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = 'f270bbbe511dc4ec47ed416bc0cefbae60e2c5cb'
REVIEWED = '12466809d26e5cb3891c2db0f57e4fbf7bbebade'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def blob(revision, path):
    return git('show', revision + ':' + path)


def symbols(data):
    return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(data).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


def main():
    facts = dict(base=BASE, reviewed_revision=REVIEWED, inspection_revision=git('rev-parse', 'HEAD').decode().strip())
    contract = json.loads(blob(REVIEWED, '.agent/contracts/121.json'))
    facts['approved_contract_sha256'] = hashlib.sha256(blob(REVIEWED, '.agent/contracts/121.json')).hexdigest()
    facts['inherited'] = {}
    for path in ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py'):
        old = symbols(blob(BASE, path)); current = symbols(blob(REVIEWED, path))
        exemption = ['main'] if path.endswith('test_workflow_assurance.py') else []
        changed = [name for name, value in old.items() if name not in exemption and current.get(name) != value]
        assert not changed, changed
        facts['inherited'][path] = dict(unchanged_symbols=sorted(set(old)-set(exemption)), dispatch_exemption=exemption, changed=changed)
        imports = lambda data: [ast.dump(n, include_attributes=False) for n in ast.parse(data).body if isinstance(n, (ast.Import, ast.ImportFrom))]
        assert imports(blob(BASE, path)) == imports(blob(REVIEWED, path)), 'new dependency import'
    assignments = lambda data: {n.targets[0].id: ast.dump(n, include_attributes=False) for n in ast.parse(data).body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id.endswith('CASES')}
    previous = assignments(blob(BASE, 'tools/test_workflow_assurance.py')); current = assignments(blob(REVIEWED, 'tools/test_workflow_assurance.py'))
    assert all(current.get(k) == v for k, v in previous.items()), 'old case inventory changed'
    facts['unchanged_case_inventories'] = list(previous)
    protected = [p for p in git('ls-tree', '-r', '--name-only', BASE).decode().splitlines() if p.startswith(('.nizam/', 'schema/', '.github/', '.agent/evidence/119/', '.agent/evidence/120/')) or p in ('.agent/qa/119.json', '.agent/qa/120.json')]
    changed = [p for p in protected if git('ls-tree', BASE, '--', p) != git('ls-tree', REVIEWED, '--', p)]
    assert not changed, changed
    facts['protected'] = dict(unchanged=len(protected), installed_files=sum(p.startswith('.nizam/') for p in protected), changed=changed)
    files = git('diff', '--name-only', BASE + '..' + REVIEWED).decode().splitlines()
    permitted = [r['path'] for r in contract['scope']['files_create'] + contract['scope']['files_modify']] + ['.agent/evidence/120/*', '.agent/qa/120-identity-archive-review.json']
    outside = [p for p in files if not any(fnmatch.fnmatchcase(p, pattern) for pattern in permitted)]
    assert not outside, outside
    facts['scope'] = dict(changed_path_count=len(files), unauthorized_paths=outside, adjacent_authorized_120_additions=[p for p in files if p.startswith('.agent/evidence/120/') or p == '.agent/qa/120-identity-archive-review.json'])
    facts['gate_envelopes'] = {}
    for path in ('.agent/validator/121-mode-a.json', '.agent/qa/121-contract-review.json', '.agent/qa/121-provisional-bundle-review-rev2.json', '.agent/qa/121-executable-bundle-review.json'):
        gate = json.loads(blob(REVIEWED, path))
        strict = gate['final_verdict']['approved'] is True and all(gate[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'))
        assert strict, path
        facts['gate_envelopes'][path] = dict(strict_approved=strict, sha256=hashlib.sha256(blob(REVIEWED, path)).hexdigest())
    stats = {}
    for row in git('diff', '--numstat', '--no-renames', BASE + '..' + REVIEWED, '--', 'tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', 'tools/README.md', 'CHANGELOG.md').decode().splitlines():
        added, deleted, path = row.split('\t'); stats[path] = int(added) + int(deleted)
    facts['product_and_tests_lines'] = stats
    facts['product_total'] = sum(n for p, n in stats.items() if p != 'tools/test_workflow_assurance.py')
    assert facts['product_total'] <= 300 and stats['tools/test_workflow_assurance.py'] <= 450
    state = json.loads(blob(REVIEWED, '.agent/run_state.json'))
    facts['coordination_summary'] = {k: state.get(k) for k in ('current_feature', 'current_phase', 'status', 'active_contract_id')}
    facts['current_counters'] = {k: v for k, v in state['circuit_breaker'].items() if k.startswith('121-')}
    argv = [sys.executable, '.agent/evidence/scope-budget-014/measure.py', '--range', '121=' + BASE + '..' + REVIEWED, '--files']
    result = subprocess.run(argv, cwd=ROOT, capture_output=True)
    for stream in ('stdout', 'stderr'):
        (ROOT / ('.agent/evidence/121/modeb1-budget.' + stream + '.txt')).write_bytes(getattr(result, stream))
    facts['budget_command'] = dict(argv=argv, cwd=str(ROOT), environment={'PYTHONDONTWRITEBYTECODE': '1'}, actual_exit=result.returncode, exercised_revision=facts['inspection_revision'], measured_revision=REVIEWED)
    assert result.returncode == 0, 'measurement failed'
    (ROOT / '.agent/evidence/121/modeb1-static.json').write_text(json.dumps(facts, indent=2) + '\n')
    print(json.dumps(facts, indent=2))
    print(result.stdout.decode())


if __name__ == '__main__':
    main()
