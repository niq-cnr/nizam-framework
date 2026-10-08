# Re-check of the partial backlog DAG (operator instruction: "reuse the partial DAG only after re-checking it.")

Planner record, 2026-10-08.

- **Subject.** The stopped agent's unreviewed draft in the worktree
  `nizam-framework-wt-reconcile` (branch `chore/backlog-reconciliation` at `9edd5d0`).
  It contained:
  - `docs/planning/backlog_dag.json` (43 packets, `generated_at` 2026-10-08T11:22:11Z,
    `base_commit` already set to `02b02c6`);
  - `.agent/evidence/backlog-reconciliation-2026-10-08/tools/validate_backlog_dag.py`;
  - `.agent/evidence/backlog-reconciliation-2026-10-08/tools/a02_premise_probes.py`;
  - seven `baseline/*.txt` captures taken at `9edd5d0`.
- **The worktree was read only.** Nothing in it was edited.
- **Method.** All three files were read in full. Both scripts were re-run, unmodified,
  against the current tree: a scratch clone at `02b02c6`, holding the Orchestrator's
  current `.agent/run_state.json` and the draft files at their draft paths. Every
  packet was then checked:
  - against `schema/work-packet.schema.json`;
  - for cycles and dangling references;
  - for whether every cited fact and file:line is true at `02b02c6`;
  - for whether its status reflects post-#64 reality.

  The scratch clone is session-local, so these two runs cannot be replayed verbatim from
  this repository. The draft remains in the worktree for replay. The corrected scripts'
  replayable runs are `dag_validation.txt` and `a02_premise_probes.txt` (`04` §5 shape).

## 1. The draft validator, re-run unmodified (exit 1)

```text
PASS V1 wrapper (plan_status=candidate, base_commit, packets)
PASS V2 43 packets validate against schema/work-packet.schema.json
PASS V3 reconciliation fields (authority, prerequisites x4, status, lane, owner, estimates)
PASS V4 unique packet ids (43)
PASS V5a no dangling references
PASS V5b consumed_by is the exact inverse of depends_on
PASS V6 acyclic (depends_on + serialize_after)
PASS V7 candidate/activated separation (allocated ids, manifest phases, declared edge changes)
     declared PROPOSED canonical edge change: 101 += ['099'] (PROPOSED (A02-AMEND; awaiting authorization with H-PHASE-014))
PASS V8a every alias A00-A16 mapped to a packet and a disposition
FAIL V8b T01-T19 + NIP cases 1-13 mapped (owners exist; honest statuses with evidence) -- T06: non-pending status without existing evidence; T18: non-pending status without existing evidence
FAIL V9 shared-file writers are totally ordered -- docs/planning/ROADMAP.md: A03-RT || F102
Traceback (most recent call last):
  ...
  File ".../validate_backlog_dag.py", line 252, in main
    md = MD.read_text(encoding="utf-8")
FileNotFoundError: [Errno 2] No such file or directory: 'docs/planning/backlog_reconciliation.md'
EXIT:1
```

