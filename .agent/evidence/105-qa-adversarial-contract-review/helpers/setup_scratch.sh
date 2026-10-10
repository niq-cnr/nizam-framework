# setup_scratch.sh ROOT : build ROOT/base (pristine <A> clone + the contract) and ROOT/impl (base + implement.py); extract commands.
set -eu
ROOT="$1"; REPO="$PWD"; H="$REPO/.agent/evidence/105-qa-adversarial-contract-review/helpers"
A=2a537644dc93cc71786e6468c8f4295079d1c973
rm -rf "$ROOT"; mkdir -p "$ROOT"
git clone -q "$REPO" "$ROOT/base"
git -C "$ROOT/base" -c advice.detachedHead=false checkout -q "$A"
cp "$REPO/.agent/contracts/105.json" "$ROOT/base/.agent/contracts/105.json"
python3 "$H/extract_cmds.py" "$REPO/.agent/contracts/105.json" "$H/cmds"
cp -a "$ROOT/base" "$ROOT/impl"
python3 "$H/implement.py" "$ROOT/impl"
git -C "$ROOT/impl" rev-parse HEAD
git -C "$ROOT/impl" status --short
