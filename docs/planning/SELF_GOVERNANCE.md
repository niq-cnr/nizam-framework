---
id: nizam-self-governance
title: "Nizam Framework — Self-Governance Commissioning"
description: "Versioned local adoption record for this repository's installed released governance."
version: 0.9.0
status: active
authoritative_source: docs/planning/SELF_GOVERNANCE.md
change_log:
  - version: "0.9.0"
    date: "2026-10-24"
    summary: "Record the official v2.0.0 installation at 603afc7b17919334a6a01df1e39e63798d9d0acd, verified against annotated tag object 4aa4b1be73b1131b1227528465981a15815c44d7; retain prior released installation and commissioning histories."
  - version: "0.8.0"
    date: "2026-10-23"
    summary: "Record the v1.11.0 installation from observed facts: stage installed, commissioning not performed (316 released files + provenance.json at 6fc683580941adf19860d9d9d00fdc81d38d8088, installed_at 2026-10-23T01:21:26Z), verified byte-for-byte against the v1.11.0 tag (annotated tag object 5b09fc0b179ff4f06ea4aec7878a34170654ade6). The v1.10.1, v1.10.0, v1.9.0, v1.8.0, v1.7.0, v1.6.0 and v1.5.0 installation records below are retained unchanged as history."
  - version: "0.7.0"
    date: "2026-10-19"
    summary: "Record the v1.10.1 installation from observed facts: stage installed, commissioning not performed (278 released files + provenance.json at 2b6a4af4d1667aad89cfaab4b1799cb8c9beb9fd, installed_at 2026-10-19T11:03:39Z). The v1.10.0, v1.9.0, v1.8.0, v1.7.0, v1.6.0, and v1.5.0 installation records below are retained unchanged as history."
  - version: "0.6.0"
    date: "2026-10-19"
    summary: "Record the v1.10.0 installation from observed facts: stage installed, commissioning not performed (278 released files + provenance.json at 6a4afd21eebeb6a11ae40ff533293d3cdbbaadd7, installed_at 2026-10-19T07:56:18Z). The v1.9.0, v1.8.0, v1.7.0, v1.6.0, and v1.5.0 installation records below are retained unchanged as history."
  - version: "0.5.0"
    date: "2026-10-18"
    summary: "Record the v1.9.0 installation from observed facts: stage installed, commissioning not performed (278 released files + provenance.json at 0c9b1c5979a922c75499e0bfe4d9dbf9524f717d, installed_at 2026-10-18T22:32:25Z). The v1.8.0, v1.7.0, v1.6.0, and v1.5.0 installation records below are retained unchanged as history."
  - version: "0.4.1"
    date: "2026-10-18"
    summary: "Clarify the release-tag vs. self-adoption ordering (V6): a tag's consumer payload is the six authored root modules plus root NIZAM.json copied by bootstrap.sh, whereas the repository's .nizam/ directory at tag creation time holds the prior self-installed release until a subsequent self-adoption commit re-bootstraps .nizam/; note shared tools/payload_integrity.py verification across verify_self_governance.py and bootstrap.sh --verify-only (V3)."
  - version: "0.4.0"
    date: "2026-10-18"
    summary: "Record the v1.8.0 installation from observed facts: stage installed, commissioning not performed (277 released files + provenance.json at 606d11ee84deff0d3b7934cbfd715223d64ac79d, installed_at 2026-10-18T13:12:27Z). The v1.7.0, v1.6.0, and v1.5.0 installation records below are retained unchanged as history."
  - version: "0.3.0"
    date: "2026-10-18"
    summary: "Record the v1.7.0 installation from observed facts: stage installed, commissioning not performed (277 released files + provenance.json at 47851d857e0ab879b848610128ee6e9e13368f0d, installed_at 2026-10-18T09:49:41Z). The v1.6.0 and v1.5.0 installation records below are retained unchanged as history."
  - version: "0.2.0"
    date: "2026-10-17"
    summary: "Record the v1.6.0 installation from observed facts: stage installed, commissioning not performed. The v1.5.0 installation record below is retained unchanged as history."
  - version: "0.1.1"
    date: "2026-10-10"
    summary: "Complete self-commissioning at fixed source candidate bfd475ff670e582cbbfc8f3187ae988dcf3c8baa: actual successful CI 38075479048, clean installed preflight PASS, immutable v1.5.0/candidate baseline and independent nine-check QA/evidence gate passed. Later documentation HEAD does not replace the assessed source candidate."
  - version: "0.1.0"
    date: "2026-10-10"
    summary: "Record the authentic public v1.5.0 installation and agent routing; committed-candidate CI and clean preflight/baseline commissioning remain pending."
