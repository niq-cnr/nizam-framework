"""Adversarial tests for the provider-neutral semantic observation contracts.

These are pure offline tests: no provider, network or credential is involved.
They prove the eight JR-12 acceptance criteria using only the validation
functions in ``tools/semantic_contract.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import semantic_contract as sc  # noqa: E402


def _raises(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except sc.SemanticContractError:
        return True
    return False


def _dist(labels, values):
    return dict(zip(labels, values))


def test_choice_definition_and_order():
    # AC-12-02: option order is identity; duplicates and empty labels are rejected
    assert sc.validate_choice_definition(["a", "b"]) == ["a", "b"]
    assert sc.validate_choice_definition(["b", "a"]) == ["b", "a"]  # not sorted
    assert _raises(sc.validate_choice_definition, ["a", "a"])
    assert _raises(sc.validate_choice_definition, [])
    assert _raises(sc.validate_choice_definition, ["a"])
    assert _raises(sc.validate_choice_definition, ["", "b"])


def test_distribution_invariants():
    # AC-12-03: unknown options, missing options, non-finite and out-of-range are unusable
    labels = ["a", "b", "c"]
    assert sc.validate_distribution(_dist(labels, [0.5, 0.3, 0.2]), labels=labels)
    assert sc.validate_distribution(_dist(labels, [0.5, 0.5, 0.0]), labels=labels)
    # materially invalid sum
    assert _raises(sc.validate_distribution, _dist(labels, [0.5, 0.5, 0.5]), labels=labels)
    # unknown option
    assert _raises(sc.validate_distribution, _dist(["a", "b", "d"], [0.5, 0.3, 0.2]), labels=labels)
    # missing option
    assert _raises(sc.validate_distribution, _dist(["a", "b"], [0.5, 0.5]), labels=labels)
    # non-finite / out of range
    assert _raises(sc.validate_distribution, _dist(labels, [0.5, float("nan"), 0.5]), labels=labels)
    assert _raises(sc.validate_distribution, _dist(labels, [1.2, -0.2, 0.0]), labels=labels)


def test_choice_answer_consistency_and_ties():
    labels = ["direct", "support", "ext", "insufficient"]
    # selected option must be modal
    ok = {"distribution": _dist(labels, [0.7, 0.1, 0.1, 0.1]), "selection": 0}
    assert sc.validate_choice_answer(ok, options=labels)
    # selected non-modal -> contradiction (AC-12-03/AC-12-04)
    bad = {"distribution": _dist(labels, [0.1, 0.7, 0.1, 0.1]), "selection": 0}
    assert _raises(sc.validate_choice_answer, bad, options=labels)
    # exactly one mode must be declared (AC-12-04)
    both = {"distribution": _dist(labels, [0.4, 0.4, 0.1, 0.1]), "selection": 0, "tie": [0, 1]}
    assert _raises(sc.validate_choice_answer, both, options=labels)
    none = {"distribution": _dist(labels, [0.4, 0.4, 0.1, 0.1])}
    assert _raises(sc.validate_choice_answer, none, options=labels)
    # explicit tie of two or more distinct options is valid
    tie = {"distribution": _dist(labels, [0.4, 0.4, 0.1, 0.1]), "tie": [0, 1]}
    assert sc.validate_choice_answer(tie, options=labels)
    # explicit insufficient_evidence is valid
    insuf = {"distribution": _dist(labels, [1.0, 0.0, 0.0, 0.0]), "insufficient_evidence": True}
    assert sc.validate_choice_answer(insuf, options=labels)


def test_noul_polarity_and_no_confidence():
    # AC-12-06: missing probability is unknown, never false
    assert _raises(sc.validate_noul_answer, {"probability": None}, polarity="yes")
    assert _raises(sc.validate_noul_answer, {}, polarity="yes")
    # AC-12-04: no invented correctness confidence
    assert _raises(sc.validate_noul_answer, {"probability": 0.7, "confidence": 0.9}, polarity="yes")
    # stable polarity
    assert _raises(sc.validate_noul_answer, {"probability": 0.7}, polarity="maybe")
    assert sc.validate_noul_answer({"probability": 0.7}, polarity="no") == {"probability": 0.7}


def test_score_rubric_and_expectation():
    rubric = [
        {"level": "low", "description": "no material change"},
        {"level": "medium", "description": "bounded change"},
        {"level": "high", "description": "consequential change"},
    ]
    ok = {"distribution": [0.1, 0.2, 0.7], "expected_level": 2}
    assert sc.validate_score_answer(ok, rubric=rubric)
    # expected level out of range
    assert _raises(sc.validate_score_answer, {"distribution": [0.1, 0.2, 0.7], "expected_level": 3}, rubric=rubric)
    # distribution wrong length
    assert _raises(sc.validate_score_answer, {"distribution": [0.5, 0.5], "expected_level": 0}, rubric=rubric)
    # non-finite probability
    assert _raises(sc.validate_score_answer, {"distribution": [0.0, float("inf"), 0.0], "expected_level": 1}, rubric=rubric)
    # rubric order changes identity; non-list / short rubrics rejected
    assert _raises(sc.validate_score_rubric, ["low", "high"])
    assert _raises(sc.validate_score_rubric, [{"level": "low", "description": "x"}])


def _base_observation(**overrides):
    obs = {
        "schema_version": 1,
        "task": {"task_id": "t", "operation_id": "op", "attempt": 1},
        "binding": {
            "base_revision": "0" * 40,
            "candidate": "1" * 40,
            "requirement_refs": ["J02"],
            "contract_refs": [],
        },
        "question": {
            "family": "DF-01",
            "version": "component_requirement.v1",
            "primitive": "choice",
            "instructions": "full context",
            "options": ["direct", "support", "ext", "insufficient"],
        },
        "model": {"requested": "jev-1", "resolved": "jev-1", "provider_request_id": "req-1"},
        "transport": {"transmitted_body_sha256": "a" * 64, "raw_response_sha256": "b" * 64},
        "execution": {"status": "succeeded", "reason_code": None},
        "answer": {
            "distribution": _dist(["direct", "support", "ext", "insufficient"], [0.7, 0.1, 0.1, 0.1]),
            "selection": 0,
        },
    }
    obs.update(overrides)
    return obs


def test_full_observation_binding():
    # AC-12-01: a coherent observation validates; malformed ones are unusable
    assert sc.validate_observation(_base_observation())
    # AC-12-03: returned-model mismatch and unknown primitive are unusable
    assert _raises(sc.validate_observation, _base_observation(model={"requested": "jev-1", "resolved": "jev-2"}))
    base = _base_observation()
    base["question"]["primitive"] = "gpt-float"
    assert _raises(sc.validate_observation, base)
    # execution status vocabulary
    assert _raises(sc.validate_observation, _base_observation(execution={"status": "maybe"}))
    # a non-succeeded observation must not claim an answer
    assert _raises(
        sc.validate_observation,
        _base_observation(execution={"status": "unavailable", "reason_code": "timeout"}),
    )
    # a succeeded observation must carry an answer
    assert _raises(sc.validate_observation, _base_observation(answer=None))


def test_observation_identity_preserves_order():
    # AC-12-02/AC-12-05: option order participates in identity
    a = _base_observation()
    b = _base_observation()
    b["question"]["options"] = ["support", "direct", "ext", "insufficient"]
    b["answer"] = {"distribution": _dist(["support", "direct", "ext", "insufficient"], [0.7, 0.1, 0.1, 0.1]), "selection": 0}
    assert sc.observation_identity(a) != sc.observation_identity(b)


def test_fresh_observation_rejects_bad_input():
    # AC-12-08: a constructor must reject type confusion / non-modal selection
    assert _raises(
        sc.fresh_observation,
        task_id="t", operation_id="op", attempt=1,
        base_revision="0" * 40, candidate="1" * 40, requirement_refs=[],
        contract_refs=[], question={"family": "DF-01", "version": "v1", "primitive": "choice",
                                    "options": ["a", "b"]},
        model={"requested": "jev-1"}, provider_request_id=None,
        transmitted_body_sha256="a" * 64, raw_response_sha256="b" * 64,
        execution_status="succeeded", reason_code=None,
        answer={"distribution": _dist(["a", "b"], [0.5, 0.5]), "selection": 0},
    )


def main() -> int:
    test_choice_definition_and_order()
    test_distribution_invariants()
    test_choice_answer_consistency_and_ties()
    test_noul_polarity_and_no_confidence()
    test_score_rubric_and_expectation()
    test_full_observation_binding()
    test_observation_identity_preserves_order()
    test_fresh_observation_rejects_bad_input()
    print("semantic-contract: Choice/Noul/Score validation and observation binding pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
