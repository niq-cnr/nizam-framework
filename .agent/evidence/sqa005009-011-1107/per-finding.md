# SQA-integrity-005..009, 011 -- reproduce, fix, disposition

Audit c905615d; findings sha256 prefix 82d4df0b34fc4235. Base 0a0a4d24.
Every finding was first reproduced on the base. None was disproved, so none is closed by
evidence alone. All six were reproduced and fixed.

| Finding | Base reproduction (probe-before.txt) | Fix | Post-fix (probe-after.txt) |
|---|---|---|---|
| 005 CI reachability | 23 of 40 top-level suites named by no CI/harness invocation (005-base-unreached.txt) | tools/ci_suites.txt + one CI loop; tools/ci_suite_exclusions.txt with reasons; tools/test_suite_coverage.py gate | 0 unaccounted; gate rc 0 |
| 006 C8 same-HEAD | committed bump 0.1.0->0.2.0, no change record: C8 PASS (rc 0) | NIZAM_C8_BASE comparison base, fail-closed on unresolvable base; CI exports PR/prior-push base | REFUSED (rc 1) |
| 007 baseline reuse | passing rerun replaced baseline digest; failing rerun deleted it | refuse (exit 64) any run into a namespace holding baseline.json, before any write | digest unchanged on pass and fail reruns |
| 008 usage totals | pre/post pair: input 240 / output 60 for one charged request; input stays unknown after completion | per-operation resolution (last non-null per field) | 120/30, charged 1, input resolved |
| 009 preregistration | 6 of 14 declared design fields enforced; 8 unset fields accepted | all 14 required; explicit not_applicable reason is the only skip | partial and unset-field records REFUSED |
| 011 SELF_GOVERNANCE | current heading names v3.0.0 while structured record and provenance are v3.1.3 | current section rewritten to v3.1.3; v3.0.0 labeled historical | heading names v3.1.3 (CONSISTENT) |

## Disproofs
None. Every finding reproduced at 0a0a4d24.

## Scope notes
- 005: 3 excluded suites fail at base (test_nf_ac02_policy_reconciliation: runtime finite-recovery gap;
  test_nf_owner_dag_and_backlog: asserts superseded v3.0.0) or are not unittest suites (test_corrective_release).
  They are excluded with the reason written down, not hidden. Fixing them is out of scope.
- 007: the fixture CLI probe was adjusted to use a fresh output namespace per dirty-tree case. The
  PASS case had written a baseline that the old overwrite behavior silently replaced.
- 009: the positive test fixture is now fully specified (it was the weakened fixture the audit named).
- 011: documentation only.

## Not changed
Historical QA records 035/036/123 and the C11/C16 intended refusals. Those are untouched.
