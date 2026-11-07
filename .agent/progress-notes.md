# Progress notes — NIP-0005 governed authoring lane

Base: 1dfa47f2f006d92e661aa2ec52b4dd0e1dd0bcdd  Branch: nip/0005-executable-claim-binding

## Step 0 — classification (2026-11 lane start)
- `tools/start_path.py classify --files <4 planned paths>` (no flags): Routine / small-change. Not the brief's route.
- Same files with `--touches-security --needs-new-contract`: High-assurance / high-risk, required_gates =
  loop1:contract_approval, capability_preflight, loop2:validator_mode_b, loop2:evaluator_qa,
  convergent_review_or_isolation_suite, loop2:evidence_capture. Matches the brief. Route followed: high-risk
  (contract-first). Approval fields stay false.
- SPAWN count so far: 0. Authoring is the lane's own artifact work (small, documentary, one author); no
  independent role is spawned here, because the gates that need independence are downstream and must not be run by this lane.

## Step 1 — spec and contract
- Wrote .agent/product_spec_nip0005.md (85 lines), committed.
- Wrote .agent/contracts/nip0005-executable-claim-binding.json (status pending, approvals all false), validated as JSON.
- SPAWN: none so far.

## Step 2 — NIP chunk 1 committed (frontmatter, status, sec 1, 1.1)
## Step 3 — NIP chunk 2 committed (1.2, A1, A2)
## Step 4 — NIP chunk 3 committed (A3, A4, 3-6)
## Step 5 — NIP chunk 3 committed; next: checker
## Step 6 — checker written, AT1-AT5 PASS (01-check.txt), negative controls (02-negative-controls.txt), placeholders written
- SPAWN: 0 (none spawned; the independent gates are the next lane step, not run here)

## NIZAMREL-1105 — release-criteria evidence (2026-11-05)

Base/head assessed: 1a331c1a (= origin/main = v3.1.3 + 34 commits). No tag created or pushed.
Route: small-change (start_path begin/done), intent .agent/evidence/NIZAMREL-1105-intent.json.

