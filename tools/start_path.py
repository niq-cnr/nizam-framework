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
import tempfile
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
    "tools/docker_trial_sandbox.sh",
    "tools/isolated_trial_adapter.py",
    "tools/convergent_review.py",
    "tools/evaluate_convergent_review_prompt.py",
    "tools/workflow_assurance.py",
    "tools/workflow_assurance_ci.py",
    "tools/runtime_session.py",
    ".github/scripts/test_sandbox_boundaries.py",
    ".github/scripts/verify_self_governance.py",
    "methodology/10_live_runtime_sessions.md",
    "methodology/11_sbcl_runtime_binding.md",
    "docs/planning/SELF_GOVERNANCE.md",
    "docs/planning/operator_gates.md",
    "ecosystem/",
)

NORMATIVE_FEATURE_PREFIXES = (
    "schema/",
    "standard/",
    "methodology/",
    "templates/",
    ".github/workflows/",
)

NORMATIVE_FEATURE_EXACT = frozenset({
    "NIZAM.json",
    "AGENTS.md",
    "bootstrap.sh",
    "tools/validate.sh",
    "tools/verify_lib.sh",
})

PROSE_EXTENSIONS = (".md", ".txt", ".rst")

TRIVIAL_DOC_PREFIXES = (
    "docs/",
    "README.md",
    "CHANGELOG.md",
    "CONTEXT.md",
    "DEBT.md",
)

FORBIDDEN_AMENDMENT_KEYS = (
    "feature_id",
    "non_goals",
    "goal",
    "goals",
    "invariants",
    "security_invariants",
    "isolation_invariants",
    "authority_scope",
    "repository",
    "status",
    "approvals",
    "approval_evidence",
    "spec_ref",
)

ALLOWED_AMENDMENT_KEYS = frozenset({
    "contract_id",
    "summary",
    "invariants_preserved",
    "files_create_add",
    "files_modify_add",
    "verification_updates",
    "estimated_lines",
    "independent_scrutiny",
    "at",
    "by",
})

ROUTE_ASSURANCE_TIER: dict[str, str] = {
    "trivial": "Routine",
    "small-change": "Routine",
    "bugfix": "Standard",
    "standard-feature": "Standard",
    "high-risk": "High-assurance",
}

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


def normalize_relative_path(
    relative: str,
    *,
    root: Path | None = None,
    reject_symlinks: bool = True,
    forbid_nizam_payload: bool = True,
) -> str:
    """Canonicalize a repository-relative path and reject traversal, absolute, NUL, .nizam/, or symlink escapes."""
    if not isinstance(relative, str) or not relative.strip():
        raise StartPathError("path must be project-relative: " + str(relative), 1)
    raw = relative.strip()
    if "\x00" in raw or "\\" in raw or raw.startswith("/"):
        raise StartPathError("path must be project-relative: " + relative, 1)
    parts: list[str] = []
    for seg in raw.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            raise StartPathError("path must not contain '..': " + relative, 1)
        parts.append(seg)
    if not parts:
        raise StartPathError("path must be project-relative: " + relative, 1)
    norm = "/".join(parts)
    if forbid_nizam_payload and (norm == ".nizam" or norm.startswith(".nizam/")):
        raise StartPathError("installed .nizam/ payload is immutable; do not edit .nizam/ directly", 1)
    if root is not None:
        root_resolved = root.resolve()
        cur = root_resolved
        for seg in parts:
            cur = cur / seg
            if reject_symlinks and cur.is_symlink():
                raise StartPathError("symlink path is forbidden in governed scope: " + norm, 1)
        resolved = cur.resolve()
        if not resolved.is_relative_to(root_resolved):
            raise StartPathError("path leaves the project root: " + relative, 1)
        if forbid_nizam_payload:
            nizam_dir = (root_resolved / ".nizam").resolve()
            if resolved == nizam_dir or resolved.is_relative_to(nizam_dir):
                raise StartPathError("installed .nizam/ payload is immutable; do not edit .nizam/ directly", 1)
    return norm


def normalize_file_list(
    files: list[str] | None,
    *,
    root: Path | None = None,
    allow_empty: bool = False,
) -> list[str]:
    """Normalize, validate, and deduplicate a list of repository-relative file paths."""
    if not isinstance(files, list):
        raise StartPathError("files must be a non-empty list of repository-relative paths", 1)
    out: list[str] = []
    seen: set[str] = set()
    for item in files:
        norm = normalize_relative_path(item, root=root)
        if norm not in seen:
            seen.add(norm)
            out.append(norm)
    if not out and not allow_empty:
        raise StartPathError("files must be a non-empty list of repository-relative paths", 1)
    return out


def _is_high_risk_path(norm_path: str) -> bool:
    return any(norm_path == prefix or norm_path.startswith(prefix) for prefix in HIGH_RISK_PREFIXES)


def _is_normative_feature_path(norm_path: str) -> bool:
    return norm_path in NORMATIVE_FEATURE_EXACT or any(
        norm_path == prefix or norm_path.startswith(prefix) for prefix in NORMATIVE_FEATURE_PREFIXES
    )


