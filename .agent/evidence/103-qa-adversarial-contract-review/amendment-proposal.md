# Amendment proposal: 103 AT4 / 104 AT7-AT8, the capable-host negative control

- **Status:** PROPOSED (draft). It needs operator approval before it is applied.
- **Author:** Planner (Protocol 04), 2026-10-09.
- **Branch / base:** `phase/014-103-sandbox-prereq` at `88959c9`.
- **Nothing has been applied.** `.agent/feature_list_014.json` (sha256 `a4685c94…2f14`)
  and `.agent/product_spec_014.md` (sha256 `8264b395…3bbd`) are byte-identical to `88959c9`.
  Contract 103 and `.agent/run_state.json` are untouched. This file is the only artifact
  written.
- **Governing rules:**
  - `methodology/00_planning.md` §9: substantive re-planning routes to the Planner and
    needs human authorization.
  - `methodology/02_adversarial_tdd.md` §3 and §10: no vacuous passes; assert the targeted
    verdict, not a bare exit.
  - `methodology/03_circuit_breaker.md` §4-§6.

---

## 1. Problem statement

Feature 103 AT4 has two branches, chosen at run time by `unshare --user --map-root-user true`.
It applies one mutation in a scratch copy: it replaces
`exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc` with `exec`
in `tools/linux_trial_sandbox.sh`. Then it requires:

- **capable host:** a non-zero exit and `^(FAIL|ERROR): test_linux_sandbox_blocks_cross_trial_files_and_network`;
- **restricted host:** a non-zero exit and that test's result line carrying `UNSUPPORTED`.

**The capable-host branch is unsatisfiable.** The mutation removes only the
**namespace half** of the sandbox, and no test in the suite detects that half on its own.

| # | Fact | Evidence |
|---|---|---|
| P1 | The mutated run never calls `unshare`, so its outcome does not depend on the host, apart from the probe. On a capable host (probe simulated; everything else real) the suite prints `Ran 54 tests` / `OK` / `CONFORMANCE: FULL`, and AT4 reports `EXPECTATION FAILED`, rc 1. | Evaluator `05-coverage-gaps.txt` F1. Reproduced here: §6 E1 "M1" and E3 "AT4 approved / impl / capable(sim) rc=1". |
| P2 | **The file leg** (`sentinel.read_text()` → exit 40) is enforced by the Landlock half alone. `tools/isolated_trial_adapter.py:101` calls `syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0)`. The sandbox mounts nothing over the path: `--mount-proc` only remounts `/proc`, and there is no pivot/chroot, so the namespaces never hide the sibling file. | Read: `tools/linux_trial_sandbox.sh:19-20` and `tools/isolated_trial_adapter.py:74-104`. |
| P3 | **The network leg** is `socket.socket().connect(('127.0.0.1',9))` followed by `except OSError: pass` (`tools/test_convergent_review.py:774-775` at base). Without a network namespace, connect raises `ConnectionRefusedError` (errno 111), which is an `OSError`, so the leg passes either way. | Read, and executed: §6 E0. |
| P4 | Disabling Landlock **does** turn the test red, with `AssertionError: 40 != 0` (`failures=1`). | Evaluator F1c. Reproduced: §6 E1 "M2". |
| P5 | Even with **all** isolation removed, `test_linux_sandbox_blocks_execution_of_runner_generated_trial_file` still passes. If the exec succeeds, `generated.sh` runs `exit 0`, and the test asserts a return code of 0. The test is vacuous by construction. The three prompt-evaluator tests also pass, because they exercise plumbing, not isolation. | §6 E1 "M2"/"M3" and the §6 A3 run all show `failures=1`, and only the cross-trial test fails. Read: `tools/test_convergent_review.py:884-904` (base numbering). |
| P6 | The activation-time premise probes never simulated AT4's capable branch. `a02_premise_probes.txt` line 15 records only the restricted-host `fail-mut` row, so the premise went unproven when 1.1.0/1.1.1 were authored. This is a Planner defect, not a Generator defect. | `.agent/evidence/backlog-reconciliation-2026-10-08/a02_premise_probes.txt:15`. P13 has no capable-branch AT4 row. |

The same refuted premise appears in five places:

1. **Feature 103 AT4** (`acceptance_tests[3]`).
2. **The 103 description**, CAPABLE-HOST EVIDENCE OBLIGATION sentence: "a throwaway branch applying exactly AT4's sandbox-removal mutation makes the job fail on test_linux_sandbox_blocks_cross_trial_files_and_network".
3. **The 104 description**, CI EVIDENCE CONTRACT: "whose only change is 103 AT4's sandbox-removal mutation of tools/linux_trial_sandbox.sh … showing the new job failing on test_linux_sandbox_blocks_cross_trial_files_and_network".
4. **104 AT7/AT8.** Their command text does not name the mutation. But AT7 (`conclusion=='failure'`) and AT8 (a FAIL line for the cross-trial test) can only be met if the description's mutation fails the job. With the approved mutation, the CI job would be green: `Ran 54 tests / OK`, P1. So AT7 and AT8 are unsatisfiable *as specified*.
5. **The spec.** The 1.1.1 change_log says "103's capable-host branches are discharged by 104's CI evidence". The 104 bullet says "CI evidence is a green run plus a throwaway-branch negative control". Neither names a mutation, so neither is false on its face, but both rest on the premise.
6. **Contract 103 rev 1.** It repeats the premise in `verification[3].expected_outcome`, `design_notes.available_isolation_branch`, `design_notes.capable_host_obligation.discharge` and non_goals bullet 5. Section 5 below covers it; the Planner does not edit contracts.

