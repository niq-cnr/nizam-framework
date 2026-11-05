# NIZAMREL-1105 — release-criteria evidence for the next framework tag

Exact head assessed: `1a331c1a1fb179e786d2c4fb806a62a441a4ce80` (= `origin/main`, = `v3.1.3` + 34 commits).
No tag exists at this head. The latest tag is `v3.1.3` (`f19357479220b6bf2b3292d31c06c66279f91efa`).

## 1. Decision: the next cut is v3.2.0 (MINOR), not v3.1.4 (PATCH)

Under `methodology/06_release_train.md` §3.4 (round up when in doubt), the change set is
not a patch:

- §3.2 MINOR covers "a schema change that only loosens constraints". `review_ledger`
  and `review_replay` change trial cardinality (1, 2 or 3 trials; previously exactly 3),
  which is a loosening, so it is MINOR at minimum.
- §3.1 MAJOR is triggered where a consumer could fail on upgrade. This needs a
  reviewed decision, see §3 below. It is recorded here as **not decided**, not as a
  silent MINOR.
- The new `external_qa_context.schema.json` adds required keys (new file, so not a
  narrowing of an existing schema; MINOR).
- `tools/external_evidence.py admit` now requires `--expected-candidate-sha256`
  (introduced by #150; the flag was absent at v3.1.3, so this is a new required input,
  not a narrowed optional one). Existing `admit` callers without it now fail. §3.1 names removal/rename of
  shipped protocol surface; a newly required CLI flag is the same class of narrowing
  as the prior v3.2.0 tier note, so **MAJOR is plausible and unresolved**.

A PATCH is ruled out: the set adds protocol capability (class-dependent trials,
external QA binding, task-failure reservation, state-boundary refusal) and schema
surface, and cannot be a typo/wording correction under §3.3.

