#!/usr/bin/env python3
"""Negative controls for validate_backlog_dag.py: each mutated DAG must FAIL the named check.

Run from the repository root:

    python3 .agent/evidence/backlog-reconciliation-2026-10-08/tools/dag_negative_controls.py

Each DAG control copies docs/planning/backlog_dag.json into a private temporary directory,
applies one mutation, runs the validator with --dag, and requires exit 1 plus a FAIL line
for the targeted check. The unmutated copy must pass (exit 0). Nothing under the
repository is written. Exit 0 only if every control behaves as expected.
"""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VALIDATOR = ".agent/evidence/backlog-reconciliation-2026-10-08/tools/validate_backlog_dag.py"
BASE = json.loads(Path("docs/planning/backlog_dag.json").read_text(encoding="utf-8"))
TMP = Path(tempfile.mkdtemp(prefix="dag-negctl-"))


def pk(doc: dict, pid: str) -> dict:
    """Return the packet with id pid."""
    return next(p for p in doc["packets"] if p["id"] == pid)


def m_cycle(d):
    pk(d, "F099")["dependency_edges"]["serialize_after"].append("F102")


def m_dangling(d):
    pk(d, "F101")["dependency_edges"]["depends_on"].append("F999")


def m_drop_edge(d):
    pk(d, "F101")["dependency_edges"]["depends_on"].remove("F099")
    pk(d, "F099")["dependency_edges"]["consumed_by"].remove("F101")


def m_drop_feature(d):
    d["packets"] = [p for p in d["packets"] if p["id"] != "F105"]
    for p in d["packets"]:
        for k in ("depends_on", "consumed_by", "serialize_after"):
            p["dependency_edges"][k] = [x for x in p["dependency_edges"].get(k, []) if x != "F105"]


def m_drift(d):
    d["activated_phase"]["spec_version"] = "1.0.1"


def m_unordered_writer(d):
    pk(d, "F108")["dependency_edges"]["serialize_after"] = []
    pk(d, "F100")["dependency_edges"]["serialize_after"] = []


def m_alias(d):
    for p in d["packets"]:
        p["aliases"] = [a for a in p["aliases"] if a != "A07"]


def m_provisional_collision(d):
    pk(d, "NIP3-110")["provisional_feature_id"] = "103"


def m_dishonest_status(d):
    d["verification_matrix"]["T09"].update(status="satisfied", evidence=[".agent/evidence/104/ci-positive.txt"])


# V11 controls run with --git-status: the real `git status --porcelain --untracked-files=all` text
# plus the listed extra lines (nothing is written to the repository).
V11_OK = ["?? .agent/validator/phase-014-activation.json", "?? .agent/evidence/phase-014-activation/eval/unit99_later.txt",
          " M .agent/run_state.json"]

CONTROLS = [
    ("unmutated copy passes", None, 0, None),
    ("V11 accepts Validator verdict + later eval/ file + run_state", ("status", V11_OK), 0, "PASS V11"),
    ("V11 rejects another .agent/validator/*.json", ("status", V11_OK + ["?? .agent/validator/phase-014-other.json"]), 1, "FAIL V11"),
    ("V11 rejects a prefix look-alike of the verdict path", ("status", ["?? .agent/validator/phase-014-activation.json.bak"]), 1, "FAIL V11"),
    ("V11 rejects a payload edit (M tools/validate.sh)", ("status", [" M tools/validate.sh"]), 1, "FAIL V11"),
    ("cycle F099 -> ... -> F102 -> F099", m_cycle, 1, "FAIL V6"),
    ("dangling dependency F999", m_dangling, 1, "FAIL V5a"),
    ("canonical edge 101->099 dropped from the mirror", m_drop_edge, 1, "FAIL V7"),
    ("canonical feature 105 missing from the DAG", m_drop_feature, 1, "FAIL V7"),
    ("spec drift (dag says 1.0.1)", m_drift, 1, "FAIL V13"),
    ("shared-file writers left unordered", m_unordered_writer, 1, "FAIL V9"),
    ("alias A07 unmapped", m_alias, 1, "FAIL V8a"),
    ("provisional id collides with allocated 103", m_provisional_collision, 1, "FAIL V7"),
    ("T09 claimed satisfied with non-existent evidence", m_dishonest_status, 1, "FAIL V8b"),
]

bad = 0
try:
    for label, mutate, want_rc, want_line in CONTROLS:
        doc = copy.deepcopy(BASE)
        extra_args: list[str] = []
        if isinstance(mutate, tuple):
            real = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=True).stdout
            sp = TMP / "status.txt"
            sp.write_text(real + "\n".join(mutate[1]) + "\n", encoding="utf-8")
            extra_args = ["--git-status", str(sp)]
        elif mutate:
            mutate(doc)
        path = TMP / "dag.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        p = subprocess.run([sys.executable, VALIDATOR, "--dag", str(path)] + extra_args, capture_output=True, text=True)
        lines = p.stdout.splitlines()
        ok = p.returncode == want_rc and (want_line is None or any(ln.startswith(want_line) for ln in lines))
        bad += not ok
        fails = [ln.split(" -- ")[0] for ln in lines if ln.startswith("FAIL")]
        print(f"{'OK  ' if ok else 'BAD '} {label:<60} rc={p.returncode} want={want_rc} fails={fails}")
finally:
    shutil.rmtree(TMP, ignore_errors=True)
print(f"NEGATIVE CONTROLS: {len(CONTROLS) - bad}/{len(CONTROLS)} behaved as expected")
sys.exit(1 if bad else 0)
