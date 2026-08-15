#!/usr/bin/env bash
set -euo pipefail

framework_root="$(git rev-parse --show-toplevel)"
source_revision="$(git rev-parse HEAD)"
scratch_root="$(mktemp -d "${TMPDIR:-/tmp}/nizam-v1-migration.XXXXXX")"

cleanup() {
  case "${scratch_root}" in
    "${TMPDIR:-/tmp}"/nizam-v1-migration.*)
      [ -d "${scratch_root}" ] && rm -rf -- "${scratch_root}"
      ;;
    *)
      echo "REFUSE cleanup of unowned path: ${scratch_root}" >&2
      return 1
      ;;
  esac
}
trap cleanup EXIT

candidate_repo="${scratch_root}/framework"
consumer_root="${scratch_root}/consumer"
candidate_tag="v1.0.0-contract-candidate"

git clone --quiet --no-local --branch phase/012-v1-consumer-safety \
  "${framework_root}" "${candidate_repo}"
candidate_revision="$(git -C "${candidate_repo}" rev-parse HEAD)"
[ "${candidate_revision}" = "${source_revision}" ] || {
  echo "FAIL candidate clone revision differs from source" >&2
  exit 1
}
git -C "${candidate_repo}" config user.name "Nizam migration rehearsal"
git -C "${candidate_repo}" config user.email "rehearsal@example.invalid"
git -C "${candidate_repo}" tag -a "${candidate_tag}" \
  -m "scratch-only v1.0.0 contract candidate" HEAD
candidate_sha="$(git -C "${candidate_repo}" rev-parse "${candidate_tag}^{commit}")"
source_url="file://${candidate_repo}"

mkdir -p "${consumer_root}/.github/workflows"
git -C "${consumer_root}" init --quiet
printf '%s\n' '# Consumer context' 'consumer-owned: true' > "${consumer_root}/CONTEXT.md"
printf '%s\n' '# Consumer agents' 'consumer-owned: true' > "${consumer_root}/AGENTS.md"
printf '%s\n' 'name: consumer-ci' 'on: [push]' > "${consumer_root}/.github/workflows/consumer.yml"
before_hashes="$(sha256sum \
  "${consumer_root}/CONTEXT.md" \
  "${consumer_root}/AGENTS.md" \
  "${consumer_root}/.github/workflows/consumer.yml")"

bash "${framework_root}/bootstrap.sh" \
  --repo-url "${source_url}" \
  --tag v0.9.0 \
  --target "${consumer_root}/.nizam"
python3 - "${consumer_root}/.nizam/provenance.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    provenance = json.load(handle)
assert provenance["tag"] == "v0.9.0", provenance
print("PASS installed real v0.9.0 payload and recorded its provenance pin")
PY

bash "${framework_root}/bootstrap.sh" \
  --repo-url "${source_url}" \
  --tag "${candidate_tag}" \
  --target "${consumer_root}/.nizam"
bash "${framework_root}/bootstrap.sh" \
  --verify-only \
  --tag "${candidate_tag}" \
  --expected-sha "${candidate_sha}" \
  --target "${consumer_root}/.nizam"

after_hashes="$(sha256sum \
  "${consumer_root}/CONTEXT.md" \
  "${consumer_root}/AGENTS.md" \
  "${consumer_root}/.github/workflows/consumer.yml")"
[ "${before_hashes}" = "${after_hashes}" ] || {
  echo "FAIL bootstrap modified consumer-owned root or CI files" >&2
  exit 1
}
echo "PASS v0.9.0 -> local v1 contract candidate re-bootstrap verified"
echo "PASS consumer-owned CONTEXT.md, AGENTS.md, and CI configuration preserved"

(
  cd "${consumer_root}"
  bash .nizam/tools/validate.sh --payload
)

python3 - "${candidate_repo}" "${framework_root}" <<'PY'
import copy
import json
import subprocess
import sys
from pathlib import Path

import jsonschema

candidate_repo = Path(sys.argv[1])
framework_root = Path(sys.argv[2])

cases = (
    ("audit_delta_neg_bare_evidence_path.json", "audit_delta.schema.json"),
    ("engineering_finding_neg_bare_evidence_path.json", "engineering_finding.schema.json"),
    ("ecosystem_membership_neg_semver_trailing_dot.json", "ecosystem_membership.schema.json"),
    ("ecosystem_membership_neg_semver_empty_build.json", "ecosystem_membership.schema.json"),
    ("ecosystem_membership_neg_semver_dot_suffix.json", "ecosystem_membership.schema.json"),
    ("preflight_verdict_invalid_pass_blocking.json", "preflight_verdict.schema.json"),
    ("preflight_verdict_invalid_pass_with_exceptions_blocking.json", "preflight_verdict.schema.json"),
    ("membership_result_neg_consistent_missing_pin.json", "ecosystem_membership_result.schema.json"),
    ("membership_result_neg_consistent_null_pin.json", "ecosystem_membership_result.schema.json"),
    ("reconciliation_plan_neg_fail_missing_cycles.json", "reconciliation_plan.schema.json"),
    ("reconciliation_plan_neg_fail_nonempty_order.json", "reconciliation_plan.schema.json"),
)


def load_old_schema(name: str) -> dict:
    raw = subprocess.check_output(
        ["git", "-C", str(candidate_repo), "show", f"v0.9.0:schema/{name}"],
        text=True,
    )
    return json.loads(raw)


def repair(name: str, artifact: dict) -> dict:
    fixed = copy.deepcopy(artifact)
    if name == "audit_delta_neg_bare_evidence_path.json":
        fixed["transitions"]["new"][0]["evidence"][0]["path"] = \
            ".agent/evidence/migration/new-finding.txt"
    elif name == "engineering_finding_neg_bare_evidence_path.json":
        fixed["evidence"][0]["path"] = ".agent/evidence/migration/finding.txt"
    elif name.startswith("ecosystem_membership_neg_semver_"):
        fixed["schema_version"] = "1.2.3-rc.1+build.7"
    elif name.startswith("preflight_verdict_invalid_"):
        fixed.pop("blocking_findings", None)
    elif name.startswith("membership_result_neg_consistent_"):
        fixed["framework_pin"] = fixed["members"][0]["framework_pin"]
    elif name == "reconciliation_plan_neg_fail_missing_cycles.json":
        fixed["cycle_findings"] = ["packet-a -> packet-a"]
    elif name == "reconciliation_plan_neg_fail_nonempty_order.json":
        fixed["order"] = []
    else:
        raise AssertionError(f"no migration repair for {name}")
    return fixed


for fixture_name, schema_name in cases:
    artifact = json.loads(
        (framework_root / "tools" / "fixtures" / fixture_name).read_text(encoding="utf-8")
    )
    old_schema = load_old_schema(schema_name)
    new_schema = json.loads(
        (candidate_repo / "schema" / schema_name).read_text(encoding="utf-8")
    )
    jsonschema.validate(artifact, old_schema)
    try:
        jsonschema.validate(artifact, new_schema)
    except jsonschema.ValidationError:
        pass
    else:
        raise AssertionError(f"legacy artifact unexpectedly accepted by v1: {fixture_name}")
    jsonschema.validate(repair(fixture_name, artifact), new_schema)
    print(f"PASS legacy-accepted -> v1-rejected -> guide-repaired: {fixture_name}")

print(f"PASS migration matrix: {len(cases)}/{len(cases)} legacy artifacts repaired")
PY

echo "MIGRATION REHEARSAL PASS"
