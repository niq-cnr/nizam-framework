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
- Noncommitting preparation, externally mediated publication, and finalization of captured evidence:
    tools/start_path.py publish [--mode prepare|publish|finalize] --capture <file> [--capture <file> ...] [--root <root>]
    tools/start_path.py prepare-publish --capture <file> [--capture <file> ...] [--root <root>]
    tools/start_path.py finalize-publish --capture <file> [--capture <file> ...] [--root <root>]
- Noncommitting stage-receipt construction and verification (with optional externally mediated commit):
    tools/start_path.py build-receipt --policy <file> --published <file> [--published <file> ...] --output <file> [--root <root>]
- Concise read-only status/readiness view:
    tools/start_path.py status [--format json|markdown] [--root <root>]
- Operational receipt transition / failure routing:
    tools/start_path.py resume --policy <file> [--receipt <file>] [--apply] [--root <root>]
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
import datetime
import hashlib
import json
import os
import platform
import re
import secrets
import stat
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
        "prepare-publish",
        "finalize-publish",
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


def _add_publish_arguments(p: argparse.ArgumentParser, *, default_mode: str | None = None) -> None:
    p.add_argument("--capture", action="append", required=True, type=Path, dest="captures", help="Path to raw <stem>.capture.json file (repeatable for multi-capture batching).")
    if default_mode is None:
        p.add_argument("--mode", choices=("prepare", "publish", "finalize"), default="prepare", help="Publication mode: noncommitting prepare (default), externally mediated publish, or noncommitting finalize.")
    else:
        p.set_defaults(mode=default_mode)
    p.add_argument("--output-revision", default=None, help="Optional expected 40-hex commit revision for Stage 1 capture outputs.")
    p.add_argument("--capture-revision", default=None, help="Optional expected 40-hex commit revision for Stage 2 receipt-capture.")
    p.add_argument("--stop-after-stage", choices=("outputs",), default=None, help="Stop after committing Stage 1 outputs and writing receipt-capture.json on disk.")
    p.add_argument("--root", type=Path, default=Path.cwd())


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
    capture_p.add_argument(
        "--continuation-basis",
        choices=("bounded-amendment", "verified-decomposition", "configured-step-limit", "operator-reset"),
        default=None,
        help="Qualifying continuation basis when attempt > 3 or decomposing a task.",
    )
    capture_p.add_argument("--parent-attempt", type=int, default=None, help="Parent attempt number for repair/continuation lineage.")
    capture_p.add_argument("--decomposition-of", default=None, help="Parent task/step identifier when continuing via verified decomposition.")
    capture_p.add_argument("--repair-summary", default=None, help="Bounded repair, amendment, or decomposition summary differentiating this attempt.")
    capture_p.add_argument("--defect-signature", default=None, help="Observed or targeted defect signature for repeated-failure detection.")
    capture_p.add_argument("--invariant-breach", action="store_true", help="Signal an invariant or authority breach (forces immediate hard stop).")
    capture_p.add_argument("--agent-id", default="nizam-local-agent")
    capture_p.add_argument("--session-id", default="local-session")
    capture_p.add_argument("--timeout-sec", type=float, default=None)
    capture_p.add_argument("--root", type=Path, default=Path.cwd())
    capture_p.add_argument("cmd", nargs=argparse.REMAINDER)

    publish_p = sub.add_parser("publish", help="Prepare, publish, or finalize completed capture outputs and project a closed 12-field receipt capture.")
    _add_publish_arguments(publish_p, default_mode=None)

    prep_pub_p = sub.add_parser("prepare-publish", help="Validate capture outputs and emit a noncommitting publish-request without mutating Git.")
    _add_publish_arguments(prep_pub_p, default_mode="prepare")

    fin_pub_p = sub.add_parser("finalize-publish", help="Verify committed capture blobs/modes and finalize .published.json without mutating Git.")
    _add_publish_arguments(fin_pub_p, default_mode="finalize")

    build_receipt_p = sub.add_parser("build-receipt", help="Bind published capture(s) into a stage receipt and verify with verify_stage_receipt.")
    build_receipt_p.add_argument("--policy", required=True, type=Path)
    build_receipt_p.add_argument("--published", action="append", required=True, type=Path, help="Path to <stem>.published.json or committed <stem>.receipt-capture.json (repeatable).")
    build_receipt_p.add_argument("--output", required=True, type=Path, help="Output path for the verified receipt JSON.")
    build_receipt_p.add_argument("--update-policy", action="store_true", help="Write pinned capture refs back into the policy file.")
    build_receipt_p.add_argument("--commit", action="store_true", help="Commit the generated receipt (and updated policy) via the externally mediated commit path.")
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
                continuation_basis=args.continuation_basis,
                parent_attempt=args.parent_attempt,
                decomposition_of=args.decomposition_of,
                repair_summary=args.repair_summary,
                defect_signature=args.defect_signature,
                invariant_breach=args.invariant_breach,
                agent_id=args.agent_id,
                session_id=args.session_id,
                timeout_sec=args.timeout_sec,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["outcome"] == "success" else 1
        if args.subcommand in ("publish", "prepare-publish", "finalize-publish"):
            result = publish_captured_evidence(
                args.root.resolve(),
                capture_path=args.captures[0] if len(args.captures) == 1 else None,
                capture_paths=args.captures,
                mode=args.mode,
                output_revision=args.output_revision,
                capture_revision=args.capture_revision,
                stop_after_stage=args.stop_after_stage,
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
            _record_task_base(root, path_id, route="bugfix", files=scope["files"], contract_id=scope.get("contract_id"))
            return f"bugfix {cause['id']}: implementation may begin"
        verify_actual_changed_scope(root, "bugfix", scope["files"], path_id, contract_id=scope.get("contract_id"))
        load_passing_qa(root, path_id)
        return f"bugfix {scope['id']}: recorded verification result exists"
    if kind == "trivial":
        intent = load_trivial_intent(root, path_id)
        if decision == "begin":
            _record_task_base(root, path_id, route="trivial", files=intent["files"])
            return f"trivial {intent['id']}: implementation may begin"
        verify_actual_changed_scope(root, "trivial", intent["files"], path_id)
        load_passing_qa(root, path_id)
        return f"trivial {intent['id']}: recorded verification result exists"
    intent = load_intent(root, path_id)
    if decision == "begin":
        _record_task_base(root, path_id, route="small-change", files=intent["files"])
        return f"small-change {intent['id']}: implementation may begin"
    verify_actual_changed_scope(root, "small-change", intent["files"], path_id)
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
            "initial_strategy_ladder_attempts": 3,
            "hard_attempt_cap": 6,
            "attempt_counter_role": "finite task-wide failed-execution budget",
            "breaker_ref": "methodology/03_circuit_breaker.md",
            "comparator_subordinate": True,
            "continuation_policy": (
                "At most six failed executions per task across steps/output directories and at most three "
                "with one defect signature; only explicit task-scoped finite operator recovery can reopen a budget. "
                "Narratives, amendments, decomposition labels and successful unrelated checks do not reset failures."
            ),
            "pass_condition": (
                "All required_gates for route '" + route + "' exit 0 and blocking verdict arrays are empty."
            ),
            "halt_condition": (
                "Stop and escalate on exhausted task/step failure budgets, three identical task-wide failures, "
                "contradiction with approved contract/invariants, "
                "missing operator authority, or exhausted execution budget/step limit; "
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

    if canonical_bytes(updated) == canonical_bytes(contract):
        raise StartPathError("lightweight amendment is a no-op; no scope or verification changes", 1)

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

    git_res = _run_git_readonly(root, ["rev-parse", "--show-toplevel"], text=True)
    if git_res.returncode == 0:
        capabilities["git_available"] = True
        capabilities["git_toplevel"] = git_res.stdout.strip()
    else:
        failures.append("git rev-parse --show-toplevel failed")

    origin_res = _run_git_readonly(root, ["remote", "get-url", "origin"], text=True)
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


def _load_git_seam():
    import importlib.util
    seam_path = Path(__file__).resolve().with_name("git_seam.py")
    if not seam_path.is_file():
        return None
    mod_name = "_nizam_git_seam_" + sha256_hex(str(seam_path).encode("utf-8"))[:16]
    if mod_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(mod_name, seam_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
    return sys.modules[mod_name]


def _run_git_readonly(
    root: Path,
    args: list[str],
    *,
    text: bool = False,
) -> subprocess.CompletedProcess:
    """Run a read-only Git query via the hardened git_seam with replacement and redirection disabled."""
    seam = _load_git_seam()
    if seam is not None:
        return seam.run_git_completed(root, args, text=text)
    if Path(root).is_symlink():
        empty = "" if text else b""
        err = "repository root is symlink\n" if text else b"repository root is symlink\n"
        return subprocess.CompletedProcess(["git", "-C", str(root), *args], 128, stdout=empty, stderr=err)
    clean_args = [a for idx, a in enumerate(args) if not (idx == 0 and a in ("--literal-pathspecs", "--no-replace-objects", "--no-optional-locks"))]
    git_env = {
        "HOME": os.devnull,
        "XDG_CONFIG_HOME": os.devnull,
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.environ.get("PATH") or "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
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
    return subprocess.run(
        ["git", "-C", str(root), "--no-optional-locks", "--no-replace-objects", "--literal-pathspecs", *clean_args],
        env=git_env,
        capture_output=True,
        text=text,
        check=False,
    )


def _authoritative_consumed_attempts(root: Path, task_id: str, step: str) -> int:
    """Return the highest already-consumed attempt number for a task/step.

    Authoritative across output directories, sessions and model switches: the
    durable circuit_breaker counter plus every prior capture file under the
    canonical evidence tree. A caller cannot reset this by choosing a different
    ``--output-dir`` or a lower ``--attempt``.
    """
    consumed = 0
    state_path = root / ".agent" / "run_state.json"
    if state_path.is_file():
        try:
            state_doc = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state_doc = {}
        if isinstance(state_doc, dict):
            cb = state_doc.get("circuit_breaker")
            if isinstance(cb, dict):
                for key in (f"{task_id}-{step}", task_id):
                    entry = cb.get(key)
                    if isinstance(entry, dict):
                        raw = entry.get("attempts")
                        if isinstance(raw, int) and not isinstance(raw, bool):
                            consumed = max(consumed, raw)
    evidence_root = root / ".agent" / "evidence"
    if evidence_root.is_dir():
        for cap_file in evidence_root.rglob(f"{task_id}-{step}-attempt*.capture.json"):
            match = re.search(r"-attempt(\d+)-", cap_file.name)
            if match:
                consumed = max(consumed, int(match.group(1)))
        for res_file in evidence_root.rglob(f"{task_id}-{step}-attempt*.reservation.json"):
            match = re.search(r"-attempt(\d+)\.reservation\.json$", res_file.name)
            if match:
                consumed = max(consumed, int(match.group(1)))
    return consumed


def _reserve_attempt(root: Path, task_id: str, step: str, attempt: int) -> None:
    """Atomically reserve an attempt number before dispatch.

    The reservation marker lives in the canonical evidence tree (not the
    caller's output directory), so concurrent allocations and output-directory
    changes cannot share or reset a sequence number. Exclusive create is the
    compare-and-swap; a pre-existing marker means the number is already taken.
    """
    marker = root / ".agent" / "evidence" / f"{task_id}-{step}-attempt{attempt}.reservation.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "schema_version": 1,
        "id": task_id,
        "step": step,
        "attempt": attempt,
        "reserved_at": utc_now_iso(),
    }
    try:
        with marker.open("xb") as fh:
            fh.write(canonical_bytes(doc) + b"\n")
    except FileExistsError:
        raise StartPathError(
            f"attempt {attempt} for {task_id}:{step} is already reserved; concurrent allocation refused",
            2,
        )


def _task_capture_history(root: Path, task_id: str) -> list[dict[str, Any]]:
    """Read task-wide canonical evidence without forgiving corrupt matching history."""
    evidence = root / ".agent" / "evidence"
    history = []
    if not evidence.exists():
        return history
    if evidence.is_symlink():
        raise StartPathError("stopping policy halt: symlink evidence history", 2)
    for path in sorted(evidence.rglob("*.capture.json")):
        doc = None
        relevant_name = path.name.startswith(task_id + "-")
        try:
            if path.is_symlink():
                if relevant_name:
                    raise ValueError("symlink history")
                continue
            doc = json.loads(path.read_bytes())
            if not isinstance(doc, dict):
                raise ValueError("non-object history")
            if doc.get("id") != task_id:
                if relevant_name and not isinstance(doc.get("id"), str):
                    raise ValueError("missing task identity")
                continue
            relative = path.relative_to(root).as_posix()
            if resolve_project_file(root, relative) != path or doc.get("capture_path") != relative or not ID_PATTERN.fullmatch(str(doc.get("step", ""))) or type(doc.get("attempt")) is not int or doc["attempt"] < 1:
                raise ValueError("invalid capture identity")
            if not isinstance(doc.get("argv"), list) or not doc["argv"] or any(not isinstance(v, str) or not v for v in doc["argv"]) or type(doc.get("executed")) is not bool or not isinstance(doc.get("outcome"), str):
                raise ValueError("invalid observed execution")
            if doc.get("executed") and type(doc.get("exit_code")) is not int:
                raise ValueError("invalid observed result")
            if doc["outcome"] in ("success", "semantic-negative") and (doc.get("executed") is not True or doc.get("exit_code") != 0 or doc.get("completion_state") != "completed" or doc.get("signal") is not None):
                raise ValueError("contradictory successful capture")
            for stream in ("stdout", "stderr"):
                ref = doc.get(stream)
                if not isinstance(ref, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(ref.get("sha256"))):
                    raise ValueError("invalid history stream")
                actual = resolve_project_file(root, ref["path"])
                if not actual.is_file() or sha256_hex(actual.read_bytes()) != ref["sha256"]:
                    raise ValueError("history stream changed")
            history.append(doc)
        except (OSError, ValueError, TypeError, KeyError, StartPathError) as exc:
            if relevant_name or (isinstance(locals().get("doc"), dict) and doc.get("id") == task_id):
                raise StartPathError("stopping policy halt: corrupt task capture history: " + str(path), 2) from exc
    return history


def _successful_task_capture(root: Path, doc: dict[str, Any], checks: list[dict[str, Any]] | None = None, candidate_sha256: str | None = None) -> bool:
    if doc.get("executed") is not True or doc.get("completion_state") != "completed" or doc.get("signal") is not None:
        return False
    if doc.get("exit_code") == 0 and doc.get("outcome") in ("success", "semantic-negative"):
        return True
    # Only the producer's prevalidated inventory predicate qualifies a raw
    # expected refusal. A semantic-negative label on its own grants no credit.
    qualified = (doc.get("continuation_lineage") or {}).get("qa_expected_predicate")
    if qualified is None and checks is not None and candidate_sha256 and doc.get("candidate_sha256") == candidate_sha256:
        match = next((check for check in checks if check["argv"] == doc.get("argv") and check["proof_kind"] == doc.get("proof_kind")), None)
        if match:
            qualified = {"context": (doc.get("environment") or {}).get("variables", {}).get("NIZAM_QA_CONTEXT_SHA256"), "check": match}
    if not isinstance(qualified, dict) or set(qualified) != {"context", "check"}:
        return False
    check = qualified["check"]
    variables = (doc.get("environment") or {}).get("variables", {})
    if not isinstance(check, dict) or qualified["context"] != variables.get("NIZAM_QA_CONTEXT_SHA256") or not qualified["context"]:
        return False
    if check.get("argv") != doc.get("argv") or check.get("proof_kind") != "semantic-negative" or doc.get("proof_kind") != "semantic-negative" or type(check.get("expected_exit")) is not int or check["expected_exit"] != doc.get("exit_code") or doc.get("outcome") != "failed" or not isinstance(check.get("diagnostic"), str) or not check["diagnostic"]:
        return False
    try:
        return any(check["diagnostic"] in resolve_project_file(root, doc[stream]["path"]).read_text(encoding="utf-8").splitlines() for stream in ("stdout", "stderr"))
    except (OSError, UnicodeError, KeyError, StartPathError):
        return False


def _failure_signature(doc: dict[str, Any]) -> str:
    signature = doc.get("defect_signature")
    if isinstance(signature, str) and signature and not signature.startswith("exit:"):
        return signature
    observed = {key: doc.get(key) for key in ("argv", "outcome", "exit_code", "signal", "completion_state")}
    observed.update({key: (doc.get(key) or {}).get("sha256") for key in ("stdout", "stderr")})
    return "observed:" + sha256_hex(canonical_bytes(observed))


def _evaluate_attempt_continuation(
    root: Path, *, task_id: str, step: str, attempt: int, target_dir: Path,
    continuation_basis: str | None = None, parent_attempt: int | None = None,
    decomposition_of: str | None = None, repair_summary: str | None = None,
    defect_signature: str | None = None, invariant_breach: bool = False,
    qa_checks: list[dict[str, Any]] | None = None, candidate_sha256: str | None = None,
) -> dict[str, Any]:
    """Apply finite task-wide failure budgets before accepting continuation labels."""
    if invariant_breach:
        raise StartPathError("stopping policy halt: invariant or authority boundary breached", 2)
    consumed = _authoritative_consumed_attempts(root, task_id, step)
    if attempt <= consumed:
        raise StartPathError(f"stopping policy halt: attempt {attempt} reuses already-consumed attempt history for {task_id}:{step}", 2)
    history = _task_capture_history(root, task_id)
    failed = [p for p in history if not _successful_task_capture(root, p, qa_checks, candidate_sha256)]
    state_path = root / ".agent" / "run_state.json"
    state = {}
    if state_path.exists():
        try:
            state = json.loads(resolve_project_file(root, ".agent/run_state.json").read_bytes())
            if not isinstance(state, dict):
                raise ValueError("invalid state")
        except (ValueError, OSError) as exc:
            raise StartPathError("stopping policy halt: unreadable circuit-breaker state", 2) from exc
    counters = state.get("circuit_breaker", {})
    task_entry = counters.get(task_id, {}) if isinstance(counters, dict) else {}
    step_entry = counters.get(f"{task_id}-{step}", task_entry) if isinstance(counters, dict) else {}
    if not isinstance(task_entry, dict) or not isinstance(step_entry, dict):
        raise StartPathError("stopping policy halt: malformed task circuit breaker", 2)
    if any(e.get("invariant_breach") is True or e.get("authority_denied") is True for e in (task_entry, step_entry)):
        raise StartPathError("stopping policy halt: invariant or authority boundary breached in circuit_breaker", 2)
    limit = step_entry.get("limit", 3)
    if type(limit) is not int or limit < 1:
        raise StartPathError("stopping policy halt: step limit must be finite positive integer", 2)
    recovery = task_entry.get("operator_recovery")
    ceiling = 6
    recovered = False
    if recovery is not None:
        required = {"task_id", "approved", "max_task_attempts", "after_capture", "authority_ref"}
        if not isinstance(recovery, dict) or set(recovery) != required or recovery["task_id"] != task_id or recovery["approved"] is not True or type(recovery["max_task_attempts"]) is not int or recovery["max_task_attempts"] < 1:
            raise StartPathError("stopping policy halt: explicit finite task operator recovery required", 2)
        try:
            authority = json.loads(resolve_project_file(root, recovery["authority_ref"]).read_bytes())
        except (ValueError, OSError, TypeError) as exc:
            raise StartPathError("stopping policy halt: invalid operator recovery authority", 2) from exc
        if authority != {"role": "operator", **recovery} or recovery["after_capture"] not in {p["capture_path"] for p in failed}:
            raise StartPathError("stopping policy halt: operator recovery lacks exact task/failed-capture binding", 2)
        ceiling = recovery["max_task_attempts"]
        recovered = True
    if len(failed) >= ceiling:
        raise StartPathError(f"stopping policy halt: finite task failed-execution budget ({ceiling}) exhausted", 2)
    signatures: dict[str, int] = {}
    for doc in failed:
        signature = _failure_signature(doc)
        signatures[signature] = signatures.get(signature, 0) + 1
    if max(signatures.values(), default=0) >= 3 and not recovered:
        raise StartPathError("stopping policy halt: three failures of the same task-wide defect signature; explicit finite task operator recovery required", 2)
    if decomposition_of:
        if decomposition_of in (task_id, step, f"{task_id}-{step}"):
            raise StartPathError("stopping policy halt: decomposition parent must be distinct", 2)
        parents = [p for p in failed if decomposition_of in (p["step"], p["capture_path"], f"{task_id}-{p['step']}")]
        if not parents:
            raise StartPathError("stopping policy halt: decomposition requires a real distinct failed parent", 2)
    if continuation_basis == "verified-decomposition" and not decomposition_of:
        raise StartPathError("stopping policy halt: verified-decomposition requires --decomposition-of", 2)
    if attempt > limit:
        raise StartPathError(f"stopping policy halt: finite configured step limit ({limit}) exhausted; labels and amendments grant no attempts", 2)
    if continuation_basis == "operator-reset" and not recovered:
        raise StartPathError("stopping policy halt: operator-reset requires recorded operator authorization with a finite exact task budget", 2)
    return {"initial_strategy_ladder_attempts": 3, "attempt": attempt, "parent_attempt": parent_attempt,
        "decomposition_of": decomposition_of, "continuation_basis": continuation_basis or ("initial-attempt" if attempt == 1 else "strategy-ladder"),
        "repair_summary": repair_summary, "configured_step_limit": limit, "contract_amendment_present": False,
        "operator_extension_present": recovered, "failed_execution_count": len(failed), "task_failed_execution_ceiling": ceiling,
        "prior_attempts": [{k: p.get(k) for k in ("id", "step", "attempt", "capture_path", "outcome", "exit_code", "defect_signature")} for p in history]}


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
    continuation_basis: str | None = None,
    parent_attempt: int | None = None,
    decomposition_of: str | None = None,
    repair_summary: str | None = None,
    defect_signature: str | None = None,
    invariant_breach: bool = False,
    agent_id: str = "nizam-local-agent",
    session_id: str = "local-session",
    timeout_sec: float | None = None,
) -> dict[str, Any]:
    """Execute a command and write stdout, stderr, and raw capture metadata to exclusive paths."""
    if not ID_PATTERN.fullmatch(task_id):
        raise StartPathError("task_id is not a single safe path token", 2)
    if not ID_PATTERN.fullmatch(step):
        raise StartPathError("step is not a single safe path token", 2)
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise StartPathError("attempt must be an integer between 1 and 3 (or >= 1 with a qualifying continuation basis)", 2)
    if not argv or not all(isinstance(x, str) and x for x in argv):
        raise StartPathError("argv must be a non-empty list of strings", 2)
    if proof_kind not in ("success", "semantic-negative"):
        raise StartPathError("proof_kind must be 'success' or 'semantic-negative'", 2)

    resolved_sha, binding_state, captured_vars = _resolve_candidate_and_env(root, candidate_sha256, env_vars)
    if "NIZAM_QA_CONTEXT_SHA256" in captured_vars or "NIZAM_QA_EXECUTION_ROOT" in captured_vars:
        if captured_vars.get("NIZAM_QA_EXECUTION_ROOT") != str(root.resolve()):
            raise StartPathError("QA capture execution root must match the actual resolved repository root", 1)

    qa_check = None
    checks = None
    if "NIZAM_QA_CONTEXT_SHA256" in captured_vars:
        wa = _load_workflow_assurance()
        try:
            candidate = candidate_sha256
            if not isinstance(candidate, dict):
                candidate_path = Path(str(candidate_sha256))
                if not candidate_path.is_absolute():
                    candidate_path = root / candidate_path
                candidate = json.loads(candidate_path.read_bytes())
                if isinstance(candidate.get("candidate"), dict):
                    candidate = candidate["candidate"]
            checks = wa.qa_bound_checks(root, task_id, candidate)
            wa.validate_qa_context(root, task_id, candidate, checks)
            wa._receipt_candidate(root, candidate, route_id=task_id)
            qa_check = next((check for check in checks if check["argv"] == argv and check["proof_kind"] == proof_kind), None)
        except (wa.AssuranceError, OSError, ValueError, TypeError, AttributeError) as exc:
            raise StartPathError("QA candidate invalid before execution: " + str(exc), 2) from exc
        for previous in _task_capture_history(root, task_id):
            if _successful_task_capture(root, previous, checks, resolved_sha) and previous.get("candidate_sha256") == resolved_sha and previous.get("argv") == argv and previous.get("proof_kind") == proof_kind and previous.get("environment") == {"runtime": candidate["environment"]["runtime"], "variables": captured_vars}:
                raise StartPathError("identical successful assessed proof already exists; reuse " + previous["capture_path"], 2)

    rel_dir = (
        output_dir.relative_to(root).as_posix()
        if output_dir.is_absolute() and output_dir.is_relative_to(root)
        else output_dir.as_posix()
    )
    target_dir = resolve_project_file(root, rel_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    continuation_lineage = _evaluate_attempt_continuation(
        root,
        task_id=task_id,
        step=step,
        attempt=attempt,
        target_dir=target_dir,
        continuation_basis=continuation_basis,
        parent_attempt=parent_attempt,
        decomposition_of=decomposition_of,
        repair_summary=repair_summary,
        defect_signature=defect_signature,
        invariant_breach=invariant_breach,
        qa_checks=checks,
        candidate_sha256=resolved_sha,
    )

    _reserve_attempt(root, task_id, step, attempt)

    head_res = _run_git_readonly(root, ["rev-parse", "HEAD"], text=True)
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

    stdout_sha = sha256_hex(stdout_bytes)
    stderr_sha = sha256_hex(stderr_bytes)
    if qa_check is not None and proof_kind == "semantic-negative" and exit_code == qa_check["expected_exit"] and completion_state == "completed" and signal_num is None:
        try:
            matched = qa_check["diagnostic"] in [line for data in (stdout_bytes, stderr_bytes) for line in data.decode("utf-8").splitlines()]
        except UnicodeError:
            matched = False
        if matched:
            continuation_lineage["qa_expected_predicate"] = {"context": captured_vars["NIZAM_QA_CONTEXT_SHA256"], "check": qa_check}
    effective_defect_sig = defect_signature
    if effective_defect_sig is None and outcome != proof_kind:
        effective_defect_sig = _failure_signature({"argv": argv, "outcome": outcome, "exit_code": exit_code, "signal": signal_num, "completion_state": completion_state, "stdout": {"sha256": stdout_sha}, "stderr": {"sha256": stderr_sha}})

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
        "defect_signature": effective_defect_sig,
        "continuation_lineage": continuation_lineage,
        "exit_code": exit_code,
        "signal": signal_num,
        "stdout": {
            "path": stdout_rel,
            "sha256": stdout_sha,
            "revision": None,
        },
        "stderr": {
            "path": stderr_rel,
            "sha256": stderr_sha,
            "revision": None,
        },
        "capture_path": receipt_rel,
    }
    with receipt_path.open("xb") as fh:
        fh.write(canonical_bytes(capture_doc) + b"\n")
    return capture_doc


def _get_git_branch_state(root: Path) -> tuple[str | None, bool]:
    """Return (branch_name_or_None, detached_head_bool) for root."""
    sym_res = _run_git_readonly(root, ["symbolic-ref", "-q", "--short", "HEAD"], text=True)
    if sym_res.returncode == 0 and sym_res.stdout.strip():
        return sym_res.stdout.strip(), False
    return None, True


def _verify_git_worktree_root(root: Path) -> tuple[str, str, Path]:
    """Verify that root is the exact Git worktree toplevel and return (head_sha, origin_url, real_index_path)."""
    wt_res = _run_git_readonly(root, ["rev-parse", "--is-inside-work-tree"], text=True)
    if wt_res.returncode != 0 or wt_res.stdout.strip() != "true":
        raise StartPathError(f"target root is not inside a Git working tree: {root}", 1)
    top_res = _run_git_readonly(root, ["rev-parse", "--show-toplevel"], text=True)
    if top_res.returncode != 0 or not top_res.stdout.strip():
        raise StartPathError(f"git rev-parse --show-toplevel failed for {root}", 1)
    if Path(top_res.stdout.strip()).resolve() != root.resolve():
        raise StartPathError(
            f"target root ({root.resolve()}) does not match Git worktree toplevel ({Path(top_res.stdout.strip()).resolve()})",
            1,
        )
    head_res = _run_git_readonly(root, ["rev-parse", "--verify", "HEAD^{commit}"], text=True)
    if head_res.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", head_res.stdout.strip()):
        raise StartPathError("git rev-parse HEAD^{commit} failed during evidence publication", 1)
    head_sha = head_res.stdout.strip()

    idx_res = _run_git_readonly(root, ["rev-parse", "--git-path", "index"], text=True)
    if idx_res.returncode != 0 or not idx_res.stdout.strip():
        raise StartPathError("git rev-parse --git-path index failed", 1)
    raw_idx = Path(idx_res.stdout.strip())
    real_index_path = raw_idx if raw_idx.is_absolute() else (root / raw_idx)

    origin_res = _run_git_readonly(root, ["remote", "get-url", "origin"], text=True)
    origin_url = origin_res.stdout.strip() if origin_res.returncode == 0 and origin_res.stdout.strip() else str(root)
    return head_sha, origin_url, real_index_path


def _verify_regular_file_mode_100644(root: Path, rel_path: str) -> tuple[Path, bytes, str]:
    """Verify rel_path is an existing regular non-symlink non-executable file (mode 100644) and return (path, bytes, sha256)."""
    norm = normalize_relative_path(rel_path, root=root, reject_symlinks=True, forbid_nizam_payload=True)
    fpath = resolve_project_file(root, norm)
    if fpath.is_symlink() or not fpath.is_file():
        raise StartPathError(f"evidence path does not exist as a regular file: {norm}", 1)
    st_mode = fpath.stat().st_mode
    if (st_mode & 0o111) != 0:
        raise StartPathError(f"evidence file must have regular mode 100644 (executable bit forbidden): {norm}", 1)
    raw_bytes = fpath.read_bytes()
    return fpath, raw_bytes, sha256_hex(raw_bytes)


def _verify_git_status_and_no_staged_conflicts(
    root: Path,
    norm_paths: list[str],
    *,
    check_staged_conflicts: bool = True,
) -> None:
    """Verify git status and git diff --cached exit 0 without refreshing .git/index, and reject same-path staged entries."""
    if not norm_paths:
        return
    lit_specs = list(norm_paths)
    status_res = _run_git_readonly(root, ["status", "--porcelain", "-z", "--", *lit_specs], text=False)
    if status_res.returncode != 0:
        err_msg = status_res.stderr.decode("utf-8", errors="replace").strip()
        raise StartPathError(f"git status failed during evidence publication: {err_msg}", 1)

    diff_res = _run_git_readonly(root, ["diff", "--cached", "--name-only", "-z", "--", *lit_specs], text=False)
    if diff_res.returncode != 0:
        err_msg = diff_res.stderr.decode("utf-8", errors="replace").strip()
        raise StartPathError(f"git diff --cached failed during evidence publication: {err_msg}", 1)

    if check_staged_conflicts:
        staged = [
            entry.decode("utf-8", errors="replace")
            for entry in diff_res.stdout.split(b"\x00")
            if entry
        ]
        if staged:
            raise StartPathError(
                "same-path staged conflict in .git/index for: " + ", ".join(staged),
                1,
            )


def _get_committed_blob_info(root: Path, revision: str, rel_path: str) -> tuple[str, str] | None:
    """Return (mode, sha256_hex) of rel_path at revision, or None if not present in the revision's tree."""
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise StartPathError(f"invalid 40-hex Git revision: {revision!r}", 1)
    commit_check = _run_git_readonly(root, ["rev-parse", "--verify", f"{revision}^{{commit}}"], text=True)
    if commit_check.returncode != 0 or commit_check.stdout.strip() != revision:
        raise StartPathError(f"Git commit does not exist: {revision}", 1)

    ls_res = _run_git_readonly(root, ["ls-tree", "-z", revision, "--", rel_path], text=False)
    if ls_res.returncode != 0:
        err = ls_res.stderr.decode("utf-8", errors="replace").strip()
        raise StartPathError(f"git ls-tree failed for {revision}:{rel_path}: {err}", 1)
    rows = [r for r in ls_res.stdout.split(b"\x00") if r]
    if not rows:
        return None
    if len(rows) != 1:
        raise StartPathError(f"unexpected git ls-tree output for {revision}:{rel_path}", 1)
    header_bytes, _, _ = rows[0].partition(b"\t")
    parts = header_bytes.decode("ascii", errors="replace").split()
    if len(parts) != 3:
        raise StartPathError(f"unexpected git ls-tree output for {revision}:{rel_path}", 1)
    mode, obj_type, obj_hash = parts
    if obj_type != "blob":
        raise StartPathError(f"committed object at {revision}:{rel_path} is not a blob ({obj_type})", 1)
    cat_res = _run_git_readonly(root, ["cat-file", "blob", obj_hash], text=False)
    if cat_res.returncode != 0:
        raise StartPathError(f"git cat-file blob failed for {revision}:{rel_path}", 1)
    return mode, sha256_hex(cat_res.stdout)


def _find_last_commit_for_paths(root: Path, revision: str, norm_paths: list[str]) -> str:
    """Return the most recent 40-hex commit in revision's history that touched norm_paths."""
    lit_specs = list(norm_paths)
    log_res = _run_git_readonly(root, ["log", "-n", "1", "--format=%H", revision, "--", *lit_specs], text=True)
    sha = log_res.stdout.strip()
    if log_res.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise StartPathError(f"failed to resolve commit history for {', '.join(norm_paths)} at {revision}", 1)
    return sha


def _get_commit_changed_paths(root: Path, revision: str) -> list[str]:
    """Return sorted repository-relative paths changed in revision."""
    dt_res = _run_git_readonly(
        root,
        ["diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z", revision],
        text=False,
    )
    if dt_res.returncode != 0:
        err_msg = dt_res.stderr.decode("utf-8", errors="replace").strip()
        raise StartPathError(f"git diff-tree failed for {revision}: {err_msg}", 1)
    return sorted(
        p.decode("utf-8", errors="replace")
        for p in dt_res.stdout.split(b"\x00")
        if p
    )


def _is_git_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    """Return True if ancestor is an ancestor of descendant in root."""
    res = _run_git_readonly(root, ["merge-base", "--is-ancestor", ancestor, descendant], text=True)
    return res.returncode == 0


def _get_commit_parents(root: Path, revision: str) -> list[str]:
    """Return the list of 40-hex parent commits for revision."""
    res = _run_git_readonly(root, ["rev-list", "--parents", "-n", "1", revision], text=True)
    if res.returncode != 0 or not res.stdout.strip():
        raise StartPathError(f"git rev-list --parents failed for {revision}", 1)
    parts = res.stdout.strip().split()
    return parts[1:]


def _verify_request_commit_binding(
    root: Path,
    commit_rev: str,
    expected_files: list[dict[str, str]],
    commit_req: dict[str, Any] | None = None,
    *,
    allowed_stage_paths: set[str] | None = None,
    pre_execution_revision: str | None = None,
) -> None:
    """Verify that commit_rev is bound to the active worktree, branch/base, and exact owned stage file delta."""
    head_sha, current_origin, _ = _verify_git_worktree_root(root)
    if not _is_git_ancestor(root, commit_rev, head_sha):
        raise StartPathError(
            f"stage commit {commit_rev} is not an ancestor of current HEAD ({head_sha})",
            1,
        )
    if pre_execution_revision is not None and not _is_git_ancestor(root, pre_execution_revision, commit_rev):
        raise StartPathError(
            f"pre-execution revision ({pre_execution_revision}) is not an ancestor of stage commit ({commit_rev})",
            1,
        )

    changed_paths = set(_get_commit_changed_paths(root, commit_rev))
    expected_path_set = {f["path"] for f in expected_files}
    missing_in_delta = sorted(expected_path_set - changed_paths)
    if missing_in_delta:
        raise StartPathError(
            f"stage commit {commit_rev} did not introduce expected stage file(s): {', '.join(missing_in_delta)}",
            1,
        )

    if commit_req is not None and isinstance(commit_req.get("files"), list):
        req_file_set = {
            f["path"]
            for f in commit_req["files"]
            if isinstance(f, dict) and isinstance(f.get("path"), str)
        }
        if changed_paths != req_file_set:
            extra = sorted(changed_paths - req_file_set)
            missing = sorted(req_file_set - changed_paths)
            raise StartPathError(
                f"stage commit {commit_rev} delta mismatch against publish-request (extra={extra}, missing={missing})",
                1,
            )
    else:
        permitted = set(allowed_stage_paths) if allowed_stage_paths is not None else set(expected_path_set)
        extra = sorted(changed_paths - permitted)
        if extra:
            raise StartPathError(
                f"stage commit {commit_rev} modified unauthorized path(s) outside owned stage delta: {', '.join(extra)}",
                1,
            )

    if commit_req is not None:
        if commit_req.get("repository_root") and Path(str(commit_req["repository_root"])).resolve() != root.resolve():
            raise StartPathError("publish-request repository_root does not match current worktree root", 1)
        if commit_req.get("repository") and not _repository_urls_match(str(commit_req["repository"]), current_origin):
            raise StartPathError("publish-request repository does not match current origin", 1)
        cur_branch, cur_detached = _get_git_branch_state(root)
        if "detached_head" in commit_req and bool(commit_req["detached_head"]) != cur_detached:
            raise StartPathError(
                f"current HEAD detached state ({cur_detached}) does not match publish-request detached_head ({commit_req.get('detached_head')})",
                1,
            )
        if not cur_detached and commit_req.get("intended_branch") is not None and cur_branch != commit_req.get("intended_branch"):
            raise StartPathError(
                f"current branch ({cur_branch!r}) does not match publish-request intended_branch ({commit_req.get('intended_branch')!r})",
                1,
            )
        intended_base = commit_req.get("intended_base")
        if isinstance(intended_base, str) and re.fullmatch(r"[0-9a-f]{40}", intended_base):
            parents = _get_commit_parents(root, commit_rev)
            if len(parents) != 1 or parents[0] != intended_base:
                raise StartPathError(
                    f"stage commit {commit_rev} parent ({parents}) does not match publish-request intended_base ({intended_base})",
                    1,
                )


def _check_files_committed_at_revision(
    root: Path,
    revision: str,
    expected_files: list[dict[str, str]],
    *,
    check_worktree_clean: bool = True,
) -> str | None:
    """Check whether expected_files are committed at revision with matching sha256 and mode 100644.

    Raises StartPathError if any path is already committed at revision with different content or mode,
    or if only a partial subset of expected_files is committed.
    Returns the commit SHA that introduced the files when all are present and match, or None when none are committed.
    """
    present_count = 0
    norm_paths = [f["path"] for f in expected_files]
    for item in expected_files:
        info = _get_committed_blob_info(root, revision, item["path"])
        if info is None:
            continue
        present_count += 1
        committed_mode, committed_sha = info
        expected_mode = item.get("mode", "100644")
        if committed_mode != expected_mode:
            raise StartPathError(
                f"committed file mode mismatch for {item['path']} at {revision}: expected {expected_mode}, got {committed_mode}",
                1,
            )
        if committed_sha != item["sha256"]:
            raise StartPathError(
                f"cannot overwrite committed evidence for {item['path']} at {revision}: committed sha256 ({committed_sha}) != current sha256 ({item['sha256']})",
                1,
            )
    if present_count == 0:
        return None
    if present_count != len(expected_files):
        raise StartPathError(
            f"partial committed evidence state at {revision} for: {', '.join(norm_paths)}",
            1,
        )
    if check_worktree_clean:
        _verify_git_status_and_no_staged_conflicts(root, norm_paths, check_staged_conflicts=True)
        for item in expected_files:
            _, _, disk_sha = _verify_regular_file_mode_100644(root, item["path"])
            if disk_sha != item["sha256"]:
                raise StartPathError(
                    f"working-tree file {item['path']} differs from committed evidence",
                    1,
                )
    return _find_last_commit_for_paths(root, revision, norm_paths)


def _build_commit_request(
    root: Path,
    origin_url: str,
    head_sha: str,
    stage: str,
    message: str,
    expected_files: list[dict[str, str]],
    *,
    pre_execution_revision: str | None = None,
    status: str = "pending_external_commit",
    intended_branch: str | None = None,
    detached_head: bool | None = None,
    next_action: str | None = None,
) -> dict[str, Any]:
    if intended_branch is None and detached_head is None:
        intended_branch, detached_head = _get_git_branch_state(root)
    if next_action is None:
        if stage == "outputs_pending":
            next_action = (
                "Commit the exact listed literal_pathspec files on top of intended_base via the authorized "
                "external commit path, then re-run 'tools/start_path.py publish --mode prepare' to project Stage 2."
            )
        elif stage == "receipt_capture_pending":
            next_action = (
                "Commit the exact listed literal_pathspec files on top of intended_base via the authorized "
                "external commit path, then run 'tools/start_path.py publish --mode finalize' to write .published.json."
            )
        else:
            next_action = (
                "Commit the exact listed literal_pathspec files on top of intended_base via the authorized "
                "external commit path."
            )
    req: dict[str, Any] = {
        "schema_version": 1,
        "stage": stage,
        "status": status,
        "repository_root": str(root),
        "repository": origin_url,
        "worktree": str(root),
        "intended_base": head_sha,
        "intended_branch": intended_branch,
        "detached_head": bool(detached_head),
        "commit_message": message,
        "next_action": next_action,
        "files": [
            {
                "path": f["path"],
                "sha256": f["sha256"],
                "mode": f.get("mode", "100644"),
                "literal_pathspec": f":(literal){f['path']}",
            }
            for f in expected_files
        ],
    }
    if pre_execution_revision is not None:
        req["pre_execution_revision"] = pre_execution_revision
    return req


def _write_publish_requests(request_paths: list[Path], req_doc: dict[str, Any]) -> None:
    payload = canonical_bytes(req_doc) + b"\n"
    for rpath in request_paths:
        rpath.parent.mkdir(parents=True, exist_ok=True)
        rpath.write_bytes(payload)


def _git_commit_literal_paths(
    root: Path,
    expected_files: list[dict[str, str]],
    message: str,
    *,
    stage: str,
    request_out_paths: list[Path] | None = None,
    pre_execution_revision: str | None = None,
) -> str:
    """Commit literal paths strictly via an explicitly configured NIZAM_MUTATION_ADAPTER (no implicit local commit fallback)."""
    head_sha, origin_url, _ = _verify_git_worktree_root(root)
    norm_paths: list[str] = []
    for item in expected_files:
        _, _, disk_sha = _verify_regular_file_mode_100644(root, item["path"])
        if disk_sha != item["sha256"]:
            raise StartPathError(f"on-disk digest mismatch before commit for {item['path']}", 1)
        norm_paths.append(item["path"])

    _verify_git_status_and_no_staged_conflicts(root, norm_paths, check_staged_conflicts=True)

    req_paths = request_out_paths or []
    prior_req: dict[str, Any] | None = None
    for rp in req_paths:
        if rp.is_file():
            try:
                loaded_rp = _read_json_file(rp)
                if loaded_rp.get("stage") == stage:
                    prior_req = loaded_rp
                    break
            except StartPathError:
                pass

    already_rev = _check_files_committed_at_revision(root, head_sha, expected_files, check_worktree_clean=True)
    if already_rev is not None:
        _verify_request_commit_binding(
            root,
            already_rev,
            expected_files,
            prior_req,
            pre_execution_revision=pre_execution_revision,
        )
        return already_rev

    if prior_req is not None and prior_req.get("status") in ("unknown_external_commit_outcome", "in_flight_external_commit"):
        prior_base = prior_req.get("intended_base")
        if isinstance(prior_base, str) and re.fullmatch(r"[0-9a-f]{40}", prior_base) and head_sha != prior_base:
            raise StartPathError(
                f"cannot reconcile {prior_req.get('status')}: HEAD ({head_sha}) moved away from intended_base ({prior_base}) without committing expected stage files",
                1,
            )

    commit_req = _build_commit_request(
        root,
        origin_url,
        head_sha,
        stage,
        message,
        expected_files,
        pre_execution_revision=pre_execution_revision,
    )
    if prior_req is not None and prior_req.get("status") in ("unknown_external_commit_outcome", "in_flight_external_commit"):
        commit_req["reconciled_from_status"] = prior_req["status"]

    adapter = os.environ.get("NIZAM_MUTATION_ADAPTER", "").strip()
    policy_mode = os.environ.get("NIZAM_MUTATION_POLICY", "").strip().lower()
    if policy_mode in ("deny", "none", "read-only", "readonly", "prepare-only") or adapter.lower() in (
        "deny",
        "none",
        "false",
        "0",
    ):
        commit_req["status"] = "denied_by_mutation_authority"
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(
            "git commit denied by runtime mutation authority; prepared publish-request written without mutating Git state",
            1,
        )

    if not adapter:
        commit_req["status"] = "pending_external_commit"
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(
            "external commit mediation required for --mode publish (NIZAM_MUTATION_ADAPTER is not configured); "
            "prepared publish-request written without mutating Git state",
            1,
        )

    import shlex

    try:
        adapter_argv = shlex.split(adapter)
    except ValueError as exc:
        commit_req["status"] = "denied_by_mutation_adapter"
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(f"invalid NIZAM_MUTATION_ADAPTER command syntax: {exc}", 1) from exc
    if not adapter_argv:
        commit_req["status"] = "pending_external_commit"
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(
            "external commit mediation required for --mode publish (NIZAM_MUTATION_ADAPTER is empty)",
            1,
        )
    commit_req["status"] = "in_flight_external_commit"
    _write_publish_requests(req_paths, commit_req)
    try:
        adapter_res = subprocess.run(
            adapter_argv,
            input=canonical_bytes(commit_req) + b"\n",
            cwd=str(root),
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        commit_req["status"] = "denied_by_mutation_adapter"
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(f"failed to execute runtime mutation adapter: {exc}", 1) from exc

    post_head, _, _ = _verify_git_worktree_root(root)
    if adapter_res.returncode < 0:
        commit_req["status"] = "unknown_external_commit_outcome"
        commit_req["recovery_hint"] = (
            "Re-run publish (--mode prepare, --mode publish, or --mode finalize) to reconcile actual repository commit state."
        )
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(
            f"runtime mutation adapter interrupted by signal {-adapter_res.returncode} (status=unknown_external_commit_outcome); "
            "reconcile repository state before retry",
            1,
        )

    if adapter_res.returncode != 0:
        if post_head != head_sha:
            commit_req["status"] = "unknown_external_commit_outcome"
            commit_req["recovery_hint"] = (
                "HEAD changed before adapter exited non-zero; re-run publish to verify and reconcile committed stage blobs."
            )
            _write_publish_requests(req_paths, commit_req)
            raise StartPathError(
                f"runtime mutation adapter exited {adapter_res.returncode} after HEAD advanced (status=unknown_external_commit_outcome); "
                "re-run to reconcile repository state",
                1,
            )
        commit_req["status"] = "denied_by_mutation_adapter"
        _write_publish_requests(req_paths, commit_req)
        err_detail = (
            adapter_res.stderr.decode("utf-8", errors="replace").strip()
            or adapter_res.stdout.decode("utf-8", errors="replace").strip()
        )
        raise StartPathError(
            f"git commit denied by runtime mutation adapter (exit {adapter_res.returncode}): {err_detail}",
            1,
        )

    raw_out = adapter_res.stdout.decode("utf-8", errors="replace").strip()
    if not raw_out:
        commit_req["status"] = "unknown_external_commit_outcome" if post_head != head_sha else "invalid_mutation_adapter_response"
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(
            f"runtime mutation adapter returned empty stdout (status={commit_req['status']}); refusing implicit local commit fallback",
            1,
        )

    try:
        resp = json.loads(raw_out)
    except json.JSONDecodeError as exc:
        commit_req["status"] = "unknown_external_commit_outcome" if post_head != head_sha else "invalid_mutation_adapter_response"
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(
            f"runtime mutation adapter returned invalid JSON ({exc.msg}; status={commit_req['status']})",
            1,
        ) from exc

    if not isinstance(resp, dict):
        commit_req["status"] = "unknown_external_commit_outcome" if post_head != head_sha else "invalid_mutation_adapter_response"
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError("runtime mutation adapter response must be a JSON object", 1)

    if resp.get("approved") is False or resp.get("status") in ("denied", "pending", "failed", "rejected"):
        st = str(resp.get("status") or "denied")
        commit_req["status"] = st
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(
            f"git commit {st} by runtime mutation adapter",
            1,
        )

    if resp.get("status") in ("unknown", "interrupted", "unknown_external_commit_outcome"):
        commit_req["status"] = "unknown_external_commit_outcome"
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(
            "runtime mutation adapter reported unknown_external_commit_outcome; re-run to reconcile repository state",
            1,
        )

    target_rev = resp.get("revision") if isinstance(resp.get("revision"), str) else resp.get("commit_rev")
    is_committed = (resp.get("committed") is True) or (resp.get("approved") is True and resp.get("status") == "committed")
    if not is_committed or not isinstance(target_rev, str) or not re.fullmatch(r"[0-9a-f]{40}", target_rev):
        commit_req["status"] = "unknown_external_commit_outcome" if post_head != head_sha else "invalid_mutation_adapter_response"
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(
            f"runtime mutation adapter response is missing required completion fields (committed=true and 40-hex revision; status={commit_req['status']}); "
            "refusing implicit local commit fallback",
            1,
        )

    if target_rev != post_head:
        commit_req["status"] = "invalid_mutation_adapter_response"
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(
            f"runtime mutation adapter reported revision {target_rev} which does not match HEAD ({post_head})",
            1,
        )

    verified_rev = _check_files_committed_at_revision(
        root,
        target_rev,
        expected_files,
        check_worktree_clean=True,
    )
    if verified_rev is None or verified_rev != target_rev:
        commit_req["status"] = "invalid_mutation_adapter_response"
        _write_publish_requests(req_paths, commit_req)
        raise StartPathError(
            "runtime mutation adapter claimed commit completion, but committed blobs were not found in Git at reported revision",
            1,
        )

    _verify_request_commit_binding(
        root,
        target_rev,
        expected_files,
        commit_req,
        pre_execution_revision=pre_execution_revision,
    )
    commit_req["status"] = "committed"
    commit_req["revision"] = target_rev
    _write_publish_requests(req_paths, commit_req)
    return target_rev


def _project_closed_capture(
    raw_capture: dict[str, Any],
    *,
    pre_rev: str,
    cand_sha: str,
    stdout_rel: str,
    stdout_sha: str,
    stderr_rel: str,
    stderr_sha: str,
    output_revision: str,
    cause: str | None = None,
    proof_kind: str | None = None,
) -> dict[str, Any]:
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

    return {
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
            "sha256": stdout_sha,
            "revision": output_revision,
        },
        "stderr": {
            "path": stderr_rel,
            "sha256": stderr_sha,
            "revision": output_revision,
        },
    }


def publish_captured_evidence(
    root: Path,
    *,
    capture_path: Path | None = None,
    capture_paths: list[Path] | None = None,
    cause: str | None = None,
    proof_kind: str | None = None,
    mode: str = "prepare",
    output_revision: str | None = None,
    capture_revision: str | None = None,
    stop_after_stage: str | None = None,
) -> dict[str, Any]:
    """Prepare, publish, or finalize completed capture outputs and project 12-field receipt capture(s)."""
    if mode not in ("prepare", "publish", "finalize"):
        raise StartPathError(f"unsupported publication mode: {mode!r}", 2)
    raw_paths: list[Path] = []
    if capture_paths:
        raw_paths.extend(capture_paths)
    elif capture_path is not None:
        raw_paths.append(capture_path)
    if not raw_paths:
        raise StartPathError("at least one --capture path is required", 2)

    items: list[dict[str, Any]] = []
    seen_cap_rels: set[str] = set()
    head_sha: str | None = None
    origin_url: str | None = None
    for cpath in raw_paths:
        resolved_cap_path = cpath if cpath.is_absolute() else (root / cpath).resolve()
        if not resolved_cap_path.is_file():
            raise StartPathError(f"capture record does not exist: {cpath}", 1)
        cap_rel = normalize_relative_path(resolved_cap_path.relative_to(root).as_posix(), root=root)
        if cap_rel in seen_cap_rels:
            raise StartPathError(f"duplicate --capture path in batch: {cap_rel}", 1)
        seen_cap_rels.add(cap_rel)

        _, _, cap_sha = _verify_regular_file_mode_100644(root, cap_rel)
        raw_capture = _read_json_file(resolved_cap_path)

        if raw_capture.get("completion_state") != "completed" or raw_capture.get("executed") is not True:
            raise StartPathError(
                "cannot publish incomplete or unexecuted capture for receipt consumption",
                1,
            )
        cand_sha = raw_capture.get("candidate_sha256")
        if (
            raw_capture.get("binding_state") != "candidate-bound"
            or not isinstance(cand_sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", cand_sha)
        ):
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

        _, _, stdout_sha = _verify_regular_file_mode_100644(root, stdout_rel)
        _, _, stderr_sha = _verify_regular_file_mode_100644(root, stderr_rel)
        if stdout_sha != stdout_info.get("sha256"):
            raise StartPathError("captured stdout file digest on disk does not match capture record", 1)
        if stderr_sha != stderr_info.get("sha256"):
            raise StartPathError("captured stderr file digest on disk does not match capture record", 1)

        if head_sha is None or origin_url is None:
            head_sha, origin_url, _ = _verify_git_worktree_root(root)
        pre_check = _run_git_readonly(root, ["cat-file", "-e", f"{pre_rev}^{{commit}}"], text=True)
        if pre_check.returncode != 0:
            raise StartPathError(f"capture pre-execution revision does not exist in Git: {pre_rev}", 1)

        stem_name = resolved_cap_path.name
        if stem_name.endswith(".capture.json"):
            base_stem = stem_name[: -len(".capture.json")]
        else:
            base_stem = resolved_cap_path.stem

        receipt_cap_path = resolved_cap_path.parent / f"{base_stem}.receipt-capture.json"
        receipt_cap_rel = normalize_relative_path(
            receipt_cap_path.relative_to(root).as_posix(),
            root=root,
            reject_symlinks=True,
        )
        published_path = resolved_cap_path.parent / f"{base_stem}.published.json"
        published_rel = normalize_relative_path(
            published_path.relative_to(root).as_posix(),
            root=root,
            reject_symlinks=True,
        )
        request_path = resolved_cap_path.parent / f"{base_stem}.publish-request.json"
        request_rel = normalize_relative_path(
            request_path.relative_to(root).as_posix(),
            root=root,
            reject_symlinks=True,
        )
        existing_req: dict[str, Any] | None = None
        if request_path.is_file():
            existing_req = _read_json_file(request_path)

        stage1_files = [
            {"path": stdout_rel, "sha256": stdout_sha, "mode": "100644"},
            {"path": stderr_rel, "sha256": stderr_sha, "mode": "100644"},
            {"path": cap_rel, "sha256": cap_sha, "mode": "100644"},
        ]

        _verify_git_status_and_no_staged_conflicts(
            root,
            [stdout_rel, stderr_rel, cap_rel, receipt_cap_rel],
            check_staged_conflicts=True,
        )

        already_published_doc: dict[str, Any] | None = None
        if published_path.is_file():
            existing_pub = _read_json_file(published_path)
            ex_out_rev = existing_pub.get("output_revision")
            ex_cap_ref = existing_pub.get("receipt_capture_ref")
            if (
                existing_pub.get("raw_capture_path") != cap_rel
                or not isinstance(ex_out_rev, str)
                or not isinstance(ex_cap_ref, dict)
                or not isinstance(ex_cap_ref.get("revision"), str)
            ):
                raise StartPathError(f"existing published record for {base_stem} is invalid or mismatched", 1)
            verified_s1 = _check_files_committed_at_revision(root, ex_out_rev, stage1_files, check_worktree_clean=True)
            if verified_s1 is None:
                raise StartPathError(f"existing published record for {base_stem} references uncommitted Stage 1 outputs", 1)
            expected_closed = _project_closed_capture(
                raw_capture,
                pre_rev=pre_rev,
                cand_sha=cand_sha,
                stdout_rel=stdout_rel,
                stdout_sha=stdout_sha,
                stderr_rel=stderr_rel,
                stderr_sha=stderr_sha,
                output_revision=ex_out_rev,
                cause=cause,
                proof_kind=proof_kind,
            )
            expected_closed_sha = sha256_hex(canonical_bytes(expected_closed) + b"\n")
            if ex_cap_ref.get("sha256") != expected_closed_sha or existing_pub.get("receipt_capture") != expected_closed:
                raise StartPathError(
                    f"cannot overwrite prior published evidence for {base_stem} with changed capture content",
                    1,
                )
            verified_s2 = _check_files_committed_at_revision(
                root,
                ex_cap_ref["revision"],
                [{"path": receipt_cap_rel, "sha256": expected_closed_sha, "mode": "100644"}],
                check_worktree_clean=True,
            )
            if verified_s2 is None:
                raise StartPathError(f"existing published record for {base_stem} references uncommitted receipt capture", 1)
            already_published_doc = dict(existing_pub)
            already_published_doc["published_path"] = published_rel
            already_published_doc["noop"] = True

        items.append({
            "base_stem": base_stem,
            "raw_capture": raw_capture,
            "pre_rev": pre_rev,
            "cand_sha": cand_sha,
            "cap_rel": cap_rel,
            "cap_sha": cap_sha,
            "stdout_rel": stdout_rel,
            "stdout_sha": stdout_sha,
            "stderr_rel": stderr_rel,
            "stderr_sha": stderr_sha,
            "receipt_cap_path": receipt_cap_path,
            "receipt_cap_rel": receipt_cap_rel,
            "published_path": published_path,
            "published_rel": published_rel,
            "request_path": request_path,
            "request_rel": request_rel,
            "existing_req": existing_req,
            "stage1_files": stage1_files,
            "already_published_doc": already_published_doc,
        })

    if all(it["already_published_doc"] is not None for it in items):
        pub_list = [it["already_published_doc"] for it in items]
        if len(pub_list) == 1:
            res = dict(pub_list[0])
            res["published"] = pub_list
            return res
        return {"noop": True, "published": pub_list}

    all_batch_s1_paths = {f["path"] for it in items for f in it["stage1_files"]}
    target_out_rev_check = output_revision or head_sha
    for it in items:
        if it["already_published_doc"] is not None:
            it["resolved_output_rev"] = it["already_published_doc"]["output_revision"]
            continue
        resolved_s1 = _check_files_committed_at_revision(
            root,
            target_out_rev_check,
            it["stage1_files"],
            check_worktree_clean=True,
        )
        if resolved_s1 is not None:
            s1_req = (
                it["existing_req"]
                if isinstance(it["existing_req"], dict) and it["existing_req"].get("stage") == "outputs_pending"
                else None
            )
            _verify_request_commit_binding(
                root,
                resolved_s1,
                it["stage1_files"],
                s1_req,
                allowed_stage_paths=all_batch_s1_paths,
                pre_execution_revision=it["pre_rev"],
            )
        it["resolved_output_rev"] = resolved_s1

    if mode == "prepare":
        uncommitted_s1: list[dict[str, str]] = []
        req_paths_s1: list[Path] = []
        req_rels_s1: list[str] = []
        reconciled_s1_status: str | None = None
        for it in items:
            if it["resolved_output_rev"] is None:
                ex_req = it["existing_req"]
                if isinstance(ex_req, dict) and ex_req.get("status") in ("unknown_external_commit_outcome", "in_flight_external_commit"):
                    ex_base = ex_req.get("intended_base")
                    if isinstance(ex_base, str) and re.fullmatch(r"[0-9a-f]{40}", ex_base) and head_sha != ex_base:
                        raise StartPathError(
                            f"cannot reconcile {ex_req.get('status')}: HEAD ({head_sha}) moved away from intended_base ({ex_base}) without committing Stage 1 files",
                            1,
                        )
                    reconciled_s1_status = str(ex_req["status"])
                uncommitted_s1.extend(it["stage1_files"])
                req_paths_s1.append(it["request_path"])
                req_rels_s1.append(it["request_rel"])
        if uncommitted_s1:
            first_it = items[0]
            msg = f"publish capture outputs for {first_it['raw_capture'].get('id', 'task')}:{first_it['raw_capture'].get('step', 'step')}"
            req_doc = _build_commit_request(
                root,
                origin_url,
                head_sha,
                "outputs_pending",
                msg,
                uncommitted_s1,
                pre_execution_revision=first_it["pre_rev"],
            )
            if reconciled_s1_status is not None:
                req_doc["reconciled_from_status"] = reconciled_s1_status
            _write_publish_requests(req_paths_s1, req_doc)
            return {
                "status": "pending_external_commit",
                "stage": "outputs_pending",
                "publish_request_path": req_rels_s1[0] if len(req_rels_s1) == 1 else req_rels_s1,
                "publish_request_paths": req_rels_s1,
                "commit_request": req_doc,
            }

        stage2_files: list[dict[str, str]] = []
        req_paths_s2: list[Path] = []
        req_rels_s2: list[str] = []
        receipt_cap_rels: list[str] = []
        all_batch_s2_paths = {it["receipt_cap_rel"] for it in items if it["already_published_doc"] is None}
        committed_s2_revs: list[str] = []
        reconciled_s2_status: str | None = None
        for it in items:
            if it["already_published_doc"] is not None:
                continue
            closed_cap = _project_closed_capture(
                it["raw_capture"],
                pre_rev=it["pre_rev"],
                cand_sha=it["cand_sha"],
                stdout_rel=it["stdout_rel"],
                stdout_sha=it["stdout_sha"],
                stderr_rel=it["stderr_rel"],
                stderr_sha=it["stderr_sha"],
                output_revision=it["resolved_output_rev"],
                cause=cause,
                proof_kind=proof_kind,
            )
            closed_bytes = canonical_bytes(closed_cap) + b"\n"
            closed_sha = sha256_hex(closed_bytes)
            existing_s2 = _get_committed_blob_info(root, head_sha, it["receipt_cap_rel"])
            if existing_s2 is not None and (existing_s2[0] != "100644" or existing_s2[1] != closed_sha):
                raise StartPathError(
                    f"cannot overwrite committed receipt capture {it['receipt_cap_rel']} with changed evidence",
                    1,
                )
            it["receipt_cap_path"].write_bytes(closed_bytes)
            s2_entry = {"path": it["receipt_cap_rel"], "sha256": closed_sha, "mode": "100644"}
            already_s2 = _check_files_committed_at_revision(root, head_sha, [s2_entry], check_worktree_clean=True)
            if already_s2 is not None:
                s2_req = (
                    it["existing_req"]
                    if isinstance(it["existing_req"], dict) and it["existing_req"].get("stage") == "receipt_capture_pending"
                    else None
                )
                _verify_request_commit_binding(
                    root,
                    already_s2,
                    [s2_entry],
                    s2_req,
                    allowed_stage_paths=all_batch_s2_paths,
                    pre_execution_revision=it["pre_rev"],
                )
                committed_s2_revs.append(already_s2)
                receipt_cap_rels.append(it["receipt_cap_rel"])
            else:
                ex_req = it["existing_req"]
                if (
                    isinstance(ex_req, dict)
                    and ex_req.get("stage") == "receipt_capture_pending"
                    and ex_req.get("status") in ("unknown_external_commit_outcome", "in_flight_external_commit")
                ):
                    ex_base = ex_req.get("intended_base")
                    if isinstance(ex_base, str) and re.fullmatch(r"[0-9a-f]{40}", ex_base) and head_sha != ex_base:
                        raise StartPathError(
                            f"cannot reconcile {ex_req.get('status')}: HEAD ({head_sha}) moved away from intended_base ({ex_base}) without committing Stage 2 receipt-capture",
                            1,
                        )
                    reconciled_s2_status = str(ex_req["status"])
                stage2_files.append(s2_entry)
                req_paths_s2.append(it["request_path"])
                req_rels_s2.append(it["request_rel"])
                receipt_cap_rels.append(it["receipt_cap_rel"])

        if not stage2_files and committed_s2_revs:
            return {
                "status": "ready_to_finalize",
                "stage": "finalize_pending",
                "output_revision": items[0]["resolved_output_rev"],
                "capture_revision": committed_s2_revs[0],
                "receipt_capture_path": receipt_cap_rels[0] if len(receipt_cap_rels) == 1 else receipt_cap_rels,
                "next_action": "Run 'tools/start_path.py publish --mode finalize' to write .published.json.",
            }

        first_it = items[0]
        msg2 = f"publish receipt capture {first_it['base_stem']}"
        req_doc2 = _build_commit_request(
            root,
            origin_url,
            head_sha,
            "receipt_capture_pending",
            msg2,
            stage2_files,
            pre_execution_revision=first_it["pre_rev"],
        )
        if reconciled_s2_status is not None:
            req_doc2["reconciled_from_status"] = reconciled_s2_status
        _write_publish_requests(req_paths_s2, req_doc2)
        return {
            "status": "pending_external_commit",
            "stage": "receipt_capture_pending",
            "output_revision": items[0]["resolved_output_rev"],
            "receipt_capture_path": receipt_cap_rels[0] if len(receipt_cap_rels) == 1 else receipt_cap_rels,
            "publish_request_path": req_rels_s2[0] if len(req_rels_s2) == 1 else req_rels_s2,
            "publish_request_paths": req_rels_s2,
            "commit_request": req_doc2,
        }

    if mode == "finalize":
        published_results: list[dict[str, Any]] = []
        target_cap_rev_check = capture_revision or head_sha
        all_batch_s2_paths = {it["receipt_cap_rel"] for it in items if it["already_published_doc"] is None}
        for it in items:
            if it["already_published_doc"] is not None:
                published_results.append(it["already_published_doc"])
                continue
            if it["resolved_output_rev"] is None:
                raise StartPathError(
                    f"finalize failed: Stage 1 capture outputs for {it['base_stem']} are not committed in Git",
                    1,
                )
            closed_cap = _project_closed_capture(
                it["raw_capture"],
                pre_rev=it["pre_rev"],
                cand_sha=it["cand_sha"],
                stdout_rel=it["stdout_rel"],
                stdout_sha=it["stdout_sha"],
                stderr_rel=it["stderr_rel"],
                stderr_sha=it["stderr_sha"],
                output_revision=it["resolved_output_rev"],
                cause=cause,
                proof_kind=proof_kind,
            )
            closed_bytes = canonical_bytes(closed_cap) + b"\n"
            closed_sha = sha256_hex(closed_bytes)
            if not it["receipt_cap_path"].is_file():
                raise StartPathError(
                    f"finalize failed: {it['receipt_cap_rel']} does not exist on disk",
                    1,
                )
            _, disk_rc_bytes, disk_rc_sha = _verify_regular_file_mode_100644(root, it["receipt_cap_rel"])
            if disk_rc_sha != closed_sha or disk_rc_bytes != closed_bytes:
                raise StartPathError(
                    f"finalize failed: on-disk {it['receipt_cap_rel']} does not match projected closed capture",
                    1,
                )
            s2_entry = {"path": it["receipt_cap_rel"], "sha256": closed_sha, "mode": "100644"}
            cap_rev = _check_files_committed_at_revision(
                root,
                target_cap_rev_check,
                [s2_entry],
                check_worktree_clean=True,
            )
            if cap_rev is None:
                raise StartPathError(
                    f"finalize failed: {it['receipt_cap_rel']} is not committed in Git at {target_cap_rev_check}",
                    1,
                )
            if cap_rev == it["resolved_output_rev"] or not _is_git_ancestor(root, it["resolved_output_rev"], cap_rev):
                raise StartPathError(
                    f"finalize failed: Stage 1 output_revision ({it['resolved_output_rev']}) must be a strict ancestor of Stage 2 capture_revision ({cap_rev})",
                    1,
                )
            s2_req = (
                it["existing_req"]
                if isinstance(it["existing_req"], dict) and it["existing_req"].get("stage") == "receipt_capture_pending"
                else None
            )
            _verify_request_commit_binding(
                root,
                cap_rev,
                [s2_entry],
                s2_req,
                allowed_stage_paths=all_batch_s2_paths,
                pre_execution_revision=it["pre_rev"],
            )
            receipt_capture_ref = {
                "path": it["receipt_cap_rel"],
                "sha256": closed_sha,
                "revision": cap_rev,
            }
            published_doc = {
                "schema_version": 1,
                "raw_capture_path": it["cap_rel"],
                "output_revision": it["resolved_output_rev"],
                "receipt_capture_ref": receipt_capture_ref,
                "stdout_ref": closed_cap["stdout"],
                "stderr_ref": closed_cap["stderr"],
                "receipt_capture": closed_cap,
            }
            it["published_path"].write_bytes(canonical_bytes(published_doc) + b"\n")
            if it["request_path"].is_file():
                it["request_path"].unlink()
            pub_out = dict(published_doc)
            pub_out["published_path"] = it["published_rel"]
            published_results.append(pub_out)

        if len(published_results) == 1:
            res = dict(published_results[0])
            res["published"] = published_results
            return res
        return {"published": published_results}

    # mode == "publish"
    uncommitted_s1_files: list[dict[str, str]] = []
    s1_req_paths: list[Path] = []
    for it in items:
        if it["already_published_doc"] is None and it["resolved_output_rev"] is None:
            uncommitted_s1_files.extend(it["stage1_files"])
            s1_req_paths.append(it["request_path"])

    if uncommitted_s1_files:
        first_it = items[0]
        if len(items) == 1:
            s1_msg = f"publish capture outputs for {first_it['raw_capture'].get('id', 'task')}:{first_it['raw_capture'].get('step', 'step')}"
        else:
            s1_msg = f"publish capture outputs for {len(items)} checks ({first_it['raw_capture'].get('id', 'task')})"
        s1_commit_sha = _git_commit_literal_paths(
            root,
            uncommitted_s1_files,
            s1_msg,
            stage="outputs_pending",
            request_out_paths=s1_req_paths,
            pre_execution_revision=first_it["pre_rev"],
        )
        for it in items:
            if it["already_published_doc"] is None and it["resolved_output_rev"] is None:
                it["resolved_output_rev"] = s1_commit_sha

    head_after_s1, origin_url, _ = _verify_git_worktree_root(root)
    s2_files_to_commit: list[dict[str, str]] = []
    s2_req_paths: list[Path] = []
    s2_req_rels: list[str] = []
    all_batch_s2_paths = {it["receipt_cap_rel"] for it in items if it["already_published_doc"] is None}
    for it in items:
        if it["already_published_doc"] is not None:
            continue
        closed_cap = _project_closed_capture(
            it["raw_capture"],
            pre_rev=it["pre_rev"],
            cand_sha=it["cand_sha"],
            stdout_rel=it["stdout_rel"],
            stdout_sha=it["stdout_sha"],
            stderr_rel=it["stderr_rel"],
            stderr_sha=it["stderr_sha"],
            output_revision=it["resolved_output_rev"],
            cause=cause,
            proof_kind=proof_kind,
        )
        closed_bytes = canonical_bytes(closed_cap) + b"\n"
        closed_sha = sha256_hex(closed_bytes)
        existing_s2_blob = _get_committed_blob_info(root, head_after_s1, it["receipt_cap_rel"])
        if existing_s2_blob is not None and (existing_s2_blob[0] != "100644" or existing_s2_blob[1] != closed_sha):
            raise StartPathError(
                f"cannot overwrite committed receipt capture {it['receipt_cap_rel']} with changed evidence",
                1,
            )
        it["receipt_cap_path"].write_bytes(closed_bytes)
        it["closed_capture"] = closed_cap
        it["closed_sha"] = closed_sha
        s2_entry = {"path": it["receipt_cap_rel"], "sha256": closed_sha, "mode": "100644"}
        it["s2_entry"] = s2_entry
        already_s2_rev = _check_files_committed_at_revision(
            root,
            head_after_s1,
            [s2_entry],
            check_worktree_clean=True,
        )
        if already_s2_rev is not None:
            s2_req = (
                it["existing_req"]
                if isinstance(it["existing_req"], dict) and it["existing_req"].get("stage") == "receipt_capture_pending"
                else None
            )
            _verify_request_commit_binding(
                root,
                already_s2_rev,
                [s2_entry],
                s2_req,
                allowed_stage_paths=all_batch_s2_paths,
                pre_execution_revision=it["pre_rev"],
            )
        it["resolved_capture_rev"] = already_s2_rev
        if already_s2_rev is None:
            s2_files_to_commit.append(s2_entry)
            s2_req_paths.append(it["request_path"])
            s2_req_rels.append(it["request_rel"])

    if stop_after_stage == "outputs":
        first_it = items[0]
        s2_msg = f"publish receipt capture {first_it['base_stem']}"
        req_doc = _build_commit_request(
            root,
            origin_url,
            head_after_s1,
            "receipt_capture_pending",
            s2_msg,
            s2_files_to_commit,
            pre_execution_revision=first_it["pre_rev"],
        )
        _write_publish_requests(s2_req_paths, req_doc)
        return {
            "status": "stopped_after_outputs",
            "stage": "receipt_capture_pending",
            "output_revision": items[0]["resolved_output_rev"],
            "receipt_capture_path": items[0]["receipt_cap_rel"] if len(items) == 1 else [i["receipt_cap_rel"] for i in items],
            "publish_request_path": s2_req_rels[0] if len(s2_req_rels) == 1 else s2_req_rels,
            "commit_request": req_doc,
        }

    if s2_files_to_commit:
        first_it = items[0]
        if len(items) == 1:
            s2_msg = f"publish receipt capture {first_it['base_stem']}"
        else:
            s2_msg = f"publish receipt captures for {len(items)} checks ({first_it['raw_capture'].get('id', 'task')})"
        s2_commit_sha = _git_commit_literal_paths(
            root,
            s2_files_to_commit,
            s2_msg,
            stage="receipt_capture_pending",
            request_out_paths=s2_req_paths,
            pre_execution_revision=first_it["pre_rev"],
        )
        for it in items:
            if it["already_published_doc"] is None and it["resolved_capture_rev"] is None:
                it["resolved_capture_rev"] = s2_commit_sha

    published_results = []
    for it in items:
        if it["already_published_doc"] is not None:
            published_results.append(it["already_published_doc"])
            continue
        receipt_capture_ref = {
            "path": it["receipt_cap_rel"],
            "sha256": it["closed_sha"],
            "revision": it["resolved_capture_rev"],
        }
        published_doc = {
            "schema_version": 1,
            "raw_capture_path": it["cap_rel"],
            "output_revision": it["resolved_output_rev"],
            "receipt_capture_ref": receipt_capture_ref,
            "stdout_ref": it["closed_capture"]["stdout"],
            "stderr_ref": it["closed_capture"]["stderr"],
            "receipt_capture": it["closed_capture"],
        }
        it["published_path"].write_bytes(canonical_bytes(published_doc) + b"\n")
        if it["request_path"].is_file():
            it["request_path"].unlink()
        pub_out = dict(published_doc)
        pub_out["published_path"] = it["published_rel"]
        published_results.append(pub_out)

    if len(published_results) == 1:
        res = dict(published_results[0])
        res["published"] = published_results
        return res
    return {"published": published_results}


def build_stage_receipt(
    root: Path,
    *,
    policy_path: Path,
    published_paths: list[Path],
    output_path: Path,
    update_policy: bool = False,
    commit_changes: bool = False,
) -> dict[str, Any]:
    """Bind one or more published captures into a stage receipt and validate with verify_stage_receipt.

    Strictly noncommitting unless commit_changes is True; raw closed-capture inputs must already be
    committed in Git and are verified read-only without staging or committing.
    """
    try:
        import workflow_assurance as wa
    except ModuleNotFoundError:
        from tools import workflow_assurance as wa

    head_sha, origin_url, _ = _verify_git_worktree_root(root)
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
    for cmd, pub_path in zip(commands, published_paths):
        resolved_pub = pub_path if pub_path.is_absolute() else (root / pub_path).resolve()
        pub_doc = _read_json_file(resolved_pub)
        if "receipt_capture_ref" in pub_doc and "receipt_capture" in pub_doc:
            cap_ref = pub_doc["receipt_capture_ref"]
            closed_cap = pub_doc["receipt_capture"]
            if (
                not isinstance(cap_ref, dict)
                or not isinstance(cap_ref.get("path"), str)
                or not isinstance(cap_ref.get("sha256"), str)
                or not isinstance(cap_ref.get("revision"), str)
            ):
                raise StartPathError(f"invalid receipt_capture_ref in {pub_path}", 1)
            verified_cap_rev = _check_files_committed_at_revision(
                root,
                cap_ref["revision"],
                [{"path": normalize_relative_path(cap_ref["path"], root=root), "sha256": cap_ref["sha256"], "mode": "100644"}],
                check_worktree_clean=False,
            )
            if verified_cap_rev is None:
                raise StartPathError(
                    f"published receipt_capture_ref is not committed in Git at {cap_ref['revision']}: {cap_ref['path']}",
                    1,
                )
        else:
            if not resolved_pub.is_relative_to(root):
                raise StartPathError(f"raw closed capture path must be inside repository root: {pub_path}", 1)
            rel_cap = normalize_relative_path(resolved_pub.relative_to(root).as_posix(), root=root)
            _, _, cap_sha = _verify_regular_file_mode_100644(root, rel_cap)
            committed_rev = _check_files_committed_at_revision(
                root,
                head_sha,
                [{"path": rel_cap, "sha256": cap_sha, "mode": "100644"}],
                check_worktree_clean=True,
            )
            if committed_rev is None:
                raise StartPathError(
                    f"raw closed capture is not committed in Git: {rel_cap} (publish or commit the capture before running build-receipt)",
                    1,
                )
            cap_ref = {
                "path": rel_cap,
                "sha256": cap_sha,
                "revision": committed_rev,
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
    out_sha = sha256_hex(out_bytes)

    to_commit_files: list[dict[str, str]] = [
        {"path": out_rel, "sha256": out_sha, "mode": "100644"},
    ]
    if update_policy and resolved_policy_path.is_relative_to(root):
        pol_rel = normalize_relative_path(resolved_policy_path.relative_to(root).as_posix(), root=root)
        _, _, pol_sha = _verify_regular_file_mode_100644(root, pol_rel)
        to_commit_files.append({"path": pol_rel, "sha256": pol_sha, "mode": "100644"})

    commit_msg = f"publish stage receipt {policy['operation_id']}"
    commit_req = _build_commit_request(
        root,
        origin_url,
        head_sha,
        "stage_receipt_pending",
        commit_msg,
        to_commit_files,
    )

    receipt_ref: dict[str, Any] = {
        "path": out_rel,
        "sha256": out_sha,
        "revision": None,
    }
    if commit_changes:
        req_out_path = resolved_out.parent / f"{resolved_out.stem}.publish-request.json"
        commit_sha = _git_commit_literal_paths(
            root,
            to_commit_files,
            commit_msg,
            stage="stage_receipt_pending",
            request_out_paths=[req_out_path],
        )
        receipt_ref["revision"] = commit_sha
        commit_req["status"] = "committed"
        commit_req["revision"] = commit_sha

    return {
        "verified": True,
        "receipt_path": out_rel,
        "receipt_ref": receipt_ref,
        "commit_request": commit_req,
        "receipt": verified,
    }


def _discover_cross_surface_status(root: Path) -> tuple[list[str], list[str], bool, list[dict[str, Any]], list[str]]:
    """Discover all feature lists, phase YAMLs, and manifest.json and detect cross-surface status contradictions."""
    import yaml

    fl_paths = sorted(
        p.relative_to(root).as_posix()
        for p in (root / ".agent").glob("feature_list*.json")
        if p.is_file()
    ) if (root / ".agent").is_dir() else []

    yaml_paths = sorted(
        p.relative_to(root).as_posix()
        for p in (root / "docs" / "planning").glob("phase_*.yaml")
        if p.is_file()
    ) if (root / "docs" / "planning").is_dir() else []

    manifest_path = root / "docs" / "planning" / "manifest.json"
    manifest_present = manifest_path.is_file()
    manifest_phases: dict[str, dict[str, Any]] = {}
    if manifest_present:
        try:
            m_doc = json.loads(manifest_path.read_text(encoding="utf-8"))
            for entry in m_doc.get("phases", []):
                if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                    manifest_phases[entry["id"]] = entry
        except (OSError, json.JSONDecodeError):
            pass

    yaml_by_phase: dict[str, tuple[str, dict[str, Any]]] = {}
    yaml_steps: dict[str, tuple[str, str]] = {}
    for yrel in yaml_paths:
        try:
            ydoc = yaml.safe_load((root / yrel).read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(ydoc, dict):
            continue
        pid = ydoc.get("id") or ydoc.get("phase_id") or ydoc.get("phase")
        if isinstance(pid, str):
            yaml_by_phase[pid] = (yrel, ydoc)
        for step in ydoc.get("steps", []):
            if isinstance(step, dict) and step.get("id") is not None:
                sid = str(step["id"])
                sstatus = str(step.get("status", "")).upper()
                yaml_steps[sid] = (yrel, sstatus)

    contradictions: list[str] = []
    phase_summary: list[dict[str, Any]] = []
    seen_phases: set[str] = set()

    def _norm_phase_status(val: Any) -> str | None:
        if not isinstance(val, str) or not val.strip():
            return None
        low = val.strip().lower()
        return "complete" if low == "completed" else low

    for fl_rel in fl_paths:
        try:
            fl_doc = json.loads((root / fl_rel).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            contradictions.append(f"{fl_rel}: invalid JSON: {exc}")
            continue
        if not isinstance(fl_doc, dict):
            continue
        pid = str(fl_doc.get("phase", ""))
        seen_phases.add(pid)
        fl_pstatus = _norm_phase_status(fl_doc.get("phase_status"))
        m_entry = manifest_phases.get(pid)
        m_status = _norm_phase_status(m_entry.get("status")) if m_entry else None
        y_entry = yaml_by_phase.get(pid)
        y_status = _norm_phase_status(y_entry[1].get("status")) if y_entry else None

        if m_entry is not None:
            m_fl = m_entry.get("feature_list")
            if isinstance(m_fl, str) and m_fl != fl_rel:
                contradictions.append(
                    f"phase {pid}: manifest feature_list ({m_fl}) != discovered ({fl_rel})"
                )
        if fl_pstatus and m_status and fl_pstatus != m_status:
            contradictions.append(
                f"phase {pid}: {fl_rel} phase_status={fl_pstatus!r} contradicts manifest status={m_status!r}"
            )
        if fl_pstatus and y_status and fl_pstatus != y_status:
            contradictions.append(
                f"phase {pid}: {fl_rel} phase_status={fl_pstatus!r} contradicts {y_entry[0]} status={y_status!r}"
            )
        if m_status and y_status and m_status != y_status:
            contradictions.append(
                f"phase {pid}: manifest status={m_status!r} contradicts {y_entry[0]} status={y_status!r}"
            )

        features = [f for f in fl_doc.get("features", []) if isinstance(f, dict)]
        completed_count = 0
        pending_count = 0
        for feat in features:
            fid = str(feat.get("id", ""))
            fstatus = str(feat.get("status", ""))
            if fstatus == "complete":
                completed_count += 1
            elif fstatus in ("pending", "in_progress", "blocked"):
                pending_count += 1

            if "passes" in feat:
                if fstatus == "complete" and feat.get("passes") is not True:
                    contradictions.append(
                        f"{fl_rel}: feature {fid} has status='complete' but passes={feat.get('passes')!r}"
                    )
                if fstatus != "complete" and feat.get("passes") is True:
                    contradictions.append(
                        f"{fl_rel}: feature {fid} has status={fstatus!r} but passes=True"
                    )
                if fstatus == "complete":
                    cpath = root / ".agent" / "contracts" / f"{fid}.json"
                    qpath = root / ".agent" / "qa" / f"{fid}.json"
                    if not cpath.is_file():
                        contradictions.append(
                            f"{fl_rel}: contemporary complete feature {fid} is missing contract .agent/contracts/{fid}.json"
                        )
                    if not qpath.is_file():
                        contradictions.append(
                            f"{fl_rel}: contemporary complete feature {fid} is missing QA verdict .agent/qa/{fid}.json"
                        )

            if fid in yaml_steps:
                yrel, sstatus = yaml_steps[fid]
                if sstatus in ("COMPLETED", "COMPLETE") and fstatus != "complete":
                    contradictions.append(
                        f"feature {fid}: {yrel} step status={sstatus!r} contradicts {fl_rel} status={fstatus!r}"
                    )
                elif fstatus == "complete" and sstatus not in ("COMPLETED", "COMPLETE"):
                    contradictions.append(
                        f"feature {fid}: {fl_rel} status='complete' contradicts {yrel} step status={sstatus!r}"
                    )

        effective_phase_status = m_status or fl_pstatus or y_status
        if effective_phase_status == "complete":
            non_terminal = [
                str(f.get("id"))
                for f in features
                if f.get("status") not in ("complete", "cancelled")
            ]
            if non_terminal:
                contradictions.append(
                    f"phase {pid}: marked complete but {fl_rel} has non-terminal features: {', '.join(non_terminal)}"
                )

        phase_summary.append({
            "phase": pid,
            "feature_list": fl_rel,
            "manifest_status": m_status,
            "feature_list_status": fl_pstatus,
            "yaml_status": y_status,
            "total_features": len(features),
            "completed_features": completed_count,
            "pending_features": pending_count,
        })

    for pid, m_entry in manifest_phases.items():
        if pid not in seen_phases:
            fl_ref = m_entry.get("feature_list")
            contradictions.append(
                f"phase {pid}: listed in manifest.json ({fl_ref}) but feature list file is missing"
            )

    return fl_paths, yaml_paths, manifest_present, phase_summary, contradictions


def generate_status_view(root: Path) -> dict[str, Any]:
    """Derive a concise read-only status/readiness view from authoritative live records."""
    head_res = _run_git_readonly(root, ["rev-parse", "HEAD"], text=True)
    head_sha = head_res.stdout.strip() if head_res.returncode == 0 else None
    origin_res = _run_git_readonly(root, ["remote", "get-url", "origin"], text=True)
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

    fl_paths, yaml_paths, manifest_present, phase_summary, contradictions = _discover_cross_surface_status(root)

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
        "discovered_feature_lists": fl_paths,
        "discovered_phase_yamls": yaml_paths,
        "manifest_present": manifest_present,
        "phase_summary": phase_summary,
        "contradictions": contradictions,
        "reconciled": len(contradictions) == 0,
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
        f"- **Cross-Surface Reconciled**: `{view.get('reconciled')}` (`{len(view.get('discovered_feature_lists', []))}` feature lists, `{len(view.get('discovered_phase_yamls', []))}` phase YAMLs, `{len(view.get('contradictions', []))}` contradictions)",
    ]
    inst = view.get("installed_governance")
    if isinstance(inst, dict):
        lines.append(
            f"- **Installed Governance**: `{inst.get('tag')}` (`{inst.get('resolved_sha')}`)"
        )
    if view.get("contradictions"):
        lines.append("")
        lines.append("## Cross-Surface Contradictions")
        for item in view["contradictions"]:
            lines.append(f"- {item}")
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

    root = root.resolve(strict=True)
    supplied = state_path or (root / ".agent" / "run_state.json")
    if not supplied.is_absolute():
        supplied = root / supplied

    def target_path() -> Path:
        try:
            relative = supplied.relative_to(root).as_posix()
        except ValueError as exc:
            raise StartPathError("receipt state must be inside the target repository", 1) from exc
        target = resolve_project_file(root, relative)
        if not target.is_file() or not stat.S_ISREG(target.lstat().st_mode):
            raise StartPathError(f"state file is not a regular file: {target}", 1)
        return target

    target_state_path = target_path()  # Reject aliases before resolving identity.

    def plan_current(policy_data, receipt_data) -> dict[str, Any]:
        state_data = _read_json_file(target_path())
        try:
            return wa.plan_receipt_transition(root, state_data, receipt_data, policy=policy_data)
        except wa.AssuranceError as exc:
            raise StartPathError(str(exc), 1) from exc

    applied = False
    if apply_changes:
        with _receipt_state_lock(root, target_state_path) as journal:
            policy_data = _read_json_file(policy_path)
            receipt_data = _read_json_file(receipt_path) if receipt_path is not None else None
            binding = {"policy_sha256": sha256_hex(canonical_bytes(policy_data)),
                "receipt_sha256": sha256_hex(canonical_bytes(receipt_data))}
            _recover_receipt_publication(target_path(), journal, binding)
            planned = plan_current(policy_data, receipt_data)
            if planned["action"] == "advance":
                try:
                    _publish_receipt_state(target_path(), planned["state"], journal, binding)
                except OSError as exc:
                    raise StartPathError(
                        "receipt state publication failed; inspect current state and replay the same verified receipt: " + str(exc), 1,
                    ) from exc
                applied = True
    else:
        planned = plan_current(_read_json_file(policy_path),
            _read_json_file(receipt_path) if receipt_path is not None else None)
    return {
        "action": planned["action"],
        "reason": planned["reason"],
        "applied": applied,
        "status": planned["state"].get("status"),
        "updated_at": planned["state"].get("updated_at"),
    }


@contextmanager
def _receipt_state_lock(root: Path, state_path: Path):
    """Serialize read/plan/publish on one stable lock, independent of replaced inode."""
    import fcntl
    key = sha256_hex(os.fsencode(str(state_path)))
    observed = _run_git_readonly(root, ["rev-parse", "--absolute-git-dir"], text=True)
    if observed.returncode != 0 or not observed.stdout.strip():
        raise StartPathError("receipt state lock requires Git administrative metadata", 1)
    administration = Path(observed.stdout.strip())
    if not administration.is_absolute() or not administration.is_dir():
        raise StartPathError("receipt state Git administrative directory is invalid", 1)
    lock_directory = administration / "nizam-receipt-state-locks"
    if lock_directory.is_symlink():
        raise StartPathError("receipt state lock directory is a symlink", 1)
    lock_directory.mkdir(mode=0o700, exist_ok=True)
    lock_path = lock_directory / (key + ".lock")
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(lock_path, flags, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise StartPathError("receipt state lock is not a regular file", 1)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield lock_path.with_suffix(".publication.json")
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _sync_receipt_directory(directory: Path) -> None:
    fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _recover_receipt_publication(target: Path, journal: Path, binding: dict[str, str]) -> None:
    """Clean only a complete proven intent; journal bytes never publish state."""
    if not os.path.lexists(journal):
        return
    try:
        if journal.is_symlink() or not stat.S_ISREG(journal.lstat().st_mode):
            raise ValueError("unsafe intent record")
        intent = _read_json_file(journal)
        fields = {"schema_version", "target", "temporary", "base_sha256", "new_sha256", "byte_length", "mode", *binding}
        if set(intent) != fields or intent["schema_version"] != 1 or intent["target"] != str(target):
            raise ValueError("intent target/shape mismatch")
        if any(intent[k] != value for k, value in binding.items()):
            raise ValueError("intent policy/receipt differs; replay the original verified receipt")
        temporary = Path(intent["temporary"])
        if temporary.parent != target.parent or not re.fullmatch(r"\.nizam-resume-[0-9a-f]{32}\.json", temporary.name):
            raise ValueError("intent temporary identity mismatch")
        if (any(not isinstance(intent[k], str) or not re.fullmatch(r"[0-9a-f]{64}", intent[k]) for k in ("base_sha256", "new_sha256"))
                or type(intent["byte_length"]) is not int or intent["byte_length"] < 0
                or type(intent["mode"]) is not int or not 0 <= intent["mode"] <= 0o7777):
            raise ValueError("intent content identity invalid")
        current = sha256_hex(target.read_bytes())
        if stat.S_IMODE(target.stat().st_mode) != intent["mode"]:
            raise ValueError("current state mode changed")
        if os.path.lexists(temporary):
            if (current != intent["base_sha256"] or temporary.is_symlink()
                    or not stat.S_ISREG(temporary.lstat().st_mode)
                    or stat.S_IMODE(temporary.stat().st_mode) != intent["mode"]):
                raise ValueError("unknown temporary/state identity or mode")
            raw = temporary.read_bytes()
            if len(raw) != intent["byte_length"] or sha256_hex(raw) != intent["new_sha256"]:
                raise ValueError("unknown or partial temporary bytes preserved")
            temporary.unlink()
            _sync_receipt_directory(target.parent)
        elif current not in (intent["base_sha256"], intent["new_sha256"]):
            raise ValueError("unknown current state preserved")
        elif current == intent["new_sha256"]:
            # A successful rename may precede a failed directory fsync. Replay
            # must establish that durability before clearing intent or noop.
            _sync_receipt_directory(target.parent)
        journal.unlink()
        _sync_receipt_directory(journal.parent)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise StartPathError("receipt publication recovery held; preserve evidence and reconcile the original receipt: " + str(exc), 1) from exc


def _publish_receipt_state(target: Path, state: dict[str, Any], journal: Path, binding: dict[str, str]) -> None:
    """Publish a complete owned state and acknowledge only after directory fsync."""
    mode = stat.S_IMODE(target.lstat().st_mode)
    raw = (json.dumps(state, indent=2) + "\n").encode("utf-8")
    temporary = target.parent / (".nizam-resume-" + secrets.token_hex(16) + ".json")
    intent = dict(schema_version=1, target=str(target), temporary=str(temporary),
        base_sha256=sha256_hex(target.read_bytes()), new_sha256=sha256_hex(raw),
        byte_length=len(raw), mode=mode, **binding)
    # Publish complete coordination metadata before the worktree temp exists.
    fd, name = tempfile.mkstemp(prefix=".publication-", dir=journal.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical_bytes(intent) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, journal)
        _sync_receipt_directory(journal.parent)
    finally:
        Path(name).unlink(missing_ok=True)
    fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "wb") as stream:
        os.fchmod(stream.fileno(), mode)
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, target)
    _sync_receipt_directory(target.parent)
    journal.unlink()
    _sync_receipt_directory(journal.parent)


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
    _receipt_replay_context: bytes | None = None,
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
    if candidate is not None:
        wa = _load_workflow_assurance()
        try:
            if feature_id is None or not isinstance(files, dict):
                raise wa.AssuranceError("candidate eligibility requires exact task intent and identity")
            paths = wa.qa_authorization_paths(root, feature_id, candidate)
            if f".agent/evidence/{feature_id}-base.json" not in paths:
                raise wa.AssuranceError("route candidate requires immutable task base; begin/capture afresh")
            checks = wa.qa_bound_checks(root, feature_id, candidate)
            wa.validate_qa_context(root, feature_id, candidate, checks)
            intent_path = next(p for p in paths if p.endswith(("-scope.json", "-intent.json")))
            if wa.canonical(wa.parse_json(wa.regular_file(root, intent_path).read_bytes())) != wa.canonical(files):
                raise wa.AssuranceError("candidate scope differs from consumed task intent")
            verify_actual_changed_scope(root, route, scoped, feature_id, contract_id=contract_id,
                _receipt_replay_context=_receipt_replay_context, _receipt_candidate_identity=candidate)
        except wa.AssuranceError as exc:
            raise StartPathError("candidate route eligibility failed: " + str(exc), 1) from exc
    return scoped


def _parse_porcelain_z(data: bytes) -> list[dict[str, Any]]:
    """Parse `git status --porcelain=v1 -z` including both endpoints of renames/copies."""
    entries = data.split(b"\x00")
    parsed: list[dict[str, Any]] = []
    idx = 0
    while idx < len(entries):
        entry = entries[idx]
        idx += 1
        if not entry or len(entry) < 4:
            continue
        code = entry[:2].decode("ascii", errors="replace")
        paths = [entry[3:].decode("utf-8", errors="surrogateescape")]
        if "R" in code or "C" in code:
            if idx < len(entries) and entries[idx]:
                paths.append(entries[idx].decode("utf-8", errors="surrogateescape"))
                idx += 1
        parsed.append({"code": code, "paths": paths})
    return parsed


def _parse_name_status_z(data: bytes) -> list[dict[str, Any]]:
    """Parse `git diff --name-status -z` including both endpoints of renames/copies."""
    parts = data.split(b"\x00")
    parsed: list[dict[str, Any]] = []
    idx = 0
    while idx < len(parts):
        status = parts[idx].decode("ascii", errors="replace")
        idx += 1
        if not status:
            continue
        if status[0] in ("R", "C"):
            if idx + 1 >= len(parts):
                raise StartPathError("malformed git diff --name-status -z rename record", 1)
            paths = [
                parts[idx].decode("utf-8", errors="surrogateescape"),
                parts[idx + 1].decode("utf-8", errors="surrogateescape"),
            ]
            idx += 2
        else:
            if idx >= len(parts):
                raise StartPathError("malformed git diff --name-status -z record", 1)
            paths = [parts[idx].decode("utf-8", errors="surrogateescape")]
            idx += 1
        parsed.append({"status": status, "paths": paths})
    return parsed


def _task_owned_governance_path(norm: str, path_id: str) -> bool:
    """Allow only the current task's own evidence/QA outputs, never shared authority records."""
    if norm == f".agent/evidence/{path_id}-base.json":
        return True
    if norm.startswith(f".agent/evidence/{path_id}-"):
        return True
    if norm.startswith(f".agent/evidence/{path_id}/"):
        return True
    if norm == f".agent/qa/{path_id}.json":
        return True
    return False


def _observe_inherited_endpoint(root: Path, raw_path: str) -> dict[str, Any]:
    """Observe index and worktree independently, never traversing a symlink."""
    path = normalize_relative_path(raw_path, forbid_nizam_payload=False)
    if path != raw_path:
        raise StartPathError("noncanonical inherited endpoint: " + raw_path, 1)
    index_result = _run_git_readonly(
        root, ["--literal-pathspecs", "ls-files", "--stage", "-z", "--", path], text=False
    )
    if index_result.returncode:
        raise StartPathError("cannot observe inherited index: " + path, 1)
    index = []
    for row in index_result.stdout.split(b"\0"):
        if not row:
            continue
        try:
            metadata, name = row.split(b"\t", 1)
            mode, oid, stage = metadata.decode("ascii").split()
            if name.decode("utf-8", errors="surrogateescape") != path:
                raise ValueError("directory or ambiguous index endpoint")
            if not re.fullmatch(r"[0-7]{6}", mode) or not re.fullmatch(r"[0-9a-f]{40,64}", oid) or stage not in ("0", "1", "2", "3"):
                raise ValueError("malformed index observation")
            index.append({"mode": mode, "object": oid, "stage": int(stage)})
        except (ValueError, UnicodeError) as exc:
            raise StartPathError("cannot observe inherited index endpoint: " + path, 1) from exc
    index.sort(key=lambda item: item["stage"])
    directory = None
    observed_presence = False
    try:
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        parts = path.split("/")
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        name = parts[-1]
        before = os.stat(name, dir_fd=directory, follow_symlinks=False)
        observed_presence = True
        if stat.S_ISLNK(before.st_mode):
            worktree = {"kind": "symlink", "target": os.readlink(name, dir_fd=directory)}
        elif stat.S_ISREG(before.st_mode):
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            with os.fdopen(fd, "rb") as fh:
                opened = os.fstat(fh.fileno())
                if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                    raise StartPathError("inherited endpoint changed during observation: " + path, 1)
                digest = hashlib.sha256()
                while chunk := fh.read(1024 * 1024):
                    digest.update(chunk)
                after = os.fstat(fh.fileno())
            signature = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_mode)
            if signature(opened) != signature(after):
                raise StartPathError("inherited endpoint changed during observation: " + path, 1)
            worktree = {"kind": "file", "sha256": digest.hexdigest(), "executable": bool(after.st_mode & 0o111)}
        else:
            raise StartPathError("unsupported inherited endpoint kind: " + path, 1)
        final = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if (before.st_dev, before.st_ino, before.st_mode, before.st_mtime_ns, before.st_ctime_ns) != (final.st_dev, final.st_ino, final.st_mode, final.st_mtime_ns, final.st_ctime_ns):
            raise StartPathError("inherited endpoint changed during observation: " + path, 1)
    except FileNotFoundError as exc:
        if observed_presence:
            raise StartPathError("inherited endpoint disappeared during observation: " + path, 1) from exc
        worktree = {"kind": "absent"}
    except OSError as exc:
        raise StartPathError("cannot safely observe inherited endpoint: " + path, 1) from exc
    finally:
        if directory is not None:
            os.close(directory)
    return {"index": index, "worktree": worktree}


def _task_authorization(root: Path, route: str, files: list[str], contract_id: str | None) -> dict[str, Any]:
    scoped = verify_route_scope_eligibility(root, route, files, contract_id=contract_id)
    if contract_id is not None:
        require_inside_contract(root, contract_id, scoped)
    return {"route": route, "files": sorted(scoped), "contract_id": contract_id}


def _record_task_base(
    root: Path, path_id: str, *, route: str, files: list[str], contract_id: str | None = None,
) -> None:
    """Exclusively record authorization and no-follow index/worktree observations."""
    marker = root / ".agent" / "evidence" / f"{path_id}-base.json"
    authorization = _task_authorization(root, route, files, contract_id)
    wa = _load_workflow_assurance()
    intent_path = root / ".agent" / "evidence" / f"{path_id}-{'scope' if route == 'bugfix' else 'intent'}.json"
    try:
        verification = wa.qa_required_checks(_read_json_file(intent_path).get("verification"))
    except wa.AssuranceError as exc:
        raise StartPathError(str(exc), 1) from exc
    if os.path.lexists(marker):
        existing = _load_task_base(root, path_id)
        if existing and existing.get("schema_version") == 2 and (existing["authorization"] != authorization or existing.get("verification") != verification):
            raise StartPathError("task authorization changed; begin with a fresh task ID", 1)
        return
    git_check = _run_git_readonly(root, ["rev-parse", "--is-inside-work-tree"], text=True)
    if git_check.returncode != 0 or git_check.stdout.strip() != "true":
        if os.path.lexists(root / ".git"):
            raise StartPathError("cannot record task base: Git repository inspection failed", 1)
        return
    top_res = _run_git_readonly(root, ["rev-parse", "--show-toplevel"], text=True)
    if top_res.returncode != 0 or Path(top_res.stdout.strip()).resolve() != root.resolve():
        raise StartPathError("cannot record task base: root is not the exact Git worktree toplevel", 1)
    head_res = _run_git_readonly(root, ["rev-parse", "--verify", "HEAD^{commit}"], text=True)
    if head_res.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", head_res.stdout.strip()):
        raise StartPathError("cannot record task base: HEAD is not a resolvable commit", 1)
    status_res = _run_git_readonly(root, ["status", "--porcelain", "-z", "--untracked-files=all"], text=False)
    if status_res.returncode != 0:
        raise StartPathError("cannot record task base: git status failed", 1)
    baseline_entries = _parse_porcelain_z(status_res.stdout)
    endpoints = sorted({p for entry in baseline_entries for p in entry["paths"]})
    doc = {"schema_version": 2, "id": path_id, "base_revision": head_res.stdout.strip(),
           "recorded_at": utc_now_iso(), "pre_existing_entries": baseline_entries,
           "authorization": authorization, "verification": verification,
           "inherited_observations": {p: _observe_inherited_endpoint(root, p) for p in endpoints}}
    marker.parent.mkdir(parents=True, exist_ok=True)
    with marker.open("xb") as fh:
        fh.write(canonical_bytes(doc) + b"\n")


def _load_task_base(root: Path, path_id: str) -> dict[str, Any] | None:
    marker = root / ".agent" / "evidence" / f"{path_id}-base.json"
    if not os.path.lexists(marker):
        return None
    if marker.is_symlink() or not marker.is_file():
        raise StartPathError("recorded task base is not a regular file", 1)
    try:
        doc = json.loads(marker.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or doc.get("id") != path_id or type(doc.get("schema_version")) is not int or doc["schema_version"] not in (1, 2) or not re.fullmatch(r"[0-9a-f]{40}", str(doc.get("base_revision"))):
            raise ValueError("invalid base identity")
        entries = doc.get("pre_existing_entries")
        if not isinstance(entries, list) or any(not isinstance(e, dict) or not isinstance(e.get("code"), str) or not isinstance(e.get("paths"), list) or not e["paths"] or any(not isinstance(p, str) for p in e["paths"]) for e in entries):
            raise ValueError("invalid inherited entries")
        if doc["schema_version"] == 2:
            auth = doc.get("authorization")
            if not isinstance(auth, dict) or set(auth) != {"route", "files", "contract_id"} or auth["route"] not in ("bugfix", "trivial", "small-change") or not isinstance(auth["files"], list) or not auth["files"] or any(not isinstance(p, str) for p in auth["files"]) or auth["files"] != sorted(set(auth["files"])) or (auth["contract_id"] is not None and (not isinstance(auth["contract_id"], str) or not ID_PATTERN.fullmatch(auth["contract_id"]))):
                raise ValueError("invalid authorization binding")
            observations = doc.get("inherited_observations")
            endpoints = {p for e in entries for p in e["paths"]}
            if not isinstance(observations, dict) or set(observations) != endpoints:
                raise ValueError("incomplete inherited observations")
            for path, observed in observations.items():
                if normalize_relative_path(path, forbid_nizam_payload=False) != path or not isinstance(observed, dict) or set(observed) != {"index", "worktree"} or not isinstance(observed["index"], list):
                    raise ValueError("invalid endpoint observation")
                for item in observed["index"]:
                    if not isinstance(item, dict) or set(item) != {"mode", "object", "stage"} or not re.fullmatch(r"[0-7]{6}", str(item["mode"])) or not re.fullmatch(r"[0-9a-f]{40,64}", str(item["object"])) or type(item["stage"]) is not int or item["stage"] not in (0, 1, 2, 3):
                        raise ValueError("invalid index observation")
                wt = observed["worktree"]
                if not isinstance(wt, dict) or wt.get("kind") not in ("absent", "file", "symlink"):
                    raise ValueError("invalid worktree observation")
                keys = {"absent": {"kind"}, "file": {"kind", "sha256", "executable"}, "symlink": {"kind", "target"}}[wt["kind"]]
                if set(wt) != keys or (wt["kind"] == "file" and (not re.fullmatch(r"[0-9a-f]{64}", str(wt["sha256"])) or type(wt["executable"]) is not bool)) or (wt["kind"] == "symlink" and not isinstance(wt["target"], str)):
                    raise ValueError("invalid worktree identity")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise StartPathError(f"recorded task base is malformed or unreadable: {marker}; begin with a fresh task ID", 1) from exc
    return doc


def verify_actual_changed_scope(
    root: Path,
    route: str,
    declared_files: list[str],
    path_id: str | None = None,
    *,
    contract_id: str | None = None,
    _receipt_replay_context: bytes | None = None,
    _receipt_candidate_identity: dict[str, Any] | None = None,
) -> None:
    """Bind completion to the complete committed/staged/unstaged/untracked delta.

    A Git-backed project fails closed on any inspection failure. A genuinely
    non-Git project keeps the historical local-only behavior (no Git state to
    bind); that mode is not a claim of Git-backed completion.
    """
    authorization = _task_authorization(root, route, declared_files, contract_id)
    scoped = authorization["files"]
    git_check = _run_git_readonly(root, ["rev-parse", "--is-inside-work-tree"], text=True)
    if git_check.returncode != 0 or git_check.stdout.strip() != "true":
        if os.path.lexists(root / ".git"):
            raise StartPathError(f"{route} completion failed: Git repository inspection failed", 1)
        return

    top_res = _run_git_readonly(root, ["rev-parse", "--show-toplevel"], text=True)
    if top_res.returncode != 0 or not top_res.stdout.strip():
        raise StartPathError(f"{route} completion failed: Git toplevel could not be resolved", 1)
    if Path(top_res.stdout.strip()).resolve() != root.resolve():
        raise StartPathError(
            f"{route} completion failed: root is not the exact Git worktree toplevel", 1
        )

    if path_id is None:
        raise StartPathError(f"{route} completion failed: task id is required for scope binding", 1)
    base_doc = _load_task_base(root, path_id)
    if base_doc is None:
        raise StartPathError(
            f"{route} completion failed: no recorded task base for {path_id}; restart through the supported begin path",
            1,
        )

    head_res = _run_git_readonly(root, ["rev-parse", "--verify", "HEAD^{commit}"], text=True)
    if head_res.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", head_res.stdout.strip()):
        raise StartPathError(f"{route} completion failed: HEAD is not a resolvable commit", 1)
    head = head_res.stdout.strip()
    base_revision = base_doc["base_revision"]

    ancestor = _run_git_readonly(root, ["merge-base", "--is-ancestor", base_revision, head], text=True)
    if ancestor.returncode != 0:
        raise StartPathError(
            f"{route} completion failed: recorded task base {base_revision} is not an ancestor of HEAD {head}",
            1,
        )

    if base_doc["schema_version"] == 2:
        if base_doc["authorization"] != authorization:
            raise StartPathError("task authorization changed; begin with a fresh task ID", 1)
    elif contract_id is not None:
        raise StartPathError("legacy task base lacks authorization proof; begin with a fresh task ID", 1)

    projections = []
    for args in (["diff", "--no-renames", "--name-status", "-z", base_revision, head, "--"],
                 ["diff", "--no-renames", "--cached", "--name-status", "-z", head, "--"],
                 ["diff", "--no-renames", "--name-status", "-z", "--"]):
        result = _run_git_readonly(root, args, text=False)
        if result.returncode:
            raise StartPathError(f"{route} completion failed: change-layer inspection failed", 1)
        projections.append(_parse_name_status_z(result.stdout))
    status_res = _run_git_readonly(root, ["status", "--porcelain", "-z", "--untracked-files=all"], text=False)
    if status_res.returncode:
        raise StartPathError(f"{route} completion failed: working-tree inspection failed", 1)
    declared_set = set(scoped)
    unchanged = set()
    inherited = {p for e in base_doc["pre_existing_entries"] for p in e["paths"]}
    for path in sorted(inherited):
        if path in declared_set or _task_owned_governance_path(path, path_id):
            continue
        if base_doc["schema_version"] != 2:
            raise StartPathError("legacy task base lacks inherited preservation proof; begin with a fresh task ID", 1)
        if _observe_inherited_endpoint(root, path) == base_doc["inherited_observations"][path]:
            unchanged.add(path)
    receipt_state_observation = None
    if _receipt_replay_context is not None:
        wa = _load_workflow_assurance()
        try:
            receipt_state_observation = wa._receipt_replay_observation(root, _receipt_replay_context,
                feature_id=path_id, route=route, candidate=_receipt_candidate_identity)
        except wa.AssuranceError as exc:
            raise StartPathError("receipt replay scope proof failed: " + str(exc), 1) from exc
    undeclared: list[str] = []

    def consider(raw_path: str) -> None:
        try:
            norm = normalize_relative_path(raw_path, root=root, forbid_nizam_payload=False)
        except StartPathError:
            norm = raw_path.strip()
        if _task_owned_governance_path(norm, path_id):
            return
        if norm == ".agent/run_state.json" and receipt_state_observation is not None:
            if _observe_inherited_endpoint(root, norm) != receipt_state_observation:
                raise StartPathError("receipt replay canonical state changed during scope verification", 1)
            return
        if norm in declared_set or norm in undeclared:
            return
        undeclared.append(norm)

    # Committed changes can never inherit a dirty-work exemption.
    for entry in projections[0]:
        for raw_path in entry["paths"]:
            consider(raw_path)
    for entries in projections[1:] + [_parse_porcelain_z(status_res.stdout)]:
        for entry in entries:
            for raw_path in entry["paths"]:
                if raw_path not in unchanged:
                    consider(raw_path)
    # Restoration/deletion can remove a path from status entirely.
    for raw_path in inherited - unchanged:
        consider(raw_path)

    if undeclared:
        raise StartPathError(
            f"{route} completion failed: working tree contains undeclared changes outside scoped files: "
            + ", ".join(undeclared)
            + f" (delta from task base {base_revision})",
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
    if isinstance(contract.get("contract_id"), str) and contract["contract_id"] != contract_id:
        raise StartPathError(
            f"contract record identity {contract['contract_id']!r} does not match requested contract {contract_id!r}",
            1,
        )
    if (
        isinstance(contract.get("feature_id"), str)
        and isinstance(contract.get("contract_id"), str)
        and contract["feature_id"] != contract["contract_id"]
    ):
        raise StartPathError(
            "contract feature_id and contract_id disagree; refusing an ambiguous contract binding",
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


def _load_workflow_assurance():
    import importlib.util
    name = "_nizam_workflow_assurance_" + hashlib.sha256(str(Path(__file__).resolve()).encode()).hexdigest()[:16]
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().with_name("workflow_assurance.py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def load_passing_qa(root: Path, path_id: str) -> None:
    """Validate structured capture proof against independent assessed authorization."""
    verdict = load_record(root, Path(".agent") / "qa" / f"{path_id}.json", "qa_verdict.schema.json")
    if (verdict.get("feature_id") or verdict.get("id")) != path_id:
        raise StartPathError("QA verdict feature_id does not match --id", 1)
    wa = _load_workflow_assurance()
    try:
        candidate = wa.parse_json(wa._qa_artifact(root, verdict.get("candidate_ref")))
        required_checks = wa.qa_bound_checks(root, path_id, candidate)
        wa.validate_qa_proof(root, verdict, feature_id=path_id, candidate=candidate, required_checks=required_checks)
    except wa.AssuranceError as exc:
        raise StartPathError("recorded verification result does not pass structured QA proof; capture afresh: " + str(exc), 1) from exc


QA_BLOCKING_KEYS = (
    "issues",
    "unsupported_claims",
    "missing_acceptance_coverage",
    "required_fixes",
)


def qa_passes(verdict: dict) -> bool:
    """Read historical QA declarations for display and compatibility diagnostics.

    This boolean does not inspect captures or establish execution proof. Authority
    consumers must use workflow_assurance.validate_qa_proof instead.
    """
    if not isinstance(verdict, dict):
        return False

    # Contradictory shape markers are never a pass.
    if "qa_pass" in verdict and "verdict" in verdict:
        if verdict.get("qa_pass") is True and verdict.get("verdict") != "pass":
            return False
        if verdict.get("qa_pass") is False and verdict.get("verdict") == "pass":
            return False

    has_evolved = "qa_pass" in verdict
    has_legacy = "verdict" in verdict
    if not has_evolved and not has_legacy:
        return False

    if has_evolved:
        if verdict.get("qa_pass") is not True:
            return False
        checks_run = verdict.get("checks_run")
        checks_passed = verdict.get("checks_passed")
        if not isinstance(checks_run, int) or isinstance(checks_run, bool) or checks_run < 1:
            return False
        if not isinstance(checks_passed, int) or isinstance(checks_passed, bool) or checks_passed != checks_run:
            return False
        final_verdict = verdict.get("final_verdict")
        if not isinstance(final_verdict, dict) or final_verdict.get("approved") is not True:
            return False
        if any(verdict.get(key) for key in QA_BLOCKING_KEYS):
            return False
        evidence_files = verdict.get("evidence_files")
        if not isinstance(evidence_files, list) or len(evidence_files) < checks_run:
            return False
        if any(not isinstance(item, str) or not item.strip() for item in evidence_files):
            return False
        checks = verdict.get("checks")
        if checks is not None:
            if not isinstance(checks, list) or len(checks) < checks_run:
                return False
            if any(not _qa_check_executed_ok(item) for item in checks):
                return False
        return True

    # Legacy shape: a favorable overall word cannot override a failed/uncaptured
    # check, a non-empty blocking array, or an explicit non-approval field.
    if verdict.get("verdict") != "pass":
        return False
    final_verdict = verdict.get("final_verdict")
    if isinstance(final_verdict, dict) and final_verdict.get("approved") is False:
        return False
    if any(verdict.get(key) for key in QA_BLOCKING_KEYS):
        return False
    checks = verdict.get("checks")
    if not isinstance(checks, list) or len(checks) < 1:
        return False
    if not all(_qa_check_executed_ok(item) for item in checks):
        return False
    return True


def _qa_check_executed_ok(check: Any) -> bool:
    """A check counts only when it actually executed successfully and names evidence."""
    if not isinstance(check, dict):
        return False
    if check.get("executed") is False:
        return False
    exit_code = check.get("exit_code")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool) or exit_code != 0:
        return False
    if check.get("status") not in (None, "pass", "passed"):
        return False
    evidence = check.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        return False
    return True


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

