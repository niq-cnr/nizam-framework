#!/usr/bin/env python3
"""Offline real-install/controller-proof tests for the existing release gate.

All repositories, tags, authority and adverse records below are disposable test
fixtures. Positive evidence comes from the official bootstrap and native capture
producer, not handwritten capture metadata or a substituted acceptance engine.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "https://example.invalid/release-fixture/framework.git"
VERSION = "9.8.7"
PRIOR = "9.8.6"
TASK = "self-install-fixture"
RC = "v9.8.7-rc.selfinstall-fixture"
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_GLOBAL=os.devnull,
           GIT_TERMINAL_PROMPT="0")


def run(root, *argv):
    return subprocess.run(argv, cwd=root, env=ENV, capture_output=True, timeout=180)


def checked(root, *argv):
    result = run(root, *argv)
    if result.returncode:
        raise AssertionError(f"fixture command {argv!r}: {result.returncode}\n"
                             + result.stdout.decode(errors="replace")
                             + result.stderr.decode(errors="replace"))
    return result.stdout


def git(root, *argv):
    return checked(root, "git", *argv).decode().strip()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2) + "\n")
    return target


def ref(root, path):
    path = Path(path)
    return {"path": path.relative_to(root).as_posix(), "sha256": digest(path.read_bytes())}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def commit(root, message):
    git(root, "add", "--all")
    git(root, "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


def anchors(root, version):
    value = json.loads((root / "NIZAM.json").read_text())
    value["framework"]["version"] = version
    write(root, "NIZAM.json", value)
    documents = {
        "CONTEXT.md": f'---\nversion: "{version}"\nchange_log:\n  - version: "{version}"\n---\nFixture\n',
        "docs/guide/index.html": f'<meta name="framework-version" content="{version}">\n<span id="footer-version">{version}</span>\n',
        "README.md": f'nizam-framework/v{version}/bootstrap.sh\nGOVERNANCE_TAG=v{version}\n--tag v{version}\nreleases/tag/v{version}\n',
        "CHANGELOG.md": f'## [Unreleased]\n\n## [{version}] - 2026-01-01\n**Patch release**\nmethodology/06_release_train.md\n',
        "docs/planning/ROADMAP.md": f'Release in preparation: v{version}\n',
    }
    for path, content in documents.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


class ReleaseSelfInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="nizam-release-self-install-")
        cls.home = Path(cls.temporary.name).resolve()
        cls.controller = cls.home / "controller"
        cls.primary = cls.home / "declared-primary"
        cls.portable = cls.home / "portable"
        cls.controller.mkdir()
        root = cls.controller
        git(root, "init", "-q")
        git(root, "config", "user.name", "Offline Release Fixture")
        git(root, "config", "user.email", "fixture@example.invalid")
        git(root, "remote", "add", "origin", ORIGIN)
        # Export the exact committed implementation through the shipped selector.
        # No private workspace records or inherited installed copy are imported.
        integrity = load("release_fixture_inventory", ROOT / "tools/payload_integrity.py")
        selected = [*integrity.MODULES, "NIZAM.json", "bootstrap.sh"]
        rows = checked(ROOT, "git", "ls-tree", "-r", "-z", "HEAD", "--", *selected)
        for row in rows.split(b"\0"):
            if not row:
                continue
            metadata, raw_path = row.split(b"\t", 1)
            mode, kind, oid = metadata.decode().split()
            if kind != "blob" or mode not in ("100644", "100755"):
                raise AssertionError("fixture export requires regular shipped blobs")
            target = root / os.fsdecode(raw_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(checked(ROOT, "git", "cat-file", "blob", oid))
            target.chmod(0o755 if mode == "100755" else 0o644)
        anchors(root, PRIOR)
        cls.baseline = commit(root, "synthetic prior release")
        git(root, "tag", "-a", "v" + PRIOR, "-m", "synthetic prior release")
        # Real prior pin is tracked in the source; it is deliberately distinct
        # from the candidate installed later at the declared primary checkout.
        transport = root.as_uri()
        checked(root, "bash", "bootstrap.sh", "--repo-url", transport, "--tag", "v" + PRIOR,
                "--expected-sha", cls.baseline, "--target", str(root / ".nizam"))
        commit(root, "portable prior stable governance")
        anchors(root, VERSION)
        gate_path = root / ".github/scripts/release_closeout.py"
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate = (ROOT / ".github/scripts/release_closeout.py").read_text()
        # Rebind only the private era boundary to this synthetic repository's B.
        # Production has no bypass parameter and its published boundary is tested.
        gate = gate.replace('SELF_INSTALL_POLICY_BASELINE = "0b0e25da77bd2adeab1929a0f0f05e1f7d6fe6c2"',
                            f'SELF_INSTALL_POLICY_BASELINE = "{cls.baseline}"')
        gate_path.write_text(gate)
        cls.candidate = commit(root, "synthetic reviewed release payload C")
        git(root, "tag", "-a", RC, "-m", "private disposable prepublication candidate")
        checked(cls.home, "git", "clone", "-q", "--no-hardlinks", str(root), str(cls.primary))
        git(cls.primary, "remote", "set-url", "origin", ORIGIN)
        git(cls.primary, "checkout", "-q", "--detach", cls.candidate)
        (root / "fixture-source.txt").write_text("selected source input\n")
        (root / "fixture-test.txt").write_text("selected test input\n")
        readback = (
            "import hashlib,json,subprocess;from pathlib import Path;"
            f"r=Path({str(cls.primary)!r});p=r/'.nizam';"
            "h=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();"
            "g=lambda *a:subprocess.check_output(['git','-C',str(r),*a],text=True).strip();"
            "print(json.dumps({'destination':str(r.resolve()),'repository':g('remote','get-url','origin'),"
            "'head':g('rev-parse','HEAD'),'provenance':json.loads((p/'provenance.json').read_text()),"
            "'NIZAM_sha256':h(p/'NIZAM.json'),'SKILL_sha256':h(p/'tools/SKILL.md'),"
            "'entrypoint_sha256':h(p/'tools/start_path.py')}))"
        )
        base_argv = ["bash", "bootstrap.sh", "--repo-url", transport, "--tag", RC,
                     "--expected-sha", cls.candidate, "--target", str(cls.primary / ".nizam")]
        commands = [base_argv,
                    [*base_argv, "--verify-only", "--require-content-integrity", "--git-repo", str(root)],
                    [sys.executable, str(cls.primary / ".nizam/tools/start_path.py"), "preflight", "--root", str(cls.primary)],
                    [sys.executable, "-c", readback]]
        names = ["install", "integrity", "entrypoint", "readback"]
        cls.checks = [{"id": name, "argv": argv, "command": shlex.join(argv),
                       "acceptance_test": "Actual disposable " + name + " operation",
                       "expected_exit": 0,
                       "proof_kind": "success", "diagnostic": None} for name, argv in zip(names, commands)]
        cls.contract_path = f".agent/contracts/{TASK}.json"
        contract = {"contract_id": TASK, "feature_id": TASK, "name": "Synthetic real self-install fixture",
                    "status": "approved", "spec_ref": cls.contract_path + "#/fixture_authority",
                    "fixture_authority": "Disposable test data only, not programme or human acceptance",
                    "scope": {"files_create": [], "files_modify": []},
                    "non_goals": ["No live installation or programme acceptance"],
                    "verification": cls.checks, "estimated_lines": 0,
                    "evidence_dir": ".agent/evidence/self-install-fixture",
                    "evidence_convention": "Actual native captures in this disposable fixture"}
        write(root, cls.contract_path, contract)
        cls.decision_path = ".agent/evidence/self-install-operator-decision.json"
        write(root, cls.decision_path, {
            "approved": True, "owner": "offline-fixture-owner", "gate": "H-CONSUMER-UPGRADE",
            "repository": "release-fixture/framework", "commit": cls.candidate,
            "destination": str(cls.primary),
            "operator_instruction_verbatim": "Synthetic fixture owner approves C at this disposable primary"})
        cls.authority_path = ".agent/evidence/self-install-authority.json"
        write(root, cls.authority_path, {
            "approved": True, "owner": "offline-fixture-owner",
            "authority_ref": ref(root, root / cls.decision_path),
            "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_url": ORIGIN, "repository": "release-fixture/framework",
            "gate": "H-CONSUMER-UPGRADE", "self_install_request": "Synthetic fixture: install C in disposable primary",
            "commit": cls.candidate, "destination": str(cls.primary)})
        cls.source = commit(root, "synthetic controller authority and exact verification E")
        wa = load("release_fixture_assurance", root / "tools/workflow_assurance.py")
        cls.wa = wa
        wa._receipt_schema(root, contract, "contract")
        cls.saved_env = {key: os.environ.get(key) for key in
                         (wa.QA_CONTEXT_VARIABLE, wa.QA_EXECUTION_ROOT_VARIABLE, "PYTHONDONTWRITEBYTECODE", "GIT_CONFIG_GLOBAL")}
        os.environ.update(PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_GLOBAL=os.devnull)
        os.environ[wa.QA_CONTEXT_VARIABLE] = wa.qa_context_sha256(root, TASK, [cls.contract_path], cls.checks)
        os.environ[wa.QA_EXECUTION_ROOT_VARIABLE] = str(root)
        tools = ["bootstrap.sh", "tools/start_path.py", "tools/workflow_assurance.py",
                 "tools/payload_integrity.py", "tools/git_seam.py", "schema/qa_verdict.schema.json", "schema/contract.schema.json"]
        # Discover optional actual transitive Git seam rather than assuming it.
        tools = [p for p in tools if (root / p).is_file()]
        identity = wa.assess_repository(root, cls.source, {
            "source": ["fixture-source.txt"], "tests": ["fixture-test.txt"], "tools": tools,
            "contracts": [cls.contract_path, cls.authority_path, cls.decision_path], "unknown_dependencies": []},
            [wa.QA_CONTEXT_VARIABLE, wa.QA_EXECUTION_ROOT_VARIABLE])
        folder = root / ".agent/evidence/self-install-fixture"
        cls.manifest = write(root, ".agent/evidence/self-install-fixture/candidate.json", identity)
        sp = wa._load_start_path_module()
        proof_checks = []
        cls.capture_paths = {}
        for policy in cls.checks:
            observed = sp.capture_command_evidence(root, task_id=TASK, step=policy["id"], attempt=1,
                output_dir=folder, argv=policy["argv"], candidate_sha256=cls.manifest,
                env_vars=list(identity["environment"]["variables"]), agent_id="offline-fixture-controller",
                session_id="real-install-self-release", timeout_sec=120)
            if (observed["outcome"], observed["exit_code"], observed["completion_state"]) != ("success", 0, "completed"):
                raise AssertionError("actual fixture capture failed: " + json.dumps(observed))
            path = root / observed["capture_path"]
            cls.capture_paths[policy["id"]] = path
            proof_checks.append({"id": policy["id"], "capture": ref(root, path)})
        cls.qa_path = f".agent/qa/{TASK}.json"
        qa = {"feature_id": TASK, "qa_pass": True, "proof_version": 2,
              "checks_run": 4, "checks_passed": 4, "checks": proof_checks,
              "candidate_ref": ref(root, cls.manifest), "adversarial": {"performed": True},
              "evidence_files": [p["capture"]["path"] for p in proof_checks],
              "issues": [], "unsupported_claims": [], "missing_acceptance_coverage": [],
              "required_fixes": [], "final_verdict": {"approved": True, "summary": "Synthetic real captured operations"}}
        write(root, cls.qa_path, qa)
        wa.validate_qa_proof(root, qa, feature_id=TASK, candidate=identity, required_checks=cls.checks)
        cls.readiness_path = f".agent/evidence/release-v{VERSION}/readiness.json"
        proof = {"candidate_commit": cls.candidate, "destination": str(cls.primary),
                 "authorization": ref(root, root / cls.authority_path), "qa_verdict": ref(root, root / cls.qa_path)}
        for name in names:
            proof[name + "_capture"] = ref(root, cls.capture_paths[name])
        write(root, cls.readiness_path, {"version": VERSION, "prepublication_self_install": proof})
        cls.final = commit(root, "portable source-accepted actual primary captures D")
        git(root, "tag", "-a", "v" + VERSION, "-m", "synthetic final stable release")
        checked(cls.home, "git", "clone", "-q", "--no-hardlinks", str(root), str(cls.portable))
        git(cls.portable, "remote", "set-url", "origin", ORIGIN)
        git(cls.portable, "tag", "-d", RC)
        cls.original = {p: p.read_bytes() for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}

    @classmethod
    def tearDownClass(cls):
        for key, value in getattr(cls, "saved_env", {}).items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        cls.temporary.cleanup()

    def tearDown(self):
        for path, data in self.original.items():
            if path.is_symlink():
                path.unlink()
            path.write_bytes(data)

    def gate(self, root=None, *args):
        return run(root or self.controller, sys.executable, ".github/scripts/release_closeout.py", *args)

    def expect(self, result, code, phrase):
        output = (result.stdout + result.stderr).decode(errors="replace")
        self.assertEqual(result.returncode, code, output)
        self.assertIn(phrase, output)

    def reseal(self):
        """Adversarial fixtures update hashes to exercise semantic, not stale-hash, checks."""
        root = self.controller
        qa = json.loads((root / self.qa_path).read_text())
        qa["candidate_ref"] = ref(root, self.manifest)
        for check in qa["checks"]:
            check["capture"] = ref(root, self.capture_paths[check["id"]])
        write(root, self.qa_path, qa)
        readiness = json.loads((root / self.readiness_path).read_text())
        proof = readiness["prepublication_self_install"]
        proof["authorization"] = ref(root, root / self.authority_path)
        proof["qa_verdict"] = ref(root, root / self.qa_path)
        for name, path in self.capture_paths.items():
            proof[name + "_capture"] = ref(root, path)
        write(root, self.readiness_path, readiness)

    def change(self, path, mutation):
        value = json.loads(path.read_text())
        mutation(value)
        write(self.controller, path.relative_to(self.controller), value)

    def restore(self):
        self.tearDown()

    def test_real_native_controller_proof_and_portable_final_tag(self):
        self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 0, "actual runtime captures")
        # The primary becomes unavailable: tag verification must use immutable
        # committed artifacts, including native stream refs with revision:null.
        hidden = self.primary.with_name("primary-unavailable")
        self.primary.rename(hidden)
        try:
            self.expect(self.gate(self.portable, "--mode", "tag", "--tag", "v" + VERSION), 0,
                        "actual runtime captures")
        finally:
            hidden.rename(self.primary)
        self.assertEqual(json.loads((self.controller / ".nizam/NIZAM.json").read_text())["framework"]["version"], PRIOR)
        self.assertEqual(json.loads((self.primary / ".nizam/NIZAM.json").read_text())["framework"]["version"], VERSION)

    def test_repository_spelling_portability_preserves_exact_host_and_path(self):
        spellings = [
            ("https://example.invalid/release-fixture/framework", True),
            ("git@example.invalid:release-fixture/framework.git", True),
            ("ssh://git@example.invalid/release-fixture/framework.git", True),
            ("https://EXAMPLE.INVALID/release-fixture/framework.git", True),
            ("https://other.invalid/release-fixture/framework.git", False),
            ("git@example.invalid:other-owner/framework.git", False),
            ("ssh://git@example.invalid/release-fixture/other-framework.git", False),
        ]
        try:
            for spelling, accepted in spellings:
                with self.subTest(remote=spelling):
                    # Only the disposable verifier clone changes origin. Its
                    # immutable controller authority, identity and captures keep
                    # the actual recorded spelling and original hashes.
                    git(self.portable, "remote", "set-url", "origin", spelling)
                    self.expect(self.gate(self.portable, "--mode", "tag", "--tag", "v" + VERSION),
                                0 if accepted else 1,
                                "actual runtime captures" if accepted else "prepublication self-install evidence")
        finally:
            git(self.portable, "remote", "set-url", "origin", ORIGIN)
        root = self.controller
        capture_path = self.capture_paths["readback"]
        original_capture = json.loads(capture_path.read_text())
        stream = root / original_capture["stdout"]["path"]
        for spelling, accepted in spellings:
            with self.subTest(readback=spelling):
                self.restore()
                # Metamorphic parser fixture, not another actual installation
                # or claimed native execution: equivalent observed repository
                # spellings must preserve the meaning of an accepted record.
                self.change(stream, lambda v: v.update(repository=spelling))
                self.change(capture_path, lambda v: v.update(stdout=ref(root, stream)))
                self.reseal()
                self.expect(self.gate(None, "--mode", "pr", "--require-self-install"),
                            0 if accepted else 1,
                            "actual runtime captures" if accepted else "prepublication self-install evidence")

    def test_ordinary_pr_and_missing_release_proof(self):
        (self.controller / self.readiness_path).unlink()
        self.expect(self.gate(None, "--mode", "pr"), 0, "all internal version anchors agree")
        self.expect(self.gate(None, "--mode", "pr", "--base-commit", self.source), 0, "all internal version anchors agree")
        self.expect(self.gate(None, "--mode", "pr", "--base-commit", self.baseline), 1, "prepublication self-install evidence")
        self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 1, "prepublication self-install evidence")

    def test_historical_boundary_is_ancestry_not_numeric_version(self):
        self.expect(self.gate(None, "--mode", "tag", "--tag", "v" + PRIOR), 0, "immutable release history")
        # Real post-policy commit with a lower maintenance version still needs
        # proof. It cannot gain historical status merely from its version.
        with tempfile.TemporaryDirectory(dir=self.home) as directory:
            future = Path(directory)
            checked(self.home, "git", "clone", "-q", str(self.controller), str(future))
            git(future, "config", "user.name", "Offline Release Fixture")
            git(future, "config", "user.email", "fixture@example.invalid")
            git(future, "remote", "set-url", "origin", ORIGIN)
            anchors(future, "9.8.5")
            commit(future, "post-policy maintenance without self-install evidence")
            git(future, "tag", "-a", "v9.8.5", "-m", "synthetic future maintenance")
            self.expect(self.gate(future, "--mode", "tag", "--tag", "v9.8.5"), 1, "prepublication self-install evidence")

    def test_resealed_authority_and_destination_adverse_controls(self):
        root = self.controller
        for name, mutate in [
            ("denied approval", lambda v: v.update(approved=False)),
            ("missing approval", lambda v: v.pop("approved", None)),
            ("pending decision", lambda v: v.update(decision="pending")),
            ("denied decision", lambda v: v.update(decision="denied")),
            ("missing owner", lambda v: v.pop("owner", None)),
            ("foreign owner", lambda v: v.update(owner="another-owner")),
            ("missing decision reference", lambda v: v.pop("authority_ref", None)),
            ("wrong decision hash", lambda v: v["authority_ref"].update(sha256="a" * 64)),
            ("foreign repository", lambda v: v.update(repository="foreign/framework")),
            ("wrong source", lambda v: v.update(source_url="https://example.invalid/foreign.git")),
            ("wrong candidate", lambda v: v.update(commit=self.baseline)),
            ("wrong target", lambda v: v.update(destination=str(self.home / "external-fixture"))),
            ("wrong gate", lambda v: v.update(gate="fixture-only")),
            ("false instruction", lambda v: v.update(self_install_request=False)),
            ("late authority", lambda v: v.update(recorded_at="2999-01-01T00:00:00Z")),
        ]:
            with self.subTest(name=name):
                self.restore()
                self.change(root / self.authority_path, mutate)
                self.reseal()
                self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 1, "prepublication self-install evidence")
        self.restore()
        self.change(root / self.readiness_path,
                    lambda v: v["prepublication_self_install"].update(destination=str(self.primary) + "/../declared-primary"))
        self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 1, "declared resolved destination")

    def test_resealed_underlying_owner_decision_must_approve_this_target(self):
        root = self.controller
        for name, mutate in [
            ("denied", lambda v: v.update(approved=False)),
            ("absent approval", lambda v: v.pop("approved", None)),
            ("pending", lambda v: v.update(decision="pending")),
            ("explicit denied", lambda v: v.update(decision="denied")),
            ("wrong owner", lambda v: v.update(owner="another-owner")),
            ("wrong gate", lambda v: v.update(gate="H-FRAMEWORK-RELEASE")),
            ("wrong repository", lambda v: v.update(repository="foreign/framework")),
            ("wrong candidate", lambda v: v.update(commit=self.baseline)),
            ("wrong destination", lambda v: v.update(destination=str(self.home / "other-primary"))),
            ("absent instruction", lambda v: v.pop("operator_instruction_verbatim", None)),
        ]:
            with self.subTest(name=name):
                self.restore()
                self.change(root / self.decision_path, mutate)
                # Keep the reference digest valid: this tests the actual owner
                # decision/binding, rather than merely rejecting stale bytes.
                self.change(root / self.authority_path,
                            lambda v: v.update(authority_ref=ref(root, root / self.decision_path)))
                self.reseal()
                self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 1,
                            "prepublication self-install evidence")
        self.restore()
        self.change(root / self.decision_path, lambda v: v.update(owner="jointly-forged-owner"))
        self.change(root / self.authority_path, lambda v: v.update(
            owner="jointly-forged-owner", authority_ref=ref(root, root / self.decision_path)))
        self.reseal()
        # Matching owner strings and valid artifact hashes still cannot replace
        # the exact owner decision assessed at the accepted controller source.
        self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 1,
                    "prepublication self-install evidence")

    def test_resealed_capture_and_accepted_qa_adverse_controls(self):
        mutations = [
            ("failed", lambda v: v.update(outcome="failed", exit_code=1)),
            ("signalled", lambda v: v.update(signal=9)),
            ("bool exit", lambda v: v.update(exit_code=False)),
            ("unexecuted", lambda v: v.update(executed=False)),
            ("incomplete", lambda v: v.update(completion_state="interrupted")),
            ("foreign task", lambda v: v.update(id="foreign")),
            ("wrong candidate", lambda v: v.update(candidate_sha256="a" * 64)),
            ("foreign cwd", lambda v: v.update(cwd=str(self.home))),
            ("short revision", lambda v: v.update(revision=self.source[:8])),
            ("old execution", lambda v: v.update(revision=self.baseline)),
            ("future evidence", lambda v: v.update(completed_at="2999-01-01T00:00:00Z")),
            ("wrong bootstrap", lambda v: v["argv"].__setitem__(1, "untrusted-bootstrap.sh")),
            ("wrong installed target", lambda v: v["argv"].__setitem__(v["argv"].index("--target") + 1, str(self.home))),
        ]
        for name, mutate in mutations:
            with self.subTest(name=name):
                self.restore()
                self.change(self.capture_paths["install"], mutate)
                self.reseal()
                self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 1, "prepublication self-install evidence")
        self.restore()
        # Mere argument membership does not execute the installed script: all
        # the right strings can be unused arguments to a different Python job.
        self.change(self.capture_paths["entrypoint"], lambda v: v.update(argv=[
            sys.executable, "-c", "print('not the installed entrypoint')",
            str(self.primary / ".nizam/tools/start_path.py"), "preflight", "--root", str(self.primary)]))
        self.reseal()
        self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 1,
                    "actual installed entrypoint")
        for mutation in [lambda v: v.update(qa_pass=False),
                         lambda v: v.update(verdict="fail"),
                         lambda v: v["final_verdict"].update(approved=False),
                         lambda v: v.update(checks_passed=3),
                         lambda v: (v["checks"].pop(), v.update(checks_run=3, checks_passed=3))]:
            with self.subTest(qa=repr(mutation)):
                self.restore()
                self.change(self.controller / self.qa_path, mutation)
                self.reseal()
                self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 1, "prepublication self-install evidence")

    def test_runtime_readback_hashes_and_controller_tree(self):
        root = self.controller
        capture_path = self.capture_paths["readback"]
        original_capture = json.loads(capture_path.read_text())
        stream = root / original_capture["stdout"]["path"]
        for name, mutate in [
            ("head", lambda v: v.update(head=self.baseline)),
            ("file hash", lambda v: v.update(entrypoint_sha256="a" * 64)),
            ("provenance candidate", lambda v: v["provenance"].update(resolved_sha=self.baseline)),
            ("provenance tag", lambda v: v["provenance"].update(tag="v9.8.7-rc.wrong")),
        ]:
            with self.subTest(name=name):
                self.restore()
                self.change(stream, mutate)
                self.change(capture_path, lambda v: v.update(stdout=ref(root, stream)))
                self.reseal()
                self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 1, "prepublication self-install evidence")
        self.restore()
        self.change(self.manifest, lambda v: v.update(source_tree="a" * 40))
        # Reseal the identity as an adversary could, then prove the actual Git
        # source tree is checked rather than trusting internally consistent JSON.
        identity = json.loads(self.manifest.read_text())
        identity["identity_sha256"] = self.wa.sha(self.wa.canonical({k: v for k, v in identity.items() if k != "identity_sha256"}))
        write(root, self.manifest.relative_to(root), identity)
        self.reseal()
        self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 1, "actual source tree")

    def test_artifact_safety_and_final_authored_payload_drift(self):
        root = self.controller
        qa_path = root / self.qa_path
        qa_path.write_bytes(qa_path.read_bytes() + b" ")
        self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 1, "digest mismatch")
        self.restore()
        qa_path.unlink()
        qa_path.symlink_to(self.primary / ".nizam/NIZAM.json")
        self.expect(self.gate(None, "--mode", "pr", "--require-self-install"), 1, "prepublication self-install evidence")
        self.restore()
        # Git immutable final payload, not unrelated ambient worktree bytes,
        # determines whether C's acceptance can cover the release.
        for relative, diagnostic in (("tools/start_path.py", "final authored payload changed"),
                                     ("bootstrap.sh", "final bootstrap changed")):
            with self.subTest(path=relative), tempfile.TemporaryDirectory(dir=self.home) as directory:
                drift = Path(directory)
                checked(self.home, "git", "clone", "-q", str(root), str(drift))
                git(drift, "config", "user.name", "Offline Release Fixture")
                git(drift, "config", "user.email", "fixture@example.invalid")
                git(drift, "remote", "set-url", "origin", ORIGIN)
                with (drift / relative).open("a") as stream:
                    stream.write("\n# material final candidate drift\n")
                commit(drift, "changed release input after installed C")
                self.expect(self.gate(drift, "--mode", "pr", "--require-self-install"), 1, diagnostic)


if __name__ == "__main__":
    unittest.main()
