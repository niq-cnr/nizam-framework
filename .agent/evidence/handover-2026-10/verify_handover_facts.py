#!/usr/bin/env python3
"""Replayable checks behind docs/planning/HANDOVER.md (handover 2026-10).

Run from the repository root (stdlib + jsonschema + PyYAML, offline):

    python3 .agent/evidence/handover-2026-10/verify_handover_facts.py facts
    python3 .agent/evidence/handover-2026-10/verify_handover_facts.py frontmatter
    python3 .agent/evidence/handover-2026-10/verify_handover_facts.py frozen
    python3 .agent/evidence/handover-2026-10/verify_handover_facts.py dag
    python3 .agent/evidence/handover-2026-10/verify_handover_facts.py dagpath

facts        Re-derives every figure HANDOVER.md states from the canonical files and git:
             phase/run_state position, completed features and their merge commits, the
             scope-budget figures, the DEBT.md Open set, the v1.4.0 tag, the compliance.yml
             jobs, the 104 CI evidence strings, the ROADMAP open-debt bullet (feature 102
             AT5's own assertion), and that every repository path HANDOVER.md cites exists
             (refs are resolved as git refs; a short, named list of future paths is allowed).
frontmatter  Validates the frontmatter of every doc this handover touched against
             schema/frontmatter.schema.json and checks authoritative_source is its own path.
frozen       Proves the frozen phase-014 acceptance infrastructure is unchanged: no diff
             against e2a50ed, no untracked file, and feature 102 AT7's sha256 pins hold.
dag          Runs the backlog DAG validator in the committed-tree view (--git-status
             /dev/null), prints its full output, and asserts the failing set is exactly the
             pre-existing {V7, V13} with V7 failing only on packet statuses (no regression)
             and V13 failing only on the canonical 7980-vs-8600 estimate gap (no spec drift).
dagpath      Derives the DAG's critical paths twice: from the DAG as committed, and from a
             temporary copy (outside the repository) in which only the F099/F103/F104/F105
             packet statuses are set to complete. Asserts the first runs through F099 and the
             second through F100 (backlog_reconciliation.md Section 6 note).

Exit 0 when every assertion holds; 1 otherwise. Writes nothing in the repository
(dagpath writes one temporary file in the system temporary directory and removes it).
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

failures: list[str] = []


def check(cond: bool, label: str, detail: str = "") -> None:
    """Print one PASS/FAIL line and record a failure."""
    print(("PASS " if cond else "FAIL ") + label + (f" -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(label)


def git(*args: str) -> str:
    """Return stripped stdout of a git command (raises on failure)."""
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def git_ok(*args: str) -> bool:
    """Return True when a git command exits 0."""
    return subprocess.run(["git", *args], capture_output=True, text=True).returncode == 0


def facts() -> None:
    """Re-derive the handover's stated facts."""
    rs = json.loads(Path(".agent/run_state.json").read_text(encoding="utf-8"))
    check(rs["current_phase"] == "014-ga-track" and rs["current_feature"] == "106" and rs["status"] == "in_progress",
          "run_state position 014-ga-track / 106 / in_progress")
    check(rs.get("active_contract_id") is None, "run_state active_contract_id is null")
    check(rs["completed_contract_ids"] == ["099", "103", "104", "105"], "completed_contract_ids == 099,103,104,105",
          str(rs["completed_contract_ids"]))
    sb = rs["scope_budget"]
    per = {f["id"]: f["actual"] for f in sb["per_feature"]}
    items = {i["id"]: i["actual"] for i in sb["phase_level_items"]}
    check(sb["original_estimate_lines"] == 8600 and sb["ceiling_130pct"] == 11180, "budget 8600 / ceiling 11180")
    check(per == {"099": 596, "103": 885, "104": 991, "105": 950} and items == {"rebaseline-1.1.4": 292},
          "per-feature 596/885/991/950 + phase item 292", f"{per} {items}")
    check(sb["total_lines_changed"] == 3714 == sum(per.values()) + sum(items.values()), "total budget-counted 3714 = sum")
    check(sb["evidence_lines_total"] == 11988, "evidence lines recorded 11988", str(sb["evidence_lines_total"]))
    check("option 1 confirmed." in sb["rebaseline"]["authorized_by"] and "2026-10-09T17:59:00Z" in sb["rebaseline"]["authorized_by"],
          "re-baseline confirmation 'option 1 confirmed.' at 2026-10-09T17:59:00Z")
    check(3 * (885 + 991 + 950) / 3 == 2826, "106 rolling threshold 3 x mean(885,991,950) = 2826")
    ext = rs["circuit_breaker"].get("104-contract", {}).get("human_authorized_extension")
    check(bool(ext) and all(rs["circuit_breaker"][f"{i}-contract"]["attempts"] == 3 for i in ("099", "103", "104", "105")),
          "104-contract carries a human_authorized_extension; 099/103/104/105 contracts each 3 attempts")
    ev = {h["at"]: h for h in rs["history"]}
    check("2026-10-10T02:11:41Z" in ev and ev["2026-10-10T02:11:41Z"]["event"] == "operator_gate_decision",
          "handover request recorded (operator_gate_decision 2026-10-10T02:11:41Z)")
    check("2026-10-09T19:28:39Z" in ev and "MAINTAINER EXECUTION PROMPT" in ev["2026-10-09T19:28:39Z"]["detail"],
          "maintainer-brief application recorded (2026-10-09T19:28:39Z)")

    fl = json.loads(Path(".agent/feature_list_014.json").read_text(encoding="utf-8"))
    st = {f["id"]: f["status"] for f in fl["features"]}
    check([f["id"] for f in fl["features"]] == ["099", "103", "104", "105", "106", "107", "109", "108", "100", "101", "102"],
          "feature list order = single lane")
    check(all(st[i] == "complete" for i in ("099", "103", "104", "105"))
          and all(st[i] == "pending" for i in ("106", "107", "109", "108", "100", "101", "102")), "feature statuses", str(st))
    deps = {f["id"]: f["dependencies"] for f in fl["features"]}
    check(deps["108"] == ["106", "107", "109"] and deps["101"] == ["099", "100"]
          and sorted(deps["102"]) == ["099", "100", "101", "103", "104", "105", "106", "107", "108", "109"]
          and all(deps[i] == [] for i in ("106", "107", "109", "100")), "pending-feature dependencies")
    est = {f["id"]: (f["estimated_lines"], f.get("estimated_lines_range")) for f in fl["features"]}
    want = {"106": (750, [530, 960]), "107": (680, [510, 850]), "109": (710, [520, 890]), "108": (690, [510, 860]),
            "100": (780, [550, 1000]), "101": (890, [580, 1200]), "102": (850, [600, 1100])}
    check(all(est[k] == v for k, v in want.items()), "pending estimates and ranges")
    check(sum(v[0] for v in want.values()) == 5350 and 3714 + 5350 == 9064 < 11180, "remaining 5350; projection 9064 < 11180")
    check(sum(f["estimated_lines"] for f in fl["features"]) == 7980, "feature-list estimates sum 7980 (V13 gap)")
    spec = yaml.safe_load(re.match(r"^---\n(.*?)\n---\n", Path(".agent/product_spec_014.md").read_text(encoding="utf-8"), re.S).group(1))
    check(str(spec["spec_version"]) == fl["spec_version"] == "1.1.6", "spec_version lockstep 1.1.6 (no drift)")
    ph = yaml.safe_load(Path("docs/planning/phase_014.yaml").read_text(encoding="utf-8"))
    check(ph["status"] == "in_progress" and {s["id"]: s["status"] for s in ph["steps"]} ==
          {"099": "COMPLETED", "103": "COMPLETED", "104": "COMPLETED", "105": "COMPLETED", "106": "PENDING", "107": "PENDING",
           "109": "PENDING", "108": "PENDING", "100": "PENDING", "101": "PENDING", "102": "PENDING"}, "phase_014.yaml statuses")
    mf = json.loads(Path("docs/planning/manifest.json").read_text(encoding="utf-8"))
    check(mf["current_phase"] == "014-ga-track", "manifest current_phase 014-ga-track")

    debt = Path("docs/planning/DEBT.md").read_text(encoding="utf-8")
    m = re.search(r"^version: (\S+)", debt, re.M)
    open_t = debt.split("## Open")[1].split("## Resolved")[0]
    rows = re.findall(r"^[|] (NDEBT-[0-9]+) [|] [^|]+ [|] (\w+) [|]", open_t, re.M)
    check(m.group(1) == "0.51.0", "DEBT.md version 0.51.0")
    check([r[0] for r in rows] == ["NDEBT-047", "NDEBT-046", "NDEBT-045", "NDEBT-044", "NDEBT-040", "NDEBT-037", "NDEBT-034", "NDEBT-026"]
          and all(r[1] == "Low" for r in rows), "DEBT Open set = 047,046,045,044,040,037,034,026, all Low", str(rows))
    r = Path("docs/planning/ROADMAP.md").read_text(encoding="utf-8").split("## Current Position")[1].split("\n## ")[0]
    bullet = [x for x in r.split("\n- ") if x.startswith("Open debt (current")]
    got = set(re.findall(r"NDEBT-[0-9]+", bullet[0].split("Resolved")[0])) if len(bullet) == 1 else set()
    check(got == {x[0] for x in rows}, "ROADMAP open-debt bullet == DEBT Open set (feature 102 AT5 assertion)", str(sorted(got)))

    check(git("cat-file", "-t", "v1.4.0") == "tag" and git("rev-parse", "v1.4.0").startswith("bb32064")
          and git("rev-parse", "v1.4.0^{commit}").startswith("9edd5d0"), "v1.4.0 = annotated tag bb32064 on 9edd5d0")
    check(git("tag", "--sort=-creatordate").splitlines()[0] == "v1.4.0", "v1.4.0 is the latest tag")
    merges = {"88959c9": "(#66)", "b8ea889": "(#67)", "2a53764": "(#68)", "e2a50ed": "(#70)", "483f016": "(#65)", "02b02c6": "(#64)", "9edd5d0": "(#63)"}
    for sha, pr in merges.items():
        check(git_ok("merge-base", "--is-ancestor", sha, "HEAD") and pr in git("log", "-1", "--format=%s", sha),
              f"{sha} is on this lineage with subject {pr}")
    wf = yaml.safe_load(Path(".github/workflows/compliance.yml").read_text(encoding="utf-8"))
    check(set(wf["jobs"]) == {"validate", "e2e_bootstrap", "fixtures_self_test", "convergent_review"},
          "compliance.yml jobs = validate, e2e_bootstrap, fixtures_self_test, convergent_review", str(sorted(wf["jobs"])))
    check(wf["concurrency"]["cancel-in-progress"] is True, "compliance.yml concurrency cancel-in-progress: true")
    pos = Path(".agent/evidence/104/ci-positive-run.txt").read_text(encoding="utf-8")
    neg = Path(".agent/evidence/104/ci-negative-run.txt").read_text(encoding="utf-8")
    check("37980556248" in pos and "CONFORMANCE: FULL" in Path(".agent/evidence/104/ci-positive-log.txt").read_text(encoding="utf-8"),
          "104 positive run 37980556248 with CONFORMANCE: FULL")
    check("37980776642" in neg and "AssertionError: 40 != 0" in Path(".agent/evidence/104/ci-negative-log.txt").read_text(encoding="utf-8"),
          "104 negative control 37980776642 with AssertionError: 40 != 0")
    check("--allow-unsupported-isolation" in Path("tools/test_convergent_review.py").read_text(encoding="utf-8"),
          "tools/test_convergent_review.py has --allow-unsupported-isolation")

    # Every path HANDOVER.md cites exists (git refs resolve as refs).
    future = {"tools/fixtures/runtime_session/", ".agent/evidence/pilot-100/", ".agent/evidence/pilot-100/aggregate.json"}
    bare_future = {"review.json", "gates-record.json"}
    text = Path("docs/planning/HANDOVER.md").read_text(encoding="utf-8").split("\n---\n", 1)[1]
    missing = []
    for tok in sorted(set(re.findall(r"`([^`\s]+)`", text))):
        if any(c in tok for c in "<*") or tok.startswith(("http", "--")):
            continue
        is_pathlike = "/" in tok or re.search(r"\.(md|json|py|sh|yaml|yml|txt)$", tok)
        if not is_pathlike or tok in future or tok in bare_future:
            continue
        name = tok[len("origin/"):] if tok.startswith("origin/") else tok
        if git_ok("rev-parse", "--verify", "-q", f"refs/remotes/origin/{name}") or git_ok("rev-parse", "--verify", "-q", f"refs/heads/{name}"):
            continue
        if tok == "measure.py":
            tok = ".agent/evidence/scope-budget-014/measure.py"
        if not Path(tok.rstrip("/")).exists():
            missing.append(tok)
    check(not missing, "every repository path / ref HANDOVER.md cites exists", ", ".join(missing))