---

## 2. Options

The original intent is the standard every option is measured against: **on a capable host,
removing the sandbox's isolation must make the required-mode conformance run fail, on
the cross-trial test.** The restricted-host branch must keep its own value.
Negative control N2 shows that this branch catches a probe that goes through the sandbox
script instead of the host's `unshare`. It is not vacuous (see A2 below).

### Option A1 (RECOMMENDED): remove *both* isolation halves, and pin the breach signature

AT4 gains a second fail-closed `--replace`, which disables the Landlock restrict-self call
in the adapter. The capable branch additionally requires `^AssertionError: 40 != 0`, the
exit code that only the cross-trial probe's sibling-secret read produces. A grep shows that
`SystemExit(40)` occurs once in the suite, at the file leg; 41 and 42 are the other legs.

Replacement AT4. This is the exact JSON string value; the only differences from the
approved text are the inserted `--replace` and `--expect` pairs:

```json
"python3 -c \"import subprocess,sys; cap=subprocess.run(['unshare','--user','--map-root-user','true'],capture_output=True).returncode==0; a=['python3','.agent/evidence/phase-014-activation/gates/scratch_run.py','--replace','tools/linux_trial_sandbox.sh','exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc','exec','--replace','tools/isolated_trial_adapter.py','syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0)','pass','--expect-rc','nonzero']+(['--expect','^(FAIL|ERROR): test_linux_sandbox_blocks_cross_trial_files_and_network','--expect','^AssertionError: 40 != 0'] if cap else ['--expect','^test_linux_sandbox_blocks_cross_trial_files_and_network.*UNSUPPORTED'])+['--','python3','tools/test_convergent_review.py']; sys.exit(subprocess.run(a).returncode)\""
```

Proven by execution: §6 E3, the amended-JSON run, and the N1-N6 controls.

| Tree / host | Result |
|---|---|
| impl, capable (sim) | rc 0, EXPECTATIONS HELD |
| impl, restricted (real) | rc 0, EXPECTATIONS HELD |
| base `88959c9`, restricted (real) | **rc 1**: red at base for the intended reason, no UNSUPPORTED line |
| base `88959c9`, capable (sim) | rc 0. On a capable host the branch is a declared non-regression guard: it is satisfied before 103 exists, and it fails any 103 implementation that neuters the five tests (N1, N3) or weakens the cross-trial assertion (N6). |

The negative controls, run against the amended AT4 taken from the amended JSON:

| Control | capable (sim) | restricted |
|---|---|---|
| N1: the probe always reports "unavailable" | **rc 1** | rc 0 (correct behaviour there) |
| N2: the probe goes through `tools/linux_trial_sandbox.sh` | rc 0 (right answer there) | **rc 1** |
| N3: the decorator silently returns when isolation is available | **rc 1** | rc 0 (not reachable) |
| N4: sandbox exec line already removed in the tree (evaluator m22) | **rc 3** (mutation precondition, fail-closed) | **rc 3** |
| N5: Landlock call already removed in the tree | **rc 3** | **rc 3** |
| N6: cross-trial assertion weakened to accept 40/41 (evaluator m07) | **rc 1** | rc 0 (S08 catches it there) |
| Pin check: a hypothetical plumbing crash (adapter exits 7) | **rc 1**: `^AssertionError: 40 != 0` fails, although the FAIL line matches | n/a |

**Fidelity of the simulation.** Under A1 the mutated sandbox script never calls `unshare`,
so `helpers/capable_shim.sh` answers **only the capability probe**. Every trial runs the
real, mutated code path. The capable-branch result is therefore what a real capable host
produces. The assumption is that the adapter can still create a Landlock ruleset; if it
cannot, the adapter raises and the cross-trial test still fails, but the 40 pin would then
report a different exit. That is the honest outcome, because 104's positive run would fail
first. This is stronger than F1c's simulation (A2), where the sandbox still calls `unshare`
and the shim drops the namespaces.

**§10 review:**
- **(a) whole-file grep:** none. The expectations are line-anchored regexes over one run's output.
- **(b) blind scope guard:** not applicable.
- **(c) bare adjacency:** none. The FAIL line and the `40 != 0` line come from the same run, and exit 40 is unique to the targeted leg.
- **(d) false-passing literal substring:** anchored `^…` patterns only.
- **(e) swallowed or bare exit:** no pipeline. The command's own exit is asserted *together with* the targeted verdict line, which is §10(e)'s prescribed remedy, and both mutations are fail-closed (rc 3 on precondition failure).
- **Vacuity:** the AT is red at base on this host, green under a correct implementation on both branches, and red for each injected defect in the branch where that defect is observable.

**What A1 does NOT prove:** that the namespace half is load-bearing. P1-P3 show that no
test can show that today. A1 states this openly (§3) and logs it as NDEBT-046 (§3.6). It does
not pretend otherwise.

### Option A2: Landlock-only mutation (evaluator F1c)

```json
"python3 -c \"import subprocess,sys; cap=subprocess.run(['unshare','--user','--map-root-user','true'],capture_output=True).returncode==0; a=['python3','.agent/evidence/phase-014-activation/gates/scratch_run.py','--replace','tools/isolated_trial_adapter.py','syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0)','pass','--expect-rc','nonzero']+(['--expect','^(FAIL|ERROR): test_linux_sandbox_blocks_cross_trial_files_and_network'] if cap else ['--expect','^test_linux_sandbox_blocks_cross_trial_files_and_network.*UNSUPPORTED'])+['--','python3','tools/test_convergent_review.py']; sys.exit(subprocess.run(a).returncode)\""
```

