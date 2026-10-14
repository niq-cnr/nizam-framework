"""Static contract-shape/command/scope checks only; no behavioral acceptance."""
import hashlib
import json
import subprocess
from pathlib import Path
import jsonschema

base = "9f361154c63c2f80768b6845c98f89a9aa1a1541"
p = Path(".agent/contracts/126.json")
c = json.loads(p.read_text())
jsonschema.Draft202012Validator(json.loads(Path(".nizam/schema/contract.schema.json").read_text())).validate(c)
assert c["status"] == "proposed"
assert not any(c["approvals"][key] for key in ("validator_mode_a", "evaluator_contract_review"))
f = next(item for item in json.loads(Path(".agent/feature_list_016.json").read_text())["features"] if item["id"] == "126")
assert [v["command"] for v in c["verification"]] == f["acceptance_tests"]
assert len(c["verification"]) == 9
assert c["estimated_lines"] == 2900 == sum(c["budget"][key] for key in ("product", "independent_tests", "process"))
assert len(p.read_text().splitlines()) <= 250
tracked = subprocess.check_output(["git", "diff", "--name-only", base], text=True).splitlines()
untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], text=True).splitlines()
assert all(name == str(p) or name.startswith(".agent/evidence/126/") for name in tracked + untracked), tracked + untracked
subprocess.run(["git", "diff", "--check", base], check=True)
print(json.dumps({"result": "pass", "checks": ["installed contract schema", "proposed without approvals", "nine exact feature commands", "budget sum", "250-line bound", "tracked/untracked proposal-only scope", "diff whitespace"], "contract_sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "base_revision": base, "exercised_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(), "live_acceptance": "not executed; tests do not exist yet"}, indent=2))
