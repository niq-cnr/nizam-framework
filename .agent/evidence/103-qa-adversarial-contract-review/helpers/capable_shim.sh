#!/bin/sh
# Simulated CAPABLE host: `unshare` succeeds for the probe, and for the sandbox call it drops the 8 namespace flags
# and execs the adapter directly (no namespaces). This is gating-logic simulation only, NOT capable-host evidence.
printf '%s\n' "$*" >> "${UNSHARE_SHIM_LOG:-/dev/null}"
if [ "$*" = "--user --map-root-user true" ]; then exit 0; fi
if [ "$1" = "--user" ] && [ "$2" = "--map-root-user" ] && [ "$3" = "--net" ]; then shift 8; exec "$@"; fi
echo "capable_shim: unexpected unshare invocation: $*" >&2; exit 98
