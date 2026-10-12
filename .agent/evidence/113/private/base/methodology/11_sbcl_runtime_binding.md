---
id: nizam-sbcl-runtime-binding
title: "SBCL Runtime Binding"
description: "Normative SBCL reference binding and folded language profile for live development, honest outcomes and fresh hermetic acceptance."
version: 0.1.0
status: active
enforcement: consumer-aspirational
authoritative_source: methodology/11_sbcl_runtime_binding.md
change_log:
  - version: "0.1.0"
    date: "2026-10-12"
    summary: "Define the SBCL reference profile and runtime hazards without claiming executable enforcement or live conformance."
---

# SBCL Runtime Binding

## 1. Binding scope and evidence boundary

This **consumer-aspirational** binding specializes
[Live Runtime Sessions](10_live_runtime_sessions.md). Consumers claiming this
binding MUST enforce both documents. Source, mutable image and durable provenance
remain distinct; a session record cannot prove source/heap identity or acceptance.
The folded language profile below is part of this binding, not a separate profile
mechanism. The existing <a href="..&#47;schema/runtime_session.schema.json">session</a> and
<a href="..&#47;schema/runtime_operation.schema.json">operation</a> schemas describe records;
record validation cannot establish live ownership or runtime conformance.

The normative document is delivered; executable controller/adapter enforcement
and all thirteen live proofs remain pending phase016 work. ASDF forms below are
illustrative until phase016 live verification. Observed local SBCL2.2.9.debian
availability is not conformance or proof of host isolation. Consumers MUST obtain
required capable isolated CI evidence before claiming live acceptance. This
binding does not authorize changing workstation sysctls or installed governance.

## 2. Reference language profile

A consumer MUST record a replayable profile binding `toolchain_identity` to the
actual SBCL executable/build/version, implementation features, platform and ASDF
version. Identify the committed source revision and source manifest with content
digests, the explicit dependency set and digest-bound `lock_ref`, permitted
build/load configuration, relevant environment and exact compile/load/test
commands. ASDF system definitions alone are not a dependency lock. Unknown or
changed inputs invalidate acceptance and require fresh assessment.

Record `core_provenance`: core origin, digest, toolchain match and whether a core
contains development-image state. Acceptance MUST use an approved clean
installation core or independently reproducible clean core; it MUST NOT boot a
core saved from a development image. Disabling init files does not remove effects
already embedded in a core.

Correlate session identity with current `owner`, principal/role, process
`generation`, `lease_epoch` and outstanding operation. Check those identities
before execution and on reattachment, using the neutral protocol's serial stream
and existing schema fields. Identity and toolchain/lock/core references provide
provenance only; they do not certify that live memory matches committed source.

## 3. Observation executes project code

`macroexpand` invokes expansion functions; `print-object` dispatch and `inspect`
or editor-bridge inspection/evaluation can invoke project code. Consumers MUST
apply the same owner, generation and lease checks and serialized operation lane
to these observations as to evaluation. Inspection is not an authorization bypass.
Printer and inspector callbacks may mutate state, signal conditions or block.

Multiple editor REPL clients, including REPLs attached through SLY, can share one
image. Consumers MUST account for every such client within the same ownership
and operation stream; a second REPL is not process isolation. Record actual
connection/process identity rather than treating editor windows as independent
sessions.

## 4. Non-atomic load and compile

`load` sequentially executes forms. `compile-file` processes top-level forms and
can execute expansion functions and compile-time `defmacro`, `defpackage` or
`eval-when` effects. Both operations are non-atomic: earlier effects can survive
a later failure. A successful output-path return alone does not establish a
successful build; inspect compilation failure/warning values under the profile's
explicit diagnostic policy.

Consumers MUST report a failed partial load or compile honestly as
`condition_signalled` with `image_consistent: false`, preserving diagnostics,
source/operation identity and known partial effects. They MUST NOT claim rollback
or image consistency merely because control returned. If consistency cannot be
established, quarantine the image and reconstruct from committed inputs before
further development claims. Reconstructing does not reset the governed attempt.

## 5. Conditions and restarts

Consumers MUST capture condition identity, bounded diagnostics and applicable
restarts **before unwind**, using `handler-bind` or the documented
`sb-ext:*invoke-debugger-hook*` when debugger entry is the appropriate boundary.
`handler-case` transfers control and unwinds before its matching clause runs;
that clause cannot recover the original dynamic restart context. The debugger
hook does not replace handlers for conditions that never enter the debugger.

