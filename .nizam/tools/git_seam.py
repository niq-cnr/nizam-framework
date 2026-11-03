#!/usr/bin/env python3
"""Hardened read-only Git observation seam for Nizam governance and assurance tools.

Enforces immutable object observation (--no-replace-objects, GIT_NO_REPLACE_OBJECTS=1,
core.useReplaceRefs=false), strips ambient Git environment/config/namespace/worktree
redirection, disables optional index locks (GIT_OPTIONAL_LOCKS=0), preserves literal
pathspecs (--literal-pathspecs, core.quotePath=false), verifies explicit repository and
worktree roots (supporting detached HEADs and linked worktrees), and distinguishes
absent objects/paths from Git command or repository-integrity failures.
"""

from __future__ import annotations

import configparser
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
from typing import Iterable, Sequence

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


class GitSeamError(Exception):
    """Raised when an immutable Git observation or repository boundary check fails."""

    def __init__(self, message: str, *, is_missing_object: bool = False) -> None:
        super().__init__(message)
        self.is_missing_object = is_missing_object


def _safe_git_path() -> str:
    """Return a minimal deterministic PATH containing the system git executable."""
    default_dirs = ["/usr/bin", "/bin", "/usr/local/bin", "/opt/homebrew/bin"]
    git_bin = shutil.which("git")
    if git_bin:
        git_parent = str(Path(git_bin).resolve().parent)
        if git_parent not in default_dirs:
            default_dirs.append(git_parent)
    return ":".join(default_dirs)


def sanitized_git_env(*, preserve_path: bool = False) -> dict[str, str]:
    """Return a clean environment dictionary with all ambient GIT_* redirection stripped."""
    return {
        "HOME": os.devnull,
        "XDG_CONFIG_HOME": os.devnull,
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.environ.get("PATH") or _safe_git_path() if preserve_path else _safe_git_path(),
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_COUNT": "5",
        "GIT_CONFIG_KEY_0": "core.useReplaceRefs",
        "GIT_CONFIG_VALUE_0": "false",
        "GIT_CONFIG_KEY_1": "core.quotePath",
        "GIT_CONFIG_VALUE_1": "false",
        "GIT_CONFIG_KEY_2": "core.fsmonitor",
        "GIT_CONFIG_VALUE_2": "false",
        "GIT_CONFIG_KEY_3": "core.hooksPath",
        "GIT_CONFIG_VALUE_3": os.devnull,
        "GIT_CONFIG_KEY_4": "protocol.allow",
        "GIT_CONFIG_VALUE_4": "never",
    }


def _check_config_no_worktree_redirect(config_path: Path, expected_worktree: Path) -> None:
    """Reject local .git/config files that redirect core.worktree to another path."""
    if not os.path.lexists(config_path):
        return
    st = config_path.lstat()
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise GitSeamError(f"unsafe Git config file mode at {config_path}")
    try:
        raw = config_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise GitSeamError(f"unreadable Git config at {config_path}: {exc}") from exc

    in_core = False
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", ";")):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            header = stripped[1:-1].strip().lower()
            in_core = header == "core" or header.startswith("core ")
            continue
        if in_core and "=" in stripped:
            key, _, val = stripped.partition("=")
            if key.strip().lower() == "worktree":
                wt_val = val.strip().strip('"')
                resolved_wt = (config_path.parent / wt_val).resolve() if not os.path.isabs(wt_val) else Path(wt_val).resolve()
                if resolved_wt != expected_worktree:
                    raise GitSeamError(
                        f"unsafe core.worktree redirection in Git config ({resolved_wt} != {expected_worktree})"
                    )


