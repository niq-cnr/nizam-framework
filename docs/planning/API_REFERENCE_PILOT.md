---
id: nizam-api-reference-pilot
title: "Approved Backlog — Focused Python API Reference"
description: "A bounded API-reference extraction pilot with measured benefit required before integration or expansion."
version: 0.1.0
status: active
authoritative_source: docs/planning/API_REFERENCE_PILOT.md
change_log:
  - version: "0.1.0"
    date: "2026-10-27"
    summary: "Record operator-approved API-REF-PILOT scope, execution sequence, adoption criteria and scheduling boundaries."
---

# Focused Python API-reference extraction pilot

Backlog ID: **API-REF-PILOT**. Work status: **approved; not started**.
The operator requested "add this plan to the project backlog" and clarified
"it is approved work" on 2026-10-27. This records approval to pursue the
bounded work; measured adoption criteria below determine whether its reference
is integrated. No numeric feature IDs or phase budget are allocated here.

## Outcome and scope

Help contributors locate implementation symbols and use them correctly faster
than with the existing documentation. Start with authored
`tools/start_path.py`, `tools/convergent_review.py` and
`tools/payload_integrity.py`. Compare the existing `tools/README.md`,
`llms-full.txt` and source before adding documentation.

Extract the useful reference capability from the reviewed generated package;
regenerate accurate content from authored source. Exclude historical `.agent/`
scripts, installed `.nizam/` files, tests and fixtures as API targets, copied
governance documents, the generated replacement skill, and network/provider
examples. Derived documentation remains subordinate to source and installed
governance. Documenting a symbol does not make it a stable public library API.

## Ordered delivery

| Stage | Depends on | Deliverable and exit condition |
| --- | --- | --- |
| A — Gap and baseline | None | Identify unanswered navigation needs; freeze 12 tasks, four per module, covering symbol location, signatures/return shapes and safe usage. Record source-backed expected answers, correctness, elapsed time and files opened with existing documentation. Stop if no material gap is demonstrated. |
| B — Implementation planning | A | Classify actual implementation scope; produce the specification, feature DAG, estimates, exact runnable acceptance checks and reviewed contracts required by installed governance. |
| C — Reference preview | B | Implement a deterministic standard-library AST extractor and generate an allowlisted three-module preview without importing or executing source modules. |
| D — Examples and verification | C | Supply one self-contained offline example per module, including imports, fixtures and expected results; execute all examples and verify reference correctness. |
| E — Adoption decision | D | Repeat the fixed task evaluation, retain raw evidence, and compare results against every adoption criterion below. |
| F — Conditional integration | E passes | Link the reference from existing documentation; add freshness, link and example checks to an appropriate existing CI job. Expand only for demonstrated navigation gaps. |

Candidate implementation paths are `tools/generate_api_reference.py`,
`tools/test_generate_api_reference.py` and `docs/reference/python/`; final scope
is fixed in stage B. The generator extracts selected signatures, annotations,
docstrings and source links, marks missing documentation rather than inventing
behavior, and keys pages by complete repository-relative source paths.

Record source paths, content digests and reproducible revision provenance.
Exclude volatile generation timestamps and define dirty-tree behavior in the
contract. Generated pages must satisfy applicable NDS rules and resolve links
in their publication layout. Keep this contributor reference outside the
consumer installation payload unless a later reviewed change explicitly adds it.

Stage D checks basename collisions, positional and keyword-only parameters,
defaults, async functions, classes, exclusions, absence of source execution,
stale output removal, link resolution, repeat-generation byte identity and
freshness detection against a temporary modified source copy.

## Significant-enhancement gate

Preregister the benchmark and use matched independent reviewers or fresh
isolated sessions with counterbalanced task variants to limit learning effects.
Record reviewer/session configuration and the development host. The 12-task
pilot is a practical adoption signal, not a general statistical performance claim.

All of these criteria must pass before stage F:

- At least **30% lower median task-completion time** than the existing-doc baseline.
- At least **11 of 12 correct answers**, with no correctness regression from baseline.
- **Zero** invented APIs, incorrect signatures, broken reference links or failing selected examples.
- Byte-identical generation from identical inputs.
- Generation/freshness checking in **under 10 seconds** for the pilot on the recorded host.
- One regeneration command and no third-party generator dependency.

These are acceptance targets, not achieved results. If the gap inventory or
pilot fails its gate, retain the findings and prefer targeted improvements to
existing documentation. Allow at most one bounded pilot revision before
revisiting scope. Reassess usefulness after several real contributor tasks
following adoption.

## Scheduling and authority

This is approved backlog work linked from the [forward roadmap](ROADMAP.md).
The active Jev readiness program retains its existing order. Scheduling does
not bypass specification, contract approval, independent evaluation or evidence
requirements. Implementation has not started; integration and whole-tree
coverage are not implied by backlog approval.
