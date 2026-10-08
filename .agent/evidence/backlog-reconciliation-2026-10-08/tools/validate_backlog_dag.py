#!/usr/bin/env python3
"""Validate the candidate backlog DAG (docs/planning/backlog_dag.json) against the activated phase-014 plan.

Run from the repository root:

    python3 .agent/evidence/backlog-reconciliation-2026-10-08/tools/validate_backlog_dag.py [--dag PATH] [--git-status PATH]

(--dag substitutes a mutated DAG copy, and --git-status substitutes a recorded
`git status --porcelain --untracked-files=all` text for V11, for negative-control runs
only; all other inputs stay fixed. Neither writes anything.)

Revision 2 (2026-10-08, main tree, post-#64); revision 2.1 admits the Validator's exact verdict path in V11. Corrections to the stopped agent's draft
(recorded in .agent/evidence/backlog-reconciliation-2026-10-08/dag_recheck.md):
V7 now requires the activated phase-014 packets to MIRROR the canonical feature list
(the draft only checked that proposed edges were declared); V10 FAILS instead of
crashing when the human view is missing; V11 confines the package to its declared
paths instead of asserting that no existing file changed (the approved amendment
edits existing planning files); V12 and V13 are new.

Checks (any failure -> exit 1):
  V1  wrapper: plan_status == "candidate", base_commit, activated_phase, packets present
  V2  every packet validates against schema/work-packet.schema.json (Draft 2020-12)
  V3  reconciliation fields: authority_status vocabulary, four prerequisites each with
      satisfied/reason, status, lane, owner_role, estimate ranges
  V4  unique packet ids
  V5  no dangling references (depends_on, consumed_by, serialize_after); consumed_by is
      the exact inverse of depends_on
  V6  no cycles over depends_on + serialize_after; prints a topological order
  V7  canonical mirror: every packet carrying a feature_id names an allocated feature
      and a manifest phase; for the activated phase its feature-dependencies EQUAL the
      canonical ones, its only non-feature dependency is ACT-014, its status and
      weighted estimate equal the canonical ones, and every canonical feature has
      exactly one packet; provisional ids are never carried as feature_id and never
      collide with an allocated id
  V8  alias coverage: A00-A16 each in a packet's aliases AND crosswalk_dispositions;
      T01-T19 and NIP-1..NIP-13 in verification_matrix with existing owners; any
      non-pending status cites evidence paths that exist; "passed" is not a status
  V9  shared-file serialization: every pair of non-complete packets touching the same
      shared file is ordered by a path in depends_on + serialize_after
  V10 human view: the reconciliation .md exists, its frontmatter validates against
      schema/frontmatter.schema.json with authoritative_source = its own path, and it
      names every packet id, alias and scenario
  V11 package confinement: every modified or untracked path is one of the package's
      declared paths, or one of the EXACT Orchestrator-owned paths
      (.agent/run_state.json; .agent/validator/phase-014-activation.json, the Validator's
      verdict on this package), reported separately. Exact paths, never a prefix: any other
      .agent/validator/* file is still a confinement failure. The Evaluator's
      .agent/evidence/phase-014-activation/eval/ files fall under the package path
      .agent/evidence/phase-014-activation/.
  V12 the canonical activated plan itself: feature list schema-valid, no dangling
      dependency, list order topological; phase_014.yaml schema-valid with one step per
      feature in list order; manifest current_phase is the activated phase
  V13 spec drift and budget: product_spec_014 spec_version == feature_list spec_version
      (the Planner drift gate) and the per-feature estimates sum to original_estimate_lines

Then reports (informational): ready set (prerequisites + dependencies + lane order),
dependency-eligible-but-lane-ordered set, near-ready set, blocked packets with causes,
technical critical path, phase-014 single-lane order, single-writer order, parallel-safe
work, shared-file order.
"""
from __future__ import annotations

import glob
import heapq
import json
import re
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

