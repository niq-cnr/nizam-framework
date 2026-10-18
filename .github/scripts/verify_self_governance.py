#!/usr/bin/env python3
"""Verify the installed governance against its immutable released Git tree."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "tools") not in sys.path:
    sys.path.insert(0, str(REPO / "tools"))

from payload_integrity import GovernanceDrift, verify_payload_integrity  # noqa: E402

TAG = "v1.8.0"
SHA = "606d11ee84deff0d3b7934cbfd715223d64ac79d"
SOURCE = "https://github.com/niq-cnr/nizam-framework.git"
EXPECTED_FILE_COUNT = 277


def verify(payload: Path) -> int:
    result = verify_payload_integrity(
        payload,
        git_repo=REPO,
        expected_tag=TAG,
        expected_sha=SHA,
        expected_source_url=SOURCE,
        expected_framework_version=TAG.lstrip("v"),
        expected_file_count=EXPECTED_FILE_COUNT,
        require_tag_ref=True,
    )
    return int(result["verified_files"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload-dir", type=Path, default=REPO / ".nizam")
    args = parser.parse_args()
    try:
        count = verify(args.payload_dir.absolute())
    except (GovernanceDrift, OSError) as error:
        print(f"SELF-GOVERNANCE FAIL: {error}", file=sys.stderr)
        return 1
    print(f"SELF-GOVERNANCE PASS: {count} released files + genuine provenance; {TAG} at {SHA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