A2 discriminates on a capable host (§6 E3: impl capable rc 0; base restricted rc 1). Two
things count against it.

- **It weakens the restricted branch.** The sandbox script keeps calling `unshare`, so
  negative control N2 (the probe goes through the sandbox script) **passes AT4 on the
  restricted host** (§6 E4: "N2 alt A2 restricted rc=0"). A1 catches the same defect
  (rc 1). Under A2, N2 would rest on supplementary checks alone.
- **It does not match the original intent.** It removes half the isolation, not "the
  sandbox", and its capable-branch result is a shim simulation rather than the real path.

§10 is clean, so A2 has no vacuity defect. It loses on coverage. **Rejected in favour of A1.**

### Option A3: bypass the adapter entirely (`exec "$@"`)

A3 replaces the two-line exec with `exec "$@"`. It discriminates: in the §6 A3 run, the
cross-trial test FAILs with `40 != 0`, and the restricted-branch power matches A1. **Rejected
on construction grounds:**

- The pinned OLD string contains `$SELF_DIR`, `$ROOT`, `$RUNNER` and `"$@"`. Inside the AT's
  bash double-quoted `python3 -c "…"`, each needs `\$` and `\"` escaping inside a JSON string,
  which makes it the most fragile text in the list.
- It also removes the adapter's runner validation and `chdir`. A failure could then be
  plumbing rather than isolation, although the 40 pin would still separate the two.

### Option B: strengthen the test so that it discriminates the namespaces (not in 103)

The approved AT4 text would stay. Instead, the network leg of
`test_linux_sandbox_blocks_cross_trial_files_and_network` would be made discriminating:

- the test binds a listener on `127.0.0.1:<ephemeral>` **outside** the sandbox and passes
  the port to the probe;
- the probe exits 41 if `connect` succeeds.

This works because a new network namespace has its own, down loopback, while removing
`--net` leaves the listener reachable. Here, a child process outside any namespace
connects (§6 B-premise, rc 0 "child connected"). The inside-the-namespace half **cannot be
proven on this host**, which restricts user namespaces, and the shim cannot simulate it,
because the shim provides no network namespace, so the unmutated strengthened test would
FAIL under simulation. The positive control could first be observed only in 104's CI.

**Judgment: B does not belong in 103.**

1. It changes a test body. That contradicts 103's approved design ("the only change to a
   test is a decorator", contract S08) and its concern, NDEBT-043 (prerequisite reporting).
   Sandbox-test adequacy is a different concern.
2. It adds scope (a MINOR spec bump, plus estimate) at the contract's **last permitted
   attempt**.
3. Its positive control is unobservable before CI.

Under A1 it is logged as **NDEBT-046** (§3.6), together with P5 (the vacuous execution
test), as a candidate for a later feature or 101's simplification review.

Exact description text, in case the operator nevertheless chose B: append to 103's scope:
"test_linux_sandbox_blocks_cross_trial_files_and_network's network leg is made
discriminating (a 127.0.0.1 listener bound outside the sandbox; the probe exits 41 on a
successful connect); this is the only permitted test-body change". AT4 would stay
byte-identical, and the spec would go to 1.2.0 (MINOR), not 1.1.3.

### Option C: narrow AT4 to the restricted host and move the capable proof to 104

Replacement AT4 under C:

```json
"python3 -c \"import subprocess,sys; cap=subprocess.run(['unshare','--user','--map-root-user','true'],capture_output=True).returncode==0; print('capable host: AT4 not applicable here; proven by 104 AT7/AT8') if cap else None; sys.exit(0 if cap else subprocess.run(['python3','.agent/evidence/phase-014-activation/gates/scratch_run.py','--replace','tools/linux_trial_sandbox.sh','exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc','exec','--expect-rc','nonzero','--expect','^test_linux_sandbox_blocks_cross_trial_files_and_network.*UNSUPPORTED','--','python3','tools/test_convergent_review.py']).returncode)\""
```

104 would then carry A1's mutation and the 40 pin, using the same 104 text as §3.3/§3.4.