installation:
  repository: niq-cnr/nizam-framework
  local_scope:
  - niq-cnr/nizam-framework
  tag: v2.0.0
  resolved_sha: 603afc7b17919334a6a01df1e39e63798d9d0acd
  framework_version: 2.0.0
  tag_object: 4aa4b1be73b1131b1227528465981a15815c44d7
  authorization_gate: H-CONSUMER-UPGRADE
  authorization_recorded_at: '2026-10-24T05:45:10.322666+00:00'
  authorization_verbatim: self install the latest nizam-framework code.
  status: installed
  commissioning_performed: false
  payload_file_count: 316
  source_url: https://github.com/niq-cnr/nizam-framework.git
  installed_at: '2026-10-24T05:45:45Z'
  evidence:
    authorization: .agent/evidence/release-v2.0.0-closeout/upgrade-authorization.json
    release: .agent/evidence/release-v2.0.0-closeout/release-facts.json
    bootstrap_install: .agent/evidence/release-v2.0.0-closeout/bootstrap-install.stdout
    verify_self_governance: .agent/evidence/release-v2.0.0-closeout/installed-integrity.stdout
    bootstrap_verify_only: .agent/evidence/release-v2.0.0-closeout/bootstrap-verify.stdout
    installed_preflight: .agent/evidence/release-v2.0.0-closeout/installed-preflight.stdout
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

# Current installation — `v2.0.0` (installed — commissioning not performed)

The operator authorized release publication and requested: “self install the latest
nizam-framework code.” The unchanged `bootstrap.sh` installed the published
immutable `v2.0.0` tag at `603afc7b17919334a6a01df1e39e63798d9d0acd` from the canonical repository
`https://github.com/niq-cnr/nizam-framework.git`. The annotated tag object is
`4aa4b1be73b1131b1227528465981a15815c44d7`. Installation completed at `2026-10-24T05:45:45Z`.

The installation contains **316 released files plus genuine provenance**.
The external trusted pin verifier and commit-bound bootstrap verification passed
with exact inventory, content and executable-mode comparisons. The installed
high-risk preflight returned `ok:true`, `sandbox_operational:true` and no failures.
These observations establish installation integrity; **commissioning was not
performed**. The already tested release payload was copied without runtime edits.

The release workflow succeeded and the GitHub Release was published at
`2026-10-24T05:44:48Z`. The local source snapshot used before this official
release remains preserved on its private historical branch; its local tag was
never published or substituted for this release.

Evidence: `.agent/evidence/release-v2.0.0-closeout/`. All prior released
installation and commissioning records remain below as historical records.

# Prior installation — `v1.11.0` (installed — commissioning not performed)

This repository has installed the public immutable `v1.11.0` release under
`.nizam/`. The stage is **installed — commissioning not performed**. Its machine
values are `installation.status: installed` and
`installation.commissioning_performed: false`. The clean installed preflight,
baseline and independent QA that completed the `v1.5.0` commissioning have not
been performed for `v1.11.0`.

The pin is tag `v1.11.0` (annotated tag object
`5b09fc0b179ff4f06ea4aec7878a34170654ade6`), resolved commit
`6fc683580941adf19860d9d9d00fdc81d38d8088`, installed at
`2026-10-23T01:21:26Z` as recorded in `.nizam/provenance.json`. The installation
contains 316 released files and that provenance record.

