# Product Spec — Phase 022: Portable Docker Trial-Sandbox Adapter

## Problem (from the 2026-10-16 local control-capability investigation)

The shipped Linux reference sandbox adapter (`tools/linux_trial_sandbox.sh` +
`tools/isolated_trial_adapter.py`) cannot start on hosts whose kernel refuses
`unshare --user --map-root-user` (`uid_map` EPERM; e.g.
`kernel.apparmor_restrict_unprivileged_userns = 1`). On such hosts the
required-conformance suite reports the five sandbox-dependent tests as
`UNSUPPORTED`, prints `CONFORMANCE: NOT FULL`, and exits non-zero. No host
security control may be relaxed to recover the native path, and the pinned
release plus current official main ship no container-equivalent adapter.
The investigation's minimal proposal (not implemented there) is the basis of
this phase.

## Goal

Add ONE canonical, trusted, Docker-backed equivalent adapter implementing the
existing `ADAPTER --root TRIAL_ROOT --runner RUNNER -- RUNNER_ARGUMENTS...`
protocol, and make sandbox conformance capability selection adapter-specific,
so a host that cannot prove user-namespace isolation can still exercise the
five sandbox-dependent evaluator/adapter obligations through the selected
equivalent adapter — without weakening any obligation, gate, or host control.

## User stories

1. As a reviewer on a userns-restricted host with a reachable Docker daemon, I
   can run `tools/test_convergent_review.py` and get `CONFORMANCE: FULL` with
   the five sandbox-dependent tests actually exercised through the Docker
   adapter (auto-selected because the native probe fails and the Docker probe
   passes), exit 0.
2. As a reviewer on a userns-capable host, behavior is unchanged: the native
   adapter is auto-selected exactly as today, and the native suite prints
   `CONFORMANCE: FULL` there.
3. As a reviewer on a host with neither capability, every sandbox-dependent
   test is still reported `UNSUPPORTED`, the run still prints
   `CONFORMANCE: NOT FULL`, and the command still exits non-zero. Selection
   never manufactures green and never drops the unsupported obligation.
4. As an operator, I can force an adapter explicitly
   (`--isolation-adapter tools/docker_trial_sandbox.sh` or the native wrapper)
   for deterministic qualification runs, and the forced run fails closed when
   that adapter's capability probe fails instead of silently skipping.
5. As the evaluator harness, I invoke the Docker adapter exactly like the
   native one (`evaluate_convergent_review_prompt.py --isolation-adapter ...`);
   the evaluator's trust-anchored no-follow/exclusive I/O, post-run input
   revalidation, deterministic convergence, closed schemas, three-trial rule,
   Git-object packet, and replay/publication semantics are unchanged.

## Required adapter properties (normative, all live-verified)

Under unchanged restrictive host controls (no sysctl/seccomp/AppArmor/userns
changes; no privileged, cap-added, host-network, host-PID, or shared-mount
containers; no daemon socket or runtime control endpoint in the observer):

- Fresh per-trial process/PID/session boundary and no network
  (`--network none`, fresh container per invocation, bounded teardown).
- Private read/write-but-NOEXEC trial storage, including after runner chmod
  (inner Landlock EXECUTE denial; EACCES observed, not ENOENT-masquerade).
- Read/execute only for the pre-resolved trusted runner and required runtime
  (inner Landlock: runner file rule + explicit interpreter allowlist rules
  needed because the pinned image's base-layer binaries are inode-distinct
  under OverlayFS; verified empirically on the QA host).
- No sibling/prior/ambient repository or credential reads (paths outside the
  trial root, runner file, and pinned image runtime are unmapped in the
  container mount namespace).
- Trusted pinned immutable image/runtime/controller provenance
  (digest-pinned public image reference constant in the trusted wrapper;
   wrapper refuses to run with any other reference; wrapper, inner adapter,
   and runner are repo-shipped or evaluator-pre-resolved trusted files whose
   digests the evaluator receipt already records).
- No daemon socket or runtime-session/control endpoint reachable by the
  observer (socket never mounted; live probes assert absence).
