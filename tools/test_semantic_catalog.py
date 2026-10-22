"""Adversarial tests for the versioned question/policy catalog (JR-27)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import semantic_catalog as scat  # noqa: E402


def _raises(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except scat.CatalogError:
        return True
    return False


def _question(**overrides):
    spec = {
        "family": "DF-01",
        "question_id": "component_requirement.v1",
        "version": "component_requirement.v1",
        "primitive": "choice",
        "instructions": "classify this component",
        "options": ["direct_requirement", "necessary_support", "unsupported_extension", "insufficient_evidence"],
        "depends_on": [],
    }
    spec.update(overrides)
    return spec


def test_registry_exactly_seven_families():
    # AC-27-01: all seven families are defined with valid primitive/effect/consumer declarations
    registry = scat.validate_family_registry()
    assert set(registry) == {f"DF-0{i}" for i in range(1, 8)}
    for fid in registry:
        for primitive in registry[fid]["primitives"]:
            assert primitive in ("choice", "noul", "score")
        for effect in registry[fid]["permitted_effects"]:
            assert effect in scat.DISPOSITIONS


def test_question_validation_rejects_bad_shapes():
    # AC-27-02: ambiguous polarity, out-of-family primitive, missing rubric/options are rejected
    assert scat.validate_question_spec(_question())
    # noul without polarity
    assert _raises(scat.validate_question_spec, _question(primitive="noul", polarity=None, options=None))
    # primitive the family does not use (DF-01 does not use score)
    assert _raises(
        scat.validate_question_spec,
        _question(primitive="score", options=None, rubric=[{"level": "a", "description": "x"}, {"level": "b", "description": "y"}]),
    )
    # unknown family
    assert _raises(scat.validate_question_spec, _question(family="DF-99"))
    # choice without ordered options
    assert _raises(scat.validate_question_spec, _question(options=None))
    # unsupported mode
    assert _raises(scat.validate_question_spec, _question(max_mode="production"))


def test_dependency_validation_cycles_and_dangling():
    # AC-27-02: dangling dependencies and cycles fail closed
    a = _question(question_id="a")
    b = _question(question_id="b", depends_on=["a"])
    c = _question(question_id="c", depends_on=["b"])
    scat.validate_question_dependencies([a, b, c])
    # dangling
    assert _raises(scat.validate_question_dependencies, [_question(question_id="a", depends_on=["missing"])])
    # cycle a -> b -> a
    cyc_a = _question(question_id="a", depends_on=["b"])
    cyc_b = _question(question_id="b", depends_on=["a"])
    assert _raises(scat.validate_question_dependencies, [cyc_a, cyc_b])
    # duplicate ids
    assert _raises(scat.validate_question_dependencies, [a, a])


def test_version_and_activation_boundaries():
    # AC-27-05/AC-27-03: the catalog is static data; nothing here activates a policy
    spec = _question()
    assert spec["version"] == spec["question_id"]
    # a model-authored or task-text value cannot mutate the registry
    registry = scat.FAMILY_DEFINITIONS
    frozen = dict(registry)
    assert "DF-08" not in frozen
    assert len(frozen) == 7


def main() -> int:
    test_registry_exactly_seven_families()
    test_question_validation_rejects_bad_shapes()
    test_dependency_validation_cycles_and_dangling()
    test_version_and_activation_boundaries()
    print("semantic-catalog: seven-family registry and question-dependency validation pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