def validate_repo_root(
    repo: Path | str,
    *,
    allow_bare: bool = False,
) -> tuple[Path, Path, Path]:
    """Verify repo is an exact non-symlinked Git toplevel (or bare repo if allow_bare=True).

    Returns (resolved_root, git_dir, common_dir) without spawning a subprocess.
    """
    supplied = Path(repo)
    if supplied.is_symlink():
        raise GitSeamError("repository root is symlink")
    try:
        resolved = supplied.resolve(strict=True)
    except OSError as exc:
        raise GitSeamError(f"repository root does not exist: {repo}") from exc
    if not resolved.is_dir():
        raise GitSeamError(f"repository root is not a directory: {repo}")

    dotgit = resolved / ".git"
    if os.path.lexists(dotgit):
        st = dotgit.lstat()
        if stat.S_ISLNK(st.st_mode):
            raise GitSeamError("repository .git entry is a symlink")
        if stat.S_ISDIR(st.st_mode):
            git_dir = dotgit
            common_dir = dotgit
        elif stat.S_ISREG(st.st_mode):
            try:
                content = dotgit.read_text(encoding="utf-8").strip()
            except (OSError, UnicodeDecodeError) as exc:
                raise GitSeamError(f"unreadable .git file at {dotgit}: {exc}") from exc
            if not content.startswith("gitdir: "):
                raise GitSeamError(f"malformed .git file at {dotgit}")
            raw_target = content[len("gitdir: "):].strip()
            target_path = Path(raw_target) if os.path.isabs(raw_target) else (resolved / raw_target)
            if target_path.is_symlink():
                raise GitSeamError("linked worktree gitdir is a symlink")
            try:
                git_dir = target_path.resolve(strict=True)
            except OSError as exc:
                raise GitSeamError(f"linked worktree gitdir missing: {target_path}") from exc
            commondir_file = git_dir / "commondir"
            if os.path.lexists(commondir_file):
                if commondir_file.is_symlink() or not commondir_file.is_file():
                    raise GitSeamError("linked worktree commondir is a symlink or non-regular file")
                rel_common = commondir_file.read_text(encoding="utf-8").strip()
                common_candidate = Path(rel_common) if os.path.isabs(rel_common) else (git_dir / rel_common)
                if common_candidate.is_symlink():
                    raise GitSeamError("linked worktree common_dir target is a symlink")
                common_dir = common_candidate.resolve(strict=True)
            else:
                common_dir = git_dir
        else:
            raise GitSeamError("unsupported .git entry mode")
    elif allow_bare and os.path.lexists(resolved / "HEAD") and os.path.lexists(resolved / "objects"):
        git_dir = resolved
        common_dir = resolved
    else:
        raise GitSeamError(f"repository must be Git toplevel: {resolved}")

    head_path = git_dir / "HEAD"
    if not os.path.lexists(head_path) or head_path.is_symlink() or not head_path.is_file():
        raise GitSeamError("missing or symlinked Git HEAD metadata")

    index_path = git_dir / "index"
    if os.path.lexists(index_path) and (index_path.is_symlink() or not index_path.is_file()):
        raise GitSeamError("unsafe or symlinked Git index file")

    objects_dir = common_dir / "objects"
    if not os.path.lexists(objects_dir) or objects_dir.is_symlink() or not objects_dir.is_dir():
        raise GitSeamError("missing or symlinked Git objects directory")

    grafts_path = common_dir / "info" / "grafts"
    if os.path.lexists(grafts_path):
        raise GitSeamError("unsafe Git grafts file present (.git/info/grafts)")

    alternates_path = objects_dir / "info" / "alternates"
    if os.path.lexists(alternates_path) and (alternates_path.is_symlink() or not alternates_path.is_file()):
        raise GitSeamError("unsafe symlinked Git object alternates file (.git/objects/info/alternates)")

    if not allow_bare or os.path.lexists(dotgit):
        _check_config_no_worktree_redirect(common_dir / "config", resolved)
        if git_dir != common_dir:
            _check_config_no_worktree_redirect(git_dir / "config.worktree", resolved)

    return resolved, git_dir, common_dir


def _normalize_git_args(args: Sequence[str]) -> list[str]:
    """Strip redundant leading --literal-pathspecs or --no-replace-objects flags."""
    cleaned: list[str] = []
    leading = True
    for arg in args:
        if leading and arg in ("--literal-pathspecs", "--no-replace-objects", "--no-optional-locks"):
            continue
        leading = False
        cleaned.append(arg)
    return cleaned


def run_git_readonly(
    repo: Path | str,
    *args: str,
    allow_bare: bool = False,
) -> bytes:
    """Execute a read-only Git command against an explicitly validated repository root."""
    validate_repo_root(repo, allow_bare=allow_bare)
    clean_args = _normalize_git_args(args)
    argv = [
        "git",
        "-C",
        str(repo),
        "--no-replace-objects",
        "--literal-pathspecs",
        *clean_args,
    ]
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            check=True,
            env=sanitized_git_env(),
        )
        return result.stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        diagnostic = getattr(exc, "stderr", b"").decode("utf-8", errors="replace").strip()
        raise GitSeamError("Git observation failed: " + (diagnostic or str(exc))) from exc


def run_git_completed(
    repo: Path | str,
    args: Sequence[str],
    *,
    text: bool = True,
) -> subprocess.CompletedProcess:
    """Execute a read-only Git command returning CompletedProcess for start_path callers.

    Enforces sanitized environment, --no-optional-locks, --no-replace-objects, and
    --literal-pathspecs while rejecting symlinked .git metadata, grafts, alternates,
    or core.worktree redirection.
    """
    supplied = Path(repo)
    if supplied.is_symlink():
        empty = "" if text else b""
        err = "repository root is symlink\n" if text else b"repository root is symlink\n"
        return subprocess.CompletedProcess(["git", "-C", str(repo), *args], 128, stdout=empty, stderr=err)

    try:
        resolved = supplied.resolve(strict=True)
        for candidate in (resolved, *resolved.parents):
            if os.path.lexists(candidate / ".git"):
                validate_repo_root(candidate, allow_bare=False)
                break
    except GitSeamError as exc:
        empty = "" if text else b""
        msg = f"fatal: {exc}\n"
        err = msg if text else msg.encode("utf-8")
        return subprocess.CompletedProcess(["git", "-C", str(repo), *args], 128, stdout=empty, stderr=err)
    except OSError as exc:
        empty = "" if text else b""
        msg = f"fatal: {exc}\n"
        err = msg if text else msg.encode("utf-8")
        return subprocess.CompletedProcess(["git", "-C", str(repo), *args], 128, stdout=empty, stderr=err)

    clean_args = _normalize_git_args(args)
    argv = [
        "git",
        "-C",
        str(repo),
        "--no-optional-locks",
        "--no-replace-objects",
        "--literal-pathspecs",
        *clean_args,
    ]
    return subprocess.run(
        argv,
        env=sanitized_git_env(preserve_path=True),
        capture_output=True,
        text=text,
        check=False,
    )


