#!/usr/bin/env python3
"""Units 7 and 8: run_state history integrity and lifecycle consistency."""
import json, re, subprocess, sys
import yaml

fails = []
def check(label, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + label + (" :: " + detail if detail else ""))
    if not cond:
        fails.append(label)

head = json.loads(subprocess.check_output(["git", "show", "HEAD:.agent/run_state.json"]))
cur = json.load(open(".agent/run_state.json"))
hh, ch = head["history"], cur["history"]
print("== UNIT 7 history integrity ==")
check("HEAD history length is 231", len(hh) == 231, str(len(hh)))
check("current history length >= HEAD", len(ch) >= len(hh), "%d vs %d" % (len(ch), len(hh)))
n_mismatch = [i for i in range(len(hh)) if ch[i] != hh[i]]
check("first %d entries deep-equal to HEAD" % len(hh), not n_mismatch, str(n_mismatch[:5]))
ser = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"))
check("first entries byte-identical under canonical serialization", ser(ch[:len(hh)]) == ser(hh))
# negative control: perturb one entry, comparison must detect it
pert = json.loads(json.dumps(ch)); pert[100]["detail"] = pert[100].get("detail", "") + "x"
check("negative control: perturbed entry detected", ser(pert[:len(hh)]) != ser(hh))
check("appended entries are chronologically >= HEAD last", all(e["at"] >= hh[-1]["at"] for e in ch[len(hh):]),
      "head last=%s new=%s" % (hh[-1]["at"], [e["at"] for e in ch[len(hh):]]))
print("appended events:", [(e["at"], e["event"]) for e in ch[len(hh):]])
check("phase_013_scope_budget_final == HEAD scope_budget", cur["phase_013_scope_budget_final"] == head["scope_budget"])
check("HEAD scope_budget non-trivial (not vacuous)", bool(head["scope_budget"]) and head["scope_budget"] != cur["scope_budget"])
check("current_phase == 014-ga-track", cur["current_phase"] == "014-ga-track", cur["current_phase"])
check("current_feature == 099", cur["current_feature"] == "099", repr(cur["current_feature"]))
check("status == in_progress", cur["status"] == "in_progress", cur["status"])
check("scope_budget.original_estimate_lines == 6660", cur["scope_budget"]["original_estimate_lines"] == 6660)

print("== UNIT 8 lifecycle consistency ==")
phase = yaml.safe_load(open("docs/planning/phase_014.yaml"))
check("phase_014.yaml status == in_progress", phase["status"] == "in_progress", phase["status"])
man = json.load(open("docs/planning/manifest.json"))
check("manifest current_phase == 014-ga-track", man["current_phase"] == "014-ga-track")
p14 = [p for p in man["phases"] if p["id"] == "014-ga-track"]
check("exactly one phase-014 manifest entry", len(p14) == 1)
check("manifest phase 014 status == in_progress", p14[0]["status"] == "in_progress")
check("manifest phase 014 activation_state == active", p14[0]["activation_state"] == "active")
others_active = [p["id"] for p in man["phases"] if p["id"] != "014-ga-track" and p.get("status") in ("in_progress",)]
check("no other phase in_progress", not others_active, str(others_active))
fl = json.load(open(".agent/feature_list_014.json"))
by_id = {f["id"]: f for f in fl["features"]}
f099 = by_id["099"]
check("feature 099 status pending", f099["status"] == "pending", f099["status"])
check("feature 099 dependencies empty", f099["dependencies"] == [], str(f099["dependencies"]))
done = {i for i, f in by_id.items() if f["status"] in ("complete", "cancelled")}
eligible = [i for i, f in by_id.items() if f["status"] == "pending" and set(f["dependencies"]) <= done]
print("eligible pending features (deps satisfied):", eligible)
check("099 in eligible set (and is the current_feature)", "099" in eligible)
check("all dependency ids reference existing features", all(d in by_id for f in by_id.values() for d in f["dependencies"]))
steps = phase["steps"]
print("phase steps:", [(s.get("id"), s.get("status")) for s in steps][:20])
spec = open(".agent/product_spec_014.md", encoding="utf-8").read()
fm = yaml.safe_load(spec.split("---", 2)[1])
check("feature_list spec_version == spec frontmatter spec_version", fl["spec_version"] == fm["spec_version"], "%s vs %s" % (fl["spec_version"], fm["spec_version"]))
check("spec frontmatter version == 1.1.2", str(fm["version"]) == "1.1.2" and str(fm["spec_version"]) == "1.1.2")
check("feature list phase == run_state current_phase", fl["phase"] == cur["current_phase"])
print("RESULT: %d failures" % len(fails))
sys.exit(1 if fails else 0)
