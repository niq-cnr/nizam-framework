#!/usr/bin/env bash
# Trusted Docker-controller equivalent of the Linux convergent-review trial
# sandbox adapter (tools/linux_trial_sandbox.sh). Implements the same
# ADAPTER --root TRIAL_ROOT --runner RUNNER -- RUNNER_ARGUMENTS... protocol:
# the trial runs in a fresh, network-less, capability-less, read-only
# container over the digest-pinned image below, with same-path bind mounts
# (trial root rw, runner ro, inner Landlock adapter ro), a fixed minimal
# container environment, and the existing isolated_trial_adapter.py invoked
# inside the container with explicit interpreter allowlist rules.
#
# Fail-closed: exit 2 = invalid arguments, exit 3 = daemon unreachable or
# pinned image absent, exit 4 = inner setup/teardown failure. Otherwise the
# container's waited exit code is propagated. Untrusted input can never
# select the image, mounts, network mode, or any runtime option: every one
# of those is a constant below, and the omission-control tests exercise
# scratch copies with a single constant reverted.
set -euo pipefail

# --- trusted constants (single-line; the suite's omission controls replace exactly one of these in a scratch copy) ---
PINNED_IMAGE="docker.io/library/python@sha256:618e7b661a89d05565fb402a5e1eab8b1b4e5df1f5ea3dc494998d092ffe1213"
NETWORK_MODE="none"
EXTRA_MOUNTS=()

SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
INNER_ADAPTER="$SELF_DIR/isolated_trial_adapter.py"
INNER_PYTHON="/usr/local/bin/python3"
INNER_ENV="/usr/bin/env"
INNER_PATH="/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"
# Verified minimal Landlock interpreter allowlist for the pinned image:
# /usr rules do not cover OverlayFS lower-layer inodes, so the shebang
# resolver, POSIX shell, and musl dynamic loader each need an explicit rule.
INTERPRETERS=(/usr/bin/env /bin/sh /lib/ld-musl-x86_64.so.1)
RUN_TIMEOUT_SECONDS=180
STOP_TIMEOUT_SECONDS=10
CONTAINER_PREFIX="nizam-review-trial-"

fail() { echo "docker_trial_sandbox: $*" >&2; }

if [[ ${1:-} == "--print-image" ]]; then
  printf '%s\n' "$PINNED_IMAGE"
  exit 0
fi

if [[ ${1:-} == "--probe" ]]; then
  if ! docker info >/dev/null 2>&1; then
    fail "docker daemon unreachable"
    exit 3
  fi
  if ! docker image inspect "$PINNED_IMAGE" >/dev/null 2>&1; then
    fail "pinned image absent locally: $PINNED_IMAGE"
    exit 3
  fi
  echo "docker_trial_sandbox: docker daemon reachable; pinned image present"
  exit 0
fi

ROOT=
RUNNER=
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root) ROOT=${2:-}; shift 2 ;;
    --runner) RUNNER=${2:-}; shift 2 ;;
    --) shift; break ;;
    *) fail "unknown argument: $1"; exit 2 ;;
  esac
done

validate_path() {
  local value=$1 label=$2
  [[ -n $value ]] || { fail "$label is required"; exit 2; }
  [[ $value == /* ]] || { fail "$label must be an absolute path: $value"; exit 2; }
  [[ $value != *","* ]] || { fail "$label must not contain a comma: $value"; exit 2; }
  [[ $value != -* && $value != */-* ]] || { fail "$label must not contain a flag-shaped component: $value"; exit 2; }
}

[[ $# -gt 0 ]] || { fail "--root, --runner, and command are required"; exit 2; }
validate_path "$ROOT" "--root"
validate_path "$RUNNER" "--runner"

if ! docker info >/dev/null 2>&1; then
  fail "docker daemon unreachable"
  exit 3
fi
if ! docker image inspect "$PINNED_IMAGE" >/dev/null 2>&1; then
  fail "pinned image absent locally: $PINNED_IMAGE"
  exit 3
fi

[[ -d $ROOT ]] || { fail "trial root is not a directory: $ROOT"; exit 4; }
[[ -f $RUNNER && -r $RUNNER ]] || { fail "runner is not a readable regular file: $RUNNER"; exit 4; }
[[ -f $INNER_ADAPTER && -r $INNER_ADAPTER ]] || { fail "inner adapter missing: $INNER_ADAPTER"; exit 4; }

NAME="${CONTAINER_PREFIX}$$-$(date +%s%N)"
cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

INTERPRETER_ARGS=()
for interpreter in "${INTERPRETERS[@]}"; do
  INTERPRETER_ARGS+=(--interpreter "$interpreter")
done

set +e
timeout --signal=KILL "${RUN_TIMEOUT_SECONDS}s" docker run --rm --name "$NAME" \
  --network "$NETWORK_MODE" \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --read-only \
  --user "$(id -u):$(id -g)" \
  --stop-timeout "$STOP_TIMEOUT_SECONDS" \
  --volume "$ROOT:$ROOT:rw" \
  --volume "$RUNNER:$RUNNER:ro" \
  --volume "$INNER_ADAPTER:$INNER_ADAPTER:ro" \
  "${EXTRA_MOUNTS[@]}" \
  --workdir "$ROOT" \
  "$PINNED_IMAGE" \
  "$INNER_ENV" -i \
  "PATH=$INNER_PATH" \
  "HOME=/nonexistent" \
  "PYTHONDONTWRITEBYTECODE=1" \
  "$INNER_PYTHON" "$INNER_ADAPTER" \
  "${INTERPRETER_ARGS[@]}" \
  --root "$ROOT" --runner "$RUNNER" -- "$@"
status=$?
set -e

case $status in
  0) exit 0 ;;
  124) fail "trial timed out after ${RUN_TIMEOUT_SECONDS}s; container removed"; exit 4 ;;
  125) fail "docker run failed to start the trial container"; exit 4 ;;
  *) exit "$status" ;;
esac
