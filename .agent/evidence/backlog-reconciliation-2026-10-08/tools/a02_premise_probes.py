#!/usr/bin/env python3
"""A02 premise probes: pre-implementation sweep + discriminating controls for EVERY phase-014 acceptance test.

Run from the repository root:

    python3 .agent/evidence/backlog-reconciliation-2026-10-08/tools/a02_premise_probes.py

Revision 3 (2026-10-08; validator round 1). Revision 2 probed only the amended tests of
099/100/101/102 and one 104 test; revision 3 covers every acceptance test in
.agent/feature_list_014.json:

  PART A -- pre-implementation sweep. Every test (all of them; coverage is asserted
  exactly against the feature list) is executed on the current, pre-implementation tree
  and must show its declared outcome:
    fail        exits non-zero (the work it verifies does not exist yet);
    fail-mut    a scratch_run negative control: exits 1 with "EXPECTATION FAILED" --
                i.e. its mutation PRECONDITION HELD (exit 3 would mean it did not) and
                the expectation is not yet met;
    inapplicable  a scratch_run test whose mutation needs the feature's own artifact
                (exit 3, "MUTATION PRECONDITION FAILED") -- correctly inapplicable;
    guard       a regression guard that passes before implementation by design;
    gate        a phase-wide gate (validator gate, fixtures, close-out) that passes now.
  PART B -- discriminating controls (P1-P21): the written test against synthetic or
  mutated inputs that a correct implementation produces (must PASS) and that a wrong
  one produces (must FAIL), plus the OLD (pre-amendment) forms read from git.

Every probed command is read verbatim from the feature list (feature id + 1-based test
index) or from git (02b02c6, or 9edd5d0 for the pre-D1 tag test). The only
substitutions are input paths, by exact replacement that must match (a non-matching
substitution aborts the probe, so no row can pass vacuously). Simulations run the
written test with a scratch COPY of the repository as its working directory, after
applying the named mutations; nothing under the repository is written.

A row is OK when the observed exit status (and, where stated, the exception class or
marker) equals the expectation. Exit 0 only if every row is OK.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROWS: list[tuple[str, bool]] = []
SCRATCH = Path(tempfile.mkdtemp(prefix="a02-probes-"))
FL = ".agent/feature_list_014.json"
GATES = ".agent/evidence/phase-014-activation/gates"
PIN = subprocess.run(["git", "rev-parse", "v1.4.0^{commit}"], capture_output=True, text=True, check=True).stdout.strip()
HEAD_COMMIT = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
CAP = subprocess.run(["unshare", "--user", "--map-root-user", "true"], capture_output=True).returncode == 0
SANDBOX = ["test_linux_sandbox_blocks_cross_trial_files_and_network", "test_linux_sandbox_blocks_execution_of_runner_generated_trial_file",
           "test_prompt_evaluator_rejects_runner_symlink_substitution_for_post_run_files", "test_prompt_evaluator_runs_three_isolated_validated_trials",
           "test_prompt_evaluator_uses_per_trial_packet_copies"]


class ProbeSetupError(Exception):
    """Raised when a probe cannot be built faithfully (e.g. a substitution matches nothing)."""


def sh(cmd: str, cwd: str | Path | None = None) -> tuple[int, str]:
    """Run a command line through bash, returning (exit status, combined output)."""
    p = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, cwd=cwd)
    return p.returncode, (p.stdout + p.stderr)


def exc(out: str) -> str:
    """Return the last Python exception class named in an output, or '-'."""
    m = re.findall(r"^(?:[\w]+\.)*(\w+(?:Error|Exception))\b", out, re.M)
    return m[-1] if m else "-"


def row(probe: str, case: str, rc: int, want: int, out: str = "", want_exc: str | None = None) -> None:
    """Record and print one probe row."""
    got = exc(out)
    ok = rc == want and (want_exc is None or got == want_exc)
    ROWS.append((f"{probe} {case}", ok))
    tail = f" exc={got}" + (f" (want {want_exc})" if want_exc else "")
    print(f"{'OK  ' if ok else 'BAD '} {probe:<4} {case:<84} rc={rc} want={want}{tail}")


def sub(text: str, old: str, new: str, count: int | None = None) -> str:
    """Exact replacement that must match (exactly `count` times when given)."""
    n = text.count(old)
    if n == 0 or (count is not None and n != count):
        raise ProbeSetupError(f"substitution target {old!r} occurs {n} times")
    return text.replace(old, new)


def at(fid: str, idx: int, rev: str | None = None) -> str:
    """Acceptance test idx (1-based) of feature fid, from the working tree or a git revision."""
    raw = Path(FL).read_text(encoding="utf-8") if rev is None else subprocess.run(
        ["git", "show", f"{rev}:{FL}"], capture_output=True, text=True, check=True).stdout
    feats = {f["id"]: f for f in json.loads(raw)["features"]}
    return feats[fid]["acceptance_tests"][idx - 1]


def write(rel: str, content: str) -> str:
    """Write a scratch file and return its absolute path."""
    p = SCRATCH / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return str(p)


_copies = 0


def copy_repo(*edits: tuple[str, str, str]) -> Path:
    """A scratch copy of the repository (with .git) after exact edits (path, old, new); each old must occur once."""
    global _copies
    _copies += 1
    root = SCRATCH / f"copy{_copies}"
    shutil.copytree(Path.cwd(), root, symlinks=True)
    for rel, old, new in edits:
        p = root / rel
        p.write_text(sub(p.read_text(encoding="utf-8"), old, new, count=1), encoding="utf-8")
    return root


def literal(label: str, text: str) -> None:
    """Print a probed command verbatim."""
    print(f"\n--- {label} ---\n{text}\n")


# =========================================================================== PART A
EXPECT = {
    "099": ["gate", "guard", "fail", "fail", "fail", "fail", "fail", "gate"],
    "103": ["fail", "fail", "fail-mut", "fail-mut", "guard", "fail", "gate", "gate"],
    "104": ["fail", "guard", "fail", "fail", "fail", "fail", "fail", "fail", "gate", "gate"],
    "105": ["fail", "fail", "fail-mut", "fail", "gate"],
    "106": ["fail", "fail", "fail", "fail-mut", "guard", "gate", "gate", "gate"],
    "107": ["fail", "fail-mut", "fail-mut", "fail", "gate", "gate"],
    "109": ["fail", "inapplicable", "guard", "fail", "gate", "gate"],
    "108": ["fail", "fail", "fail", "fail", "gate", "gate", "gate"],
    "100": ["fail", "fail", "fail", "fail", "gate"],
    "101": ["fail", "fail", "fail", "gate", "gate"],
    "102": ["fail", "fail", "fail", "guard", "fail", "fail", "guard", "gate", "gate", "gate"],
}
WHY_GUARD = {
    ("099", 2): "key_documents landed with the proposal (NDEBT-005)",
    ("103", 5): "fail-closed sandbox must stay byte-identical to 02b02c6",
    ("104", 2): "job-count statements consistent at 3 jobs; discrimination in P10",
    ("106", 5): "no check number beyond C16 (C17 earmarked by NIP-0003)",
    ("109", 3): "existing primitive keeps accepting a role-less doc",
    ("102", 4): "no tag created since activation (fetches origin first)",
    ("102", 7): "frozen acceptance infrastructure unchanged since activation",
}
print("== PART A: pre-implementation sweep of every acceptance test ==")
fl_doc = json.loads(Path(FL).read_text(encoding="utf-8"))
listed = {(f["id"], i) for f in fl_doc["features"] for i in range(1, len(f["acceptance_tests"]) + 1)}
declared = {(fid, i) for fid, v in EXPECT.items() for i in range(1, len(v) + 1)}
cov_ok = listed == declared
ROWS.append(("A0 coverage", cov_ok))
print(f"{'OK  ' if cov_ok else 'BAD '} A0   expectation table covers exactly the {len(listed)} acceptance tests"
      + ("" if cov_ok else f" -- missing {sorted(listed - declared)} extra {sorted(declared - listed)}"))
for f in fl_doc["features"]:
    for i, cmd in enumerate(f["acceptance_tests"], 1):
        kind = EXPECT.get(f["id"], [None] * 99)[i - 1]
        rc, out = sh(cmd)
        last = (out.strip().splitlines() or [""])[-1][:70]
        if kind in ("gate", "guard"):
            ok = rc == 0
        elif kind == "fail":
            ok = rc != 0 and "MUTATION PRECONDITION FAILED" not in out and rc not in (126, 127)
        elif kind == "fail-mut":
            ok = rc == 1 and "EXPECTATION FAILED" in out and "MUTATION PRECONDITION FAILED" not in out
        elif kind == "inapplicable":
            ok = rc == 3 and "MUTATION PRECONDITION FAILED" in out
        else:
            ok = False
        note = WHY_GUARD.get((f["id"], i), "")
        ROWS.append((f"A {f['id']} AT{i}", ok))
        print(f"{'OK  ' if ok else 'BAD '} A    {f['id']} AT{i:<2} {kind:<12} rc={rc:<3} {note or last}")

print("\n== PART B: discriminating controls ==")
try:
    # ====================================================== P1 missing edge 101 -> 099
    P1 = ("python3 -c \"import json,sys; f={x['id']:x for x in json.load(open('.agent/feature_list_014.json'))['features']}; "
          "sys.exit(0 if set(f['101']['dependencies'])>={'099','100'} else 1)\"")
    literal("P1 edge detector", P1)
    rc, out = sh(P1)
    row("P1", "amended feature_list_014.json (101 deps include 099) -> PASS", rc, 0, out)
    old = write("fl_02b02c6.json", subprocess.run(["git", "show", f"02b02c6:{FL}"], capture_output=True, text=True, check=True).stdout)
    rc, out = sh(sub(P1, FL, old))
    row("P1", "02b02c6 feature_list_014.json (edge absent) -> FAIL", rc, 1, out)

    # ====================================================== P2 exit-captured validator gate
    NEW_V = at("099", 1)
    OLD_V = at("099", 1, "02b02c6")
    literal("P2 NEW 099 AT1 (the gate used by every feature)", NEW_V)

    def fake(name: str, lines: list[str], code: int) -> str:
        return write(f"{name}.sh", "cat <<'X'\n" + "\n".join(lines) + f"\nX\nexit {code}\n")

    def checks(n: int, skip: int = 0) -> list[str]:
        return [f"[C{i}] PASS check-{i}" for i in range(1, n + 1) if i != skip]

    for case, script, want_new, want_old in [
        ("real tree", None, 0, 0),
        ("synthetic: prints 16/16 SUMMARY but exits 1 (pipeline-swallow false pass)", fake("optimistic", checks(16) + ["SUMMARY: 16 passed, 0 failed"], 1), 1, 0),
        ("synthetic: a check silently dropped (15/15, exit 0)", fake("dropped", checks(16, skip=9) + ["SUMMARY: 15 passed, 0 failed"], 0), 1, 1),
        ("synthetic: an authorized new check added (17/17, exit 0)", fake("added", checks(17) + ["SUMMARY: 17 passed, 0 failed"], 0), 0, 1),
        ("synthetic: a FAIL line under a '0 failed' SUMMARY, exit 0", fake("lying", checks(16) + ["[C3] FAIL x", "SUMMARY: 16 passed, 0 failed"], 0), 1, 0),
        ("synthetic: SUMMARY passed-count disagrees with PASS lines", fake("miscount", checks(16) + ["SUMMARY: 17 passed, 0 failed"], 0), 1, 1),
    ]:
        rc, out = sh(NEW_V if script is None else NEW_V + f" --command 'bash {script}'")
        row("P2", "NEW  " + case, rc, want_new, out)
        rc, out = sh(OLD_V if script is None else sub(OLD_V, "bash tools/validate.sh", f"bash {script}"))
        row("P2", "OLD  " + case, rc, want_old, out)

    # ====================================================== P3 099 AT5 per-gate rows
    GATES_MD = "docs/planning/operator_gates.md"
    NEW_G, OLD_G = at("099", 5), at("099", 5, "02b02c6")
    text = Path(GATES_MD).read_text(encoding="utf-8")

    def move(t: str, gates: tuple[str, ...]) -> str:
        for g in gates:
            line = next(ln for ln in t.splitlines() if ln.startswith(f"| `{g}` |"))
            t = t.replace(line + "\n", "")
            t = sub(t, "| `H-TRAIN-ENTRY` |", f"| `{g}` | (scope) | `.agent/product_spec_014.md` | DEFINED (feature 099) — OUTSTANDING. |\n| `H-TRAIN-ENTRY` |")
        return t

    for case, t, want_new, want_old in [
        # OLD false-passes: Section 1's H-PHASE-NNN row MENTIONS both gates (activation record) while both are reserved.
        ("current file (both still reserved; Section 1 merely mentions them)", text, 1, 0),
        ("only H-CONSOLIDATION defined (H-GA still reserved)", move(text, ("H-CONSOLIDATION",)), 1, 0),
        ("both defined and removed from Section 2", move(text, ("H-CONSOLIDATION", "H-GA")), 0, 0),
    ]:
        p = write(re.sub(r"\W+", "_", case) + ".md", t)
        rc, out = sh(sub(NEW_G, GATES_MD, p))
        row("P3", "NEW  " + case, rc, want_new, out)
        rc, out = sh(sub(OLD_G, GATES_MD, p))
        row("P3", "OLD  " + case, rc, want_old, out)

    # ====================================================== P4 102 AT1 (NameError) + correction
    import yaml  # noqa: E402

    PH = "docs/planning/phase_014.yaml"
    NEW_P, OLD_P = at("102", 1), at("102", 1, "02b02c6")
    base = yaml.safe_load(Path(PH).read_text(encoding="utf-8"))
    EVF = ".agent/evidence/phase-014-activation/validate.txt"
    done = dict(base, status="complete", steps=[dict(s, status="COMPLETED", evidence=EVF) for s in base["steps"]])
    ghost = dict(done, steps=[dict(s, evidence=".agent/evidence/102/does-not-exist.txt") if s["id"] == "102" else s for s in done["steps"]])
    half = dict(done, steps=[{k: v for k, v in dict(s, status="PENDING").items() if k != "evidence"} if s["id"] == "102" else s for s in done["steps"]])
    for case, d, wn, wne, wo, woe in [
        ("current phase_014.yaml (in_progress)", None, 1, "AssertionError", 1, "NameError"),
        ("scratch: complete, all steps COMPLETED with evidence", done, 0, "-", 1, "NameError"),
        ("scratch: complete but step 102 PENDING", half, 1, "AssertionError", 1, "NameError"),
        ("scratch: status 'done' (outside schema enum)", dict(done, status="done"), 1, "ValidationError", 1, "NameError"),
        ("scratch: complete, step 102 evidence path does not exist", ghost, 1, "AssertionError", 1, "NameError"),
    ]:
        target = PH if d is None else write(re.sub(r"\W+", "_", case) + ".yaml", yaml.safe_dump(d, sort_keys=False))
        rc, out = sh(sub(NEW_P, PH, target) if d is not None else NEW_P)
        row("P4", "NEW  " + case, rc, wn, out, wne)
        rc, out = sh(sub(OLD_P, PH, target) if d is not None else OLD_P)
        row("P4", "OLD  " + case, rc, wo, out, woe)

    # ====================================================== P5 phase-scoped tag check (fetches tags first)
    NEW_T, PRE_D1, D1_T = at("102", 4), at("102", 4, "9edd5d0"), at("102", 4, "02b02c6")
    literal("P5 NEW 102 AT4", NEW_T)
    rc, out = sh(PRE_D1)
    row("P5", "PRE-D1 fixed v1.4.0 absence on real tree -> false failure once v1.4.0 exists", rc, 1, out)
    rc, out = sh(D1_T)
    row("P5", "D1 fixed v1.5.0 absence on real tree -> passes (blind to any other tag)", rc, 0, out)
    rc, out = sh(NEW_T)
    row("P5", "NEW real tree after `git fetch --tags` (tag set == activation baseline)", rc, 0, out)
    tags = subprocess.run(["git", "tag", "-l"], capture_output=True, text=True, check=True).stdout.split()
    for case, cur, want in [
        ("synthetic: v1.5.0 cut during the phase", tags + ["v1.5.0"], 1),
        ("synthetic: a non-release tag 'pilot-snapshot' created", tags + ["pilot-snapshot"], 1),
        ("synthetic: ephemeral e2e-1791457101-354425 present (harness)", tags + ["e2e-1791457101-354425"], 0),
        ("synthetic: a baseline tag deleted (nothing created)", [t for t in tags if t != "v0.1.0"], 0),
    ]:
        rc, out = sh(NEW_T + " --current-tags " + ",".join(cur))
        row("P5", "NEW  " + case, rc, want, out)
    bad_base = write("tag-baseline-malformed.txt", "git tag -l\nv1.3.0\n")
    rc, out = sh(NEW_T + f" --baseline {bad_base}")
    row("P5", "NEW  malformed baseline (no EXIT line, no v1.4.0) -> usage 2, never 0", rc, 2, out)
    rc, out = sh(sub(NEW_T, "origin", "no-such-remote-xyz"))
    row("P5", "NEW  tag fetch fails (unreachable remote) -> the test fails, never passes blind", rc, 128, out)

    # ====================================================== P6 100 real members, pin, ordering
    PIL = ".agent/evidence/pilot-100"
    A2, A3, A4 = at("100", 2), at("100", 3), at("100", 4)
    OLD_A1, OLD_A4 = at("100", 1, "02b02c6"), at("100", 4, "02b02c6")
    p84 = SCRATCH / "pilot084"
    p84.mkdir()
    shutil.copy(".agent/evidence/pilot-084/membership.json", p84 / "registry.json")
    shutil.copy(".agent/evidence/pilot-084/membership_run.json", p84 / "aggregate.json")
    (p84 / "members.json").write_text(json.dumps([{"name": m, "origin_url": "", "branch": "", "head_sha": ""} for m in ("member-alpha", "member-beta")]))
    (p84 / "README.md").write_text("pilot\n")
    (p84 / "gates-record.md").write_text("- H-CONSUMER-UPGRADE recorded\n")
    rc, out = sh(sub(A2, PIL, str(p84)))
    row("P6", "NEW  100 AT2 on pilot-084 (scratch pilot, pin 9ca14c4 != v1.4.0) -> FAIL", rc, 1, out, "AssertionError")
    rc, out = sh(sub(A3, PIL, str(p84)))
    row("P6", "NEW  100 AT3 on pilot-084 (/tmp members, no remotes) -> FAIL", rc, 1, out, "AssertionError")
    rc, out = sh(sub(OLD_A1, PIL, str(p84)))
    row("P6", "OLD  100 AT1 existence check on the same scratch evidence -> accepts", rc, 0, out)
    rc, out = sh(sub(OLD_A4, PIL, str(p84)))
    row("P6", "OLD  100 AT4 broad grep on the same scratch evidence -> accepts", rc, 0, out)
    real = SCRATCH / "pilot-real"
    real.mkdir()
    reg = json.loads(Path(".agent/evidence/pilot-084/membership.json").read_text())
    names = ["svc-alpha", "svc-beta"]
    reg["in_scope"] = [{"name": n, "status": "active"} for n in names]
    reg["authoritative_source"] = ".agent/evidence/pilot-100/registry.json"
    agg = json.loads(Path(".agent/evidence/pilot-084/membership_run.json").read_text())
    agg["framework_pin"] = PIN
    agg["members"] = [dict(agg["members"][0], name=n, repo_root=f"/srv/work/{n}-pilot-100", framework_pin=PIN) for n in names]
    (real / "registry.json").write_text(json.dumps(reg))
    (real / "aggregate.json").write_text(json.dumps(agg))
    (real / "members.json").write_text(json.dumps([
        {"name": n, "origin_url": f"https://example.org/acme/{n}.git", "branch": "pilot/100-v1.4.0", "head_sha": "a" * 40} for n in names]))
    rc, out = sh(sub(A2, PIL, str(real)))
    row("P6", "NEW  100 AT2 synthetic real pilot at the peeled v1.4.0 commit -> PASS", rc, 0, out)
    tagobj = subprocess.run(["git", "rev-parse", "v1.4.0"], capture_output=True, text=True, check=True).stdout.strip()
    tobj = SCRATCH / "pilot-tagobj"
    shutil.copytree(real, tobj)
    (tobj / "aggregate.json").write_text(json.dumps(dict(agg, framework_pin=tagobj, members=[dict(m, framework_pin=tagobj) for m in agg["members"]])))
    rc, out = sh(sub(A2, PIL, str(tobj)))
    row("P6", "NEW  100 AT2 pin recorded as the annotated TAG OBJECT (not the commit) -> FAIL", rc, 1, out, "AssertionError")
    rc, out = sh(sub(A3, PIL, str(real)))
    row("P6", "NEW  100 AT3 synthetic real members (remote, isolated branch, sha) -> PASS", rc, 0, out)
    m2 = SCRATCH / "pilot-main"
    shutil.copytree(real, m2)
    on_main = json.loads((real / "members.json").read_text())
    on_main[1]["branch"] = "main"
    (m2 / "members.json").write_text(json.dumps(on_main))
    rc, out = sh(sub(A3, PIL, str(m2)))
    row("P6", "NEW  100 AT3 one member worked on its main branch -> FAIL", rc, 1, out, "AssertionError")
    hist = json.loads(Path(".agent/run_state.json").read_text())

    def gate_case(tag: str, recs: list[dict], events: list[dict]) -> tuple[str, str]:
        d = SCRATCH / f"gates_{tag}"
        shutil.copytree(real, d)
        (d / "gates-record.json").write_text(json.dumps(recs))
        return str(d), write(f"run_state_{tag}.json", json.dumps(dict(hist, history=hist["history"] + events)))

    def rec(n: str, dec: str, boot: str) -> dict:
        return {"member": n, "gate": "H-CONSUMER-UPGRADE", "verbatim": f"approve {n} at v1.4.0", "decided_at": dec, "bootstrapped_at": boot}

    def ev(n: str, at_: str) -> dict:
        return {"at": at_, "event": "operator_gate_decision", "detail": f"H-CONSUMER-UPGRADE for {n} at v1.4.0"}

    good = ([rec("svc-alpha", "2026-10-09T10:00:00Z", "2026-10-09T10:05:00Z"), rec("svc-beta", "2026-10-09T10:01:00Z", "2026-10-09T10:06:00Z")],
            [ev("svc-alpha", "2026-10-09T10:00:00Z"), ev("svc-beta", "2026-10-09T10:01:00Z")])
    for case, (recs, evs), want in [
        ("each member: one decision, recorded in run_state, before bootstrap", good, 0),
        ("svc-beta decided AFTER its bootstrap (NDEBT-018 violation)",
         ([good[0][0], rec("svc-beta", "2026-10-09T10:09:00Z", "2026-10-09T10:06:00Z")], [good[1][0], ev("svc-beta", "2026-10-09T10:09:00Z")]), 1),
        ("svc-beta has no decision at all", ([good[0][0]], [good[1][0]]), 1),
        ("svc-beta decision only self-reported (no run_state event)", (good[0], [good[1][0]]), 1),
    ]:
        d, rsp = gate_case(re.sub(r"\W+", "_", case)[:24], recs, evs)
        rc, out = sh(sub(sub(A4, PIL, d), ".agent/run_state.json", rsp))
        row("P6", "NEW  100 AT4 " + case, rc, want, out)

    # ====================================================== P7 101 scoped audit checks (+ zero-findings rule)
    B1, B2, B3 = at("101", 1), at("101", 2), at("101", 3)
    OLD_B1, OLD_B2 = at("101", 1, "02b02c6"), at("101", 2, "02b02c6")
    AB = ".agent/evidence/phase-014-activation/audits-baseline.txt"
    real_audits = sorted(Path(".agent/audits").iterdir())
    finding_src = real_audits[0] / "findings.json"
    pilot_agg = str(real / "aggregate.json")

    def audits_tree(idx: int, name: str, findings: str, section: bool, review: dict | None, readme_only: bool) -> tuple[str, str]:
        root = SCRATCH / f"audits_{idx}"
        shutil.copytree(".agent/audits", root / "audits")
        d = root / "audits" / name
        d.mkdir()
        if readme_only:
            (d / "README.md").write_text("Notes; consolidation reserved behind H-CONSOLIDATION.\n")
        if findings == "real":
            shutil.copy(finding_src, d / "findings.json")
        elif findings == "empty":
            (d / "findings.json").write_text("[]")
        if review is not None:
            (d / "review.json").write_text(json.dumps(dict(review, inputs=[pilot_agg if i == ".agent/evidence/pilot-100/aggregate.json" else i for i in review["inputs"]])))
        sect = "## 4. Consolidation Candidates\n\nAll reserved behind H-CONSOLIDATION.\n" if section else "## 4. Candidates\n\nnone\n"
        (d / "report.md").write_text("# Review\n\nH-CONSOLIDATION mentioned in the intro only.\n\n" + sect)
        bl = root / "audits-baseline.txt"
        bl.write_text("ls -1 .agent/audits\n" + "\n".join(p.name for p in real_audits) + "\nEXIT:0\n")
        return str(root / "audits"), str(bl)

    gr = {"revision": HEAD_COMMIT, "timestamp": "2026-10-10T09:00:00Z", "inputs": [".agent/evidence/pilot-100/aggregate.json"]}
    for idx, (case, name, wf, ws, rv, ro, w1, w2, w3, wo) in enumerate([
        ("stray notes dir '*simplification*' with README naming H-CONSOLIDATION only", "x-simplification-notes", "none", False, None, True, 1, 1, 1, 0),
        ("schema-valid findings; H-CONSOLIDATION only outside the consolidation section", "sr-simplification-2026", "real", False, gr, False, 0, 0, 1, 0),
        ("review.json does not cite pilot-100 evidence", "sr-simplification-2026", "real", True, dict(gr, inputs=[EVF]), False, 0, 1, 0, 0),
        ("EMPTY findings.json without a zero_findings_justification", "sr-simplification-2026", "empty", True, gr, False, 1, 0, 0, 0),
        ("EMPTY findings.json with a stated zero_findings_justification", "sr-simplification-2026", "empty", True, dict(gr, zero_findings_justification="no candidate cleared the evidence floor"), False, 0, 0, 0, 0),
        ("complete: schema-valid findings, anchored review, scoped reservation", "sr-simplification-2026", "real", True, gr, False, 0, 0, 0, 0),
    ]):
        a, bl = audits_tree(idx, name, wf, ws, rv, ro)

        def prep(cmd: str) -> str:
            return sub(sub(cmd, ".agent/audits", a), AB, bl).replace(".agent/evidence/pilot-100/aggregate.json", pilot_agg)

        for label, cmd, want in (("AT1", B1, w1), ("AT2", B2, w2), ("AT3", B3, w3)):
            rc, out = sh(prep(cmd))
            row("P7", f"NEW  101 {label} {case}", rc, want, out)
        rc1, _ = sh(sub(OLD_B1, ".agent/audits", a))
        rc2, _ = sh(sub(OLD_B2, ".agent/audits/", a + "/"))
        row("P7", "OLD  101 AT1+AT2 " + case, 0 if (rc1 == 0 and rc2 == 0) else 1, wo)

    # ====================================================== P8 102 GA-readiness dossier (Planner hardening)
    C2, C3, C5 = at("102", 2), at("102", 3), at("102", 5)
    OLD_C2, OLD_C3 = at("102", 2, "02b02c6"), at("102", 3, "02b02c6")
    DOS = ".agent/evidence/102/ga-readiness.json"
    keys = ["real_production_pilot", "stable_release_history", "recorded_consumer_adoptions", "no_open_critical_high_debt", "benchmark_thresholds"]

    def pre(status: str = "met", ev_: list | None = None) -> dict:
        return {"status": status, "evidence": ev_ or [EVF], "revision": HEAD_COMMIT, "timestamp": "2026-10-10T09:00:00Z"}

    good_d = {"h_ga": "OUTSTANDING", "ga_declared": False, "preconditions": {k: pre() for k in keys}}
    good_d["preconditions"]["real_production_pilot"] = pre("met", [pilot_agg])
    debt_open = Path("docs/planning/DEBT.md").read_text(encoding="utf-8")
    debt_high = write("DEBT_high.md", sub(debt_open, "|----|------|----------|-------------|-------|\n",
                                          "|----|------|----------|-------------|-------|\n| NDEBT-099 | 2026-10-10 | High | synthetic |  |\n"))
    for case, d, debt, want2, want3 in [
        ("well-formed dossier, H-GA OUTSTANDING", good_d, None, 0, 0),
        ("a precondition missing", dict(good_d, preconditions={k: v for k, v in good_d["preconditions"].items() if k != "benchmark_thresholds"}), None, 1, 0),
        ("ga_declared true", dict(good_d, ga_declared=True), None, 1, 0),
        ("an evidence path that does not exist", dict(good_d, preconditions=dict(good_d["preconditions"], stable_release_history=pre("met", ["nope/x.txt"]))), None, 1, 0),
        ("debt claimed 'met' while the register has an open High row", good_d, debt_high, 0, 1),
    ]:
        dp = write(re.sub(r"\W+", "_", case) + ".json", json.dumps(d))
        c3 = sub(C3, DOS, dp).replace(".agent/evidence/pilot-100/aggregate.json", pilot_agg)
        if debt:
            c3 = sub(c3, "docs/planning/DEBT.md", debt)
        rc, out = sh(sub(C2, DOS, dp))
        row("P8", "NEW  102 AT2 " + case, rc, want2, out)
        rc, out = sh(c3)
        row("P8", "NEW  102 AT3 " + case, rc, want3, out)
    md = write("102/ga-readiness-dossier.md", "# Dossier\n\nH-GA was OUTSTANDING last week; GA DECLARED today.\n")
    rc, out = sh(sub(OLD_C2, ".agent/evidence/102/ga-readiness-dossier.md", md) + " && " + sub(OLD_C3, ".agent/evidence/102/ga-readiness-dossier.md", md))
    row("P8", "OLD  102 AT2+AT3 substring checks accept a dossier that declares GA", rc, 0, out)

    # ====================================================== P9 102 AT5 ROADMAP open-debt bullet
    rc, out = sh(C5)
    row("P9", "NEW  real ROADMAP (stale 'two rows' bullet naming NDEBT-036) -> FAIL", rc, 1, out, "AssertionError")
    want_ids = re.findall(r"^\| (NDEBT-\d+) \|", debt_open.split("## Open")[1].split("## Resolved")[0], re.M)
    road = Path("docs/planning/ROADMAP.md").read_text(encoding="utf-8")
    start = road.index("- Open debt (current")
    end = road.index("`NDEBT-036` is **Resolved**", start) + len("`NDEBT-036` is **Resolved**")
    fixed = write("ROADMAP_fixed.md", road[:start] + "- Open debt (current, at DEBT.md v0.49.0): " + ", ".join(f"`{i}`" for i in want_ids)
                  + " remain Open. Resolved since the last roll: `NDEBT-036`" + road[end:])
    rc, out = sh(sub(C5, "docs/planning/ROADMAP.md", fixed))
    row("P9", "NEW  synthetic ROADMAP naming exactly the Open ids -> PASS", rc, 0, out)

    # ====================================================== P10 104 AT2 derived job-count
    J2 = at("104", 2)
    wf = Path(".github/workflows/compliance.yml").read_text(encoding="utf-8")
    JOB_YAML = "\n  convergent_review:\n    runs-on: ubuntu-latest\n    steps:\n      - run: python3 tools/test_convergent_review.py\n"
    wf4 = write("compliance4.yml", wf + JOB_YAML)
    dod = Path("standard/definition_of_done.md").read_text(encoding="utf-8")
    dod4 = write("dod4.md", dod.replace("`fixtures_self_test` -- passes", "`fixtures_self_test`, and `convergent_review` -- passes")
                 .replace("all three, plus", "all four, plus").replace("three-job workflow", "four-job workflow").replace("three jobs `.github", "four jobs `.github"))
    for case, w, d, want in [
        ("real tree (3 jobs, DoD says three)", None, None, 0),
        ("4th job added, DoD still says three", wf4, None, 1),
        ("4th job added, DoD names it and says four", wf4, dod4, 0),
    ]:
        c = J2
        if w:
            c = sub(c, ".github/workflows/compliance.yml", w)
        if d:
            c = sub(c, "standard/definition_of_done.md", d)
        rc, out = sh(c)
        row("P10", "NEW  104 AT2 " + case, rc, want, out)

    # ====================================================== P11 scratch_run is fail-closed
    SRN = f"python3 {GATES}/scratch_run.py"
    for case, cmd, want in [
        ("--replace target absent -> mutation precondition 3", f"{SRN} --replace NIZAM.json 'NO-SUCH-TEXT-xyz' 'y' --expect-rc 0 -- true", 3),
        ("--replace target occurs twice -> 3", f"{SRN} --replace tools/linux_trial_sandbox.sh 'ROOT' 'X' --expect-rc 0 -- true", 3),
        ("--write over an existing file -> 3", f"{SRN} --write NIZAM.json '{{}}' --expect-rc 0 -- true", 3),
        ("--py-mutate raising -> 3", f"{SRN} --py-mutate 'raise ValueError(1)' --expect-rc 0 -- true", 3),
        ("expectation unmet -> 1", f"{SRN} --expect-rc 0 -- false", 1),
        ("expectations met -> 0", f"{SRN} --write zz/probe.txt hi --expect-rc 0 --expect '^hi$' -- cat zz/probe.txt", 0),
    ]:
        rc, out = sh(cmd)
        row("P11", case, rc, want, out)
    rc, out = sh("test ! -e zz/probe.txt")
    row("P11", "the real tree was not written by the scratch run", rc, 0, out)

    # ====================================================== P12 099 simulated implementation (positive) + scoping
    nz = json.loads(Path("NIZAM.json").read_text())
    nz["capabilities"] += [{"id": "nizam-ecosystem-simplification-review", "summary": "s", "authoritative_source": "ecosystem/06_simplification_review.md"},
                           {"id": "nizam-ecosystem-ga-gate", "summary": "g", "authoritative_source": "ecosystem/08_ga_gate.md"}]
    sk = json.loads(Path("tools/skill.json").read_text())
    sk["capabilities"] += [{"name": "ecosystem_simplification_review", "description": "d", "module": "ecosystem/06_simplification_review.md"},
                           {"name": "ecosystem_ga_gate", "description": "d", "module": "ecosystem/08_ga_gate.md"}]
    card_old = "<code>ecosystem/07_progress_comparison.md</code>.</p>"
    card_all = ", ".join(f"<code>{p}</code>" for p in sorted(str(x) for x in Path("ecosystem").glob("0*.md"))) + ".</p>"
    c99 = copy_repo(("ecosystem/06_simplification_review.md", "status: draft\n", "status: active\n"),
                    ("ecosystem/06_simplification_review.md", "version: 0.1.0\n", "version: 0.2.0\n"),
                    ("ecosystem/08_ga_gate.md", "status: draft\n", "status: active\n"),
                    ("ecosystem/08_ga_gate.md", "version: 0.1.0\n", "version: 0.2.0\n"),
                    ("docs/guide/index.html", card_old, "<code>ecosystem/07_progress_comparison.md</code>, " + card_all))
    (c99 / "NIZAM.json").write_text(json.dumps(nz, indent=2))
    (c99 / "tools/skill.json").write_text(json.dumps(sk, indent=2))
    gpath = c99 / "docs/planning/operator_gates.md"
    gpath.write_text(move(gpath.read_text(), ("H-CONSOLIDATION", "H-GA")))
    for i in (3, 4, 5, 6, 7):
        rc, out = sh(at("099", i), cwd=c99)
        row("P12", f"099 AT{i} on a simulated correct implementation -> PASS", rc, 0, out)
    tools_card = "<code>tools/interface.md</code>, <code>tools/validate.sh</code>, <code>tools/README.md</code>.</p>"
    c99b = copy_repo(("docs/guide/index.html", tools_card, tools_card + "\n        <p>" + card_all))
    rc, out = sh(at("099", 7), cwd=c99b)
    row("P12", "099 AT7 all ecosystem paths added to a DIFFERENT card (not the ecosystem card) -> FAIL", rc, 1, out, "AssertionError")

    # ====================================================== P13 103 stub-suite simulations (restricted-host branch)
    def stub_suite(required_rc: int, allow_rc: int, unsupported: list[str], extra: str = "", conformance: str = "CONFORMANCE: NOT FULL") -> str:
        lines = [f"{t} (__main__.SemanticMutationTests.{t}) ... skipped 'UNSUPPORTED: user-namespace isolation unavailable'" if t in unsupported
                 else f"{t} (__main__.SemanticMutationTests.{t}) ... skipped 'host'" for t in SANDBOX]
        body = "\n".join(lines) + ("\n" + extra if extra else "") + f"\n{conformance}\nOK (skipped=5)"
        return ("#!/usr/bin/env python3\nimport sys\nprint(" + repr(body) + ")\n"
                f"sys.exit({allow_rc} if '--allow-unsupported-isolation' in sys.argv else {required_rc})\n")

    if CAP:
        print("NOTE P13 isolation-capable host: restricted-host stub rows not applicable here; capable branch evidenced by 104 AT5-AT8")
    else:
        for case, stub, w1, w2 in [
            ("correct: 5 UNSUPPORTED, NOT FULL, required exit 1, allow exit 0", stub_suite(1, 0, SANDBOX), 0, 0),
            ("wrong: required mode exits 0 (silent pass)", stub_suite(0, 0, SANDBOX), 1, 0),
            ("wrong: one sandbox test not marked UNSUPPORTED", stub_suite(1, 0, SANDBOX[:4]), 1, 1),
            ("wrong: a non-sandbox test FAILs under the flag", stub_suite(1, 0, SANDBOX, "FAIL: test_manifest_is_frozen_twelve_case_corpus (x)"), 1, 1),
            ("wrong: no CONFORMANCE line", stub_suite(1, 0, SANDBOX, conformance=""), 1, 1),
        ]:
            c = copy_repo()
            (c / "tools/test_convergent_review.py").write_text(stub)
            rc, out = sh(at("103", 1), cwd=c)
            row("P13", "103 AT1 " + case, rc, w1, out)
            rc, out = sh(at("103", 2), cwd=c)
            row("P13", "103 AT2 " + case, rc, w2, out)
    rc, out = sh(f"{SRN} --replace tools/fixtures/convergent_review/manifest.json '\"cases\"' '\"cases_tampered\"' --expect-rc nonzero "
                 "--expect '^(FAIL|ERROR): test_(?!linux_sandbox|prompt_evaluator_(rejects|runs_three|uses_per))' -- python3 tools/test_convergent_review.py")
    row("P13", "103 AT3's tamper is effective today (non-sandbox tests fail, flag aside)", rc, 0, out)
    mv_good = copy_repo(("tools/README.md", "The required convergent review gate runs with",
                         "Use --allow-unsupported-isolation locally; outcomes: UNSUPPORTED tests with CONFORMANCE: NOT FULL, or CONFORMANCE: FULL.\nThe required convergent review gate runs with"))
    rc, out = sh(at("103", 6), cwd=mv_good)
    row("P13", "103 AT6 tokens in the Machine Validation section -> PASS", rc, 0, out)
    mv_bad = copy_repo(("tools/README.md", "### Fixture self-test (`tools/fixtures_self_test.sh`)",
                        "### Fixture self-test (`tools/fixtures_self_test.sh`)\n\n--allow-unsupported-isolation UNSUPPORTED CONFORMANCE: NOT FULL CONFORMANCE: FULL"))
    rc, out = sh(at("103", 6), cwd=mv_bad)
    row("P13", "103 AT6 same tokens only in the Fixture self-test section -> FAIL (scoped)", rc, 1, out, "AssertionError")

    # ====================================================== P14 104 simulations: job, scoped docs, CI evidence contract
    c104 = copy_repo(("tools/README.md", "The required convergent review gate runs with", "CI job `convergent_review` runs it.\nThe required convergent review gate runs with"),
                     ("schema/README.md", "| `review_packet.schema.json` |", "The review family's sole validator is `tools/test_convergent_review.py`.\n\n| `review_packet.schema.json` |"))
    (c104 / ".github/workflows/compliance.yml").write_text(wf + JOB_YAML)
    for i in (1, 3, 4):
        rc, out = sh(at("104", i), cwd=c104)
        row("P14", f"104 AT{i} on a simulated correct implementation -> PASS", rc, 0, out)
    cflag = copy_repo()
    (cflag / ".github/workflows/compliance.yml").write_text(wf + JOB_YAML.replace("test_convergent_review.py", "test_convergent_review.py --allow-unsupported-isolation"))
    rc, out = sh(at("104", 1), cwd=cflag)
    row("P14", "104 AT1 job runs the suite WITH --allow-unsupported-isolation -> FAIL", rc, 1, out, "AssertionError")
    cdd3 = copy_repo(("schema/README.md", "## DD-3", "## DD-3\n\nThe review family's sole validator is `tools/test_convergent_review.py`.\n\n"))
    rc, out = sh(at("104", 3), cwd=cdd3)
    row("P14", "104 AT3 sole-validator sentence outside the Schemas section -> FAIL (scoped)", rc, 1, out, "AssertionError")

    def ev_files(root: Path, kind: str, run: dict, log_lines: list[str], run_exit: int = 0, log_exit: int = 0, log_job: int | None = None) -> None:
        d = root / ".agent/evidence/104"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"ci-{kind}-run.txt").write_text(f"gh run view 4242 --json headSha,headBranch,conclusion,jobs\n{json.dumps(run, indent=1)}\nEXIT:{run_exit}\n")
        jid = log_job if log_job is not None else run["jobs"][-1]["databaseId"]
        (d / f"ci-{kind}-log.txt").write_text(f"gh run view --job {jid} --log\n" + "\n".join(log_lines) + f"\nEXIT:{log_exit}\n")

    jobs_ok = [{"name": "validate", "databaseId": 1, "conclusion": "success"}, {"name": "convergent_review", "databaseId": 7, "conclusion": "success"}]
    jobs_bad = [{"name": "validate", "databaseId": 1, "conclusion": "success"}, {"name": "convergent_review", "databaseId": 9, "conclusion": "failure"}]
    pos_run = {"headSha": HEAD_COMMIT, "headBranch": "phase/014-ga-track", "conclusion": "success", "jobs": jobs_ok}
    pos_log = ["convergent_review\tRun\t2026Z Ran 54 tests in 4.3s", "convergent_review\tRun\t2026Z OK", "convergent_review\tRun\t2026Z CONFORMANCE: FULL"]
    neg_run = {"headSha": "b" * 40, "headBranch": "throwaway/104-sandbox-removal", "conclusion": "failure", "jobs": jobs_bad}
    neg_log = ["convergent_review\tRun\t2026Z FAIL: test_linux_sandbox_blocks_cross_trial_files_and_network (__main__.X)", "FAILED (failures=1)"]
    for case, pr, pl, nr, nl, kw, want5, want6, want7, want8 in [
        ("well-formed positive and negative evidence", pos_run, pos_log, neg_run, neg_log, {}, 0, 0, 0, 0),
        ("positive run on another branch", dict(pos_run, headBranch="main"), pos_log, neg_run, neg_log, {}, 1, 0, 0, 0),
        ("positive headSha not an ancestor of HEAD", dict(pos_run, headSha="c" * 40), pos_log, neg_run, neg_log, {}, 1, 0, 0, 0),
        ("positive log shows skipped tests", pos_run, pos_log + ["convergent_review\tRun\t2026Z OK (skipped=5)"], neg_run, neg_log, {}, 0, 1, 0, 0),
        ("positive log is another job's log", pos_run, pos_log, neg_run, neg_log, {"log_job": 1}, 0, 1, 0, 0),
        ("negative run not on a throwaway/104- branch", pos_run, pos_log, dict(neg_run, headBranch="feature/x"), neg_log, {}, 0, 0, 1, 0),
        ("negative log fails a different test", pos_run, pos_log, neg_run, ["FAIL: test_manifest_is_frozen_twelve_case_corpus (x)"], {}, 0, 0, 0, 1),
    ]:
        c = copy_repo()
        (c / ".github/workflows/compliance.yml").write_text(wf + JOB_YAML)
        ev_files(c, "positive", pr, pl, log_job=kw.get("log_job"))
        ev_files(c, "negative", nr, nl, log_exit=1)
        for i, want in ((5, want5), (6, want6), (7, want7), (8, want8)):
            rc, out = sh(at("104", i), cwd=c)
            row("P14", f"104 AT{i} {case}", rc, want, out)

    # ====================================================== P15 105 scoped README check
    c105 = copy_repo(("tools/README.md", "### Fixture self-test (`tools/fixtures_self_test.sh`)", "### Fixture self-test (`tools/fixtures_self_test.sh`)\n\nA claim map assigns each fixture subdirectory to one suite."))
    rc, out = sh(at("105", 4), cwd=c105)
    row("P15", "105 AT4 'claim map' in the Fixture self-test section -> PASS", rc, 0, out)
    c105b = copy_repo(("tools/README.md", "## Machine Validation", "## Machine Validation\n\nA claim map exists."))
    rc, out = sh(at("105", 4), cwd=c105b)
    row("P15", "105 AT4 'claim map' only in another section -> FAIL (scoped)", rc, 1, out, "AssertionError")

    # ====================================================== P16 106 simulations
    skill_row = next(l for l in Path("tools/README.md").read_text().splitlines() if l.startswith("| [`skill.json`]"))
    c106 = copy_repo(("tools/README.md", skill_row, skill_row[:-2] + " Its capabilities are an intentional subset of NIZAM.json's (C13). |"))
    nz6 = json.loads(Path("NIZAM.json").read_text())
    nz6["capabilities"].append({"id": "nizam-ecosystem-bootstrap", "summary": "b", "authoritative_source": "ecosystem/00_ecosystem_bootstrap.md"})
    (c106 / "NIZAM.json").write_text(json.dumps(nz6, indent=2))
    for i in (1, 2):
        rc, out = sh(at("106", i), cwd=c106)
        row("P16", f"106 AT{i} on a simulated correct implementation -> PASS", rc, 0, out)
    c106b = copy_repo(("tools/README.md", "## Machine Validation", "## Machine Validation\n\nskill.json is an intentional subset of NIZAM.json."))
    rc, out = sh(at("106", 1), cwd=c106b)
    row("P16", "106 AT1 decision stated outside the skill.json row -> FAIL (row-scoped)", rc, 1, out, "AssertionError")

    # ====================================================== P17 107 simulations + C1/C2 trigger specificity
    c107 = copy_repo(("docs/nips/NIP-0002-zero-to-n-project-spectrum.md", "status: accepted\n", "status: active\n"),
                     ("tools/validate.sh", "python3 + jsonschema against schema/frontmatter.schema.json.", "python3 + jsonschema against schema/frontmatter.schema.json; docs/nips/*.md too."),
                     ("tools/validate.sh", "Format (belt-and-braces beyond schema). For the same shipped-doc", "Format (belt-and-braces beyond schema; docs/nips/ too). For the same shipped-doc"),
                     ("tools/README.md", "| C1 | Frontmatter schema | Every shipped `.md`'s frontmatter validates against `schema/frontmatter.schema.json`. |",
                      "| C1 | Frontmatter schema | Every shipped `.md` (and docs/nips/) validates against `schema/frontmatter.schema.json`. |"))
    for i in (1, 4):
        rc, out = sh(at("107", i), cwd=c107)
        row("P17", f"107 AT{i} on a simulated correct implementation -> PASS", rc, 0, out)
    c107b = copy_repo(("tools/validate.sh", "python3 + jsonschema against schema/frontmatter.schema.json.", "python3 + jsonschema against schema/frontmatter.schema.json; docs/nips/*.md too."),
                      ("tools/README.md", "| C1 | Frontmatter schema | Every shipped `.md`'s frontmatter validates against `schema/frontmatter.schema.json`. |",
                       "| C1 | Frontmatter schema | Every shipped `.md` (and docs/nips/) validates against `schema/frontmatter.schema.json`. |"))
    rc, out = sh(at("107", 4), cwd=c107b)
    row("P17", "107 AT4 docs/nips/ named in the C1 paragraph but not the C2 paragraph -> FAIL", rc, 1, out, "AssertionError")
    NIP1 = "docs/nips/NIP-0001-ecosystem-engineering-cycle.md"
    rc, out = sh(f"{SRN} --replace {NIP1} 'status: active' 'status: accepted' --expect-rc 1 --expect '^\\[C1\\] FAIL' -- bash tools/validate.sh --target {NIP1}")
    row("P17", "107 AT2's mutation is a C1 trigger (proven via --target today)", rc, 0, out)
    rc, out = sh(f"{SRN} --replace {NIP1} 'authoritative_source: {NIP1}' 'authoritative_source: docs/nips/NIP-0001-moved.md' --expect-rc 1 "
                 f"--expect '^\\[C2\\] FAIL' --forbid '^\\[C1\\] FAIL' -- bash tools/validate.sh --target {NIP1}")
    row("P17", "107 AT3's mutation is a C2-ONLY trigger (C2 FAIL, C1 PASS via --target today)", rc, 0, out)

    # ====================================================== P18 109 simulations
    cp = Path("standard/capability_profiles.md").read_text()
    hdr = "| Capability Profile | Task Type | Latency Budget | Cost Budget | Safety Class |"
    sep = cp.split(hdr + "\n")[1].splitlines()[0]
    role_edits = [("standard/capability_profiles.md", hdr + "\n" + sep, "| Capability Profile | Role | Task Type | Latency Budget | Cost Budget | Safety Class |\n|---" + sep)]
    for prof, role in (("orchestrator-primary", "Orchestrator"), ("planner-creative", "Planner"), ("generator-deterministic", "Generator"),
                       ("validator-structural", "Validator"), ("evaluator-adversarial", "Evaluator")):
        role_edits.append(("standard/capability_profiles.md", f"| `{prof}` |", f"| `{prof}` | {role} |"))
    c109 = copy_repo(*role_edits)
    rc, out = sh(at("109", 1), cwd=c109)
    row("P18", "109 AT1 with an explicit Role column -> PASS", rc, 0, out)
    rc, out = sh(at("109", 2), cwd=c109)
    row("P18", "109 AT2 once a Role column exists the swap applies (not 3), and today's C15 misses it -> 1", rc, 1, out)
    for case, fn, want in [
        ("primitive prints a 'vlib_profiles_map_roles: ... Role' diagnostic and returns 1", "echo \"vlib_profiles_map_roles: $1: no Role column\"; return 1", 0),
        ("primitive returns 1 silently (no targeted diagnostic)", "return 1", 1),
        ("primitive prints the diagnostic but returns 0", "echo \"vlib_profiles_map_roles: $1: no Role column\"; return 0", 1),
        ("primitive returns 2 with the diagnostic (not the contracted code)", "echo \"vlib_profiles_map_roles: $1: no Role column\"; return 2", 1),
    ]:
        c = copy_repo()
        with open(c / "tools/verify_lib.sh", "a", encoding="utf-8") as fh:
            fh.write("\nvlib_profiles_map_roles() {\n  " + fn + "\n}\n")
        rc, out = sh(at("109", 4), cwd=c)
        row("P18", "109 AT4 " + case, rc, want, out)

    # ====================================================== P19 108 mutation controls
    help_ins = ("Shipped-doc set (the file set",
                "  C14 Workflow SHA pins.\n\n  C15 Capability-profile roles.\n\n  C16 Feature-list lifecycle.\n\nShipped-doc set (the file set")
    payload_old = ("C8): every .md under standard/, templates/, and tools/ EXCLUDING\ntools/fixtures/; and schema/README.md. CONTEXT.md, docs/architecture/,\n"
                   "methodology/, and registry/ are intentionally excluded because they are not\ninjected into consumer repositories by bootstrap.sh.")
    payload_new = ("C8): every .md under standard/, templates/, methodology/, ecosystem/, and tools/\nEXCLUDING tools/fixtures/; and schema/README.md. CONTEXT.md,\n"
                   "docs/architecture/ and registry/ are intentionally excluded because they are not\ninjected into consumer repositories by bootstrap.sh.")
    c108 = copy_repo(("tools/validate.sh", help_ins[0], help_ins[1]),
                     ("tools/validate.sh", "Zero case-insensitive occurrences of", "Zero case-sensitive occurrences of"),
                     ("tools/validate.sh", payload_old, payload_new),
                     ("tools/interface.md", "(Section 2, Item 4).", "(Section 2, Item 5)."))
    for i in (1, 2, 3, 4):
        rc, out = sh(at("108", i), cwd=c108)
        row("P19", f"108 AT{i} on a simulated correct implementation -> PASS", rc, 0, out)
    for case, edits, i in [
        ("help paragraphs for C14 and C15 only (C16 missing)", [("tools/validate.sh", help_ins[0], "  C14 Pins.\n\n  C15 Roles.\n\nShipped-doc set (the file set")], 1),
        ("text says case-sensitive but the sweep greps with -i", [("tools/validate.sh", "Zero case-insensitive occurrences of", "Zero case-sensitive occurrences of"),
                                                                  ("tools/validate.sh", "grep -InE 'nizamiq", "grep -iInE 'nizamiq")], 2),
        ("payload paragraph adds ecosystem/ but still calls methodology/ excluded",
         [("tools/validate.sh", "every .md under standard/, templates/, and tools/ EXCLUDING", "every .md under standard/, templates/, ecosystem/, and tools/ EXCLUDING")], 3),
        ("interface.md item 10 cites Item 6", [("tools/interface.md", "(Section 2, Item 4).", "(Section 2, Item 6).")], 4),
    ]:
        c = copy_repo(*edits)
        rc, out = sh(at("108", i), cwd=c)
        row("P19", f"108 AT{i} wrong: {case} -> FAIL", rc, 1, out, "AssertionError")

    # ====================================================== P20 102 AT7 frozen-infrastructure hash pin
    c = copy_repo((f"{GATES}/scratch_run.py", "Exit codes: 0 expectations held;", "Exit codes (edited): 0 expectations held;"))
    rc, out = sh(at("102", 7), cwd=c)
    row("P20", "102 AT7 a frozen gate script edited during the phase -> FAIL", rc, 1, out, "AssertionError")
    c = copy_repo((".agent/evidence/phase-014-activation/tag-baseline.txt", "v1.4.0\n", "v1.4.0\nv1.5.0\n"))
    rc, out = sh(at("102", 7), cwd=c)
    row("P20", "102 AT7 the tag baseline widened to admit v1.5.0 -> FAIL", rc, 1, out, "AssertionError")

except ProbeSetupError as err:
    print(f"PROBE SETUP ERROR: {err}")
    ROWS.append(("setup", False))
finally:
    shutil.rmtree(SCRATCH, ignore_errors=True)

bad = [r for r, ok in ROWS if not ok]
print(f"\nPROBES: {len(ROWS) - len(bad)}/{len(ROWS)} rows matched expectation; scratch removed: {not SCRATCH.exists()}")
for r in bad:
    print("MISMATCH: " + r)
sys.exit(1 if bad else 0)