Restarts established by `restart-case` or `restart-bind` have dynamic extent.
Serialize bounded restart descriptions while applicable; durable descriptions
are not invocable restart objects. Consumers MUST NOT automatically invoke an
arbitrary restart or replay a saved restart object after its context has ended.
Any authorized restart selection belongs to the correlated active operation.

Diagnostic printing MUST bound depth, length, total bytes and execution/time
budget. Bind appropriate printer controls, including `*print-level*`,
`*print-length*` and `*print-circle*`, but do not assume they bound custom
`print-object` or condition-report callbacks. Avoid recursively invoking unsafe
project printers; use a trusted minimal type/identity fallback and report
truncation or capture failure explicitly. A stuck reporting callback remains
execution subject to the timeout and busy-lane rules below.

## 6. Image drift

Deleting or renaming a function or deleting a `defmethod` from source does not
remove its old live definition. Reloading `defvar` retains an existing bound
value, so a changed initializer may never run. Consumers MUST treat these drift
classes as a reason to reconstruct when source/image consistency is uncertain;
warm-image tests cannot establish reproducibility.

Under this binding, changed `defstruct` definitions and `defconstant` values
MUST trigger reconstruction from committed source. This is a conservative binding
policy, not a claim that Common Lisp universally prohibits all redefinition.
Changing a constant to a different value has undefined consequences under the
language rules; structure redefinition also has implementation-sensitive limits.

CLOS standard-class redefinition can lazily update existing instances. Old
objects and external effects may remain; user-defined update methods can execute
code. Class redefinition removes certain generated accessor methods as specified
by the language, but it does not erase arbitrary user methods deleted from
source. Consumers MUST NOT equate successful redefinition or reload with a
fresh image.

## 7. Threads and special variables

SBCL global special values are shared; dynamic bindings are thread-local, and
new threads do not inherit parent dynamic bindings. Consumers MUST establish
explicit worker bindings for package, readtable, printer settings and operation
context; a parent `let` around thread creation is insufficient. Do not confuse
bindings with synchronization of shared mutable values.

Consumers MUST account for outstanding worker threads, shared REPL clients and
external resource handles before ownership transfer, image reuse or
reconstruction. Their identities and unresolved effects remain in provenance;
a worker completing does not by itself establish image consistency.

## 8. Timeouts and cancellation

`join-thread :timeout` bounds waiting, not execution. On timeout, consumers MUST
record `wait_outcome: stopped_waiting` and preserve the observed `running`,
`cancel_requested` or `unknown` status. The operation lane stays busy until its
outcome is resolved; stopping a wait cannot authorize a conflicting submit.

`interrupt-thread` and `terminate-thread` are asynchronous mechanisms with
`unwind-protect`, cleanup and reentrancy hazards. A cancellation request MUST NOT
be treated as confirmed cancellation. Consumers MUST observe execution stopping
under the correlated operation/session/generation/lease identity before recording
`cancelled`, and assess remaining effects and consistency separately. Confirmed
termination does not undo already executed forms or release every resource.

When cancellation cannot be confirmed, preserve uncertainty, quarantine the
image and reconstruct as needed; do not silently free the lane or claim success.
Process replacement and new generation retain the same contract/step/attempt
accounting under [the circuit breaker](03_circuit_breaker.md). Diagnostic or
infrastructure failures remain failures in that governed step.

## 9. Fresh-environment acceptance

Acceptance MUST start a fresh process with `sbcl --no-sysinit --no-userinit`,
using the profile's clean core and pinned toolchain. It MUST compile committed
source and dependencies afresh, load the new products and execute the recorded
tests. An unsaved definition, a deleted definition surviving in the development
image or a fasl compiled against an unsaved macro must not make acceptance pass.
A fresh process alone is not a fresh build.

Consumers MUST use private `HOME` and XDG configuration/cache/data locations,
a newly created empty private ASDF output directory and an explicit committed
source/dependency set. Replace inherited `CL_SOURCE_REGISTRY` and
`ASDF_OUTPUT_TRANSLATIONS` with approved explicit configurations, each containing
`:ignore-inherited-configuration`. Empty environment variables alone are
insufficient. Verify actual dependency resolution and emitted/loaded artifact
paths against the profile; reject inherited fasls or shared build caches.

The following ASDF configuration forms are **illustrative**, not a tested
launcher. The named directories represent a sealed candidate source/dependency
set and its new empty private output directory. Phase016 must verify the forms,
configuration precedence and compile/load/test sequence with the pinned versions
on capable required isolated CI before any live conformance claim.

