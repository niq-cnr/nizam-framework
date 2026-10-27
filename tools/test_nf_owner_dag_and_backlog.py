#!/usr/bin/env python3
"""Mechanical verification of the NF-OWNER-2026-10-27 execution DAG, backlog crosswalk, and governance separation."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent
PLAN_DIR = ROOT / "docs" / "planning" / "nf-owner-2026-10-27"
DAG_PATH = PLAN_DIR / "execution-dag.json"
CROSSWALK_PATH = PLAN_DIR / "INTAKE_AND_BACKLOG_CROSSWALK.md"
ARCH_PATH = PLAN_DIR / "ARCHITECTURE_AND_MIGRATION.md"
GAUNTLET_PATH = PLAN_DIR / "GAUNTLET_AND_GATES.md"


class NfOwnerDagAndBacklogTests(unittest.TestCase):
    def test_dag_acyclic_complete_and_preserves_backlog(self) -> None:
        """Verify execution-dag.json is acyclic, maps NF-R01..NF-R05 & NF-AC01..NF-AC05, and preserves JR/Phase020/Debts."""
        self.assertTrue(DAG_PATH.is_file(), f"Missing {DAG_PATH}")
        dag = json.loads(DAG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(dag["mandate_id"], "NF-OWNER-2026-10-27")
        self.assertEqual(
            dag["baseline"]["commit_sha"],
            "2b8298ae1d5a41534e00b6710a738b4b181b87fa",
        )
        self.assertEqual(
            dag["baseline"]["tree_sha"],
            "cf9bf9ffd066c4c2724837baaf652323af230f52",
        )
        self.assertEqual(dag["baseline"]["installed_nizam_pin"]["version"], "v2.0.0")
        self.assertEqual(
            dag["baseline"]["installed_nizam_pin"]["commit_sha"],
            "603afc7b17919334a6a01df1e39e63798d9d0acd",
        )

        # Verify preserved upstream programs exist and match actual files on disk
        preserved = dag["preserved_programs"]
        jr_dag_path = ROOT / preserved["jev_readiness"]["authority_path"]
        self.assertTrue(jr_dag_path.is_file())
        self.assertEqual(preserved["jev_readiness"]["requirement_count"], 36)
        self.assertEqual(preserved["jev_readiness"]["acceptance_criteria_count"], 239)
        self.assertEqual(
            preserved["phase_020_sbcl_fresh_acceptance"]["feature_sequence"],
            ["130", "131", "132"],
        )
        self.assertEqual(
            preserved["docker_trial_adapter_and_debts"]["open_debts"],
            ["NDEBT-034", "NDEBT-040", "NDEBT-056"],
        )
        self.assertEqual(preserved["api_ref_pilot"]["disposition"], "defer")

        # Verify nodes N00..N08 and J01 exist and form a valid acyclic DAG
        nodes = {n["id"]: n for n in dag["nodes"]}
        expected_ids = {"N00", "N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08", "J01"}
        self.assertEqual(set(nodes.keys()), expected_ids)

        visiting: set[str] = set()
        visited: set[str] = set()

        def dfs(nid: str) -> None:
            self.assertNotIn(nid, visiting, f"Cycle detected at {nid}")
            if nid in visited:
                return
            visiting.add(nid)
            for dep in nodes[nid]["depends_on"]:
                self.assertIn(dep, nodes, f"Unknown dependency {dep} in {nid}")
                dfs(dep)
            visiting.remove(nid)
            visited.add(nid)

        for nid in nodes:
            dfs(nid)

        # Check all NF-R01..NF-R05 and NF-AC01..NF-AC05 are covered by completed nodes N00..N08
        covered_reqs: set[str] = set()
        covered_acs: set[str] = set()
        for nid in ("N00", "N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08"):
            node = nodes[nid]
            self.assertEqual(node["status"], "completed", f"Node {nid} must be completed")
            covered_reqs.update(node["requirements"])
            covered_acs.update(node["acceptance_criteria"])
            for sp in node["scope_paths"]:
                self.assertTrue((ROOT / sp).exists(), f"Missing scope_path {sp} for node {nid}")
        self.assertEqual(covered_reqs, {"NF-R01", "NF-R02", "NF-R03", "NF-R04", "NF-R05"})
        self.assertEqual(covered_acs, {"NF-AC01", "NF-AC02", "NF-AC03", "NF-AC04", "NF-AC05"})
        self.assertEqual(nodes["J01"]["status"], "externally_gated")

    def test_installed_nizam_and_run_state_preserved_untouched(self) -> None:
        """Verify .nizam/ (v2.0.0) and .agent/run_state.json were not modified or forged."""
        prov = json.loads((ROOT / ".nizam" / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(prov["tag"], "v2.0.0")
        self.assertEqual(prov["resolved_sha"], "603afc7b17919334a6a01df1e39e63798d9d0acd")

        run_state = json.loads((ROOT / ".agent" / "run_state.json").read_text(encoding="utf-8"))
        self.assertEqual(run_state["current_phase"], "020-sbcl-fresh-acceptance")
        self.assertEqual(run_state["current_feature"], "130")
        self.assertIsNone(run_state.get("active_contract"))
        self.assertEqual(run_state["status"], "in_progress")

        # Verify git diff against origin/main has zero changes under .nizam/ or .agent/run_state.json
        diff_proc = subprocess.run(
            ["git", "-C", str(ROOT), "diff", "--name-only", "origin/main", "--", ".nizam", ".agent/run_state.json"],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(diff_proc.stdout.strip(), "")

    def test_planning_documents_present_and_complete(self) -> None:
        """Verify crosswalk, LAASP architecture, and hostile gauntlet documents exist and contain required sections."""
        for doc_path in (CROSSWALK_PATH, ARCH_PATH, GAUNTLET_PATH):
            self.assertTrue(doc_path.is_file(), f"Missing {doc_path}")
            text = doc_path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), f"{doc_path} missing YAML frontmatter")

        crosswalk = CROSSWALK_PATH.read_text(encoding="utf-8")
        for token in ("JR-00", "020-sbcl-fresh-acceptance", "#107", "NDEBT-034", "NDEBT-040", "NDEBT-056", "API-REF-PILOT", "NF-R01", "NF-R05"):
            self.assertIn(token, crosswalk)

        gauntlet = GAUNTLET_PATH.read_text(encoding="utf-8")
        for gate in ("G1", "G2", "G3", "G4", "G5", "G6", "Node `N04` Exit Report", "Node `N08` Exit Report", "Node `J01`"):
            self.assertIn(gate, gauntlet)


if __name__ == "__main__":
    unittest.main()
