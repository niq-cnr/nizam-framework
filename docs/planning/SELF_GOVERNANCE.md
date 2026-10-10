---
id: nizam-self-governance
title: "Nizam Framework — Self-Governance Commissioning"
description: "Versioned local adoption record for this repository's installed released governance."
version: 0.1.1
status: active
authoritative_source: docs/planning/SELF_GOVERNANCE.md
change_log:
  - version: "0.1.1"
    date: "2026-10-10"
    summary: "Complete self-commissioning at fixed source candidate bfd475ff670e582cbbfc8f3187ae988dcf3c8baa: actual successful CI 38075479048, clean installed preflight PASS, immutable v1.5.0/candidate baseline and independent nine-check QA/evidence gate passed. Later documentation HEAD does not replace the assessed source candidate."
  - version: "0.1.0"
    date: "2026-10-10"
    summary: "Record the authentic public v1.5.0 installation and agent routing; committed-candidate CI and clean preflight/baseline commissioning remain pending."
commissioning:
  repository: niq-cnr/nizam-framework
  local_scope:
    - niq-cnr/nizam-framework
  tag: v1.5.0
  resolved_sha: f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852
  authorization_gate: H-CONSUMER-UPGRADE
  status: commissioned
  candidate_sha: bfd475ff670e582cbbfc8f3187ae988dcf3c8baa
  evidence:
    identity: .agent/evidence/self-commission-v1.5.0/identity.json
    ci: .agent/evidence/self-commission-v1.5.0/ci.json
    preflight: .agent/reconciliation/self-commission-v1.5.0/preflight.json
    baseline: .agent/reconciliation/self-commission-v1.5.0/baseline.json
    drift: .agent/evidence/self-commission-v1.5.0/02-drift.txt
    payload: .agent/evidence/self-commission-v1.5.0/04-payload.txt
    qa: .agent/qa/self-commission-v1.5.0.json
  source_url: https://github.com/niq-cnr/nizam-framework.git
  installed_at: "2026-10-10T18:12:44Z"
---

# Local adoption and commissioning

The actual repository has installed and commissioned the public immutable `v1.5.0`
release under `.nizam/`. The assessed source candidate is
`bfd475ff670e582cbbfc8f3187ae988dcf3c8baa`: its actual successful CI, clean
installed preflight PASS, immutable baseline and independent nine-check QA all
passed. The evidence-capture gate passed before this completed record was written.

The operator's verbatim authorization was: "This the niq-cnr/nizam-framework
project must itself install and comission v1.5.0 of the nizam-framework itself."
The `H-CONSUMER-UPGRADE` decision was recorded at `2026-10-10T17:56:56Z` in
`.agent/run_state.json` and committed at `481a58a` before installation. Its scope
is this single repository. It authorizes local self-adoption without changing an
external organization registry or the historical phase-014 scope.

Bootstrap generated `.nizam/provenance.json` with the public source URL,
released commit, tag and actual installation timestamp above. The installation
contains 238 released files and that provenance record. The authored root
modules and root index remain the product source; [AGENTS.md](../../AGENTS.md)
routes local sessions through the installed index and skill.

The installation used these real commands:

```sh
bash bootstrap.sh --repo-url https://github.com/niq-cnr/nizam-framework.git --tag v1.5.0 --expected-sha f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852 --target .nizam
bash bootstrap.sh --verify-only --tag v1.5.0 --expected-sha f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852 --target .nizam
```

The standing `self_governance` CI job checks the complete installed file set,
every released file's bytes and Git executable bit, and the trusted provenance
pin. It rejects extra, missing, modified or non-regular files. Private-copy
adversarial checks exercise those failures, and the installed validator runs
with `--payload`. Bootstrap's verify-only check alone is insufficient to prove
complete byte equality.

Commissioning captured the real source candidate and CI reference outside the
repository, then ran the installed preflight against that clean committed checkout
with `--repo-root . --governance-root .nizam`. No new repository evidence was
written before the clean preflight and baseline capture finished. The baseline
records framework `v1.5.0` and source candidate `bfd475ff670e582cbbfc8f3187ae988dcf3c8baa`.
Later documentation commits preserve that assessed revision.

The [actual successful CI run](https://github.com/niq-cnr/nizam-framework/actions/runs/38075479048)
completed on 2026-10-10. Independent QA passed all nine checks at
`.agent/qa/self-commission-v1.5.0.json`; the command/exit-code evidence gate is
`.agent/evidence/self-commission-v1.5.0/evidence-gate.txt`. Original preflight and
baseline bytes are archived under `.agent/reconciliation/self-commission-v1.5.0/`.
The baseline retains its original temporary collection-log path;
`.agent/evidence/self-commission-v1.5.0/source-mapping.json` records the archived
log and content hashes without rewriting the historical baseline. No synthetic
self-fixture or fabricated audit establishes this commissioning.