DAG = Path("docs/planning/backlog_dag.json")
MD = Path("docs/planning/backlog_reconciliation.md")
PACKAGE_PATHS = (
    "docs/planning/backlog_reconciliation.md", "docs/planning/backlog_dag.json",
    ".agent/evidence/backlog-reconciliation-2026-10-08/", ".agent/evidence/phase-014-activation/",
    ".agent/feature_list_014.json", ".agent/product_spec_014.md", "docs/planning/phase_014.yaml",
    "docs/planning/manifest.json", "docs/planning/operator_gates.md", "docs/planning/ROADMAP.md",
    "docs/planning/DEBT.md", "CHANGELOG.md",
)
# Exact paths (compared with ==, never as prefixes): files the Orchestrator legitimately writes beside this package.
ORCHESTRATOR_OWNED = (".agent/run_state.json", ".agent/validator/phase-014-activation.json")
SHARED = ("NIZAM.json", "tools/skill.json", "tools/validate.sh", "tools/verify_lib.sh",
          ".github/workflows/compliance.yml", "tools/fixtures_self_test.sh", "tools/README.md",
          "tools/interface.md", "standard/definition_of_done.md", "CHANGELOG.md", ".agent/run_state.json",
          ".agent/feature_list_014.json")
ROLES = {"Planner", "Generator", "Validator", "Evaluator", "Orchestrator"}
STATUSES = {"complete", "in_progress", "pending"}
AUTH_RE = re.compile(r"^(authorized|proposal|blocked-on-H-[A-Z0-9-]+)$")
VM_STATUSES = {"pending", "partially-evidenced", "satisfied"}
ACTIVATION_PACKET = "ACT-014"

failures: list[str] = []


