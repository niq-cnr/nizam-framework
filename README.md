# Nizam Framework

**Proportion-scaled, cryptographically verifiable governance for AI-assisted and human software engineering.**

[![Release v1.10.1](https://img.shields.io/badge/release-v1.10.1-0d9488?style=flat-square)](https://github.com/niq-cnr/nizam-framework/releases/tag/v1.10.1)
[![Interactive Guide](https://img.shields.io/badge/docs-Interactive_HTML_Guide-2563eb?style=flat-square)](https://niq-cnr.github.io/nizam-framework/)
[![LLM Index: llms.txt](https://img.shields.io/badge/AI_Index-llms.txt-7c3aed?style=flat-square)](llms.txt)
[![LLM Reference: llms-full.txt](https://img.shields.io/badge/AI_Reference-llms--full.txt-6d28d9?style=flat-square)](llms-full.txt)
[![Dependencies: Zero](https://img.shields.io/badge/dependencies-zero_(POSIX_sh_%2B_Python_3.10%2B)-16a34a?style=flat-square)](#quickstart)
[![License: MIT](https://img.shields.io/badge/license-MIT-475569?style=flat-square)](LICENSE)

Nizam is order, system, and governance distilled into a single, portable payload. It is a
generalised, AI-legible, versioned governance framework: a Hybrid Mono-Repo of standards,
protocols, schemas, and templates that any AI agent or engineering team can consume, in
any runtime, for any project.

Nizam does not ship application code or infrastructure. It ships the rules by which
software gets built responsibly — and the machine-readable index that lets an AI agent
find exactly the rule it needs, without reading everything.

| Audience | Fast-Track Entry Points |
| :--- | :--- |
| **Developers & Engineering Leads** | **Humans start here:** read this README, then explore the **[Interactive HTML User Guide](https://niq-cnr.github.io/nizam-framework/)** ([local source](docs/guide/index.html)) for a visual walkthrough of every design decision, the bootstrap flow, and the execution loop. The three start paths below are also in that guide under "Start paths". Jump straight to **[Quickstart](#quickstart)** to install `.nizam/` in 60 seconds. |
| **AI Agents & LLM Crawlers** | **Agents working on this repository:** start with [AGENTS.md](AGENTS.md), then query `.nizam/NIZAM.json` and load `.nizam/tools/SKILL.md` from the installed release. External LLMs and context indexers can ingest **[`llms.txt`](llms.txt)** (concise index) or **[`llms-full.txt`](llms-full.txt)** (complete single-file CLI, schema, and protocol reference). |

General Availability declared by the operator on 2026-10-10. See the [GA decision](docs/planning/operator_gates.md) for the operator record and explicit evidence exceptions.

**Current development status:** the durable project position is [ROADMAP.md](docs/planning/ROADMAP.md); the active 2026-10-22 engineering direction is the [Jev readiness program](docs/planning/jev-readiness/PROGRAM.md), whose deterministic control repairs are landed locally and awaiting independent verification. `v1.10.1` remains the latest released and installed payload; source work does not change it.

### Copy & Paste Single-Prompt Agent Onboarding (`v1.10.1`)

Want your AI coding agent (Claude Code, Cursor, Antigravity, Codex, Windsurf, or any CLI/IDE agent) to onboard your repository to the latest immutable Nizam release with zero manual setup? **Copy and paste this single prompt into your coding agent:**

```text
Onboard this repository to the Nizam governance framework (immutable release v1.10.1, commit 2b6a4af4d1667aad89cfaab4b1799cb8c9beb9fd):

1. Read https://niq-cnr.github.io/nizam-framework/llms.txt for the Nizam v1.10.1 AI Agent Entry Protocol and CLI reference.
2. Fetch and run the official bootstrap script pinned to v1.10.1 with commit-bound content verification (never overwrite existing AGENTS.md, CONTEXT.md, or CI files):
   curl -fsSL https://raw.githubusercontent.com/niq-cnr/nizam-framework/v1.10.1/bootstrap.sh -o bootstrap.sh && chmod +x bootstrap.sh
   GOVERNANCE_TAG=v1.10.1 ./bootstrap.sh --tag v1.10.1 --expected-sha 2b6a4af4d1667aad89cfaab4b1799cb8c9beb9fd --git-repo .nizam-ref/
   ./bootstrap.sh --verify-only --tag v1.10.1 --expected-sha 2b6a4af4d1667aad89cfaab4b1799cb8c9beb9fd --git-repo .nizam-ref/ --require-content-integrity
3. Query .nizam/NIZAM.json and load .nizam/tools/SKILL.md (resolve paths relative to .nizam/; never edit files inside .nizam/; always set PYTHONDONTWRITEBYTECODE=1).
4. Run `PYTHONDONTWRITEBYTECODE=1 python3 .nizam/tools/start_path.py preflight` and `PYTHONDONTWRITEBYTECODE=1 python3 .nizam/tools/start_path.py status`, then summarize the verified installation and ask what task we should classify first.
```

---

## Why Nizam?

Unstructured AI coding agents fail in predictable ways: they flood their context windows, grade their own homework, mutate Git state behind the operator's back, or spin in infinite retry loops. Heavyweight enterprise frameworks fail in the opposite direction by forcing 5-file specifications onto a 2-line bug fix.

| Common Agentic Delivery Failure | How Nizam Solves It |
| :--- | :--- |
| **Context Window Bloat & Rule Hallucination** | **O(1) Capability Discovery (`NIZAM.json`)**: Agents query a compact JSON index to load only the exact protocol, schema, or template required for the current step. |
| **One-Size-Fits-All Ceremony** | **Proportion-Scaled Routing (`tools/start_path.py classify`)**: Tasks route deterministically into `trivial`, `bugfix`, `small-change`, `standard-feature`, or `high-risk` based on file paths and semantic risk flags. |
| **Self-Grading Agents** | **Adversarial Role Separation (`standard/AGF.md`)**: The **Generator** (`@developer`) cannot approve its own contract or final verification; an independent **Validator** and **Evaluator** (`@reviewer`) audit every feature gate. |
| **Hidden Git Commits & Index Tampering** | **Noncommitting Default & Receipt Pipeline (`publish` / `build-receipt`)**: Read and preparation paths preserve `HEAD`, refs, and `.git/index` byte-for-byte. Actual Git publication requires an explicit `NIZAM_MUTATION_ADAPTER` and produces a two-stage cryptographic receipt (`stage-receipt-<stage>.json`). |
| **Blind Retry Loops or Premature 3-Strike Stops** | **Work-Specific Stopping Rules & Lineage (`capture`)**: A 3-attempt initial strategy ladder transitions cleanly into Attempt 4+ when invariants hold and a new `--Diagnostic-Hypothesis` + `--Refined-Scope` is recorded, while halting (`exit 2`) immediately on invariant breaches or repeated identical defect signatures. |
| **Supply-Chain Drift in Installed Rules** | **Commit-Bound Verification (`bootstrap.sh --verify-only`)**: Consumer installations pin an immutable release tag (`v1.10.1`) and verify every installed file, mode, and SHA-256 digest against the expected commit SHA without executing code from inside `.nizam/`. |

---

## Architecture at a Glance

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                        CONSUMER REPOSITORY WORKSPACE                         │
│                                                                              │
│  ┌────────────────────────────────────┐  ┌────────────────────────────────┐  │
│  │ .nizam/ (Immutable Release v1.10.1)│  │ .agent/ (Live Project State)   │  │
│  │ ├── NIZAM.json (Machine Index)     │  │ ├── run_state.json             │  │
│  │ ├── provenance.json (Commit Pin)   │  │ ├── lightweight_log.jsonl      │  │
│  │ ├── tools/ (SKILL.md, start_path)  │  │ ├── contracts/NNN.json         │  │
│  │ ├── standard/ (NDS, AGF, GIP...)   │  │ ├── validator/ & qa/           │  │
│  │ ├── methodology/ (00..03)          │  │ └── evidence/<id>/             │  │
│  │ ├── schema/ & templates/           │  │     ├── capture-*.json         │  │
│  │ └── ecosystem/ (9-Stage Cycle)     │  │     └── stage-receipt-*.json   │  │
│  └─────────────────┬──────────────────┘  └───────────────▲────────────────┘  │
│                    │ 1. Query Index & Classify           │ 3. Exclusive      │
│                    ▼                                     │    Evidence &     │
│  ┌───────────────────────────────────────────────────────┴────────────────┐  │
│  │                     tools/start_path.py Workflow                       │  │
│  │                                                                        │  │
│  │  • trivial / bugfix / small-change ──► begin ──► verify ──► done       │  │
│  │  • standard-feature / high-risk    ──► preflight ──► capture ──►       │  │
│  │                                        publish (prepare|publish|       │  │
│  │                                        finalize) ──► resume            │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

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

### Route Selection Matrix (`tools/start_path.py classify`)

| Route | Typical Scope & Trigger | Pre-Code Gate | Completion Gate | CLI Entry & Closeout |
| :--- | :--- | :--- | :--- | :--- |
| **`trivial`** | `<= 2` low-risk files (docs, comments, formatting), zero risk flags | Recorded intent (`.agent/evidence/<id>-intent.json`) | Recorded verification result (`.agent/qa/<id>.json`) | `tools/start_path.py begin trivial --id <id>` / `done trivial --id <id>` |
| **`bugfix`** | Scoped defect repair (`--bugfix`) within existing behavior boundaries | Assessed cause + scoped fix (`<id>-cause.json`, `<id>-scope.json`) | Recorded verification result (`.agent/qa/<id>.json`) | `tools/start_path.py begin bugfix --id <id>` / `done bugfix --id <id>` |
| **`small-change`** | `<= 3` files of unambiguous non-feature maintenance, zero risk flags | Recorded intent (`.agent/evidence/<id>-intent.json`) | Recorded verification result (`.agent/qa/<id>.json`) | `tools/start_path.py begin small-change --id <id>` / `done small-change --id <id>` |
| **`standard-feature`** | New capability (`--new-feature`) or `> 3` files across components | Approved `.agent/contracts/NNN.json` (`validator` + `qa` pre-code verdicts) | Independent post-implementation check + recorded verification result + stage receipts | `tools/start_path.py preflight` → `capture` → `publish` → `resume` |
| **`high-risk`** | Protected paths (`schema/`, `standard/`, `.github/workflows/`, `bootstrap.sh`, `NIZAM.json`) or `--breaking-change` / `--security-sensitive` / `--authority-change` | Approved contract + explicit Human Operator gate (`E1`) | Full feature verification stack + receipt-qualified transitions | `tools/start_path.py classify` → Operator gate → full contract loop |

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

---

## Quickstart

### 1. Bootstrap `.nizam/` from an Immutable Release Tag

Fetch `bootstrap.sh` pinned to the latest released tag and run it against your repo:

```sh
curl -fsSL https://raw.githubusercontent.com/niq-cnr/nizam-framework/v1.10.1/bootstrap.sh -o bootstrap.sh
chmod +x bootstrap.sh
GOVERNANCE_TAG=v1.10.1 ./bootstrap.sh --tag v1.10.1 --expected-sha 2b6a4af4d1667aad89cfaab4b1799cb8c9beb9fd --git-repo .nizam-ref/
```

`--tag v1.10.1` (equivalently `GOVERNANCE_TAG=v1.10.1`) pins the inheritance to a real
released tag — never a floating branch (`main`, `master`, `HEAD` are all refused). The
current bootstrap verifies `--expected-sha` before staging, fetches the tag with a
Git **blob filter** (`blob:none`), sparse-materializes only the payload roots below,
stages and verifies the payload, and atomically installs it under `.nizam/` (the
default target). Development-only paths — `.agent/`, `.nizam/`, `docs/`, `registry/`
and the historical evidence archive — are neither downloaded as blobs nor checked out.
The installer fails closed if the transport cannot honor the filter instead of silently
performing a full download. The published `v1.10.1` script predates this retrieval
change: the pinned example commands below remain valid for that immutable release,
while the `bootstrap.sh` at this repository's HEAD uses the filtered/sparse path for
the next release.

Passing `--git-repo .nizam-ref/` (outside `.nizam/`) retains the verified **sparse**
reference: only the selected payload working files plus the Git commit/tree/blob objects
needed for later offline `--verify-only` checks. `.nizam-ref/` is ignored by Git and is
never part of the framework history. Offline verification sets `GIT_NO_LAZY_FETCH=1`
and fails with a precise diagnostic when a required local object is absent; it never
silently re-downloads missing history.
What you get:

```text
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

### 2. Re-Verify Payload Integrity Anytime (`--verify-only`)

Re-verify an installed `.nizam/` payload at any time with `bootstrap.sh --verify-only`
(which never executes code from inside `.nizam/`):

```sh
# Commit-bound content-integrity verification (verifies every file, mode, and digest against the expected commit in --git-repo):
./bootstrap.sh --verify-only --tag v1.10.1 --expected-sha 2b6a4af4d1667aad89cfaab4b1799cb8c9beb9fd --git-repo .nizam-ref/ --require-content-integrity

# Unbound directory comparison (reports content_integrity=directory_match_unbound; does not satisfy --expected-sha or --require-content-integrity):
./bootstrap.sh --verify-only --tag v1.10.1 --source-root /path/to/unpacked-release/

# Structural and provenance-pin check only (reports structural_only; content_integrity=not_checked):
./bootstrap.sh --verify-only --tag v1.10.1 --structural-only
```

### Repository footprint and historical evidence

The ordinary checkout no longer carries every completed feature's raw evidence
transcript. `.agent/evidence-archive/index.json` binds each archived path to the Git
blob that still holds its bytes in ordinary history. The active tree keeps current
acceptance evidence, contracts, QA records, run state and authority records.

```sh
# Verify the archive offline (no fetch, no ref mutation, no code execution)
PYTHONDONTWRITEBYTECODE=1 python3 tools/evidence_archive.py verify

# Materialize one completed tranche into a fresh directory outside the checkout
PYTHONDONTWRITEBYTECODE=1 python3 tools/evidence_archive.py restore \
  --tranche feature-133 --output /tmp/nizam-evidence-133
```

Validator check C16 resolves an archived path only for a completed feature whose
recorded contract/QA digests still match. A reopened or changed feature, a new current
acceptance attempt, or a missing current artifact still requires fresh on-disk evidence;
archived bytes are historical integrity, never a fresh test pass. New captures that need
input-integrity evidence use `tools/evidence_preservation.py`, which stores one
content-addressed inventory per unchanged input set and keeps each run's command,
producer and timings in a separate receipt.

### 3. Classify & Govern Your First Change

```sh
# 1. Classify candidate paths into trivial | bugfix | small-change | standard-feature | high-risk
PYTHONDONTWRITEBYTECODE=1 python3 .nizam/tools/start_path.py classify \
  --paths src/parser.py tests/test_parser.py --bugfix

# 2. Check concise read-only governance status
PYTHONDONTWRITEBYTECODE=1 python3 .nizam/tools/start_path.py status
```

See the [v1.10.1 release](https://github.com/niq-cnr/nizam-framework/releases/tag/v1.10.1)
and the [v0.9.0 → v1.0.0 migration guide](docs/migration-v1.0.0.md), and run
`tools/validate.sh` (the same repo-local compliance check that
`.github/workflows/compliance.yml` runs in CI, and that its rationale is recorded in the
`docs/architecture/` ADRs) to confirm a bootstrapped target stays compliant.

---

## AI Agent & LLM Quick-Load (`llms.txt`)

Nizam is built from the ground up for machine legibility. In addition to `.nizam/NIZAM.json` and `.nizam/tools/SKILL.md`, this repository and its GitHub Pages site publish standard [`llmstxt.org`](https://llmstxt.org/) endpoints:

| Artifact | Local Path | Hosted URL (GitHub Pages) | Purpose |
| :--- | :--- | :--- | :--- |
| **`llms.txt`** | [`llms.txt`](llms.txt) | `https://niq-cnr.github.io/nizam-framework/llms.txt` | Concise, structured index of the AI Agent Entry Protocol, 5 start paths, CLI commands, standards, and schemas. |
| **`llms-full.txt`** | [`llms-full.txt`](llms-full.txt) | `https://niq-cnr.github.io/nizam-framework/llms-full.txt` | Complete single-file technical reference covering every `start_path.py` subcommand, flag, stopping rule, role profile, permission class (`R0`–`E1`), and validation check (`C1`–`C16`). |
| **`NIZAM.json`** | [`NIZAM.json`](NIZAM.json) | — | Machine-queryable capability index mapped into `.nizam/NIZAM.json` in consumer repositories. |
| **`SKILL.md` / `skill.json`** | [`tools/SKILL.md`](tools/SKILL.md) | — | Runtime-agnostic skill definition and adapter contract (`tools/skill.json`). |

### Canonical 4-Step Protocol for AI Coding Agents

1. **Discover**: Read `.nizam/NIZAM.json` and `.nizam/tools/SKILL.md` (resolve paths relative to `.nizam/`). Never modify files inside `.nizam/`. Always pass `PYTHONDONTWRITEBYTECODE=1` when invoking Python tools.
2. **Classify**: Run `PYTHONDONTWRITEBYTECODE=1 python3 .nizam/tools/start_path.py classify --paths <files...>` before planning or editing.
3. **Execute & Capture**:
   - For `trivial`, `bugfix`, or `small-change`: gate entry with `start_path.py begin <route> --id <id>` and close out with `start_path.py done <route> --id <id>`.
   - For `standard-feature` or `high-risk`: run `start_path.py preflight`, record exclusive verification outputs via `start_path.py capture`, and use `start_path.py amend-contract` for bounded mechanical scope/verification updates when goals and invariants are unchanged.
4. **Publish & Transition Without Hidden Mutations**: Use `start_path.py publish` (defaults to `--mode prepare`, noncommitting) and `start_path.py build-receipt` with an operator-configured `NIZAM_MUTATION_ADAPTER` for two-stage receipt-qualified commits, and `start_path.py resume` for receipt-verified state transitions.

---

## Local governance

This repository has installed its public `v1.10.1` governance under `.nizam/`.
The installed payload is verified byte-for-byte against the pinned tag by the
standing `self_governance` CI job (`verify_self_governance.py` and
`bootstrap.sh --verify-only`, both backed by `tools/payload_integrity.py`).
When a release tag `vX.Y.Z` is cut on this repository, the consumer payload
defined by that tag is the six authored root modules (`standard/`,
`methodology/`, `templates/`, `schema/`, `tools/`, `ecosystem/`) plus root
`NIZAM.json` packaged by `bootstrap.sh` — never the repository's own `.nizam/`
directory (which at tag creation time still records the prior self-installed
release until a post-release self-adoption commit updates `.nizam/`).
Commissioning of this release (clean installed preflight, baseline and
independent QA) has not been performed. The earlier commissioning at assessed
source candidate `bfd475f` remains recorded in `docs/planning/SELF_GOVERNANCE.md`.
The [self-governance record](docs/planning/SELF_GOVERNANCE.md) records the exact pin,
operator authorization and current stage. Root framework modules remain the
authored product; local agent work follows the installed governance.

---

## Design Decisions

- **DD-1 — Tool-Driven State Management.** Agents query the root `NIZAM.json` index to
  find the minimal governance files a task needs, instead of bulk-reading directories.
  See [ADR-001](docs/architecture/ADR-001-hybrid-monorepo-topology.md) and
  [ADR-002](docs/architecture/ADR-002-declarative-capability-index.md).
- **DD-2 — Universal Circuit Breaker.** Every execution loop embeds a work-specific
  diagnostic stopping and circuit-breaker policy: attempt counters drive escalating
  investigative posture or bounded decomposition when invariants hold, while invariant
  breaches, specification contradictions, or repeated unresolved defect signatures halt
  the loop, mark it blocked, and escalate.
- **DD-3 — Evidence Externalisation.** Proof of work lives in files referenced by path,
  never pasted inline into YAML or JSON state.
- **DD-4 — Unified Skill Payload.** Exactly one skill payload under `tools/`, loaded by
  any runtime through a single adapter interface — no per-runtime forks.
- **DD-5 — Zero-Dependency POSIX Bootstrap.** Consumer installation and verification
  require only POSIX `sh`, `git`, and Python 3.10+ standard library — see
  [ADR-003](docs/architecture/ADR-003-zero-dependency-posix-bootstrap.md).

---

## Modules

| Module | Installed In `.nizam/`? | Purpose |
| :--- | :---: | :--- |
| [`schema/`](schema/nizam_index.schema.json) | Yes | JSON Schemas (Draft 2020-12) for every machine-readable framework artifact (`NIZAM.json`, `run_state.json`, `provenance.json`, `skill.json`, contracts, QA/validator verdicts, receipts). |
| [`standard/`](standard/AGF.md) | Yes | The Nizam Documentation Standard ([NDS](standard/NDS.md)), the Agent Governance Framework ([AGF](standard/AGF.md)), the Governance Inheritance Protocol ([GIP](standard/GIP.md)), [anti-hallucination constraints](standard/anti_hallucination.md), and the constitutional policy set ([capability profiles](standard/capability_profiles.md), [CI gates](standard/ci_gates.md), [MCP policy](standard/mcp_policy.md), [failure modes](standard/failure_modes.md), [provenance](standard/provenance.md), [permission classes](standard/permission_classes.md), [cross-repo governance](standard/cross_repo_governance.md)). |
| [`methodology/`](methodology/00_planning.md) | Yes | End-to-end delivery lifecycle: [00 Planning](methodology/00_planning.md), [01 Execution](methodology/01_execution.md), [02 Quality & Circuit Breaker](methodology/02_quality.md), and [03 Release Train](methodology/03_release.md). |
| [`templates/`](templates/AGENTS.md.tpl) | Yes | Consumer-repo document and manifest templates (`AGENTS.md.tpl`, `contract.json.tpl`, `product_spec.md.tpl`, `run_state.json.tpl`, `qa_verdict.json.tpl`, `validator_verdict.json.tpl`). |
| [`tools/`](tools/SKILL.md) | Yes | The single runtime-agnostic skill payload ([`SKILL.md`](tools/SKILL.md), [`skill.json`](tools/skill.json), [`interface.md`](tools/interface.md)) plus executable governance CLIs (`start_path.py`, `payload_integrity.py`, `validate.sh`). |
| [`ecosystem/`](ecosystem/README.md) | Yes | The reusable 9-stage **Bootstrap → Preflight → Baseline → Audit → Plan → Execute → Verify → Promote → Compare** lifecycle and 7 typed handoff contracts (`H-01`..`H-06`, `H-CONSUMER-UPGRADE`). |
| [`registry/`](registry/README.md) | Authoring repo | The `NIZAM.json` index schema documentation and scope-definition patterns. |
| [`docs/`](docs/guide/index.html) | Authoring repo | Architecture Decision Records (`docs/architecture/`), versioned migration guidance ([`docs/migration-v1.0.0.md`](docs/migration-v1.0.0.md)), and the self-contained [HTML user guide](docs/guide/index.html). |

---

## Automated Compliance Suite (`tools/validate.sh`)

Every pull request and release tag is gated by 16 deterministic checks (`C1`–`C16`) executed by `PYTHONDONTWRITEBYTECODE=1 bash tools/validate.sh`:

| Check | Invariant Verified |
| :--- | :--- |
| **`C1`–`C4`** | Root structure, YAML frontmatter across all `.md` files, `NIZAM.json` path resolution, and JSON Schema syntax. |
| **`C5`–`C8`** | Zero internal branding/cluster leakage, Markdown link resolution, template index coverage, and `ecosystem/` handoff catalog integrity. |
| **`C9`–`C11`** | `docs/guide/index.html` path resolution, module/discovery/version consistency with `NIZAM.json`, and `tools/skill.json` ↔ `tools/SKILL.md` synchronization. |
| **`C12`–`C16`** | `.agent/run_state.json` schema compliance, self-governance lockstep (`AGENTS.md` ↔ `.nizam/`), `payload_integrity.py` self-check, `test_start_path.py` unit suite, and `test_public_entry.py` public entry contract. |

---

## Versioning

Nizam is released as semantically versioned git tags (`vMAJOR.MINOR.PATCH`). See
[CHANGELOG.md](CHANGELOG.md) for the version history. Consumer repos pin to a specific tag when
bootstrapping — never to a floating branch.

## License

Licensed under the MIT License — see [LICENSE](LICENSE).
