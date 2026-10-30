#!/usr/bin/env python3
"""Independent real-process pending-capacity controls; no model/network calls."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

import external_evidence as ee
import test_nf_ac04_generic_admission as generic

TOOLS = Path(__file__).resolve().parent


class NativePendingCapacityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="nf-pending-independent-")
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.root = self.base / "non-git-consumer"
        self.root.mkdir()
        self.children = []
        self.addCleanup(self.stop_children)
        self.env = {k: os.environ[k] for k in ("PATH", "HOME", "LANG") if k in os.environ}
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"

    def stop_children(self):
        for process in self.children:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.communicate(timeout=5)

    def argv(self, step, attempt=1, *, code="pass", signature=None, task="budget"):
        args = [sys.executable, str(TOOLS / "start_path.py"), "capture", "--root", str(self.root),
                "--id", task, "--step", step, "--attempt", str(attempt), "--output-dir",
                str(self.root / ".agent/evidence" / step)]
        if signature is not None:
            args += ["--defect-signature", signature]
        return args + ["--", sys.executable, "-c", code]

    def capture(self, step, attempt=1, *, failed=False, signature=None, task="budget"):
        code = "raise SystemExit(7)" if failed else "pass"
        return subprocess.run(self.argv(step, attempt, code=code, signature=signature, task=task),
                              env=self.env, capture_output=True, text=True, timeout=10)

    def blocked(self, step, *, attempt=1, failed=False, signature=None):
        ready = self.base / (step + "-" + str(attempt) + ".ready")
        release = self.base / (step + "-" + str(attempt) + ".release")
        code = ("import pathlib,time,sys; ready=pathlib.Path(sys.argv[1]); release=pathlib.Path(sys.argv[2]);"
                "ready.write_text('actual command executing'); deadline=time.monotonic()+15\n"
                "while not release.exists():\n"
                " if time.monotonic()>deadline: raise RuntimeError('fixture release deadline')\n"
                " time.sleep(.01)\n"
                "raise SystemExit(" + ("7" if failed else "0") + ")")
        args = self.argv(step, attempt, code=code, signature=signature) + [str(ready), str(release)]
        process = subprocess.Popen(args, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
        self.children.append(process)
        return process, ready, release

    def await_ready(self, entries, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if all(ready.exists() or process.poll() is not None for process, ready, _ in entries):
                return
            time.sleep(.01)
        self.fail("actual captures did not reach dispatch or refusal before fixture deadline")

    def finish(self, entry):
        process, _, release = entry
        release.write_text("release")
        out, err = process.communicate(timeout=8)
        return process.returncode, out, err

    def test_seven_processes_reserve_potential_capacity_before_any_terminal_outcome(self):
        entries = [self.blocked("parallel" + str(i), failed=True, signature="distinct-" + str(i)) for i in range(7)]
        self.await_ready(entries)
        started = sum(ready.exists() for _, ready, _ in entries)
        try:
            self.assertGreaterEqual(started, 2, "independent steps must really overlap, not global single-flight")
            self.assertLessEqual(started, 3, "unresolved potential signature failures exceeded three available slots")
            self.assertFalse(list(self.root.rglob("*.capture.json")), "barrier must precede every terminal outcome")
        finally:
            results = [self.finish(entry) for entry in entries]
        observed = [json.loads(out) for _, out, _ in results if out.strip().startswith("{")]
        self.assertLessEqual(sum(doc.get("outcome") == "failed" for doc in observed), 6)
        self.assertEqual(sum(doc.get("executed") is True for doc in observed), started)

    def test_two_independent_steps_overlap_and_terminal_success_releases_capacity(self):
        entries = [self.blocked("success" + str(i)) for i in range(3)]
        self.await_ready(entries)
        self.assertTrue(all(ready.exists() for _, ready, _ in entries), "three initially available slots should run")
        result = self.capture("fourth")
        self.assertEqual(result.returncode, 2, "fourth pending execution must refuse")
        code, out, err = self.finish(entries[0])
        self.assertEqual(code, 0, out + err)
        replacement = self.blocked("replacement")
        self.await_ready([replacement])
        self.assertTrue(replacement[1].exists(), "successful terminal evidence must release its slot")
        for entry in entries[1:] + [replacement]:
            code, out, err = self.finish(entry)
            self.assertEqual(code, 0, out + err)
        captures = [json.loads(p.read_bytes()) for p in self.root.rglob("*.capture.json")]
        self.assertTrue(all(c["outcome"] == "success" for c in captures), "pending must not become observed failure")
        self.assertFalse((self.root / ".git").exists())

    def test_positive_two_actual_non_git_commands_overlap_before_either_outcome(self):
        entries = [self.blocked("overlap" + str(i)) for i in range(2)]
        self.await_ready(entries)
        self.assertTrue(all(ready.exists() and process.poll() is None for process, ready, _ in entries))
        self.assertFalse(list(self.root.rglob("*.capture.json")), "both commands must overlap before terminal evidence")
        for entry in entries:
            code, out, err = self.finish(entry)
            self.assertEqual(code, 0, out + err)
            self.assertEqual(json.loads(out)["outcome"], "success")
        self.assertFalse((self.root / ".git").exists())

    def test_unknown_interrupted_reservation_holds_capacity_in_fresh_processes(self):
        interrupted = self.blocked("unknown")
        self.await_ready([interrupted]); self.assertTrue(interrupted[1].exists())
        os.killpg(interrupted[0].pid, signal.SIGKILL)
        interrupted[0].communicate(timeout=5)
        self.assertFalse(list(self.root.rglob("*.capture.json")))
        entries = [self.blocked("restarted" + str(i)) for i in range(3)]
        self.await_ready(entries)
        self.assertEqual(sum(ready.exists() for _, ready, _ in entries), 2,
                         "unknown prior execution must retain one slot across fresh controllers")
        for entry in entries:
            self.finish(entry)

    def test_same_step_pending_refuses_retry_and_restart_keeps_unknown_capacity(self):
        interrupted = self.blocked("interrupted")
        self.await_ready([interrupted])
        self.assertTrue(interrupted[1].exists())
        result = self.capture("interrupted", attempt=2)
        self.assertEqual(result.returncode, 2, "same-step pending cannot be retried before outcome")
        os.killpg(interrupted[0].pid, signal.SIGKILL)
        interrupted[0].communicate(timeout=5)
        self.assertFalse(list(self.root.rglob("*.capture.json")), "killed producer must have no invented terminal evidence")
        entries = [self.blocked("afterrestart" + str(i)) for i in range(3)]
        self.await_ready(entries)
        self.assertEqual(sum(ready.exists() for _, ready, _ in entries), 2,
                         "fresh processes must retain one interrupted slot across restart")
        for entry in entries:
            self.finish(entry)
        self.assertEqual(self.capture("interrupted", attempt=2).returncode, 2)

    def test_two_observed_same_signature_failures_plus_pending_hold_last_signature_slot(self):
        for step in ("first", "second"):
            result = self.capture(step, failed=True, signature="same-signature")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        pending = self.blocked("potential", signature="different-claimed-signature")
        self.await_ready([pending]); self.assertTrue(pending[1].exists())
        self.assertEqual(self.capture("unrelated-label", signature="another-label").returncode, 2)
        code, out, err = self.finish(pending)
        self.assertEqual(code, 0, out + err)
        result = self.capture("after-success", signature="yet-another-label")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fresh_check_inside_reservation_refuses_sixth_failure_race(self):
        for i in range(5):
            result = self.capture("failed" + str(i), failed=True, signature="signature-" + str(i))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        ready, release, executed = self.base / "pre-reserve", self.base / "reserve-release", self.base / "stale-executed"
        code = r'''import json,pathlib,sys,time
sys.path.insert(0,sys.argv[1]);import start_path as sp
root=pathlib.Path(sys.argv[2]);ready=pathlib.Path(sys.argv[3]);release=pathlib.Path(sys.argv[4]);executed=sys.argv[5]
original=sp._reserve_attempt
def paused(*args,**kwargs):
 ready.write_text('before actual reservation');deadline=time.monotonic()+12
 while not release.exists():
  if time.monotonic()>deadline:raise RuntimeError('release deadline')
  time.sleep(.01)
 return original(*args,**kwargs)
sp._reserve_attempt=paused
try:
 result=sp.capture_command_evidence(root,task_id='budget',step='stale',attempt=1,output_dir=root/'.agent/evidence/stale',argv=[sys.executable,'-c',"import pathlib,sys;pathlib.Path(sys.argv[1]).write_text('executed')",executed])
 print(json.dumps(result))
except sp.StartPathError as exc:
 print(str(exc),file=sys.stderr);sys.exit(2)
'''
        process = subprocess.Popen([sys.executable, "-c", code, str(TOOLS), str(self.root), str(ready), str(release), str(executed)],
                                   env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        self.children.append(process)
        deadline = time.monotonic() + 5
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertTrue(ready.exists(), "actual public capture must reach pre-reservation seam")
        sixth = self.capture("sixth", failed=True, signature="sixth-distinct")
        self.assertEqual(sixth.returncode, 1, sixth.stdout + sixth.stderr)
        release.write_text("release")
        out, err = process.communicate(timeout=8)
        self.assertEqual(process.returncode, 2, "stale authorization dispatched after sixth failure: " + out + err)
        self.assertFalse(executed.exists())

    def test_corrupt_pending_marker_preserved_and_refused_not_treated_as_free_capacity(self):
        pending = self.blocked("corrupt")
        self.await_ready([pending]); self.assertTrue(pending[1].exists())
        os.killpg(pending[0].pid, signal.SIGKILL); pending[0].communicate(timeout=5)
        marker = self.root / ".agent/evidence/budget-corrupt-attempt1.reservation.json"
        self.assertTrue(marker.is_file()); marker.write_bytes(b'{unknown-partial')
        result = self.capture("new-step")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(marker.read_bytes(), b'{unknown-partial')

    def test_exact_finite_operator_recovery_allows_parallel_slots_without_clearing_history(self):
        last = None
        for i in range(3):
            result = self.capture("same" + str(i), failed=True, signature="same-defect")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            last = json.loads(result.stdout)["capture_path"]
        self.assertEqual(self.capture("without-authority").returncode, 2)
        recovery = dict(task_id="budget", approved=True, max_task_attempts=5, after_capture=last,
                        authority_ref=".agent/evidence/operator.json")
        (self.root / recovery["authority_ref"]).write_text(json.dumps({"role": "operator", **recovery}))
        (self.root / ".agent/run_state.json").write_text(json.dumps({"circuit_breaker": {"budget": {"operator_recovery": recovery}}}))
        entries = [self.blocked("recovered" + str(i), failed=True, signature="same-defect") for i in range(2)]
        self.await_ready(entries)
        self.assertTrue(all(ready.exists() for _, ready, _ in entries), "finite recovery must preserve two available independent slots")
        self.assertEqual(self.capture("beyond-finite").returncode, 2)
        self.assertEqual(self.capture("recovered0", attempt=2).returncode, 2, "authority cannot clear pending same-step")
        for entry in entries:
            code, out, err = self.finish(entry); self.assertEqual(code, 1, out + err)
        captures = [json.loads(p.read_bytes()) for p in self.root.rglob("*.capture.json")]
        self.assertEqual(sum(c["outcome"] == "failed" for c in captures), 5)
        self.assertEqual(self.capture("exhausted").returncode, 2)


class ExternalPendingCapacityTests(unittest.TestCase):
    def setUp(self):
        self.helper = generic.NfAc04GenericAdmissionTests(methodName="runTest")
        self.helper.setUp(); self.addCleanup(self.helper.tearDown)
        self.root = self.helper.repo
        self.serial = 0

    def allocate(self, step, task="pending", **kwargs):
        return ee.allocate_attempt_permit(self.root, task_id=task, step_id=step,
            run_id="run-" + step, candidate_commit=self.helper.cand_commit, **kwargs)

    def settle(self, allocation, *, failed=False, signature=None):
        self.serial += 1
        outcome = "failed" if failed else "passed"
        artifacts = self.helper._write_artifacts("pending-" + str(self.serial), test_outcome=outcome)
        envelope = self.helper._build_valid_envelope(allocation, artifacts, test_outcome=outcome,
            admission_decision="rejected" if failed else "admitted", defect_signature=signature)
        return self.helper._admit(envelope)

    def ledger(self):
        return json.loads((self.root / ".agent/evidence/external_admissions/ledger.json").read_bytes())

    def test_pending_cross_step_capacity_and_success_release_preserve_actual_counts(self):
        allocations = [self.allocate("step" + str(i)) for i in range(3)]
        before = self.ledger(); self.assertEqual(before["tasks"]["pending"]["failed_count"], 0)
        with self.assertRaises(ee.ExternalEvidenceError): self.allocate("fourth")
        self.assertEqual(self.ledger(), before, "refusal cannot change historical counts")
        self.settle(allocations[0])
        self.allocate("after-success")
        self.assertEqual(self.ledger()["tasks"]["pending"]["failed_count"], 0)
        with self.assertRaises(ee.ExternalEvidenceError): self.allocate("step1", parent_attempt=1, continuation_basis="strategy_ladder")
        with self.assertRaises(ee.ExternalEvidenceError): self.allocate("still-full")

    def test_two_actual_same_signature_failures_charge_unknown_pending_across_other_steps(self):
        for i in range(2): self.settle(self.allocate("failed" + str(i)), failed=True, signature="ab" * 32)
        pending = self.allocate("potential")
        before = self.ledger()
        with self.assertRaises(ee.ExternalEvidenceError): self.allocate("changed-step")
        self.assertEqual(self.ledger(), before)
        self.settle(pending)
        self.allocate("released-slot")
        self.assertEqual(self.ledger()["tasks"]["pending"]["failed_count"], 2)

    def test_task_ceiling_counts_five_actual_failures_and_one_unsettled_step(self):
        for i in range(5): self.settle(self.allocate("failed" + str(i)), failed=True, signature=(str(i) * 64))
        self.allocate("sixth-potential")
        before = self.ledger()
        with self.assertRaises(ee.ExternalEvidenceError): self.allocate("seventh")
        self.assertEqual(self.ledger(), before)
        self.assertEqual(before["tasks"]["pending"]["failed_count"], 5)

    def test_finite_operator_recovery_reserves_only_remaining_capacity_without_reset(self):
        last = None
        for i in range(3): last = self.settle(self.allocate("same" + str(i)), failed=True, signature="ac" * 32)
        authority = ".agent/evidence/external/operator-recovery.json"
        document = dict(role="operator", task_id="pending", approved=True, max_task_attempts=5,
                        after_capture=last["admission_path"], authority_ref=authority)
        (self.root / authority).write_text(json.dumps(document))
        for i in range(2): self.allocate("recovery" + str(i), operator_recovery_ref=authority)
        before = self.ledger()
        with self.assertRaises(ee.ExternalEvidenceError): self.allocate("beyond", operator_recovery_ref=authority)
        self.assertEqual(self.ledger(), before)
        self.assertEqual(before["tasks"]["pending"]["failed_count"], 3)
        with self.assertRaises(ee.ExternalEvidenceError):
            self.allocate("recovery0", parent_attempt=1, continuation_basis="operator_recovery", operator_recovery_ref=authority)


if __name__ == "__main__":
    unittest.main()
