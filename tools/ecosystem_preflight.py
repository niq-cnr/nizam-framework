#!/usr/bin/env python3
"""ecosystem_preflight.py -- Minimum deterministic Ecosystem Engineering Cycle preflight CLI.

Implements the minimum viable slice of two ecosystem-module protocols:

- ``ecosystem/01_clean_state_preflight.md`` -- the three-verdict vocabulary
  (PASS / PASS_WITH_EXCEPTIONS / FAIL), the blocking-vs-non-blocking
  distinction (Sec 4), and the operator-exception rule (Sec 5).
- ``ecosystem/02_evidence_baseline.md`` -- the six baseline field categories
  (Sec 3), each item anchored to a real revision and timestamp (Sec 4).

This CLI intentionally implements the MINIMUM slice of those protocols that
is deterministically checkable today: git clean-state (tracked and untracked
changes) plus required-schema-reference resolution. Consumer-registered
custom blocking conditions and the P0-defect/H-RISK acceptance-of-risk gate
are explicitly NOT implemented here (no typed source of either exists yet in
this repository); see feature 041's contract non_goals for the full list of
deferred behavior.

Exit codes
----------
This CLI documents its exit codes both here and via ``--help``:

    0   PASS -- no blocking finding, no non-blocking finding (exception).
        Both preflight.json and baseline.json are written, schema-valid.
        Safe to proceed to Baseline/Audit/Plan/Execute.
    1   FAIL -- at least one blocking finding was detected. Only
        preflight.json is written (a baseline is never captured against a
        FAIL verdict, per protocol Sec 2). Execution MUST NOT proceed.
    2   PASS_WITH_EXCEPTIONS (pending operator approval) -- no blocking
        finding, but one or more non-blocking findings (exceptions) were
        surfaced, and no --operator-approver/--operator-authorization were
        supplied. Per protocol Sec 5 the tool MUST NOT proceed: the
        schema-gated preflight.json is WITHHELD entirely; only an
        informational, deliberately non-schema-conformant
        preflight.pending.json is written so the pending exceptions remain
        visible. Re-invoke with the operator-approval flags to continue.
    3   PASS_WITH_EXCEPTIONS (approved) -- the same exceptions, but
        --operator-approver and --operator-authorization were supplied.
        preflight.json is written with a populated operator_approval block,
        and baseline.json is captured (protocol Sec 2: a baseline follows a
        PASS or an approved PASS_WITH_EXCEPTIONS).
    64  Usage error -- missing or invalid command-line arguments. Distinct
        from every domain exit code (0/1/2/3) above.

Example
-------
    python3 tools/ecosystem_preflight.py \\
        --execution-id exec-2026-07-17-001 \\
        --output-dir /tmp/preflight-out \\
        --self-fixture \\
        --tolerate-untracked v0.6.0-release-notes.md \\
        --tolerate-untracked-prefix .agent/evidence/exec-2026-07-17-001/ \\
        --ci-run-file /tmp/ci-run.json \\
        --operator-approver "jane@example.com" \\
        --operator-authorization "reviewed exceptions, approved for dogfood run"
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import subprocess
import sys
from typing import Sequence

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_PASS_WITH_EXCEPTIONS_PENDING = 2
EXIT_PASS_WITH_EXCEPTIONS_APPROVED = 3
EXIT_USAGE_ERROR = 64

REQUIRED_REFERENCE_PATHS: tuple[str, ...] = (
    "schema/preflight_verdict.schema.json",
    "schema/ecosystem_baseline.schema.json",
)


class PreflightUsageError(Exception):
    """Raised for a malformed CLI invocation; the caller maps this to exit 64.

    This is a custom error class (per the house code-generation standard of
    "consistent error handling with custom error classes") rather than a bare
    ``SystemExit`` from argparse's own default handler, so a usage error is
    never silently conflated with any domain exit code (0/1/2/3) above.
    """


class _UsageErrorArgumentParser(argparse.ArgumentParser):
    """An ``argparse.ArgumentParser`` whose ``error()`` raises, not exits.

    argparse's default ``error()`` prints a usage message and calls
    ``sys.exit(2)`` directly, which would collide with this CLI's own domain
    exit code 2 (PASS_WITH_EXCEPTIONS, pending). Overriding it to raise
    :class:`PreflightUsageError` lets the top-level entry point map every
    malformed invocation to the single, documented, distinct exit code 64.
    """

    def error(self, message: str) -> None:  # noqa: D102 - argparse override
        raise PreflightUsageError(message)


def read_utc_now() -> datetime.datetime:
    """Return the current time as a single, timezone-aware UTC clock read.

    Called exactly once per CLI invocation (methodology/04_tool_driven_state.md's
    Clock-Read Timestamps rule) so every timestamp field emitted by a single
    run is mutually consistent, never drifting between fields.
    """
    return datetime.datetime.now(datetime.timezone.utc)


def format_iso8601(moment: datetime.datetime) -> str:
    """Format a timezone-aware UTC datetime as a ``YYYY-MM-DDTHH:MM:SSZ`` string."""
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def run_git(repo_root: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a ``git`` subcommand against ``repo_root`` and capture its result.

    Never raises on a non-zero git exit status; callers inspect
    ``result.returncode`` explicitly so a git failure becomes an ordinary,
    handled preflight finding rather than an uncaught exception (no silent
    failures; no bare ``except``).
    """
    return subprocess.run(
        ["git", "-C", repo_root, *args],
        capture_output=True,
        text=True,
        check=False,
    )


