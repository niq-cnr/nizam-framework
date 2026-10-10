#!/usr/bin/env python3
"""Private-clone probes for contract 107. Does not modify the source worktree."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

SOURCE = Path("/home/cnross/workspace02/nizam-framework")
EVIDENCE = SOURCE / ".agent/evidence/107-qa-adversarial-contract-review"
CLONE = Path("/tmp/nizam-107-qa")
A = "7972e4f2d46abf6b8e0f02e8c11e94ac0f7aa0f4"
FDC = "fdc076ff6b4665d7b40a5a74a9dae5562dd568bf"
HELPERS = EVIDENCE / "helpers"


def run(argv, cwd, env=None):
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def capture(name, invocation, argv, cwd, env=None, shell=False):
    proc = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        shell=shell,
        executable="/bin/bash" if shell else None,
    )
    body = proc.stdout + proc.stderr
    if body and not body.endswith("\n"):
        body += "\n"
    text = invocation + "\n" + body + f"EXIT:{proc.returncode}\n"
    (EVIDENCE / name).write_text(text, encoding="utf-8")
    print(f"CAPTURE {name} EXIT:{proc.returncode}", flush=True)
    return proc.returncode, body


def contract_commands(contract):
    out = {}
    for item in contract["verification"]:
        label = item["acceptance_test"][:24]
        out[item.get("acceptance_test_index") or item["acceptance_test"][:12]] = item["command"]
    return out


def write_script(path: Path, command: str) -> None:
    path.write_text(command if command.endswith("\n") else command + "\n", encoding="utf-8")
    path.chmod(0o755)


def apply_pins(root: Path, pins: dict) -> None:
    vpath = root / "tools/validate.sh"
    v = vpath.read_text(encoding="utf-8")
    for key in ("c1_help_old", "c2_help_old", "call_old"):
        count = v.count(pins[key])
        if count != 1:
            raise SystemExit(f"apply: {key} count {count}")
    v = v.replace(pins["c1_help_old"], pins["c1_help_new"], 1)
    v = v.replace(pins["c2_help_old"], pins["c2_help_new"], 1)
    v = v.replace(pins["call_old"], pins["call_new"], 1)
    vpath.write_text(v, encoding="utf-8")

    npath = root / pins["nip2"]
    n = npath.read_text(encoding="utf-8")
    for needle in ("version: 0.2.0\n", "status: accepted\n", "change_log:\n"):
        count = n.count(needle)
        if count != 1:
            raise SystemExit(f"apply: NIP needle {needle!r} count {count}")
    n = n.replace("version: 0.2.0\n", "version: 0.2.1\n", 1)
    n = n.replace("status: accepted\n", "status: active\n", 1)
    n = n.replace("change_log:\n", "change_log:\n" + pins["nip2_changelog_entry"], 1)
    npath.write_text(n, encoding="utf-8")
    active = n.count("status: active")
    print(f"NIP-0002 status: active count {active}", flush=True)
    if active != 1:
        raise SystemExit("apply: status: active count is not 1")

    rpath = root / "tools/README.md"
    r = rpath.read_text(encoding="utf-8")
    if r.count("version: 0.15.0\n") != 1 or r.count(pins["c1_row_old"]) != 1 or r.count("change_log:\n") != 1:
        raise SystemExit(
            f"apply: README anchors {r.count('version: 0.15.0' + chr(10))} "
            f"{r.count(pins['c1_row_old'])} {r.count('change_log:' + chr(10))}"
        )
    entry = (
        "  - version: \"0.16.0\"\n"
        "    date: \"2026-10-10\"\n"
        f"    summary: \"{pins['readme_summary']}\"\n"
    )
    r = r.replace("version: 0.15.0\n", "version: 0.16.0\n", 1)
    r = r.replace("change_log:\n", "change_log:\n" + entry, 1)
    r = r.replace(pins["c1_row_old"], pins["c1_row_new"], 1)
    rpath.write_text(r, encoding="utf-8")
    print("pins applied", flush=True)


def main() -> int:
    os.chdir(SOURCE)
    contract = json.loads((SOURCE / ".agent/contracts/107.json").read_text(encoding="utf-8"))
    pins = contract["design_notes"]["pinned_interface"]
    commands = {item.get("evidence_file", str(i)): item["command"] for i, item in enumerate(contract["verification"])}

    # Regex sanity against the already captured --target shape, with the NIP-0001 name.
    sample = (
        "  docs/nips/NIP-0001-ecosystem-engineering-cycle.md: "
        "frontmatter schema violation: 'accepted' is not one of ['draft', 'active', 'deprecated']"
    )
    status = (
        "  docs/nips/NIP-0001-ecosystem-engineering-cycle.md: "
        "status 'accepted' is not one of draft/active/deprecated"
    )
    source = (
        "  docs/nips/NIP-0001-ecosystem-engineering-cycle.md: "
        "authoritative_source 'docs/nips/NIP-0001-moved.md' != own path "
        "'docs/nips/NIP-0001-ecosystem-engineering-cycle.md' and != 'NA'"
    )
    for label, pat, line in (
        ("c1_schema_detail", pins["c1_schema_detail"], sample),
        ("c2_status_detail", pins["c2_status_detail"], status),
        ("c2_source_detail", pins["c2_source_detail"], source),
    ):
        matched = re.search(pat, line, re.M) is not None
        print(f"REGEX {label} {'MATCH' if matched else 'MISS'}", flush=True)
        if not matched:
            return 2

    s01 = commands[".agent/evidence/107/s01-contract-valid.txt"]
    write_script(HELPERS / "s01.sh", s01)
    capture(
        "02-s01.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/s01.sh",
        ["bash", str(HELPERS / "s01.sh")],
        SOURCE,
    )
    capture(
        "02-git-diff-fdc076f-head.txt",
        f"git diff --name-only {FDC} HEAD",
        ["git", "diff", "--name-only", FDC, "HEAD"],
        SOURCE,
    )
    capture(
        "02-git-diff-fdc076f-a.txt",
        f"git diff --name-only {FDC} {A}",
        ["git", "diff", "--name-only", FDC, A],
        SOURCE,
    )

    if CLONE.exists():
        shutil.rmtree(CLONE)
    print("cloning", flush=True)
    cloned = run(["git", "clone", "--local", str(SOURCE), str(CLONE)], SOURCE)
    print(cloned.stdout + cloned.stderr, flush=True)
    if cloned.returncode != 0:
        return 2
    run(["git", "config", "user.email", "qa-probe@example.invalid"], CLONE)
    run(["git", "config", "user.name", "qa-probe"], CLONE)
    shutil.copy(SOURCE / ".agent/contracts/107.json", CLONE / ".agent/contracts/107.json")

    at2 = commands[".agent/evidence/107/at2-c1-bad-status.txt"]
    at3 = commands[".agent/evidence/107/at3-c2-authoritative-source.txt"]
    write_script(HELPERS / "at2.sh", at2)
    write_script(HELPERS / "at3.sh", at3)
    capture(
        "03-base-at2.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/at2.sh",
        ["bash", str(HELPERS / "at2.sh")],
        CLONE,
    )
    capture(
        "04-base-at3.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/at3.sh",
        ["bash", str(HELPERS / "at3.sh")],
        CLONE,
    )

    apply_pins(CLONE, pins)

    for key, script, evidence in (
        (".agent/evidence/107/s04-pinned-structure.txt", "s04.sh", "05-positive-s04.txt"),
        (".agent/evidence/107/at1-nip-0002-status.txt", "at1.sh", "05-positive-at1.txt"),
        (".agent/evidence/107/at4-help-and-readme.txt", "at4.sh", "05-positive-at4.txt"),
    ):
        write_script(HELPERS / script, commands[key])
        capture(
            evidence,
            f"bash .agent/evidence/107-qa-adversarial-contract-review/helpers/{script}",
            ["bash", str(HELPERS / script)],
            CLONE,
        )

    capture(
        "06-positive-validate.txt",
        "bash tools/validate.sh",
        ["bash", "tools/validate.sh"],
        CLONE,
    )
    capture(
        "06-positive-validate-payload.txt",
        "bash tools/validate.sh --payload",
        ["bash", "tools/validate.sh", "--payload"],
        CLONE,
    )
    write_script(HELPERS / "at5.sh", commands[".agent/evidence/107/at5-validator-gate.txt"])
    capture(
        "07-positive-at5.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/at5.sh",
        ["bash", str(HELPERS / "at5.sh")],
        CLONE,
    )
    capture(
        "08-positive-at2.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/at2.sh",
        ["bash", str(HELPERS / "at2.sh")],
        CLONE,
    )
    capture(
        "09-positive-at3.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/at3.sh",
        ["bash", str(HELPERS / "at3.sh")],
        CLONE,
    )
    write_script(HELPERS / "s05.sh", commands[".agent/evidence/107/s05-discriminating.txt"])
    capture(
        "10-positive-s05.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/s05.sh",
        ["bash", str(HELPERS / "s05.sh")],
        CLONE,
    )

    # C8 negative: drop only the new README change_log entry. CHANGELOG.md stays at A.
    c8_code = textwrap.dedent(
        f"""
        p = root / "tools/README.md"
        t = p.read_text()
        entry = (
            "  - version: \\"0.16.0\\"\\n"
            "    date: \\"2026-10-10\\"\\n"
            "    summary: \\"{pins['readme_summary']}\\"\\n"
        )
        assert t.count(entry) == 1, t.count(entry)
        assert "version: 0.16.0\\n" in t
        p.write_text(t.replace(entry, "", 1))
        """
    ).strip()
    write_script(
        HELPERS / "mutant_c8.py",
        "import subprocess, sys\n"
        f"code = {c8_code!r}\n"
        "argv = [sys.executable, '.agent/evidence/phase-014-activation/gates/scratch_run.py', "
        "'--py-mutate', code, '--expect-rc', '1', "
        "'--expect', r'^\\[C8\\] FAIL version-bump-vs-changelog$', "
        "'--expect', 'tools/README.md: version bumped 0.15.0 -> 0.16.0', "
        "'--forbid', r'^\\[C1\\] FAIL', '--', 'bash', 'tools/validate.sh']\n"
        "sys.exit(subprocess.run(argv).returncode)\n",
    )
    capture(
        "11-mutant-c8-no-changelog-entry.txt",
        "python3 .agent/evidence/107-qa-adversarial-contract-review/helpers/mutant_c8.py",
        [sys.executable, str(HELPERS / "mutant_c8.py")],
        CLONE,
    )

    shipped_code = textwrap.dedent(
        """
        p = root / "tools/validate.sh"
        t = p.read_text()
        old = '  files+=("CONTEXT.md")\\n'
        new = old + '  files+=("docs/nips/NIP-0001-ecosystem-engineering-cycle.md")\\n'
        assert t.count(old) == 1, t.count(old)
        p.write_text(t.replace(old, new, 1))
        nip = root / "docs/nips/NIP-0001-ecosystem-engineering-cycle.md"
        suffix = "\\n\\n```\\nuntagged probe\\n```\\n\\nSee docs/nips/DOES-NOT-EXIST.md for the probe.\\n"
        assert suffix not in nip.read_text()
        nip.write_text(nip.read_text() + suffix)
        """
    ).strip()
    # The py-mutate source is executed as Python, so the escapes above are for the
    # shell helper. Build the mutate source directly instead.
    shipped_code = (
        "p = root / \"tools/validate.sh\"\n"
        "t = p.read_text()\n"
        "old = \"  files+=(\\\"CONTEXT.md\\\")\\n\"\n"
        "new = old + \"  files+=(\\\"docs/nips/NIP-0001-ecosystem-engineering-cycle.md\\\")\\n\"\n"
        "assert t.count(old) == 1, t.count(old)\n"
        "p.write_text(t.replace(old, new, 1))\n"
        "nip = root / \"docs/nips/NIP-0001-ecosystem-engineering-cycle.md\"\n"
        "suffix = \"\\n\\n```\\nuntagged probe\\n```\\n\\nSee docs/nips/DOES-NOT-EXIST.md for the probe.\\n\"\n"
        "assert suffix not in nip.read_text()\n"
        "nip.write_text(nip.read_text() + suffix)\n"
    )
    write_script(
        HELPERS / "mutant_shipped.py",
        "import json, subprocess, sys\n"
        "from pathlib import Path\n"
        f"code = {shipped_code!r}\n"
        "argv = [sys.executable, '.agent/evidence/phase-014-activation/gates/scratch_run.py', "
        "'--py-mutate', code, '--expect-rc', '1', "
        "'--expect', r'^\\[C3\\] FAIL', '--expect', r'^\\[C9\\] FAIL', "
        "'--expect', 'DOES-NOT-EXIST', '--', 'bash', 'tools/validate.sh']\n"
        "proc = subprocess.run(argv)\n"
        "sys.exit(proc.returncode)\n",
    )
    capture(
        "12-mutant-shipped-set-poison.txt",
        "python3 .agent/evidence/107-qa-adversarial-contract-review/helpers/mutant_shipped.py",
        [sys.executable, str(HELPERS / "mutant_shipped.py")],
        CLONE,
    )

    banner_code = (
        "p = root / \"tools/validate.sh\"\n"
        "t = p.read_text()\n"
        "old = \"  echo \\\"[C1] FAIL frontmatter-schema\\\"\\n\"\n"
        "new = \"  echo \\\"[C1] FAIL other-banner\\\"\\n\"\n"
        "assert t.count(old) == 1, t.count(old)\n"
        "p.write_text(t.replace(old, new, 1))\n"
    )
    write_script(
        HELPERS / "mutant_banner.py",
        "import subprocess, sys\n"
        f"code = {banner_code!r}\n"
        "base = [sys.executable, '.agent/evidence/phase-014-activation/gates/scratch_run.py', "
        "'--replace', 'docs/nips/NIP-0001-ecosystem-engineering-cycle.md', "
        "'status: active', 'status: accepted', '--py-mutate', code]\n"
        "loose = base + ['--expect-rc', '1', '--expect', r'^\\[C1\\] FAIL', "
        "'--expect', r'NIP-0001-ecosystem-engineering-cycle\\.md', '--', 'bash', 'tools/validate.sh']\n"
        "exact = base + ['--expect-rc', '1', '--expect', r'^\\[C1\\] FAIL frontmatter-schema$', "
        "'--', 'bash', 'tools/validate.sh']\n"
        "a = subprocess.run(loose)\n"
        "print('LOOSE_AT2_EXIT', a.returncode)\n"
        "b = subprocess.run(exact)\n"
        "print('EXACT_BANNER_EXIT', b.returncode)\n"
        "sys.exit(0 if a.returncode == 0 and b.returncode == 1 else 1)\n",
    )
    capture(
        "13-mutant-banner-at2-vs-exact.txt",
        "python3 .agent/evidence/107-qa-adversarial-contract-review/helpers/mutant_banner.py",
        [sys.executable, str(HELPERS / "mutant_banner.py")],
        CLONE,
    )

    predicate(CLONE, contract)
    return 0


def predicate(clone: Path, contract: dict) -> None:
    """Real-git S02/S03. Commits stay in the clone."""
    backup = Path("/tmp/nizam-107-impl")
    if backup.exists():
        shutil.rmtree(backup)
    backup.mkdir()
    for rel in (
        "tools/validate.sh",
        "tools/README.md",
        "docs/nips/NIP-0002-zero-to-n-project-spectrum.md",
    ):
        target = backup / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(clone / rel, target)
    run(["git", "checkout", "--", "tools/validate.sh", "tools/README.md",
         "docs/nips/NIP-0002-zero-to-n-project-spectrum.md"], clone)

    approved = json.loads((clone / ".agent/contracts/107.json").read_text(encoding="utf-8"))
    approved["status"] = "approved"
    (clone / ".agent/contracts/107.json").write_text(
        json.dumps(approved, indent=2) + "\n", encoding="utf-8"
    )
    state_path = clone / ".agent/run_state.json"
    state = state_path.read_text(encoding="utf-8")
    old_stamp = "2026-10-10T06:40:52Z"
    new_stamp = "2026-10-10T07:00:00Z"
    if state.count(old_stamp) != 1:
        raise SystemExit(f"run_state stamp count {state.count(old_stamp)}")
    state_path.write_text(state.replace(old_stamp, new_stamp, 1), encoding="utf-8")
    run(["git", "add", ".agent/contracts/107.json", ".agent/run_state.json"], clone)
    committed = run(["git", "commit", "-m", "qa-probe B: approved contract and run_state"], clone)
    print(committed.stdout + committed.stderr, flush=True)
    if committed.returncode != 0:
        raise SystemExit("commit B failed")
    b_sha = run(["git", "rev-parse", "HEAD"], clone).stdout.strip()
    print("B", b_sha, flush=True)

    s03 = next(item["command"] for item in contract["verification"] if item["evidence_file"].endswith("s03-scope-boundary.txt"))
    s02 = next(item["command"] for item in contract["verification"] if item["evidence_file"].endswith("s02-attempt-root-delta.txt"))
    write_script(HELPERS / "s03.sh", s03)
    write_script(HELPERS / "s02.sh", s02)

    # Outcome: run_state differs from A, deliverables absent. Must not be a run_state hard-fail.
    capture(
        "14a-s03-run-state-without-deliverables.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/s03.sh",
        ["bash", str(HELPERS / "s03.sh")],
        clone,
    )

    for rel in (
        "tools/validate.sh",
        "tools/README.md",
        "docs/nips/NIP-0002-zero-to-n-project-spectrum.md",
    ):
        shutil.copy(backup / rel, clone / rel)
    attempt = clone / ".agent/evidence/107/attempt-base.txt"
    attempt.parent.mkdir(parents=True, exist_ok=True)
    attempt.write_text(f"git rev-parse HEAD\n{b_sha}\nEXIT:0\n", encoding="utf-8")

    capture(
        "14b-s03-with-run-state-and-deliverables.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/s03.sh",
        ["bash", str(HELPERS / "s03.sh")],
        clone,
    )
    capture(
        "14c-git-diff-name-only-a.txt",
        f"git diff --name-only {A}",
        ["git", "diff", "--name-only", A],
        clone,
    )
    capture(
        "14d-s02-in-scope-delta.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/s02.sh",
        ["bash", str(HELPERS / "s02.sh")],
        clone,
    )

    # Generator edits run_state after B.
    state_path.write_text(state_path.read_text(encoding="utf-8").replace(new_stamp, "2026-10-10T08:00:00Z", 1), encoding="utf-8")
    capture(
        "14e-s02-generator-run-state.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/s02.sh",
        ["bash", str(HELPERS / "s02.sh")],
        clone,
    )
    run(["git", "checkout", "--", ".agent/run_state.json"], clone)

    phase = clone / "docs/planning/phase_014.yaml"
    phase.write_text(phase.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    capture(
        "14f-s03-phase-yaml.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/s03.sh",
        ["bash", str(HELPERS / "s03.sh")],
        clone,
    )
    run(["git", "checkout", "--", "docs/planning/phase_014.yaml"], clone)

    debt = clone / "docs/planning/DEBT.md"
    debt.write_text(debt.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    capture(
        "14g-s03-debt.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/s03.sh",
        ["bash", str(HELPERS / "s03.sh")],
        clone,
    )
    run(["git", "checkout", "--", "docs/planning/DEBT.md"], clone)

    feature = clone / ".agent/feature_list_014.json"
    feature.write_text(feature.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    capture(
        "14h-s03-feature-list.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/s03.sh",
        ["bash", str(HELPERS / "s03.sh")],
        clone,
    )
    run(["git", "checkout", "--", ".agent/feature_list_014.json"], clone)

    # Confirm S03 is clean again after the owned-file restorations.
    capture(
        "14i-s03-restored.txt",
        "bash .agent/evidence/107-qa-adversarial-contract-review/helpers/s03.sh",
        ["bash", str(HELPERS / "s03.sh")],
        clone,
    )


if __name__ == "__main__":
    sys.exit(main())
