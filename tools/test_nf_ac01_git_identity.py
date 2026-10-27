#!/usr/bin/env python3
"""NF-AC01 acceptance suite: immutable Git identity observation across Nizam tools.

Covers Finding F02 and requirement NF-R01:
- Commit and blob replacement refs (default and custom namespaces)
- GIT_DIR, GIT_WORK_TREE, GIT_INDEX_FILE, GIT_OBJECT_DIRECTORY,
  GIT_ALTERNATE_OBJECT_DIRECTORIES, GIT_COMMON_DIR, GIT_NAMESPACE,
  GIT_REPLACE_REF_BASE, and GIT_CONFIG_* environment/config injection
- Local .git/info/grafts, .git/objects/info/alternates, and core.worktree redirection
- Wrong roots (subdirectories, non-repos, symlinked roots, symlinked .git metadata)
- Legitimate detached HEAD and linked worktrees (`git worktree add`)
- Absent objects vs Git command failures (`is_missing_object`)
- Symlinks (120000), mode changes (100644 -> 100755), and pathspec-looking names
- Clean, staged, unstaged, untracked, and committed deltas
- Unchanged HEAD, refs, and index after read-only inspection
- Actual receipt consumption (`_receipt_candidate` & `verify_stage_receipt`) rejecting `git replace A B`
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import convergent_review as cr  # noqa: E402
import git_seam  # noqa: E402
import payload_integrity as pi  # noqa: E402
import start_path as sp  # noqa: E402
import workflow_assurance as wa  # noqa: E402


ORIGIN_URL = "https://github.com/niq-cnr/nizam-framework.git"
ENV_VAR = "NIZAM_NF_AC01_ENV"


def _git_raw(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
    ).strip()


def _init_disposable_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "--object-format=sha1", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "nf-ac01@example.test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "NF AC01"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "commit.gpgsign", "false"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "core.autocrlf", "false"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "core.filemode", "true"], check=True)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", ORIGIN_URL], check=True)
    return repo


def _populate_assessed_repo(repo: Path, source_bytes: bytes = b"VALUE = 'original'\n") -> dict[str, list[str]]:
    inputs = {
        "source": ["src/app.py"],
        "tests": ["tests/test_app.py"],
        "tools": ["tools/runner.sh"],
        "contracts": ["contracts/c1.json"],
        "unknown_dependencies": [],
    }
    (repo / "src").mkdir(parents=True, exist_ok=True)
    (repo / "tests").mkdir(parents=True, exist_ok=True)
    (repo / "tools").mkdir(parents=True, exist_ok=True)
    (repo / "contracts").mkdir(parents=True, exist_ok=True)
    (repo / "src/app.py").write_bytes(source_bytes)
    (repo / "tests/test_app.py").write_bytes(b"def test_ok():\n    assert True\n")
    (repo / "tools/runner.sh").write_bytes(b"#!/bin/sh\nexit 0\n")
    (repo / "tools/runner.sh").chmod(0o755)
    (repo / "contracts/c1.json").write_bytes(b'{"status": "approved"}\n')
    subprocess.run(["git", "-C", str(repo), "add", "--all"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "anchor commit"], check=True)
    return inputs


class NfAc01GitIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(
            tempfile.mkdtemp(
                prefix="nizam-nf-ac01-",
                dir="/private/tmp" if Path("/private/tmp").is_dir() else None,
            )
        ).resolve()
        self.saved_env = os.environ.get(ENV_VAR)
        os.environ[ENV_VAR] = "ac01-baseline"

    def tearDown(self) -> None:
        if self.saved_env is None:
            os.environ.pop(ENV_VAR, None)
        else:
            os.environ[ENV_VAR] = self.saved_env
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _snapshot_git_state(self, repo: Path) -> dict[str, object]:
        git_dir = repo / ".git"
        if git_dir.is_file():
            raw = git_dir.read_text(encoding="utf-8").strip()
            git_dir = (repo / raw[len("gitdir: "):]).resolve()
        head_bytes = (git_dir / "HEAD").read_bytes()
        index_path = git_dir / "index"
        index_sha = hashlib.sha256(index_path.read_bytes()).hexdigest() if index_path.exists() else None
        refs = subprocess.run(
            ["git", "-C", str(repo), "show-ref"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        return {
            "head": hashlib.sha256(head_bytes).hexdigest(),
            "index": index_sha,
            "refs": refs,
        }

    def test_f02_commit_and_blob_replace_refs_rejected_in_helpers_and_receipt_consumption(self) -> None:
        """Reproduce Finding F02 (`git replace A B`) and prove rejection in assess_repository, _receipt_candidate, and verify_stage_receipt."""
        repo = _init_disposable_repo(self.temp_dir)
        inputs = _populate_assessed_repo(repo, b"VALUE = 'original'\n")
        commit_a = _git_raw(repo, "rev-parse", "HEAD")
        tree_a = _git_raw(repo, "rev-parse", f"{commit_a}^{{tree}}")
        blob_a = _git_raw(repo, "rev-parse", f"{commit_a}:src/app.py")

        candidate_a = wa.assess_repository(repo, commit_a, inputs, [ENV_VAR])
        self.assertEqual(candidate_a["source_commit"], commit_a)
        self.assertEqual(candidate_a["source_tree"], tree_a)
        self.assertIsNone(wa._receipt_candidate(repo, candidate_a, commit_a))

        # Create commit B with modified src/app.py
        (repo / "src/app.py").write_bytes(b"VALUE = 'tampered'\n")
        subprocess.run(["git", "-C", str(repo), "add", "src/app.py"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "commit B"], check=True)
        commit_b = _git_raw(repo, "rev-parse", "HEAD")
        tree_b = _git_raw(repo, "rev-parse", f"{commit_b}^{{tree}}")
        blob_b = _git_raw(repo, "rev-parse", f"{commit_b}:src/app.py")
        candidate_b = wa.assess_repository(repo, commit_b, inputs, [ENV_VAR])

        # Without replacement, candidate_b with source_commit forged to commit_a fails:
        forged_candidate = copy.deepcopy(candidate_b)
        forged_candidate["source_commit"] = commit_a
        forged_candidate["identity_sha256"] = wa.sha(
            wa.canonical({k: v for k, v in forged_candidate.items() if k != "identity_sha256"})
        )
        with self.assertRaises(wa.AssuranceError):
            wa._receipt_candidate(repo, forged_candidate, commit_b)

        # Attack F02: introduce `git replace commit_a commit_b`, `git replace blob_a blob_b`, and custom replace ref namespace
        subprocess.run(["git", "-C", str(repo), "replace", commit_a, commit_b], check=True)
        subprocess.run(["git", "-C", str(repo), "replace", blob_a, blob_b], check=True)
        subprocess.run(
            ["git", "-C", str(repo), "update-ref", f"refs/custom-replace/{commit_a}", commit_b],
            check=True,
        )
        subprocess.run(["git", "-C", str(repo), "config", "core.useReplaceRefs", "true"], check=True)

        # Ambient git (without --no-replace-objects) observes commit_b's tree when resolving commit_a:
        ambient_tree = _git_raw(repo, "rev-parse", f"{commit_a}^{{tree}}")
        self.assertEqual(ambient_tree, tree_b)

        poison_env = {
            "GIT_REPLACE_REF_BASE": "refs/custom-replace/",
            "GIT_NAMESPACE": "poison-ns",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.useReplaceRefs",
            "GIT_CONFIG_VALUE_0": "true",
        }
        old_env = {k: os.environ.get(k) for k in poison_env}
        try:
            os.environ.update(poison_env)
            # 1. git_seam and wa.git / wa.blobs must still observe commit_a's true tree and blob_a's true bytes
            self.assertEqual(wa.git(repo, "rev-parse", f"{commit_a}^{{tree}}").decode().strip(), tree_a)
            self.assertEqual(wa.blobs(repo, [blob_a])[blob_a], b"VALUE = 'original'\n")

            # 2. _receipt_candidate MUST REJECT forged_candidate even when `git replace commit_a commit_b` is active!
            with self.assertRaisesRegex(wa.AssuranceError, "receipt candidate actual tree"):
                wa._receipt_candidate(repo, forged_candidate, commit_b)

            # 3. Actual verify_stage_receipt consumption MUST REJECT a receipt carrying forged_candidate!
            ref_c1 = {
                "path": "contracts/c1.json",
                "sha256": wa.sha(b'{"status": "approved"}\n'),
                "revision": commit_a,
            }
            forged_policy = {
                "schema_version": 1,
                "repository": ORIGIN_URL,
                "feature_id": "130",
                "stage": "qa-passed",
                "operation_id": "op-f02",
                "candidate": forged_candidate,
                "contract": ref_c1,
                "operator": ref_c1,
                "producer": {"agent_id": "test-agent", "session_id": "test-session"},
                "prerequisites": [],
                "commands": [
                    {
                        "argv": ["true"],
                        "expected_exit": 0,
                        "proof_kind": "success",
                        "diagnostic": "ok",
                        "capture": ref_c1,
                    }
                ],
                "from_status": "in_progress",
                "to_status": "qa_passed",
                "at": "2026-10-27T10:00:00Z",
                "recovery": None,
            }
            forged_receipt = {
                "schema_version": 1,
                "repository": ORIGIN_URL,
                "feature_id": "130",
                "stage": "qa-passed",
                "operation_id": "op-f02",
                "status": "passed",
                "candidate": forged_candidate,
                "producer": {"agent_id": "test-agent", "session_id": "test-session"},
                "contract_ref": forged_policy["contract"],
                "operator_ref": forged_policy["operator"],
                "prerequisites": [],
                "checks": [],
                "verdict": {
                    "final_verdict": {"approved": True, "summary": "ok"},
                    "issues": [],
                    "missing_acceptance_coverage": [],
                    "unsupported_claims": [],
                },
            }
            with self.assertRaisesRegex(wa.AssuranceError, "receipt candidate actual tree"):
                wa.verify_stage_receipt(repo, forged_receipt, policy=forged_policy)

            # 4. assess_repository at commit_a (when checked out to commit_b) still observes true commit_a and rejects because src/app.py bytes changed
            with self.assertRaisesRegex(wa.AssuranceError, "unknown/assessed bytes changed: src/app.py"):
                wa.assess_repository(repo, commit_a, inputs, [ENV_VAR])

            # 5. convergent_review packet builder ignores replace refs and reads true old/new blobs
            packet = cr.build_packet_from_git(repo, "host/org/repo", "nf-ac01-pkt", "full_audit", commit_a, commit_b)
            self.assertEqual(packet["delta"][0]["old_content"], "VALUE = 'original'\n")

            # 6. start_path _get_committed_blob_info reads unreplaced blob_a at commit_a
            info_a = sp._get_committed_blob_info(repo, commit_a, "src/app.py")
            self.assertIsNotNone(info_a)
            assert info_a is not None
            self.assertEqual(info_a[0], "100644")
            self.assertEqual(info_a[1], hashlib.sha256(b"VALUE = 'original'\n").hexdigest())

            # 7. payload_integrity _repo_has_commit works through hardened seam
            self.assertTrue(pi._repo_has_commit(repo, commit_a))
        finally:
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_environment_and_config_redirection_rejected_or_neutralized(self) -> None:
        """Verify GIT_DIR, GIT_WORK_TREE, GIT_INDEX_FILE, GIT_OBJECT_DIRECTORY, alternates, grafts, and core.worktree are blocked."""
        repo = _init_disposable_repo(self.temp_dir)
        _populate_assessed_repo(repo, b"legit\n")
        legit_head = _git_raw(repo, "rev-parse", "HEAD")

        decoy = _init_disposable_repo(self.temp_dir / "decoy-holder")
        _populate_assessed_repo(decoy, b"decoy\n")
        decoy_head = _git_raw(decoy, "rev-parse", "HEAD")
        self.assertNotEqual(legit_head, decoy_head)

        injected_env = {
            "GIT_DIR": str(decoy / ".git"),
            "GIT_WORK_TREE": str(decoy),
            "GIT_INDEX_FILE": str(decoy / ".git/index"),
            "GIT_OBJECT_DIRECTORY": str(decoy / ".git/objects"),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(decoy / ".git/objects"),
            "GIT_COMMON_DIR": str(decoy / ".git"),
            "GIT_CONFIG_PARAMETERS": "'core.worktree=" + str(decoy) + "'",
        }
        saved = {k: os.environ.get(k) for k in injected_env}
        try:
            os.environ.update(injected_env)
            observed = git_seam.run_git_readonly(repo, "rev-parse", "HEAD").decode("ascii").strip()
            self.assertEqual(observed, legit_head)
            sp_res = sp._run_git_readonly(repo, ["rev-parse", "HEAD"], text=True)
            self.assertEqual(sp_res.returncode, 0)
            self.assertEqual(sp_res.stdout.strip(), legit_head)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

        # Local .git/info/grafts must fail closed
        grafts = repo / ".git/info/grafts"
        grafts.parent.mkdir(parents=True, exist_ok=True)
        grafts.write_text(f"{legit_head}\n", encoding="utf-8")
        try:
            with self.assertRaisesRegex(git_seam.GitSeamError, "grafts"):
                git_seam.validate_repo_root(repo)
        finally:
            grafts.unlink()

        # Symlinked .git/objects/info/alternates must fail closed
        alternates = repo / ".git/objects/info/alternates"
        alternates.parent.mkdir(parents=True, exist_ok=True)
        alternates.symlink_to(decoy / ".git/objects")
        try:
            with self.assertRaisesRegex(git_seam.GitSeamError, "alternates"):
                git_seam.validate_repo_root(repo)
        finally:
            alternates.unlink()

        # Local core.worktree redirection in .git/config must fail closed
        subprocess.run(["git", "-C", str(repo), "config", "core.worktree", str(decoy)], check=True)
        try:
            with self.assertRaisesRegex(git_seam.GitSeamError, "core.worktree"):
                git_seam.validate_repo_root(repo)
        finally:
            subprocess.run(["git", "-C", str(repo), "config", "--unset", "core.worktree"], check=True)

    def test_wrong_roots_and_legitimate_linked_and_detached_worktrees(self) -> None:
        """Reject non-repos, subdirectories, and symlinked roots while preserving detached and linked worktrees."""
        repo = _init_disposable_repo(self.temp_dir)
        inputs = _populate_assessed_repo(repo, b"hello\n")
        head = _git_raw(repo, "rev-parse", "HEAD")

        # Subdirectory is rejected as repo root
        sub = repo / "src"
        with self.assertRaisesRegex(git_seam.GitSeamError, "toplevel"):
            git_seam.validate_repo_root(sub)
        with self.assertRaises(wa.AssuranceError):
            wa.assess_repository(sub, head, inputs, [ENV_VAR])

        # Non-repo directory is rejected
        non_repo = self.temp_dir / "not-a-repo"
        non_repo.mkdir()
        with self.assertRaisesRegex(git_seam.GitSeamError, "toplevel"):
            git_seam.validate_repo_root(non_repo)

        # Symlinked repo root is rejected
        symlink_root = self.temp_dir / "symlink-repo"
        symlink_root.symlink_to(repo, target_is_directory=True)
        with self.assertRaisesRegex(git_seam.GitSeamError, "symlink"):
            git_seam.validate_repo_root(symlink_root)

        # Detached HEAD worktree is accepted
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", "--detach", head], check=True)
        assessed_detached = wa.assess_repository(repo, head, inputs, [ENV_VAR])
        self.assertEqual(assessed_detached["source_commit"], head)

        # Linked worktree (`git worktree add`) is accepted
        linked_wt = self.temp_dir / "linked-wt"
        subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", "--detach", str(linked_wt), head], check=True)
        assessed_linked = wa.assess_repository(linked_wt, head, inputs, [ENV_VAR])
        self.assertEqual(assessed_linked["source_commit"], head)

    def test_absent_objects_versus_git_errors_distinguished(self) -> None:
        """Distinguish missing Git objects (is_missing_object=True) from corrupt/non-blob/command errors."""
        repo = _init_disposable_repo(self.temp_dir)
        _populate_assessed_repo(repo, b"alpha\n")
        head = _git_raw(repo, "rev-parse", "HEAD")

        # Absent path in tree returns None (not an exception)
        self.assertIsNone(git_seam.resolve_git_path_entry(repo, head, "nonexistent.txt"))

        # Absent object OID raises GitSeamError with is_missing_object=True
        missing_oid = "0" * 40
        with self.assertRaises(git_seam.GitSeamError) as ctx_missing:
            git_seam.read_git_blob(repo, missing_oid)
        self.assertTrue(ctx_missing.exception.is_missing_object)

        # Passing a commit OID to read_git_blob raises GitSeamError with is_missing_object=False (non-blob object)
        with self.assertRaises(git_seam.GitSeamError) as ctx_nonblob:
            git_seam.read_git_blob(repo, head)
        self.assertFalse(ctx_nonblob.exception.is_missing_object)

        # Invalid/corrupt repo root raises GitSeamError with is_missing_object=False
        with self.assertRaises(git_seam.GitSeamError) as ctx_bad_repo:
            git_seam.run_git_readonly(self.temp_dir / "missing-repo", "status")
        self.assertFalse(ctx_bad_repo.exception.is_missing_object)

    def test_symlinks_modes_pathspec_names_deltas_and_read_only_invariance(self) -> None:
        """Verify symlinks, mode changes, pathspec-looking names, dirty/staged/untracked states, and read-only invariance."""
        repo = _init_disposable_repo(self.temp_dir)
        weird_name = ":(icase)*[glob]?.txt"
        script_name = "run.sh"
        link_name = "link.txt"

        (repo / weird_name).write_text("literal-one\n", encoding="utf-8")
        (repo / script_name).write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
        (repo / link_name).symlink_to(script_name)
        subprocess.run(
            ["git", "-C", str(repo), "--literal-pathspecs", "add", "--", weird_name, script_name, link_name],
            check=True,
        )
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
        base = _git_raw(repo, "rev-parse", "HEAD")

        # Mode change + literal pathspec content change
        (repo / script_name).chmod(0o755)
        (repo / weird_name).write_text("literal-two\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(repo), "--literal-pathspecs", "add", "--", weird_name, script_name],
            check=True,
        )

        # Staged conflict detected by start_path
        with self.assertRaises(sp.StartPathError):
            sp._verify_git_status_and_no_staged_conflicts(repo, [weird_name], check_staged_conflicts=True)

        # Commit the staged changes
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "head"], check=True)
        head = _git_raw(repo, "rev-parse", "HEAD")

        # Snapshot HEAD/refs/index before read-only inspections
        before = self._snapshot_git_state(repo)

        entry_weird = git_seam.resolve_git_path_entry(repo, head, weird_name)
        self.assertIsNotNone(entry_weird)
        assert entry_weird is not None
        self.assertEqual(entry_weird[0], "100644")

        entry_script = git_seam.resolve_git_path_entry(repo, head, script_name)
        self.assertIsNotNone(entry_script)
        assert entry_script is not None
        self.assertEqual(entry_script[0], "100755")

        entry_link = git_seam.resolve_git_path_entry(repo, head, link_name)
        self.assertIsNotNone(entry_link)
        assert entry_link is not None
        self.assertEqual(entry_link[0], "120000")

        info_w = sp._get_committed_blob_info(repo, head, weird_name)
        self.assertIsNotNone(info_w)
        assert info_w is not None
        self.assertEqual(info_w[0], "100644")
        self.assertEqual(info_w[1], hashlib.sha256(b"literal-two\n").hexdigest())

        last_commit = sp._find_last_commit_for_paths(repo, head, [weird_name])
        self.assertEqual(last_commit, head)

        packet = cr.build_packet_from_git(repo, "host/org/repo", "nf-ac01-modes", "full_audit", base, head)
        self.assertEqual(packet["head_sha"], head)

        after = self._snapshot_git_state(repo)
        self.assertEqual(before, after, "read-only Git inspection must not mutate HEAD, index, or refs")


if __name__ == "__main__":
    unittest.main()
