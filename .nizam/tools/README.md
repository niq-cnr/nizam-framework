---
id: nizam-tools-readme
title: "Tools Module — Index"
description: "Index for the tools/ module: the one unified, runtime-agnostic skill payload (manifest, instructions, and adapter interface) agents load to act on the Nizam framework."
version: 0.37.1
status: active
authoritative_source: tools/README.md
change_log:
  - version: "0.37.1"
    date: "2026-10-19"
    summary: "v1.9.0 audit follow-up (C1-C3): default start_path.py publish to noncommitting --mode prepare, require explicit NIZAM_MUTATION_ADAPTER for --mode publish and build-receipt --commit with request/commit binding, enforce GIT_OPTIONAL_LOCKS=0 on read-side Git queries, require explicit --git-repo and --expected-sha for commit-bound payload_integrity.py verification while labeling --source-root as directory_match_unbound, and evaluate work-specific continuation lineage in start_path.py classify and capture."
  - version: "0.37.0"
    date: "2026-10-18"
    summary: "Document payload_integrity.py, start_path.py publish --mode prepare|publish|finalize and build-receipt mutation mediation (V1), non-conflated validate.sh --payload summary (V4), C13 skill.json/SKILL.md version parity (V5), and provenance-based installed-payload discovery."
  - version: "0.36.0"
    date: "2026-10-18"
    summary: "Document Phase 019 generic repository/worktree assurance profile preregistration (124), shadow comparison and promotion recommendation (125), seven profile regression cases, and the start_path.py task-routing/capture/status CLI."
  - version: "0.35.0"
    date: "2026-10-18"
    summary: "Document authoritative five-job CI suite ownership, remove duplicate ci-candidate-bound/ci-blocker-rejected execution from fixtures_self_test.sh and duplicate fixtures_self_test.sh execution from convergent_review, and pin CI Python 3.12 with shared requirements."
  - version: "0.34.0"
    date: "2026-10-17"
    summary: "Register the Docker trial-sandbox adapter, its pinned-image requirement and fail-closed behavior, adapter-specific conformance selection, and the Docker boundary/guard suite additions."
  - version: "0.33.0"
    date: "2026-10-15"
    summary: "Document per-call receipt input batching and four independent synthetic controls."
  - version: "0.32.0"
    date: "2026-10-15"
    summary: "Document selected capable CI proof and read-only controls readiness."
  - version: "0.31.0"
    date: "2026-10-15"
    summary: "Document read-only evidence-based failure routing and unchanged attempt budgets."
  - version: "0.30.0"
    date: "2026-10-14"
    summary: "Document conflict assessments, isolated attempts and captured owned rollback."
  - version: "0.29.1"
    date: "2026-10-14"
    summary: "Clarify literal repository bindings and the legacy Root integration boundary."
  - version: "0.29.0"
    date: "2026-10-14"
    summary: "Document candidate-bound receipt gates, idempotent proposals and explicit proof recovery."
  - version: "0.28.0"
    date: "2026-10-14"
    summary: "Document strict convergent AGF mapping and the historical foundation receipt boundary."
  - version: "0.27.0"
    date: "2026-10-14"
    summary: "Document bounded partial-core aggregation and separate hosted fourteen-leaf proof."
  - version: "0.26.0"
    date: "2026-10-14"
    summary: "Document bounded waits, confirmed cancellation, checked reattachment and explicit source replay with fourteen fixture checks."
  - version: "0.25.0"
    date: "2026-10-14"
    summary: "Document the partial stub controller CLI and nine-case fixture-harness integration."
  - version: "0.24.0"
    date: "2026-10-14"
    summary: "Document candidate-bound foundation readiness and independent current20 prerequisites."
  - version: "0.23.0"
    date: "2026-10-13"
    summary: "Document active117 authorized-entry preflight, immutable dual-gate bindings and twenty current regression cases."
  - version: "0.22.0"
    date: "2026-10-13"
    summary: "Document immutable independent acceptance bundles and case-specific positive/red evidence; retain local recorded-identity boundaries."
  - version: "0.21.0"
    date: "2026-10-13"
    summary: "Document assessed-source identity and record continuity, with eleven permanent independent cases in the existing CI job."
  - version: "0.20.0"
    date: "2026-10-12"
    summary: "Index the optional runtime-session adapter and source routing while retaining record-only and future live-proof boundaries."
  - version: "0.19.0"
    date: "2026-10-11"
    summary: "Document ten C12 families and shared pure runtime-record relations; retain the record-only proof boundary."
  - version: "0.18.0"
    date: "2026-10-11"
    summary: "Document the scoped payload help correction and maintenance regression/helper CI commands; capable-host test and closure proof remain pending at source intake."
  - version: "0.17.0"
    date: "2026-10-10"
    summary: "C15 calls both primitives: vlib_profiles_cover_roles (the 5<->5 coverage check) and the new vlib_profiles_map_roles, which parses the explicit Role column of standard/capability_profiles.md and fails a swapped profile-to-role mapping (phase-014 feature 109, NDEBT-026)."
  - version: "0.16.0"
    date: "2026-10-10"
    summary: "Name docs/nips/ on the C1 row: the default sweep checks every NIP markdown file under C1 and C2 only, and those files are not part of the shipped-doc set (NDEBT-044 b)."
  - version: "0.15.0"
    date: "2026-10-10"
    summary: "Record the intentional-subset rule: every tools/skill.json module is the authoritative_source of some NIZAM.json capability, C13 enforces it, and NIZAM.json gains nizam-ecosystem-bootstrap (NDEBT-044 a)."
  - version: "0.14.0"
    date: "2026-10-09"
    summary: "Describe the fixtures self-test claim map: every subdirectory of `tools/fixtures/` is claimed by exactly one owning suite, the completeness guard accounts for files at any depth, and the self-test demonstrates its failure cases in a private scratch area (NDEBT-042)."
  - version: "0.13.0"
    date: "2026-10-09"
    summary: "Name the `convergent_review` CI job in Machine Validation: the convergent review suite runs in required-conformance mode in `.github/workflows/compliance.yml`, behind a guarded user-namespace step (NDEBT-041)."
  - version: "0.12.0"
    date: "2026-10-09"
    summary: "Document required-conformance mode for the convergent review suite: the UNSUPPORTED outcome and the CONFORMANCE: NOT FULL line with a non-zero exit when user-namespace isolation is unavailable, the local-only --allow-unsupported-isolation flag, and the CONFORMANCE: FULL outcome on a capable host (NDEBT-043)."
  - version: "0.11.0"
    date: "2026-09-17"
    summary: "Reconcile Git deltas and reads, commit parsing, sandbox and safe I/O, publication semantics, and standalone-ledger initial-head and exact evidence-attribution validation."
  - version: "0.10.0"
    date: "2026-09-17"
    summary: "Document the trusted packet builder, mandatory Linux sandbox adapter, schema-plus-relational packet validation, and expanded seven-blocker regression suite."
  - version: "0.9.0"
    date: "2026-09-17"
    summary: "Index the dependency-free convergent review CLI, frozen 12-case corpus, and permanent stdlib unittest suite."
  - version: "0.8.0"
    date: "2026-08-18"
    summary: "Phase-013 feature 092: document the new C16 feature-list lifecycle check (`.agent/feature_list*.json` schema validation plus the era-safe complete -> contract -> QA-verdict -> evidence-file referential rule) -- the Compliance Coverage section now documents sixteen checks (C1-C16, SUMMARY: 16 passed)."
  - version: "0.7.0"
    date: "2026-08-15"
    summary: "Phase-012 feature 089 (issue #52): synchronize C12 documentation with all eight ecosystem fixture families currently routed by the validator."
  - version: "0.6.0"
    date: "2026-07-20"
    summary: "Count sync for the v0.8.0 release (phase 006 feature 059): the Compliance Coverage section now documents fifteen checks (C1–C15, SUMMARY: 15 passed) with new rows for C14 (workflow SHA-pinning) and C15 (capability-profile ↔ AGF-role correspondence), both added by feature 058."
  - version: "0.5.0"
    date: "2026-07-19"
    summary: "Sync to phase-006 feature 052 (fixtures self-test closure): document tools/fixtures_self_test.sh (NDEBT-009 -- runs every fixture through its targeted check, non-vacuously, with a completeness guard), C12's --target ecosystem routing (NDEBT-015) and naming-conformance guard (NDEBT-016), and correct the C13 row's payload carve-out to registry/+docs/ only (methodology/+ecosystem/ became injected in feature 051)."
  - version: "0.4.1"
    date: "2026-07-19"
    summary: "Review-round correction (PR #28): the Compliance Coverage prose still said 'runs twelve checks' and 'As of phase 005' after the 0.4.0 C13 sync; both now match the thirteen-check C1-C13 set delivered by phase 006 feature 049."
  - version: "0.4.0"
    date: "2026-07-19"
    summary: "Sync to the phase-006 compliance validator: document the new C13 skill-index integrity check (feature 049, NDEBT-007 fix — tools/skill.json entry_point and every capabilities[].module pointer must resolve; payload mode skips the non-injected dirs pending F-051) and the new SUMMARY: 13 passed, 0 failed total."
  - version: "0.3.0"
    date: "2026-07-10"
    summary: "Sync to the phase-004 compliance validator: document the full C1-C11 check set (C9 repo-wide path-resolution, C10 single-source-of-truth consistency, C11 dogfood schema validation, all added by phase 004) and the new SUMMARY: 11 passed, 0 failed total."
  - version: "0.3.1"
    date: "2026-07-17"
    summary: "Sync to the phase-005 compliance validator: document the new C12 ecosystem schema-family fixture check (feature 042) and the new SUMMARY: 12 passed, 0 failed total."
