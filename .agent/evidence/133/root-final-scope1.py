"""Root final accounting: unchanged frozen snapshot plus explicit authored views.

Run once after local closure/current-docs review. Outputs stay outside checkout.
Raw observations never become authored cost merely because they are large.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess

BASE = '599d7c5aa0c0c80ce8da596c7aeae2924d7dca04'
FROZEN = '.agent/evidence/scope-budget-014/measure.py'
FROZEN_SHA = '3d40a57b5200d7cd00f3fdfbc2cb348b87e9523669d1b9d2682419ca526d9973'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args])


def records(raw):
    for entry in raw.split(bytes([0])):
        if entry:
            added, deleted, path = entry.decode().split(chr(9), 2)
            yield path, 0 if added == '-' else int(added) + int(deleted)


def owner(path):
    if path.startswith('.agent/evidence/123/'):
        return 'legacy018-administration'
    if not path.startswith('.agent/evidence/') or path.startswith(('.agent/evidence/133/', '.agent/evidence/performance-maintenance/')) or path == '.agent/evidence/133-qa-adversarial.txt':
        return 'maintenance133'
    raise AssertionError(('unclassified ownership', path))


def authored(path, raw):
    p = Path(path)
    if p.suffix in {'.py', '.go', '.sh'}:
        return 'source'
    if '.stdin' in p.name and not raw.startswith(b'PACK'):
        try:
            ast.parse(raw)
        except (SyntaxError, UnicodeDecodeError, ValueError):
            return None
        return 'inline-source'
    if path == '.agent/evidence/performance-maintenance/attribution1/capture-index.sha256':
        return 'maintained-index'
    if path == '.agent/evidence/133-qa-adversarial.txt' or p.name.startswith('pr-description-') or p.suffix == '.md':
        return 'maintained-prose'
    if p.suffix != '.json' or '/raw/' in path:
        return None
    if any(token in p.name for token in ('.execution.', '.started.', '.stdout.', '.stderr.', '.capture-summary.', '.preservation-', 'capture-index')):
        return None
    value = json.loads(raw)
    if isinstance(value, dict) and 'argv' in value and any(k in value for k in ('actual_exit', 'child_pid', 'wrapper_pid')):
        return None
    return 'maintained-mixed-json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output.resolve(strict=True)
    root = Path.cwd().resolve()
    assert out != root and root not in out.parents
    assert sha(Path(FROZEN).read_bytes()) == FROZEN_SHA
    qa = json.loads(Path('.agent/qa/133.json').read_bytes())
    docs = json.loads(Path('.agent/validator/133-closeoutdocs2.json').read_bytes())
    for verdict in (qa, docs):
        assert verdict['final_verdict']['approved'] is True
        assert all(verdict[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'))
    assert json.loads(Path('.agent/evidence/133/evidence-capture.json').read_bytes())['capture_complete'] is True
    head = git('rev-parse', 'HEAD').decode().strip()
    helper = runpy.run_path('.agent/evidence/123/fresh-qa-capture1.py')
    frame = helper['execute'](root, out, 'frozen', ['python3', FROZEN, '--range', '133=' + BASE + '..' + head, '--files'], 600)
    assert frame['actual_exit'] == 0
    text = (out / 'frozen.stdout.txt').read_text()
    def total(key):
        values = re.findall(r'^\s*' + key + r'=(\d+)', text, re.M)
        assert len(values) == 1, key
        return int(values[0])
    assert total('UNCLASSIFIED_LINES') == 0
    classify = runpy.run_path(FROZEN)['classify']
    raw = git('diff', '--numstat', '--no-renames', '-z', BASE, head)
    (out / 'numstat.raw').write_bytes(raw)
    canonical = {sha(Path(p).read_bytes()) for p in git('ls-files', '*.py', '*.go', '*.sh').decode().splitlines() if Path(p).is_file()}
    snapshot = []
    seen_inline = set()
    for path, lines in records(raw):
        if not path.startswith('.agent/evidence/'):
            continue
        data = git('show', head + ':' + path)
        kind = authored(path, data)
        duplicate = kind == 'inline-source' and (sha(data) in canonical or sha(data) in seen_inline)
        if kind == 'inline-source':
            seen_inline.add(sha(data))
        snapshot.append([path, owner(path), lines, 0 if kind is None or duplicate else lines, kind, sha(data)])
    commits = git('rev-list', '--reverse', '--topo-order', '--no-merges', BASE + '..' + head).decode().splitlines()
    churn = []
    seen_inline = set()
    for commit in commits:
        for path, lines in records(git('diff-tree', '--no-commit-id', '--numstat', '--no-renames', '-r', '-z', commit)):
            category = classify(path)
            if category.startswith('budget/'):
                churn.append([commit, path, 'maintenance133', lines, 'budget-authored-change'])
            elif category == 'evidence':
                spec = commit + ':' + path
                found = subprocess.run(['git', 'show', spec], capture_output=True)
                data = found.stdout if found.returncode == 0 else git('show', commit + '^:' + path)
                kind = authored(path, data)
                duplicate = kind == 'inline-source' and (sha(data) in canonical or sha(data) in seen_inline)
                if kind == 'inline-source':
                    seen_inline.add(sha(data))
                if kind is not None:
                    churn.append([commit, path, owner(path), 0 if duplicate else lines, kind])
            else:
                assert category == 'excluded/run_state', (path, category)
    overlay = sum(r[3] for r in snapshot if r[1] == 'maintenance133')
    chronological = sum(r[3] for r in churn if r[2] == 'maintenance133')
    snapshot_total = total('BUDGET_COUNTED_LINES') + overlay
    actual = max(snapshot_total, chronological)
    report = dict(feature_id='133', measurement_revision=head, range=BASE + '..' + head,
                  frozen_classifier_sha256=FROZEN_SHA, frozen_budget=total('BUDGET_COUNTED_LINES'),
                  frozen_product=total('PRODUCT_LINES'), frozen_process=total('PROCESS_OVERHEAD_LINES'),
                  frozen_evidence=total('EVIDENCE_LINES'), frozen_excluded=total('EXCLUDED_LINES'),
                  authored_snapshot_overlay=overlay, snapshot_total=snapshot_total,
                  authored_chronological_total=chronological, actual_conservative=actual,
                  legacy018_post_endpoint_authored_snapshot=sum(r[3] for r in snapshot if r[1] == 'legacy018-administration'),
                  legacy018_post_endpoint_authored_chronological=sum(r[3] for r in churn if r[2] == 'legacy018-administration'),
                  original_estimate=2000, ceiling=2600, budget_gate_passed=actual <= 2600,
                  prior_completed_features=[], first_feature_exception=True,
                  snapshot_columns=['path', 'owner', 'frozen_evidence_lines', 'authored_charge', 'kind', 'sha256'],
                  authored_snapshot=snapshot,
                  chronological_columns=['commit', 'path', 'owner', 'authored_change_lines', 'kind'], authored_chronological=churn,
                  limitations=['Frozen file-delta classifier output is unchanged. Supplemental authored views include maintained mixed reports, source/stdin, failed attempts and carried preparation; raw observations are separate.',
                               'Chronological view sums each non-merge mutation once, including overwritten failed/draft versions. It is an explicit conservative supplement, not added again to the endpoint snapshot. Exact retained inline source copies are charged once by hash.',
                               'Dedicated E123 administration is attributed separately; immutable prior018 totals/failed gate are not remeasured or changed. Future020/comparison branches are absent from this source ancestry.',
                               'Root run_state coordination remains excluded under the unchanged classifier. Terminal-only unretained authoring, tokens, agent time and billed cost are not invented; this is not an exhaustive work-cost measure.',
                               'One immutable final endpoint; subsequent measurement/integration administration is retained separately, not folded into a second baseline.'])
    (out / 'scope-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'authored_snapshot', 'authored_chronological', 'limitations'}}, sort_keys=True))


if __name__ == '__main__':
    main()
