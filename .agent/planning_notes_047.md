# Planning Note — Feature 047: PR-stack review response (round 2: PRs #22-#24)

**Status:** planning artifact (generator source material). Not a shipped file; not part
of feature 047's scope-of-change. Written by @planner 2026-07-18.

Feature 047 answers CodeRabbit's round-2 comments across PRs #22/#23/#24 (30 comments).
All fixes land as **one new commit at the stack tip** (stacked-PR convention); earlier
PR threads resolved by reference to the tip commit. **Do NOT implement fixes in this
file** — this is the brief for @generator's contract.

Verified context at triage: branch `agent/ecosystem-governance-cycle`, HEAD `6db8363`
(feature 046 close-out; deliverables `dd4e234`); DEBT.md `0.12.0`; ROADMAP `0.5.0`.
Both FIX defects AH-2-re-verified still present at HEAD `6db8363` (see §2). Next free
DEBT ids: NDEBT-021, NDEBT-022 (highest registered is NDEBT-020).

**PR #21:** CodeRabbit **skipped** the review ("Too many files! 291 files, 141 over the
limit of 150"; issue comment 5009595054, run `eeadf725`). Zero inline comments; none
coming. **No feature action** — orchestrator surfaces to the operator (optionally a
narrowed `coderabbit review --dir <path>` / `--base <closer-branch>` re-run).

---

## 1. Disposition summary (encode; do not re-triage)

| PR | FIX | DEBT | EXPLAIN | DUPLICATE | total |
|----|-----|------|---------|-----------|-------|
| 21 | 0 | 0 | 0 | 0 | 0 (review skipped) |
| 22 | 2 | 4 | 4 | 0 | 10 |
| 23 | 0 | 1 | 13 | 1 | 15 |
| 24 | 0 | 1 | 3 | 1 | 5 |
| **all** | **2** | **6** | **20** | **2** | **30** |

