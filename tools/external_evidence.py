#!/usr/bin/env python3
"""Generic optional external evidence admission and host-allocated attempt lineage (NF-R04).

This module provides a neutral, standalone local CLI and library interface for admitting
external verification evidence into a Nizam-governed consumer repository without any
dependency on Agentic SDLC. It is completely optional and disabled unless explicitly
invoked by a consumer workflow.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import tempfile
from typing import Any, Iterator, Mapping, Sequence

import jsonschema

TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import git_seam  # noqa: E402


SCHEMA_VERSION = "1.0.0"
PROTOCOL_VERSION = "1.0.0"
SUPPORTED_PROFILE_ID = "generic-external-evidence-v1"
SUPPORTED_PROFILE_VERSION = "1.1.0"
DEFAULT_STEP_LIMIT = 3
DEFAULT_TASK_FAILURE_CEILING = 6
MAX_SIGNATURE_FAILURES = 3

FORBIDDEN_COMMISSIONING_IDS = frozenset({
    "117",
    "123",
    "feature117",
    "feature-117",
    "feature_117",
    "wa123",
    "wa-123",
    "wa_123",
    "fixture-only-capture-producer",
    "fixture-only-session",
})

REQUIRED_ARTIFACT_ROLES = frozenset({"stdout", "stderr", "verdict_report"})


class ExternalEvidenceError(ValueError):
    """Fail-closed error during attempt permit allocation or external evidence admission."""

    def __init__(self, message: str, *, code: str = "external_evidence_error", exit_code: int = 1) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize value as deterministic UTF-8 canonical JSON bytes."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _fsync_dir(directory: Path) -> None:
    fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_atomic_json(target: Path, payload: Mapping[str, Any], *, mode: int = 0o600) -> bytes:
    """Write canonical JSON atomically via temp file + fsync + os.replace + parent dir fsync."""
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_json_bytes(payload) + b"\n"
    fd, tmp_name = tempfile.mkstemp(prefix=f".tmp-{target.name}-", dir=str(target.parent))
    tmp_path = Path(tmp_name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
        _fsync_dir(target.parent)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
    return raw


def _write_exclusive_bytes(target: Path, raw: bytes, *, mode: int = 0o600) -> None:
    """Create a new file exclusively (`O_CREAT | O_EXCL`) and fsync file and parent dir."""
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(target, flags, mode)
    except FileExistsError as exc:
        raise ExternalEvidenceError(
            f"exclusive evidence file already exists: {target}",
            code="exclusive_file_exists",
        ) from exc
    with os.fdopen(fd, "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    _fsync_dir(target.parent)


def _read_regular_file(root: Path, rel_path: str, label: str) -> tuple[Path, bytes]:
    """Resolve rel_path inside root, rejecting traversal, symlinks, or non-regular files."""
    if not rel_path or rel_path.startswith("/") or "\\" in rel_path or ".." in Path(rel_path).parts:
        raise ExternalEvidenceError(f"{label}: unsafe relative path {rel_path!r}", code="unsafe_path")
    current = root.resolve(strict=True)
    for part in Path(rel_path).parts:
        current = current / part
        if os.path.lexists(current) and current.is_symlink():
            raise ExternalEvidenceError(f"{label}: symlink encountered at {rel_path!r}", code="symlink_rejected")
    if not current.exists():
        raise ExternalEvidenceError(f"{label}: missing file {rel_path!r}", code="missing_file")
    st = os.lstat(current)
    if not stat.S_ISREG(st.st_mode):
        raise ExternalEvidenceError(f"{label}: not a regular file {rel_path!r}", code="non_regular_file")
    return current, current.read_bytes()


def _check_not_commissioning_evidence(token: str, field_name: str) -> None:
    norm = token.strip().lower()
    if norm in FORBIDDEN_COMMISSIONING_IDS or "feature117" in norm or "wa123" in norm:
        raise ExternalEvidenceError(
            f"{field_name}: historical commissioning evidence ({token!r}) is forbidden as runtime proof",
            code="commissioning_evidence_rejected",
        )


def _validate_identifier(value: Any, field_name: str) -> None:
    """Enforce the existing wire identifier contract before constructing paths."""
    try:
        jsonschema.Draft202012Validator(_load_admission_schema()["$defs"]["safe_token"]).validate(value)
    except jsonschema.ValidationError as exc:
        raise ExternalEvidenceError(f"{field_name}: invalid safe_token identifier", code="invalid_identifier") from exc


def _admission_dir(repo_root: Path) -> Path:
    return repo_root / ".agent" / "evidence" / "external_admissions"


@contextmanager
def _exclusive_state_lock(repo_root: Path) -> Iterator[Path]:
    state_dir = _admission_dir(repo_root)
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / "state.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0), 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield state_dir
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _cleanup_staging_files(state_dir: Path) -> list[str]:
    """Remove any leftover `.tmp-*` staging files from interrupted/crashed processes."""
    cleaned: list[str] = []
    if not state_dir.exists():
        return cleaned
    for sub in (state_dir, state_dir / "permits", state_dir / "admitted"):
        if not sub.is_dir():
            continue
        for item in sub.iterdir():
            if item.name.startswith(".tmp-"):
                try:
                    item.unlink()
                    cleaned.append(str(item.relative_to(state_dir)))
                except OSError:
                    pass
    return sorted(cleaned)


def _load_or_init_ledger(state_dir: Path) -> dict[str, Any]:
    ledger_path = state_dir / "ledger.json"
    if not ledger_path.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "tasks": {},
            "permits": {},
            "admissions": {},
        }
    if ledger_path.is_symlink():
        raise ExternalEvidenceError("external admission ledger.json is a symlink", code="corrupt_ledger")
    try:
        raw = ledger_path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExternalEvidenceError(f"corrupt external admission ledger: {exc}", code="corrupt_ledger") from exc
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != SCHEMA_VERSION
        or not isinstance(data.get("tasks"), dict)
        or not isinstance(data.get("permits"), dict)
        or not isinstance(data.get("admissions"), dict)
    ):
        raise ExternalEvidenceError("malformed external admission ledger structure", code="corrupt_ledger")
    return data


def _read_admission_record(repo_root: Path, rel_path: str, admission_key: str) -> dict[str, Any]:
    _, raw = _read_regular_file(repo_root, rel_path, "admission record")
    try:
        doc = json.loads(raw.decode("utf-8"))
        valid = (
            isinstance(doc, dict)
            and set(doc) == {"schema_version", "admission_key", "envelope_sha256", "envelope"}
            and doc["schema_version"] == SCHEMA_VERSION
            and doc["admission_key"] == admission_key
            and isinstance(doc["envelope"], dict)
            and doc["envelope_sha256"] == sha256_hex(canonical_json_bytes(doc["envelope"]))
        )
    except (UnicodeDecodeError, ValueError, TypeError) as exc:
        raise ExternalEvidenceError("invalid retained admission record", code="corrupt_admission") from exc
    if not valid:
        raise ExternalEvidenceError("retained admission record digest/binding mismatch", code="corrupt_admission")
    return doc


def _untracked_state_files(repo_root: Path, state_dir: Path, ledger: Mapping[str, Any]) -> list[str]:
    """Never silently discard records published before an interrupted ledger write."""
    expected: set[str] = set()
    for entry in ledger["permits"].values():
        if not isinstance(entry, dict) or not all(isinstance(entry.get(k), str) for k in ("permit_path", "token_path")):
            raise ExternalEvidenceError("malformed retained permit entry", code="corrupt_ledger")
        expected.update((entry["permit_path"], entry["token_path"]))
    for entry in ledger["admissions"].values():
        if not isinstance(entry, dict) or not isinstance(entry.get("admission_path"), str):
            raise ExternalEvidenceError("malformed retained admission entry", code="corrupt_ledger")
        expected.add(entry["admission_path"])
    actual = {
        str(item.relative_to(repo_root))
        for sub in (state_dir / "permits", state_dir / "admitted") if sub.is_dir()
        for item in sub.iterdir()
    }
    return sorted(actual - expected)


def _verify_operator_recovery(
    repo_root: Path,
    task_id: str,
    recovery_ref: str | None,
    failed_admission_paths: set[str],
) -> int | None:
    """Validate explicit finite operator recovery when present; return finite ceiling or None."""
    if recovery_ref is None:
        return None
    _, raw = _read_regular_file(repo_root, recovery_ref, "operator_recovery_ref")
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExternalEvidenceError(f"invalid operator_recovery_ref JSON: {exc}", code="invalid_operator_recovery") from exc
    required = {"role", "task_id", "approved", "max_task_attempts", "after_capture", "authority_ref"}
    if (
        not isinstance(doc, dict)
        or set(doc.keys()) != required
        or doc.get("role") != "operator"
        or doc.get("task_id") != task_id
        or doc.get("approved") is not True
        or type(doc.get("max_task_attempts")) is not int
        or doc["max_task_attempts"] < 1
        or doc.get("authority_ref") != recovery_ref
    ):
        raise ExternalEvidenceError(
            "operator_recovery_ref must be a closed operator authority object with positive integer max_task_attempts",
            code="invalid_operator_recovery",
        )
    if doc["after_capture"] not in failed_admission_paths:
        raise ExternalEvidenceError(
            f"operator_recovery_ref.after_capture ({doc['after_capture']!r}) does not bind a recorded failed admission for task {task_id}",
            code="invalid_operator_recovery",
        )
    return int(doc["max_task_attempts"])


def allocate_attempt_permit(
    repo_root: Path,
    *,
    task_id: str,
    step_id: str,
    run_id: str,
    candidate_commit: str,
    continuation_basis: str = "initial_attempt",
    parent_attempt: int | None = None,
    operator_recovery_ref: str | None = None,
    step_limit: int = DEFAULT_STEP_LIMIT,
) -> dict[str, Any]:
    """Allocate a host-owned monotonic attempt permit under exclusive lock."""
    for field, value in (("task_id", task_id), ("step_id", step_id), ("run_id", run_id)):
        _validate_identifier(value, field)
    repo_root = Path(repo_root).resolve(strict=True)
    git_seam.validate_repo_root(repo_root)
    _check_not_commissioning_evidence(task_id, "task_id")
    _check_not_commissioning_evidence(step_id, "step_id")
    _check_not_commissioning_evidence(run_id, "run_id")

    if type(step_limit) is not int or step_limit < 1:
        raise ExternalEvidenceError("step_limit must be a positive integer", code="invalid_step_limit")

    try:
        verified_commit = git_seam.run_git_readonly(
            repo_root, "rev-parse", "--verify", f"{candidate_commit}^{{commit}}"
        ).decode("ascii").strip()
        candidate_tree = git_seam.run_git_readonly(
            repo_root, "rev-parse", "--verify", f"{verified_commit}^{{tree}}"
        ).decode("ascii").strip()
    except git_seam.GitSeamError as exc:
        raise ExternalEvidenceError(f"candidate_commit validation failed: {exc}", code="invalid_candidate_commit") from exc
    if verified_commit != candidate_commit:
        raise ExternalEvidenceError("candidate_commit must be an exact 40-hex commit SHA", code="invalid_candidate_commit")

    with _exclusive_state_lock(repo_root) as state_dir:
        _cleanup_staging_files(state_dir)
        ledger = _load_or_init_ledger(state_dir)
        task_state = ledger["tasks"].setdefault(
            task_id,
            {
                "steps": {},
                "failed_count": 0,
                "failed_admissions": [],
                "signature_counts": {},
                "history": [],
            },
        )
        step_state = task_state["steps"].setdefault(
            step_id,
            {"allocated_attempts": 0, "admitted_attempts": 0},
        )

        # Refuse allocating a new attempt if a prior permit for this step is still pending admission
        next_attempt = int(step_state["allocated_attempts"]) + 1
        if step_state["allocated_attempts"] != step_state["admitted_attempts"]:
            raise ExternalEvidenceError(
                f"cannot allocate attempt {next_attempt} for {task_id}:{step_id} while attempt {step_state['allocated_attempts']} has no recorded outcome",
                code="unsettled_prior_attempt",
            )

        if next_attempt == 1:
            if parent_attempt is not None or continuation_basis != "initial_attempt":
                raise ExternalEvidenceError(
                    "attempt 1 requires parent_attempt=null and continuation_basis='initial_attempt'",
                    code="invalid_lineage",
                )
        else:
            if parent_attempt != next_attempt - 1:
                raise ExternalEvidenceError(
                    f"attempt {next_attempt} requires parent_attempt={next_attempt - 1}, got {parent_attempt}",
                    code="invalid_lineage",
                )
            if continuation_basis == "initial_attempt":
                raise ExternalEvidenceError(
                    f"attempt {next_attempt} cannot use continuation_basis='initial_attempt'",
                    code="invalid_lineage",
                )

        failed_paths = set(task_state.get("failed_admissions", []))
        recovered_ceiling = _verify_operator_recovery(repo_root, task_id, operator_recovery_ref, failed_paths)
        task_ceiling = recovered_ceiling if recovered_ceiling is not None else DEFAULT_TASK_FAILURE_CEILING

        if int(task_state["failed_count"]) >= task_ceiling:
            raise ExternalEvidenceError(
                f"circuit-breaker halt: task {task_id} failed-attempt ceiling ({task_ceiling}) exhausted",
                code="task_ceiling_exhausted",
                exit_code=2,
            )

        sig_counts = task_state.get("signature_counts", {})
        if any(int(c) >= MAX_SIGNATURE_FAILURES for c in sig_counts.values()) and recovered_ceiling is None:
            raise ExternalEvidenceError(
                f"circuit-breaker halt: task {task_id} has {MAX_SIGNATURE_FAILURES} failures with the same defect signature; explicit finite operator recovery required",
                code="signature_ceiling_exhausted",
                exit_code=2,
            )

        if next_attempt > step_limit and recovered_ceiling is None:
            raise ExternalEvidenceError(
                f"circuit-breaker halt: step {task_id}:{step_id} attempt {next_attempt} exceeds configured step limit ({step_limit})",
                code="step_limit_exhausted",
                exit_code=2,
            )

        permit_id = f"permit-{task_id}-{step_id}-a{next_attempt}"
        permit_token = secrets.token_hex(32)
        permit_doc = {
            "schema_version": SCHEMA_VERSION,
            "permit_id": permit_id,
            "task_id": task_id,
            "step_id": step_id,
            "run_id": run_id,
            "attempt_number": next_attempt,
            "parent_attempt": parent_attempt,
            "continuation_basis": continuation_basis,
            "operator_recovery_ref": operator_recovery_ref,
            "candidate_commit": candidate_commit,
            "candidate_tree": candidate_tree,
            "task_failure_ceiling": task_ceiling,
        }
        permit_raw = canonical_json_bytes(permit_doc)
        permit_digest = sha256_hex(permit_raw)
        permit_rel = f".agent/evidence/external_admissions/permits/{task_id}-{step_id}-attempt{next_attempt}.permit.json"
        token_rel = f".agent/evidence/external_admissions/permits/{task_id}-{step_id}-attempt{next_attempt}.token"

        _write_exclusive_bytes(repo_root / permit_rel, permit_raw + b"\n", mode=0o600)
        _write_exclusive_bytes(repo_root / token_rel, (permit_token + "\n").encode("ascii"), mode=0o600)

        step_state["allocated_attempts"] = next_attempt
        ledger["permits"][permit_id] = {
            "permit_id": permit_id,
            "permit_digest": permit_digest,
            "permit_path": permit_rel,
            "token_path": token_rel,
            "task_id": task_id,
            "step_id": step_id,
            "run_id": run_id,
            "attempt_number": next_attempt,
            "parent_attempt": parent_attempt,
            "continuation_basis": continuation_basis,
            "operator_recovery_ref": operator_recovery_ref,
            "candidate_commit": candidate_commit,
            "candidate_tree": candidate_tree,
            "consumed": False,
        }
        _write_atomic_json(state_dir / "ledger.json", ledger)
        return {
            "permit": permit_doc,
            "permit_digest": permit_digest,
            "permit_path": permit_rel,
            "permit_token": permit_token,
        }


def compute_producer_proof(
    *,
    envelope_binding: Mapping[str, Any],
    permit_digest: str,
    permit_token: str,
    candidate_commit: str,
    candidate_tree: str,
    execution_identity: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
    producer_id: str,
    session_id: str,
    issued_at: str,
) -> dict[str, str]:
    """Authenticate the complete profile-1.1 envelope and producer identity."""
    binding = {key: value for key, value in envelope_binding.items() if key != "producer_proof"}
    required = set(_load_admission_schema()["required"]) - {"producer_proof"}
    if set(binding) != required:
        raise ExternalEvidenceError("producer proof requires complete envelope binding", code="incomplete_proof_binding")
    payload = {
        "mac_profile": "nizam-external-envelope-hmac-v2",
        "envelope_binding": binding,
        "permit_digest": permit_digest,
        "candidate_commit": candidate_commit,
        "candidate_tree": candidate_tree,
        "execution_identity": dict(execution_identity),
        "artifacts": [dict(a) for a in artifacts],
        "producer_id": producer_id,
        "session_id": session_id,
        "issued_at": issued_at,
    }
    mac = hmac.new(
        permit_token.encode("ascii"),
        canonical_json_bytes(payload),
        hashlib.sha256,
    ).hexdigest()
    return {
        "producer_id": producer_id,
        "session_id": session_id,
        "permit_binding_digest": mac,
        "issued_at": issued_at,
    }


def _load_admission_schema() -> dict[str, Any]:
    schema_path = ROOT_DIR / "schema" / "external_evidence_admission.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def admit_external_evidence(
    repo_root: Path,
    envelope: Mapping[str, Any],
    *,
    expected_candidate_sha256: str,
    expected_policy_id: str,
    expected_policy_version: str,
    expected_policy_digest: str,
    expected_framework_version: str,
    expected_framework_commit: str,
    expected_framework_tree: str,
    expected_contract_path: str,
    expected_acceptance_collection_digest: str,
    expected_regression_collection_digest: str,
    expected_tool_id: str | None = None,
    expected_adapter_id: str | None = None,
) -> dict[str, Any]:
    """Validate and atomically admit or record an external evidence submission under lock."""
    if not isinstance(expected_candidate_sha256, str) or re.fullmatch(r"[0-9a-f]{64}", expected_candidate_sha256) is None:
        raise ExternalEvidenceError("expected_candidate_sha256 must be a trusted lowercase SHA256", code="invalid_expected_candidate_digest")
    repo_root = Path(repo_root).resolve(strict=True)
    git_seam.validate_repo_root(repo_root)

    if not isinstance(envelope, Mapping):
        raise ExternalEvidenceError("envelope must be a JSON object", code="schema_violation")

    # 1. Explicit protocol/profile version check before schema validation for clear diagnostics
    if envelope.get("schema_version") != SCHEMA_VERSION or envelope.get("protocol_version") != PROTOCOL_VERSION:
        raise ExternalEvidenceError(
            f"unsupported schema/protocol version: {envelope.get('schema_version')!r} / {envelope.get('protocol_version')!r}",
            code="unsupported_version",
        )
    if envelope.get("profile_id") != SUPPORTED_PROFILE_ID or envelope.get("profile_version") != SUPPORTED_PROFILE_VERSION:
        raise ExternalEvidenceError(
            f"unsupported profile: {envelope.get('profile_id')!r}@{envelope.get('profile_version')!r}",
            code="unsupported_profile",
        )

    schema = _load_admission_schema()
    try:
        jsonschema.Draft202012Validator(schema).validate(dict(envelope))
    except jsonschema.ValidationError as exc:
        raise ExternalEvidenceError(
            f"external evidence schema validation failed: {exc.message}",
            code="schema_violation",
        ) from exc

    if envelope["consumer_binding"]["candidate_sha256"] != expected_candidate_sha256:
        raise ExternalEvidenceError("candidate_sha256 does not match trusted host expectation", code="candidate_digest_mismatch")

    lineage = envelope["attempt_lineage"]
    task_id = lineage["task_id"]
    step_id = lineage["step_id"]
    run_id = lineage["run_id"]
    attempt_number = int(lineage["attempt_number"])
    permit_id = lineage["permit_id"]
    permit_digest = lineage["permit_digest"]
    contract_binding = envelope["contract_binding"]
    producer_proof = envelope["producer_proof"]

    # 2. Reject copied historical commissioning evidence (feature117 / WA123) across all identity fields
    _check_not_commissioning_evidence(task_id, "attempt_lineage.task_id")
    _check_not_commissioning_evidence(step_id, "attempt_lineage.step_id")
    _check_not_commissioning_evidence(run_id, "attempt_lineage.run_id")
    _check_not_commissioning_evidence(contract_binding["contract_id"], "contract_binding.contract_id")
    _check_not_commissioning_evidence(producer_proof["producer_id"], "producer_proof.producer_id")
    _check_not_commissioning_evidence(producer_proof["session_id"], "producer_proof.session_id")
    for req_id in contract_binding["requirement_ids"]:
        _check_not_commissioning_evidence(req_id, "contract_binding.requirement_ids")
    for ac_id in contract_binding["acceptance_criteria_ids"]:
        _check_not_commissioning_evidence(ac_id, "contract_binding.acceptance_criteria_ids")

    envelope_raw = canonical_json_bytes(envelope)
    envelope_sha256 = sha256_hex(envelope_raw)
    admission_key = f"{task_id}:{step_id}:{attempt_number}"

    with _exclusive_state_lock(repo_root) as state_dir:
        _cleanup_staging_files(state_dir)
        ledger = _load_or_init_ledger(state_dir)

        # 3. Identify replay, but never bypass current host bindings or evidence checks.
        existing_admission = ledger["admissions"].get(admission_key)
        if existing_admission is not None:
            if existing_admission.get("envelope_sha256") != envelope_sha256 or existing_admission.get("permit_id") != permit_id:
                raise ExternalEvidenceError(
                    f"conflicting reuse of attempt {admission_key}", code="conflicting_attempt_reuse",
                )

        # 4. Verify host-allocated permit binding and authenticate producer proof
        permit_entry = ledger["permits"].get(permit_id)
        if permit_entry is None:
            raise ExternalEvidenceError(
                f"unallocated or unknown permit_id {permit_id!r}",
                code="unallocated_permit",
            )
        if permit_entry.get("consumed") is True and existing_admission is None:
            raise ExternalEvidenceError(
                f"permit {permit_id!r} was already consumed by another admission",
                code="conflicting_attempt_reuse",
            )
        if (
            permit_entry["permit_digest"] != permit_digest
            or permit_entry["task_id"] != task_id
            or permit_entry["step_id"] != step_id
            or permit_entry["run_id"] != run_id
            or permit_entry["attempt_number"] != attempt_number
            or permit_entry["parent_attempt"] != lineage["parent_attempt"]
            or permit_entry["continuation_basis"] != lineage["continuation_basis"]
            or permit_entry["operator_recovery_ref"] != lineage["operator_recovery_ref"]
        ):
            raise ExternalEvidenceError(
                f"attempt_lineage does not match host-allocated permit {permit_id!r}",
                code="permit_lineage_mismatch",
            )

        _, permit_disk_raw = _read_regular_file(repo_root, permit_entry["permit_path"], "permit_file")
        if sha256_hex(permit_disk_raw.strip()) != permit_digest:
            raise ExternalEvidenceError("on-disk permit file digest mismatch", code="corrupt_permit")
        _, token_disk_raw = _read_regular_file(repo_root, permit_entry["token_path"], "permit_token")
        permit_token = token_disk_raw.decode("ascii").strip()

        consumer = envelope["consumer_binding"]
        if (
            consumer["candidate_commit"] != permit_entry["candidate_commit"]
            or consumer["candidate_tree"] != permit_entry["candidate_tree"]
        ):
            raise ExternalEvidenceError(
                "consumer_binding candidate_commit/candidate_tree does not match host-allocated permit",
                code="candidate_mismatch",
            )

        # 5. Verify policy, framework, repository/git, contract, collection, and tool/adapter bindings
        pol = envelope["policy_binding"]
        if (
            pol["policy_id"] != expected_policy_id
            or pol["policy_version"] != expected_policy_version
            or pol["policy_digest"] != expected_policy_digest
        ):
            raise ExternalEvidenceError("policy_binding mismatch against active governance policy", code="policy_mismatch")

        fw = envelope["framework_identity"]
        if (
            fw["version"] != expected_framework_version
            or fw["commit_sha"] != expected_framework_commit
            or fw["tree_sha"] != expected_framework_tree
        ):
            raise ExternalEvidenceError("framework_identity mismatch against expected framework pin", code="framework_mismatch")

        try:
            origin_url = git_seam.run_git_readonly(repo_root, "remote", "get-url", "origin").decode("utf-8").strip()
            actual_cand_commit = git_seam.run_git_readonly(
                repo_root, "rev-parse", "--verify", f"{consumer['candidate_commit']}^{{commit}}"
            ).decode("ascii").strip()
            actual_cand_tree = git_seam.run_git_readonly(
                repo_root, "rev-parse", "--verify", f"{actual_cand_commit}^{{tree}}"
            ).decode("ascii").strip()
            actual_base_commit = git_seam.run_git_readonly(
                repo_root, "rev-parse", "--verify", f"{consumer['base_commit']}^{{commit}}"
            ).decode("ascii").strip()
            git_seam.run_git_readonly(repo_root, "merge-base", "--is-ancestor", actual_base_commit, actual_cand_commit)
        except git_seam.GitSeamError as exc:
            raise ExternalEvidenceError(f"Git consumer binding verification failed: {exc}", code="git_binding_mismatch") from exc

        if consumer["repository"].rstrip("/") != origin_url.rstrip("/"):
            raise ExternalEvidenceError(
                f"consumer_binding.repository ({consumer['repository']!r}) != origin ({origin_url!r})",
                code="repository_mismatch",
            )
        if actual_cand_tree != consumer["candidate_tree"]:
            raise ExternalEvidenceError("consumer_binding.candidate_tree does not match immutable Git tree", code="tree_mismatch")

        _, contract_raw = _read_regular_file(repo_root, expected_contract_path, "contract")
        if sha256_hex(contract_raw) != contract_binding["contract_digest"]:
            raise ExternalEvidenceError("contract_binding.contract_digest does not match contract file on disk", code="contract_mismatch")
        try:
            contract_doc = json.loads(contract_raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ExternalEvidenceError(f"invalid contract JSON: {exc}", code="contract_mismatch") from exc
        if str(contract_doc.get("contract_id") or contract_doc.get("id")) != contract_binding["contract_id"]:
            raise ExternalEvidenceError("contract_binding.contract_id does not match contract file", code="contract_mismatch")

        coll = envelope["collection_binding"]
        if (
            coll["acceptance_collection_digest"] != expected_acceptance_collection_digest
            or coll["regression_collection_digest"] != expected_regression_collection_digest
        ):
            raise ExternalEvidenceError(
                "collection_binding digests do not match frozen acceptance/regression collections",
                code="collection_mismatch",
            )

        exec_id = envelope["execution_identity"]
        if expected_tool_id is not None and exec_id["tool_id"] != expected_tool_id:
            raise ExternalEvidenceError(f"execution_identity.tool_id ({exec_id['tool_id']!r}) != {expected_tool_id!r}", code="tool_mismatch")
        if expected_adapter_id is not None and exec_id["adapter_id"] != expected_adapter_id:
            raise ExternalEvidenceError(
                f"execution_identity.adapter_id ({exec_id['adapter_id']!r}) != {expected_adapter_id!r}",
                code="adapter_mismatch",
            )

        # 6. Verify status separation rules
        status_sep = envelope["status_separation"]
        test_outcome = status_sep["test_outcome"]
        exec_status = status_sep["execution_status"]
        decision = status_sep["admission_decision"]

        if exec_status != "completed" and decision == "admitted":
            raise ExternalEvidenceError(
                f"status separation violation: incomplete execution ({exec_status}) cannot have admission_decision='admitted'",
                code="status_separation_violation",
            )
        if test_outcome == "failed" and decision == "admitted":
            raise ExternalEvidenceError(
                "status separation violation: failed test_outcome cannot have admission_decision='admitted'",
                code="status_separation_violation",
            )
        if test_outcome == "failed" and lineage["defect_signature"] is None:
            raise ExternalEvidenceError(
                "failed test_outcome requires a non-null sha256 defect_signature in attempt_lineage",
                code="missing_defect_signature",
            )

        # 7. Verify all artifact descriptors on disk (no partial captures, symlinks, or commissioning payloads)
        artifacts = envelope["artifacts"]
        roles_present: set[str] = set()
        seen_paths: set[str] = set()
        for index, art in enumerate(artifacts):
            role = art["role"]
            rel = art["path"]
            if rel in seen_paths:
                raise ExternalEvidenceError(f"artifacts[{index}]: duplicate path {rel!r}", code="duplicate_artifact")
            seen_paths.add(rel)
            roles_present.add(role)
            _, art_raw = _read_regular_file(repo_root, rel, f"artifacts[{index}]")
            if len(art_raw) != art["byte_length"] or sha256_hex(art_raw) != art["sha256"]:
                raise ExternalEvidenceError(
                    f"artifacts[{index}] ({rel}): on-disk byte_length/sha256 mismatch",
                    code="artifact_digest_mismatch",
                )
            if role == "verdict_report":
                try:
                    verdict_doc = json.loads(art_raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ExternalEvidenceError(f"verdict_report is not valid UTF-8 JSON: {exc}", code="invalid_verdict_report") from exc
                if not isinstance(verdict_doc, dict):
                    raise ExternalEvidenceError("verdict_report must be a JSON object", code="invalid_verdict_report")
                if verdict_doc.get("commissioning_fixture") is True or str(verdict_doc.get("feature_id", "")).lower() in FORBIDDEN_COMMISSIONING_IDS:
                    raise ExternalEvidenceError(
                        "verdict_report contains historical commissioning fixture markers",
                        code="commissioning_evidence_rejected",
                    )
                if verdict_doc.get("test_outcome") != test_outcome:
                    raise ExternalEvidenceError(
                        "verdict_report.test_outcome does not match status_separation.test_outcome",
                        code="verdict_outcome_mismatch",
                    )

        missing_roles = REQUIRED_ARTIFACT_ROLES - roles_present
        if missing_roles:
            raise ExternalEvidenceError(
                f"partial capture rejected: missing required artifact roles {sorted(missing_roles)}",
                code="partial_capture",
            )

        expected_proof = compute_producer_proof(
            envelope_binding=envelope,
            permit_digest=permit_digest,
            permit_token=permit_token,
            candidate_commit=consumer["candidate_commit"],
            candidate_tree=consumer["candidate_tree"],
            execution_identity=envelope["execution_identity"],
            artifacts=envelope["artifacts"],
            producer_id=producer_proof["producer_id"],
            session_id=producer_proof["session_id"],
            issued_at=producer_proof["issued_at"],
        )
        if not hmac.compare_digest(expected_proof["permit_binding_digest"], producer_proof["permit_binding_digest"]):
            raise ExternalEvidenceError(
                "producer_proof.permit_binding_digest failed host permit authentication",
                code="forged_producer_proof",
            )

        # 8. Durable record publication followed by one atomic ledger transition.
        admission_rel = f".agent/evidence/external_admissions/admitted/{task_id}-{step_id}-attempt{attempt_number}.admission.json"
        admission_record = {
            "schema_version": SCHEMA_VERSION,
            "admission_key": admission_key,
            "envelope_sha256": envelope_sha256,
            "envelope": dict(envelope),
        }
        if existing_admission is not None:
            retained = _read_admission_record(repo_root, existing_admission["admission_path"], admission_key)
            if retained != admission_record:
                raise ExternalEvidenceError("retained admission differs from validated replay", code="corrupt_admission")
            return {
                "ok": True, "idempotent_replay": True, "admission_key": admission_key,
                "envelope_sha256": envelope_sha256, "admission_path": existing_admission["admission_path"],
                "admission_decision": decision, "test_outcome": test_outcome, "execution_status": exec_status,
            }
        if os.path.lexists(repo_root / admission_rel):
            retained = _read_admission_record(repo_root, admission_rel, admission_key)
            if retained != admission_record:
                raise ExternalEvidenceError("conflicting orphan admission preserved", code="conflicting_orphan_admission")
            # The previous record was durable but the ledger transition was not.
            # All current bindings above were rechecked before completing it once.
        else:
            _write_exclusive_bytes(repo_root / admission_rel, canonical_json_bytes(admission_record) + b"\n", mode=0o600)

        task_state = ledger["tasks"][task_id]
        step_state = task_state["steps"][step_id]
        step_state["admitted_attempts"] = attempt_number
        permit_entry["consumed"] = True

        is_failure = exec_status != "completed" or test_outcome == "failed" or decision != "admitted"
        if is_failure:
            task_state["failed_count"] = int(task_state["failed_count"]) + 1
            task_state.setdefault("failed_admissions", []).append(admission_rel)
            sig = lineage["defect_signature"] or sha256_hex(f"{task_id}:{step_id}:{exec_status}:{test_outcome}".encode("utf-8"))
            sig_counts = task_state.setdefault("signature_counts", {})
            sig_counts[sig] = int(sig_counts.get(sig, 0)) + 1

        task_state.setdefault("history", []).append({
            "admission_key": admission_key,
            "attempt_number": attempt_number,
            "permit_id": permit_id,
            "envelope_sha256": envelope_sha256,
            "admission_path": admission_rel,
            "test_outcome": test_outcome,
            "execution_status": exec_status,
            "admission_decision": decision,
        })
        ledger["admissions"][admission_key] = {
            "admission_key": admission_key,
            "permit_id": permit_id,
            "envelope_sha256": envelope_sha256,
            "admission_path": admission_rel,
            "test_outcome": test_outcome,
            "execution_status": exec_status,
            "admission_decision": decision,
        }
        _write_atomic_json(state_dir / "ledger.json", ledger)
        return {
            "ok": True,
            "idempotent_replay": False,
            "admission_key": admission_key,
            "envelope_sha256": envelope_sha256,
            "admission_path": admission_rel,
            "admission_decision": decision,
            "test_outcome": test_outcome,
            "execution_status": exec_status,
        }


def reconcile_admission_state(repo_root: Path) -> dict[str, Any]:
    """Reconcile external admission state after an interrupted run and verify ledger consistency."""
    repo_root = Path(repo_root).resolve(strict=True)
    with _exclusive_state_lock(repo_root) as state_dir:
        cleaned = _cleanup_staging_files(state_dir)
        ledger = _load_or_init_ledger(state_dir)
        orphans = _untracked_state_files(repo_root, state_dir, ledger)
        if orphans:
            raise ExternalEvidenceError(
                f"unresolved published records preserved for explicit recovery: {orphans}", code="unreconciled_state",
            )
        for permit_id, pentry in ledger["permits"].items():
            _, raw = _read_regular_file(repo_root, pentry["permit_path"], f"permit {permit_id}")
            if sha256_hex(raw.strip()) != pentry["permit_digest"]:
                raise ExternalEvidenceError(f"permit {permit_id} digest mismatch during reconciliation", code="corrupt_permit")
        for adm_key, aentry in ledger["admissions"].items():
            doc = _read_admission_record(repo_root, aentry["admission_path"], adm_key)
            if doc.get("envelope_sha256") != aentry["envelope_sha256"]:
                raise ExternalEvidenceError(f"admission {adm_key} digest mismatch during reconciliation", code="corrupt_admission")
        return {
            "ok": True,
            "cleaned_staging_files": cleaned,
            "permit_count": len(ledger["permits"]),
            "admission_count": len(ledger["admissions"]),
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    alloc = sub.add_parser("allocate-attempt", help="allocate a host-owned attempt permit")
    alloc.add_argument("--root", required=True)
    alloc.add_argument("--task-id", required=True)
    alloc.add_argument("--step-id", required=True)
    alloc.add_argument("--run-id", required=True)
    alloc.add_argument("--candidate-commit", required=True)
    alloc.add_argument("--continuation-basis", default="initial_attempt")
    alloc.add_argument("--parent-attempt", type=int, default=None)
    alloc.add_argument("--operator-recovery-ref", default=None)
    alloc.add_argument("--step-limit", type=int, default=DEFAULT_STEP_LIMIT)

    admit = sub.add_parser("admit-evidence", help="validate and admit an external evidence envelope")
    admit.add_argument("--root", required=True)
    admit.add_argument("--envelope", required=True)
    admit.add_argument("--expected-candidate-sha256", required=True)
    admit.add_argument("--expected-policy-id", required=True)
    admit.add_argument("--expected-policy-version", required=True)
    admit.add_argument("--expected-policy-digest", required=True)
    admit.add_argument("--expected-framework-version", required=True)
    admit.add_argument("--expected-framework-commit", required=True)
    admit.add_argument("--expected-framework-tree", required=True)
    admit.add_argument("--expected-contract-path", required=True)
    admit.add_argument("--expected-acceptance-collection-digest", required=True)
    admit.add_argument("--expected-regression-collection-digest", required=True)
    admit.add_argument("--expected-tool-id", default=None)
    admit.add_argument("--expected-adapter-id", default=None)

    reconcile = sub.add_parser("reconcile", help="reconcile state and clean interrupted staging files")
    reconcile.add_argument("--root", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "allocate-attempt":
            res = allocate_attempt_permit(
                Path(args.root),
                task_id=args.task_id,
                step_id=args.step_id,
                run_id=args.run_id,
                candidate_commit=args.candidate_commit,
                continuation_basis=args.continuation_basis,
                parent_attempt=args.parent_attempt,
                operator_recovery_ref=args.operator_recovery_ref,
                step_limit=args.step_limit,
            )
            print(json.dumps(res, indent=2, sort_keys=True))
            return 0
        if args.command == "admit-evidence":
            env_doc = json.loads(Path(args.envelope).read_text(encoding="utf-8"))
            res = admit_external_evidence(
                Path(args.root),
                env_doc,
                expected_candidate_sha256=args.expected_candidate_sha256,
                expected_policy_id=args.expected_policy_id,
                expected_policy_version=args.expected_policy_version,
                expected_policy_digest=args.expected_policy_digest,
                expected_framework_version=args.expected_framework_version,
                expected_framework_commit=args.expected_framework_commit,
                expected_framework_tree=args.expected_framework_tree,
                expected_contract_path=args.expected_contract_path,
                expected_acceptance_collection_digest=args.expected_acceptance_collection_digest,
                expected_regression_collection_digest=args.expected_regression_collection_digest,
                expected_tool_id=args.expected_tool_id,
                expected_adapter_id=args.expected_adapter_id,
            )
            print(json.dumps(res, indent=2, sort_keys=True))
            return 0
        if args.command == "reconcile":
            res = reconcile_admission_state(Path(args.root))
            print(json.dumps(res, indent=2, sort_keys=True))
            return 0
        return 2
    except ExternalEvidenceError as exc:
        print(json.dumps({"ok": False, "code": exc.code, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    sys.exit(main())