**Rejected.** The capable branch becomes `sys.exit(0)`, a **vacuous pass** by construction
(§3 false-pass, and §10's "not acceptance coverage"). The Evaluator would lose the
capable-host check on any capable workstation. C is strictly dominated by A1, which keeps a
real, satisfiable capable branch *and* hands the same proof to 104.

### Recommendation

**A1.** It is the smallest change that makes every affected acceptance test satisfiable and
non-vacuous. It keeps the original intent ("removing isolation fails the run"), keeps the
restricted branch's power (N2), adds an attributable breach signature (the 40 pin), changes
no implementation scope, and states the namespace-coverage gap openly instead of claiming it.

**Not in scope of the amendment, but recommended at the contract stage:** binding 104's
throwaway diff to exactly this mutation. That is a supplementary check for contract 104, so
it needs no AT change; see §5.2.

---

## 3. Exact before → after text (option A1)

### 3.1 `.agent/feature_list_014.json`, feature 103

**`acceptance_tests[3]` (AT4).** Before, as in the file now:

```json
"python3 -c \"import subprocess,sys; cap=subprocess.run(['unshare','--user','--map-root-user','true'],capture_output=True).returncode==0; a=['python3','.agent/evidence/phase-014-activation/gates/scratch_run.py','--replace','tools/linux_trial_sandbox.sh','exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc','exec','--expect-rc','nonzero']+(['--expect','^(FAIL|ERROR): test_linux_sandbox_blocks_cross_trial_files_and_network'] if cap else ['--expect','^test_linux_sandbox_blocks_cross_trial_files_and_network.*UNSUPPORTED'])+['--','python3','tools/test_convergent_review.py']; sys.exit(subprocess.run(a).returncode)\""
```

After: the Option A1 string in §2, verbatim.

**`description`.** Replace exactly this substring, which occurs once.

Before:

> 104 AT7/AT8 (a throwaway branch applying exactly AT4's sandbox-removal mutation makes the job fail on test_linux_sandbox_blocks_cross_trial_files_and_network = AT4's capable branch).

After:

> 104 AT7/AT8 (a throwaway branch applying exactly AT4's isolation-removal mutation, i.e. both of AT4's replacements: the unshare namespace line in tools/linux_trial_sandbox.sh and the Landlock restrict-self call in tools/isolated_trial_adapter.py, makes the job fail on test_linux_sandbox_blocks_cross_trial_files_and_network with 'AssertionError: 40 != 0', the cross-trial secret read = AT4's capable branch). KNOWN LIMIT (NDEBT-046): no test in the suite detects the loss of the namespace half on its own. Removing only the unshare line leaves all 54 tests passing, because Landlock still enforces the file leg and the network leg accepts any OSError (ECONNREFUSED included); so AT4 proves that removing isolation is detected, through the filesystem leg. Making the sandbox tests discriminate the namespaces is outside 103's scope.

**`acceptance_provenance`.** Before:
`{"new_feature_design": "all (maintenance fold approved; tests are Planner design)"}`.
After:
`{"new_feature_design": "all (maintenance fold approved; tests are Planner design)", "operator_approved_amendment_1_1_3": [4]}`

### 3.2 `.agent/feature_list_014.json`, feature 104

**`acceptance_tests[6]` (AT7): unchanged.** It binds the throwaway branch prefix, the run
conclusion and the job's conclusion. All three are satisfiable once the mutation in the
description is A1's.

**`acceptance_tests[7]` (AT8).** Replace the final assertion.

Before:

```json
... b='\\n'.join(t); assert re.search(r'\\b(FAIL|ERROR): test_linux_sandbox_blocks_cross_trial_files_and_network\\b',b), t[-1]\""
```

After:

```json
... b='\\n'.join(t); assert re.search(r'\\b(FAIL|ERROR): test_linux_sandbox_blocks_cross_trial_files_and_network\\b',b) and re.search(r'\\bAssertionError: 40 != 0\\b',b), t[-1]\""
```

Everything before `b='\\n'.join(t);` is byte-identical. The full amended string was
generated and executed from a scratch copy of the JSON (§6 amend_check). On synthetic
evidence:

| Synthetic job log | Amended AT8 | Approved AT8 |
|---|---|---|
| FAIL line plus `40 != 0` | rc 0 | rc 0 |
| FAIL line plus `1 != 0` (plumbing crash) | **rc 1** | rc 0 (it passes the crash) |
| `40 != 0`, but a different test FAILs | rc 1 | rc 1 |

**`description`.** Replace exactly this substring, which occurs once.

Before:

> (negative control) on a throwaway branch named throwaway/104-<slug> whose only change is 103 AT4's sandbox-removal mutation of tools/linux_trial_sandbox.sh — .agent/evidence/104/ci-negative-run.txt and ci-negative-log.txt by the same two commands, showing the new job failing on test_linux_sandbox_blocks_cross_trial_files_and_network; the throwaway branch is deleted afterwards.

After:

> (negative control) on a throwaway branch named throwaway/104-<slug>, never merged, whose only change is 103 AT4's isolation-removal mutation (exactly AT4's two --replace operations: the unshare namespace line of tools/linux_trial_sandbox.sh becomes `exec`, and the Landlock restrict-self call of tools/isolated_trial_adapter.py becomes `pass`) — .agent/evidence/104/ci-negative-run.txt and ci-negative-log.txt by the same two commands, showing the new job failing on test_linux_sandbox_blocks_cross_trial_files_and_network with 'AssertionError: 40 != 0' (the cross-trial secret was read); the throwaway branch is deleted afterwards.

**`acceptance_provenance`.** Before:
`{"new_feature_design": "all (maintenance fold approved; tests are Planner design)"}`.
After:
`{"new_feature_design": "all (maintenance fold approved; tests are Planner design)", "operator_approved_amendment_1_1_3": [8]}`

**`estimated_lines`: unchanged for both features** (103: 280; 104: 230). A1 changes
verification text, not implementation scope.

### 3.3 `.agent/feature_list_014.json`, top level

- `"spec_version": "1.1.2"` → `"spec_version": "1.1.3"`, in lockstep with the spec.
- `planning_note`: replace the substring `Spec 1.1.2 (validator round-1 corrections` with
  `Spec 1.1.3 (1.1.3: 103 AT4 and 104 AT8 amended after the Evaluator refuted the capable-host premise of the sandbox-removal mutation — the mutation now removes both isolation halves and pins 'AssertionError: 40 != 0'; operator decision <T-DECISION>; NDEBT-046 logged. 1.1.2: validator round-1 corrections`

  `<T-DECISION>` is the `operator_gate_decision` timestamp recorded in `run_state` before
  application (NDEBT-018).

A scratch copy with exactly §3.1-§3.3 applied (excluding the planning_note and provenance
edits) differs from the real file only in: 103 `description`, 103 `acceptance_tests[3]`,
104 `description`, 104 `acceptance_tests[7]`, and the top-level `spec_version`. Every other
key is equal (§6 amend_check: "changed fields").

### 3.4 `.agent/product_spec_014.md`

**Frontmatter.** Before:

```yaml
version: 1.1.2
spec_version: "1.1.2"
...
updated_at: "2026-10-08T13:22:24Z"
change_log:
  - version: "1.1.2"
```

After. Prepend the new entry, newest first, following the file's existing order:

```yaml
version: 1.1.3
spec_version: "1.1.3"
...
updated_at: "<T-APPLY>"
change_log:
  - version: "1.1.3"
    date: "<T-APPLY>"
    summary: "PATCH (no scope change; design intent unchanged; product_spec_013 1.1.2 / 014 1.0.1 precedent: factual correction of acceptance-test commands), routed through the Planner per methodology/00_planning.md Section 9 under operator decision <T-DECISION> (run_state operator_gate_decision, recorded before this change per NDEBT-018). The Evaluator's contract-103 review (.agent/qa/103-contract-review.json issue 1; evidence 05-coverage-gaps.txt F1/F1c) refuted, by execution, the premise that removing the unshare namespaces from tools/linux_trial_sandbox.sh turns test_linux_sandbox_blocks_cross_trial_files_and_network red on a capable host: Landlock alone enforces the file leg and the network leg accepts any OSError, so the suite stays 'Ran 54 tests / OK / CONFORMANCE: FULL'. Applied: 103 AT4's mutation now removes both isolation halves (adds the fail-closed replacement of the adapter's Landlock restrict-self call) and its capable branch also requires 'AssertionError: 40 != 0'; 104 AT8 requires the same breach signature; the 103 and 104 descriptions and this spec's 103/104 bullets name the isolation-removal mutation; the namespace-coverage gap and the vacuous execution test are logged as NDEBT-046 (not in phase-014 scope). Proven in scratch (amendment-proposal.md Section 6): red at base on the restricted host, green under a contract-faithful implementation on both branches, and red for each injected defect in the branch that can observe it. feature_list_014 spec_version moves to 1.1.3 in lockstep."
  - version: "1.1.2"
```

Also `last_audited: "2026-10-08"` → `last_audited: "<T-APPLY date>"`.

**103 bullet** (the "Maintenance tranche — design decisions" section). Before:

```markdown
  `--allow-unsupported-isolation` turns the same report into exit 0, for local
  development only; CI never passes it. On a capable host the run prints
  `CONFORMANCE: FULL`. The capability probe is the host's `unshare`, independent of
  the sandbox script. The sandbox script and the trial adapter are not modified.
```

After: the same four lines, followed by:

```markdown

  Capable-host proof (103 AT4's capable branch, discharged in CI by 104's negative
  control): with *both* isolation halves removed in a scratch copy — the `unshare`
  namespace line of the sandbox script and the adapter's Landlock restrict-self call —
  the run fails on `test_linux_sandbox_blocks_cross_trial_files_and_network` with
  `AssertionError: 40 != 0` (the cross-trial secret was read). Removing the namespaces
  alone is detected by no test in the suite: Landlock still enforces the file leg and
  the network leg accepts any `OSError`. That gap is `NDEBT-046`, outside 103's scope.
```

**104 bullet.** Before:

```markdown
  `schema/README.md` states that the suite is the review schema family's **sole
  validator**; C12 coverage of that family is left to 101 / `H-CONSOLIDATION`. CI
  evidence is a green run plus a throwaway-branch negative control.
```

After:

```markdown
  `schema/README.md` states that the suite is the review schema family's **sole
  validator**; C12 coverage of that family is left to 101 / `H-CONSOLIDATION`. CI
  evidence is a green run plus a throwaway-branch negative control. The throwaway
  branch is never merged; its only change is 103 AT4's isolation-removal mutation
  (both halves removed), and the job must fail on
  `test_linux_sandbox_blocks_cross_trial_files_and_network` with
  `AssertionError: 40 != 0`.
```

**"Acceptance-test provenance and probe coverage" section.** Before:

```markdown
- **new_feature_design** — all tests of 103–109 (the fold was approved; their tests are
  Planner design).
```

After: the same, followed by:

```markdown
- **operator_approved_amendment_1_1_3** — 103 AT4 and 104 AT8, rewritten after the
  Evaluator refuted their capable-host premise (`.agent/qa/103-contract-review.json`
  issue 1); operator decision <T-DECISION>. Planner design in origin.
```

### 3.5 Version-bump implications

- **Spec 1.1.2 → 1.1.3 (PATCH).** The precedent is 014 1.0.1 and product_spec_013 1.1.2:
  a factual correction of acceptance-test commands, with design intent unchanged. No feature
  is added or removed, no interface changes, and no *approved* contract is invalidated:
  contract 103 is `proposed`, and 104 has no contract.
- **Feature list.** `spec_version` 1.1.3 moves in lockstep. Drift gate: no pending feature
  is left on 1.1.2, because the field is list-level.
- **Option B instead** would be MINOR (1.2.0), because it adds scope.
- **Releases.** No release-facing version changes. 103/104's `version_impact` (MINOR at the
  next release) is unchanged.

