---
id: nizam-evidence-lifecycle-cleanup
title: "Evidence Retention, Distribution and Maintainability Cleanup"
description: "Bounded forward migration that moves completed historical evidence into Git-object archive form, makes installation proportional to the payload, and records the resulting current-vs-historical acceptance lifecycle."
version: 1.0.0
status: active
authoritative_source: docs/planning/cleanup/EVIDENCE_LIFECYCLE.md
change_log:
  - version: "1.0.0"
    date: "2026-10-22"
    summary: "Initial cleanup plan and change record for the operator-submitted 2026-10-22 mandate: baseline reconciliation, maintained fixtures, bounded preservation, Git-object archive + resolver, completed-tranche removal, filtered/sparse installer, compatibility vectors, documentation, budgets and rollback."
---

# Evidence retention, distribution and maintainability cleanup

## 1. Authority and boundary

The operator submitted this bounded cleanup as the authority for the work.
This is a direct repository-maintenance instruction, not a repeat of the
`H-CONSOLIDATION` ecosystem Repeat-stage decision; that recurring gate remains
`OUTSTANDING` in `docs/planning/operator_gates.md` and is not claimed here.

In scope: evidence retention and capture, fixture/configuration ownership,
historical archive resolution, evidence removal, installer retrieval, bounded
compatibility work and documentation. Out of scope and **not** performed:
merging PRs, publishing releases, creating or moving tags, deploying, upgrading
external consumers, or changing the installed self-governance `.nizam/` payload
(which remains at v1.10.1, `2b6a4af4d1667aad89cfaab4b1799cb8c9beb9fd`).

## 2. Baseline (audit reference)

Measured from the clean Git tree at `c5297f6ad2ef726ee85ca0b86e3df25fdcd0060a`
with `git ls-tree -rl HEAD` (logical tracked bytes):

| Category | Files | Bytes |
| --- | ---: | ---: |
| `.agent/evidence/` | 15,997 | 432,859,072 |
| Other `.agent/` records | 604 | 8,255,540 |
| Installed `.nizam/` | 279 | 2,460,048 |
| Authored framework, docs, tests, schemas, CI | 335 | 3,842,381 |
| **Total** | **17,215** | **447,417,041** |

Evidence was 96.75% of tracked bytes. The published v1.10.1 payload is 278
released files / 2,459,822 bytes (plus `provenance.json`). The old bootstrap
fetched a full shallow tree and `cp -R`'d the whole clone into `--git-repo`,
so a 2.46 MB payload materialized the whole development tree.

## 3. Work map

| Task | Delivered | Acceptance |
| --- | --- | --- |
| T0 | Baseline, dependency map, task ownership, this record | A01 |
| T1 | Fixtures/control policies promoted to `tools/fixtures/workflow_assurance/`; CI selector location moved; historical originals immutable in Git | A02 |
| T2 | `tools/evidence_preservation.py` (content-addressed bounded inventories, distinct run receipts, atomic/link publication); `.nizam-ref/` ignore; CI growth guard | A03 |
| T3 | `schema/evidence_archive.schema.json`, `.agent/evidence-archive/index.json`, `tools/evidence_archive.py`, C16 historical resolution | A04–A07 |
| T4 | 98 completed tranches / 14,828 files / 420,194,201 bytes moved out of HEAD; fresh-clone + GC restore proof | A04–A08, A12 |
| T5 | Blob-filtered (`blob:none`) fetch + precise sparse checkout + verified sparse reference retention + rollback pair | A09–A11 |
| T6 | Fixed canonical-format compatibility vectors for all three byte formats; full `publish_captured_evidence` decomposition deferred (see §8) | A13 (partial) |
| T7 | README, methodology, tools docs, schema registration, CI wiring, metrics, this record | A14 |

## 4. Archive contract

- Index: `.agent/evidence-archive/index.json`; schema:
  `schema/evidence_archive.schema.json`; resolver:
  `tools/evidence_archive.py`.
- Repository identity: exact origin plus `archive_commit`/`archive_tree`
  (`c5297f6a…`), an ordinary ancestor of the cleaned mainline. No moving branch
  or tag is used as archive identity.
- Every entry binds `[canonical path, Git mode, raw-byte SHA-256]`; each digest
  binds `[Git blob oid, byte length]`. Identical content is stored once.
- Each tranche binds the completed feature id, the feature lists that marked it
  complete, and the original contract and QA record SHA-256 values.
- Resolution for C16 succeeds only when the requesting feature and the owning
  tranche are complete and their contract/QA digests still match. A changed,
  reopened or re-accepted feature requires current evidence. A missing current
  artifact never silently falls back to archive bytes.
- Verification is read-only and offline (`git cat-file --batch`); it does not
  mutate refs, fetch, execute restored code, or repair the worktree.
  `restore` requires a destination outside the active checkout, refuses
  non-matching existing bytes, and preserves executable modes.

## 5. Removal and recovery record

Pilot and final migration are the same verified forward change because the
tranches share one closed dependency class: completed numeric features with
contract + QA records and no live test/CI dependency after fixture promotion.

