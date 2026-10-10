#!/usr/bin/env python3
"""S04 must fail when every pin is present except the subset block."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

os.chdir(lib.REPO)
parent = Path(tempfile.mkdtemp(prefix="nizam-106-s04mut-"))
tree = parent / "repo"
try:
    lib.copy_tree(tree)
    lib.apply_faithful(tree, subset=False)
    proc = lib.run(lib.verification("s04-pinned-structure.txt")["command"], tree, timeout=60)
    sys.stdout.write(lib.format_result("S04 without subset block", proc, tree))
    sys.exit(proc.returncode)
finally:
    shutil.rmtree(parent, ignore_errors=True)
