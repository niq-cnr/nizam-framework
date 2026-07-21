# Pilot evidence — feature 063 (scratch-consumer first pilot)

Execution of the ecosystem cycle against a real, non-self **scratch consumer** (a fresh
`git init` repo with `src/calc.py` + `README.md`, bootstrapped from the released `v0.8.0`
tag). The consumer repo is ephemeral (created under the session scratchpad, never pushed);
only these framework-side evidence snapshots are committed.

## Outcome

- **Adoption path held.** `bootstrap.sh` clone → inject → `--verify-only` PASS; and
  `tools/validate.sh --payload` was green (11/11) inside the consumer — the Track-4
  CWD-independence assertion holds against genuinely foreign content.
- **Preflight/Baseline carry self-fixture assumptions** (findings A, B below) — these are
  the two decisions captured in `docs/architecture/ADR-004-ecosystem-tool-consumer-readiness.md`.
- **Audit and Compare are artifact-based and ran cleanly** once the layout gap was
  bridged: `ecosystem_audit.py` assembled schema-valid `findings.json` + `report.md` for
  both runs, and `compare_ecosystem_baselines.py` produced a schema-valid delta
  (1 resolved, 1 persisting) — see `compare_delta.json`.

## Files

| File | What it shows | Debt |
|------|---------------|------|
| `A_preflight_framework_root_FAIL.json` | A clean Preflight against a real bootstrapped consumer is a hard **FAIL** (3 blocking findings): the injected `.nizam/` is flagged untracked and the `REQUIRED_REFERENCE_PATHS` resolve at repo-root, not under `.nizam/`. | NDEBT-027 (finding A) |
| `A_preflight_governance_root_workaround_PASS_WITH_EXCEPTIONS.json` | The same run once the payload prefix is declared tolerated — a hand-applied workaround for the missing governance-root option. | NDEBT-027 |
| `B_baseline_framework_ref_misanchored.json` | `framework_references[0].revision` = the consumer's HEAD (`81054aac…`), labelled "self-referential minimum-viable default" — **not** the framework pin. | NDEBT-028 (finding B) |
| `B_consumer_provenance_pin_v0.8.0.json` | The injected `.nizam/provenance.json` records the true framework pin `v0.8.0`, which the baseline should have anchored to. | NDEBT-028 |
| `audit_run1_report.md` | Rendered audit for run 1 (2 findings against the consumer's modest engineering state). | — |
| `compare_delta.json` | Compare-stage delta across the two runs: `F-cons-01` resolved (with closure evidence), `F-cons-02` persisting. Downstream stages are consumer-ready today. | — |
