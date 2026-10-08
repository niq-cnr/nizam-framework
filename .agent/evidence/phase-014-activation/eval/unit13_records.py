#!/usr/bin/env python3
"""Unit 13: ROADMAP latest-tag line, CHANGELOG brand-token control, and operator verbatim quotes."""
import json, re, sys, yaml
fails = []
def check(label, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + label + (" :: " + detail if detail else ""))
    if not cond: fails.append(label)

# --- ROADMAP: exactly one BODY line
road = open("docs/planning/ROADMAP.md", encoding="utf-8").read()
end = road.index("\n---", 4); body = road[end + 4:]
hits = [l for l in body.splitlines() if "Latest released tag: v1.4.0" in l]
print("ROADMAP body lines containing the phrase:", len(hits)); [print("   ", h[:160]) for h in hits]
check("ROADMAP body has exactly one 'Latest released tag: v1.4.0' line", len(hits) == 1)
other = [l for l in body.splitlines() if "Latest released tag:" in l and "v1.4.0" not in l]
check("no stale 'Latest released tag:' body line naming another tag", not other, str(other)[:200])

# --- CHANGELOG brand tokens (regex written n[i]zamiq so this file itself does not match)
cl = open("CHANGELOG.md", encoding="utf-8").read()
rx = re.compile("n[i]zamiq")
check("CHANGELOG lowercase brand tokens == 0", len(rx.findall(cl)) == 0, str(len(rx.findall(cl))))
check("control: regex does detect a planted token", len(rx.findall(cl + "\nni" + "zamiq")) == 1)
check("control: CHANGELOG is non-empty and mentions the brand in permitted case", cl.count("Nizam") > 0, "Nizam x%d" % cl.count("Nizam"))
check("CHANGELOG has an [Unreleased] heading", "## [Unreleased]" in cl)

# --- operator verbatim quotes
rs = json.load(open(".agent/run_state.json"))
want = {"2026-10-08T11:21:14Z": "- H-PHASE-014. Activate Phase 014 with the proposed amendments, Approved. - Maintenance tranche, fold them into Phase 014, Approved.",
        "2026-10-08T12:29:26Z": "reuse the partial DAG only after re-checking it.",
        "2026-10-08T12:50:31Z": "In approve the increased budget.",
        "2026-10-08T13:20:12Z": "acknowledged."}
hist = {e["at"]: e for e in rs["history"]}
quotes = {}
for at, q in want.items():
    check("run_state %s contains its verbatim quote" % at, q in hist[at]["detail"], q[:60])
    quotes[at] = q
# every quoted segment in the new run_state entries following 'verbatim' is one of the known quotes (no unlisted quote)
new = rs["history"][231:]
found = set()
for e in new:
    for m in re.finditer(r"[Vv]erbatim[^'\"]{0,80}'(.+?)'(?=[\s,.;):]|$)", e["detail"]):
        found.add(m.group(1))
for f in sorted(found): print("   run_state-extracted quote:", f[:100])
check("every run_state-extracted verbatim segment is a known quote", all(any(f.startswith(q.rstrip('.')) for q in quotes.values()) for f in found))
# planning records: where each quote is cited
records = {
  "docs/planning/operator_gates.md": open("docs/planning/operator_gates.md", encoding="utf-8").read(),
  "docs/planning/ROADMAP.md": road,
  "docs/planning/DEBT.md": open("docs/planning/DEBT.md", encoding="utf-8").read(),
  "docs/planning/manifest.json": json.dumps(json.load(open("docs/planning/manifest.json")), ensure_ascii=False),
  "docs/planning/phase_014.yaml": open("docs/planning/phase_014.yaml", encoding="utf-8").read(),
  ".agent/feature_list_014.json": json.dumps(json.load(open(".agent/feature_list_014.json")), ensure_ascii=False),
  ".agent/product_spec_014.md": open(".agent/product_spec_014.md", encoding="utf-8").read(),
  "docs/planning/backlog_reconciliation.md": open("docs/planning/backlog_reconciliation.md", encoding="utf-8").read(),
  "docs/planning/backlog_dag.json": json.dumps(json.load(open("docs/planning/backlog_dag.json")), ensure_ascii=False),
  "CHANGELOG.md": cl,
}
# normalize apostrophe/whitespace only for matching; no semantic change
norm = lambda s: re.sub(r"\s+", " ", s)
for at, q in quotes.items():
    where = [p for p, t in records.items() if q in norm(t) or q in t]
    print("quote @%s cited verbatim in: %s" % (at, where))
    check("quote @%s appears verbatim in at least one planning record" % at, bool(where))
# a record that cites a quote by its stem (first 5 words) but not verbatim = a paraphrase defect
for at, q in quotes.items():
    stem = " ".join(q.split()[:4])
    for p, t in records.items():
        for m in re.finditer(re.escape(stem), norm(t)):
            seg = norm(t)[m.start(): m.start() + len(q)]
            if seg != q:
                check("record %s cites %s stem verbatim" % (p, at), False, seg[:100])
# recorded-in-operator_gates by timestamp
og = records["docs/planning/operator_gates.md"]
for at in ("2026-10-08T11:21:14Z", "2026-10-08T12:50:31Z", "2026-10-08T13:20:12Z"):
    print("operator_gates.md cites timestamp %s: %s" % (at, at in og))
# negative control: a one-word change must not match
check("control: altered quote is not found", not any(("In approve the increased budgets." in t) for t in records.values()))
print("RESULT: %d failures" % len(fails)); sys.exit(1 if fails else 0)
