#!/usr/bin/env python3
"""TypeSafe client with three modes: replay (default), live, Fake (tests).

- ``--replay``: read cached responses from ``audit/responses/<id>.json``.
  Needs no key. Verifies the stored request hash against the current
  state+questions and fails loudly on drift.
- ``--live``: POST each fixture's ``{model, state, questions}`` to
  ``POST https://api.typesafe.ai/v1/systemone`` with
  ``Authorization: Bearer <TYPESAFE_API_KEY>``. Refuses with a clear error
  when the env var is unset. Never prints, logs or stores the key or
  request headers.
- ``FakeClient``: test-only stub with the same ``evaluate`` interface.

Cache file format (one JSON file per fixture id). Stored fields only::

    fixture_id, request_hash, created_at, model_requested, response

where ``response`` is the API response body verbatim
(``model`` / ``answers`` / ``usage``). Top-level ``model`` and ``usage``
mirror the body for convenience. No headers, no key, no auth material.

Replay/analysis path is stdlib-only (json, urllib, hashlib, datetime).
The live path also uses stdlib (urllib), so no SDK install is needed.

Docs grounding: request/response shapes follow https://docs.typesafe.ai/api.md
(state, model, questions map; answers keyed by question id; usage with
input_tokens/output_tokens; 401/422/429/529 errors). One request carries all
four questions over shared state (parallel_questions cookbook).
"""
from __future__ import annotations

import datetime
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

from . import questions as Q
from . import state as S

ROOT = Path(__file__).resolve().parents[1]
RESPONSES_DIR = ROOT / "audit" / "responses"

API_KEY_ENV = "TYPESAFE_API_KEY"

# Cache keys that must never appear (case-insensitive exact match on any
# nested key, plus header/auth text in the raw file).
FORBIDDEN_CACHE_KEYS = {
    "headers", "authorization", "api_key", "apikey", "bearer",
    "secret", "credentials", "credential", "auth", "cookie", "set-cookie",
}


class LiveRefusedError(RuntimeError):
    """Raised when --live is requested without TYPESAFE_API_KEY set."""


def cache_path(fixture_id: str) -> Path:
    return RESPONSES_DIR / f"{fixture_id}.json"


def utcnow_iso() -> str:
    return (datetime.datetime.now(datetime.timezone.utc)
            .isoformat(timespec="seconds").replace("+00:00", "Z"))


def check_no_auth_material(obj: object) -> None:
    """Fail if any mapping key looks like headers/auth material."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).lower() in FORBIDDEN_CACHE_KEYS:
                raise ValueError(f"cache must not store {key!r}")
            check_no_auth_material(value)
    elif isinstance(obj, list):
        for item in obj:
            check_no_auth_material(item)


def save_cache(fixture_id: str, request_hash: str, model_requested: str,
               response_body: dict, created_at: str | None = None) -> Path:
    check_no_auth_material(response_body)
    doc = {
        "fixture_id": fixture_id,
        "request_hash": request_hash,
        "created_at": created_at or utcnow_iso(),
        "model_requested": model_requested,
        "model": response_body.get("model"),
        "usage": response_body.get("usage", {}),
        "response": response_body,
    }
    path = cache_path(fixture_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return path


def load_cache(fixture_id: str) -> dict:
    return json.loads(cache_path(fixture_id).read_text(encoding="utf-8"))


def current_request(fixture: dict, index=None, raw_cache=None) -> tuple[dict, str]:
    """Build (payload, hash) for one fixture with current code."""
    built_state = S.build_state(fixture, index, raw_cache)
    questions = Q.questions_for(fixture)
    payload = Q.build_payload(Q.MODEL, built_state, questions)
    digest = S.request_hash(payload["model"], payload["state"],
                            payload["questions"])
    return payload, digest


def verify_cache(fixture: dict, cached: dict, index=None,
                 raw_cache=None) -> dict:
    """Replay one cached response; fail loudly on request-hash drift."""
    _, digest = current_request(fixture, index, raw_cache)
    if cached.get("request_hash") != digest:
        raise ValueError(
            f"request drift for {fixture['id']}: cached "
            f"{cached.get('request_hash')} != current {digest} "
            f"(state+questions changed; do not trust this replay)")
    if cached.get("fixture_id") != fixture["id"]:
        raise ValueError(f"cache id mismatch: {cached.get('fixture_id')}")
    check_no_auth_material(cached)
    return cached


def replay_all(fixtures: list[dict]) -> list[tuple[dict, dict]]:
    """Replay every fixture; returns [(fixture, cached)] or raises."""
    index = S.load_sections()
    raw_cache: dict[str, str] = {}
    out = []
    for fixture in fixtures:
        cached = load_cache(fixture["id"])
        out.append((fixture, verify_cache(fixture, cached, index, raw_cache)))
    return out


class FakeClient:
    """Test-only stub. ``answers`` maps question id -> answer dict."""

    def __init__(self, answers: dict, model: str = "fake-test-1",
                 usage: dict | None = None):
        self._answers = answers
        self._model = model
        self._usage = usage or {"input_tokens": 0, "output_tokens": 0}

    def evaluate(self, payload: dict) -> dict:
        answers = {}
        for qid in payload["questions"]:
            if qid not in self._answers:
                raise KeyError(f"FakeClient has no answer for {qid}")
            answers[qid] = self._answers[qid]
        return {"model": self._model, "answers": answers,
                "usage": dict(self._usage)}

    def evaluate_and_cache(self, fixture: dict, index=None,
                           raw_cache=None) -> Path:
        payload, digest = current_request(fixture, index, raw_cache)
        body = self.evaluate(payload)
        return save_cache(fixture["id"], digest, payload["model"], body)


def _read_api_key() -> str:
    key = os.environ.get(API_KEY_ENV, "")
    if not key:
        raise LiveRefusedError(
            f"--live refuses: environment variable {API_KEY_ENV} is not set. "
            f"Replay with: python3 audit/run_audit.py --replay "
            f"(no key needed).")
    return key


def live_evaluate(payload: dict, api_key: str,
                  endpoint: str = Q.ENDPOINT, timeout: float = 120.0) -> dict:
    """POST one payload with stdlib urllib. Never logs the key/headers."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + api_key},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(
            f"live request failed: HTTP {exc.code} ({detail})") from exc


def live_all(fixtures: list[dict], api_key: str | None = None,
              limit: int | None = None) -> list[Path]:
    """Run the live audit and cache one response per fixture id."""
    key = api_key if api_key else _read_api_key()
    index = S.load_sections()
    raw_cache: dict[str, str] = {}
    paths = []
    for fixture in fixtures[:limit] if limit else fixtures:
        payload, digest = current_request(fixture, index, raw_cache)
        body = live_evaluate(payload, key)
        check_no_auth_material(body)
        paths.append(save_cache(fixture["id"], digest, payload["model"], body))
    return paths
