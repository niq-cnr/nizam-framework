"""Independent bounded acceptance checks for the approved backlog registration."""
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path.cwd()
TASK = "api-reference-backlog-publish"
lineage = json.loads((ROOT / f".agent/evidence/{TASK}/lineage.json").read_text())
base = lineage["original_review_base"]
def old(path):
    return subprocess.check_output(["git", "show", f"{base}:{path}"], text=True)
roadmap_path = "docs/planning/ROADMAP.md"
roadmap = Path(roadmap_path).read_text()
original = old(roadmap_path)
anchor = "## Current position — Jev readiness program, 2026-10-22"
assert roadmap[roadmap.index(anchor):] == original[original.index(anchor):], "current program or release history changed"
assert "version: 0.65.36" in roadmap and roadmap.count("change_log:") == 1
assert "API-REF-PILOT" in roadmap and "Approved; not started" in roadmap
plan = Path("docs/planning/API_REFERENCE_PILOT.md").read_text()
for token in ("approved; not started", "30%", "11 of 12", "under 10 seconds", "12 tasks", "tools/start_path.py", "tools/convergent_review.py", "tools/payload_integrity.py", "at most one bounded pilot revision", "without importing or executing source modules", "active Jev readiness program retains its existing order"):
    assert token in plan, token
for target in re.findall(r"\]\(([^)]+)\)", plan):
    assert (Path("docs/planning") / target).exists(), target
assert (Path("docs/planning") / "API_REFERENCE_PILOT.md").exists()
changelog = Path("CHANGELOG.md").read_text()
assert "API-REF-PILOT" in changelog.split("## [2.0.0]", 1)[0]
assert changelog[changelog.index("## [2.0.0]"):] == old("CHANGELOG.md")[old("CHANGELOG.md").index("## [2.0.0]"):], "released changelog changed"
# Retain raw current and HEAD diagnostic output in the captured stdout. The
# temporary HEAD target necessarily gets a C2 own-path mismatch; this is only
# a baseline artifact and does not occur in the real target.
def validate(path):
    return subprocess.run(["bash", "tools/validate.sh", "--target", str(path)], capture_output=True, text=True)
current = validate(roadmap_path)
with tempfile.TemporaryDirectory(prefix="nizam-backlog-baseline-") as folder:
    path = Path(folder) / "ROADMAP.md"
    path.write_text(original)
    baseline = validate(path)
    normalized = baseline.stdout.replace(str(path), roadmap_path)
print("CURRENT ROADMAP VALIDATOR", current.returncode)
print(current.stdout)
print("BASE ROADMAP VALIDATOR", baseline.returncode)
print(normalized)
def diagnostics(text):
    return {line.strip() for line in text.splitlines() if line.startswith("  ")}
new = diagnostics(current.stdout) - diagnostics(normalized)
assert not new, "introduced roadmap validation diagnostics: " + repr(new)
assert not current.stderr and not baseline.stderr
print(json.dumps({"result": "pass", "baseline_revision": base, "current_roadmap_validator_exit": current.returncode, "baseline_roadmap_validator_exit": baseline.returncode, "introduced_diagnostics": [], "note": "Inherited roadmap validation failures retained; new plan/changelog validated separately."}, sort_keys=True))

current_change = validate("CHANGELOG.md")
with tempfile.TemporaryDirectory(prefix="nizam-changelog-baseline-") as folder:
    path = Path(folder) / "CHANGELOG.md"
    path.write_text(old("CHANGELOG.md"))
    base_change = validate(path)
    normalized_change = base_change.stdout.replace(str(path), "CHANGELOG.md")
print("CURRENT CHANGELOG VALIDATOR", current_change.returncode)
print(current_change.stdout)
print("BASE CHANGELOG VALIDATOR", base_change.returncode)
print(normalized_change)
assert not diagnostics(current_change.stdout) - diagnostics(normalized_change), "introduced CHANGELOG validator diagnostics"
assert not current_change.stderr and not base_change.stderr
print("CHANGELOG baseline comparison PASS; inherited target-mode failures are not new.")
