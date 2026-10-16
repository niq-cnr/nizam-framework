#!/usr/bin/env python3
"""Deterministic 129-B1 stale-attempt apply check.

The helper capture read observes the on-disk run_state buffer. The supervisor
pre-apply read is forced to observe a different attempts integer. A correct
binding refuses before execution. Applying the cached attempt_ok is a failure.
This process does not modify product, runner, contract, or run_state files.
"""
import hashlib
import json
import os
import shutil
import signal
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path("/home/cnross/.grok/worktrees/workspace02-nizam-framework/subagent-01a14426-b6f8-7852-96e7-8132cc003862")
EXPECTED = "e47a645f947ccb2cce0f40eafe93a740e421487f"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TMPDIR"] = "/tmp"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import runtime_session as rs  # noqa: E402

ORCH = {"principal_kind": "agent", "role": "Orchestrator", "agent_id": "root"}
OWNER = {"principal_kind": "agent", "role": "Generator", "agent_id": "owner"}
STEP = "129-implementation"
ORIGINAL_READ = Path.read_bytes
STATE = {
    "armed": None,
    "run_state": None,
    "controller": None,
    "log": None,
    "disk": None,
    "mutated": None,
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def append_log(row):
    path = STATE["log"]
    if path is None:
        return
    line = (json.dumps(row, sort_keys=True) + "\n").encode()
    fd = os.open(path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


def patched_read_bytes(self):
    data = ORIGINAL_READ(self)
    run_state = STATE["run_state"]
    flag = STATE["armed"]
    if run_state is None or Path(self) != Path(run_state) or flag is None or not os.path.exists(flag):
        return data
    supervisor_pid = None
    try:
        meta = json.loads(ORIGINAL_READ(Path(STATE["controller"])))
        supervisor_pid = meta.get("supervisor_pid")
    except (OSError, ValueError, TypeError):
        supervisor_pid = None
    is_supervisor = supervisor_pid is not None and os.getpid() == supervisor_pid
    served = STATE["mutated"] if is_supervisor else data
    try:
        parsed = json.loads(served)
        attempts = parsed["circuit_breaker"][STEP]["attempts"]
    except (ValueError, KeyError, TypeError):
        attempts = None
    append_log({
        "pid": os.getpid(),
        "is_supervisor": is_supervisor,
        "sha256": sha256(served),
        "attempts": attempts,
        "bytes": len(served),
    })
    return served


Path.read_bytes = patched_read_bytes


def lisp_write(path, value):
    return (
        "(with-open-file (s " + json.dumps(str(path))
        + " :direction :output :if-exists :supersede :if-does-not-exist :create) (write-line "
        + json.dumps(value) + " s))"
    )


def invoke(root, action, request):
    try:
        response = rs.client(action, root, request)
    except rs.SessionError as exc:
        response = rs.response_error(exc.reason)
    except Exception as exc:
        response = {"ok": False, "error": "harness:" + type(exc).__name__, "detail": str(exc)}
    code = rs.response_code(response) if isinstance(response, dict) and "ok" in response else 70
    return code, response


def kill_owned(controller):
    if not controller.is_file():
        return
    try:
        meta = json.loads(controller.read_text())
    except (OSError, ValueError):
        return
    pids = [meta.get("supervisor_pid"), meta.get("child_pid")]
    group = meta.get("supervisor_pgid")
    for pid in pids:
        if isinstance(pid, int) and pid > 1:
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    break
                except OSError:
                    break
    if isinstance(group, int) and group > 1:
        try:
            os.killpg(group, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass


def main():
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    head = os.popen("git -C " + json.dumps(str(ROOT)) + " rev-parse HEAD").read().strip()
    report = {
        "target": "129-B1",
        "name": "stale-attempt apply race",
        "started_at": started,
        "cwd": str(ROOT),
        "revision": head,
        "environment": {"PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": "/tmp"},
        "product_sha256": sha256((ROOT / "tools/runtime_session.py").read_bytes()),
        "runner_sha256": sha256((ROOT / "tools/test_runtime_session.py").read_bytes()),
        "lisp_sha256": sha256((ROOT / "tools/sbcl_session_loop.lisp").read_bytes()),
        "passed": False,
        "failures": [],
    }
    if head != EXPECTED:
        report["failures"].append(f"HEAD {head} != {EXPECTED}")
        print(json.dumps(report, indent=2, sort_keys=True))
        return report
    home = Path(tempfile.mkdtemp(prefix="qa5-b1-", dir="/tmp"))
    os.environ["HOME"] = str(home)
    os.environ["XDG_CACHE_HOME"] = str(home / "cache")
    os.environ["XDG_CONFIG_HOME"] = str(home / "config")
    os.environ["XDG_DATA_HOME"] = str(home / "data")
    report["fixture"] = str(home)
    root = home / "state"
    root.mkdir()
    run_state = home / "run_state.json"
    disk_obj = {
        "repository": "scratch",
        "current_phase": "020",
        "current_feature": "129",
        "status": "in_progress",
        "history": [],
        "updated_at": "2026-10-16T00:00:00Z",
        "scope_budget": {"original_estimate_lines": 7350, "total_lines_changed": 0, "per_feature": []},
        "circuit_breaker": {STEP: {"attempts": 1, "limit": 3}},
    }
    disk = (json.dumps(disk_obj, sort_keys=True) + "\n").encode()
    run_state.write_bytes(disk)
    mutated_obj = json.loads(disk)
    mutated_obj["circuit_breaker"][STEP]["attempts"] = 2
    mutated = (json.dumps(mutated_obj, sort_keys=True) + "\n").encode()
    if mutated == disk or json.loads(mutated)["circuit_breaker"][STEP]["attempts"] != 2:
        report["failures"].append("mutation did not change the governed attempts integer")
        print(json.dumps(report, indent=2, sort_keys=True))
        return report
    session_id = "qa5b1"
    controller = root / session_id / "controller.json"
    log_path = home / "reads.jsonl"
    flag = home / "arm-divergent-reread"
    STATE.update(run_state=run_state, controller=controller, log=str(log_path),
                 disk=disk, mutated=mutated, armed=str(flag))
    report["disk_sha256"] = sha256(disk)
    report["mutated_sha256"] = sha256(mutated)
    report["disk_digest"] = rs.digest_buffers([("run_state", disk)])
    report["mutated_digest"] = rs.digest_buffers([("run_state", mutated)])
    report["digests_differ"] = report["disk_digest"] != report["mutated_digest"]
    opening = {
        "session_id": session_id,
        "requester": ORCH,
        "owner": OWNER,
        "purpose": "develop",
        "contract_id": "129",
        "step_key": STEP,
        "attempt": 1,
        "run_state_path": str(run_state),
        "runtime": "sbcl",
    }
    opened = False
    try:
        code, response = invoke(root, "open-session", opening)
        report["open"] = {"exit": code, "ok": response.get("ok"), "error": response.get("error")}
        if code != 0 or not response.get("ok"):
            report["failures"].append(f"open-session failed: {code} {response}")
            return report
        opened = True
        record = response["result"]
        meta = json.loads(ORIGINAL_READ(controller))
        exe = os.readlink(f"/proc/{meta['child_pid']}/exe")
        report["runtime"] = {"controller_runtime": meta.get("runtime"), "child_exe": exe, "child_pid": meta.get("child_pid")}
        if meta.get("runtime") != "sbcl" or "sbcl" not in Path(exe).name and "sbcl" not in exe:
            report["failures"].append(f"runtime is not SBCL: {report['runtime']}")
            return report
        positive = home / "positive-witness.txt"
        stale = home / "stale-witness.txt"
        nonce = os.urandom(8).hex()
        identity = {
            "session_id": session_id,
            "requester": OWNER,
            "expected_generation": record["generation"],
            "expected_lease_epoch": record["lease_epoch"],
            "contract_id": "129",
            "step_key": STEP,
            "attempt": 1,
        }
        positive_request = {
            **identity,
            "operation_id": "positive-op",
            "kind": "evaluate",
            "payload": {"expression": "(progn " + lisp_write(positive, nonce) + " (+ 19 23))"},
            "context": {},
            "limits": {},
        }
        code, response = invoke(root, "submit-operation", positive_request)
        report["positive_submit"] = {"exit": code, "ok": response.get("ok"), "error": response.get("error")}
        if code != 0 or not response.get("ok"):
            report["failures"].append(f"positive submit failed: {code} {response}")
            return report
        deadline = time.monotonic() + 12
        terminal = None
        while time.monotonic() < deadline:
            pcode, presponse = invoke(root, "poll-operation", {
                "session_id": session_id,
                "requester": OWNER,
                "expected_generation": record["generation"],
                "expected_lease_epoch": record["lease_epoch"],
                "operation_id": "positive-op",
            })
            if presponse.get("ok") and presponse.get("result", {}).get("status") in rs.TERMINAL:
                terminal = presponse["result"]
                report["positive_poll_exit"] = pcode
                break
            time.sleep(0.05)
        result_path = root / session_id / "operations" / "positive-op.result.json"
        result = json.loads(ORIGINAL_READ(result_path)) if result_path.is_file() else None
        report["positive_terminal"] = terminal["status"] if terminal else None
        report["positive_result"] = None if result is None else result.get("result")
        report["positive_witness"] = positive.read_text().splitlines() if positive.is_file() else None
        if terminal is None or terminal.get("status") != "completed" or terminal.get("executed") is not True:
            report["failures"].append(f"positive control did not complete: {terminal}")
            return report
        if result is None or result.get("result") != 42 or result.get("image_consistent") is not True:
            report["failures"].append(f"positive SBCL result was not 42: {result}")
            return report
        if report["positive_witness"] != [nonce]:
            report["failures"].append("positive side effect missing")
            return report
        if ORIGINAL_READ(run_state) != disk:
            report["failures"].append("product wrote the governed run_state during the positive control")
            return report
        flag.write_text("armed\n")
        stale_request = {
            **identity,
            "operation_id": "stale-op",
            "kind": "evaluate",
            "payload": {"expression": "(progn " + lisp_write(stale, nonce) + " (+ 7 7))"},
            "context": {},
            "limits": {},
        }
        code, response = invoke(root, "submit-operation", stale_request)
        report["adversarial_submit"] = {
            "exit": code,
            "ok": response.get("ok"),
            "error": response.get("error"),
            "keys": sorted(response.keys()),
        }
        reads = []
        if log_path.is_file():
            for line in log_path.read_text().splitlines():
                if line:
                    reads.append(json.loads(line))
        report["reads"] = reads
        helper = [row for row in reads if not row["is_supervisor"]]
        supervisor = [row for row in reads if row["is_supervisor"]]
        op_path = root / session_id / "operations" / "stale-op.json"
        result_stale = root / session_id / "operations" / "stale-op.result.json"
        operation = json.loads(ORIGINAL_READ(op_path)) if op_path.is_file() else None
        report["stale_operation"] = operation
        report["stale_witness_exists"] = stale.exists()
        report["run_state_unchanged"] = ORIGINAL_READ(run_state) == disk
        if not helper or any(row["sha256"] != sha256(disk) or row["attempts"] != 1 for row in helper):
            report["failures"].append("helper capture did not observe the original attempts=1 buffer")
        if not supervisor or any(row["sha256"] != sha256(mutated) or row["attempts"] != 2 for row in supervisor):
            report["failures"].append("supervisor pre-apply read did not observe attempts=2")
        if response.get("ok") is not False or response.get("error") not in ("ambiguous_state", "attempt_mismatch"):
            report["failures"].append(f"stale certificate was not refused closed: {code} {response}")
        if response.get("error") == "ambiguous_state" and code != 70:
            report["failures"].append(f"ambiguous_state exit was {code}, expected 70")
        if response.get("error") == "attempt_mismatch" and code != 1:
            report["failures"].append(f"attempt_mismatch exit was {code}, expected 1")
        if stale.exists():
            report["failures"].append("stale submit executed project code")
        if result_stale.exists():
            report["failures"].append("stale submit published a result file")
        if operation is not None and (operation.get("executed") is True or operation.get("status") != "rejected"):
            report["failures"].append(f"stale operation record shows execution: {operation}")
        if not report["digests_differ"]:
            report["failures"].append("injected buffers did not change input_digest")
        if not report["run_state_unchanged"]:
            report["failures"].append("adversarial check changed on-disk run_state")
        report["passed"] = not report["failures"]
        return report
    finally:
        report["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if opened:
            try:
                invoke(root, "close-session", {
                    "session_id": session_id,
                    "requester": ORCH,
                    "expected_generation": record["generation"],
                    "expected_lease_epoch": record["lease_epoch"],
                })
            except Exception:
                pass
        kill_owned(controller)
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    outcome = main()
    sys.exit(0 if outcome.get("passed") else 1)