---
## Assurance profiles and task entry CLI — features 124–125

[`workflow_assurance.py`](workflow_assurance.py) provides `preregister_profile_comparison`,
`evaluate_profile_comparison`, and `verify_profiles_ready` (plus CLI subcommands
`preregister-profile`, `evaluate-profile`, `verify-profiles-ready`, `verify-receipt`,
`plan-transition`, and `route-failure`). Feature 124 preregisters `Routine`, `Standard`,
and `High-assurance` tier applicability, exact `standard/AGF.md` and
`standard/capability_profiles.md` role/profile bindings,
stable A11 baseline controls, candidate/test-bundle digests, zero missed-blocker tolerance,
and cost/latency bounds before any shadow run starts. Feature 125 evaluates same-candidate
baseline vs. shadow runs, records every outcome including failures, rejects promotion
recommendations on any missed baseline blocker or bound violation, and enforces
`promoted: false` and `active_gates_reduced: false` (no self-promotion). Seven permanent
selectors (`preregister-before-run`, `roles-reused`, `reject-unstable-baseline`,
`same-candidate`, `missed-baseline-blocker`, `cost-latency-accounting`, `no-self-promotion`)
and `--check profiles-ready` run through [`test_workflow_assurance.py`](test_workflow_assurance.py).
[`start_path.py`](start_path.py) (tested by [`test_start_path.py`](test_start_path.py) and
[`test_public_entry.py`](test_public_entry.py)) provides `classify`, `preflight`, `begin`,
`capture`, `publish` (`--mode prepare|publish|finalize`, plus `prepare-publish` and
`finalize-publish` subcommands), `build-receipt`, `check-verdict`, `amend-contract`, `done`,
`status`, and `resume`.

## Development runtime controller — features 126–127

`runtime_session.py` provides a detached supervisor and one stub child per
session, using an exclusive lock, generation counter/nonce, explicit ownership
and lease checks, and one outstanding operation. This coordinates declared
identities; it does not authenticate callers or prove source/image equivalence.

```bash
python3 tools/runtime_session.py open-session --root /absolute/private/state --request /absolute/request
```

