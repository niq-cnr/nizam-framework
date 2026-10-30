#!/usr/bin/env python3
"""Independent neutral regression for external/native authority separation.

These are synthetic authority fixtures with real local proof captures. Generic
HMAC admission alone must never establish native typed QA or completion.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import external_evidence as ee
import start_path
import test_nf_ac04_generic_admission as generic
from test_workflow_assurance import ReceiptFixture, load_api, git


class ExternalQaAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.generic = generic.NfAc04GenericAdmissionTests(methodName="runTest")
        self.generic.setUp(); self.addCleanup(self.generic.tearDown)
        self.root = self.generic.repo

    def allocate(self, task="bridge-task"):
        return ee.allocate_attempt_permit(self.root, task_id=task, step_id="verify",
            run_id="neutral-run", candidate_commit=git(self.root, "rev-parse", "HEAD"))

    def test_native_reservation_prevents_external_first_reservation(self):
        start_path._reserve_attempt(self.root, "bridge-task", "verify", 1)
        marker = self.root / ".agent/evidence/bridge-task-verify-attempt1.reservation.json"
        original = marker.read_bytes()
        with self.assertRaises(ee.ExternalEvidenceError):
            self.allocate()
        self.assertEqual(marker.read_bytes(), original)

    def test_external_reservation_prevents_native_first_reservation(self):
        self.allocate()
        ledger = self.root / ".agent/evidence/external_admissions/ledger.json"
        original = ledger.read_bytes()
        with self.assertRaises(start_path.StartPathError):
            start_path._reserve_attempt(self.root, "bridge-task", "verify", 1)
        self.assertEqual(ledger.read_bytes(), original)
        self.assertFalse((self.root / ".agent/evidence/bridge-task-verify-attempt1.reservation.json").exists())

    def test_actual_concurrent_native_external_first_reservations_have_only_one_winner(self):
        ready = [self.generic.temp_dir / "native-ready", self.generic.temp_dir / "external-ready"]
        code = """import json,pathlib,sys,time
sys.path.insert(0,sys.argv[1])
import start_path,external_evidence
root=pathlib.Path(sys.argv[2]);kind=sys.argv[3]
pathlib.Path(sys.argv[4]).write_text('ready')
deadline=time.monotonic()+5
while not pathlib.Path(sys.argv[5]).exists() and time.monotonic()<deadline:time.sleep(.005)
try:
 if kind=='native':start_path._reserve_attempt(root,'bridge-task','verify',1)
 else:external_evidence.allocate_attempt_permit(root,task_id='bridge-task',step_id='verify',run_id='neutral-run',candidate_commit=sys.argv[6])
 print(json.dumps({'reserved':True,'kind':kind}))
