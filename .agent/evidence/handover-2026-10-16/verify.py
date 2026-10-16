"""Read-only handover checks and existing capture-driver orchestration."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import runpy
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def metadata():
    import jsonschema
    import yaml

    state = json.loads((ROOT / '.agent/run_state.json').read_text())
    assert state['current_phase'] == '020-sbcl-fresh-acceptance'
    assert state['current_feature'] == '129' and state['status'] == 'in_progress'
    quote = state['handover']['dogfooding_authorization_verbatim']
    assert quote in (ROOT / 'docs/planning/HANDOVER-2026-10-16.md').read_text()
    assert quote in (ROOT / 'docs/planning/HANDOVER.md').read_text()
    schema = json.loads((ROOT / '.nizam/schema/frontmatter.schema.json').read_text())
    for name in ['HANDOVER.md', 'HANDOVER-2026-10-16.md', 'ROADMAP.md']:
        raw = (ROOT / 'docs/planning' / name).read_text()
        assert raw.startswith('---\n')
        front = yaml.safe_load(raw[4:].split('\n---\n', 1)[0])
        jsonschema.validate(front, schema)
    expected = {
        'tools/runtime_session.py': 'fe5917389ee3bdec342bd440d7ce48adf7d7e933cb4cf3f4dc1d1bbb1cecb345',
        'tools/test_runtime_session.py': 'd186e915424040b32ee9c232d952a170ec0a806cf415126abf34a8a81eda0431',
        '.agent/contracts/129.json': '71c6374a6bd88a1110de3fceb612a1392f0b203736e13843caace9fec52c26e6',
    }
    for name, digest in expected.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    assert not (ROOT / 'tools/sbcl_session_loop.lisp').exists()
    verdict = json.loads((ROOT / '.agent/validator/129-mode-b.json').read_text())
    assert verdict['final_verdict']['approved'] is False
    assert [row['id'] for row in verdict['issues']] == ['129-B1', '129-B2']
    held = ROOT / '.agent/evidence/phase020-candidate-accounting-preparation1'
    for name, digest in json.loads((held / 'index.json').read_text()).items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    frame = json.loads((held / 'static2.execution.json').read_text())
    assert frame['actual_exit'] == 0 and frame['child_pid'] == 193015
    observed = json.loads((ROOT / '.agent/evidence/129/source3-environment-diagnosis1/static3.stdout.txt').read_text())
    installed = {}
    for path in sorted((ROOT / '.nizam').rglob('*')):
        if path.is_file():
            assert not path.is_symlink()
            installed[path.relative_to(ROOT).as_posix()] = {
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'bytes': path.stat().st_size,
                'mode': stat.S_IMODE(path.stat().st_mode),
            }
    assert len(installed) == 239 and installed == observed['installed_before']
    retained = json.loads((ROOT / '.agent/evidence/handover-2026-10-16/revisions.json').read_text())
    for ref, revision in retained['refs'].items():
        actual = subprocess.check_output(['git', 'rev-parse', ref], cwd=ROOT, text=True).strip()
        assert actual == revision, ref
    assert state['scope_budget']['measurement_status'].startswith('Allocated but unmeasured.')
    print(json.dumps({'result': 'PASS', 'scope': 'handover authority, held accounting bytes, rejected-candidate boundary, retained refs and immutable installed payload', 'installed_files': len(installed), 'numeric_cost_measured': False, 'diagnostic_executed': False, 'Source4_implemented': False}, sort_keys=True))


if __name__ == '__main__':
    if sys.argv[1:] == ['--metadata']:
        metadata()
    else:
        output = Path(sys.argv[1]).resolve(strict=True)
        assert output != ROOT and ROOT not in output.parents
        capture = runpy.run_path(str(ROOT / '.agent/evidence/123/fresh-qa-capture1.py'))['execute']
        jobs = [('metadata', [sys.executable, str(Path(__file__).resolve()), '--metadata']),
                ('repository', ['bash', 'tools/validate.sh']),
                ('payload', ['bash', 'tools/validate.sh', '--payload'])]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(capture, ROOT, output, name, argv, 180) for name, argv in jobs]
            results = [future.result() for future in futures]
        for name, result in zip((job[0] for job in jobs), results):
            print(json.dumps({'name': name, 'actual_exit': result['actual_exit'], 'child_pid': result['child_pid'], 'exercised_revision': result['exercised_revision']}))
        sys.exit(0 if all(result['actual_exit'] == 0 for result in results) else 1)
