#!/usr/bin/env python3
"""Check both parents' backlog/release facts survive a two-file merge."""
from pathlib import Path
import subprocess


def parent(revision, name):
    return subprocess.check_output(['git', 'show', revision + ':' + name], text=True)

changelog = Path('CHANGELOG.md').read_text()
roadmap = Path('docs/planning/ROADMAP.md').read_text()
main_change = parent('origin/main', 'CHANGELOG.md')
pr_roadmap = parent('HEAD', 'docs/planning/ROADMAP.md')
main_roadmap = parent('origin/main', 'docs/planning/ROADMAP.md')
for text in (changelog, roadmap):
    assert all(marker not in text for marker in ('<<<<<<< ', '=======\n', '>>>>>>> '))
assert changelog[changelog.index('## [3.0.0]'):]==main_change[main_change.index('## [3.0.0]'):]
assert 'Record the approved `API-REF-PILOT` backlog plan' in changelog
for needle in ('Register API-REF-PILOT as operator-approved backlog work',
               'Prepare an independent v3.0.0 MAJOR corrective candidate',
               'Attach NF-01–NF-22 documentation alignment as a bounded workstream',
               '## Documentation alignment owner execution (2026-10-27)',
               'Release in preparation: v3.0.0', 'Latest released tag: v2.0.0'):
    assert needle in roadmap, needle
assert 'API-REF-PILOT' in pr_roadmap and '## Documentation alignment owner execution' in main_roadmap
assert 'version: 0.65.38\n' in roadmap and '  - version: "0.65.38"' in roadmap
print('both parent backlog and release facts preserved; version collision reconciled')