def frontmatter() -> None:
    """Validate the frontmatter of every doc this handover touched."""
    schema = json.loads(Path("schema/frontmatter.schema.json").read_text(encoding="utf-8"))
    for doc in ("docs/planning/HANDOVER.md", "docs/planning/ROADMAP.md", "docs/planning/backlog_reconciliation.md"):
        m = re.match(r"^---\n(.*?)\n---\n", Path(doc).read_text(encoding="utf-8"), re.S)
        fm = yaml.safe_load(m.group(1)) if m else None
        errs = [] if fm is None else [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(fm)]
        check(fm is not None and not errs and fm["authoritative_source"] == doc,
              f"{doc} frontmatter valid (version {fm and fm.get('version')}, top change_log {fm and fm['change_log'][0]['version']})",
              "; ".join(errs) or "authoritative_source mismatch")
        check(fm is not None and fm["version"] == fm["change_log"][0]["version"], f"{doc} version == newest change_log entry")


def frozen() -> None:
    """Prove the frozen phase-014 acceptance infrastructure is unchanged."""
    d = ".agent/evidence/phase-014-activation/"
    check(git_ok("diff", "--quiet", "e2a50ed", "--", d), f"no diff against e2a50ed under {d}")
    check(git("status", "--porcelain", "--untracked-files=all", "--", d) == "", f"no untracked or modified file under {d}")
    pins = {
        "gates/phase_tag_check.py": "72f8df85c9e64bec711c909ce38cc27ae518715e1a8644fa9774af5a72a91b3b",
        "gates/scratch_run.py": "7135e7a41a924a98aad1076b68e3df9fd9b06ce4406abb83f19cab2ff7460451",
        "gates/validator_gate.py": "d343318c23a74473dc6365ae7f9d1dc48708c2ebba209a5d4a0373e9c7881166",
        "audits-baseline.txt": "4eaec75056d0d926836ad45c439dd936ac5169d717f640b231c0f73172143174",
        "tag-baseline.txt": "d548ed02934b39a286ccc61c279d88728c2af76a8fbfffb230013e49188b8b14",
        "validate.txt": "35aaee4c2ff8288ed7757e7ec135f913b49ffeae77be1f6db32baba22032ec22",
        "validate_payload.txt": "16cae6f76d8ddc81f54b7400881dd5fdd344de1f58e8ecec0de26b584cf4e680",
    }
    bad = [p for p, h in pins.items() if hashlib.sha256(Path(d + p).read_bytes()).hexdigest() != h]
    check(not bad, "feature 102 AT7 sha256 pins hold (7 files)", ", ".join(bad))