def resolve_self_fixture_repo_root(script_path: str) -> str:
    """Resolve the git working tree the shipped script itself lives inside.

    Used by ``--self-fixture`` when the caller does not also pass an explicit
    ``--repo-root``: it auto-detects the repository containing this script
    (``tools/ecosystem_preflight.py``) so the CLI can dogfood the framework
    it ships with, without the caller needing to know the absolute path.

    Raises:
        PreflightUsageError: if the script's own directory is not inside a
            git working tree.
    """
    script_dir = os.path.dirname(os.path.abspath(script_path))
    result = run_git(script_dir, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        raise PreflightUsageError(
            "--self-fixture could not resolve this script's own repository "
            f"root (git rev-parse --show-toplevel failed): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def collect_git_clean_state_findings(
    repo_root: str,
    tolerated_untracked_paths: Sequence[str],
    tolerated_untracked_prefixes: Sequence[str] = (),
) -> tuple[list[str], list[dict[str, str]]]:
    """Collect blocking findings and non-blocking exceptions from git status.

    Implements ecosystem/01_clean_state_preflight.md Sec 4 bullet 1: any
    staged or unstaged change to a tracked file is unconditionally blocking;
    an untracked file is blocking unless its repo-relative path was
    explicitly declared tolerated, in which case it is surfaced as a
    non-blocking exception, never silently dropped (Sec 4's non-downgrade
    invariant: a blocking finding is never produced here for a tolerated path,
    and a tolerated path is never silently omitted either).

    A path is tolerated if it exactly equals one of ``tolerated_untracked_paths``
    (the ``--tolerate-untracked`` EXACT-match allow-list -- the 043/044 approved
    runs depend on this exact semantics, including git's own collapse of an
    entirely-untracked directory to one trailing-slash entry) OR it begins with
    one of ``tolerated_untracked_prefixes`` (the ``--tolerate-untracked-prefix``
    additive option, NDEBT-018: lets a run tolerate a whole in-flight artifact
    directory by one declared prefix rather than enumerating each file). The
    exact-match set is preferred: a path matched exactly keeps the historical
    ``declared_tolerated_untracked`` kind, so 043/044 semantics are unchanged.

    Parses ``git status --porcelain=v1 -z`` (NUL-delimited, NDEBT-021): the
    default porcelain-v1 C-quotes paths with spaces or non-ASCII bytes, which
    would break the literal tolerate-list membership test; the ``-z`` form emits
    each path raw. ``-z`` does NOT pass ``--untracked-files=all``, so git still
    collapses an untracked directory to a single entry -- the trailing-slash
    directory form the 043/044 tolerate sets rely on is preserved. A rename/copy
    entry (status ``R``/``C``) emits its original path as the following NUL
    field; that paired field is consumed so it is never mis-parsed as its own
    entry (a rename is a tracked change and blocks regardless).

    Returns:
        A ``(blocking_findings, exceptions)`` pair. ``blocking_findings`` is a
        list of human-readable strings. ``exceptions`` is a list of small
        structured dicts (kind/path/message), matching
        ``schema/preflight_verdict.schema.json``'s intentionally open
        ``exceptions[]`` item shape.
    """
    result = run_git(repo_root, "status", "--porcelain=v1", "-z")
    if result.returncode != 0:
        return (
            [
                f"required reference does not resolve: '{repo_root}' is not a "
                f"readable git working tree ({result.stderr.strip()})"
            ],
            [],
        )

    tolerated = set(tolerated_untracked_paths)
    prefixes = tuple(tolerated_untracked_prefixes)
    blocking_findings: list[str] = []
    exceptions: list[dict[str, str]] = []

    entries = result.stdout.split("\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        status_code, repo_relative_path = entry[:2], entry[3:]
        # porcelain -z renames/copies emit the ORIGINAL path as the next NUL
        # field; consume it so it is never read as a spurious bare entry.
        if status_code and status_code[0] in ("R", "C"):
            index += 1
        if status_code == "??":
            if repo_relative_path in tolerated:
                exceptions.append(
                    {
                        "kind": "declared_tolerated_untracked",
                        "path": repo_relative_path,
                        "message": (
                            "declared-tolerated untracked file present: "
                            f"{repo_relative_path}"
                        ),
                    }
                )
            elif any(repo_relative_path.startswith(prefix) for prefix in prefixes):
                exceptions.append(
                    {
                        "kind": "declared_tolerated_untracked_prefix",
                        "path": repo_relative_path,
                        "message": (
                            "untracked file under a declared-tolerated prefix: "
                            f"{repo_relative_path}"
                        ),
                    }
                )
            else:
                blocking_findings.append(
                    f"untracked change not declared tolerated: {repo_relative_path}"
                )
        else:
            blocking_findings.append(
                f"uncommitted tracked change ({status_code.strip()}): {repo_relative_path}"
            )

    return blocking_findings, exceptions


def collect_required_reference_findings(repo_root: str) -> list[str]:
    """Return one blocking finding for each required schema path not resolvable.

    Implements ecosystem/01_clean_state_preflight.md Sec 4 bullet 2: a
    required evidence/reference path that is missing, unreadable, or does not
    resolve to an existing path is its own blocking finding. This minimum CLI
    requires the two schemas its own output must validate against.

    NDEBT-021.2: a required reference must resolve to a READABLE REGULAR FILE.
    The former ``os.path.exists`` accepted a *directory* sitting at the path
    (e.g. a stray ``schema/preflight_verdict.schema.json/`` directory), which is
    not a usable schema; ``os.path.isfile`` plus an ``os.access`` read-permission
    probe rejects both a directory and an unreadable file, so a non-file at a
    required path is correctly blocking rather than silently accepted.
    """
    findings: list[str] = []
    for relative_path in REQUIRED_REFERENCE_PATHS:
        absolute_path = os.path.join(repo_root, relative_path)
        if not (os.path.isfile(absolute_path) and os.access(absolute_path, os.R_OK)):
            findings.append(f"required reference missing or unreadable: {relative_path}")
    return findings


def collect_head_resolution_findings(repo_root: str) -> list[str]:
    """Return a blocking finding if ``repo_root``'s git HEAD does not resolve.

    NDEBT-021.2: an unresolved HEAD (e.g. an unborn repository with zero
    commits) previously slipped through silently -- ``resolve_head_revision``
    falls back to the literal string ``"unknown"`` and the baseline was
    synthesized anchored to that non-revision. A baseline anchored to an
    unresolvable revision is not a valid baseline, so an unresolved HEAD is
    surfaced here as its own blocking finding; ``resolve_head_revision``'s
    ``"unknown"`` fallback is thereby unreachable on the non-blocking path and
    remains only as a defensive backstop.
    """
    result = run_git(repo_root, "rev-parse", "HEAD")
    if result.returncode != 0:
        return [
            "required reference does not resolve: git HEAD does not resolve "
            f"({result.stderr.strip()})"
        ]
    return []


def resolve_head_revision(repo_root: str) -> str:
    """Return ``repo_root``'s current ``git rev-parse HEAD``, or ``"unknown"``.

    Never raises: an unresolved HEAD (e.g. a repository with zero commits) is
    reported as the literal string ``"unknown"`` rather than crashing the
    baseline-synthesis step, since a blocking required-reference or
    clean-state finding will already have surfaced the underlying problem.
    """
    result = run_git(repo_root, "rev-parse", "HEAD")
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def find_repository_revision_inconsistencies(document: dict[str, object]) -> list[str]:
    """Return same-repository revision-inconsistency messages for a baseline.

    NDEBT-023 / ecosystem/02_evidence_baseline.md Sec 4: a baseline MUST NOT
    declare inconsistent revisions for the same repository. Checked within
    ``repository_references``: all entries sharing the same explicit
    ``repository`` identifier MUST declare the same ``revision``. Revisions are
    compared only among entries KNOWN to be the same repository (by the explicit
    key), so distinct repositories at distinct revisions -- and the
    ``dependency_references`` tool-version "revision", never grouped here at all
    -- can never trigger a false positive. The rule is a relational cross-item
    constraint not cleanly expressible in JSON Schema, so it is enforced here
    (and mirrored in ``tools/validate.sh``'s C12) rather than in the schema.
    """
    revisions_by_repository: dict[str, set[str]] = {}
    references = document.get("repository_references", [])
    if isinstance(references, list):
        for item in references:
            if not isinstance(item, dict):
                continue
            repository = item.get("repository")
            revision = item.get("revision")
            if not isinstance(repository, str) or not isinstance(revision, str):
                continue
            revisions_by_repository.setdefault(repository, set()).add(revision)
    return [
        f"repository '{repository}' declares inconsistent revisions across "
        f"repository_references: {sorted(revisions)}"
        for repository, revisions in sorted(revisions_by_repository.items())
        if len(revisions) > 1
    ]


def load_ci_reference(path: str) -> dict[str, object]:
    """Load and validate a caller-supplied CI-run reference (``--ci-run-file``).

    NDEBT-017: the tool itself performs no CI lookup (no network call); a caller
    or orchestrator that has already resolved a real CI run supplies it here.
    The file MUST parse to a JSON object carrying at least a non-empty
    ``revision`` and ``timestamp`` (the baseline reference-item contract,
    ``schema/ecosystem_baseline.schema.json`` Sec 4); any other fields (system,
    conclusion, url, ...) are preserved verbatim. A missing file, unparseable
    JSON, a non-object, or a missing required key is a usage error (exit 64),
    never a silently fabricated reference.

    Raises:
        PreflightUsageError: on an unreadable file, invalid JSON, a non-object,
            or a missing/empty required key.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            reference = json.load(handle)
    except OSError as error:
        raise PreflightUsageError(f"--ci-run-file could not be read: {error}")
    except json.JSONDecodeError as error:
        raise PreflightUsageError(f"--ci-run-file is not valid JSON: {error}")
    if not isinstance(reference, dict):
        raise PreflightUsageError("--ci-run-file must contain a JSON object")
    for required_key in ("revision", "timestamp"):
        value = reference.get(required_key)
        if not isinstance(value, str) or not value:
            raise PreflightUsageError(
                f"--ci-run-file object is missing a non-empty '{required_key}' "
                "(a CI reference must be anchored to a revision and timestamp)"
            )
    return reference


def build_baseline_document(
    execution_id: str,
    repo_root: str,
    output_dir: str,
    captured_at: str,
    ci_reference: dict[str, object] | None = None,
) -> dict[str, object]:
    """Synthesize a schema-valid baseline document anchored to real, observed state.

    Populates all six required baseline field categories
    (``schema/ecosystem_baseline.schema.json``), each item carrying a real,
    independently-observable ``revision`` and the run's own ``timestamp`` --
    never a fabricated or unlabelled value:

    - ``framework_references`` / ``repository_references`` both anchor to
      ``repo_root``'s own ``git rev-parse HEAD`` (the minimum-viable default:
      in self-fixture/single-repository mode the framework IS the repository
      under inspection).
    - ``dependency_references`` anchors to this CLI's own Python runtime
      version, the one real, inspectable tooling dependency the deterministic
      collection itself relies on.
    - ``ci_references``: when ``ci_reference`` is supplied (``--ci-run-file``,
      NDEBT-017) it is used verbatim (already validated to carry revision +
      timestamp), tagged with a ``source`` marker; otherwise it anchors to the
      HEAD revision with an explicit, honest ``note`` documenting that this
      minimum CLI resolves no real CI run itself -- a documented limitation,
      never a fabricated "verified" claim.
    - ``planning_references`` anchors to ``docs/planning/manifest.json``'s
      path at the same HEAD revision.
    - ``evidence_references`` anchors to this run's own collection-log.txt
      evidence file under ``output_dir``.

    Raises:
        RuntimeError: if the synthesized document declares inconsistent
            revisions for the same repository (NDEBT-023). The self-fixture path
            anchors every reference to one HEAD and never triggers it; the guard
            is a defensive invariant for a future multi-repository extension.
    """
    head_revision = resolve_head_revision(repo_root)
    repository_name = os.path.basename(os.path.abspath(repo_root))
    evidence_log_path = os.path.join(output_dir, "collection-log.txt")

    if ci_reference is not None:
        ci_entry: dict[str, object] = dict(ci_reference)
        ci_entry.setdefault("source", "caller-supplied (--ci-run-file)")
    else:
        ci_entry = {
            "revision": head_revision,
            "timestamp": captured_at,
            "system": "self-fixture (no externally-verified CI run available)",
            "note": (
                "KNOWN LIMITATION: this minimum-viable CLI does not itself resolve "
                "a real CI run; supply --ci-run-file with a caller-resolved CI "
                "reference to anchor this field (NDEBT-017)."
            ),
        }

    document: dict[str, object] = {
        "execution_id": execution_id,
        "captured_at": captured_at,
        "framework_references": [
            {
                "revision": head_revision,
                "timestamp": captured_at,
                "name": f"{repository_name} working tree (self-referential minimum-viable default)",
            }
        ],
        "repository_references": [
            {"revision": head_revision, "timestamp": captured_at, "repository": repository_name}
        ],
        "dependency_references": [
            {
                "revision": platform.python_version(),
                "timestamp": captured_at,
                "dependency": "python3 runtime (this CLI's own deterministic-collection dependency)",
            }
        ],
        "ci_references": [ci_entry],
        "planning_references": [
            {"revision": head_revision, "timestamp": captured_at, "path": "docs/planning/manifest.json"}
        ],
        "evidence_references": [
            {"revision": head_revision, "timestamp": captured_at, "path": evidence_log_path}
        ],
    }

    inconsistencies = find_repository_revision_inconsistencies(document)
    if inconsistencies:
        raise RuntimeError(
            "internal invariant violated -- the synthesized baseline declares "
            "inconsistent same-repository revisions (NDEBT-023): "
            + "; ".join(inconsistencies)
        )
    return document


def write_json_document(path: str, document: dict[str, object]) -> None:
    """Write ``document`` to ``path`` as indented JSON with a trailing newline."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2)
        handle.write("\n")


STALE_OUTPUT_ARTIFACTS: tuple[str, ...] = (
    "preflight.json",
    "preflight.pending.json",
    "baseline.json",
)


def clean_output_dir(output_dir: str) -> None:
    """Remove any stale verdict/baseline artifacts from a reused output dir.

    NDEBT-021.4: a reused ``--output-dir`` could otherwise retain a prior run's
    ``preflight.json`` / ``preflight.pending.json`` / ``baseline.json`` alongside
    this run's, producing a contradictory mix -- e.g. a FAIL ``preflight.json``
    next to a stale PASS-run ``baseline.json``, or an approved ``preflight.json``
    next to a stale ``preflight.pending.json``. Each run pre-cleans exactly the
    three artifact names it may write, so the directory reflects only the current
    run. Nothing else in the directory is touched (evidence logs and any
    caller-supplied files are left intact).
    """
    for artifact_name in STALE_OUTPUT_ARTIFACTS:
        artifact_path = os.path.join(output_dir, artifact_name)
        if os.path.isfile(artifact_path):
            os.remove(artifact_path)


def write_collection_log(
    output_dir: str,
    execution_id: str,
    repo_root: str,
    captured_at: str,
    blocking_findings: Sequence[str],
    exceptions: Sequence[dict[str, str]],
) -> None:
    """Write the run's plain-text evidence log to ``output_dir/collection-log.txt``."""
    lines = [
        f"ecosystem_preflight.py collection log -- execution_id={execution_id}",
        f"repo_root={repo_root}",
        f"captured_at={captured_at}",
        f"blocking_findings={list(blocking_findings)}",
        f"exceptions={list(exceptions)}",
    ]
    with open(os.path.join(output_dir, "collection-log.txt"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def build_argument_parser() -> _UsageErrorArgumentParser:
    """Construct this CLI's argument parser."""
    parser = _UsageErrorArgumentParser(
        prog="ecosystem_preflight.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--execution-id",
        required=True,
        help="The ecosystem-cycle execution identifier this preflight run belongs to.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help=(
            "Directory where preflight.json / baseline.json / collection-log.txt "
            "are written (created if absent). Never defaults into .agent/ -- "
            "the real .agent/reconciliation/<execution-id>/ write is a later "
            "feature's dogfood-run scope."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "The git working tree to inspect. Defaults to the current directory, "
            "UNLESS --self-fixture is given with no explicit --repo-root, in which "
            "case it auto-resolves to this script's own repository. An explicit "
            "'.' is honored even under --self-fixture (NDEBT-021.3: the former "
            "default='.' made an explicit '.' indistinguishable from the default)."
        ),
    )
    parser.add_argument(
        "--self-fixture",
        action="store_true",
        help=(
            "Auto-resolve --repo-root (when not also explicitly given) to the "
            "repository this script itself lives inside, for framework dogfooding."
        ),
    )
    parser.add_argument(
        "--tolerate-untracked",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "A repo-relative path of an untracked file the operator has "
            "explicitly declared tolerated (EXACT match, including git's "
            "collapsed 'dir/' entry for an entirely-untracked directory). "
            "Repeatable."
        ),
    )
    parser.add_argument(
        "--tolerate-untracked-prefix",
        action="append",
        default=[],
        metavar="PREFIX",
        help=(
            "A repo-relative path PREFIX; any untracked file whose path begins "
            "with it is declared tolerated (surfaced as a non-blocking exception "
            "of kind declared_tolerated_untracked_prefix). Additive to "
            "--tolerate-untracked's exact-match set; repeatable. Lets a run "
            "tolerate a whole in-flight artifact directory by one declared prefix "
            "rather than enumerating each file (NDEBT-018.1)."
        ),
    )
    parser.add_argument(
        "--ci-run-file",
        help=(
            "Path to a JSON file describing a caller-resolved CI run, used to "
            "anchor the baseline's ci_references instead of the honest "
            "KNOWN-LIMITATION default. The object MUST carry a non-empty "
            "'revision' and 'timestamp' (the baseline reference-item contract); "
            "other fields (system, conclusion, url, ...) pass through. The tool "
            "performs no network call -- the caller/orchestrator, which already "
            "resolves CI runs, supplies the reference (NDEBT-017)."
        ),
    )
    parser.add_argument(
        "--operator-approver",
        help="Identity of the operator approving a PASS_WITH_EXCEPTIONS verdict.",
    )
    parser.add_argument(
        "--operator-authorization",
        help="The operator's verbatim authorization text or a reference to it.",
    )
    parser.add_argument(
        "--operator-approved-at",
        help="Timestamp of the operator's approval decision (defaults to the run's own clock read).",
    )
    return parser


def main(argv: Sequence[str]) -> int:
    """Run the CLI and return its process exit code (see the module docstring's table)."""
    parser = build_argument_parser()
    try:
        args = parser.parse_args(list(argv))
    except PreflightUsageError as usage_error:
        print(f"usage error: {usage_error}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    try:
        if args.self_fixture and args.repo_root is None:
            repo_root = resolve_self_fixture_repo_root(__file__)
        else:
            repo_root = args.repo_root if args.repo_root is not None else "."
        repo_root = os.path.abspath(repo_root)
        ci_reference = load_ci_reference(args.ci_run_file) if args.ci_run_file else None
    except PreflightUsageError as usage_error:
        print(f"usage error: {usage_error}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    os.makedirs(args.output_dir, exist_ok=True)
    clean_output_dir(args.output_dir)
    captured_at = format_iso8601(read_utc_now())

    blocking_findings, exceptions = collect_git_clean_state_findings(
        repo_root, args.tolerate_untracked, args.tolerate_untracked_prefix
    )
    blocking_findings += collect_required_reference_findings(repo_root)
    blocking_findings += collect_head_resolution_findings(repo_root)

    write_collection_log(
        args.output_dir, args.execution_id, repo_root, captured_at, blocking_findings, exceptions
    )

    if blocking_findings:
        write_json_document(
            os.path.join(args.output_dir, "preflight.json"),
            {
                "verdict": "FAIL",
                "execution_id": args.execution_id,
                "generated_at": captured_at,
                "blocking_findings": blocking_findings,
            },
        )
        print(f"PREFLIGHT VERDICT: FAIL ({len(blocking_findings)} blocking finding(s))")
        return EXIT_FAIL

    if exceptions:
        operator_has_approved = bool(args.operator_approver and args.operator_authorization)
        if not operator_has_approved:
            write_json_document(
                os.path.join(args.output_dir, "preflight.pending.json"),
                {
                    "verdict": "PASS_WITH_EXCEPTIONS",
                    "execution_id": args.execution_id,
                    "generated_at": captured_at,
                    "exceptions": exceptions,
                    "status": "PENDING_OPERATOR_APPROVAL",
                },
            )
            print(
                "PREFLIGHT VERDICT: PASS_WITH_EXCEPTIONS (pending operator approval) -- "
                "re-invoke with --operator-approver and --operator-authorization"
            )
            return EXIT_PASS_WITH_EXCEPTIONS_PENDING

        write_json_document(
            os.path.join(args.output_dir, "preflight.json"),
            {
                "verdict": "PASS_WITH_EXCEPTIONS",
                "execution_id": args.execution_id,
                "generated_at": captured_at,
                "exceptions": exceptions,
                "operator_approval": {
                    "approver": args.operator_approver,
                    "approved_at": args.operator_approved_at or captured_at,
                    "authorization": args.operator_authorization,
                },
            },
        )
        write_json_document(
            os.path.join(args.output_dir, "baseline.json"),
            build_baseline_document(
                args.execution_id, repo_root, args.output_dir, captured_at, ci_reference
            ),
        )
        print("PREFLIGHT VERDICT: PASS_WITH_EXCEPTIONS (approved)")
        return EXIT_PASS_WITH_EXCEPTIONS_APPROVED

    write_json_document(
        os.path.join(args.output_dir, "preflight.json"),
        {"verdict": "PASS", "execution_id": args.execution_id, "generated_at": captured_at},
    )
    write_json_document(
        os.path.join(args.output_dir, "baseline.json"),
        build_baseline_document(
            args.execution_id, repo_root, args.output_dir, captured_at, ci_reference
        ),
    )
    print("PREFLIGHT VERDICT: PASS")
    return EXIT_PASS


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