def _is_trivial_eligible_file(norm_path: str, root: Path | None = None) -> bool:
    """Return True only for non-executable prose documentation outside governance, schema, and tooling."""
    if _is_high_risk_path(norm_path) or _is_normative_feature_path(norm_path):
        return False
    if norm_path.startswith(("tools/", "schema/", "standard/", "methodology/", "templates/", "ecosystem/", ".github/", ".agent/")):
        return False
    if not norm_path.endswith(PROSE_EXTENSIONS):
        return False
    if not any(norm_path == prefix or norm_path.startswith(prefix) for prefix in TRIVIAL_DOC_PREFIXES):
        return False
    if root is not None:
        candidate_file = root / norm_path
        if candidate_file.is_file() and (candidate_file.stat().st_mode & 0o111):
            return False
    return True


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
        "publish",
        "build-receipt",
        "status",
        "resume",
    ):
        return _main_extended(raw_argv)
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
    """Run extended task routing, amendment, preflight, capture, publish, build-receipt, status, or resume commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="subcommand", required=True)

    classify_p = sub.add_parser("classify", help="Classify a task into one of the 5 semantic routes.")
    classify_p.add_argument("--files", nargs="*", default=[], help="Repository-relative files in scope.")
    classify_p.add_argument("--bugfix", action="store_true", help="Task repairs a reproducible defect.")
    classify_p.add_argument("--editorial", action="store_true", help="Task is editorial/comment/typo only.")
    classify_p.add_argument("--needs-new-contract", action="store_true", help="Task introduces new contract obligations.")
    classify_p.add_argument("--touches-schema", "--schema-change", action="store_true", dest="touches_schema", help="Task modifies schemas or public interfaces.")
    classify_p.add_argument("--touches-security", action="store_true", help="Task touches security/isolation/authority boundaries.")
    classify_p.add_argument("--touches-runtime", action="store_true", help="Task touches persistent-runtime session semantics.")
    classify_p.add_argument("--root", type=Path, default=None, help="Optional project root for symlink/mode checks.")

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
    preflight_p.add_argument("--route", default=None, help="Optional route name; high-risk enables operational sandbox probing.")
    preflight_p.add_argument("--root", type=Path, default=Path.cwd())

    capture_p = sub.add_parser("capture", help="Capture command output and provenance to an exclusive path.")
    capture_p.add_argument("--id", required=True, dest="task_id")
    capture_p.add_argument("--step", required=True)
    capture_p.add_argument("--attempt", required=True, type=int)
    capture_p.add_argument("--output-dir", required=True, type=Path)
    capture_p.add_argument("--candidate", "--candidate-sha256", default=None, dest="candidate", help="64-hex candidate digest or path to candidate JSON file.")
    capture_p.add_argument("--env-var", action="append", default=None, dest="env_vars", help="Environment variable name to record (repeatable).")
    capture_p.add_argument("--proof-kind", choices=("success", "semantic-negative"), default="success")
    capture_p.add_argument("--cause-class", choices=("environment", "contract", "implementation", "verifier", "transient", "unknown"), default=None)
    capture_p.add_argument("--agent-id", default="nizam-local-agent")
    capture_p.add_argument("--session-id", default="local-session")
    capture_p.add_argument("--timeout-sec", type=float, default=None)
    capture_p.add_argument("--root", type=Path, default=Path.cwd())
    capture_p.add_argument("cmd", nargs=argparse.REMAINDER)

    publish_p = sub.add_parser("publish", help="Publish completed capture outputs into Git and project a closed 12-field receipt capture.")
    publish_p.add_argument("--capture", required=True, type=Path, help="Path to raw <stem>.capture.json file.")
    publish_p.add_argument("--root", type=Path, default=Path.cwd())

    build_receipt_p = sub.add_parser("build-receipt", help="Bind published capture(s) into a stage receipt and verify with verify_stage_receipt.")
    build_receipt_p.add_argument("--policy", required=True, type=Path)
    build_receipt_p.add_argument("--published", action="append", required=True, type=Path, help="Path to <stem>.published.json (repeatable).")
    build_receipt_p.add_argument("--output", required=True, type=Path, help="Output path for the verified receipt JSON.")
    build_receipt_p.add_argument("--update-policy", action="store_true", help="Write pinned capture refs back into the policy file.")
    build_receipt_p.add_argument("--commit", action="store_true", help="Commit the generated receipt (and updated policy) into Git.")
    build_receipt_p.add_argument("--root", type=Path, default=Path.cwd())

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
                root=args.root.resolve() if args.root else None,
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
                require_sandbox=args.require_sandbox or (args.route == "high-risk"),
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
                candidate_sha256=args.candidate,
                env_vars=args.env_vars,
                proof_kind=args.proof_kind,
                cause_class=args.cause_class,
                agent_id=args.agent_id,
                session_id=args.session_id,
                timeout_sec=args.timeout_sec,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["outcome"] == "success" else 1
        if args.subcommand == "publish":
            result = publish_captured_evidence(
                args.root.resolve(),
                capture_path=args.capture,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.subcommand == "build-receipt":
            result = build_stage_receipt(
                args.root.resolve(),
                policy_path=args.policy,
                published_paths=args.published,
                output_path=args.output,
                update_policy=args.update_policy,
                commit_changes=args.commit,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
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
        verify_actual_changed_scope(root, "bugfix", scope["files"])
        load_passing_qa(root, path_id)
        return f"bugfix {scope['id']}: recorded verification result exists"
    if kind == "trivial":
        intent = load_trivial_intent(root, path_id)
        if decision == "begin":
            return f"trivial {intent['id']}: implementation may begin"
        verify_actual_changed_scope(root, "trivial", intent["files"])
        load_passing_qa(root, path_id)
        return f"trivial {intent['id']}: recorded verification result exists"
    intent = load_intent(root, path_id)
    if decision == "begin":
        return f"small-change {intent['id']}: implementation may begin"
    verify_actual_changed_scope(root, "small-change", intent["files"])
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
    root: Path | None = None,
) -> dict[str, Any]:
    """Classify a change into one of 5 semantic routes using canonical paths and semantic properties."""
    scoped = normalize_file_list(files, root=root, allow_empty=False)

    reasons: list[str] = []
    high_risk_files = [p for p in scoped if _is_high_risk_path(p)]
    feature_surface_files = [p for p in scoped if _is_normative_feature_path(p)]
    trivial_eligible = all(_is_trivial_eligible_file(p, root=root) for p in scoped)

    if touches_security or touches_runtime or high_risk_files:
        route = "high-risk"
        if touches_security:
            reasons.append("touches security, isolation, or authority verification boundary")
        if touches_runtime:
            reasons.append("touches persistent-runtime session boundary")
        if high_risk_files:
            reasons.append("touches high-risk files: " + ", ".join(high_risk_files))
    elif needs_new_contract or touches_schema or feature_surface_files:
        route = "standard-feature"
        if needs_new_contract:
            reasons.append("introduces new contract obligations")
        if touches_schema:
            reasons.append("modifies schema or capability index")
        if feature_surface_files:
            reasons.append("touches normative governance, entry, or schema files: " + ", ".join(feature_surface_files))
    elif is_bugfix:
        route = "bugfix"
        reasons.append("repairs reproducible defect within bounded scope")
    elif is_editorial and trivial_eligible:
        route = "trivial"
        reasons.append("editorial or documentation-only adjustment with no contract/schema/tool impact")
    else:
        route = "small-change"
        if is_editorial and not trivial_eligible:
            reasons.append("editorial flag ignored because scope includes code, tooling, or non-prose path(s)")
        reasons.append("bounded unambiguous change requiring no new feature contract")

    return {
        "route": route,
        "assurance_tier": ROUTE_ASSURANCE_TIER[route],
        "files": scoped,
        "reasons": reasons,
        "required_gates": ROUTE_GATES[route],
        "stopping_conditions": {
            "max_attempts": 3,
            "attempt_counter_role": "telemetry",
            "breaker_ref": "methodology/03_circuit_breaker.md",
            "comparator_subordinate": True,
            "pass_condition": (
                "All required_gates for route '" + route + "' exit 0 and blocking verdict arrays are empty."
            ),
            "halt_condition": (
                "Stop and diagnose on repeated identical deterministic failure, contradiction with approved "
                "contract/invariants, missing operator authority, or exhausted execution budget; "
                "comparator claims remain subordinate to stopping rules."
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


def _is_vacuous_or_weakened_command(new_cmd: str, old_cmd: str | None) -> str | None:
    """Detect vacuous shell no-ops or replacements that drop real verification targets."""
    stripped = new_cmd.strip()
    if not stripped or stripped.startswith("#"):
        return "verification command must be an executable check, not empty or comment"
    segments = [seg.strip() for seg in re.split(r"(?:&&|\|\||;|\|)", stripped) if seg.strip()]
    if not segments:
        return "verification command is empty"
    vacuous_heads = {"true", "/bin/true", "/usr/bin/true", ":", "exit", "echo", "printf", "pass"}
    non_vacuous_found = False
    for seg in segments:
        tokens = seg.split()
        while tokens and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[0]):
            tokens.pop(0)
        if not tokens:
            continue
        head = tokens[0]
        joined = " ".join(tokens)
        if head in vacuous_heads:
            continue
        if head in ("python", "python3") and len(tokens) >= 3 and tokens[1] == "-c":
            code = " ".join(tokens[2:]).strip(" '\"")
            if code in ("", "pass", "import sys; sys.exit(0)", "raise SystemExit(0)"):
                continue
        if joined in ("true", "/bin/true", "/usr/bin/true", ":"):
            continue
        non_vacuous_found = True
    if not non_vacuous_found:
        return f"verification command {new_cmd!r} is vacuous (no-op)"
    if old_cmd:
        old_has_runner = any(
            marker in old_cmd
            for marker in ("tools/", ".github/scripts/", "pytest", "unittest", "validate.sh")
        )
        new_has_runner = any(
            marker in stripped
            for marker in ("tools/", ".github/scripts/", "pytest", "unittest", "validate.sh")
        )
        if old_has_runner and not new_has_runner:
            return f"verification command {new_cmd!r} weakens existing tool/test verification {old_cmd!r}"
    return None


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
    for forbidden in FORBIDDEN_AMENDMENT_KEYS:
        if forbidden in amendment:
            raise StartPathError(f"lightweight amendment cannot modify {forbidden}; re-enter Loop 1", 1)
    unknown_keys = sorted(set(amendment) - ALLOWED_AMENDMENT_KEYS)
    if unknown_keys:
        raise StartPathError(
            "amendment contains unknown or unsupported field(s): " + ", ".join(unknown_keys),
            1,
        )
    if amendment.get("contract_id") != contract_id:
        raise StartPathError("amendment contract_id does not match --contract", 1)
    if amendment.get("invariants_preserved") is not True:
        raise StartPathError("amendment requires invariants_preserved: true", 1)
    summary = amendment.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise StartPathError("amendment requires a non-empty summary", 1)

    updated = copy.deepcopy(contract)
    scope = updated.setdefault("scope", {"files_create": [], "files_modify": []})
    existing_all_paths: list[str] = []
    for k in ("files_create", "files_modify"):
        for e in scope.get(k, []):
            if isinstance(e, dict) and isinstance(e.get("path"), str):
                norm_existing = normalize_relative_path(e["path"], root=root)
                e["path"] = norm_existing
                existing_all_paths.append(norm_existing)
    existing_prose_only = bool(existing_all_paths) and all(
        _is_trivial_eligible_file(p, root=root) for p in existing_all_paths
    )

    added_paths: list[str] = []
    scope_diff: dict[str, list[str]] = {"files_create_added": [], "files_modify_added": []}
    semantic_reasons: list[str] = []

    for key, target_key, diff_key in (
        ("files_create_add", "files_create", "files_create_added"),
        ("files_modify_add", "files_modify", "files_modify_added"),
    ):
        entries = amendment.get(key, [])
        if not isinstance(entries, list):
            raise StartPathError(f"{key} must be a list", 1)
        existing = {e["path"] for e in scope.get(target_key, []) if isinstance(e, dict) and "path" in e}
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("purpose"), str):
                raise StartPathError(f"{key} entries require path and purpose strings", 1)
            rel_path = normalize_relative_path(entry["path"], root=root)
            if _is_high_risk_path(rel_path) or _is_normative_feature_path(rel_path):
                raise StartPathError(
                    f"lightweight amendment cannot add protected security/payload/schema/governance path: {rel_path}",
                    1,
                )
            if existing_prose_only and not _is_trivial_eligible_file(rel_path, root=root):
                semantic_reasons.append(
                    f"adding non-prose/tooling path {rel_path!r} to prose-only contract scope expands risk class"
                )
            if rel_path not in existing:
                scope[target_key].append({"path": rel_path, "purpose": entry["purpose"]})
                existing.add(rel_path)
                added_paths.append(rel_path)
                scope_diff[diff_key].append(rel_path)

    verification_updates = amendment.get("verification_updates", [])
    if not isinstance(verification_updates, list):
        raise StartPathError("verification_updates must be a list", 1)
    updated_tests: list[str] = []
    verification_diff: list[dict[str, str | None]] = []
    for item in verification_updates:
        if not isinstance(item, dict) or not isinstance(item.get("acceptance_test"), str) or not isinstance(item.get("command"), str):
            raise StartPathError("verification_updates entries require acceptance_test and command strings", 1)
        new_cmd = item["command"]
        matched = False
        old_cmd: str | None = None
        for existing_v in updated.get("verification", []):
            if existing_v.get("acceptance_test") == item["acceptance_test"]:
                old_cmd = existing_v.get("command")
                weak_reason = _is_vacuous_or_weakened_command(new_cmd, old_cmd)
                if weak_reason is not None:
                    raise StartPathError("lightweight amendment rejected: " + weak_reason, 1)
                existing_v["command"] = new_cmd
                matched = True
                break
        if not matched:
            weak_reason = _is_vacuous_or_weakened_command(new_cmd, None)
            if weak_reason is not None:
                raise StartPathError("lightweight amendment rejected: " + weak_reason, 1)
            updated.setdefault("verification", []).append(
                {"acceptance_test": item["acceptance_test"], "command": new_cmd}
            )
        updated_tests.append(item["acceptance_test"])
        verification_diff.append({
            "acceptance_test": item["acceptance_test"],
            "old_command": old_cmd,
            "new_command": new_cmd,
        })

    amendment_class = "semantic" if semantic_reasons else "mechanical"
    re_approval_required = amendment_class == "semantic"
    if re_approval_required and apply_changes:
        raise StartPathError(
            "semantic scope expansion requires re-approval and cannot be applied as a mechanical amendment: "
            + "; ".join(semantic_reasons),
            1,
        )

    amendment_record = {
        "at": amendment.get("at") or utc_now_iso(),
        "by": amendment.get("by") or "start_path:amend-contract",
        "type": "lightweight-scope-or-verification-update",
        "amendment_class": amendment_class,
        "re_approval_required": re_approval_required,
        "summary": summary.strip(),
        "prior_contract_sha256": prior_sha256,
        "added_files": added_paths,
        "updated_verification": updated_tests,
        "scope_diff": scope_diff,
        "verification_diff": verification_diff,
        "invariants_preserved": True,
    }
    updated.setdefault("amendments", []).append(amendment_record)
    _validate_against_schema(updated, "contract.schema.json", contract_rel.as_posix())

    new_bytes = (json.dumps(updated, indent=2) + "\n").encode("utf-8")
    amended_sha256 = sha256_hex(new_bytes)
    if apply_changes:
        contract_path.write_bytes(new_bytes)
    return {
        "contract_id": contract_id,
        "amendment_class": amendment_class,
        "re_approval_required": re_approval_required,
        "applied": bool(apply_changes),
        "prior_contract_sha256": prior_sha256,
        "amended_contract_sha256": amended_sha256,
        "added_files": added_paths,
        "updated_verification": updated_tests,
        "scope_diff": scope_diff,
        "verification_diff": verification_diff,
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


def _probe_sandbox_operational(root: Path) -> tuple[bool, bool, str | None]:
    """Verify sandbox scripts exist and execute a minimal isolation probe via isolated_trial_adapter.py."""
    sandbox_script = root / "tools" / "linux_trial_sandbox.sh"
    if not sandbox_script.is_file():
        sandbox_script = FRAMEWORK / "tools" / "linux_trial_sandbox.sh"
    adapter_script = root / "tools" / "isolated_trial_adapter.py"
    if not adapter_script.is_file():
        adapter_script = FRAMEWORK / "tools" / "isolated_trial_adapter.py"

    if not sandbox_script.is_file() or not adapter_script.is_file():
        return False, False, "sandbox scripts (linux_trial_sandbox.sh / isolated_trial_adapter.py) are missing"

    bwrap_bin = shutil.which("bwrap")
    if bwrap_bin is not None:
        try:
            bwrap_ver = subprocess.run(
                [bwrap_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if bwrap_ver.returncode != 0:
                return False, False, f"bwrap on PATH ({bwrap_bin}) is broken (exited {bwrap_ver.returncode})"
        except (OSError, subprocess.SubprocessError) as exc:
            return False, False, f"bwrap on PATH ({bwrap_bin}) failed to execute: {exc}"

    try:
        with tempfile.TemporaryDirectory(prefix="nizam-preflight-sandbox-") as tmp_dir:
            probe_root = Path(tmp_dir).resolve()
            probe_tools = probe_root / ".nizam" / "tools"
            probe_tools.mkdir(parents=True, exist_ok=True)
            probe_runner = probe_tools / "probe.py"
            probe_runner.write_text(
                "#!/usr/bin/env python3\nimport sys\nprint('sandbox-probe-ok')\nsys.exit(0)\n",
                encoding="utf-8",
            )
            probe_runner.chmod(0o755)
            env = dict(os.environ)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            probe_res = subprocess.run(
                [
                    sys.executable,
                    str(adapter_script),
                    "--root",
                    str(probe_root),
                    "--runner",
                    str(probe_runner),
                    "--",
                    str(probe_runner),
                ],
                cwd=str(probe_root),
                capture_output=True,
                text=True,
                env=env,
                timeout=15,
                check=False,
            )
            if probe_res.returncode == 0 and "sandbox-probe-ok" in probe_res.stdout:
                return True, True, None
            detail = (probe_res.stderr or probe_res.stdout or "").strip()
            return True, False, f"sandbox adapter probe failed (exit {probe_res.returncode}): {detail}"
    except (OSError, subprocess.SubprocessError) as exc:
        return True, False, f"sandbox adapter probe raised exception: {exc}"


def preflight_capabilities(root: Path, *, require_sandbox: bool = False) -> dict[str, Any]:
    """Check runtime, Git, schema, repository-binding, and operational sandbox readiness before a governed attempt."""
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
        "sandbox_operational": False,
        "installed": False,
        "available": False,
        "operational": False,
        "qualified": False,
        "status": "degraded",
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

    sb_avail, sb_oper, sb_err = _probe_sandbox_operational(root)
    capabilities["sandbox_available"] = sb_avail and sb_oper
    capabilities["sandbox_operational"] = sb_oper
    if require_sandbox and not sb_oper:
        failures.append(sb_err or "sandbox required but isolated_trial_adapter probe did not succeed")

    f019_path = root / ".agent" / "feature_list_019.json"
    if f019_path.is_file():
        try:
            f019 = json.loads(f019_path.read_text(encoding="utf-8"))
            by_id = {
                str(r.get("id")): r
                for r in f019.get("features", [])
                if isinstance(r, dict)
            }
            capabilities["qualified"] = all(
                by_id.get(fid, {}).get("status") == "complete" and by_id.get(fid, {}).get("passes") is True
                for fid in ("124", "125")
            )
        except (OSError, json.JSONDecodeError):
            capabilities["qualified"] = False

    capabilities["installed"] = bool((root / ".nizam" / "provenance.json").is_file() or capabilities["schemas_present"])
    capabilities["available"] = bool(
        capabilities["git_available"]
        and capabilities["schemas_present"]
        and (not require_sandbox or capabilities["sandbox_available"])
    )
    capabilities["operational"] = bool(
        capabilities["dont_write_bytecode"]
        and capabilities["git_available"]
        and capabilities["run_state_valid"]
        and capabilities["repository_binding_aligned"]
        and capabilities["schemas_present"]
        and (not require_sandbox or capabilities["sandbox_operational"])
    )
    ok = len(failures) == 0
    capabilities["status"] = "ready" if ok else "degraded"

    return {
        "ok": ok,
        "status": capabilities["status"],
        "capabilities": capabilities,
        "failures": failures,
    }


def _resolve_candidate_and_env(
    root: Path,
    candidate_arg: str | dict[str, Any] | Path | None,
    env_vars: list[str] | None,
) -> tuple[str | None, str, dict[str, str]]:
    """Resolve candidate_sha256, binding_state, and captured environment variables."""
    resolved_sha: str | None = None
    binding_state = "unbound"
    candidate_env_vars: dict[str, str] | None = None

    if isinstance(candidate_arg, dict):
        resolved_sha = sha256_hex(canonical_bytes(candidate_arg))
        binding_state = "candidate-bound"
        env_block = candidate_arg.get("environment")
        if isinstance(env_block, dict) and isinstance(env_block.get("variables"), dict):
            candidate_env_vars = {str(k): str(v) for k, v in env_block["variables"].items()}
    elif isinstance(candidate_arg, Path) or (
        isinstance(candidate_arg, str) and candidate_arg.strip()
    ):
        raw_str = str(candidate_arg).strip()
        if re.fullmatch(r"[0-9a-f]{64}", raw_str):
            resolved_sha = raw_str
            binding_state = "candidate-bound"
        else:
            cand_path = Path(raw_str)
            if not cand_path.is_absolute():
                cand_path = (root / cand_path).resolve()
            if not cand_path.is_file():
                raise StartPathError(
                    f"candidate must be a 64-hex sha256 digest or existing candidate JSON file: {raw_str}",
                    2,
                )
            cand_doc = _read_json_file(cand_path)
            if "candidate" in cand_doc and isinstance(cand_doc["candidate"], dict):
                cand_doc = cand_doc["candidate"]
            resolved_sha = sha256_hex(canonical_bytes(cand_doc))
            binding_state = "candidate-bound"
            env_block = cand_doc.get("environment")
            if isinstance(env_block, dict) and isinstance(env_block.get("variables"), dict):
                candidate_env_vars = {str(k): str(v) for k, v in env_block["variables"].items()}
    elif candidate_arg is not None:
        raise StartPathError("invalid candidate argument", 2)

    captured_vars: dict[str, str] = {}
    if candidate_env_vars is not None:
        for k, v in candidate_env_vars.items():
            captured_vars[k] = os.environ.get(k, v)
    if env_vars:
        for item in env_vars:
            if not isinstance(item, str) or not item.strip():
                continue
            token = item.strip()
            if "=" in token:
                k, v = token.split("=", 1)
                captured_vars[k.strip()] = v
            else:
                if token not in os.environ:
                    raise StartPathError(f"requested --env-var {token!r} is not set in environment", 2)
                captured_vars[token] = os.environ[token]
    if not captured_vars:
        captured_vars["PYTHONDONTWRITEBYTECODE"] = "1"

    return resolved_sha, binding_state, captured_vars


def capture_command_evidence(
    root: Path,
    *,
    task_id: str,
    step: str,
    attempt: int,
    output_dir: Path,
    argv: list[str],
    candidate_sha256: str | dict[str, Any] | Path | None = None,
    env_vars: list[str] | None = None,
    proof_kind: str = "success",
    cause_class: str | None = None,
    agent_id: str = "nizam-local-agent",
    session_id: str = "local-session",
    timeout_sec: float | None = None,
) -> dict[str, Any]:
    """Execute a command and write stdout, stderr, and raw capture metadata to exclusive paths."""
    if not ID_PATTERN.fullmatch(task_id):
        raise StartPathError("task_id is not a single safe path token", 2)
    if not ID_PATTERN.fullmatch(step):
        raise StartPathError("step is not a single safe path token", 2)
    if not isinstance(attempt, int) or isinstance(attempt, bool) or not (1 <= attempt <= 3):
        raise StartPathError("attempt must be an integer between 1 and 3 (circuit breaker cap)", 2)
    if not argv or not all(isinstance(x, str) and x for x in argv):
        raise StartPathError("argv must be a non-empty list of strings", 2)
    if proof_kind not in ("success", "semantic-negative"):
        raise StartPathError("proof_kind must be 'success' or 'semantic-negative'", 2)

    resolved_sha, binding_state, captured_vars = _resolve_candidate_and_env(root, candidate_sha256, env_vars)

    rel_dir = (
        output_dir.relative_to(root).as_posix()
        if output_dir.is_absolute() and output_dir.is_relative_to(root)
        else output_dir.as_posix()
    )
    target_dir = resolve_project_file(root, rel_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    head_res = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    revision = head_res.stdout.strip() if head_res.returncode == 0 else None

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
    for k, v in captured_vars.items():
        env[k] = v

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
            outcome = proof_kind
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

    duration_ms = max(1, (time.monotonic_ns() - start_ns) // 1_000_000)
    completed_at = utc_now_iso()

    with stdout_path.open("xb") as fh:
        fh.write(stdout_bytes)
    with stderr_path.open("xb") as fh:
        fh.write(stderr_bytes)

    stdout_rel = stdout_path.relative_to(root).as_posix()
    stderr_rel = stderr_path.relative_to(root).as_posix()
    receipt_rel = receipt_path.relative_to(root).as_posix()

    inferred_cause = cause_class
    if inferred_cause is None and outcome != proof_kind:
        if not executed or outcome in ("setup-error", "interrupted"):
            inferred_cause = "environment"
        else:
            inferred_cause = "implementation"

    capture_doc: dict[str, Any] = {
        "schema_version": 1,
        "id": task_id,
        "step": step,
        "attempt": attempt,
        "argv": argv,
        "cwd": str(root),
        "revision": revision,
        "binding_state": binding_state,
        "candidate_sha256": resolved_sha,
        "environment": {
            "runtime": {
                "implementation": platform.python_implementation(),
                "version": platform.python_version(),
                "system": platform.system(),
                "machine": platform.machine(),
            },
            "variables": captured_vars,
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
        "proof_kind": proof_kind,
        "cause_class": inferred_cause,
        "exit_code": exit_code,
        "signal": signal_num,
        "stdout": {
            "path": stdout_rel,
            "sha256": sha256_hex(stdout_bytes),
            "revision": None,
        },
        "stderr": {
            "path": stderr_rel,
            "sha256": sha256_hex(stderr_bytes),
            "revision": None,
        },
        "capture_path": receipt_rel,
    }
    with receipt_path.open("xb") as fh:
        fh.write(canonical_bytes(capture_doc) + b"\n")
    return capture_doc


def _git_ensure_committed(root: Path, rel_paths: list[str], message: str) -> str:
    """Stage and commit the specified repository-relative paths if needed, returning HEAD sha."""
    add_res = subprocess.run(
        ["git", "-C", str(root), "add", "--", *rel_paths],
        capture_output=True,
        text=True,
        check=False,
    )
    if add_res.returncode != 0:
        raise StartPathError(f"git add failed during evidence publication: {add_res.stderr.strip()}", 1)
    diff_res = subprocess.run(
        ["git", "-C", str(root), "diff", "--cached", "--name-only", "--", *rel_paths],
        capture_output=True,
        text=True,
        check=False,
    )
    if diff_res.returncode == 0 and diff_res.stdout.strip():
        commit_res = subprocess.run(
            ["git", "-C", str(root), "commit", "-qm", message, "--", *rel_paths],
            capture_output=True,
            text=True,
            check=False,
        )
        if commit_res.returncode != 0:
            raise StartPathError(f"git commit failed during evidence publication: {commit_res.stderr.strip()}", 1)
    head_res = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if head_res.returncode != 0 or not head_res.stdout.strip():
        raise StartPathError("git rev-parse HEAD failed during evidence publication", 1)
    return head_res.stdout.strip()


def publish_captured_evidence(
    root: Path,
    *,
    capture_path: Path,
    cause: str | None = None,
    proof_kind: str | None = None,
) -> dict[str, Any]:
    """Commit completed capture outputs into Git and project a closed 12-field receipt capture."""
    resolved_cap_path = capture_path if capture_path.is_absolute() else (root / capture_path).resolve()
    if not resolved_cap_path.is_file():
        raise StartPathError(f"capture record does not exist: {capture_path}", 1)
    raw_capture = _read_json_file(resolved_cap_path)

    if raw_capture.get("completion_state") != "completed" or raw_capture.get("executed") is not True:
        raise StartPathError(
            "cannot publish incomplete or unexecuted capture for receipt consumption",
            1,
        )
    cand_sha = raw_capture.get("candidate_sha256")
    if raw_capture.get("binding_state") != "candidate-bound" or not isinstance(cand_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", cand_sha):
        raise StartPathError(
            "cannot publish unbound capture for receipt consumption (candidate_sha256 is required)",
            1,
        )
    pre_rev = raw_capture.get("revision")
    if not isinstance(pre_rev, str) or not re.fullmatch(r"[0-9a-f]{40}", pre_rev):
        raise StartPathError("capture record is missing a valid 40-hex pre-execution revision", 1)

    stdout_info = raw_capture.get("stdout", {})
    stderr_info = raw_capture.get("stderr", {})
    stdout_rel = normalize_relative_path(stdout_info.get("path", ""), root=root)
    stderr_rel = normalize_relative_path(stderr_info.get("path", ""), root=root)
    cap_rel = normalize_relative_path(resolved_cap_path.relative_to(root).as_posix(), root=root)

    stdout_file = resolve_project_file(root, stdout_rel)
    stderr_file = resolve_project_file(root, stderr_rel)
    if not stdout_file.is_file() or not stderr_file.is_file():
        raise StartPathError("captured stdout/stderr files are missing on disk", 1)
    if sha256_hex(stdout_file.read_bytes()) != stdout_info.get("sha256"):
        raise StartPathError("captured stdout file digest on disk does not match capture record", 1)
    if sha256_hex(stderr_file.read_bytes()) != stderr_info.get("sha256"):
        raise StartPathError("captured stderr file digest on disk does not match capture record", 1)

    output_revision = _git_ensure_committed(
        root,
        [stdout_rel, stderr_rel, cap_rel],
        f"publish capture outputs for {raw_capture.get('id', 'task')}:{raw_capture.get('step', 'step')}",
    )

    exit_code = raw_capture.get("exit_code")
    if exit_code == 0:
        eff_kind = proof_kind or raw_capture.get("proof_kind") or (
            raw_capture.get("outcome") if raw_capture.get("outcome") in ("success", "semantic-negative") else "success"
        )
        projected_outcome = eff_kind
    else:
        eff_cause = cause or raw_capture.get("cause_class")
        if eff_cause in ("infrastructure", "semantic"):
            projected_outcome = f"{eff_cause}-failed"
        elif eff_cause in ("environment", "transient"):
            projected_outcome = "infrastructure-failed"
        elif eff_cause in ("contract", "implementation", "verifier"):
            projected_outcome = "semantic-failed"
        else:
            projected_outcome = "failed"

    closed_capture: dict[str, Any] = {
        "schema_version": 1,
        "argv": raw_capture["argv"],
        "cwd": raw_capture["cwd"],
        "revision": pre_rev,
        "candidate_sha256": cand_sha,
        "environment": raw_capture["environment"],
        "producer": raw_capture["producer"],
        "executed": True,
        "outcome": projected_outcome,
        "exit_code": exit_code,
        "stdout": {
            "path": stdout_rel,
            "sha256": stdout_info["sha256"],
            "revision": output_revision,
        },
        "stderr": {
            "path": stderr_rel,
            "sha256": stderr_info["sha256"],
            "revision": output_revision,
        },
    }

    stem_name = resolved_cap_path.name
    if stem_name.endswith(".capture.json"):
        base_stem = stem_name[: -len(".capture.json")]
    else:
        base_stem = resolved_cap_path.stem

    receipt_cap_path = resolved_cap_path.parent / f"{base_stem}.receipt-capture.json"
    receipt_cap_rel = normalize_relative_path(receipt_cap_path.relative_to(root).as_posix(), root=root)
    closed_bytes = canonical_bytes(closed_capture) + b"\n"
    receipt_cap_path.write_bytes(closed_bytes)

    capture_revision = _git_ensure_committed(
        root,
        [receipt_cap_rel],
        f"publish receipt capture {base_stem}",
    )
    receipt_capture_ref = {
        "path": receipt_cap_rel,
        "sha256": sha256_hex(closed_bytes),
        "revision": capture_revision,
    }

    published_doc = {
        "schema_version": 1,
        "raw_capture_path": cap_rel,
        "output_revision": output_revision,
        "receipt_capture_ref": receipt_capture_ref,
        "stdout_ref": closed_capture["stdout"],
        "stderr_ref": closed_capture["stderr"],
        "receipt_capture": closed_capture,
    }
    published_path = resolved_cap_path.parent / f"{base_stem}.published.json"
    published_rel = normalize_relative_path(published_path.relative_to(root).as_posix(), root=root)
    published_path.write_bytes(canonical_bytes(published_doc) + b"\n")
    published_doc["published_path"] = published_rel
    return published_doc


def build_stage_receipt(
    root: Path,
    *,
    policy_path: Path,
    published_paths: list[Path],
    output_path: Path,
    update_policy: bool = False,
    commit_changes: bool = False,
) -> dict[str, Any]:
    """Bind one or more published captures into a stage receipt and validate with verify_stage_receipt."""
    try:
        import workflow_assurance as wa
    except ModuleNotFoundError:
        from tools import workflow_assurance as wa

    resolved_policy_path = policy_path if policy_path.is_absolute() else (root / policy_path).resolve()
    policy = _read_json_file(resolved_policy_path)
    commands = policy.get("commands")
    if not isinstance(commands, list) or not commands:
        raise StartPathError("receipt policy must contain a non-empty commands list", 1)
    if len(published_paths) != len(commands):
        raise StartPathError(
            f"number of --published inputs ({len(published_paths)}) must match policy.commands ({len(commands)})",
            1,
        )

    checks: list[dict[str, Any]] = []
    for idx, (cmd, pub_path) in enumerate(zip(commands, published_paths)):
        resolved_pub = pub_path if pub_path.is_absolute() else (root / pub_path).resolve()
        pub_doc = _read_json_file(resolved_pub)
        if "receipt_capture_ref" in pub_doc and "receipt_capture" in pub_doc:
            cap_ref = pub_doc["receipt_capture_ref"]
            closed_cap = pub_doc["receipt_capture"]
        else:
            rel_cap = normalize_relative_path(resolved_pub.relative_to(root).as_posix(), root=root)
            head_sha = _git_ensure_committed(root, [rel_cap], f"pin capture {rel_cap}")
            cap_ref = {
                "path": rel_cap,
                "sha256": sha256_hex(resolved_pub.read_bytes()),
                "revision": head_sha,
            }
            closed_cap = pub_doc
        cmd["capture"] = cap_ref
        checks.append({
            "argv": cmd["argv"],
            "executed": True,
            "outcome": cmd["proof_kind"],
            "exit_code": 0,
            "stdout": closed_cap["stdout"],
            "stderr": closed_cap["stderr"],
            "capture": cap_ref,
        })

    if update_policy:
        resolved_policy_path.write_bytes(canonical_bytes(policy) + b"\n")

    receipt = {
        "schema_version": 1,
        "repository": policy["repository"],
        "feature_id": policy["feature_id"],
        "stage": policy["stage"],
        "operation_id": policy["operation_id"],
        "status": "passed",
        "candidate": policy["candidate"],
        "producer": policy["producer"],
        "contract_ref": policy["contract"],
        "operator_ref": policy["operator"],
        "prerequisites": policy["prerequisites"],
        "checks": checks,
        "verdict": {
            "final_verdict": {"approved": True},
            "issues": [],
            "missing_acceptance_coverage": [],
            "unsupported_claims": [],
        },
    }

    try:
        verified = wa.verify_stage_receipt(root, receipt, policy=policy)
    except wa.AssuranceError as exc:
        raise StartPathError(str(exc), 1) from exc

    resolved_out = output_path if output_path.is_absolute() else (root / output_path).resolve()
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    out_bytes = canonical_bytes(verified) + b"\n"
    resolved_out.write_bytes(out_bytes)
    out_rel = normalize_relative_path(resolved_out.relative_to(root).as_posix(), root=root)

    receipt_ref: dict[str, Any] = {
        "path": out_rel,
        "sha256": sha256_hex(out_bytes),
        "revision": None,
    }
    if commit_changes:
        to_commit = [out_rel]
        if update_policy and resolved_policy_path.is_relative_to(root):
            to_commit.append(normalize_relative_path(resolved_policy_path.relative_to(root).as_posix(), root=root))
        commit_sha = _git_ensure_committed(root, to_commit, f"publish stage receipt {policy['operation_id']}")
        receipt_ref["revision"] = commit_sha

    return {
        "verified": True,
        "receipt_path": out_rel,
        "receipt_ref": receipt_ref,
        "receipt": verified,
    }


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


def verify_route_scope_eligibility(
    root: Path,
    route: str,
    files: list[str] | dict[str, Any] | None,
    *,
    contract_id: str | None = None,
    feature_id: str | None = None,
    candidate: dict[str, Any] | None = None,
) -> list[str]:
    """Enforce a single canonical scope eligibility decision across classify, begin, done, and receipt verification."""
    if isinstance(files, dict):
        intent_doc = files
        if feature_id is not None and intent_doc.get("id") != feature_id:
            raise StartPathError("intent id does not match feature_id", 1)
        if intent_doc.get("path") not in (None, route):
            raise StartPathError(f"intent path must be {route!r}", 1)
        if intent_doc.get("needs_new_contract") is True:
            raise StartPathError("needs_new_contract is true; use the feature path", 1)
        if contract_id is None and isinstance(intent_doc.get("contract_id"), str):
            contract_id = intent_doc["contract_id"]
        file_list = intent_doc.get("files")
    else:
        file_list = files

    scoped = normalize_file_list(file_list, root=root, allow_empty=False)
    classification = classify_task(
        files=scoped,
        is_bugfix=(route == "bugfix"),
        is_editorial=(route == "trivial"),
        needs_new_contract=False,
        root=root,
    )
    computed_route = classification["route"]

    if route == "trivial":
        if computed_route != "trivial":
            raise StartPathError(
                f"trivial path cannot modify schema, governance, tooling, or high-risk files (classified as {computed_route}): "
                + ", ".join(scoped),
                1,
            )
    elif route == "small-change":
        if computed_route not in ("trivial", "small-change"):
            raise StartPathError(
                f"small-change path cannot modify {computed_route} files (use feature/high-risk contract path): "
                + ", ".join(scoped),
                1,
            )
    elif route == "bugfix":
        if computed_route in ("standard-feature", "high-risk") and contract_id is None:
            raise StartPathError(
                f"bugfix touching {computed_route} files requires an approved contract_id: " + ", ".join(scoped),
                1,
            )
    else:
        raise StartPathError(f"unsupported non-feature route: {route}", 2)
    return scoped


def verify_actual_changed_scope(root: Path, route: str, declared_files: list[str]) -> None:
    """Verify declared scope remains eligible and that no undeclared non-.agent working-tree changes exist."""
    scoped = verify_route_scope_eligibility(root, route, declared_files)
    git_check = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        check=False,
    )
    if git_check.returncode != 0 or git_check.stdout.strip() != "true":
        return

    top_res = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if top_res.returncode != 0 or Path(top_res.stdout.strip()).resolve() != root.resolve():
        return

    status_res = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "-z", "--untracked-files=all"],
        capture_output=True,
        check=False,
    )
    if status_res.returncode != 0:
        return

    declared_set = set(scoped)
    undeclared: list[str] = []
    entries = status_res.stdout.split(b"\x00")
    idx = 0
    while idx < len(entries):
        entry = entries[idx]
        idx += 1
        if not entry or len(entry) < 4:
            continue
        xy = entry[:2].decode("ascii", errors="replace")
        raw_path = entry[3:].decode("utf-8", errors="replace")
        if "R" in xy or "C" in xy:
            idx += 1
        try:
            norm = normalize_relative_path(raw_path, root=root, forbid_nizam_payload=False)
        except StartPathError:
            norm = raw_path.strip()
        if norm.startswith(".agent/"):
            continue
        if norm not in declared_set and norm not in undeclared:
            undeclared.append(norm)

    if undeclared:
        raise StartPathError(
            f"{route} completion failed: working tree contains undeclared changes outside scoped files: "
            + ", ".join(undeclared),
            1,
        )


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
    scoped = verify_route_scope_eligibility(
        root,
        "bugfix",
        scope.get("files"),
        contract_id=contract_id,
    )
    scope["files"] = scoped
    if contract_id is not None:
        require_inside_contract(root, contract_id, scoped)
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
    if intent.get("path") not in (None, "trivial"):
        raise StartPathError("intent path must be 'trivial'", 1)
    if intent["needs_new_contract"] is True:
        raise StartPathError("needs_new_contract is true; use the feature path", 1)
    scoped = verify_route_scope_eligibility(root, "trivial", intent.get("files"))
    intent["files"] = scoped
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
    if intent.get("path") not in (None, "small-change"):
        raise StartPathError("intent path must be 'small-change'", 1)
    if intent["needs_new_contract"] is True:
        raise StartPathError(
            "needs_new_contract is true; use the feature path",
            1,
        )
    scoped = verify_route_scope_eligibility(root, "small-change", intent.get("files"))
    intent["files"] = scoped
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
                    allowed.add(normalize_relative_path(entry["path"], root=root, forbid_nizam_payload=False))
    outside = [path for path in files if path not in allowed]
    if outside:
        raise StartPathError(
            "scoped files are not inside the named contract: " + ", ".join(outside),
            1,
        )


def load_passing_qa(root: Path, path_id: str) -> None:
    """Require a schema-valid passing QA verdict bound to path_id with >=1 passing check and non-empty evidence."""
    verdict = load_record(
        root,
        Path(".agent") / "qa" / f"{path_id}.json",
        "qa_verdict.schema.json",
    )
    verdict_id = verdict.get("feature_id") or verdict.get("id")
    if verdict_id != path_id:
        raise StartPathError(
            f"QA verdict feature_id ({verdict_id!r}) does not match --id ({path_id!r})",
            1,
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
        if len(path.read_bytes().strip()) == 0:
            raise StartPathError("evidence file is empty (non-empty verification output required): " + relative, 1)


def qa_passes(verdict: dict) -> bool:
    """Apply the pass rule for either shipped QA verdict shape, requiring >=1 executed passing check."""
    if verdict.get("qa_pass") is True:
        checks_run = verdict.get("checks_run")
        checks_passed = verdict.get("checks_passed")
        if not isinstance(checks_run, int) or isinstance(checks_run, bool) or checks_run < 1:
            return False
        if not isinstance(checks_passed, int) or isinstance(checks_passed, bool) or checks_passed != checks_run:
            return False
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
        checks = verdict.get("checks")
        if not isinstance(checks, list) or len(checks) < 1:
            return False
        if any(not isinstance(c, dict) or c.get("status") not in (None, "pass") for c in checks):
            return False
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
    """Resolve a repository-relative file and reject paths that leave root or traverse symlinks."""
    norm = normalize_relative_path(relative, root=root, forbid_nizam_payload=False, reject_symlinks=True)
    path = (root / norm).resolve()
    if not path.is_relative_to(root.resolve()):
        raise StartPathError("path leaves the project root: " + relative, 1)
    return path


def require_project_path(relative: str, root: Path | None = None) -> str:
    """Reject absolute paths, parent-directory segments, and symlink escapes."""
    return normalize_relative_path(relative, root=root)


class StartPathError(Exception):
    """A start-path decision failed closed."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


if __name__ == "__main__":
    sys.exit(main())

