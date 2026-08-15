#!/usr/bin/env python3
"""Static issue-52 methodology assertions for phase-012 feature 088."""

import json
from pathlib import Path

import jsonschema
import yaml


def text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def require(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS {label}")


skill = json.loads(text("tools/skill.json"))
agent_governance = next(c for c in skill["capabilities"] if c["name"] == "agent_governance")
for role in ("Orchestrator", "Planner", "Generator", "Validator", "Evaluator"):
    require(f"R01 skill names {role}", role in agent_governance["description"])

handoff = text("methodology/04_tool_driven_state.md")
for edge in (
    "Orchestrator to\nPlanner",
    "Planner to Generator",
    "Generator to Validator",
    "Validator to Evaluator",
    "Evaluator back to Orchestrator",
):
    require(f"R02 handoff {edge.replace(chr(10), ' ')}", edge in handoff)

eval_doc = text("methodology/05_eval_and_trace.md")
require("R03 Orchestrator eval row", "| Orchestrator |" in eval_doc)
require("R03 five-role eval gate", "any of the five roles" in eval_doc)

breaker = text("methodology/03_circuit_breaker.md")
require("M01 no shared reset", "git reset --hard" not in breaker)
require("M01 no repository clean", "git clean" not in breaker)
require("M01 isolated worktree recovery", "git worktree add --detach" in breaker and "only that exact root" in breaker)
require("M02 canonical phase state", "lifecycle source of truth" in breaker)
require("M02 derived run state", "coordination state derived" in breaker and "idempotent" in breaker)
require("M02 no cross-file atomic claim", "never\n   claims two files share one atomic filesystem write" in breaker)
require("M03 corrected escalation reference", "Escalation (Section 4, step 4)" in breaker)

release = text("methodology/06_release_train.md")
require("M04 durable release prep is gated", "Durable preparation" in release and "pass Loop 1 and Loop 2" in release)
require("M04 only tag act is outside another contract", "tag act is a release **mechanic**" in release and "creates no\ntracked file diff" in release)

promotion = text("methodology/07_eval_gated_promotion.md")
require("M05 eval uses third-attempt trip", "Only a\n   third failed attempt trips the breaker" in promotion)
require("M06 durable repin stays gated", "MUST NOT silently edit the durable capability profile" in promotion)

cross_repo = text("methodology/08_cross_repo_dependency_gate.md")
require("M07 Orchestrator routes but does not author", "The Orchestrator records\n   the dependency and request reference; it does not author the delta" in cross_repo)

planning = text("methodology/00_planning.md")
require("M08 current feature excluded from baseline", "completed **before the current feature**" in planning and "MUST NOT participate in its\n   own baseline" in planning)

execution = text("methodology/01_execution.md")
require("M09 explicit evidence gate", "**Evidence is a completion gate, not post-processing.**" in execution)
require("M09 missing evidence blocks completion", "the feature remains `in_progress`" in execution and "Missing or unreferenced evidence is a Loop 2 failure" in execution)

phase = yaml.safe_load(text("docs/planning/phase_012.yaml"))
jsonschema.validate(phase, json.loads(text("schema/phase.schema.json")))
require("M02 phase-012 canonical document validates", phase["id"] == "012-v1-consumer-safety")
manifest = json.loads(text("docs/planning/manifest.json"))
current = next(p for p in manifest["phases"] if p["id"] == manifest["current_phase"])
require("M02 manifest registers canonical phase document", current["phase_definition"] == "docs/planning/phase_012.yaml")