The 6 DEBT findings collapse to **2 registered rows**: the four PR-22 preflight items
(#6-#9) + the PR-23 untracked-rejection-probe note (#15) bundle into **NDEBT-021**; the
PR-24 CHANGELOG-date item (#29) is **carried by the orchestrator as a release-day note,
not a DEBT row** (see §5); the PR-23 taxonomy item (#11) is **NDEBT-022**.

---

## 2. FIX specifications (exact edits for @generator; scope = 2 files only)

### FIX 1 — `docs/planning/DEBT.md`, NDEBT-016 row (currently line 21)

AH-2 verified present at HEAD `6db8363`: the row's regex code-span contains three RAW
pipes, so GFM parses the row as 8 cells (MD056). Escape the three pipes as `\|` inside
the code-span; GFM renders `\|` as a literal `|` even inside a code span, restoring the
correct **5-cell** row with byte-identical *rendered* content.

- FROM (code-span): `` `(?:^|_)(?:neg|invalid)(?:_|\.)` ``
- TO (code-span):   `` `(?:^\|_)(?:neg\|invalid)(?:_\|\.)` ``

**Invariant:** the row MUST stay `| NDEBT-016 | 2026-07-17 | Low | … | … |` — severity
cell = `Low` in **position 3**. This keeps 045's committed release scan (`045-verify-18`,
counts open High/Critical rows via the severity cell) and 046's NDEBT-scan-style checks
green. No committed evidence pins DEBT.md bytes. Change **only** the three pipes; do not
reword the cell.

### FIX 2 — `tools/validate.sh` (DOC-ONLY, ZERO behavior change)

AH-2 verified present at HEAD `6db8363`. Two spots. **Do NOT touch line 319** — its
phrasing ("independently inspectable via a direct python3+jsonschema invocation") is
already correct (the refuted part of the finding).

Spot A — help text (lines ~108-109):
- FROM: `--target is the only mode under which files in tools/fixtures/ are ever read.`
- TO:   `Files in tools/fixtures/ are read only under --target and by the default sweep's C12 ecosystem-fixture check.`
  (rationale: false since C12 reads the three ecosystem fixture families in the DEFAULT
  sweep — `validate.sh:1593`.)

Spot B — comment (line ~1336):
- FROM: `(each fixture is already individually inspectable that way)`
- TO:   `(each fixture is directly inspectable via python3+jsonschema; --target currently misroutes these families -- NDEBT-015)`
  (rationale: the old comment implies `--target` works for these families; registered
  **NDEBT-015** records that all three ecosystem families misroute under `--target`.)

Fix now, **pre-tag**, because `tools/validate.sh` ships inside the v0.7.0 consumer
payload. Behavior invariance is asserted by both sweeps staying green (12/12 default,
10/10 payload), the e2e bootstrap staying green, and the doc-only diff guard (AT#11).

---

## 3. DEBT rows to register (both Low/Medium ONLY — protects 045-verify-18)

### NDEBT-021 (Low) — ecosystem_preflight.py minimum-CLI hardening backlog

> `tools/ecosystem_preflight.py` minimum-CLI hardening backlog (bundles CodeRabbit
> PR-22 items 3607425422/3607425426/3607425428/3607425430 + the PR-23 untracked-rejection
> probe note from 3607428783), deferred post-v0.7.0 alongside NDEBT-017: (1) it parses
> default porcelain-v1 output, so special-character/space/non-ASCII paths are C-quoted
> and fail literal tolerate-list matching — **fails CLOSED** (a tolerated odd path
> becomes blocking, never a silent pass); the naive `-z --untracked-files=all` fix would
> BREAK the directory-prefix exception semantics the committed 043/044 approved exception
> sets rely on (`.agent/evidence/<exec-id>/` tolerated as one porcelain dir entry), so the
> fix must be NUL-delimited parsing that preserves dir-prefix exceptions; (2) the
> required-reference check uses `os.path.exists` (accepts directories) and an unresolved
> HEAD yields baseline revision `"unknown"` rather than its own blocking finding —
> reachable only in an unborn-repo-with-gitignored-schemas setup; (3) explicit
> `--repo-root '.'` is indistinguishable from the default under `--self-fixture`
> (`default="."`); default it to `None`; (4) a reused `--output-dir` is not pre-cleaned,
> so mixed-verdict runs can leave contradictory `preflight.json`/`preflight.pending.json`/
> `baseline.json` leftovers; (5) add an executed untracked-not-tolerated -> FAIL probe to
> the hardening test scope. **Severity Low:** all fail-closed / pathological-input /
> unused-combination edges; no shipped invocation is affected (043/044 dogfood runs used
> fresh per-step dirs and ASCII paths).

### NDEBT-022 (Medium) — ecosystem/07 progress-comparison taxonomy + score semantics

> `ecosystem/07_progress_comparison.md` Sec 3's four-class transition taxonomy
> {new, resolved, reopened, stale} is **non-exhaustive**: it has no class for a finding
> that persists across both inputs with freshly re-confirmed evidence (F-audit044-ndebt-015,
> re-captured at revision `cba6422`), nor for a finding resolved *before* the first
> baseline (ndebt-002); and the delta score fields (`open_findings_before/after` = 3->5)
> count *recorded* findings, not open-only (which would be 2->4). The committed audit-044
> delta (`.agent/audits/audit-2026-07-17-cba6422/`) bridged both **transparently** via
> `unchanged_facts` + explicit notes (report.md:16-23,46-57) with correct, fully-cited +2
> net movement — **nothing hidden or distorted**, so the immutable committed artifact needs
> NO change. Fix path: amend the LIVE `ecosystem/07` protocol doc in a future phase with a
> persisting/re-confirmed class, a first-comparison (pre-window-resolved) rule, and exact
> open-vs-recorded score-count semantics before the next audit. **Severity Medium** (not
> Low): a spec-completeness defect that will recur in every future comparison; **not**
> High (nothing concealed, movement correct and traceable, and DEBT Open must stay free of
> High/Critical for 045-verify-18).

**Also:** bump the DEBT.md frontmatter `version` from `0.12.0`. New rows must carry NO
raw pipes in any cell (the very defect FIX 1 corrects) — escape any `|` as `\|`.

---

## 4. Ready-to-post PR reply texts (§replies — 22 total: 20 EXPLAIN + 2 DUPLICATE)

The orchestrator posts these verbatim as replies on the corresponding PR #22/#23/#24
review threads. No repository change accompanies them. Each is grounded in the triage
evidence (comment id, file, and the corroborating commit/line cited).

### PR #22

**R1 — id 3607425408 · `.agent/evidence/041-verify-16.txt:1` (EXPLAIN)**
> This is feature 041's point-in-time capture: C12 landed in feature 042; at 041's commit
> `78d32c3` the sweep was C1-C11, so 11 was the correct expected count. The current-state
> 12-pass evidence you're asking for already exists in `.agent/evidence/042/verification.txt`
> (lines 26/45) and was re-confirmed by the 045 release-package verification. Committed
> evidence captures are immutable point-in-time records here.

**R2 — id 3607425412 · `.agent/evidence/042-verify-01.txt:1` (EXPLAIN)**
> Anti-vacuity companions here are deliberately HEAD-anchored and captured pre-commit
> (house rule, registered as NDEBT-014 class 1 after a working-tree-anchored variant failed
> in feature 038): at capture time HEAD was the pre-implementation commit, so
> `git show HEAD:` proved the check's target genuinely absent. These captures are immutable
> point-in-time records — post-merge irreproducibility is expected and applies to every
> anti-vacuity companion in the series.

**R3 — id 3607425414 · `.agent/evidence/042-verify-{13,14,15,16}.txt:1` (EXPLAIN)**
> For this validator, last-line summary matching is equivalent to exit-status checking:
> validate.sh's exit code is literally `[ "${failed}" -eq 0 ]` (line 1599), and a run that
> dies early can't emit the SUMMARY as its final line. verify-13's purpose is solely
> C12-absence under `--target`. The belt-and-braces rc capture you suggest was in fact
> adopted in later evidence (`044-verify-22`). These committed captures are immutable
> point-in-time records.

**R4 — id 3607425415 · `.agent/evidence/042-verify-17.txt:1` (EXPLAIN, refuted)**
> This is a non-goal guard, not an allowlist guard: the listed paths are contract 042's
> forbidden set (see `.agent/contracts/042.json` non_goals, which enumerates exactly these
> paths as must-not-modify). `git diff --quiet HEAD -- <forbidden>` failing when any of them
> changed is precisely the intended semantics. Allow-list scope enforcement was handled
> separately (Mode B whole-diff review against the contract's scope).

### PR #23

**R12 — id 3607428771 · `delta.json:63-68` (EXPLAIN, burden inverted)**
> Sec 5 of `ecosystem/07` puts the burden the other way: a finding is flagged stale unless
> there is fresh confirmation provably captured at or after the later execution's anchor.
> Date-only granularity can't prove at-or-after `12:54:09Z`, so `stale` is the mandated
> fail-safe classification, not a claim that needs a pre-baseline proof. Recording it stale
> is strictly conservative — the alternative is silently reusing possibly-outdated evidence,
> which the rule exists to prevent. The artifact is an immutable committed record.

**R13 — id 3607428775 · `.agent/evidence/043-verify-02.txt:1-10` (EXPLAIN)**
> verify-02's scope is the pending-step mechanics; the field-shape assertions live in the
> companions that ran against the real dogfood artifacts: `043-verify-12` loads the pending
> file and set-compares its exceptions against the approved verdict, and `043-verify-11`
> schema-validates the approved verdict incl. anti-placeholder operator checks. The pending
> document has exactly one writer (`ecosystem_preflight.py` lines 451-460). Committed
> evidence is immutable here.

**R14 — id 3607428779 · `.agent/evidence/043-verify-05.txt:11-20` (EXPLAIN)**
> The capture disambiguates itself: the recorded traceback is the exception-set assertion
> naming `999-drift.json`, not a load failure, and the T1 arm — the same two preflight
> invocations without the drift file — succeeded in the same run, proving the tool executed
> correctly. So DRIFT_CAUGHT=1 was earned for the right reason at capture time. The file is
> an immutable point-in-time record; the tightening you suggest applies to future evidence
> authoring.

**R15 — id 3607428783 · `.agent/evidence/043-verify-08.txt:1` (EXPLAIN)**
> verify-08's role was documenting the tolerate-list decision procedure, not testing the
> CLI; the CLI's real blocking behavior is exercised by the committed dogfood run itself —
> including a genuine exit-1 FAIL on the first approved attempt (recorded as NDEBT-018) —
> and by verify-02/05's real invocations. Evidence files are immutable; we've registered an
> explicit untracked-rejection probe for the post-release preflight-hardening scope
> (NDEBT-021).

**R16 — id 3607428785 · `.agent/evidence/043-verify-{11,12,13}.txt` (EXPLAIN, refuted at capture)**
> At 043's capture time exactly one dogfood directory existed in the tree (`git ls-tree` at
> `6d7a47b` shows only `dogfood-2026-07-17-28c8253` — the second execution landed with
> feature 044), so the selection was deterministic, and verify-13 pins the loaded baseline
> to the live `git rev-parse HEAD`. These are immutable point-in-time captures; the 044
> evidence generation switched to ID-pinned-by-exclusion selection.

**R17 — id 3607428788 · `043-verify-{14,15}` + `044-verify-{23,25,26,27}` (EXPLAIN, cross-ref R16)**
> The 044 checks don't pick "newest": they pin the first execution ID literally and select
> the second by exclusion, which is unique at the capture-time cardinality of exactly two
> directories; and `044-verify-27` cross-binds `delta.compared_baselines.before/after`
> revisions to both real baseline files, which is the direct assertion against run-mixing.
> The 043 files ran when only one directory existed (see the sibling comment). Immutable
> captures.

**R18 — id 3607428794 · `.agent/evidence/043-verify-17.txt:1` (EXPLAIN)**
> Point-in-time non-goal guard in the house form of its era; untracked-aware checking ran in
> the companion `043-verify-19` for the `.agent` surfaces, and Mode B's whole-diff review of
> the committed tree confirms nothing out-of-scope landed, so the theoretical evasion masked
> nothing. The raw-git-diff-vs-`vlib_scope_guard` form gap is already registered debt
> (NDEBT-014 item 2, guard-form harmonization). Evidence files are immutable.

**R19 — id 3607428797 · `.agent/evidence/043-verify-19.txt:1` (EXPLAIN)**
> The untracked arm of this guard does scan `.agent/evidence` and `.agent/reconciliation`;
> the tracked-diff arm intentionally mirrors the contracts-025/028 precedent (qa+contracts),
> because tracked modifications anywhere are caught by Mode B's whole-tree `git diff HEAD`
> review against the contract's scope — which ran for 043. The capture is immutable;
> widening the tracked arm in future guards falls under registered NDEBT-014 item 2.

**R20 — id 3607428798 · `.agent/evidence/044-verify-01.txt:1` (EXPLAIN, refuted at capture)**
> Empirically the single directory at the capture HEAD was 043's (`git ls-tree` at
> `6d7a47b`: only `dogfood-2026-07-17-28c8253`; no `.agent/audits` path), and every consumer
> check that depends on identity (`044-verify-23/25/26/27`) pins that ID literally. The
> count-based anti-vacuity check was therefore sound over the real tree it ran against, and
> committed evidence captures are immutable — we can't take the committable suggestion.

**R21 — id 3607428809 · `.agent/evidence/044-verify-02.txt:1-4` (EXPLAIN, cross-ref R14)**
> The capture's own output shows the isolated run executed correctly (pending verdict, exit
> 2, artifact assertions), and a failed `cd` would have left `dogfood-verify2-pending`
> artifacts in the real repo that the same feature's immutability/scope guards and Mode B
> whole-diff review would have caught — the committed tree has none. Immutable point-in-time
> record; the `&&`-chaining point is taken for future evidence authoring (same class as the
> 043-verify-05 comment).

**R23 — id 3607428816 · `.agent/evidence/044-verify-22.txt:1` (EXPLAIN)**
> The gate is rc==0 plus "0 failed" on the tool's own final SUMMARY line — validate.sh's
> exit code is literally `[ failed -eq 0 ]`, and a truncated run can't satisfy both. The
> exact 12-check count is pinned in the 042 consolidated verification and re-verified in the
> 045 release package; 044's capture deliberately asserted the invariant (nothing failed,
> run complete) rather than re-pinning a count owned by another feature's surface. Immutable
> point-in-time record.

