# Planning Note — Feature 046: PR-stack review response (round 1: PR #20)

**Status:** planning artifact (generator source material). Not a shipped file; not
part of feature 046's scope-of-change. Written by @planner 2026-07-18.

Feature 046 answers CodeRabbit's six actionable comments on PR #20
(CHANGES_REQUESTED). All fixes land as **one new commit at the stack tip**
(stacked-PR convention); earlier PR threads are resolved by reference to that tip
commit. **Do NOT implement fixes in this file** — this is the brief for
@generator's contract.

Verified context at the time of triage: branch `agent/ecosystem-governance-cycle`,
HEAD `ada3b9c`; manifest phase 005 active since 2026-07-17; the two FIX defects
confirmed still present in-tree (AH-2 satisfied).

---

## 1. AH-2 Triage Table (encode this disposition; do not re-triage)

| # | CodeRabbit finding | Disposition | Action in 046 |
|---|--------------------|-------------|----------------|
| 1 | `.agent/product_spec_005.md` frontmatter `status: draft` but the spec is the ACTIVATED plan of record (body says "Status: ACTIVE"; manifest phase 005 active 2026-07-17) | **FIX** (confirmed present) | Flip `status` → `active` (frontmatter enum is draft/active/deprecated); house-pattern `version` bump + `change_log` entry. Spec **body/other frontmatter unchanged** — status flip + its own change_log only. |
| 2 | `docs/planning/ROADMAP.md` Sequencing Recommendation (~line 168) still says "Track 2 is the recommended phase 005" — contradicts the file's own supersession note (~line 95-102) that Track 2 was SUPERSEDED as the phase-005 selection by NIP-0001 | **FIX** (confirmed present) | Rewrite the one sentence to frame Track 2 as **candidate scope for a subsequent phase**. ROADMAP `version` bump + `change_log` entry. |
| 3 | The `bash tools/validate.sh 2>&1 \| tail -1 \| grep …` pattern (historical evidence e.g. `.agent/evidence/031-verify-09.txt` + some committed acceptance commands) lacks pipefail / explicit exit-code capture — the validator's own exit status is not asserted | **REGISTER AS DEBT** (no code change now) | New row **NDEBT-019, severity Low**. Hardening deferred to the methodology/02 verification-authoring standard. Historical evidence captures are **IMMUTABLE** — do not edit them. False-PASS is only theoretical (a failing sweep emits no "0 failed" SUMMARY line). |
| 4 | During 045's contract review round 1 the evaluator misfired `rm -f` at the real `CHANGELOG.md` during a probe (self-caught + restored same turn via `git checkout`, zero lasting effect, disclosed in `.agent/qa/045-contract-review.json` history) | **REGISTER AS DEBT** (no code change now) | New row **NDEBT-020, severity Medium**. Registers the incident + the strengthened probe-isolation rule: verify cwd before any destructive command; destructive commands must never carry real-repo paths. |
| 5 | Comment on `.agent/evidence/031-verify-04.txt`: `startswith('005')` is too loose | **EXPLAIN-AND-RESOLVE** (no repo change) | Post rationale §2.1 as a PR reply. |
| 6 | Comment on `.agent/feature_list_005.json` acceptance checks "not load-bearing" | **EXPLAIN-AND-RESOLVE** (no repo change; REFUTED) | Post rationale §2.2 as a PR reply. |
| 7 | Comment on `ecosystem/README.md` "stub in PR-F1" | **EXPLAIN-AND-RESOLVE** (no repo change) | Post rationale §2.3 as a PR reply. |

**Severity constraint (load-bearing):** NDEBT-019 and NDEBT-020 MUST be Low or
Medium. Feature 045's release-readiness verification entry 18 requires **zero Open
P0/P1 rows** and is re-run at the release gate — a P0/P1 row here would break it.

---

## 2. Explain-and-resolve rationale (ready-to-post PR reply text)

The orchestrator posts these verbatim as replies on the corresponding PR #20
review threads. No repository change accompanies them.

### 2.1 — `.agent/evidence/031-verify-04.txt` (`startswith('005')` too loose)

