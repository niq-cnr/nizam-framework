---
id: nizam-migration-v1-0-0
title: "Migrating from Nizam v0.9.0 to v1.0.0"
description: "Clean-break consumer migration guide for the schema invariants tightened in Nizam v1.0.0."
version: 1.1.0
status: active
authoritative_source: docs/migration-v1.0.0.md
last_audited: "2026-08-15"
tags: [migration, v1, breaking-change, consumer]
change_log:
  - version: "1.1.0"
    date: "2026-08-15"
    summary: "Release-preparation refresh: distinguish disposable pre-release rehearsal from production adoption of the released immutable v1.0.0 tag, which remains subject to H-CONSUMER-UPGRADE."
  - version: "1.0.0"
    date: "2026-08-15"
    summary: "Initial clean-break guide covering every v0.9.0 artifact shape rejected by the v1.0.0 schema invariants."
---

# Migrating from v0.9.0 to v1.0.0

Nizam v1.0.0 is a clean break. It deliberately rejects contradictory or
under-specified artifacts that v0.9.0 accepted. There is no compatibility mode
or dual-validation window.

Do not hand-edit the injected `.nizam/` payload. Update the consumer's pinned
tag to `v1.0.0`, re-run `bootstrap.sh`, then repair the consumer-owned artifacts
reported by validation. A pre-release candidate may be used only in a disposable
rehearsal. Production adoption requires the released immutable `v1.0.0` tag and
the consumer's recorded `H-CONSUMER-UPGRADE` decision.

## Evidence paths must identify an artifact

Both engineering findings and audit deltas now require content below the
evidence directory.

```json
{"path": ".agent/evidence/", "revision": "abc123"}
```

becomes, for example:

```json
{"path": ".agent/evidence/audit-17/check-01.txt", "revision": "abc123"}
```

## Membership schema versions use SemVer 2.0.0

Values such as `1.2.3.`, `1.2.3+`, and `1.2.3.foo` are invalid. Use canonical
SemVer such as `1.2.3` or `1.2.3-rc.1+build.7`. Numeric identifiers cannot have
leading zeroes, and prerelease/build identifier lists cannot be empty.

## Successful preflight verdicts omit blocking findings

A `PASS` or `PASS_WITH_EXCEPTIONS` artifact must not contain
`blocking_findings`, even as an empty array:

```json
{"verdict": "PASS", "blocking_findings": []}
```

becomes:

```json
{"verdict": "PASS"}
```

If a blocking condition exists, use `FAIL` and provide at least one item:

```json
{"verdict": "FAIL", "blocking_findings": ["working tree is dirty"]}
```

## A consistent membership result names its common pin

`framework_pin_consistent: true` now requires a non-empty string
`framework_pin`:

```json
{"ecosystem_verdict": "PASS", "framework_pin_consistent": true, "framework_pin": "35ed361d606aec83513cd307df6ce76bd7250422"}
```

Regenerate membership results with `tools/ecosystem_membership_run.py` rather
than inventing a pin. A missing or null pin means consistency has not been
demonstrated and cannot be represented as `true`.

## A failed reconciliation plan records the cycle and no order

The v1 failure shape is explicit:

```json
{
  "plan_verdict": "FAIL",
  "order": [],
  "cycle_findings": ["packet-a -> packet-b -> packet-a"]
}
```

A `FAIL` document with a missing/empty `cycle_findings` array or a populated
`order` is invalid. Re-run `tools/ecosystem_reconcile.py` from the source
membership result and packet input so it emits the failure record.

## Verification sequence

After re-bootstrap and consumer-owned artifact repair, run:

```bash
bash .nizam/tools/validate.sh --payload
bash .nizam/bootstrap.sh --verify-only --target .nizam
```

If the consumer vendors additional v0.9.0-generated artifacts, validate each
against the corresponding schema before declaring the migration complete.