**R24 — id 3607428819 · `.agent/evidence/044-verify-24.txt:5-12` (EXPLAIN, refuted empirically)**
> Empirically refuted for the artifact this ran against: `findings.json` holds exactly five
> findings with unique IDs, and the check already pinned all five expected IDs with exact
> confidence and status values. The residual you describe (extras/duplicates) did not exist,
> so the capture's verdict is sound. Committed evidence is immutable; exact-set assertions
> are a fair authoring note for future audits.

**R25 — id 3607428820 · `.agent/run_state.json:4` (EXPLAIN, resolved at tip)**
> Resolved at the stack tip: commit `ada3b9c` (PR #24) advances run_state to
> `current_feature` 045 / `status` awaiting_human_gate — PR #23's diff shows the state as of
> 044's close, and under our stacked-PR fix-at-tip convention the advance rides the next
> slice. `run_state.json` is orchestrator-owned with append-only history, so no change is
> made on this slice.

### PR #24

**R26 — id 3607421285 · `.agent/evidence/045-verify-03.txt:1-3` (EXPLAIN)**
> The section-scoped check exists: `045-verify-04/05` extract the `[0.7.0]` span with awk
> and pin seven content tokens plus the C1-C12 and version-bump mentions inside that span
> specifically; verify-03 is the deliberately coarse smoke layer above them. Committed
> evidence is immutable, and the substantive assertion you want is already in the same
> evidence set.

**R27 — id 3607421288 · `.agent/evidence/045-verify-13.txt:1` (EXPLAIN)**
> The `.agent` exclusion is `vlib_scope_guard`'s documented contract (`verify_lib.sh` line
> 106): it guards the product tree, while `.agent` surfaces are governed by their own
> checks — `045-verify-15` pins `run_state.json` untouched, and the feature's own `.agent`
> lifecycle artifacts are contract deliverables reviewed by Mode B's whole-diff gate. The
> `.agent/evidence/045` argument is a redundant no-op, not a hole. The capture is immutable;
> we may note the ignored-allowlist-entry pitfall in the NDEBT-014 verification-authoring
> catalogue.

