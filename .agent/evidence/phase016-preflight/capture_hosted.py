"""Capture actual GitHub capability evidence; fail closed on incomplete jobs."""
import datetime, hashlib, json, subprocess
from pathlib import Path

REPO = "niq-cnr/nizam-framework"
RUN = "38532840713"
JOB = "115748548462"
ROOT = Path(__file__).resolve().parent

def api(path):
    return subprocess.check_output(["gh", "api", f"repos/{REPO}/{path}"])

def save(name, data):
    (ROOT / name).write_bytes(data)
    return {"path": str((ROOT / name).relative_to(Path.cwd())), "sha256": hashlib.sha256(data).hexdigest()}

run_bytes = api(f"actions/runs/{RUN}")
job_bytes = api(f"actions/jobs/{JOB}")
run, job = json.loads(run_bytes), json.loads(job_bytes)
assert job["run_id"] == int(RUN)
assert job["status"] == "completed" and job["conclusion"] == "success", "job is not passing and complete"
assert run["head_sha"] == "fcc97b50c43f82d4f4c672543ce556a178d1ddc0"
commands = {
    "Run required isolation suite": "PYTHONDONTWRITEBYTECODE=1 python3 tools/test_convergent_review.py",
    "Check SBCL version": "sbcl --version",
    "Check fresh SBCL without init files": "sbcl --no-sysinit --no-userinit --non-interactive --eval '(assert (= (+ 1 1) 2))'",
}
steps = {s["name"]: s for s in job["steps"]}
for name in commands:
    assert steps[name]["status"] == "completed" and steps[name]["conclusion"] == "success"
log_bytes = api(f"actions/jobs/{JOB}/logs")
log = log_bytes.decode()
for command in commands.values():
    assert command in log, command
assert "CONFORMANCE: FULL" in log, "required isolation did not report full conformance"
assert "--allow-unsupported-isolation" not in log

def receipt(marker):
    matches = [line.split(marker, 1)[1] for line in log.splitlines() if marker in line and not line.split(marker, 1)[1].startswith('" +')]
    parsed = []
    for value in matches:
        try: parsed.append(json.loads(value))
        except json.JSONDecodeError: pass
    assert len(parsed) == 1, (marker, len(parsed))
    return parsed[0]

environment = receipt("CAPABILITY_RUNNER_RECEIPT=")
checkout = receipt("MAINTENANCE_CHECKOUT_RECEIPT=")
assert environment["environment"]["GITHUB_RUN_ID"] == RUN
assert environment["environment"]["GITHUB_JOB"] == "convergent_review"
assert environment["environment"]["RUNNER_OS"] == "Linux"
assert environment["environment"]["GITHUB_SHA"] == checkout["checkout_sha"]
for rel, expected in checkout["source_sha256"].items():
    source = subprocess.check_output(["git", "show", f"{run['head_sha']}:{rel}"])
    assert hashlib.sha256(source).hexdigest() == expected, rel
artifacts = [save("hosted-run.json", run_bytes), save("hosted-job.json", job_bytes), save("hosted-job.log", log_bytes)]
result = {
    "owner": "/root", "kind": "actual-same-host-capability-receipt", "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source_head": run["head_sha"], "checkout": checkout, "environment": environment,
    "run_id": int(RUN), "job_id": int(JOB), "url": job["html_url"],
    "commands": [{"command": command, "step": name, "conclusion": "success", "exit_code": 0,
                  "exit_code_basis": "GitHub Actions successful step for this single fail-closed shell command", "started_at": steps[name]["started_at"], "completed_at": steps[name]["completed_at"]} for name, command in commands.items()],
    "artifacts": artifacts, "capability_preflight_passed": True,
    "limits": "Capability only. No controller/live case acceptance, phase activation, merge readiness or comparative performance claim."
}
(ROOT / "hosted-result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"capability_preflight_passed": True, "job": JOB, "checkout": checkout["checkout_sha"]}))
