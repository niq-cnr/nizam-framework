# v3.1.3 self-adoption evidence

Recorded 2026-11-03 for operator requests:

- `self install the latest nizam-framework.`
- `also install for agents/subagents`

## What was installed

| Target | Path | Result |
| --- | --- | --- |
| Framework self-adoption | `niq-cnr/nizam-framework` → `.nizam/` | v3.1.3 `f1935747…`, 341 released files + `provenance.json` |
| Hermes agent estate | `~/.hermes/.nizam` | v3.1.3 verified `content_integrity=verified` after removing two generated `.pyc` files |
| Pi agent estate | `~/.pi/agent/.nizam` | v3.1.3 verified `content_integrity=verified`, no drift |

The immutable pin is annotated tag `v3.1.3` → tag object `ba66c3e6c44bbb61204fe6193d5af2464c6c7825`,
commit `f19357479220b6bf2b3292d31c06c66279f91efa`, published 2026-10-29T19:02:23Z.

## Commands and captures

Install (framework checkout, unchanged bootstrap, network source):

```
bash bootstrap.sh --repo-url https://github.com/niq-cnr/nizam-framework.git \
  --tag v3.1.3 --expected-sha f19357479220b6bf2b3292d31c06c66279f91efa \
  --target /home/cnross/code/nizamiq/nizam-framework/.nizam \
  --git-repo /home/cnross/code/worktrees/framework-v313-release-reference.git
```

Captured in `bootstrap-install.stdout` / `.stderr`. Bootstrap identity against the tag is
recorded in `bootstrap-tag.sha256` and `bootstrap-local.sha256` (identical).

Commit-bound verification (`--verify-only --require-content-integrity`) and the installed
preflight capture live beside it:

- `bootstrap-verify.stdout` / `.stderr` — `PASS (content_integrity=verified)`
- `installed-preflight.stdout` / `.stderr` — `status: ready`, no failures
- `agent-estate-hermes-verify.*`, `agent-estate-hermes-preflight.*`
- `agent-estate-pi-verify.*`, `agent-estate-pi-preflight.*`

## Scope of the claim

Installed payload integrity, provenance and entrypoint readiness only. No commissioning,
consumer baseline, service activation or model-behaviour claim is made. The Pi estate
preflight reports `degraded` solely because its home directory is not a git work tree; the
payload itself is byte-exact and Pi lanes resolve git inside their worktrees.
