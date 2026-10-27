#!/usr/bin/env python3
"""NF-AC05 acceptance suite: standalone consumer qualification, v2.0.0 -> candidate upgrade, binary review, and generic external evidence admission (NF-R05)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

V2_TAG = "v2.0.0"
V2_SHA = "603afc7b17919334a6a01df1e39e63798d9d0acd"


def _clean_standalone_env() -> dict[str, str]:
    """Return a clean environment with zero Agentic SDLC or ambient Git overrides."""
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        "TMPDIR": "/private/tmp" if Path("/private/tmp").is_dir() else tempfile.gettempdir(),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    return env


def _run(
    cmd: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    run_env = _clean_standalone_env()
    if env:
        run_env.update(env)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=run_env,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"Command {cmd} failed (exit {proc.returncode}):\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc


def _create_candidate_fixture_repo(temp_dir: Path) -> tuple[Path, str, str]:
    """Create a disposable Git repo containing v2.0.0 and a tagged snapshot of the candidate working tree."""
    cand_repo = temp_dir / "nizam-candidate-source"
    _run(["git", "clone", "--quiet", f"file://{ROOT}", str(cand_repo)], cwd=temp_dir)
    _run(["git", "config", "user.name", "NF Test"], cwd=cand_repo)
    _run(["git", "config", "user.email", "nf-test@example.invalid"], cwd=cand_repo)
    _run(["git", "config", "uploadpack.allowFilter", "true"], cwd=cand_repo)

    # Copy all authored candidate files from ROOT into cand_repo so uncommitted worktree edits are included
    for module in ("standard", "methodology", "registry", "templates", "schema", "tools", "ecosystem", "docs"):
        src_mod = ROOT / module
        dst_mod = cand_repo / module
        if dst_mod.exists():
            shutil.rmtree(dst_mod)
        shutil.copytree(src_mod, dst_mod, symlinks=True)
    for top_file in ("NIZAM.json", "bootstrap.sh", "README.md", "CHANGELOG.md"):
        if (ROOT / top_file).exists():
            shutil.copy2(ROOT / top_file, cand_repo / top_file)

    _run(["git", "add", "-A"], cwd=cand_repo)
    status = _run(["git", "status", "--porcelain"], cwd=cand_repo).stdout.strip()
    if status:
        _run(["git", "commit", "-m", "Candidate snapshot for NF-AC05 e2e qualification"], cwd=cand_repo)
    cand_sha = _run(["git", "rev-parse", "HEAD"], cwd=cand_repo).stdout.strip()
    fw_ver = json.loads((ROOT / "NIZAM.json").read_text(encoding="utf-8"))["framework"]["version"]
    cand_tag = f"e2e-{fw_ver}-rc1"
    _run(["git", "tag", "-a", cand_tag, cand_sha, "-m", "Disposable candidate fixture tag"], cwd=cand_repo)
    return cand_repo, cand_tag, cand_sha


def _init_disposable_consumer(temp_dir: Path) -> Path:
    """Create a standalone consumer repository with zero Agentic SDLC dependencies."""
    consumer = temp_dir / "standalone-consumer"
    consumer.mkdir(parents=True)
    _run(["git", "init", "-q"], cwd=consumer)
    _run(["git", "config", "user.name", "Standalone Consumer"], cwd=consumer)
    _run(["git", "config", "user.email", "consumer@example.invalid"], cwd=consumer)
    _run(["git", "remote", "add", "origin", "https://example.invalid/standalone/consumer.git"], cwd=consumer)

    (consumer / "README.md").write_text("# Standalone Consumer\n", encoding="utf-8")
    (consumer / "CONTEXT.md").write_text("# Consumer Context\n", encoding="utf-8")
    (consumer / "src").mkdir()
    (consumer / "src" / "app.py").write_text("def greet() -> str:\n    return 'hello'\n", encoding="utf-8")
    (consumer / ".agent" / "contracts").mkdir(parents=True)
    (consumer / ".agent" / "evidence").mkdir(parents=True)
    (consumer / ".agent" / "qa").mkdir(parents=True)
    (consumer / "docs" / "planning").mkdir(parents=True)
    run_state = {
        "repository": "https://example.invalid/standalone/consumer.git",
        "current_phase": "001-initial",
        "current_feature": "triv1",
        "status": "in_progress",
        "updated_at": "2026-10-27T00:00:00Z",
        "scope_budget": {
            "original_estimate_lines": 50,
            "total_lines_changed": 0,
            "per_feature": [{"id": "001", "estimated": 50, "actual": 0}],
        },
        "circuit_breaker": {},
        "history": [{"at": "2026-10-27T00:00:00Z", "event": "genesis", "detail": "Initialized consumer repository"}],
    }
    (consumer / ".agent" / "run_state.json").write_text(
        json.dumps(run_state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    contract_001 = {
        "contract_id": "001",
        "feature_id": "001",
        "name": "Initial consumer feature",
        "status": "approved",
        "spec_ref": "CONTEXT.md",
        "scope": {
            "files_create": [],
            "files_modify": [
                {"path": "README.md", "purpose": "Update consumer README"},
                {"path": "src/app.py", "purpose": "Main consumer module"},
            ],
        },
        "non_goals": ["No external dependencies"],
        "verification": [
            {"acceptance_test": "test -f README.md", "command": "test -f README.md"}
        ],
        "estimated_lines": 50,
        "evidence_dir": ".agent/evidence/001/",
        "evidence_convention": ".agent/evidence/001/check.txt",
        "approvals": {
            "validator_mode_a": True,
            "evaluator_contract_review": True,
            "approved_at": "2026-10-27T00:00:00Z",
            "revisions": 1,
        },
        "dod_ref": ".nizam/standard/definition_of_done.md",
    }
    (consumer / ".agent" / "contracts" / "001.json").write_text(
        json.dumps(contract_001, indent=2) + "\n", encoding="utf-8"
    )
    feature_list = {
        "phase": "001-initial",
        "spec_version": "0.1.0",
        "phase_status": "in_progress",
        "original_estimate_lines": 50,
        "features": [
            {
                "id": "001",
                "name": "Initial consumer feature",
                "description": "Standalone consumer feature.",
                "status": "in_progress",
                "passes": False,
                "dependencies": [],
                "acceptance_tests": ["test -f README.md"],
                "estimated_lines": 50,
            }
        ],
    }
    (consumer / ".agent" / "feature_list.json").write_text(
        json.dumps(feature_list, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema_version": 1,
        "updated_at": "2026-10-27T00:00:00Z",
        "current_phase": "001-initial",
        "phases": [
            {
                "id": "001-initial",
                "title": "Initial Consumer Phase",
                "feature_list": ".agent/feature_list.json",
                "status": "in_progress",
            }
        ],
    }
    (consumer / "docs" / "planning" / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    _run(["git", "add", "-A"], cwd=consumer)
    _run(["git", "commit", "-m", "Initial consumer commit"], cwd=consumer)
    return consumer


class StandaloneQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="nf-ac05-")
        cls.temp_dir = Path(cls._tmp.name)
        cls.cand_repo, cls.cand_tag, cls.cand_sha = _create_candidate_fixture_repo(cls.temp_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_n04_core_standalone_lifecycle_and_v2_compatibility(self) -> None:
        """Node N04: v2.0.0 installation, upgrade to candidate, standalone start_path + 1.0.0 review + negative controls."""
        consumer = _init_disposable_consumer(self.temp_dir / "n04")
        bootstrap_sh = self.cand_repo / "bootstrap.sh"

        # 1. Install released v2.0.0 into consumer/.nizam
        _run(
            [
                "bash",
                str(bootstrap_sh),
                "--tag",
                V2_TAG,
                "--expected-sha",
                V2_SHA,
                "--repo-url",
                f"file://{self.cand_repo}",
                "--target",
                str(consumer / ".nizam"),
            ],
            cwd=consumer,
        )
        # Verify v2.0.0 installation integrity & payload validation
        verify_v2 = _run(
            [
                "bash",
                str(bootstrap_sh),
                "--verify-only",
                "--tag",
                V2_TAG,
                "--expected-sha",
                V2_SHA,
                "--git-repo",
                str(self.cand_repo),
                "--require-content-integrity",
                "--target",
                str(consumer / ".nizam"),
            ],
            cwd=consumer,
        )
        self.assertIn("content_integrity=verified", verify_v2.stdout)
        val_v2 = _run(["bash", ".nizam/tools/validate.sh", "--payload"], cwd=consumer)
        self.assertIn("SUMMARY (payload mode): 10 exercised passed, 0 failed", val_v2.stdout)

        # 2. Unreleased fixture tag without --allow-fixture-tag is rejected
        bad_tag = _run(
            [
                "bash",
                str(bootstrap_sh),
                "--tag",
                self.cand_tag,
                "--expected-sha",
                self.cand_sha,
                "--repo-url",
                f"file://{self.cand_repo}",
                "--target",
                str(consumer / ".nizam"),
            ],
            cwd=consumer,
            check=False,
        )
        self.assertNotEqual(bad_tag.returncode, 0)

        # 3. Upgrade consumer/.nizam from v2.0.0 to candidate using --allow-fixture-tag
        shutil.rmtree(consumer / ".nizam")
        _run(
            [
                "bash",
                str(bootstrap_sh),
                "--tag",
                self.cand_tag,
                "--allow-fixture-tag",
                "--expected-sha",
                self.cand_sha,
                "--repo-url",
                f"file://{self.cand_repo}",
                "--target",
                str(consumer / ".nizam"),
            ],
            cwd=consumer,
        )
        verify_cand = _run(
            [
                "bash",
                str(bootstrap_sh),
                "--verify-only",
                "--tag",
                self.cand_tag,
                "--allow-fixture-tag",
                "--expected-sha",
                self.cand_sha,
                "--git-repo",
                str(self.cand_repo),
                "--require-content-integrity",
                "--target",
                str(consumer / ".nizam"),
            ],
            cwd=consumer,
        )
        self.assertIn("content_integrity=verified", verify_cand.stdout)
        val_cand = _run(["bash", ".nizam/tools/validate.sh", "--payload"], cwd=consumer)
        self.assertIn("SUMMARY (payload mode): 10 exercised passed, 0 failed", val_cand.stdout)

        # Commit the installed .nizam payload in the consumer repository
        _run(["git", "add", ".nizam"], cwd=consumer)
        _run(["git", "commit", "-m", "Bootstrap candidate .nizam payload"], cwd=consumer)

        # 4. Exercise standalone start_path.py: classify, preflight, status, non-feature begin -> capture -> done
        classify_triv = _run(
            [
                sys.executable,
                ".nizam/tools/start_path.py",
                "classify",
                "--editorial",
                "--files",
                "README.md",
            ],
            cwd=consumer,
        )
        self.assertEqual(json.loads(classify_triv.stdout)["route"], "trivial")
        classify_feat = _run(
            [
                sys.executable,
                ".nizam/tools/start_path.py",
                "classify",
                "--needs-new-contract",
                "--files",
                "src/app.py",
            ],
            cwd=consumer,
        )
        self.assertEqual(json.loads(classify_feat.stdout)["route"], "standard-feature")

        preflight_proc = _run(
            [sys.executable, ".nizam/tools/start_path.py", "preflight"],
            cwd=consumer,
        )
        preflight_out = json.loads(preflight_proc.stdout)
        self.assertTrue(preflight_out["ok"])
        self.assertEqual(preflight_out["status"], "ready")

        # Negative control: attempting to touch .nizam/ in a non-feature route is rejected
        bad_intent = {
            "id": "trivbad",
            "path": "trivial",
            "summary": "Illegal attempt to touch .nizam/",
            "needs_new_contract": False,
            "files": [".nizam/tools/start_path.py"],
        }
        (consumer / ".agent" / "evidence" / "trivbad-intent.json").write_text(
            json.dumps(bad_intent, indent=2) + "\n", encoding="utf-8"
        )
        bad_begin = _run(
            [sys.executable, ".nizam/tools/start_path.py", "begin", "trivial", "--id", "trivbad"],
            cwd=consumer,
            check=False,
        )
        self.assertNotEqual(bad_begin.returncode, 0)
        (consumer / ".agent" / "evidence" / "trivbad-intent.json").unlink()

        # Execute full standalone trivial route (begin -> capture -> done) using only consumer .nizam/
        import importlib.util
        wa_spec = importlib.util.spec_from_file_location(
            "installed_consumer_assurance", consumer / ".nizam" / "tools" / "workflow_assurance.py"
        )
        assert wa_spec is not None and wa_spec.loader is not None
        wa_api = importlib.util.module_from_spec(wa_spec)
        wa_spec.loader.exec_module(wa_api)

        check_spec = {
            "id": "readme-exists",
            "argv": [sys.executable, "-c", "from pathlib import Path; assert Path('README.md').is_file()"],
            "expected_exit": 0,
            "proof_kind": "success",
            "diagnostic": None,
        }
        intent_payload = {
            "id": "triv1",
            "path": "trivial",
            "summary": "Verify a bounded README edit using installed tools",
            "needs_new_contract": False,
            "files": ["README.md"],
            "verification": [check_spec],
        }
        intent_rel = ".agent/evidence/triv1-intent.json"
        (consumer / intent_rel).write_bytes(wa_api.canonical(intent_payload))
        _run(["git", "add", intent_rel], cwd=consumer)
        _run(["git", "commit", "--only", "-qm", "pin triv1 verification inventory", "--", intent_rel], cwd=consumer)

        _run([sys.executable, ".nizam/tools/start_path.py", "begin", "trivial", "--id", "triv1"], cwd=consumer)
        (consumer / "README.md").write_text("# Standalone Consumer\n\nVerified standalone.\n", encoding="utf-8")
        base_rel = ".agent/evidence/triv1-base.json"
        _run(["git", "add", "README.md", base_rel], cwd=consumer)
        _run(
            ["git", "commit", "--only", "-qm", "assess triv1 declared edit and immutable base", "--", "README.md", base_rel],
            cwd=consumer,
        )

        auth_paths = wa_api.qa_authorization_paths(consumer, "triv1")
        ctx_sha = wa_api.qa_context_sha256(consumer, "triv1", auth_paths, [check_spec])
        qa_env = {
            wa_api.QA_CONTEXT_VARIABLE: ctx_sha,
            wa_api.QA_EXECUTION_ROOT_VARIABLE: str(consumer),
            "NIZAM_CONSUMER_TEST": "1",
        }
        os_env_backup = {k: os.environ.get(k) for k in qa_env}
        try:
            os.environ.update(qa_env)
            inputs = {
                "source": ["README.md"],
                "tests": ["src/app.py"],
                "contracts": auth_paths,
                "tools": [
                    ".nizam/tools/start_path.py",
                    ".nizam/tools/workflow_assurance.py",
                    ".nizam/schema/qa_verdict.schema.json",
                    ".nizam/schema/contract.schema.json",
                    ".nizam/schema/small_change_intent.schema.json",
                ],
                "unknown_dependencies": [],
            }
            head_now = _run(["git", "rev-parse", "HEAD"], cwd=consumer).stdout.strip()
            candidate = wa_api.assess_route_candidate(
                consumer,
                "triv1",
                head_now,
                inputs,
                [wa_api.QA_CONTEXT_VARIABLE, wa_api.QA_EXECUTION_ROOT_VARIABLE, "NIZAM_CONSUMER_TEST"],
            )
        finally:
            for k, old_v in os_env_backup.items():
                if old_v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = old_v

        ev_dir = consumer / ".agent" / "evidence" / "triv1"
        ev_dir.mkdir(parents=True, exist_ok=True)
        cand_path = ev_dir / "candidate.json"
        cand_path.write_bytes(wa_api.canonical(candidate))
        cap_proc = _run(
            [
                sys.executable,
                ".nizam/tools/start_path.py",
                "capture",
                "--id",
                "triv1",
                "--step",
                "qa",
                "--attempt",
                "1",
                "--output-dir",
                ".agent/evidence/triv1",
                "--candidate",
                str(cand_path),
                "--proof-kind",
                "success",
                "--agent-id",
                "consumer-evaluator",
                "--session-id",
                "consumer-qa-session",
                "--",
                *check_spec["argv"],
            ],
            cwd=consumer,
            env=qa_env,
        )
        cap_out = json.loads(cap_proc.stdout)
        self.assertTrue(cap_out["executed"])
        self.assertEqual(cap_out["exit_code"], 0)
        cap_ref = {
            "path": cap_out["capture_path"],
            "sha256": hashlib.sha256((consumer / cap_out["capture_path"]).read_bytes()).hexdigest(),
        }
        verdict = {
            "proof_version": 2,
            "feature_id": "triv1",
            "candidate_ref": {
                "path": cand_path.relative_to(consumer).as_posix(),
                "sha256": hashlib.sha256(cand_path.read_bytes()).hexdigest(),
            },
            "qa_pass": True,
            "checks_run": 1,
            "checks_passed": 1,
            "checks": [{"id": check_spec["id"], "capture": cap_ref}],
            "adversarial": {"performed": True},
            "evidence_files": [cap_out["capture_path"]],
            "issues": [],
            "unsupported_claims": [],
            "missing_acceptance_coverage": [],
            "required_fixes": [],
            "final_verdict": {"approved": True, "summary": "Executed installed consumer verification."},
        }
        qa_path = consumer / ".agent" / "qa" / "triv1.json"
        qa_path.write_bytes(wa_api.canonical(verdict))
        done_proc = _run(
            [sys.executable, ".nizam/tools/start_path.py", "done", "trivial", "--id", "triv1"],
            cwd=consumer,
            env=qa_env,
        )
        self.assertEqual(done_proc.returncode, 0)

        # 5. Exercise 1.0.0 text convergent review in consumer
        base_sha = _run(["git", "rev-parse", "HEAD"], cwd=consumer).stdout.strip()
        (consumer / "src" / "app.py").write_text("def greet() -> str:\n    return 'hello world'\n", encoding="utf-8")
        _run(["git", "add", "src/app.py"], cwd=consumer)
        _run(["git", "commit", "-m", "Update greet to hello world"], cwd=consumer)
        head_sha = _run(["git", "rev-parse", "HEAD"], cwd=consumer).stdout.strip()

        rev_dir = self.temp_dir / "n04-review"
        rev_dir.mkdir(parents=True)
        pkt_path = rev_dir / "packet.json"
        _run(
            [
                sys.executable,
                ".nizam/tools/convergent_review.py",
                "build-packet",
                "--repo",
                str(consumer),
                "--repository",
                "standalone/consumer",
                "--review-id",
                "n04-rev-1",
                "--mode",
                "ordinary",
                "--packet-version",
                "1.0.0",
                "--base",
                base_sha,
                "--head",
                head_sha,
                "--output",
                str(pkt_path),
            ],
            cwd=consumer,
        )
        pkt_obj = json.loads(pkt_path.read_text(encoding="utf-8"))
        self.assertEqual(pkt_obj["schema_version"], "1.0.0")
        pkt_sha = hashlib.sha256(pkt_path.read_bytes()).hexdigest()
        trial_paths = []
        for idx in (1, 2, 3):
            tp = rev_dir / f"trial-{idx}.json"
            trial_doc = {
                "schema_version": "1.0.0",
                "review_id": "n04-rev-1",
                "trial_number": idx,
                "packet_digest": pkt_sha,
                "head_sha": head_sha,
                "observations": [],
            }
            tp.write_bytes((json.dumps(trial_doc, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
            trial_paths.append(tp)
        out_dir = rev_dir / "published"
        _run(
            [
                sys.executable,
                ".nizam/tools/convergent_review.py",
                "converge",
                "--packet",
                str(pkt_path),
                "--trial",
                str(trial_paths[0]),
                "--trial",
                str(trial_paths[1]),
                "--trial",
                str(trial_paths[2]),
                "--output-dir",
                str(out_dir),
            ],
            cwd=consumer,
        )
        ledger = json.loads((out_dir / "ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["verdict"], "approve")

        # 6. Negative control: tampering with an installed .nizam file fails --verify-only
        readme_path = consumer / ".nizam" / "standard" / "README.md"
        orig_bytes = readme_path.read_bytes()
        try:
            readme_path.write_bytes(orig_bytes + b"\n<!-- drift -->\n")
            drift_proc = _run(
                [
                    "bash",
                    str(bootstrap_sh),
                    "--verify-only",
                    "--tag",
                    self.cand_tag,
                    "--allow-fixture-tag",
                    "--expected-sha",
                    self.cand_sha,
                    "--git-repo",
                    str(self.cand_repo),
                    "--require-content-integrity",
                    "--target",
                    str(consumer / ".nizam"),
                ],
                cwd=consumer,
                check=False,
            )
            self.assertNotEqual(drift_proc.returncode, 0)
        finally:
            readme_path.write_bytes(orig_bytes)

    def test_n08_extended_standalone_binary_review_and_external_evidence(self) -> None:
        """Node N08: 1.1.0 binary convergent review + generic external evidence admission + disabled/unknown profile behavior."""
        consumer = _init_disposable_consumer(self.temp_dir / "n08")
        bootstrap_sh = self.cand_repo / "bootstrap.sh"
        _run(
            [
                "bash",
                str(bootstrap_sh),
                "--tag",
                self.cand_tag,
                "--allow-fixture-tag",
                "--expected-sha",
                self.cand_sha,
                "--repo-url",
                f"file://{self.cand_repo}",
                "--target",
                str(consumer / ".nizam"),
            ],
            cwd=consumer,
        )
        _run(["git", "add", ".nizam"], cwd=consumer)
        _run(["git", "commit", "-m", "Install candidate .nizam payload"], cwd=consumer)

        # 1. Verify standalone operation works when external evidence integration is completely absent
        status_proc = _run([sys.executable, ".nizam/tools/start_path.py", "status", "--format", "json"], cwd=consumer)
        status_obj = json.loads(status_proc.stdout)
        self.assertTrue(status_obj["reconciled"])
        self.assertEqual(status_obj["contradictions"], [])

        # 2. Commit a binary asset + text change and run 1.1.0 binary convergent review
        base_sha = _run(["git", "rev-parse", "HEAD"], cwd=consumer).stdout.strip()
        (consumer / "assets").mkdir(exist_ok=True)
        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        (consumer / "assets" / "logo.png").write_bytes(png_bytes)
        (consumer / "src" / "app.py").write_text("def greet() -> str:\n    return 'binary-ready'\n", encoding="utf-8")
        _run(["git", "add", "assets/logo.png", "src/app.py"], cwd=consumer)
        _run(["git", "commit", "-m", "Add PNG logo and update app.py"], cwd=consumer)
        head_sha = _run(["git", "rev-parse", "HEAD"], cwd=consumer).stdout.strip()
        head_tree = _run(["git", "rev-parse", f"{head_sha}^{{tree}}"], cwd=consumer).stdout.strip()

        rev_dir = self.temp_dir / "n08-binary-review"
        rev_dir.mkdir(parents=True)
        pkt_path = rev_dir / "packet-1.1.json"
        _run(
            [
                sys.executable,
                ".nizam/tools/convergent_review.py",
                "build-packet",
                "--repo",
                str(consumer),
                "--repository",
                "standalone/consumer",
                "--review-id",
                "n08-rev-bin",
                "--mode",
                "ordinary",
                "--packet-version",
                "auto",
                "--base",
                base_sha,
                "--head",
                head_sha,
                "--output",
                str(pkt_path),
            ],
            cwd=consumer,
        )
        pkt_obj = json.loads(pkt_path.read_text(encoding="utf-8"))
        self.assertEqual(pkt_obj["schema_version"], "1.1.0")
        by_path = {entry["path"]: entry for entry in pkt_obj["review_files"]}
        self.assertEqual(by_path["assets/logo.png"]["record_kind"], "opaque_binary")
        self.assertEqual(by_path["assets/logo.png"]["validated_media_type"], "image/png")
        self.assertEqual(by_path["assets/logo.png"]["inspection_scope"], "integrity_only")
        self.assertEqual(by_path["src/app.py"]["record_kind"], "text")

        pkt_sha = hashlib.sha256(pkt_path.read_bytes()).hexdigest()
        trial_paths = []
        for idx in (1, 2, 3):
            tp = rev_dir / f"trial-{idx}.json"
            trial_doc = {
                "schema_version": "1.0.0",
                "review_id": "n08-rev-bin",
                "trial_number": idx,
                "packet_digest": pkt_sha,
                "head_sha": head_sha,
                "observations": [],
            }
            tp.write_bytes((json.dumps(trial_doc, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
            trial_paths.append(tp)
        out_dir = rev_dir / "published"
        _run(
            [
                sys.executable,
                ".nizam/tools/convergent_review.py",
                "converge",
                "--packet",
                str(pkt_path),
                "--trial",
                str(trial_paths[0]),
                "--trial",
                str(trial_paths[1]),
                "--trial",
                str(trial_paths[2]),
                "--output-dir",
                str(out_dir),
            ],
            cwd=consumer,
        )
        _run(
            [
                sys.executable,
                ".nizam/tools/convergent_review.py",
                "verify-replay",
                "--replay",
                str(out_dir / "replay.json"),
            ],
            cwd=consumer,
        )

        # 3. Exercise generic optional external evidence admission CLI inside consumer
        alloc_proc = _run(
            [
                sys.executable,
                ".nizam/tools/external_evidence.py",
                "allocate-attempt",
                "--root",
                str(consumer),
                "--task-id",
                "001",
                "--step-id",
                "qa",
                "--run-id",
                "run-n08-1",
                "--candidate-commit",
                head_sha,
            ],
            cwd=consumer,
        )
        alloc_res = json.loads(alloc_proc.stdout)
        permit = alloc_res["permit"]
        permit_digest = alloc_res["permit_digest"]
        permit_token = alloc_res["permit_token"]
        self.assertEqual(permit["attempt_number"], 1)
        self.assertEqual(permit["candidate_commit"], head_sha)

        # Write external evidence artifacts and contract
        ext_dir = consumer / ".agent" / "evidence" / "001"
        ext_dir.mkdir(parents=True, exist_ok=True)
        stdout_rel = ".agent/evidence/001/ext.stdout.txt"
        stderr_rel = ".agent/evidence/001/ext.stderr.txt"
        verdict_rel = ".agent/evidence/001/ext.verdict.json"
        stdout_raw = b"run n08: passed\n"
        stderr_raw = b""
        verdict_raw = b'{"executed_tests":4,"suite":"standalone-acceptance","test_outcome":"passed"}\n'
        (consumer / stdout_rel).write_bytes(stdout_raw)
        (consumer / stderr_rel).write_bytes(stderr_raw)
        (consumer / verdict_rel).write_bytes(verdict_raw)

        artifacts = [
            {
                "role": "stdout",
                "path": stdout_rel,
                "media_type": "text/plain; charset=utf-8",
                "byte_length": len(stdout_raw),
                "sha256": hashlib.sha256(stdout_raw).hexdigest(),
            },
            {
                "role": "stderr",
                "path": stderr_rel,
                "media_type": "text/plain; charset=utf-8",
                "byte_length": len(stderr_raw),
                "sha256": hashlib.sha256(stderr_raw).hexdigest(),
            },
            {
                "role": "verdict_report",
                "path": verdict_rel,
                "media_type": "application/json",
                "byte_length": len(verdict_raw),
                "sha256": hashlib.sha256(verdict_raw).hexdigest(),
            },
        ]
        exec_id = {
            "tool_id": "neutral-pytest-runner",
            "tool_version": "8.3.0",
            "adapter_id": "neutral-local-adapter",
            "adapter_version": "1.0.0",
            "config_digest": "77" * 32,
            "isolation_mode": "container",
            "isolation_digest": "88" * 32,
        }
        import importlib.util
        ee_spec = importlib.util.spec_from_file_location(
            "installed_consumer_external_evidence", consumer / ".nizam" / "tools" / "external_evidence.py"
        )
        assert ee_spec is not None and ee_spec.loader is not None
        ee_api = importlib.util.module_from_spec(ee_spec)
        ee_spec.loader.exec_module(ee_api)

        proof = ee_api.compute_producer_proof(
            permit_digest=permit_digest,
            permit_token=permit_token,
            candidate_commit=head_sha,
            candidate_tree=head_tree,
            execution_identity=exec_id,
            artifacts=artifacts,
            producer_id="neutral-verifier-worker",
            session_id="sess-20261027-n08",
            issued_at="2026-10-27T12:00:00Z",
        )
        contract_rel = ".agent/contracts/001.json"
        contract_doc = {
            "contract_id": "001",
            "status": "approved",
            "requirements": ["REQ-001"],
            "acceptance_criteria": ["AC-001"],
        }
        contract_bytes = ee_api.canonical_json_bytes(contract_doc) + b"\n"
        (consumer / contract_rel).write_bytes(contract_bytes)
        contract_digest = hashlib.sha256(contract_bytes).hexdigest()

        policy_id = "nizam-standalone-default"
        policy_ver = "1.0.0"
        policy_dig = "11" * 32
        fw_ver = json.loads((ROOT / "NIZAM.json").read_text(encoding="utf-8"))["framework"]["version"]
        fw_commit = self.cand_sha
        fw_tree = _run(["git", "rev-parse", f"{self.cand_sha}^{{tree}}"], cwd=self.cand_repo).stdout.strip()
        acc_dig = "55" * 32
        reg_dig = "66" * 32

        envelope = {
            "schema_version": "1.0.0",
            "protocol_version": "1.0.0",
            "profile_id": "generic-external-evidence-v1",
            "profile_version": "1.0.0",
            "policy_binding": {
                "policy_id": policy_id,
                "policy_version": policy_ver,
                "policy_digest": policy_dig,
            },
            "framework_identity": {
                "name": "nizam-framework",
                "version": fw_ver,
                "commit_sha": fw_commit,
                "tree_sha": fw_tree,
            },
            "consumer_binding": {
                "repository": "https://example.invalid/standalone/consumer.git",
                "base_commit": base_sha,
                "candidate_commit": head_sha,
                "candidate_tree": head_tree,
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
                "defect_signature": None,
                "operator_recovery_ref": permit["operator_recovery_ref"],
            },
            "contract_binding": {
                "contract_id": "001",
                "contract_digest": contract_digest,
                "requirement_ids": ["REQ-001"],
                "acceptance_criteria_ids": ["AC-001"],
            },
            "collection_binding": {
                "acceptance_collection_id": "acc-suite-v1",
                "acceptance_collection_digest": acc_dig,
                "regression_collection_id": "reg-suite-v1",
                "regression_collection_digest": reg_dig,
            },
            "execution_identity": exec_id,
            "producer_proof": proof,
            "status_separation": {
                "test_outcome": "passed",
                "execution_status": "completed",
                "admission_decision": "admitted",
            },
            "artifacts": artifacts,
        }
        env_file = self.temp_dir / "n08-envelope.json"
        env_file.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")

        admit_args = [
            sys.executable,
            ".nizam/tools/external_evidence.py",
            "admit-evidence",
            "--root",
            str(consumer),
            "--envelope",
            str(env_file),
            "--expected-policy-id",
            policy_id,
            "--expected-policy-version",
            policy_ver,
            "--expected-policy-digest",
            policy_dig,
            "--expected-framework-version",
            fw_ver,
            "--expected-framework-commit",
            fw_commit,
            "--expected-framework-tree",
            fw_tree,
            "--expected-contract-path",
            contract_rel,
            "--expected-acceptance-collection-digest",
            acc_dig,
            "--expected-regression-collection-digest",
            reg_dig,
        ]
        admit_proc = _run(admit_args, cwd=consumer)
        admit_res = json.loads(admit_proc.stdout)
        self.assertTrue(admit_res["ok"])
        self.assertFalse(admit_res["idempotent_replay"])

        # Idempotent duplicate delivery succeeds
        dup_proc = _run(admit_args, cwd=consumer)
        dup_res = json.loads(dup_proc.stdout)
        self.assertTrue(dup_res["idempotent_replay"])

        # Unknown profile_id fails closed
        bad_env = dict(envelope)
        bad_env["profile_id"] = "unknown-profile-v99"
        bad_env_file = self.temp_dir / "n08-bad-envelope.json"
        bad_env_file.write_text(json.dumps(bad_env, indent=2) + "\n", encoding="utf-8")
        bad_args = list(admit_args)
        bad_args[bad_args.index(str(env_file))] = str(bad_env_file)
        bad_proc = _run(bad_args, cwd=consumer, check=False)
        self.assertNotEqual(bad_proc.returncode, 0)
        self.assertIn("unsupported_profile", bad_proc.stderr)

        # Reconcile admission state
        rec_proc = _run(
            [
                sys.executable,
                ".nizam/tools/external_evidence.py",
                "reconcile",
                "--root",
                str(consumer),
            ],
            cwd=consumer,
        )
        rec_res = json.loads(rec_proc.stdout)
        self.assertTrue(rec_res["ok"])
        self.assertEqual(rec_res["permit_count"], 1)
        self.assertEqual(rec_res["admission_count"], 1)


if __name__ == "__main__":
    unittest.main()