def check(cond: bool, label: str, detail: str = "") -> None:
    """Print one PASS/FAIL line and record a failure."""
    print(("PASS " if cond else "FAIL ") + label + (f" -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(label + (f": {detail}" if detail else ""))


def frontmatter(path: Path) -> dict | None:
    """Return the YAML frontmatter of a Markdown file, or None."""
    m = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    return yaml.safe_load(m.group(1)) if m else None


def main() -> int:
    """Run V1-V13 and the derived reports."""
    dag = Path(sys.argv[sys.argv.index("--dag") + 1]) if "--dag" in sys.argv else DAG
    doc = json.loads(dag.read_text(encoding="utf-8"))
    packets = doc.get("packets", [])
    by_id = {p["id"]: p for p in packets}
    act = doc.get("activated_phase", {})

    # V1
    check(doc.get("plan_status") == "candidate" and bool(doc.get("base_commit")) and bool(packets)
          and bool(act.get("phase_id")) and bool(act.get("feature_list")),
          "V1 wrapper (plan_status=candidate, base_commit, activated_phase, packets)")

    # V2
    schema = json.loads(Path("schema/work-packet.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    bad = [f"{p.get('id')}: {e.message}" for p in packets for e in validator.iter_errors(p)]
    check(not bad, f"V2 {len(packets)} packets validate against schema/work-packet.schema.json", "; ".join(bad[:5]))

    # V3
    probs = []
    for p in packets:
        pid = p["id"]
        if not AUTH_RE.match(p.get("authority_status", "")):
            probs.append(f"{pid}: authority_status")
        pre = p.get("prerequisites", {})
        for k in ("technical", "authority", "environment", "evidence"):
            v = pre.get(k)
            if not (isinstance(v, dict) and isinstance(v.get("satisfied"), bool) and str(v.get("reason", "")).strip()):
                probs.append(f"{pid}: prerequisites.{k}")
        if p.get("status") not in STATUSES:
            probs.append(f"{pid}: status")
        if p.get("concurrency_lane") not in doc.get("lanes", {}):
            probs.append(f"{pid}: lane")
        if p.get("owner_role") not in ROLES:
            probs.append(f"{pid}: owner_role")
        e = p.get("estimate", {})
        for k in ("naive_lines", "weighted_lines"):
            r = e.get(k)
            if not (isinstance(r, list) and len(r) == 2 and r[0] <= r[1]):
                probs.append(f"{pid}: estimate.{k}")
        if p["status"] == "pending" and p["authority_status"] != "authorized" and pre.get("authority", {}).get("satisfied"):
            probs.append(f"{pid}: authority prerequisite marked satisfied but authority_status={p['authority_status']}")
    check(not probs, "V3 reconciliation fields (authority, prerequisites x4, status, lane, owner, estimates)", "; ".join(probs[:8]))

    # V4
    ids = [p["id"] for p in packets]
    dups = sorted({i for i in ids if ids.count(i) > 1})
    check(not dups, f"V4 unique packet ids ({len(ids)})", ", ".join(dups))

    # V5
    dang, inv = [], []
    for p in packets:
        e = p["dependency_edges"]
        for key in ("depends_on", "consumed_by", "serialize_after"):
            for t in e.get(key, []):
                if t not in by_id:
                    dang.append(f"{p['id']}.{key}->{t}")
        expect = sorted(q["id"] for q in packets if p["id"] in q["dependency_edges"]["depends_on"])
        if sorted(e.get("consumed_by", [])) != expect:
            inv.append(p["id"])
    check(not dang, "V5a no dangling references", ", ".join(dang))
    check(not inv, "V5b consumed_by is the exact inverse of depends_on", ", ".join(inv))

    # V6 cycles + topological order (depends_on + serialize_after), tie-break lane_rank
    indeg = {i: 0 for i in by_id}
    succ: dict[str, list[str]] = {i: [] for i in by_id}
    for p in packets:
        for d in set(p["dependency_edges"]["depends_on"]) | set(p["dependency_edges"].get("serialize_after", [])):
            if d in by_id:
                indeg[p["id"]] += 1
                succ[d].append(p["id"])
    heap = [(by_id[i].get("lane_rank", 0), i) for i, n in indeg.items() if n == 0]
    heapq.heapify(heap)
    topo = []
    while heap:
        _, i = heapq.heappop(heap)
        topo.append(i)
        for s in succ[i]:
            indeg[s] -= 1
            if indeg[s] == 0:
                heapq.heappush(heap, (by_id[s].get("lane_rank", 0), s))
    cyc = sorted(i for i, n in indeg.items() if n > 0)
    check(not cyc, "V6 acyclic (depends_on + serialize_after)", "cycle among: " + ", ".join(cyc))
    print("     topological order: " + " -> ".join(topo))

    # V7 canonical mirror
    allocated: dict[str, tuple[str, dict]] = {}
    for fl in sorted(glob.glob(".agent/feature_list*.json")):
        d = json.loads(Path(fl).read_text(encoding="utf-8"))
        for f in d.get("features", d if isinstance(d, list) else []):
            allocated[str(f.get("id"))] = (fl, f)
    max_alloc = max(int(i) for i in allocated if i.isdigit())
    manifest = json.loads(Path("docs/planning/manifest.json").read_text(encoding="utf-8"))
    phase_ids = {ph["id"] for ph in manifest.get("phases", [])}
    canon = {f["id"]: f for f in json.loads(Path(act.get("feature_list", "")).read_text(encoding="utf-8"))["features"]} if act.get("feature_list") else {}
    fid_of = {p["id"]: p.get("feature_id") for p in packets}
    v7 = []
    for p in packets:
        fid = p.get("feature_id")
        if "phase_id" in p and p["phase_id"] not in phase_ids:
            v7.append(f"{p['id']}: phase_id {p['phase_id']} not in manifest")
        prov = p.get("provisional_feature_id")
        if prov and fid:
            v7.append(f"{p['id']}: provisional id carried as feature_id")
        if prov and int(prov) <= max_alloc:
            v7.append(f"{p['id']}: provisional id {prov} collides with allocated ids (max {max_alloc})")
        if fid is None:
            continue
        if fid not in allocated:
            v7.append(f"{p['id']}: feature_id {fid} not allocated in any feature list")
            continue
        if p.get("phase_id") != act.get("phase_id"):
            continue
        c = canon[fid]
        deps = p["dependency_edges"]["depends_on"]
        feat_deps = sorted(fid_of[d] for d in deps if fid_of.get(d))
        nonfeat = sorted(d for d in deps if not fid_of.get(d))
        if feat_deps != sorted(c["dependencies"]):
            v7.append(f"{fid}: dependencies {feat_deps} != canonical {sorted(c['dependencies'])}")
        if nonfeat != [ACTIVATION_PACKET]:
            v7.append(f"{fid}: non-feature dependencies {nonfeat} != ['{ACTIVATION_PACKET}']")
        if p["status"] != c["status"]:
            v7.append(f"{fid}: status {p['status']} != canonical {c['status']}")
        if p["estimate"]["weighted_lines"] != [c["estimated_lines"], c["estimated_lines"]]:
            v7.append(f"{fid}: weighted estimate {p['estimate']['weighted_lines']} != canonical {c['estimated_lines']}")
    mirrored = [p.get("feature_id") for p in packets if p.get("phase_id") == act.get("phase_id")]
    for fid in canon:
        if mirrored.count(fid) != 1:
            v7.append(f"canonical feature {fid} mirrored by {mirrored.count(fid)} packets")
    check(not v7, f"V7 canonical mirror of {act.get('feature_list')} ({len(canon)} features; provisional ids above {max_alloc})", "; ".join(v7[:8]))

    # V8 alias + scenario coverage
    aliases = {a for p in packets for a in p.get("aliases", [])}
    disp = doc.get("crosswalk_dispositions", {})
    want_a = [f"A{n:02d}" for n in range(17)]
    miss_a = [a for a in want_a if a not in aliases or a not in disp]
    check(not miss_a, "V8a every alias A00-A16 mapped to a packet and a disposition", ", ".join(miss_a))
    vm = doc.get("verification_matrix", {})
    want_t = [f"T{n:02d}" for n in range(1, 20)] + [f"NIP-{n}" for n in range(1, 14)]
    v8 = []
    for k in want_t:
        r = vm.get(k)
        if not r:
            v8.append(f"{k}: missing")
            continue
        if r.get("status") not in VM_STATUSES:
            v8.append(f"{k}: status {r.get('status')}")
        if not r.get("owning_packets"):
            v8.append(f"{k}: no owner")
        v8 += [f"{k}: owner {o} missing" for o in r.get("owning_packets", []) if o not in by_id]
        if r.get("status") != "pending" and (not r.get("evidence") or any(not Path(e).exists() for e in r["evidence"])):
            v8.append(f"{k}: non-pending status without existing evidence")
    check(not v8, "V8b T01-T19 + NIP cases 1-13 mapped (owners exist; honest statuses with evidence)", "; ".join(v8))

    # V9 shared-file serialization
    reach: dict[str, set[str]] = {}

    def reachable(src: str) -> set[str]:
        if src not in reach:
            seen, stack = set(), [src]
            while stack:
                for s in succ[stack.pop()]:
                    if s not in seen:
                        seen.add(s)
                        stack.append(s)
            reach[src] = seen
        return reach[src]

    v9, shared_order = [], {}
    live = [p for p in packets if p["status"] != "complete"]
    files = SHARED + tuple(sorted({s for p in packets for s in p.get("shared_files", []) if s.startswith("docs/planning/")}))
    for f in files:
        touch = [i for i in topo if i in {p["id"] for p in live if f in p.get("shared_files", [])}]
        shared_order[f] = touch
        for i, a in enumerate(touch):
            for b in touch[i + 1:]:
                if b not in reachable(a) and a not in reachable(b):
                    v9.append(f"{f}: {a} || {b}")
    check(not v9, "V9 shared-file writers are totally ordered", "; ".join(v9[:6]))

    # V10 human view
    if not MD.is_file():
        check(False, "V10a reconciliation .md frontmatter validates (authoritative_source = own path)", f"{MD} missing")
        check(False, "V10b .md names every packet id, alias and scenario", f"{MD} missing")
    else:
        md = MD.read_text(encoding="utf-8")
        fm = frontmatter(MD)
        fm_err = "no frontmatter"
        fm_ok = False
        if fm is not None:
            errs = list(jsonschema.Draft202012Validator(json.loads(Path("schema/frontmatter.schema.json").read_text())).iter_errors(fm))
            fm_ok = not errs and fm.get("authoritative_source") == str(MD) and bool(fm.get("change_log"))
            fm_err = "; ".join(e.message for e in errs) or f"authoritative_source={fm.get('authoritative_source')} change_log={bool(fm.get('change_log'))}"
        check(fm_ok, "V10a reconciliation .md frontmatter validates (authoritative_source = own path; change_log present)", fm_err)
        tok = lambda t: re.search(r"(?<![A-Za-z0-9-])" + re.escape(t) + r"(?![A-Za-z0-9-])", md)  # noqa: E731
        miss = [i for i in ids if not tok(i)] + [a for a in want_a + want_t if not tok(a)]
        check(not miss, "V10b .md names every packet id, alias and scenario", ", ".join(miss))

    # V11 package confinement
    if "--git-status" in sys.argv:
        st = Path(sys.argv[sys.argv.index("--git-status") + 1]).read_text(encoding="utf-8")
    else:
        st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=True).stdout
    paths = [ln[3:] for ln in st.splitlines() if ln.strip()]
    orch = [x for x in paths if x in ORCHESTRATOR_OWNED]
    stray = [x for x in paths if x not in ORCHESTRATOR_OWNED and not x.startswith(PACKAGE_PATHS)]
    check(not stray, f"V11 changed/untracked paths confined to the package ({len(paths) - len(orch)} paths)", "; ".join(stray))
    if orch:
        print(f"     note: {', '.join(orch)} modified -- Orchestrator-owned, not written by this package")

    # V12 canonical activated plan
    v12 = []
    fl_doc = json.loads(Path(act["feature_list"]).read_text(encoding="utf-8"))
    for e in jsonschema.Draft202012Validator(json.loads(Path("schema/feature_list.schema.json").read_text())).iter_errors(fl_doc):
        v12.append(f"feature list: {e.message}")
    order = [f["id"] for f in fl_doc["features"]]
    pos = {i: n for n, i in enumerate(order)}
    for f in fl_doc["features"]:
        for d in f["dependencies"]:
            if d not in pos:
                v12.append(f"{f['id']}: dangling dependency {d}")
            elif pos[d] >= pos[f["id"]]:
                v12.append(f"{f['id']}: list order not topological (depends on later {d})")
    ph_entry = next((ph for ph in manifest["phases"] if ph["id"] == act["phase_id"]), {})
    ph_doc = yaml.safe_load(Path(ph_entry.get("phase_definition", "")).read_text(encoding="utf-8")) if ph_entry.get("phase_definition") else {}
    for e in jsonschema.Draft202012Validator(json.loads(Path("schema/phase.schema.json").read_text())).iter_errors(ph_doc):
        v12.append(f"phase yaml: {e.message}")
    if [s.get("id") for s in ph_doc.get("steps", [])] != order:
        v12.append("phase yaml steps do not match the feature list order")
    if manifest.get("current_phase") != act["phase_id"]:
        v12.append(f"manifest current_phase {manifest.get('current_phase')} != {act['phase_id']}")
    check(not v12, f"V12 canonical plan: feature list + {ph_entry.get('phase_definition')} + manifest", "; ".join(v12[:6]))

    # V13 drift + budget
    spec = frontmatter(Path(".agent/product_spec_014.md")) or {}
    total = sum(f["estimated_lines"] for f in fl_doc["features"])
    v13 = []
    if str(spec.get("spec_version")) != fl_doc["spec_version"] or act.get("spec_version") != fl_doc["spec_version"]:
        v13.append(f"SPEC DRIFT: product_spec {spec.get('spec_version')} / feature_list {fl_doc['spec_version']} / dag {act.get('spec_version')}")
    if total != fl_doc["original_estimate_lines"] or act.get("original_estimate_lines") != total:
        v13.append(f"estimates sum {total} != original_estimate_lines {fl_doc['original_estimate_lines']} (dag {act.get('original_estimate_lines')})")
    check(not v13, f"V13 spec_version lockstep ({fl_doc['spec_version']}) and estimate reconciliation ({total})", "; ".join(v13))

    # ---------------------------------------------------------------- reports
    print("\n== REPORT (derived from the JSON) ==")
    done = {p["id"] for p in packets if p["status"] == "complete"}
    ready, near, blocked, eligible_later = [], [], [], []
    for i in topo:
        p = by_id[i]
        if p["status"] != "pending":
            continue
        unmet = {k: v["reason"] for k, v in p["prerequisites"].items() if not v["satisfied"]}
        deps_ok = all(d in done for d in p["dependency_edges"]["depends_on"])
        lane_ok = all(d in done for d in p["dependency_edges"].get("serialize_after", []))
        if deps_ok and not unmet and p["authority_status"] == "authorized" and lane_ok:
            ready.append(i)
        elif deps_ok and not unmet and p["authority_status"] == "authorized":
            eligible_later.append(i)
        elif p["authority_status"] == "authorized" and set(unmet) <= {"technical", "evidence"}:
            near.append((i, unmet))
        else:
            blocked.append((i, unmet))
    inflight = [i for i in topo if by_id[i]["status"] == "in_progress"]
    print("in progress: " + (", ".join(f"{i} ({'; '.join(v['reason'] for v in by_id[i]['prerequisites'].values() if not v['satisfied'])})" for i in inflight) or "(none)"))
    print("ready set (all prerequisites met AND the single lane's serialize_after predecessors complete): " + (", ".join(ready) or "(none)"))
    print("dependency-eligible, waiting only on lane order (serialize_after): " + (", ".join(eligible_later) or "(none)"))
    print("near-ready (authorized; waiting only on in-flight technical/evidence events):")
    for i, u in near:
        print(f"  {i}: " + " | ".join(f"{k}: {v}" for k, v in u.items()))
    print("blocked (authority or environment):")
    for i, u in blocked:
        print(f"  {i} [{by_id[i]['authority_status']}]: " + "; ".join(f"{k}: {v}" for k, v in sorted(u.items()) if k in ("authority", "environment")))

    w = {i: (0 if by_id[i]["status"] == "complete" else sum(by_id[i]["estimate"]["weighted_lines"]) / 2) for i in by_id}
    best: dict[str, float] = {}
    prev: dict[str, str | None] = {}
    for i in topo:
        deps = by_id[i]["dependency_edges"]["depends_on"]
        b = max(deps, key=lambda d: best.get(d, 0), default=None)
        best[i] = w[i] + (best.get(b, 0) if b else 0)
        prev[i] = b
    end: str | None = max(best, key=best.get)
    path = []
    while end:
        path.append(end)
        end = prev[end]
    path.reverse()
    lo = sum(by_id[i]["estimate"]["weighted_lines"][0] for i in path if by_id[i]["status"] != "complete")
    hi = sum(by_id[i]["estimate"]["weighted_lines"][1] for i in path if by_id[i]["status"] != "complete")
    print("technical critical path (depends_on only; weighted-line midpoint; gate turnaround EXCLUDED, unknown):")
    print("  " + " -> ".join(path) + f"  [weighted lines {lo}-{hi}]")
    sub = [i for i in topo if by_id[i].get("phase_id") == act.get("phase_id")]
    print(f"phase {act.get('phase_id')} single-lane order (canonical list order): " + " -> ".join(sub))
    print("phase-014 critical path (canonical dependencies): " + " -> ".join(i for i in path if i in sub or i == ACTIVATION_PACKET))
    sw = [i for i in topo if by_id[i]["concurrency_lane"] == "single-writer" and by_id[i]["status"] != "complete"]
    print("single-writer execution order (one implementation lane; beyond F102 candidate):")
    print("  " + " -> ".join(sw))
    ps = [i for i in topo if by_id[i]["concurrency_lane"] != "single-writer" and by_id[i]["status"] != "complete"]
    print("parallel-safe (read-only / new-files-only) work: " + (", ".join(ps) or "(none)"))
    print("shared-file serialization (writers in order):")
    for f, o in shared_order.items():
        if len(o) > 1:
            print(f"  {f}: " + " -> ".join(o))

    print(f"\nSUMMARY: {'FAIL' if failures else 'PASS'} ({len(failures)} failing checks; {len(packets)} packets)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