**R30 — id 3607421292 · `README.md:22-24,42` (EXPLAIN)**
> This is the release-package convention: the README inside the v0.7.0 tag must pin v0.7.0
> (the previous release did the same), and re-pinning is an explicit contract-045
> deliverable asserted by committed evidence (`045-verify-12`). The PR is a draft that only
> merges as part of the H-FRAMEWORK-RELEASE human step, in which merge and tag publication
> are one operator action — so there is no published state where these links dangle beyond
> that step itself. Pinning the old tag would instead ship a v0.7.0 whose bootstrap fetches
> v0.6.0.

### Duplicates (2)

**R22-DUP — id 3607428813 · `.agent/evidence/044-verify-19.txt:1` (DUPLICATE of R18 / id 3607428794)**
> Same finding class and resolution as `043-verify-17` (see that thread): this is the
> non-goal forbidden-path guard in tracked-diff form; the committed 044 tree (`422a074`)
> passed Mode B's whole-diff review, so nothing out-of-scope was masked, and the
> guard-form harmonization is already registered as NDEBT-014 item 2. Immutable capture.

**R28-DUP — id 3607421290 · `.agent/evidence/045-verify-16.txt:1-3` (DUPLICATE of R3 / id 3607425414)**
> Same exit-status-masking class as the `042-verify-14` thread (see there): validate.sh
> exits `[ failed -eq 0 ]` (line 1599), so `tail -1 | grep -Eqx '... 0 failed'` on its final
> SUMMARY line is equivalent to asserting exit 0, and a dying run can't print the SUMMARY
> last. The explicit-rc form exists at `044-verify-22`. Immutable capture.

