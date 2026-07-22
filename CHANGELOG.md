# Changelog

All notable changes to the Nizam framework are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`schema/ecosystem_membership.schema.json` — the required, validated membership registry**
  (phase 010 feature 075; `NDEBT-031`; NIP-0002 Stage 3). The artifact that sets `n` for the 0–n
  spectrum: a JSON schema validating a consumer's ecosystem-membership registry — the four scope
  lists (`in_scope`/`incubating`/`reference_archive`/`out_of_scope`) as arrays of entries, every
  entry with an identifying `name`, and `out_of_scope` entries recording a `reason`. The
  **exactly-one-list invariant** (no `name` in two lists) is a relational cross-array constraint
  JSON Schema cannot express, so `tools/validate.sh` **C12** enforces it in code (mirroring the
  `ecosystem_baseline` same-repo-revision split), wired at both entry points (full-sweep +
  `--target` router, discriminated by ≥2 of the four scope-list keys) with a positive fixture, a
  schema-invalid negative, and a schema-valid-but-multilist negative caught by the code check.
  `registry/scope_definition_patterns.md` → v0.3.0 is **promoted from a draft pattern to a
  required, schema-backed active artifact**; the schema is registered in `NIZAM.json` and
  `schema/README.md` (v0.9.0). The multi-repo *tooling* that iterates this registry is features
  076–077.

- **Phase 010 proposed** — `.agent/product_spec_010.md` (status draft) and
  `.agent/feature_list_010.json` (features 075–079, DAG-validated acyclic, root {075}, est 1160
  lines) propose **0–n Project Spectrum, Stage 3: The n-case (Multi-Repo Tooling)**, the
  realization of `NIP-0002` Stage 3. Scope: a JSON schema for an ecosystem-membership registry
  promoting `registry/scope_definition_patterns.md` from a draft pattern to a required, validated
  artifact that sets `n` (`NDEBT-031`); multi-repo iteration over the `in_scope` set of repo-roots;
  cross-repo aggregation + a common-framework-pin consistency check; hermetic n-case coverage; then
  a pilot proving the n-case against a scratch multi-repo ecosystem. NIP-0002 Stage 4 (the `04`/`05`
  coordination protocols, activating the reserved `H-PLANNING-AUTHORITY` / `H-TRAIN-ENTRY` gates),
  the release cut carrying the whole loop (`NDEBT-029`), and a real non-scratch multi-repo pilot are
  carried as phase-011 candidate scope. `docs/planning/ROADMAP.md` (v0.23.0) and
  `docs/planning/manifest.json` record the proposal (pending/proposed); it awaits activation gate
  `H-PHASE-010` and is not yet active (`.agent/run_state.json` untouched).

- **Phase 009 (0–n Project Spectrum, Stage 2: Greenfield Genesis) complete** (feature 074;
  `NDEBT-030`). The 0-case was piloted end-to-end against a scratch greenfield project stood up
  **from nothing** by `bootstrap.sh --genesis` using the fixed tools (070–073): genesis created
  the project (`git init` + deterministic scaffold + injected `.nizam/` with `tag` + `resolved_sha`
  provenance), and Preflight returned `PASS_WITH_EXCEPTIONS` with the injected `.nizam/` the single
  expected exception — the same clean outcome ADR-004 gave the count-1 case, with no hand-applied
  workaround. Evidence under `.agent/evidence/pilot-074/`; `H-CONSUMER-UPGRADE` exercised a third
  time (a pre-release/branch pilot). `manifest.json` phase-009 → complete. The phase-010 candidate
  scope (NIP-0002 Stages 3–4) is validated by the pilot (the n-case `NDEBT-031` builds on the
  `incubating` partition this phase populated). A real, non-scratch greenfield pilot and a released
  tag carrying the genesis capability (`NDEBT-029`) remain outstanding.

- **Genesis e2e coverage** (phase 009 feature 073; `NDEBT-030`; NIP-0002 Stage 2).
  `tools/e2e_bootstrap_test.sh` gains `assert_genesis`: a hermetic case proving the 0-case
  end-to-end — `bootstrap.sh --genesis` stands up a new project from nothing, the deterministic
  scaffold (README + CONTEXT + `src/` placeholder) and a `resolved_sha`-pinned provenance are
  present, the committed project passes Preflight as `PASS_WITH_EXCEPTIONS` (the injected `.nizam/`
  the only exception), and a non-empty `--project-root` is refused. The existing
  inject-into-an-existing-repo path stays green (regression-guarded).

- **`incubating → in_scope` promotion — the count-0→1 transition** (phase 009 feature 072;
  `NDEBT-030`; NIP-0002 Stage 2). `registry/scope_definition_patterns.md` → v0.2.0 gains
  **Section 2.3** modelling the scope registry's `incubating` partition as the count-0→1 state: a
  greenfield-genesis project (`bootstrap.sh --genesis`) enters the registry in `incubating` and is
  promoted to `in_scope` once it clears its first clean Preflight/Baseline, as an explicit recorded
  edit that **moves** the entry (preserving the Section 2.1 exactly-one-list invariant); demotion
  is symmetric. Scoped to the single-project count-0→1 case only — promoting the registry to a
  required, validated ecosystem-membership artifact the tools iterate to set `n` (count-1→n) stays
  `NDEBT-031`/phase 010. A `tools/fixtures_self_test.sh` scratch probe asserts the transition shape
  (promotion moves the entry; a two-list "copied-not-moved" entry is detected).

- **`bootstrap.sh --genesis` — greenfield-genesis capability** (phase 009 feature 071;
  `NDEBT-030`; NIP-0002 Stage 2). Mechanizes standing up a *new* project from nothing (the
  0-case): `bootstrap.sh --genesis --project-root DIR [--project-name NAME]` `git init`s an empty
  project root, scaffolds a minimal deterministic skeleton (a `README`, a `CONTEXT.md`
  consumer-inputs stub naming the `ecosystem/00` §6 inputs, and a `src/` source placeholder),
  then reuses the normal clone → inject → verify → provenance install (recording `tag` +
  `resolved_sha`) into `<project-root>/.nizam`. It **refuses a non-empty `--project-root`** (a
  brownfield adoption, not a genesis), and a genesis that fails partway removes a project root it
  created (nothing half-built is left behind). The existing inject-into-an-existing-repo path and
  `--verify-only` are unchanged (regression-guarded). `ecosystem/00_ecosystem_bootstrap.md` →
  v0.6.0: §8's mechanization note now names `bootstrap.sh --genesis`, the §3 spectrum table's
  0-case row rolls to "Covered (Section 8 + `bootstrap.sh --genesis`)", and the "two honest
  limits" prose to "protocol + capability exist but not yet in a released tag" (the `NDEBT-029`
  release gap).

- **Greenfield-genesis protocol** (phase 009 feature 070; `NDEBT-030`; NIP-0002 Stage 2). The
  0-case of the 0–n spectrum — standing up a *new* project from nothing — becomes a first-class
  protocol: `ecosystem/00_ecosystem_bootstrap.md` → v0.5.0 gains **Section 8 (Greenfield
  Genesis)** defining the create-and-scaffold entry path (create the repository → scaffold a
  minimal deterministic skeleton + the consumer-supplied inputs of Section 6 → the normal inject
  + verify of Section 5 recording provenance (Section 7) → register the project `incubating` for
  promotion `incubating → in_scope`, the count-0→1 transition). Establishes "genesis"/"scaffold"
  vocabulary for a new *consumer* project, distinct from the framework's own phase-001 genesis.
  The Section 3 spectrum table's 0-case row and the "two honest limits" prose are corrected from
  "no protocol or tooling yet" to "protocol defined (Section 8); create-and-scaffold capability +
  `incubating→in_scope` transition mechanized in NIP-0002 Stage 2". References renumbered to
  Section 9; Sections 4–7 (and every cross-reference to the Section 7 provenance shape) unchanged.

