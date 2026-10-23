"""Read-only F4 diagnostic, OUTSIDE F1/F2 scope; not acceptance or passing QA.

Use the existing upstream synthetic ReceiptFixture in a disposable Git repo.
Its own receipt command really runs successfully. Its authority and QA records
are explicitly synthetic parser fixtures, never operator/QA approvals.
"""
import json
import os
import runpy
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "tools"))
suite = runpy.run_path("tools/test_workflow_assurance.py", run_name="readonly_receipt_diagnostic")
api = suite["load_api"]()
sp = runpy.run_path("tools/start_path.py", run_name="readonly_qa_predicate")
prior = os.environ.get("NIZAM_WA120_FIXTURE")
os.environ["NIZAM_WA120_FIXTURE"] = "observed"
results = []
try:
    with tempfile.TemporaryDirectory(prefix="nizam-r02-receipt-readonly-") as parent:
        f = suite["ReceiptFixture"](api, parent)

        def inspect(label):
            entry = next(e for e in f.policy["prerequisites"] if e["kind"] == "fresh-qa")
            value = api.parse_json(api._receipt_artifact(f.root, entry["artifact"]))
            result = {
                "case": label,
                "direct_qa_predicate_passes": sp["qa_passes"](value),
                "fresh_qa": value,
                "receipt_own_capture": {
                    k: f.capture[k] for k in ("executed", "exit_code", "outcome")
                },
            }
            try:
                api.verify_stage_receipt(f.root, f.receipt, policy=f.policy)
                result["receipt_accepted"] = True
                result["proposed_transition"] = api.plan_receipt_transition(
                    f.root, f.state, f.receipt, policy=f.policy,
                )["action"]
            except api.AssuranceError as exc:
                result["receipt_accepted"] = False
                result["diagnostic"] = str(exc)
            results.append(result)

        inspect("aggregate_pass_with_empty_per_check_evidence")
        f.bad_artifact("fresh-qa", lambda value: value.update(
            evidence_files=["proof/never-executed.json"],
            checks=[{
                "command": "ordinary-failed-check", "executed": True,
                "exit_code": 7, "status": "failed",
                "evidence": "proof/never-executed.json",
            }],
        ))
        inspect("aggregate_pass_with_declared_failed_check_and_missing_evidence")
        f.bad_artifact("fresh-qa", lambda value: value.update(qa_pass=False))
        inspect("aggregate_fail_control")
finally:
    if prior is None:
        os.environ.pop("NIZAM_WA120_FIXTURE", None)
    else:
        os.environ["NIZAM_WA120_FIXTURE"] = prior

print(json.dumps({
    "kind": "read-only unmodified source diagnostic using disposable upstream fixture",
    "scope": "OUTSIDE F1/F2 implementation scope; not acceptance or passing QA",
    "limits": "Synthetic QA/authority records; actual successful receipt command. No source mutation or actual governance transition.",
    "results": results,
}, indent=2))
