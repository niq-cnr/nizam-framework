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

- Decision: v3.2.0 (MINOR, completing the prepared cut) rather than v3.1.4 (PATCH); the
  change set adds schema/protocol capability, which §3.4 forbids mislabelling as PATCH.
  MAJOR vs MINOR for the new required `--expected-candidate-sha256` is an unresolved operator decision.
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