The other implemented actions are `submit-operation`, `poll-operation`,
`transfer-session`, `close-session`, `cancel-operation` and `reattach-session`,
with the same arguments. The JSON request
includes session/requester identity; existing sessions require the current
generation and lease. Open supplies owner, development purpose and a read-only
run-state path binding contract/step/attempt. Submit adds operation ID, kind,
payload, context and limits. Stub payload expressions are JSON data for set/get
or a release-file gate; they are never Python evaluation. Only submit dispatches
execution. Duplicate IDs return conflict without replacing prior records.

Each response is one JSON object with `ok` and `result` or `error`; rejected
submits reaching the supervisor also return their rejection record. Exit codes
are 0 for successful/admitted work, 1 for refusal, 64 for malformed usage and 70
for infrastructure failure. Admission is not completion: poll the operation.

The private state root contains a directory per session: `controller.json` for
process/attempt metadata, `runtime_session.json`, `supervisor.lock`, `control.sock`,
operation records and separate child-result frames under `operations/`, and
bounded `child.stdout.log`/`child.stderr.log` diagnostics. Child stdin and fd 3
carry JSON lines. Atomic records are development provenance only. Public review
trials receive no endpoint or record-writing access; the supervisor independently
rejects trial requests delivered to it. Close observes process termination without
claiming rollback of effects.

A poll optionally supplies `limits: {"timeout_seconds": 0.25}` (finite 0–30).
Without limits it returns an immediate snapshot. A deadline records
`stopped_waiting`; execution stays pending and conflicting submits remain busy.
Unknown outcomes return infrastructure exit 70. Completion replaces the wait
outcome with `completed_wait`; a disconnected client never cancels work.

Cancel adds operation ID and contract/step/attempt to current owner, generation
and lease identity. It returns `cancel_requested` with confirmation false.
Only a matching child acknowledgement of stopped execution produces `cancelled`
and confirmation true. The stub gate cancels cooperatively; this promises no
rollback. Already completed work retains its record and result unchanged.

Reattach adds the same governed binding, the exact nullable
`expected_outstanding_operation_ref`, and a closed `handoff` object with absolute
`workspace_path`, committed `source_revision`, `source_manifest` entries
(`path`, `sha256`), ordered `command_refs` and `external_resources`. Manifest
files must match both Git HEAD and workspace bytes. Command references name
committed JSON templates containing exactly `kind`, `payload`, `context`, `limits`.
Paths are relative regular files without traversal or symlink escape. Resource
objects use the existing runtime record schema. A successful check publishes
`handoff.json` and a reattach session snapshot without changing owner, lease,
generation, pending work or governed attempt. Partial publication fails closed.

For replay, obtain the pinned inputs in a fresh private worktree, open a separate
development session, read templates in order and submit each with fresh operation
IDs and that session's actual owner/generation/lease and governed binding. Poll
each outcome before continuing. Lifecycle calls never execute the templates.
Handoff provenance does not prove source/heap equality or independent acceptance.

`PYTHONDONTWRITEBYTECODE=1 python3 tools/test_runtime_session.py --check core-ready`
runs fourteen bounded leaf subprocesses, failing on any error or missing proof.
Its partial stub scope is cases 1/2/3/5/6/8(policy)/9/10/13 and five named checks.
`fixtures_self_test.sh` separately runs fourteen leaves in hosted CI; it does not
run `core-ready`. Independent QA/capture still gate bounded core closure.
SBCL/full adapter, phase020 fresh acceptance and final CI131 remain pending.
The reserved `accept` action fails without side effects.

## Conflict lanes and owned rollback — feature 121

`assess_conflict_lanes` checks pinned current coordination and dispatch ownership;
`verify_isolated_attempt` additionally observes a real detached Git worktree and
all committed, staged, live and ignored changes. Conflicting file/state ownership
serializes, and allocated attempts retain the existing maximum of three.
`rollback_owned_attempt` removes only that validated owned worktree through Git,
after external failure capture. The Orchestrator must ensure exclusive ownership
and stopped processes; unrelated changes block removal. Assessments never reserve
lanes or authenticate callers, and repository spellings must remain aligned.

## Receipt gates and recovery — feature 120

`verify_stage_receipt(repo, receipt, *, policy)` checks independently pinned
operator/prerequisite authority, protected candidate inputs and actual command
captures. Trusted callers supply policy and capture provenance; hashes and
recorded producer names establish integrity, without authenticating execution.
`plan_receipt_transition(repo, state, receipt, *, policy)` proposes one owned
history/status update or an identical-receipt noop. Missing proof returns
`rerun-required` or a verified `republish` proposal; callers must actually restore
and revalidate the receipt. Both APIs preserve inputs and never execute recorded
commands or write lifecycle state. Existing default acceptance includes37 cases.

Policy, candidate and state must use the literal Git `origin` repository string,
with consistently bound authority spelling; the APIs perform no alias normalization.
Existing Root records use differing spellings and require explicitly reviewed
compatibility or migration before live adoption; aligned synthetic fixtures prove
library behavior only.

Receipt candidate validation batches immutable inputs by exact revision and literal
path, then reads their validated blobs through the existing Git batch helper.
The observations live for one call; current files, modes and environment are read
afresh. Ownership rules, origin and ancestry checks retain their existing meaning.
`python3 tools/test_receipt_candidate_batching.py` runs four independent synthetic
checks in order; `--check` selects `real-git-count-reduction`, `semantic-equivalence`,
`fresh-mutations` or `literal-paths-and-modes`. The fixture shell suite invokes all
four and retains its existing 166 fixture-file denominator, while the separate
`python3 tools/test_workflow_assurance.py` step in `fixtures_self_test` owns all
48 Workflow Assurance cases once per run. These checks establish real Git launch
reduction, not a wall-time speedup or hosted qualification. Changed protected
Source makes feature 123's existing current-readiness proof historical; this
maintenance does not rebind that proof.

## Convergent findings to AGF verdict — feature 119

