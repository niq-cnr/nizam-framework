---
id: convergent-automated-code-review
title: "Convergent Automated Code Review"
description: "Defines prior-ledger-first, authenticated three-trial code review whose lifecycle, verdict, rendering, and replay integrity are owned by deterministic code."
version: 1.3.0
status: active
authoritative_source: standard/convergent_code_review.md
change_log:
  - version: "1.3.0"
    date: "2026-09-17"
    summary: "Reconcile mode-only deltas, controlled Git reads, commit parsing, sandbox and no-follow I/O, publication state, and standalone-ledger initial-head and exact current-consensus evidence guarantees."
  - version: "1.2.0"
    date: "2026-09-17"
    summary: "Add a trusted Git-object packet builder and full-tree commitment, authenticated old bytes, the mandatory schema-plus-relational validity contract, strict slash-only identities, enforceable trial sandbox adapters, no-follow replay reads, and atomic no-replace publication."
  - version: "1.1.0"
    date: "2026-09-17"
    summary: "Authenticate the complete review universe and evidence, permit new consensus findings in later reviews, preserve symbol case, define safe paths, isolated trials, revert and rename semantics, canonical JSON, and transactional publication."
---

# Convergent Automated Code Review

## 1. Purpose and Trust Boundary

This standard defines a runtime-neutral review protocol that can use any model or review agent without delegating review state or merge authority to that model. A model is an **observation-only sensor**: it may report an active candidate or a resolution observation with evidence. It MUST NOT assign trusted finding identifiers, lifecycle states, counts, suppressions, or verdicts. Deterministic code MUST validate inputs and MUST own semantic fingerprints, lifecycle transitions, counts, the final verdict, Markdown rendering, the embedded ledger, and replay verification.

The normative implementation is `tools/convergent_review.py`. Its artifact contracts are `schema/review_packet.schema.json`, `schema/review_trial.schema.json`, `schema/review_ledger.schema.json`, `schema/review_suppression.schema.json`, and `schema/review_replay.schema.json`.

## 2. Authenticated Scope

Packets MUST be produced from immutable repository objects by a trusted builder such as `convergent_review.py build-packet`, not assembled by the model under review. Every packet contains a `review_files` array. Each entry names a repository-relative path and carries current-head UTF-8 text plus its SHA-256 `content_digest`. A deleted path is represented by a `null` content tombstone whose digest is SHA-256 of zero bytes. The deterministic engine verifies each content digest. This array, rather than ambient repository access, is the authenticated review universe.

The `delta` array records each changed path's old and new content digest, old and new Git mode, **and the exact old UTF-8 content whenever the old digest is non-null**. Old content is hashed and authenticated before a trial can inspect it; a trial can therefore distinguish an introduced change from pre-existing code. Digest, mode, and content presence MUST agree for each side. Both digests cannot be null. The old and new `(digest, mode)` pairs MUST differ, so equal digests are valid only for an authenticated mode-only change such as an executable-bit transition. Paths cannot repeat. A non-null new digest MUST equal the matching `review_files` digest. A deleted delta path MUST have a matching absence tombstone, which makes a true deletion or full revert representable as current-head evidence.

### 2.1 Ordinary review

Ordinary review is **prior-ledger first**. When a previous reviewed head exists, its ledger is loaded before new observations are converged. Existing findings are tracked regardless of whether changed lines still expose them to a model. New discovery is limited to paths in the packet's delta. A new candidate on an unchanged path is invalid input.

A prior ledger's `head_sha` MUST equal the new packet's `base_sha`. Every packet, trial, ledger, and replay record MUST bind the exact current `head_sha`; stale-head input fails closed. A later review can still discover a genuinely new issue: a candidate absent from the prior ledger becomes `new` when at least two current trials report it active within ordinary delta scope.

### 2.2 Full audit