except Exception as exc:print(json.dumps({'reserved':False,'kind':kind,'error':str(exc)}))
"""
        processes = []
        for index, kind in enumerate(("native", "external")):
            processes.append(subprocess.Popen([sys.executable, "-c", code,
                str(Path(__file__).parent), str(self.root), kind, str(ready[index]),
                str(ready[1-index]), git(self.root, "rev-parse", "HEAD")],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        try:
            results = []
            for process in processes:
                stdout, stderr = process.communicate(timeout=20)
                self.assertEqual(process.returncode, 0, stderr)
                results.append(json.loads(stdout))
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill(); process.wait()
        self.assertTrue(all(path.exists() for path in ready), "both actual contenders must run")
        self.assertEqual(sum(result["reserved"] for result in results), 1, results)

    def test_generic_admission_cannot_satisfy_public_native_qa_or_receipt_completion(self):
        with patch.dict(os.environ, {"NIZAM_WA120_FIXTURE": "observed"}), tempfile.TemporaryDirectory(prefix="external-native-proof-") as directory:
            fixture = ReceiptFixture(load_api(), directory)
            root = fixture.root
            entry = next(row for row in fixture.policy["prerequisites"] if row["kind"] == "fresh-qa")
            verdict = json.loads(subprocess.check_output(["git", "-C", str(root), "show",
                entry["artifact"]["revision"] + ":" + entry["artifact"]["path"]]))
            checks = [fixture.qa_check]
            # Positive controls: genuine current typed proof and receipt work.
            fixture.api.validate_qa_proof(root, verdict, feature_id="120", candidate=fixture.candidate, required_checks=checks)
            self.assertEqual(fixture.api.plan_receipt_transition(root, fixture.state,
                fixture.receipt, policy=fixture.policy)["action"], "advance")
            helper = self.generic
            contract = (helper.repo / helper.contract_rel).read_bytes()
            helper.repo = root
            (root / helper.contract_rel).parent.mkdir(parents=True, exist_ok=True)
            (root / helper.contract_rel).write_bytes(contract)
            helper.cand_commit = git(root, "rev-parse", "HEAD")
            helper.base_commit = helper.cand_commit
            helper.cand_tree = git(root, "rev-parse", "HEAD^{tree}")
            allocation = ee.allocate_attempt_permit(root, task_id="120", step_id="verify",
                run_id="neutral-proof", candidate_commit=helper.cand_commit)
            envelope = helper._build_valid_envelope(allocation, helper._write_artifacts("generic-only"))
            envelope["consumer_binding"]["repository"] = fixture.repository
            proof = envelope["producer_proof"]
            envelope["producer_proof"] = ee.compute_producer_proof(envelope_binding=envelope,
                permit_digest=allocation["permit_digest"], permit_token=allocation["permit_token"],
                candidate_commit=helper.cand_commit, candidate_tree=helper.cand_tree,
                execution_identity=envelope["execution_identity"], artifacts=envelope["artifacts"],
                producer_id=proof["producer_id"], session_id=proof["session_id"], issued_at=proof["issued_at"])
            admitted = helper._admit(envelope)
            self.assertIs(admitted["ok"], True, "fixture must genuinely admit generic envelope")
            self.assertEqual(admitted["admission_decision"], "admitted")
            original_state = copy.deepcopy(fixture.state)
            operations = {
                "public-native-QA": lambda: fixture.api.validate_qa_proof(root, verdict,
                    feature_id="120", candidate=fixture.candidate, required_checks=checks),
                "public-receipt-completion": lambda: fixture.api.plan_receipt_transition(root,
                    fixture.state, fixture.receipt, policy=fixture.policy),
            }
            for name, operation in operations.items():
                with self.subTest(consumer=name), self.assertRaises(fixture.api.AssuranceError):
                    operation()
            self.assertEqual(fixture.state, original_state, "unmapped admission cannot advance state")


class ReservationNamespaceCompatibilityTests(unittest.TestCase):
    """Independent actual-process compatibility and stable-namespace regressions."""
    def clean_environment(self, directory):
        env = {key: os.environ[key] for key in ("PATH", "LANG", "SYSTEMROOT") if key in os.environ}
        for key in ("HOME", "TMPDIR", "XDG_RUNTIME_DIR"):
            value = directory / key.lower(); value.mkdir(parents=True)
            env[key] = str(value)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return env

    def test_public_unbound_capture_still_works_without_git_initialization(self):
        with tempfile.TemporaryDirectory(prefix="bridge-nongit-public-") as directory:
            base = Path(directory); root = base / "project"; root.mkdir()
            result = subprocess.run([sys.executable, str(Path(start_path.__file__).resolve()),
                "capture", "--root", str(root), "--id", "compat-nongit", "--step", "verify",
                "--attempt", "1", "--output-dir", str(root / ".agent/evidence/capture"),
                "--", sys.executable, "-c", "print('actual-unbound-capture')"],
                env=self.clean_environment(base / "ambient"), capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            capture = json.loads(result.stdout)
            self.assertEqual(capture["binding_state"], "unbound")
            self.assertEqual(capture["outcome"], "success")
            self.assertEqual((root / capture["stdout"]["path"]).read_text().strip(), "actual-unbound-capture")
            self.assertFalse((root / ".git").exists(), "capture must not initialize Git implicitly")

    def test_native_external_lock_survives_git_init_and_ambient_path_changes(self):
        import time
        native_code = r"""import contextlib,json,pathlib,sys,time
