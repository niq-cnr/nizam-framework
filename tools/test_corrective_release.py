#!/usr/bin/env python3
"""Offline exact-commit core installation/rollback rehearsal; never publishes tags."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODULES = ('standard', 'methodology', 'templates', 'schema', 'tools', 'ecosystem')


def run(argv, cwd):
    result = subprocess.run(argv, cwd=cwd, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                            'GIT_TERMINAL_PROMPT': '0', 'GIT_CONFIG_GLOBAL': '/dev/null'},
                            text=True, capture_output=True)
    print(json.dumps({'argv': argv, 'exit_code': result.returncode}))
    print(result.stdout, end='')
    print(result.stderr, end='')
    if result.returncode:
        raise RuntimeError('rehearsal command failed')
    return result.stdout.strip()


def inventory(payload):
    paths = [payload / 'NIZAM.json']
    for module in MODULES:
        paths.extend(p for p in (payload / module).rglob('*') if p.is_file())
    entries = [{'path': p.relative_to(payload).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                'executable': bool(p.stat().st_mode & 0o111)} for p in sorted(paths)]
    digest = hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'files': len(entries), 'inventory_sha256': digest,
            'canonicalization': 'sorted paths; JSON sort_keys=true separators=comma:colon; path,sha256,executable; excludes provenance'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--prior', required=True)
    parser.add_argument('--prior-sha', required=True)
    args = parser.parse_args()
    sha = run(['git', 'rev-parse', '--verify', args.candidate + '^{commit}'], ROOT)
    prior = run(['git', 'rev-parse', '--verify', args.prior + '^{commit}'], ROOT)
    if prior != args.prior_sha:
        raise RuntimeError('prior release identity mismatch')
    with tempfile.TemporaryDirectory(prefix='nizam-core-rehearsal-') as tmp:
        area = Path(tmp)
        source = area / 'source'
        consumer = area / 'consumer'
        consumer.mkdir()
        run(['git', 'clone', '--quiet', '--no-hardlinks', '--no-checkout', str(ROOT), str(source)], area)
        run(['git', 'checkout', '--quiet', '--detach', sha], source)
        # Only this disposable repository receives a fixture tag. No remote write.
        fixture_tag = 'e2e-nf-corrective-candidate'
        run(['git', 'tag', fixture_tag, sha], source)
        bootstrap = str(source / 'bootstrap.sh')
        ref = str(consumer / '.nizam-ref')
        common = ['--repo-url', str(source), '--git-repo', ref]
        run(['bash', bootstrap, '--tag', fixture_tag, '--allow-fixture-tag', '--expected-sha', sha, *common], consumer)
        run(['bash', bootstrap, '--verify-only', '--tag', fixture_tag, '--allow-fixture-tag', '--expected-sha', sha,
             '--git-repo', ref, '--require-content-integrity'], consumer)
        # The payload is the only working directory. No documentation package is installed or fetched.
        run(['bash', 'tools/validate.sh', '--payload'], consumer / '.nizam')
        candidate_inventory = inventory(consumer / '.nizam')
        # Roll back using the supported immutable bootstrap route, not payload edits.
        run(['bash', bootstrap, '--tag', args.prior, '--expected-sha', prior, *common], consumer)
        run(['bash', bootstrap, '--verify-only', '--tag', args.prior, '--expected-sha', prior,
             '--git-repo', ref, '--require-content-integrity'], consumer)
        run(['bash', 'tools/validate.sh', '--payload'], consumer / '.nizam')
        prior_inventory = inventory(consumer / '.nizam')
        print(json.dumps({'candidate_sha': sha, 'candidate_payload': candidate_inventory,
                          'prior_sha': prior, 'prior_payload': prior_inventory,
                          'core_install': 'passed', 'rollback': 'passed', 'documentation_packages': 'absent',
                          'documentation_origin': 'not_configured_or_contacted',
                          'release_publication': 'not_performed', 'commissioning': 'not_performed'}, sort_keys=True))


if __name__ == '__main__':
    main()
