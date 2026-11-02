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
