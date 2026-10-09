#!/bin/bash
# rec.sh OUTFILE CMD... : write OUTFILE in the 04 Section-5 shape: line 1 the exact invocation, then verbatim stdout+stderr,
# final line EXIT:<code> read from the process itself (no pipeline between the command and the exit capture).
out="$1"; shift
{ printf '%s\n' "$*"; "$@" 2>&1; rc=$?; printf 'EXIT:%s\n' "$rc"; } > "$out"
tail -n 1 "$out"
