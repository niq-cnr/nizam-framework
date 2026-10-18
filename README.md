# Nizam

Nizam is order, system, and governance distilled into a single, portable payload. It is a
generalised, AI-legible, versioned governance framework: a Hybrid Mono-Repo of standards,
protocols, schemas, and templates that any AI agent or engineering team can consume, in
any runtime, for any project.

Nizam does not ship application code or infrastructure. It ships the rules by which
software gets built responsibly — and the machine-readable index that lets an AI agent
find exactly the rule it needs, without reading everything.

**Humans start here:** read this README, then the full [HTML user guide](docs/guide/index.html)
for a walkthrough of every design decision, the bootstrap flow, and the execution loop.
The three start paths below are also in that guide under "Start paths".
**Agents working on this repository:** start with [AGENTS.md](AGENTS.md), then query
`.nizam/NIZAM.json` and load `.nizam/tools/SKILL.md` from the installed release.

General Availability declared by the operator on 2026-10-10. See the [GA decision](docs/planning/operator_gates.md) for the operator record and explicit evidence exceptions.

## Start paths

Three ways to begin work. They use the same Planner, Generator, Validator, and
Evaluator roles already described in the user guide. The feature path is the full
contract loop. The bug-fix path and the small-change path are shorter routes over
those roles, not a second process. A reader does not need to open `methodology/`
to see which path to use.

These paths cover documented properties of other public toolkits: Spec Kit's
specify-before-build sequence, Spec Kit's assessed-cause bug repair, Superpowers'
design-then-plan and quick-task entries, and BMAD Method's right-sized process.
This README does not rank Nizam against those projects. A comparison sentence
belongs only beside a recorded run of the preregistered study in
[docs/planning/agentic-excellence.md](docs/planning/agentic-excellence.md). That
study has not been executed.

### New feature

Specify what to build and agree the design before planning the implementation.
This is the feature path.

Artifacts this path leaves:

- `.agent/product_spec.md` and `.agent/feature_list.json` — the specification.
- `.agent/contracts/NNN.json` — scope, non-goals, and verification commands.
  It starts at `status: "proposed"`.
- An independent pre-code verdict under `.agent/validator/` and a contract-review
  verdict under `.agent/qa/`. Together they approve the contract.
- After implementation, an independent post-implementation check under
  `.agent/validator/` and a recorded verification result under `.agent/qa/`,
  with command output under `.agent/evidence/`.

Implementation may begin only after the contract is approved. The feature is not
done until that independent post-implementation check and that recorded
verification result both exist. Each verdict counts only when `approved` is
true and `issues`, `missing_acceptance_coverage`, and `unsupported_claims` are
empty.

### Bug fix

Record an assessed cause, a scoped fix, and a recorded verification result.
This is the bug-fix path.

Artifacts this path leaves:

- `.agent/evidence/<id>-cause.json` — the assessed cause.
- `.agent/evidence/<id>-scope.json` — the scoped fix: the files in scope and
  the non-goals.
- `.agent/qa/<id>.json` — the recorded verification result, with command output
  under `.agent/evidence/`.

Implementation may begin once the assessed cause and the scoped fix are both
recorded. `tools/start_path.py begin bugfix --id <id>` is that decision: it
exits 0 only when those two records validate. The bug fix is not done until
the recorded verification result exists, which
`tools/start_path.py done bugfix --id <id>` checks. A repair that stays inside
an already approved contract does not open a new feature specification or
repeat the feature path's pre-code contract gates.

### Small unambiguous change

Record the intent, make the change, and record a verification result. This is
the small-change path, for a change whose outcome is already unambiguous.

Artifacts this path leaves:

- `.agent/evidence/<id>-intent.json` — the intent.
- `.agent/qa/<id>.json` — the recorded verification result, with command output
  under `.agent/evidence/`.

Implementation may begin once the intent is recorded. `tools/start_path.py begin small-change --id <id>` is that decision, and `tools/start_path.py done small-change --id <id>` checks the recorded verification result. The small-change path records intent and a verification result and does not require the full feature-gate stack. Use the feature path when the change needs a new contract.