> This is an **immutable point-in-time evidence capture**. It recorded the manifest
> state as it existed at feature-031 verification time, and that state is committed
> history and correct. The `startswith('005')` looseness is a known class already
> catalogued in **NDEBT-014** (the contract-verification defect catalogue, item on
> bare/loose token matching), whose remediation is folding the class into the
> methodology/02 verification-authoring standard. Editing this evidence file would
> rewrite an audit record; the gap it represents is already tracked and its live
> successors (contract-031 verification entries 7-8) use exact-text pinning. No
> change here.

### 2.2 — `.agent/feature_list_005.json` acceptance checks "not load-bearing" (REFUTED)

> This concern is **refuted by the tree**. `tools/fixtures/preflight_verdict_invalid_exceptions.json`
> IS the exact "PASS_WITH_EXCEPTIONS without operator_approval" negative fixture — its
> sole jsonschema violation is the missing `operator_approval` (verified). The
> incomplete-approval case is covered by `preflight_verdict_invalid_approval_incomplete.json`.
> Validator check **C12 asserts every `invalid_` fixture is rejected on every full
> sweep**, so these checks are load-bearing, not decorative. The separate
> capability-path concern is enforced by **C9 (path-validity)** and **C10
> (consistency)** on `NIZAM.json`. No change required.

### 2.3 — `ecosystem/README.md` "stub in PR-F1"

> `ecosystem/README.md` shipped **complete-for-031** in PR-F1 (frontmatter `active`,
> module description) as the indexed entry point of the plan of record. Features
> 032-040 completed it **within this same PR stack** (now v0.2.0, with Shipped/Planned
> navigation). At the stack tip the file is complete, not a stub. PR-F1's history
> cannot be rewritten: the committed dogfood baselines pin real commit SHAs, and
> rewriting PR-F1 would invalidate the `.agent/reconciliation/*` evidence. Evaluate
> the file at the stack tip, where it is complete. No change required.

---

## 3. Constraints for @generator (scope + authoring)

**Files @generator may change — exactly these three, nothing else:**
1. `.agent/product_spec_005.md` — `status: draft` → `active`, plus its own frontmatter
   `version` bump + one `change_log` entry recording the activation. **Do NOT edit the
   spec body or any other frontmatter field.** The 046 rationale lives in the feature
   entry's `description`, NOT in the spec (keep the spec stable while it is under review
   in PR #20).
2. `docs/planning/ROADMAP.md` — rewrite the single stale Sequencing-Recommendation
   sentence ("Track 2 is the recommended phase 005") to frame Track 2 as candidate
   scope for a subsequent phase; bump `version` + add one `change_log` entry.
3. `docs/planning/DEBT.md` — add rows **NDEBT-019 (Low)** and **NDEBT-020 (Medium)** to
   the Open table, bump the frontmatter `version` (currently `0.11.0`), and add any
   register-section prose per the house format.

**Forbidden (do NOT touch):**
- Any `.agent/evidence/*` file (immutable audit captures) — the NDEBT-019 remediation
  is deferred to methodology/02, not a hot-fix here.
- `.agent/evidence/045-release-readiness-checklist.md` — SHA-pinned by contract 045.
- Any `methodology/*` file (NDEBT-019 hardening is deferred).
- `NIZAM.json`, any `README`, `CHANGELOG.md`.

**Authoring rules (avoid every NDEBT-014 catalogued defect class):**
- Anti-vacuity companions must be **HEAD-anchored** (here: `git show HEAD^:…`), never
  working-tree-anchored, so they don't go mutually-exclusive post-implementation.
- Use backtick/code-span or word-boundary tokens, never bare substrings that false-pass
  on containing words.
- Do not rely on line-based section-scoped greps for phrases that could markdown-wrap.
- Assert the validator's **exit status**, not only the piped SUMMARY line (this is the
  NDEBT-019 lesson — feature 046's own sweep acceptance tests already model the fix:
  `out=$(bash tools/validate.sh 2>&1); rc=$?; test $rc -eq 0 && echo "$out" | …`).
- Both sweeps must stay green: **12/12 default**, **10/10 payload**. DEBT/ROADMAP/spec
  edits must respect their schemas and the C-checks.

**Landing convention:** one new commit at the stack tip; earlier PR threads resolved by
reference to the tip commit (stacked-PR convention).
