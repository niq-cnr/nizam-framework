#!/usr/bin/env python3
"""Offline first-contact link regressions using the real validator dispatch/C9."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run_c9(readme, *, payload=False):
    """Isolate C9 while retaining production file-set construction and dispatch."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "tools").mkdir()
        shutil.copyfile(ROOT / "tools/verify_lib.sh", root / "tools/verify_lib.sh")
        (root / "CONTEXT.md").write_text("# Context\n")
        (root / "standard").mkdir()
        (root / "standard/NDS.md").write_text("# Standard\n")
        (root / "README.md").write_text(readme)
        source = (ROOT / "tools/validate.sh").read_text()
        assert source.rstrip().endswith('main "$@"')
        source = source.rstrip().removesuffix('main "$@"')
        # Other control implementations have separate suites. Do not stub C9 or its
        # library: these tests check real path resolution plus the real default/
        # payload dispatch, independently of frontmatter requirements.
        controls = ["frontmatter_schema", "format", "fences", "index", "branding",
                    "bootstrap", "module_readmes", "version_changelog", "consistency",
                    "dogfood_sweep", "ecosystem_fixtures", "skill_index", "workflow_pins",
                    "capability_profile_roles", "feature_list_lifecycle",
                    "feature_lifecycle_payload_skip"]
        prefixes = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 16]
        for number, name in zip(prefixes, controls):
            source += f"\ncheck_c{number}_{name}() {{ return 0; }}\n"
        source += '\ncheck_c1_frontmatter_schema() { for f in "$@"; do [ "$f" != README.md ] || return 1; done; }\n'
        source += '\nmain "$@"\n'
        script = root / "tools/validate.sh"
        script.write_text(source)
        return subprocess.run(["bash", str(script), *(["--payload"] if payload else [])],
                              cwd=root, text=True, capture_output=True)


class FirstContactTests(unittest.TestCase):
    def test_missing_root_target_is_rejected(self):
        result = run_c9("# Welcome\n[Module](standard/missing.md)\n")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("[C9] FAIL", result.stdout)
        self.assertIn("standard/missing.md", result.stdout)

    def test_readme_without_frontmatter_passes(self):
        result = run_c9("# Welcome\n[Standard](standard/NDS.md)\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[C9] PASS", result.stdout)

    def test_url_example_and_declared_placeholders(self):
        result = run_c9('''# Welcome
[Standard](standard/NDS.md)
```sh
curl https://example.invalid/pinned/bootstrap.sh
python tools/placeholder_check.py
```
Template target: `.agent/contracts/NNN.json`.
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_payload_does_not_require_authoring_readme(self):
        result = run_c9("# Welcome\n[Not shipped](standard/missing.md)\n", payload=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_actual_readme_local_links_resolve(self):
        readme = (ROOT / "README.md").read_text()
        broken = []
        for target in re.findall(r"\]\(([^)\s]+)\)", readme):
            if target.startswith(("https://", "http://", "#", "mailto:")):
                continue
            path = target.split("#", 1)[0]
            if path and not (ROOT / path).exists():
                broken.append(path)
        self.assertEqual(broken, [])
        self.assertFalse(readme.startswith("---\n"), "Reader README must not acquire NDS frontmatter")


if __name__ == "__main__":
    unittest.main()
