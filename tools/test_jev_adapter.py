"""Adversarial tests for the optional host-side Jev adapter (JR-14), mock transport only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "providers"))

import providers.jev as jev  # noqa: E402


def _raises(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except (jev.JevConfigError, jev.JevTransportError, ValueError):
        return True
    return False


def _config(**overrides):
    config = {"endpoint": "https://api.typesafe.ai/v1/systemone", "model": "jev-1.14.0", "timeout_sec": 5.0, "api_key_env": "TYPESAFE_API_KEY"}
    config.update(overrides)
    return config


def _choice_question():
    return {"family": "DF-01", "version": "component_requirement.v1", "primitive": "choice",
            "instructions": "classify", "options": ["direct_requirement", "necessary_support", "unsupported_extension", "insufficient_evidence"]}


def _choice_answer(choice="direct_requirement", probs=None):
    probs = probs or {"direct_requirement": 0.8, "necessary_support": 0.1, "unsupported_extension": 0.05, "insufficient_evidence": 0.05}
    return {"type": "choice", "choice": choice, "confidence": 0.9, "probabilities": probs}


def _ok_transport(status=200, model="jev-1.14.0", answers=None, request_id="req-1"):
    def transport(endpoint, body, api_key, timeout):
        payload = {"model": model, "usage": {"input_tokens": 10, "output_tokens": 5}, "answers": answers or {}}
        return status, {"x-typesafe-request-id": request_id}, json.dumps(payload).encode()
    return transport


def _dispatch_args():
    return dict(
        state="the component proposal",
        questions={"q1": _choice_question()},
        operation_id="op-1",
        attempt=1,
        task_id="t",
        base_revision="0" * 40,
        candidate="1" * 40,
        requirement_refs=["J02"],
    )


def test_config_trust_boundary():
    # AC-14-05: untrusted endpoint, disabled TLS, redirects and floating aliases are denied
    assert _raises(jev.validate_config, _config(endpoint="http://api.typesafe.ai/v1/systemone"))
    assert _raises(jev.validate_config, _config(endpoint="https://api.typesafe.ai/v1/systemone@evil"))
    assert _raises(jev.validate_config, _config(verify_tls=False))
    assert _raises(jev.validate_config, _config(allow_redirects=True))
    assert _raises(jev.validate_config, _config(model="jev-latest"))
    assert _raises(jev.validate_config, _config(timeout_sec=0))
    # a valid config passes
    assert jev.validate_config(_config())["model"] == "jev-1.14.0"


def test_successful_mock_dispatch():
    answers = {"q1": _choice_answer()}
    transport = _ok_transport(answers=answers)
    result = jev.dispatch(_config(), transport=transport, **_dispatch_args())
    assert result["status"] == "succeeded"
    assert result["resolved_model"] == "jev-1.14.0"
    assert result["charged_requests"] == 1
    obs = result["observations"][0]
    assert obs["answer"]["selection"] == 0
    assert obs["execution"]["status"] == "succeeded"


def test_transport_fallbacks():
    # AC-14-01: 429, 5xx, malformed, model mismatch, missing answer -> bounded fallback
    result = jev.dispatch(_config(), transport=_ok_transport(status=429, answers={"q1": _choice_answer()}), **_dispatch_args())
    assert result["status"] == "unavailable" and result["reason_code"] == "rate_limited"

    result = jev.dispatch(_config(), transport=_ok_transport(status=503, answers={"q1": _choice_answer()}), **_dispatch_args())
    assert result["status"] == "unavailable" and result["reason_code"] == "provider_unavailable"

    def malformed(*a):
        return 200, {}, b"not json"
    result = jev.dispatch(_config(), transport=malformed, **_dispatch_args())
    assert result["status"] == "invalid_response"

    result = jev.dispatch(_config(), transport=_ok_transport(model="jev-1.13.0", answers={"q1": _choice_answer()}), **_dispatch_args())
    assert result["status"] == "invalid_response"

    result = jev.dispatch(_config(), transport=_ok_transport(answers={}), **_dispatch_args())
    assert result["status"] == "invalid_response"


def test_lost_response_unknown():
    def lost(endpoint, body, api_key, timeout):
        raise jev.JevTransportError("connection reset")
    result = jev.dispatch(_config(), transport=lost, **_dispatch_args())
    assert result["status"] == "unavailable" and result["reason_code"] == "provider_unavailable"
    assert result["answer"] is None


def test_missing_credentials_no_network():
    # AC-14-04: a missing credential produces an ineligible fallback with no call and no leak
    calls = []
    def spy(endpoint, body, api_key, timeout):
        calls.append(api_key)
        return 200, {}, b"{}"
    import os
    old = os.environ.pop("TYPESAFE_API_KEY", None)
    try:
        result = jev.dispatch(_config(), transport=spy, **_dispatch_args())
    finally:
        if old is not None:
            os.environ["TYPESAFE_API_KEY"] = old
    assert result["status"] == "ineligible"
    assert calls == []


def test_no_secret_in_diagnostics():
    # AC-14-05 / AC-14-04: the bearer token never appears in any output string
    import os
    os.environ["TYPESAFE_API_KEY"] = "sk-super-secret-token"
    captured = {}
    def transport(endpoint, body, api_key, timeout):
        captured["api_key"] = api_key
        return 200, {"x-typesafe-request-id": "r"}, json.dumps({"model": "jev-1.14.0", "usage": {"input_tokens": None, "output_tokens": None}, "answers": {"q1": _choice_answer()}}).encode()
    result = jev.dispatch(_config(), transport=transport, **_dispatch_args())
    serialized = json.dumps(result, default=str)
    assert "sk-super-secret-token" not in serialized


def main() -> int:
    import os
    os.environ.setdefault("TYPESAFE_API_KEY", "sk-test-key")
    test_config_trust_boundary()
    test_successful_mock_dispatch()
    test_transport_fallbacks()
    test_lost_response_unknown()
    test_missing_credentials_no_network()
    test_no_secret_in_diagnostics()
    print("jev-adapter: trust boundary, bounded fallbacks and secret isolation pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
