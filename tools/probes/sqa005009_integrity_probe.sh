#!/usr/bin/env bash
# Disposable live probes for framework-integrity findings SQA-integrity-005, -006, -007,
# -008, -009 and -011 (audit c905615d; findings sha256 82d4df0b34fc4235...). Writes only
# mktemp fixtures; the checkout is read-only input. Each case prints one line:
#   "CASE <id> rc=<n> <verdict>"  where verdict states whether the defect is observed.
# Usage: bash tools/probes/sqa005009_integrity_probe.sh [REPO_ROOT]
set -uo pipefail
REPO="$(cd "${1:-$(dirname "$0")/../..}" && pwd)"
W="$(mktemp -d "${TMPDIR:-/tmp}/sqa005009-probe.XXXXXX")"
export PYTHONDONTWRITEBYTECODE=1
say() { printf '%s\n' "$*"; }
trap 'rm -rf "${W}"' EXIT

# ---- 005: CI reachability of dedicated suites (static: named by a workflow or harness) ----
unreached=()
for f in "${REPO}"/tools/test_*.py; do
  rel="tools/$(basename "${f}")"
  # A suite is accounted for when CI runs it (ci_suites.txt) or it has a documented exclusion.
  if ! grep -qxF -- "${rel}" "${REPO}/tools/ci_suites.txt" 2>/dev/null \
     && ! grep -q -- "^${rel}|" "${REPO}/tools/ci_suite_exclusions.txt" 2>/dev/null; then
    unreached+=("${rel}")
  fi
done
cov_rc=$(cd "${REPO}" && PYTHONDONTWRITEBYTECODE=1 python3 tools/test_suite_coverage.py >/dev/null 2>&1; echo $?)
say "CASE 005-ci-reachability unaccounted_suites=${#unreached[@]} coverage_gate_rc=${cov_rc} (defect observed if unaccounted>0 or gate rc!=0)"

# ---- 006: C8 against a committed two-revision version bump (CI-form comparison) ----
P006="${W}/p006"; mkdir -p "${P006}/docs"
git -C "${P006}" init -q
git -C "${P006}" config user.email probe@local; git -C "${P006}" config user.name probe
printf -- '---\nid: x\ntitle: "x"\ndescription: "x"\nversion: 0.1.0\nstatus: active\nchange_log:\n  - version: "0.1.0"\n    date: "2026-01-01"\n    summary: "init"\n---\n# X\n' > "${P006}/docs/x.md"
git -C "${P006}" add -A && git -C "${P006}" commit -qm base
sed -i 's/version: 0.1.0/version: 0.2.0/' "${P006}/docs/x.md"
git -C "${P006}" commit -qam "committed bump without change record"
c8_fn="${W}/c8fn.sh"
s=$(grep -n '^check_c8_version_changelog() {' "${REPO}/tools/validate.sh" | cut -d: -f1)
# The function ends at the first column-0 "}" after its final "  return 1".
e=$(awk -v s="${s}" 'NR>s && /^  return 1$/ {r=NR} NR>s && /^}$/ && r && NR>r {print NR; exit}' "${REPO}/tools/validate.sh")
sed -n "${s},${e}p" "${REPO}/tools/validate.sh" > "${c8_fn}"
# CI form: the committed bump is compared with its prior revision (HEAD~1) via NIZAM_C8_BASE.
c8_out=$(cd "${P006}" && NIZAM_C8_BASE=HEAD~1 bash -c "source '${c8_fn}'; check_c8_version_changelog docs/x.md" 2>&1); c8_rc=$?
if [ "${c8_rc}" -eq 0 ]; then v006="ACCEPTED (defect observed: committed bump with no change record passes)"; else v006="REFUSED (committed bump with no change record is caught)"; fi
say "CASE 006-committed-bump-no-changelog rc=${c8_rc} ${v006}"

