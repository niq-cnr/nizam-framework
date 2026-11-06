#!/usr/bin/env python3
"""Verify a consumer's .nizam/provenance.lock.json against .nizam/provenance.json and the declared range.

Checks (stable failure prefixes):
  lock-shape          lock exists, is a JSON object with exactly the five keys
  lock-format         framework_version/tag/resolved_sha/source_url field formats
  range-syntax        declared_range parses as comma-separated semver comparators
  range-unsatisfied   framework_version satisfies every comparator
  lock-payload-drift  provenance.json fields equal the lock's fields
  payload-missing     provenance.json absent (fail closed)

CLI:
  python3 tools/check_provenance_lock.py --repo DIR
  python3 tools/check_provenance_lock.py --self-test

Exit 0 only when all checks pass; 1 on any FAIL; 2 for usage errors.
Python 3 standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

LOCK_KEYS = {"framework_version", "tag", "resolved_sha", "declared_range", "source_url"}
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
TAG_OK_RE = re.compile(r"^v\d+\.\d+\.\d+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
COMPARATOR_RE = re.compile(r"^(==|>=|<=|>|<)(\d+\.\d+\.\d+)$")
# Forms bootstrap.sh --repo-url can record verbatim: scheme URLs (https/http/ssh/file/git),
# scp-like git@host:path, or an absolute local path. Whitespace/control chars rejected separately.
SOURCE_URL_RE = re.compile(r"^((https?|ssh|git|file)://[^\s\x00-\x1f\x7f]+|[\w.-]+@[\w.-]+:[^\s\x00-\x1f\x7f]+|/[^\s\x00-\x1f\x7f]*)$")

FAIL_PREFIX = "[PCL] FAIL "
PASS_PREFIX = "[PCL] PASS "


def _fail(name: str, detail: str) -> str:
    return f"{FAIL_PREFIX}{name}: {detail}"


def _parse_comparators(declared_range: str) -> list[tuple[str, tuple[int, ...]]] | None:
    """Return parsed comparators, or None on syntax failure."""
    if not isinstance(declared_range, str) or not declared_range.strip():
        return None
    out = []
    for part in declared_range.split(","):
        part = part.strip()
        m = COMPARATOR_RE.match(part)
        if not m:
            return None
        out.append((m.group(1), tuple(int(x) for x in m.group(2).split("."))))
    return out


def _satisfied(version: tuple[int, ...], op: str, ref: tuple[int, ...]) -> bool:
    if op == "==":
        return version == ref
    if op == ">=":
        return version >= ref
    if op == "<=":
        return version <= ref
    if op == ">":
        return version > ref
    return version < ref  # "<"


def check_lock(lock_raw: str, payload_raw: str | None) -> list[str]:
    """Run all checks over raw lock/payload file contents; return FAIL lines."""
    fails: list[str] = []

    lock: dict | None = None
    try:
        parsed = json.loads(lock_raw)
        if isinstance(parsed, dict):
            lock = parsed
        else:
            fails.append(_fail("lock-shape", "lock is not a JSON object"))
    except (ValueError, TypeError):
        fails.append(_fail("lock-shape", "lock does not parse as JSON"))
    if lock is not None and set(lock.keys()) != LOCK_KEYS:
        extra = sorted(set(lock.keys()) - LOCK_KEYS)
        missing = sorted(LOCK_KEYS - set(lock.keys()))
        fails.append(_fail("lock-shape", f"keys differ: extra={extra} missing={missing}"))

    framework_version = tag = resolved_sha = declared_range = None
    if lock is not None:
        framework_version = lock.get("framework_version")
        resolved_sha = lock.get("resolved_sha")
        declared_range = lock.get("declared_range")
        tag = lock.get("tag")
        source_url = lock.get("source_url")
        if not isinstance(framework_version, str) or not VERSION_RE.match(framework_version):
            fails.append(_fail("lock-format", f"framework_version {framework_version!r} is not MAJOR.MINOR.PATCH"))
        if not isinstance(tag, str) or not isinstance(framework_version, str) or tag != "v" + framework_version:
            fails.append(_fail("lock-format", f"tag {tag!r} is not 'v' + framework_version"))
        if not isinstance(resolved_sha, str) or not SHA_RE.match(resolved_sha):
            fails.append(_fail("lock-format", f"resolved_sha {resolved_sha!r} is not 40 lowercase hex"))
        if (not isinstance(source_url, str) or not source_url
                or re.search(r"\s", source_url) or not SOURCE_URL_RE.match(source_url)):
            fails.append(_fail("lock-format", f"source_url {source_url!r} is not a non-empty recordable repository URL (scheme URL, scp-like, or absolute path) without whitespace or control characters"))

    comparators = _parse_comparators(declared_range)
    if comparators is None:
        fails.append(_fail("range-syntax", f"declared_range {declared_range!r} is not a comma-separated list of ==/>=/<=/>/< comparators"))
    elif isinstance(framework_version, str) and VERSION_RE.match(framework_version):
        version = tuple(int(x) for x in framework_version.split("."))
        for op, ref in comparators:
            if not _satisfied(version, op, ref):
                fails.append(_fail("range-unsatisfied", f"framework_version {framework_version} does not satisfy {op}{'.'.join(str(x) for x in ref)}"))

    if payload_raw is None:
        fails.append(_fail("payload-missing", "provenance.json is absent"))
    else:
        try:
            payload = json.loads(payload_raw)
        except (ValueError, TypeError):
            payload = None
        if not isinstance(payload, dict):
            fails.append(_fail("lock-payload-drift", "provenance.json does not parse as a JSON object"))
        elif lock is not None:
            for lock_key, payload_key in (
                ("framework_version", "framework_version"),
                ("tag", "tag"),
                ("resolved_sha", "resolved_sha"),
                ("source_url", "source_url"),
            ):
                pv = payload.get(payload_key)
                lv = lock.get(lock_key)
                if pv != lv:
                    fails.append(_fail("lock-payload-drift", f"lock {lock_key} {lv!r} != provenance.json {payload_key} {pv!r}"))

    return fails


def run_repo(repo: Path) -> int:
    lock_path = repo / ".nizam" / "provenance.lock.json"
    payload_path = repo / ".nizam" / "provenance.json"
    if not lock_path.exists():
        print(_fail("lock-shape", f"lock file not found at {lock_path}"))
        return 1
    lock_raw = lock_path.read_text(encoding="utf-8")
    payload_raw: str | None = (
        payload_path.read_text(encoding="utf-8") if payload_path.exists() else None
    )
    fails = check_lock(lock_raw, payload_raw)
    if fails:
        for line in fails:
            print(line)
        return 1
    for name in ("lock-shape", "lock-format", "range-syntax", "range-unsatisfied", "payload-missing", "lock-payload-drift"):
        print(f"{PASS_PREFIX}{name}")
    return 0


def run_self_test() -> int:
    ok = True
    base_lock = {
        "framework_version": "3.1.3",
        "tag": "v3.1.3",
        "resolved_sha": "0" * 40,
        "declared_range": ">=3.1.0,<4.0.0",
        "source_url": "https://example.com/fw.git",
    }
    payload = dict(base_lock)
    payload["installed_at"] = "2026-11-05T00:00:00Z"

    def expect(name: str, expected_fail: str | None, fails: list[str]):
        nonlocal ok
        actual = next((f.split(":")[0].replace(FAIL_PREFIX, "") for f in fails), None)
        passed = (expected_fail is None and not fails) or (
            expected_fail is not None and fails and all(f.startswith(FAIL_PREFIX + expected_fail) for f in fails)
        )
        print(f"{'PASS' if passed else 'FAIL'} case={name} expected={expected_fail or 'pass'} actual={actual or 'pass'}")
        if not passed:
            ok = False

    import tempfile

    def lock_json(**over):
        d = dict(base_lock)
        d.update(over)
        return json.dumps(d, indent=2)

    def expect_prefix(name: str, prefix: str, fails: list[str]):
        nonlocal ok
        present = bool(fails) and any(f.startswith(FAIL_PREFIX + prefix) for f in fails)
        print(f"{'PASS' if present else 'FAIL'} case={name} requires={prefix}")
        if not present:
            ok = False

    payload_json = json.dumps(payload, indent=2)
    expect("consistent-pass", None, check_lock(lock_json(), payload_json))
    shifted_payload = json.dumps({**payload, "tag": "v9.9.9"}, indent=2)
    expect("tag-drift", "lock-payload-drift", check_lock(lock_json(), shifted_payload))
    shifted_payload = json.dumps({**payload, "resolved_sha": "1" * 40}, indent=2)
    expect("sha-mismatch", "lock-payload-drift", check_lock(lock_json(), shifted_payload))
    range_lock = json.dumps({**base_lock, "framework_version": "4.1.0", "tag": "v4.1.0"}, indent=2)
    range_payload = json.dumps({**payload, "framework_version": "4.1.0", "tag": "v4.1.0"}, indent=2)
    expect("out-of-range", "range-unsatisfied", check_lock(range_lock, range_payload))
    sha_payload = json.dumps({**payload, "resolved_sha": "XYZ"}, indent=2)
    expect("malformed-sha", "lock-format", check_lock(lock_json(resolved_sha="XYZ"), sha_payload))
    expect("mismatched-source-url", "lock-payload-drift",
           check_lock(lock_json(source_url="https://evil.example/fork.git"), payload_json))
    expect_prefix("empty-source-url", "lock-format", check_lock(lock_json(source_url=""), payload_json))
    expect_prefix("null-source-url", "lock-format", check_lock(lock_json(source_url=None), payload_json))
    expect_prefix("missing-source-url", "lock-shape",
                  check_lock(json.dumps({k: v for k, v in base_lock.items() if k != "source_url"}, indent=2), payload_json))
    expect_prefix("bad-scheme-source-url", "lock-format", check_lock(lock_json(source_url="ftp://example.com/f.git"), payload_json))
    expect_prefix("whitespace-source-url", "lock-format", check_lock(lock_json(source_url="https://example.com/a b.git"), payload_json))
    file_payload = json.dumps({**payload, "source_url": "file:///tmp/fw/src"}, indent=2)
    expect("file-scheme-source-url-pass", None, check_lock(lock_json(source_url="file:///tmp/fw/src"), file_payload))
    expect("extra-key", "lock-shape", check_lock(lock_json(extra="k"), payload_json))
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        (repo / ".nizam").mkdir()
        (repo / ".nizam" / "provenance.lock.json").write_text(lock_json(), encoding="utf-8")
        expect("missing-payload", "payload-missing", [l for l in run_repo_capture(repo) if l.startswith(FAIL_PREFIX)])
    expect("range-exact-pass", None, check_lock(lock_json(declared_range="==3.1.3"), payload_json))
    exact414_payload = json.dumps({**payload, "framework_version": "3.1.4", "tag": "v3.1.4"}, indent=2)
    expect(
        "range-exact-fail",
        "range-unsatisfied",
        check_lock(lock_json(framework_version="3.1.4", tag="v3.1.4", declared_range="==3.1.3"), exact414_payload),
    )
    expect("range-open-pass", None, check_lock(lock_json(declared_range=">=3.1.0,<4.0.0"), payload_json))
    return 0 if ok else 1


def run_repo_capture(repo: Path) -> list[str]:
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_repo(repo)
    return buf.getvalue().splitlines()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify .nizam/provenance.lock.json against .nizam/provenance.json and the declared range.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo", type=Path, help="repository root to check")
    group.add_argument("--self-test", action="store_true", help="run built-in assertions in a temp dir")
    args = parser.parse_args()
    if args.self_test:
        return run_self_test()
    if not args.repo.is_dir():
        print(f"{FAIL_PREFIX}usage: --repo {args.repo} is not a directory")
        return 2
    return run_repo(args.repo)


if __name__ == "__main__":
    sys.exit(main())
