# setup_scratch.sh ROOT : build ROOT/base (pristine <A> clone + contract/validator files) and ROOT/impl (base + implement.py)
set -eu
ROOT="$1"; REPO="$PWD"; H="$REPO/.agent/evidence/104-qa-adversarial-contract-review/helpers"
rm -rf "$ROOT"; mkdir -p "$ROOT"
git clone -q "$REPO" "$ROOT/base"
git -C "$ROOT/base" -c advice.detachedHead=false checkout -q f3b6dcb3a2e9c8a465e8ccb1be2e67fce721deef
cp "$REPO/.agent/contracts/104.json" "$ROOT/base/.agent/contracts/104.json"
mkdir -p "$ROOT/base/.agent/validator"; cp "$REPO/.agent/validator/104-mode-a.json" "$ROOT/base/.agent/validator/"
git clone -q "$ROOT/base" "$ROOT/impl" 2>/dev/null || true
rm -rf "$ROOT/impl"; cp -a "$ROOT/base" "$ROOT/impl"
python3 "$H/implement.py" "$ROOT/impl"
git -C "$ROOT/impl" rev-parse HEAD
git -C "$ROOT/impl" status --short
