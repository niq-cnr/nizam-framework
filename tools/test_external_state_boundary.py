#!/usr/bin/env python3
"""Independent cooperative managed-state boundary controls, using real public APIs.

Only owned temporary fixtures are modified. Actual signed generic envelopes are
synthetic authority fixtures, never production/native QA or consumer adoption.
Public calls run in fresh processes with a deadline, including FIFO/socket cases.
No hostile same-UID concurrent rename protection is claimed.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import external_evidence as ee
import test_nf_ac04_generic_admission as generic

TOOLS = Path(__file__).resolve().parent
FIXED = (
    ".agent", ".agent/evidence", ".agent/evidence/external_admissions",
    ".agent/evidence/external_admissions/permits",
    ".agent/evidence/external_admissions/admitted",
)
OPERATIONS = ("allocate", "admit", "typed-admit", "reconcile")
CHILD = r'''
import copy,json,os,pathlib,sys
sys.path.insert(0,sys.argv[1])
import external_evidence as ee
import external_qa as qa
import test_nf_ac04_generic_admission as generic
request=json.loads(pathlib.Path(sys.argv[2]).read_text())
root=pathlib.Path(request['root'])
try:
 for name in request.get('missing_primitives',[]):delattr(os,name)
 op=request['operation']
 if op=='allocate':
  result=ee.allocate_attempt_permit(root,task_id='namespace-new',step_id='verify',
    run_id='namespace-run',candidate_commit=request['commit'])
 elif op=='reconcile':result=ee.reconcile_admission_state(root)
 else:
  helper=generic.NfAc04GenericAdmissionTests(methodName='runTest')
  helper.repo=root;helper.contract_rel=request['contract_rel']
  envelope=request['envelope']
  if op=='admit':result=helper._admit(envelope)
  else:
   # Only reaches the real generic state guard. Native context is deliberately
   # not qualified by this boundary-only negative fixture.
   candidate={'boundary_fixture':'not-native-qualification'}
   digest=ee.sha256_hex(ee.canonical_json_bytes(candidate))
   envelope['consumer_binding']['candidate_sha256']=digest
   allocation=request['allocation'];proof=envelope['producer_proof']
   envelope['producer_proof']=ee.compute_producer_proof(envelope_binding=envelope,
    permit_digest=allocation['permit_digest'],permit_token=allocation['permit_token'],
    candidate_commit=request['commit'],candidate_tree=request['tree'],
    execution_identity=envelope['execution_identity'],artifacts=envelope['artifacts'],
    producer_id=proof['producer_id'],session_id=proof['session_id'],issued_at=proof['issued_at'])
   result=qa.admit_external_qa(root,envelope,
    context_ref={'path':'.agent/evidence/unqualified-context.json','sha256':'a'*64},
    expected_feature_id='F-201',expected_candidate=candidate,required_checks=[],
    expected_execution_identity=envelope['execution_identity'],
    expected_producer={'agent_id':proof['producer_id'],'session_id':proof['session_id']},
    admission_expectations={
     'expected_candidate_sha256':digest,
     'expected_policy_id':generic.POLICY_ID,'expected_policy_version':generic.POLICY_VERSION,
     'expected_policy_digest':generic.POLICY_DIGEST,
     'expected_framework_version':generic.FW_VERSION,'expected_framework_commit':generic.FW_COMMIT,
     'expected_framework_tree':generic.FW_TREE,'expected_contract_path':helper.contract_rel,
     'expected_acceptance_collection_digest':generic.ACC_COLLECTION_DIGEST,
     'expected_regression_collection_digest':generic.REG_COLLECTION_DIGEST,
     'expected_tool_id':'neutral-pytest-runner','expected_adapter_id':'neutral-local-adapter'})
 print(json.dumps({'status':'accepted','result':result}))
except BaseException as exc:
 controlled=isinstance(exc,(ee.ExternalEvidenceError,qa.ee.ExternalEvidenceError))
 print(json.dumps({'status':'refused' if controlled else 'raw-error',
  'type':type(exc).__name__,'code':getattr(exc,'code',None),'message':str(exc)}))
'''


def snapshot(root: Path) -> dict:
    """No-follow complete bytes/modes/type inventory; never reads FIFO/socket/link."""
    records = {}
    def visit(path):
        info = path.lstat()
        row = {"mode": stat.S_IMODE(info.st_mode), "kind": stat.S_IFMT(info.st_mode)}
        if stat.S_ISREG(info.st_mode):
            raw = path.read_bytes()
            row.update(sha256=hashlib.sha256(raw).hexdigest(), byte_length=len(raw))
        elif stat.S_ISLNK(info.st_mode):
            row["target"] = os.readlink(path)
        records[path.relative_to(root).as_posix()] = row
        if stat.S_ISDIR(info.st_mode):
            for child in sorted(path.iterdir()):
                visit(child)
    if os.path.lexists(root):
        visit(root)
    return records


class ExternalStateBoundaryTests(unittest.TestCase):
    def setUp(self):
        # Disable automatic fixture Git maintenance before its first init/write.
        # Preserve full snapshots rather than excluding transient Git locks.
        self.environment = patch.dict(os.environ, {
            "PYTHONDONTWRITEBYTECODE": "1", "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "maintenance.auto", "GIT_CONFIG_VALUE_0": "false",
            "GIT_CONFIG_KEY_1": "gc.auto", "GIT_CONFIG_VALUE_1": "0",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def fixture(self):
        helper = generic.NfAc04GenericAdmissionTests(methodName="runTest")
        helper.setUp()
        self.addCleanup(helper.tearDown)
        allocation = ee.allocate_attempt_permit(helper.repo, task_id="F-201", step_id="verify",
                                                run_id="namespace-seed",
                                                candidate_commit=helper.cand_commit)
        envelope = helper._build_valid_envelope(allocation, helper._write_artifacts("namespace"))
        state = helper.repo / ".agent/evidence/external_admissions"
        (state / "admitted").mkdir(exist_ok=True)
        outside = helper.temp_dir / "outside-owned"
        outside.mkdir(mode=0o750)
        (outside / ".tmp-unrelated-sentinel").write_bytes(b"outside owned sentinel\n")
        (outside / ".tmp-unrelated-sentinel").chmod(0o640)
        helper.allocation = allocation
        helper.envelope = envelope
        helper.state = state
        helper.outside = outside
        helper.physical = {"ledger": state / "ledger.json", "permits": state / "permits",
                           "admitted": state / "admitted"}
        return helper

    def counters(self, fixture):
        physical = fixture.physical
        ledger = json.loads(physical["ledger"].read_bytes())
        return {
            "ledger_sha256": hashlib.sha256(physical["ledger"].read_bytes()).hexdigest(),
            "permits": len(ledger["permits"]), "admissions": len(ledger["admissions"]),
            "allocated": sum(s["allocated_attempts"] for t in ledger["tasks"].values()
                             for s in t["steps"].values()),
            "admitted": sum(s["admitted_attempts"] for t in ledger["tasks"].values()
                            for s in t["steps"].values()),
            "permit_files": len(list(physical["permits"].iterdir())),
            "admission_files": len(list(physical["admitted"].iterdir())),
        }

    def checkpoint(self, fixture):
        return {"outside": snapshot(fixture.outside),
                "namespace": snapshot(fixture.repo / ".agent"),
                "counters": self.counters(fixture)}

    def invoke(self, fixture, operation, *, missing_primitives=()):
        request = {"root": str(fixture.repo), "operation": operation,
                   "commit": fixture.cand_commit, "tree": fixture.cand_tree,
                   "contract_rel": fixture.contract_rel,
                   "allocation": fixture.allocation, "envelope": copy.deepcopy(fixture.envelope),
                   "missing_primitives": list(missing_primitives)}
        request_path = fixture.temp_dir / "private-request.json"
        request_path.write_text(json.dumps(request))
        request_path.chmod(0o600)
        started = time.monotonic()
        process = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD, str(TOOLS),
                                  str(request_path)], capture_output=True, text=True, timeout=5,
                                 env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertLess(time.monotonic() - started, 5)
        return json.loads(process.stdout)

    def refuse_unchanged(self, fixture, operation, *, missing_primitives=()):
        before = self.checkpoint(fixture)
        result = self.invoke(fixture, operation, missing_primitives=missing_primitives)
        after = self.checkpoint(fixture)
        # Capture side effects even when the public operation eventually refuses.
        self.assertEqual(after, before, (operation, result, "namespace/outside state changed"))
        self.assertEqual(result["status"], "refused", result)
        self.assertEqual(result["type"], "ExternalEvidenceError", result)
        return result

    def relocate(self, fixture, target):
        destination = fixture.outside / "relocated"
        target.rename(destination)
        for key, path in list(fixture.physical.items()):
            if path == target or path.is_relative_to(target):
                fixture.physical[key] = destination / path.relative_to(target)
        return destination

    def test_existing_namespace_components_refuse_before_cleanup_or_target_mutation(self):
        for operation in OPERATIONS:
            for relative in FIXED:
                for kind in ("symlink", "dangling", "file"):
                    with self.subTest(operation=operation, relative=relative, kind=kind):
                        f = self.fixture()
                        target = f.repo / relative
                        destination = self.relocate(f, target)
                        # The original reproduced attack deletes this owned staging file.
                        (destination / ".tmp-redirected-staging").write_bytes(b"preserve outside\n")
                        (destination / ".tmp-redirected-staging").chmod(0o640)
                        if kind == "file":
                            target.write_bytes(b"unsafe existing namespace component\n")
                            target.chmod(0o640)
                        else:
                            target.symlink_to(destination if kind == "symlink"
                                              else f.outside / "does-not-exist",
                                              target_is_directory=True)
                        self.refuse_unchanged(f, operation)

    def test_existing_unsafe_sibling_refuses_before_creating_missing_child_or_lock(self):
        for operation in OPERATIONS:
            for unsafe_name, missing_name in (("permits", "admitted"), ("admitted", "permits")):
                with self.subTest(operation=operation, unsafe=unsafe_name):
                    f = self.fixture()
                    unsafe = f.state / unsafe_name
                    destination = self.relocate(f, unsafe)
                    unsafe.symlink_to(destination, target_is_directory=True)
                    missing = f.state / missing_name
                    backup = f.outside / "removed-safe-sibling"
                    missing.rename(backup)
                    for key, path in list(f.physical.items()):
                        if path == missing:
                            f.physical[key] = backup
                    (f.state / "state.lock").unlink()
                    self.refuse_unchanged(f, operation)
                    self.assertFalse(os.path.lexists(missing))
                    self.assertFalse(os.path.lexists(f.state / "state.lock"))

    def test_unsafe_lock_refuses_promptly_before_staging_cleanup(self):
        for operation in OPERATIONS:
            for kind in ("symlink", "dangling", "fifo", "directory", "socket"):
                with self.subTest(operation=operation, kind=kind):
                    f = self.fixture()
                    lock = f.state / "state.lock"
                    lock.unlink()
                    (f.state / ".tmp-preexisting-stage").write_bytes(b"not cleanup credit\n")
                    target = f.outside / "external-lock"
                    target.write_bytes(b"outside lock must not be opened or changed\n")
                    target.chmod(0o640)
                    if kind in ("symlink", "dangling"):
                        lock.symlink_to(target if kind == "symlink" else f.outside / "missing")
                    elif kind == "fifo":
                        os.mkfifo(lock, 0o600)
                    elif kind == "directory":
                        lock.mkdir()
                    else:
                        owned_socket = socket.socket(socket.AF_UNIX)
                        self.addCleanup(owned_socket.close)
                        owned_socket.bind(str(lock))
                    self.refuse_unchanged(f, operation)

    def test_unknown_staging_entries_are_preserved_and_refused_without_partial_cleanup(self):
        for operation in OPERATIONS:
            for folder in ("", "permits", "admitted"):
                for kind in ("symlink", "fifo", "directory"):
                    with self.subTest(operation=operation, folder=folder, kind=kind):
                        f = self.fixture()
                        container = f.state / folder
                        regular = container / ".tmp-a-regular"
                        regular.write_bytes(b"must not partially clean before refusing unknown\n")
                        unknown = container / ".tmp-z-unknown"
                        if kind == "symlink":
                            unknown.symlink_to(f.outside / ".tmp-unrelated-sentinel")
                        elif kind == "fifo":
                            os.mkfifo(unknown, 0o600)
                        else:
                            unknown.mkdir()
                        self.refuse_unchanged(f, operation)

    def test_unsupported_nofollow_directory_and_nonblocking_primitives_refuse_without_effects(self):
        for primitive in ("O_NOFOLLOW", "O_DIRECTORY", "O_NONBLOCK"):
            with self.subTest(primitive=primitive):
                f = self.fixture()
                self.refuse_unchanged(f, "reconcile", missing_primitives=(primitive,))

    def test_positive_real_admission_replay_reconcile_and_regular_staging_cleanup(self):
        f = self.fixture()
        before = snapshot(f.outside)
        admitted = self.invoke(f, "admit")
        self.assertEqual(admitted["status"], "accepted", admitted)
        self.assertIs(admitted["result"]["ok"], True)
        self.assertIs(admitted["result"]["idempotent_replay"], False)
        replay = self.invoke(f, "admit")
        self.assertIs(replay["result"]["idempotent_replay"], True)
        counts = self.counters(f)
        self.assertEqual((counts["permits"], counts["admissions"], counts["allocated"],
                          counts["admitted"]), (1, 1, 1, 1))
        stages = []
        for folder in ("", "permits", "admitted"):
            path = f.state / folder / ".tmp-interrupted-regular"
            path.write_bytes(b"owned interrupted staging\n")
            stages.append(path)
        ordinary = f.state / "unrelated-operator-note"
        ordinary.write_bytes(b"preserve non-staging regular file\n")
        result = self.invoke(f, "reconcile")
        self.assertEqual(result["status"], "accepted", result)
        self.assertEqual(len(result["result"]["cleaned_staging_files"]), 3)
        self.assertTrue(all(not path.exists() for path in stages))
        self.assertEqual(ordinary.read_bytes(), b"preserve non-staging regular file\n")
        self.assertEqual(self.counters(f), counts)
        self.assertEqual(snapshot(f.outside), before)

    def test_positive_new_public_allocation_preserves_existing_history(self):
        f = self.fixture()
        ledger_before = json.loads(f.physical["ledger"].read_bytes())
        seed = copy.deepcopy(ledger_before["tasks"]["F-201"])
        outside_before = snapshot(f.outside)
        result = self.invoke(f, "allocate")
        self.assertEqual(result["status"], "accepted", result)
        self.assertEqual(result["result"]["permit"]["task_id"], "namespace-new")
        ledger_after = json.loads(f.physical["ledger"].read_bytes())
        self.assertEqual(ledger_after["tasks"]["F-201"], seed)
        self.assertEqual(len(ledger_after["permits"]), 2)
        self.assertEqual(snapshot(f.outside), outside_before)

    def test_positive_existing_directory_and_regular_lock_modes_are_not_repaired(self):
        f = self.fixture()
        for relative in FIXED:
            (f.repo / relative).chmod(0o750)
        (f.state / "state.lock").chmod(0o640)
        before = self.checkpoint(f)
        result = self.invoke(f, "reconcile")
        self.assertEqual(result["status"], "accepted", result)
        self.assertEqual(self.checkpoint(f), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
