"""Private-scratch helpers for the feature-106 contract-testability review.

Never writes a contracted path in the real repository. Copies and mutations
stay under a temporary directory.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
A = "2a22ecdfda6ff3895792a1d974489d091e11e696"
CONTRACT_PATH = REPO / ".agent" / "contracts" / "106.json"


def contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def pins() -> dict:
    return contract()["design_notes"]["pinned_interface"]


def verification(suffix: str) -> dict:
    matches = [
        item
        for item in contract()["verification"]
        if item["evidence_file"].endswith(suffix)
    ]
    if len(matches) != 1:
        raise SystemExit(f"expected one verification entry for {suffix}, found {len(matches)}")
    return matches[0]


def s05_body() -> str:
    command = verification("s05-discriminating.txt")["command"]
    prefix = "python3 - <<'PY'\n"
    if not command.startswith(prefix):
        raise SystemExit("S05 command does not start with the expected heredoc")
    body = command[len(prefix) :]
    if body.endswith("\nPY\n"):
        body = body[: -len("\nPY\n")]
    elif body.endswith("\nPY"):
        body = body[: -len("\nPY")]
    else:
        raise SystemExit("S05 command does not end with the expected heredoc closer")
    return body


def load_s05_definitions(tree: Path) -> dict:
    """Exec the contract's S05 script up to, but not including, the case runner."""
    body = s05_body()
    marker = "\nfor case in CASES:\n"
    if marker not in body:
        raise SystemExit("S05 runner marker missing")
    preamble = body.split(marker, 1)[0] + "\n"
    previous = Path.cwd()
    namespace = {"__name__": "s05_definitions"}
    os.chdir(tree)
    try:
        exec(compile(preamble, "<s05-preamble>", "exec"), namespace)  # noqa: S102
    finally:
        os.chdir(previous)
    return namespace


def copy_tree(dest: Path) -> None:
    """Copy the repository, omitting the untracked .nizam directory."""

    def ignore(directory: str, names: list[str]) -> set[str]:
        if Path(directory).resolve() == REPO:
            return {".nizam"}
        return set()

    shutil.copytree(REPO, dest, symlinks=True, ignore=ignore)


def git_show(tree: Path, spec: str) -> str:
    proc = subprocess.run(
        ["git", "show", spec],
        cwd=tree,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr)
    return proc.stdout


def apply_faithful(tree: Path, *, subset: bool = True) -> None:
    """Apply the pinned edits. subset=False omits only the C13 subset block."""
    pin = pins()
    validate = tree / "tools" / "validate.sh"
    text = validate.read_text(encoding="utf-8")
    anchor = pin["help_anchor"]
    if text.count(anchor) != 1:
        raise SystemExit(f"help anchor count {text.count(anchor)}")
    text = text.replace(anchor, anchor + pin["help_addition"], 1)
    if subset:
        problem = pin["problem_anchor"]
        if text.count(problem) != 1:
            raise SystemExit(f"problem anchor count {text.count(problem)}")
        text = text.replace(problem, pin["subset_block"] + problem, 1)
    validate.write_text(text, encoding="utf-8")

    self_test = tree / "tools" / "fixtures_self_test.sh"
    base = self_test.read_text(encoding="utf-8")
    start = base.index("test_c13() {\n")
    call = base.index("\ntest_c13\n", start)
    self_test.write_text(base[:start] + pin["test_c13"] + base[call + 1 :], encoding="utf-8")

    index = tree / "NIZAM.json"
    raw = index.read_text(encoding="utf-8")
    needle = pin["nizam_needle"]
    if raw.count(needle) != 1:
        raise SystemExit(f"nizam needle count {raw.count(needle)}")
    index.write_text(raw.replace(needle, pin["nizam_insert"] + needle, 1), encoding="utf-8")

    fixture = tree / pin["fixture_path"]
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text(pin["fixture_text"], encoding="utf-8")

    readme = tree / "tools" / "README.md"
    readme_text = readme.read_text(encoding="utf-8")
    if readme_text.count(pin["skill_row_old"]) != 1 or readme_text.count(pin["c13_row_old"]) != 1:
        raise SystemExit("README pin rows are not unique")
    readme_text = readme_text.replace(pin["skill_row_old"], pin["skill_row_new"], 1)
    readme_text = readme_text.replace(pin["c13_row_old"], pin["c13_row_new"], 1)
    readme_text = readme_text.replace("version: 0.14.0\n", "version: 0.15.0\n", 1)
    summary = pin["readme_summary"].replace("\\", "\\\\").replace('"', '\\"')
    entry = (
        'change_log:\n'
        '  - version: "0.15.0"\n'
        '    date: "2026-10-10"\n'
        f'    summary: "{summary}"\n'
    )
    if readme_text.count("change_log:\n") != 1:
        raise SystemExit("change_log anchor missing")
    readme_text = readme_text.replace("change_log:\n", entry, 1)
    readme.write_text(readme_text, encoding="utf-8")

    changelog = tree / "CHANGELOG.md"
    changelog_text = changelog.read_text(encoding="utf-8")
    bullet = pin["changelog_bullet"]
    marker = "## [1.4.0]"
    position = changelog_text.index(marker)
    changelog.write_text(
        changelog_text[:position] + bullet + "\n\n" + changelog_text[position:],
        encoding="utf-8",
    )


def c13_python(validate_text: str) -> str:
    start = validate_text.index("check_c13_skill_index() {")
    begin = validate_text.index("<<'PY'\n", start) + len("<<'PY'\n")
    end = validate_text.index("\nPY\n", begin)
    return validate_text[begin:end]


def run(command: list[str] | str, cwd: Path, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    if isinstance(command, str):
        return subprocess.run(
            ["bash", "-c", command],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def redact(text: str, scratch: Path | None = None) -> str:
    if scratch is not None:
        text = text.replace(str(scratch), "$SCRATCH")
    text = text.replace(str(REPO), "$REPO")
    return text


def format_result(name: str, proc: subprocess.CompletedProcess[str], scratch: Path | None = None) -> str:
    body = redact(proc.stdout + proc.stderr, scratch)
    return f"### {name} rc={proc.returncode}\n{body}"


def approve_and_commit_base(tree: Path) -> str:
    """Commit the contract as approved. This is B, inside the scratch only."""
    path = tree / ".agent" / "contracts" / "106.json"
    text = path.read_text(encoding="utf-8")
    field = '"status": "proposed"'
    if text.count(field) != 1:
        raise SystemExit(f"status field count {text.count(field)}")
    path.write_text(text.replace(field, '"status": "approved"', 1), encoding="utf-8")
    subprocess.run(["git", "config", "user.email", "evaluator@example.invalid"], cwd=tree, check=True)
    subprocess.run(["git", "config", "user.name", "Evaluator Scratch"], cwd=tree, check=True)
    subprocess.run(["git", "add", "--", ".agent/contracts/106.json"], cwd=tree, check=True)
    subprocess.run(
        ["git", "commit", "-m", "contract 106 approved (scratch only)"],
        cwd=tree,
        check=True,
        capture_output=True,
        text=True,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tree,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    evidence = tree / ".agent" / "evidence" / "106"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "attempt-base.txt").write_text(f"git rev-parse HEAD\n{sha}\nEXIT:0\n", encoding="utf-8")
    return sha
