#!/usr/bin/env bash
# Disposable live probes for framework-integrity findings SQA-integrity-001/002/010
# (audit c905615d; findings sha256 82d4df0b34fc4235...). Only throwaway fixtures under
# a mktemp dir are written; the checkout is read-only input.
# Usage: bash tools/probes/f001_integrity_probe.sh [REPO_ROOT]
set -uo pipefail
REPO="$(cd "${1:-$(dirname "$0")/../..}" && pwd)"
W="$(mktemp -d "${TMPDIR:-/tmp}/f001-probe.XXXXXX")"
TAG="v$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["framework"]["version"])' "${REPO}/NIZAM.json")"
export ALLOW_FIXTURE_TAG=1 PYTHONDONTWRITEBYTECODE=1
say() { printf '%s\n' "$*"; }

git clone -q "${REPO}" "${W}/src" || { say "PROBE-ERROR clone"; exit 2; }
git -C "${W}/src" config uploadpack.allowFilter true
git -C "${W}/src" -c user.email=p@x -c user.name=p tag -f -a "${TAG}" -m fixture HEAD
SHA="$(git -C "${W}/src" rev-parse "${TAG}^{commit}")"
say "fixture: tag=${TAG} sha=${SHA}"

install() { # $1=target $2=git-repo (may be empty)
  local args=(--repo-url "file://${W}/src" --tag "${TAG}" --target "$1" --expected-sha "${SHA}")
  [ -n "$2" ] && args+=(--git-repo "$2")
  bash "${REPO}/bootstrap.sh" "${args[@]}"
}

say "== 001 consumer lock vs exact payload inventory =="
C1="${W}/c001"; mkdir -p "${C1}"; git -C "${C1}" init -q
install "${C1}/.nizam" "${W}/ref001" >"${W}/001-install.log" 2>&1; say "install_rc=$?"
# Lock derived from the installed provenance.json (lock-payload fields agree by construction).
python3 - "${C1}/.nizam/provenance.json" "${C1}/.nizam/provenance.lock.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
lock = {"framework_version": p["framework_version"], "tag": p["tag"], "resolved_sha": p["resolved_sha"],
        "declared_range": ">=3.1.0,<4.0.0", "source_url": p["source_url"]}
json.dump(lock, open(sys.argv[2], "w"), indent=2)
PY
(cd "${REPO}" && python3 tools/check_provenance_lock.py --repo "${C1}"); say "lock_check_rc=$?"
python3 "${REPO}/tools/payload_integrity.py" --payload-dir "${C1}/.nizam" --git-repo "${W}/ref001" \
  --expected-tag "${TAG}" --expected-sha "${SHA}" --expected-source-url "file://${W}/src" \
  --require-tag-ref --require-reference-tree; say "payload_verify_rc=$?"
# Negative control: an extra non-lock file must still fail (must remain failing after fix).
C1x="${W}/c001x"; cp -R "${C1}" "${C1x}"; echo junk > "${C1x}/.nizam/extra-file.txt"
python3 "${REPO}/tools/payload_integrity.py" --payload-dir "${C1x}/.nizam" --git-repo "${W}/ref001" \
  --expected-tag "${TAG}" --expected-sha "${SHA}" --expected-source-url "file://${W}/src" \
  --require-tag-ref --require-reference-tree; say "extra_file_verify_rc=$?"

# Upgrade metadata loss: a reinstall replaces the whole target, so a consumer lock is dropped.
install "${C1}/.nizam" "${W}/ref001" >"${W}/001-upgrade.log" 2>&1; say "reinstall_rc=$?"
say "lock_after_reinstall=$([ -e "${C1}/.nizam/provenance.lock.json" ] && echo PRESERVED || echo LOST)"

say "== 002 target/reference overlap =="
# Sentinel lives INSIDE the project directory so replacement/deletion is observable.
run_overlap() { # $1 name $2 target $3 reference $4 project-dir (sentinel holder)
  mkdir -p "$4"; echo sentinel > "$4/SENTINEL.txt"
  install "$2" "$3" >"${W}/002-$1.log" 2>&1; rc=$?
  if [ -f "$4/SENTINEL.txt" ]; then s=intact; else s=DELETED; fi
  say "case=$1 install_rc=${rc} project_sentinel=${s} project_entries=[$(ls -A "$4" 2>/dev/null | tr '\n' ' ')]"
}
B=$(mktemp -d "${W}/o.XXXX")
run_overlap equal      "$B/eq/.nizam"      "$B/eq/.nizam"      "$B/eq"
run_overlap descendant "$B/de/.nizam"      "$B/de/.nizam/ref"  "$B/de"
run_overlap ancestor   "$B/an/proj/.nizam" "$B/an"             "$B/an/proj"
run_overlap disjoint   "$B/dj/proj/.nizam" "$B/dj/ref-sibling" "$B/dj/proj"

say "== 010 lock source_url attribution (checker) =="
python3 - "${REPO}" "${SHA}" <<'PY'
import json, sys
sys.path.insert(0, sys.argv[1] + "/tools")
import check_provenance_lock as c
sha = sys.argv[2]
pay = {"framework_version": "3.1.3", "tag": "v3.1.3", "resolved_sha": sha,
       "source_url": "https://github.com/niq-cnr/nizam-framework.git", "installed_at": "x"}
base = {"framework_version": "3.1.3", "tag": "v3.1.3", "resolved_sha": sha, "declared_range": ">=3.1.0,<4.0.0"}
cases = {
  "matching-url": dict(base, source_url="https://github.com/niq-cnr/nizam-framework.git"),
  "mismatched-url": dict(base, source_url="https://evil.example/fork.git"),
  "empty-url": dict(base, source_url=""),
  "null-url": dict(base, source_url=None),
  "missing-url": {k: v for k, v in base.items()},
}
for name, lock in cases.items():
    fails = c.check_lock(json.dumps(lock), json.dumps(pay))
    print(f"case={name} fails={fails or 'NONE (silent)'}")
PY
say "probe_workdir=${W}"
