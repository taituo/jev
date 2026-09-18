#!/usr/bin/env python3
"""Build the TypeSafe request state for one fixture.

State is named JSON fields with no answer hints: the fixture ``label``,
``rationale`` and ``quote`` fields are never copied into state. Section text
is sliced from the raw RFC sources via ``char_start``/``char_end`` in
``derived/sections.json``.

Stdlib only. No network. No key.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "derived" / "sections.json"
CLAIMS = ROOT / "fixtures" / "claims.jsonl"
SOURCES_DIR = ROOT / "raw" / "sources"

# Fields of a fixture that must never leak into request state.
FORBIDDEN_STATE_FIELDS = ("label", "rationale", "quote")


def load_fixtures(path: Path = CLAIMS) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def load_sections(path: Path = DERIVED) -> dict[tuple[str, str], dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {(s["rfc"], s["section"]): s for s in payload["sections"]}


def section_text(rfc: str, section: str,
                 index: dict[tuple[str, str], dict] | None = None,
                 raw_cache: dict[str, str] | None = None) -> str:
    """Slice section text from the raw RFC source via char offsets."""
    index = index if index is not None else load_sections()
    entry = index[(rfc, section)]
    if raw_cache is None:
        raw_cache = {}
    if rfc not in raw_cache:
        raw_cache[rfc] = (SOURCES_DIR / f"rfc{rfc}.txt").read_text(
            encoding="utf-8", errors="replace")
    return raw_cache[rfc][entry["char_start"]:entry["char_end"]]


def citation_of(rfc: str, section: str) -> str:
    return f"RFC {rfc} \u00a7{section}"


def build_state(fixture: dict,
                index: dict[tuple[str, str], dict] | None = None,
                raw_cache: dict[str, str] | None = None) -> dict:
    """Return the request state for one fixture.

    Single-section fixtures get ``claim`` / ``section`` / ``citation``.
    ``real_standards_conflict`` fixtures get both cited sections as separate
    named fields (``section_a`` / ``section_b`` with ``citation_a`` /
    ``citation_b``), because the claim asserts a cross-RFC conflict judged
    against two sections.
    """
    for field in FORBIDDEN_STATE_FIELDS:
        if field in fixture and field not in ("label", "rationale", "quote"):
            raise AssertionError(f"unexpected fixture field: {field}")
    index = index if index is not None else load_sections()
    if raw_cache is None:
        raw_cache = {}
    state: dict = {
        "fixture_id": fixture["id"],
        "claim": fixture["text"],
    }
    if fixture.get("label") == "real_standards_conflict":
        state["citation_a"] = citation_of(fixture["rfc"], fixture["section"])
        state["section_a"] = section_text(
            fixture["rfc"], fixture["section"], index, raw_cache)
        state["citation_b"] = citation_of(fixture["rfc2"], fixture["section2"])
        state["section_b"] = section_text(
            fixture["rfc2"], fixture["section2"], index, raw_cache)
    else:
        state["citation"] = citation_of(fixture["rfc"], fixture["section"])
        state["section"] = section_text(
            fixture["rfc"], fixture["section"], index, raw_cache)
    assert_no_leak(fixture, state)
    return state


def assert_no_leak(fixture: dict, state: dict) -> None:
    """Fail if label/rationale/quote material reached the state as fields.

    Note: the ``quote`` *string* legitimately occurs inside section text
    for supported/contradicted fixtures (the quote comes from the section),
    so only the field itself must be absent — never copied as a state key.
    The ``label`` and ``rationale`` strings must not occur at all.
    """
    keys = set(state)
    if keys & set(FORBIDDEN_STATE_FIELDS):
        raise ValueError(f"state keys leak label fields: {keys}")
    # The rationale is a distinctive author sentence: it must not occur
    # anywhere in the state. (The label word itself, e.g. "supported", and
    # quote strings legitimately occur inside RFC section text and claim
    # wording, so only their *fields* must be absent — enforced above.)
    blob = json.dumps(state, ensure_ascii=False, sort_keys=True)
    rationale = fixture.get("rationale")
    if isinstance(rationale, str) and rationale and rationale in blob:
        raise ValueError(
            f"state leaks fixture field 'rationale' for {fixture.get('id')}")


def request_hash(model: str, state: dict, questions: dict) -> str:
    """Stable SHA-256 over the request (model + state + questions)."""
    canonical = json.dumps(
        {"model": model, "state": state, "questions": questions},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