```lisp
(asdf:initialize-source-registry
 '(:source-registry
   (:directory "/candidate/src/")
   (:directory "/candidate/deps/")
   :ignore-inherited-configuration))
(asdf:initialize-output-translations
 '(:output-translations
   (t ("/candidate/build/" :implementation))
   :ignore-inherited-configuration))
```

The future launcher MUST replace inherited configuration before project
resolution, restrict dependencies to the manifest and ensure no development
systems or caches are preloaded in its acceptance core. These forms cannot by
themselves establish process isolation, dependency locking or hermetic execution.
Session provenance and development test results never substitute for fresh,
independently captured acceptance evidence.

## 10. Outcome mapping

Consumers MUST use exactly the existing operation status vocabulary, preserving
wait outcome and consistency separately. Capturing a warning or other condition
does not always imply abnormal completion; the operation's observed outcome and
explicit diagnostic policy determine its status.

| Status | SBCL observation and required record meaning |
| --- | --- |
| `completed` | Observed normal completion under the profile's diagnostic policy; not source/heap equivalence or acceptance proof. |
| `condition_signalled` | Operation ended through a captured condition; partial load/compile records `image_consistent: false`. |
| `cancelled` | Cancellation is confirmed by observed stopping; `cancellation_confirmed: true` is required, with consistency assessed separately. |
| `terminated` | Correlated process termination was observed; it does not imply rollback or confirmed clean resources. |
| `rejected` | Admission refused before project code executes, including foreign owner, stale generation/lease, busy lane or review trial. |
| `running` | Execution is outstanding, including after a bounded wait returns `stopped_waiting`. |
| `cancel_requested` | Cancellation was requested but execution stopping has not been confirmed. |
| `unknown` | Observation cannot establish the outcome; preserve uncertainty and outstanding work. |

Infrastructure failures MUST remain governed failures with diagnostic references,
using existing observed outcomes rather than inventing a new record status.

## 11. Primary references

Consumers MUST check the pinned versions against official sources and capture
source/command evidence independently. The links supply language/implementation
semantics; this binding supplies the conservative reconstruction and acceptance
policy. Online manuals can describe newer versions than the observed local SBCL;
they do not prove controller behavior or all thirteen live cases.

- CLHS [macro expansion](https://www.lispworks.com/documentation/HyperSpec/Body/f_mexp_.htm),
  [printing](https://www.lispworks.com/documentation/HyperSpec/Body/f_pr_obj.htm),
  [load](https://www.lispworks.com/documentation/HyperSpec/Body/f_load.htm),
  [compile-file](https://www.lispworks.com/documentation/HyperSpec/Body/f_cmp_fi.htm),
  [top-level processing](https://www.lispworks.com/documentation/HyperSpec/Body/03_bca.htm)
  and [defining macros](https://www.lispworks.com/documentation/HyperSpec/Body/03_bcaa.htm)
  support Sections3–4.
- CLHS [handler-bind](https://www.lispworks.com/documentation/HyperSpec/Body/m_handle.htm),
  [handler-case](https://www.lispworks.com/documentation/HyperSpec/Body/m_hand_1.htm),
  [restart-case](https://www.lispworks.com/documentation/HyperSpec/Body/m_rst_ca.htm)
  and [restart-bind](https://www.lispworks.com/documentation/HyperSpec/Body/m_rst_bi.htm)
  support Section5.
- CLHS [defvar](https://www.lispworks.com/documentation/HyperSpec/Body/m_defpar.htm),
  [defstruct](https://www.lispworks.com/documentation/HyperSpec/Body/m_defstr.htm),
  [defconstant](https://www.lispworks.com/documentation/HyperSpec/Body/m_defcon.htm)
  and [class redefinition](https://www.lispworks.com/documentation/HyperSpec/Body/04_cf.htm)
  support Section6.
- The SBCL manual's [special variables](https://www.sbcl.org/manual/#Special-Variables),
  [thread operations](https://www.sbcl.org/manual/#Threading),
  [debugger invocation](https://www.sbcl.org/manual/#Debugger-Invocation)
  and [startup options](https://www.sbcl.org/manual/#Toplevel-Options)
  support Sections5,7–9.
- ASDF's [source registry](https://asdf.common-lisp.dev/asdf%2Ehtml#Controlling-where-ASDF-searches-for-systems)
  and [output translations](https://asdf.common-lisp.dev/asdf%2Ehtml#Controlling-where-ASDF-saves-compiled-files)
  support Section9; the forms remain illustrative pending phase016 proof.
