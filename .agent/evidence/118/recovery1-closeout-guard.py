"""Disclosed closeout-only adapter; frozen B2 acceptance and product stay unchanged."""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PIN = 'df63760287c5bae6f43f988d66976ce334e3185d95db4e54143b39a663ddf0b0'
PATH = '.agent/evidence/118/scope-guard.py'
B2 = '07d5a780b16de3d44c5aac263f41404c0b9049d2'
DEBT = 'docs/planning/DEBT.md'
for part in (ROOT / PATH, *(ROOT / PATH).parents):
    if part == ROOT:
        break
    assert not part.is_symlink(), 'pinned guard symlink'
assert hashlib.sha256((ROOT / PATH).read_bytes()).hexdigest() == PIN, 'exact B2 guard pin'
assert not (ROOT / PATH).stat().st_mode & 0o111, 'B2 guard executable mode'
git_blob = subprocess.check_output(['git', '-C', str(ROOT), 'show', B2 + ':' + PATH])
assert hashlib.sha256(git_blob).hexdigest() == PIN and git_blob == (ROOT / PATH).read_bytes(), 'actual B2 blob/current identity'
assert subprocess.check_output(['git', '-C', str(ROOT), 'ls-tree', B2, '--', PATH], text=True).split()[:2] == ['100644', 'blob'], 'actual B2 Git mode'
spec = importlib.util.spec_from_file_location('frozen_B2_closeout', ROOT / PATH)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
ORIGINAL_DEBT = g.debt


def debt(complete):
    """Same approved debt policy, corrected actual five-column table parser."""
    before = g.at(DEBT, g.COORD).decode()
    now = g.safe(DEBT).read_text()
    if not complete:
        g.require(now == before, 'debt054 only after capture')
        return
    a, b = before.split('---', 2), now.split('---', 2)
    om, nm = g.yaml.safe_load(a[1]), g.yaml.safe_load(b[1])
    g.require(nm['version'] == '0.75.0' and len(nm['change_log']) == len(om['change_log']) + 1 and nm['change_log'][0]['version'] == '0.75.0', 'debt sole new version/log')
    g.same(nm['change_log'][1:], om['change_log'], 'all old debt logs')
    g.same(g.strip(nm, {'version', 'change_log'}), g.strip(om, {'version', 'change_log'}), 'debt metadata')
    old = [x for x in a[2].splitlines() if x.startswith('| NDEBT-054 |')]
    new = [x for x in b[2].splitlines() if x.startswith('| NDEBT-054 |')]
    g.require(len(old) == len(new) == 1, 'one054 debt row')
    old_cells, new_cells = old[0].split('|'), new[0].split('|')
    for cells in (old_cells, new_cells):
        g.require(len(cells) == 7 and cells[0] == cells[-1] == '', 'exact five debt columns')
    g.same(old_cells[:5], new_cells[:5], '054 identity/date/severity/description')
    notes = new_cells[5]
    g.require('RESOLVED' in notes.upper() and g.CAPTURE in notes and g.QA in notes and g.E + 'recovery-authorization.json' in notes, '054 actual resolution refs in Notes')
    g.require(new[0] in b[2].split('## Resolved', 1)[1] and new[0] not in b[2].split('## Resolved', 1)[0], '054 moved to Resolved')
    g.require(a[2].replace(old[0] + '\n', '') == b[2].replace(new[0] + '\n', ''), 'all unrelated debt body exact')


