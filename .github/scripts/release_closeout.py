#!/usr/bin/env python3
"""Release close-out gate: internal version-anchor consistency.

Mechanizes the internal-consistency invariant of
methodology/06_release_train.md across the release surface: every place
the framework's version is spelled out must agree with a single reference
(NIZAM.json's ``framework.version``, hereafter ``V``).

Two modes:

  ``--mode pr``
      Assert every version anchor in the CURRENT WORKING TREE agrees
      with V. Run as a paths-filtered pull-request gate
      (``.github/workflows/release_closeout.yml``).

  ``--mode tag --tag vX.Y.Z``
      Assert the same anchors agree with each other AS THEY EXISTED AT
      THE GIVEN TAG (read via ``git show TAG:<path>``, never the ambient
      checkout -- this is load-bearing for ``workflow_dispatch``
      republication, whose ref is the default branch, not the tag), plus
      three tag-specific checks: the tag's own shape, the tag versus V
      at that tag, and CHANGELOG.md's top section versus the tag. Wired
      as a blocking step in ``.github/workflows/release.yml`` between tag
      resolution and CHANGELOG extraction.

Era-safety (``--mode tag`` only): a tag that predates one of these six
anchor files entirely SKIPS that anchor's assertion group (rule (a));
a tag whose ROADMAP.md body carries no disposition line naming that
tag's own version SKIPS the ROADMAP group (rule (b), pre-convention
ROADMAP); a tag whose anchor FILE exists but a specific anchor WITHIN
it is absent (e.g. CONTEXT.md with no ``change_log`` key) emits a named
FAIL rather than a SKIP or an uncaught exception (rule (a-EXT) -- a
present-but-incomplete file is real, reportable drift, not an
era-safety gap). See ``.agent/contracts/097.json`` design_notes for the
full rationale and the verified 14-tag hand-walk.

Stdlib-only, network-free. Never creates, deletes, or pushes a ref of
any kind; ``--mode tag`` shells out only to the read-only,
ref-non-mutating ``git show``. Generalizes the
``require(label, condition)`` style of
``.agent/evidence/091/verify_release_prep.py``, hardened for unattended
CI use: instead of letting an ``AssertionError`` surface as a
traceback, this prints ``FAIL <label>`` and exits 1 at the first
failing assertion.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

TAG_SHAPE_RE = re.compile(r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

# CONTEXT.md: the frontmatter's top-level, UNINDENTED "version:" key (never
# the indented "- version:" lines inside change_log entries, which this
# regex's ^-anchor deliberately excludes).
CONTEXT_FRONTMATTER_VERSION_RE = re.compile(r'^version:\s*"?([^"\s]+)"?\s*$', re.MULTILINE)
# CONTEXT.md: the FIRST change_log entry's version (change_log[0].version).
CONTEXT_CHANGE_LOG_VERSION_RE = re.compile(r'change_log:\s*\n\s*-\s*version:\s*"?([^"\s]+)"?')

# README.md: generic (any-version) presence probes, used to distinguish
# "this pin convention does not exist yet at this tag" (era-safety a-EXT)
# from "this pin convention exists but names the wrong version" (a genuine
# value-drift FAIL).
README_PIN_GENERIC_RES = [
    re.compile(r"nizam-framework/v\d+\.\d+\.\d+/bootstrap\.sh"),
    re.compile(r"GOVERNANCE_TAG=v\d+\.\d+\.\d+"),
    re.compile(r"--tag v\d+\.\d+\.\d+"),
    re.compile(r"releases/tag/v\d+\.\d+\.\d+"),
]

# CHANGELOG.md: the literal-starts-with "## [VERSION] - " heading format
# (YYYY-MM-DD suffix not asserted beyond presence of a heading match), and
# the tier-banner-plus-citation convention within that section's body.
CHANGELOG_HEADING_RE = re.compile(r"^## \[([^\]]+)\] - ", re.MULTILINE)
CHANGELOG_ANY_HEADING_RE = re.compile(r"^## \[", re.MULTILINE)
CHANGELOG_TIER_BANNER_RE = re.compile(r"\*\*(Major|Minor|Patch) release\*\*")
CHANGELOG_CITATION = "methodology/06_release_train.md"

ANCHOR_PATHS = {
    "nizam": "NIZAM.json",
    "context": "CONTEXT.md",
    "guide": "docs/guide/index.html",
    "readme": "README.md",
    "changelog": "CHANGELOG.md",
    "roadmap": "docs/planning/ROADMAP.md",
}


def require(label: str, condition: bool) -> None:
    """Print ``PASS <label>`` on success; print ``FAIL <label>`` and exit
    1 immediately on the first failing assertion (first-failure semantics).
    """
    if not condition:
        print(f"FAIL {label}")
        sys.exit(1)
    print(f"PASS {label}")


def skip(label: str, reason: str) -> None:
    """Record an era-safety SKIP as an explicit, reason-carrying PASS line."""
    print(f"PASS {label} (skipped: {reason})")


def fail_anchor_absent(label: str, path: str, tag: Optional[str]) -> None:
    """Rule (a-EXT): the anchor FILE exists but the specific anchor within
    it is absent. A named FAIL, never a SKIP and never an uncaught
    exception. In --mode pr (tag is None) this degrades to a plain FAIL,
    since PR mode's anchors are always expected present in the working
    tree.
    """
    if tag is None:
        require(label, False)
    else:
        require(f"{label} (anchor absent in {path} at {tag})", False)


def read_working_tree(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def read_at_tag(tag: str, path: str) -> Optional[str]:
    """Read ``path`` as it existed at ``tag`` via a read-only ``git show``,
    or return None if the file did not exist there (rule (a) input).
    """
    result = subprocess.run(
        ["git", "show", f"{tag}:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def document_body(content: str) -> str:
    """Return a frontmatter'd document's BODY: lines strictly after the
    closing frontmatter '---' delimiter (the second literal '---' line,
    since the first opens the frontmatter). If fewer than two '---' lines
    are found, the whole document is treated as the body.
    """
    lines = content.splitlines()
    dash_indices = [i for i, line in enumerate(lines) if line == "---"]
    if len(dash_indices) < 2:
        return content
    return "\n".join(lines[dash_indices[1] + 1 :])


# --- Assertion groups (shared between --mode pr and --mode tag) ----------


def group_context(content: Optional[str], path: str, tag: Optional[str], version: str) -> None:
    """Group 1: CONTEXT.md frontmatter version == V AND change_log[0].version == V."""
    label = "CONTEXT.md version anchor (frontmatter + change_log[0])"
    if content is None:
        skip(label, f"{path} absent at {tag}")
        return
    fm_match = CONTEXT_FRONTMATTER_VERSION_RE.search(content)
    cl_match = CONTEXT_CHANGE_LOG_VERSION_RE.search(content)
    if fm_match is None or cl_match is None:
        fail_anchor_absent(label, path, tag)
        return
    require(label, fm_match.group(1) == version and cl_match.group(1) == version)


def group_guide(content: Optional[str], path: str, tag: Optional[str], version: str) -> None:
    """Group 2: docs/guide/index.html framework-version meta == V AND
    footer-version span == V."""
    label = "docs/guide/index.html version anchors (meta + footer)"
    if content is None:
        skip(label, f"{path} absent at {tag}")
        return
    meta_key_present = 'name="framework-version"' in content
    footer_key_present = 'id="footer-version"' in content
    if not meta_key_present or not footer_key_present:
        fail_anchor_absent(label, path, tag)
        return
    meta_ok = f'<meta name="framework-version" content="{version}">' in content
    footer_ok = f'<span id="footer-version">{version}</span>' in content
    require(label, meta_ok and footer_ok)


def group_readme(content: Optional[str], path: str, tag: Optional[str], version: str) -> None:
    """Group 3: README.md's four version pins (curl URL / GOVERNANCE_TAG /
    --tag / releases-tag) all == V. The migration-guide link is
    deliberately excluded (it legitimately stays pinned to the last
    version that shipped a migration guide across no-new-migration MINOR
    releases -- see contract 097's migration_link_exclusion_rationale)."""
    label = "README.md version pins (curl URL / GOVERNANCE_TAG / --tag / releases-tag)"
    if content is None:
        skip(label, f"{path} absent at {tag}")
        return
    generic_present = [bool(pattern.search(content)) for pattern in README_PIN_GENERIC_RES]
    if not any(generic_present):
        fail_anchor_absent(label, path, tag)
        return
    exact_pins = [
        f"nizam-framework/v{version}/bootstrap.sh",
        f"GOVERNANCE_TAG=v{version}",
        f"--tag v{version}",
        f"releases/tag/v{version}",
    ]
    require(label, all(pin in content for pin in exact_pins))


def changelog_top_section(content: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (heading_version, section_body) for the first '## [' heading
    strictly after '## [Unreleased]', or (None, None) if no such heading
    is found."""
    unreleased_idx = content.find("## [Unreleased]")
    if unreleased_idx == -1:
        return None, None
    rest = content[unreleased_idx + len("## [Unreleased]") :]
    heading_match = CHANGELOG_HEADING_RE.search(rest)
    if heading_match is None:
        return None, None
    heading_version = heading_match.group(1)
    tail = rest[heading_match.end() :]
    next_heading_match = CHANGELOG_ANY_HEADING_RE.search(tail)
    section = tail[: next_heading_match.start()] if next_heading_match else tail
    return heading_version, section


def group_changelog(
    content: Optional[str], path: str, tag: Optional[str], version: str
) -> Optional[str]:
    """Group 4: CHANGELOG.md's first '## [' heading after '## [Unreleased]'
    is literal-starts-with '## [V] - ' AND that section's body carries a
    tier banner ('**Major/Minor/Patch release**') AND cites
    methodology/06_release_train.md. Returns the heading's own version
    string (used by tag-mode addition (c)), or None if skipped/absent."""
    label = "CHANGELOG.md top released section (heading + tier banner)"
    if content is None:
        skip(label, f"{path} absent at {tag}")
        return None
    heading_version, section = changelog_top_section(content)
    if heading_version is None:
        fail_anchor_absent(label, path, tag)
        return None
    tier_ok = (
        section is not None
        and CHANGELOG_TIER_BANNER_RE.search(section) is not None
        and CHANGELOG_CITATION in section
    )
    if not tier_ok:
        fail_anchor_absent(label, path, tag)
        return heading_version
    require(label, heading_version == version)
    return heading_version


def group_roadmap(content: Optional[str], path: str, tag: Optional[str], version: str) -> None:
    """Group 5: ROADMAP.md names vV in exactly one of 'Latest released
    tag: vV' or 'Release in preparation: vV', scoped to the document
    BODY only (lines strictly after the closing frontmatter '---'), since
    the frontmatter's change_log array may legitimately narrate a PAST
    disposition using the same literal phrase for an earlier version.

    In --mode tag only, a body-scoped count of 0 SKIPS this group (rule
    (b): pre-convention ROADMAP, or a stale prior-version-only
    disposition survives at that tag) rather than FAILing; --mode pr has
    no such skip -- the current tree's disposition is unconditionally
    required.
    """
    label = "ROADMAP.md disposition line (Latest released tag / Release in preparation)"
    if content is None:
        skip(label, f"{path} absent at {tag}")
        return
    body = document_body(content)
    pattern = re.compile(
        rf"Latest released tag: v{re.escape(version)}\b"
        rf"|Release in preparation: v{re.escape(version)}\b"
    )
    count = sum(1 for line in body.splitlines() if pattern.search(line))
    if tag is not None and count == 0:
        skip(label, f"pre-convention ROADMAP at {tag}")
        return
    require(label, count == 1)


# --- Mode drivers ----------------------------------------------------------


def run_pr_mode() -> None:
    nizam = json.loads(read_working_tree(ANCHOR_PATHS["nizam"]))
    version = nizam["framework"]["version"]

    group_context(read_working_tree(ANCHOR_PATHS["context"]), ANCHOR_PATHS["context"], None, version)
    group_guide(read_working_tree(ANCHOR_PATHS["guide"]), ANCHOR_PATHS["guide"], None, version)
    group_readme(read_working_tree(ANCHOR_PATHS["readme"]), ANCHOR_PATHS["readme"], None, version)
    group_changelog(read_working_tree(ANCHOR_PATHS["changelog"]), ANCHOR_PATHS["changelog"], None, version)
    group_roadmap(read_working_tree(ANCHOR_PATHS["roadmap"]), ANCHOR_PATHS["roadmap"], None, version)

    print(f"Release close-out: all internal version anchors agree with V={version} (--mode pr).")


def run_tag_mode(tag: str) -> None:
    # Tag-mode addition (a): the tag itself matches the semver-tag shape,
    # checked FIRST -- before any git-show read is attempted -- so a
    # malformed tag is attributed to this assertion, not misread as a
    # file-absence SKIP on whichever anchor happens to be checked first.
    require("tag shape (vMAJOR.MINOR.PATCH)", bool(TAG_SHAPE_RE.match(tag)))

    nizam_content = read_at_tag(tag, ANCHOR_PATHS["nizam"])
    require(f"NIZAM.json readable at {tag} (V reference)", nizam_content is not None)
    version = json.loads(nizam_content)["framework"]["version"]

    # Tag-mode addition (b): the tag, minus its leading 'v', equals V as it
    # existed AT THAT TAG -- catching a tag pushed against a tree whose
    # anchors were never bumped.
    require(f"tag {tag} matches NIZAM.json framework.version at tag ({version})", tag[1:] == version)

    group_context(read_at_tag(tag, ANCHOR_PATHS["context"]), ANCHOR_PATHS["context"], tag, version)
    group_guide(read_at_tag(tag, ANCHOR_PATHS["guide"]), ANCHOR_PATHS["guide"], tag, version)
    group_readme(read_at_tag(tag, ANCHOR_PATHS["readme"]), ANCHOR_PATHS["readme"], tag, version)

    changelog_content = read_at_tag(tag, ANCHOR_PATHS["changelog"])
    heading_version = group_changelog(changelog_content, ANCHOR_PATHS["changelog"], tag, version)

    group_roadmap(read_at_tag(tag, ANCHOR_PATHS["roadmap"]), ANCHOR_PATHS["roadmap"], tag, version)

    # Tag-mode addition (c): CHANGELOG.md's top released section names the
    # same version as the tag itself -- catching a CHANGELOG edited out of
    # lockstep with the tag. Only runs if group 4 produced a heading
    # version (it SKIPS, rather than raising, when CHANGELOG.md itself is
    # absent at the tag -- which never happens across real history, but is
    # handled here rather than assumed).
    if heading_version is not None:
        require(f"CHANGELOG.md top section matches tag {tag}", heading_version == tag[1:])

    print(f"Release close-out: tag {tag}'s anchors are internally consistent (--mode tag).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["pr", "tag"], required=True)
    parser.add_argument("--tag", default=None, help="Required, and only meaningful, with --mode tag.")
    args = parser.parse_args()

    if args.mode == "tag" and not args.tag:
        parser.error("--mode tag requires --tag vX.Y.Z")

    if args.mode == "pr":
        run_pr_mode()
    else:
        run_tag_mode(args.tag)

    return 0


if __name__ == "__main__":
    sys.exit(main())
