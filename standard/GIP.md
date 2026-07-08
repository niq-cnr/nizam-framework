---
id: governance-inheritance-protocol
title: "Governance Inheritance Protocol (GIP)"
description: "The runtime-agnostic protocol by which a consumer repository inherits, verifies, and keeps in sync with the Nizam governance framework, via pinned-tag cloning and drift detection."
version: 0.1.0
status: active
authoritative_source: standard/GIP.md
---

# Governance Inheritance Protocol (GIP)

## 1. Core Directive

**A repository that does not inherit a pinned, verifiable copy of the framework's
governance content is not framework-compliant.**

Any repository that adopts the Nizam framework MUST inherit its governance content
(`standard/`, `templates/`, `schema/`) through a single, atomic, verifiable operation, not
through ad hoc copy-paste or hand-authored reproductions. This protocol defines that
operation, the compliance checks that follow it, and how a consumer repository detects
when its inherited copy has drifted from the framework it claims to follow.

## 2. Pinned-Tag Inheritance

Inheritance is triggered when a repository first adopts the framework, and re-triggered
whenever it upgrades to a newer framework release.

1. **Clone a pinned tag, never a floating branch.** The consumer MUST clone a specific
   semantic-version git tag of the framework repository (e.g. `v0.3.0`), never `main` or
   any other floating branch reference. Pinning prevents a consumer from silently
   inheriting mid-development governance changes.
2. **Inject the governance directories.** The consumer copies the framework's `standard/`,
   `templates/`, and `schema/` directories into its own workspace (conventionally at its
   repository root, or a dedicated governance directory it declares in its own
   `CONTEXT.md`).
3. **Load, don't just copy.** Any agent operating in the consumer repository MUST read the
   injected governance documents into its working context before acting, and is bound by
   their directives for the duration of its session.
4. **Record the pin.** The consumer records the inherited framework version (the pinned
   tag) in a machine-readable location (for example its own capability index or a
   `governance_version` field) so that later drift detection has a baseline to compare
   against.

### 2.1 Bootstrap Verification

Inheritance is not complete until it is verified. The framework ships `bootstrap.sh` at
its repository root as the canonical, reusable implementation of clone → inject → verify.
Any consumer MAY invoke it directly rather than reimplementing the steps in Section 2.

`bootstrap.sh` performs, as one atomic operation:

1. Clone the pinned tag (never a floating branch) of the framework repository.
2. Inject `standard/`, `templates/`, and `schema/` into the consumer's target location.
3. Verify the injection succeeded before declaring success.

The verification step confirms, at minimum:

- Every required governance file landed on disk (a minimum set including the four
  `standard/` documents and the `schema/frontmatter.schema.json` validation target).
- Any machine-readable index the framework ships (its root capability index) parses as
  valid JSON.
- Every `.md` file injected under `standard/` carries frontmatter with the six required
  keys defined in `NDS.md` Section 2.

If any required file is missing, any index fails to parse, or any injected document fails
frontmatter validation, `bootstrap.sh` MUST exit non-zero with a clear diagnostic naming
the specific missing or invalid artifact. A silent partial injection is a protocol
violation — the consumer repository MUST treat a non-zero exit as "inheritance did not
happen," not as "inheritance mostly happened."

## 3. Compliance Verification

After a successful bootstrap, and periodically thereafter, a consumer repository SHOULD
re-run the same verification checks described in Section 2.1 as a standalone compliance
check, independent of whether a new bootstrap was just run. At minimum this means:

1. The required governance files are present and non-empty.
2. Any root capability index (equivalent to the framework's own `NIZAM.json`) parses.
3. Frontmatter on every injected governance document is present and schema-valid.

A repository that fails compliance verification MUST NOT represent itself as
framework-compliant until the failure is remediated.

## 4. Drift Detection

Because injected governance content is a copy, not a live reference, it can diverge from
the pinned tag it was sourced from — through local hand-editing, partial re-injection, or
simple staleness as newer framework tags are released. Drift detection is the periodic
process of catching this divergence.

1. **Baseline.** The consumer's recorded pinned tag (Section 2, point 4) is the baseline
   for comparison.
2. **Re-verification cadence.** A consumer repository SHOULD re-verify its injected
   governance content against its recorded pinned tag on a regular cadence (for example,
   before each release, or on a scheduled interval), not only at initial bootstrap time.
3. **Detecting local mutation.** If an injected file under `standard/`, `templates/`, or
   `schema/` no longer matches the content shipped at the recorded pinned tag, the
   consumer has drifted through local mutation. Locally hand-patched governance files are
   themselves a drift signal, independent of whether the patch was well-intentioned.
4. **Detecting staleness.** If a newer semantic-version tag of the framework has been
   released since the consumer's recorded pin, the consumer is stale relative to the
   framework's current governance content, even if its own injected copy is internally
   unmodified.
5. **Remediation: re-bootstrap, don't hand-patch.** The correct remediation for both local
   mutation and staleness is to re-run `bootstrap.sh` against the appropriate pinned tag
   (the same tag, to undo local mutation, or a newer tag, to resolve staleness) and let
   the injection overwrite the drifted copy. Hand-patching individual injected files is
   prohibited — it reintroduces exactly the divergence drift detection exists to catch,
   and it defeats the auditability of "this repository runs framework version X" as a
   single, verifiable claim.

## 5. Enforcement

- Any process responsible for onboarding a new consumer repository to the framework MUST
  ensure Section 2's inheritance sequence (or an invocation of `bootstrap.sh`) is
  performed before the repository is treated as framework-compliant.
- A consumer's own CI SHOULD run the compliance checks in Section 3 on a regular cadence
  and fail loudly, rather than silently, on drift.
- No consumer repository may reference an inherited governance document as authoritative
  if that document's content differs from the pinned tag's shipped copy without having
  gone through the re-bootstrap remediation in Section 4, point 5.
