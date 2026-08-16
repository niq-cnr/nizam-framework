# Release Readiness — v1.0.0

Gate: `H-FRAMEWORK-RELEASE` (operator-only). Prepared 2026-08-15 from release-
preparation base `5d0e688` on `phase/012-v1-consumer-safety`. Target tier: MAJOR,
because v1 tightens contracts that v0.9.0 accepted. At preparation time the pipeline
had not created, pushed, or approved `v1.0.0`; the operator subsequently executed
the gate and published the release as recorded below.

## Automated readiness

1. Framework validator: **15/15 PASS** (`.agent/evidence/091/final-validator.txt`).
2. Fixture and CLI self-test: **77/77 PASS** (`.agent/evidence/091/final-selftest.txt`).
3. Hermetic bootstrap/genesis/n-case/coordination e2e: **PASS**
   (`.agent/evidence/091/final-e2e.txt`).
4. Seven Python tools compile and five shipped shell files pass syntax:
   **PASS** (`.agent/evidence/091/final-syntax.txt`).
5. Actual v0.9.0 payload → local v1 contract-candidate re-bootstrap: **PASS**;
   consumer root/CI files preserved; payload validator 11/11; all 11 legacy
   artifacts v0.9-valid → v1-invalid → v1-valid after guide repair
   (`.agent/evidence/091/final-migration.txt`).
6. Release metadata verification: **PASS** (`.agent/evidence/091/final-release-prep.txt`).

## Issue #52 finding-to-evidence map

Every row in `.agent/evidence/085/issue-matrix.json` is mapped below. Status
`READY` means remediated and validated on the release-preparation branch. The
complete mapped set is now published in `v1.0.0`.

| Finding | Status | Primary evidence |
|---|---|---|
| S01 | READY | `.agent/evidence/086/schema-green.txt` |
| S02 | READY | `.agent/evidence/086/schema-green.txt` |
| S03 | READY | `.agent/evidence/086/schema-green.txt` |
| S04 | READY | `.agent/evidence/086/schema-green.txt` |
| S05 | READY | `.agent/evidence/086/schema-green.txt` |
| S06 | READY | `.agent/evidence/086/schema-green.txt` |
| T01 | READY | `.agent/evidence/087/tool-green.txt` |
| R01 | READY | `.agent/evidence/088/static.txt` |
| R02 | READY | `.agent/evidence/088/static.txt` |
| R03 | READY | `.agent/evidence/088/static.txt` |
| M01 | READY | `.agent/evidence/088/static.txt` |
| M02 | READY | `.agent/evidence/088/static.txt` |
| M03 | READY | `.agent/evidence/088/static.txt` |
| M04 | READY | `.agent/evidence/088/static.txt` |
| M05 | READY | `.agent/evidence/088/static.txt` |
| M06 | READY | `.agent/evidence/088/static.txt` |
| M07 | READY | `.agent/evidence/088/static.txt` |
| M08 | READY | `.agent/evidence/088/static.txt` |
| M09 | READY | `.agent/evidence/088/static.txt` |
| E01 | READY | `.agent/evidence/089/static.txt` |
| E02 | READY | `.agent/evidence/089/static.txt` |
| E03 | READY | `.agent/evidence/089/static.txt` |
| E04 | READY | `.agent/evidence/089/static.txt` |
| E05 | READY | `.agent/evidence/089/static.txt` |
| E06 | READY | `.agent/evidence/089/static.txt` |
| C01 | READY | `.agent/evidence/089/static.txt` |
| C02 | READY | `.agent/evidence/089/static.txt` |
| C03 | READY | `.agent/evidence/089/static.txt` |
| D01 | READY | `.agent/evidence/089/static.txt` |
| D02 | READY | `.agent/evidence/087/tool-green.txt` |

The integration-level migration proof for S01–S06 is additionally captured in
`.agent/evidence/090/migration-rehearsal.txt`; it proves each of the 11 concrete
legacy fixtures crosses the v0.9-accepted → v1-rejected boundary and validates
after the documented repair.

## Release surfaces

- `NIZAM.json`, `CONTEXT.md`, and both HTML guide anchors identify `1.0.0`.
- README quickstart and release link pin `v1.0.0`; the migration guide is linked.
- CHANGELOG has a fresh empty `[Unreleased]` followed by dated `[1.0.0] -
  2026-08-15`, classified MAJOR with the clean-break migration link.
- `docs/migration-v1.0.0.md` covers every newly rejected v0.9.0 shape and requires
  released-tag production adoption through `H-CONSUMER-UPGRADE`.
- The immutable `v1.0.0` release now exists; this post-release refresh resolves
  `NDEBT-036` and records v1.0.0 as the latest released tag.
- Local automated checks report no unresolved blocking finding. Final PR review,
  merge, tag, and publication state is recorded below.

## External review and human gate

- Release-preparation PR: **MERGED** 2026-08-15 at `9453b3c` —
  [#53](https://github.com/niq-cnr/nizam-framework/pull/53).
- GitHub Actions at final PR head `ddfa1bc`: **validate SUCCESS,
  fixtures_self_test SUCCESS, e2e_bootstrap SUCCESS**.
- Unresolved blocking automated-review findings: **0** at the final
  2026-08-15T19:21:14Z recheck; GitHub reported empty latest-reviews and comments
  collections, and all three PR checks passed.
- Human release-readiness sign-off: **DONE 2026-08-15 — `H-FRAMEWORK-RELEASE`**;
  the operator applied the release tag and confirmed "tags applied."
- Immutable annotated tag `v1.0.0`: **DONE 2026-08-15** — operator-pushed at
  reviewed merge commit `9453b3c`.
- GitHub Release publication: **DONE 2026-08-15** — `release.yml` run
  [31903527120](https://github.com/niq-cnr/nizam-framework/actions/runs/31903527120)
  succeeded and published
  [v1.0.0](https://github.com/niq-cnr/nizam-framework/releases/tag/v1.0.0)
  from the `[1.0.0]` CHANGELOG section.

The release is published. `NDEBT-036` moves to Resolved in the accompanying
post-release ledger refresh, and v1.0.0 is the latest released tag. Consumer
adoption remains a separate, per-consumer `H-CONSUMER-UPGRADE` decision.
