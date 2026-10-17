#!/usr/bin/env python3
"""Drive tools/start_path.py against temporary project records."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "start_path.py"


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the shipped start-path command against one project root."""
    return subprocess.run(
        [sys.executable, str(TOOL), *args, "--root", str(root)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write(root: Path, relative: str, payload: dict) -> None:
    """Write one JSON record under the temporary project."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def cause(path_id: str) -> dict:
    return {
        "id": path_id,
        "path": "bugfix",
        "summary": "The public start path had no consumer.",
        "evidence": ["readme promised a file no tool read"],
    }


def scope(path_id: str, files: list[str], contract_id: str | None = None) -> dict:
    payload = {
        "id": path_id,
        "path": "bugfix",
        "files": files,
        "non_goals": ["no feature-loop change"],
    }
    if contract_id is not None:
        payload["contract_id"] = contract_id
    return payload


def contract(status: str, paths: list[str]) -> dict:
    return {
        "contract_id": "c1",
        "feature_id": "c1",
        "name": "repair",
        "status": status,
        "spec_ref": ".agent/product_spec.md",
        "scope": {
            "files_create": [],
            "files_modify": [{"path": path, "purpose": "repair"} for path in paths],
        },
        "non_goals": ["no new feature"],
        "verification": [
            {
                "acceptance_test": "start path done",
                "command": "python3 tools/start_path.py done bugfix --id demo",
            }
        ],
        "estimated_lines": 10,
        "evidence_dir": ".agent/evidence",
        "evidence_convention": "one JSON receipt per command",
    }


def qa(path_id: str, evidence: str) -> dict:
    return {
        "feature_id": path_id,
        "qa_pass": True,
        "checks_run": 1,
        "checks_passed": 1,
        "adversarial": {"performed": True},
        "evidence_files": [evidence],
        "issues": [],
        "unsupported_claims": [],
        "missing_acceptance_coverage": [],
        "required_fixes": [],
        "final_verdict": {"approved": True, "summary": "verification recorded"},
    }


def expect(result: subprocess.CompletedProcess[str], code: int, text: str) -> None:
    """Require an exit code and a phrase from the real command output."""
    combined = result.stdout + result.stderr
    if result.returncode != code or text not in combined:
        raise SystemExit(
            f"expected exit {code} and {text!r}\n"
            f"got exit {result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
        )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nizam-start-path-") as name:
        root = Path(name)
        missing = run(root, "begin", "bugfix", "--id", "demo")
        expect(missing, 1, "required record does not exist")

        write(root, ".agent/evidence/demo-cause.json", cause("demo"))
        write(root, ".agent/evidence/demo-scope.json", scope("demo", ["README.md"]))
        began = run(root, "begin", "bugfix", "--id", "demo")
        expect(began, 0, "implementation may begin")
        undone = run(root, "done", "bugfix", "--id", "demo")
        expect(undone, 1, "required record does not exist")

        evidence = ".agent/evidence/demo-qa-out.txt"
        write(root, evidence, {"command": "true"})
        (root / evidence).write_text("exit 0\n", encoding="utf-8")
        write(root, ".agent/qa/demo.json", qa("demo", evidence))
        finished = run(root, "done", "bugfix", "--id", "demo")
        expect(finished, 0, "recorded verification result exists")

        write(root, ".agent/evidence/bound-cause.json", cause("bound"))
        write(
            root,
            ".agent/evidence/bound-scope.json",
            scope("bound", ["OTHER.md"], "c1"),
        )
        write(root, ".agent/contracts/c1.json", contract("approved", ["README.md"]))
        outside = run(root, "begin", "bugfix", "--id", "bound")
        expect(outside, 1, "not inside the named contract")

        write(
            root,
            ".agent/evidence/bound-scope.json",
            scope("bound", ["README.md"], "c1"),
        )
        write(root, ".agent/contracts/c1.json", contract("proposed", ["README.md"]))
        proposed = run(root, "begin", "bugfix", "--id", "bound")
        expect(proposed, 1, "not already approved")
        write(root, ".agent/contracts/c1.json", contract("approved", ["README.md"]))
        bound = run(root, "begin", "bugfix", "--id", "bound")
        expect(bound, 0, "implementation may begin")

        write(
            root,
            ".agent/evidence/tiny-intent.json",
            {
                "id": "tiny",
                "path": "small-change",
                "summary": "Fix one spelled word.",
                "needs_new_contract": True,
            },
        )
        refused = run(root, "begin", "small-change", "--id", "tiny")
        expect(refused, 1, "needs_new_contract")
        write(
            root,
            ".agent/evidence/tiny-intent.json",
            {
                "id": "tiny",
                "path": "small-change",
                "summary": "Fix one spelled word.",
                "needs_new_contract": False,
            },
        )
        small = run(root, "begin", "small-change", "--id", "tiny")
        expect(small, 0, "implementation may begin")
        small_evidence = ".agent/evidence/tiny-out.txt"
        (root / small_evidence).write_text("exit 0\n", encoding="utf-8")
        write(root, ".agent/qa/tiny.json", qa("tiny", small_evidence))
        small_done = run(root, "done", "small-change", "--id", "tiny")
        expect(small_done, 0, "recorded verification result exists")

        escaped = run(root, "begin", "bugfix", "--id", "../demo")
        expect(escaped, 2, "safe path token")

    print("start-path: bugfix and small-change gates match the shipped command")
    return 0


if __name__ == "__main__":
    sys.exit(main())