- **Phase 009 proposed** — `.agent/product_spec_009.md` (status draft) and
  `.agent/feature_list_009.json` (features 070–074, DAG-validated acyclic, root {070}, est 1000
  lines) propose **0–n Project Spectrum, Stage 2: Greenfield Genesis**, the realization of
  `NIP-0002` Stage 2 (the 0-case). Scope: the greenfield-genesis protocol (`NDEBT-030`), a
  create-and-scaffold-from-nothing capability, the `incubating→in_scope` (count-0→1) transition
  on the scope registry, hermetic e2e coverage, then a pilot proving the 0-case. NIP-0002
  Stages 3–4 (n-case multi-repo tooling + membership registry `NDEBT-031`, `04`/`05` protocols)
  and the release cut carrying audit/compare (`NDEBT-029`) are carried as phase-010 candidate
  scope. `docs/planning/ROADMAP.md` and `docs/planning/manifest.json` recorded the proposal
  (pending/proposed). **Subsequently activated 2026-07-22** (gate `H-PHASE-009`, operator
  "Activate phase 009"): `.agent/run_state.json` records `phase_activated`, `current_phase` →
  `009-greenfield-genesis`, `product_spec_009` → active, scope budget reset (phase-008 archived);
  ROADMAP → v0.21.0 (Plan of Record banner) and `operator_gates.md` → v0.8.0 record the
  disposition.
- **`bootstrap.sh` commit-SHA pinning** (phase 008 feature 067; `NDEBT-033`). The Bootstrap
  provenance now records the **resolved commit SHA** the pinned tag pointed at (`resolved_sha`
  in `provenance.json`), making the pin an immutable commit rather than just a tag *name* — a
  tag can be moved on the remote to replay a different payload. `bootstrap.sh --verify-only`
  requires the recorded commit to be present (a payload predating this feature is rejected as
  drift) and, given a caller-supplied `--expected-sha` (resolved out-of-band from the authentic
  tag), rejects a recorded commit that differs — catching a moved tag even when the tag string
  matches. `--verify-only` stays network-free (it never re-resolves the tag). Documented in
  lockstep in `ecosystem/00_ecosystem_bootstrap.md` §7 and `standard/GIP.md` §4; covered by a
  new `tools/e2e_bootstrap_test.sh` `assert_provenance_sha_pin` case (record + correct/wrong
  `--expected-sha`).

- **`ecosystem_preflight.py` baseline provenance-pin anchoring** (phase 008 feature 066;
  ADR-004 decision 2, `NDEBT-028`). A Baseline's `framework_references` now anchors to the
  **injected framework pin** recorded in the governance-root's `provenance.json` (its `tag` /
  `framework_version`) rather than the consumer's own git HEAD, so a real bootstrapped
  consumer's baseline names *which framework* it ran under; `repository_references` continues
  to anchor to the consumer HEAD (*which consumer revision*). When there is no distinct injected
  payload (`--self-fixture` / framework-root layout, or no readable pin) it falls back to the
  historical HEAD-anchored self-referential default, unchanged. Closes phase-007 pilot finding B;
  guarded by a `tools/fixtures_self_test.sh` probe asserting the framework pin (`v0.8.0`) and the
  consumer HEAD are distinct and each correct.
- **`ecosystem_preflight.py` governance-root resolution** (phase 008 feature 065; ADR-004
  decision 1, `NDEBT-027`). The Preflight tool now resolves its required schema references
  against a **governance-root** distinct from the repository root, so a real bootstrapped
  consumer — whose payload lives under `.nizam/` — no longer hard-FAILs on missing references.
  A new `--governance-root` option sets it explicitly; otherwise it is discovered (the injected
  `.nizam/` payload, identified by its `NIZAM.json` + `schema/` markers) under `--repo-root`,
  falling back to the repo-root for the framework-root/`--self-fixture` layout (unchanged). The
  injected payload directory is surfaced as an expected `injected_governance_payload` exception
  rather than a blocking untracked finding, so a clean Preflight against a real consumer is a
  `PASS_WITH_EXCEPTIONS`, not the phase-007 pilot's hard FAIL (finding A). Guarded by new
  `tools/fixtures_self_test.sh` probes (discovery, explicit governance-root, clean framework-root
  regression) and a `tools/e2e_bootstrap_test.sh` assertion that runs the fixed Preflight against
  a genuinely bootstrapped `.nizam/` consumer.

- **Phase 008 proposed** — `.agent/product_spec_008.md` (status draft) and
  `.agent/feature_list_008.json` (features 065–069, DAG-validated acyclic, est 1010 lines)
  propose **0–n Project Spectrum, Stage 1: Consumer-Readiness**, the realization of the
  accepted `NIP-0002` Stage 1. Scope: `ADR-004` governance-root resolution (`NDEBT-027`) +
  provenance-pin anchoring (`NDEBT-028`), bootstrap commit-SHA pinning (`NDEBT-033`), GIP §5.1
  brownfield reconciliation (`NDEBT-032`), then a re-pilot proving the fixed single-project
  loop. NIP-0002 Stages 2–4 (0-case greenfield genesis, n-case multi-repo tooling + membership
  registry, `04`/`05` protocols) are carried as phase-009 candidate scope. **Historical
  proposal-time state:** this entry recorded the proposal at status draft (pending/proposed,
  awaiting gate `H-PHASE-008`); phase 008 was **subsequently activated (H-PHASE-008) and
  completed** — see the "Phase 008 … complete" entry under Changed below for the current
  lifecycle state.
