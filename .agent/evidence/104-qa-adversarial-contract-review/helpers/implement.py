#!/usr/bin/env python3
"""implement.py TREE : positive-control implementation of contract 104 rev 3 (scratch clone only; never run in the repo).
Applies design_notes.pinned_texts exactly as the Generator would."""
import json, re, sys, pathlib, yaml
tree = pathlib.Path(sys.argv[1])
P = json.load(open(tree / '.agent/contracts/104.json'))['design_notes']['pinned_texts']
q = lambda s: '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'

# workflow: append the pinned job after fixtures_self_test, 2-space indented
path = tree / '.github/workflows/compliance.yml'
t = path.read_text()
assert t.endswith('      - run: bash tools/fixtures_self_test.sh\n')
job = ''.join(('  ' + l if l.strip() else l) for l in P['workflow_job_yaml'].splitlines(True))
path.write_text(t + '\n' + job.rstrip('\n') + '\n')

def bump(text, old_v, new_v, summary):
    assert text.count('version: %s\n' % old_v) == 1
    text = text.replace('version: %s\n' % old_v, 'version: %s\n' % new_v, 1)
    assert text.count('change_log:\n') == 1
    return text.replace('change_log:\n', 'change_log:\n  - version: "%s"\n    date: "2026-10-09"\n    summary: %s\n' % (new_v, q(summary)), 1)

# DoD
path = tree / 'standard/definition_of_done.md'
t = bump(path.read_text(), '0.1.0', '0.2.0', P['dod_change_log_summary'])
for a, b in P['dod_replacements']:
    flat = ' '.join(a.split())
    # sources may span a line break in the document: match whitespace-flexibly
    rx = re.compile(r'\s+'.join(re.escape(w) for w in a.split()))
    assert len(rx.findall(t)) == 1, a
    t = rx.sub(lambda m: b, t, count=1)
path.write_text(t)

# tools/README.md
path = tree / 'tools/README.md'
t = bump(path.read_text(), '0.12.0', '0.13.0', P['readme_change_log_summary'])
anchor = 'never runs a trial outside the sandbox.\n\n## Compliance Coverage'
assert t.count(anchor) == 1
t = t.replace(anchor, 'never runs a trial outside the sandbox.\n\n' + P['readme_paragraph'] + '\n\n## Compliance Coverage', 1)
path.write_text(t)

# schema/README.md
path = tree / 'schema/README.md'
t = bump(path.read_text(), '0.18.0', '0.19.0', P['schema_change_log_summary'])
anchor = '\n\n## DD-3 — Evidence Externalisation'
assert t.count(anchor) == 1
t = t.replace(anchor, '\n\n' + P['schema_readme_line'] + anchor, 1)
path.write_text(t)

# CHANGELOG
path = tree / 'CHANGELOG.md'
t = path.read_text()
m = re.search(r'\n\n## \[1\.4\.0\] - 2026-10-08', t)
assert m
t = t[:m.start()] + '\n' + P['changelog_bullet'] + t[m.start():]
path.write_text(t)

# phase yaml
path = tree / 'docs/planning/phase_014.yaml'
t = path.read_text()
anchor = '    description: Convergent-review suite enforced in CI, and the review schema family\'s validator stated (NDEBT-041); depends on 103.\n    status: PENDING\n'
assert t.count(anchor) == 1
t = t.replace(anchor, anchor + '    docs_updated: %s\n    changelog_entry: %s\n    evidence: %s\n' % (P['phase_yaml_docs_updated'], q(P['phase_yaml_changelog_entry']), P['phase_yaml_evidence']), 1)
path.write_text(t)
print('implemented in', tree)
