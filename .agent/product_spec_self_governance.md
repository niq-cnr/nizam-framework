# Self-governance commissioning proposal — v1.5.0

Proposal only. No implementation before independent Mode A and contract-review
approval. User explicitly authorizes niq-cnr/nizam-framework to adopt its own
released governance; this overrides its historical framework-outside-ecosystem
position for this repository only. No external scope registry is modified.

## Immutable installation and local scope

Install public released tag `v1.5.0`, peeled commit
`f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852`, using the real bootstrap CLI:

```sh
bash bootstrap.sh --repo-url https://github.com/niq-cnr/nizam-framework.git --tag v1.5.0 --expected-sha f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852 --target .nizam
bash bootstrap.sh --verify-only --tag v1.5.0 --expected-sha f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852 --target .nizam
```

Orchestrator first confirms public peeled tag SHA. Retain bootstrap-generated
provenance including genuine installed_at and public source_url. Commit 238
released payload files plus provenance: 22457 mechanical payload lines,
1216327 bytes. Never rewrite installed modules, templates or index for local
routing. Root canonical standard/templates/schema/tools/methodology/ecosystem and
root NIZAM.json remain identical to the final release-closeout base.

Root AGENTS.md routes future sessions FIRST to `.nizam/NIZAM.json`, then the
installed `.nizam/tools/SKILL.md` and only the required installed protocols.
Installed governance is the rules used to work here; root modules remain the
framework's authored product. Local scope is exactly niq-cnr/nizam-framework,
recorded in docs/planning/SELF_GOVERNANCE.md under the actual operator authorization.
Do not invent organization scope aliases, add ECOSYSTEM.json membership, copy
unfilled template scope assertions or require a nonexistent external scope repo.
No CONTEXT.md version bump is necessary; framework release anchors remain 1.5.0.

## Maintained deliverables

- AGENTS.md: NDS frontmatter, version 0.1.0, canonical root routing and local scope;
  contract gates, durable-state/evidence rules and immutable installed-payload rule.
- docs/planning/SELF_GOVERNANCE.md: versioned commissioning record (0.1.0 initial,
  0.1.1 completion) with operator authorization, public tag and full commit,
  generated provenance, candidate consumer commit, commands/evidence, local scope,
  exact distinction between installation, clean-state baseline and later audits.
- README.md: concise local self-governance section linking the commissioning record
  and naming installed entrypoints; retain current release/migration links.
- CHANGELOG.md: new Unreleased envelope-only self-adoption note; preserve every
  dated release section. No new version tag or framework-version changes.
- ROADMAP.md and operator_gates.md: bump their own document versions/change_logs,
  current self-commissioning disposition and a user-authorized H-CONSUMER-UPGRADE
  adoption record, preserving historical phase-014 and release evidence.
- .github/scripts/verify_self_governance.py: envelope-only verifier containing
  sole operational TAG/SHA/source URL constants, accepting --payload-dir for
  isolated adversarial verification. Compare exact installed file inventory and
  every file's bytes/executable mode to git ls-tree/cat-file at the immutable SHA;
  fail missing/extra/modified files, symlinks/special nodes, root symlink, bad/missing
  provenance, wrong source/tag/SHA/version/time format or missing git object.
  Provenance is the sole allowed installed file absent from the released tree.
  Confirm locally fetched tag peels to expected SHA; never derive the trusted pin
  from mutable provenance. Network-free verifier, clear nonzero failures.
- .github/scripts/test_self_governance.py: meaningful temporary-copy negative
  checks for changed bytes, missing/extra file, executable-mode drift, symlink,
  provenance wrong tag/SHA/source and missing provenance; original .nizam untouched.
- compliance.yml self_governance job reuses current exact checkout/setup-python
  action SHA pins, full history, persist-credentials false, installs existing
  jsonschema/pyyaml dependencies and runs verifier, adversarial checks and installed
  `bash .nizam/tools/validate.sh --payload`. Existing jobs stay intact.

## Real commissioning sequence and evidence

1. Orchestrator records user self-adoption decision before downstream records;
   final release-closeout plus decision commit is the immutable contract diff base.
