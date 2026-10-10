#!/bin/bash
# Evaluator probe, feature 107. Invoked only as the scratch_run command.
# Never mutates the real worktree. Two serial validate.sh runs, never overlapped
# with tools/fixtures_self_test.sh.
set -u
cwd=$(pwd -P)
case "$cwd" in
  *nizam-scratch-run-*/repo) ;;
  *)
    echo "REFUSING: cwd is not a private scratch copy: $cwd"
    exit 9
    ;;
esac
if [ "$cwd" = "/home/cnross/workspace02/nizam-wt-107-attempt1" ]; then
  echo "REFUSING: cwd is the real worktree"
  exit 9
fi
NIP="docs/nips/NIP-0003-live-runtime-sessions.md"
python3 - << 'PY'
from pathlib import Path
p = Path("docs/nips/NIP-0003-live-runtime-sessions.md")
t = p.read_text(encoding="utf-8")
old = "status: draft\n"
count = t.count(old)
if count != 1:
    raise SystemExit("precondition failed: status: draft count %s" % count)
if "status: accepted\n" in t:
    raise SystemExit("precondition failed: status accepted already present")
p.write_text(t.replace(old, "status: accepted\n", 1), encoding="utf-8")
PY
rc1=0
out1=$(bash tools/validate.sh 2>&1) || rc1=$?
detail="  docs/nips/NIP-0003-live-runtime-sessions.md: frontmatter schema violation: 'accepted' is not one of ['draft', 'active', 'deprecated']"
printf '%s\n' "$out1" | grep -E '^(SUMMARY: |\[C1\] |\[C2\] )|^  docs/nips/NIP-0003' || true
fail=0
if ! printf '%s\n' "$out1" | grep -Fxq '[C1] FAIL frontmatter-schema'; then
  echo 'ACCEPTED_MISSING_C1_BANNER'
  fail=1
fi
if ! printf '%s\n' "$out1" | grep -Fxq "$detail"; then
  echo 'ACCEPTED_MISSING_C1_DETAIL'
  fail=1
fi
if [ "$rc1" -eq 0 ]; then
  echo 'ACCEPTED_RC_ZERO'
  fail=1
else
  echo "ACCEPTED_RC:$rc1"
fi
if [ "$fail" -eq 0 ]; then
  echo 'ACCEPTED C1 FAIL'
fi
python3 - << 'PY'
from pathlib import Path
p = Path("docs/nips/NIP-0003-live-runtime-sessions.md")
t = p.read_text(encoding="utf-8")
old = "status: accepted\n"
count = t.count(old)
if count != 1:
    raise SystemExit("valid-status precondition failed: status accepted count %s" % count)
p.write_text(t.replace(old, "status: active\n", 1), encoding="utf-8")
print("status-now: active")
PY
rc2=0
out2=$(bash tools/validate.sh 2>&1) || rc2=$?
printf '%s\n' "$out2" | grep -E '^(SUMMARY: |\[C1\] |\[C2\] )' || true
if printf '%s\n' "$out2" | grep -Eq '^\[C1\] FAIL'; then
  echo 'valid-c1-fail: present'
  fail=1
else
  echo 'valid-c1-fail: absent'
fi
if ! printf '%s\n' "$out2" | grep -Fxq '[C1] PASS frontmatter-schema'; then
  echo 'VALID_MISSING_C1_PASS'
  fail=1
fi
if ! printf '%s\n' "$out2" | grep -Fxq '[C2] PASS format'; then
  echo 'VALID_MISSING_C2_PASS'
  fail=1
fi
if ! printf '%s\n' "$out2" | grep -Fxq 'SUMMARY: 16 passed, 0 failed'; then
  echo 'VALID_SUMMARY_UNEXPECTED'
  fail=1
fi
if [ "$rc2" -ne 0 ]; then
  echo "VALID_RC:$rc2"
  fail=1
else
  echo 'VALID_RC:0'
fi
if [ "$fail" -eq 0 ]; then
  echo 'VALID STATUS C1 PASS'
fi
exit "$fail"