### 3.6 `docs/planning/DEBT.md` (applied together with the amendment)

New Open row, inserted at the top of Open (highest id first). Bump the file's version and
add a change_log entry per its convention.

> | NDEBT-046 | <T-APPLY date> | Low | **The convergent-review sandbox tests do not discriminate the namespace half of the trial sandbox, and one sandbox test is vacuous.** Re-verified at `88959c9` in scratch (`.agent/evidence/103-qa-adversarial-contract-review/amendment-proposal.md` §6; evaluator `05-coverage-gaps.txt` F1/F1c): (a) removing `exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc` from `tools/linux_trial_sandbox.sh` leaves `tools/test_convergent_review.py` at `Ran 54 tests / OK` — `test_linux_sandbox_blocks_cross_trial_files_and_network`'s file leg is enforced by Landlock alone and its network leg (`connect(('127.0.0.1',9))`, `except OSError: pass`) passes on ECONNREFUSED as well as on an unreachable namespace loopback; nothing exercises the PID/IPC/UTS namespaces; (b) `test_linux_sandbox_blocks_execution_of_runner_generated_trial_file` passes with all isolation removed, because a successful exec of `generated.sh` (`exit 0`) yields the asserted return code 0. | OPEN — not a sandbox defect (the sandbox is fail-closed and unchanged); a test-adequacy gap. Phase-014 103 AT4 / 104 AT7-AT8 therefore prove isolation removal through the filesystem leg only (spec 1.1.3). Remedy candidates: a network leg that connects to a listener bound outside the sandbox (exit 41 on success); a generated file whose successful exec exits with a distinct non-zero code; a PID-namespace assertion (e.g. the runner observes itself as a low PID). Positive controls need a capable host (CI). Candidate input to feature 101's simplification review or a post-104 maintenance feature; not scheduled. |

