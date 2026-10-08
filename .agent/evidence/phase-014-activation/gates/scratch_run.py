#!/usr/bin/env python3
"""Phase-014 acceptance helper: run a command in a mutated scratch copy of the repository.

Frozen at phase-014 activation (Planner-authored acceptance infrastructure). No
phase-014 feature contract may modify anything under
.agent/evidence/phase-014-activation/.

Run from the repository root:

    python3 .agent/evidence/phase-014-activation/gates/scratch_run.py \
        [--replace PATH OLD NEW]... [--write PATH TEXT]... [--py-mutate CODE]... \
        --expect-rc N|nonzero [--expect REGEX]... [--forbid REGEX]... -- CMD [ARG...]

The working tree (tracked and untracked files, plus .git, so `git show HEAD:<path>`
still works) is copied into a private temporary directory. The mutations are applied
in order, then CMD runs with the copy as its working directory. The real repository
is never written. The temporary directory is always removed.

Mutations are fail-closed, so a negative control can never pass vacuously:
  --replace   OLD must occur EXACTLY once in PATH;
  --write     PATH must not already exist;
  --py-mutate CODE runs with `root` (a pathlib.Path to the copy) in scope and must not raise.
A failed mutation precondition exits 3, never 0.

Expectations (all must hold for exit 0) are checked over stdout+stderr:
  --expect-rc N|nonzero   the command's exit status;
  --expect REGEX          must match (re.M) at least once;
  --forbid REGEX          must not match.

Exit codes: 0 expectations held; 1 an expectation failed; 2 usage; 3 mutation precondition failed.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class MutationPreconditionError(Exception):
    """Raised when a mutation cannot be applied exactly as specified."""


def copy_tree(dest: Path) -> Path:
    """Copy the repository root (the current directory) into dest/repo and return it."""
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != Path.cwd().resolve():
        raise SystemExit("scratch_run: must be run from the repository root")
    target = dest / "repo"
    shutil.copytree(Path.cwd(), target, symlinks=True)
    return target


def apply_mutations(root: Path, ops: list[tuple[str, list[str]]]) -> list[str]:
    """Apply every mutation in order; return a human-readable log line per mutation."""
    log = []
    for kind, values in ops:
        if kind == "replace":
            rel, old, new = values
            path = root / rel
            if not path.is_file():
                raise MutationPreconditionError(f"--replace: {rel} does not exist")
            text = path.read_text(encoding="utf-8")
            count = text.count(old)
            if count != 1:
                raise MutationPreconditionError(f"--replace: {old!r} occurs {count} times in {rel} (need exactly 1)")
            path.write_text(text.replace(old, new), encoding="utf-8")
            log.append(f"replaced 1 occurrence in {rel}")
        elif kind == "write":
            rel, content = values
            path = root / rel
            if path.exists():
                raise MutationPreconditionError(f"--write: {rel} already exists")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            log.append(f"wrote new file {rel}")
        elif kind == "py":
            (code,) = values
            try:
                exec(compile(code, "<py-mutate>", "exec"), {"root": root, "Path": Path})  # noqa: S102
            except Exception as exc:  # any failure is a precondition failure, never a pass
                raise MutationPreconditionError(f"--py-mutate raised {type(exc).__name__}: {exc}") from exc
            log.append("applied --py-mutate")
    return log


def main() -> int:
    """Parse arguments, run the command in a mutated copy, and check expectations."""
    argv = sys.argv[1:]
    if "--" not in argv:
        print("scratch_run: usage error: missing '--' before the command")
        return 2
    split = argv.index("--")
    opts, command = argv[:split], argv[split + 1:]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--replace", nargs=3, action="append", default=[], metavar=("PATH", "OLD", "NEW"))
    parser.add_argument("--write", nargs=2, action="append", default=[], metavar=("PATH", "TEXT"))
    parser.add_argument("--py-mutate", action="append", default=[], metavar="CODE")
    parser.add_argument("--expect-rc", required=True)
    parser.add_argument("--expect", action="append", default=[])
    parser.add_argument("--forbid", action="append", default=[])
    args = parser.parse_args(opts)
    if not command:
        print("scratch_run: usage error: empty command")
        return 2
    ops = ([("replace", v) for v in args.replace] + [("write", v) for v in args.write]
           + [("py", [c]) for c in args.py_mutate])

    tmp = Path(tempfile.mkdtemp(prefix="nizam-scratch-run-"))
    try:
        root = copy_tree(tmp)
        try:
            for line in apply_mutations(root, ops):
                print(f"scratch_run: {line}")
        except MutationPreconditionError as exc:
            print(f"scratch_run: MUTATION PRECONDITION FAILED: {exc}")
            return 3
        proc = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out = proc.stdout + proc.stderr
    print(f"scratch_run: command {' '.join(command)} -> exit {proc.returncode}")
    print("\n".join("  | " + ln for ln in out.splitlines()[-40:]))

    checks = []
    if args.expect_rc == "nonzero":
        checks.append(("exit status is non-zero", proc.returncode != 0))
    else:
        checks.append((f"exit status == {args.expect_rc}", proc.returncode == int(args.expect_rc)))
    checks += [(f"output matches {rx!r}", re.search(rx, out, re.M) is not None) for rx in args.expect]
    checks += [(f"output does not match {rx!r}", re.search(rx, out, re.M) is None) for rx in args.forbid]
    ok = True
    for label, cond in checks:
        print(("PASS " if cond else "FAIL ") + label)
        ok = ok and cond
    print(f"scratch_run: {'EXPECTATIONS HELD' if ok else 'EXPECTATION FAILED'}; scratch removed: {not tmp.exists()}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
