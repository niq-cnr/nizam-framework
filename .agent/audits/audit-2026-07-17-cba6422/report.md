# Dogfood Framework Audit + Delta Report

Audit id: `audit-2026-07-17-cba6422`. Compares baseline #1 (execution-id
`dogfood-2026-07-17-28c8253`, revision `e73cd04bad78c696c815bf253fb627a93f20c9c0`)
against baseline #2 (execution-id `dogfood-2026-07-17-6d7a47b`, revision
`cba6422c01ee024cd3c597adaed977590f6373ef`), per `ecosystem/03_engineering_audit.md`
(Audit) and `ecosystem/07_progress_comparison.md` (Compare). Full machine-readable
detail lives in `findings.json` and `delta.json`, referenced by path below; no raw
evidence is re-pasted inline (per the Evidence Capture Convention).

## Findings Summary (see `findings.json`)

Five real findings, sourced from the live DEBT register and this run's own dogfood
evidence:

- `F-audit044-ndebt-015` -- open, Confirmed. `tools/validate.sh --target` misroutes
  all three ecosystem fixture families (live-reproduced this run).
- `F-audit044-ndebt-002` -- **resolved**, Confirmed, with real closure evidence
  (commits `bcb02d2`, `0840094`). NDEBT-002 was previously resolved (pre-baseline-1) -- it closed on 2026-07-10, well before baseline #1 was ever
  captured (2026-07-17) -- so it is recorded here as a resolved finding but is
  **never** classified in `delta.json`'s cross-execution `resolved` transition
  bucket (see Delta Summary below).
- `F-audit044-ndebt-016` -- open, Suspected. Flagged `stale` in the delta (evidence
  predates baseline #2's own capture; deliberately not re-verified this run).
- `F-audit044-ndebt-017` -- open, Confirmed. Flagged `new` in the delta (absent from
  DEBT.md at baseline #1's pinned revision, present at baseline #2's).
- `F-audit044-ndebt-018` -- open, Confirmed. Flagged `new` in the delta (the same
  dogfood self-reference friction class, independently re-observed live in this
  run's own pending/approved preflight steps).

## Delta Summary (see `delta.json`)

- **Unchanged facts (stable):** `dependency_references[0].revision` (python3
  3.14.4, identical across both baselines); NDEBT-002 and NDEBT-016's continued,
  unchanged presence in `docs/planning/DEBT.md` at both revisions.
- **Changed facts (deliberate):** `repository_references[0].revision` /
  `framework_references[0].revision` -- baseline #1's
  `e73cd04bad78c696c815bf253fb627a93f20c9c0` versus baseline #2's
  `cba6422c01ee024cd3c597adaed977590f6373ef` -- a real, honestly-detected change
  (the passage of real framework commits between the two dogfood executions), read
  from each baseline artifact's own declared `revision` field, never derived by
  parsing either execution-id label.
- **new:** `F-audit044-ndebt-017`, `F-audit044-ndebt-018` (both genuinely absent
  from DEBT.md at baseline #1's pinned revision `e73cd04...`, present at baseline
  #2's).
- **resolved:** honestly empty. Nothing genuinely transitioned open-to-resolved
  *within this comparison's own window* -- NDEBT-002 is previously resolved (pre-baseline-1), not an in-window closure (see Findings Summary above and
  `design_notes.resolved_class_is_pre_baseline1_only` in contract 044).
- **reopened:** honestly empty -- this is the framework's first-ever comparison, so
  there is no prior comparison's resolved-classification for anything to reopen
  against.
- **stale:** `F-audit044-ndebt-016` (evidence dated 2026-07-17, predating baseline
  #2's own `captured_at` of 2026-07-17T12:54:09Z, with no fresh re-confirmation
  captured this run).
- **Score movement:** open-findings count moved from 3 (baseline-#1-era reference
  point) to 5 (this audit's own findings.json at baseline #2), traceable entirely
  to the two `new` findings cited above (`score_movement.cited_findings`).

## Forward Prioritization

`F-audit044-ndebt-015` (the `--target` misrouting) remains the highest-value next
self-compliance candidate, corroborating `docs/planning/ROADMAP.md` Track 2 item
1's existing NDEBT-007 pairing.