- **`docs/nips/NIP-0002-zero-to-n-project-spectrum.md`** — a framework-capability
  proposal (added at status Proposed; subsequently **Accepted** via gate H-NIP — see
  the Changed entry below) that the Ecosystem Engineering Cycle explicitly span an
  ecosystem of **0 to n projects**: 0 (greenfield genesis — a new project from nothing),
  1 (a single project, greenfield or brownfield), and n (many associated repositories).
  Defines the ecosystem-membership/scope registry (reusing
  `registry/scope_definition_patterns.md`'s `in_scope`/`incubating` partitions) as the
  artifact that sets `n`, refines NIP-0001's "multi-repository" framing to be explicit
  about project count, and lays out a staged, evidence-led realization. On its acceptance
  it became the plan-of-record selection for phase 008. Authored on the operator's
  2026-07-21 design requirement and the phase-007 pilot evidence.
- **`docs/architecture/ADR-004-ecosystem-tool-consumer-readiness.md`** — the two narrower,
  pilot-proven architecture decisions NIP-0002 spawns (status **Accepted**, implementation
  sequenced into phase 008): the ecosystem tools must (1) resolve a **governance-root** so
  they locate the injected `.nizam/` payload rather than assuming the framework-root
  layout, and (2) anchor a Baseline's `framework_references` to the injected **provenance
  pin** (`.nizam/provenance.json`), not the consumer's HEAD. Records the phase-007
  scratch-consumer pilot findings A and B.
- **`ecosystem/00_ecosystem_bootstrap.md`** — the Bootstrap-stage protocol (phase 007
  feature 060), the lifecycle's entry stage, which had no protocol document until now.
  It wraps (does not restate) `standard/GIP.md` and `bootstrap.sh`: the
  pinned-immutable-tag precondition (floating refs refused), the injected six-module
  payload + `NIZAM.json`, verification and provenance/drift, coexistence with a
  non-empty consumer (GIP §5 rename-and-diff + adoption tiers), the consumer-supplied
  inputs each ecosystem must provide, and the entry condition into Preflight. The
  `ecosystem/README.md` Module Navigation status for `00` is flipped Planned→Shipped
  (five of nine protocols now shipped); the capability is registered in `tools/skill.json`
  and `NIZAM.json`. Authored under the operator-activated phase 007 (gate H-PHASE-007);
  the still-Planned `04/05/06/08` protocols remain deferred until real consumer-pilot
  evidence prioritises them.
- **`tools/compare_ecosystem_baselines.py`** + **`tools/validate_evidence_freshness.py`**
  — the deterministic Compare stage (the two NIP-0001-named tools), making Compare
  tool-driven (previously prose-only). `compare_ecosystem_baselines.py` classifies
  every finding across two audits into the closed five-class taxonomy of
  `ecosystem/07_progress_comparison.md` (`new`/`resolved`/`reopened`/`persisting`/`stale`)
  plus `pre_window_resolved`, and emits a schema-valid `delta.json`
  (`schema/audit_delta.schema.json`). It enforces the protocol's rules mechanically:
  closure-only-with-evidence (§4 — a finding merely absent from the later audit is
  reported UNCLASSIFIABLE, never auto-resolved), stale-evidence non-reuse (§5, via
  the shared freshness rule), the open-findings-only score (§6.1), and the
  first-comparison rule (§3.2 — `reopened` empty without `--prior-delta`).
  `validate_evidence_freshness.py` defines and exposes that freshness rule (evidence
  is current iff re-confirmed at or after the later anchor) as both a library
  (imported by the Compare tool) and a CLI. Both mirror `ecosystem_preflight.py`
  (stdlib-only, documented exit tables, `_UsageErrorArgumentParser`→64) and are
  guarded by standing CLI behavior probes in `tools/fixtures_self_test.sh`.
- **`tools/ecosystem_audit.py`** — a deterministic Audit-stage CLI, making the
  Audit stage tool-driven (previously prose-only; its dogfood artifacts were
  hand-authored). It mechanizes `ecosystem/03_engineering_audit.md`'s **entry
  condition** (§2 — refuses to assemble an audit unless the preflight verdict is
  `PASS` or an operator-approved `PASS_WITH_EXCEPTIONS` and a baseline exists for
  the *same* execution) and **artifact production** (§7 — validates
  auditor-authored findings against `schema/engineering_finding.schema.json`'s
  shape and the no-promotion-beyond-evidence closure rule, then emits the
  canonical `findings.json` top-level array + a rendered `report.md`, evidence
  externalised by path). It makes no engineering judgement — findings come from
  the auditor via `--findings-input`. Stdlib-only, mirroring
  `ecosystem_preflight.py` (documented exit-code table 0/1/2/64,
  `_UsageErrorArgumentParser`→64, single clock read); guarded by standing CLI
  behavior probes in `tools/fixtures_self_test.sh`.
- **`schema/audit_delta.schema.json`** — the fourth core ecosystem-cycle schema,
  validating the progress-comparison delta artifact
  (`ecosystem/07_progress_comparison.md` §7): the two revision/timestamp-anchored
  reference points and the closed five-class transition taxonomy
  (`new`/`resolved`/`reopened`/`persisting`/`stale` — all five buckets present, no
  sixth class admitted). Enforces the protocol's invariants: the
  closure-only-with-evidence rule (§4 — non-empty `closure_evidence` on every
  `resolved` and pre-window-resolved finding), fresh evidence required on
  `persisting` findings (§3), both `open_findings_count` endpoints present, and —
  since JSON Schema cannot express a constraint spanning sibling arrays — a
  code-level check in **both** C12 entry points rejecting a finding id classified
  into more than one transition class (§3 "exactly one class", mirroring the
  NDEBT-023 same-repo-revision check). Wired into `tools/validate.sh` **C12** as
  the fourth ecosystem family at both entry points (full-sweep and `--target`
  router, discriminated by its full `earlier`/`later`/`transitions` shape matched
  ahead of the generic key routes so an additive property cannot divert a valid
  delta), with one positive and three negative fixtures under `tools/fixtures/`,
  registered in `NIZAM.json`,
  indexed in `schema/README.md`, and covered by `tools/fixtures_self_test.sh`.
  Completes the four core ecosystem-cycle schemas
  (baseline / preflight-verdict / engineering-finding / audit-delta).

### Changed

- **Phase 008 (0–n Project Spectrum, Stage 1: Consumer-Readiness) complete** (feature 069).
  The fixed loop (065–068) was re-piloted against a freshly bootstrapped **scratch/throwaway**
  consumer (a loop-mechanics proof, not a real production project) and proved the phase-007
  pilot findings resolved **with no hand-applied workaround**: Preflight =
  `PASS_WITH_EXCEPTIONS` (the injected `.nizam/` is a single expected exception, not a hard
  FAIL — finding A); the baseline `framework_references` names the injected pin while
  `repository_references` names the consumer HEAD (finding B); provenance carries
  `resolved_sha` and `--verify-only --expected-sha` holds (067). Evidence under
  `.agent/evidence/pilot-069/`; `docs/planning/manifest.json` phase-008 → complete;
  `H-CONSUMER-UPGRADE` exercised a second time (a pre-release/branch pilot — a released-tag
  adoption of the fixed framework stays outstanding until the next release). NIP-0002 Stages
  2–4 remain the phase-009 candidate scope, validated by this re-pilot; a real, non-scratch
  consumer pilot remains the open production-maturity criterion.

- **Brownfield coexistence clarified as covered-by-construction** (phase 008 feature 068;
  `NDEBT-032`, resolved-by-design). Investigation showed the premise "mechanize GIP §5.1
  rename-and-diff in `bootstrap.sh`" contradicts **GIP §5.1 point 3**: `bootstrap.sh` injects
  only the `.nizam/` payload and never writes to a consumer's root `CONTEXT.md`/`AGENTS.md`/CI,
  so it *cannot* silently overwrite them — the coexistence safety is guaranteed by construction,
  and reconciling a consumer's own root files against `.nizam/templates/` is inherently a
  consumer-side manual step. `ecosystem/00_ecosystem_bootstrap.md` §3 + §5.1 (v0.4.0) corrected
  from "not yet mechanized" to "covered by construction"; `NDEBT-032` moved to Resolved
  (`docs/planning/DEBT.md` v0.31.0). No `bootstrap.sh` change.

- **`NIP-0002` accepted (gate H-NIP) → phase 008 selected.** The operator accepted
  `docs/nips/NIP-0002-zero-to-n-project-spectrum.md` (status proposed → **accepted**, v0.2.0),
  selecting **phase 008 (The 0–n Project Spectrum)** as its realization — the way NIP-0001's
  acceptance selected phase 005. Selection is not activation: phase 008 still needs its own
  `product_spec_008` + `feature_list_008` + `H-PHASE-008`. Recorded in `.agent/run_state.json`
  (`operator_gate_decision`), `docs/planning/operator_gates.md` (H-NIP second exercise,
  v0.4.0), and `docs/planning/ROADMAP.md` (phase-008 section rolled candidate → authorized,
  v0.14.0).
- **`ecosystem/00_ecosystem_bootstrap.md` → v0.2.0** — made the **0-to-n project
  spectrum** first-class (new Section 3), on the operator's 2026-07-21 design
  requirement: the Bootstrap stage now names and scopes the 0 (greenfield genesis),
  1-greenfield, 1-brownfield, and n (multi-repository) cases and states honestly which
  are mechanized today versus delegated to the GIP tiers, the scope-membership registry,
  or the deferred `04`/`05` coordination protocols. Cross-references NIP-0002 (the
  capability framing) and ADR-004 (the single-project consumer-readiness fixes).
- **`docs/planning/DEBT.md` → v0.30.0** — recorded the phase-007 scratch-consumer pilot
  friction and the 0-to-n gaps as `NDEBT-027`…`NDEBT-032`: preflight governance-root
  assumption (A), baseline framework-pin mis-anchoring (B), audit/compare not yet in a
  released tag (C), the absent 0-case (D), single-`--repo-root` tools versus multi-repo
  prose (E), and `bootstrap.sh` lacking GIP §5.1 brownfield reconciliation (F). Each
  cross-references ADR-004 or NIP-0002 and is sequenced into phase 008. Plus `NDEBT-033`
  (from the PR #42 review): bootstrap provenance pins the tag name but not its resolved
  commit SHA — hardening deferred to phase 008.

### Fixed

- **Doc-truth in the ecosystem protocols** — retired the stale "schema … not yet
  present at the time this protocol was authored" parentheticals in
  `ecosystem/01_clean_state_preflight.md`, `ecosystem/02_evidence_baseline.md`, and
  `ecosystem/03_engineering_audit.md` (their schemas shipped in features 037–039 and
  have been present under `schema/` since), and updated
  `ecosystem/07_progress_comparison.md` from its "optional / deferrable / not yet
  present" bare-filename reference to the now-present, directory-qualified
  `schema/audit_delta.schema.json`. No protocol semantics changed.

## [0.8.0] - 2026-07-20

**Minor release** (`methodology/06_release_train.md` §3.2): phase 006
(Enforcement Closure & Hardening, features 049–059) adds new *optional*
capability — validator checks C13/C14/C15, new `tools/verify_lib.sh`
primitives, additional `tools/ecosystem_preflight.py` options, an additive
`enforcement:` frontmatter field (rides `additionalProperties: true`), and
documentation-honesty markings — without invalidating any consumer content
that previously validated. One schema narrowing is disclosed per §4 and
classified minor-not-breaking: `schema/preflight_verdict.schema.json` now
requires `blocking_findings` when `verdict` is `FAIL` (feature 056), but a
preflight verdict is tool output regenerated each run by the same-release
`tools/ecosystem_preflight.py`, not durable consumer-authored content, so
upgrading invalidates no consumer document.

### Added

- **Constitutional-layer mechanize-or-descope decision** (phase 006 feature 058,
  gate **H-CONSTITUTIONAL**, Track 3): the operator's per-document decision on the
  v0.4.0 NMF-hybrid constitutional policy surface, so every consumer first-contact
  surface is honest about what the framework enforces. **Mechanized (2):**
  `standard/provenance_policy.md`'s SHA-pinned-Actions rule is now verified by
  `tools/validate.sh` check **C14** (a new `vlib_workflows_sha_pinned` primitive over
  the workflows directory), and `standard/capability_profiles.md`'s five-profile ↔
  five-AGF-role correspondence by check **C15** (a new `vlib_profiles_cover_roles`
  primitive) — the default sweep is now 15 checks, both dogfooded green.
  **Descoped consumer-aspirational (7):** `standard/ci_gates.md`,
  `methodology/05_eval_and_trace.md`, `methodology/07_eval_gated_promotion.md`,
  `standard/mcp_policy.md`, `standard/permission_classes.md`,
  `standard/failure_modes.md`, and `standard/cross_repo_governance.md` gain an
  `enforcement: consumer-aspirational` frontmatter field and a body banner, and
  `tools/SKILL.md`'s cross-repo directive is softened to match. `docs/guide/index.html`
  is refreshed to name the constitutional documents and reflect each decision;
  ROADMAP Track 3 is marked resolved. The two mechanized docs are marked
  `enforcement: partially-enforced`.
- **Preflight + ecosystem-schema hardening bundle** (phase 006 feature 056,
  resolving **NDEBT-021, -023, -024, -017, -018**): the deferred
  `tools/ecosystem_preflight.py` hardening backlog, each item carrying a
  discriminating executed probe (the CLI is not CI-covered, so the
  untracked-not-tolerated and tolerate-polarity probes are now standing guards in
  `tools/fixtures_self_test.sh`). **NDEBT-021** — NUL-delimited
  `git status --porcelain=v1 -z` parsing that preserves the directory-prefix
  tolerate semantics the 043/044 approved runs depend on; readable-regular-file
  reference checks (`os.path.isfile` + `os.access`, rejecting a directory at the
  path) and an unresolved-HEAD blocking finding; `--repo-root` defaulting to
  `None` so an explicit `.` is honored under `--self-fixture`; and an output-dir
  pre-clean so a reused directory never mixes contradictory verdicts.
  **NDEBT-018** — an additive `--tolerate-untracked-prefix` option (tolerate a
  whole in-flight artifact directory by one declared prefix, preserving the exact
  043/044 dir-collapse semantics) and `ecosystem/01_clean_state_preflight.md`
  (0.1.2) §4.1 codifying that an orchestrator gate-decision tracked-state write
  must be committed before the gated preflight invocation. **NDEBT-017** — a
  pluggable, offline `--ci-run-file` that anchors `ci_references` to a
  caller-resolved CI run (no in-tool network call). **NDEBT-023** — same-repo
  revision-consistency mechanized in the capture tool and validator `C12` (a new
  schema-valid but rule-violating
  `ecosystem_baseline_neg_inconsistent_revisions.json` fixture is caught by the
  code-level check). **NDEBT-024** — a `blocking_findings` array required when
  `verdict` is `FAIL` in `schema/preflight_verdict.schema.json`, with
  `preflight_verdict_fail.json` rebuilt on it. The five documented exit codes
  (0/1/2/3/64) are unchanged; sweeps 13/13 and 11/11, self-test 47/47, e2e green.
- **Progress-comparison taxonomy completion** (phase 006 feature 057, resolving
  **NDEBT-022**): `ecosystem/07_progress_comparison.md` (0.2.0) completes its
  finding-state taxonomy so a real corpus classifies without workarounds.
  Section 3 adds the fifth transition class **`persisting`** (present on both
  sides with freshly re-confirmed, current evidence — the exact opposite of
  `stale`), a **pre-window-resolved** recording rule (§3.1: a finding resolved
  before the earlier input's reference point is recorded but is not a
  cross-execution transition and is excluded from the open-findings score), and
  a **first-comparison** rule (§3.2: an empty `reopened` bucket on a first
  comparison is correct). Section 6.1 fixes the score-count semantics — the
  open-findings score counts `open` findings only, never resolved or
  pre-window-resolved recorded findings. The audit-044 corpus now classifies
  directly (015 persisting, 002 pre-window-resolved, 016 stale, 017/018 new;
  open-only 2→4); the committed `audit-2026-07-17-cba6422` artifacts stay
  immutable.
- **Work-packet template ↔ schema alignment** (phase 006 feature 054, resolving
  **NDEBT-011**): `templates/work-packet.template.json` now validates end-to-end
  against `schema/work-packet.schema.json` — the three enum/integer dispatch
  fields that held the `{{TIER}}`/`{{BLAST_RADIUS}}`/`{{MERGE_ORDER}}`
  placeholders are omitted from the starter template (they cannot be
  schema-valid, and shipping literal defaults would let a copied packet silently
  carry a wrong tier / blast-radius / merge-order) and are documented in the
  schema for consumers that need cross-repo dispatch, so the schema's own
  `description` claim to validate the template is now true. The parse-validity-only caveat is
  retired from `templates/README.md` (0.2.2) and `schema/README.md` (0.7.1), and
  a `tools/fixtures_self_test.sh` guard mechanically asserts the conformance in
  CI (`jsonschema.validate` of the template against its schema) so it cannot
  silently drift back to non-conformance.
- **Enumeration/bare-ref recurrence guards** (phase 006 feature 055, resolving
  **NDEBT-005**): two vetted `tools/verify_lib.sh` primitives — the library's
  seventh and eighth — mechanize the two NDEBT-003 defect classes F-027 had
  fixed by hand, both sourced from the single canonical index `NIZAM.json`
  rather than re-derived lists. `vlib_enumeration_complete` asserts the
  disk→index (completeness) direction `C4` does not cover: every on-disk
  governed document under a module directory must be enumerated in that
  module's `key_documents`. `vlib_bare_ref_resolves` flags a bare,
  non-`/`-qualified `NN_name.md` reference whose basename matches no
  `key_document` — the shape `C9` and `C10` both miss. Both ride the F-052
  self-test surface with seeded-omission and seeded-bare-stale-reference
  fixtures plus a real-tree recurrence sweep (enumeration over all four
  documentation modules; bare-ref over `methodology/` + `standard/`, the
  stable modules where the defect occurred, excluding the still-evolving
  `ecosystem/` and quoting registers to avoid false positives).
  `fixtures_self_test` now accounts for 46 fixtures (was 43).
- `tools/validate.sh` check **C13** (skill-index integrity; phase 006 feature
  049, resolving NDEBT-007): `tools/skill.json` is JSON-parsed and its
  `entry_point` plus every `capabilities[].module` pointer must resolve to an
  existing file — the enforcement hole that let the `release_train` capability
  ship a retired module pointer from v0.4.0 through v0.5.3 undetected is
  closed. Runs in the full sweep (SUMMARY migrates `12 passed` → `13 passed`)
  and in `--payload` mode (`10 passed` → `11 passed`), where pointers into the
  non-injected directories are skipped pending the F-051 payload-contract
  decision. Negative fixture
  `tools/fixtures/skill_index_neg_dangling_module.json` reproduces the defect
  class; `tools/README.md` (0.4.0) and the `NIZAM.json` validator capability
  summary document the C1–C13 set.
- **Fixtures self-test** `tools/fixtures_self_test.sh` and a `fixtures_self_test`
  CI job (phase 006 feature 052, resolving **NDEBT-009**): every shipped
  `tools/fixtures/` fixture is run through its targeted surface —
  `validate.sh --target` for check-level fixtures, the `verify_lib.sh`
  primitives for primitive-level ones, and a `tools/skill.json` substitution
  for the C13 negative fixture — asserting the **specific** verdict (not a
  bare non-zero exit, which most `.md` fixtures already return from incidental
  C1/C2 failures), with a completeness guard that fails on any unaccounted
  fixture. Closes the dormancy gap where a check regressing to a vacuous pass
  would not have been caught.
- `tools/validate.sh` **C12 `--target` routing** (feature 052, resolving
  **NDEBT-015**): a `--target` invocation against an `ecosystem_baseline`,
  `preflight_verdict`, or `engineering_finding` fixture now content-routes to
  its shipped schema and emits a discriminating `[C12]` verdict, instead of
  misrouting to C4/C11 and failing regardless of polarity.
- `tools/validate.sh` **C12 naming-conformance guard** (feature 052, resolving
  **NDEBT-016**): the fixture-polarity classifier is case-insensitive and a
  basename carrying a `neg`/`invalid` look-alike that is not the canonical
  delimited-lowercase token (uppercase `_NEG_`, full-word `_negative_`) is a
  named FAIL, so the classifier cannot be gamed by a look-alike name.
- **Orchestrator role + operational-rule codification** (phase 006 feature
  053): `standard/AGF.md` (0.2.0) now defines the **Orchestrator** in Section 2
  — the coordination/state-ownership role that sequences the four execution
  roles, parses each gate verdict, owns `run_state.json`'s run-position and
  coordination fields (Section 5 rule 4), and enforces the circuit breaker —
  resolving **NDEBT-010**, the load-bearing-but-undefined role that
  `capability_profiles.md`, `permission_classes.md`, `mcp_policy.md`, and
  `methodology/06_release_train.md` (0.3.1) all already referenced.
  `methodology/02_adversarial_tdd.md` (0.4.0) gains Section 10 anti-pattern (e)
  (explicit exit-code assertion — **NDEBT-019**), Section 11 Probe Isolation
  (**NDEBT-013/020**), and Section 12, the five-class verification-authoring
  defect catalogue (**NDEBT-014**). `tools/verify_lib.sh` gains a sixth vetted
  primitive, `vlib_word_present` (whole-word match, fixing the
  substring-on-containing-word false-pass), fixture-tested via
  `tools/fixtures_self_test.sh`. Three stale "four agent roles" descriptions of
  AGF were corrected in-scope (`standard/README.md`,
  `methodology/01_execution.md`, `methodology/00_planning.md`).

### Changed

- **Bootstrap payload enlarged to six directories** (phase 006 feature 051,
  the H-PAYLOAD-CONTRACT decision, resolving **NDEBT-008**): `bootstrap.sh`
  now injects `methodology/` and `ecosystem/` alongside `standard/`,
  `templates/`, `schema/`, and `tools/` (plus `NIZAM.json`). Consumer
  `.nizam/` installs previously omitted these two directories, so the many
  `tools/skill.json` and `tools/SKILL.md` cross-references into `methodology/`
  (and the `ecosystem/` references added in feature 040) dangled in a real
  install. `standard/GIP.md` (0.4.0 — Sections 1, 2, 2.1, 4, 5.1) and
  `CONTEXT.md` (0.7.0) now name the six-directory payload authoritatively; the
  C4/C9/C13 `--payload` carve-outs for `methodology/`+`ecosystem/` are retired
  (those paths are now required to resolve), leaving only the still-non-injected
  `registry/` and `docs/` carved out; `tools/e2e_bootstrap_test.sh` asserts the
  enlarged payload. Verified load-bearing: a payload missing the two dirs now
  FAILs both `validate.sh --payload` and `bootstrap.sh --verify-only`. This
  enlarges what consumers receive on their next re-bootstrap; `registry/` and
  `docs/` remain framework-envelope and are still never injected.

### Fixed

- `tools/validate.sh` self-description drift left by feature 051 (found and
  corrected in-scope during feature 052): the C4/C13 `--help` text, the C13
  function comment, and the C13 payload-mode PASS message still named
  `methodology/`+`ecosystem/` among the payload-skipped directories and said
  the carve-out was "pending the F-051 payload-contract decision" — but
  feature 051 already made those two directories injected/required, narrowing
  the skip set to `registry/`+`docs/`. The code (`skipped_dirs`,
  `SKIPPED_DIR_PREFIXES`, the C9 allow-list) was already correct; only the
  human-readable descriptions lagged. An NDEBT-005-class enumeration-
  completeness miss.
- `tools/validate.sh` C4 payload mode: `ecosystem` joined the non-injected
  carve-out set (`methodology`, `registry`, `docs`). NIZAM.json has indexed
  `ecosystem/` paths since feature 040, but `bootstrap.sh` does not inject the
  directory, so a real consumer v0.7.0 payload would have false-failed C4 —
  masked in the framework's own payload-mode runs because the directory exists
  on disk here. Registered as an NDEBT-008 broadening; the carve-out narrows
  again when F-051 decides the payload contract.
- `tools/validate.sh` C4 + C13 path hygiene (feature-049 review round, PR
  #28): indexed paths and skill-module pointers are normalized before the
  payload carve-out test, so a traversal spelling
  (`ecosystem/../tools/x.md`) can no longer ride a non-injected-dir skip;
  absolute paths and paths escaping the repo root now FAIL in every mode
  instead of matching host files. The repo-containment check runs on every
  present path *before* the carve-out, so a symlinked carve-out path
  (`ecosystem/evil -> /etc`) is rejected in payload mode too rather than
  riding the skip; genuinely-absent carve-out paths stay allowed. C13 also
  never carves out the `entry_point` in payload mode — the skill's single
  entry document must resolve in any payload, so a mis-declared
  `entry_point` under a non-injected prefix FAILs rather than ride the
  capability-module carve-out. The `--help` payload descriptions now name
  the full carve-out set including `ecosystem/`.
- `tools/validate.sh --payload` is now **CWD-independent** (phase 006 feature
  050, resolving **NDEBT-012** / the first external-consumer bug report,
  issue #18): in `--payload` mode the validator anchors to its own payload
  root (the parent of its `tools/` directory), so
  `bash .nizam/tools/validate.sh --payload` run from a consumer repository
  root now behaves identically to `cd .nizam && bash tools/validate.sh
  --payload` instead of failing to find the payload's own files. Default and
  `--target` modes stay CWD-anchored (unchanged documented contract).
- `tools/validate.sh` check **C9** payload carve-out (feature 050, resolving
  **NDEBT-004**): in `--payload` mode a directory-qualified cross-reference is
  only required to resolve if its target is under an injected-payload prefix
  (`standard/`, `templates/`, `schema/`, `tools/`); references into
  non-injected framework-envelope paths (`methodology/`, `ecosystem/`,
  `registry/`, `docs/`, `.agent/`, `.github/`, …) are expected-absent in a
  consumer subset and are skipped — the C9 analog of C4's existing carve-out.
  A real bootstrapped payload previously false-failed C9 on 26 such
  references even from the payload root; both `--payload` invocation forms now
  pass green. The default full sweep applies no carve-out, so stale
  non-injected references are still caught. `tools/e2e_bootstrap_test.sh`
  gains a from-consumer-repo-root `--payload` assertion so the regression
  class stays closed. (The NDEBT-004 fix is landed and verified; resolving it
  *within* feature 050 rather than its own feature is an operator scope call
  disclosed as pending ratification — see the PR #29 description — and
  finalized on merge.)

## [0.7.0] - 2026-07-17

### Added

- `.github/workflows/release.yml`: mechanizes GitHub Release publication.
  On every `vMAJOR.MINOR.PATCH` tag push (or manual dispatch for a
  pre-existing tag), it extracts the tag's own `## [X.Y.Z]` CHANGELOG
  section (read at the tag, not at `main`), titles the Release from the
  annotated tag's subject line, and creates-or-updates the Release page
  idempotently. A tag whose at-tag CHANGELOG carries no matching section
  fails loudly, enforcing `methodology/06_release_train.md` Section 2's
  changelog discipline at publication time — the failure class of the
  v0.5.2/v0.5.3 cycle (tagged without CHANGELOG entries) and of v0.6.0
  (tagged without a Release page). The logic is inline in the workflow, not
  under `tools/`, because `tools/` is bootstrap-injected consumer payload
  and Release publication is a framework-envelope concern.
- `ecosystem/README.md` plus 4 new protocol documents
  (`ecosystem/01_clean_state_preflight.md`, `ecosystem/02_evidence_baseline.md`,
  `ecosystem/03_engineering_audit.md`, `ecosystem/07_progress_comparison.md`):
  the reusable, schema-governed Ecosystem Engineering Cycle (handover
  NIP-0001), extending Nizam's repository-local contract-first loop to
  ecosystem scale. Framework-side only this phase; consumer adoption is
  deferred to a successor programme phase.
- `schema/preflight_verdict.schema.json`, `schema/ecosystem_baseline.schema.json`,
  `schema/engineering_finding.schema.json`, plus matching positive/negative
  `tools/fixtures/` fixtures for all three schema families.
- `tools/ecosystem_preflight.py`: a deterministic, self-fixture-capable CLI
  implementing the clean-state preflight protocol (three-verdict vocabulary,
  operator-exception rule).
- `tools/validate.sh` check **C12** (ecosystem schema-family fixture
  validation). The default sweep's `SUMMARY` migrates from `11 passed, 0
  failed` to `12 passed, 0 failed`; `--payload` mode is unaffected (still
  `10 passed, 0 failed`), since C12 is deliberately full-sweep-only.
- `docs/nips/NIP-0001-ecosystem-engineering-cycle.md`: the accepted NIP
  recording the Ecosystem Engineering Cycle's scope and rationale.
- The framework's first self-dogfood evidence cycle: two gated preflight +
  baseline runs (`.agent/reconciliation/dogfood-2026-07-17-28c8253/`,
  `.agent/reconciliation/dogfood-2026-07-17-6d7a47b/`) and a first
  engineering audit + progress comparison
  (`.agent/audits/audit-2026-07-17-cba6422/`), registering NDEBT-013 through
  NDEBT-018.

### Changed

- `docs/planning/ROADMAP.md` (0.2.0): Current Position refreshed after the
  2026-07-15 release-readiness audit — the v0.6.0 annotated tag was cut and
  pushed 2026-07-15 at the release commit (955c1d7), executing Track 1's first
  human gate; the residual v0.6.0 GitHub Release publication and the GitHub
  Pages gate remain recorded, and the phase-005 candidate scope gains the
  NDEBT-012 payload-validator fix.
- `docs/planning/DEBT.md` (0.8.0): registered NDEBT-012 — `tools/validate.sh
  --payload` is CWD-sensitive and fails when invoked from a consumer
  repository root instead of inside `.nizam/` (GitHub issue #18, the first
  bug report from a real external consumer; corroborates NDEBT-004 and
  NDEBT-008's consumer-context concerns).
- Release metadata: `NIZAM.json` `framework.version` and the
  `docs/guide/index.html` version anchors bumped to `0.7.0`; the `README.md`
  quickstart re-pinned to `v0.7.0`; `CONTEXT.md` bumped to 0.6.0 for the
  release state.
- `NIZAM.json`: the `nizam-compliance-validator` capability summary now
  describes the full C1-C12 check set — it had continued to enumerate only
  the eleven v0.6.0-era check domains after C12 (ecosystem schema-family
  fixture validation) shipped in this release.

## [0.6.0] - 2026-07-13

### Added

- `tools/verify_lib.sh`: a vetted, sourced verification-helper library exposing
  five fixture-tested primitives contracts and `validate.sh` checks compose
  instead of re-inventing — section-scoped grep, the untracked-aware scope
  guard, strict-version-increase-vs-HEAD, punctuation-stripped path
  resolution, and the generalized stale-payload-enumeration guard. A matching
  verification-authoring standard section was added to
  `methodology/02_adversarial_tdd.md`, codifying the anti-patterns a
  contract's verification suite must not use (whole-file vacuous greps,
  `git diff HEAD` scope guards blind to new untracked files, bare-adjacency
  checks, and content-free substring checks).
- `tools/validate.sh` checks **C9** (repo-wide path-resolution), **C10**
  (single-source-of-truth consistency: payload-set enumeration, bootstrapped-
  consumer discovery order, framework-version anchor), and **C11** (dogfood
  schema validation of `.agent/qa/*.json`, `.agent/contracts/*.json`, and
  `.agent/run_state.json` against the shipped schemas, enforce-if-present /
  skip-if-absent). The full sweep's `SUMMARY` migrated from `8 passed, 0
  failed` to `11 passed, 0 failed`.
- `schema/contract_review.schema.json`, describing the pre-code
  contract-review artifact shape, and a reconciled `schema/qa_verdict.schema.json`
  (`anyOf` union of the legacy and evolved QA-verdict shapes) so every
  historical `.agent/qa/*.json` validates without edits; `schema/contract.schema.json`
  now documents `amendments[]` as an explicit property. Resolves NDEBT-002.
- `tools/e2e_bootstrap_test.sh`: a hermetic (network-free), dual-mode
  end-to-end harness that exercises the real `bootstrap.sh` inject → verify
  adoption path via a local `file://` clone and an ephemeral annotated tag —
  asserting the injected payload, `NIZAM.json` index integrity, the
  documented `.nizam/tools/skill.json` discovery path, and a `--verify-only`
  pass — plus a `--self-test-negative` mode proving the discovery-path guard
  is load-bearing. A second CI job in `.github/workflows/compliance.yml`
  (`e2e_bootstrap`, alongside the existing `validate` job) runs it on every
  PR and push to `main`. `bootstrap.sh` itself is unmodified.
- `docs/planning/ROADMAP.md`: a forward roadmap naming the outstanding human
  gates (the v0.6.0 release cut, GitHub Pages publishing for `docs/guide/`),
  the candidate scope for a phase 005 sourced from the open debt register,
  and the mechanize-or-descope decision required for the constitutional
  policy surface shipped in v0.4.0.

### Fixed

- `tools/skill.json`: the `release_train` capability's `module` pointer now
  names `methodology/06_release_train.md`; it had pointed at
  `methodology/05_release_train.md`, a path retired by the v0.4.0 methodology
  renumbering that inserted `05_eval_and_trace.md`. The identical stale
  pointer in `tools/interface.md` was fixed during the v0.5.x cycle, but
  `skill.json` — whose content no validator check sweeps (C4 parses only
  `NIZAM.json`; C9 sweeps only `.md`/`.html` bodies) — was missed and shipped
  broken from v0.4.0 through v0.5.3. `skill.json` `version` bumped
  0.1.0 → 0.1.1; the enforcement gap is registered as NDEBT-007.
- `standard/AGF.md` (0.1.1): Section 6's circuit-breaker cross-reference no
  longer calls `methodology/03_circuit_breaker.md` "forthcoming" (it shipped
  at genesis), and the Section 4 verdict rule's dropped word is restored
  ("a single non-empty entry in any of the three arrays blocks advancement").
- `standard/GIP.md` (0.3.1): Section 2.1's verification minimum no longer
  hard-codes "the four `standard/` documents" — the module has shipped eleven
  governance documents since v0.4.0.
- `registry/README.md` (0.2.1): removed the stale "13 capability entries"
  hard count (the root index now carries 24 capability entries).
- `schema/README.md` (0.4.0): added the missing `work-packet.schema.json` row
  to the Schemas table — the schema shipped in v0.5.0 but was never indexed
  in its own module README.
- `NIZAM.json`: the `schema` module's `key_documents` list now includes
  `schema/contract_review.schema.json`, which was present in the top-level
  `schemas[]` array but missing from the module index.
- `CONTEXT.md` (0.4.1) and root `README.md`: the `standard/` module
  descriptions now name the constitutional policy documents shipped since
  v0.4.0 instead of only the four genesis-era core documents; the README
  quickstart is re-pinned from v0.5.1 to v0.5.3 (the latest released tag).
- `docs/planning/manifest.json`: phase `004-durable-enforcement` status
  corrected from the stale `in_progress` to `complete` — run_state recorded
  `phase_complete` on 2026-07-10 and the phase PR merged — with a lifecycle
  note recording the outstanding v0.6.0 human release gate.
- `docs/planning/DEBT.md` (0.7.0): NDEBT-003 moved to Resolved (both of its
  defects were fixed by F-027 and verified in-tree, but the register was
  never updated); new entries NDEBT-007 through NDEBT-011 registered from
  the 2026-07-12 external project review.
- `NIZAM.json` `framework.version` and the `docs/guide/index.html` version
  anchors (meta `framework-version` and the footer version span) reconciled
  from the stale `0.5.1` to `0.5.3`: the v0.5.2 and v0.5.3 hotfix releases
  were tagged without bumping the root capability index, leaving agents that
  discover the framework through `NIZAM.json` a conflicting release identity
  (PR #16 review finding).

### Changed

- Release metadata: `NIZAM.json` `framework.version` and the
  `docs/guide/index.html` version anchors bumped to `0.6.0`; the `README.md`
  quickstart re-pinned to `v0.6.0`; `CONTEXT.md` bumped to 0.5.0 for the
  release state.
- `NIZAM.json`: the `nizam-compliance-validator` capability summary now
  describes the full C1–C11 check set — it had continued to enumerate only
  the eight v0.2.0-era check domains after C9 (repo-wide path resolution),
  C10 (single-source-of-truth consistency), and C11 (dogfood schema
  validation) shipped in this release.

## [0.5.3] - 2026-07-09

### Fixed

- Stripped trailing whitespace from `standard/failure_modes.md` in the
  governance payload, which caused CI failures on consumer repos.
  *(Backfilled 2026-07-12: v0.5.3 was tagged and released on GitHub without a
  CHANGELOG entry, violating `methodology/06_release_train.md`'s changelog
  discipline; this entry restores the record. See the v0.5.3 GitHub Release.)*

## [0.5.2] - 2026-07-09

### Fixed

- `tools/validate.sh` C8 (`check_c8_version_changelog`) path resolution in
  payload mode: `git show HEAD:<path>` now prepends
  `git rev-parse --show-prefix`, so in payload mode (CWD = `.nizam/`) it
  correctly resolves `.nizam/`-relative paths instead of repo-root paths,
  eliminating false "version downgrade" failures on consumer repos that have
  their own `tools/` or `templates/` directories at the repo root. (PR #14)
  *(Backfilled 2026-07-12: v0.5.2 was tagged and released on GitHub without a
  CHANGELOG entry; this entry restores the record. See the v0.5.2 GitHub
  Release.)*

## [0.5.1] - 2026-07-09

### Added

- `tools/validate.sh --payload` mode: validates the `bootstrap.sh`-injected
  consumer payload subset (`standard/`, `templates/`, `schema/`, `tools/`,
  `NIZAM.json`) without requiring framework-envelope files (`CONTEXT.md`,
  `README.md`, `CHANGELOG.md`, `bootstrap.sh`, `methodology/`, `registry/`,
  `docs/`). C4 skips registry schema validation when absent and filters
  non-injected dir paths; C5 sweeps only existing files; C6 is skipped;
  C7 checks only injected module READMEs. Default and `--target` modes are
  unchanged (8/8 pass, no regression). (PR #12)

### Fixed

- ADR-001 follow-up note documenting the `--payload` validation path.

## [0.5.0] - 2026-07-09

### Added

- `schema/work-packet.schema.json`: JSON Schema for the work-packet artifact
  (`templates/work-packet.template.json`). Requires the historical minimal set
  (`id`, `objective`, `scope`, `acceptance`, `evidence`, `non_goals`) so every
  pre-existing packet stays valid, and adds optional linking/dispatch fields an
  execution ledger (for example a Kanban dispatcher) needs to bind a packet to a
  plan of record: `repo`, `tier` (seven-tier model of
  `standard/cross_repo_governance.md`), `blast_radius` (local/cluster/ecosystem),
  `concurrency_lane`, `dependency_edges` (`depends_on`/`consumed_by`) and
  `merge_order` (upstream-before-downstream ordering of
  `methodology/08_cross_repo_dependency_gate.md`), and the foreign keys
  `contract_id`, `phase_id`, `feature_id`, and `train_id`. `templates/work-packet.template.json`
  gains the matching optional placeholder fields and corrects the `merge_order`
  placeholder to an unquoted integer (`0`) matching the integer schema. `NIZAM.json`
  indexes the new schema.

### Fixed

- Compliance hotfix restoring `tools/validate.sh` to green (the v0.4.0/v0.4.1
  releases had shipped a tree failing the framework's own validator): removed
  vendor-specific org branding — a stray org name in
  `standard/cross_repo_governance.md` (C5 branding sweep) and the `$id` URLs of
  `schema/debt.schema.json` and `schema/capability_profile.schema.json`, now in
  the vendor-neutral `urn:nizam-framework:schema:*` form matching the other
  shipped schemas; corrected `methodology/06_release_train.md`'s
  `authoritative_source` to its own path after the `05` -> `06` rename (C2 format);
  and synced `docs/guide/index.html`'s embedded framework-version anchor to `0.4.1`
  to match `NIZAM.json` `framework.version`.
- Schema hardening: clamped `qa_verdict.schema.json` `exit_code` to `0..255`
  (POSIX range); enforced `minimum: 0` on `run_state.schema.json` per-feature
  line count fields; enforced `maximum: 3` on circuit breaker `limit` (aligning
  with the documented mandatory 3-strike rule).
- Documentation drift: updated `README.md` quickstart tag from `v0.1.0` to
  `v0.5.0`; added `docs/` to the `README.md` Modules table and `CONTEXT.md`
  Module Map; bumped `CONTEXT.md` version from `0.2.0` to `0.3.0`; bumped
  `tools/SKILL.md` version from `0.1.0` to `0.2.0` to reflect the Cross-Repo
  Intelligence, Eval-Gated Promotion, and Cross-Repo Dependency Gate additions
  that landed in `v0.4.0` but were not versioned; synced `docs/guide/index.html`
  and `NIZAM.json` `framework.version` to `0.5.0`.

## [0.4.1] - 2026-07-08

### Changed

- **Tool-agnostic automated-review gate**: Renamed the `MERGE_READY` formula
  factor `CODERABBIT_CLEAN` to `AUTOMATED_REVIEW_CLEAN` in `standard/ci_gates.md`
  and generalized the corresponding gate description. The framework now MANDATES
  a blocking, deny-by-default automated code-review gate (a conformant tool must
  have run on the latest relevant SHA with no unresolved blocking findings) but
  no longer dictates the specific tool — the consumer declares it (e.g. in its
  `NIZAM.json` / governance config). `methodology/05_eval_and_trace.md` L8 is
  likewise generalized from a CodeRabbit-specific reference to a tool-agnostic
  automated code-review gate. The attributed 10-gate enforcement table is unchanged.

## [0.4.0] - 2026-07-08

### Added

- **Nizam Manifesto Framework (NMF) Hybrid**: Integrated the constitutional breadth of the Vibe Coding Manifesto into the installable, schema-driven Nizam Framework format (ADR-003).
- `standard/capability_profiles.md` and `schema/capability_profile.schema.json`: Capability Profile Model binding roles to task types and safety classes, not specific models.
- `standard/ci_gates.md`: The mandatory 10-gate `MERGE_READY` formula.
- `standard/mcp_policy.md`: MCP Security Policy for namespace rules and surface allocations.
- `standard/failure_modes.md`: The seven canonical failure modes and detection/response protocols.
- `standard/provenance_policy.md`: Supply-Chain Provenance Policy for artifact attestations and audit envelopes.
- `standard/permission_classes.md`: Permission and Sandbox Policy defining deny-by-default RBAC and Kubernetes allocations.
- `standard/cross_repo_governance.md`: Cross-Repository Intelligence rules, executable truth layer, and seven-tier architecture model.
- `methodology/05_eval_and_trace.md`: Eval and Trace Infrastructure defining the verification hierarchy and role-specific eval suites.
- `methodology/07_eval_gated_promotion.md`: Eval-Gated Model Promotion Protocol treating model changes as code changes.
- `methodology/08_cross_repo_dependency_gate.md`: Cross-Repo Dependency Gate requiring upstream contract delta approval before downstream execution.
- `templates/DEBT.md` and `schema/debt.schema.json`: Circuit Breaker Debt Log for recording circuit breaker trips and architectural debt.

### Changed

- Renamed `methodology/05_release_train.md` to `methodology/06_release_train.md` to maintain ordering.
- Updated `NIZAM.json` to index all new capabilities, modules, schemas, and templates.
- Updated `standard/README.md` and `methodology/README.md` to reflect new protocol documents.
- Updated `tools/SKILL.md` to mandate Cross-Repo Intelligence queries before action, and to acknowledge Eval-Gated Promotion and Cross-Repo Dependency Gates.

## [0.3.0] - 2026-07-08

### Added

- `docs/guide/index.html`, a self-contained, dependency-free HTML user guide
  covering discovery, adoption, the contract-first execution loop, and the
  circuit breaker; and `docs/architecture/ADR-002-html-user-guide.md`,
  recording the decision to ship it. `NIZAM.json` gains a `docs` module
  indexing both Architecture Decision Records (`ADR-001`, `ADR-002`) and the
  guide.
- `LICENSE`, the MIT license (copyright held by "The Nizam Framework
  Authors"), with a corresponding license notice added to `README.md`.

### Changed

- `CONTEXT.md`: rewritten to be current — stale forward-references removed,
  the phase-002 compliance-validator and CI-gate surfaces added, the
  injected payload corrected to the actual four directories plus
  `NIZAM.json`, the `.agent/` path documented, and `status` flipped to
  `active`.
- `README.md`: given a quickstart, a two-audience (framework-maintainer
  vs. consumer-repo) split, links to the HTML guide and the GitHub Release,
  and mentions of the compliance validator, the CI gate, and the
  Architecture Decision Records.

### Fixed

- `tools/interface.md`: corrected the runtime-adapter discovery order so a
  bootstrapped consumer's `.nizam/tools/skill.json` is checked first, with
  the repository-root `tools/skill.json` retained as an explicitly labeled
  framework-checkout fallback.
- `standard/GIP.md`: corrected the injected-payload description (previously
  stale at three directories) to the actual four directories plus
  `NIZAM.json` everywhere it is enumerated, and added an Adopting in an
  Existing Repository section defining incremental adoption tiers.

## [0.2.0] - 2026-07-08

### Added

- `docs/architecture/ADR-001-ci-compliance-enforcement.md`: records the
  decision to adopt CI enforcement of `standard/NDS.md` §7 via a repo-local,
  runtime-agnostic compliance validator invoked by a GitHub Actions workflow
  on every pull request and every push to `main`, closing the gap between
  the framework's prescribed enforcement and its previously-unenforced
  shipped state.
- `tools/validate.sh`, the repo-local NDS compliance validator: eight checks
  (C1-C8) — frontmatter schema, format, untagged-fence sweep, `NIZAM.json`
  index integrity, branding/endpoint leakage, `bootstrap.sh` sanity, module
  README presence, and version-bump-vs-changelog — plus `tools/fixtures/`
  negative fixtures exercising each failure mode, and a `nizam-compliance-validator`
  capability entry indexing it in `NIZAM.json`.
- `.github/workflows/compliance.yml`, the CI gate running `tools/validate.sh`
  on `pull_request` and on `push` to `main` (full-history checkout, so the
  C8 version-bump-vs-changelog check's `git show HEAD:<path>` lookups
  resolve correctly).

### Changed

- `.agent/product_spec.md` §2.1 (Hybrid Mono-Repo Layout): amended to add
  `.github/workflows/` and `tools/validate.sh` to the architecture diagram;
  `spec_version` bumped 1.0.0 → 1.1.0.
- `methodology/02_adversarial_tdd.md` (0.2.0): adds the External Anchor Rule
  (Section 7) and the Mandatory Adversarial Evidence requirement (Section 8).
- `methodology/04_tool_driven_state.md` (0.2.0): adds the Evidence Capture
  Convention and the Clock-Read Timestamps rule (Section 5).
- `methodology/00_planning.md` (0.2.0): adds the Plan Amendment Rule
  (Section 9), covering orchestrator-registrable amendments, Planner-routed
  re-planning, and scope-budget re-baselines.
- `methodology/05_release_train.md` (0.2.0): adds Release Mechanics
  Ownership (Section 6), assigning changelog roll-up, date-stamping, and tag
  creation to the release-manager/orchestrator role.

## [0.1.0] - 2026-07-08

### Added

- Framework genesis: the Nizam hybrid mono-repo, shipping six governance
  modules as a single portable payload — `standard/` (documentation standard,
  governance inheritance protocol, agent governance framework, universal
  anti-hallucination constraints), `methodology/` (planning enforcement,
  contract-first execution harness, adversarial TDD, circuit breaker,
  tool-driven state, release train), `registry/` (the `NIZAM.json` index
  schema and scope-definition patterns), `templates/` (consumer-repo
  CONTEXT/AGENTS/DEBT/ADR/work-packet/phase/manifest templates), `schema/`
  (JSON Schemas for every machine-readable framework artifact), and `tools/`
  (the single, unified, runtime-agnostic skill payload).
- `NIZAM.json`, the root machine-readable capability index and context
  router, validating against `registry/nizam-index.schema.json`.
- `bootstrap.sh`, the unified clone → inject → verify governance inheritance
  mechanism (the evolution of the earlier AGIP (a predecessor prototype)) —
  clones a pinned `GOVERNANCE_TAG`, stages and injects `standard/`,
  `templates/`, `schema/`, `tools/`, and `NIZAM.json` into a consumer
  repository's `.nizam/`
  directory, verifies the injection, and records provenance. Supports a
  network-free `--verify-only` drift-detection mode and a `--help` mode.

### Changed

- `methodology/00_planning.md`: the Scope Budget Protocol's per-feature check
  now defines the rolling-average bootstrap rule for when fewer than three
  features have completed.
- `methodology/03_circuit_breaker.md`: Section 4's breach procedure now
  requires discarding untracked/generated artifacts (not just a
  `git reset --hard`) on circuit-breaker trip, and merges the prior two
  separate BLOCKED-state writes into one atomic write single-sourced from the
  phase document's step-level status.
- `standard/AGF.md`: the JSON Verdict Parse Rule now includes a parse-valid
  example verdict block alongside the existing gate-rule fragment.
- `templates/ADR_TEMPLATE.md`, `templates/AGENTS.md`, `templates/README.md`,
  `tools/interface.md`: documentation corrections (PROPOSED default status,
  single-token session-start placeholder, disambiguated `product_spec.md`
  path, corrected checklist section citations).

### Fixed

- `bootstrap.sh`: `--verify-only` now checks for `python3` up front (via
  `require_command python3`), so a python3-less machine gets the clear
  "required command not found" diagnostic instead of a misleading generic
  failure from `check_nizam_index()`/`check_provenance_tag()`.
- NDS compliance: `authoritative_source` frontmatter values across all shipped
  governance `.md` files are now repo-relative (the stale `nizam-framework/`
  prefix is stripped), matching `NIZAM.json`'s existing repo-relative
  precedent.
- NDS compliance: every previously-untagged fenced code block across the
  shipped docs (`standard/AGF.md`, `standard/NDS.md`,
  `methodology/00_planning.md`, `methodology/01_execution.md`,
  `registry/scope_definition_patterns.md`) now carries an honest ```text``` or
  ```json``` language tag per NDS Sec 6.2.
- `.agent/product_spec.md`: `status` corrected from `DRAFT` to the schema-valid
  lowercase `draft`.
- Verdict-shape canonicalization: the JSON verdict shape is now consistent
  across `standard/AGF.md`, `methodology/01_execution.md`, and
  `tools/SKILL.md` on the sibling-array form (`final_verdict` holds only
  `approved`; `issues`, `missing_acceptance_coverage`, and
  `unsupported_claims` are top-level siblings of `final_verdict`, matching
  actual pipeline practice).