Because an immutable Git tag cannot contain a commit created after the tag is
cut, the repository's `.nizam/` directory in the `v1.11.0` tag tree holds the
prior self-installed release (`v1.10.1`). A release tag's consumer payload is
always the six authored root modules (`standard/`, `methodology/`, `templates/`,
`schema/`, `tools/`, `ecosystem/`) plus root `NIZAM.json` copied by
`bootstrap.sh`, never the tagged tree's `.nizam/` directory. After the tag was
published, this separate self-adoption commit re-ran `bootstrap.sh` against that
published tag to update this repository's `.nizam/`.

The operator authorization is gate `H-CONSUMER-UPGRADE`, recorded in
`.agent/run_state.json` for this self-adoption. The operator's instructions were:
"Prepare the project for the next release. - self install. - update the version
references ready for tagging." under the session's existing manage/triage/merge
authority. The authorization covers local installation for this single
repository.

The installation was verified against the tag: the payload trees are identical
to the tag, and `verify_self_governance.py`, its drift test, `validate.sh
--payload` and `bootstrap.sh --verify-only` all exited 0. Captures:
`.agent/evidence/release-v1.11.0-closeout/bootstrap-install.txt`,
`verify-self-governance.txt`, `test-self-governance.txt`,
`payload-validate.txt` and `bootstrap-verify-only.txt` in the same directory.

> **Historical record — the `v1.10.1` installation, retained unchanged below. It does not describe the current installation.**

# Prior installation — `v1.10.1` (installed — commissioning not performed)

This repository has installed the public immutable `v1.10.1` release under
`.nizam/`. The stage is **installed — commissioning not performed**. Its machine
values are `installation.status: installed` and
`installation.commissioning_performed: false`. The clean installed preflight,
baseline and independent QA that completed the `v1.5.0` commissioning have not been
performed for `v1.10.1`.

The pin is tag `v1.10.1` (annotated tag object `5b6fdb64a5bc3bf1def755b8269696d9e95b3a41`),
resolved commit `2b6a4af4d1667aad89cfaab4b1799cb8c9beb9fd`, installed at
`2026-10-19T11:03:39Z` as recorded in `.nizam/provenance.json`. The installation
contains 278 released files and that provenance record.

Because an immutable Git tag cannot contain a commit created after the tag is
cut, the repository's `.nizam/` directory at any release tag `vX.Y.Z` holds the
prior self-installed release (`v1.10.0` inside the `v1.10.1` tag tree, `v1.9.0` inside
the `v1.10.0` tag tree). A release tag's consumer payload is always the six authored
root modules (`standard/`, `methodology/`, `templates/`, `schema/`, `tools/`,
`ecosystem/`) plus root `NIZAM.json` copied by `bootstrap.sh`, never the tagged
tree's `.nizam/` directory. After the tag is published, a separate self-adoption
commit runs `bootstrap.sh` against that published tag to update this repository's
`.nizam/`.

The operator authorization is gate `H-CONSUMER-UPGRADE`, recorded in
`.agent/run_state.json` at `2026-10-19T06:00:00Z` before the re-bootstrap ran. The
operator's verbatim instructions were: "Reuse existing session authorization for
concrete commits, merges, releases, and this repository's supported self-adoption."
The authorization covers local installation for this single repository.

The installation was verified against the tag: the payload trees are identical to
the tag, and `verify_self_governance.py`, its drift tests, `validate.sh --payload`
and `bootstrap.sh --verify-only` (which shares `tools/payload_integrity.py` with
`verify_self_governance.py` and never executes code from inside `.nizam/`) all exited 0. Captures:
`.agent/evidence/release-v1.10.1-closeout/bootstrap-install.txt`,
`verify-self-governance.txt`, `test-self-governance.txt`,
`payload-validate.txt` and `bootstrap-verify-only.txt`
in the same directory.

