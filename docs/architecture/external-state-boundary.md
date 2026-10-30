---
id: external-state-boundary
title: "External admission state namespace"
description: "Nofollow namespace checks precede external state creation, locking and staging cleanup."
tags: [security, evidence, filesystem]
status: active
last_audited: "2026-10-30"
authoritative_source: tools/external_evidence.py
version: 1.0.0
---

# External admission state namespace

Allocation, generic admission, the typed admission shared core, and reconciliation
use the same managed namespace under `.agent/evidence/external_admissions`.
Before creating directories or the state lock, they inspect every existing fixed
ancestor and the `permits` and `admitted` children. A symlink, dangling symlink or
non-directory component refuses before any state cleanup or publication.

The implementation opens directories with `O_DIRECTORY` and `O_NOFOLLOW`, checks
the actual opened descriptor, and creates missing ancestors relative to validated
parent descriptors. It opens `state.lock` relative to the state descriptor using
`O_NOFOLLOW` and `O_NONBLOCK`, then checks that the actual opened file is regular
before acquiring the existing lock. Unsafe lock types refuse promptly. Missing
required primitives refuse with a controlled `unsafe_state_namespace` diagnostic.
Existing directory and regular lock modes are preserved; no permission repair or
namespace relocation occurs. The existing common task lock retains its ordering.

Staging cleanup opens the validated managed directories relative to the state
descriptor. It first inspects all `.tmp-*` entries without following links, across
all three directories. Only after every such entry is regular does it unlink
staging files relative to those descriptors. Unknown nonregular entries are
preserved and refused, including a staging symlink pointing at an outside file.
A refusal during this inspection does not partially clean other regular stages.
Non-staging files and published permit/admission histories keep their existing
validation and recovery rules. A regular staging file remains disposable under
the existing interrupted-publication convention; it never supplies ledger or
completion authority.

These checks guard a cooperative host against unsafe pre-existing namespace
components. Existing publication helpers still use paths after validation. This
is not a guarantee against a hostile process with the same user identity renaming
directories concurrently, nor a claim of process isolation, producer trust or
human approval. Public APIs, wire/profile versions, task budgets and the single
existing ledger remain unchanged. Source acceptance does not upgrade an installed
payload or qualify an external producer pair.

The independent `tools/test_external_state_boundary.py` corpus exercises actual
public operations in bounded child processes, including namespace and lock types,
outside byte/mode preservation, unchanged ledger counts, no partial cleanup,
missing primitive refusal, real authenticated replay, regular staging recovery
and preservation of existing directory/lock modes. Typed negative cases exercise
the shared generic guard; they do not qualify a typed consumer pair.
