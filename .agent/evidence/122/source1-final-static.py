"""Static final scope and prior verdict preservation; no behavior rerun."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

base = '59375cf49fad8b6caaec8dd3911f2cc1f685dcf3'
def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True).stdout
verdict_paths = git('ls-tree', '-r', '--name-only', base, '--', '.agent/qa', '.agent/validator').decode().splitlines()
for path in verdict_paths:
    assert Path(path).read_bytes() == git('show', base + ':' + path), path
    row = git('ls-tree', base, '--', path).decode().split()[0]
    assert bool(Path(path).stat().st_mode & 0o111) == (row == '100755'), path
changes = git('diff', '--name-only', base).decode().splitlines()
assert set(changes) <= {'tools/workflow_assurance.py', 'tools/README.md', 'methodology/03_circuit_breaker.md', 'CHANGELOG.md'} | set(p for p in changes if p.startswith('.agent/evidence/122/source1-'))
result_path = Path('.agent/evidence/122/source1-default-result.json')
result = json.loads(result_path.read_text())
assert result['actual_exit'] == 0 and result['preserved'] and result['order_exact'] and len(result['ordered_passes']) == 46
assert result['installed_count'] == 239
# Preserve the original capture, and correct only a metadata label, without rerunning behavior.
Path('.agent/evidence/122/source1-default-result-original.json').write_bytes(result_path.read_bytes())
result['test_git_blob'] = result['environment'].pop('python')
result['metadata_correction'] = 'Observed test hash-object value moved from mislabeled environment.python to test_git_blob; original capture retained, behavior not rerun.'
result_path.write_text(json.dumps(result, indent=2) + '\n')
check = subprocess.run(['git', 'diff', '--check'], capture_output=True)
Path('.agent/evidence/122/source1-diff-check.stdout.txt').write_bytes(check.stdout)
Path('.agent/evidence/122/source1-diff-check.stderr.txt').write_bytes(check.stderr)
assert check.returncode == 0
print(json.dumps({'static_checks': 'passed', 'prior_qa_validator_files_unchanged': len(verdict_paths), 'installed_unchanged': result['installed_count'], 'source_sha256': hashlib.sha256(Path('tools/workflow_assurance.py').read_bytes()).hexdigest(), 'python_executable': sys.executable, 'python_version': sys.version, 'behavior_rerun': False, 'diff_check_actual_exit': check.returncode}, indent=2))
