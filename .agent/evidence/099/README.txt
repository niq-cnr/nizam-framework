Feature 099 evidence index (contract .agent/contracts/099.json, attempt 1 of 3, step key 099-implementation).
Capture wrapper: each verification entry's command text is extracted programmatically from the contract's
verification[].command and run with `bash -c` from the attempt-root repo root; the file holds the command text
(line 1..n), the verbatim stdout+stderr, and a final `EXIT:<code>` line read from the process itself.
AT1 was captured first and again last, after every edit.

at1-validator-gate.txt                           AT1  validator gate
at2-key-documents-guard.txt                      AT2  NIZAM.json ecosystem key_documents guard
at3-capability-register.txt                      AT3  NIZAM.json capabilities register 06 and 08
at4-skill-json-register.txt                      AT4  tools/skill.json capabilities register 06 and 08
at5-gates-defined-not-reserved.txt               AT5  operator_gates.md gates DEFINED, not reserved
at6-frontmatter-active.txt                       AT6  ecosystem 06/08 frontmatter active, version bumped
at7-guide-ecosystem-card.txt                     AT7  guide ecosystem card lists every ecosystem/0*.md
at8-fixtures-self-test.txt                       AT8  tools/fixtures_self_test.sh
s01-contract-schema-valid.txt                    S1   schema validity
s02-validator-gate-payload.txt                   S2   validator gate --payload
s03-scope-boundary.txt                           S3   scope boundary
s04-frozen-infra-and-workflows-untouched.txt     S4   frozen infra and .github untouched
s05-no-tag-created.txt                           S5   no tag created (needs network for git fetch)
s06-release-closeout-pr.txt                      S6   release close-out, PR mode
s07-gates-defined-not-exercised.txt              S7   gates defined not exercised; Section 2 pin; 06/08 body delta
s08-ecosystem-readme-and-versions.txt            S8   version bumps and README literals
s09-skill-json-version-and-count.txt             S9   skill.json 0.3.0 -> 0.4.0, +2 capabilities
s10-nizam-capabilities-additive.txt              S10  NIZAM.json capabilities additive (33 -> 35)
s11-phase-yaml-step-record.txt                   S11  phase_014.yaml step 099 record
s12-guide-scope-ecosystem-key-documents-only.txt S12  guide change confined to Key documents paragraph
