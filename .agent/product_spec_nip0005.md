# Product spec — NIP-0005 executable claim binding (proposed)

Status of this spec: **proposed authoring task**. Not approved. Gates have not run.

## 1. Goal

Author `docs/nips/NIP-0005-executable-claim-binding.md` as a **proposed** Nizam Improvement Proposal, through
the governed Nizam path, so that independent reviewers can judge it. The NIP proposes that every normative
claim carry an executable binding (`verified_by` or typed `unverifiable`), that no artifact define its own
expected state, and that a receipt whose expectation is recomputed from the artifact be classified
`SELF_CERTIFYING` rather than satisfying a gate. The NIP body is fixed text supplied by the operator
(lane brief, "THE NIP CONTENT"), copied verbatim.

## 2. Classification and route

- `tools/start_path.py classify --touches-security --needs-new-contract` over the four planned paths returns
  `assurance_tier: High-assurance`, `route: high-risk`.
- Required gates (from the classifier, not asserted by this spec as passed):
  `loop1:contract_approval`, `capability_preflight`, `loop2:validator_mode_b`, `loop2:evaluator_qa`,
  `convergent_review_or_isolation_suite`, `loop2:evidence_capture`.
- Without the security/new-contract flags the classifier returns Routine/small-change; the High-assurance
  route is the one that applies because the NIP touches authority-verification and evidence-authority
  boundaries.

## 3. Scope

Files created (only these; `files_modify` is empty):

1. `docs/nips/NIP-0005-executable-claim-binding.md` — NIP body (verbatim from brief).
2. `.agent/product_spec_nip0005.md` — this spec.
3. `.agent/contracts/nip0005-executable-claim-binding.json` — contract, shaped like
   `.agent/contracts/post-ga-nip-planning.json`.
4. `.agent/evidence/nip0005/check_nip0005.py` — checker for AT1–AT5.
5. `.agent/evidence/nip0005/` — evidence directory; holds `01-check.txt` (actual checker output).
6. `.agent/validator/nip0005-*.json` and `.agent/qa/nip0005-*.json` — **placeholders only** (see §6).
7. `.agent/progress-notes.md` — lane log (already present; a process record, not a deliverable).

## 4. Non-goals

- No `.nizam/` edits (installed payload is immutable under the local AGENTS.md).
- No gate changes, no reduction of any existing gate or requirement.
- No claim-binding implementation (the NIP proposes one; this task does not build it).
- No H-NIP self-acceptance. The NIP stays `status: proposed`.
- No approval field set to `true`; no contract `status: complete`; no verdict asserting a gate passed.
- No push, no PR. Commit on the current branch and stop.
- No modification of existing NIP files, planning files, backlog, roadmap, changelog or run state.

## 5. Acceptance tests

Each is run by `.agent/evidence/nip0005/check_nip0005.py` with a specific sub-command; the exit code and
output are captured as evidence.

- **AT1** — The NIP's YAML frontmatter parses; `id` equals `nip-0005-executable-claim-binding`; `status`
  equals `proposed`.
- **AT2** — Headings `### A1`, `### A2`, `### A3`, `### A4` all exist in the NIP.
- **AT3** — The Status section contains the phrase `awaiting H-NIP acceptance`. No line that mentions a
  gate also asserts it is active, adopted or accepted without a negation or pending qualifier.
- **AT4** — The observations table in §1.1 has no placeholder text in any result cell; each result cell is
  non-empty; the integers `5`, `8`, `4`, `23`, `56`, `33` each appear as standalone integers in the table.
- **AT5** — `git diff --name-only <base_revision>..HEAD` contains no path beginning with `.nizam/`.

The checker must exit non-zero on any failure and print which assertion failed. Assertions must not be
weakened to pass; if one fails, the NIP or checker is fixed, not the assertion.

## 6. Approvals and placeholders

The contract's `approvals` object is `{"validator_mode_a": false, "evaluator_contract_review": false,
"revisions": 0}`. Every approval stays `false`. `.agent/validator/nip0005-*.json` and
`.agent/qa/nip0005-*.json` are **placeholders** that record `"approved": false` and "pending independent
review". They are not verdicts. Verdicts are written only by independent reviewers.

## 7. H-NIP acceptance

H-NIP acceptance of NIP-0005 is a **separate future act by the operator**. This task does not perform,
request on the operator's behalf, or imply it. Until that act, the NIP remains `proposed`, awaiting H-NIP
acceptance, and no gate it proposes is active.

## 8. Definition of done

- The four authored files exist and are committed (plus the placeholders in §3.6).
- `python3 .agent/evidence/nip0005/check_nip0005.py` exits 0; its output is captured in
  `.agent/evidence/nip0005/01-check.txt`.
- Contract `status` is `pending`; every approval is `false`.
- `git diff --name-only 1dfa47f2f006d92e661aa2ec52b4dd0e1dd0bcdd..HEAD` shows no `.nizam/` path.
- Reference: `.nizam/standard/definition_of_done.md`.
