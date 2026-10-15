"""Root once-only scope accounting. Preparation until docs/preparation gates admit it.

Keep frozen classifier output. A separate conservative authored-process overlay
charges maintained source/decisions under evidence paths without changing rules.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASE = '79811ef76df950b8151e2af62637ab7d1df34305'
FROZEN = '.agent/evidence/scope-budget-014/measure.py'
FROZEN_SHA = '3d40a57b5200d7cd00f3fdfbc2cb348b87e9523669d1b9d2682419ca526d9973'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve(strict=True)
    root = Path.cwd().resolve()
    assert root not in out.parents and out != root
    assert sha(Path(FROZEN).read_bytes()) == FROZEN_SHA
    assert not Path('.agent/evidence/123/selection.json').exists()
    head = git('rev-parse', 'HEAD').decode().strip()
    argv = ['python3', FROZEN, '--range', '123='+BASE+'..'+head, '--files']
    result = subprocess.run(argv, capture_output=True)
    (out/'frozen.stdout.txt').write_bytes(result.stdout)
    (out/'frozen.stderr.txt').write_bytes(result.stderr)
    assert result.returncode == 0, result.stderr.decode()
    text = result.stdout.decode()
    def total(key):
        rows = re.findall(r'^\s*'+key+r'=(\d+)', text, re.M)
        assert len(rows) == 1, key
        return int(rows[0])
    assert total('UNCLASSIFIED_LINES') == 0
    raw = git('diff', '--numstat', '--no-renames', '-z', BASE, head)
    (out/'numstat.raw').write_bytes(raw)
    records = []
    for entry in raw.split(b'\0'):
        if not entry:
            continue
        added, deleted, path = entry.decode().split('\t', 2)
        records.append((path, 0 if added == '-' else int(added)+int(deleted)))
    prep = json.loads(Path('.agent/evidence/123/scope-classification-preparation1.json').read_bytes())
    canonical = {p: Path(p).read_bytes() for p in prep['authored_process_overlay']['canonical_source_paths']}
    canonical.update({p.as_posix(): p.read_bytes() for p in Path('.agent/evidence/123').rglob('*.py')})
    mechanical = {'.agent/evidence/123/controls-evidence.json', '.agent/evidence/123/capture-host2.json',
                  '.agent/evidence/123/verify-host1-recovery2.json'}
    rows = []
    for path, lines in records:
        if not path.startswith('.agent/evidence/123/'):
            continue
        p = Path(path)
        if not p.exists():
            continue  # Endpoint no-renames convention; removed selections stay in history.
        raw = p.read_bytes()
        kind, charge = 'raw observed bytes or mechanical derived capture', 0
        if path in canonical or p.suffix in {'.py', '.go'}:
            kind, charge = 'maintained source; distinct attempts counted separately', lines
        elif p.name.startswith('pr-description-') and p.suffix == '.txt':
            kind, charge = 'authored PR description', lines
        elif p.suffix == '.json' and path not in mechanical:
            observed = any(token in p.name for token in ('.execution.', '.started.', '.stdout.', '.stderr.', '.signal.', '.capture-summary.', '.preservation-'))
            try:
                value = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                assert observed, ('unclassified non-JSON authored artifact', path)
                value = None
            observed |= p.name in {'capture-index.json', 'wrapper-launch.json', 'setup-summary.json'}
            observed |= isinstance(value, dict) and 'argv' in value and any(k in value for k in ('actual_exit', 'child_pid'))
            observed |= isinstance(value, dict) and 'files' in value and ('capture' in p.name or 'inventory' in p.name)
            observed |= isinstance(value, dict) and 'physical_before' in value and 'physical_after' in value
            if not observed:
                kind, charge = 'authored decision/report; entire mixed document conservatively charged', lines
        elif '.stdin' in p.name and not raw.startswith(b'PACK'):
            try:
                ast.parse(raw)
            except (SyntaxError, UnicodeDecodeError, ValueError):
                pass
            else:
                duplicates = [name for name, source in canonical.items() if source == raw]
                kind = 'exact retained source copy: '+', '.join(duplicates) if duplicates else 'retained inline authored source'
                charge = 0 if duplicates else lines
        if path == prep['external_cli_provenance']['canonical_authored_delta']['path']:
            assert sha(raw) == prep['external_cli_provenance']['canonical_authored_delta']['sha256']
            kind = 'external CLI authored delta only; unchanged upstream excluded'
            charge = sum(s.startswith(('+', '-')) and not s.startswith(('+++', '---')) for s in raw.decode().splitlines())
        rows.append(dict(path=path, sha256=sha(raw), frozen_evidence_lines=lines,
                         authored_process_overlay=charge, attribution=kind))
    overlay = sum(r['authored_process_overlay'] for r in rows)
    frozen = total('BUDGET_COUNTED_LINES')
    actual = frozen + overlay
    prior = 4303
    last_three = (1397 + 1245 + 939)/3
    report = dict(feature_id='123', measurement_revision=head, range=BASE+'..'+head,
                  frozen_classifier_sha256=FROZEN_SHA, frozen_budget=frozen,
                  frozen_product_lines=total('PRODUCT_LINES'),
                  frozen_process_lines=total('PROCESS_OVERHEAD_LINES'),
                  frozen_evidence_lines=total('EVIDENCE_LINES'),
                  frozen_excluded_lines=total('EXCLUDED_LINES'),
                  authored_process_overlay=overlay, actual_conservative=actual,
                  prior_completed_total=prior, phase_total_conservative=prior+actual,
                  original_phase_estimate=7200, phase_ceiling=9360,
                  ceiling_exceeded=prior+actual > 9360,
                  three_times_prior_average=3*last_three,
                  rolling_threshold_exceeded=actual > 3*last_three,
                  attribution=rows,
                  limitations=['Mixed maintained JSON reports are charged in full as a conservative upper bound, including their quoted facts; frozen categories remain unchanged.',
                               'Exact retained stdin source copies are shown with canonical hashes and charged once; distinct failed/repaired source programs remain counted.',
                               'Terminal-only administrative commands not retained as authored files cannot be assigned an invented line count; this is file-delta accounting, not an exhaustive agent-work or token-cost measurement.',
                               'Measurement is this immutable endpoint once; subsequent factual measurement/CI/merge records are retained separately, never silently folded into a second baseline.'])
    (out/'scope-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'attribution','limitations'}},sort_keys=True))

if __name__ == '__main__':
    main()
