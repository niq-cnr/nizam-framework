#!/usr/bin/env python3
"""Read the shipped smoke-precondition record and require the operator freeze.

The check opens the JSON file. It does not restate the comparison.
"""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / ".agent" / "evidence" / "agentic-excellence" / "smoke-preconditions.json"


def main():
    data = json.loads(RECORD.read_text(encoding="utf-8"))
    if data["budget_ceiling_usd"] != 100:
        raise SystemExit("budget ceiling is not the operator selection")
    if data["currency"] != "USD":
        raise SystemExit("currency is not USD")
    if data["stop_on_exhaustion"] is not True:
        raise SystemExit("exhaustion does not stop the smoke")
    if data["paid_model_calls_authorized"] is not True:
        raise SystemExit("paid smoke calls are not authorized")
    if data["confirmation_campaign_authorized"] is not False:
        raise SystemExit("confirmation campaign must stay unauthorized")
    if data["novice_study_authorized"] is not False:
        raise SystemExit("novice study must stay unauthorized")
    snapshot = data["model_snapshot"]
    if snapshot["model"] != "gpt-6.1-sol":
        raise SystemExit("model snapshot is not gpt-6.1-sol")
    if snapshot["reasoning_effort"] != "high":
        raise SystemExit("reasoning effort is not high")
    if snapshot["applies_to_arms"] != ["nizam", "superpowers", "bmad-stable", "spec-kit"]:
        raise SystemExit("model snapshot does not apply to the four primary arms")
    if data["task_manifest"] is not None or data["hidden_oracles"] is not None:
        raise SystemExit("manifest or oracles are recorded before an independent seal")
    if data["scored_smoke"]["status"] != "not-started":
        raise SystemExit("scored smoke must stay not-started until the seal exists")
    if data["match_established"] is not False or data["superiority_established"] is not False:
        raise SystemExit("a match or superiority result is recorded")
    claim = data["claim"]
    if claim != (
        "This record does not say Nizam matches or surpasses "
        "Superpowers, BMAD Method, or GitHub Spec Kit."
    ):
        raise SystemExit("non-claim sentence changed")
    print("smoke-preconditions: 100 USD ceiling and gpt-6.1-sol are frozen")
    print("smoke-preconditions: manifest and oracles are unsealed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
