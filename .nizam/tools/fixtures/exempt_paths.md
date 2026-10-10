# check_c9_path_resolution PASS/Exemption Fixture

This body names only resolving paths and exempt placeholder forms, and
must leave C9 PASSing when this file is directly --target-ed.

Two real, resolving, directory-qualified references: tools/verify_lib.sh
and schema/README.md.

Two vlib_path_resolves placeholder exemptions: an NNN-bearing path
.agent/contracts/NNN.json, and a step-N-bearing path (deliberately
nonexistent, exempt solely via the step- pattern)
docs/planning/step-02-report.md.

Two directory-only illustrative references, which have no shipped
extension and are never even extracted as candidate tokens: tools/.claude/
and tools/.codex/.

Two C9-specific additional exemptions: the bootstrapped-consumer path
.nizam/tools/skill.json (the `.nizam/` prefix), and the schema/README.md
singleton-artifact tokens .agent/capability_profile.json and
.agent/debt.json.