sys.path.insert(0,sys.argv[1]);import start_path
root=pathlib.Path(sys.argv[2]); ready=pathlib.Path(sys.argv[3]); release=pathlib.Path(sys.argv[4])
original=start_path._task_reservation_lock
@contextlib.contextmanager
def observed_lock(root,task):
 with original(root,task):
  ready.write_text('actual-lock-acquired')
  deadline=time.monotonic()+15
  while not release.exists():
   if time.monotonic()>deadline:raise RuntimeError('release deadline')
   time.sleep(.01)
  yield
start_path._task_reservation_lock=observed_lock
try:
 start_path._reserve_attempt(root,'compat-reservation','verify',1)
 print(json.dumps({'reserved':True}))
except Exception as exc:print(json.dumps({'reserved':False,'error':str(exc)}))
"""
        external_code = r"""import json,pathlib,sys
sys.path.insert(0,sys.argv[1]);import external_evidence
pathlib.Path(sys.argv[3]).write_text('actual-external-call-starting')
try:
 external_evidence.allocate_attempt_permit(pathlib.Path(sys.argv[2]),task_id='compat-reservation',step_id='verify',run_id='external-contender',candidate_commit=sys.argv[4])
 print(json.dumps({'reserved':True}))
except Exception as exc:print(json.dumps({'reserved':False,'error':str(exc)}))
"""
        for initialize_before_lock in (False, True):
            with self.subTest(git_initialized_before_lock=initialize_before_lock), tempfile.TemporaryDirectory(prefix="bridge-namespace-race-") as directory:
                base=Path(directory); root=base/"project"; root.mkdir(); (root/"source.txt").write_text("private source\n")
                def initialize():
                    for args in (("init",), ("config","user.name","Private fixture"),
                                 ("config","user.email","private@example.invalid"),
                                 ("add","source.txt"), ("commit","-m","private fixture")):
                        subprocess.run(["git","-C",str(root),*args],check=True,capture_output=True)
                if initialize_before_lock: initialize()
                ready=base/"native-ready"; release=base/"release"; external_ready=base/"external-ready"
                native=subprocess.Popen([sys.executable,"-c",native_code,str(Path(__file__).resolve().parent),
                    str(root),str(ready),str(release)],env=self.clean_environment(base/"native-ambient"),
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                external=None
                try:
                    deadline=time.monotonic()+5
                    while not ready.exists() and native.poll() is None and time.monotonic()<deadline: time.sleep(.01)
                    if not ready.exists():
                        out,err=native.communicate(timeout=2)
                        self.fail("native must acquire actual reservation lock before Git init: "+out+err)
                    if not initialize_before_lock: initialize()
                    candidate=git(root,"rev-parse","HEAD")
                    external=subprocess.Popen([sys.executable,"-c",external_code,str(Path(__file__).resolve().parent),
                        str(root),str(external_ready),candidate],env=self.clean_environment(base/"external-ambient"),
                        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                    deadline=time.monotonic()+5
                    while not external_ready.exists() and external.poll() is None and time.monotonic()<deadline: time.sleep(.01)
                    self.assertTrue(external_ready.exists(), "external contender must really start")
                    time.sleep(.2)
                    self.assertIsNone(external.poll(), "external contender must wait on same actual lock despite Git init and ambient paths")
                    release.write_text("release")
                    native_out,native_err=native.communicate(timeout=10)
                    external_out,external_err=external.communicate(timeout=10)
                    self.assertEqual(native.returncode,0,native_err); self.assertEqual(external.returncode,0,external_err)
                    self.assertIs(json.loads(native_out)["reserved"],True,native_out)
                    self.assertIs(json.loads(external_out)["reserved"],False,external_out)
                    marker=root/".agent/evidence/compat-reservation-verify-attempt1.reservation.json"
                    self.assertTrue(marker.is_file(), "native winner retains real attempt authority")
                    ledger=root/".agent/evidence/external_admissions/ledger.json"
                    if ledger.exists(): self.assertNotIn("compat-reservation",json.loads(ledger.read_bytes())["tasks"])
                finally:
                    release.write_text("release")
                    for process in (native,external):
                        if process is not None and process.poll() is None:
                            process.kill(); process.wait()


class ExternalQaMappingTests(unittest.TestCase):
    """Actual native proof, authenticated projection, and durable replay integration."""
    def setUp(self):
        import importlib.util
        self.environment = patch.dict(os.environ, {"NIZAM_WA120_FIXTURE": "observed"})
        self.environment.start(); self.addCleanup(self.environment.stop)
        self.directory = tempfile.TemporaryDirectory(prefix="external-qa-mapping-")
        self.addCleanup(self.directory.cleanup)
        self.fixture = f = ReceiptFixture(load_api(), self.directory.name)
        self.root = f.root
        source = Path(__file__).resolve().parent
        extras = ["tools/external_qa.py", "tools/external_evidence.py", "tools/git_seam.py",
            "schema/external_qa_context.schema.json", "schema/external_evidence_admission.schema.json"]
        for path in extras:
            f.write(path, (source.parent / path).read_bytes())
        f.inputs["tools"] += extras
        f.producer = {"agent_id": "neutral-controller", "session_id": "neutral-session"}
        f.candidate_revision = f.commit("assessed canonical bridge inputs")
        f.candidate = f.api.assess_repository(self.root, f.candidate_revision, f.inputs,
            list(f.candidate["environment"]["variables"]), {"record.json": ["/status", "/updated_at", "/history"]})
        f.policy["candidate"] = copy.deepcopy(f.candidate)
        f.policy["producer"] = copy.deepcopy(f.producer)
        f.make_qa_proof(); f.capture = f.actual_capture("success"); f.set_capture(f.capture)
        f.set_stage("feature-complete")
        name = "test_external_qa_" + ee.sha256_hex(str(self.root).encode())
        spec = importlib.util.spec_from_file_location(name, self.root / "tools/external_qa.py")
        self.api = importlib.util.module_from_spec(spec); sys.modules[name] = self.api; spec.loader.exec_module(self.api)
        self.generic = generic.NfAc04GenericAdmissionTests(methodName="runTest")
        self.generic.setUp(); self.addCleanup(self.generic.tearDown)
        helper = self.generic
        raw = (helper.repo / helper.contract_rel).read_bytes(); helper.repo = self.root
        (self.root / helper.contract_rel).parent.mkdir(parents=True, exist_ok=True)
        (self.root / helper.contract_rel).write_bytes(raw)
        helper.base_commit = helper.cand_commit = git(self.root, "rev-parse", "HEAD")
        helper.cand_tree = git(self.root, "rev-parse", "HEAD^{tree}")
        self.allocation = self.api.ee.allocate_attempt_permit(self.root, task_id="120", step_id="verify",
            run_id="neutral-native-proof", candidate_commit=helper.cand_commit)
        self.artifacts = helper._write_artifacts("native-mapping")
        self.qa_ref = next(row for row in f.policy["prerequisites"] if row["kind"] == "fresh-qa")["artifact"]
        self.qa = json.loads(f.api._qa_artifact(self.root, self.qa_ref))
        refs = [self.qa_ref, self.qa["candidate_ref"], f.contract, f.ref("tools/external_qa.py", f.candidate_revision)]
        for row in self.qa["checks"]:
            refs.append(row["capture"])
            cap = json.loads(f.api._qa_artifact(self.root, row["capture"]))
            refs += [cap[stream] for stream in ("stdout", "stderr")]
        seen = {row["path"] for row in self.artifacts}
        for ref in refs:
            if ref["path"] not in seen:
                raw = (self.root / ref["path"]).read_bytes()
                self.artifacts.append(dict(role="trace_bundle", path=ref["path"], media_type="application/octet-stream",
                    byte_length=len(raw), sha256=ee.sha256_hex(raw)))
                seen.add(ref["path"])
        self.envelope = helper._build_valid_envelope(self.allocation, self.artifacts)
        self.envelope["consumer_binding"].update(repository=f.repository,
            candidate_sha256=ee.sha256_hex(ee.canonical_json_bytes(f.candidate)))
        self.context = dict(schema_version=1, mapping_id=self.api.MAPPING_ID, feature_id="120",
            candidate_ref=self.qa["candidate_ref"], qa_ref=self.qa_ref, host_policy_ref=f.contract,
            execution_profile_ref=refs[3], required_checks_sha256=ee.sha256_hex(ee.canonical_json_bytes([f.qa_check])),
            execution_identity_sha256=ee.sha256_hex(ee.canonical_json_bytes(self.envelope["execution_identity"])),
            producer=f.producer, artifact_modes=[dict(path=a["path"], sha256=a["sha256"], byte_length=a["byte_length"],
                mode="100755" if (self.root / a["path"]).stat().st_mode & 0o111 else "100644") for a in self.artifacts])
        self.context_ref = dict(path=".agent/evidence/external/native-context.json", sha256="", revision=None)
        self.reseal()
        self.expectations = dict(expected_candidate_sha256=self.envelope["consumer_binding"]["candidate_sha256"],
            expected_policy_id=generic.POLICY_ID, expected_policy_version=generic.POLICY_VERSION,
            expected_policy_digest=generic.POLICY_DIGEST, expected_framework_version=generic.FW_VERSION,
            expected_framework_commit=generic.FW_COMMIT, expected_framework_tree=generic.FW_TREE,
            expected_contract_path=helper.contract_rel, expected_acceptance_collection_digest=generic.ACC_COLLECTION_DIGEST,
            expected_regression_collection_digest=generic.REG_COLLECTION_DIGEST)

    def reseal(self):
        raw = ee.canonical_json_bytes(self.context)
        (self.root / self.context_ref["path"]).write_bytes(raw)
        self.context_ref["sha256"] = ee.sha256_hex(raw)
        self.envelope["artifacts"] = [a for a in self.artifacts if a["path"] != self.context_ref["path"]] + [dict(
            role="trace_bundle", path=self.context_ref["path"], sha256=ee.sha256_hex(raw), byte_length=len(raw), media_type="application/json")]
        self.envelope["producer_proof"] = self.api.ee.compute_producer_proof(envelope_binding=self.envelope,
            permit_digest=self.allocation["permit_digest"], permit_token=self.allocation["permit_token"],
            candidate_commit=self.generic.cand_commit, candidate_tree=self.generic.cand_tree,
            execution_identity=self.envelope["execution_identity"], artifacts=self.envelope["artifacts"],
            producer_id=self.fixture.producer["agent_id"], session_id=self.fixture.producer["session_id"], issued_at="2026-10-30T00:00:00Z")

    def admit(self):
        return self.api.admit_external_qa(self.root, self.envelope, context_ref=self.context_ref,
            expected_feature_id="120", expected_candidate=self.fixture.candidate, required_checks=[self.fixture.qa_check],
            expected_execution_identity=self.envelope["execution_identity"], expected_producer=self.fixture.producer,
            admission_expectations=self.expectations)

    def test_typed_mapping_admits_once_then_actual_native_receipt_advances(self):
        before = copy.deepcopy(self.fixture.state)
        admitted = self.admit()
        self.assertEqual(admitted["completion_status"], "not_advanced")
        self.assertEqual(self.fixture.state, before)
        replay = self.admit(); self.assertTrue(replay["idempotent_replay"])
        self.fixture.api.validate_qa_proof(self.root, self.qa, feature_id="120",
            candidate=self.fixture.candidate, required_checks=[self.fixture.qa_check])
        self.assertEqual(self.fixture.api.plan_receipt_transition(self.root, self.fixture.state,
            self.fixture.receipt, policy=self.fixture.policy)["action"], "advance")
        ledger = json.loads((self.root / ".agent/evidence/external_admissions/ledger.json").read_bytes())
        self.assertEqual(len(ledger["admissions"]), 1)
        self.assertEqual(ledger["tasks"]["120"]["steps"]["verify"]["allocated_attempts"], 1)

    def test_wrong_authenticated_mode_refuses_without_consuming_permit(self):
        self.context["artifact_modes"][0]["mode"] = "100755"; self.reseal()
        with self.assertRaises(self.api.ee.ExternalEvidenceError): self.admit()
        ledger = json.loads((self.root / ".agent/evidence/external_admissions/ledger.json").read_bytes())
        self.assertEqual(ledger["admissions"], {})
        self.assertFalse(next(iter(ledger["permits"].values()))["consumed"])

    def test_interrupted_ledger_publication_replays_one_typed_transition(self):
        original = self.api.ee._write_atomic_json
        def interrupt(path, value):
            if Path(path).name == "ledger.json": raise OSError("independent publication boundary")
            return original(path, value)
        with patch.object(self.api.ee, "_write_atomic_json", interrupt):
            with self.assertRaises(OSError): self.admit()
        replay = self.admit(); self.assertFalse(replay["idempotent_replay"])
        self.assertTrue(self.admit()["idempotent_replay"])
        ledger = json.loads((self.root / ".agent/evidence/external_admissions/ledger.json").read_bytes())
        self.assertEqual(len(ledger["tasks"]["120"]["history"]), 1)

    def test_native_consumption_reauthenticates_retained_envelope_without_writes(self):
        self.admit()
        ledger_path = self.root / ".agent/evidence/external_admissions/ledger.json"
        ledger = json.loads(ledger_path.read_bytes()); entry = next(iter(ledger["admissions"].values()))
        path = self.root / entry["admission_path"]; record = json.loads(path.read_bytes())
        record["envelope"]["policy_binding"]["policy_version"] = "spliced-policy"
        record["envelope_sha256"] = ee.sha256_hex(ee.canonical_json_bytes(record["envelope"]))
        entry["envelope_sha256"] = record["envelope_sha256"]
        path.write_bytes(ee.canonical_json_bytes(record)); ledger_path.write_bytes(ee.canonical_json_bytes(ledger))
        before = self.fixture.snapshot()
        with self.assertRaises(self.fixture.api.AssuranceError):
            self.fixture.api.validate_qa_proof(self.root, self.qa, feature_id="120",
                candidate=self.fixture.candidate, required_checks=[self.fixture.qa_check])
        self.assertEqual(self.fixture.snapshot(), before, "read-only consumption modified authority/evidence")

    def test_native_consumption_refuses_changed_authenticated_artifact_mode(self):
        self.admit()
        capture = json.loads(self.fixture.api._qa_artifact(self.root, self.qa["checks"][0]["capture"]))
        stream = self.root / capture["stdout"]["path"]; stream.chmod(0o755)
        with self.assertRaises(self.fixture.api.AssuranceError):
            self.fixture.api.validate_qa_proof(self.root, self.qa, feature_id="120",
                candidate=self.fixture.candidate, required_checks=[self.fixture.qa_check])

    def test_unknown_execution_holds_existing_permit_without_second_allocation(self):
        self.envelope["status_separation"].update(execution_status="interrupted", admission_decision="rejected")
        self.reseal()
        with self.assertRaises(self.api.ee.ExternalEvidenceError) as held: self.admit()
        self.assertEqual(held.exception.code, "unsettled_external_execution")
        ledger = json.loads((self.root / ".agent/evidence/external_admissions/ledger.json").read_bytes())
        self.assertEqual(ledger["admissions"], {})
        with self.assertRaises(self.api.ee.ExternalEvidenceError):
            self.api.ee.allocate_attempt_permit(self.root, task_id="120", step_id="verify",
                run_id="second-unknown-run", candidate_commit=self.generic.cand_commit,
                continuation_basis="different_strategy", parent_attempt=1)

    def test_interrupted_native_reservation_holds_external_other_step(self):
        with tempfile.TemporaryDirectory(prefix="native-reservation-hold-") as directory:
            helper = generic.NfAc04GenericAdmissionTests(methodName="runTest")
            helper.setUp()
            try:
                start_path._reserve_attempt(helper.repo, "held-task", "first-step", 1)
                with self.assertRaises(ee.ExternalEvidenceError):
                    ee.allocate_attempt_permit(helper.repo, task_id="held-task", step_id="different-step",
                        run_id="different-run", candidate_commit=helper.cand_commit)
            finally:
                helper.tearDown()

    def test_new_unsettled_permit_blocks_earlier_successful_mapping_completion(self):
        self.admit()
        self.api.ee.allocate_attempt_permit(self.root, task_id="120", step_id="verify", run_id="next-run",
            candidate_commit=self.generic.cand_commit, continuation_basis="strategy_ladder", parent_attempt=1)
        with self.assertRaises(self.fixture.api.AssuranceError):
            self.fixture.api.validate_qa_proof(self.root, self.qa, feature_id="120",
                candidate=self.fixture.candidate, required_checks=[self.fixture.qa_check])

    def test_native_optional_revision_references_remain_supported(self):
        self.context_ref.pop("revision")
        for field in ("candidate_ref", "qa_ref"):
            self.context[field] = {k: v for k, v in self.context[field].items() if k != "revision"}
        self.reseal()
        self.assertEqual(self.admit()["completion_status"], "not_advanced")

    def test_legacy_profile_refuses_without_history_or_permit_changes(self):
        path = self.root / ".agent/evidence/external_admissions/ledger.json"
        original = path.read_bytes()
        self.envelope["profile_version"] = "1.0.0"
        with self.assertRaises(self.api.ee.ExternalEvidenceError) as refused: self.admit()
        self.assertEqual(refused.exception.code, "unsupported_profile")
        self.assertEqual(path.read_bytes(), original)

    def test_pinned_prebridge_reader_refuses_new_typed_record_preserving_history(self):
        import importlib.util
        self.admit()
        ledger_path = self.root / ".agent/evidence/external_admissions/ledger.json"
        original = ledger_path.read_bytes(); ledger = json.loads(original)
        entry = next(iter(ledger["admissions"].values()))
        source = subprocess.check_output(["git", "-C", str(Path(__file__).resolve().parents[1]),
            "show", "8865b30faa010b76045deb89ce062a7bd22ede99:tools/external_evidence.py"])
        path = Path(self.directory.name) / "pinned-prebridge-external-evidence.py"; path.write_bytes(source)
        spec = importlib.util.spec_from_file_location("pinned_prebridge_" + ee.sha256_hex(source), path)
        old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
        with self.assertRaises(old.ExternalEvidenceError) as refused:
            old._read_admission_record(self.root, entry["admission_path"], entry["admission_key"])
        self.assertEqual(refused.exception.code, "corrupt_admission")
        self.assertEqual(ledger_path.read_bytes(), original)

    def test_generic_only_record_cannot_be_silently_upgraded_on_replay(self):
        self.api.ee.admit_external_evidence(self.root, self.envelope, **self.expectations)
        path = self.root / ".agent/evidence/external_admissions/ledger.json"
        original = path.read_bytes()
        with self.assertRaises(self.api.ee.ExternalEvidenceError): self.admit()
        self.assertEqual(path.read_bytes(), original)
        with self.assertRaises(self.fixture.api.AssuranceError):
            self.fixture.api.validate_qa_proof(self.root, self.qa, feature_id="120",
                candidate=self.fixture.candidate, required_checks=[self.fixture.qa_check])

    def test_completed_host_rejection_settles_once_without_typed_completion_credit(self):
        self.envelope["status_separation"]["admission_decision"] = "rejected"; self.reseal()
        result = self.admit()
        self.assertIsNone(result["qa_mapping"])
        self.assertEqual(result["completion_status"], "not_advanced")
        self.assertTrue(self.admit()["idempotent_replay"])
        ledger = json.loads((self.root / ".agent/evidence/external_admissions/ledger.json").read_bytes())
        self.assertEqual(ledger["tasks"]["120"]["failed_count"], 1)
        self.assertEqual(len(ledger["tasks"]["120"]["history"]), 1)
        with self.assertRaises(self.fixture.api.AssuranceError):
            self.fixture.api.validate_qa_proof(self.root, self.qa, feature_id="120",
                candidate=self.fixture.candidate, required_checks=[self.fixture.qa_check])


class CoordinationBoundaryTests(unittest.TestCase):
    def test_external_symlink_publication_history_refuses_before_outside_writes(self):
        helper = generic.NfAc04GenericAdmissionTests(methodName="runTest"); helper.setUp()
        try:
            with tempfile.TemporaryDirectory(prefix="outside-external-history-") as directory:
                outside = Path(directory)
                evidence = helper.repo / ".agent/evidence"; evidence.mkdir(parents=True)
                (evidence / "external_admissions").symlink_to(outside, target_is_directory=True)
                with self.assertRaises(ee.ExternalEvidenceError):
                    ee.allocate_attempt_permit(helper.repo, task_id="safe-history", step_id="verify",
                        run_id="history-run", candidate_commit=helper.cand_commit)
                self.assertEqual(list(outside.iterdir()), [], "unsafe history created an outside lock or ledger")
        finally:
            helper.tearDown()

    def test_nofollow_and_opened_metadata_refuse_without_repair_or_native_execution(self):
        with tempfile.TemporaryDirectory(prefix="coordination-boundary-") as directory:
            root = Path(directory)
            with start_path._task_reservation_lock(root, "positive-control"):
                pass
            namespace = Path("/tmp") / ("nizam-task-reservations-" + str(os.geteuid()))
            key = start_path.sha256_hex(start_path.canonical_bytes([str(root.resolve()), "unsafe-lock"]))
            lock = namespace / (key + ".lock")
            sentinel = root / "sentinel"; sentinel.write_text("preserve\n")
            try:
                lock.symlink_to(sentinel)
                with self.assertRaises(start_path.StartPathError):
                    start_path._reserve_attempt(root, "unsafe-lock", "verify", 1)
                self.assertEqual(sentinel.read_text(), "preserve\n")
                self.assertTrue(lock.is_symlink())
                lock.unlink()
                original_open = os.open
                def change_opened_mode(path, flags, *args, **kwargs):
                    fd = original_open(path, flags, *args, **kwargs)
                    if str(path) == key + ".lock": os.fchmod(fd, 0o644)
                    return fd
                with patch.object(os, "open", change_opened_mode), self.assertRaises(start_path.StartPathError):
                    start_path._reserve_attempt(root, "unsafe-lock", "verify", 1)
                self.assertEqual(lock.stat().st_mode & 0o777, 0o644, "unsafe opened mode must not be repaired")
                self.assertFalse((root / ".agent/evidence/unsafe-lock-verify-attempt1.reservation.json").exists())
            finally:
                lock.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
