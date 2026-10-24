# R02 completion and structured proof repairs

Version: 1.0.0. Status: planned; implementation and QA remain outstanding.

## Purpose and authority

Repair F1–F4 in the framework source in two sequential bounded changes. This
execution uses a fresh clone on the current machine, with canonical origin
https://github.com/niq-cnr/nizam-framework.git. The report's copied guest
approval and successful preflight do not prove this checkout's qualification.

The operator explicitly stated: “as you are working to fix the nazim-framework
you are authorized to override the governance controls that you are fixing.”
The operator subsequently instructed: “Implement the plan.” This authorizes
repairing the defective completion and proof controls, including necessary
local execution through those defective controls; it is not a claim that a
failed gate passed. Retain fresh preflight observations, separate role review,
actual QA captures and honest failure records. Do not change installed .nizam/
payloads, release, deploy, merge, publish externally or repair the CL-owned bug.

## Architecture and change 1: completion preservation (r02-completion)

Limit first-change product edits to tools/start_path.py and
tools/test_start_path.py. Completion carries the task's recorded contract
identity into eligibility and rechecks approval, identity and scope. Persist
the original contract binding so substitution is refused.

Task-base version 2 records inherited index object/mode/stage separately from
worktree presence, kind, exact content or symlink target, and executable mode.
Observe links without following them. Compare every original endpoint,
including vanished status entries and both rename/copy endpoints. Account for
committed, staged, unstaged and untracked changes with rename detection disabled
for scope accounting. An inherited exception is valid only with unchanged
observations; mutations require declared scope. Legacy records without needed
proof fail closed and require a fresh task rather than rebasing their initial
identity onto current bytes.

## Architecture and change 2: one proof rule (r02-proof-validation)

Depend on accepted first-change completion. Introduce one shared structured QA
validator in tools/workflow_assurance.py, used by direct completion and route
and feature receipt prerequisites. Retain receipt command-capture checks.

New governed completion requires a resolvable assessed candidate manifest using
the existing manifest identity model, with canonical digest and material input
validation. Bare Git identities or unchecked 64-character strings are not
sufficient. Bind authorization and scope eligibility to the assessed candidate.

Pin an exact required-check inventory at task begin (or approved feature
contract), independently of submitted QA. Each check declares exact argv,
expected exit, proof kind and required diagnostic. Extend task, contract and QA
schemas and producer documentation. Validate inventory equality, each capture's
candidate, argv, execution/result, outcome and observed predicate, plus exact
capture/stdout/stderr bytes. Normalize supported raw and published captures
explicitly. Historical records remain readable; new transitions require legacy
records to carry equivalent verifiable proof or fresh execution.

An ordinary failure cannot prove ordinary success. A semantic negative passes
only when its expected exit and diagnostic match, including a successful wrapper
that actually asserts the child's expected refusal. Empty streams are valid
exact bytes; missing streams and failed reads are refusals.

## Phase acceptance

Separate contracts and independent pre/post-code review govern both changes.
Run the two tool suites and compliance/isolation checks, retaining raw streams
and per-execution captures. First-change tests cover approved/unapproved,
missing/substituted/revoked contracts; tracked/untracked/index/mode/link/rename
mutation; vanished endpoints; layer cancellation; unchanged inherited controls;
and legacy behavior. Second-change tests exercise direct and both receipt paths
for failed-capture contradictions, missing inventory/proof, wrong candidates,
material-input changes, wrong argv, tampered streams and reused proof, alongside
ordinary success, semantic negatives and zero-byte streams. Update passing
fixtures to use actual structured capture proof and keep insufficient forms as
rejection controls. No completion claim precedes fresh passing QA and review.
