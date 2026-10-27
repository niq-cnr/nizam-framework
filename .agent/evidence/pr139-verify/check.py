#!/usr/bin/env python3
"""Bind reproduced integration files to the PR commit and both parent facts."""
import subprocess
from pathlib import Path

PR = '65036ef8eea1eef4dcf9a3a772570736a0baf499'
BASE = '52a91abbee308282e24a5296d3597e9494e9a849'
names = ('CHANGELOG.md', 'docs/planning/ROADMAP.md', 'docs/planning/API_REFERENCE_PILOT.md')
for name in names:
    expected = subprocess.check_output(['git', 'show', f'{PR}:{name}'])
    assert Path(name).read_bytes() == expected, name
changelog, roadmap, plan = [Path(n).read_text() for n in names]
main_change = subprocess.check_output(['git', 'show', f'{BASE}:CHANGELOG.md'], text=True)
assert changelog[changelog.index('## [3.0.0]'):] == main_change[main_change.index('## [3.0.0]'):]
for text in (changelog, roadmap, plan):
    assert all(mark not in text for mark in ('<<<<<<< ', '=======\n', '>>>>>>> '))
assert 'Record the approved `API-REF-PILOT` backlog plan' in changelog
assert '## Documentation alignment owner execution (2026-10-27)' in roadmap
assert 'Release in preparation: v3.0.0' in roadmap and 'API-REF-PILOT' in roadmap
assert 'version: 0.65.38\n' in roadmap and 'version: "0.65.38"' in roadmap
print('three verified source files byte-match PR 65036ef8 and preserve both parent records')