> **Historical record — the `v1.10.0` installation, retained unchanged below. It does not describe the current installation.**

# Prior installation — `v1.10.0` (installed — commissioning not performed)

This repository has installed the public immutable `v1.10.0` release under
`.nizam/`. The stage is **installed — commissioning not performed**. Its machine
values are `installation.status: installed` and
`installation.commissioning_performed: false`. The clean installed preflight,
baseline and independent QA that completed the `v1.5.0` commissioning have not been
performed for `v1.10.0`.

The pin is tag `v1.10.0` (annotated tag object `8971603d2091fd5f5602f556b49499a0c8aa7a29`),
resolved commit `6a4afd21eebeb6a11ae40ff533293d3cdbbaadd7`, installed at
`2026-10-19T07:56:18Z` as recorded in `.nizam/provenance.json`. The installation
contains 278 released files and that provenance record.

Because an immutable Git tag cannot contain a commit created after the tag is
cut, the repository's `.nizam/` directory at any release tag `vX.Y.Z` holds the
prior self-installed release (`v1.9.0` inside the `v1.10.0` tag tree, `v1.8.0` inside
the `v1.9.0` tag tree). A release tag's consumer payload is always the six authored
root modules (`standard/`, `methodology/`, `templates/`, `schema/`, `tools/`,
`ecosystem/`) plus root `NIZAM.json` copied by `bootstrap.sh`, never the tagged
tree's `.nizam/` directory. After the tag is published, a separate self-adoption
commit runs `bootstrap.sh` against that published tag to update this repository's
`.nizam/`.

The operator authorization is gate `H-CONSUMER-UPGRADE`, recorded in
`.agent/run_state.json` at `2026-10-19T06:00:00Z` before the re-bootstrap ran. The
operator's verbatim instructions were: "Reuse existing session authorization for
concrete commits, merges, releases, and this repository's supported self-adoption."
The authorization covers local installation for this single repository.

The installation was verified against the tag: the payload trees are identical to
the tag, and `verify_self_governance.py`, its drift tests, `validate.sh --payload`
and `bootstrap.sh --verify-only` (which shares `tools/payload_integrity.py` with
`verify_self_governance.py` and never executes code from inside `.nizam/`) all exited 0. Captures:
`.agent/evidence/release-v1.10.0-closeout/00a-reinstall-tree-identity.txt`,
`00b-reinstall-verify-self-governance.txt`, `00c-reinstall-test-self-governance.txt`,
`00d-reinstall-payload-validate.txt` and `00e-reinstall-bootstrap-verify-only.txt`
in the same directory.

> **Historical record — the `v1.9.0` installation, retained unchanged below. It does not describe the current installation.**

# Prior installation — `v1.9.0` (installed — commissioning not performed)

This repository has installed the public immutable `v1.9.0` release under
`.nizam/`. The stage is **installed — commissioning not performed**. Its machine
values are `installation.status: installed` and
`installation.commissioning_performed: false`. The clean installed preflight,
baseline and independent QA that completed the `v1.5.0` commissioning have not been
performed for `v1.9.0`.

The pin is tag `v1.9.0` (annotated tag object `7e721b6e0fb2a0a3014efda388e1097378e3da87`),
resolved commit `0c9b1c5979a922c75499e0bfe4d9dbf9524f717d`, installed at
`2026-10-18T22:32:25Z` as recorded in `.nizam/provenance.json`. The installation
contains 278 released files and that provenance record.

Because an immutable Git tag cannot contain a commit created after the tag is
cut, the repository's `.nizam/` directory at any release tag `vX.Y.Z` holds the
prior self-installed release (`v1.8.0` inside the `v1.9.0` tag tree, `v1.7.0` inside
the `v1.8.0` tag tree). A release tag's consumer payload is always the six authored
root modules (`standard/`, `methodology/`, `templates/`, `schema/`, `tools/`,
`ecosystem/`) plus root `NIZAM.json` copied by `bootstrap.sh`, never the tagged
tree's `.nizam/` directory. After the tag is published, a separate self-adoption
commit runs `bootstrap.sh` against that published tag to update this repository's
`.nizam/`.