- Pre-removal commit: `c5297f6a` (archive tree retained by history).
- Removed: `.agent/evidence/<id>/` and `.agent/evidence/<id>-*` for 98 completed
  features; 14,828 files / 420,194,201 logical bytes.
- Retained: current/other `.agent/` state, contracts, QA, validators, authority
  records, non-tranche evidence (11,670,458 bytes), and installed `.nizam/`.
- Restore command:
  `PYTHONDONTWRITEBYTECODE=1 python3 tools/evidence_archive.py restore --tranche feature-114 --output /tmp/nizam-evidence-114`.
- Observed recovery: restored `feature-133` (1,333 files) and `feature-114`
  (2,002 files) byte-identically after a fresh clone and after
  `git reflog expire --all --expire=now && git gc --prune=now` in a disposable
  clone. A06 retention proof passed.
- Rollback: ordinary `git revert` of the removal commit restores the prior
  working-tree paths. No tag, ref, approval or force-push is involved.

## 6. Installer contract

- `bootstrap.sh` fetches only `refs/tags/<tag>` with `--depth 1
  --filter=blob:none`, then sparse-materializes the exact payload roots.
- It refuses a silently full acquisition (`assert_blob_filter_applied`) when no
  excluded object remains absent; filtered retrieval is a hard requirement.
- It verifies that every selected blob is locally present before staging
  (`rev-list --objects --missing=print`, no lazy fetch).
- `--git-repo` retains the sparse reference (selected working files + Git
  reference objects), staged and verified before replacement. A failed target
  or reference replacement restores the previous valid pair.
- `--verify-only` exports `GIT_NO_LAZY_FETCH=1`; a missing required local object
  fails explicitly. The standalone candidate bootstrap was tested against the
  real immutable v1.10.1 release and verified offline with its own historical
  verifier loaded from the verified reference commit.
- Local `file://` test transports opt in with `uploadpack.allowFilter=true`;
  transports that cannot filter fail closed.

## 7. Measured outcome

| Metric | Baseline | Candidate | Budget |
| --- | ---: | ---: | --- |
| Active tracked tree | 447,417,041 B / 17,215 files | ≈28.44 MiB / 2,406 files | ≤32 MiB / ≤2,500 files |
| Evidence in active tree | 432,859,072 B / 15,997 files | 11,670,458 B / 1,169 files | preservation-first |
| Candidate payload | 278 files / 2,459,822 B (v1.10.1) | ≈2.59 MiB / 294 files² | ≤400 files / ≤4 MiB |
| Retained reference working files (v1.10.1) | full tree ≈447 MB | 278 files / 2,459,822 B | exact payload, ≤4 MiB |
| Retained reference Git database (v1.10.1) | full clone storage | ≈3.5 MiB | ≤16 MiB |
| Local/fresh Git database | 62 MiB / 58 MiB after GC | unchanged (history retained) | report separately |
| New evidence blobs >1 MiB | — | 0 | fail unless bounded exception |
| Recursive repository copies in new evidence | — | 0 | 0 |
| Unexpected excluded dirs in reference checkout | — | 0 | 0 |

The authoritative machine-readable values are in
`docs/planning/cleanup/metrics.json` for the delivered commit. The budget target
is met with margin.

² Includes the new archive schema/tools/fixtures. The installed candidate stays
well under the 4 MiB / 400-file gate.

No network-transfer or timing savings are claimed because transfer was not
instrumented. Git already deduplicated identical blobs internally; the savings
above are checkout/materialization and reference-retention savings, not a claim
about pack-network bytes.

## 8. Deferred and retained work

- **T6 full decomposition is not done.** `tools/start_path.py`'s
  `publish_captured_evidence` remains one function. A safe extraction requires
  running the existing `test_start_path.py` suite, which is environment-bound
  (Landlock sandbox) and failed on this macOS host before and after the change;
  the remaining refactor is deferred rather than risk untested publication /
  receipt / mutation-adapter semantics. The fixed canonical-format vectors were
  added (`tools/test_canonical_formats.py`) so any future extraction fails on
  byte drift.
- **Feature 130 / phase 020** and all other active state are untouched.
  `H-CONSOLIDATION` remains OUTSTANDING; this mandate is recorded as the direct
  operator request, not as a completed Repeat-stage gate.
- Evidence that is not owned by a completed numeric feature tranche (release
  close-outs, phase preparation, audit/handover records) stays in the active
  tree for this pass. It is historical but was not classified as an eligible
  tranche in the pilot, so it is retained rather than silently discarded.
- Release, tag, merge, distribution and external-consumer upgrade remain
  separate operator actions.

## 9. PR order and rollback

Recommended review order on top of `c5297f6a`:

1. `cleanup/evidence-archive-2026-10-22` — archive schema/tool, fixture
   promotion, C16 resolution, and completed-tranche removal (this record).
2. `cleanup/bootstrap-sparse-2026-10-22` — filtered/sparse installer and e2e
   transport configuration (depends on 1 only for the new payload inventory).
3. `cleanup/preservation-docs-2026-10-22` — bounded preservation producer,
   canonical-format vectors, CI guards and documentation (depends on 1).

The branches are not independently mergeable in arbitrary order; 2 and 3 are
based on 1. If a later change regresses, revert the specific forward commit.
Never reset or force-push the shared branch.
