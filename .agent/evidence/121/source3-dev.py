"""Generator Source3: unchanged independent probe then one default42; stop on failure."""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import traceback

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / '.agent/evidence/121'
BASE = 'aea85b48ee2628b527ff00f48b5d5b7e225c490f'
OLD = 'f270bbbe511dc4ec47ed416bc0cefbae60e2c5cb'
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, env=ENV).strip()


def write(name, value):
    (E / ('source3-' + name + '.json')).write_text(json.dumps(value, indent=2) + '\n')


def identity():
    result = {}
    for p in git('ls-files').splitlines():
        if p.startswith('.agent/evidence/121/source3-'):
            continue
        q = ROOT / p
        mode = q.lstat().st_mode
        data = os.readlink(q).encode() if stat.S_ISLNK(mode) else q.read_bytes()
        result[p] = dict(sha256=hashlib.sha256(data).hexdigest(), git_blob=git('hash-object', p), mode=stat.S_IMODE(mode))
    return result


def symbols(source):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(source).body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def inventories(source):
    return {t.id: ast.dump(n.value, include_attributes=False) for n in ast.parse(source).body
            if isinstance(n, ast.Assign) for t in n.targets
            if isinstance(t, ast.Name) and t.id.endswith('CASES')}


def main():
    revision = git('rev-parse', 'HEAD')
    report = dict(role='Generator', attempt=3, revision=revision, base=BASE, commands=[])
    before = None
    try:
        dispatch = json.loads((E / 'source3-dispatch.json').read_text())
        assert str(ROOT) == dispatch['root'] and dispatch['attempt'] == 3
        subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, revision], cwd=ROOT, env=ENV, check=True)
        before = identity()
        write('identity-before', before)
        assert before['tools/test_workflow_assurance.py']['sha256'] == dispatch['test_sha256']
        assert before['.agent/contracts/121.json']['sha256'] == dispatch['approved_contract_sha256']
        assert git('diff', 'HEAD', '--', *before) == ''
        assert before['.agent/evidence/121/modeb1-probe.py']['git_blob'] == git('rev-parse', BASE + ':.agent/evidence/121/modeb1-probe.py')
        preserved = {}
        for path, exempt in [('tools/workflow_assurance.py', set()), ('tools/test_workflow_assurance.py', {'main'})]:
            old_text = git('show', OLD + ':' + path)
            current_text = (ROOT / path).read_text()
            old_symbols, current_symbols = symbols(old_text), symbols(current_text)
            inherited = sorted(set(old_symbols) - exempt)
            assert all(current_symbols.get(k) == old_symbols[k] for k in inherited)
            if exempt:
                assert all(inventories(current_text).get(k) == v for k, v in inventories(old_text).items())
            preserved[path] = dict(unchanged_symbols=inherited, exemption=sorted(exempt))
        initial = symbols(git('show', BASE + ':tools/workflow_assurance.py'))
        actual = symbols((ROOT / 'tools/workflow_assurance.py').read_text())
        changed = sorted(k for k in initial if actual.get(k) != initial[k])
        assert changed == ['assess_conflict_lanes', 'rollback_owned_attempt', 'verify_isolated_attempt']
        assert len([p for p in before if p.startswith('.nizam/')]) == 239
        assert git('diff', OLD, 'HEAD', '--', 'schema', '.nizam') == ''
        bank = ast.parse((ROOT / 'tools/test_workflow_assurance.py').read_text())
        cases = {t.id: ast.literal_eval(n.value) for n in bank.body if isinstance(n, ast.Assign)
                 for t in n.targets if isinstance(t, ast.Name) and t.id in ('AGF_CASES', 'RECEIPT_CASES', 'LANE_CASES')}
        expected = [r['case'] for r in json.loads((ROOT / '.agent/evidence/118/api-interface.json').read_text())['current_cases']]
        expected += list(cases['AGF_CASES']) + list(cases['RECEIPT_CASES']) + list(cases['LANE_CASES'])
        assert len(expected) == len(set(expected)) == 42
        report.update(input_identity={p: before[p] for p in ('tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', '.agent/contracts/121.json')}, inherited=preserved, changed_new_api_symbols=changed, installed_count=239)
        write('preservation', report)
        for label, argv in [('probe', ['python3', '.agent/evidence/121/modeb1-probe.py']), ('default42', ['python3', 'tools/test_workflow_assurance.py'])]:
            result = subprocess.run(argv, cwd=ROOT, env=ENV, capture_output=True)
            out, err = E / ('source3-' + label + '.stdout.txt'), E / ('source3-' + label + '.stderr.txt')
            out.write_bytes(result.stdout)
            err.write_bytes(result.stderr)
            record = dict(argv=argv, cwd=str(ROOT), environment={'PYTHONDONTWRITEBYTECODE': '1'}, exercised_revision=revision, actual_exit=result.returncode, stdout=str(out.relative_to(ROOT)), stderr=str(err.relative_to(ROOT)), stdout_sha256=hashlib.sha256(result.stdout).hexdigest(), stderr_sha256=hashlib.sha256(result.stderr).hexdigest())
            report['commands'].append(record)
            write('result', report)
            print(label, 'actual_exit', result.returncode, flush=True)
            assert result.returncode == 0, label + ' failed; stop without retry'
            if label == 'default42':
                markers = [line[5:] for line in result.stdout.decode().splitlines() if line.startswith('PASS ')]
                record['ordered42_match'] = markers == expected
                record['ordered_markers'] = markers
                assert markers == expected
        report['passed'] = True
    except BaseException:
        report['failure'] = traceback.format_exc()
        raise
    finally:
        if before is not None:
            after = identity()
            write('identity-after', after)
            report['protected_unchanged'] = before == after
            report['protected_count'] = len(before)
        write('result', report)
    assert report['protected_unchanged']


if __name__ == '__main__':
    main()
