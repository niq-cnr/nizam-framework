# Release Readiness — v1.3.0

Gate: `H-FRAMEWORK-RELEASE` (operator-only). Prepared 2026-09-30 on the
`feat/methodology-review-gate-flake-management` branch, packaging the
Review-Gate Flake Management doctrine
(`methodology/09_review_gate_flake_management.md`) and its registration
(`NIZAM.json` capability + methodology key_documents, `methodology/README.md`
index row, `docs/guide/index.html` methodology card). Target tier: MINOR, per
`methodology/06_release_train.md` Section 3.2 — a new protocol document added
under `methodology/`, purely additive and new-optional; nothing that validated
under v1.2.0 is invalidated. At preparation time the pipeline has not created,
pushed, or approved `v1.3.0`.

This preparation also corrects release-state drift recorded in
`docs/planning/ROADMAP.md` and `docs/planning/operator_gates.md`: v1.2.0 was
released 2026-09-17 (tag `7441ffa`, run 35232527341) and v1.2.1 was tagged
2026-09-19 (`250fdd9`, run 35456401143 failed the tag-mode close-out because
no `[1.2.1]` CHANGELOG section was cut); both facts are now recorded where the
stale "Release in preparation: v1.2.0" bullet stood.

## Automated readiness

1. Framework validator: full default sweep **16/16 PASS** (`bash tools/validate.sh`).
2. Fixture and CLI self-test: **79/79 PASS** (`bash tools/fixtures_self_test.sh`).
3. Release close-out gate, `--mode pr`, at V=1.3.0: **PASS** --
   all five anchor groups agree (`python3 .github/scripts/release_closeout.py --mode pr`).
4. Hermetic e2e bootstrap harness: **PASS** (`bash tools/e2e_bootstrap_test.sh`,
   including `assert_multirepo` and `assert_stage4`).
5. Real repository tag probe: `git rev-parse -q --verify refs/tags/v1.3.0`
   returns non-zero -- **no `v1.3.0` tag exists**.

Raw captured outputs: `.agent/evidence/flake-methodology-2026-09-30/`
(01-validate-sh.txt, 02-fixtures-self-test.txt, 03-release-closeout-pr.txt,
04-tag-probe-and-sanitization.txt, 05-e2e-bootstrap.txt).

## Content map

| Surface | Summary |
|---|---|
| `methodology/09_review_gate_flake_management.md` | The doctrine: fail-closed principles; the open F1-F6 flake-class taxonomy; the bounded retry ladder (trial-local retry, ONE re-dispatch, class-exception vs honest re-run); protected-repository rules; telemetry duties; evidence duties (naming, post-merge races, canonical-vs-vendored resync wave); KPI targets. |
| `NIZAM.json` | capability `nizam-review-gate-flake-management`; methodology key_documents entry; `framework.version` 1.3.0. |
| `methodology/README.md` | Index row + module description (v0.4.0). |
| `docs/guide/index.html` | methodology module card lists 09; meta/footer anchors 1.3.0. |
| `CHANGELOG.md` / `README.md` / `CONTEXT.md` | Dated `[1.3.0]` MINOR section; four rolling pins to v1.3.0; CONTEXT frontmatter + change_log[0] at 1.3.0. |
| `docs/planning/ROADMAP.md`, `docs/planning/operator_gates.md` | v1.3.0 preparation dispositions + v1.2.0/v1.2.1 release-fact corrections. |

Provenance: the doctrine was validated in production fleet operations on
2026-09-30 (fail-closed gate behavior, bounded retry ladder, class taxonomy
with ledger and engine diagnoses).

`H-FRAMEWORK-RELEASE` sign-off and the tag remain outstanding — this pipeline
never self-tags per `methodology/06_release_train.md` Section 6.
