# Independent evaluation — release criteria at origin/main 5ecc7e39 (PR #164)

Lane tag: NIZAMREL-EVAL-1105
Subject: PR #164 `chore/release-criteria-v314` (squash-merged at `5ecc7e39`, 2026-11-05T12:04:12Z)
Assessed head: `5ecc7e39fcc1eb107cab637008dfe69e1a2e7ca5` (= origin/main at assessment)
Latest tag: `v3.1.3` = `f19357479220b6bf2b3292d31c06c66279f91efa`
Evaluator: independent, single run, read-only outside this record file. No code, CI, tag, changelog or merge action was taken.

## VERDICT: NOT-QUALIFIED

No tag should be cut from this head on the present evidence. The PR's own residual list is accurate as far as it goes, but the PR text and the merged record contain claims the evidence does not support, and at least one release-train gate (§6.1) is unmet. Items marked PASS below are confirmed; they do not alter the verdict.

## Per-item findings

### 1. PR #164 diff at merge state (stale text and prior_ledger references)

- Command: `gh pr view 164 --json state,mergeCommit,mergedAt,body` → `MERGED`, merge `5ecc7e39`, `2026-11-05T12:04:12Z`.
- Command: `git diff --stat 1a331c1a 5ecc7e39` → 21 files, 633 insertions, 1 deletion. Only `.agent/`, `CHANGELOG.md` and the new record README changed. No tool, schema, standard or `.nizam/` file changed.
- Stale v1.4.0 trial-count text: the only remaining "exactly three" in the CHANGELOG is on the `standard/convergent_code_review.md (v1.4.0, historical; ...)` line, and it is explicitly marked historical and superseded. **PASS for the CHANGELOG line.** Broader search (`grep -rn "exactly three\|three independent"` over `standard templates schema docs ecosystem`) found current-tense text still describing three trials in `templates/convergent-review-prompt.md` (line 22, "exactly three independent observation extractors"), `templates/README.md` (line 40), `schema/review_trial.schema.json` (line 5), `schema/README.md` (lines 144, 147), and `standard/convergent_code_review.md` line 87 (which correctly describes the governance default of three). The schema and template rows contradict the class-dependent 1.5.0 rule (docs-config=1, code=2, governance=3). **FINDING (warning, not in the PR's own list): the trial-count text is stale outside the CHANGELOG line that PR #164 fixed.** The PR's claim of "no stale v1.4.0 trial-count text anywhere" is therefore only true for the CHANGELOG.
- `prior_ledger` references: the PR's `count-and-ancestry.txt` records `prior_ledger_at_v3.1.3=2`. Running `git ls-tree -r --name-only v3.1.3 | grep -i ledger` shows the ledger-named files at v3.1.3 are fixtures under `tools/fixtures/convergent_review/0{5,6,7,8}-*/prior-ledger.json` and `.nizam/` mirrors, plus unrelated `.agent/evidence/*/ledger.json` files. None is a "closed ledger" in the sense the PR's false claim implied. **PASS: the current text no longer makes the false claim; the remaining references are fixtures only.** The count `2` is not reproduced by any command in the PR's evidence and is not a closed-ledger count, so it is not treated as evidence.
- Version anchors: `tools/release_closeout.py` is not at this path. The gate is `.github/scripts/release_closeout.py`. `python3 .github/scripts/release_closeout.py --mode pr` → exit 0 (`all internal version anchors agree with V=3.2.0`). `--mode tag --tag v3.1.3` → exit 0. **PASS** on the gate.
- Note: root `NIZAM.json` reads `3.2.0` at this head (from `c3f3baaa`, "prepare v3.2.0 MINOR release"), and no tag exists for it. The PR asserts it "does not bump NIZAM.json"; that is accurate, but a 3.2.0 anchor already exists on main without a tag, and the PR's decision table still treats 3.2.0 as pending. This is a state inconsistency worth operator attention, not a gate failure.

### 2. Release-train classification (sample of 34 commits)

Commit count re-derived: `git rev-list --count v3.1.3..1a331c1a` = 34 (28 non-merge, 6 merge). `git rev-list --count v3.1.3..5ecc7e39` = **35** (the extra commit is the squash merge `5ecc7e39` itself; the PR's "34" counts to base `1a331c1a`, so this is a counting-basis difference, not an error in the PR).

Sampled against `methodology/06_release_train.md` (read live, §3.1–§3.4):

| Commit | PR tier | Evaluator check (live diff) | Verdict |
|---|---|---|---|
| 8865b30f (#150) | MINOR, MAJOR-question | `tools/external_evidence.py` at v3.1.3 has `--expected-candidate-sha256` count 0; at head it is `required=True` (line 1145). §3.1 says a required-key/narrowing change is MAJOR. | **PR under-classifies.** The PR itself flags MAJOR as "plausible and unresolved"; under §3.4 the higher tier applies. Should be MAJOR. |
| 1a331c1a (#163) | MINOR | `schema/review_ledger.schema.json` `minItems` 3→1 and `review_replay` 4→2 (loosening, §3.2); but `tools/external_evidence.py` changed, and CONTEXT/CHANGELOG record a class-dependent trial rule. Loosening only: MINOR holds. | Holds. |
| 2ce3d571 (#162) | MINOR | `standard/definition_of_done.md` restructured; `ci_gates.md` changed from 10-gate formula to tiered bar; `GIP`/`provenance` consumer pin changed from exact tag+SHA to declared range (`provenance_policy` 0.4.0). A consumer that pins exact SHA loses an enforced check. | **PR under-classifies.** Removal of a required gate formula and a changed pinning rule is arguably §3.1-shaped; under §3.4 should round to MAJOR or at least be explicitly argued. Not argued in the PR. |
| ce73d2e9 (#161) | PATCH | `git show ce73d2e9 -- tools/evidence_archive.py` adds only a `# codeql[...]` comment line; test file gets two mode assertions. Permissions unchanged. | Holds (PATCH). |
| e42d8efa / ab621661 / 04121fd0 | PATCH | `tools/validate.sh` `--payload` fix and regression test. | Holds (PATCH), though the `.nizam/tools/validate.sh` mirror is unchanged, so the fix is not on the installed payload. |
| 452ad19c (#153) | MINOR | new reservation behaviour in `start_path.py`, no shipped-schema narrowing. | Holds (MINOR at minimum). |
| 1dfa47f2 (#154) | MINOR (refusal surface) | adds `docs/architecture/external-state-boundary.md`, new CI test line in `compliance.yml`. | Holds (MINOR). |
| 804cd1bf (#152) | MINOR | new `schema/external_qa_context.schema.json`. | Holds (MINOR). |
| eb31e716 (#151) | MINOR | durable receipt publication; no schema change. | Holds (MINOR), but arguably PATCH-like bug fix. Round-up rule supports MINOR. |
| c3f3baaa | "—" (release prep) | changes CHANGELOG, NIZAM.json (→3.2.0), README anchors. Not a payload change. | Holds. |

Sample coverage: 10 commits checked against live diffs (8865b30f, 1a331c1a, 2ce3d571, ce73d2e9, e42d8efa, 452ad19c, 1dfa47f2, 804cd1bf, eb31e716, c3f3baaa) plus 51bab7b8 (NIP-0005 status vocabulary, `docs/nips` only, no payload effect, holds).

**FINDING: two MINOR/MAJOR calls do not follow §3.4 "round up when in doubt"**: 8865b30f (the PR itself names MAJOR as plausible, yet the release decision table keeps MINOR open) and 2ce3d571 (a gate formula and a pinning rule changed without a MAJOR argument). The release tier is therefore not "decided between MINOR and MAJOR" as the PR says; under §3.4 it is at minimum MAJOR for 8865b30f.

### 3. Client-unblocking claim (ce73d2e9)

- `git merge-base --is-ancestor ce73d2e9 5ecc7e39` → ancestor = yes.
- `git merge-base --is-ancestor ce73d2e9 1a331c1a` → yes.
- `git merge-base --is-ancestor ce73d2e9 v3.1.3` → **not an ancestor** (not in v3.1.3).
- `git tag --contains ce73d2e9 | wc -l` → 0. No tag contains it.
- **PASS** on the ancestry claim. The "client-unblocking" wording is unverified: no client build or CodeQL run was available to this evaluator, so the statement that it unblocks the Aegis red is **not independently verified**.

### 4. Checks on main at 5ecc7e39 (EXECUTED-IN-CI vs CONFIGURED-BUT-DOES-NOT-EXECUTE vs DOCUMENTED-INTENT)

The adopted reporting doctrine named in the brief (the three labels) was not found in this repository or in the local skills directory (`grep -rln "EXECUTED-IN-CI\|CONFIGURED-BUT\|DOCUMENTED-INTENT"` over the repo and `~/.agents/skills` returned nothing). The labels below are applied as the brief defines them, and this is recorded as a limitation.

Command: `gh run list --commit 5ecc7e39fcc1eb107cab637008dfe69e1a2e7ca5` → one run, workflow `compliance`, run `42024036239`, `event=push`, status `completed`, conclusion `success`.
Command: `gh run view 42024036239 --json jobs` → five jobs, all `completed/success`:

| Job | Status | Label |
|---|---|---|
| fixtures_self_test | completed / success | EXECUTED-IN-CI |
| validate | completed / success | EXECUTED-IN-CI |
| self_governance | completed / success | EXECUTED-IN-CI |
| e2e_bootstrap | completed / success | EXECUTED-IN-CI |
| convergent_review | completed / success | EXECUTED-IN-CI |

Other workflows on this commit: `release_closeout`, `release`, `pages` produced **no runs** for `5ecc7e39` (`gh run list --workflow <name>.yml --commit 5ecc7e39` → `[]`). For this head these are NOT-TRIGGERED (no run record exists; their configured triggers produced nothing). They are not labelled EXECUTED-IN-CI, and absence of a run is not treated as a failure.

Two jobs in `compliance.yml` required by the release discussion were not individually inspected to completion: the logs for `fixtures_self_test` (sub-steps including `tools/test_workflow_assurance.py`) were run and succeeded; the remaining steps' individual conclusions were not enumerated beyond job level. Recorded as **partially verified**.

Local re-execution: `python3 .github/scripts/release_closeout.py --mode pr` and `--mode tag --tag v3.1.3` both exited 0 locally on this worktree at 5ecc7e39. This is local evidence only; it is not CI evidence.

Not executed by this evaluator: `tools/validate.sh` full suite, `fixtures_self_test.sh`, `verify_self_governance.py` (the PR's evidence records them; re-running them locally was not necessary to reach the verdict and was not done, so they are reported as **not independently re-executed**).

### 5. Named residuals in the PR decision table

| Residual (PR §"Named residuals") | Evaluator confirmation |
|---|---|
| 1. Prepublication self-install (§6.1) not met for any next tag | **CONFIRMED NOT-READY.** `ls .agent/evidence/release-v3.2.0` → does not exist. `ls .agent/evidence/release-v3.1.4` not checked (no such candidate named). The v3.1.3 proof (`release-v3.1.3-self-install/`) binds candidate `2162b8e9`, not 5ecc7e39. Gate-level: §6.1 requires a new owner-approved install. Not performed. |
| 2. MAJOR-vs-MINOR tier | **CONFIRMED OPEN, and under-stated.** §3.4 requires round-up; 8865b30f is at least arguably MAJOR and is currently left open. See §2. |
| 3. NIP-0005 is `draft` | **CONFIRMED.** `docs/nips/NIP-0005-executable-claim-binding.md` line 6: `status: draft`. Must not ship as active. |
| 4. `external_evidence.py admit` required-flag migration note | **CONFIRMED in CHANGELOG** (line "Existing `admit` callers without it now fail"). No separate consumer migration document exists (`ls docs/migration-v3.2*` → none). The CHANGELOG note is the only migration text. Treated as **partially addressed**. |
| 5. Independent acceptance not recorded (`.agent/qa/NIZAMREL-1105.json` absent) | **CONFIRMED.** `ls .agent/qa/NIZAMREL-1105.json` → No such file. `.agent/progress-notes.md` records that round 2 of the evaluator had no shell and that `start_path.py done` is NOT satisfied. This record is an independent evaluation by a fresh-context evaluator, but it does not create the QA file (no native QA authority was given to this lane), so acceptance remains **unrecorded**. |

No residual was silently dropped: all five appear in the PR and are confirmed as open. **However, two items were under-stated**: the tier question (2) is effectively MAJOR under §3.4 for 8865b30f, and the stale trial-count text (new finding in §1) is outside the PR's residual list entirely.

## Summary of findings

1. **§6.1 self-install not met** for any candidate. (Blocker; confirmed.)
2. **Tier under-classified** against §3.4 for 8865b30f (MAJOR) and 2ce3d571 (gate formula and pin rule changed, not argued). (Blocker for tag decision.)
3. **Current-tense "three trials" text persists** in `templates/convergent-review-prompt.md`, `templates/README.md`, `schema/review_trial.schema.json`, `schema/README.md`, contradicting class-dependent 1.5.0. (Warning; not in PR's list.)
4. **Independent acceptance not recorded** in `.agent/qa/`. (Blocker for completion of the PR's own lane.)
5. **Root `NIZAM.json` already reads 3.2.0** at head with no tag, while the decision table treats 3.2.0 as pending. (Warning; state inconsistency.)
6. **`ce73d2e9` ancestry verified**; "client-unblocking" effect **not verified** (no client CI/CodeQL run available). (Partially verified.)

## Items NOT verified (explicit list)

- The adopted reporting doctrine with the labels EXECUTED-IN-CI / CONFIGURED-BUT-DOES-NOT-EXECUTE / DOCUMENTED-INTENT: not found anywhere in repo or local skills. Labels applied per the brief's own definitions only.
- Full per-step conclusions for every step in `compliance.yml` jobs (only job-level conclusions were enumerated).
- `tools/validate.sh` full run, `fixtures_self_test.sh`, `verify_self_governance.py`: recorded by the PR; not re-executed here.
- The Aegis / consumer CodeQL red and whether ce73d2e9 clears it: no consumer CI access.
- Physical-model lineage or any LiteLLM routing claim: not applicable; no model call was made.
- Whether `.agent/evidence/release-v3.1.4` or any candidate readiness record exists under another name: only `release-v3.2.0` was checked.
- The count `prior_ledger_at_v3.1.3=2` in the PR's evidence: no reproducing command in the PR's record; not confirmed.
- The `.nizam/` mirror differences from the root authored payload: expected for an installed v3.1.3 copy that lags the root payload; not treated as a defect.
- Whether the 35-commit count (v3.1.3..5ecc7e39) vs 34 (v3.1.3..1a331c1a) reflects an intended scope boundary: the PR states the base as 1a331c1a; the evaluator treats 5ecc7e39 as the assessed head per the brief, and the one extra commit is the PR merge itself.

## Commands run (exact)

- `gh pr view 164 --repo niq-cnr/nizam-framework --json number,title,state,mergeCommit,mergedAt,baseRefName,headRefName,body`
- `git rev-list --count v3.1.3..1a331c1a` → 34; `git rev-list --no-merges`/`--merges` → 28 / 6
- `git merge-base --is-ancestor ce73d2e9 5ecc7e39` → yes; `... ce73d2e9 v3.1.3` → no; `git tag --contains ce73d2e9 | wc -l` → 0
- `gh run list --repo niq-cnr/nizam-framework --commit 5ecc7e39fcc1eb107cab637008dfe69e1a2e7ca5` → run 42024036239 success
- `gh run view 42024036239 --json jobs` → 5 jobs, all success
- `python3 .github/scripts/release_closeout.py --mode pr` → exit 0; `--mode tag --tag v3.1.3` → exit 0
- `git show ce73d2e9 -- tools/evidence_archive.py` (single added comment line)
- `grep -rn "exactly three\|three independent" templates schema standard docs` → current-tense stale hits listed above
- `cmp` of root vs `.nizam/` mirror files (differences expected, not a finding)
