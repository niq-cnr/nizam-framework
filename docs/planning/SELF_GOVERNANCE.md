---
id: nizam-self-governance
title: "Nizam Framework — Self-Governance Commissioning"
description: "Versioned local adoption record for this repository's installed released governance."
version: 0.1.0
status: active
authoritative_source: docs/planning/SELF_GOVERNANCE.md
change_log:
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
  status: installed
  candidate_sha: null
  evidence: {}
  source_url: https://github.com/niq-cnr/nizam-framework.git
  installed_at: "2026-10-10T18:12:44Z"
---

# Local adoption and commissioning

The actual repository has installed the public immutable `v1.5.0` release under
`.nizam/`. Commissioning is pending a committed source candidate, its successful
CI run, and a real clean installed preflight with an immutable baseline. The
structured record above distinguishes installation from completed commissioning.

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

Commissioning captures the actual source candidate and real successful CI
reference outside the repository, then runs the installed preflight against that
clean committed checkout with `--repo-root . --governance-root .nizam`. Outputs
remain outside the repository until clean preflight and baseline capture finish.
The final record will reference that fixed source candidate, immutable archived
outputs, and passing independent QA even if a later documentation commit advances
HEAD. No synthetic self-fixture or fabricated audit establishes commissioning.
