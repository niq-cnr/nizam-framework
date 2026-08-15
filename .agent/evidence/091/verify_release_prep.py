#!/usr/bin/env python3
"""Verify the prepare-only v1.0.0 release package and issue mapping."""

import json
import subprocess
from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def require(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS {label}")


nizam = json.loads(read("NIZAM.json"))
require("framework version is 1.0.0", nizam["framework"]["version"] == "1.0.0")

context = read("CONTEXT.md")
require(
    "CONTEXT release anchor is 1.0.0",
    "version: 1.0.0" in context and '- version: "1.0.0"' in context,
)

guide = read("docs/guide/index.html")
require(
    "guide anchors are 1.0.0",
    '<meta name="framework-version" content="1.0.0">' in guide
    and '<span id="footer-version">1.0.0</span>' in guide,
)
require("guide license statement matches LICENSE", "Nizam ships under the MIT License" in guide)

readme = read("README.md")
for required in (
    "nizam-framework/v1.0.0/bootstrap.sh",
    "GOVERNANCE_TAG=v1.0.0",
    "--tag v1.0.0",
    "releases/tag/v1.0.0",
    "docs/migration-v1.0.0.md",
    "| `ecosystem/` |",
):
    require(f"README contains {required}", required in readme)

changelog = read("CHANGELOG.md")
unreleased_at = changelog.index("## [Unreleased]")
release_at = changelog.index("## [1.0.0] - 2026-08-15")
prior_at = changelog.index("## [0.9.0] - 2026-07-22")
require("CHANGELOG release order", unreleased_at < release_at < prior_at)
require(
    "CHANGELOG classifies clean break",
    "**Major release**" in changelog[release_at:prior_at]
    and "docs/migration-v1.0.0.md" in changelog[release_at:prior_at],
)

migration = read("docs/migration-v1.0.0.md")
require(
    "migration guide is release-ready",
    "version: 1.1.0" in migration
    and "released immutable `v1.0.0` tag" in migration
    and "`H-CONSUMER-UPGRADE`" in migration,
)

roadmap = read("docs/planning/ROADMAP.md")
require(
    "roadmap separates prepared and released tags",
    "Release in preparation: v1.0.0 (MAJOR)" in roadmap
    and "Latest released tag: v0.9.0" in roadmap,
)
debt = read("docs/planning/DEBT.md")
require(
    "NDEBT-036 remains release-gated",
    "NDEBT-036" in debt
    and "Awaiting `H-FRAMEWORK-RELEASE` sign-off" in debt
    and "Close only after the release exists" in debt,
)
gates = read("docs/planning/operator_gates.md")
require(
    "release gate remains outstanding",
    "v1.0.0 PREPARED / OUTSTANDING" in gates
    and "no sign-off or tag is recorded" in gates,
)

matrix = json.loads(read(".agent/evidence/085/issue-matrix.json"))
finding_ids = [finding["id"] for finding in matrix["findings"]]
require("issue matrix has 30 unique findings", len(finding_ids) == 30 and len(set(finding_ids)) == 30)
readiness = read(".agent/evidence/release-readiness-v1.0.0.md")
for finding_id in finding_ids:
    require(f"readiness maps {finding_id}", f"| {finding_id} | READY |" in readiness)

feature_list = json.loads(read(".agent/feature_list_012.json"))
require(
    "all phase-012 features implementation-complete",
    all(feature["status"] == "complete" for feature in feature_list["features"]),
)

tag_probe = subprocess.run(
    ["git", "rev-parse", "-q", "--verify", "refs/tags/v1.0.0"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    check=False,
)
require("real repository has no v1.0.0 tag", tag_probe.returncode != 0)
