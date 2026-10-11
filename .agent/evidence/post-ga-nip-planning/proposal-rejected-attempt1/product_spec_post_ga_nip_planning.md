# Post-GA NIP planning — proposed documentation contract

## Authority and boundary

The operator's “proced with the logical next steps” authorizes the previously
proposed NIP3 revision and Workflow Assurance scope draft. It does not accept an
unseen NIP or activate a phase. This is standalone planning work outside the
completed phase014 budget. No numbered feature allocation or runtime work.

Scope baseline: 4663ab4dc39020f4d3226dc0f7e5016a835b4b04.
Recorded authorization/isolation head: 55ad2f4d3f183d296e87055430997fcc07ab8cb5.
Both independent pre-code gates must approve before any repository edits.

## NIP-0003 revision

Revise docs/nips/NIP-0003-live-runtime-sessions.md to remain proposed/pending H-NIP.
Replace only provisional future feature103–113 identities with110–120 and propagate
their dependencies/cross-references. Actual completed phase014 feature105 remains105:
its delivered fixture claim map is the current baseline; future authoring binding
was original provisional109 and becomes116. The new live-session CI job would
be the sixth job, alongside actual validate, e2e_bootstrap, fixtures_self_test,
convergent_review and self_governance; existing delivered CI is not deferred.

State actual phase014 completion/cancelled100/101, released public v1.5.0 pin
f749f4d47f3fb4fc2a447cdf8bdb3e7e5fede852, actual required isolation default and
current available SBCL (capture actual sbcl --version). Lack of native workstation
isolation is not absence of SBCL or absence of required capable CI.
Use historical102 dossier/current DEBT (only040/034 Open)/real commissioning and
maintenance evidence as inputs; do not invent F101 review or require its findings.

Preserve the baseline 13-case conformance table and four recorded operator
choices byte-for-byte except the documented old-provisional103–113 to110–120 shift
within the case table. Decision quotations are entirely unchanged. A dated
current-state overlay distinguishes updated premises from historical decision text.
New acceptance and implementation gates remain unmet.

## Proposed NIP-0004 Workflow Assurance

Create docs/nips/NIP-0004-workflow-assurance.md with schema-valid frontmatter,
status proposed, explicit H-NIP and future H-PHASE prerequisites. Scope the actual
Section7 outline without rewriting dated reconciliation history. Address:

- candidate identity (commit/tree/source digest, checkout identity) and invalidation
  when assessed source, contracts, inputs or tests change;
- stage-specific operator versus automated gates, verdict-to-transition mapping,
  blockers and evidence receipts (pending/running/pass/fail are not interchangeable);
- independent development/acceptance test ownership and red-before-repair evidence;
- routing, profile/permissions and parent-only coordinator ownership;
- dependency, conflict and concurrency boundaries, isolation/retry/rollback;
- staged policy decisions, actual unresolved choices, and a concrete acceptance
  matrix binding each proposed obligation to inputs/checks/evidence/negative controls.

Each topic is proposed design. Distinguish actual current behavior from future
requirements. No automatic policy acceptance, new reserved gate activation or
phase allocation; later acceptance/scoping/implementation require separate gates.
Existing WA drafting authority remains valid; it does not grant NIP acceptance.

## Current planning records

Own only backlog_dag.json, backlog_reconciliation.md, ROADMAP.md, HANDOVER.md,
operator_gates.md and Unreleased CHANGELOG beside the two NIPs. After actual
independent verification mark only authorized revision/drafting packets complete
(A03-RT, A03-WA-DRAFT, A03-WA-FINAL as genuinely delivered). Update only their
current scope/input/dependency/prerequisite facts and inverse edges where required;
do not mark PLAN-NEXT/PLAN-WA/NIP3 implementation or other proposal packets accepted
or complete. A03-RT editing restriction may reflect actual revision authorization,
while its prohibition on acceptance remains. Preserve other packet authority/status,
canonical feature mirrors, phase014/manifest/budgets and pending human gates.
Version changed docs accurately; current gate notes are informational, not decisions.

## Verification and lifecycle

Evaluator owns a NEW snapshot checker under .agent/evidence/post-ga-nip-planning/check_nip_planning.py.
Six exact commands in the contract check NIP3, WA, planning, scope, negative
controls and documentation/release/installed integrity. Checks read actual source
and immutable baseline, not future QA files. No circular closure or future-path
claims. Mark drafting delivered only after actual source review/checks; final QA
and completion are separate parent-owned artifacts, never prerequisites invented
inside NIP source. Preserve previous QA/evidence/checkers byte-for-byte.

Scope guard uses Git baseline diff and untracked names with exact product/task
allowlist. Parent may change only updated_at, active_contract_id, last_action,
append-only task history and task-prefixed bounded counters; all prior history,
other counters, phase/run-position/budget/gate-decision fields stay unchanged.

No installed changes, authored runtime/modules/index/context/version anchors,
DEBT records, phase feature/spec/YAML/manifest, historic dossiers or released
CHANGELOG sections. Preserve HANDOVER historical body and reconciliation dated
history. Any historical explanation needing correction uses a current overlay.
