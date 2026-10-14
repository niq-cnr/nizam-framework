"""Bounded static checks for the phase-016 CI transport; no hosted claims."""
import copy
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

BASE = "4e7abcb427b89e60684bb8b72c19ec021775a2e9"
WORKFLOW = ".github/workflows/compliance.yml"
before = yaml.safe_load(subprocess.check_output(["git", "show", f"{BASE}:{WORKFLOW}"], text=True))
after = yaml.safe_load(Path(WORKFLOW).read_text())
old_steps = before["jobs"]["convergent_review"]["steps"]
new_steps = after["jobs"]["convergent_review"]["steps"]
assert isinstance(new_steps, list) and all(isinstance(step, dict) for step in new_steps)
normalized = copy.deepcopy(after)
normalized["jobs"]["convergent_review"]["steps"] = old_steps
assert normalized == before, "Workflow content outside convergent_review steps changed"
assert new_steps[:len(old_steps) - 1] == old_steps[:-1], "Existing setup/boundary steps changed"
assert old_steps[-1] == {"run": "PYTHONDONTWRITEBYTECODE=1 python3 tools/test_convergent_review.py && bash tools/fixtures_self_test.sh"}
added = new_steps[len(old_steps) - 1:]
assert len(added) == 6
assert added[0]["name"] == "Record capability runner environment"
assert set(added[0]) == {"name", "run"}
assert added[1:] == [
    {"name": "Install SBCL", "run": "sudo apt-get update\nsudo apt-get install -y sbcl\n"},
    {"name": "Check SBCL version", "run": "sbcl --version"},
    {"name": "Check fresh SBCL without init files", "run": "sbcl --no-sysinit --no-userinit --non-interactive --eval '(assert (= (+ 1 1) 2))'"},
    {"name": "Run required isolation suite", "run": "PYTHONDONTWRITEBYTECODE=1 python3 tools/test_convergent_review.py"},
    {"name": "Run fixture self-test", "run": "bash tools/fixtures_self_test.sh"},
], "Unexpected commands, flags, or conditional step behavior"
for step in added:
    assert isinstance(step["run"], str)
    subprocess.run(["bash", "-n"], input=step["run"], text=True, check=True)
metadata_python = added[0]["run"].split("python3 - <<'PY'\n", 1)[1].rsplit("PY\n", 1)[0]
compile(metadata_python, "capability-runner-metadata", "exec")
subprocess.run(["git", "diff", "--check", BASE], check=True)
changed = subprocess.check_output(["git", "diff", "--name-only", BASE], text=True).splitlines()
assert all(path == WORKFLOW or path.startswith(".agent/evidence/phase016-preflight/") for path in changed), changed
print(json.dumps({
    "base": BASE,
    "exercised_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "workflow_sha256": hashlib.sha256(Path(WORKFLOW).read_bytes()).hexdigest(),
    "checks": ["typed YAML mappings/lists/strings", "outside-job equality", "existing steps equality", "exact added command/step shape", "bash syntax", "metadata Python syntax", "diff whitespace", "bounded changed paths"],
    "result": "pass",
    "hosted_capability": "not exercised; GitHub run required",
}, sort_keys=True, indent=2))
