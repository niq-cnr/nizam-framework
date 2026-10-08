#!/usr/bin/env python3
"""Unit 12: frontmatter schema validation + change_log[0].version == version, with negative controls and HEAD comparison."""
import copy, json, subprocess, sys
import jsonschema, yaml
DOCS = [".agent/product_spec_014.md", "docs/planning/backlog_reconciliation.md", "docs/planning/operator_gates.md",
        "docs/planning/ROADMAP.md", "docs/planning/DEBT.md"]
schema = json.load(open("schema/frontmatter.schema.json"))
validator = jsonschema.Draft202012Validator(schema)
def front(text):
    assert text.startswith("---\n"), "no opening delimiter"
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end])
bad = 0
for d in DOCS:
    fm = front(open(d, encoding="utf-8").read())
    errs = [e.message[:160] for e in validator.iter_errors(fm)]
    cl0 = fm["change_log"][0]["version"]
    ok_ver = str(cl0) == str(fm["version"])
    # negative controls: drop a required key; skew change_log[0].version
    m1 = copy.deepcopy(fm); m1.pop("version")
    ctl1 = bool(list(validator.iter_errors(m1)))
    m2 = copy.deepcopy(fm); m2["change_log"][0]["version"] = "9.9.9"
    ctl2 = str(m2["change_log"][0]["version"]) != str(m2["version"])
    try:
        head = subprocess.run(["git", "show", "HEAD:" + d], capture_output=True, text=True, check=True).stdout
        head_v = str(front(head)["version"])
    except subprocess.CalledProcessError:
        head_v = "(new file)"
    changed = head_v != str(fm["version"])
    status = "OK  " if not errs and ok_ver and ctl1 and ctl2 else "FAIL"
    bad += status == "FAIL"
    print("%s %-45s schema_errors=%d version=%s change_log[0].version=%s match=%s HEAD_version=%s bumped=%s controls=%s/%s"
          % (status, d, len(errs), fm["version"], cl0, ok_ver, head_v, changed, ctl1, ctl2))
    for e in errs: print("     ", e)
print("RESULT: %d of %d docs failing" % (bad, len(DOCS)))
sys.exit(1 if bad else 0)
