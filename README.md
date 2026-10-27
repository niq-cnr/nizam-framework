# Nizam Framework

**Proportion-scaled, cryptographically verifiable governance for AI-assisted and human software engineering.**

[![Release v2.0.0](https://img.shields.io/badge/release-v2.0.0-0d9488?style=flat-square)](https://github.com/niq-cnr/nizam-framework/releases/tag/v2.0.0)
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

**Current development status:** the durable project position is [ROADMAP.md](docs/planning/ROADMAP.md); the Jev readiness foundation (deterministic governance repairs and the provider-neutral semantic architecture) is merged and off-by-default, with live qualification still gated. `v2.0.0` is the latest official release at `603afc7b17919334a6a01df1e39e63798d9d0acd` and is now the official local `.nizam/` installation. Commit-bound integrity and installed high-risk preflight passed; full consumer commissioning remains incomplete. Discover the active workspace pin from `.nizam/provenance.json`; prior experimental source installations remain separate historical records.

### Copy & Paste Single-Prompt Agent Onboarding (`v2.0.0`)

The published annotated `v2.0.0` tag resolves to `603afc7b17919334a6a01df1e39e63798d9d0acd`.
Existing consumers must follow the [v2.0.0 migration guide](docs/migration-v2.0.0.md)
and record their own upgrade authorization before adopting it.

Want your AI coding agent (Claude Code, Cursor, Antigravity, Codex, Windsurf, or any CLI/IDE agent) to onboard your repository to the latest immutable Nizam release with zero manual setup? **Copy and paste this single prompt into your coding agent:**

```text
Onboard this repository to the Nizam governance framework (immutable release v2.0.0, commit 603afc7b17919334a6a01df1e39e63798d9d0acd):

1. Read https://niq-cnr.github.io/nizam-framework/llms.txt for the Nizam v2.0.0 AI Agent Entry Protocol and CLI reference.
2. Fetch and run the official bootstrap script pinned to v2.0.0 with commit-bound content verification (never overwrite existing AGENTS.md, CONTEXT.md, or CI files):
   curl -fsSL https://raw.githubusercontent.com/niq-cnr/nizam-framework/v2.0.0/bootstrap.sh -o bootstrap.sh && chmod +x bootstrap.sh
   GOVERNANCE_TAG=v2.0.0 ./bootstrap.sh --tag v2.0.0 --expected-sha '603afc7b17919334a6a01df1e39e63798d9d0acd' --git-repo .nizam-ref/
   ./bootstrap.sh --verify-only --tag v2.0.0 --expected-sha '603afc7b17919334a6a01df1e39e63798d9d0acd' --git-repo .nizam-ref/ --require-content-integrity
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
| **Blind Retry Loops or Premature 3-Strike Stops** | **Work-Specific Stopping Rules & Lineage (`capture`)**: Failures are bounded across the whole task: six failed executions total and three with one signature, plus finite configured step limits. Only explicit finite operator recovery can reopen an exhausted budget; successes, hypotheses, amendments and decomposition labels do not reset it. |
| **Supply-Chain Drift in Installed Rules** | **Commit-Bound Verification (`bootstrap.sh --verify-only`)**: Consumer installations pin an immutable release tag (`v2.0.0`) and verify every installed file, mode, and SHA-256 digest against the expected commit SHA without executing code from inside `.nizam/`. |

---

## Architecture at a Glance

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                        CONSUMER REPOSITORY WORKSPACE                         │
│                                                                              │
│  ┌────────────────────────────────────┐  ┌────────────────────────────────┐  │
│  │ .nizam/ (Immutable Release v2.0.0)│  │ .agent/ (Live Project State)   │  │
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

Before `begin`, pin typed verification in the intent/scope or approved contract.
Completion requires assessed per-check captures, not a passing summary alone;
see [v2.0.0 migration](docs/migration-v2.0.0.md) and [the producer interface](tools/interface.md#45-structured-qa-proof-for-completion-and-receipt-prerequisites).

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
curl -fsSL https://raw.githubusercontent.com/niq-cnr/nizam-framework/v2.0.0/bootstrap.sh -o bootstrap.sh
chmod +x bootstrap.sh
GOVERNANCE_TAG=v2.0.0 ./bootstrap.sh --tag v2.0.0 --expected-sha '603afc7b17919334a6a01df1e39e63798d9d0acd' --git-repo .nizam-ref/
```

`--tag v2.0.0` (equivalently `GOVERNANCE_TAG=v2.0.0`) pins the inheritance to a real
released tag — never a floating branch (`main`, `master`, `HEAD` are all refused). The
current bootstrap verifies `--expected-sha` before staging, fetches the tag with a
Git **blob filter** (`blob:none`), sparse-materializes only the payload roots below,
stages and verifies the payload, and atomically installs it under `.nizam/` (the
default target). Development-only paths — `.agent/`, `.nizam/`, `docs/`, `registry/`
and the historical evidence archive — are neither downloaded as blobs nor checked out.
The installer fails closed if the transport cannot honor the filter instead of silently
performing a full download.

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
./bootstrap.sh --verify-only --tag v2.0.0 --expected-sha '603afc7b17919334a6a01df1e39e63798d9d0acd' --git-repo .nizam-ref/ --require-content-integrity

# Unbound directory comparison (reports content_integrity=directory_match_unbound; does not satisfy --expected-sha or --require-content-integrity):
./bootstrap.sh --verify-only --tag v2.0.0 --source-root /path/to/unpacked-release/

# Structural and provenance-pin check only (reports structural_only; content_integrity=not_checked):
./bootstrap.sh --verify-only --tag v2.0.0 --structural-only
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

See the [v2.0.0 release](https://github.com/niq-cnr/nizam-framework/releases/tag/v2.0.0)
and the [v1.x → v2.0.0 migration guide](docs/migration-v2.0.0.md), and run
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

The official local installation is `v2.0.0` at `603afc7b17919334a6a01df1e39e63798d9d0acd`,
installed at `2026-10-24T05:45:45Z` (`316` released files + `provenance.json`).
The trusted pin verifier, commit-bound bootstrap verification and installed
high-risk preflight passed. Earlier experimental source installations remain
historical records; this adoption uses the published immutable tag. Discover
workspace installation facts from `.nizam/provenance.json`.
The public installed payload is verified byte-for-byte against its pinned tag by the
standing `self_governance` CI job (`verify_self_governance.py` and
`bootstrap.sh --verify-only`, both backed by `tools/payload_integrity.py`).
When a release tag `vX.Y.Z` is cut on this repository, the consumer payload
defined by that tag is the six authored root modules (`standard/`,
`methodology/`, `templates/`, `schema/`, `tools/`, `ecosystem/`) plus root
`NIZAM.json` packaged by `bootstrap.sh` — never the repository's own `.nizam/`
directory (which at tag creation time still records the prior self-installed
release until a post-release self-adoption commit updates `.nizam/`).
Installed integrity and preflight checks do not establish full commissioning:
a fresh consumer baseline and independent consumer QA have not been completed. The earlier commissioning at assessed
source candidate `bfd475f` remains recorded in `docs/planning/SELF_GOVERNANCE.md`.
The [self-governance record](docs/planning/SELF_GOVERNANCE.md) records the exact pin,
operator authorization and current stage. Root framework modules remain the
authored product; local agent work follows the installed governance.

---

## Design Decisions

- **DD-1 — Tool-Driven State Management.** Agents query the root `NIZAM.json` index to
  find the minimal governance files a task needs, instead of bulk-reading directories.
  See [tool-driven state](methodology/04_tool_driven_state.md) and the
  [root capability index](NIZAM.json).
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
  [bootstrap.sh](bootstrap.sh) and the [inheritance protocol](standard/GIP.md).

---

## Modules

| Module | Installed In `.nizam/`? | Purpose |
| :--- | :---: | :--- |
| [`schema/`](schema/README.md) | Yes | JSON Schemas (Draft 2020-12) for the declared artifact families, including the planning manifest, feature lists, contracts, QA verdicts and run state. The governance skill manifest has its own schema; the root capability index schema lives in `registry/`. See each schema's documented validation surface. |
| [`standard/`](standard/AGF.md) | Yes | The Nizam Documentation Standard ([NDS](standard/NDS.md)), the Agent Governance Framework ([AGF](standard/AGF.md)), the Governance Inheritance Protocol ([GIP](standard/GIP.md)), [anti-hallucination constraints](standard/anti_hallucination.md), and the constitutional policy set ([capability profiles](standard/capability_profiles.md), [CI gates](standard/ci_gates.md), [MCP policy](standard/mcp_policy.md), [failure modes](standard/failure_modes.md), [provenance](standard/provenance_policy.md), [permission classes](standard/permission_classes.md), [cross-repo governance](standard/cross_repo_governance.md)). |
| [`methodology/`](methodology/00_planning.md) | Yes | End-to-end delivery lifecycle: [00 Planning](methodology/00_planning.md), [01 Execution](methodology/01_execution.md), [02 Adversarial TDD](methodology/02_adversarial_tdd.md), [03 Circuit Breaker](methodology/03_circuit_breaker.md), and [06 Release Train](methodology/06_release_train.md). |
| [`templates/`](templates/README.md) | Yes | Consumer templates: `AGENTS.md`, `CONTEXT.md`, `DEBT.md`, `ADR_TEMPLATE.md`, `work-packet.template.json`, `phase_template.yaml`, `manifest.template.json`, `DoD.md`, and `convergent-review-prompt.md`. |
| [`tools/`](tools/SKILL.md) | Yes | The single runtime-agnostic skill payload ([`SKILL.md`](tools/SKILL.md), [`skill.json`](tools/skill.json), [`interface.md`](tools/interface.md)) plus executable governance CLIs (`start_path.py`, `payload_integrity.py`, `validate.sh`). |
| [`ecosystem/`](ecosystem/README.md) | Yes | The reusable ten-stage **Bootstrap → Preflight → Baseline → Audit → Plan → Execute → Verify → Promote → Compare → Repeat** lifecycle and its operator-gated coordination protocols. |
| [`registry/`](registry/README.md) | Authoring repo | The `NIZAM.json` index schema documentation and scope-definition patterns. |
| [`docs/`](docs/guide/index.html) | Authoring repo | Architecture Decision Records (`docs/architecture/`), versioned migration guidance ([`docs/migration-v2.0.0.md`](docs/migration-v2.0.0.md), with prior versions retained), and the self-contained [HTML user guide](docs/guide/index.html). |

---

## Automated Compliance Suite (`tools/validate.sh`)

Every pull request and release tag is gated by 16 deterministic checks (`C1`–`C16`) executed by `PYTHONDONTWRITEBYTECODE=1 bash tools/validate.sh`:

| Check | Invariant Verified |
| :--- | :--- |
| **C1** | Governed-document frontmatter validates against its schema. |
| **C2** | Required document fields have valid formats. |
| **C3** | Shipped Markdown code fences carry language tags. |
| **C4** | `NIZAM.json` validates and its indexed paths resolve. |
| **C5** | Shipped content contains no prohibited branding or internal endpoints. |
| **C6** | `bootstrap.sh` passes syntax and declared installation sanity checks. |
| **C7** | Required module READMEs exist. |
| **C8** | Frontmatter version increases have matching change records. |
| **C9** | Concrete paths resolve in shipped documents, root README and the guide; declared examples/placeholders retain their exemptions. |
| **C10** | Shipped payload, discovery and version statements remain consistent. |
| **C11** | Present local contracts, QA verdicts and run state validate against their schemas. |
| **C12** | Ecosystem and runtime schema-family fixtures retain expected outcomes. |
| **C13** | The governance skill manifest, version parity, unique capability names, indexed module subset and contained paths validate. |
| **C14** | External GitHub Actions references use immutable commit SHAs. |
| **C15** | Capability profiles cover and correctly map the five AGF roles. |
| **C16** | Feature-list lifecycle records satisfy the applicable contract, QA and evidence invariants. |

These checks have mode-specific scopes; see [the tools reference](tools/README.md).
The planning manifest (`schema/manifest.schema.json`), governance skill manifest
(`tools/skill.json`) and optional recommendation catalogue are distinct artifacts.
No recommendation catalogue or external documentation package is required for
core compliance. Reader-facing README content does not require NDS frontmatter;
its local paths are checked independently.

---

## Versioning

Nizam is released as semantically versioned git tags (`vMAJOR.MINOR.PATCH`). See
[CHANGELOG.md](CHANGELOG.md) for the version history. Consumer repos pin to a specific tag when
bootstrapping — never to a floating branch.

## License

Licensed under the MIT License — see [LICENSE](LICENSE).
