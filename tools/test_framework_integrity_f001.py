#!/usr/bin/env python3
"""Regression tests for framework-integrity findings 001/002/010
(contract framework-integrity-f001-1106). Standard library only; writes only
mktemp fixtures. Run:

  PYTHONDONTWRITEBYTECODE=1 python3 tools/test_framework_integrity_f001.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"
BOOTSTRAP = REPO / "bootstrap.sh"
VERSION = json.loads((REPO / "NIZAM.json").read_text())["framework"]["version"]
TAG = "v" + VERSION
env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "ALLOW_FIXTURE_TAG": "1"}


def bootstrap(target: str, ref: str | None, sha: str, src: str) -> tuple[int, str]:
    args = ["bash", str(BOOTSTRAP), "--repo-url", "file://" + src, "--tag", TAG,
            "--target", target, "--expected-sha", sha]
    if ref:
        args += ["--git-repo", ref]
    r = subprocess.run(args, capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


def make_fixture_repo() -> tuple[str, str]:
    """Clone the checkout into a temp dir, add the fixture tag, return (path, sha)."""
    w = tempfile.mkdtemp(prefix="f001-fixture-")
    src = os.path.join(w, "src")
    subprocess.run(["git", "clone", "-q", str(REPO), src], check=True, env=env)
    subprocess.run(["git", "-C", src, "config", "uploadpack.allowFilter", "true"],
                   check=True, env=env)
    subprocess.run(["git", "-C", src, "-c", "user.email=p@x", "-c", "user.name=p",
                    "tag", "-f", "-a", TAG, "-m", "fixture", "HEAD"],
                   check=True, capture_output=True, env=env)
    sha = subprocess.run(["git", "-C", src, "rev-parse", TAG + "^{commit}"],
                         check=True, capture_output=True, text=True, env=env).stdout.strip()
    return src, sha


def pif(payload_dir: str, src: str, sha: str) -> tuple[int, str]:
    """Drive tools/payload_integrity.py --git-repo against a fixture repo."""
    r = subprocess.run([sys.executable, str(TOOLS / "payload_integrity.py"),
                        "--payload-dir", payload_dir, "--git-repo", src,
                        "--expected-tag", TAG, "--expected-sha", sha,
                        "--expected-source-url", "file://" + src,
                        "--require-tag-ref", "--require-reference-tree"],
                       capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout + r.stderr)


class Test010LockSourceUrl(unittest.TestCase):
    def check(self, lock: dict, payload: dict) -> tuple[set[str], list[str]]:
        old = list(sys.path)
        sys.path.insert(0, str(TOOLS))
        try:
            import check_provenance_lock as c
        finally:
            sys.path = old
        failures = [l for l in c.check_lock(json.dumps(lock), json.dumps(payload))
                    if l.startswith("[PCL] FAIL")]
        return {f.split(":")[0].replace("[PCL] FAIL ", "") for f in failures}, failures

    def test_010(self):
        sha = "a" * 40
        url = "https://github.com/niq-cnr/nizam-framework.git"
        lock = {"framework_version": "3.1.3", "tag": "v3.1.3", "resolved_sha": sha,
                "declared_range": ">=3.1.0,<4.0.0", "source_url": url}
        payload = {"framework_version": "3.1.3", "tag": "v3.1.3", "resolved_sha": sha,
                   "source_url": url, "installed_at": "2026-11-05T00:00:00Z"}

        prefixes, fails = self.check(dict(lock), payload)
        self.assertEqual((prefixes, fails), (set(), []))

        # Positive supported variants: version/range/SHA and file:// URL.
        self.assertEqual(set(), self.check({**lock, "declared_range": "==3.1.3"}, payload)[0])
        self.assertEqual(set(), self.check({**lock, "source_url": "file:///tmp/fw/src"},
                                           {**payload, "source_url": "file:///tmp/fw/src"})[0])

        # Negative: mismatched URL -> lock-payload-drift.
        self.assertIn("lock-payload-drift",
                      self.check({**lock, "source_url": "https://evil.example/fork.git"}, payload)[0])

        # Negative: empty / null / whitespace / bad scheme / non-string -> lock-format.
        for bad in ("", None, "https://a b/c.git", "ftp://example.com/f.git", 7):
            prefixes, _ = self.check({**lock, "source_url": bad}, payload)
            self.assertIn("lock-format", prefixes, f"case source_url={bad!r}")
            self.assertTrue(prefixes <= {"lock-format", "lock-payload-drift"},
                            f"case source_url={bad!r} prefixes={prefixes}")

        # Exact comparison: trailing slash or .git difference is a mismatch, never normalised.
        for variant in (url + "/", url[:-4]):
            self.assertIn("lock-payload-drift",
                          self.check({**lock, "source_url": variant}, payload)[0], f"variant={variant!r}")
        # Recordable forms bootstrap.sh --repo-url may write verbatim must be accepted.
        for ok_url in ("ssh://git@example.com/fw.git", "git@example.com:org/fw.git",
                        "/srv/git/fw.git", "http://mirror.local/fw.git"):
            self.assertEqual(set(), self.check({**lock, "source_url": ok_url},
                                               {**payload, "source_url": ok_url})[0], f"ok={ok_url!r}")

        # Negative: missing key -> lock-shape (stable, never silent).
        prefixes, _ = self.check({k: v for k, v in lock.items() if k != "source_url"}, payload)
        self.assertIn("lock-shape", prefixes)


class Test001PayloadIntegrity(unittest.TestCase):
    CLS_SRC: str
    CLS_SHA: str
    CLS_W: str

    @classmethod
    def setUpClass(cls):
        cls.CLS_W = tempfile.mkdtemp(prefix="f001-pl-")
        cls.CLS_SRC, cls.CLS_SHA = make_fixture_repo()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.CLS_W, ignore_errors=True)

    def test_001(self):
        src, sha = self.CLS_SRC, self.CLS_SHA
        consumer = os.path.join(self.CLS_W, "c" + os.urandom(3).hex())
        os.makedirs(consumer)
        rc, out = bootstrap(os.path.join(consumer, ".nizam"), None, sha, src)
        self.assertEqual(0, rc, out)
        payload = os.path.join(consumer, ".nizam")

        prov = json.loads(Path(payload, "provenance.json").read_text())

        # (i) Lock-free payload still verifies (the verifier must not demand it).
        rc_i, out_i = pif(payload, src, sha)
        self.assertEqual(0, rc_i, out_i)

        # (ii) Consumer adds the lock derived from provenance.json -> rc 0.
        lock = {"framework_version": prov["framework_version"], "tag": prov["tag"],
                "resolved_sha": prov["resolved_sha"], "declared_range": ">=" + VERSION,
                "source_url": prov["source_url"]}
        Path(payload, "provenance.lock.json").write_text(json.dumps(lock))
        rc_ii, out_ii = pif(payload, src, sha)
        self.assertEqual(0, rc_ii, out_ii)

        # (iii) Same payload plus one extra non-lock file -> rc 1 inventory drift.
        Path(payload, "extra-file.txt").write_text("junk")
        rc_iii, out_iii = pif(payload, src, sha)
        self.assertNotEqual(0, rc_iii, out_iii)
        self.assertIn("extra", out_iii)

    def test_001_reinstall_preserves_lock(self):
        src, sha = self.CLS_SRC, self.CLS_SHA
        consumer = os.path.join(self.CLS_W, "c" + os.urandom(3).hex())
        os.makedirs(consumer)
        payload = os.path.join(consumer, ".nizam")
        rc, out = bootstrap(payload, None, sha, src)
        self.assertEqual(0, rc, out)
        prov = json.loads(Path(payload, "provenance.json").read_text())
        lock = {"framework_version": prov["framework_version"], "tag": prov["tag"],
                "resolved_sha": prov["resolved_sha"], "declared_range": ">=" + VERSION,
                "source_url": prov["source_url"]}
        lock_path = Path(payload, "provenance.lock.json")
        lock_path.write_text(json.dumps(lock, indent=2))
        original = lock_path.read_bytes()

        # Reinstall (upgrade) over the existing target: lock must be retained
        # byte-for-byte and the installed payload must verify with the lock.
        rc, out = bootstrap(payload, None, sha, src)
        self.assertEqual(0, rc, out)
        self.assertTrue(lock_path.exists(), "lock lost after reinstall")
        self.assertEqual(original, lock_path.read_bytes(), "lock mutated after reinstall")
        rc, out = pif(payload, src, sha)
        self.assertEqual(0, rc, out)


def assert_outside_target_cases(cls_w: str) -> dict[str, tuple[str, str, bool]]:
    return {
        "equal": (f"{cls_w}/x", f"{cls_w}/x", False),
        "candidate-inside-target": (f"{cls_w}/x/sub", f"{cls_w}/x", False),
        "target-inside-candidate": (f"{cls_w}", f"{cls_w}/x", False),
        "sibling": (f"{cls_w}/y", f"{cls_w}/x", True),
        "root-as-ancestor-of-target": ("/", f"{cls_w}/x", False),
        "trailing-slash-equal": (f"{cls_w}/x/", f"{cls_w}/x", False),
    }


class Test002BootstrapOverlap(unittest.TestCase):
    CLS_SRC: str
    CLS_SHA: str
    CLS_W: str

    @classmethod
    def setUpClass(cls):
        cls.CLS_W = tempfile.mkdtemp(prefix="f002-")
        cls.CLS_SRC, cls.CLS_SHA = make_fixture_repo()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.CLS_W, ignore_errors=True)

    def test_assert_outside_target(self):
        text = BOOTSTRAP.read_text()
        start = text.index("# Confirms candidate path")
        end = text.index("\n}\n", start) + 3
        helper = Path(self.CLS_W, "guard.sh")
        helper.write_text('die() { echo "DIE $*"; exit 1; }\n' + text[start:end])
        for label, (cand, targ, ok) in assert_outside_target_cases(self.CLS_W).items():
            r = subprocess.run(["bash", "-c",
                                f"source '{helper}'\nassert_outside_target '{cand}' '{targ}' '{label}'"],
                               capture_output=True, text=True)
            self.assertEqual(ok, r.returncode == 0,
                             f"label={label} rc={r.returncode} out={r.stdout} err={r.stderr}")

    def test_002_installed_paths(self):
        src, sha = self.CLS_SRC, self.CLS_SHA
        B = self.CLS_W
        cases = {"equal": ("eq", "eq", "eq"), "descendant": ("de", "de", "de"),
                 "ancestor": ("an", "an", "an"), "disjoint": ("dj", "dj", "dj")}
        results = {}
        for name, (holder, target_rel, ref_rel) in cases.items():
            root = os.path.join(B, name)
            self.addCleanup(shutil.rmtree, root, ignore_errors=True)
            proj = os.path.join(root, holder)
            Path(proj).mkdir(parents=True)
            Path(proj, "SENTINEL.txt").write_text("sentinel")
            target = os.path.join(proj, ".nizam")
            ref = {"equal": target, "descendant": os.path.join(target, "ref"),
                   "ancestor": proj, "disjoint": os.path.join(root, "ref-sibling")}[name]
            results[name] = (bootstrap(target, ref, sha, src), Path(proj, "SENTINEL.txt").exists())

        for name in ("equal", "descendant", "ancestor"):
            (rc, out), sentinel = results[name]
            self.assertNotEqual(0, rc, f"{name} must be rejected: {out[-400:]}")
            self.assertTrue(sentinel, f"{name} sentinel deleted")

        (rc, out), sentinel = results["disjoint"]
        self.assertEqual(0, rc, out)
        self.assertTrue(sentinel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
