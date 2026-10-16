#!/usr/bin/env python3
"""Gate the bug-fix and small-change start paths.

The feature path stays on methodology/01_execution.md. This tool does not
approve a feature contract and it does not skip either feature loop.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

FRAMEWORK = Path(__file__).resolve().parents[1]
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
APPROVED_CONTRACT_STATUSES = frozenset({"approved", "implemented", "complete"})


def main(argv: list[str] | None = None) -> int:
    """Run a begin or done decision for one non-feature path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decision", choices=("begin", "done"))
    parser.add_argument("kind", choices=("bugfix", "small-change"))
    parser.add_argument("--id", required=True, dest="path_id")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root whose .agent directory holds the path records.",
    )
    args = parser.parse_args(argv)
    try:
        message = decide(args.decision, args.kind, args.path_id, args.root.resolve())
    except StartPathError as error:
        print(str(error), file=sys.stderr)
        return error.exit_code
    print(message)
    return 0


def decide(decision: str, kind: str, path_id: str, root: Path) -> str:
    """Return the success sentence for a path decision."""
    if not ID_PATTERN.fullmatch(path_id):
        raise StartPathError("identifier is not a single safe path token", 2)
    if kind == "bugfix":
        cause, scope = load_bugfix(root, path_id)
        if decision == "begin":
            return f"bugfix {cause['id']}: implementation may begin"
        load_passing_qa(root, path_id)
        return f"bugfix {scope['id']}: recorded verification result exists"
    intent = load_intent(root, path_id)
    if decision == "begin":
        return f"small-change {intent['id']}: implementation may begin"
    load_passing_qa(root, path_id)
    return f"small-change {intent['id']}: recorded verification result exists"


def load_bugfix(root: Path, path_id: str) -> tuple[dict, dict]:
    """Load and cross-check the cause and scope records."""
    cause = load_record(
        root,
        Path(".agent") / "evidence" / f"{path_id}-cause.json",
        "bugfix_cause.schema.json",
    )
    scope = load_record(
        root,
        Path(".agent") / "evidence" / f"{path_id}-scope.json",
        "bugfix_scope.schema.json",
    )
    if cause["id"] != path_id or scope["id"] != path_id:
        raise StartPathError("cause or scope id does not match --id", 1)
    contract_id = scope.get("contract_id")
    if contract_id is not None:
        require_inside_contract(root, contract_id, scope["files"])
    for relative in scope["files"]:
        require_project_path(relative)
    return cause, scope


def load_intent(root: Path, path_id: str) -> dict:
    """Load a small-change intent and refuse work that needs a feature contract."""
    intent = load_record(
        root,
        Path(".agent") / "evidence" / f"{path_id}-intent.json",
        "small_change_intent.schema.json",
    )
    if intent["id"] != path_id:
        raise StartPathError("intent id does not match --id", 1)
    if intent["needs_new_contract"] is True:
        raise StartPathError(
            "needs_new_contract is true; use the feature path",
            1,
        )
    return intent


def require_inside_contract(root: Path, contract_id: str, files: list[str]) -> None:
    """Require an already approved contract that names every scoped file."""
    if not ID_PATTERN.fullmatch(contract_id):
        raise StartPathError("contract_id is not a single safe path token", 1)
    contract = load_record(
        root,
        Path(".agent") / "contracts" / f"{contract_id}.json",
        "contract.schema.json",
    )
    if contract.get("status") not in APPROVED_CONTRACT_STATUSES:
        raise StartPathError(
            "named contract is not already approved",
            1,
        )
    allowed: set[str] = set()
    scope = contract.get("scope")
    if isinstance(scope, dict):
        for key in ("files_create", "files_modify"):
            entries = scope.get(key)
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, dict) and isinstance(entry.get("path"), str):
                    allowed.add(entry["path"])
    outside = [path for path in files if path not in allowed]
    if outside:
        raise StartPathError(
            "scoped files are not inside the named contract: " + ", ".join(outside),
            1,
        )


def load_passing_qa(root: Path, path_id: str) -> None:
    """Require a schema-valid passing QA verdict with one real evidence file."""
    verdict = load_record(
        root,
        Path(".agent") / "qa" / f"{path_id}.json",
        "qa_verdict.schema.json",
    )
    if not qa_passes(verdict):
        raise StartPathError("recorded verification result does not pass", 1)
    evidence = listed_evidence(verdict)
    if not evidence:
        raise StartPathError("recorded verification result names no evidence file", 1)
    for relative in evidence:
        path = resolve_project_file(root, relative)
        if not path.is_file():
            raise StartPathError("evidence file does not exist: " + relative, 1)


def qa_passes(verdict: dict) -> bool:
    """Apply the pass rule for either shipped QA verdict shape."""
    if verdict.get("qa_pass") is True:
        final_verdict = verdict.get("final_verdict")
        approved = isinstance(final_verdict, dict) and final_verdict.get("approved") is True
        blocked = any(
            verdict.get(key)
            for key in (
                "issues",
                "unsupported_claims",
                "missing_acceptance_coverage",
                "required_fixes",
            )
        )
        return approved and not blocked
    if verdict.get("verdict") == "pass":
        return not verdict.get("required_fixes")
    return False


def listed_evidence(verdict: dict) -> list[str]:
    """Collect evidence paths named by either QA verdict shape."""
    paths: list[str] = []
    files = verdict.get("evidence_files")
    if isinstance(files, list):
        paths.extend(item for item in files if isinstance(item, str))
    checks = verdict.get("checks")
    if isinstance(checks, list):
        for check in checks:
            if isinstance(check, dict) and isinstance(check.get("evidence"), str):
                paths.append(check["evidence"])
    return paths


def load_record(root: Path, relative: Path, schema_name: str) -> dict:
    """Read one JSON record and validate it against a framework schema."""
    path = resolve_project_file(root, relative.as_posix())
    if not path.is_file():
        raise StartPathError("required record does not exist: " + relative.as_posix(), 1)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise StartPathError(
            f"{relative.as_posix()} is not JSON: {error.msg}",
            1,
        ) from error
    if not isinstance(data, dict):
        raise StartPathError(relative.as_posix() + " must be a JSON object", 1)
    schema_path = FRAMEWORK / "schema" / schema_name
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(data)
    except SchemaError as error:
        raise StartPathError(f"schema {schema_name} is invalid: {error.message}", 2) from error
    except OSError as error:
        raise StartPathError(f"schema {schema_name} is unreadable: {error}", 2) from error
    except ValidationError as error:
        raise StartPathError(
            f"{relative.as_posix()} failed {schema_name}: {error.message}",
            1,
        ) from error
    return data


def resolve_project_file(root: Path, relative: str) -> Path:
    """Resolve a repository-relative file and reject paths that leave root."""
    require_project_path(relative)
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise StartPathError("path leaves the project root: " + relative, 1)
    return path


def require_project_path(relative: str) -> None:
    """Reject absolute paths and parent-directory segments."""
    if not relative or relative.startswith(("/", "\\")):
        raise StartPathError("path must be project-relative: " + relative, 1)
    if ".." in Path(relative).parts:
        raise StartPathError("path must not contain '..': " + relative, 1)


class StartPathError(Exception):
    """A start-path decision failed closed."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


if __name__ == "__main__":
    sys.exit(main())
