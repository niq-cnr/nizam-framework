# v1.5.0 release readiness — PASS

Evaluator verdict: all nine contracted acceptance results pass. The repaired committed candidate is `00ef2ef418dbdce1867c9b528da3e97ff20160db`; independent Mode B approval is recorded in `.agent/validator/release-v1.5.0-mode-b.json`. The final machine-readable QA verdict is `.agent/qa/release-v1.5.0.json`.

| Acceptance check | Result | Source commit | Evidence |
|---|---|---|---|
| AT1 Full compliance (16/16) | PASS, exit 0 | `00ef2ef` | `.agent/evidence/release-v1.5.0-prep/01-validate-sh.txt` |
| AT2 Fixtures (147/147) | PASS, exit 0 | `20cdd9a` | `.agent/evidence/release-v1.5.0-prep/02-fixtures-self-test.txt` |
| AT3 Release anchor closeout (V=1.5.0) | PASS, exit 0 | `20cdd9a` | `.agent/evidence/release-v1.5.0-prep/03-release-closeout-pr.txt` |
| AT4 Bootstrap e2e | PASS, exit 0 | `00ef2ef` | `.agent/evidence/release-v1.5.0-prep/04-e2e-bootstrap.txt` |
| AT5 Tag absence with positive origin control | PASS, exit 0 | `20cdd9a` | `.agent/evidence/release-v1.5.0-prep/05-tag-probe-and-sanitization.txt` |
| AT6 Version pins and current disposition | PASS, exit 0 | `00ef2ef` | `.agent/evidence/release-v1.5.0-prep/06-guide-anchors.txt` |
| AT7 Bounded tracked/untracked scope | PASS, exit 0 | `00ef2ef` | `.agent/evidence/release-v1.5.0-prep/07-scope.txt` |
| AT8 Current operator GA declaration | PASS, exit 0 | `00ef2ef` | `.agent/evidence/release-v1.5.0-prep/08-ga-declaration.txt` |
| AT9 Added-line hygiene and preserved history | PASS, exit 0 | `20cdd9a` | `.agent/evidence/release-v1.5.0-prep/09-hygiene-and-history.txt` |

AT1, AT4, AT6, AT7 and AT8 reran independently at the repaired candidate. AT2, AT3, AT5 and AT9 carry the earlier independent passing run at `20cdd9a47a37713cb6bf9b20ee0e1f718494d610`; their original captures retain that SHA. The repair only changes the guide link’s HTML serialization, scoped contract verification metadata and coordinator retry bookkeeping. The browser decodes the guide destination to the same immutable tag URL. The e2e capture resolves the repaired candidate exactly. Full compliance and fixtures ran serially in the original round; fixtures were unaffected by the repair.

The one additional evaluator-originated adversarial check ran in an isolated clone of the final candidate: the scope guard passed its positive control and rejected a new out-of-scope `tools/unplanned-release-probe.txt`. Evidence: `.agent/evidence/release-v1.5.0-prep/release-v1.5.0-qa-adversarial.txt`. The delivery tree was untouched by that probe.

General Availability declared by the operator on 2026-10-10. The verbatim decision "GA is declared." was recorded at `2026-10-10T16:32:48Z` in `.agent/run_state.json` before downstream documentation, at commit `14e632fa04242aaf56eedc15eab377c03ba87511`. The operator declaration takes precedence for this release; `real_production_pilot` is `not_met` and `recorded_consumer_adoptions` is `insufficient_evidence`. These evidence gaps remain unresolved. The historical dossier `.agent/evidence/102/ga-readiness.json` remains byte-identical at SHA256 `d98ccec0f3c57cda51876db3286b57005143ef771b88b4c92f36748de4c0f590`. H-CONSOLIDATION remains outstanding.

v1.5.0 is a MINOR release. C13 intentionally tightens skill capability indexing in both full sweep and `--payload`; existing but unindexed modules now fail. The shipped manifest/index pair remains compliant. The record makes no claim of identical validator behavior for independently modified manifests.

The failed first QA round and all original captures are preserved in `.agent/qa/release-v1.5.0-failed-round1.json` and flat `failed-round1-` evidence files with remapped references. All final QA evidence paths exist and contain invocation, source SHA, output and actual exit status. This preparation is ready for the authorized clean PR merge and separate annotated tag/pin mechanic. No merge or tag was performed by the evaluator.
