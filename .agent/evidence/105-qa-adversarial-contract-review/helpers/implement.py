#!/usr/bin/env python3
"""implement.py TREE : positive-control implementation of contract 105 rev 2 (scratch clone only; never run in the repo).
Applies design_notes.reference_implementation.text and design_notes.pinned_texts exactly as the Generator would."""
import json, re, sys, pathlib, yaml
tree = pathlib.Path(sys.argv[1])
D = json.load(open(tree / '.agent/contracts/105.json'))['design_notes']
P = D['pinned_texts']
q = lambda s: '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'

# 1. script: replace everything from the separator that precedes '# COMPLETENESS GUARD' to EOF
path = tree / 'tools/fixtures_self_test.sh'
t = path.read_text()
marker = '# ---------------------------------------------------------------------------\n# COMPLETENESS GUARD'
assert t.count(marker) == 1
path.write_text(t[:t.index(marker)] + D['reference_implementation']['text'])

# 2. tools/README.md: version bump + head entry + paragraph as the last paragraph (end of file)
path = tree / 'tools/README.md'
t = path.read_text()
assert t.count('version: 0.13.0\n') == 1
t = t.replace('version: 0.13.0\n', 'version: 0.14.0\n', 1)
t = t.replace('change_log:\n', 'change_log:\n  - version: "0.14.0"\n    date: "2026-10-09"\n    summary: %s\n' % q(P['readme_change_log_summary']), 1)
assert t.endswith('`e2e_bootstrap`.\n')
t = t + '\n' + P['readme_paragraph'] + '\n'
path.write_text(t)

# 3. CHANGELOG: bullet after the feature-104 bullet, before [1.4.0]
path = tree / 'CHANGELOG.md'
t = path.read_text()
m = re.search(r'\n\n## \[1\.4\.0\] - 2026-10-08', t)
assert m
t = t[:m.start()] + '\n' + P['changelog_bullet'] + t[m.start():]
path.write_text(t)

# 4. phase yaml
path = tree / 'docs/planning/phase_014.yaml'
t = path.read_text()
anchor = '    description: Nested-fixture ownership — the fixture-subdirectory claim map pulled forward from NIP-0003 feature 109 (NDEBT-042).\n    status: PENDING\n'
assert t.count(anchor) == 1
t = t.replace(anchor, anchor + '    docs_updated: %s\n    changelog_entry: %s\n    evidence: %s\n' % (P['phase_yaml_docs_updated'], q(P['phase_yaml_changelog_entry']), P['phase_yaml_evidence']), 1)
path.write_text(t)
print('implemented in', tree)
