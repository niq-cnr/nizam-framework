#!/usr/bin/env python3
"""Unit 6: jsonschema validation of four governed files, with negative controls."""
import copy, json, sys
import jsonschema, yaml

PAIRS = [
    (".agent/feature_list_014.json", "schema/feature_list.schema.json", "json"),
    ("docs/planning/phase_014.yaml", "schema/phase.schema.json", "yaml"),
    ("docs/planning/manifest.json", "schema/manifest.schema.json", "json"),
    (".agent/run_state.json", "schema/run_state.schema.json", "json"),
]
bad = 0
for doc_path, schema_path, kind in PAIRS:
    with open(doc_path, encoding="utf-8") as fh:
        doc = json.load(fh) if kind == "json" else yaml.safe_load(fh)
    with open(schema_path, encoding="utf-8") as fh:
        schema = json.load(fh)
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    validator = cls(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    # negative control: inject an unknown top-level key and drop a required key; schema must object
    mutated = copy.deepcopy(doc)
    req = schema.get("required", [])
    control = "n/a"
    if req:
        mutated.pop(req[0], None)
        control = "rejects-missing-%s" % req[0] if list(cls(schema).iter_errors(mutated)) else "VACUOUS"
    status = "VALID" if not errors else "INVALID"
    print("%-8s %-40s vs %-38s required=%d top-level-keys=%d negative-control=%s"
          % (status, doc_path, schema_path, len(req), len(doc), control))
    for e in errors[:5]:
        print("   ", list(e.path), e.message[:200])
    if errors or control == "VACUOUS":
        bad += 1
print("RESULT: %d of %d invalid/vacuous" % (bad, len(PAIRS)))
sys.exit(1 if bad else 0)
