FF...
======================================================================
FAIL: test_actual_readme_local_links_resolve (__main__.FirstContactTests.test_actual_readme_local_links_resolve)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/cnross/.codex/worktrees/acd4/nizam-framework/tools/test_first_contact.py", line 81, in test_actual_readme_local_links_resolve
    self.assertEqual(broken, [])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: Lists differ: ['docs/architecture/ADR-001-hybrid-monorep[280 chars]tpl'] != []

First list contains 8 additional elements.
First extra element 0:
'docs/architecture/ADR-001-hybrid-monorepo-topology.md'

+ []
- ['docs/architecture/ADR-001-hybrid-monorepo-topology.md',
-  'docs/architecture/ADR-002-declarative-capability-index.md',
-  'docs/architecture/ADR-003-zero-dependency-posix-bootstrap.md',
-  'schema/nizam_index.schema.json',
-  'standard/provenance.md',
-  'methodology/02_quality.md',
-  'methodology/03_release.md',
-  'templates/AGENTS.md.tpl']

======================================================================
FAIL: test_missing_root_target_is_rejected (__main__.FirstContactTests.test_missing_root_target_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/cnross/.codex/worktrees/acd4/nizam-framework/tools/test_first_contact.py", line 48, in test_missing_root_target_is_rejected
    self.assertNotEqual(result.returncode, 0, result.stdout)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : [C9] PASS path-resolution
SUMMARY: 16 passed, 0 failed


----------------------------------------------------------------------
Ran 5 tests in 0.757s

FAILED (failures=2)
