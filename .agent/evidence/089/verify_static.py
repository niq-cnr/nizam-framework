#!/usr/bin/env python3
"""Replayable issue-52 documentation assertions for phase-012 feature 089."""

from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def body(path: str) -> str:
    return read(path).split("---", 2)[2]


def require(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS {label}")


bootstrap = body("ecosystem/00_ecosystem_bootstrap.md")
require(
    "E01 n-case names shipped iteration and coordination",
    "Phase 010 shipped membership iteration/aggregation" in bootstrap
    and "phase 011 shipped the `04_dependency_reconciliation.md`" in bootstrap
    and "`05_release_train_coordination.md` protocols and tools" in bootstrap,
)
require(
    "E01 stale deferred-stage claim removed",
    "genuine cross-repository coordination lives in the deferred" not in bootstrap
    and "The n-case is deferred to phase 010" not in bootstrap,
)
require(
    "E02 genesis command is scaffold automation",
    "scaffold automation, not a substitute for consumer authority" in bootstrap,
)
for obligation in (
    "make and record those decisions",
    "add the `incubating` registry entry",
    "clean Preflight and Baseline results",
):
    require(f"E02 genesis requires {obligation}", obligation in bootstrap)

preflight = body("ecosystem/01_clean_state_preflight.md")
require(
    "E03 only finalized preflight emits verdict",
    "Every finalized preflight run MUST emit" in preflight,
)
require(
    "E03 pending path remains explicit",
    "writes `preflight.pending.json`" in preflight
    and "withholds `preflight.json` entirely" in preflight,
)

reconciliation = body("ecosystem/04_dependency_reconciliation.md")
require(
    "E04 PASS requires packet repositories in aggregate scope",
    "every packet repository belongs\n  to the source aggregate's `in_scope` set"
    in reconciliation,
)

ecosystem_index = body("ecosystem/README.md")
require(
    "E05 Baseline requires revision and timestamp",
    "both a stated revision and timestamp" in ecosystem_index
    and "a stated revision or timestamp" not in ecosystem_index,
)
require(
    "E06 Compare names all five transitions",
    "new, resolved, reopened, persisting, and stale findings" in ecosystem_index,
)

capabilities = body("standard/capability_profiles.md")
require(
    "C01 C15 is a capability, not execution evidence",
    "When a checkout runs `tools/validate.sh`, check C15 verifies" in capabilities
    and "not evidence that a consumer executed it" in capabilities
    and "IS verified" not in capabilities,
)

provenance = body("standard/provenance_policy.md")
require(
    "C02 C14 is a capability, not execution evidence",
    "When a checkout runs `tools/validate.sh`, check C14 verifies" in provenance
    and "not evidence that a consumer executed it" in provenance
    and "IS verified" not in provenance,
)

gip = body("standard/GIP.md")
require(
    "C03 consumer owns root and CI reconciliation",
    "consumer's reconciliation process**, not `bootstrap.sh`" in gip
    and "preserve/diff/merge work and adds recommended CI checks" in gip,
)
require(
    "C03 bootstrap owns only injected payload",
    "`bootstrap.sh` writes only\nthe governance payload" in gip
    and "does\nnot mutate the consumer's root documents or CI configuration" in gip,
)

tools_index = body("tools/README.md")
families = (
    "ecosystem_baseline",
    "preflight_verdict",
    "engineering_finding",
    "audit_delta",
    "ecosystem_membership",
    "membership_result",
    "reconciliation_plan",
    "release_train_manifest",
)
for family in families:
    require(f"D01 C12 lists {family}", family in tools_index)
require(
    "D01 membership fixture-to-schema mapping is explicit",
    "`membership_result` fixtures target `ecosystem_membership_result.schema.json`"
    in tools_index,
)

compare = body("ecosystem/07_progress_comparison.md")
require(
    "T01 protocol matches resolved-to-open implementation",
    "present and resolved in the earlier input but present and open" in compare
    and "later open record's evidence is retained" in compare,
)
require(
    "T01 first comparison can classify reopened",
    "earlier input can itself contain a resolved finding" in compare
    and "it is `reopened`" in compare,
)