The operator authorization is gate `H-CONSUMER-UPGRADE`, recorded in
`.agent/run_state.json` at `2026-10-18T16:40:00Z` before the re-bootstrap ran. The
operator's verbatim instructions were: "Where the session already authorizes a
concrete commit, merge, release, or self-upgrade, use that authority without
requesting it again." and "This project, itself the nizam-framework project, should
also adopt this new latest release." The authorization covers local installation for
this single repository.

The installation was verified against the tag: the payload trees are identical to
the tag, and `verify_self_governance.py`, its drift tests, `validate.sh --payload`
and `bootstrap.sh --verify-only` (which shares `tools/payload_integrity.py` with
`verify_self_governance.py` whenever the reference tree is reachable) all exited 0. Captures:
`.agent/evidence/release-v1.9.0-closeout/00a-reinstall-tree-identity.txt`,
`00b-reinstall-verify-self-governance.txt`, `00c-reinstall-test-self-governance.txt`,
`00d-reinstall-payload-validate.txt` and `00e-reinstall-bootstrap-verify-only.txt`
in the same directory.

> **Historical record — the `v1.8.0` installation, retained unchanged below. It does not describe the current installation.**

# Prior installation — `v1.8.0` (installed — commissioning not performed)

This repository has installed the public immutable `v1.8.0` release under
`.nizam/`. The stage is **installed — commissioning not performed**. Its machine
values are `installation.status: installed` and
`installation.commissioning_performed: false`. The clean installed preflight,
baseline and independent QA that completed the `v1.5.0` commissioning have not been
performed for `v1.8.0`.

The pin is tag `v1.8.0` (annotated tag object `faeb50dfdb055cc4d5018ab8d474979be71f876f`),
resolved commit `606d11ee84deff0d3b7934cbfd715223d64ac79d`, installed at
`2026-10-18T13:12:27Z` as recorded in `.nizam/provenance.json`. The installation
contains 277 released files and that provenance record.

Because an immutable Git tag cannot contain a commit created after the tag is
cut, the repository's `.nizam/` directory at any release tag `vX.Y.Z` holds the
prior self-installed release (`v1.7.0` inside the `v1.8.0` tag tree). A release
tag's consumer payload is always the six authored root modules (`standard/`,
`methodology/`, `templates/`, `schema/`, `tools/`, `ecosystem/`) plus root
`NIZAM.json` copied by `bootstrap.sh`, never the tagged tree's `.nizam/`
directory. After the tag is published, a separate self-adoption commit runs
`bootstrap.sh` against that published tag to update this repository's `.nizam/`.

The operator authorization is gate `H-CONSUMER-UPGRADE`, recorded in
`.agent/run_state.json` at `2026-10-18T12:40:00Z` before the re-bootstrap ran. The
operator's verbatim instructions were: "Use merge, release, self-upgrade, and other
external-action authority already granted in the session." and "This project, itself
the nizam-framework project, should also adopt this new latest release." The
authorization covers local installation for this single repository.

The installation was verified against the tag: the payload trees are identical to
the tag, and `verify_self_governance.py`, its drift tests, `validate.sh --payload`
and `bootstrap.sh --verify-only` (which shares `tools/payload_integrity.py` with
`verify_self_governance.py` whenever the reference tree is reachable) all exited 0. Captures:
`.agent/evidence/release-v1.8.0-closeout/00a-reinstall-tree-identity.txt`,
`00b-reinstall-verify-self-governance.txt`, `00c-reinstall-test-self-governance.txt`,
`00d-reinstall-payload-validate.txt` and `00e-reinstall-bootstrap-verify-only.txt`
in the same directory.

