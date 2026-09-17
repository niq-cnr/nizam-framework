#!/usr/bin/env bash
set -euo pipefail

ROOT=
RUNNER=
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root) ROOT=$2; shift 2 ;;
    --runner) RUNNER=$2; shift 2 ;;
    --) shift; break ;;
    *) echo "linux_trial_sandbox: unknown argument: $1" >&2; exit 2 ;;
  esac
done
[[ -n "$ROOT" && -n "$RUNNER" && $# -gt 0 ]] || {
  echo "linux_trial_sandbox: --root, --runner, and command are required" >&2
  exit 2
}
SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc \
  "$SELF_DIR/isolated_trial_adapter.py" --root "$ROOT" --runner "$RUNNER" -- "$@"
