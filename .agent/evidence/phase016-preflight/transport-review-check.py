"""Independent static transport review; does not claim hosted capability."""
import copy
import hashlib
import json
import subprocess

import yaml

BASE = "4e7abcb427b89e60684bb8b72c19ec021775a2e9"
HEAD = "407909921e4a479aa33956662c9544afc7343699"
WORKFLOW = ".github/workflows/compliance.yml"


def git(*args):
    return subprocess.check_output(["git", *args], text=True)


assert git("rev-parse", "HEAD").strip() == HEAD
old_text = git("show", f"{BASE}:{WORKFLOW}")
new_text = git("show", f"{HEAD}:{WORKFLOW}")
old = yaml.safe_load(old_text)
new = yaml.safe_load(new_text)
steps = new["jobs"]["convergent_review"]["steps"]
old_steps = old["jobs"]["convergent_review"]["steps"]
restored = copy.deepcopy(new)
restored["jobs"]["convergent_review"]["steps"] = old_steps
assert restored == old, "Outside-job configuration changed"
assert steps[:len(old_steps)-1] == old_steps[:-1]
added = steps[len(old_steps)-1:]
assert len(added) == 6
assert all(set(step) == {"name", "run"} for step in added)
assert added[1]["run"].splitlines() == ["sudo apt-get update", "sudo apt-get install -y sbcl"]
assert added[2]["run"] == "sbcl --version"
assert added[3]["run"] == "sbcl --no-sysinit --no-userinit --non-interactive --eval '(assert (= (+ 1 1) 2))'"
assert added[4]["run"] == "PYTHONDONTWRITEBYTECODE=1 python3 tools/test_convergent_review.py"
assert added[5]["run"] == "bash tools/fixtures_self_test.sh"
assert old_steps[-1]["run"] == added[4]["run"] + " && " + added[5]["run"]
assert "--allow-unsupported-isolation" not in new_text
for step in added:
    subprocess.run(["bash", "-n"], input=step["run"], text=True, check=True)
receipt = added[0]["run"].split("python3 - <<'PY'\n")[1].rsplit("PY\n", 1)[0]
compile(receipt, "capability-receipt", "exec")
for field in ("GITHUB_SHA", "GITHUB_JOB", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "RUNNER_NAME", "RUNNER_OS", "RUNNER_ARCH", "ImageVersion"):
    assert field in receipt
changed = git("diff", "--name-only", BASE, HEAD).splitlines()
assert all(path == WORKFLOW or path.startswith(".agent/evidence/phase016-preflight/") for path in changed)
# Raw captured diff evidence legitimately includes a space-only context line.
subprocess.run(["git", "diff", "--check", BASE, HEAD, "--", WORKFLOW], check=True)
print(json.dumps({
    "reviewed_revision": HEAD,
    "base_revision": BASE,
    "workflow_sha256": hashlib.sha256(new_text.encode()).hexdigest(),
    "checks": ["typed YAML equality outside changed steps", "existing setup, pins, permissions and other jobs preserved", "exact SBCL and required-isolation commands in same job", "no condition or continue-on-error added", "original fixture command preserved after isolation", "receipt environment identity fields", "shell and embedded Python syntax", "only workflow and new preflight evidence changed", "diff whitespace"],
    "result": "pass",
    "hosted_capability": "pending; not exercised by this static review"
}, indent=2))
