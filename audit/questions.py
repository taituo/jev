#!/usr/bin/env python3
"""The four review questions asked per claim in ONE request over shared state.

Single reviewable file. Wording follows the TypeSafe docs guidance
(https://docs.typesafe.ai/primitives/choice.md,
https://docs.typesafe.ai/primitives/noul.md,
https://docs.typesafe.ai/cookbooks/citation_check.md):

- one narrow judgment per question;
- Choice options each defined (no bare labels);
- Noul instructions phrased so a high value means "yes";
- no double negatives;
- state referenced with backticked paths (`` `claim` ``, `` `section` ``).

Q1 mirrors the citation_check cookbook's supports / contradicts /
says_nothing Choice. Q2/Q3 are speculative Nouls asked up front per the
parallel_questions cookbook (batching adds no answer change); code decides
which answers to use. Q4 is a second Choice on scope.

Two variants share Q1 semantics: ``QUESTIONS`` for single-section fixtures
(state fields ``claim`` / ``section``) and ``QUESTIONS_CONFLICT`` for
``real_standards_conflict`` fixtures (state fields ``claim`` /
``section_a`` / ``section_b``). Q1 verdict labels are identical in both so
analysis is uniform; conflicts are still reported separately (see
PREREGISTRATION.md) because the claim is judged against two sections.

Stdlib only. No network. No key.
"""
from __future__ import annotations

MODEL = "jev-latest"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"

Q1_ID = "q1_relation"
Q2_ID = "q2_verbatim"
Q3_ID = "q3_beyond"
Q4_ID = "q4_scope"

Q1_OPTIONS = ("supports", "contradicts", "says_nothing")
Q4_OPTIONS = ("fully", "partly", "outside")

QUESTIONS: dict = {
    Q1_ID: {
        "type": "choice",
        "instructions": "How does `section` relate to `claim`?",
        "criteria": {
            "supports": "The section states the claim or directly implies that it is true.",
            "contradicts": "The section states the opposite of the claim or implies that the claim is false.",
            "says_nothing": "The section does not address what the claim asserts, either way.",
        },
    },
    Q2_ID: {
        "type": "noul",
        "instructions": "Does `section` state `claim` in near-verbatim words?",
        "criteria": {
            "true": "The claim repeats the section wording with at most small rephrasing.",
            "false": "The claim uses different words or adds content not stated in the section.",
        },
    },
    Q3_ID: {
        "type": "noul",
        "instructions": "Does `claim` go beyond what `section` establishes?",
        "criteria": {
            "true": "The claim adds a requirement, number, or fact the section does not state.",
            "false": "Everything the claim asserts is established by the section.",
        },
    },
    Q4_ID: {
        "type": "choice",
        "instructions": "How much of `claim` falls within the scope of `section`?",
        "criteria": {
            "fully": "The whole claim is about the topic the section covers.",
            "partly": "Part of the claim is about the section topic and part is about something else.",
            "outside": "The claim is about a different topic than the section covers.",
        },
    },
}

QUESTIONS_CONFLICT: dict = {
    Q1_ID: {
        "type": "choice",
        "instructions": "How do `section_a` and `section_b` taken together relate to `claim`?",
        "criteria": {
            "supports": "The two sections together state the claim or directly imply that it is true.",
            "contradicts": "The two sections together state the opposite of the claim or imply that the claim is false.",
            "says_nothing": "The two sections together do not address what the claim asserts, either way.",
        },
    },
    Q2_ID: {
        "type": "noul",
        "instructions": "Does either `section_a` or `section_b` state `claim` in near-verbatim words?",
        "criteria": {
            "true": "The claim repeats wording from at least one of the two sections with at most small rephrasing.",
            "false": "The claim uses different words or adds content stated in neither section.",
        },
    },
    Q3_ID: {
        "type": "noul",
        "instructions": "Does `claim` go beyond what `section_a` and `section_b` together establish?",
        "criteria": {
            "true": "The claim adds a requirement, number, or fact the two sections together do not state.",
            "false": "Everything the claim asserts is established by the two sections together.",
        },
    },
    Q4_ID: {
        "type": "choice",
        "instructions": "How much of `claim` falls within the combined scope of `section_a` and `section_b`?",
        "criteria": {
            "fully": "The whole claim is about topics the two sections cover.",
            "partly": "Part of the claim is about the sections' topics and part is about something else.",
            "outside": "The claim is about a different topic than the two sections cover.",
        },
    },
}


def questions_for(fixture: dict) -> dict:
    """Return the question set for one fixture (conflict-aware)."""
    if fixture.get("label") == "real_standards_conflict":
        return QUESTIONS_CONFLICT
    return QUESTIONS


def build_payload(model: str, state: dict, questions: dict) -> dict:
    """Return the exact JSON body sent to POST /v1/systemone."""
    return {"model": model, "state": state, "questions": questions}
