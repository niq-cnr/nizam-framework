#!/usr/bin/env python3
"""Stage1 planning assessment (2026-10-11); frozen after this planning PR."""

import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import sys

import jsonschema
import yaml

DAG = Path("docs/planning/backlog_dag.json")
CANONICAL = Path(".agent/feature_list_014.json")
CONCERNS = ["NDEBT-047", "NDEBT-046", "NDEBT-045", "A04a"]
TERMINAL = {"complete", "cancelled"}
BASE = "0de2820c87b154929a854840a7d85b4497afde9c"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def proof_exists(reference):
    if Path(reference).exists():
        return True
    commit = re.search(r"\bcommit ([0-9a-f]{40})\b", reference)
    return bool(commit) and subprocess.run(["git", "cat-file", "-e", commit[1] + "^{commit}"], capture_output=True).returncode == 0


def validate(doc):
    packets = doc["packets"]
    baseline = json.loads(subprocess.check_output(["git", "show", BASE + ":docs/planning/backlog_dag.json"], text=True))
    base_packets = {p["id"]: p for p in baseline["packets"]}
    require(set(p["id"] for p in packets) == set(base_packets), "unauthorized packet inventory")
    for p in packets:
        original = base_packets[p["id"]]
        expected = copy.deepcopy(original["prerequisites"]["authority"])
        authority_status = original["authority_status"]
        if p["id"] == "A04a":
            authority_status = "authorized"
            expected = {"satisfied": True, "reason": "Operator authorized the bounded A04a maintenance scope; execution requires PR1 merge and independent maintenance contract gates."}
        require(p["authority_status"] == authority_status and p["prerequisites"]["authority"] == expected, "unrecorded packet authority: " + p["id"])
        if p.get("feature_id") is None:
            require(p["status"] == original["status"], "unrecorded nonfeature status: " + p["id"])
    by_id = {p["id"]: p for p in packets}
    require(len(by_id) == len(packets), "duplicate packet IDs")
    require(doc["plan_status"] == "candidate", "future plan must remain candidate")
    require(doc["activated_phase"]["current_status"] == "complete", "phase mirror is stale")
    schema = json.loads(Path("schema/work-packet.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(schema)
    for p in packets:
        validator.validate(p)
        require(p["status"] in TERMINAL | {"pending", "in_progress"}, "unknown status")
        edges = p["dependency_edges"]
        for key in ("depends_on", "serialize_after", "consumed_by"):
            require(len(edges[key]) == len(set(edges[key])), "duplicate edges")
            require(all(x in by_id for x in edges[key]), "dangling reference")
        inverse = sorted(q["id"] for q in packets if p["id"] in q["dependency_edges"]["depends_on"])
        require(sorted(edges["consumed_by"]) == inverse, "inverse edge drift")
        if p["status"] not in TERMINAL:
            require(not any(by_id[x]["status"] == "cancelled" for x in edges["depends_on"] + edges["serialize_after"]), "active cancelled dependency")
        pre = p["prerequisites"]
        for key in ("technical", "authority", "environment", "evidence"):
            require(isinstance(pre[key]["satisfied"], bool) and pre[key]["reason"].strip(), "invalid prerequisite")
            if p["status"] not in TERMINAL:
                require(not re.search(r"\b(?:F101|(?:feature )?101)(?:['’]s)?\s+(?:findings|audit artifact)", pre[key]["reason"], re.I), "obsolete live F101 evidence premise")
        if p["status"] not in TERMINAL:
            reason = pre["technical"]["reason"]
            named = set(re.findall(r"\bNIP3-\d+\b", reason))
            require(named.issubset(set(edges["depends_on"] + edges["serialize_after"])), "obsolete live predecessor premise")
            if p["id"].startswith("NIP3-"):
                require(all(dep in reason for dep in edges["depends_on"]), "live predecessor premise mismatch")
        if pre["evidence"]["satisfied"]:
            proof = p.get("available_inputs", p["evidence"])
            require(bool(proof) and all(proof_exists(x) for x in proof), "nonexistent satisfied evidence")
        if p["status"] not in TERMINAL and p["authority_status"] != "authorized":
            require(not pre["authority"]["satisfied"], "unapproved authority marked satisfied")
    visiting, visited = set(), set()

    def visit(pid):
        require(pid not in visiting, "cycle")
        if pid in visited:
            return
        visiting.add(pid)
        edges = by_id[pid]["dependency_edges"]
        for dep in edges["depends_on"] + edges["serialize_after"]:
            visit(dep)
        visiting.remove(pid)
        visited.add(pid)

    for pid in by_id:
        visit(pid)
    features = json.loads(CANONICAL.read_text())["features"]
    mirrors = [p for p in packets if p.get("feature_id") is not None]
    require(len(mirrors) == len(features), "canonical mirror count")
    for feature in features:
        found = [p for p in mirrors if p["feature_id"] == feature["id"]]
        require(len(found) == 1, "canonical mirror identity")
        p = found[0]
        require(p["status"] == feature["status"], "canonical status mismatch")
        require(set(p["dependency_edges"]["depends_on"]) == {"ACT-014"} | {"F" + x for x in feature["dependencies"]}, "canonical dependency mismatch")
        require(p["estimate"]["weighted_lines"] == [feature["estimated_lines"]] * 2, "canonical estimate mismatch")
        if p["status"] == "complete":
            qa_path = ".agent/qa/" + feature["id"] + ".json"
            qa = json.loads(Path(qa_path).read_text())
            require(qa["qa_pass"] and qa["final_verdict"]["approved"], "completed feature lacks approved QA")
            require(all(not qa[k] for k in ("issues", "missing_acceptance_coverage", "unsupported_claims")), "completed QA has blocking findings")
            require(qa_path in p["evidence"] and all(Path(x).exists() for x in qa["evidence_files"]), "completed feature proof missing")
        else:
            require(not p["prerequisites"]["technical"]["satisfied"] and not p["prerequisites"]["evidence"]["satisfied"], "cancelled execution enabled")
    for pid in ("PLAN-NEXT", "A03-WA-FINAL", "A03-RT", "PLAN-WA"):
        p = by_id[pid]
        require("F101" not in p["dependency_edges"]["depends_on"], "cancelled F101 dependency")
        inputs = p["available_inputs"]
        require(".agent/evidence/102/ga-readiness.json" in inputs and ".agent/qa/self-commission-v1.5.0.json" in inputs, "factual replacement inputs missing")
        require(all(Path(x).is_file() for x in inputs), "fake replacement input")
        require("101 findings" not in p["prerequisites"]["evidence"]["reason"], "obsolete F101 evidence premise")
    for pid in ("PLAN-NEXT", "PLAN-WA"):
        require(not by_id[pid]["prerequisites"]["authority"]["satisfied"], "future NIP/WA activated")
    notice = doc["authorized_follow_up"]
    require(notice["concerns"] == CONCERNS and notice["numeric_feature_ids_allocated"] is False, "unauthorized maintenance scope")
    require(notice["sequence"] == ["planning-refresh-PR-merge", "independent-maintenance-contract-gates", "maintenance-source-PR"], "maintenance sequence bypass")
    a04 = by_id["A04a"]
    require(a04["status"] == "pending" and a04["authority_status"] == "authorized" and not a04["dependency_edges"]["depends_on"], "A04a standalone boundary")
    require(not a04["prerequisites"]["technical"]["satisfied"] and not a04["prerequisites"]["evidence"]["satisfied"], "maintenance prematurely executable")
    ready = [p["id"] for p in packets if p["status"] not in TERMINAL and all(x["satisfied"] for x in p["prerequisites"].values()) and all(by_id[x]["status"] == "complete" for x in p["dependency_edges"]["depends_on"])]
    require(not {"F100", "F101", "A04a"}.intersection(ready), "terminal or ungated maintenance ready")
    print("CURRENT VIEW PASS:", len(features), "canonical mirrors; ready =", ready)


def documents(doc):
    paths = ["docs/planning/backlog_reconciliation.md", "docs/planning/ROADMAP.md", "docs/planning/HANDOVER.md"]
    schema = json.loads(Path("schema/frontmatter.schema.json").read_text())
    texts = {}
    for path in paths:
        text = Path(path).read_text()
        fm = yaml.safe_load(text.split("---", 2)[1])
        jsonschema.Draft202012Validator(schema).validate(fm)
        require(fm["authoritative_source"] == path and fm["version"] == fm["change_log"][0]["version"], "document frontmatter/version drift")
        texts[path] = text
    human = texts[paths[0]].split("## Current planning view", 1)[1].split("## Prior reconciliation history", 1)[0]
    for feature in json.loads(CANONICAL.read_text())["features"]:
        require("| F" + feature["id"] + " | " + feature["status"] + " |" in human, "human canonical status mismatch")
    require(all(x in human for x in CONCERNS), "human maintenance notice missing")
    require("check_current_view.py" in human and ".agent/qa/self-commission-v1.5.0.json" in human, "human proof/checker pointers")
    for text in texts.values():
        prose = re.sub(r"\s+", " ", text.lower())
        require("planning refresh" in prose and re.search(r"separate(?:ly gated)? maintenance contract", prose), "current two-step notice missing")
    require("AGENTS.md" in texts[paths[2]] and "SELF_GOVERNANCE.md" in texts[paths[2]], "handover installed routing missing")
    print("DOCUMENT VIEW PASS: current status, versions, commissioned pointers and authorized sequence")


def controls(doc):
    validate(doc)
    cases = []
    for kind in ("stale", "reactivated", "cancelled-dependency", "cycle", "fake-proof", "future-authority", "obsolete-premise", "obsolete-predecessor"):
        mutant = copy.deepcopy(doc)
        p = {x["id"]: x for x in mutant["packets"]}
        if kind == "stale": p["F099"]["status"] = "pending"
        elif kind == "reactivated": p["F100"]["status"] = "in_progress"
        elif kind == "cancelled-dependency":
            p["PLAN-NEXT"]["dependency_edges"]["depends_on"].append("F101")
            p["F101"]["dependency_edges"]["consumed_by"].append("PLAN-NEXT")
        elif kind == "cycle":
            p["A04a"]["dependency_edges"]["depends_on"] = ["A04a"]
            p["A04a"]["dependency_edges"]["consumed_by"] = ["A04a"]
        elif kind == "fake-proof": p["PLAN-NEXT"]["available_inputs"].append(".agent/evidence/nonexistent-planning-proof.txt")
        elif kind == "future-authority": p["PLAN-NEXT"]["prerequisites"]["authority"]["satisfied"] = True
        elif kind == "obsolete-premise": p["NIP3-110"]["prerequisites"]["evidence"]["reason"] = "101 findings reconciled at PLAN-NEXT"
        else: p["NIP3-111"]["prerequisites"]["technical"]["reason"] = "NIP3-103"
        try:
            validate(mutant)
        except (ValueError, jsonschema.ValidationError):
            cases.append(kind)
            print("NEGATIVE REJECTED:", kind)
        else:
            raise ValueError("negative unexpectedly passed: " + kind)
    future = [p for p in doc["packets"] if p.get("feature_id") is None and p["status"] not in TERMINAL and p["id"] != "A04a"]
    for original in future:
        for kind in ("combined-authority", "terminal-status-spoof", "in-progress-status-spoof"):
            mutant = copy.deepcopy(doc)
            target = next(p for p in mutant["packets"] if p["id"] == original["id"])
            if kind == "combined-authority":
                target["authority_status"] = "authorized" if original["authority_status"] != "authorized" else "proposal"
                target["prerequisites"]["authority"]["satisfied"] = not original["prerequisites"]["authority"]["satisfied"]
            else:
                target["status"] = "complete" if kind == "terminal-status-spoof" else "in_progress"
            try:
                validate(mutant)
            except (ValueError, jsonschema.ValidationError):
                cases.append(kind + ":" + original["id"])
                print("NEGATIVE REJECTED:", cases[-1])
            else:
                raise ValueError("negative unexpectedly passed: " + kind + ":" + original["id"])
    require(len(cases) == 8 + 3 * len(future), "negative controls incomplete")
    print("CONTROLS PASS:", len(cases), "isolated mutations; entire future authority/status projection bound to approved base")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dag", type=Path, default=DAG)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--documents", action="store_true")
    args = parser.parse_args()
    doc = json.loads(args.dag.read_text())
    try:
        if args.self_test: controls(doc)
        elif args.documents: documents(doc)
        else: validate(doc)
    except (ValueError, KeyError, OSError, jsonschema.ValidationError) as error:
        print("CURRENT VIEW FAIL:", error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