# ---- 007: second preflight run in a completed output namespace ----
P007="${W}/p007"; mkdir -p "${P007}/repo"
cp -r "${REPO}/schema" "${P007}/repo/"
git -C "${P007}/repo" init -q; git -C "${P007}/repo" add -A
git -C "${P007}/repo" -c user.email=p@l -c user.name=p commit -qm init
OUT="${P007}/out"
python3 "${REPO}/tools/ecosystem_preflight.py" --execution-id E1 --output-dir "${OUT}" \
  --repo-root "${P007}/repo" --self-fixture >/dev/null 2>&1; r1=$?
d1=$(sha256sum "${OUT}/baseline.json" 2>/dev/null | cut -c1-64)
python3 "${REPO}/tools/ecosystem_preflight.py" --execution-id E2 --output-dir "${OUT}" \
  --repo-root "${P007}/repo" --self-fixture >/dev/null 2>&1; r2=$?
d2=$(sha256sum "${OUT}/baseline.json" 2>/dev/null | cut -c1-64)
# Failing rerun: dirty the tree, rerun, check whether the baseline survives.
echo dirty > "${P007}/repo/dirty.txt"
python3 "${REPO}/tools/ecosystem_preflight.py" --execution-id E3 --output-dir "${OUT}" \
  --repo-root "${P007}/repo" --self-fixture >/dev/null 2>&1; r3=$?
d3=$(sha256sum "${OUT}/baseline.json" 2>/dev/null | cut -c1-64)
say "CASE 007-baseline-reuse first_rc=${r1} first_sha=${d1:-absent} rerun_pass_rc=${r2} rerun_pass_sha=${d2:-absent} rerun_fail_rc=${r3} rerun_fail_sha=${d3:-absent} (defect observed if an existing baseline digest changes or disappears)"

# ---- 008: usage totals for one operation with pre-dispatch and completion rows ----
u008=$(cd "${REPO}/tools" && python3 - <<'PY'
import usage_accounting as ua
base = dict(schema_version=1, operation_id="op1", model={"requested": "m"}, dispatched=True,
            outcome="success", usage={"input_tokens": 120, "output_tokens": 30})
pre = dict(base, kind="pre_dispatch", outcome=None, usage=None, event_id="p")
post = dict(base, kind="completion", event_id="c")
t = ua.usage_totals([pre, post])
ok = t["known"]["input_tokens"] == 120 and t["known"]["output_tokens"] == 30 and "input_tokens" not in t["unknown"]
print(("CORRECT" if ok else "DEFECT"), t["known"]["input_tokens"], t["known"]["output_tokens"], t["unknown"], t["charged_requests"])
PY
); 
say "CASE 008-usage-pre-post-pair ${u008} (defect observed if DEFECT: expect input=120 output=30 unknown=[] charged=1)"

# ---- 009: preregistration missing claimed-mandatory fields ----
p009=$(cd "${REPO}/tools" && python3 - <<'PY'
import evaluation_harness as eh
doc = eh.preregistration_template()
doc.update({"corpus_version": "v1", "assignment": "matched", "sample_size_rationale": "power",
            "quality_criteria": "critical-miss <= 1", "coverage_abstention_criteria": ">= 90%",
            "stopping_rule": "stop at budget or 3 misses"})
try:
    eh.validate_preregistration(doc)
    print("ACCEPTED")
except eh.HarnessError as e:
    print("REFUSED")
PY
)
unset_fields=$(cd "${REPO}/tools" && python3 -c "
import evaluation_harness as eh
t=eh.preregistration_template()
print(','.join(k for k,v in t.items() if k!='schema_version' and (v in ('',None))))")
say "CASE 009-partial-prereg ${p009} unset_declared_fields=[${unset_fields}] (defect observed if ACCEPTED with unset fields)"

# ---- 011: SELF_GOVERNANCE current-installation heading vs structured record ----
heading=$(grep -m1 -E '^# Current installation' "${REPO}/docs/planning/SELF_GOVERNANCE.md")
tag=$(grep -m1 -E '^  tag: ' "${REPO}/docs/planning/SELF_GOVERNANCE.md" | awk '{print $2}')
if printf '%s' "${heading}" | grep -q -- "${tag}"; then v011="CONSISTENT"; else v011="DEFECT (heading does not name current tag ${tag})"; fi
say "CASE 011-self-governance-heading heading='${heading}' structured_tag=${tag} ${v011}"
