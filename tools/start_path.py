#!/usr/bin/env python3
"""Gate task start paths, lightweight amendments, preflight, capture, and status.

Supports:
- Legacy and direct path gating:
    tools/start_path.py begin|done trivial|bugfix|small-change --id <id> [--root <root>]
- Semantic task classification across 5 routes (trivial, bugfix, small-change,
  standard-feature, high-risk):
    tools/start_path.py classify [--files FILE ...] [--bugfix] [--editorial] ...
- Lightweight contract amendments when goals and invariants are unchanged:
    tools/start_path.py amend-contract --contract <id> --amendment <file> [--apply]
- Review verdict validation (blocking vs. advisory_minor):
    tools/start_path.py check-verdict --verdict <file> [--ledger <file> ...]
- Capability preflight before governed attempts:
    tools/start_path.py preflight [--require-sandbox] [--root <root>]
- Safe exclusive per-execution command evidence capture:
    tools/start_path.py capture --id <id> --step <step> --attempt <n> --output-dir <dir> -- <cmd> ...
- Concise read-only status/readiness view:
    tools/start_path.py status [--format json|markdown] [--root <root>]
- Operational receipt transition / failure routing:
    tools/start_path.py resume --policy <file> [--receipt <file>] [--apply] [--root <root>]
"""

from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import os
import platform
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

FRAMEWORK = Path(__file__).resolve().parents[1]
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
APPROVED_CONTRACT_STATUSES = frozenset({"approved", "implemented", "complete"})

HIGH_RISK_PREFIXES = (
    ".nizam/",
    "tools/linux_trial_sandbox.sh",
    "tools/isolated_trial_adapter.py",
    "tools/convergent_review.py",
    "tools/workflow_assurance.py",
    "tools/runtime_session.py",
    ".github/scripts/test_sandbox_boundaries.py",
    "methodology/10_live_runtime_sessions.md",
    "methodology/11_sbcl_runtime_binding.md",
)

TRIVIAL_DOC_PREFIXES = (
    "docs/",
    "README.md",
    "CHANGELOG.md",
    "CONTEXT.md",
)

ROUTE_GATES: dict[str, list[str]] = {
    "trivial": [
        "start_path:begin:trivial",
        "validate.sh",
        "start_path:done:trivial",
    ],
    "bugfix": [
        "start_path:begin:bugfix",
        "targeted_reproducer_and_regression_test",
        "validate.sh",
        "independent_acceptance_verdict",
        "start_path:done:bugfix",
    ],
    "small-change": [
        "start_path:begin:small-change",
        "targeted_verification",
        "validate.sh",
        "independent_acceptance_verdict",
        "start_path:done:small-change",
    ],
    "standard-feature": [
        "loop1:contract_approval",
        "loop2:validator_mode_b",
        "loop2:evaluator_qa",
        "loop2:evidence_capture",
    ],
    "high-risk": [
        "loop1:contract_approval",
        "capability_preflight",
        "loop2:validator_mode_b",
        "loop2:evaluator_qa",
        "convergent_review_or_isolation_suite",
        "loop2:evidence_capture",
    ],
}


def canonical_bytes(value: Any) -> bytes:
    """Serialize a JSON value into canonical UTF-8 bytes."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Return lowercase SHA-256 hex digest."""
    return hashlib.sha256(data).hexdigest()


def utc_now_iso() -> str:
    """Return compact UTC ISO-8601 timestamp."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str] | None = None) -> int:
    """Dispatch legacy begin/done or extended start_path subcommands."""
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv and raw_argv[0] in ("begin", "done"):
        return _main_begin_done(raw_argv)
    if raw_argv and raw_argv[0] in (
        "classify",
        "amend-contract",
        "check-verdict",
        "preflight",
        "capture",
        "status",
        "resume",
    ):
        return _main_extended(raw_argv)
    # Default help/error compatibly when no valid command is given
    return _main_begin_done(raw_argv)


def _main_begin_done(argv: list[str]) -> int:
    """Run a begin or done decision for one non-feature path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decision", choices=("begin", "done"))
    parser.add_argument("kind", choices=("trivial", "bugfix", "small-change"))
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