> **Historical record — the `v1.7.0` installation, retained unchanged below. It does not describe the current installation.**

# Prior installation — `v1.7.0` (installed — commissioning not performed)

This repository has installed the public immutable `v1.7.0` release under
`.nizam/`. The stage is **installed — commissioning not performed**. Its machine
values are `installation.status: installed` and
`installation.commissioning_performed: false`. The clean installed preflight,
baseline and independent QA that completed the `v1.5.0` commissioning have not been
performed for `v1.7.0`.

The pin is tag `v1.7.0` (annotated tag object `6a4cf599f3850ae31561ba38f9da29237d0a4a53`),
resolved commit `47851d857e0ab879b848610128ee6e9e13368f0d`, installed at
`2026-10-18T09:49:41Z` as recorded in `.nizam/provenance.json`. The installation
contains 277 released files and that provenance record.

The operator authorization is gate `H-CONSUMER-UPGRADE`, recorded in
`.agent/run_state.json` at `2026-10-18T09:28:00Z` before the re-bootstrap ran. The
operator's verbatim instructions were: "Once the PR merges prepare the current
build as the next release then tag/pin/release this as the latest verison." and
"This project, itself the nizam-framework project, should also adopt this new
latest release." The authorization covers local installation for this single
repository.

The installation was verified against the tag: the payload trees are identical to
the tag, and `verify_self_governance.py`, its drift tests, `validate.sh --payload`
and `bootstrap.sh --verify-only` all exited 0. Captures:
`.agent/evidence/release-v1.7.0-closeout/00a-reinstall-tree-identity.txt`,
`00b-reinstall-verify-self-governance.txt`, `00c-reinstall-test-self-governance.txt`,
`00d-reinstall-payload-validate.txt` and `00e-reinstall-bootstrap-verify-only.txt`
in the same directory.

> **Historical record — the `v1.6.0` installation, retained unchanged below. It does not describe the current installation.**

# Prior installation — `v1.6.0` (installed — commissioning not performed)

This repository has installed the public immutable `v1.6.0` release under
`.nizam/`. The stage is **installed — commissioning not performed**. Its machine
values are `installation.status: installed` and
`installation.commissioning_performed: false`. The clean installed preflight,
baseline and independent QA that completed the `v1.5.0` commissioning have not been
performed for `v1.6.0`. Commissioning of `v1.6.0` is not authorized by any decision
recorded here.

The pin is tag `v1.6.0`, resolved commit `4e7db5a47d753555abd4d724c5d16f2b5eb86c3e`,
installed at `2026-10-17T06:06:58Z` as recorded in `.nizam/provenance.json`. The
installation contains 276 released files and that provenance record.

The operator authorization is gate `H-CONSUMER-UPGRADE`, recorded in
`.agent/run_state.json` at `2026-10-17T18:25:00Z`. The operator's verbatim text
was: "instell the latest release of the nizam-framework into thei project,
https://github.com/niq-cnr/nizam-framework/releases ." The authorization covers
installation only, for this single repository. Ordering is disclosed: the
re-bootstrap was prepared on PR #114 (commits `9a830aa4` and `05c070b4`) before this
authorization was recorded, and the decision ratifies that prepared installation;
it is not back-dated.

Before the decision was recorded the installation was re-verified against the tag:
the payload trees are identical to the tag, and `verify_self_governance.py`, its
drift tests, `validate.sh --payload` and `bootstrap.sh --verify-only` all exited 0.
Captures: `.agent/evidence/release-v1.6.0-closeout/00a-reinstall-tree-identity.txt`,
`00b-reinstall-verify-self-governance.txt`, `00c-reinstall-test-self-governance.txt`,
`00d-reinstall-payload-validate.txt` and `00e-reinstall-bootstrap-verify-only.txt`
in the same directory.

> **Historical record — the `v1.5.0` installation and its completed commissioning, retained unchanged below. It does not describe the current installation.**

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
