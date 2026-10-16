"""Verify actual normal merge against the admitted PR candidate."""
import json
from pathlib import Path
import subprocess

base = Path(__file__).resolve().parent
pr = json.loads((base / 'postmerge-pr.stdout.txt').read_text())
head = '19efbca54be6b2d58f637b22ee4b4185cf32b342'
previous = 'c8ef3cd44dd795ae249769b79a99ef4ebf3f0ad7'
merge = 'bfd15d10eb718d2cf18272b35c1bb5857af71f3f'
git = lambda *args: subprocess.check_output(['git', *args], text=True).strip()
assert pr['state'] == 'MERGED' and pr['headRefOid'] == head and pr['baseRefOid'] == previous
assert pr['mergeCommit']['oid'] == merge
assert git('show', '-s', '--format=%P', merge).split() == [previous, head]
assert git('rev-parse', merge + '^{tree}') == git('rev-parse', head + '^{tree}')
assert git('rev-parse', 'origin/main') == merge
assert json.loads((base / 'normal-merge.execution.json').read_text())['actual_exit'] == 0
assert len(pr['statusCheckRollup']) == 6 and all(row['conclusion'] == 'SUCCESS' for row in pr['statusCheckRollup'])
proof = dict(pr=105, head=head, base=previous, normal_merge=merge, parents=[previous, head],
             tested_tree=git('rev-parse', head + '^{tree}'), actual_merge_tree=git('rev-parse', merge + '^{tree}'),
             merged_at=pr['mergedAt'], required_checks='all six SUCCESS', feedback='fresh complete premerge snapshot; only known own CI1 status comment',
             normal_merge_execution=str(base / 'normal-merge.execution.json'),
             qualified_ci_evidence='.agent/evidence/133/ci/pr105-terminal2/report.json',
             main_delivery='Pending matching actual-merge main CI; no current-controls-ready or live adoption claim')
(base / 'merge-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof, sort_keys=True))