(The traceback's absolute session paths are elided.)

**Findings:**

- **Schema:** all 43 packets validated (V2).
- **Structure:** no cycles (V6) and no dangling references (V5).
- **V8b:** T06 and T18 cited `a02_premise_probes.txt`, which was never captured.
- **V9:** two writers of `docs/planning/ROADMAP.md` were unordered.
- **V10:** crashed instead of failing.
- **V11:** never ran. Its premise ("no existing file modified") is in any case
  incompatible with the approved amendment.

## 2. The draft probes, re-run unmodified (46/48, exit 1)

All rows of P1–P4, P6 and P7 matched. Two P5 rows did not:

```text
BAD  P5   OLD  real tree (v1.4.0 exists) -> can never pass again                     rc=0 want=1 exc=-
BAD  P5   NEW  v1.4.0 new since baseline; decision only in R3's unmerged run_state   rc=0 want=1 exc=-
PROBES: 46/48 rows matched expectation; scratch removed
MISMATCH: P5 OLD  real tree (v1.4.0 exists) -> can never pass again
MISMATCH: P5 NEW  v1.4.0 new since baseline; decision only in R3's unmerged run_state
EXIT:1
```

Both are stale premises from before PR #64:

1. **The "OLD" row read the current 102 AT4.** D1 had already retargeted it from
   `v1.4.0` to `v1.5.0`, so it passes.
2. **The second row assumed an unmerged release decision.** The H-FRAMEWORK-RELEASE
   decision for v1.4.0 is now merged in run_state, so the draft's "authorized new tag"
   logic accepted it.

That logic is itself out of scope. The approved amendment is "assert no tag was
created during the phase". It does not mean "no unauthorized tag".

## 3. Citations checked at `02b02c6` (all true)

| Cited by the draft | Verified content at `02b02c6` |
|---|---|
| `ROADMAP.md:768` | The single "Latest released tag: v1.4.0" disposition line. |
| `ROADMAP.md:815` | "Open debt (current, at DEBT.md v0.40.0): two rows remain Open". Stale against 8 Open rows; that is NDEBT-044 (e). |
| `ROADMAP.md:261,264` | "expected v1.5.0" / "expected v1.6.0". |
| `product_spec_014.md:30` and `:100` | The run_state "untouched" wording. |
| `product_spec_014.md:86` | ".github/ is untouched". |
| `product_spec_014.md:139-146` | NDEBT-034 deferred; open debt carried. |
| `product_spec_014.md:154-156` | H-PHASE-014 OUTSTANDING. |
| `product_spec_014.md:165-166` | No release prepared. |
| `methodology/00_planning.md:186-193` and `:195-201` | Orchestrator-registrable vs Planner-routed amendments. |
| `operator_gates.md:134` | The H-PHASE-NNN row. |
| `standard/definition_of_done.md:160,211` | Three-job statements. |
| `standard/AGF.md:40` | The Evaluator row, without the Loop-1 contract review. |
| `standard/AGF.md:129-136` | Orchestrator-owned coordination fields. |
| `methodology/03_circuit_breaker.md:51-57` | The strategy ladder. |
| `docs/nips/NIP-0003-live-runtime-sessions.md:485` | "No case is claimed working until its live proof passes in CI." |
| `NIP-0003:489-491` | The provisional ids are confirmed at phase-015 planning "in case phase 014 consumes more ids". |
| `NIP-0003:494-495` | The ×2.3 weight, 5,400. |
| `NIP-0003:504,526` | "expected v1.4.0" / "expected v1.5.0". |
| `NIP-0003:512-513` | SBCL "not currently installed". |

One citation was corrected:

- **`methodology/01_execution.md:38-39`** (the draft's reference) is narrower than the
  Evaluator contract-review block, which spans lines 36-40. Corrected in `A04a`.

Two re-verified facts contradict the draft or the NIP:

- **SBCL is installed.** `/usr/bin/sbcl`, SBCL 2.2.9.debian, contradicting
  NIP-0003:512-513. The draft already noted this.
- **The fixture counts hold.** NDEBT-042 says 79 top-level fixture files and 67 nested
  ones, with `-maxdepth 1` at `tools/fixtures_self_test.sh:949`. Both are true.

## 4. Kept, corrected, dropped

**Kept as drafted** (content re-verified):

- `A00` (now also citing this record), `A01`, `A03-SCOPE`, `R3` (complete, PR #64);
- `A03-WA-DRAFT`, `A03-WA-FINAL`;
- `PLAN-016` (environment reason updated: SBCL re-verified);
- `A09`, `A10`, `A11-D`, `A11-CI`, `A04b`, `A14`, `A15`, `A16-WA`;
- the lanes;
- 30 of the 32 verification-matrix rows, as statuses. The owners are re-pointed.

**Corrected:**

| Item | Correction |
|------|------------|
| `A02-AMEND` | pending/blocked → **complete**. It is applied by this package under the H-PHASE-014 event (11:21:14Z), with an explicit allowed-path list; it no longer serializes after the dropped `A08-044E`. |
| `ACT-014` | pending/blocked → **in_progress**. The canonical phase document and the manifest are written; the Orchestrator's run_state write is outstanding. Its scope now includes `.agent/evidence/phase-014-activation/`, where the baselines are captured. |
| `F099`, `F100`, `F101`, `F102` | Rebuilt to **mirror** `.agent/feature_list_014.json`: dependencies (101 → 099 applied; 102 → 103–109), status, canonical weighted estimates, and the hardened tests by reference. `F100`'s authority is now `blocked-on-H-CONSUMER-UPGRADE`. Its environment item is the undesignated member set. |
| `A05`, `A06`, `A07` | Re-identified as activated `F103`, `F104`, `F105`, with feature ids allocated from the highest id across all feature lists (102). |
| `NIP3-103`..`NIP3-113` | Renamed `NIP3-110`..`NIP3-120`; their provisional ids shift by seven because phase 014 allocated 103–109. `NIP3-113` loses the NDEBT-044 (d) fix to F108. `NIP3-116` now depends on `F104`/`F105` and reuses the claim map. |
| `A03-RT` | Authority `authorized` → `proposal`: the operator forbade editing the NIP in this package. It now serializes after `F102` (fixing V9). Its objective gains the newly stale premises: the id shift, claim-map reuse, four → five jobs, isolation-flag polarity, and the spec citation. |
| `PLAN-NEXT` | Drops NDEBT-026/037/044; ids are "provisionally 110". |
| `PLAN-WA` | Serializes after `NIP3-114`. |
| `PLAN-016` | No longer serializes after `A16-WA` (that hard-ordered phase 016 behind the entire WA programme, contradicting PLAN-WA's "open question"); it serializes after `PLAN-WA` (planning order only). |
| `A09` | Serializes after `NIP3-120`. This is the candidate order for the `tools/validate.sh` writers, recorded as an open, non-blocking question. |
| `estimate_weighting` | The basis is re-anchored to NIP-0003:494-495 (2330 → 5400) and phase-013's realized 2.89×. |
| `verification_matrix` T05 | Evidence was the debt row describing the problem. It is now the feature-093 QA adjudication: one manual positive, no mechanized negative control. |
| `verification_matrix` T06/T18 | Evidence captured. |
| `verification_matrix` T08 | Adds the 02b02c6 re-check. |
| Wrapper | `proposed_canonical_edge_changes` (now empty) is superseded by `applied_canonical_edge_changes`. New `activated_phase` block. `generated_at` re-read from the clock. |

**Dropped:**

| Packet | Disposition |
|--------|-------------|
| `A08-044E` | Folded into F102 AT5, the phase-close roll. A standalone ledger edit would go stale again as the tranche resolves rows. |
| `A08-026`, `A08-037`, `A08-044` | Superseded by activated F109, F108, and F106/F107/F108. |

**Scripts:**

- **`tools/validate_backlog_dag.py`** (revision 2):
  - V7 now requires a canonical mirror, plus the provisional-id collision check;
  - V10 fails gracefully;
  - V11 is path confinement;
  - V12 (the canonical plan) and V13 (the spec-drift gate and budget sum) are new;
  - the reports gain an in-progress list and the phase-014 single-lane order.
  - a new companion, `tools/dag_negative_controls.py`, proves the validator is not
    vacuous: ten mutated DAGs (a cycle, a dangling reference, a dropped canonical
    edge, a missing feature, spec drift, unordered writers, an unmapped alias, a
    provisional-id collision, a dishonest matrix status) each fail their targeted
    check, and the unmutated copy passes (`dag_negative_controls.txt`).
- **`tools/a02_premise_probes.py`** (revision 2):
  - it probes the acceptance tests as written in the feature list, and the OLD forms
    from git (`02b02c6`; the pre-D1 form from `9edd5d0`);
  - P5 is rewritten to the approved phase-scoped "no new tag" semantics;
  - P8–P11 are new: the dossier, the ROADMAP roll, the derived job-count, and the
    fail-closed scratch helper;
  - 88/88 rows.

**Baselines:**

- `baseline/*.txt` is copied verbatim from the draft (byte-identical; `9edd5d0`).
- `recheck-02b02c6/*.txt` holds fresh captures in a clean clone at `02b02c6`.

## 5. Validator round 1 (2026-10-08): script revisions

- **`tools/a02_premise_probes.py` → revision 3.**
  - Part A sweeps every acceptance test in `.agent/feature_list_014.json` on the
    pre-implementation tree. Each test has a declared outcome: fail, fail-mut
    (mutation precondition held), inapplicable, guard or gate. Coverage is asserted
    exactly against the list.
  - Part B adds simulations for 099, 103–109, 101 and 102: P12–P20, including the
    108 mutation controls and the 102 hash-pin controls.
- **`tools/validate_backlog_dag.py`.** The ready set now also requires the lane's
  `serialize_after` predecessors to be complete, and the dependency-eligible-but-
  lane-ordered packets are reported separately.
- **ACT-014 is complete.** The run_state position landed at 12:18:31Z.
- **`tools/at_compile_check.py` is new.** It runs `bash -n` on every acceptance test
  and `compile()` on every embedded Python body.

## 6. Evaluator follow-up (2026-10-08): V11 exact Orchestrator paths

V11 rejected the untracked Validator verdict `.agent/validator/phase-014-activation.json`
(Evaluator units 09b, 09c and 09e). That file is now in V11's exact Orchestrator-owned set, beside
`.agent/run_state.json`. It is compared by equality, never as a `.agent/validator/` prefix. The
validator gains a probe-only `--git-status PATH` input. `dag_negative_controls.py` gains four V11
controls, and the unmutated copy passes again: 14/14.
