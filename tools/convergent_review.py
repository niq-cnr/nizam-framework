#!/usr/bin/env python3
"""Deterministic, dependency-free convergent code-review engine.

Models produce observation-only trial documents. This module validates those closed
shapes and owns semantic fingerprints, lifecycle transitions, counts, verdicts,
rendering, embedded ledgers, and content-addressed replay evidence.
"""

from __future__ import annotations

import argparse
import base64
import ctypes
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA_VERSION = "1.0.0"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
REVIEW_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TOKEN_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
MARKER_RE = re.compile(r"<!-- nizam-review-ledger:([A-Za-z0-9+/=]+) -->")
SEVERITIES = ("blocker", "important", "minor")
LIFECYCLES = ("new", "persisting", "resolved", "reopened", "suppressed")
ACTIVE_LIFECYCLES = {"new", "persisting", "reopened", "suppressed"}
COUNT_KEYS = (
    "new",
    "persisting",
    "resolved",
    "reopened",
    "suppressed",
    "active_blocker",
    "active_important",
    "active_minor",
)
MAX_FINDINGS = 10000
MAX_TEXT = 20000
MAX_LINE = 1000000000
MAX_SOURCE_BYTES = 10000000
EMPTY_DIGEST = hashlib.sha256(b"").hexdigest()
RENAME_NOREPLACE = 1


class ReviewError(ValueError):
    """A deterministic validation or replay failure."""


class PublicationResult:
    """State returned after an atomic publication attempt."""

    def __init__(self, visible: bool, durable: bool, durability_error: str | None = None) -> None:
        self.visible = visible
        self.durable = durable
        self.durability_error = durability_error


def _reject_duplicates(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReviewError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json_bytes(raw: bytes, label: str) -> Any:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReviewError(f"{label}: not UTF-8: {exc}") from exc
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicates)
    except (json.JSONDecodeError, ReviewError) as exc:
        raise ReviewError(f"{label}: invalid JSON: {exc}") from exc


def read_raw_json(path: Path, label: str) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ReviewError(f"{label}: cannot read {path}: {exc}") from exc
    return parse_json_bytes(raw, label), raw


def _open_directory_nofollow(path: Path, label: str) -> int:
    """Open a directory by walking from an explicit trust anchor without links."""
    flags = (
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) |
        getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_DIRECTORY", 0)
    )
    anchor = Path("/") if path.is_absolute() else Path(".")
    parts = path.parts[1:] if path.is_absolute() else path.parts
    descriptor = os.open(anchor, flags)
    try:
        for part in parts:
            if part in ("", "."):
                continue
            if part == "..":
                raise ReviewError(f"{label}: parent traversal is not allowed in trusted-root paths")
            child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except OSError as exc:
        os.close(descriptor)
        raise ReviewError(f"{label}: cannot open directory path without following symlinks: {exc}") from exc
    except BaseException:
        os.close(descriptor)
        raise


