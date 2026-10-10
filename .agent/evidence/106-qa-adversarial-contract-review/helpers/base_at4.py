#!/usr/bin/env python3
"""Run acceptance test 4 against the unmodified tree. It must fail closed."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

os.chdir(lib.REPO)
command = lib.verification("at4-planning-moved.txt")["command"]
proc = lib.run(command, lib.REPO, timeout=180)
sys.stdout.write(lib.format_result("AT4 at <A>", proc))
sys.exit(proc.returncode)
