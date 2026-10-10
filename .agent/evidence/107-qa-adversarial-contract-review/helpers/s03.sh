python3 - <<'PY'
import json, subprocess, sys
A = "7972e4f2d46abf6b8e0f02e8c11e94ac0f7aa0f4"
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
bad = []
contract = json.load(open(".agent/contracts/107.json"))
scope = {item["path"] for key in ("files_create", "files_modify") for item in contract["scope"][key]}
modified = {item["path"] for item in contract["scope"]["files_modify"]}
owned = {".agent/contracts/107.json", ".agent/run_state.json", ".agent/feature_list_014.json"}
prefixes = (".agent/validator/107", ".agent/qa/107", ".agent/evidence/107/qa/", ".agent/evidence/107/failed-attempt", ".agent/evidence/107-qa-")
changed = set(run("git", "diff", "--name-only", "-z", A).split("\0")) - {""}
fields = run("git", "status", "--porcelain", "--untracked-files=all", "-z").split("\0")
index = 0
while index < len(fields):
    entry = fields[index]
    index += 1
    if not entry:
        continue
    changed.add(entry[3:])
    if entry[0] in "RC" or entry[1] in "RC":
        if index < len(fields):
            changed.add(fields[index])
            index += 1
extra = sorted(path for path in changed if path not in scope and path not in owned and not path.startswith(prefixes))
missing = sorted(modified - changed)
if extra:
    bad.append("paths outside scope and allowlist: " + repr(extra))
if missing:
    bad.append("files_modify paths not changed: " + repr(missing))
if ".agent/feature_list_014.json" in changed:
    bad.append("feature list changed inside the attempt; status flips are Orchestrator-owned")
if "docs/planning/phase_014.yaml" in changed or "docs/planning/DEBT.md" in changed:
    bad.append("orchestrator-owned file changed inside the attempt")
print("changed", len(changed), "problems:", bad)
sys.exit(1 if bad else 0)
PY
