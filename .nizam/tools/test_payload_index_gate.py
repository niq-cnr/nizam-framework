#!/usr/bin/env python3
"""H-18 regression: `validate.sh --payload` must judge the Git INDEX, not the worktree.

Scenarios (each runs the real --payload gate in a private Git repository):

* clean payload passes, reading from the index;
* a defect staged and then restored in the worktree is still caught (the staged bytes ship);
* an unstaged worktree-only edit does not change the result;
* UNTRACKED-LIBRARY: `tools/verify_lib.sh` exists only in the index, not on disk. The validator must
  find it and must not emit `FATAL: required library tools/verify_lib.sh not found`. This fails against
  any implementation that validates a temp export without the library, and is the regression that keeps
  the suite from staying green while the FATAL remains.

The payload is laid out either as the repository root or nested under `.nizam/` (a consumer repo).
"""

from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_DIRS = ("standard", "templates", "methodology", "ecosystem", "schema", "tools")
DEFECT_FILE = "standard/NDS.md"
LIBRARY = "tools/verify_lib.sh"
FATAL_LIBRARY = "FATAL: required library tools/verify_lib.sh not found"


def _git(repo, *args, input_text=None):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, input=input_text
    )


class PayloadIndexGateBase(unittest.TestCase):
    """Shared scenarios. Concrete subclasses pick the payload layout; the base is never run directly."""

    layout = None  # "root" or "nested"

    def setUp(self):
        if self.layout is None:
            self.skipTest("abstract base")
        self.tmp = Path(tempfile.mkdtemp(prefix="payload-index-gate-"))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.email", "t@t")
        _git(self.repo, "config", "user.name", "t")
        payload = self.repo if self.layout == "root" else self.repo / ".nizam"
        payload.mkdir(parents=True, exist_ok=True)
        for d in PAYLOAD_DIRS:
            shutil.copytree(ROOT / d, payload / d, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(ROOT / "NIZAM.json", payload / "NIZAM.json")
        if (ROOT / "provenance.json").exists():
            shutil.copy(ROOT / "provenance.json", payload / "provenance.json")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-qm", "base payload")
        self.payload = payload
        self.target = payload / DEFECT_FILE

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_gate(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(
            ["bash", str(self.payload / "tools" / "validate.sh"), "--payload"],
            cwd=str(self.repo), env=env, text=True, capture_output=True,
        )

    def test_clean_payload_passes_from_index(self):
        result = self._run_gate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("source=index", result.stdout)
        self.assertIn("10 exercised passed, 0 failed", result.stdout)

    def test_staged_defect_fails_even_after_worktree_restored(self):
        # Stage the defect, then restore the pristine worktree copy: the index still carries the defect.
        pristine = self.target.read_bytes()
        defect = b"\n".join(line for line in pristine.split(b"\n") if not line.startswith(b"status:"))
        self.target.write_bytes(defect)
        _git(self.repo, "add", "--", str(self.target.relative_to(self.repo)))
        self.target.write_bytes(pristine)

        result = self._run_gate()
        self.assertNotEqual(result.returncode, 0, "gate passed a staged defect:\n" + result.stdout)
        self.assertIn(DEFECT_FILE, result.stdout)

    def test_unstaged_worktree_defect_does_not_affect_index_gate(self):
        # Worktree-only edit that is not staged: the commit ships the index, so the gate must pass.
        self.target.write_bytes(b"not frontmatter at all\n")
        result = self._run_gate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_library_present_only_in_index_is_found_not_fatal(self):
        # UNTRACKED-LIBRARY regression. verify_lib.sh is staged but absent from the worktree.
        lib_path = self.payload / LIBRARY
        lib_bytes = lib_path.read_bytes()
        _git(self.repo, "rm", "-q", "--cached", "--", str(lib_path.relative_to(self.repo)))
        _git(self.repo, "add", "--", str(lib_path.relative_to(self.repo)))
        lib_path.unlink()  # staged in the index, not on disk
        self.assertFalse(lib_path.exists())
        self.assertEqual(
            _git(self.repo, "show", f":{lib_path.relative_to(self.repo).as_posix()}").stdout.encode(),
            lib_bytes,
        )

        result = self._run_gate()
        combined = result.stdout + result.stderr
        self.assertNotIn(FATAL_LIBRARY, combined, combined)
        self.assertEqual(result.returncode, 0, combined)
        self.assertIn("10 exercised passed, 0 failed", result.stdout)


class RootLayoutPayloadIndexGateTests(PayloadIndexGateBase):
    layout = "root"


class NestedLayoutPayloadIndexGateTests(PayloadIndexGateBase):
    layout = "nested"


if __name__ == "__main__":
    unittest.main()
