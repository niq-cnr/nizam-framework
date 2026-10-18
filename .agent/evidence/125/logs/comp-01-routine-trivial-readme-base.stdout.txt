[comp-01-routine-trivial-readme:base:Baseline]
{
  "assurance_tier": "Routine",
  "files": [
    "README.md"
  ],
  "reasons": [
    "editorial or documentation-only adjustment with no contract/schema/tool impact"
  ],
  "required_gates": [
    "start_path:begin:trivial",
    "validate.sh",
    "start_path:done:trivial"
  ],
  "review_remit": {
    "advisory_fields": [
      "advisory_minor"
    ],
    "blocking_fields": [
      "issues",
      "missing_acceptance_coverage",
      "unsupported_claims",
      "required_fixes"
    ],
    "evidence_required_for_blockers": true
  },
  "route": "trivial",
  "stopping_conditions": {
    "attempt_counter_role": "telemetry",
    "breaker_ref": "methodology/03_circuit_breaker.md",
    "comparator_subordinate": true,
    "halt_condition": "Stop and diagnose on repeated identical deterministic failure, contradiction with approved contract/invariants, missing operator authority, or exhausted execution budget; comparator claims remain subordinate to stopping rules.",
    "max_attempts": 3,
    "pass_condition": "All required_gates for route 'trivial' exit 0 and blocking verdict arrays are empty."
  }
}
