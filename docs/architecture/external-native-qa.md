---
id: external-native-qa
title: "Optional external observations and native QA"
description: "One permit and admission authority with authenticated native proof mapping and separate governed completion."
version: 1.0.0
status: active
authoritative_source: docs/architecture/external-native-qa.md
---

# Optional external observations and native QA

`tools/external_qa.py` adds an explicitly invoked library boundary to the
existing `generic-external-evidence-v1` profile at version `1.1.0`. It runs no
verifier, creates no second budget, and does not advance completion. The host
allocates one canonical permit before an actual trusted verifier invocation.
Native and external first reservations share one POSIX task lock in a fixed
private `/tmp/nizam-task-reservations-<effective uid>` directory, keyed by the
canonical root path and task identifier. Opened directory/lock descriptors must
be user-owned with modes `0700`/`0600` and reject symlinks. Ambient temporary or
home directories and Git initialization cannot select another lock. This
supported coordination profile assumes cooperating controllers with the same
effective user. Lock files contain no ownership or budget data and are never
removed by the reservation protocol;
existing native reservations/captures and external permits/ledger remain the
owners. Mixed, corrupt or interrupted matching history holds the task rather
than selecting a fresh authority. Output directory, step and contract changes
do not convert task ownership.

The host calls `admit_external_qa(repo_root, envelope, context_ref=...,
expected_feature_id=..., expected_candidate=..., required_checks=...,
expected_execution_identity=..., expected_producer=...,
admission_expectations=...)`. Host expectations are selected independently of
the producer's envelope. `admission_expectations` carries the existing generic
admission keywords, including the separately trusted candidate digest. The
native candidate must include the exact active bridge, verifier and schema
inputs in its tool closure. Import this API from the assessed consumer's
`tools/` or `.nizam/tools/` layout with the corresponding native companions.

`schema/external_qa_context.schema.json` defines the closed context. It binds
the feature, assessed candidate and independent QA references, full approved
required-check inventory digest, host-selected execution identity, producer,
and immutable assessed host policy/execution-profile inputs. Every consumed
candidate, QA, capture and stream reference is covered by the authenticated
envelope and checked against current bytes and modes. The mode inventory
covers every envelope artifact except the context itself; the context's outer
descriptor avoids self-reference. Modes are `100644` or `100755`. Native
capture revision identifies the consumer's source-preserving candidate;
driver/image/tool revisions belong in authenticated execution artifacts.

The existing native proof core interprets the complete approved inventory,
counts, exact diagnostics and actual captures. An optional producer emits
observations; it cannot invent an independent adversarial review, human
approval or required checks. One exact verifier-driver invocation can be one
approved native check, with its internal collection, tool, isolation and
execution records retained as authenticated artifacts. Other native required
checks remain required. The selected Agentic controller is an optional
consumer, not a dependency of this provider-neutral module.

Passing typed projection and generic admission publish in the same existing
ledger transition. Identical replay revalidates the projection and current
artifacts without another execution or permit. A record published before an
interrupted ledger write completes at most one transition after exact
revalidation. Generic-only admission cannot be upgraded silently on replay.
Completed failed outcomes can settle the generic ledger without a typed
mapping. Noncompleted execution holds the existing permit; the host must
reconcile actual execution and cleanup before resubmitting retained evidence.

Public native QA and receipt consumers require the matching latest recorded
typed mapping for an externally owned task. They reauthenticate retained
producer proof, current artifact bytes/modes and native proof without writes.
A new unsettled permit holds completion. `completion_status: not_advanced`
always describes this API's result. Governed completion remains the existing
done or verified receipt/resume route, with its existing independent QA and
operator requirements.

Token possession and a valid schema do not establish an isolated execution
channel. Actual producer source/image, protected token delivery, collection
freezing, cleanup and host isolation require separate exact-pair execution
qualification. Unrestricted host code can still mutate files outside the
protocol. No model, gateway, network service, release or installation is
activated by importing or documenting this optional boundary.