---

## 4. Authority and the exact decision requested

The changed tests are operator-approved. 103 and 104 carry `acceptance_provenance:
new_feature_design`, approved through the H-PHASE-014 maintenance fold, operator decision
2026-10-08T11:21:14Z. Changing them is **substantive re-planning** under
`methodology/00_planning.md` §9: the operator's authorization did not specify this test
shape. It routes through the Planner, and the Planner cannot authorize it. The Orchestrator
also cannot register it on its own power, because no recorded decision covers it.

**Sequence (NDEBT-018: record before act):**

1. The operator decides.
2. The Orchestrator appends an `operator_gate_decision` history entry to
   `.agent/run_state.json` with the verbatim text and timestamp `<T-DECISION>`.
3. The Planner applies §3.1-§3.6 in one commit `<A>` on `phase/014-103-sandbox-prereq`.
   The commit touches only `.agent/feature_list_014.json`, `.agent/product_spec_014.md`
   and `docs/planning/DEBT.md`; the Orchestrator commits `run_state` separately or in the
   same commit, as it prefers.
4. Contract 103 revision 2 is drafted against `<A>` (§5).

**Decision requested. The operator is asked to reply with exactly:**

> **Approve amendment A1 to the phase-014 acceptance tests (spec 1.1.3): 103 AT4 removes both isolation halves (namespaces and Landlock) and its capable branch requires 'AssertionError: 40 != 0'; 104 AT8 requires the same signature; the 103/104 descriptions and spec bullets are updated as proposed; NDEBT-046 is logged. Approved.**

Alternatives the operator may give instead: "Approve option A2 …" (not recommended);
"Decline, keep the approved tests". If declined, contract 103 cannot be approved without
claiming an unsatisfiable AT. Feature 103 would have to be BLOCKED, or descoped under
`methodology/03_circuit_breaker.md` §6, and 104 AT7/AT8 would remain unsatisfiable.

---

## 5. Effect on contracts 103 and 104

### 5.1 Contract 103

- **Attempt budget.** `run_state.circuit_breaker["103-contract"] = {attempts: 2, limit: 3}`.
  Revision 2 is attempt 3/3, the **last permitted**. The amendment does **not** reset the
  counter. A reset is only available after a BLOCK, through a human under
  `03_circuit_breaker.md` §6, and 103 is paused, not blocked. Revision 2 must therefore
  fold everything in one pass.

- **Issue 1 (AT4, high): resolved by this amendment.** Revision 2 must:
  - copy the amended AT4 verbatim into `verification[3]` (`acceptance_test` == `command`
    == the feature-list string);
  - set `expected_outcome`. Restricted host: rc 0 with UNSUPPORTED. Capable host: FAIL
    line plus `40 != 0`, not exercised here and discharged by 104 AT7/AT8.
  - set `state_at_base`: restricted, rc 1, no UNSUPPORTED line; both mutation
    preconditions hold (§6 E3: base restricted shows "replaced 1 occurrence" twice);
  - reword `design_notes.available_isolation_branch`,
    `capable_host_obligation.discharge` and non_goals bullet 5 to the §3.1 wording,
    including the NDEBT-046 known limit;
  - extend the hazards line ("AT4's mutation needs the exec line to occur exactly once …")
    to the Landlock call in `tools/isolated_trial_adapter.py`. It occurs once at line 101,
    and AT5 already freezes both files.

  The evidence filename `at4-sandbox-removal-mutation.txt` may stay. If it is renamed,
  S01's files_create count must follow.

- **Re-anchor (mandatory).** Several supplementary checks are anchored to `88959c9`:
  - **S01** compares the ATs with `git show 88959c9:.agent/feature_list_014.json`, so it
    would reject the amended AT4.
  - **S02** decomposes feature-list changes against `88959c9`, so it would see the
    amendment as foreign.
  - **S07** guards `.agent/product_spec_014.md` against `88959c9`, so it would fail on
    spec 1.1.3.
  - S03-S06, S08, S14 and S15 also use `BASE = '88959c9'`.

  Revision 2 must set `BASE` to `<A>`, and rename `state_at_base_88959c9` consistently,
  S01's own key check included. `<A>` changes only the three planning files, so every
  code-surface comparison (tools/, schema/, .github/, the frozen infrastructure) gives
  identical results against `<A>` and `88959c9`. S15's "88959c9 is an ancestor of B"
  still holds.

