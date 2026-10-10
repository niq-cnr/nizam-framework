#!/usr/bin/env python3
"""Everything pinned except the subset block. AT4 and S05 must not pass."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

os.chdir(lib.REPO)


def main() -> int:
    parent = Path(tempfile.mkdtemp(prefix="nizam-106-nosubset-"))
    tree = parent / "repo"
    try:
        lib.copy_tree(tree)
        lib.apply_faithful(tree, subset=False)
        at4 = lib.run(lib.verification("at4-planning-moved.txt")["command"], tree, timeout=180)
        print(lib.format_result("AT4 without subset block", at4, tree))
        s05 = lib.run(lib.verification("s05-discriminating.txt")["command"], tree, timeout=900)
        print(lib.format_result("S05 without subset block", s05, tree))
        if at4.returncode == 0 or s05.returncode == 0:
            print("UNEXPECTED PASS without the subset block")
            return 0 if s05.returncode == 0 else at4.returncode
        print(f"caught: AT4 rc={at4.returncode} S05 rc={s05.returncode}")
        return s05.returncode
    finally:
        shutil.rmtree(parent, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