`convergent_agf_verdict(ledger, report, *, expected_repository, expected_head_sha)`
validates the authoritative converged ledger and explicit bindings, returning
independent copies of the verdict, three blocking arrays, fixes and minor advice.
Active unsuppressed blocker/important findings append issues and fixes; minor
findings remain advisory. Approval requires exact boolean true, empty blocking
arrays and ledger approval. Existing blockers remain intact; malformed inputs
raise `AssuranceError`. This pure API neither authenticates provenance nor advances
workflow state. The default runner executes all twenty original and six new cases.

## Evidence-based failure routing — feature 122

`route_failed_attempt(repo, request, *, policy)` reads independently selected
immutable authority, classification, capture and coordination references. It
returns a failed infrastructure-diagnosis or semantic-repair proposal for allocated
attempts one and two, or halt for attempt three. It preserves counters and the
history prefix, accepting optional lane inventories only when identical.
Semantic classification requires a schema-valid rejecting verdict; both causes
require an actual nonzero outer wrapper capture, pinned output bytes/modes and
candidate/environment bindings. Expected inner negatives do not clear outer
failure. Missing, stale or relabeled proof raises `AssuranceError`.

This API writes no state and authorizes no retry. Producer labels and hashes
establish binding, not authentication or factual truth; the Orchestrator owns
policy selection and counters. Fixture authority is synthetic. Root repository
binding migration remains unapplied. Four selectors extend the default to 46;
full controls readiness remains a separate feature123 obligation.

## Foundation readiness — feature 118

`verify_foundation_ready(repo, prerequisite)` observes the immutable SourceC,
explicit current and historical input bytes/modes, distinct recorded evaluator
identity, and all twenty exact case proofs. The permanent runner accepts
`--check foundation-ready` using the canonical feature118 prerequisite receipt;
its original twenty cases remain available independently alongside six AGF cases.
The immutable receipt is checked at commit `8ac94f6808e8197111197c9acbf59b2aa92efc7c`;
changed source/test inputs correctly reject that stale receipt. A record-only HEAD
advance preserves readiness when the assessed inputs remain unchanged.

Readiness supports the bounded foundation. Phase completion follows the live
[phase017 record](../docs/planning/phase_017.yaml) and requires separate Mode B,
fresh three-command QA plus an independent spot check, and Root evidence capture.
The installed `.nizam/` payload recorded in `.nizam/provenance.json` remains
unchanged until an authorized re-bootstrap; full WA controls, runtime and
controller work require their separately authorized phases.


# tools/

The `tools/` module owns the one unified, runtime-agnostic skill payload agents
load to act on the Nizam framework. There is exactly one skill, loadable by any
agent runtime through the same adapter contract — no per-runtime forks.

| File | Purpose |
|---|---|
| [`skill.json`](skill.json) | Machine-readable capability manifest: the skill's name and version (which C13 enforces must match `SKILL.md` frontmatter `version`), its `entry_point` (`SKILL.md`), a `capabilities` array mapping named capabilities to the framework module path each one is backed by, the abstract `runtime_requirements` any host environment must provide, and the `state_interface` describing the root index and the `.agent/` artifact families. Its capabilities are an intentional subset of NIZAM.json, not an equal list: every module is the authoritative_source of some NIZAM.json capability, and NIZAM.json-only entries are allowed. The optional live_runtime_session requirement is false; adapter and SBCL binding capabilities route to their authoritative sources. |
| [`SKILL.md`](SKILL.md) | The single instructions payload any agent runtime loads to act on the framework: when to load it, how to consume the framework by querying the root index rather than bulk-reading, a summary of the contract-first execution loop, the circuit-breaker and anti-hallucination obligations every role carries, the durable-state and evidence-by-path obligations, and the verdict JSON formats every gate produces. |
| [`interface.md`](interface.md) | The runtime-adapter specification: how any agent runtime discovers `skill.json`, loads `SKILL.md` as instructions context, maps the framework's three abstract operations (`read-state`, `write-evidence`, `run-verification`) onto its own native tool primitives, and the ten-item Adapter Conformance Checklist an integrator ticks through. Section 6 adds seven optional session calls and conditional S1–S9 for claiming adapters. |
| [`payload_integrity.py`](payload_integrity.py) | Shared installed-payload integrity comparator invoked from outside the target payload by `bootstrap.sh --verify-only` and `.github/scripts/verify_self_governance.py`: compares the complete file inventory (excluding only `provenance.json`), exact byte content, regular-file/no-symlink rules, and executable file modes (`100755` vs `100644`) of an installed payload against an explicit `--git-repo` + `--expected-sha` commit tree (`content_integrity=verified`) or an unbound `--source-root` directory (`content_integrity=directory_match_unbound`). |
| [`convergent_review.py`](convergent_review.py) | Dependency-free deterministic library and CLI for controlled no-replace Git-object packet construction; authenticated content and Git mode deltas; structural-plus-relational validation; semantic fingerprints; three-trial convergence; lifecycle and verdicts; canonical JSON and embedded-ledger Markdown; trust-anchored no-follow replay; and atomic no-replace publication with explicit visible/durable state. |
| [`evaluate_convergent_review_prompt.py`](evaluate_convergent_review_prompt.py) | Prompt evaluator that requires a trusted sandbox adapter for each of exactly three runner invocations, uses exclusive no-follow per-trial input/output I/O, validates substitutions before convergence, and publishes one complete evaluation directory. |
| [`linux_trial_sandbox.sh`](linux_trial_sandbox.sh) and [`isolated_trial_adapter.py`](isolated_trial_adapter.py) | Linux reference adapter: user/network/IPC/UTS/PID namespaces plus Landlock filesystem confinement; trial-root data is readable/writable but non-executable, while execute permission is limited to the trusted runner and runtime. |
| [`docker_trial_sandbox.sh`](docker_trial_sandbox.sh) | Trusted Docker-controller equivalent adapter (feature 134) implementing the same `ADAPTER --root TRIAL_ROOT --runner RUNNER -- RUNNER_ARGUMENTS...` protocol on hosts whose kernel refuses `unshare --user`: one fresh `--network none --cap-drop ALL --no-new-privileges --read-only` container per trial over a digest-pinned `python:3-alpine` image, same-path bind mounts (trial root rw, runner and inner Landlock adapter ro), a fixed minimal container environment, and the inner `isolated_trial_adapter.py` with an explicit interpreter allowlist. It never auto-pulls and fails closed: exit 2 (arguments), 3 (daemon unreachable or pinned image absent), 4 (inner setup); `--probe` reports capability, `--print-image` prints the pinned digest. The pinned image must be pulled by an explicit reviewed step (the CI pull step or an operator pull) before use; when the rolling-tag digest is garbage-collected upstream, re-pinning is a reviewed debt-register act (NDEBT-056), never an automatic pull. Untrusted input can never select the image, mounts, or any runtime option. |
| [`test_convergent_review.py`](test_convergent_review.py) | Permanent stdlib `unittest` suite exercising the frozen 12-case corpus and adversarial blocker regressions, including controlled Git reads, absent-versus-error object lookup, mode-only changes, commit-header parsing, sandbox no-execute, evaluator substitution, replay ancestors, and publication visibility/durability. |

