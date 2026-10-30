#!/usr/bin/env python3
"""Independent real-receipt publication/crash/concurrency regressions.

Only standard IO fault boundaries are instrumented; proof planning is real.
Every authority label in ReceiptFixture remains explicitly synthetic.
"""
import copy
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from test_workflow_assurance import ReceiptFixture, load_api


def worker(arguments):
    root, policy, receipt, state, mode, marker, peer = map(str, arguments)
    root, policy, receipt, state = map(Path, (root, policy, receipt, state))
    # Execute the actually assessed fixture implementation in its active layout.
    # Loading the outer repository module would rightly fail QA layout binding.
    workflow_assurance = load_api(root / "tools/workflow_assurance.py")
    sys.modules["workflow_assurance"] = workflow_assurance
    start_path = workflow_assurance._load_start_path_module()
    before = state.read_bytes()
    if mode == "race":
        original = workflow_assurance.plan_receipt_transition

        def synchronized_plan(*args, **kwargs):
            try:
                result = original(*args, **kwargs)
            except Exception:
                # A correctly serialized conflicting contender reaches the real
                # planner and refuses after the winner; record that observation.
                Path(marker).write_text("refused")
                raise
            Path(marker).write_text(result["action"])
            deadline = time.monotonic() + 0.7
            while not Path(peer).exists() and time.monotonic() < deadline:
                time.sleep(0.005)
            return result

        workflow_assurance.plan_receipt_transition = synchronized_plan
    elif mode in ("before", "after"):
        original_write = Path.write_text
        original_replace, original_rename = os.replace, os.rename

        def direct_write(path, text, *args, **kwargs):
            if path == state:
                # Old implementation truncates the live file before interruption.
                if mode == "before":
                    with path.open("w", encoding="utf-8") as stream:
                        stream.write(text[:16]); stream.flush(); os.fsync(stream.fileno())
                    os._exit(75)
                original_write(path, text, *args, **kwargs)
                os._exit(75)
            return original_write(path, text, *args, **kwargs)

        def publish(original):
            def call(source, destination, *args, **kwargs):
                if Path(destination) == state and mode == "before":
                    os._exit(75)
                result = original(source, destination, *args, **kwargs)
                if Path(destination) == state:
                    os._exit(75)
                return result
            return call

        Path.write_text = direct_write
        os.replace, os.rename = publish(original_replace), publish(original_rename)
    elif mode == "directory-sync-failure":
        original_sync = os.fsync

        def sync(fd):
            if (stat.S_ISDIR(os.fstat(fd).st_mode)
                    and Path(os.readlink(f"/proc/self/fd/{fd}")).resolve() == state.parent.resolve()
                    and state.read_bytes() != before):
                raise OSError("independent post-publication directory sync failure")
            return original_sync(fd)

        os.fsync = sync
    try:
        result = start_path.resume_from_receipt(root, policy_path=policy,
            receipt_path=receipt, state_path=state, apply_changes=True)
        print(json.dumps(result), flush=True)
        return 0
    except Exception as exc:
        print(json.dumps({"refused": type(exc).__name__, "message": str(exc)}), flush=True)
        return 2


class ResumeDurabilityTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"NIZAM_WA120_FIXTURE": "observed"})
        self.environment.start(); self.addCleanup(self.environment.stop)
        self.directory = tempfile.TemporaryDirectory(prefix="resume-durability-")
        self.addCleanup(self.directory.cleanup)
        self.fixture = ReceiptFixture(load_api(), self.directory.name)
        self.root = self.fixture.root
        self.start_path = self.fixture.api._load_start_path_module()
        self.state = self.root / "record.json"
        self.state.chmod(0o600)
        self.evidence = self.root / ".agent/evidence/resume-durability-fixture"
        self.evidence.mkdir(parents=True)
        self.policy = self.evidence / "policy.json"
        self.receipt = self.evidence / "receipt.json"
        self.policy.write_text(json.dumps(self.fixture.policy))
        self.receipt.write_text(json.dumps(self.fixture.receipt))
        self.before = self.state.read_bytes()
        # Genuine existing gate validation plus real local-process captures.
        self.expected = self.fixture.api.plan_receipt_transition(self.root,
            json.loads(self.before), self.fixture.receipt, policy=self.fixture.policy)["state"]

    def command(self, mode="ordinary", receipt=None, marker="unused", peer="unused"):
        return [sys.executable, str(Path(__file__).resolve()), "--worker", str(self.root),
                str(self.policy), str(receipt or self.receipt), str(self.state), mode,
                str(marker), str(peer)]

    def run_worker(self, mode="ordinary"):
        return subprocess.run(self.command(mode), capture_output=True, text=True, timeout=40)

    def test_real_verified_readonly_then_apply_and_identical_replay(self):
        snapshot = self.fixture.snapshot()
        with patch.dict(sys.modules, {"workflow_assurance": self.fixture.api}):
            result = self.start_path.resume_from_receipt(self.root, policy_path=self.policy,
                receipt_path=self.receipt, state_path=self.state, apply_changes=False)
        self.assertEqual(result["action"], "advance"); self.assertFalse(result["applied"])
        self.assertEqual(self.fixture.snapshot(), snapshot, "readonly created lock or changed bytes")
        applied = self.run_worker(); self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.assertEqual(json.loads(self.state.read_bytes()), self.expected)
        complete = self.state.read_bytes()
        replay = self.run_worker(); self.assertEqual(replay.returncode, 0, replay.stdout + replay.stderr)
        self.assertEqual(json.loads(replay.stdout)["action"], "noop")
        self.assertEqual(self.state.read_bytes(), complete)
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o600)

    def test_real_interruption_before_publication_preserves_old_complete_state(self):
        result = self.run_worker("before")
        self.assertEqual(result.returncode, 75, result.stdout + result.stderr)
        self.assertEqual(self.state.read_bytes(), self.before, "interruption truncated durable owned state")
        self.assertEqual(json.loads(self.state.read_bytes()), json.loads(self.before))

    def test_real_interruption_after_publication_has_complete_new_state_and_noop_replay(self):
        result = self.run_worker("after")
        self.assertEqual(result.returncode, 75, result.stdout + result.stderr)
        self.assertEqual(json.loads(self.state.read_bytes()), self.expected)
        replay = self.run_worker(); self.assertEqual(replay.returncode, 0, replay.stdout + replay.stderr)
        self.assertEqual(json.loads(replay.stdout)["action"], "noop")

    def concurrent(self, second_receipt):
        markers = [self.evidence / "contender-a", self.evidence / "contender-b"]
        first = subprocess.Popen(self.command("race", marker=markers[0], peer=markers[1]),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        second = subprocess.Popen(self.command("race", receipt=second_receipt,
                                  marker=markers[1], peer=markers[0]),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            outputs = [(p, *p.communicate(timeout=40)) for p in (first, second)]
        finally:
            for process in (first, second):
                if process.poll() is None:
                    process.kill(); process.wait()
        self.assertTrue(all(p.exists() for p in markers), "not both contenders reached real receipt planner")
        return [(p.returncode, json.loads(stdout), stderr) for p, stdout, stderr in outputs]

    def test_concurrent_identical_receipt_has_one_advance_one_noop(self):
        results = self.concurrent(self.receipt)
        self.assertTrue(all(code == 0 for code, _, _ in results), results)
        self.assertEqual(sorted(r["action"] for _, r, _ in results), ["advance", "noop"], results)
        self.assertEqual(json.loads(self.state.read_bytes()), self.expected)

    def test_concurrent_conflicting_receipts_cannot_both_advance_stale_state(self):
        conflicting = copy.deepcopy(self.fixture.receipt)
        conflicting["verdict"]["final_verdict"]["summary"] = "different valid synthetic receipt"
        # Both receipts really pass independently from the original state.
        self.fixture.api.plan_receipt_transition(self.root, json.loads(self.before),
            conflicting, policy=self.fixture.policy)
        second = self.evidence / "conflicting-receipt.json"
        second.write_text(json.dumps(conflicting))
        results = self.concurrent(second)
        self.assertEqual(sum(code == 0 and result.get("action") == "advance"
                             for code, result, _ in results), 1, results)
        self.assertEqual(sum(code != 0 for code, _, _ in results), 1, results)
        state = json.loads(self.state.read_bytes())
        self.assertEqual(len(state["history"]), len(json.loads(self.before)["history"]) + 1)

    def test_post_publication_directory_sync_failure_refuses_success_then_replays(self):
        result = self.run_worker("directory-sync-failure")
        self.assertNotEqual(result.returncode, 0, "unsynced publication falsely reported applied")
        self.assertEqual(json.loads(self.state.read_bytes()), self.expected)
        replay = self.run_worker(); self.assertEqual(replay.returncode, 0, replay.stdout + replay.stderr)
        self.assertEqual(json.loads(replay.stdout)["action"], "noop")

    def test_unknown_interrupted_temporary_content_is_preserved_and_refused(self):
        before_paths = set(self.state.parent.iterdir())
        interrupted = self.run_worker("before")
        self.assertEqual(interrupted.returncode, 75, interrupted.stdout + interrupted.stderr)
        self.assertEqual(self.state.read_bytes(), self.before)
        new_files = [path for path in set(self.state.parent.iterdir()) - before_paths if path.is_file()]
        self.assertEqual(len(new_files), 1, "fixture must reach actual unpublished temporary file")
        residue = new_files[0]
        residue.write_bytes(b"unowned-concurrent-replacement")
        residue.chmod(0o644)
        replay = self.run_worker()
        self.assertNotEqual(replay.returncode, 0, "unknown residue cannot authorize recovery or publication")
        self.assertEqual(residue.read_bytes(), b"unowned-concurrent-replacement")
        self.assertEqual(stat.S_IMODE(residue.stat().st_mode), 0o644)
        self.assertEqual(self.state.read_bytes(), self.before)

    def test_symlink_state_target_refuses_without_mutating_referent(self):
        alias = self.root / "record-alias.json"
        alias.symlink_to(self.state.name)
        with patch.dict(sys.modules, {"workflow_assurance": self.fixture.api}):
            with self.assertRaises(Exception):
                self.start_path.resume_from_receipt(self.root, policy_path=self.policy,
                    receipt_path=self.receipt, state_path=alias, apply_changes=True)
        self.assertEqual(self.state.read_bytes(), self.before)
        self.assertTrue(alias.is_symlink())


class TrivialResumeIntegrationTests(unittest.TestCase):
    def test_interrupted_trivial_publication_replays_without_undeclared_temporary_files(self):
        import test_start_path as fixtures
        original = fixtures.run
        interrupted_roots = set()

        def interrupt_first_apply(root, *arguments):
            if arguments and arguments[0] == "resume" and str(root) not in interrupted_roots:
                interrupted_roots.add(str(root))
                policy = arguments[arguments.index("--policy") + 1]
                receipt = arguments[arguments.index("--receipt") + 1]
                state = root / ".agent/run_state.json"
                before = state.read_bytes()
                interrupted = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                    "--worker", str(root), policy, receipt, str(state), "before", "unused", "unused"],
                    capture_output=True, text=True, timeout=40)
                self.assertEqual(interrupted.returncode, 75, interrupted.stdout + interrupted.stderr)
                self.assertEqual(state.read_bytes(), before, "actual interrupted publication changed old state")
            return original(root, *arguments)

        with patch.object(fixtures, "run", interrupt_first_apply):
            # Reuse the exact real trivial-route/ordinary+linked flow, retaining
            # every successful apply, noop, unchanged-untracked and byte assertion.
            self.test_real_trivial_receipt_and_replay_do_not_contaminate_ordinary_or_linked_worktree()
        self.assertEqual(len(interrupted_roots), 2, "both ordinary and linked paths must reach interruption")

    def test_real_trivial_receipt_and_replay_do_not_contaminate_ordinary_or_linked_worktree(self):
        import test_start_path as fixtures
        from test_workflow_assurance import git
        with patch.dict(os.environ, {}):
            for linked in (False, True):
                with self.subTest(linked_worktree=linked), tempfile.TemporaryDirectory(prefix="resume-trivial-") as directory:
                    parent = Path(directory)
                    root = parent / "main"
                    fixtures.proof_bootstrap(root)
                    (root / "schema/run_state.schema.json").write_bytes(
                        (Path(__file__).resolve().parents[1] / "schema/run_state.schema.json").read_bytes())
                    state = dict(repository="https://example.invalid/qa-fixture.git", current_phase="fixture-phase",
                        current_feature="trivial-resume", status="in_progress", updated_at="2026-10-24T00:00:00Z",
                        scope_budget=dict(original_estimate_lines=10, total_lines_changed=0, per_feature=[]),
                        circuit_breaker={}, history=[])
                    fixtures.write(root, ".agent/run_state.json", state)
                    (root / "README.md").write_text("before\n")
                    git(root, "add", ".")
                    git(root, "commit", "-qm", "actual trivial consumer baseline")
                    if linked:
                        checkout = parent / "linked"
                        git(root, "worktree", "add", "-qb", "trivial-lane", str(checkout), "HEAD")
                        root = checkout
                        self.assertTrue((root / ".git").is_file())
                    fixtures.write(root, ".agent/evidence/trivial-resume-intent.json", dict(
                        id="trivial-resume", path="trivial", summary="Scoped editorial change",
                        needs_new_contract=False, files=["README.md"], verification=[dict(fixtures.CHECK)]))
                    begin = fixtures.run(root, "begin", "trivial", "--id", "trivial-resume")
                    self.assertEqual(begin.returncode, 0, begin.stdout + begin.stderr)
                    (root / "README.md").write_text("after\n")
                    verdict = fixtures.record_proof(root, "trivial-resume")
                    _, policy, receipt = fixtures.route_receipt(root, "trivial-resume", verdict)
                    folder = root / ".agent/evidence/trivial-resume"
                    policy_path, receipt_path = folder / "policy.json", folder / "receipt.json"
                    policy_path.write_text(json.dumps(policy)); receipt_path.write_text(json.dumps(receipt))
                    untracked_before = git(root, "ls-files", "--others", "--exclude-standard", "-z")
                    def resume():
                        return fixtures.run(root, "resume", "--policy", str(policy_path),
                                            "--receipt", str(receipt_path), "--apply")
                    applied = resume()
                    self.assertEqual(git(root, "ls-files", "--others", "--exclude-standard", "-z"),
                        untracked_before, "coordination lock contaminated assessed worktree")
                    self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
                    self.assertEqual(json.loads(applied.stdout)["action"], "advance")
                    completed = (root / ".agent/run_state.json").read_bytes()
                    replay = resume()
                    self.assertEqual(replay.returncode, 0, replay.stdout + replay.stderr)
                    self.assertEqual(json.loads(replay.stdout)["action"], "noop")
                    self.assertEqual((root / ".agent/run_state.json").read_bytes(), completed)
                    self.assertEqual(git(root, "ls-files", "--others", "--exclude-standard", "-z"), untracked_before)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        raise SystemExit(worker(sys.argv[2:]))
    unittest.main()