## Quickstart

Fetch `bootstrap.sh` pinned to the latest released tag and run it against your repo:

```sh
curl -fsSL https://raw.githubusercontent.com/niq-cnr/nizam-framework/v1.7.0/bootstrap.sh -o bootstrap.sh
chmod +x bootstrap.sh
GOVERNANCE_TAG=v1.7.0 ./bootstrap.sh --tag v1.7.0
```

`--tag v1.7.0` (equivalently `GOVERNANCE_TAG=v1.7.0`) pins the inheritance to a real
released tag — never a floating branch (`main`, `master`, `HEAD` are all refused). This
clones the pinned tag, stages the governance payload, verifies it landed correctly, and
atomically installs it under `.nizam/` (the default target). What you get:

```
.nizam/
├── standard/
├── templates/
├── schema/
├── tools/
├── methodology/
├── ecosystem/
├── NIZAM.json
└── provenance.json
```

See the [v1.7.0 release](https://github.com/niq-cnr/nizam-framework/releases/tag/v1.7.0)
and the [v0.9.0 → v1.0.0 migration guide](docs/migration-v1.0.0.md), and run
`tools/validate.sh` (the same repo-local compliance check that
`.github/workflows/compliance.yml` runs in CI, and that its rationale is recorded in the
`docs/architecture/` ADRs) to confirm a bootstrapped target stays compliant.

## Local governance

This repository has installed its public `v1.6.0` governance under `.nizam/`.
The installed payload is verified byte-for-byte against the pinned tag by the
standing `self_governance` CI job. Commissioning of this release (clean
installed preflight, baseline and independent QA) has not been performed.
The earlier commissioning at assessed source candidate `bfd475f` remains
recorded in `docs/planning/SELF_GOVERNANCE.md`.
The [self-governance record](docs/planning/SELF_GOVERNANCE.md) records the exact pin,
operator authorization and current stage. Root framework modules remain the
authored product; local agent work follows the installed governance.

## Design Decisions

- **DD-1 — Tool-Driven State Management.** Agents query the root `NIZAM.json` index to
  find the minimal governance files a task needs, instead of bulk-reading directories.
- **DD-2 — Universal Circuit Breaker.** Every execution loop embeds a mandatory 3-strike
  breaker: three failed attempts halts the loop, marks it blocked, and escalates.
- **DD-3 — Evidence Externalisation.** Proof of work lives in files referenced by path,
  never pasted inline into YAML or JSON state.
- **DD-4 — Unified Skill Payload.** Exactly one skill payload under `tools/`, loaded by
  any runtime through a single adapter interface — no per-runtime forks.

## Modules

| Module | Purpose |
|--------|---------|
| `schema/` | JSON Schemas for every machine-readable framework artifact. |
| `standard/` | The Nizam Documentation Standard (NDS), the Agent Governance Framework (AGF), the Governance Inheritance Protocol (GIP), the anti-hallucination constraints, and the constitutional policy set (capability profiles, CI gates, MCP policy, failure modes, provenance, permission classes, cross-repo governance). |
| `methodology/` | Planning, execution, adversarial TDD, circuit breaker, release train. |
| `templates/` | Consumer-repo document and manifest templates. |
| `tools/` | The single runtime-agnostic skill payload. |
| `registry/` | The `NIZAM.json` index schema and scope-definition patterns. |
| `ecosystem/` | The reusable Bootstrap → Preflight → Baseline → Audit → Plan → Execute → Verify → Promote → Compare lifecycle for one or many repositories. |
| `docs/` | Architecture Decision Records, versioned migration guidance, and the self-contained HTML user guide. |

## Versioning

Nizam is released as semantically versioned git tags (`vMAJOR.MINOR.PATCH`). See
`CHANGELOG.md` for the version history. Consumer repos pin to a specific tag when
bootstrapping — never to a floating branch.

## License

Licensed under the MIT License — see [LICENSE](LICENSE).