The optional session surface routes through [the adapter interface](interface.md),
[Live Runtime Sessions](..&#47;methodology/10_live_runtime_sessions.md) and
[SBCL Runtime Binding](..&#47;methodology/11_sbcl_runtime_binding.md). Adapters without
sessions remain conformant. Existing schemas/C12 validate declared records only;
the partial stub controller proves only the bounded cases above. Query
`.nizam/provenance.json` and `tools/start_path.py preflight` for the installed
payload pin and active runtime capabilities.

## Sealed independent acceptance bundles

`verify_acceptance_bundle(repo, bundle, independent_review)` verifies a closed
canonical seal over immutable Git baseline inputs, source-obligation snapshot,
test/API/naive-control bytes and modes, observed environment, distinct recorded
agent/session identities and each case's setup, positive control and intended red.
The independent review is a separate nine-field record binding the same seal.
Recorded commands are read as evidence; the verifier never executes them.

Every case binds distinct actual positive/case input files and its operation hash.
Setup and positive controls must exit 0; the red must exit 1 with the case-specific
policy assertion and opposite observed accept/reject result. Missing API, import,
transport or unrelated failures do not qualify. Changes to sealed bytes or
observed environment require a new bundle and independent review. Implementation
Source identity is separately assessed: a later record-only HEAD is allowed while
sealed inputs still match their immutable Git blobs and actual current bytes.

Prepare `WA_BUNDLE_FILE` and `WA_REVIEW_FILE` as complete absolute filenames of
strict JSON inputs, with `WA_REPO_ROOT` the repository being observed:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/workflow_assurance.py bundle --repo "$WA_REPO_ROOT" --bundle "$WA_BUNDLE_FILE" --review "$WA_REVIEW_FILE"
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_workflow_assurance.py --base-cases
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_workflow_assurance.py
```

The regression flag runs the eleven feature 115 cases; the default suite now runs
those plus five feature 116 cases in the existing CI job. Use independently
reviewed inputs and output evidence; local role records are not cryptographic
authentication or runtime permission enforcement. Feature 117 entry checks and
feature 118 foundation closure remain pending. Earlier feature 115 documentation
below records its initial eleven-case suite; the current default count is sixteen.
The authored tool does not silently mutate the installed `.nizam/` payload.

## Assessed-source identity and record continuity

[`workflow_assurance.py`](workflow_assurance.py) provides a dependency-free,
read-only API: `assess_repository`, `compare_identity` and `verify_record_update`.
Assessments bind an explicit immutable Git commit/tree, observed origin, source,
contract, test and tool bytes/modes, actual runtime identifiers and named environment
variables. An input manifest declares nonempty `source`, `contracts`, `tests` and
`tools` path lists plus `unknown_dependencies: []`.

Every tracked path is checked against actual anchor blobs and current raw bytes,
including staged content. Untracked and ignored files invalidate conservatively.
Paths must be regular, canonical relative files with no symlink components.
Explicit JSON record masks allow existing scalar leaves to change with the same
JSON type and permit `/history` append only with its exact original prefix intact.
All other parsed keys/values remain unchanged. Record-only commits can advance
HEAD while the assessed anchor and every assessed input remain unchanged.

Set `WA_REPO_ROOT` to the repository root and `WA_SOURCE_COMMIT` to the full
immutable assessed commit. Set each task-specific `WA_*_FILE` variable below to
the complete absolute filename of your prepared JSON input outside that
repository. These variables are caller configuration, not observed evidence.

```bash
python3 tools/workflow_assurance.py assess --repo "$WA_REPO_ROOT" --source-commit "$WA_SOURCE_COMMIT" --inputs "$WA_INPUTS_FILE" --environment-names "$WA_ENV_NAMES_FILE" --record-ownership "$WA_RECORD_OWNERSHIP_FILE"
python3 tools/workflow_assurance.py compare --before "$WA_BEFORE_IDENTITY_FILE" --after "$WA_AFTER_IDENTITY_FILE"
python3 tools/workflow_assurance.py record --before "$WA_BEFORE_RECORD_FILE" --after "$WA_AFTER_RECORD_FILE" --owned-fields "$WA_OWNED_FIELDS_FILE"
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_workflow_assurance.py
```

The last command runs eleven independently authored feature 115 cases and is
permanent in the existing `fixtures_self_test` CI job. Unknown cases, invalid JSON,
missing observations and unsafe paths exit nonzero. Keep CLI input/output files
outside the assessed repository unless they have a declared record mask.
This local identity utility does not authenticate callers or authorize entry;
sealed-bundle enforcement, entry/role checks and foundation closure belong to
features 116–118. It implements no runtime controller or live acceptance and does
not silently mutate the installed `.nizam/` payload.

## Design Decision — DD-4: Unified Skill Payload

This module exists to remediate one specific failure mode observed in prior
governance deployments: a skill's instructions being duplicated and forked
per agent runtime (a `.claude/`-style directory alongside a `.codex/`-style
directory, each drifting independently from the other over time). DD-4's
rule is unconditional:

- **Exactly one payload.** `SKILL.md` is the only skill-instructions document
  the framework ships. It is written in a runtime-agnostic voice with no
  vendor-specific tool names, so that no runtime's adapter ever needs its own
  rewritten copy.
- **No per-runtime fork directories.** No `tools/.claude/`, no `tools/.codex/`,
  no equivalent runtime-specific subdirectory under `tools/` — or anywhere
  else in the repository — is permitted. A runtime that needs a thin,
  runtime-native pointer to `SKILL.md` is expected to reference or include it
  verbatim (`interface.md` Section 3.3), never to restate its content.
- **One adapter contract, many adapters.** `interface.md` defines the single
  contract (discovery, loading, the three abstract operations) that any
  number of runtime-specific adapters can each independently implement,
  without the framework itself ever needing to know how many runtimes exist
  or what any one of them is called.

*Acceptance anchor:* exactly one `SKILL.md` exists in the whole repository,
and no per-runtime skill fork directory exists under `tools/`
(`product_spec.md` Section 4, DD-4).

## Machine Validation

Every `.md` in this module carries the same six-key frontmatter
(`standard/NDS.md` Section 2) and validates against
`schema/frontmatter.schema.json`, identically to every other module's governed
documents. `skill.json` is validated as plain JSON (`python3 -c
"import json; json.load(open('tools/skill.json'))"`); it carries no schema of
its own within this module — it is pure data consumed by `SKILL.md` and
`interface.md`, not a document requiring frontmatter.

The required convergent review gate runs with `python3 tools/test_convergent_review.py`.
Its fixtures are the 12 directories indexed by
`tools/fixtures/convergent_review/manifest.json`; every case retains three raw trials.
The adversarial cases verify that the builder ignores replace refs and inherited Git
redirection, only a successful empty tree lookup means path absence, mode-only deltas
remain authenticated, commit message text cannot forge a tree header, trial-root files
cannot execute, runner output substitution is rejected, replay rejects symlinked root
ancestors, standalone ledger validation rejects unrelated initial lifecycle heads and
non-consensus trial evidence, and a post-rename parent-`fsync` failure remains visible but
not durable.

Sandbox capability selection is adapter-specific (feature 134). With no override, `tools/test_convergent_review.py` probes the native user-namespace adapter first and, only when that probe fails, probes the Docker adapter (`tools/docker_trial_sandbox.sh --probe` plus a smoke trial, requiring a reachable daemon and the digest-pinned image pulled locally); the first adapter with a passing probe is selected and recorded on stderr as one line naming the selected adapter path and its sha256. `--isolation-adapter PATH` forces an adapter for deterministic qualification runs and is honored before the remaining arguments pass through to unittest; a forced adapter whose capability probe fails is reported UNSUPPORTED like any unprovable host — selection never manufactures green and never falls back from a forced adapter. On a host that cannot prove isolation with any adapter (for example one whose kernel refuses `unshare --user --map-root-user true`, as with `kernel.apparmor_restrict_unprivileged_userns = 1`, with no reachable Docker daemon or no pinned image), the five sandbox-dependent tests are not run. Each is reported on its own result line as `UNSUPPORTED` (an explicit skip whose reason begins `UNSUPPORTED: user-namespace isolation unavailable`), the run prints `CONFORMANCE: NOT FULL`, and the command exits non-zero: the required gate never passes on a host that cannot prove isolation. `--allow-unsupported-isolation` is for local development only and CI never passes it; it turns that same outcome into exit 0 while still printing every `UNSUPPORTED` line and `CONFORMANCE: NOT FULL`, and it never masks any other failure. When an adapter is selected the sandbox tests execute under it — through the Docker adapter on a userns-restricted host with a reachable daemon they exercise for real, including live in-sandbox guards (zero effective capabilities, no daemon socket path, a fresh PID namespace, no ambient environment forwarding, and a host-existing ambient file unreadable inside) and omission controls proving each container boundary layer load-bearing (exec-permitted mutant 42, bad interpreter 53, mounted-sibling 40, in-container loopback 41). On an isolation-capable host the native adapter stays the default and its behavior is unchanged. `linux_trial_sandbox.sh` and `isolated_trial_adapter.py` are not relaxed by this mode and still fail closed; the suite never runs a trial outside the sandbox.

CI runs this suite as the `convergent_review` job of `.github/workflows/compliance.yml`, in required-conformance mode and never with `--allow-unsupported-isolation`. The job first runs a guarded step that enables unprivileged user namespaces only on runners whose kernel exposes the AppArmor user-namespace restriction key, and it installs `jsonschema` and `pyyaml` so that no ordinary test is skipped. A runner that still cannot provide isolation therefore fails the job instead of passing it, and the job log must show `CONFORMANCE: FULL`. The same job then pulls the digest-pinned Docker trial-sandbox image and runs both the boundary suite and the required-conformance suite a second time with the Docker adapter forced (`.github/scripts/test_sandbox_boundaries.py --adapter tools/docker_trial_sandbox.sh` and `tools/test_convergent_review.py --isolation-adapter tools/docker_trial_sandbox.sh`), so the Docker adapter's boundary and conformance behavior is gated on every run; no host security control is relaxed or relied on by those steps.

## Compliance Coverage — C1–C16

`tools/validate.sh`, the repo-local NDS compliance validator, runs sixteen
checks on every PR and push to `main` (`.github/workflows/compliance.yml`).
As of phase 013 (feature 092's C16 feature-list lifecycle check), the
full default sweep reports `SUMMARY: 16 passed, 0 failed`, while `--payload` mode
separates exercised checks from non-applicable, skipped, and out-of-scope checks
(`SUMMARY (payload mode): 10 exercised passed, 0 failed, 2 not-applicable (C11, C16), 1 skipped (C6), 3 out-of-scope (C12, C14, C15); content_integrity=not_checked, operational_acceptance=not_assessed`):

| Check | Name | What it enforces |
|---|---|---|
| C1 | Frontmatter schema | Every shipped `.md`'s frontmatter validates against `schema/frontmatter.schema.json`. The default sweep also checks every markdown file under `docs/nips/`; those files are not in the shipped-doc set, so C9 and C10 do not scan them, and `--payload` does not check them. |
| C2 | Format | Frontmatter fields (`version`, `status`, etc.) match their required format. |
| C3 | Untagged-fence sweep | No fenced code block in a shipped `.md` is missing a language tag. |
| C4 | `NIZAM.json` index integrity | Every path `NIZAM.json` indexes resolves on disk. |
| C5 | Branding/endpoint leakage | No vendor-specific branding or internal endpoint strings ship in the framework payload. |
| C6 | `bootstrap.sh` sanity | The inject/verify script passes its own internal sanity checks (`SKIP` in `--payload` mode because `bootstrap.sh` is not copied into `.nizam/`). |
| C7 | Module README presence | Every module directory carries a governed `README.md`. |
| C8 | Version-bump-vs-changelog | Any file whose frontmatter `version` increased vs `HEAD` is matched by a `change_log` entry for the new version, or a `CHANGELOG.md` line naming the file. |
| C9 | Repo-wide path-resolution | Every concrete repo-relative file path named in a shipped doc resolves on disk (placeholder/illustrative paths documented-exempt). |
| C10 | Single-source-of-truth consistency | Payload-set enumeration, bootstrapped-consumer discovery order, and the framework-version anchor stay consistent across every shipped doc. |
| C11 | Dogfood schema validation | Every `.agent/qa/*.json`, `.agent/contracts/*.json`, and `.agent/run_state.json` (when present) validates against the shipped schemas — enforce-if-present in repo mode, and reported as `NOT_APPLICABLE` (not counted as an exercised pass) in `--payload` mode because `.agent/` is not part of a consumer payload. |
| C12 | Ecosystem schema-family fixture validation | Every `tools/fixtures/{ecosystem_baseline,preflight_verdict,engineering_finding,audit_delta,ecosystem_membership,membership_result,reconciliation_plan,release_train_manifest,runtime_session,runtime_operation}_*.json` fixture validates (positive) or is rejected (negative) against its shipped schema, proving all ten routed families are load-bearing rather than dormant (`membership_result` fixtures target `ecosystem_membership_result.schema.json`). A `--target` invocation against one of these fixtures routes to a discriminating per-file C12 verdict (feature 052, NDEBT-015), and a non-conforming polarity marker in a fixture name (e.g. uppercase `_NEG_`, full-word `_negative_`) is itself a FAIL (NDEBT-016). Runtime records use shared `vlib_runtime_record_relations` for owner, generation, lease and continuity comparisons in both targeted validation and the sweep. Records prove no live runtime behavior; consumer sessions are not auto-swept (`OUT_OF_SCOPE` in `--payload` mode). |
| C13 | Skill-index integrity | `tools/skill.json` JSON-parses, its `version` matches `tools/SKILL.md` frontmatter `version` (V5), and its `entry_point` plus every `capabilities[].module` pointer resolves to an existing file (NDEBT-007 fix); in `--payload` mode, pointers into the still-non-injected directories (registry/, docs/) are skipped as expected-absent, while methodology/ and ecosystem/ — injected into the payload as of feature 051 (NDEBT-008) — are required to resolve. Every module must also be the authoritative_source of some NIZAM.json capability (an intentional subset, not equality; NIZAM.json-only entries are allowed). |
| C14 | Workflow SHA-pinning | Every external (third-party) `uses:` reference in `.github/workflows/` is pinned to a 40-hex commit SHA, not a floating tag or branch; local `./`/`../` actions are exempt (they ship in-repo and need no pin). Feature 058 — mechanizes `standard/provenance_policy.md`'s SHA-pinned-Actions requirement; default sweep only (`OUT_OF_SCOPE` in `--payload` mode). |
| C15 | Capability-profile ↔ AGF-role mapping | C15 calls both `vlib_profiles_cover_roles` (5↔5 coverage: every profile identifier in `standard/capability_profiles.md` is present and each one's corresponding role is defined in `standard/AGF.md`) and `vlib_profiles_map_roles` (phase-014 feature 109, NDEBT-026), a primitive that parses the table's explicit `Role` column and fails unless each of the five profile rows names its own role — so a swapped profile-to-role mapping now fails C15. Feature 058 — mechanizes the five-profile ↔ five-role correspondence; 109 adds the Role column and the mapping primitive; default sweep only (`OUT_OF_SCOPE` in `--payload` mode). |
| C16 | Feature-list lifecycle invariant | Every `.agent/feature_list*.json` (when present) validates against `schema/feature_list.schema.json`; and for every feature with `status: "complete"`, IF `.agent/contracts/<id>.json` exists THEN `.agent/qa/<id>.json` MUST also exist, and if that QA verdict carries a top-level `evidence_files` array, every path it lists MUST exist on disk. Era-safe: a complete feature with no contract file at all (the framework's own pre-contract-first history) is not flagged. Feature 092 — mechanizes "complete implies approved contract and passing QA verdict and evidence on disk"; enforce-if-present in repo mode, and reported as `NOT_APPLICABLE` (not counted as an exercised pass) in `--payload` mode (`.agent/` is never part of the bootstrap.sh payload). A `--target` invocation against a feature-list-shaped file routes to schema-only validation (the era-safe referential rule is a whole-repo-tree relational property, not evaluable on one isolated file). |

C9, C10, and C11 were added by phase 004 (`tools/verify_lib.sh` supplies
their shared, fixture-tested primitives); C12 was added by phase 005
(feature 042); C13 by phase 006 (feature 049), C14 (workflow SHA-pinning)
and C15 (capability-profile ↔ AGF-role) by phase 006 (feature 058), and
C16 (feature-list lifecycle invariant) by phase 013 (feature 092); C1–C8
shipped in earlier phases. Run `bash tools/validate.sh --help` for the
full per-check description.

### Fixture self-test (`tools/fixtures_self_test.sh`)

The negative fixtures under `tools/fixtures/` are the evidence that each
check is load-bearing rather than vacuous, but nothing exercised them in CI
until phase-006 feature 052 (NDEBT-009). `tools/fixtures_self_test.sh` runs
**every** fixture through its targeted surface — `validate.sh --target` for
the check-level fixtures, the `verify_lib.sh` primitives for the
primitive-level ones, and a `tools/skill.json` substitution for the C13
fixture — and asserts the **specific** verdict, never a bare non-zero exit
(most `.md` fixtures exit non-zero from incidental C1/C2 failures unrelated
to what they test, so an exit-code-only test would pass vacuously). A
**completeness guard** fails if any file under `tools/fixtures/` is not
accounted for, so a newly-added fixture cannot silently go dormant. It runs
as its own CI job (`fixtures_self_test`) alongside `validate` and
`e2e_bootstrap`.

The completeness guard also consults a **claim map**, the `FIXTURE_CLAIMS` array in the script: every subdirectory of `tools/fixtures/` is claimed by exactly one owning suite, as one `<subdirectory>|<suite file>` row, and a file below a claimed subdirectory, at any depth, is accounted for by that claim. The guard fails on an unclaimed subdirectory, on a doubly-claimed subdirectory, on a claim naming a suite file that does not exist, and on a claim naming a subdirectory that is not on disk. The self-test demonstrates those four cases itself, in a private scratch area that the scratch helper confines outside the repository, and prints one `OK   claim-map` line for each. A claim proves ownership, not execution: that the owning suite runs is proven by its own CI job (`tools/test_convergent_review.py` owns the `convergent_review` subdirectory and runs as the `convergent_review` job). A future suite that adds a fixture subdirectory registers its row in this same map; there is no second registry.

### Post-GA maintenance regression checks

The C13 interruption helper `.github/scripts/test_c13_cleanup.py` exercises the
actual fixture swap and owned cleanup; its `--source-ref` mode demonstrates the
unrepaired baseline failure before cleanup repair. The required sandbox helper
`.github/scripts/test_sandbox_boundaries.py` uses a real outside listener and
isolated namespace, filesystem and executable-permission omissions under the
selected adapter (native auto-selected first; `--adapter PATH` forces one).
Setup errors cannot count as confinement; an incapable host reports
`UNSUPPORTED` with exit64. Under the Docker adapter the same suite additionally
runs the live in-sandbox guards (zero capabilities, no daemon socket, fresh PID
namespace, fixed minimal environment, ambient marker not forwarded, host-existing
ambient file unreadable inside) and the container omission controls are
short-lived ephemeral containers over scratch data with no daemon socket, no
host mounts, and no sysctl/seccomp/AppArmor change.

The standing CI jobs in `.github/workflows/compliance.yml` assign each suite to
one authoritative job owner (pinned to Python `3.12` and shared dependencies):
`validate` runs `bash tools/validate.sh`; `e2e_bootstrap` runs
`bash tools/e2e_bootstrap_test.sh`; `fixtures_self_test` runs the C13 cleanup
helper, `bash tools/fixtures_self_test.sh`, and `python3 tools/test_workflow_assurance.py`
once; `convergent_review` runs the native and Docker sandbox boundary and
required-conformance suites plus conditional `WA123` steps; and `self_governance`
runs the installed-payload drift verifiers and `bash .nizam/tools/validate.sh --payload`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 .github/scripts/test_c13_cleanup.py
bash tools/fixtures_self_test.sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_workflow_assurance.py
PYTHONDONTWRITEBYTECODE=1 python3 .github/scripts/test_sandbox_boundaries.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_convergent_review.py
```

The existing jobs emit checkout SHA and source digest receipts. Actual capable CI
and independent QA remain prerequisites to debt closure; local unsupported results
are recorded as limitations. The installed `.nizam/` payload recorded in
`.nizam/provenance.json` remains unchanged until an authorized re-bootstrap.


## Authorized entry — feature 117

`verify_authorized_entry(repo, entry)` checks actual repository origin and local
phase authority, the released installed pin and critical index/skill/role bytes,
the immutable proposal and both referenced independent approvals, and explicit
role/path/field write intents. It uses the five installed AGF role/profile pairs.
Approved local grants permit independent Evaluator test authorship; permission
class defaults remain consumer-aspirational. The check observes intent and does
not write files or authenticate recorded agents.

The project preflight runs while approved feature 117 is active. It rejects after
117 completes or during 118; portable cases retain real approved active snapshots.
The current suite includes twenty cases, with `--pre-entry-cases` selecting the
prior sixteen. Historical 115/116 QA and bundle receipts retain their assessed
revisions; a changed shared runner does not reseal them.

Set `WA_ENTRY_FILE` to the complete absolute filename of an entry JSON input.
The file names the actual approved contract and immutable authority references;
write grants come from that contract. Keep operator input files outside the
assessed repository when using the separate identity commands.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/workflow_assurance.py entry --repo . --entry "$WA_ENTRY_FILE"
```


## Candidate-bound control proof

`workflow_assurance_ci.py` composes the existing observation sandbox, convergence
and receipt APIs in the existing `convergent_review` job. Root selects capture
inputs first, then independently selects immutable captures for the matching
runtime verify pass. Experiment output commits and bounded bundles keep the
assessed source anchor distinct from each actual checkout and output revision.
The observer checks changed workflow `continue-on-error` lines; its three enforced
executions are bounded deterministic dogfood. Synthetic parser fixtures remain
separate from actual hosted command, trial and artifact evidence.

`verify_controls_ready(repo, evidence, *, policy)` observes Root-selected completed
hosted proof without running historical receipt commands or comparing that
runtime with the local interpreter. `--check controls-ready` retains the same
boundary. Strict review, QA, evidence capture and canonical closure remain
separate gates. The experiment configures its own selected Git transport; live
Root binding migration and the installed payload remain unchanged.
