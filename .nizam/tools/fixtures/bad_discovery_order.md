# C10 Sub-Check (2) FAIL Fixture -- Reversed Discovery Order

This body deliberately reverses the correct discovery order for regression
testing C10's discovery-order sub-check.

1. **Framework-checkout fallback.** The runtime falls back to a
   repository-root `tools/skill.json` path when no bootstrapped-consumer
   payload is present.
2. **Bootstrapped-consumer discovery.** The runtime first looks for
   `tools/skill.json` under `.nizam/tools/skill.json`.
