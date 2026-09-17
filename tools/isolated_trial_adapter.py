#!/usr/bin/env python3
"""Landlock half of the Linux convergent-review trial isolation adapter.

The evaluator starts this program inside new user/network/IPC/UTS/PID namespaces.
This program then restricts filesystem access to the trial root, the runner file,
and read/execute-only system runtime paths before executing the trusted runner.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import stat
import sys
from pathlib import Path

SYS_LANDLOCK_CREATE_RULESET = 444
SYS_LANDLOCK_ADD_RULE = 445
SYS_LANDLOCK_RESTRICT_SELF = 446
LANDLOCK_CREATE_RULESET_VERSION = 1
LANDLOCK_RULE_PATH_BENEATH = 1
PR_SET_NO_NEW_PRIVS = 38

EXECUTE = 1 << 0
WRITE_FILE = 1 << 1
READ_FILE = 1 << 2
READ_DIR = 1 << 3
REMOVE_DIR = 1 << 4
REMOVE_FILE = 1 << 5
MAKE_CHAR = 1 << 6
MAKE_DIR = 1 << 7
MAKE_REG = 1 << 8
MAKE_SOCK = 1 << 9
MAKE_FIFO = 1 << 10
MAKE_BLOCK = 1 << 11
MAKE_SYM = 1 << 12
REFER = 1 << 13
TRUNCATE = 1 << 14
BASE_ACCESS = (
    EXECUTE | WRITE_FILE | READ_FILE | READ_DIR | REMOVE_DIR | REMOVE_FILE |
    MAKE_CHAR | MAKE_DIR | MAKE_REG | MAKE_SOCK | MAKE_FIFO | MAKE_BLOCK | MAKE_SYM
)


class RulesetAttr(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]


class PathBeneathAttr(ctypes.Structure):
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int)]


def syscall(number: int, *arguments: object) -> int:
    libc = ctypes.CDLL(None, use_errno=True)
    result = int(libc.syscall(number, *arguments))
    if result < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return result


def add_path_rule(ruleset_fd: int, path: Path, access: int) -> None:
    descriptor = os.open(path, getattr(os, "O_PATH", os.O_RDONLY) | getattr(os, "O_CLOEXEC", 0))
    try:
        is_directory = stat.S_ISDIR(os.fstat(descriptor).st_mode)
        allowed = access if is_directory else access & (READ_FILE | WRITE_FILE | EXECUTE | TRUNCATE)
        attribute = PathBeneathAttr(allowed_access=allowed, parent_fd=descriptor)
        syscall(SYS_LANDLOCK_ADD_RULE, ruleset_fd, LANDLOCK_RULE_PATH_BENEATH, ctypes.byref(attribute), 0)
    finally:
        os.close(descriptor)


def restrict_filesystem(root: Path, runner: Path) -> int:
    abi = syscall(SYS_LANDLOCK_CREATE_RULESET, 0, 0, LANDLOCK_CREATE_RULESET_VERSION)
    handled = BASE_ACCESS
    if abi >= 2:
        handled |= REFER
    if abi >= 3:
        handled |= TRUNCATE
    ruleset_attr = RulesetAttr(handled_access_fs=handled)
    ruleset_fd = syscall(
        SYS_LANDLOCK_CREATE_RULESET, ctypes.byref(ruleset_attr), ctypes.sizeof(ruleset_attr), 0,
    )
    try:
        # Trial data is readable/writable but never executable. EXECUTE is granted
        # only to the pre-resolved trusted runner and installed runtime trees below.
        trial_access = handled & ~EXECUTE
        add_path_rule(ruleset_fd, root, trial_access)
        add_path_rule(ruleset_fd, runner, READ_FILE | EXECUTE)
        for system_path in (Path("/usr"), Path("/lib"), Path("/lib64")):
            if system_path.exists():
                add_path_rule(ruleset_fd, system_path, READ_FILE | READ_DIR | EXECUTE)
        cache = Path("/etc/ld.so.cache")
        if cache.exists():
            add_path_rule(ruleset_fd, cache, READ_FILE)
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0)
    finally:
        os.close(ruleset_fd)
    return abi


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--runner", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = Path(args.root).resolve(strict=True)
    runner = Path(args.runner).resolve(strict=True)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or Path(command[0]).resolve(strict=True) != runner:
        raise SystemExit("adapter command must execute the exact trusted runner")
    os.chdir(root)
    restrict_filesystem(root, runner)
    os.execv(str(runner), command)
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
