"""Optional host-side Jev adapter (ordinary HTTP, no SDK, no daemon).

Jev is TypeSafe's System One model, served by ``POST https://api.typesafe.ai/v1/systemone``.
The request carries a shared ``state`` plus a ``questions`` dict of atomic typed
questions; the response returns a ``model`` (resolved version ID), nullable
``usage``, and ``answers`` discriminated by ``type``. Because Jev ingests ``state``
once and evaluates questions against it in parallel, a batch of independent
questions over the same state is a single charged request.

This adapter is optional and imported only when a governed/advisory/shadow live
call is authorized; the default ``off`` mode never imports it. It pins an exact
model version (never a floating alias), disables opaque retries (one transport
attempt per dispatch), and validates the trust boundary (trusted HTTPS endpoint,
TLS verification, no redirects, secrets never in diagnostics).

Consult the current official documentation before live activation; the wire
shape below reflects the docs retrieved 2026-10-22 and must be re-verified.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any, Callable

from semantic_contract import (
    SemanticContractError,
    fresh_observation,
)

DEFAULT_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
DEFAULT_TIMEOUT_SEC = 30.0
MAX_RESPONSE_BYTES = 16 * 1024 * 1024

Transport = Callable[[str, bytes, str, float], tuple[int, dict[str, str], bytes]]


class JevConfigError(ValueError):
    """The adapter configuration violates the trust boundary."""


class JevTransportError(ValueError):
    """A transport failure that must surface as a bounded explicit fallback."""


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the adapter configuration and enforced trust boundary.

    - endpoint must be an exact, trusted HTTPS URL with no credentials fragment;
    - verify_tls can never be disabled;
    - redirects are disabled (a redirect from the trusted endpoint is denied);
    - the model must be a non-empty exact version identity (an alias is rejected
      so a floating alias can never silently change the model);
    - the API key is read from an environment variable, never a config literal.
    """
    if not isinstance(config, dict):
        raise JevConfigError("config must be an object")
    endpoint = config.get("endpoint", DEFAULT_ENDPOINT)
    if not isinstance(endpoint, str) or not endpoint.startswith("https://"):
        raise JevConfigError("endpoint must be an exact https:// URL")
    if "@" in endpoint or "?" in endpoint or "#" in endpoint:
        raise JevConfigError("endpoint must not carry credentials, a query or a fragment")
    verify_tls = config.get("verify_tls", True)
    if verify_tls is not True:
        raise JevConfigError("TLS verification cannot be disabled")
    if config.get("allow_redirects") not in (False, None):
        raise JevConfigError("redirects must be disabled on the trusted endpoint")
    model = config.get("model")
    if not isinstance(model, str) or not model.strip() or model in ("jev-latest", "jev-preview"):
        raise JevConfigError("model must be an exact pinned version id, never a floating alias")
    timeout = config.get("timeout_sec", DEFAULT_TIMEOUT_SEC)
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise JevConfigError("timeout_sec must be a positive number")
    api_key_env = config.get("api_key_env", "TYPESAFE_API_KEY")
    if not isinstance(api_key_env, str) or not api_key_env.strip():
        raise JevConfigError("api_key_env must name an environment variable for the credential")
    return {
        "endpoint": endpoint,
        "verify_tls": True,
        "model": model,
        "timeout_sec": float(timeout),
        "api_key_env": api_key_env,
    }


def _read_api_key(config: dict[str, Any]) -> str:
    """Return the credential from the named environment variable, or raise without leaking it."""
    import os

    key = os.environ.get(config["api_key_env"])
    if not key:
        raise JevConfigError(f"credential environment variable {config['api_key_env']!r} is not set")
    return key


