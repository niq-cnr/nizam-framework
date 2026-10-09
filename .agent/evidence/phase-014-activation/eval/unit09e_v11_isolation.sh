#!/bin/bash
# Unit 9 isolation probe: prove the V11 / negative-control divergence is caused solely by the untracked
# .agent/validator/phase-014-activation.json (post-dates the committed captures). Works on a COPY of the repo.
set -u
export PYTHONDONTWRITEBYTECODE=1
SRC="$(pwd)"; COPY="$(mktemp -d "${TMPDIR:-/tmp}/eval-v11-copy.XXXXXX")"
OUT="$(mktemp -d "${TMPDIR:-/tmp}/eval-v11-out.XXXXXX")"
cp -a "$SRC/." "$COPY/"
rm -f "$COPY/.agent/validator/phase-014-activation.json"
cd "$COPY" || exit 3
B=.agent/evidence/backlog-reconciliation-2026-10-08
echo "--- validate_backlog_dag.py on copy without the validator verdict file"
python3 $B/tools/validate_backlog_dag.py > "$OUT"/out_b.txt 2>&1; rc_b=$?
grep -E "^(PASS|FAIL) V11|^SUMMARY|^ready set" "$OUT"/out_b.txt; echo "rc=$rc_b"
diff <(sed '1d' $B/dag_validation.txt | grep -v '^EXIT:') "$OUT"/out_b.txt > "$OUT"/diff_b.txt; echo "diff vs committed capture (lines): $(wc -l < "$OUT"/diff_b.txt)"; cat "$OUT"/diff_b.txt
echo "--- dag_negative_controls.py on copy"
python3 $B/tools/dag_negative_controls.py > "$OUT"/out_c.txt 2>&1; rc_c=$?
tail -1 "$OUT"/out_c.txt; echo "rc=$rc_c"
diff <(sed '1d' $B/dag_negative_controls.txt | grep -v '^EXIT:') "$OUT"/out_c.txt > "$OUT"/diff_c.txt; echo "diff vs committed capture (lines): $(wc -l < "$OUT"/diff_c.txt)"; cat "$OUT"/diff_c.txt
cd "$SRC"; rm -rf "$COPY" "$OUT"
[ "$rc_b" = 0 ] && [ "$rc_c" = 0 ]
