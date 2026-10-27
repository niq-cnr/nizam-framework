#!/usr/bin/env python3
"""Exercise the consumer template against installed governance and task routing."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ConsumerTemplateTests(unittest.TestCase):
    def test_rendered_standalone_and_ecosystem(self):
        template = (ROOT / "templates/AGENTS.md").read_text()
        for ecosystem in (False, True):
            with self.subTest(ecosystem=ecosystem), tempfile.TemporaryDirectory() as tmp:
                consumer = Path(tmp)
                values = {"REPO_NAME": "example", "CURRENT_OBJECTIVE": "Repair docs",
                          "ACTIVE_PHASE_ID": "demo", "ACTIVE_PHASE_NAME": "Demo",
                          "YYYY-MM-DDTHH:MMZ": "2026-10-27T12:00Z", "HANDOFF_NOTES": "None"}
                rendered = template
                for key, value in values.items():
                    rendered = rendered.replace("{{" + key + "}}", value)
                (consumer / "AGENTS.md").write_text(rendered)
                if ecosystem:
                    (consumer / "ECOSYSTEM.json").write_text(json.dumps({"membership": "configured"}))
                installed = consumer / ".nizam"
                for name in ("NIZAM.json", "tools/SKILL.md", "methodology/01_execution.md",
                             "methodology/03_circuit_breaker.md", "standard/AGF.md"):
                    target = installed / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / name, target)
                self.assertIn(".nizam/NIZAM.json", rendered)
                self.assertIn(".nizam/tools/SKILL.md", rendered)
                self.assertRegex(rendered, r"(?i)relative to `?\.nizam/")
                for token in re.findall(r"`(\.nizam/[^` ]+)`", rendered):
                    self.assertTrue((consumer / token.rstrip("/.")).exists(), token)
                self.assertRegex(rendered, r"(?i)(if|when).*ecosystem")
                self.assertNotIn("Treat an unlisted repository as out of scope by default and halt.", rendered)
                self.assertNotIn("Only implement the current `active_contract_id`", rendered)
                self.assertNotRegex(rendered, r"(?i)halt.*third consecutive")
                for route in ("trivial", "bugfix", "small-change", "standard-feature", "high-risk"):
                    self.assertIn(route, rendered)
                self.assertIn("start_path.py classify", rendered)
                self.assertIn("methodology/03_circuit_breaker.md", rendered)
                # The same current canonical protocols are installed for both host contexts.
                index = json.loads((installed / "NIZAM.json").read_text())
                source = next(c["authoritative_source"] for c in index["capabilities"]
                              if c["id"] == "nizam-contract-first-execution")
                self.assertTrue((installed / source).is_file())

    def test_canonical_classification_examples(self):
        cases = [("trivial", ["--files", "docs/example.md", "--editorial"]),
                 ("bugfix", ["--files", "app.py", "--bugfix"]),
                 ("small-change", ["--files", "app.py"]),
                 ("standard-feature", ["--files", "app.py", "--needs-new-contract"]),
                 ("high-risk", ["--files", "app.py", "--touches-security"])]
        for expected, args in cases:
            with self.subTest(route=expected):
                result = subprocess.run([sys.executable, str(ROOT / "tools/start_path.py"),
                                         "classify", *args], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["route"], expected)


if __name__ == "__main__":
    unittest.main()
