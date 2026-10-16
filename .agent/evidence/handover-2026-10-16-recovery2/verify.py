"""Read-only stopped handover checks; uses the existing capture driver."""
import concurrent.futures
import gzip
import hashlib
import json
from pathlib import Path
import runpy
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def metadata():
    import jsonschema
    import yaml
    load = lambda name: json.loads((ROOT / name).read_bytes())
    state = load('.agent/run_state.json')
    assert state['current_phase'] == '020-sbcl-fresh-acceptance'
    assert state['current_feature'] == state['active_contract_id'] == '129'
    assert state['status'] == 'in_progress'
    assert state['circuit_breaker']['129-source']['attempts'] == 4
    assert state['circuit_breaker']['129-source']['status'].startswith('Source4-held')
    for key in ['dogfooding_authorization_verbatim', 'delivery_bar_verbatim']:
        quote = state['handover'][key]
        for name in ['HANDOVER.md', 'HANDOVER-2026-10-16.md']:
            assert quote in (ROOT / 'docs/planning' / name).read_text()
    assert 'prepare the project for handover' in state['handover']['goal']
    schema = load('.nizam/schema/frontmatter.schema.json')
    for name in ['HANDOVER.md', 'HANDOVER-2026-10-16.md', 'ROADMAP.md']:
        raw = (ROOT / 'docs/planning' / name).read_text()
        jsonschema.validate(yaml.safe_load(raw[4:].split('\n---\n', 1)[0]), schema)
    pins = {
        'tools/runtime_session.py': 'fe5917389ee3bdec342bd440d7ce48adf7d7e933cb4cf3f4dc1d1bbb1cecb345',
        'tools/test_runtime_session.py': 'd186e915424040b32ee9c232d952a170ec0a806cf415126abf34a8a81eda0431',
        '.agent/contracts/129.json': '71c6374a6bd88a1110de3fceb612a1392f0b203736e13843caace9fec52c26e6',
        '.agent/evidence/129/replacement-architecture2/report.json': '57fe0fc935827ce5c13a06f020ab5bd2e5ad9cf32225be53dc50d7d4e04e0b62',
        '.agent/evidence/phase020-closed-candidate-inventory1/assemble.py': '74b4b52133386747f3373279d65d3cfb2555cba6b1c3a57a8edab905a09d4742',
    }
    for name, digest in pins.items():
        assert SHA((ROOT / name).read_bytes()) == digest, name
    assert not (ROOT / 'tools/sbcl_session_loop.lisp').exists()
    assert load('.agent/contracts/129.json')['status'] == 'approved'
    assert load('.agent/validator/129-mode-b.json')['final_verdict']['approved'] is False
    review = load('.agent/validator/020-candidate-accounting-closure2.json')
    assert review['final_verdict']['approved'] is True
    assert all(review[key] == [] for key in ['issues', 'missing_acceptance_coverage', 'unsupported_claims'])
    for index in ['.agent/evidence/129/implementation4/qualification-index1.json',
                  '.agent/evidence/129/replacement-architecture2/index.json']:
        for row in load(index)['files']:
            raw = (ROOT / row['path']).read_bytes()
            assert SHA(raw) == row['sha256'] and len(raw) == row['bytes']
    prefix = '.agent/evidence/phase020-closed-candidate-inventory1/'
    for name, digest in load(prefix + 'index.json')['files'].items():
        assert SHA((ROOT / prefix / name).read_bytes()) == digest
    frame = load(prefix + 'static1.execution.json')
    assert frame['actual_exit'] == 0 and frame['child_pid'] == 427002
    for stream in ['stdin', 'stdout', 'stderr']:
        row = frame[stream]
        raw = (ROOT / prefix / Path(row['path']).name).read_bytes()
        assert SHA(raw) == row['sha256'] and len(raw) == row['bytes']
    assert not (ROOT / prefix / 'inventory.json.gz').exists()
    report = load('.agent/evidence/129/replacement-architecture2/report.json')
    assert 'provisional and unreviewed' in report['status']
    for probe, pid in [('leases', 420629), ('seals', 420627)]:
        prefix = '.agent/evidence/129/replacement-architecture2/' + probe + '/'
        frame = load(prefix + probe + '.execution.json')
        assert frame['actual_exit'] == 0 and frame['child_pid'] == pid and not frame['timed_out']
        for stream in ['stdout', 'stderr']:
            row = frame[stream]
            raw = (ROOT / prefix / Path(row['path']).name).read_bytes()
            assert SHA(raw) == row['sha256'] and len(raw) == row['bytes']
        before = (ROOT / prefix / (probe + '.preservation-before.json.gz')).read_bytes()
        after = (ROOT / prefix / (probe + '.preservation-after.json.gz')).read_bytes()
        assert before == after
        inventory = json.loads(gzip.decompress(before))
        assert len(inventory['rows']) == 16842
        assert sum(row['path'].startswith('.nizam/') for row in inventory['rows']) == 239
    expected = load('.agent/evidence/129/source3-environment-diagnosis1/static3.stdout.txt')['installed_before']
    installed = {p.relative_to(ROOT).as_posix(): {'sha256': SHA(p.read_bytes()), 'bytes': p.stat().st_size, 'mode': stat.S_IMODE(p.stat().st_mode)}
                 for p in sorted((ROOT / '.nizam').rglob('*')) if p.is_file()}
    assert installed == expected and len(installed) == 239
    for ref, revision in load('.agent/evidence/handover-2026-10-16-recovery2/revisions.json')['refs'].items():
        assert subprocess.check_output(['git', 'rev-parse', ref], cwd=ROOT, text=True).strip() == revision
    assert state['scope_budget']['measurement_status'].startswith('Allocated but unmeasured.')
    print('PASS: handover authority/bar, stopped recovery refs, rejected baseline, provisional alternatives, unexecuted accounting and immutable239 installed files. No product/QA/budget/comparison approval.')


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
            results = list(pool.map(lambda job: capture(ROOT, output, job[0], job[1], 180), jobs))
        for (name, _), result in zip(jobs, results):
            print(json.dumps({'name': name, 'actual_exit': result['actual_exit'], 'child_pid': result['child_pid'], 'exercised_revision': result['exercised_revision']}))
        sys.exit(0 if all(result['actual_exit'] == 0 for result in results) else 1)