def _main_extended(argv: list[str]) -> int:
    """Run extended task routing, amendment, preflight, capture, status, or resume commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="subcommand", required=True)

    classify_p = sub.add_parser("classify", help="Classify a task into one of the 5 semantic routes.")
    classify_p.add_argument("--files", nargs="*", default=[], help="Repository-relative files in scope.")
    classify_p.add_argument("--bugfix", action="store_true", help="Task repairs a reproducible defect.")
    classify_p.add_argument("--editorial", action="store_true", help="Task is editorial/comment/typo only.")
    classify_p.add_argument("--needs-new-contract", action="store_true", help="Task introduces new contract obligations.")
    classify_p.add_argument("--touches-schema", action="store_true", help="Task modifies schemas or public interfaces.")
    classify_p.add_argument("--touches-security", action="store_true", help="Task touches security/isolation/authority boundaries.")
    classify_p.add_argument("--touches-runtime", action="store_true", help="Task touches persistent-runtime session semantics.")

    amend_p = sub.add_parser("amend-contract", help="Validate and optionally apply a lightweight contract amendment.")
    amend_p.add_argument("--contract", required=True, dest="contract_id")
    amend_p.add_argument("--amendment", required=True, type=Path)
    amend_p.add_argument("--apply", action="store_true")
    amend_p.add_argument("--root", type=Path, default=Path.cwd())

    verdict_p = sub.add_parser("check-verdict", help="Validate blocking vs. advisory review verdict semantics.")
    verdict_p.add_argument("--verdict", required=True, type=Path)
    verdict_p.add_argument("--ledger", type=Path)
    verdict_p.add_argument("--expected-repository")
    verdict_p.add_argument("--expected-head-sha")

    preflight_p = sub.add_parser("preflight", help="Run capability preflight before a governed attempt.")
    preflight_p.add_argument("--require-sandbox", action="store_true")
    preflight_p.add_argument("--root", type=Path, default=Path.cwd())

    capture_p = sub.add_parser("capture", help="Capture command output and provenance to an exclusive path.")
    capture_p.add_argument("--id", required=True, dest="task_id")
    capture_p.add_argument("--step", required=True)
    capture_p.add_argument("--attempt", required=True, type=int)
    capture_p.add_argument("--output-dir", required=True, type=Path)
    capture_p.add_argument("--candidate-sha256", default=None)
    capture_p.add_argument("--agent-id", default="nizam-local-agent")
    capture_p.add_argument("--session-id", default="local-session")
    capture_p.add_argument("--timeout-sec", type=float, default=None)
    capture_p.add_argument("--root", type=Path, default=Path.cwd())
    capture_p.add_argument("cmd", nargs=argparse.REMAINDER)

    status_p = sub.add_parser("status", help="Generate a concise read-only status/readiness view.")
    status_p.add_argument("--format", choices=("json", "markdown"), default="json")
    status_p.add_argument("--root", type=Path, default=Path.cwd())

    resume_p = sub.add_parser("resume", help="Verify stage receipt and plan/apply state transition.")
    resume_p.add_argument("--policy", required=True, type=Path)
    resume_p.add_argument("--receipt", type=Path, default=None)
    resume_p.add_argument("--state", type=Path, default=None)
    resume_p.add_argument("--apply", action="store_true")
    resume_p.add_argument("--root", type=Path, default=Path.cwd())

    args = parser.parse_args(argv)
    try:
        if args.subcommand == "classify":
            result = classify_task(
                files=args.files,
                is_bugfix=args.bugfix,
                is_editorial=args.editorial,
                needs_new_contract=args.needs_new_contract,
                touches_schema=args.touches_schema,
                touches_security=args.touches_security,
                touches_runtime=args.touches_runtime,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.subcommand == "amend-contract":
            amendment_data = _read_json_file(args.amendment)
            result = amend_contract(
                args.root.resolve(),
                args.contract_id,
                amendment_data,
                apply_changes=args.apply,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.subcommand == "check-verdict":
            verdict_data = _read_json_file(args.verdict)
            ledger_data = _read_json_file(args.ledger) if args.ledger else None
            result = validate_review_verdict(
                verdict_data,
                ledger=ledger_data,
                expected_repository=args.expected_repository,
                expected_head_sha=args.expected_head_sha,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["approved"] else 1
        if args.subcommand == "preflight":
            result = preflight_capabilities(
                args.root.resolve(),
                require_sandbox=args.require_sandbox,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["ok"] else 1
        if args.subcommand == "capture":
            cmd = list(args.cmd)
            if cmd and cmd[0] == "--":
                cmd = cmd[1:]
            if not cmd:
                raise StartPathError("capture requires a command after --", 2)
            result = capture_command_evidence(
                args.root.resolve(),
                task_id=args.task_id,
                step=args.step,
                attempt=args.attempt,
                output_dir=args.output_dir,
                argv=cmd,
                candidate_sha256=args.candidate_sha256,
                agent_id=args.agent_id,
                session_id=args.session_id,
                timeout_sec=args.timeout_sec,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["outcome"] == "success" else 1
        if args.subcommand == "status":
            view = generate_status_view(args.root.resolve())
            if args.format == "markdown":
                print(render_status_markdown(view))
            else:
                print(json.dumps(view, indent=2, sort_keys=True))
            return 0
        if args.subcommand == "resume":
            result = resume_from_receipt(
                args.root.resolve(),
                policy_path=args.policy,
                receipt_path=args.receipt,
                state_path=args.state,
                apply_changes=args.apply,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
    except StartPathError as error:
        print(str(error), file=sys.stderr)
        return error.exit_code
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
    if kind == "trivial":
        intent = load_trivial_intent(root, path_id)
        if decision == "begin":
            return f"trivial {intent['id']}: implementation may begin"
        load_passing_qa(root, path_id)
        return f"trivial {intent['id']}: recorded verification result exists"
    intent = load_intent(root, path_id)
    if decision == "begin":
        return f"small-change {intent['id']}: implementation may begin"
    load_passing_qa(root, path_id)
    return f"small-change {intent['id']}: recorded verification result exists"


def classify_task(
    *,
    files: list[str] | None = None,
    is_bugfix: bool = False,
    is_editorial: bool = False,
    needs_new_contract: bool = False,
    touches_schema: bool = False,
    touches_security: bool = False,
    touches_runtime: bool = False,
) -> dict[str, Any]:
    """Classify a change into one of 5 semantic routes (never by line count alone)."""
    scoped = [f.strip() for f in (files or []) if f and f.strip()]
    for path in scoped:
        require_project_path(path)
        if path == ".nizam" or path.startswith(".nizam/"):
            raise StartPathError("installed .nizam/ payload is immutable; do not edit .nizam/ directly", 1)

    reasons: list[str] = []
    high_risk_files = [
        p for p in scoped
        if any(p == prefix or p.startswith(prefix) for prefix in HIGH_RISK_PREFIXES)
    ]
    schema_files = [p for p in scoped if p.startswith("schema/") or p == "NIZAM.json"]
    doc_only_files = bool(scoped) and all(
        any(p == prefix or p.startswith(prefix) for prefix in TRIVIAL_DOC_PREFIXES)
        or p.endswith(".md")
        for p in scoped
    ) and not any(
        p.startswith(("standard/", "methodology/", "tools/", "schema/", "ecosystem/"))
        for p in scoped
    )

    if touches_security or touches_runtime or high_risk_files:
        route = "high-risk"
        if touches_security:
            reasons.append("touches security, isolation, or authority verification boundary")
        if touches_runtime:
            reasons.append("touches persistent-runtime session boundary")
        if high_risk_files:
            reasons.append("touches high-risk files: " + ", ".join(high_risk_files))
    elif needs_new_contract or touches_schema or schema_files:
        route = "standard-feature"
        if needs_new_contract:
            reasons.append("introduces new contract obligations")
        if touches_schema or schema_files:
            reasons.append("modifies schema or capability index")
    elif is_bugfix:
        route = "bugfix"
        reasons.append("repairs reproducible defect within bounded scope")
    elif is_editorial and (not scoped or doc_only_files):
        route = "trivial"
        reasons.append("editorial or documentation-only adjustment with no contract/schema/tool impact")
    else:
        route = "small-change"
        reasons.append("bounded unambiguous change requiring no new feature contract")

    return {
        "route": route,
        "files": scoped,
        "reasons": reasons,
        "required_gates": ROUTE_GATES[route],
        "stopping_conditions": {
            "max_attempts": 3,
            "breaker_ref": "methodology/03_circuit_breaker.md",
            "comparator_subordinate": True,
            "pass_condition": (
                "All required_gates for route '" + route + "' exit 0 and blocking verdict arrays are empty."
            ),
            "halt_condition": (
                "Stop and escalate to human on 3rd failed attempt at any repeatable step; "
                "a 4th autonomous attempt is forbidden even if a comparator bar is not yet won."
            ),
        },
        "review_remit": {
            "blocking_fields": [
                "issues",
                "missing_acceptance_coverage",
                "unsupported_claims",
                "required_fixes",
            ],
            "advisory_fields": ["advisory_minor"],
            "evidence_required_for_blockers": True,
        },
    }


def amend_contract(
    root: Path,
    contract_id: str,
    amendment: dict[str, Any],
    *,
    apply_changes: bool = False,
) -> dict[str, Any]:
    """Validate and optionally apply a bounded mechanical amendment to an approved contract."""
    if not ID_PATTERN.fullmatch(contract_id):
        raise StartPathError("contract_id is not a single safe path token", 2)
    contract_rel = Path(".agent") / "contracts" / f"{contract_id}.json"
    contract_path = resolve_project_file(root, contract_rel.as_posix())
    if not contract_path.is_file():
        raise StartPathError("required record does not exist: " + contract_rel.as_posix(), 1)
    prior_bytes = contract_path.read_bytes()
    prior_sha256 = sha256_hex(prior_bytes)
    contract = load_record(root, contract_rel, "contract.schema.json")
    if contract.get("status") != "approved":
        raise StartPathError("only an approved contract may use lightweight amend-contract", 1)

    if not isinstance(amendment, dict):
        raise StartPathError("amendment must be a JSON object", 1)
    if amendment.get("contract_id") != contract_id:
        raise StartPathError("amendment contract_id does not match --contract", 1)
    if amendment.get("invariants_preserved") is not True:
        raise StartPathError("amendment requires invariants_preserved: true", 1)
    summary = amendment.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise StartPathError("amendment requires a non-empty summary", 1)
    for forbidden in ("feature_id", "non_goals", "status", "approvals"):
        if forbidden in amendment:
            raise StartPathError(f"lightweight amendment cannot modify {forbidden}; re-enter Loop 1", 1)

    updated = copy.deepcopy(contract)
    scope = updated.setdefault("scope", {"files_create": [], "files_modify": []})
    added_paths: list[str] = []
    for key, target_key in (("files_create_add", "files_create"), ("files_modify_add", "files_modify")):
        entries = amendment.get(key, [])
        if not isinstance(entries, list):
            raise StartPathError(f"{key} must be a list", 1)
        existing = {e["path"] for e in scope.get(target_key, []) if isinstance(e, dict) and "path" in e}
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("purpose"), str):
                raise StartPathError(f"{key} entries require path and purpose strings", 1)
            rel_path = entry["path"]
            require_project_path(rel_path)
            if rel_path.startswith(".nizam/") or rel_path in (
                "tools/linux_trial_sandbox.sh",
                "tools/isolated_trial_adapter.py",
            ):
                raise StartPathError(f"lightweight amendment cannot add protected security/payload path: {rel_path}", 1)
            if rel_path not in existing:
                scope[target_key].append({"path": rel_path, "purpose": entry["purpose"]})
                existing.add(rel_path)
                added_paths.append(rel_path)

    verification_updates = amendment.get("verification_updates", [])
    if not isinstance(verification_updates, list):
        raise StartPathError("verification_updates must be a list", 1)
    updated_tests: list[str] = []
    for item in verification_updates:
        if not isinstance(item, dict) or not isinstance(item.get("acceptance_test"), str) or not isinstance(item.get("command"), str):
            raise StartPathError("verification_updates entries require acceptance_test and command strings", 1)
        if not item["command"].strip():
            raise StartPathError("verification command must be non-empty", 1)
        matched = False
        for existing_v in updated.get("verification", []):
            if existing_v.get("acceptance_test") == item["acceptance_test"]:
                existing_v["command"] = item["command"]
                matched = True
                break
        if not matched:
            updated.setdefault("verification", []).append(
                {"acceptance_test": item["acceptance_test"], "command": item["command"]}
            )
        updated_tests.append(item["acceptance_test"])

    amendment_record = {
        "at": amendment.get("at") or utc_now_iso(),
        "by": amendment.get("by") or "start_path:amend-contract",
        "type": "lightweight-scope-or-verification-update",
        "summary": summary.strip(),
        "prior_contract_sha256": prior_sha256,
        "added_files": added_paths,
        "updated_verification": updated_tests,
        "invariants_preserved": True,
    }
    updated.setdefault("amendments", []).append(amendment_record)
    _validate_against_schema(updated, "contract.schema.json", contract_rel.as_posix())

    new_bytes = (json.dumps(updated, indent=2) + "\n").encode("utf-8")
    if apply_changes:
        contract_path.write_bytes(new_bytes)
    return {
        "contract_id": contract_id,
        "applied": bool(apply_changes),
        "prior_contract_sha256": prior_sha256,
        "amended_contract_sha256": sha256_hex(new_bytes),
        "added_files": added_paths,
        "updated_verification": updated_tests,
    }


def validate_review_verdict(
    verdict: dict[str, Any],
    *,
    ledger: dict[str, Any] | None = None,
    expected_repository: str | None = None,
    expected_head_sha: str | None = None,
) -> dict[str, Any]:
    """Validate blocking vs. advisory review verdict rules (reusing convergent_agf_verdict when ledger is supplied)."""
    if ledger is not None:
        try:
            import workflow_assurance as wa
        except ModuleNotFoundError:
            from tools import workflow_assurance as wa
        try:
            verdict = wa.convergent_agf_verdict(
                ledger,
                verdict,
                expected_repository=expected_repository or ledger.get("repository", ""),
                expected_head_sha=expected_head_sha or ledger.get("head_sha", ""),
            )
        except Exception as exc:
            raise StartPathError(f"convergent verdict mapping failed: {exc}", 1) from exc

    if not isinstance(verdict, dict):
        raise StartPathError("verdict must be a JSON object", 1)
    fv = verdict.get("final_verdict")
    if not isinstance(fv, dict) or not isinstance(fv.get("approved"), bool):
        raise StartPathError("final_verdict.approved must be a boolean", 1)

    blocking_keys = ("issues", "missing_acceptance_coverage", "unsupported_claims")
    for key in blocking_keys:
        if not isinstance(verdict.get(key), list):
            raise StartPathError(f"blocking field {key} must be an array", 1)
    if "required_fixes" in verdict and not isinstance(verdict["required_fixes"], list):
        raise StartPathError("required_fixes must be an array when present", 1)
    advisory = verdict.get("advisory_minor", [])
    if not isinstance(advisory, list):
        raise StartPathError("advisory_minor must be an array when present", 1)

    # Every blocking issue must carry concrete text or structured evidence (never empty/vacuous)
    for item in verdict["issues"]:
        if isinstance(item, str):
            if not item.strip():
                raise StartPathError("blocking issue string must not be empty", 1)
        elif isinstance(item, dict):
            has_detail = bool(item.get("description") or item.get("title") or item.get("evidence"))
            if not has_detail:
                raise StartPathError("blocking issue object must include description, title, or evidence", 1)
        else:
            raise StartPathError("blocking issue must be a non-empty string or object", 1)

    blocking_count = sum(len(verdict.get(k, [])) for k in blocking_keys) + len(verdict.get("required_fixes", []))
    approved = fv["approved"] is True and blocking_count == 0
    if fv["approved"] is True and blocking_count > 0:
        raise StartPathError("final_verdict.approved cannot be true when blocking arrays are non-empty", 1)

    return {
        "approved": approved,
        "blocking_count": blocking_count,
        "advisory_minor_count": len(advisory),
        "verdict": verdict,
    }


def _repository_urls_match(repo_a: Any, repo_b: Any) -> bool:
    if not isinstance(repo_a, str) or not isinstance(repo_b, str) or not repo_a or not repo_b:
        return False
    norm_a = repo_a.rstrip("/")
    norm_b = repo_b.rstrip("/")
    if norm_a.endswith(".git"):
        norm_a = norm_a[:-4]
    if norm_b.endswith(".git"):
        norm_b = norm_b[:-4]
    return norm_a == norm_b


def preflight_capabilities(root: Path, *, require_sandbox: bool = False) -> dict[str, Any]:
    """Check runtime, Git, schema, repository-binding, and sandbox readiness before a governed attempt."""
    failures: list[str] = []
    capabilities: dict[str, Any] = {
        "python_version": platform.python_version(),
        "dont_write_bytecode": sys.dont_write_bytecode or os.environ.get("PYTHONDONTWRITEBYTECODE") == "1",
        "git_available": False,
        "git_toplevel": None,
        "origin_url": None,
        "run_state_valid": False,
        "repository_binding_aligned": False,
        "schemas_present": False,
        "sandbox_available": False,
    }
    if not capabilities["dont_write_bytecode"]:
        failures.append("PYTHONDONTWRITEBYTECODE=1 is required to avoid contaminating payload trees")

    git_res = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if git_res.returncode == 0:
        capabilities["git_available"] = True
        capabilities["git_toplevel"] = git_res.stdout.strip()
    else:
        failures.append("git rev-parse --show-toplevel failed")

    origin_res = subprocess.run(
        ["git", "-C", str(root), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
    )
    if origin_res.returncode == 0:
        capabilities["origin_url"] = origin_res.stdout.strip()

    required_schemas = (
        "contract.schema.json",
        "qa_verdict.schema.json",
        "run_state.schema.json",
        "bugfix_cause.schema.json",
        "bugfix_scope.schema.json",
        "small_change_intent.schema.json",
    )
    missing_schemas = [s for s in required_schemas if not (FRAMEWORK / "schema" / s).is_file()]
    if not missing_schemas:
        capabilities["schemas_present"] = True
    else:
        failures.append("missing framework schemas: " + ", ".join(missing_schemas))

    run_state_path = root / ".agent" / "run_state.json"
    if run_state_path.is_file():
        try:
            state = load_record(root, Path(".agent/run_state.json"), "run_state.schema.json")
            capabilities["run_state_valid"] = True
            if capabilities["origin_url"] and _repository_urls_match(state.get("repository"), capabilities["origin_url"]):
                capabilities["repository_binding_aligned"] = True
            elif capabilities["origin_url"]:
                failures.append(
                    f"run_state.repository ({state.get('repository')!r}) does not match git origin ({capabilities['origin_url']!r})"
                )
        except StartPathError as exc:
            failures.append(str(exc))
    else:
        capabilities["run_state_valid"] = True
        capabilities["repository_binding_aligned"] = True

    sandbox_script = root / "tools" / "linux_trial_sandbox.sh"
    if not sandbox_script.is_file():
        sandbox_script = FRAMEWORK / "tools" / "linux_trial_sandbox.sh"
    has_bwrap = shutil.which("bwrap") is not None
    has_docker = shutil.which("docker") is not None
    capabilities["sandbox_available"] = sandbox_script.is_file() and (has_bwrap or has_docker)
    if require_sandbox and not capabilities["sandbox_available"]:
        failures.append("sandbox required but neither bwrap nor docker is available with linux_trial_sandbox.sh")

    return {
        "ok": len(failures) == 0,
        "capabilities": capabilities,
        "failures": failures,
    }


def capture_command_evidence(
    root: Path,
    *,
    task_id: str,
    step: str,
    attempt: int,
    output_dir: Path,
    argv: list[str],
    candidate_sha256: str | None = None,
    agent_id: str = "nizam-local-agent",
    session_id: str = "local-session",
    timeout_sec: float | None = None,
) -> dict[str, Any]:
    """Execute a command and write stdout, stderr, and receipt metadata to exclusive paths."""
    if not ID_PATTERN.fullmatch(task_id):
        raise StartPathError("task_id is not a single safe path token", 2)
    if not ID_PATTERN.fullmatch(step):
        raise StartPathError("step is not a single safe path token", 2)
    if not isinstance(attempt, int) or not (1 <= attempt <= 3):
        raise StartPathError("attempt must be an integer between 1 and 3 (circuit breaker cap)", 2)
    if not argv or not all(isinstance(x, str) and x for x in argv):
        raise StartPathError("argv must be a non-empty list of strings", 2)

    rel_dir = output_dir.relative_to(root).as_posix() if output_dir.is_absolute() and output_dir.is_relative_to(root) else output_dir.as_posix()
    target_dir = resolve_project_file(root, rel_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    head_res = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    revision = head_res.stdout.strip() if head_res.returncode == 0 else "0" * 40

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    nonce = secrets.token_hex(4)
    stem = f"{task_id}-{step}-attempt{attempt}-{stamp}-{nonce}"
    stdout_path = target_dir / f"{stem}.stdout.txt"
    stderr_path = target_dir / f"{stem}.stderr.txt"
    receipt_path = target_dir / f"{stem}.capture.json"

    for p in (stdout_path, stderr_path, receipt_path):
        if p.exists():
            raise StartPathError(f"evidence target already exists; refusing overwrite: {p}", 1)

    started_at = utc_now_iso()
    start_ns = time.monotonic_ns()
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    executed = False
    completion_state = "completed"
    outcome = "setup-error"
    exit_code: int | None = None
    signal_num: int | None = None
    stdout_bytes = b""
    stderr_bytes = b""

    try:
        proc = subprocess.run(
            argv,
            cwd=str(root),
            env=env,
            capture_output=True,
            timeout=timeout_sec,
            check=False,
        )
        executed = True
        stdout_bytes = proc.stdout
        stderr_bytes = proc.stderr
        if proc.returncode < 0:
            completion_state = "interrupted"
            outcome = "interrupted"
            signal_num = -proc.returncode
            exit_code = proc.returncode
        elif proc.returncode == 0:
            completion_state = "completed"
            outcome = "success"
            exit_code = 0
        else:
            completion_state = "completed"
            outcome = "failed"
            exit_code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        executed = True
        completion_state = "interrupted"
        outcome = "interrupted"
        exit_code = -1
        stdout_bytes = exc.stdout if isinstance(exc.stdout, bytes) else (exc.stdout or "").encode("utf-8")
        stderr_bytes = exc.stderr if isinstance(exc.stderr, bytes) else (exc.stderr or "").encode("utf-8")
    except OSError as exc:
        executed = False
        completion_state = "completed"
        outcome = "setup-error"
        exit_code = 127
        stderr_bytes = f"OSError: {exc}\n".encode("utf-8")

    duration_ms = max(0, (time.monotonic_ns() - start_ns) // 1_000_000)
    completed_at = utc_now_iso()

    with stdout_path.open("xb") as fh:
        fh.write(stdout_bytes)
    with stderr_path.open("xb") as fh:
        fh.write(stderr_bytes)

    stdout_rel = stdout_path.relative_to(root).as_posix()
    stderr_rel = stderr_path.relative_to(root).as_posix()
    receipt_rel = receipt_path.relative_to(root).as_posix()

    capture_doc = {
        "schema_version": 1,
        "id": task_id,
        "step": step,
        "attempt": attempt,
        "argv": argv,
        "cwd": str(root),
        "revision": revision,
        "candidate_sha256": candidate_sha256 or ("0" * 64),
        "environment": {
            "runtime": {
                "implementation": platform.python_implementation(),
                "version": platform.python_version(),
                "system": platform.system(),
                "machine": platform.machine(),
            },
            "variables": {"PYTHONDONTWRITEBYTECODE": "1"},
        },
        "producer": {
            "agent_id": agent_id,
            "session_id": session_id,
        },
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_ms": duration_ms,
        "executed": executed,
        "completion_state": completion_state,
        "outcome": outcome,
        "exit_code": exit_code,
        "signal": signal_num,
        "stdout": {
            "path": stdout_rel,
            "sha256": sha256_hex(stdout_bytes),
            "revision": revision,
        },
        "stderr": {
            "path": stderr_rel,
            "sha256": sha256_hex(stderr_bytes),
            "revision": revision,
        },
        "capture_path": receipt_rel,
    }
    with receipt_path.open("xb") as fh:
        fh.write(canonical_bytes(capture_doc) + b"\n")
    return capture_doc


def generate_status_view(root: Path) -> dict[str, Any]:
    """Derive a concise read-only status/readiness view from authoritative live records."""
    head_res = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    head_sha = head_res.stdout.strip() if head_res.returncode == 0 else None
    origin_res = subprocess.run(
        ["git", "-C", str(root), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
    )
    origin_url = origin_res.stdout.strip() if origin_res.returncode == 0 else None

    state_path = root / ".agent" / "run_state.json"
    state: dict[str, Any] = {}
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))

    prov_path = root / ".nizam" / "provenance.json"
    installed: dict[str, Any] | None = None
    if prov_path.is_file():
        installed = json.loads(prov_path.read_text(encoding="utf-8"))

    f019_path = root / ".agent" / "feature_list_019.json"
    phase_019_profiles: list[dict[str, Any]] = []
    if f019_path.is_file():
        f019 = json.loads(f019_path.read_text(encoding="utf-8"))
        for row in f019.get("features", []):
            phase_019_profiles.append({
                "id": row.get("id"),
                "name": row.get("name"),
                "status": row.get("status"),
                "passes": row.get("passes"),
                "dependencies": row.get("dependencies", []),
            })

    cb = state.get("circuit_breaker", {})
    current_feat = str(state.get("current_feature", ""))
    active_breakers = {
        k: v for k, v in cb.items()
        if current_feat and k.startswith(current_feat + "-")
    }
    history = state.get("history", [])
    recent_history = [
        {"at": h.get("at"), "event": h.get("event")}
        for h in history[-3:]
        if isinstance(h, dict)
    ]

    return {
        "repository": state.get("repository"),
        "origin_url": origin_url,
        "repository_binding_aligned": _repository_urls_match(state.get("repository"), origin_url),
        "head_revision": head_sha,
        "current_phase": state.get("current_phase"),
        "current_feature": state.get("current_feature"),
        "status": state.get("status"),
        "updated_at": state.get("updated_at"),
        "installed_governance": installed,
        "phase_019_profiles": phase_019_profiles,
        "active_circuit_breakers": active_breakers,
        "total_circuit_breaker_entries": len(cb),
        "recent_history": recent_history,
    }


def render_status_markdown(view: dict[str, Any]) -> str:
    """Format the concise status view as Markdown."""
    lines = [
        "# Nizam Concise Status View",
        "",
        f"- **Repository**: `{view.get('repository')}` (origin aligned: `{view.get('repository_binding_aligned')}`)",
        f"- **HEAD**: `{view.get('head_revision')}`",
        f"- **Active Position**: phase `{view.get('current_phase')}`, feature `{view.get('current_feature')}`, status `{view.get('status')}`",
        f"- **Updated At**: `{view.get('updated_at')}`",
    ]
    inst = view.get("installed_governance")
    if isinstance(inst, dict):
        lines.append(
            f"- **Installed Governance**: `{inst.get('tag')}` (`{inst.get('resolved_sha')}`)"
        )
    if view.get("phase_019_profiles"):
        lines.append("")
        lines.append("## Phase 019 Assurance Profiles")
        for row in view["phase_019_profiles"]:
            lines.append(
                f"- **{row['id']}** ({row['name']}): status=`{row['status']}`, passes=`{row['passes']}`, deps=`{row['dependencies']}`"
            )
    return "\n".join(lines) + "\n"


def resume_from_receipt(
    root: Path,
    *,
    policy_path: Path,
    receipt_path: Path | None = None,
    state_path: Path | None = None,
    apply_changes: bool = False,
) -> dict[str, Any]:
    """Run workflow_assurance.plan_receipt_transition on the start/resume path."""
    try:
        import workflow_assurance as wa
    except ModuleNotFoundError:
        from tools import workflow_assurance as wa

    target_state_path = state_path or (root / ".agent" / "run_state.json")
    if not target_state_path.is_file():
        raise StartPathError(f"state file does not exist: {target_state_path}", 1)
    state_data = _read_json_file(target_state_path)
    policy_data = _read_json_file(policy_path)
    receipt_data = _read_json_file(receipt_path) if receipt_path is not None else None
    try:
        planned = wa.plan_receipt_transition(root, state_data, receipt_data, policy=policy_data)
    except wa.AssuranceError as exc:
        raise StartPathError(str(exc), 1) from exc

    applied = False
    if apply_changes and planned["action"] == "advance":
        target_state_path.write_text(json.dumps(planned["state"], indent=2) + "\n", encoding="utf-8")
        applied = True
    return {
        "action": planned["action"],
        "reason": planned["reason"],
        "applied": applied,
        "status": planned["state"].get("status"),
        "updated_at": planned["state"].get("updated_at"),
    }


def _read_json_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise StartPathError(f"required record does not exist: {path}", 1)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StartPathError(f"{path} is not JSON: {exc.msg}", 1) from exc
    if not isinstance(data, dict):
        raise StartPathError(f"{path} must be a JSON object", 1)
    return data


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


def load_trivial_intent(root: Path, path_id: str) -> dict:
    """Load a trivial-change intent and refuse non-trivial or contract-requiring work."""
    intent = load_record(
        root,
        Path(".agent") / "evidence" / f"{path_id}-intent.json",
        "small_change_intent.schema.json",
    )
    if intent["id"] != path_id:
        raise StartPathError("intent id does not match --id", 1)
    if intent["needs_new_contract"] is True:
        raise StartPathError("needs_new_contract is true; use the feature path", 1)
    for relative in intent.get("files", []):
        require_project_path(relative)
        if any(relative == p or relative.startswith(p) for p in HIGH_RISK_PREFIXES) or relative.startswith("schema/"):
            raise StartPathError("trivial path cannot modify schema or high-risk files: " + relative, 1)
    return intent


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


def _validate_against_schema(data: dict, schema_name: str, label: str) -> None:
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
            f"{label} failed {schema_name}: {error.message}",
            1,
        ) from error


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
    _validate_against_schema(data, schema_name, relative.as_posix())
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
