#!/bin/bash
# Evaluator probe, run only inside a scratch_run copy. Never invoked against the real tree.
set -u
rc1=0
out1=$(bash tools/validate.sh 2>&1) || rc1=$?
detail='capabilities[9] (anti_hallucination) -> ecosystem/README.md is not the authoritative_source of any NIZAM.json capability'
printf '%s\n' "$out1" | grep -E '^(SUMMARY: |\[C13\] )|^  capabilities\[9\]' || true
if ! printf '%s\n' "$out1" | grep -Fxq '[C13] FAIL skill-index'; then
  echo 'MUTATED_MISSING_BANNER'
  exit 1
fi
if ! printf '%s\n' "$out1" | grep -Fxq "  ${detail}"; then
  echo 'MUTATED_MISSING_DETAIL'
  exit 1
fi
if printf '%s\n' "$out1" | grep -Fq 'does not resolve'; then
  echo 'dangling-line: present'
  exit 1
fi
echo 'dangling-line: absent'
if printf '%s\n' "$out1" | grep -Eq '^\[C4\] FAIL'; then
  echo 'mutated-c4: present'
  exit 1
fi
echo 'mutated-c4: absent'
if [ "$rc1" -eq 0 ]; then
  echo 'MUTATED_RC_ZERO'
  exit 1
fi
echo 'MUTATED C13 FAIL'

python3 - << 'PY'
from pathlib import Path
p = Path("tools/skill.json")
text = p.read_text(encoding="utf-8")
old = '"module": "ecosystem/README.md"'
new = '"module": "standard/anti_hallucination.md"'
count = text.count(old)
if count != 1:
    raise SystemExit("restore precondition failed: %s" % count)
p.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

if ! git -c safe.directory="$(pwd)" diff --quiet -- tools/skill.json; then
  echo 'PIN_MISMATCH'
  git -c safe.directory="$(pwd)" diff -- tools/skill.json
  exit 1
fi
echo 'pin-restored: matches HEAD'

rc2=0
out2=$(bash tools/validate.sh 2>&1) || rc2=$?
printf '%s\n' "$out2" | grep -E '^(SUMMARY: |\[C13\] )' || true
if [ "$rc2" -ne 0 ]; then
  echo "RESTORED_RC_${rc2}"
  exit 1
fi
if ! printf '%s\n' "$out2" | grep -Fxq '[C13] PASS skill-index'; then
  echo 'RESTORED_MISSING_PASS'
  exit 1
fi
if printf '%s\n' "$out2" | grep -Eq '^\[C13\] FAIL'; then
  echo 'RESTORED_STILL_FAIL'
  exit 1
fi
echo 'RESTORED C13 PASS'
