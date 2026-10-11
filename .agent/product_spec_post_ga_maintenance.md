# Small post-GA maintenance — proposal only, after planning-refresh PR merges

Scope is exactly NDEBT-047, NDEBT-046, NDEBT-045 and A04a. Separate contract/PR2;
no source work before PR1 merges, the actual merge commit becomes contract base,
and both independent pre-code gates approve. Use nonnumeric contract ID
post-ga-maintenance; allocate no provisional NIP3 feature IDs or new phase.
Installed .nizam stays immutablev1.5.0; root source changes remain Unreleased.

## Role split and acceptance behavior

Evaluator authors the regression tests and helpers first, records red047 against
actual unmodified fixture-script trap chain, and designs046 controls independently.
Generator changes only cleanup implementation, truthful payloadhelp and role text,
plus associated versioned documentation/actual debt closeout. Evaluator later runs
all blackbox controls and verifies closure independently. A test-owning session
never approves its own testability/implementation gate; parent preserves role
independence and two-stage pre/post-code gates.

047: actual top-level scratch_dirs replaces cleanup EXIT trap before C13 swap.
Evaluator helper uses an owned private real repository copy and deterministic
actual-swapped-file barrier, not arbitrary sleep. Interrupt the actual swap window;
assert exact original tools/skill.json bytes restored, owned backup and scratch
paths removed and unrelated sentinel retained. Preserve subshell/parent ownership:
child cleanup must never remove parent-owned directories. First red must prove
current script fails these assertions; Generator repair composes safe cleanup
without weakening the scratch-root guards, fixture ownership or C13 checks.

046: improve existing tests only; sandbox remains unchanged. Parent genuinely
listens on a TCP endpoint outside the sandbox. Intact sandbox denies connection;
namespace-only omission while retaining Landlock reaches listener and fails41.
Landlock-only omission retaining namespaces exposes sibling file and fails40.
Generated executable contains valid shebang and real newline bytes; successful
execution returns42. Only EACCES proves blocking; unrelated OSError, missing
interpreter, connection refused, process startup or timeout are separate errors,
never confinement success. Actual PID namespace identity is checked where feasible.
Capable CI runs intact positives and isolated namespace/Landlock/exec mutants.
Restricted workstation keeps explicit UNSUPPORTED/non-full result; do not change
workstation sysctl or weaken the required CI gate.

045: fix only --payload option help paragraph to actual injected six modules/index,
non-injected envelope carveouts and actual12-check C1-C5/C7-C11/C13/C16 set with C6
skipped; no validator behavior or check-count changes.

A04a: standard/AGF.md Evaluator row describes independent Loop1 contract review
then Loop2 verification; templates/AGENTS.md delegation text carries both stages.
Bump modified frontmatter/version/change_log; no behavior or role-permission changes.
ToolsREADME describes actual cleanup/sandbox test proof and helper commands without
claiming namespace conformance on incapable hosts.

## Maintained scope

Root tools/fixtures_self_test.sh, tools/test_convergent_review.py, tools/validate.sh
(help only), standard/AGF.md, templates/AGENTS.md, tools/README.md; envelope helpers
.github/scripts/test_c13_cleanup.py and .github/scripts/test_sandbox_boundaries.py;
compliance.yml only adds helper invocations to existing pinned-action jobs and
preserves current guarded userns step. No sandbox/adapter source change.

Close DEBT047/046/045 and mark A04a complete only AFTER actual regression/namespace
CI and independent QA/evidence closure. Update CURRENT backlog DAG/human view,
ROADMAP/HANDOVER/current Unreleased notes accordingly; no completed feature-number
allocation. New .agent/evidence/post-ga-maintenance/check_maintenance_view.py accepts
proved A04a complete/three closed debt states. Stage1 checker, QA and all evidence
remain frozen snapshots; no overwrite of post-ga-planning-refresh outputs.

Evidence files bind actual commands/exit/candidate/CIrun. Red regression and capable
CI precede closure; pending source stage may carry tests but never claims debt
resolved. Final QA is used only by final closure checker, not by test execution
before QA exists. Parent alone owns bounded task state/counters/history.
No NIP3/WA acceptance/drafting/phase015/newrelease or installedpin update.

## Concrete Evaluator helper and execution protocol (still proposal only)

047 helper default runs current real source; --source-ref 0eb3bcf5e15f612b4c87f86ff8a2521a0e2d66f2
runs the actual old top-level script/trap chain in an owned private git copy.
Red must exit1 with C13 RESTORATION FAIL; exit2 setup/timeout is not regression
proof. The actual fixture-byte barrier precedes owned-process-group SIGTERM.
Evaluator authors this diagnostic/ownership contract; Generator repairs only after
independent recorded red failure. Final CI fixtures_self_test job runs the exact
AT1 green command, followed by existing standing fixture command.

046 helper is required by default: incapable host emits UNSUPPORTED and exit64,
which never passes acceptance. Capable CI executes intact0, Landlock-only omission
40, namespace-only omission41 and executable-permission omission42 with setup/
unexpectedOSerror separately fatal. Existing guarded CI sysctl is retained;
workstation sysctl remains untouched.

