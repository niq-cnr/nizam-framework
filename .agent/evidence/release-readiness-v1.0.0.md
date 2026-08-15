# Release Readiness — v1.0.0

Gate: `H-FRAMEWORK-RELEASE` (operator-only). Prepared 2026-08-15 from release-
preparation base `5d0e688` on `phase/012-v1-consumer-safety`. Target tier: MAJOR,
because v1 tightens contracts that v0.9.0 accepted. The pipeline has not created,
pushed, or approved `v1.0.0`.

## Automated readiness

1. Framework validator: **15/15 PASS** (`.agent/evidence/090/validator.txt`).
2. Fixture and CLI self-test: **77/77 PASS** (`.agent/evidence/090/selftest.txt`).
3. Hermetic bootstrap/genesis/n-case/coordination e2e: **PASS**
   (`.agent/evidence/090/e2e.txt`).
4. Seven Python tools compile and five shipped shell files pass syntax:
   **PASS** (`.agent/evidence/090/syntax.txt`).
5. Actual v0.9.0 payload → local v1 contract-candidate re-bootstrap: **PASS**;
   consumer root/CI files preserved; payload validator 11/11; all 11 legacy
   artifacts v0.9-valid → v1-invalid → v1-valid after guide repair
   (`.agent/evidence/090/migration-rehearsal.txt`).
6. Release metadata verification: **PASS** (`.agent/evidence/091/release-prep.txt`).

## Issue #52 finding-to-evidence map

Every row in `.agent/evidence/085/issue-matrix.json` is mapped below. Status
`READY` means remediated and validated on this branch; publication still depends
on the release gate.

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
- `NDEBT-036` remains Open until the immutable release exists; ROADMAP still names
  v0.9.0 as the latest released tag and v1.0.0 as release-in-preparation.
- Local automated checks report no unresolved blocking finding. PR review/check
  state is recorded below after publication of the draft PR.

## External review and human gate

- Draft PR: **PENDING** at initial preparation; update after push.
- Unresolved blocking automated-review findings: **0 known** at initial preparation;
  recheck the draft PR before sign-off.
- Human release-readiness sign-off: **PENDING — `H-FRAMEWORK-RELEASE`**.
- Immutable annotated tag `v1.0.0`: **PENDING — operator action**.
- GitHub Release publication: **PENDING — `release.yml` after tag push**.

The release is prepared, not released. Do not close NDEBT-036, advertise v1.0.0
as the latest released tag, or run bulk consumer upgrades until the two operator
actions—sign-off and annotated tag publication—are recorded.