def fixture():
    """Use immutable real COORD row even when the caller is already complete."""
    before = g.at(DEBT, g.COORD).decode()
    a = before.split('---', 2)
    meta = g.yaml.safe_load(a[1])
    meta['version'] = '0.75.0'
    meta['change_log'].insert(0, dict(version='0.75.0', date='2026-10-14', summary='PRIVATE debt parser fixture'))
    old = next(x for x in a[2].splitlines() if x.startswith('| NDEBT-054 |'))
    cells = old.split('|')
    g.require(len(cells) == 7, 'actual baseline five-column row')
    cells[5] = ' RESOLVED — ' + g.E + 'recovery-authorization.json ' + g.QA + ' ' + g.CAPTURE + ' '
    new = '|'.join(cells)
    body = a[2].replace(old + '\n', '')
    marker = '|----|------|----------|-------------|------------|\n'
    g.require(body.count(marker) == 1, 'actual Resolved table marker')
    body = body.replace(marker, marker + new + '\n', 1)
    return before, '---\n' + g.yaml.safe_dump(meta, sort_keys=False) + '---' + body, new


def private_debt_controls(original_red=False):
    """Only scratch writes; no product API or real capture bypass is installed."""
    before, valid, row = fixture()
    source = g.ROOT
    with tempfile.TemporaryDirectory(prefix='nizam118-closeout-controls-') as parent:
        scratch = Path(parent) / 'repo'
        subprocess.run(['git', 'clone', '-q', '--shared', '--no-checkout', str(source), str(scratch)], check=True)
        target = scratch / DEBT
        target.parent.mkdir(parents=True)
        g.ROOT = scratch
        try:
            target.write_text(valid)
            if original_red:
                print('PRIVATE_REAL_ROW: exactly five columns; Notes replaced and054 moved; unmodified B2 debt() follows', flush=True)
                ORIGINAL_DEBT(True)
                g.require(False, 'original guard unexpectedly accepted valid resolution')
            debt(True)
            target.write_text(before)
            debt(False)
            trials = [('missing-cell', valid.replace(row, '|'.join(row.split('|')[:-2]) + '|'), True), ('duplicate-ID', valid.replace(row, row + '\n' + row), True), ('premature-resolution', valid, False), ('sixth-cell', valid.replace(row, row + ' extra |'), True), ('unrelated-debt', valid.replace('NDEBT-040', 'NDEBT-999'), True), ('wrong-version', valid.replace('0.75.0', '0.76.0'), True), ('missing-capture-ref', valid.replace(g.CAPTURE, 'missing-capture'), True), ('missing-QA-ref', valid.replace(g.QA, 'missing-QA'), True), ('missing-authorization-ref', valid.replace(g.E + 'recovery-authorization.json', 'missing-auth'), True)]
            for index in (1, 2, 3, 4):
                cells = row.split('|'); cells[index] = ' changed '
                trials.append(('identity-column-' + str(index), valid.replace(row, '|'.join(cells)), True))
            # Keep real row bytes but put it back in Open: section ownership matters.
            misplaced = valid.replace(row + '\n', '').replace('|----|------|----------|-------------|-------|\n', '|----|------|----------|-------------|-------|\n' + row + '\n', 1)
            trials.append(('wrong-section', misplaced, True))
            for label, raw, complete in trials:
                target.write_text(raw)
                try:
                    debt(complete)
                except (AssertionError, KeyError, ValueError):
                    print('PASS PRIVATE debt rejection: ' + label)
                else:
                    g.require(False, 'accepted private debt mutation ' + label)
            print('PASS PRIVATE debt: real five-column positive; baseline unchanged before capture; ' + str(len(trials)) + ' negatives; immutable COORD source')
        finally:
            g.ROOT = source


# The only two substitutions. Original scope/approved/closure and every other check remain callable unchanged.
g.debt = debt
g._debt_controls = private_debt_controls


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--scope', action='store_true')
    mode.add_argument('--controls', action='store_true')
    mode.add_argument('--original-valid-row-red', action='store_true')
    args = parser.parse_args()
    if args.scope:
        g.scope(g.BASE)
        print('PASS disclosed closeout adapter: original pinned B2 scope with corrected debt callback')
    else:
        private_debt_controls(args.original_valid_row_red)
        print('LIMIT: private debt fixtures; no actual capture or product acceptance claim')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as exc:
        print(str(exc))
        raise SystemExit(1)