Therefore the semantically correct cut is to **complete v3.2.0** (already prepared by
PR #159), not v3.1.4. A `v3.1.4` tag would mislabel MINOR/MAJOR content as a patch,
which §3.4 forbids. This PR does not bump `NIZAM.json` (it stays at 3.2.0), so the
close-out gate will not demand self-install evidence in this PR.

## 2. Classification of the 34 commits `v3.1.3..1a331c1a`

Merge commits (6) are listed with their PR; non-merge commits (28) are classified
individually. Tier is per §3; `—` means no shipped-contract effect.

| Commit | Subject | Tier | Basis |
|---|---|---|---|
| 8865b30f | external evidence admission authenticated/recovered (#150) | MINOR (CLI input now required → see MAJOR note) | `external_evidence.py` `--expected-candidate-sha256` required; new schema keys |
| eb31e716 | durably serialize receipt state publication (#151) | MINOR | new durable-publication behaviour; no schema change |
| 804cd1bf | bind optional external observations to native QA authority (#152) | MINOR | new `external_qa_context.schema.json` (new file) |
| 452ad19c | reserve task failure capacity before dispatch (#153) | MINOR | new reservation behaviour; no shipped-schema narrowing |
| 1dfa47f2 | refuse unsafe external state namespace (#154) | PATCH-like fix, but adds refusal surface → MINOR | `external-state-boundary.md` added |
| 118c73a2 | record NIP-0005 high-risk classification (lane log) | — | `.agent/` only |
| dd5d9bda | NIP-0005 durable product spec | — | `.agent/` only |
| b16d0b77 | NIP-0005 pending contract, approvals false | — | `.agent/` only |
| ba91eb08 | NIP-0005 body chunk 1 | — | `docs/nips/` (not shipped payload) |
| 3ac5d8dc | NIP-0005 log chunk 1 | — | `.agent/` only |
| e6a60bdc | NIP-0005 body chunk 2 | — | `docs/nips/` |
| 9393b755 | NIP-0005 log chunk 2 | — | `.agent/` only |
| ef7c715d | NIP-0005 body chunk 3 | — | `docs/nips/` |
| 6696bc87 | NIP-0005 log chunk 3 | — | `.agent/` only |
| 51542e68 | NIP-0005 log chunk 3 complete | — | `.agent/` only |
| 89f65ce9 | NIP-0005 AT1-AT5 checker + evidence | — | `.agent/evidence/nip0005/` |
| 51bab7b8 | NIP-0005 status vocabulary fix | — | `docs/nips/`, `.agent/` |
| e42d8efa | validate `--payload` judges Git index (regression) | PATCH | `tools/validate.sh` fix, `.nizam/tools` mirror |
| ab621661 | judge Git index in `--payload`, not installation | PATCH | `tools/validate.sh` fix |
| 04121fd0 | `--payload` falls back to worktree | PATCH | `tools/validate.sh` fix |
| c3f3baaa | prepare v3.2.0 MINOR (release prep, merged #159) | — | release-prep anchors; not a payload change |
| ca1fd736 | self-adopt published v3.1.3 payload | — | `.nizam/` runtime install (not authored payload) |
| 68ce00c1 | record v3.1.3 self-adoption in gate registry | — | `.agent/run_state.json`, `operator_gates.md` |
| 1bd40915 | repin verifier + agent instructions to v3.1.3 | — | `verify_self_governance.py`, `AGENTS.md` |
| dc06711f | README records v3.1.3 local installation | — | `README.md` |
| ce73d2e9 | suppress CodeQL py/overly-permissive-file (#161) | PATCH | `tools/evidence_archive.py` annotation only; permissions unchanged |
| 2ce3d571 | amend normative standard to simplification list (#162) | MINOR | `definition_of_done` compressed; `ci_gates` tiered; `GIP`/`provenance` changed |
| 1a331c1a | class-dependent trials 3b, ceiling-ten 4 (#163) | MINOR (trial cardinality loosened; new schema keys) | `review_ledger`/`review_replay` schema; `convergent_code_review` 1.4.0→class-dependent |

Count check: 34 = 28 non-merge + 6 merge. Merges #155, #157, #158, #159, #160, #162
are recorded as merges of the rows above; #161 is the squash of ce73d2e9.
No commit is silently skipped.

## 3. Unresolved tier question (operator decision required)

Whether the tier is MINOR or MAJOR depends on `external_evidence.py admit`'s newly required
`--expected-candidate-sha256` and the `definition_of_done` restructure. Under §3.4 the
conservative reading is **MAJOR**. This evidence pack does not decide it. The existing
v3.2.0 CHANGELOG entry already records this as an operator decision.

## 4. Release criteria at HEAD (evidence in this directory)

| Criterion | Result | File |
|---|---|---|
| `tools/validate.sh` 16/16 | PASS | validate-sh.txt |
| `release_closeout.py --mode pr` (anchors at V=3.2.0) | PASS | closeout-pr.txt |
| `release_closeout.py --mode tag --tag v3.1.3` | PASS (era-safe; self-install historical) | closeout-tag-v3.1.3.txt |
| `release_closeout.py --mode pr --base-commit <HEAD>` | PASS (no version bump vs base) | closeout-pr-base-head.txt |
| `--base-commit v3.1.3` | FAIL: a tag name is not a 40-hex SHA; this is operator misuse, not a gate defect | closeout-pr-base-tagname-misuse.txt |
| `verify_self_governance.py` (installed = v3.1.3) | PASS, 341 files | verify-self-governance.txt |
| fixtures self-test | PASS | fixtures-self-test.txt |
| CI on main at HEAD (compliance workflow) | success (run 41995598380) | gh run list |

Payload identity at HEAD (`tools/payload_integrity.py` selector: standard, templates,
schema, tools, methodology, ecosystem, NIZAM.json; SHA-256 of `git ls-tree -r -z`):
`2518b084a87ce4d22be3cbd508813bf4381fd13d1b12b2b1a9abf2ca6dd36636` (350 entries).

## 5. Prepublication self-install (methodology §6.1) — NOT MET for any next tag

- `.agent/evidence/release-v3.2.0/` does not exist. No `readiness.json` and no accepted
  `prepublication_self_install` record exists for v3.2.0 or any v3.1.4 candidate.
- The existing `release-v3.1.3-self-install/` proof binds candidate `2162b8e9…`, not HEAD
  `1a331c1a`. The authored payload has changed since then (39 authored files differ
  v3.1.3..HEAD), so that proof is invalid for this head (§6.1: "changing that payload
  invalidates the proof").
- The installed `.nizam/` is still v3.1.3 (`verify_self_governance` PASS), so no self-install
  against HEAD has been performed.
- **Blocker**: a new `H-CONSUMER-UPGRADE` owner approval plus a real safe-host
  self-install of the exact candidate payload is required before the human tag decision.
  This lane does not perform, fabricate or approve either step.

## 6. Client-unblocking commits (tag-contained)

Any tag at or after `1a331c1a` contains `ce73d2e9`, which is the CodeQL fix that
unblocks the consumer Aegis Analyze(python) red. Verified with `git merge-base --is-ancestor`.
It is contained in **no tag today**.

## 7. Named residuals NOT ready

1. MAJOR-vs-MINOR tier (operator decision, §3).
2. Prepublication self-install at HEAD (§5); requires owner approval and a safe-host run.
3. NIP-0005 is `draft` and must not be shipped as active.
4. `tools/external_evidence.py` required-flag change needs consumer migration notes (CHANGELOG already names this).
5. `--payload` checks run against an exported temp index, not in place (CHANGELOG limitation).