2. Approved Generator installs payload, adds routing/checks/initial record and
   exact scoped docs. Independent Mode B checks source scope. Parent commits the
   implementation candidate and waits for actual self_governance CI green.
3. Evaluator runs the REAL installed preflight against that clean actual checkout,
   output under a validated temporary path outside the repo. Explicit supported
   flags: `--execution-id self-commission-v1.5.0 --repo-root . --governance-root
   .nizam --output-dir <temporary-run-root>/preflight --ci-run-file <actual-ci.json>`.
   No self-fixture, synthetic tag, fake repo or untracked tolerances. Require PASS
   exit 0. If dirty, fix the real tree/commit bookkeeping before rerunning.
4. CI reference JSON is independently fetched actual run URL/revision/timestamp
   and conclusion, never manufactured success. Baseline framework reference is
   v1.5.0 from installed provenance; repository reference is the candidate HEAD.
   Existing preflight CLI simultaneously emits baseline.json and collection-log.txt;
   validate the actual JSON against installed schemas. There is no separate
   ecosystem_baseline.py CLI and no Consumer Inputs requirement for these flags.
5. No engineering audit is fabricated for commissioning. The supported audit CLI
   is only a findings assembler; meaningful self-installation commissioning is
   established by exact inheritance, real CI and clean preflight/baseline. Any
   genuinely identified open finding is recorded as evidence and remediated through
   ordinary scoped work, rather than feeding empty fake PASS findings to the CLI.
6. Capture invocation/output/actual exit/SHA for every required command, preserve
   immutable preflight/baseline outputs under approved .agent evidence and
   reconciliation/reconciliation directories. CLI outputs may name absolute temporary
   collection-log path: retain originals unchanged; record artifact source-to-repo
   mapping and content hashes alongside copied logs, do not rewrite baseline fields.
7. Complete SELF_GOVERNANCE 0.1.1/current notices only after evaluator QA/evidence
   gate; approval covers this planned completion stage in the same bounded scope.
   Historical phase-014 tests and dossier remain unchanged. Parent commits closeout,
   merges clean PR and verifies actual standing CI; no release retagging.

Estimated maintained changes: 430 lines plus mechanically copied 22457 payload
lines and small genuine provenance; evidence excluded. No product feature changes.
Final proposal base is 481a58a17194438bb63b67acbfb85a84da740897 (release closeout
plus actual operator self-adoption decision). Contract status remains proposed until both gates approve.

AT6/7/10 are executable checks in the contract. Parent promotion includes the
planning/spec and contract/verdict artifacts; all evidence/data stays immutable.

## Final reviewed corrections (supersedes draft ordering)

Approved diff base: 481a58a17194438bb63b67acbfb85a84da740897, after actual release
closeout and recorded H-CONSUMER-UPGRADE authorization. No new gate is introduced.
Root SELF_GOVERNANCE frontmatter commissioning mapping contains repository,
local_scope (exact singleton niq-cnr/nizam-framework), tag, resolved_sha,
authorization_gate, status, candidate_sha and evidence. Initial 0.1.0 status
installed carries null candidate and no completed evidence; final 0.1.1 status
commissioned carries the fixed source candidate and authentic evidence paths,
including exact .agent/qa/self-commission-v1.5.0.json approved before completion.

Outside-first ordering is mandatory: commit installed source/initial routing/docs,
obtain actual successful candidate CI outside repo, and write identity.json outside
repo capturing candidate SHA. With the real candidate tree clean, run installed
preflight/baseline with output outside repo before any new in-repository evidence
write. Afterward archive original immutable bytes and CI/identity; final record
updates never redefine the candidate. AT6/AT10 compare captured candidate identity,
not later documentation HEAD. Preserve baseline absolute evidence reference plus
archived log content-hash/source mapping; never silently rewrite baseline fields.

Orchestrator may append self-commission history and update its contract/attempt/
completion coordination only. Preserve every existing history entry, unrelated
circuit counter and all frozen phase data. AT7 mechanically bounds these changes.
The installed verifier compares regular file type plus Git executable bit, not
raw group/owner write bits altered by umask. Reject symlinks and special nodes.
Use PYTHONDONTWRITEBYTECODE=1 for installed invocations and CI to avoid accidental
__pycache__ extras. No engineering audit is manufactured or required by this scope.