The convergent_review CI job installs jsonschema AND pyyaml, then runs exact AT2
helper command and exact AT3 combined full required suite && fixtures command.
No allow-unsupported flag. Independent Evaluator records actual fresh job/step
execution at the fixed candidate, including run/job URLs, headSHA, start/completion,
actual step exit/conclusion and raw command output. A fresh actual GitHub job
rerun may establish execution; never infer acceptance from old green logs.
Initial red/test candidate commits may run in a draft PR while this contract is
approved; final closure waits repaired source candidate and capable green CI.
All task evidence is NEW; stage1 artifacts and checker stay immutable.

Final closure view references actual approvedQA only after parent parses it and
captures the evidence gate. Source/intake predicates accept pending/open state;
no test or CI job depends on future finalQA/closed-debt states. The actual PR1 merge base is 0eb3bcf5e15f612b4c87f86ff8a2521a0e2d66f2.
Helper diagnostics and executable staged predicates are now explicit; no source
work begins until both independent pre-code gates approve.


## Explicit immutable candidate and staged proof predicates

Before final doc changes parent captures once the committed repaired-source SHA in
`.agent/evidence/post-ga-maintenance/source-candidate.json`: full candidate_sha,
actual PR1 base_sha, recorded_at, and source_sha256 for exactly the nine assessed
source/test/workflow paths listed in the contract. Compute each digest from
`git show candidate_sha:path`; verify current source bytes equal that tree. Final
checker reads this record, never ambient HEAD, and refuses overwritten/different
candidate data. Final planning docs can advance HEAD without changing assessed
source files or rebinding proof.

Durable genuine proof destinations are explicit: `capable-ci-receipt.json`,
`red-base-receipt.json`, `00-c13-red-base.txt`, `evidence-gate.txt` within the new
evidence directory and `.agent/qa/post-ga-maintenance.json`. Receipt field schemas
are in contract design_notes. Green receipt binds AT1/2/3 exact commands, declared
capture paths and archived output digests, actual run/job/step URLs/times/conclusions
to the same immutable candidate. Evaluator independently obtains actual GitHub API
run head and step execution; text-only inferred receipts are insufficient. Red
receipt binds exact --source-ref base/exit1/target diagnostic and actual pre-repair
ordering. Shallow-checkout CI fallback must fetch that base object in its owned
execution (or narrowly set fetch-depth0), not count missing-object setup2 as red.

Checker requires explicit `--stage intake` or `--stage final`, with no default or
auto fallback. Intake checks all three debts exclusively Open and A04a pending;
it runs before QA and cannot depend on future proof. Final requires all three
exclusively Resolved and A04a complete; fixed source hashes, red proof, actual CI
receipt, exact approved6/6 QA candidate/commands/evidence and durable evidence-gate
EXIT0 all must match. The intake invocation is AT6. After QA and evidence gate,
final-record authorization requires the separately captured exact command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 .agent/evidence/post-ga-maintenance/check_maintenance_view.py --stage final --self-test
```

Final output goes to `06-final-maintenance-closure.txt`, distinct from AT6 intake
capture; it is subsequent closeout proof, never a future prerequisite for QA.
The checker implementation must expose a pure closure predicate reused by actual
parsed inputs and isolated controls. `--self-test` rejects missing required CI,
wrong command/head/hash, missing/false/wrong-candidate QA, missing evidence gate,
stale source digest, wrong debt/A04a state and intake artifacts passed as final.
Synthetic control fixtures are explicitly checker tests, never real acceptance
or commissioning evidence. Final self-tests also mutate actual captured proof
copies and preserve originals. Every negative must fail a named invariant; setup
errors are separate failures, not valid rejection proof.

Executable pure predicates and 15 named negative controls are in
`/home/cnross/.tmp/nizam-maint-contract-attempt2-vq9bvve9/post-ga-maintenance-closure-predicates-r1.py`, hash-bound in the proposed
contract. They pass isolated synthetic controls without modifying repository files.
The approved Generator task checker incorporates these predicates and reads
actual stage/debt/DAG/candidate/receipt/QA/archive inputs; controls never establish
real CI or QA acceptance.

Final proposal base: `0eb3bcf5e15f612b4c87f86ff8a2521a0e2d66f2` (actual clean merged PR1).
Parent-only intake/counter commit may follow it under the bounded coordinator
semantic guard. All prior evidence and installed payload remain frozen.

CI run.head_sha binds the actual PR source candidate; Actions checkout HEAD can
be a synthetic merge commit. Add an explicit narrow receipt step in each existing
acceptance job which emits actual checkout_sha and the nine current source/test/
workflow SHA256 values. Per-check receipt captures these fields from that job;
all digests must equal the immutable candidate Git-tree map. Do not require Git
checkout HEAD equals PR head. Independent QA binds actual step execution/raw logs
and receipt source identity; stale checkout source digest is a named negative.

CI commands and checkout/digest receipt emission are stateless: never read future
source-candidate.json/CI receipt/QA/final closure. Commit and push repaired source
with intake docs first; parent then records its actual SHA outside the repo.
Evaluator fresh CI execution/rerun uses that exact PR head before metadata commits.
Later evidence/final-doc commits preserve all nine source bytes and bind the same
captured candidate; no self-referential own-commit SHA record is required.

Attempt2 proposed correction: evidence-gate parser accepts both actual `EXIT:0`
and `EXIT: 0`, with explicit positive controls; missing/nonzero markers reject.
Original attempt1 files/verdict remain untouched. Receipt canonical run timestamps
come from actual run_started_at/updated_at; job and step completion values come
from their real completed_at fields, with raw API archived.