- Decision: PATCH (v3.1.4) is rejected. The change set adds schema/protocol capability, which §3.4 forbids
  mislabelling as PATCH. MINOR (v3.2.0, completing PR #159) vs MAJOR is an unresolved operator decision,
  driven by the newly required `--expected-candidate-sha256` on `external_evidence.py admit`.
- All 34 commits classified: .agent/evidence/NIZAMREL-1105/README.md §2 (no silent skips).
- ce73d2e9 is an ancestor of HEAD and contained in no tag; it unblocks the consumer CodeQL red on the next tag.
- Release criteria at HEAD: validate.sh 16/16; release_closeout pr/tag PASS; verify_self_governance PASS;
  CI compliance success on main run 41995598380.
- BLOCKER: no prepublication self-install evidence for HEAD (§6.1). The v3.1.3 proof binds candidate
  2162b8e9 and is invalid for this head. Needs H-CONSUMER-UPGRADE owner approval + safe-host install.
- NIZAM.json left at 3.2.0 (no bump), so the close-out gate does not require self-install evidence in this PR.
- SPAWN count: 0. No independent evaluator spawned in this lane; required independent acceptance is
  therefore outstanding and is named as a residual in the PR.
- CHANGELOG: [Unreleased] gained Added/Changed/Fixed entries for #152-#154, #162, #163 with tier notes.

## NIZAMREL-1105 — PR and receipt (2026-11-05)

- PR: https://github.com/niq-cnr/nizam-framework/pull/164 (base main, head b50ae034).
- Exact-head CI on b50ae034: closeout, convergent_review, e2e_bootstrap, fixtures_self_test,
  self_governance, validate — all PASS.
- Independent evaluator (fresh context, fleet-evaluator/lane-evaluator), 2 rounds. Round 1 failed (62):
  false prior_ledger claim, MINOR stated as settled, unverified counts. Fixed in aae8189b. Round 2 failed (40):
  the evaluator had NO shell (read/find/grep only), so re-execution checks were not run; its one real finding
  (stale v1.4.0 trial-count line) was fixed in b50ae034. Those checks were then run by the lane directly
  and recorded in .agent/evidence/NIZAMREL-1105/. Evaluator-side re-execution is NOT independent evidence.
- OPEN: no independent acceptance verdict with shell exists, so .agent/qa/NIZAMREL-1105.json is absent and
  `start_path.py done small-change` is NOT satisfied. Do not record this lane as accepted.
- No tag created or pushed. No NIZAM.json or .nizam/ change.
- Blockers before any tag: MINOR vs MAJOR (operator); prepublication self-install of the cut head (§6.1,
  needs H-CONSUMER-UPGRADE owner approval and a safe-host install).

## NIZAMREL-EVAL-1105 — independent release-criteria evaluation receipt (2026-11-05)

- Subject: origin/main `5ecc7e39` (PR #164 squash). Read-only; no tag, merge, CI, changelog or code change.
- Verdict: **NOT-QUALIFIED**. Record: `docs/eval-records/eval-release-criteria-5ecc7e39.md`.
- Key findings: §6.1 self-install not met for any candidate; §3.4 round-up not applied to 8865b30f (MAJOR-plausible) or 2ce3d571; current-tense "three trials" text remains in templates/schema outside the CHANGELOG line PR #164 fixed; root NIZAM.json already at 3.2.0 with no tag; independent acceptance `.agent/qa/NIZAMREL-1105.json` absent.
- ce73d2e9: ancestor of 5ecc7e39 and 1a331c1a; not in v3.1.3; contained in 0 tags. Client unblocking not verified.
- CI on 5ecc7e39: compliance run 42024036239, 5/5 jobs success. release_closeout/release/pages: no run for this commit.
- Reporting-doctrine labels named in the brief were not found in repo or local skills; labels applied per the brief's own definitions.
- Local: `release_closeout.py --mode pr` exit 0; `--mode tag --tag v3.1.3` exit 0.
- No tag created or pushed. No merge. No changes outside this record and this receipt.

## SQA-005..009,011 — framework integrity fix (2026-11-07)

- Scope: exactly SQA-integrity-005, -006, -007, -008, -009, -011 from audit c905615d (findings sha256
  prefix 82d4df0b34fc4235). Base origin/main `0a0a4d24`. Branch `fix/framework-integrity-sqa005-009-1107`.
- Head: `505d4c04` (tree `1bf85152`); fix commits `75d65b4a`, `e4eddcf4`, `505d4c04`; evidence `5d106314`.
- Reproduction: all six findings reproduced at the base before any change (probe-before.txt). None was
  disproved, so none is closed by evidence alone. Per-finding record: .agent/evidence/sqa005009-011-1107/per-finding.md.
- Fixes: 005 CI manifest + coverage gate (23 of 40 suites were unreached at base); 006 explicit C8 base
  with fail-closed CI step; 007 refuse baseline reuse before any write (lexists); 008 per-operation usage
  resolution, conflicts refused; 009 all 14 design fields required, design-defining fields non-waivable;
  011 SELF_GOVERNANCE current section names v3.1.3, v3.0.0 labeled historical.
- Battery at 505d4c04: validate.sh 14 passed / 2 failed (C11, C16 only — intended refusals, unchanged);
  fixtures_self_test 176/176, 0 failed; test_start_path rc 0; test_framework_integrity_s003004 19 OK;
  test_framework_integrity_sqa005009 27 OK; CI dedicated loop rc 0 (21 suites); coverage gate 0 unaccounted.
  Captures: .agent/evidence/sqa005009-011-1107/battery-FINAL.txt and *-FINAL.txt.
- Base negatives: 13 fail + 3 error on pristine 0a0a4d24 (negatives-on-base-table-FINAL.txt). Errors are
  helper absence (2) and the absent CI loop (1); none is a spurious failure.
- Independent evaluation: round 1 on 75d65b4a returned fail (72) on six points; each was verified and
  fixed in e4eddcf4. Round 2 (fresh context) on e4eddcf4 returned pass (86): all eight points closed, with
  warnings. The P6 label and the stale regression diffstat were then addressed in 505d4c04. Evaluator
  rounds ran with read/grep tools only; their test results are artifact-verified, not re-executed.
- Hard constraints verified at head (protected-paths-final.txt): .agent/qa/035/036/123.json unchanged;
  .nizam/ and NIZAM.json unchanged; tools/verify_lib.sh and tools/ecosystem_audit.py unchanged; no tag;
  no tracked .pyc. The fixtures_self_test.sh hunks (lines ~749-777) are disjoint from #170 (684, 855, 870).
- Residuals (not closed here): the excluded suites test_nf_ac02_policy_reconciliation (runtime
  finite-recovery exit-code gap) and test_nf_owner_dag_and_backlog (asserts superseded v3.0.0) fail at base
  and are excluded with reasons in tools/ci_suite_exclusions.txt; fixing them is a separate item.
  The CI workflow step exit-1 for an unresolvable C8 base is verified by reading and by a replayed run,
  not by a test in the required CI job.
- Untracked .agent/harness/ (runtime leases/node state written during this session) is not part of this
  change and is not committed.
- No release tag, no version bump, no NXOS/Mandate work, no H-CONSUMER-UPGRADE self-install.