def dag() -> None:
    """Assert the backlog DAG validator fails only on the pre-existing V7 (statuses) and V13."""
    out = subprocess.run([sys.executable, ".agent/evidence/backlog-reconciliation-2026-10-08/tools/validate_backlog_dag.py",
                          "--git-status", "/dev/null"], capture_output=True, text=True)
    print(out.stdout, end="")
    print(out.stderr, end="")
    fails = {ln.split()[1]: ln for ln in out.stdout.splitlines() if ln.startswith("FAIL ")}
    check(set(fails) == {"V7", "V13"}, "DAG validator failing set is exactly the pre-existing {V7, V13}", str(sorted(fails)))
    v7 = fails.get("V7", "").split(" -- ", 1)[-1].split("; ")
    check(all(re.fullmatch(r"(099|103|104|105): status pending != canonical complete", x) for x in v7),
          "V7 fails only on the four completed packets' statuses (estimates now mirrored)", "; ".join(v7))
    check("dag 8600" in fails.get("V13", ""), "V13 sees the refreshed DAG budget 8600 (gap 7980 is canonical, by design)")
    check("SPEC DRIFT" not in fails.get("V13", ""), "V13 has no spec drift (DAG activated_phase.spec_version synced to 1.1.6)",
          fails.get("V13", ""))
    check(out.returncode == 1, "validator exit 1 (the two pre-existing failures)")


