# Workflow-assurance fixtures

Maintained, reusable test fixtures and control configuration for
`tools/workflow_assurance.py` and `tools/test_workflow_assurance.py`.

These files were promoted out of historical feature evidence so that ordinary
regression tests and CI no longer depend on a developer's accumulated
`.agent/evidence/` workspace. The original historical files remain immutable at
their original commits and are bound by
`.agent/evidence-archive/index.json`; this directory is the maintained copy.

Ownership:

- `bundle_fixtures.py`, `entry_fixtures.py`, `foundation_fixtures.py`,
  `scope_guard_*.py` — test-only fixture code. They construct synthetic
  repositories and may read historical authority/proposal objects by declared
  Git revision; they never grant current acceptance.
- `wa123_controls_policy.json`, `wa125_profiles_policy.json` — frozen control
  policies observed by the `controls-ready` and `profiles-ready` checks. Their
  `evidence_ref` values deliberately point at immutable historical Git
  objects.
- `wa123_selection.json` — reserved location for the live Root-selected CI
  operation. When absent, the WA123 selection step in `.github/workflows/
  compliance.yml` intentionally performs no capture or verify run.

Synthetic evidence directories created inside temporary test repositories are
valid. Tests must not require the historical development checkout beyond
objects reachable from ordinary Git history.