def _read_regular_nofollow(path: Path, label: str) -> bytes:
    """Read a regular file while refusing symlinks in every path component."""
    parent_descriptor = _open_directory_nofollow(path.parent, label)
    descriptor = -1
    flags = (
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) |
        getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        if path.name in ("", ".", ".."):
            raise ReviewError(f"{label}: invalid file name")
        descriptor = os.open(path.name, flags, dir_fd=parent_descriptor)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ReviewError(f"{label}: must be a singly-linked regular non-symlink file: {path}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            return handle.read()
    except OSError as exc:
        raise ReviewError(f"{label}: cannot open regular non-symlink file {path}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent_descriptor)


def _read_relative_regular_nofollow(root: Path, relative: str, label: str) -> bytes:
    """Open every retained relative path component with no-follow semantics."""
    validate_path(relative, label)
    directory_flags = (
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) |
        getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_DIRECTORY", 0)
    )
    file_flags = (
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) |
        getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    )
    descriptors: list[int] = []
    try:
        descriptors.append(_open_directory_nofollow(root, label))
        parts = relative.split("/")
        for part in parts[:-1]:
            descriptors.append(os.open(part, directory_flags, dir_fd=descriptors[-1]))
        descriptor = os.open(parts[-1], file_flags, dir_fd=descriptors[-1])
        descriptors.append(descriptor)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ReviewError(f"{label}: must be a singly-linked retained regular non-symlink file")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            return handle.read()
    except OSError as exc:
        raise ReviewError(f"{label}: cannot read without following symlinks: {exc}") from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _write_relative_regular_nofollow(root: Path, relative: str, raw: bytes, label: str) -> None:
    """Exclusively create a regular file below root without following links."""
    validate_path(relative, label)
    directory_flags = (
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) |
        getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_DIRECTORY", 0)
    )
    file_flags = (
        os.O_WRONLY | os.O_CREAT | os.O_EXCL |
        getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptors: list[int] = []
    file_descriptor = -1
    try:
        descriptors.append(_open_directory_nofollow(root, label))
        parts = relative.split("/")
        for part in parts[:-1]:
            descriptors.append(os.open(part, directory_flags, dir_fd=descriptors[-1]))
        file_descriptor = os.open(parts[-1], file_flags, 0o600, dir_fd=descriptors[-1])
        with os.fdopen(file_descriptor, "wb", closefd=False) as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise ReviewError(f"{label}: cannot exclusively create regular non-symlink file: {exc}") from exc
    finally:
        if file_descriptor >= 0:
            os.close(file_descriptor)
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require_canonical_json(value: Any, raw: bytes, label: str) -> None:
    try:
        canonical = canonical_json_bytes(value)
    except UnicodeEncodeError as exc:
        raise ReviewError(f"{label}: contains a non-UTF-8 Unicode scalar: {exc}") from exc
    if raw != canonical:
        raise ReviewError(f"{label}: must be canonical UTF-8 JSON")


def _closed(obj: Any, required: Iterable[str], optional: Iterable[str], ctx: str) -> Mapping[str, Any]:
    if not isinstance(obj, dict):
        raise ReviewError(f"{ctx}: expected object")
    required_set = set(required)
    allowed = required_set | set(optional)
    missing = sorted(required_set - set(obj))
    extra = sorted(set(obj) - allowed)
    if missing:
        raise ReviewError(f"{ctx}: missing required field(s): {', '.join(missing)}")
    if extra:
        raise ReviewError(f"{ctx}: unknown field(s): {', '.join(extra)}")
    return obj


def _string(value: Any, ctx: str, *, minimum: int = 1, maximum: int = MAX_TEXT, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str):
        raise ReviewError(f"{ctx}: expected string")
    if not minimum <= len(value) <= maximum:
        raise ReviewError(f"{ctx}: length must be between {minimum} and {maximum}")
    if pattern is not None and pattern.fullmatch(value) is None:
        raise ReviewError(f"{ctx}: invalid format")
    return value


def _integer(value: Any, ctx: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReviewError(f"{ctx}: expected integer")
    if not minimum <= value <= maximum:
        raise ReviewError(f"{ctx}: must be between {minimum} and {maximum}")
    return value


def _enum(value: Any, choices: Sequence[str], ctx: str) -> str:
    if value not in choices:
        raise ReviewError(f"{ctx}: expected one of {', '.join(choices)}")
    return str(value)


def _safe_slash_path(value: Any, ctx: str, *, maximum: int, minimum_segments: int) -> str:
    path = _string(value, ctx, maximum=maximum)
    if path.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", path):
        raise ReviewError(f"{ctx}: absolute paths are not allowed")
    if "\\" in path:
        raise ReviewError(f"{ctx}: backslash is not allowed")
    if any(unicodedata.category(character) == "Cc" for character in path):
        raise ReviewError(f"{ctx}: control characters are not allowed")
    parts = path.split("/")
    if len(parts) < minimum_segments or any(part in ("", ".", "..") for part in parts):
        raise ReviewError(f"{ctx}: must be a normalized slash-separated relative identity")
    return path


def validate_path(value: Any, ctx: str) -> str:
    return _safe_slash_path(value, ctx, maximum=1024, minimum_segments=1)


def validate_repository(value: Any, ctx: str) -> str:
    return _safe_slash_path(value, ctx, maximum=512, minimum_segments=2)


def _digest(value: Any, ctx: str) -> str:
    digest = _string(value, ctx, minimum=64, maximum=64, pattern=DIGEST_RE)
    if digest == "0" * 64:
        raise ReviewError(f"{ctx}: all-zero digest is not a valid content binding")
    return digest


def _nullable_digest(value: Any, ctx: str) -> str | None:
    if value is None:
        return None
    return _digest(value, ctx)


def _nullable_sha(value: Any, ctx: str) -> str | None:
    if value is None:
        return None
    return _string(value, ctx, minimum=40, maximum=40, pattern=SHA_RE)


def _git_object_id(kind: str, raw: bytes) -> str:
    return hashlib.sha1(f"{kind} {len(raw)}\0".encode("ascii") + raw).hexdigest()


def _git_tree_id(entries: Sequence[Mapping[str, Any]]) -> str:
    """Reconstruct a Git SHA-1 tree object from a complete flat blob manifest."""
    root: dict[str, Any] = {}
    for entry in entries:
        cursor = root
        parts = entry["path"].split("/")
        for part in parts[:-1]:
            existing = cursor.setdefault(part, {})
            if not isinstance(existing, dict) or "__leaf__" in existing:
                raise ReviewError(f"packet.scope_commitment.entries: file/directory collision at {entry['path']}")
            cursor = existing
        if parts[-1] in cursor:
            raise ReviewError(f"packet.scope_commitment.entries: duplicate or prefix collision at {entry['path']}")
        cursor[parts[-1]] = {"__leaf__": entry}

    def emit(node: Mapping[str, Any]) -> str:
        records: list[tuple[bytes, bytes]] = []
        for name, value in node.items():
            encoded = name.encode("utf-8")
            if "__leaf__" in value:
                entry = value["__leaf__"]
                record = entry["mode"].encode("ascii") + b" " + encoded + b"\0" + bytes.fromhex(entry["object_id"])
                records.append((encoded, record))
            else:
                object_id = emit(value)
                record = b"40000 " + encoded + b"\0" + bytes.fromhex(object_id)
                records.append((encoded + b"/", record))
        raw = b"".join(record for _, record in sorted(records, key=lambda pair: pair[0]))
        return _git_object_id("tree", raw)

    return emit(root)


def validate_packet_schema_stage(packet: Any) -> Mapping[str, Any]:
    """Implement the closed JSON-Schema stage; cross-item relations are separate."""
    obj = _closed(
        packet,
        (
            "schema_version", "review_id", "repository", "mode", "base_sha", "head_sha",
            "scope_commitment", "delta", "review_files",
        ),
        (),
        "packet",
    )
    if obj["schema_version"] != SCHEMA_VERSION:
        raise ReviewError(f"packet.schema_version: expected {SCHEMA_VERSION}")
    _string(obj["review_id"], "packet.review_id", pattern=REVIEW_ID_RE, maximum=128)
    validate_repository(obj["repository"], "packet.repository")
    _enum(obj["mode"], ("ordinary", "full_audit"), "packet.mode")
    _string(obj["base_sha"], "packet.base_sha", minimum=40, maximum=40, pattern=SHA_RE)
    _string(obj["head_sha"], "packet.head_sha", minimum=40, maximum=40, pattern=SHA_RE)
    commitment = obj["scope_commitment"]
    if commitment is not None:
        commitment = _closed(
            commitment,
            ("object_format", "commit_content", "root_tree", "manifest_digest", "entries"),
            (),
            "packet.scope_commitment",
        )
        if commitment["object_format"] != "git-sha1":
            raise ReviewError("packet.scope_commitment.object_format: expected git-sha1")
        _string(commitment["commit_content"], "packet.scope_commitment.commit_content", maximum=1000000)
        _string(commitment["root_tree"], "packet.scope_commitment.root_tree", minimum=40, maximum=40, pattern=SHA_RE)
        _digest(commitment["manifest_digest"], "packet.scope_commitment.manifest_digest")
        entries = commitment["entries"]
        if not isinstance(entries, list) or len(entries) > 100000:
            raise ReviewError("packet.scope_commitment.entries: expected array with at most 100000 entries")
        for index, item in enumerate(entries):
            entry = _closed(item, ("path", "mode", "object_id"), (), f"packet.scope_commitment.entries[{index}]")
            validate_path(entry["path"], f"packet.scope_commitment.entries[{index}].path")
            _enum(entry["mode"], ("100644", "100755", "120000"), f"packet.scope_commitment.entries[{index}].mode")
            _string(entry["object_id"], f"packet.scope_commitment.entries[{index}].object_id", minimum=40, maximum=40, pattern=SHA_RE)
    review_files = obj["review_files"]
    if not isinstance(review_files, list) or len(review_files) > 100000:
        raise ReviewError("packet.review_files: expected array with at most 100000 entries")
    for index, item in enumerate(review_files):
        entry = _closed(item, ("path", "content_digest", "content"), (), f"packet.review_files[{index}]")
        validate_path(entry["path"], f"packet.review_files[{index}].path")
        _digest(entry["content_digest"], f"packet.review_files[{index}].content_digest")
        if entry["content"] is not None:
            content = _string(entry["content"], f"packet.review_files[{index}].content", minimum=0, maximum=MAX_SOURCE_BYTES)
            try:
                content_raw = content.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ReviewError(f"packet.review_files[{index}].content: not valid UTF-8 text: {exc}") from exc
            if len(content_raw) > MAX_SOURCE_BYTES:
                raise ReviewError(f"packet.review_files[{index}].content: exceeds {MAX_SOURCE_BYTES} UTF-8 bytes")
    if not isinstance(obj["delta"], list) or len(obj["delta"]) > 100000:
        raise ReviewError("packet.delta: expected array with at most 100000 entries")
    for index, item in enumerate(obj["delta"]):
        entry = _closed(
            item, ("path", "old_digest", "old_content", "old_mode", "new_digest", "new_mode"), (),
            f"packet.delta[{index}]",
        )
        validate_path(entry["path"], f"packet.delta[{index}].path")
        old_digest = _nullable_digest(entry["old_digest"], f"packet.delta[{index}].old_digest")
        old_mode = entry["old_mode"]
        new_digest = _nullable_digest(entry["new_digest"], f"packet.delta[{index}].new_digest")
        new_mode = entry["new_mode"]
        if (old_digest is None) != (entry["old_content"] is None) or (old_digest is None) != (old_mode is None):
            raise ReviewError(f"packet.delta[{index}]: old content/mode presence must match old digest")
        if (new_digest is None) != (new_mode is None):
            raise ReviewError(f"packet.delta[{index}]: new mode presence must match new digest")
        if old_mode is not None:
            _enum(old_mode, ("100644", "100755", "120000"), f"packet.delta[{index}].old_mode")
        if new_mode is not None:
            _enum(new_mode, ("100644", "100755", "120000"), f"packet.delta[{index}].new_mode")
        if entry["old_content"] is not None:
            old_content = _string(entry["old_content"], f"packet.delta[{index}].old_content", minimum=0, maximum=MAX_SOURCE_BYTES)
            try:
                old_raw = old_content.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ReviewError(f"packet.delta[{index}].old_content: not valid UTF-8 text: {exc}") from exc
            if len(old_raw) > MAX_SOURCE_BYTES:
                raise ReviewError(f"packet.delta[{index}].old_content: exceeds {MAX_SOURCE_BYTES} UTF-8 bytes")
    return obj


def validate_packet_relations(packet: Mapping[str, Any]) -> None:
    """Mandatory relational stage beyond pure Draft 2020-12 JSON Schema."""
    source_by_path: dict[str, Mapping[str, Any]] = {}
    for index, entry in enumerate(packet["review_files"]):
        path = entry["path"]
        if path in source_by_path:
            raise ReviewError(f"packet.review_files[{index}].path: duplicate path {path}")
        content_raw = b"" if entry["content"] is None else entry["content"].encode("utf-8")
        if sha256(content_raw) != entry["content_digest"]:
            raise ReviewError(f"packet.review_files[{index}].content_digest: does not match content bytes")
        source_by_path[path] = entry

    seen: set[str] = set()
    for index, entry in enumerate(packet["delta"]):
        path = entry["path"]
        old = entry["old_digest"]
        new = entry["new_digest"]
        old_mode = entry["old_mode"]
        new_mode = entry["new_mode"]
        if old is None and new is None:
            raise ReviewError(f"packet.delta[{index}]: old_digest and new_digest cannot both be null")
        if old == new and old_mode == new_mode:
            raise ReviewError(f"packet.delta[{index}]: digests and modes must describe an actual delta")
        if path in seen:
            raise ReviewError(f"packet.delta[{index}].path: duplicate path {path}")
        seen.add(path)
        old_content = entry["old_content"]
        if (old is None) != (old_content is None):
            raise ReviewError(f"packet.delta[{index}]: old_content presence must match old_digest")
        if old_content is not None and sha256(old_content.encode("utf-8")) != old:
            raise ReviewError(f"packet.delta[{index}].old_digest: does not match authenticated old_content bytes")
        source = source_by_path.get(path)
        if new is None:
            if source is None or source["content"] is not None or source["content_digest"] != EMPTY_DIGEST:
                raise ReviewError(f"packet.delta[{index}]: deleted path requires an authenticated absence tombstone")
        else:
            if source is None or source["content"] is None:
                raise ReviewError(f"packet.delta[{index}]: current content is missing from packet.review_files")
            if source["content_digest"] != new:
                raise ReviewError(f"packet.delta[{index}].new_digest: does not match current review-file content")

    commitment = packet["scope_commitment"]
    if packet["mode"] == "ordinary":
        if commitment is not None:
            raise ReviewError("packet.scope_commitment: must be null in ordinary mode")
        return
    if commitment is None:
        raise ReviewError("packet.scope_commitment: full_audit requires an authenticated complete Git tree")
    entries = commitment["entries"]
    paths = [entry["path"] for entry in entries]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ReviewError("packet.scope_commitment.entries: paths must be unique and sorted")
    if sha256(canonical_json_bytes(entries)) != commitment["manifest_digest"]:
        raise ReviewError("packet.scope_commitment.manifest_digest: does not match canonical entries")
    if _git_tree_id(entries) != commitment["root_tree"]:
        raise ReviewError("packet.scope_commitment.root_tree: does not match complete manifest")
    commit_raw = commitment["commit_content"].encode("utf-8")
    if _git_object_id("commit", commit_raw) != packet["head_sha"]:
        raise ReviewError("packet.scope_commitment.commit_content: does not authenticate packet.head_sha")
    header_block = commitment["commit_content"].split("\n\n", 1)[0]
    tree_lines = [line for line in header_block.splitlines() if line.startswith("tree ")]
    if tree_lines != [f"tree {commitment['root_tree']}"]:
        raise ReviewError("packet.scope_commitment.commit_content: header must bind exactly one valid root tree")
    manifest_by_path = {entry["path"]: entry for entry in entries}
    present_paths = {path for path, source in source_by_path.items() if source["content"] is not None}
    if set(manifest_by_path) != present_paths:
        raise ReviewError("packet.scope_commitment.entries: must equal the complete present review_files universe")
    for path, entry in manifest_by_path.items():
        source = source_by_path[path]
        if _git_object_id("blob", source["content"].encode("utf-8")) != entry["object_id"]:
            raise ReviewError(f"packet.scope_commitment.entries: Git blob does not match authenticated bytes for {path}")
    for index, delta_entry in enumerate(packet["delta"]):
        if delta_entry["new_digest"] is not None:
            committed = manifest_by_path[delta_entry["path"]]
            if delta_entry["new_mode"] != committed["mode"]:
                raise ReviewError(f"packet.delta[{index}].new_mode: does not match authenticated head-tree mode")


def validate_packet(packet: Any) -> Mapping[str, Any]:
    obj = validate_packet_schema_stage(packet)
    validate_packet_relations(obj)
    return obj


def _packet_sources(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {entry["path"]: entry for entry in packet["review_files"]}


def validate_candidate(finding: Any, ctx: str) -> Mapping[str, Any]:
    obj = _closed(finding, ("severity", "category", "path", "symbol", "rule", "title", "description"), (), ctx)
    _enum(obj["severity"], SEVERITIES, f"{ctx}.severity")
    _string(obj["category"], f"{ctx}.category", pattern=TOKEN_RE, maximum=64)
    validate_path(obj["path"], f"{ctx}.path")
    _string(obj["symbol"], f"{ctx}.symbol", maximum=256)
    _string(obj["rule"], f"{ctx}.rule", pattern=TOKEN_RE, maximum=64)
    _string(obj["title"], f"{ctx}.title", maximum=500)
    _string(obj["description"], f"{ctx}.description", maximum=MAX_TEXT)
    return obj


def validate_evidence(evidence: Any, ctx: str, *, ledger: bool = False) -> Mapping[str, Any]:
    required = ("path", "start_line", "end_line", "excerpt", "content_digest")
    if ledger:
        required = ("trial_number",) + required
    obj = _closed(evidence, required, (), ctx)
    if ledger:
        _integer(obj["trial_number"], f"{ctx}.trial_number", 1, 3)
    validate_path(obj["path"], f"{ctx}.path")
    start = _integer(obj["start_line"], f"{ctx}.start_line", 0, MAX_LINE)
    end = _integer(obj["end_line"], f"{ctx}.end_line", 0, MAX_LINE)
    if end < start:
        raise ReviewError(f"{ctx}: end_line precedes start_line")
    _string(obj["excerpt"], f"{ctx}.excerpt", minimum=0, maximum=4000)
    _digest(obj["content_digest"], f"{ctx}.content_digest")
    return obj


def validate_current_evidence(evidence: Mapping[str, Any], packet: Mapping[str, Any], ctx: str) -> None:
    source = _packet_sources(packet).get(evidence["path"])
    if source is None:
        raise ReviewError(f"{ctx}.path: is not in the authenticated current-head review universe")
    if evidence["content_digest"] != source["content_digest"]:
        raise ReviewError(f"{ctx}.content_digest: does not match authenticated current-head bytes")
    if source["content"] is None:
        if evidence["start_line"] != 0 or evidence["end_line"] != 0 or evidence["excerpt"] != "":
            raise ReviewError(f"{ctx}: absence evidence requires line range 0-0 and an empty excerpt")
        return
    if evidence["start_line"] == 0 or evidence["end_line"] == 0:
        raise ReviewError(f"{ctx}: present content requires positive line numbers")
    lines = source["content"].splitlines()
    if evidence["end_line"] > len(lines):
        raise ReviewError(f"{ctx}: line range exceeds authenticated current-head content")
    expected = "\n".join(lines[evidence["start_line"] - 1:evidence["end_line"]])
    if evidence["excerpt"] != expected:
        raise ReviewError(f"{ctx}.excerpt: does not match the authenticated line range")


def semantic_fingerprint(repository: str, finding: Mapping[str, Any]) -> str:
    validate_candidate(finding, "finding")
    descriptor = {
        "category": finding["category"].strip().casefold(),
        "path": finding["path"],
        "repository": repository,
        "rule": finding["rule"].strip().casefold(),
        "symbol": " ".join(finding["symbol"].split()),
    }
    return sha256(canonical_json_bytes(descriptor))


def validate_trial(trial: Any, packet: Mapping[str, Any], packet_digest: str, ctx: str) -> Mapping[str, Any]:
    obj = _closed(trial, ("schema_version", "review_id", "trial_number", "packet_digest", "head_sha", "observations"), (), ctx)
    if obj["schema_version"] != SCHEMA_VERSION:
        raise ReviewError(f"{ctx}.schema_version: expected {SCHEMA_VERSION}")
    if obj["review_id"] != packet["review_id"]:
        raise ReviewError(f"{ctx}.review_id: does not match packet")
    _integer(obj["trial_number"], f"{ctx}.trial_number", 1, 3)
    if obj["packet_digest"] != packet_digest:
        raise ReviewError(f"{ctx}.packet_digest: does not bind the exact packet bytes")
    if obj["head_sha"] != packet["head_sha"]:
        raise ReviewError(f"{ctx}.head_sha: does not bind the current head")
    observations = obj["observations"]
    if not isinstance(observations, list) or len(observations) > MAX_FINDINGS:
        raise ReviewError(f"{ctx}.observations: expected array with at most {MAX_FINDINGS} entries")
    seen: set[str] = set()
    for index, observation in enumerate(observations):
        prefix = f"{ctx}.observations[{index}]"
        item = _closed(observation, ("action", "finding", "evidence"), (), prefix)
        _enum(item["action"], ("active", "resolved"), f"{prefix}.action")
        finding = validate_candidate(item["finding"], f"{prefix}.finding")
        evidence = item["evidence"]
        if not isinstance(evidence, list) or not 1 <= len(evidence) <= 100:
            raise ReviewError(f"{prefix}.evidence: expected 1 to 100 evidence entries")
        for evidence_index, evidence_item in enumerate(evidence):
            evidence_ctx = f"{prefix}.evidence[{evidence_index}]"
            validated = validate_evidence(evidence_item, evidence_ctx)
            validate_current_evidence(validated, packet, evidence_ctx)
        if not any(evidence_item["path"] == finding["path"] for evidence_item in evidence):
            raise ReviewError(f"{prefix}.evidence: must include authenticated evidence at the finding path")
        fingerprint = semantic_fingerprint(packet["repository"], finding)
        if fingerprint in seen:
            raise ReviewError(f"{prefix}: duplicate semantic finding in one trial")
        seen.add(fingerprint)
    return obj


def validate_suppression(record: Any, repository: str, ctx: str) -> Mapping[str, Any]:
    obj = _closed(record, ("schema_version", "repository", "fingerprint", "authorized_by", "authorization_ref", "authorized_at", "reason"), (), ctx)
    if obj["schema_version"] != SCHEMA_VERSION:
        raise ReviewError(f"{ctx}.schema_version: expected {SCHEMA_VERSION}")
    if obj["repository"] != repository:
        raise ReviewError(f"{ctx}.repository: does not match packet")
    _digest(obj["fingerprint"], f"{ctx}.fingerprint")
    _string(obj["authorized_by"], f"{ctx}.authorized_by", maximum=256)
    _string(obj["authorization_ref"], f"{ctx}.authorization_ref", maximum=1024)
    _string(obj["authorized_at"], f"{ctx}.authorized_at", maximum=64, pattern=DATETIME_RE)
    _string(obj["reason"], f"{ctx}.reason", maximum=4000)
    return obj


def validate_consensus(value: Any, ctx: str) -> Mapping[str, Any]:
    obj = _closed(value, ("active_trials", "resolved_trials"), (), ctx)
    for key in ("active_trials", "resolved_trials"):
        trials = obj[key]
        if not isinstance(trials, list) or len(trials) > 3:
            raise ReviewError(f"{ctx}.{key}: expected array with at most three entries")
        normalized = [_integer(item, f"{ctx}.{key}", 1, 3) for item in trials]
        if normalized != sorted(set(normalized)):
            raise ReviewError(f"{ctx}.{key}: trials must be unique and sorted")
    if set(obj["active_trials"]) & set(obj["resolved_trials"]):
        raise ReviewError(f"{ctx}: one trial cannot report both active and resolved")
    return obj


def validate_ledger_suppression(value: Any, ctx: str) -> Mapping[str, Any] | None:
    if value is None:
        return None
    obj = _closed(value, ("record_digest", "authorized_by", "authorization_ref", "authorized_at", "reason"), (), ctx)
    _digest(obj["record_digest"], f"{ctx}.record_digest")
    _string(obj["authorized_by"], f"{ctx}.authorized_by", maximum=256)
    _string(obj["authorization_ref"], f"{ctx}.authorization_ref", maximum=1024)
    _string(obj["authorized_at"], f"{ctx}.authorized_at", maximum=64, pattern=DATETIME_RE)
    _string(obj["reason"], f"{ctx}.reason", maximum=4000)
    return obj


def calculate_counts(findings: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {key: 0 for key in COUNT_KEYS}
    for finding in findings:
        lifecycle = finding["lifecycle"]
        counts[lifecycle] += 1
        if lifecycle in ACTIVE_LIFECYCLES and lifecycle != "suppressed":
            counts[f"active_{finding['severity']}"] += 1
    return counts


def validate_ledger(ledger: Any, ctx: str = "ledger") -> Mapping[str, Any]:
    obj = _closed(
        ledger,
        (
            "schema_version", "review_id", "repository", "mode", "base_sha", "head_sha",
            "packet_digest", "prior_ledger_digest", "trial_digests", "findings", "counts", "verdict",
        ),
        (),
        ctx,
    )
    if obj["schema_version"] != SCHEMA_VERSION:
        raise ReviewError(f"{ctx}.schema_version: expected {SCHEMA_VERSION}")
    _string(obj["review_id"], f"{ctx}.review_id", pattern=REVIEW_ID_RE, maximum=128)
    validate_repository(obj["repository"], f"{ctx}.repository")
    _enum(obj["mode"], ("ordinary", "full_audit"), f"{ctx}.mode")
    _string(obj["base_sha"], f"{ctx}.base_sha", minimum=40, maximum=40, pattern=SHA_RE)
    _string(obj["head_sha"], f"{ctx}.head_sha", minimum=40, maximum=40, pattern=SHA_RE)
    _digest(obj["packet_digest"], f"{ctx}.packet_digest")
    _nullable_digest(obj["prior_ledger_digest"], f"{ctx}.prior_ledger_digest")
    digests = obj["trial_digests"]
    if not isinstance(digests, list) or len(digests) != 3:
        raise ReviewError(f"{ctx}.trial_digests: expected exactly three digests")
    for index, digest in enumerate(digests):
        _digest(digest, f"{ctx}.trial_digests[{index}]")
    if len(set(digests)) != 3:
        raise ReviewError(f"{ctx}.trial_digests: digests must be unique")
    findings = obj["findings"]
    if not isinstance(findings, list) or len(findings) > MAX_FINDINGS:
        raise ReviewError(f"{ctx}.findings: expected array with at most {MAX_FINDINGS} entries")
    seen: set[str] = set()
    fingerprints: list[str] = []
    for index, finding in enumerate(findings):
        prefix = f"{ctx}.findings[{index}]"
        item = _closed(
            finding,
            (
                "fingerprint", "severity", "category", "path", "symbol", "rule", "title", "description",
                "lifecycle", "first_seen_head", "last_seen_head", "resolved_head", "evidence",
                "resolution_evidence", "consensus", "suppression",
            ),
            (),
            prefix,
        )
        candidate = {key: item[key] for key in ("severity", "category", "path", "symbol", "rule", "title", "description")}
        validate_candidate(candidate, prefix)
        fingerprint = _digest(item["fingerprint"], f"{prefix}.fingerprint")
        if fingerprint != semantic_fingerprint(obj["repository"], candidate):
            raise ReviewError(f"{prefix}.fingerprint: does not match semantic fields")
        if fingerprint in seen:
            raise ReviewError(f"{prefix}.fingerprint: duplicate")
        seen.add(fingerprint)
        fingerprints.append(fingerprint)
        lifecycle = _enum(item["lifecycle"], LIFECYCLES, f"{prefix}.lifecycle")
        _string(item["first_seen_head"], f"{prefix}.first_seen_head", minimum=40, maximum=40, pattern=SHA_RE)
        _string(item["last_seen_head"], f"{prefix}.last_seen_head", minimum=40, maximum=40, pattern=SHA_RE)
        resolved = _nullable_sha(item["resolved_head"], f"{prefix}.resolved_head")
        if obj["prior_ledger_digest"] is None:
            if lifecycle not in ("new", "suppressed"):
                raise ReviewError(f"{prefix}.lifecycle: initial ledger permits only new or suppressed findings")
            if item["first_seen_head"] != obj["head_sha"]:
                raise ReviewError(f"{prefix}.first_seen_head: initial finding must equal ledger.head_sha")
            if item["last_seen_head"] != obj["head_sha"]:
                raise ReviewError(f"{prefix}.last_seen_head: initial finding must equal ledger.head_sha")
        if lifecycle == "resolved" and resolved is None:
            raise ReviewError(f"{prefix}.resolved_head: required for resolved lifecycle")
        if lifecycle != "resolved" and resolved is not None:
            raise ReviewError(f"{prefix}.resolved_head: must be null for active lifecycle")
        evidence_trials: dict[str, set[int]] = {}
        for evidence_key in ("evidence", "resolution_evidence"):
            evidence = item[evidence_key]
            if not isinstance(evidence, list) or len(evidence) > 300:
                raise ReviewError(f"{prefix}.{evidence_key}: expected array with at most 300 entries")
            evidence_trials[evidence_key] = set()
            for evidence_index, evidence_item in enumerate(evidence):
                validated_evidence = validate_evidence(evidence_item, f"{prefix}.{evidence_key}[{evidence_index}]", ledger=True)
                evidence_trials[evidence_key].add(validated_evidence["trial_number"])
        consensus = validate_consensus(item["consensus"], f"{prefix}.consensus")
        active_trials = consensus["active_trials"]
        resolved_trials = consensus["resolved_trials"]
        if evidence_trials["evidence"] != set(active_trials):
            raise ReviewError(f"{prefix}.evidence: trial attribution must exactly match active consensus")
        if evidence_trials["resolution_evidence"] != set(resolved_trials):
            raise ReviewError(f"{prefix}.resolution_evidence: trial attribution must exactly match resolved consensus")
        if lifecycle == "new" and len(active_trials) < 2:
            raise ReviewError(f"{prefix}.lifecycle: new requires 2-of-3 active consensus")
        if lifecycle == "reopened":
            if obj["prior_ledger_digest"] is None or len(active_trials) < 2:
                raise ReviewError(f"{prefix}.lifecycle: reopened requires a prior ledger and 2-of-3 active consensus")
        if lifecycle == "persisting":
            if obj["prior_ledger_digest"] is None:
                raise ReviewError(f"{prefix}.lifecycle: persisting requires a prior ledger")
            if len(resolved_trials) >= 2:
                raise ReviewError(f"{prefix}.lifecycle: persisting cannot carry 2-of-3 resolved consensus")
        if lifecycle == "resolved":
            if len(active_trials) >= 2:
                raise ReviewError(f"{prefix}.lifecycle: resolved finding cannot carry 2-of-3 active consensus")
            if resolved == obj["head_sha"]:
                if obj["prior_ledger_digest"] is None:
                    raise ReviewError(f"{prefix}.lifecycle: current-head resolution requires a prior ledger")
                if len(resolved_trials) < 2:
                    raise ReviewError(f"{prefix}.lifecycle: current-head resolution requires 2-of-3 resolved consensus")
                if not item["resolution_evidence"]:
                    raise ReviewError(f"{prefix}.resolution_evidence: current-head resolution requires evidence")
        suppression = validate_ledger_suppression(item["suppression"], f"{prefix}.suppression")
        if lifecycle == "suppressed":
            if suppression is None:
                raise ReviewError(f"{prefix}.suppression: required for suppressed lifecycle")
            if len(resolved_trials) >= 2:
                raise ReviewError(f"{prefix}.lifecycle: suppressed finding cannot carry 2-of-3 resolved consensus")
            if obj["prior_ledger_digest"] is None and len(active_trials) < 2:
                raise ReviewError(f"{prefix}.lifecycle: initial suppressed finding requires 2-of-3 active consensus")
        elif suppression is not None:
            raise ReviewError(f"{prefix}.suppression: only valid for suppressed lifecycle")
        if lifecycle == "new" and not item["evidence"]:
            raise ReviewError(f"{prefix}.evidence: new finding requires active evidence")
        if lifecycle == "reopened" and not item["evidence"]:
            raise ReviewError(f"{prefix}.evidence: reopened finding requires active evidence")
    if fingerprints != sorted(fingerprints):
        raise ReviewError(f"{ctx}.findings: must be sorted by fingerprint")
    counts = _closed(obj["counts"], COUNT_KEYS, (), f"{ctx}.counts")
    for key in COUNT_KEYS:
        _integer(counts[key], f"{ctx}.counts.{key}", 0, MAX_FINDINGS)
    expected_counts = calculate_counts(findings)
    if dict(counts) != expected_counts:
        raise ReviewError(f"{ctx}.counts: do not match finding lifecycles and severities")
    verdict = _enum(obj["verdict"], ("approve", "request_changes"), f"{ctx}.verdict")
    expected_verdict = "request_changes" if counts["active_blocker"] or counts["active_important"] else "approve"
    if verdict != expected_verdict:
        raise ReviewError(f"{ctx}.verdict: inconsistent with active blocker/important counts")
    return obj


def _ledger_evidence(trial_number: int, items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result = [{"trial_number": trial_number, **dict(item)} for item in items]
    return sorted(result, key=lambda item: canonical_json_bytes(item))


def _dedupe_sorted(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_bytes: dict[bytes, dict[str, Any]] = {}
    for item in items:
        value = dict(item)
        by_bytes[canonical_json_bytes(value)] = value
    return [by_bytes[key] for key in sorted(by_bytes)]


def _representative(reports: Sequence[tuple[int, Mapping[str, Any], Sequence[Mapping[str, Any]]]]) -> dict[str, Any]:
    candidates = [dict(report[1]) for report in reports]
    chosen = dict(sorted(candidates, key=canonical_json_bytes)[0])
    rank = {"minor": 0, "important": 1, "blocker": 2}
    chosen["severity"] = max((candidate["severity"] for candidate in candidates), key=lambda value: rank[value])
    return chosen


def _prior_candidate(finding: Mapping[str, Any]) -> dict[str, Any]:
    return {key: finding[key] for key in ("severity", "category", "path", "symbol", "rule", "title", "description")}


def _prior_candidate_with_current_severity(
    finding: Mapping[str, Any],
    active_reports: Sequence[tuple[int, Mapping[str, Any], Sequence[Mapping[str, Any]]]],
) -> dict[str, Any]:
    """Preserve stable prior prose while never downgrading current risk.

    Severity is deliberately excluded from the semantic fingerprint. When the
    same finding persists or reopens, the current independent observations may
    therefore report a higher severity than the historical ledger. The gate
    must use the most severe value across both sources.
    """
    candidate = _prior_candidate(finding)
    if active_reports:
        rank = {"minor": 0, "important": 1, "blocker": 2}
        candidate["severity"] = max(
            [candidate["severity"], *(report[1]["severity"] for report in active_reports)],
            key=lambda value: rank[value],
        )
    return candidate


def converge_documents(
    packet: Mapping[str, Any],
    packet_digest: str,
    trials: Sequence[Mapping[str, Any]],
    trial_digests: Mapping[int, str],
    prior: Mapping[str, Any] | None,
    prior_digest: str | None,
    suppression_inputs: Sequence[tuple[Mapping[str, Any], str]],
) -> dict[str, Any]:
    validate_packet(packet)
    prior_by_fp: dict[str, Mapping[str, Any]] = {}
    if prior is not None:
        validate_ledger(prior, "prior_ledger")
        if prior["repository"] != packet["repository"] or prior["review_id"] != packet["review_id"]:
            raise ReviewError("prior_ledger: repository and review_id must match packet")
        if prior["head_sha"] != packet["base_sha"]:
            raise ReviewError("prior_ledger.head_sha: must equal packet.base_sha")
        prior_by_fp = {finding["fingerprint"]: finding for finding in prior["findings"]}
    if (prior is None) != (prior_digest is None):
        raise ReviewError("prior ledger digest binding is incomplete")

    if len(trials) != 3:
        raise ReviewError("converge requires exactly three trials")
    for index, trial in enumerate(trials):
        validate_trial(trial, packet, packet_digest, f"trial[{index}]")
    ordered_trials = sorted(trials, key=lambda item: item["trial_number"])
    if [item["trial_number"] for item in ordered_trials] != [1, 2, 3]:
        raise ReviewError("trials must have unique trial_number values 1, 2, and 3")

    observations: dict[str, dict[str, list[tuple[int, Mapping[str, Any], Sequence[Mapping[str, Any]]]]]] = {}
    delta_paths = {item["path"] for item in packet["delta"]}
    added_by_digest = {
        item["new_digest"] for item in packet["delta"]
        if item["old_digest"] is None and item["new_digest"] is not None
    }
    rename_only_paths = {
        item["path"] for item in packet["delta"]
        if item["new_digest"] is None and item["old_digest"] in added_by_digest
    }
    for trial in ordered_trials:
        trial_number = trial["trial_number"]
        for observation in trial["observations"]:
            candidate = observation["finding"]
            fingerprint = semantic_fingerprint(packet["repository"], candidate)
            if (
                observation["action"] == "active"
                and fingerprint not in prior_by_fp
                and packet["mode"] == "ordinary"
                and candidate["path"] not in delta_paths
            ):
                raise ReviewError(
                    f"trial {trial_number}: ordinary-mode new candidate {fingerprint} is outside packet.delta ({candidate['path']})"
                )
            if observation["action"] == "resolved" and candidate["path"] in rename_only_paths:
                raise ReviewError(
                    f"trial {trial_number}: rename alone cannot resolve finding {fingerprint} ({candidate['path']})"
                )
            grouped = observations.setdefault(fingerprint, {"active": [], "resolved": []})
            grouped[observation["action"]].append((trial_number, candidate, observation["evidence"]))

    suppressions: dict[str, dict[str, Any]] = {}
    for index, (record, record_digest) in enumerate(suppression_inputs):
        validate_suppression(record, packet["repository"], f"suppression[{index}]")
        _digest(record_digest, f"suppression[{index}].record_digest")
        fingerprint = record["fingerprint"]
        if fingerprint in suppressions:
            raise ReviewError(f"suppression: duplicate record for {fingerprint}")
        suppressions[fingerprint] = {
            "record_digest": record_digest,
            "authorized_by": record["authorized_by"],
            "authorization_ref": record["authorization_ref"],
            "authorized_at": record["authorized_at"],
            "reason": record["reason"],
        }

    output: dict[str, dict[str, Any]] = {}
    all_fingerprints = sorted(set(prior_by_fp) | set(observations))
    for fingerprint in all_fingerprints:
        prior_finding = prior_by_fp.get(fingerprint)
        grouped = observations.get(fingerprint, {"active": [], "resolved": []})
        active_reports = grouped["active"]
        resolved_reports = grouped["resolved"]
        active_trials = sorted(report[0] for report in active_reports)
        resolved_trials = sorted(report[0] for report in resolved_reports)

        if prior_finding is None:
            if len(active_trials) < 2:
                continue
            candidate = _representative(active_reports)
            evidence = _dedupe_sorted(
                item
                for trial_number, _, items in active_reports
                for item in _ledger_evidence(trial_number, items)
            )
            finding = {
                "fingerprint": fingerprint,
                **candidate,
                "lifecycle": "new",
                "first_seen_head": packet["head_sha"],
                "last_seen_head": packet["head_sha"],
                "resolved_head": None,
                "evidence": evidence,
                "resolution_evidence": _dedupe_sorted(
                    item
                    for trial_number, _, items in resolved_reports
                    for item in _ledger_evidence(trial_number, items)
                ),
                "consensus": {"active_trials": active_trials, "resolved_trials": resolved_trials},
                "suppression": None,
            }
        else:
            candidate = _prior_candidate_with_current_severity(prior_finding, active_reports)
            if prior_finding["lifecycle"] in ACTIVE_LIFECYCLES:
                if len(resolved_trials) >= 2:
                    resolution_evidence = _dedupe_sorted(
                        item
                        for trial_number, _, items in resolved_reports
                        for item in _ledger_evidence(trial_number, items)
                    )
                    finding = {
                        "fingerprint": fingerprint,
                        **candidate,
                        "lifecycle": "resolved",
                        "first_seen_head": prior_finding["first_seen_head"],
                        "last_seen_head": prior_finding["last_seen_head"],
                        "resolved_head": packet["head_sha"],
                        "evidence": _dedupe_sorted(
                            item
                            for trial_number, _, items in active_reports
                            for item in _ledger_evidence(trial_number, items)
                        ),
                        "resolution_evidence": resolution_evidence,
                        "consensus": {"active_trials": active_trials, "resolved_trials": resolved_trials},
                        "suppression": None,
                    }
                else:
                    current_evidence = _dedupe_sorted(
                        item
                        for trial_number, _, items in active_reports
                        for item in _ledger_evidence(trial_number, items)
                    )
                    current_resolution_evidence = _dedupe_sorted(
                        item
                        for trial_number, _, items in resolved_reports
                        for item in _ledger_evidence(trial_number, items)
                    )
                    finding = {
                        "fingerprint": fingerprint,
                        **candidate,
                        "lifecycle": "persisting",
                        "first_seen_head": prior_finding["first_seen_head"],
                        "last_seen_head": packet["head_sha"],
                        "resolved_head": None,
                        "evidence": current_evidence,
                        "resolution_evidence": current_resolution_evidence,
                        "consensus": {"active_trials": active_trials, "resolved_trials": resolved_trials},
                        "suppression": prior_finding["suppression"],
                    }
            else:
                if len(active_trials) >= 2:
                    current_evidence = _dedupe_sorted(
                        item
                        for trial_number, _, items in active_reports
                        for item in _ledger_evidence(trial_number, items)
                    )
                    finding = {
                        "fingerprint": fingerprint,
                        **candidate,
                        "lifecycle": "reopened",
                        "first_seen_head": prior_finding["first_seen_head"],
                        "last_seen_head": packet["head_sha"],
                        "resolved_head": None,
                        "evidence": current_evidence,
                        "resolution_evidence": _dedupe_sorted(
                            item
                            for trial_number, _, items in resolved_reports
                            for item in _ledger_evidence(trial_number, items)
                        ),
                        "consensus": {"active_trials": active_trials, "resolved_trials": resolved_trials},
                        "suppression": prior_finding["suppression"],
                    }
                else:
                    current_evidence = _dedupe_sorted(
                        item
                        for trial_number, _, items in active_reports
                        for item in _ledger_evidence(trial_number, items)
                    )
                    current_resolution_evidence = _dedupe_sorted(
                        item
                        for trial_number, _, items in resolved_reports
                        for item in _ledger_evidence(trial_number, items)
                    )
                    finding = {
                        "fingerprint": fingerprint,
                        **candidate,
                        "lifecycle": "resolved",
                        "first_seen_head": prior_finding["first_seen_head"],
                        "last_seen_head": prior_finding["last_seen_head"],
                        "resolved_head": prior_finding["resolved_head"],
                        "evidence": current_evidence,
                        "resolution_evidence": current_resolution_evidence,
                        "consensus": {"active_trials": active_trials, "resolved_trials": resolved_trials},
                        "suppression": prior_finding["suppression"],
                    }

        if fingerprint in suppressions:
            if finding["lifecycle"] == "resolved":
                raise ReviewError(f"suppression {fingerprint}: cannot suppress a resolved finding")
            finding["suppression"] = suppressions[fingerprint]
        if finding["lifecycle"] != "resolved" and finding["suppression"] is not None:
            finding["lifecycle"] = "suppressed"
        output[fingerprint] = finding

    for fingerprint in suppressions:
        if fingerprint not in output:
            raise ReviewError(f"suppression {fingerprint}: does not reference a consensus or prior finding")

    findings = [output[fingerprint] for fingerprint in sorted(output)]
    counts = calculate_counts(findings)
    ledger = {
        "schema_version": SCHEMA_VERSION,
        "review_id": packet["review_id"],
        "repository": packet["repository"],
        "mode": packet["mode"],
        "base_sha": packet["base_sha"],
        "head_sha": packet["head_sha"],
        "packet_digest": packet_digest,
        "prior_ledger_digest": prior_digest,
        "trial_digests": [trial_digests[number] for number in (1, 2, 3)],
        "findings": findings,
        "counts": counts,
        "verdict": "request_changes" if counts["active_blocker"] or counts["active_important"] else "approve",
    }
    validate_ledger(ledger)
    return ledger


def _escape_markdown(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_markdown(ledger: Mapping[str, Any]) -> str:
    validate_ledger(ledger)
    lines = [
        "# Convergent Code Review",
        "",
        f"- **Repository:** `{_escape_markdown(ledger['repository'])}`",
        f"- **Review:** `{_escape_markdown(ledger['review_id'])}`",
        f"- **Mode:** `{ledger['mode']}`",
        f"- **Base:** `{ledger['base_sha']}`",
        f"- **Current head:** `{ledger['head_sha']}`",
        f"- **Verdict:** **{ledger['verdict']}**",
        "",
        "## Counts",
        "",
        "| Count | Value |",
        "|---|---:|",
    ]
    for key in COUNT_KEYS:
        lines.append(f"| `{key}` | {ledger['counts'][key]} |")
    lines.extend(["", "## Findings", ""])
    if not ledger["findings"]:
        lines.append("No consensus or carried findings.")
    else:
        lines.extend([
            "| Lifecycle | Severity | Path | Symbol | Finding | Fingerprint |",
            "|---|---|---|---|---|---|",
        ])
        for finding in ledger["findings"]:
            lines.append(
                "| {lifecycle} | {severity} | `{path}` | `{symbol}` | {title} | `{fingerprint}` |".format(
                    lifecycle=finding["lifecycle"],
                    severity=finding["severity"],
                    path=_escape_markdown(finding["path"]),
                    symbol=_escape_markdown(finding["symbol"]),
                    title=_escape_markdown(finding["title"]),
                    fingerprint=finding["fingerprint"],
                )
            )
    marker = base64.b64encode(canonical_json_bytes(ledger)).decode("ascii")
    lines.extend(["", f"<!-- nizam-review-ledger:{marker} -->", ""])
    return "\n".join(lines)


def extract_embedded_ledger(markdown: str) -> dict[str, Any]:
    matches = MARKER_RE.findall(markdown)
    if len(matches) != 1:
        raise ReviewError(f"Markdown must contain exactly one ledger marker; found {len(matches)}")
    try:
        raw = base64.b64decode(matches[0], validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ReviewError(f"ledger marker is not valid base64: {exc}") from exc
    ledger = parse_json_bytes(raw, "embedded ledger")
    validate_ledger(ledger, "embedded ledger")
    if raw != canonical_json_bytes(ledger):
        raise ReviewError("embedded ledger is not canonical JSON")
    return dict(ledger)


def _write_atomic(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _fsync_tree(root: Path) -> None:
    for directory, directory_names, filenames in os.walk(root, topdown=False, followlinks=False):
        current = Path(directory)
        for name in [*directory_names, *filenames]:
            candidate = current / name
            metadata = os.lstat(candidate)
            if stat.S_ISLNK(metadata.st_mode):
                raise ReviewError(f"staged publication contains a symlink: {candidate}")
        for filename in filenames:
            descriptor = os.open(
                current / filename,
                os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) |
                getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
            )
            try:
                metadata = os.fstat(descriptor)
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                    raise ReviewError(f"staged publication contains a non-regular or multiply-linked file: {current / filename}")
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        descriptor = os.open(
            current,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) |
            getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _rename_noreplace(source: Path, destination: Path) -> PublicationResult:
    """Atomically publish and explicitly report post-visibility durability state."""
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise ReviewError("atomic no-replace publication requires renameat2 support")
    renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    renameat2.restype = ctypes.c_int
    result = renameat2(
        -100, os.fsencode(source), -100, os.fsencode(destination), RENAME_NOREPLACE,
    )
    if result != 0:
        error = ctypes.get_errno()
        if error in (errno.EEXIST, errno.ENOTEMPTY):
            raise ReviewError(f"output directory must not already exist: {destination}")
        raise OSError(error, os.strerror(error), str(destination))
    parent_descriptor = -1
    durability_error: OSError | None = None
    try:
        parent_descriptor = os.open(destination.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        os.fsync(parent_descriptor)
    except OSError as exc:
        durability_error = exc
    finally:
        if parent_descriptor >= 0:
            try:
                os.close(parent_descriptor)
            except OSError as exc:
                if durability_error is None:
                    durability_error = exc
    if durability_error is not None:
        return PublicationResult(visible=True, durable=False, durability_error=str(durability_error))
    return PublicationResult(visible=True, durable=True)


def _path_ref(role: str, path: str, digest: str, size: int, trial_number: int | None = None) -> dict[str, Any]:
    ref: dict[str, Any] = {"role": role, "path": path, "digest": digest, "bytes": size}
    if trial_number is not None:
        ref["trial_number"] = trial_number
    return ref


def _safe_replay_path(root: Path, relative: str) -> Path:
    validate_path(relative, "replay.artifacts.path")
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ReviewError(f"replay artifact escapes replay root: {relative}") from exc
    return candidate


def validate_replay(replay: Any) -> Mapping[str, Any]:
    obj = _closed(
        replay,
        ("schema_version", "review_id", "repository", "head_sha", "artifacts", "output_digests"),
        (),
        "replay",
    )
    if obj["schema_version"] != SCHEMA_VERSION:
        raise ReviewError(f"replay.schema_version: expected {SCHEMA_VERSION}")
    _string(obj["review_id"], "replay.review_id", pattern=REVIEW_ID_RE, maximum=128)
    validate_repository(obj["repository"], "replay.repository")
    _string(obj["head_sha"], "replay.head_sha", minimum=40, maximum=40, pattern=SHA_RE)
    artifacts = obj["artifacts"]
    if not isinstance(artifacts, list) or not 4 <= len(artifacts) <= 10006:
        raise ReviewError("replay.artifacts: expected between 4 and 10006 entries")
    roles: list[str] = []
    trial_numbers: list[int] = []
    paths: set[str] = set()
    for index, artifact in enumerate(artifacts):
        prefix = f"replay.artifacts[{index}]"
        item = _closed(artifact, ("role", "path", "digest", "bytes"), ("trial_number",), prefix)
        role = _enum(item["role"], ("packet", "trial", "prior_ledger", "suppression"), f"{prefix}.role")
        roles.append(role)
        path = validate_path(item["path"], f"{prefix}.path")
        if path in paths:
            raise ReviewError(f"{prefix}.path: duplicate {path}")
        paths.add(path)
        _digest(item["digest"], f"{prefix}.digest")
        _integer(item["bytes"], f"{prefix}.bytes", 1, 1000000000)
        if role == "trial":
            if "trial_number" not in item:
                raise ReviewError(f"{prefix}.trial_number: required for trial artifact")
            trial_numbers.append(_integer(item["trial_number"], f"{prefix}.trial_number", 1, 3))
        elif "trial_number" in item:
            raise ReviewError(f"{prefix}.trial_number: only valid for trial artifact")
    if roles.count("packet") != 1 or roles.count("prior_ledger") > 1 or sorted(trial_numbers) != [1, 2, 3]:
        raise ReviewError("replay.artifacts: require one packet and trials 1, 2, and 3")
    outputs = _closed(obj["output_digests"], ("ledger", "markdown"), (), "replay.output_digests")
    for key in ("ledger", "markdown"):
        _digest(outputs[key], f"replay.output_digests.{key}")
    return obj


def build_replay(
    packet: Mapping[str, Any], artifacts: Sequence[dict[str, Any]], ledger_raw: bytes, markdown_raw: bytes
) -> dict[str, Any]:
    replay = {
        "schema_version": SCHEMA_VERSION,
        "review_id": packet["review_id"],
        "repository": packet["repository"],
        "head_sha": packet["head_sha"],
        "artifacts": sorted(artifacts, key=lambda item: (item["role"], item.get("trial_number", 0), item["path"])),
        "output_digests": {"ledger": sha256(ledger_raw), "markdown": sha256(markdown_raw)},
    }
    validate_replay(replay)
    return replay


def _load_convergence_inputs(args: argparse.Namespace) -> tuple[
    Mapping[str, Any], str, list[Mapping[str, Any]], dict[int, str], Mapping[str, Any] | None, str | None,
    list[tuple[Mapping[str, Any], str]], list[tuple[dict[str, Any], bytes]],
]:
    packet, packet_raw = read_raw_json(Path(args.packet), "packet")
    require_canonical_json(packet, packet_raw, "packet")
    validate_packet(packet)
    packet_digest = sha256(packet_raw)
    retained: list[tuple[dict[str, Any], bytes]] = [
        (_path_ref("packet", "inputs/packet.json", packet_digest, len(packet_raw)), packet_raw)
    ]
    trials: list[Mapping[str, Any]] = []
    trial_digests: dict[int, str] = {}
    for trial_arg in args.trial:
        trial, trial_raw = read_raw_json(Path(trial_arg), f"trial {trial_arg}")
        require_canonical_json(trial, trial_raw, f"trial {trial_arg}")
        validate_trial(trial, packet, packet_digest, f"trial {trial_arg}")
        number = trial["trial_number"]
        if number in trial_digests:
            raise ReviewError(f"duplicate trial_number: {number}")
        digest = sha256(trial_raw)
        trial_digests[number] = digest
        trials.append(trial)
        relative = f"inputs/trial-{number}.json"
        retained.append((_path_ref("trial", relative, digest, len(trial_raw), number), trial_raw))
    if sorted(trial_digests) != [1, 2, 3]:
        raise ReviewError("converge requires exactly three trial files numbered 1, 2, and 3")

    prior: Mapping[str, Any] | None = None
    prior_digest: str | None = None
    if args.prior_ledger:
        prior, prior_raw = read_raw_json(Path(args.prior_ledger), "prior ledger")
        require_canonical_json(prior, prior_raw, "prior ledger")
        validate_ledger(prior, "prior ledger")
        prior_digest = sha256(prior_raw)
        retained.append((_path_ref("prior_ledger", "inputs/prior-ledger.json", prior_digest, len(prior_raw)), prior_raw))

    loaded_suppressions: list[tuple[Mapping[str, Any], bytes, str]] = []
    for suppression_arg in args.suppression:
        suppression, suppression_raw = read_raw_json(Path(suppression_arg), f"suppression {suppression_arg}")
        require_canonical_json(suppression, suppression_raw, f"suppression {suppression_arg}")
        validate_suppression(suppression, packet["repository"], f"suppression {suppression_arg}")
        digest = sha256(suppression_raw)
        loaded_suppressions.append((suppression, suppression_raw, digest))
    loaded_suppressions.sort(key=lambda item: (item[0]["fingerprint"], item[2]))
    suppressions: list[tuple[Mapping[str, Any], str]] = []
    for index, (suppression, suppression_raw, digest) in enumerate(loaded_suppressions, start=1):
        suppressions.append((suppression, digest))
        relative = f"inputs/suppression-{index:03d}.json"
        retained.append((_path_ref("suppression", relative, digest, len(suppression_raw)), suppression_raw))
    return packet, packet_digest, trials, trial_digests, prior, prior_digest, suppressions, retained


def _git_environment() -> dict[str, str]:
    """Minimal deterministic Git environment with replacement/redirect inputs disabled."""
    return {
        "HOME": os.devnull,
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/bin:/bin",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.useReplaceRefs",
        "GIT_CONFIG_VALUE_0": "false",
        "GIT_NO_REPLACE_OBJECTS": "1",
    }


def _git(repo: Path, *arguments: str, text: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "--no-replace-objects", *arguments],
        capture_output=True, check=False, env=_git_environment(),
    )
    if completed.returncode != 0:
        raise ReviewError(f"git {' '.join(arguments)} failed: {completed.stderr.decode('utf-8', 'replace').strip()}")
    if text:
        return completed.stdout.decode("utf-8").strip()
    return completed.stdout


def _git_path_entry(repo: Path, commit: str, path: str) -> tuple[str, str] | None:
    """Resolve one path to an immutable blob, distinguishing absence from Git failure."""
    raw = bytes(_git(repo, "ls-tree", "-z", commit, "--", path))
    records = [record for record in raw.split(b"\0") if record]
    if not records:
        return None
    if len(records) != 1:
        raise ReviewError(f"Git tree lookup returned multiple entries for {path}")
    metadata, raw_path = records[0].split(b"\t", 1)
    if raw_path.decode("utf-8") != path:
        raise ReviewError(f"Git tree lookup returned unexpected path for {path}")
    mode_bytes, kind_bytes, oid_bytes = metadata.split(b" ", 2)
    mode = mode_bytes.decode("ascii")
    kind = kind_bytes.decode("ascii")
    object_id = oid_bytes.decode("ascii")
    if kind != "blob" or mode not in ("100644", "100755", "120000"):
        raise ReviewError(f"packet builder refuses unsupported tree entry {mode} {kind} {path}")
    return mode, object_id


def _git_blob(repo: Path, object_id: str, ctx: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo), "--no-replace-objects", "cat-file", "blob", object_id],
        capture_output=True, check=False, env=_git_environment(),
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise ReviewError(f"{ctx}: immutable Git blob read failed: {detail or 'unknown Git error'}")
    return completed.stdout


def _decode_git_text(raw: bytes, ctx: str) -> str:
    if len(raw) > MAX_SOURCE_BYTES:
        raise ReviewError(f"{ctx}: exceeds {MAX_SOURCE_BYTES} bytes")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReviewError(f"{ctx}: full packet construction refuses non-UTF-8 blobs: {exc}") from exc


def build_packet_from_git(
    repo: Path, repository: str, review_id: str, mode: str, base_ref: str, head_ref: str,
) -> dict[str, Any]:
    """Trusted packet builder: read immutable Git objects, never the ambient worktree."""
    validate_repository(repository, "repository")
    _string(review_id, "review_id", pattern=REVIEW_ID_RE, maximum=128)
    _enum(mode, ("ordinary", "full_audit"), "mode")
    base_sha = str(_git(repo, "rev-parse", f"{base_ref}^{{commit}}", text=True))
    head_sha = str(_git(repo, "rev-parse", f"{head_ref}^{{commit}}", text=True))
    _string(base_sha, "base_sha", minimum=40, maximum=40, pattern=SHA_RE)
    _string(head_sha, "head_sha", minimum=40, maximum=40, pattern=SHA_RE)
    changed_raw = bytes(_git(repo, "diff", "--no-renames", "--name-only", "-z", base_sha, head_sha))
    changed_paths = sorted(item.decode("utf-8") for item in changed_raw.split(b"\0") if item)
    for path in changed_paths:
        validate_path(path, "git changed path")

    delta: list[dict[str, Any]] = []
    sources: dict[str, dict[str, Any]] = {}
    for changed_path in changed_paths:
        old_entry = _git_path_entry(repo, base_sha, changed_path)
        new_entry = _git_path_entry(repo, head_sha, changed_path)
        old_mode, old_object_id = old_entry if old_entry is not None else (None, None)
        new_mode, new_object_id = new_entry if new_entry is not None else (None, None)
        old_raw = _git_blob(repo, old_object_id, f"old blob {changed_path}") if old_object_id else None
        new_raw = _git_blob(repo, new_object_id, f"new blob {changed_path}") if new_object_id else None
        old_content = _decode_git_text(old_raw, f"old blob {changed_path}") if old_raw is not None else None
        new_content = _decode_git_text(new_raw, f"new blob {changed_path}") if new_raw is not None else None
        old_digest = sha256(old_raw) if old_raw is not None else None
        new_digest = sha256(new_raw) if new_raw is not None else None
        delta.append({
            "path": changed_path, "old_digest": old_digest, "old_content": old_content,
            "old_mode": old_mode, "new_digest": new_digest, "new_mode": new_mode,
        })
        sources[changed_path] = {
            "path": changed_path,
            "content_digest": new_digest if new_digest is not None else EMPTY_DIGEST,
            "content": new_content,
        }

    commitment: dict[str, Any] | None = None
    if mode == "full_audit":
        tree_raw = bytes(_git(repo, "ls-tree", "-r", "-z", head_sha))
        entries: list[dict[str, str]] = []
        for record in tree_raw.split(b"\0"):
            if not record:
                continue
            metadata, raw_path = record.split(b"\t", 1)
            mode_bytes, kind_bytes, oid_bytes = metadata.split(b" ", 2)
            tree_path = raw_path.decode("utf-8")
            validate_path(tree_path, "git tree path")
            git_mode = mode_bytes.decode("ascii")
            kind = kind_bytes.decode("ascii")
            object_id = oid_bytes.decode("ascii")
            if kind != "blob" or git_mode not in ("100644", "100755", "120000"):
                raise ReviewError(f"full_audit refuses unsupported tree entry {git_mode} {kind} {tree_path}")
            blob_raw = _git_blob(repo, object_id, f"head blob {tree_path}")
            content = _decode_git_text(blob_raw, f"head blob {tree_path}")
            entries.append({"path": tree_path, "mode": git_mode, "object_id": object_id})
            sources[tree_path] = {
                "path": tree_path, "content_digest": sha256(blob_raw), "content": content,
            }
        entries.sort(key=lambda item: item["path"])
        root_tree = str(_git(repo, "rev-parse", f"{head_sha}^{{tree}}", text=True))
        if _git_tree_id(entries) != root_tree:
            raise ReviewError("trusted builder tree reconstruction does not match Git head tree")
        commit_raw = bytes(_git(repo, "cat-file", "commit", head_sha))
        commit_content = _decode_git_text(commit_raw, "head commit")
        commitment = {
            "object_format": "git-sha1",
            "commit_content": commit_content,
            "root_tree": root_tree,
            "manifest_digest": sha256(canonical_json_bytes(entries)),
            "entries": entries,
        }

    packet = {
        "schema_version": SCHEMA_VERSION,
        "review_id": review_id,
        "repository": repository,
        "mode": mode,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "scope_commitment": commitment,
        "delta": delta,
        "review_files": [sources[path] for path in sorted(sources)],
    }
    validate_packet(packet)
    return packet


def cmd_build_packet(args: argparse.Namespace) -> int:
    packet = build_packet_from_git(
        Path(args.repo).resolve(strict=True), args.repository, args.review_id,
        args.mode, args.base, args.head,
    )
    raw = canonical_json_bytes(packet)
    if args.output == "-":
        sys.stdout.buffer.write(raw)
    else:
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    return 0


def cmd_fingerprint(args: argparse.Namespace) -> int:
    value, raw = read_raw_json(Path(args.finding), "finding")
    require_canonical_json(value, raw, "finding")
    validate_candidate(value, "finding")
    repository = validate_repository(args.repository, "repository")
    print(semantic_fingerprint(repository, value))
    return 0


def cmd_converge(args: argparse.Namespace) -> int:
    packet, packet_digest, trials, trial_digests, prior, prior_digest, suppressions, retained = _load_convergence_inputs(args)
    ledger = converge_documents(packet, packet_digest, trials, trial_digests, prior, prior_digest, suppressions)
    ledger_raw = canonical_json_bytes(ledger)
    markdown_raw = render_markdown(ledger).encode("utf-8")
    output_dir = Path(args.output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=str(output_dir.parent)))
    try:
        _write_atomic(staging / "ledger.json", ledger_raw)
        _write_atomic(staging / "review.md", markdown_raw)
        for ref, raw in retained:
            _write_atomic(_safe_replay_path(staging, ref["path"]), raw)
        replay = build_replay(packet, [ref for ref, _ in retained], ledger_raw, markdown_raw)
        _write_atomic(staging / "replay.json", canonical_json_bytes(replay))
        verify_replay_directory(staging / "replay.json")
        _fsync_tree(staging)
        publication = _rename_noreplace(staging, output_dir)
        if not publication.durable:
            print(
                f"convergent_review: warning: output published at {output_dir}, but parent-directory durability failed: "
                f"{publication.durability_error}",
                file=sys.stderr,
            )
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    ledger, raw_input = read_raw_json(Path(args.ledger), "ledger")
    require_canonical_json(ledger, raw_input, "ledger")
    validate_ledger(ledger)
    raw = render_markdown(ledger).encode("utf-8")
    if args.output == "-":
        sys.stdout.buffer.write(raw)
    else:
        _write_atomic(Path(args.output), raw)
    return 0


def cmd_extract_ledger(args: argparse.Namespace) -> int:
    try:
        markdown = Path(args.markdown).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ReviewError(f"cannot read Markdown: {exc}") from exc
    ledger = extract_embedded_ledger(markdown)
    raw = canonical_json_bytes(ledger)
    if args.output == "-":
        sys.stdout.buffer.write(raw)
    else:
        _write_atomic(Path(args.output), raw)
    return 0


def verify_replay_directory(replay_path: Path) -> None:
    replay_raw = _read_regular_nofollow(replay_path, "replay")
    replay = parse_json_bytes(replay_raw, "replay")
    validate_replay(replay)
    if replay_raw != canonical_json_bytes(replay):
        raise ReviewError("replay.json is not canonical JSON")
    root = replay_path.parent
    ledger_raw = _read_relative_regular_nofollow(root, "ledger.json", "ledger output")
    markdown_raw = _read_relative_regular_nofollow(root, "review.md", "Markdown output")
    if sha256(ledger_raw) != replay["output_digests"]["ledger"]:
        raise ReviewError("ledger output digest mismatch")
    if sha256(markdown_raw) != replay["output_digests"]["markdown"]:
        raise ReviewError("Markdown output digest mismatch")
    ledger = parse_json_bytes(ledger_raw, "ledger output")
    validate_ledger(ledger)
    if ledger_raw != canonical_json_bytes(ledger):
        raise ReviewError("ledger output is not canonical JSON")
    markdown = markdown_raw.decode("utf-8")
    if render_markdown(ledger).encode("utf-8") != markdown_raw:
        raise ReviewError("Markdown output is not the deterministic rendering of ledger.json")
    if canonical_json_bytes(extract_embedded_ledger(markdown)) != ledger_raw:
        raise ReviewError("embedded ledger does not match ledger.json")

    loaded_packet: Mapping[str, Any] | None = None
    packet_digest = ""
    loaded_trials: list[Mapping[str, Any]] = []
    trial_digests: dict[int, str] = {}
    loaded_prior: Mapping[str, Any] | None = None
    prior_digest: str | None = None
    loaded_suppressions: list[tuple[Mapping[str, Any], str]] = []
    for artifact in replay["artifacts"]:
        raw = _read_relative_regular_nofollow(
            root, artifact["path"], f"replay artifact {artifact['path']}",
        )
        if len(raw) != artifact["bytes"] or sha256(raw) != artifact["digest"]:
            raise ReviewError(f"replay artifact digest/size mismatch: {artifact['path']}")
        value = parse_json_bytes(raw, artifact["path"])
        require_canonical_json(value, raw, artifact["path"])
        if artifact["role"] == "packet":
            validate_packet(value)
            loaded_packet = value
            packet_digest = artifact["digest"]
        elif artifact["role"] == "trial":
            loaded_trials.append(value)
            trial_digests[artifact["trial_number"]] = artifact["digest"]
        elif artifact["role"] == "prior_ledger":
            validate_ledger(value, "replay prior ledger")
            loaded_prior = value
            prior_digest = artifact["digest"]
        else:
            loaded_suppressions.append((value, artifact["digest"]))
    if loaded_packet is None:
        raise ReviewError("replay does not contain a packet")
    if loaded_packet["review_id"] != replay["review_id"] or loaded_packet["repository"] != replay["repository"] or loaded_packet["head_sha"] != replay["head_sha"]:
        raise ReviewError("replay identity/head does not match retained packet")
    for trial in loaded_trials:
        validate_trial(trial, loaded_packet, packet_digest, f"replay trial {trial.get('trial_number')}")
    for suppression, _ in loaded_suppressions:
        validate_suppression(suppression, loaded_packet["repository"], "replay suppression")
    recomputed = converge_documents(loaded_packet, packet_digest, loaded_trials, trial_digests, loaded_prior, prior_digest, loaded_suppressions)
    if canonical_json_bytes(recomputed) != ledger_raw:
        raise ReviewError("replayed convergence does not reproduce ledger.json")


def cmd_verify_replay(args: argparse.Namespace) -> int:
    verify_replay_directory(Path(args.replay))
    print("replay verified")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    builder = subparsers.add_parser("build-packet", help="build a trusted packet from immutable Git objects")
    builder.add_argument("--repo", required=True)
    builder.add_argument("--repository", required=True)
    builder.add_argument("--review-id", required=True)
    builder.add_argument("--mode", choices=("ordinary", "full_audit"), required=True)
    builder.add_argument("--base", required=True)
    builder.add_argument("--head", required=True)
    builder.add_argument("--output", default="-")
    builder.set_defaults(func=cmd_build_packet)
    fingerprint = subparsers.add_parser("fingerprint", help="calculate one stable semantic fingerprint")
    fingerprint.add_argument("--repository", required=True)
    fingerprint.add_argument("--finding", required=True)
    fingerprint.set_defaults(func=cmd_fingerprint)
    converge = subparsers.add_parser("converge", help="converge exactly three observation trials")
    converge.add_argument("--packet", required=True)
    converge.add_argument("--trial", action="append", required=True)
    converge.add_argument("--prior-ledger")
    converge.add_argument("--suppression", action="append", default=[])
    converge.add_argument("--output-dir", required=True)
    converge.set_defaults(func=cmd_converge)
    render = subparsers.add_parser("render", help="render a validated ledger as deterministic Markdown")
    render.add_argument("--ledger", required=True)
    render.add_argument("--output", default="-")
    render.set_defaults(func=cmd_render)
    extract = subparsers.add_parser("extract-ledger", help="extract and validate the embedded ledger marker")
    extract.add_argument("--markdown", required=True)
    extract.add_argument("--output", default="-")
    extract.set_defaults(func=cmd_extract_ledger)
    verify = subparsers.add_parser("verify-replay", help="verify content-addressed inputs and outputs")
    verify.add_argument("--replay", required=True)
    verify.set_defaults(func=cmd_verify_replay)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "converge" and len(args.trial) != 3:
            raise ReviewError("converge requires exactly three --trial arguments")
        return int(args.func(args))
    except (ReviewError, OSError, UnicodeDecodeError) as exc:
        print(f"convergent_review: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