Whole-tree discovery requires an explicit human choice of `mode: full_audit`. A full-audit packet MUST carry `scope_commitment`: the exact Git commit content whose object ID equals `head_sha`, its root tree ID, a canonical complete flat tree manifest with Git modes and blob object IDs, and the manifest SHA-256. The engine reconstructs the Git tree object, authenticates the commit-to-tree link, binds every manifest blob to `review_files`, and requires the manifest paths to equal the complete set of present review files. Commit-to-tree validation parses only the commit header block before the first blank line and requires exactly one `tree <root_tree>` header; message text beginning with `tree ` is inert, while a second tree header fails closed. Omitting an arbitrary file therefore fails closed. An empty full-audit universe passes only when the authenticated head commit points to the real empty Git tree. Full audit does not weaken consensus, evidence, suppression, replay, or current-head rules. A model cannot select or infer this mode.

The trusted builder MUST invoke Git with a controlled allowlisted environment that discards inherited repository-redirection variables and disables replace refs through the command line, configuration, and `GIT_NO_REPLACE_OBJECTS`. Base/head resolution, diffs, trees, commits, and blobs therefore name the immutable object database selected by the explicit repository argument. A successful tree lookup with no record means that a path is absent; a non-zero Git command or blob-read failure is an error and MUST NOT be converted into an absence tombstone.

## 3. Safe Identities and Canonical Encoding

Repository identities contain two or more slash-separated segments and may represent subgroups such as `host/org/team/repo` or scoped names such as `registry/@scope/package`. Repository-relative paths may contain spaces and Unicode. Runtime and schemas reject **backslash anywhere**, absolute paths, Windows drive roots, empty segments, `.` and `..` segments, repeated separators, NUL, and both C0/DEL and C1 control characters.

Packet validity is a two-stage contract: (1) `review_packet.schema.json` enforces the closed structural shape and local constraints; (2) the mandatory `validate_packet_relations` contract enforces projected path uniqueness, sibling digest inequality, content/digest equality, and full-tree commitments. Draft 2020-12 cannot express those cross-item and sibling-value relations under this representation. A consumer MUST run both stages and MUST NOT describe plain JSON Schema validation alone as packet validity.

Every packet, trial, prior ledger, suppression record, ledger output, and replay manifest MUST use canonical UTF-8 JSON: Unicode text is emitted directly, object keys are sorted, separators are compact, and one trailing line feed is present. Duplicate JSON keys and noncanonical input bytes fail closed. The exact canonical packet bytes are hashed to bind all three trials.

## 4. Stable Semantic Identity

A finding fingerprint is the SHA-256 digest of canonical JSON over `repository`, `path`, `symbol`, `category`, and `rule`. Presentation text, severity, evidence excerpts, and line numbers are deliberately excluded. Category and rule tokens are already constrained lowercase. Repository, path, and symbol preserve exact case because they can be case-sensitive; `Foo` and `foo` are distinct symbols. Whitespace runs inside a symbol are normalized to one space, but case is never folded.

A line shift or rewritten explanation does not create a new finding. Changing the affected symbol, path, category, rule, or repository does. The CLI MUST recalculate every fingerprint. Raw trials contain no trusted identifier or model-owned count.

## 5. Three Independent Trials

Every convergence run consumes **exactly three** trial documents, numbered 1, 2, and 3. Each is bound to the exact packet digest and current head. A workspace, `cwd`, or `HOME` change alone is **not isolation**. Each trial MUST run through a trusted sandbox adapter that creates a separate process session and enforces: no network connectivity; a private PID/session boundary; read/write but **no execute** access inside that trial's root; read/execute access only to the pre-resolved trusted runner and required runtime; and no access to sibling trial roots, ambient repository files, or prior-trial artifacts. A runner-generated file remains non-executable even if the runner sets its executable mode bit. The evaluator's adapter protocol is `ADAPTER --root TRIAL_ROOT --runner RUNNER -- RUNNER_ARGUMENTS...`. `tools/linux_trial_sandbox.sh` plus `tools/isolated_trial_adapter.py` is the Linux reference implementation using user/network/IPC/UTS/PID namespaces and Landlock. Other runtimes may supply an equivalent container, VM, seatbelt, or capability sandbox adapter, but fail closed if the boundary cannot be enforced.

