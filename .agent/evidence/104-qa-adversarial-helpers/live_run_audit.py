"""Evaluator adversarial audit for feature 104 (read-only).

Independently re-derives, from the LIVE GitHub Actions runs (read-only
`gh run view`), that:
  P1. the positive run executed all 54 tests with no skip, including the five
      ISOLATION_DEPENDENT_TESTS (names derived by AST from the suite source at
      the run's headSha, not from the capture or the contract);
  N1. the negative run's convergent_review failure is caused only by
      test_linux_sandbox_blocks_cross_trial_files_and_network (AssertionError
      40 != 0, the cross-trial secret was read) and no other test regressed;
  N2. the positive and negative runs ran the identical 54-test set, and the
      only per-test status difference is that one test.
It trusts nothing in .agent/evidence/104/ci-*.txt except the two run ids on
line 1 of ci-positive-run.txt / ci-negative-run.txt (the ids are then
re-resolved live).
"""
import ast
import json
import re
import subprocess
import sys


def sh(*argv):
    p = subprocess.run(argv, capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("command failed: %s\n%s" % (" ".join(argv), p.stderr))
    return p.stdout


def run_id(capture):
    first = open(".agent/evidence/104/%s-run.txt" % capture).readline().strip()
    m = re.fullmatch(r"gh run view ([0-9]+) --json headSha,headBranch,conclusion,jobs", first)
    assert m, first
    return m.group(1)


def live(capture):
    rid = run_id(capture)
    r = json.loads(sh("gh", "run", "view", rid, "--json", "headSha,headBranch,conclusion,jobs"))
    jobs = [j for j in r["jobs"] if j["name"] == "convergent_review"]
    assert len(jobs) == 1, jobs
    log = sh("gh", "run", "view", "--job", str(jobs[0]["databaseId"]), "--log")
    return rid, r, jobs[0], log


def suite_facts(sha):
    src = sh("git", "show", sha + ":tools/test_convergent_review.py")
    tree = ast.parse(src)
    tests, dependent = [], []
    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        for fn in [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]:
            tests.append(fn.name)
            if any(isinstance(d, ast.Name) and d.id == "requires_user_namespace_isolation" for d in fn.decorator_list):
                dependent.append(fn.name)
    return tests, dependent


LINE = re.compile(r"^(test_\w+) \(__main__\.\w+\.\w+\) \.\.\. ?(.*)$")


def parse(log):
    status, summary = {}, {}
    body = []
    for raw in log.splitlines():
        parts = raw.split("\t", 2)
        text = parts[2] if len(parts) == 3 else raw
        text = text.lstrip("﻿")
        text = re.sub(r"^\d{4}-\d\d-\d\dT[\d:.]+Z ", "", text)
        body.append(text)
        m = LINE.match(text)
        if m:
            status[m.group(1)] = m.group(2).strip() or "<no status on line>"
    joined = "\n".join(body)
    summary["ran"] = re.findall(r"^Ran (\d+) tests? in", joined, re.M)
    summary["verdict"] = re.findall(r"^(OK.*|FAILED.*)$", joined, re.M)
    summary["conformance"] = re.findall(r"^CONFORMANCE: .*$", joined, re.M)
    summary["fail_blocks"] = re.findall(r"^(FAIL|ERROR): (test_\w+)", joined, re.M)
    summary["assertion"] = re.findall(r"^AssertionError: .*$", joined, re.M)
    summary["unsupported"] = len(re.findall(r"UNSUPPORTED|skipped", joined))
    return status, summary


bad = []
prid, pr, pjob, plog = live("ci-positive")
nrid, nr, njob, nlog = live("ci-negative")
print("positive run", prid, pr["headBranch"], pr["headSha"], pr["conclusion"], "job", pjob["databaseId"], pjob["conclusion"])
print("negative run", nrid, nr["headBranch"], nr["headSha"], nr["conclusion"], "job", njob["databaseId"], njob["conclusion"])

ptests, pdep = suite_facts(pr["headSha"])
ntests, ndep = suite_facts(nr["headSha"])
print("suite at positive headSha: %d tests, isolation-dependent (AST): %s" % (len(ptests), pdep))
if len(pdep) != 5:
    bad.append("expected exactly 5 isolation-dependent tests by AST, got %d" % len(pdep))
if sorted(ptests) != sorted(ntests) or pdep != ndep:
    bad.append("suite test set differs between positive and negative headSha")

pst, psum = parse(plog)
nst, nsum = parse(nlog)
print("positive summary:", psum)
print("negative summary:", nsum)

# P1: executed, not skipped
if sorted(pst) != sorted(ptests):
    bad.append("P1: tests in the live positive log != tests in the suite source at its headSha: %s" % sorted(set(pst) ^ set(ptests)))
if psum["ran"] != [str(len(ptests))] or psum["verdict"] != ["OK"] or psum["conformance"] != ["CONFORMANCE: FULL"]:
    bad.append("P1: positive summary is not 'Ran 54 / plain OK (no skipped= suffix) / CONFORMANCE: FULL'")
if psum["unsupported"] or psum["fail_blocks"]:
    bad.append("P1: positive log contains skipped/UNSUPPORTED text or a FAIL/ERROR block")
bad_status = {t: s for t, s in pst.items() if s not in ("ok", "<no status on line>")}
if bad_status:
    bad.append("P1: positive per-test statuses other than ok: %r" % bad_status)
for t in pdep:
    print("  isolation-dependent %-75s positive status: %s" % (t, pst.get(t)))
    if t not in pst:
        bad.append("P1: %s absent from the live positive log" % t)
no_status_p = sorted(t for t, s in pst.items() if s == "<no status on line>")
print("positive tests whose verbose line carries no trailing status (output interleaving; their outcome is covered by the plain 'OK' summary with no skipped= suffix):", no_status_p)

# N1: failure caused only by the sandbox test
want = "test_linux_sandbox_blocks_cross_trial_files_and_network"
if nr["conclusion"] != "failure" or njob["conclusion"] != "failure":
    bad.append("N1: negative run/job did not fail")
if nsum["fail_blocks"] != [("FAIL", want)]:
    bad.append("N1: failure blocks are not exactly [FAIL %s]: %r" % (want, nsum["fail_blocks"]))
if nsum["verdict"] != ["FAILED (failures=1)"] or nsum["ran"] != [str(len(ntests))]:
    bad.append("N1: negative verdict is not 'FAILED (failures=1)' over all 54 tests: %r" % (nsum,))
if nsum["assertion"] != ["AssertionError: 40 != 0 : "]:
    bad.append("N1: assertion line is not the 40 != 0 cross-trial secret read: %r" % (nsum["assertion"],))
if nsum["conformance"] != ["CONFORMANCE: NOT FULL (run unsuccessful)"]:
    bad.append("N1: conformance line unexpected: %r" % (nsum["conformance"],))
if sorted(nst) != sorted(ntests):
    bad.append("N1: tests in the live negative log != suite source")

# N2: identical set, single differing status
diff = {t: (pst[t], nst[t]) for t in pst if pst[t] != nst.get(t)}
print("per-test status differences positive -> negative:", diff)
if set(diff) != {want} or diff[want] != ("ok", "FAIL"):
    bad.append("N2: status differences are not exactly {%s: ok -> FAIL}: %r" % (want, diff))
others = [t for t in pdep if t != want]
for t in others:
    print("  other isolation-dependent %-67s negative status: %s" % (t, nst.get(t)))
    if nst.get(t) == "FAIL":
        bad.append("N2: %s also failed on the negative run" % t)
# other jobs in the negative run
oj = sorted((j["name"], j["conclusion"]) for j in nr["jobs"] if j["name"] != "convergent_review")
print("other jobs on the negative run:", oj)
if any(c != "success" for _, c in oj):
    bad.append("N2: a non-convergent_review job also failed on the negative run: %r" % (oj,))

print("problems:", bad)
sys.exit(1 if bad else 0)
