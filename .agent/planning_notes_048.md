# Planning Note — Feature 048: PR-stack review response (round 3: operator review of PR #21)

**Status:** planning artifact (generator source material). Not a shipped file; not part
of feature 048's scope-of-change. Written 2026-07-18 by the operator-directed
review-response session (single-session execution, all roles collapsed; process
honesty per the durable-state rule — no separate planner/generator/evaluator agents
were dispatched for this overhead feature).

Feature 048 answers the **operator's own review of PR #21** (six inline comment
threads = five logical findings; CodeRabbit skipped PR #21 entirely, 291 files > 150
limit) plus two round-2 stragglers left open after feature 047 closed: the contested
CodeRabbit thread on PR #20 (`.agent/feature_list_005.json` acceptance-check
load-bearing finding, CodeRabbit re-check reply of 2026-07-18T04:09:52Z) and
CodeRabbit's direct question on PR #22 (follow-up issue vs NDEBT-021 record). Both
stragglers are REPLY-ONLY; no file change.

All fixes land as **one new commit at the stack tip** (stacked-PR convention; house
precedent 046/047); the operator's PR #21 threads are answered by reference to the tip
commit. Queued by feature 047's close-out (run_state event, 2026-07-18): "operator's
own review of PR #21 (five inline comments) triaged -> feature 048 (fix items 1-3 +
NDEBT-023/024 + NDEBT-019 pipe fix)".

Verified context at planning: branch `agent/ecosystem-cycle-pr-f5`, HEAD `68cb36f`
(feature 047 close-out; deliverable `6d273c6`); DEBT.md `0.13.0`; ecosystem/README.md
`0.2.0`; ecosystem/01|03|07 all `0.1.0`. Every finding AH-2 re-verified still present
at HEAD `68cb36f` (see per-item notes). Next free DEBT ids: NDEBT-023, NDEBT-024
(highest registered is NDEBT-022). Mechanical row scan at HEAD: NDEBT-019 is the ONLY
row parsing to 7 cells (every other row parses to 5) — confirms 047 Mode B's queued
observation. Mechanical dangling-ref scan of `ecosystem/*.md` at HEAD finds exactly
three sites: `03_engineering_audit.md:140` (`ecosystem/08_ga_gate.md`),
`07_progress_comparison.md:131` and `:160` (`schema/audit_delta.schema.json`) —
exactly the operator's inventory, nothing more.

---

## 1. Disposition summary (operator's five logical findings)

| # | Thread (file) | Disposition |
|---|---------------|-------------|
| 1 | `ecosystem/README.md` L80 — stale "Of the Planned documents…" paragraph contradicts the table (02/03/07 now Shipped); process note re version discipline | **FIX 1** |
| 2 | `ecosystem/01_clean_state_preflight.md` L107 — Sec 5 pending-halt vs Sec 6 "schema-valid artifact" contradiction (pre-approval PWE artifact is schema-invalid, empirically confirmed) | **FIX 2** |
| 3 | `ecosystem/02_evidence_baseline.md` L85 — Sec 4 same-repo revision-consistency FAIL condition enforced by neither schema, fixture, nor capture tool | **DEBT → NDEBT-023 (Low)** |
| 4 | `ecosystem/03_engineering_audit.md` L140 + `ecosystem/07_progress_comparison.md` L131/L160 (two threads, one finding) — dangling directory-qualified refs violating the module's own bare-filename convention | **FIX 3** |
| 5 | `tools/fixtures/preflight_verdict_fail.json` L8 — `blocking: true` item inside `exceptions` whose schema description says "non-blocking"; also diverges from the shipped tool's real FAIL shape (`blocking_findings` key) | **DEBT → NDEBT-024 (Low)** |

