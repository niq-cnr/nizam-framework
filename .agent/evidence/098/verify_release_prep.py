#!/usr/bin/env python3
"""Verify the prepare-only v1.1.0 release package and phase-013 completeness.

Generalizes ``.agent/evidence/091/verify_release_prep.py`` at V=1.1.0:
stdlib-only, network-free, ``require(label, condition)`` style. Designed to
run in TWO PHASES across feature 098's own contracted implementation --
see ``verify_release_prep_098_status_design`` in ``.agent/contracts/098.json``
design_notes for the full rationale:

* PRE-Step-7 (during Loop 2 evidence capture, before the generator's
  durable-state procedure flips feature 098's own status): the six-sibling
  completeness check (092-097) is strict; feature 098's own status is read
  and printed as a non-failing acknowledgment line, not hard-required to
  equal any particular value.
* POST-Step-7 (after the flip): the same script, unmodified, runs cleanly
  again -- the acknowledgment line now legitimately observes 'complete'.

Never creates, deletes, or pushes any git ref; the only subprocess call is
the read-only ``git rev-parse -q --verify refs/tags/v1.1.0`` tag probe.
"""

import json
import subprocess
from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def require(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS {label}")


# --- C10 version anchors: NIZAM.json / CONTEXT.md / guide / README --------

nizam = json.loads(read("NIZAM.json"))
require("framework version is 1.1.0", nizam["framework"]["version"] == "1.1.0")

context = read("CONTEXT.md")
require(
    "CONTEXT release anchor is 1.1.0",
    "version: 1.1.0" in context and '- version: "1.1.0"' in context,
)

guide = read("docs/guide/index.html")
require(
    "guide anchors are 1.1.0",
    '<meta name="framework-version" content="1.1.0">' in guide
    and '<span id="footer-version">1.1.0</span>' in guide,
)
require("guide license statement matches LICENSE", "Nizam ships under the MIT License" in guide)

readme = read("README.md")
for required in (
    "nizam-framework/v1.1.0/bootstrap.sh",
    "GOVERNANCE_TAG=v1.1.0",
    "--tag v1.1.0",
    "releases/tag/v1.1.0",
    "[v1.1.0 release]",
    "docs/migration-v1.0.0.md",
    "| `ecosystem/` |",
):
    require(f"README contains {required}", required in readme)
require(
    "README migration guide stays pinned to v1.0.0 (no new v1.1.0 guide)",
    "docs/migration-v1.1.0.md" not in readme,
)

# --- CHANGELOG.md: Unreleased < [1.1.0] < [1.0.0], tier banner + citation -

changelog = read("CHANGELOG.md")
unreleased_at = changelog.index("## [Unreleased]")
release_at = changelog.index("## [1.1.0]")
prior_at = changelog.index("## [1.0.0]")
require("CHANGELOG release order", unreleased_at < release_at < prior_at)
release_section = changelog[release_at:prior_at]
require(
    "CHANGELOG classifies the MINOR tier with the release-train citation",
    "**Minor release**" in release_section
    and "methodology/06_release_train.md" in release_section
    and "Section 3.2" in release_section,
)
unreleased_body = changelog[unreleased_at:release_at]
require(
    "CHANGELOG Unreleased carries no bullet content",
    unreleased_body.count("\n- ") == 0,
)

# --- ROADMAP.md: both dispositions present in the document body ----------

roadmap = read("docs/planning/ROADMAP.md")
require(
    "roadmap names the prepared v1.1.0 disposition and retains the released v1.0.0 tag",
    "Release in preparation: v1.1.0" in roadmap
    and "Latest released tag: v1.0.0" in roadmap,
)

# --- DEBT.md: NDEBT-038 Resolved, NDEBT-040/037 stay Open -----------------

debt = read("docs/planning/DEBT.md")
open_start = debt.index("## Open")
resolved_start = debt.index("## Resolved")
open_section = debt[open_start:resolved_start]
resolved_section = debt[resolved_start:]
require("NDEBT-038 no longer Open", "NDEBT-038" not in open_section)
require("NDEBT-038 present in Resolved", "NDEBT-038" in resolved_section)
require(
    "NDEBT-040 and NDEBT-037 stay Open (out of this feature's scope)",
    "NDEBT-040" in open_section and "NDEBT-037" in open_section,
)

# --- operator_gates.md: v1.1.0 PREPARED/OUTSTANDING language --------------

gates = read("docs/planning/operator_gates.md")
require(
    "operator_gates H-FRAMEWORK-RELEASE row carries v1.1.0 PREPARED/OUTSTANDING language",
    "v1.1.0" in gates and "PREPARED" in gates and "OUTSTANDING" in gates,
)
require(
    "operator_gates states no sign-off or tag is recorded for v1.1.0",
    "no sign-off or tag is recorded for v1.1.0" in gates,
)

# --- Readiness record: per-feature READY rows + tier + disposition -------

readiness = read(".agent/evidence/release-readiness-v1.1.0.md")
for fid in ("092", "093", "094", "095", "096", "097", "098"):
    require(f"readiness names feature {fid}", f"| {fid} | READY |" in readiness)
require("readiness names the MINOR tier", "MINOR" in readiness)
require(
    "readiness states the H-FRAMEWORK-RELEASE PREPARED/OUTSTANDING disposition",
    "PREPARED" in readiness and "OUTSTANDING" in readiness,
)
require(
    "readiness states no v1.1.0 tag exists",
    "no `v1.1.0` tag exists" in readiness or "No `v1.1.0` git ref" in readiness,
)

# --- Feature-list completeness: six siblings strict, 098 acknowledged ----

feature_list = json.loads(read(".agent/feature_list_013.json"))
features = {f["id"]: f for f in feature_list["features"]}
require(
    "all six sibling phase-013 features (092-097) implementation-complete",
    all(features[fid]["status"] == "complete" for fid in ("092", "093", "094", "095", "096", "097")),
)
feature_098_status = features["098"]["status"]
print(
    f"PASS feature 098 status acknowledged ({feature_098_status}) -- "
    "pre-Step-7 evidence capture expects non-complete; a post-Step-7 "
    "re-run legitimately observes 'complete'"
)

# --- Real repository: no v1.1.0 tag ---------------------------------------

tag_probe = subprocess.run(
    ["git", "rev-parse", "-q", "--verify", "refs/tags/v1.1.0"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    check=False,
)
require("real repository has no v1.1.0 tag", tag_probe.returncode != 0)