def read_git_blobs(
    repo: Path | str,
    object_ids: Iterable[str],
    *,
    allow_bare: bool = False,
) -> dict[str, bytes]:
    """Read a batch of immutable Git blobs via cat-file --batch with replacement disabled."""
    validate_repo_root(repo, allow_bare=allow_bare)
    ids = sorted(set(object_ids))
    for oid in ids:
        if not isinstance(oid, str) or not SHA40_RE.fullmatch(oid):
            raise GitSeamError(f"invalid Git blob object id: {oid!r}")
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "--no-replace-objects", "cat-file", "--batch"],
            input=("\n".join(ids) + "\n").encode("ascii"),
            capture_output=True,
            check=True,
            env=sanitized_git_env(),
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GitSeamError("Git blob observation failed") from exc

    output = result.stdout
    offset = 0
    values: dict[str, bytes] = {}
    for oid in ids:
        end = output.find(b"\n", offset)
        if end < offset:
            raise GitSeamError("missing/nonblob Git input", is_missing_object=True)
        header = output[offset:end].decode("ascii", errors="replace").split()
        if len(header) == 2 and header[0] == oid and header[1] == "missing":
            raise GitSeamError(f"missing/nonblob Git input: {oid}", is_missing_object=True)
        if len(header) != 3 or header[0] != oid or header[1] != "blob":
            raise GitSeamError("missing/nonblob Git input", is_missing_object=False)
        size = int(header[2])
        offset = end + 1
        if output[offset + size : offset + size + 1] != b"\n":
            raise GitSeamError("truncated Git blob observation")
        values[oid] = output[offset : offset + size]
        offset += size + 1
    if offset != len(output):
        raise GitSeamError("unexpected Git blob output")
    return values


def read_git_blob(
    repo: Path | str,
    object_id: str,
    context: str = "blob",
    *,
    allow_bare: bool = False,
) -> bytes:
    """Read a single immutable Git blob, distinguishing missing objects from Git errors."""
    try:
        return read_git_blobs(repo, [object_id], allow_bare=allow_bare)[object_id]
    except GitSeamError as exc:
        raise GitSeamError(
            f"{context}: immutable Git blob read failed: {exc}",
            is_missing_object=exc.is_missing_object,
        ) from exc


def resolve_git_path_entry(
    repo: Path | str,
    commit: str,
    path: str,
    *,
    allowed_modes: tuple[str, ...] = ("100644", "100755", "120000"),
    allow_bare: bool = False,
) -> tuple[str, str] | None:
    """Resolve one literal path in a commit tree to (mode, blob_oid) or None if absent."""
    if not isinstance(commit, str) or not SHA40_RE.fullmatch(commit):
        raise GitSeamError(f"commit must be explicit 40-hex SHA: {commit!r}")
    verified = run_git_readonly(repo, "rev-parse", "--verify", f"{commit}^{{commit}}", allow_bare=allow_bare).decode("ascii").strip()
    if verified != commit:
        raise GitSeamError(f"commit anchor is not an exact commit object: {commit}")
    raw = run_git_readonly(repo, "ls-tree", "-z", commit, "--", path, allow_bare=allow_bare)
    records = [record for record in raw.split(b"\0") if record]
    if not records:
        return None
    if len(records) != 1:
        raise GitSeamError(f"Git tree lookup returned multiple entries for {path}")
    metadata, raw_path = records[0].split(b"\t", 1)
    if raw_path.decode("utf-8", errors="surrogateescape") != path:
        raise GitSeamError(f"Git tree lookup returned unexpected path for {path}")
    mode_bytes, kind_bytes, oid_bytes = metadata.split(b" ", 2)
    mode = mode_bytes.decode("ascii")
    kind = kind_bytes.decode("ascii")
    object_id = oid_bytes.decode("ascii")
    if kind != "blob" or mode not in allowed_modes:
        raise GitSeamError(f"unsupported tree entry {mode} {kind} {path}")
    return mode, object_id


def mutate_remove_worktree(repo: Path | str, attempt_root: str) -> bytes:
    """Authorized worktree removal helper for rollback_owned_attempt only."""
    validate_repo_root(repo, allow_bare=False)
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "--no-replace-objects", "worktree", "remove", "--force", attempt_root],
            capture_output=True,
            check=True,
            env=sanitized_git_env(),
        )
        return result.stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        diagnostic = getattr(exc, "stderr", b"").decode("utf-8", errors="replace").strip()
        raise GitSeamError("Git worktree rollback failed: " + (diagnostic or str(exc))) from exc
