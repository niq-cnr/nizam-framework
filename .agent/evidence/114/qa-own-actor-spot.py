#!/usr/bin/env python3
"""Fresh Evaluator's single preregistered scratch-only actor-independence spot."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
REVIEW = Path('.agent/evidence/114/source-review.json')
CHECK = [sys.executable, '.agent/evidence/114/check_114.py', 'readiness']

def run(scratch, label, expected, diagnostic=None):
    observed = subprocess.run(CHECK, cwd=scratch, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, env={**os.environ,
                              'PYTHONDONTWRITEBYTECODE': '1'})
    sys.stdout.buffer.write(('SPOT_STAGE: ' + label + '\n').encode())
    sys.stdout.buffer.write(observed.stdout)
    sys.stdout.buffer.write(('OBSERVED_EXIT: %d\n' % observed.returncode).encode())
    sys.stdout.buffer.flush()
    assert observed.returncode == expected, (label, observed.returncode)
    if diagnostic:
        assert ('FAIL feature114 ' + diagnostic).encode() in observed.stdout, observed.stdout

def main():
    original = (ROOT / REVIEW).read_bytes()
    genuine = json.loads(original)
    fixed = json.loads((ROOT / '.agent/evidence/114/fixed-inputs.json').read_bytes())
    assert genuine['actor'] == fixed['actors']['final_qa']
    assert genuine['final_verdict']['approved'] is True
    assert all(genuine[k] == [] for k in ('issues', 'missing_acceptance_coverage',
                                        'unsupported_claims'))
    # All source/fixed/history files stay immutable hardlinks; only the review
    # scratch copy is unlinked before mutation. No real-workspace file is written.
    with tempfile.TemporaryDirectory(prefix='nizam114-qa-own-actor-') as directory:
        scratch = Path(directory) / 'candidate'
        shutil.copytree(ROOT, scratch, copy_function=os.link, symlinks=True)
        run(scratch, 'genuine-independent-review', 0)
        borrowed = scratch / REVIEW
        borrowed.unlink()
        invalid = dict(genuine)
        invalid['actor'] = fixed['actors']['generator']
        borrowed.write_text(json.dumps(invalid, indent=2) + '\n')
        try:
            run(scratch, 'generator-attributed-semantic-review', 1, 'SEMANTIC_REVIEW')
        finally:
            borrowed.write_bytes(original)
        run(scratch, 'restored-independent-review', 0)
    assert (ROOT / REVIEW).read_bytes() == original
    print('OWN SPOT PASS: actual genuine review passed; Generator actor rejected '
          'with SEMANTIC_REVIEW/1; restored fresh Evaluator passed/0; '
          'real review and source/fixed inputs unchanged.')

if __name__ == '__main__':
    main()