- **Issues 2-4 (medium/medium/low): fixable inside the contract, no AT change.**
  - **S17:** the flag together with partial capability must still produce the five FAIL
    lines and `CONFORMANCE: NOT FULL (run unsuccessful)` (evaluator F3; mutant m05c).
  - **S18:** a capable shim plus a jsonschema stub that raises ImportError gives exit 0,
    the bare `CONFORMANCE: FULL`, and five ordinary skips (evaluator F4; mutant m18).
    This is also the first exercise of the capable gating branch.
  - **S14 hardening:** spawn tokens in added lines are confined to the import line and to
    `probe_user_namespace_isolation`, regardless of class nesting or aliasing (m08b/m08c).

- **Claims discipline.** 103 still claims no capable-host pass. The capable branches of
  AT1, AT2 and AT4 stay with 104, which can now be satisfied.

### 5.2 Feature 104 (no contract yet)

- **AT7: text unchanged, now satisfiable.** With A1's mutation the CI job fails, as shown
  by the faithful simulation in §2.
- **AT8: amended.** It also requires the 40 breach signature.
- **The description names the A1 mutation.** The throwaway branch modifies
  `tools/isolated_trial_adapter.py` as well. It is never merged, and the 104 description
  already scopes `.github/` to 104 alone, which this does not touch.
- **Recommended supplementary check for contract 104 (a contract-level S-check; no
  operator approval needed).** Before deleting the throwaway branch, capture
  `.agent/evidence/104/ci-negative-diff.txt`. Its first line is
  `git diff <base40> <head40> --`, followed by the body and `EXIT:0`. Assert:
  - `<head40>` equals `headSha` in `ci-negative-run.txt`;
  - `<base40>` is an ancestor of HEAD;
  - the changed files are exactly `{tools/isolated_trial_adapter.py, tools/linux_trial_sandbox.sh}`;
  - the `+`/`-` lines are exactly the four mutation lines.

  This closes the gap where AT7/AT8 accept *any* failing throwaway change. It was proven
  in scratch on a real commit: the exact mutation gives rc 0; the same mutation plus an
  extra `tools/convergent_review.py` line gives rc 1 with the offending file listed.
  Check body:

  ```python
  import json,re,subprocess,sys
  R=json.loads('\n'.join(open('.agent/evidence/104/ci-negative-run.txt').read().splitlines()[1:-1]))
  t=open('.agent/evidence/104/ci-negative-diff.txt').read().splitlines()
  m=re.fullmatch(r'git diff ([0-9a-f]{40}) ([0-9a-f]{40}) --',t[0]); assert m and t[-1]=='EXIT:0', (t[0],t[-1])
  assert m.group(2)==R['headSha'], (m.group(2),R['headSha'])
  assert subprocess.run(['git','merge-base','--is-ancestor',m.group(1),'HEAD']).returncode==0, 'diff base is not an ancestor of HEAD'
  b=t[1:-1]
  F=sorted(re.findall(r'^diff --git a/(\S+) b/\S+$','\n'.join(b),re.M))
  D=sorted(l.rstrip(chr(92)).rstrip() for l in b if l[:1] in '+-' and l[:3] not in ('+++','---'))
  W=sorted(['-exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc','+exec','-        syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0)','+        pass'])
  assert F==['tools/isolated_trial_adapter.py','tools/linux_trial_sandbox.sh'] and D==W, (F,D)
  ```

- **Carried forward, unchanged by this amendment.** 104's runner must have `jsonschema`
  installed, because AT1's capable branch and 104 AT6 forbid `skipped`. If hosted runners
  cannot create a Landlock ruleset, the positive run fails first; escalate, never weaken.

---

## 6. Evidence (scratch only; executed 2026-10-09 on this host)

**Host.** `kernel.apparmor_restrict_unprivileged_userns = 1`. The probe
`unshare --user --map-root-user true` returns rc 1
(`write failed /proc/self/uid_map: Operation not permitted`). Kernel 6.8.0-142, Python
3.12.3, jsonschema present.

**Setup.** Everything ran in the session scratchpad, outside the repository:

- a clone at `88959c9` (`base`);
- a second clone at `88959c9` plus contract 103 plus the evaluator's
  `helpers/implement.py` (`impl`: the positive control, +4 modified files);
- `capbin/unshare` = `helpers/capable_shim.sh` (sha256 `161ce443…26ed`).

"capable (sim)" means `PATH=capbin:$PATH`. The repository's tracked files, the feature
list, the spec, the contract and run_state were never written. `git status` was unchanged
before and after.

**Reproduction.** In such a clone, run the amended AT4 string twice:
`PATH=<capbin>:$PATH bash -c '<AT4>'`, and plain `bash -c '<AT4>'`.

**E0: network leg outside any namespace.**

```
OSError ConnectionRefusedError 111 -> caught by `except OSError: pass`
```

**E1: suite profile per mutation, impl tree, capable (sim).**