The evaluator MUST use trust-anchored, component-by-component no-follow I/O for per-trial packet, prompt, optional prior ledger, trial output, and captured stdout/stderr files. Inputs are re-read after the runner exits, output files MUST be singly linked regular files, and evaluator-created files MUST use exclusive creation. Runner substitution by a symlink, hard link, FIFO, pre-created output name, or rewritten trusted input therefore fails before convergence.

A candidate absent from the prior ledger becomes `new` only when at least two trials independently report it active. This rule applies on initial and later reviews. A singleton candidate is rejected as non-consensus. Matching observations are grouped by recalculated fingerprint. Evidence is de-duplicated and sorted. The most severe current report wins; remaining display fields are chosen by canonical byte order.

## 6. Authenticated Evidence

Every current trial evidence item MUST reference a path in `review_files`. Its digest MUST equal that entry's authenticated digest. For present content, its inclusive positive line range MUST exist and its excerpt MUST equal exactly those lines joined by line feed. For an absence tombstone, the only valid evidence is line range `0` through `0` with an empty excerpt. Evidence MUST include the finding's own path. Unrelated paths, paraphrased excerpts, out-of-range lines, and all-zero digests are invalid.

These checks apply equally to active and resolution observations. A fabricated resolution therefore cannot remove a prior finding. In every standalone ledger, the distinct trial numbers represented by `evidence` MUST equal `consensus.active_trials` exactly, and those represented by `resolution_evidence` MUST equal `consensus.resolved_trials` exactly. This artifact version carries no per-evidence origin ledger or origin head, so a copied historical item cannot be distinguished from a current trial item by standalone validation. The engine therefore uses the stricter safe rule: it does not carry unlabelled historical evidence into a later ledger. Historical bytes remain authenticated in the retained prior ledger through `prior_ledger_digest` and replay, while current-head evidence arrays contain only observations attributable to the recorded current consensus.

## 7. Lifecycle and Fail-Closed Carrying

The closed lifecycle vocabulary is `new`, `persisting`, `resolved`, `reopened`, and `suppressed`.

| State | Deterministic condition |
|---|---|
| `new` | No prior entry for the fingerprint and active observation in at least two current trials, whether or not a prior ledger exists. |
| `persisting` | Prior active finding not independently marked resolved with authentic evidence by at least two trials. Active disagreement, silence, or a 1-of-3 resolution vote cannot remove it. |
| `resolved` | Prior active finding receives authentic resolution observations from at least two trials. A prior resolved finding remains resolved unless reopened by active consensus. |
| `reopened` | Prior resolved finding is again active in at least two trials. |
| `suppressed` | Otherwise-active finding has a valid human-authorized suppression record; its provenance remains in the ledger. |

An unresolved prior finding **fails closed**. It is carried even when no trial repeats it. A split 1-of-3 resolution is `persisting`. A path rename or move alone never resolves a finding: when a deleted path's old digest reappears as an added path's new digest in the same delta, a resolution observation on the old path is invalid. A true revert or deletion remains representable when authenticated current bytes or an absence tombstone demonstrate that the defective behavior is gone. When `prior_ledger_digest` is null, every finding is necessarily `new` or `suppressed`, and both `first_seen_head` and `last_seen_head` MUST equal the ledger's `head_sha`; an unrelated syntactically valid SHA is rejected.

## 8. Suppression

