#!/usr/bin/env python3
"""NF-AC02 acceptance suite: installation/activation and finite recovery policy reconciliation.

Covers Findings F10 & F11 and requirement NF-R02:
- Finding F10 (standard/GIP.md): complete atomic 6-module+index .nizam/ payload required;
  Section 5.2 expresses proportionate workflow activation in external consumer config;
  partial/missing-module .nizam/ payloads are rejected by payload_integrity.py and validate.sh --payload.
- Finding F11 (methodology/03_circuit_breaker.md & start_path.py): Section 6 routes continuation
  through finite scoped operator_recovery without resetting attempt counters to 0;
  runtime enforces 3-attempt same-signature and 6-attempt task ceilings, preserves history,
  rejects forged/infinite/unauthenticated recovery, and stops again at the new finite ceiling.
"""

from __future__ import annotations

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

import payload_integrity as pi  # noqa: E402
import start_path as sp  # noqa: E402


class NfAc02PolicyReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(
            tempfile.mkdtemp(
                prefix="nizam-nf-ac02-",
                dir="/private/tmp" if Path("/private/tmp").is_dir() else None,
            )
        ).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_f10_gip_prose_and_complete_payload_enforcement(self) -> None:
        """Verify GIP.md resolves Finding F10 and validators reject partial/missing-module payloads."""
        gip_text = (ROOT_DIR / "standard/GIP.md").read_text(encoding="utf-8")
        # Split frontmatter from body so change_log history is distinguished from active normative prose
        parts = gip_text.split("---", 2)
        self.assertEqual(len(parts), 3)
        body = parts[2]

        self.assertNotIn("The consumer inherits `standard/` alone", body)
        self.assertIn("complete, atomic,\nverified six-module-plus-index payload", body)
        self.assertIn("Tier 1 — `docs-standard-only` (workflow activation).", body)
        self.assertIn("Tier 2 — `templates` (workflow activation).", body)
        self.assertIn("Tier 3 — `full loop` (workflow activation).", body)

        # Stage a complete consumer payload from current ROOT_DIR and verify it passes payload_integrity
        payload_dir = self.temp_dir / "consumer/.nizam"
        payload_dir.mkdir(parents=True, exist_ok=True)
        for mod in ("standard", "templates", "schema", "tools", "methodology", "ecosystem"):
            shutil.copytree(ROOT_DIR / mod, payload_dir / mod)
        shutil.copy2(ROOT_DIR / "NIZAM.json", payload_dir / "NIZAM.json")
        prov = json.loads((ROOT_DIR / ".nizam/provenance.json").read_text(encoding="utf-8"))
        root_ver = json.loads((ROOT_DIR / "NIZAM.json").read_text(encoding="utf-8"))["framework"]["version"]
        prov["framework_version"] = root_ver
        prov["tag"] = f"v{root_ver}"
        (payload_dir / "provenance.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8")

        res_ok = subprocess.run(
            [
                sys.executable,
                str(ROOT_DIR / "tools/payload_integrity.py"),
                "--payload-dir",
                str(payload_dir),
                "--source-root",
                str(ROOT_DIR),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res_ok.returncode, 0, res_ok.stdout + res_ok.stderr)

        # Removing any module (e.g. templates/ or methodology/) simulating partial install MUST fail closed
        for missing_mod in ("templates", "methodology", "ecosystem"):
            partial_dir = self.temp_dir / f"partial-{missing_mod}/.nizam"
            shutil.copytree(payload_dir, partial_dir)
            shutil.rmtree(partial_dir / missing_mod)
            res_partial = subprocess.run(
                [
                    sys.executable,
                    str(ROOT_DIR / "tools/payload_integrity.py"),
                    "--payload-dir",
                    str(partial_dir),
                    "--source-root",
                    str(ROOT_DIR),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(res_partial.returncode, 0, f"missing module {missing_mod} must fail payload_integrity")

            res_val = subprocess.run(
                ["bash", str(partial_dir / "tools/validate.sh"), "--payload"],
                cwd=str(partial_dir.parent),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(res_val.returncode, 0, f"missing module {missing_mod} must fail validate.sh --payload")

    def test_f11_circuit_breaker_prose_and_finite_recovery_enforcement(self) -> None:
        """Verify 03_circuit_breaker.md resolves Finding F11 and runtime enforces 3-signature / 6-task ceilings and finite recovery."""
        cb_text = (ROOT_DIR / "methodology/03_circuit_breaker.md").read_text(encoding="utf-8")
        parts = cb_text.split("---", 2)
        self.assertEqual(len(parts), 3)
        body = parts[2]

        self.assertNotIn("(resetting the\n  attempt counter to 0)", body)
        self.assertNotIn("(resetting the attempt counter to 0)", body)
        self.assertIn("never resetting attempt counters to 0", body)
        self.assertIn("circuit_breaker[task_id].operator_recovery", body)

        # Set up a disposable governed consumer repo to exercise runtime capture ceilings and operator_recovery
        repo = self.temp_dir / "cb-repo"
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "cb@example.test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "CB Test"], check=True)
        subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", "https://example.invalid/cb.git"], check=True)
        (repo / "README.md").write_text("# CB\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)

        run_state = {
            "schema_version": "1.0.0",
            "project": "cb-test",
            "repository": "https://example.invalid/cb.git",
            "active_phase": "001-cb",
            "active_feature": "001",
            "status": "in_progress",
            "circuit_breaker": {
                "task-sig": {"attempts": 0, "limit": 3},
                "task-six": {"attempts": 0, "limit": 10},
            },
        }
        (repo / ".agent").mkdir(parents=True, exist_ok=True)
        (repo / ".agent/run_state.json").write_text(json.dumps(run_state, indent=2) + "\n", encoding="utf-8")

        def run_capture(task_id: str, step: str, attempt: int, fail_code: int, msg: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [
                    sys.executable,
                    str(ROOT_DIR / "tools/start_path.py"),
                    "capture",
                    "--id",
                    task_id,
                    "--step",
                    step,
                    "--attempt",
                    str(attempt),
                    "--output-dir",
                    str(repo / ".agent/evidence/captures"),
                    "--root",
                    str(repo),
                    "--",
                    sys.executable,
                    "-c",
                    f"import sys; sys.stderr.write({msg!r}); sys.exit({fail_code})",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        # 1. 3-attempt same-signature ceiling on task-sig: attempts 1..3 record failed captures (exit 1); attempt 4 is halted (exit 2)!
        for att in (1, 2, 3):
            res = run_capture("task-sig", "verify", att, 1, "identical-error\n")
            self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        res_4 = run_capture("task-sig", "verify-renamed-step", 1, 1, "identical-error\n")
        self.assertEqual(res_4.returncode, 2)
        self.assertIn("three failures of the same task-wide defect signature", res_4.stderr)

        # 2. 6-attempt task ceiling across distinct signatures on task-six: attempts 1..6 record; attempt 7 is halted (exit 2)!
        last_capture_rel = ""
        for att in range(1, 7):
            res = run_capture("task-six", f"step-{att}", 1, 1, f"distinct-error-{att}\n")
            self.assertEqual(res.returncode, 1)
            doc = json.loads(res.stdout)
            last_capture_rel = doc["capture_path"]

        res_7_blocked = run_capture("task-six", "step-7", 1, 1, "distinct-error-7\n")
        self.assertEqual(res_7_blocked.returncode, 2)
        self.assertIn("finite task failed-execution budget (6) exhausted", res_7_blocked.stderr)

        # 3. Forged operator_recovery (missing role: "operator" in authority file, or boolean limit) is rejected!
        auth_rel = ".agent/evidence/task-six-recovery-auth.json"
        auth_path = repo / auth_rel
        auth_path.parent.mkdir(parents=True, exist_ok=True)
        recovery_obj = {
            "task_id": "task-six",
            "approved": True,
            "max_task_attempts": 7,
            "after_capture": last_capture_rel,
            "authority_ref": auth_rel,
        }
        # Missing role: "operator" in authority_ref
        auth_path.write_text(json.dumps(recovery_obj, indent=2) + "\n", encoding="utf-8")
        run_state["circuit_breaker"]["task-six"]["operator_recovery"] = recovery_obj
        (repo / ".agent/run_state.json").write_text(json.dumps(run_state, indent=2) + "\n", encoding="utf-8")

        res_forged = run_capture("task-six", "step-7", 1, 1, "distinct-error-7\n")
        self.assertEqual(res_forged.returncode, 2)
        self.assertIn("operator recovery lacks exact task/failed-capture binding", res_forged.stderr)

        # 4. Valid finite operator_recovery (with role: "operator") allows the 7th task execution while preserving attempts 1..6,
        #    and then blocks the 8th execution at the new finite ceiling (7)!
        auth_path.write_text(json.dumps({**recovery_obj, "role": "operator"}, indent=2) + "\n", encoding="utf-8")
        res_7_allowed = run_capture("task-six", "step-7", 1, 1, "distinct-error-7\n")
        self.assertEqual(res_7_allowed.returncode, 1)
        self.assertIn('"step": "step-7"', res_7_allowed.stdout)

        # All 7 historical captures are preserved on disk (never reset or erased)
        captures = list((repo / ".agent/evidence/captures").glob("task-six-*.capture.json"))
        self.assertEqual(len(captures), 7)

        # 8th execution is blocked by the new finite ceiling (7)
        res_8_blocked = run_capture("task-six", "step-8", 1, 1, "distinct-error-8\n")
        self.assertEqual(res_8_blocked.returncode, 2)
        self.assertIn("finite task failed-execution budget (7) exhausted", res_8_blocked.stderr)


if __name__ == "__main__":
    unittest.main()
