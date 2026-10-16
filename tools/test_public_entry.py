#!/usr/bin/env python3
"""Read the shipped public entry and require the three start paths.

The checks open README.md and docs/guide/index.html. They do not
reimplement the prose.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GUIDE = ROOT / "docs/guide" / "index.html"


def section(text, start, end):
    """Return the slice from start through the line before end."""
    begin = text.index(start)
    finish = text.index(end, begin)
    return text[begin:finish]


def require(text, needle):
    if needle not in text:
        raise SystemExit("missing required text: " + needle)


def main():
    readme = README.read_text(encoding="utf-8")
    guide = GUIDE.read_text(encoding="utf-8")
    paths = section(readme, "## Start paths", "## Quickstart")
    guide_paths = section(guide, 'id="start-paths"', 'id="execution-loop"')
    install = section(readme, "## Quickstart", "## Local governance")

    for text in (paths, guide_paths):
        require(text, "New feature")
        require(text, "Bug fix")
        require(text, "Small unambiguous change")
        require(text, "Implementation may begin only after the contract is approved")
        require(text, "independent post-implementation check")
        require(text, "recorded verification result")
        require(text, "assessed cause")
        require(text, "scoped fix")
        require(text, "does not require the full feature-gate stack")
        require(text, "Implementation may begin once the intent is recorded")
        for banned in ("surpass", "superior", "world class", "matches Superpowers",
                       "matches BMAD", "matches Spec Kit"):
            if banned in text:
                raise SystemExit("comparison claim in public entry: " + banned)

    require(install, "--tag v1.5.0")
    require(install, "never a floating branch (`main`, `master`, `HEAD` are all refused)")
    require(install, "`tools/validate.sh`")
    require(paths, "Spec Kit")
    require(paths, "Superpowers")
    require(paths, "BMAD Method")
    print("public-entry: feature, bug-fix, and small-change paths present")
    print("public-entry: install pin and compliance check present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