Suppression is not model output. It requires a separate record naming the exact repository and deterministic fingerprint, human authorizer, durable authorization reference, authorization timestamp, and reason. The record's content digest and authorization fields are retained while the finding remains suppressed. A suppression for an unknown or resolved finding is invalid; when a suppressed finding resolves, its current entry clears `suppression`, while the digest-bound retained prior ledger preserves the authorization history. Suppression removes the finding from active blocker and important counts but never erases retained history.

## 9. Verdict, Counts, and Rendering

Deterministic code derives lifecycle counts and active severity counts directly from final sorted findings. The only verdicts are `approve` and `request_changes`. `request_changes` is mandatory if and only if at least one unsuppressed active `blocker` or `important` finding remains. Active minor findings are reported but do not by themselves request changes.

Ledger arrays are stable-sorted. Markdown is a pure rendering of the ledger and carries one compact Base64 marker containing the exact canonical ledger bytes. Extracting that marker MUST reproduce `ledger.json`, and displayed counts MUST come from the same deterministic count object.

## 10. Replay and Evidence Retention

Every raw canonical packet, all three raw canonical trials, any prior ledger, and every suppression record MUST be retained without reserialization. Replay metadata records each artifact's role, safe relative retained path, byte count, and SHA-256 digest. It also records the ledger and Markdown output digests. Trial artifact numbers MUST be exactly 1, 2, and 3.

Replay verification MUST walk from an explicit filesystem trust anchor with `lstat`/no-follow-equivalent semantics and MUST reject symlink substitutions for every ancestor of the replay root, the replay-root path itself, the replay manifest, `ledger.json`, `review.md`, every retained path component, and every retained artifact. Resolving a path and opening the resolved target is not equivalent because it silently accepts a symlinked ancestor. It re-hashes every retained artifact and both outputs, requires canonical JSON for retained JSON, validates closed shapes and packet/head bindings, re-authenticates every current evidence item against retained packet bytes, regenerates the ledger, regenerates Markdown, and verifies the embedded ledger. Any byte-level tampering, fabricated evidence, duplicate trial number, or unrelated artifact path fails.

## 11. Transactional Publication

A conforming publisher MUST stage the complete output directory privately, write and `fsync` every file, `fsync` staged directories, build the replay manifest, and successfully run replay verification before publication. It MUST publish with an atomic **no-replace** primitive such as Linux `renameat2(RENAME_NOREPLACE)` or an equivalently exclusive, correctly synchronized reservation protocol; an existence check followed by ordinary rename is forbidden because it races. Existing destinations and symlink destinations are rejected rather than overwritten.

Publication has separate **visibility** and **durability** transitions. Any failure before the no-replace rename MUST remove staging and MUST NOT expose a partial output. A successful rename commits one complete visible output and returns `PublicationResult(visible=True, ...)`; it is then followed by parent-directory `fsync`. If that post-visibility `fsync` or descriptor close fails, the result MUST be `visible=True, durable=False` with the durability error. The caller MUST report the durability warning but MUST NOT claim the destination is absent, delete it, overwrite it, or retry publication to the same path. Only a successful parent-directory sync yields `visible=True, durable=True`.

## 12. Required Invocation Surface

A conforming deterministic implementation provides these operations:

- `build-packet`: construct an ordinary or full-audit packet from immutable Git base/head objects, authenticating old bytes and complete full-audit trees.
- `fingerprint`: calculate semantic identity from a candidate finding.
- `converge`: validate and converge one packet, exactly three trials, an optional prior ledger, and optional suppression records.
- `render`: render validated canonical ledger content as Markdown.
- `extract-ledger`: recover and validate the Base64 ledger marker.
- `verify-replay`: verify retained artifact authenticity and reproduce the outputs.

The reference CLI uses only the Python standard library. Failure to parse, authenticate, bind, converge, replay, or publish before visibility MUST return a non-zero status and MUST NOT emit a trusted verdict. A post-visibility parent-directory durability failure is instead reported as the committed-but-not-confirmed-durable publication state defined in Section 11; it MUST never trigger a second publication attempt.
