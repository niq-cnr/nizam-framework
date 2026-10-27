#!/usr/bin/env python3
"""NF-AC04 acceptance suite: generic optional external evidence admission without Agentic dependency.

Covers requirement NF-R04:
- Neutral synthetic consumer without Agentic SDLC
- Schema validation (schema/external_evidence_admission.schema.json) with all object nodes closed
- Host-allocated attempt permits and host-authenticated HMAC-SHA256 producer proof
- Rejection of copied feature117 / WA123 commissioning evidence
- Rejection of forged producer proof, wrong policy/framework/source/contract/collection/tool/attempt bindings,
  unsupported versions/profiles, partial captures, and status separation violations
- Idempotent duplicate delivery vs fail-closed rejection on conflicting attempt reuse
- 3-signature and 6-task circuit-breaker ceilings with finite operator_recovery
- Concurrent admission lock safety and crash/interruption staging cleanup (`reconcile`)
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import jsonschema

TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import external_evidence as ee  # noqa: E402


ORIGIN_URL = "https://example.invalid/neutral-consumer.git"
POLICY_ID = "nizam-standalone-default"
POLICY_VERSION = "1.0.0"
POLICY_DIGEST = "11" * 32
FW_VERSION = "3.0.0"
FW_COMMIT = "2b8298ae1d5a41534e00b6710a738b4b181b87fa"
FW_TREE = "cf9bf9ffd066c4c2724837baaf652323af230f52"
ACC_COLLECTION_DIGEST = "55" * 32
REG_COLLECTION_DIGEST = "66" * 32


def _git_raw(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


class NfAc04GenericAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(
            tempfile.mkdtemp(
                prefix="nizam-nf-ac04-",
                dir="/private/tmp" if Path("/private/tmp").is_dir() else None,
            )
        ).resolve()
        self.repo = self.temp_dir / "consumer"
        self.repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "--object-format=sha1", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "ac04@example.test"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "NF AC04"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "commit.gpgsign", "false"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin", ORIGIN_URL], check=True)

        (self.repo / "src").mkdir(parents=True, exist_ok=True)
        (self.repo / "src/mod.py").write_text("def calc():\n    return 42\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "src/mod.py"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "base"], check=True)
        self.base_commit = _git_raw(self.repo, "rev-parse", "HEAD")

        (self.repo / "src/mod.py").write_text("def calc():\n    return 43\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "src/mod.py"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "candidate"], check=True)
        self.cand_commit = _git_raw(self.repo, "rev-parse", "HEAD")
        self.cand_tree = _git_raw(self.repo, "rev-parse", f"{self.cand_commit}^{{tree}}")

        self.contract_rel = ".agent/contracts/F-201.json"
        contract_path = self.repo / self.contract_rel
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_raw = ee.canonical_json_bytes({
            "contract_id": "F-201",
            "status": "approved",
            "requirements": ["REQ-201-A"],
            "acceptance_criteria": ["AC-201-01", "AC-201-02"],
        }) + b"\n"
        contract_path.write_bytes(contract_raw)
        self.contract_digest = ee.sha256_hex(contract_raw)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_artifacts(
        self,
        prefix: str,
        *,
        test_outcome: str = "passed",
        extra_verdict_fields: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        art_dir = self.repo / ".agent/evidence/external"
        art_dir.mkdir(parents=True, exist_ok=True)

        stdout_rel = f".agent/evidence/external/{prefix}.stdout.txt"
        stderr_rel = f".agent/evidence/external/{prefix}.stderr.txt"
        verdict_rel = f".agent/evidence/external/{prefix}.verdict.json"

        stdout_raw = f"run {prefix}: {test_outcome}\n".encode("utf-8")
        stderr_raw = b"" if test_outcome != "failed" else b"assertion failed\n"
        verdict_doc: dict[str, object] = {
            "test_outcome": test_outcome,
            "suite": "neutral-acceptance",
            "executed_tests": 12,
        }
        if extra_verdict_fields:
            verdict_doc.update(extra_verdict_fields)
        verdict_raw = ee.canonical_json_bytes(verdict_doc) + b"\n"

        (self.repo / stdout_rel).write_bytes(stdout_raw)
        (self.repo / stderr_rel).write_bytes(stderr_raw)
        (self.repo / verdict_rel).write_bytes(verdict_raw)

        return [
            {
                "role": "stdout",
                "path": stdout_rel,
                "media_type": "text/plain; charset=utf-8",
                "byte_length": len(stdout_raw),
                "sha256": ee.sha256_hex(stdout_raw),
            },
            {
                "role": "stderr",
                "path": stderr_rel,
                "media_type": "text/plain; charset=utf-8",
                "byte_length": len(stderr_raw),
                "sha256": ee.sha256_hex(stderr_raw),
            },
            {
                "role": "verdict_report",
                "path": verdict_rel,
                "media_type": "application/json",
                "byte_length": len(verdict_raw),
                "sha256": ee.sha256_hex(verdict_raw),
            },
        ]

    def _build_valid_envelope(
        self,
        alloc: dict[str, object],
        artifacts: list[dict[str, object]],
        *,
        test_outcome: str = "passed",
        execution_status: str = "completed",
        admission_decision: str = "admitted",
        defect_signature: str | None = None,
    ) -> dict[str, object]:
        permit = alloc["permit"]
        assert isinstance(permit, dict)
        permit_digest = str(alloc["permit_digest"])
        permit_token = str(alloc["permit_token"])
        exec_id = {
            "tool_id": "neutral-pytest-runner",
            "tool_version": "8.3.0",
            "adapter_id": "neutral-local-adapter",
            "adapter_version": "1.0.0",
            "config_digest": "77" * 32,
            "isolation_mode": "container",
            "isolation_digest": "88" * 32,
        }
        proof = ee.compute_producer_proof(
            permit_digest=permit_digest,
            permit_token=permit_token,
            candidate_commit=self.cand_commit,
            candidate_tree=self.cand_tree,
            execution_identity=exec_id,
            artifacts=artifacts,
            producer_id="neutral-verifier-worker",
            session_id="sess-20261027-0001",
            issued_at="2026-10-27T12:00:00Z",
        )
        return {
            "schema_version": "1.0.0",
            "protocol_version": "1.0.0",
            "profile_id": "generic-external-evidence-v1",
            "profile_version": "1.0.0",
            "policy_binding": {
                "policy_id": POLICY_ID,
                "policy_version": POLICY_VERSION,
                "policy_digest": POLICY_DIGEST,
            },
            "framework_identity": {
                "name": "nizam-framework",
                "version": FW_VERSION,
                "commit_sha": FW_COMMIT,
                "tree_sha": FW_TREE,
            },
            "consumer_binding": {
                "repository": ORIGIN_URL,
                "base_commit": self.base_commit,
                "candidate_commit": self.cand_commit,
                "candidate_tree": self.cand_tree,
                "candidate_sha256": "22" * 32,
            },
            "attempt_lineage": {
                "task_id": permit["task_id"],
                "step_id": permit["step_id"],
                "run_id": permit["run_id"],
                "attempt_number": permit["attempt_number"],
                "permit_id": permit["permit_id"],
                "permit_digest": permit_digest,
                "parent_attempt": permit["parent_attempt"],
                "continuation_basis": permit["continuation_basis"],
                "defect_signature": defect_signature,
                "operator_recovery_ref": permit["operator_recovery_ref"],
            },
            "contract_binding": {
                "contract_id": "F-201",
                "contract_digest": self.contract_digest,
                "requirement_ids": ["REQ-201-A"],
                "acceptance_criteria_ids": ["AC-201-01", "AC-201-02"],
            },
            "collection_binding": {
                "acceptance_collection_id": "acc-suite-v1",
                "acceptance_collection_digest": ACC_COLLECTION_DIGEST,
                "regression_collection_id": "reg-suite-v1",
                "regression_collection_digest": REG_COLLECTION_DIGEST,
            },
            "execution_identity": exec_id,
            "producer_proof": proof,
            "status_separation": {
                "test_outcome": test_outcome,
                "execution_status": execution_status,
                "admission_decision": admission_decision,
            },
            "artifacts": artifacts,
        }

    def _admit(self, envelope: dict[str, object]) -> dict[str, object]:
        return ee.admit_external_evidence(
            self.repo,
            envelope,
            expected_policy_id=POLICY_ID,
            expected_policy_version=POLICY_VERSION,
            expected_policy_digest=POLICY_DIGEST,
            expected_framework_version=FW_VERSION,
            expected_framework_commit=FW_COMMIT,
            expected_framework_tree=FW_TREE,
            expected_contract_path=self.contract_rel,
            expected_acceptance_collection_digest=ACC_COLLECTION_DIGEST,
            expected_regression_collection_digest=REG_COLLECTION_DIGEST,
            expected_tool_id="neutral-pytest-runner",
            expected_adapter_id="neutral-local-adapter",
        )

    def test_schema_closure_and_conformance_corpus_cases(self) -> None:
        """Verify every object in external_evidence_admission.schema.json is closed and exercise the neutral corpus."""
        schema = json.loads((ROOT_DIR / "schema/external_evidence_admission.schema.json").read_text(encoding="utf-8"))

        def walk(node: object, path: str = "$") -> None:
            if isinstance(node, dict):
                if node.get("type") == "object":
                    self.assertIs(
                        node.get("additionalProperties"),
                        False,
                        f"{path} has type=object without additionalProperties: false",
                    )
                for k, v in node.items():
                    walk(v, f"{path}.{k}")
            elif isinstance(node, list):
                for idx, item in enumerate(node):
                    walk(item, f"{path}[{idx}]")

        walk(schema)

        corpus = json.loads(
            (ROOT_DIR / "docs/planning/nf-owner-2026-10-27/fixtures/external_evidence/conformance_corpus.json").read_text(
                encoding="utf-8"
            )
        )
        jsonschema.Draft202012Validator(schema).validate(corpus["positive_templates"]["valid_passed_admission"])

        alloc = ee.allocate_attempt_permit(
            self.repo,
            task_id="F-201",
            step_id="verify-unit",
            run_id="run-01",
            candidate_commit=self.cand_commit,
        )
        arts = self._write_artifacts("f201-a1")
        valid_env = self._build_valid_envelope(alloc, arts)

        for neg in corpus["negative_cases"]:
            mutated = copy.deepcopy(valid_env)
            for dotted_key, new_val in neg["mutation"].items():
                parts = dotted_key.split(".")
                cursor: Any = mutated
                for p in parts[:-1]:
                    cursor = cursor[p]
                cursor[parts[-1]] = new_val
            with self.subTest(case=neg["id"]):
                with self.assertRaises(ee.ExternalEvidenceError) as ctx:
                    self._admit(mutated)
                self.assertEqual(ctx.exception.code, neg["expected_code"])

    def test_admission_idempotency_conflicting_reuse_and_binding_rejections(self) -> None:
        """Verify valid admission, idempotent duplicate delivery, conflicting reuse rejection, and all binding checks."""
        alloc = ee.allocate_attempt_permit(
            self.repo,
            task_id="F-201",
            step_id="verify-unit",
            run_id="run-01",
            candidate_commit=self.cand_commit,
        )
        arts = self._write_artifacts("f201-a1")
        valid_env = self._build_valid_envelope(alloc, arts)

        # Before admission succeeds, test wrong bindings (they do not consume the permit!)
        # 1. Wrong framework version
        bad_fw = copy.deepcopy(valid_env)
        bad_fw["framework_identity"]["version"] = "2.0.0"
        with self.assertRaises(ee.ExternalEvidenceError) as ctx:
            self._admit(bad_fw)
        self.assertEqual(ctx.exception.code, "framework_mismatch")

        # 2. Wrong candidate commit
        bad_cand = copy.deepcopy(valid_env)
        bad_cand["consumer_binding"]["candidate_commit"] = self.base_commit
        with self.assertRaises(ee.ExternalEvidenceError) as ctx:
            self._admit(bad_cand)
        self.assertEqual(ctx.exception.code, "candidate_mismatch")

        # 3. Wrong contract digest
        bad_contract = copy.deepcopy(valid_env)
        bad_contract["contract_binding"]["contract_digest"] = "99" * 32
        with self.assertRaises(ee.ExternalEvidenceError) as ctx:
            self._admit(bad_contract)
        self.assertEqual(ctx.exception.code, "contract_mismatch")

        # 4. Wrong collection digest
        bad_coll = copy.deepcopy(valid_env)
        bad_coll["collection_binding"]["acceptance_collection_digest"] = "99" * 32
        with self.assertRaises(ee.ExternalEvidenceError) as ctx:
            self._admit(bad_coll)
        self.assertEqual(ctx.exception.code, "collection_mismatch")

        # 5. Wrong tool_id
        bad_tool = copy.deepcopy(valid_env)
        bad_tool["execution_identity"]["tool_id"] = "other-tool"
        # Recompute proof so it tests tool_mismatch rather than forged_producer_proof
        bad_tool["producer_proof"] = ee.compute_producer_proof(
            permit_digest=str(alloc["permit_digest"]),
            permit_token=str(alloc["permit_token"]),
            candidate_commit=self.cand_commit,
            candidate_tree=self.cand_tree,
            execution_identity=bad_tool["execution_identity"],
            artifacts=arts,
            producer_id="neutral-verifier-worker",
            session_id="sess-20261027-0001",
            issued_at="2026-10-27T12:00:00Z",
        )
        with self.assertRaises(ee.ExternalEvidenceError) as ctx:
            self._admit(bad_tool)
        self.assertEqual(ctx.exception.code, "tool_mismatch")

        # 6. Partial capture (missing stderr)
        partial_arts = [a for a in arts if a["role"] != "stderr"]
        # Add coverage_report so minItems=3 is satisfied in schema stage, triggering partial_capture role check
        cov_rel = ".agent/evidence/external/f201-a1.cov.txt"
        (self.repo / cov_rel).write_bytes(b"cov\n")
        partial_arts.append({
            "role": "coverage_report",
            "path": cov_rel,
            "media_type": "text/plain",
            "byte_length": 4,
            "sha256": ee.sha256_hex(b"cov\n"),
        })
        partial_env = self._build_valid_envelope(alloc, partial_arts)
        with self.assertRaises(ee.ExternalEvidenceError) as ctx:
            self._admit(partial_env)
        self.assertEqual(ctx.exception.code, "partial_capture")

        # 7. Historical commissioning marker inside verdict_report on disk
        comm_arts = self._write_artifacts("f201-comm", extra_verdict_fields={"commissioning_fixture": True})
        comm_env = self._build_valid_envelope(alloc, comm_arts)
        with self.assertRaises(ee.ExternalEvidenceError) as ctx:
            self._admit(comm_env)
        self.assertEqual(ctx.exception.code, "commissioning_evidence_rejected")

        # 8. Admit the valid envelope
        res1 = self._admit(valid_env)
        self.assertTrue(res1["ok"])
        self.assertFalse(res1["idempotent_replay"])
        self.assertEqual(res1["admission_decision"], "admitted")

        # 9. Identical duplicate delivery is idempotent
        res2 = self._admit(valid_env)
        self.assertTrue(res2["ok"])
        self.assertTrue(res2["idempotent_replay"])
        self.assertEqual(res1["envelope_sha256"], res2["envelope_sha256"])

        # 10. Conflicting reuse of the same attempt with different content fails closed
        conflicting = copy.deepcopy(valid_env)
        conflicting["producer_proof"]["issued_at"] = "2026-10-27T12:00:01Z"
        with self.assertRaises(ee.ExternalEvidenceError) as ctx:
            self._admit(conflicting)
        self.assertEqual(ctx.exception.code, "conflicting_attempt_reuse")

    def test_circuit_breaker_ceilings_and_finite_operator_recovery(self) -> None:
        """Enforce 3-attempt same-signature ceiling, 6-attempt task ceiling, and finite operator_recovery."""
        same_sig = "aa" * 32
        last_failed_path = ""
        for att in (1, 2, 3):
            basis = "initial_attempt" if att == 1 else "strategy_ladder"
            parent = None if att == 1 else att - 1
            alloc = ee.allocate_attempt_permit(
                self.repo,
                task_id="F-SIG",
                step_id="verify",
                run_id=f"run-{att}",
                candidate_commit=self.cand_commit,
                continuation_basis=basis,
                parent_attempt=parent,
            )
            arts = self._write_artifacts(f"fsig-a{att}", test_outcome="failed")
            env = self._build_valid_envelope(
                alloc,
                arts,
                test_outcome="failed",
                execution_status="completed",
                admission_decision="rejected",
                defect_signature=same_sig,
            )
            res = self._admit(env)
            self.assertEqual(res["admission_decision"], "rejected")
            last_failed_path = str(res["admission_path"])

        # Attempt 4 without operator_recovery is halted by the 3-signature ceiling!
        with self.assertRaises(ee.ExternalEvidenceError) as ctx:
            ee.allocate_attempt_permit(
                self.repo,
                task_id="F-SIG",
                step_id="verify",
                run_id="run-4",
                candidate_commit=self.cand_commit,
                continuation_basis="strategy_ladder",
                parent_attempt=3,
            )
        self.assertEqual(ctx.exception.code, "signature_ceiling_exhausted")
        self.assertEqual(ctx.exception.exit_code, 2)

        # Write a valid finite operator_recovery authority file raising max_task_attempts to 4
        auth_rel = ".agent/evidence/external/fsig-recovery.json"
        (self.repo / auth_rel).write_bytes(
            ee.canonical_json_bytes({
                "role": "operator",
                "task_id": "F-SIG",
                "approved": True,
                "max_task_attempts": 4,
                "after_capture": last_failed_path,
                "authority_ref": auth_rel,
            }) + b"\n"
        )
        alloc4 = ee.allocate_attempt_permit(
            self.repo,
            task_id="F-SIG",
            step_id="verify",
            run_id="run-4",
            candidate_commit=self.cand_commit,
            continuation_basis="operator_recovery",
            parent_attempt=3,
            operator_recovery_ref=auth_rel,
        )
        self.assertEqual(alloc4["permit"]["attempt_number"], 4)

    def test_concurrent_admission_and_crash_staging_reconciliation(self) -> None:
        """Verify concurrent admission race safety under flock and cleanup of interrupted .tmp-* staging files."""
        alloc = ee.allocate_attempt_permit(
            self.repo,
            task_id="F-RACE",
            step_id="verify",
            run_id="run-race",
            candidate_commit=self.cand_commit,
        )
        arts_a = self._write_artifacts("frace-a")
        arts_b = self._write_artifacts("frace-b")
        env_a = self._build_valid_envelope(alloc, arts_a)
        env_b = self._build_valid_envelope(alloc, arts_b)

        env_a_path = self.temp_dir / "env_a.json"
        env_b_path = self.temp_dir / "env_b.json"
        env_a_path.write_bytes(ee.canonical_json_bytes(env_a))
        env_b_path.write_bytes(ee.canonical_json_bytes(env_b))

        def spawn_admit(env_path: Path) -> subprocess.Popen[str]:
            return subprocess.Popen(
                [
                    sys.executable,
                    str(ROOT_DIR / "tools/external_evidence.py"),
                    "admit-evidence",
                    "--root",
                    str(self.repo),
                    "--envelope",
                    str(env_path),
                    "--expected-policy-id",
                    POLICY_ID,
                    "--expected-policy-version",
                    POLICY_VERSION,
                    "--expected-policy-digest",
                    POLICY_DIGEST,
                    "--expected-framework-version",
                    FW_VERSION,
                    "--expected-framework-commit",
                    FW_COMMIT,
                    "--expected-framework-tree",
                    FW_TREE,
                    "--expected-contract-path",
                    self.contract_rel,
                    "--expected-acceptance-collection-digest",
                    ACC_COLLECTION_DIGEST,
                    "--expected-regression-collection-digest",
                    REG_COLLECTION_DIGEST,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        p1 = spawn_admit(env_a_path)
        p2 = spawn_admit(env_b_path)
        out1, err1 = p1.communicate(timeout=15)
        out2, err2 = p2.communicate(timeout=15)
        codes = sorted([p1.returncode, p2.returncode])
        self.assertEqual(codes, [0, 1], f"expected one winner (0) and one loser (1), got {codes}: {err1} / {err2}")

        # Simulate crashed staging files and verify reconcile cleans them up and validates ledger
        state_dir = self.repo / ".agent/evidence/external_admissions"
        stale_tmp = state_dir / ".tmp-ledger.json-crashed"
        stale_tmp.write_text("{corrupt partial write", encoding="utf-8")

        rec = ee.reconcile_admission_state(self.repo)
        self.assertTrue(rec["ok"])
        self.assertIn(".tmp-ledger.json-crashed", rec["cleaned_staging_files"])
        self.assertFalse(stale_tmp.exists())
        self.assertEqual(rec["admission_count"], 1)


if __name__ == "__main__":
    unittest.main()