```
M0 no mutation                                   RC 0  Ran 54 tests  OK                 CONFORMANCE: FULL
M1 namespaces removed (approved AT4 mutation)    RC 0  Ran 54 tests  OK                 CONFORMANCE: FULL
M2 Landlock disabled only (F1c)                  RC 1  AssertionError: 40 != 0  FAILED (failures=1)  CONFORMANCE: NOT FULL (run unsuccessful)
M3 namespaces removed AND Landlock disabled (A1) RC 1  AssertionError: 40 != 0  FAILED (failures=1)  CONFORMANCE: NOT FULL (run unsuccessful)
```

**A3 run.** Two-line exec replaced by `exec "$@"`, capable (sim): `AssertionError: 40 != 0`,
`FAILED (failures=1)`, EXPECTATIONS HELD.

**E2: same mutations, restricted host (real).** M1 and M3 both give: five
`… skipped 'UNSUPPORTED: user-namespace isolation unavailable (unshare: write failed /proc/self/uid_map: Operation not permitted)'`,
`OK (skipped=5)`, `CONFORMANCE: NOT FULL (UNSUPPORTED isolation-dependent tests: 5)`, RC 1.

**E3: the AT commands themselves.** Approved AT4:

```
impl capable(sim) rc=1 EXPECTATION FAILED | impl restricted rc=0 HELD | base capable(sim) rc=1 | base restricted rc=1
```

Proposed A1, executed from the amended JSON copy. In every row, both mutations report
"replaced 1 occurrence".

```
impl capable(sim) rc=0 HELD   (PASS non-zero | PASS FAIL-line | PASS '^AssertionError: 40 != 0')
impl restricted   rc=0 HELD   (PASS non-zero | PASS UNSUPPORTED line)
base capable(sim) rc=0 HELD   (declared capable-host guard)
base restricted   rc=1 EXPECTATION FAILED (no UNSUPPORTED line: red at base for the intended reason)
```

Alternative A2:

```
impl capable(sim) rc=0 | impl restricted rc=0 | base capable(sim) rc=0 | base restricted rc=1
```

**E4: negative controls.** One defect each, in a fresh copy of impl.

```
N1 probe always unavailable          | A1: capable rc=1, restricted rc=0 | A2: capable rc=1, restricted rc=0 | approved: capable rc=1, restricted rc=0
N2 probe via linux_trial_sandbox.sh  | A1: capable rc=0, restricted rc=1 | A2: capable rc=0, restricted rc=0  <- A2 misses it
N3 decorator silently passes         | A1: capable rc=1, restricted rc=0
N4 exec line already removed in tree | A1: rc=3 both (MUTATION PRECONDITION FAILED)
N5 Landlock call removed in tree     | A1: rc=3 both (MUTATION PRECONDITION FAILED)
N6 cross-trial assertion weakened    | A1: capable rc=1, restricted rc=0
PIN plumbing-crash variant (adapter exits 7), capable(sim): rc=1 — PASS FAIL-line, FAIL '^AssertionError: 40 != 0'
```

**amend_check.** Amended feature-list copy, scratch only.

```
changed fields: [('103','description'), ('103','acceptance_tests',[3]), ('104','description'), ('104','acceptance_tests',[7])] | spec_version 1.1.2 -> 1.1.3
other top-level keys equal: True
104 AT8 amended on synthetic evidence: good rc=0; plumbing crash (1 != 0) rc=1 (approved AT8: rc=0); other test failing rc=1
```

**B premise.** A listener bound on 127.0.0.1 is reachable from a child process outside any
namespace: rc 0, "child connected". The inside-the-namespace half is not observable on
this host.

**Diff-binding S-check (§5.2).** On a real scratch commit: exact mutation → rc 0; plus one
extra line in `tools/convergent_review.py` → rc 1, `AssertionError` listing the three files.

---

```
[STATE: Phase 014 | FEATURE: 103 (paused before contract rev 2 = attempt 3/3) | STEP: PLAN-AMENDMENT PROPOSED | DEPS: 104 -> 103 VERIFIED]
recommendation: OPTION A1 — 103 AT4 removes BOTH isolation halves (sandbox unshare line -> 'exec'; adapter Landlock restrict-self -> 'pass') and its capable branch also requires '^AssertionError: 40 != 0'; 104 AT8 requires '\bAssertionError: 40 != 0\b'; 104 AT7 text unchanged; 103/104 descriptions + spec 103/104 bullets + provenance updated; spec 1.1.2 -> 1.1.3 (PATCH) with feature_list_014 spec_version in lockstep; NDEBT-046 logged (namespace half undiscriminated; execution test vacuous). Rejected: A2 (loses N2 on the restricted branch), A3 (fragile $-escaping), B (test-body scope; not 103; unobservable here), C (vacuous capable pass).
proven: amended AT4 red at base (restricted), green under the positive control on both branches, red for N1/N3/N6 (capable) and N2 (restricted), rc 3 for N4/N5; approved AT4 capable branch rc 1 under the positive control (unsatisfiable).
operator_decision_requested (verbatim): "Approve amendment A1 to the phase-014 acceptance tests (spec 1.1.3): 103 AT4 removes both isolation halves (namespaces and Landlock) and its capable branch requires 'AssertionError: 40 != 0'; 104 AT8 requires the same signature; the 103/104 descriptions and spec bullets are updated as proposed; NDEBT-046 is logged. Approved."
then: Orchestrator records operator_gate_decision -> Planner applies §3 in commit <A> -> Generator drafts contract 103 rev 2 (attempt 3/3) re-anchored to <A>, folding evaluator issues 2-4.
not modified: .agent/feature_list_014.json, .agent/product_spec_014.md, .agent/contracts/103.json, .agent/run_state.json, docs/planning/DEBT.md
```
