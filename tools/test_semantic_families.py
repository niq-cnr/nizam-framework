"""Adversarial tests for the DF-01 component traceability family (JR-15)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import semantic_contract as sc  # noqa: E402
import semantic_families as sf  # noqa: E402


def _raises(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except sf.FamilyAdmissionError:
        return True
    return False


def _state(**overrides):
    state = {
        "approved_requirements": ["R1: record an evidence file per executed check"],
        "non_goals": [],
        "component_proposal": {"path": "tools/start_path.py", "proposal": "record evidence paths"},
        "source_context": "relevant source excerpt",
    }
    state.update(overrides)
    return state


def test_admission_requires_mandatory_sources():
    # AC-15-02: missing mandatory context prevents dispatch
    sf.admit("DF-01", _state())
    assert _raises(sf.admit, "DF-01", _state(approved_requirements=None))
    assert _raises(sf.admit, "DF-01", _state(component_proposal={}))
    assert _raises(sf.admit, "DF-01", {})  # both missing


def test_projection_renders_full_context():
    # AC-15-02 / J04: substantive context goes into instructions, not opaque ids
    state = _state()
    projected = sf.build_projections("DF-01", state, sf.DF01_QUESTION)
    instructions = projected["instructions"]
    assert "R1: record an evidence file" in instructions
    assert "tools/start_path.py" in instructions
    # ordered options preserved and validated
    assert projected["options"] == [
        "direct_requirement",
        "necessary_support",
        "unsupported_extension",
        "insufficient_evidence",
    ]
    # a wrong-family question is rejected
    assert _raises(sf.build_projections, "DF-02", state, sf.DF01_QUESTION)


def test_four_options_are_valid_choice_semantics():
    # AC-15-01: necessary_support and insufficient_evidence are distinct valid outcomes
    labels = sf.DF01_QUESTION["options"]
    necessary = {"distribution": _d(labels, "necessary_support"), "selection": 1}
    sc.validate_choice_answer(necessary, options=labels)
    insufficient = {"distribution": _d(labels, "insufficient_evidence"), "insufficient_evidence": True}
    sc.validate_choice_answer(insufficient, options=labels)
    # an author's unsupported necessity assertion is data, not authority: it is
    # still a normal selection the policy may override deterministically


def _d(labels, modal):
    # build a distribution with the named option as unique modal summing to 1
    others = (1.0 - 0.8) / (len(labels) - 1)
    return {l: (0.8 if l == modal else others) for l in labels}


def test_fixture_cases_cover_all_four_categories():
    # AC-15-01: fixtures include explicit, support, extension and missing-evidence cases
    fixture = json.loads((ROOT / "tools/fixtures/semantic/df01_cases.json").read_text())
    expected = {case["expected"] for case in fixture["cases"]}
    assert expected == set(sf.DF01_QUESTION["options"])
    # every case names immutable ids and a requirement/component (AC-16-01 seed)
    for case in fixture["cases"]:
        assert case["id"].startswith("df01-")
        assert "component" in case and "expected" in case


def test_family_questions_valid_and_no_self_activation():
    sf.validate_family_questions()
    # all seven families have typed question definitions (JR-28..33 covered)
    assert set(sf.FAMILY_QUESTIONS) == {f"DF-0{i}" for i in range(1, 8)}
    for family, questions in sf.FAMILY_QUESTIONS.items():
        assert len(questions) >= 1, family
    # the family registry is static; a model/authored value cannot expand it
    assert "DF-08" not in sf.FAMILY_QUESTIONS


def main() -> int:
    test_admission_requires_mandatory_sources()
    test_projection_renders_full_context()
    test_four_options_are_valid_choice_semantics()
    test_fixture_cases_cover_all_four_categories()
    test_family_questions_valid_and_no_self_activation()
    print("semantic-families: DF-01 admission, projection and fixtures pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