def build_systemone_body(state: Any, questions: dict[str, dict[str, Any]]) -> bytes:
    """Build the Jev ``/v1/systemone`` request body from the bounded state and typed questions.

    Each question maps to Jev's per-question shape: ``type`` (choice/noul/score),
    ``instructions``, and the primitive fields (``criteria`` for choice, ``rubric``
    for score). A missing or malformed question is refused here, before any
    network activity.
    """
    if not isinstance(questions, dict) or not questions:
        raise SemanticContractError("a Jev request needs at least one typed question")
    out_questions: dict[str, dict[str, Any]] = {}
    for name, question in questions.items():
        if not isinstance(name, str) or not name.strip():
            raise SemanticContractError("question names must be non-empty strings")
        if not isinstance(question, dict):
            raise SemanticContractError(f"question {name!r} must be an object")
        primitive = question.get("primitive")
        if primitive not in ("choice", "noul", "score"):
            raise SemanticContractError(f"question {name!r} has unsupported primitive {primitive!r}")
        wire: dict[str, Any] = {
            "type": primitive,
            "instructions": question.get("instructions", ""),
        }
        if primitive == "choice":
            options = question.get("options")
            if not isinstance(options, list) or len(options) < 2:
                raise SemanticContractError(f"choice question {name!r} needs ordered options")
            wire["criteria"] = options
        elif primitive == "score":
            rubric = question.get("rubric")
            if not isinstance(rubric, list) or len(rubric) < 2:
                raise SemanticContractError(f"score question {name!r} needs an ordered rubric")
            wire["rubric"] = [level.get("description") for level in rubric]
        out_questions[name] = wire
    body = {"state": state, "questions": out_questions}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def default_http_transport(endpoint: str, body: bytes, api_key: str, timeout_sec: float) -> tuple[int, dict[str, str], bytes]:
    """Perform one ordinary HTTPS POST with TLS verification and no redirects.

    This is the only place a network call happens, and it is never reached in
    ``off``/``mock``/``replay`` mode. Redirects are disabled by using a handler
    whose redirect handler always refuses, so an endpoint that redirects is
    denied rather than silently followed.
    """
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise JevTransportError("redirect from the trusted endpoint was denied")

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=timeout_sec) as response:
            status = response.status
            headers = {k.lower(): v for k, v in response.headers.items()}
            data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise JevTransportError("response exceeded the maximum allowed size")
            return status, headers, data
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, exc.read(MAX_RESPONSE_BYTES)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise JevTransportError(f"transport failed: {type(exc).__name__}") from exc


def _fallback(reason_code: str, status: str = "unavailable") -> dict[str, Any]:
    """Build a bounded fallback result that never masquerades as a semantic answer."""
    return {"status": status, "reason_code": reason_code, "answer": None}


def parse_response(
    body: bytes,
    *,
    requested_model: str,
    questions: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], str | None]:
    """Parse a Jev response into provider-neutral observations.

    Returns ``(observations, usage, resolved_model)``. Malformed JSON, a missing
    ``model`` field, a resolved model that disagrees with the requested pinned
    model, unknown answer keys, out-of-range probabilities and missing mandatory
    answers all raise, so the caller records ``invalid_response`` rather than
    coercing the residual into a valid observation.
    """
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SemanticContractError("malformed JSON response") from exc
    if not isinstance(payload, dict):
        raise SemanticContractError("response is not a JSON object")
    resolved = payload.get("model")
    if not isinstance(resolved, str) or not resolved.strip():
        raise SemanticContractError("response is missing the resolved model")
    if requested_model and resolved != requested_model:
        raise SemanticContractError(
            f"resolved model {resolved!r} does not match requested model {requested_model!r}"
        )
    raw_usage = payload.get("usage") or {}
    usage = {
        "input_tokens": raw_usage.get("input_tokens"),
        "output_tokens": raw_usage.get("output_tokens"),
    }
    answers = payload.get("answers")
    if not isinstance(answers, dict):
        raise SemanticContractError("response is missing its answers object")

    observations: list[dict[str, Any]] = []
    for name, question in questions.items():
        if name not in answers:
            raise SemanticContractError(f"response is missing the answer for question {name!r}")
        raw = answers[name]
        if not isinstance(raw, dict):
            raise SemanticContractError(f"answer for question {name!r} is not an object")
        primitive = question["primitive"]
        if raw.get("type") != primitive:
            raise SemanticContractError(
                f"answer for question {name!r} has type {raw.get('type')!r}, expected {primitive!r}"
            )
        normalized = _normalize_answer(primitive, question, raw)
        observations.append(normalized)
    return observations, usage, resolved


