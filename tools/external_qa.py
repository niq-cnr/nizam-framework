#!/usr/bin/env python3
"""Optional authenticated observations to existing native QA; never completion."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import sys

import jsonschema

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_ee_name = "_nizam_external_evidence_" + hashlib.sha256(str(TOOLS_DIR).encode()).hexdigest()
if _ee_name not in sys.modules:
    _ee_spec = importlib.util.spec_from_file_location(_ee_name, TOOLS_DIR / "external_evidence.py")
    _ee_module = importlib.util.module_from_spec(_ee_spec)
    sys.modules[_ee_name] = _ee_module
    _ee_spec.loader.exec_module(_ee_module)
ee = sys.modules[_ee_name]

MAPPING_ID = "generic-external-native-qa-v1"


def _native_api():
    name = "_nizam_external_qa_native_" + ee.sha256_hex(str(TOOLS_DIR).encode())
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, TOOLS_DIR / "workflow_assurance.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def _ref(reference):
    if type(reference) is not dict or set(reference) not in ({"path", "sha256"}, {"path", "sha256", "revision"}):
        raise ee.ExternalEvidenceError("external QA requires native typed artifact references", code="invalid_qa_mapping")
    return reference


def _validated_projection(repo_root, envelope, *, context_ref, expected_feature_id,
        expected_candidate, required_checks, expected_execution_identity, expected_producer):
    """Called only inside authenticated admission's existing durable transition."""
    wa = _native_api()
    try:
        root = Path(repo_root).resolve(strict=True)
        descriptors = {a["path"]: a for a in envelope["artifacts"]}

        def bound(reference):
            reference = _ref(reference)
            raw = wa._qa_artifact(root, reference)
            descriptor = descriptors.get(reference["path"])
            if (type(descriptor) is not dict or descriptor["sha256"] != ee.sha256_hex(raw)
                    or descriptor["byte_length"] != len(raw)):
                raise ee.ExternalEvidenceError("native QA artifact is not authenticated by envelope", code="unauthenticated_qa_artifact")
            _, current = ee._read_regular_file(root, reference["path"], "external QA artifact")
            if current != raw:
                raise ee.ExternalEvidenceError("native QA historical/current artifact differs", code="qa_artifact_changed")
            return raw

        context_raw = bound(context_ref)
        context = json.loads(context_raw)
        schema = json.loads((TOOLS_DIR.parent / "schema/external_qa_context.schema.json").read_text())
        jsonschema.Draft202012Validator(schema).validate(context)
        checks = wa.qa_required_checks(required_checks)
        candidate_digest = ee.sha256_hex(ee.canonical_json_bytes(expected_candidate))
        checks_digest = ee.sha256_hex(ee.canonical_json_bytes(checks))
        execution_digest = ee.sha256_hex(ee.canonical_json_bytes(expected_execution_identity))
        if (context["feature_id"] != expected_feature_id or envelope["attempt_lineage"]["task_id"] != expected_feature_id
                or envelope["consumer_binding"]["candidate_sha256"] != candidate_digest
                or context["required_checks_sha256"] != checks_digest
                or context["execution_identity_sha256"] != execution_digest
                or envelope["execution_identity"] != expected_execution_identity
                or context["producer"] != expected_producer
                or expected_producer != {"agent_id": envelope["producer_proof"]["producer_id"],
                    "session_id": envelope["producer_proof"]["session_id"]}):
            raise ee.ExternalEvidenceError("external QA trusted host binding mismatch", code="qa_host_binding_mismatch")
        candidate = json.loads(bound(context["candidate_ref"]))
        if ee.canonical_json_bytes(candidate) != ee.canonical_json_bytes(expected_candidate):
            raise ee.ExternalEvidenceError("external QA assessed candidate mismatch", code="qa_candidate_mismatch")
        modes = {a["path"]: a for a in context["artifact_modes"]}
        if (len(modes) != len(context["artifact_modes"]) or
                set(modes) != set(descriptors) - {context_ref["path"]}):
            raise ee.ExternalEvidenceError("external QA complete artifact-mode inventory required", code="qa_mode_inventory_mismatch")
        for path, artifact in modes.items():
            target, raw = ee._read_regular_file(root, path, "external QA mode inventory")
            mode = "100755" if stat.S_IMODE(target.stat().st_mode) & 0o111 else "100644"
            if (artifact["mode"] != mode or artifact["sha256"] != ee.sha256_hex(raw)
                    or artifact["byte_length"] != len(raw)
                    or descriptors[path]["sha256"] != artifact["sha256"]
                    or descriptors[path]["byte_length"] != artifact["byte_length"]):
                raise ee.ExternalEvidenceError("external QA artifact content/mode changed", code="qa_artifact_changed")
        for field, category in (("host_policy_ref", "contracts"), ("execution_profile_ref", "tools")):
            reference = _ref(context[field]); raw = bound(reference)
            selected = {row["path"]: row for row in candidate["assessed_inputs"][category]}
            if (reference.get("revision") is None or reference["path"] not in selected
                    or reference["path"] in candidate["record_ownership"]
                    or selected[reference["path"]]["sha256"] != ee.sha256_hex(raw)):
                raise ee.ExternalEvidenceError("external QA policy/profile must be whole immutable assessed inputs", code="qa_unassessed_profile")
        # The actual optional bridge code is part of the assessed tool closure.
        prefix = "" if TOOLS_DIR == root / "tools" else ".nizam/"
        if TOOLS_DIR != root / (prefix + "tools"):
            raise ee.ExternalEvidenceError("external QA must use the assessed active consumer layout", code="qa_active_layout_mismatch")
        selected_tools = {row["path"] for row in candidate["assessed_inputs"]["tools"]}
        needed = {prefix + p for p in ("tools/external_qa.py", "tools/external_evidence.py", "tools/git_seam.py", "schema/external_qa_context.schema.json", "schema/external_evidence_admission.schema.json")}
        if not needed <= selected_tools:
            raise ee.ExternalEvidenceError("external QA manifest omits active bridge/schema inputs", code="qa_unassessed_bridge")
        qa = json.loads(bound(context["qa_ref"]))
        for row in qa.get("checks", []):
            capture = json.loads(bound(row["capture"]))
            if capture.get("producer") != expected_producer:
                raise ee.ExternalEvidenceError("external QA capture producer mismatch", code="qa_producer_mismatch")
            for stream in ("stdout", "stderr"):
                bound(capture[stream])
        status = envelope["status_separation"]
        if status["execution_status"] != "completed":
            raise ee.ExternalEvidenceError("external QA execution unsettled; retain the existing permit", code="unsettled_external_execution")
        if status["test_outcome"] != "passed" or status["admission_decision"] != "admitted":
            # Completed failures settle in the same generic ledger and grant no
            # typed completion credit. Unknown execution remains unsettled above.
            return None
        wa._validate_qa_proof_core(root, qa, feature_id=expected_feature_id,
            candidate=expected_candidate, required_checks=checks)
        return {"mapping_id": MAPPING_ID, "feature_id": expected_feature_id,
            "candidate_sha256": candidate_digest, "qa_sha256": ee.sha256_hex(ee.canonical_json_bytes(qa)),
            "required_checks_sha256": checks_digest, "execution_identity_sha256": execution_digest,
            "producer": copy.deepcopy(expected_producer), "context_ref": copy.deepcopy(context_ref),
            "candidate_ref": copy.deepcopy(context["candidate_ref"]), "qa_ref": copy.deepcopy(context["qa_ref"]),
            "artifact_modes": copy.deepcopy(context["artifact_modes"])}
    except ee.ExternalEvidenceError:
        raise
    except (wa.AssuranceError, jsonschema.ValidationError, OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ee.ExternalEvidenceError("external native QA proof invalid: " + str(exc), code="invalid_qa_mapping") from exc


def admit_external_qa(repo_root, envelope, *, context_ref, expected_feature_id,
        expected_candidate, required_checks, expected_execution_identity,
        expected_producer, admission_expectations):
    """Authenticate, interpret and record observations; completion stays separate."""
    digest = ee.sha256_hex(ee.canonical_json_bytes(expected_candidate))
    if admission_expectations.get("expected_candidate_sha256") != digest:
        raise ee.ExternalEvidenceError("host admission digest differs from assessed native candidate", code="qa_host_binding_mismatch")
    request = dict(context_ref=context_ref, expected_feature_id=expected_feature_id,
        expected_candidate=expected_candidate, required_checks=required_checks,
        expected_execution_identity=expected_execution_identity, expected_producer=expected_producer)
    result = ee.admit_external_evidence(repo_root, envelope, **dict(admission_expectations), _qa_request=request)
    return dict(result, qa_mapping=result.get("qa_mapping"), completion_status="not_advanced")
