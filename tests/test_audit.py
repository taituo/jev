#!/usr/bin/env python3
"""Tests for the project-1 offline audit harness.

Stdlib unittest only. No network. No key.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

from audit import analyze as A
from audit import client as C
from audit import questions as Q
from audit import state as S

FORBIDDEN_KEY_RE = re.compile(r"sk-[A-Za-z0-9]{16,}")
HARDCODED_KEY_RE = re.compile(r"api_key\s*=\s*[\"'][^\"']+[\"']")


def make_cached(choice, conf, probs, q2=0.5, q3=0.5, q4="fully",
                model="fake-test-1"):
    return {
        "fixture_id": "t",
        "request_hash": "h",
        "created_at": "2026-01-01T00:00:00Z",
        "model_requested": "jev-latest",
        "model": model,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "response": {
            "model": model,
            "answers": {
                Q.Q1_ID: {"type": "choice", "choice": choice,
                          "confidence": conf, "probabilities": probs},
                Q.Q2_ID: {"type": "noul", "noul": q2},
                Q.Q3_ID: {"type": "noul", "noul": q3},
                Q.Q4_ID: {"type": "choice", "choice": q4, "confidence": 0.7,
                          "probabilities": {"fully": 0.7, "partly": 0.2,
                                            "outside": 0.1}},
            },
            "usage": {"input_tokens": 1, "output_tokens": 1},
        },
    }


def make_pair(fid, label, choice, conf, probs, q2=0.5, q3=0.5):
    fixture = {"id": fid, "label": label}
    cached = make_cached(choice, conf, probs, q2, q3)
    cached["fixture_id"] = fid
    return fixture, cached


class TestBuildState(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = S.load_fixtures()
        cls.index = S.load_sections()
        cls.raw_cache: dict[str, str] = {}

    def test_all_40_states_leak_no_label_fields(self):
        self.assertEqual(len(self.fixtures), 40)
        for fixture in self.fixtures:
            with self.subTest(fixture=fixture["id"]):
                st = S.build_state(fixture, self.index, self.raw_cache)
                self.assertEqual(set(st) & {"label", "rationale", "quote"}, set())
                blob = json.dumps(st, ensure_ascii=False, sort_keys=True)
                # The rationale is a distinctive author sentence and must be
                # absent entirely. Label/quote *words* legitimately occur
                # inside RFC text and claim wording, so only their fields
                # (checked above) must be absent.
                self.assertNotIn(fixture["rationale"], blob,
                                 f"{fixture['id']} leaks rationale")
                self.assertIn(fixture["text"], blob)

    def test_single_section_slices_exact_raw_chars(self):
        fixture = next(f for f in self.fixtures if f["id"] == "c001")
        st = S.build_state(fixture, self.index, self.raw_cache)
        raw = (ROOT / "raw" / "sources" / "rfc7519.txt").read_text(
            encoding="utf-8", errors="replace")
        entry = self.index[("7519", "1")]
        self.assertEqual(st["section"],
                         raw[entry["char_start"]:entry["char_end"]])
        self.assertEqual(st["citation"], "RFC 7519 \u00a71")
        self.assertIn("claim", st)
        self.assertNotIn("section_a", st)

    def test_conflict_has_both_sections_as_named_fields(self):
        fixture = next(f for f in self.fixtures if f["id"] == "c037")
        st = S.build_state(fixture, self.index, self.raw_cache)
        for key in ("section_a", "section_b", "citation_a", "citation_b",
                    "claim", "fixture_id"):
            self.assertIn(key, st, f"conflict state missing {key}")
        self.assertNotIn("section", st)
        raw7519 = (ROOT / "raw" / "sources" / "rfc7519.txt").read_text(
            encoding="utf-8", errors="replace")
        raw8725 = (ROOT / "raw" / "sources" / "rfc8725.txt").read_text(
            encoding="utf-8", errors="replace")
        a = self.index[("7519", "6")]
        b = self.index[("8725", "3.2")]
        self.assertEqual(st["section_a"], raw7519[a["char_start"]:a["char_end"]])
        self.assertEqual(st["section_b"], raw8725[b["char_start"]:b["char_end"]])


class TestQuestions(unittest.TestCase):
    def test_q1_options_and_definitions(self):
        q1 = Q.QUESTIONS[Q.Q1_ID]
        self.assertEqual(q1["type"], "choice")
        self.assertEqual(set(q1["criteria"]),
                         {"supports", "contradicts", "says_nothing"})
        for option, rubric in q1["criteria"].items():
            self.assertTrue(isinstance(rubric, str) and rubric.strip(),
                            f"Q1 option {option} needs a definition")

    def test_q4_options_and_definitions(self):
        q4 = Q.QUESTIONS[Q.Q4_ID]
        self.assertEqual(q4["type"], "choice")
        self.assertEqual(set(q4["criteria"]), {"fully", "partly", "outside"})
        for option, rubric in q4["criteria"].items():
            self.assertTrue(isinstance(rubric, str) and rubric.strip(),
                            f"Q4 option {option} needs a definition")

    def test_noul_criteria_and_yes_means_high(self):
        for qid in (Q.Q2_ID, Q.Q3_ID):
            question = Q.QUESTIONS[qid]
            self.assertEqual(question["type"], "noul")
            self.assertIn("true", question["criteria"])
            self.assertIn("false", question["criteria"])

    def test_no_double_negatives_in_instructions(self):
        for qid, question in Q.QUESTIONS.items():
            text = question["instructions"].lower()
            self.assertNotIn(" not ", text, f"{qid} has a negation")
            self.assertNotIn("never", text, f"{qid} has a negation")
            self.assertNotIn("no ", text.split("`")[0],
                             f"{qid} instruction starts with a negative")

    def test_conflict_variant_keeps_q1_labels(self):
        q1 = Q.QUESTIONS_CONFLICT[Q.Q1_ID]
        self.assertEqual(set(q1["criteria"]),
                         {"supports", "contradicts", "says_nothing"})


class TestFakeRoundTrip(unittest.TestCase):
    def test_fake_client_round_trips_cache_format(self):
        fixture = S.load_fixtures()[0]
        answers = {
            Q.Q1_ID: {"type": "choice", "choice": "supports",
                      "confidence": 0.95,
                      "probabilities": {"supports": 0.95, "contradicts": 0.03,
                                        "says_nothing": 0.02}},
            Q.Q2_ID: {"type": "noul", "noul": 0.8},
            Q.Q3_ID: {"type": "noul", "noul": 0.1},
            Q.Q4_ID: {"type": "choice", "choice": "fully", "confidence": 0.9,
                      "probabilities": {"fully": 0.9, "partly": 0.07,
                                        "outside": 0.03}},
        }
        fake = C.FakeClient(answers)
        with tempfile.TemporaryDirectory() as tmp:
            old = C.RESPONSES_DIR
            C.RESPONSES_DIR = Path(tmp)
            try:
                path = fake.evaluate_and_cache(fixture)
                cached = json.loads(Path(path).read_text(encoding="utf-8"))
            finally:
                C.RESPONSES_DIR = old
        for key in ("fixture_id", "request_hash", "created_at",
                    "model_requested", "model", "usage", "response"):
            self.assertIn(key, cached, f"cache missing {key}")
        self.assertEqual(cached["fixture_id"], fixture["id"])
        self.assertEqual(cached["response"]["answers"], answers)
        self.assertEqual(cached["response"]["usage"],
                         {"input_tokens": 0, "output_tokens": 0})
        payload, digest = C.current_request(fixture)
        self.assertEqual(cached["request_hash"], digest)
        C.check_no_auth_material(cached)


class TestReplayDrift(unittest.TestCase):
    def test_replay_detects_request_hash_drift(self):
        fixture = S.load_fixtures()[1]
        answers = {
            Q.Q1_ID: {"type": "choice", "choice": "supports",
                      "confidence": 0.9,
                      "probabilities": {"supports": 0.9, "contradicts": 0.05,
                                        "says_nothing": 0.05}},
            Q.Q2_ID: {"type": "noul", "noul": 0.5},
            Q.Q3_ID: {"type": "noul", "noul": 0.5},
            Q.Q4_ID: {"type": "choice", "choice": "fully", "confidence": 0.9,
                      "probabilities": {"fully": 0.9, "partly": 0.05,
                                        "outside": 0.05}},
        }
        fake = C.FakeClient(answers)
        with tempfile.TemporaryDirectory() as tmp:
            old = C.RESPONSES_DIR
            C.RESPONSES_DIR = Path(tmp)
            try:
                fake.evaluate_and_cache(fixture)
                cached = C.load_cache(fixture["id"])
                C.verify_cache(fixture, cached)  # no drift: passes
                original = Q.QUESTIONS[Q.Q1_ID]["instructions"]
                Q.QUESTIONS[Q.Q1_ID]["instructions"] = (
                    "CHANGED instructions that alter the request hash")
                try:
                    with self.assertRaises(ValueError) as ctx:
                        C.verify_cache(fixture, cached)
                finally:
                    Q.QUESTIONS[Q.Q1_ID]["instructions"] = original
            finally:
                C.RESPONSES_DIR = old
        self.assertIn("drift", str(ctx.exception).lower())


class TestLiveRefuses(unittest.TestCase):
    def test_live_refuses_without_env_var(self):
        fixture = S.load_fixtures()[0]
        env = {k: v for k, v in os.environ.items()
               if k != C.API_KEY_ENV}
        old = dict(os.environ)
        os.environ.clear()
        os.environ.update(env)
        try:
            with self.assertRaises(C.LiveRefusedError) as ctx:
                C.live_all([fixture])
        finally:
            os.environ.clear()
            os.environ.update(old)
        self.assertIn(C.API_KEY_ENV, str(ctx.exception))

    def test_no_hardcoded_key_in_audit_sources(self):
        for path in sorted((ROOT / "audit").glob("*.py")):
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(FORBIDDEN_KEY_RE.search(text),
                              f"{path.name} looks like a hardcoded key")
            self.assertIsNone(HARDCODED_KEY_RE.search(text),
                              f"{path.name} hardcodes an api key")

    def test_replay_path_is_stdlib_only(self):
        banned = ("typesafe_sdk", "import requests", "httpx", "urllib3",
                  "openai", "anthropic")
        for path in sorted((ROOT / "audit").glob("*.py")):
            text = path.read_text(encoding="utf-8")
            for token in banned:
                self.assertNotIn(token, text, f"{path.name} uses {token}")


def _probs(choice):
    return {k: (0.9 if k == choice else 0.05) for k in
            ("supports", "contradicts", "says_nothing")}


class TestAnalyzeSynthetic(unittest.TestCase):
    # Hand-computed reference set (6 headline records):
    # t01 supported/supports 0.95 -> correct, unflagged, high bucket
    # t02 supported/says_nothing 0.92 -> wrong, flagged, high bucket
    # t03 fabricated_quote/says_nothing 0.85 -> correct, flagged, low bucket
    # t04 unsupported/supports 0.99 -> wrong, unflagged, high bucket
    # t05 contradicted/contradicts 0.50 -> correct, flagged, low bucket
    # t06 supported/supports 0.60 -> correct, unflagged, low bucket
    # Expected: accuracy 4/6; flagged defects 2/3; flagged supported 1/3;
    # high bucket n=3 precision 1/3; low bucket n=3 precision 3/3;
    # gap = (1/3 - 1)*100 = -66.67pp; triage: none reaches 95%.
    @classmethod
    def setUpClass(cls):
        pairs = [
            make_pair("t01", "supported", "supports", 0.95,
                      _probs("supports"), q2=0.9, q3=0.1),
            make_pair("t02", "supported", "says_nothing", 0.92,
                      _probs("says_nothing"), q2=0.2, q3=0.8),
            make_pair("t03", "fabricated_quote", "says_nothing", 0.85,
                      _probs("says_nothing"), q2=0.1, q3=0.9),
            make_pair("t04", "unsupported", "supports", 0.99,
                      _probs("supports"), q2=0.8, q3=0.2),
            make_pair("t05", "contradicted", "contradicts", 0.50,
                      _probs("contradicts"), q2=0.3, q3=0.7),
            make_pair("t06", "supported", "supports", 0.60,
                      _probs("supports"), q2=0.95, q3=0.05),
        ]
        cls.records = A.to_records(pairs)
        cls.metrics = A.compute_metrics(cls.records)

    def test_overall_counts(self):
        m = self.metrics
        self.assertEqual(m["n_headline"], 6)
        self.assertEqual(m["n_supported"], 3)
        self.assertEqual(m["n_defects"], 3)
        self.assertAlmostEqual(m["accuracy_headline"], 4 / 6)
        self.assertEqual(m["flagged_defects"], 2)
        self.assertEqual(m["flagged_supported"], 1)
        self.assertAlmostEqual(m["detection_rate"], 2 / 3)
        self.assertAlmostEqual(m["false_flag_rate"], 1 / 3)

    def test_confusion_matrix(self):
        cm = self.metrics["confusion"]
        self.assertEqual(cm["supports"], {"supports": 2, "contradicts": 0,
                                          "says_nothing": 1})
        self.assertEqual(cm["says_nothing"], {"supports": 1, "contradicts": 0,
                                              "says_nothing": 1})
        self.assertEqual(cm["contradicts"], {"supports": 0, "contradicts": 1,
                                             "says_nothing": 0})

    def test_confidence_buckets(self):
        b = self.metrics["confidence_buckets"]
        self.assertEqual(b["high"]["n"], 3)
        self.assertEqual(b["high"]["correct"], 1)
        self.assertAlmostEqual(b["high"]["precision"], 1 / 3)
        self.assertEqual(b["low"]["n"], 3)
        self.assertEqual(b["low"]["correct"], 3)
        self.assertAlmostEqual(b["low"]["precision"], 1.0)
        self.assertAlmostEqual(b["gap_pp"], (1 / 3 - 1.0) * 100)

    def test_triage_none_reaches_target(self):
        tri = self.metrics["triage"]
        self.assertIsNone(tri["threshold"])
        self.assertIn("no ", tri["statement"].lower())
        self.assertIn("95%", tri["statement"])

    def test_noul_sweeps_at_0_5(self):
        q3 = {r["threshold"]: r for r in self.metrics["noul_q3_sweep"]}[0.5]
        self.assertEqual(q3["positives"], 3)  # t02, t03, t05
        self.assertEqual(q3["positives_flagged"], 3)
        self.assertEqual(q3["positives_not_flagged"], 0)
        q2 = {r["threshold"]: r for r in self.metrics["noul_q2_sweep"]}[0.5]
        self.assertEqual(q2["positives"], 3)  # t01, t04, t06
        self.assertEqual(q2["positives_flagged"], 0)
        self.assertEqual(q2["positives_not_flagged"], 3)

    def test_per_class_table(self):
        pc = self.metrics["per_class"]
        self.assertEqual(pc["supported"], {"n": 3, "correct": 2, "flagged": 1})
        self.assertEqual(pc["fabricated_quote"],
                         {"n": 1, "correct": 1, "flagged": 1})
        self.assertEqual(pc["unsupported"],
                         {"n": 1, "correct": 0, "flagged": 0})
        self.assertEqual(pc["contradicted"],
                         {"n": 1, "correct": 1, "flagged": 1})

    def test_markdown_renders_tables(self):
        md = A.render_markdown(self.metrics)
        for heading in ("## Overall", "## Per class", "## Confusion matrix",
                        "## Choice confidence buckets", "## Triage curve",
                        "## Noul threshold sweep",
                        "## Real standards conflicts"):
            self.assertIn(heading, md)


class TestCacheHygiene(unittest.TestCase):
    def test_repo_responses_hold_no_responses_yet(self):
        files = sorted((ROOT / "audit" / "responses").iterdir())
        names = [p.name for p in files]
        self.assertEqual(names, [".gitkeep"], f"unexpected files: {names}")

    def test_no_auth_text_in_repo_cache_or_docs(self):
        for path in (ROOT / "audit" / "responses").iterdir():
            text = path.read_text(encoding="utf-8", errors="replace")
            self.assertNotIn("Authorization", text)
            self.assertNotIn("Bearer", text)
            self.assertNotIn("api_key", text.lower())


if __name__ == "__main__":
    unittest.main()