def dagpath() -> None:
    """Show that the DAG's derived critical path runs through F099 only because of stale packet statuses."""
    import os
    import tempfile
    tool = ".agent/evidence/backlog-reconciliation-2026-10-08/tools/validate_backlog_dag.py"

    def paths(extra: list[str]) -> tuple[str, str]:
        out = subprocess.run([sys.executable, tool, "--git-status", "/dev/null", *extra], capture_output=True, text=True).stdout
        lines = out.splitlines()
        tech = next(lines[i + 1].strip() for i, ln in enumerate(lines) if ln.startswith("technical critical path"))
        phase = next(ln for ln in lines if ln.startswith("phase-014 critical path"))
        return tech, phase

    tech, phase = paths([])
    print("as committed:\n  " + tech + "\n  " + phase)
    check("-> F099 -> F101 -> F102 ->" in tech and "[weighted lines 19720-25910]" in tech and phase.endswith("ACT-014 -> F099 -> F101 -> F102"),
          "as committed: critical paths run through F099 (19720-25910)")
    doc = json.loads(Path("docs/planning/backlog_dag.json").read_text(encoding="utf-8"))
    changed = 0
    for pk in doc["packets"]:
        if pk["id"] in ("F099", "F103", "F104", "F105"):
            pk["status"] = "complete"
            changed += 1
    check(changed == 4, "what-if copy changes exactly four packet statuses")
    fd, tmp = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        tech2, phase2 = paths(["--dag", tmp])
    finally:
        os.unlink(tmp)
    print("with F099/F103/F104/F105 complete:\n  " + tech2 + "\n  " + phase2)
    check("-> F100 -> F101 -> F102 ->" in tech2 and "[weighted lines 19580-25770]" in tech2 and phase2.endswith("ACT-014 -> F100 -> F101 -> F102"),
          "statuses refreshed: critical paths run through F100 (19580-25770)")


def main() -> int:
    """Dispatch one subcommand."""
    modes = {"facts": facts, "frontmatter": frontmatter, "frozen": frozen, "dag": dag, "dagpath": dagpath}
    if len(sys.argv) != 2 or sys.argv[1] not in modes:
        print(f"usage: {sys.argv[0]} {{{'|'.join(modes)}}}", file=sys.stderr)
        return 1
    modes[sys.argv[1]]()
    print(f"SUMMARY: {'FAIL' if failures else 'PASS'} ({len(failures)} failing)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
