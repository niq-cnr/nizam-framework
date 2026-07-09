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
**Agents:** load `tools/SKILL.md` (discovered via the root `NIZAM.json` capability index)
as your instructions payload — do not bulk-read the governance directories.

## Quickstart

Fetch `bootstrap.sh` pinned to the latest released tag and run it against your repo:

```sh
curl -fsSL https://raw.githubusercontent.com/niq-cnr/nizam-framework/v0.5.0/bootstrap.sh -o bootstrap.sh
chmod +x bootstrap.sh
GOVERNANCE_TAG=v0.5.0 ./bootstrap.sh --tag v0.5.0
```

`--tag v0.5.0` (equivalently `GOVERNANCE_TAG=v0.5.0`) pins the inheritance to a real
released tag — never a floating branch (`main`, `master`, `HEAD` are all refused). This
clones the pinned tag, stages the governance payload, verifies it landed correctly, and
atomically installs it under `.nizam/` (the default target). What you get:

```
.nizam/
├── standard/
├── templates/
├── schema/
├── tools/
├── NIZAM.json
└── provenance.json
```

See the [v0.5.0 release](https://github.com/niq-cnr/nizam-framework/releases/tag/v0.5.0)
for release notes, and run `tools/validate.sh` (the same repo-local compliance check that
`.github/workflows/compliance.yml` runs in CI, and that its rationale is recorded in the
`docs/architecture/` ADRs) to confirm a bootstrapped target stays compliant.

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
| `standard/` | The Nizam Documentation Standard (NDS), the Agent Governance Framework (AGF), the Governance Inheritance Protocol (GIP), and the anti-hallucination constraints. |
| `methodology/` | Planning, execution, adversarial TDD, circuit breaker, release train. |
| `templates/` | Consumer-repo document and manifest templates. |
| `tools/` | The single runtime-agnostic skill payload. |
| `registry/` | The `NIZAM.json` index schema and scope-definition patterns. |
| `docs/` | Architecture Decision Records and the self-contained HTML user guide. |

## Versioning

Nizam is released as semantically versioned git tags (`vMAJOR.MINOR.PATCH`). See
`CHANGELOG.md` for the version history. Consumer repos pin to a specific tag when
bootstrapping — never to a floating branch.

## License

Licensed under the MIT License — see [LICENSE](LICENSE).