- Evaluator trust-anchored no-follow/exclusive/singly-linked I/O and post-run
  input revalidation (unchanged evaluator; exercised through this adapter).
- Actual waited exits, bounded teardown, no leaked trial state (`docker run`
  wait semantics, `--rm`, named-container force-remove trap, outer timeout).

Untrusted packet/PR/env input cannot choose the image, mounts, or any
privileged runtime option: the wrapper accepts no such input and passes a
fixed minimal container environment.

## Technical direction

- `tools/docker_trial_sandbox.sh`: trusted controller wrapper. Parses the
  adapter protocol; validates paths (absolute, no comma/flag-shaped
  components); runs `docker run` with `--network none --cap-drop ALL
  --security-opt no-new-privileges --read-only --user <invoking uid:gid>
  --stop-timeout` and same-path bind mounts (trial root rw; runner file ro;
  inner adapter file ro); reassembles the inner command; propagates the
  container's exit code; bounded teardown. `--probe` capability mode and
  `--print-image` introspection mode for tests/CI. Fails closed (distinct
  exit codes) when the daemon is unreachable or the pinned image is absent.
- `tools/isolated_trial_adapter.py`: additive optional repeatable
  `--interpreter PATH` argument adding READ|EXECUTE file rules for required
  interpreter binaries before restriction. Native invocations pass no such
  flag and behave byte-identically to today.
- `tools/test_convergent_review.py`: capability-probe abstraction
  (native unshare probe; Docker daemon+image+smoke probe), auto-selection
  with native precedence, explicit `--isolation-adapter` override (via
  `--isolation-adapter` argument recognized before unittest passthrough),
  adapter-flavored boundary exercises for the five sandbox-dependent tests,
  Docker-specific live regression guards (CapEff==0, no docker socket, fresh
  PID namespace, ambient-file unreadable while present on host), and the same
  hardened live-listener/EACCES/omission-control patterns: a genuinely-live
  listener proven reachable outside, refusal inside, sibling denial proven
  real by host-side existence, exec denial EACCES-only, exec-permitted and
  bad-interpreter mutants, and mount-omission controls. UNSUPPORTED semantics
  and the required-conformance exit rule are preserved verbatim.
- `.github/scripts/test_sandbox_boundaries.py`: optional `--adapter` argument
  selecting the same machinery; default unchanged.
- `.github/workflows/compliance.yml` (convergent_review job only): pull the
  pinned digest image, then run the Docker-adapter boundary/conformance
  steps. No sysctl step, SBCL steps, or WA123 steps are altered, removed, or
  imitated; no host relaxation is introduced or relied on by the new steps.
- Registration: `tools/README.md` documents the adapter and selection
  behavior; `NIZAM.json` tools key_documents gains the new wrapper; CHANGELOG
  Unreleased entry; DEBT.md records the image re-pin policy risk; planning
  manifest gains phase 022.

## Non-goals

- No change to the evaluator engine, schemas, packet/replay/publication
  semantics, or any consumer-facing surface.
- No service/platform/general orchestration layer; no runtime-session broker;
  no ambient-credential forwarding; no live-model observation runner (the
  model-integration gap is explicitly preserved and not claimed closed).
- No editing of installed `.nizam/` payload; no release tag; no gate
  fabrication or historical evidence rewrite.
- No host security-control changes anywhere (local or CI), including the
  existing CI sysctl-enablement step, which remains untouched and is not used
  as authority for the Docker route.

## Design criteria / acceptance basis

Every required property above is proven by a live command captured as
evidence: allowed work runs (fake runner end-to-end through the adapter),
forbidden work fails for the boundary reason (EACCES exec denial after chmod;
unmapped-path denial with host-side existence proof; network refusal with a
proven-live listener), each layer is proven load-bearing by an omission
control (exec-permitted mutant, mounted-sibling control, in-container
loopback control), and the five previously-UNSUPPORTED evaluator/adapter
obligations execute for real under the Docker adapter on the restrictive QA
host. The native path and its unsupported-stays-nonzero rule remain intact,
demonstrated by a forced-native run on the restrictive host.