---

## 5. Non-feature carries (orchestrator handles; NOT in 047's diff)

- **CHANGELOG `[0.7.0] - 2026-07-17` date (id 3607421291, PR-24 item #29):** valid but NOT
  fixed here. The v0.7.0 tag is gated on H-FRAMEWORK-RELEASE, so the heading date will
  predate publication. Carry it as a **release-day note to the operator**: before pushing
  the tag, true-up the `## [0.7.0] - <date>` heading to the actual publication date.
  Safe because `release.yml`'s extraction is date-agnostic (prefix-match `index($0, "## ["
  ver "]") == 1`, release.yml:83-88); the byte-pinned 045 checklist does not pin CHANGELOG
  bytes. **Do NOT edit CHANGELOG.md in feature 047.**
- **PR #21:** review skipped (291 files > 150). No feature action; orchestrator decides on a
  narrowed re-run.

---

## 6. Constraints for @generator

**Files @generator may change — exactly these two, nothing else:**
1. `docs/planning/DEBT.md` — FIX 1 (escape the three NDEBT-016 pipes; severity stays Low in
   cell 3), add NDEBT-021 (Low) + NDEBT-022 (Medium), bump frontmatter `version` from
   `0.12.0`. New rows: no raw pipes in any cell.
2. `tools/validate.sh` — FIX 2 spots A + B only; **do NOT touch line 319**; ZERO behavior
   change (comments/help-text bytes only).

**Forbidden (do NOT touch):** any `.agent/evidence/*` (immutable); the SHA-pinned
`.agent/evidence/045-release-readiness-checklist.md` and the release-notes hash;
`.agent/run_state.json`; `CHANGELOG.md`; `README.md`; `NIZAM.json`;
`tools/ecosystem_preflight.py`; any `ecosystem/*` doc; any tag creation.

**Authoring rules (avoid every NDEBT-014 catalogued defect class):**
- Anti-vacuity companions must be **HEAD^-anchored** (`git show HEAD^:…`), never
  working-tree-anchored.
- Content checks that could markdown-wrap must be **whitespace-collapsed** before matching
  (the 047 ATs use `' '.join(text.split())`), never line-based greps for multi-line phrases.
- Use structured parses or `grep -F` fixed strings / code-span tokens, never bare substrings
  that false-pass on containing words.
- Assert the validator's **exit status**, not only the piped SUMMARY line (NDEBT-019 lesson;
  the 047 sweep ATs already model it).
- The real payload SUMMARY literal carries the `(payload mode)` qualifier:
  `SUMMARY (payload mode): 10 passed, 0 failed` (per the feature-046 correction).

**Landing / timing convention:** one new commit at the stack tip; earlier PR threads
resolved by reference to the tip commit. The tip-diff confinement AT (AT#17) is valid ONLY
at the deliverable tip commit, BEFORE the lifecycle close-out commit advances HEAD — the
standing scope proof is contract 047's `vlib_scope_guard` entry (feature-046
`head_caret_timing_note` precedent). 047 must LAND BEFORE the operator executes
H-FRAMEWORK-RELEASE (validate.sh ships in the v0.7.0 payload).
