#!/usr/bin/env python3
"""Independent contract-plan checks only; no product acceptance or edits."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name("validator-mode-a-02-probes")
OUT.mkdir(exist_ok=False)
TASK = "NIZAM-R02-COMPLETION"
CONTRACT = ROOT / ".agent/contracts" / (TASK + ".json")
raw = CONTRACT.read_bytes()
contract = json.loads(raw)
assert hashlib.sha256(raw).hexdigest() == "504f0939544b936d4f8a67661dbd811a1af42526860584f3a97a9181eb9b9066"
tokens = shlex.split(next(v["command"] for v in contract["verification"] if v["id"] == "SCOPE"))
assert len(tokens) == 4 and tokens[:3] == ["PYTHONDONTWRITEBYTECODE=1", "python3", "-c"]
predicate = tokens[3]
assert predicate.count(contract["source_revision"]) == 1
env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
env.update(PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_GLOBAL=os.devnull,
           GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_SYSTEM=os.devnull,
           GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
products = ["tools/start_path.py", "tools/test_start_path.py"]
sha = lambda data: hashlib.sha256(data).hexdigest()
before = {p: sha((ROOT / p).read_bytes()) for p in products}


def save(path, data):
    with path.open("xb") as handle:
        handle.write(data)


def record(path, obj):
    save(path, (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode())


cases = [
    ("clean", 0, []),
    ("masked-commit", 1, ["outside.txt"]),
    ("masked-index", 1, ["outside.txt"]),
    ("rename-to-metadata", 1, ["outside.txt"]),
    ("official-reservation", 0, []),
    ("versioned-review", 0, []),
    ("foreign-reservation", 1, [".agent/evidence/NIZAM-R02-COMPLETIONX-probe-attempt1.reservation.json"]),
    ("shared-state", 1, [".agent/run_state.json"]),
    ("actual-copy-observation", 0, []),
]
results = []
for name, expected_exit, expected_paths in cases:
    dest = OUT / name
    dest.mkdir()
    with tempfile.TemporaryDirectory(prefix="validator-r02-contract-02-") as temp:
        fixture = Path(temp)
        commands = []

        def run(argv, label):
            started = datetime.datetime.now(datetime.timezone.utc).isoformat()
            proc = subprocess.run(argv, cwd=fixture, env=env, capture_output=True)
            stdout_name = label + ".stdout.txt"
            stderr_name = label + ".stderr.txt"
            save(dest / stdout_name, proc.stdout)
            save(dest / stderr_name, proc.stderr)
            commands.append({"label": label, "argv": argv, "cwd": str(fixture),
                             "started_at": started, "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                             "exit_code": proc.returncode, "stdout_path": stdout_name,
                             "stderr_path": stderr_name, "stdout_sha256": sha(proc.stdout),
                             "stderr_sha256": sha(proc.stderr)})
            return proc

        def git(*args):
            p = run(["git", "-c", "user.name=Independent validator fixture",
                     "-c", "user.email=validator@example.invalid", "-c", "commit.gpgsign=false",
                     "-c", "core.hooksPath=" + os.devnull, *args], "git-%02d" % len(commands))
            assert p.returncode == 0, (args, p.stderr)
            return p.stdout

        def put(path, content):
            target = fixture / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

        git("init", "-q")
        put("outside.txt", b"outside original\n")
        put("tools/start_path.py", b"declared original\n")
        git("add", ".")
        git("commit", "-qm", "validator baseline")
        base = git("rev-parse", "HEAD").decode().strip()
        if name == "masked-commit":
            put("outside.txt", b"committed undeclared change\n")
            git("add", "outside.txt")
            git("commit", "-qm", "undeclared change")
            git("restore", "--source=" + base, "--staged", "--worktree", "--", "outside.txt")
            assert git("diff", "--name-only", base, "HEAD", "--") == b"outside.txt\n"
            assert git("diff", "--name-only", base, "--") == b""
            assert git("diff", "--cached", "--name-only", base, "--") == b""
        elif name == "masked-index":
            put("outside.txt", b"indexed undeclared change\n")
            git("add", "outside.txt")
            put("outside.txt", b"outside original\n")
            assert git("diff", "--name-only", base, "--") == b""
            assert git("diff", "--cached", "--name-only", base, "--") == b"outside.txt\n"
        elif name == "rename-to-metadata":
            path = ".agent/evidence/" + TASK + "/renamed.txt"
            (fixture / path).parent.mkdir(parents=True)
            git("mv", "outside.txt", path)
            observed = git("diff", "--cached", "--name-status", "-M", base, "--")
            assert b"R100\toutside.txt\t" in observed
        elif name == "official-reservation":
            proc = run([sys.executable, str(ROOT / ".nizam/tools/start_path.py"), "capture",
                        "--id", TASK, "--step", "validator-probe", "--attempt", "1",
                        "--output-dir", ".agent/evidence/" + TASK + "/capture-fixture",
                        "--root", str(fixture), "--", sys.executable, "-c", "print('capture control')"], "official-capture")
            assert proc.returncode == 0
            marker = fixture / (".agent/evidence/" + TASK + "-validator-probe-attempt1.reservation.json")
            assert marker.is_file()
            save(dest / "observed.reservation.json", marker.read_bytes())
        elif name == "versioned-review":
            put(".agent/qa/" + TASK + "-contract-review-02.json", b"{}\n")
        elif name in ("foreign-reservation", "shared-state"):
            put(expected_paths[0], b"{}\n")
        elif name == "actual-copy-observation":
            git("config", "status.renames", "copies")
            put("copied.txt", b"outside original\n")
            put("outside.txt", b"modified original\n")
            git("add", "outside.txt", "copied.txt")
            observed = git("status", "--porcelain", "-z")
            fields = observed.split(b"\0")
            copy_pairs = []
            i = 0
            while i < len(fields) and fields[i]:
                field = fields[i]
                i += 1
                if b"C" in field[:2] or b"R" in field[:2]:
                    original = fields[i]
                    i += 1
                    if b"C" in field[:2]:
                        copy_pairs.append([original.decode(), field[3:].decode()])
            assert copy_pairs == [["outside.txt", "copied.txt"]]
            record(dest / "execution.json", {"case": name, "commands": commands,
                   "passed": True, "copy_pairs": copy_pairs,
                   "purpose": "Actual supported Git C-record precondition only; no product callable executed."})
            results.append({"case": name, "passed": True, "record": name + "/execution.json"})
            continue
        source = predicate.replace(contract["source_revision"], base, 1)
        proc = run([sys.executable, "-c", source], "scope")
        observed = json.loads(proc.stdout)
        passed = proc.returncode == expected_exit and observed["unexpected"] == expected_paths
        record(dest / "execution.json", {"case": name, "commands": commands, "fixture_base": base,
               "passed": passed, "expected_exit": expected_exit, "observed_exit": proc.returncode,
               "expected_unexpected": expected_paths, "observed": observed,
               "substitution": "Only pinned source_revision literal replaced with disposable fixture base."})
        results.append({"case": name, "passed": passed, "record": name + "/execution.json"})
        assert passed, name

after = {p: sha((ROOT / p).read_bytes()) for p in products}
assert before == after and raw == CONTRACT.read_bytes()
summary = {"purpose": "Independent revision-2 contract soundness review only; no implementation or qualification.",
           "contract_sha256": sha(raw), "cases": results, "passed": all(v["passed"] for v in results),
           "source_before_sha256": before, "source_after_sha256": after,
           "contract_unchanged": True}
record(OUT / "summary.json", summary)
print(json.dumps(summary, sort_keys=True))