Plus, carried from 047 Mode B (non-blocking observation, queued): **NDEBT-019 row
pipe fix** — escape the two raw pipes in the row's `bash tools/validate.sh 2>&1 |
tail -1 | grep ...` code-span so the row parses back to 5 cells (identical class and
mechanism to 047's NDEBT-016 fix; GFM renders `\|` as a literal `|` inside a code
span).

## 2. FIX specifications (scope = 5 files, all doc-truth; ZERO behavior change)

### FIX 1 — `ecosystem/README.md` (0.2.0 -> 0.2.1)

Replace the stale sentence block ("Of the Planned documents, `02_evidence_baseline.md`,
`03_engineering_audit.md`, and `07_progress_comparison.md` are mandatory-first-release
scope … later programme phase.") with the truthful state: the four core protocols
(01/02/03/07 — the mandatory first-release surface per product_spec_005.md Sec 2.3
"four core protocols (preflight/baseline/audit/comparison)") shipped in features
033-036; the five Planned documents (00/04/05/06/08) are the deferrable set
(Sec 2.3) and may be protocol-only or land in a later programme phase. Keep the
'"Shipped" means / "Planned" means' definition sentence untouched. Bump version +
change_log entry — this also models, going forward, the NDS Sec 7 edit discipline the
operator's process note flagged (the 034/035/036 row-flips edited this governed doc
without a version bump; invisible to C8 because `ecosystem/` is not in
`build_shipped_md_set`, verified at HEAD).

### FIX 2 — `ecosystem/01_clean_state_preflight.md` (0.1.0 -> 0.1.1, add change_log)

Append a "finalization timing" passage to Section 6 defining WHEN schema-validity is
required, matching the shipped CLI byte-for-byte (`tools/ecosystem_preflight.py`
docstring exit codes 2/3 and emission logic): schema-validity binds the FINAL artifact
(PASS / FAIL / PASS_WITH_EXCEPTIONS with the Sec-5 operator-approval decision folded
in). A run halting pending approval does NOT emit `preflight.json`; it records the
pending exceptions in an informational, deliberately non-schema-conformant pending
artifact alongside the eventual location (the shipped CLI: `preflight.pending.json`,
withholding `preflight.json` entirely) until the operator decision is recorded. State
explicitly that the pre-approval PASS_WITH_EXCEPTIONS state being unrepresentable as a
schema-valid `preflight.json` is BY DESIGN (the required `operator_approval` block is
the mechanism that makes an unapproved artifact impossible to mistake for an approved
one). Section 5's text is left untouched — with the artifact lifecycle defined in
Sec 6, its "record the pending exceptions in the verdict artifact" reads correctly as
the pending form.

### FIX 3 — bare-filename convention (03: 0.1.0 -> 0.1.1; 07: 0.1.0 -> 0.1.1; add change_logs)

- `ecosystem/03_engineering_audit.md` L140: `` `ecosystem/08_ga_gate.md` `` ->
  `` `08_ga_gate.md` `` (sole occurrence, verified).
- `ecosystem/07_progress_comparison.md` L131 + L160:
  `` `schema/audit_delta.schema.json` `` -> `` `audit_delta.schema.json` `` (both
  occurrences; L131 wording adjusted to "an optional `audit_delta.schema.json` (planned
  under `schema/`; …)" so the deferred location stays stated without a
  directory-qualified dangling path; L160's References entry likewise).

Rationale: the module README's own convention ("never directory-qualified until it
actually exists in this repository, to avoid a dangling reference") — the exact
landmine contract 032 fenced against; C9 does not sweep `ecosystem/` today (verified:
green 12/12 at HEAD with the refs dangling) so the fix is future-proofing for the
sweep extension, mechanically neutral now.

## 3. DEBT row texts (register in `docs/planning/DEBT.md`, 0.13.0 -> 0.14.0)

Both rows MUST be severity Low or Medium (045-verify-18: DEBT Open stays free of
High/Critical), single physical line, no raw unescaped pipes in any cell.

**NDEBT-023 (Low):** `ecosystem/02_evidence_baseline.md` Sec 4 declares a baseline
invalid when "declared revisions for the same repository are inconsistent across the
baseline's fields", but nothing mechanized enforces it: `schema/ecosystem_baseline.schema.json`
accepts two fully-anchored `repository_references` entries for the same repository at
different revisions (confirmed empirically with jsonschema Draft 2020-12 during the
operator's PR #21 review), the sole related negative fixture
`ecosystem_baseline_neg_mixed_timestamps.json` exercises only the missing-timestamp
sub-case, and `tools/ecosystem_preflight.py`'s `build_baseline_document` performs no
cross-entry same-repo consistency check (self-runs anchor every reference to the one
freshly-resolved HEAD, so the framework's own dogfood runs cannot produce the
inconsistency; the exposure is consumer-/hand-authored and future multi-repo
baselines). Remediation: same-repo revision-consistency negative fixture + a
documented capture-tool check (schema-level if expressible); post-v0.7.0 alongside
NDEBT-021.

**NDEBT-024 (Low):** `tools/fixtures/preflight_verdict_fail.json` places a
`blocking: true` item inside `exceptions`, whose schema field description reads "the
non-blocking findings surfaced by the run" — schema-valid (items are open objects)
but semantically muddled, and divergent from the shipped CLI's real FAIL emission,
which records blocking findings under a separate `blocking_findings` key and never
inside `exceptions`. Remediation: align the three surfaces post-v0.7.0 (a
`blocking_findings`/`blocking_conditions` key in the schema with the fixture updated
to the tool's real shape, or a loosened `exceptions` description), keeping C12 green.

## 4. Reply plan (after the tip commit exists)

- PR #21: one reply per thread (6), citing the deliverable commit for FIX items,
  the NDEBT ids for DEBT items; operator resolves their own threads.
- PR #20 contested thread (comment 3607368655): stacked-tree adjudication reply —
  concede CodeRabbit's tree-state facts at 45e3b67 (fixtures/C12/schema genuinely
  absent THERE), pin the stack-tip enforcement (fixture `preflight_verdict_invalid_exceptions.json`
  landed in PR-F2/feature 038; C12 asserts every `invalid_` fixture rejects on every
  default sweep since PR-F3/feature 042), and note the acceptance_tests entries are
  the planner's forward-looking plan of record, superseded by the negotiated
  per-feature contracts whose entries use exact-text pinning — same stacked-stack
  resolution CodeRabbit itself applied when withdrawing the ecosystem/README stub
  finding on this PR.
- PR #22 question (comment 3607425426 thread): NDEBT-021 record is sufficient —
  DEBT.md is this repository's canonical debt register (house pattern; GitHub issues
  are used for external consumer reports, e.g. issue #18/NDEBT-012); decline the
  follow-up issue with thanks.

## 5. Invariants (verify before commit)

- Both sweeps green with rc asserted: default `SUMMARY: 12 passed, 0 failed`,
  payload `SUMMARY (payload mode): 10 passed, 0 failed`; e2e bootstrap PASS.
- `.agent/evidence/045-release-readiness-checklist.md` SHA-256 unchanged
  (06f266c06abd9b3793477771de265698dbec0a00761c6d81818decbc7e31b5ea);
  `v0.6.0-release-notes.md` and `CHANGELOG.md` untouched by the diff; no `v0.7.0`
  tag on the remote (the pipeline never self-tags).
- DEBT.md: every `| NDEBT-` row parses to exactly 5 GFM cells; Open table carries no
  High/Critical severity.
- Deliverable-commit diff confined to exactly: `docs/planning/DEBT.md`,
  `ecosystem/README.md`, `ecosystem/01_clean_state_preflight.md`,
  `ecosystem/03_engineering_audit.md`, `ecosystem/07_progress_comparison.md`.
- No CHANGELOG.md entry (house precedent: 046/047 review-response doc-truth fixes
  carry in-file change_log records only; the [0.7.0] release section stays
  byte-stable for the pending H-FRAMEWORK-RELEASE).