def _normalize_answer(primitive: str, question: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    """Translate a Jev answer into the provider-neutral answer shape.

    Confidence is deliberately dropped: Jev documents it as a certainty signal,
    not a probability of correctness, and the neutral answer carries only the
    validated distribution/selection/probability/score.
    """
    if primitive == "choice":
        probabilities = raw.get("probabilities")
        choice = raw.get("choice")
        options = question["options"]
        valid = set(options)
        if not isinstance(probabilities, dict) or set(probabilities) != valid:
            raise SemanticContractError("choice probabilities do not match the declared options")
        if choice not in valid:
            raise SemanticContractError(f"selected choice {choice!r} is not a declared option")
        selection = options.index(choice)
        return {"distribution": probabilities, "selection": selection}
    if primitive == "noul":
        probability = raw.get("noul")
        return {"probability": probability}
    if primitive == "score":
        score = raw.get("score")
        legend = raw.get("legend")
        probabilities = raw.get("probabilities")
        if not isinstance(probabilities, dict):
            raise SemanticContractError("score answer is missing its level probabilities")
        n = len(question["rubric"])
        if set(int(k) for k in probabilities) != set(range(n)):
            raise SemanticContractError("score probabilities do not cover every rubric level")
        ordered = [probabilities.get(str(i), probabilities.get(i)) for i in range(n)]
        expected = int(round(float(score))) if score is not None else None
        return {"distribution": ordered, "expected_level": expected, "legend": legend}
    raise SemanticContractError(f"unsupported primitive {primitive!r}")


def dispatch(
    config: dict[str, Any],
    *,
    state: Any,
    questions: dict[str, dict[str, Any]],
    operation_id: str,
    attempt: int,
    task_id: str,
    base_revision: str,
    candidate: str,
    requirement_refs: list[str] | None = None,
    contract_refs: list[str] | None = None,
    transport: Transport | None = None,
) -> dict[str, Any]:
    """Run one accounted dispatch and return an execution result with observations.

    A transport here is the real stdlib HTTPS call; tests inject a mock. Every
    failure path returns a bounded fallback (``unavailable``/``invalid_response``
    with an explicit reason) and never a fabricated answer.
    """
    config = validate_config(config)
    body = build_systemone_body(state, questions)
    transport = transport or default_http_transport

    try:
        api_key = _read_api_key(config)
    except JevConfigError as exc:
        return {"status": "ineligible", "reason_code": "unsupported_capability", "answer": None, "detail": str(exc)}

    try:
        status, headers, data = transport(config["endpoint"], body, api_key, config["timeout_sec"])
    except JevTransportError as exc:
        return _fallback("provider_unavailable", "unavailable")

    if status == 429:
        return _fallback("rate_limited", "unavailable")
    if status >= 500:
        return _fallback("provider_unavailable", "unavailable")
    if status != 200:
        return _fallback("invalid_response", "unavailable")

    requested_id = headers.get("x-typesafe-request-id") or None
    try:
        observations, usage, resolved_model = parse_response(data, requested_model=config["model"], questions=questions)
    except SemanticContractError as exc:
        return {"status": "invalid_response", "reason_code": "invalid_response", "answer": None, "detail": str(exc)}

    bound_observations = [
        fresh_observation(
            task_id=task_id,
            operation_id=operation_id,
            attempt=attempt,
            base_revision=base_revision,
            candidate=candidate,
            requirement_refs=list(requirement_refs or []),
            contract_refs=list(contract_refs or []),
            question={"family": q.get("family", ""), "version": q.get("version", ""),
                      "primitive": q["primitive"], "instructions": q.get("instructions", ""),
                      "options": q.get("options"), "polarity": q.get("polarity", "yes"),
                      "rubric": q.get("rubric")},
            model={"requested": config["model"], "resolved": resolved_model},
            provider_request_id=requested_id,
            transmitted_body_sha256=_sha256(body),
            raw_response_sha256=_sha256(data),
            execution_status="succeeded",
            reason_code=None,
            answer=ans,
        )
        for q, ans in zip(questions.values(), observations)
    ]
    return {
        "status": "succeeded",
        "reason_code": None,
        "observations": bound_observations,
        "usage": usage,
        "resolved_model": resolved_model,
        "provider_request_id": requested_id,
        "charged_requests": 1,
    }


def _sha256(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()
