#!/usr/bin/env python3
"""Deterministic validation for Slice 1. Stdlib only, no network, no keys."""
from __future__ import annotations

import hashlib
import json
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_DIR = ROOT / "raw" / "sources"
DERIVED = ROOT / "derived" / "sections.json"
CLAIMS = ROOT / "fixtures" / "claims.jsonl"
WIKI = ROOT / "wiki"
CHECKSUMS = SOURCES_DIR / "SHA256SUMS"

RFCs = ["7519", "7515", "7516", "6749", "6750", "8725"]
CIT_RE = re.compile(r"RFC\s+(7519|7515|7516|6749|6750|8725)\s+§(\d+(?:\.\d+)*)")
ALLOWED_LABELS = {
    "supported",
    "fabricated_quote",
    "contradicted",
    "unsupported",
    "wrong_section",
    "real_standards_conflict",
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sections():
    payload = json.loads(DERIVED.read_text(encoding="utf-8"))
    return payload["sections"]


def load_claims():
    out = []
    for line in CLAIMS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


class TestChecksums(unittest.TestCase):
    def test_checksum_file_covers_all_rfcs(self):
        text = CHECKSUMS.read_text(encoding="utf-8")
        for num in RFCs:
            self.assertIn(f"rfc{num}.txt", text, f"missing pin for rfc{num}")

    def test_raw_files_match_pins(self):
        pinned = {}
        for line in CHECKSUMS.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            sha, name = line.split()
            pinned[name] = sha
        for num in RFCs:
            p = SOURCES_DIR / f"rfc{num}.txt"
            self.assertTrue(p.exists(), f"missing {p}")
            self.assertEqual(sha256_of(p), pinned[f"rfc{num}.txt"])


class TestSections(unittest.TestCase):
    def test_index_exists_and_sorted(self):
        secs = load_sections()
        self.assertGreaterEqual(len(secs), 100, "unexpectedly few sections")
        keys = [(s["rfc"], [int(x) for x in s["section"].split(".")]) for s in secs]
        self.assertEqual(keys, sorted(keys), "sections must be sorted")
        ids = [s["stable_id"] for s in secs]
        self.assertEqual(len(ids), len(set(ids)), "stable_id must be unique")
        for s in secs:
            self.assertEqual(s["stable_id"], f"rfc{s['rfc']}-s{s['section']}")

    def test_section_hashes_match_source_slices(self):
        secs = load_sections()
        cache = {}
        for s in secs[:50]:  # sample for speed, plus full stable_id check elsewhere
            rfc = s["rfc"]
            if rfc not in cache:
                cache[rfc] = (SOURCES_DIR / f"rfc{rfc}.txt").read_text(
                    encoding="utf-8", errors="replace"
                )
            body = cache[rfc][s["char_start"] : s["char_end"]]
            self.assertEqual(hashlib.sha256(body.encode("utf-8")).hexdigest(), s["sha256"])


class TestClaims(unittest.TestCase):
    def test_exactly_40_and_ids(self):
        claims = load_claims()
        self.assertEqual(len(claims), 40, "must freeze exactly 40 claims")
        ids = [c["id"] for c in claims]
        self.assertEqual(len(ids), len(set(ids)), "claim ids must be unique")
        self.assertEqual(ids, [f"c{i:03d}" for i in range(1, 41)])

    def test_label_balance(self):
        claims = load_claims()
        counts = Counter(c["label"] for c in claims)
        self.assertEqual(set(counts) - ALLOWED_LABELS, set())
        self.assertEqual(counts["supported"], 26)
        self.assertEqual(counts["real_standards_conflict"], 4)
        defects = sum(counts[k] for k in ("fabricated_quote", "contradicted", "unsupported", "wrong_section"))
        self.assertEqual(defects, 10)
        for k in ("fabricated_quote", "contradicted", "unsupported", "wrong_section"):
            self.assertGreaterEqual(counts[k], 2, f"need at least 2 of {k}")

    def test_claim_shape(self):
        for c in load_claims():
            self.assertIn(c["label"], ALLOWED_LABELS)
            self.assertTrue(c["text"].strip())
            self.assertTrue(c["rationale"].strip(), f"{c['id']} needs one-line rationale")
            self.assertIn(c["rfc"], RFCs)
            self.assertRegex(c["section"], r"^\d+(?:\.\d+)*$")
            if c["label"] == "real_standards_conflict":
                self.assertIn(c.get("rfc2"), RFCs)
                self.assertRegex(c.get("section2", ""), r"^\d+(?:\.\d+)*$")
                self.assertTrue({c["rfc"], c["rfc2"]} >= {"7519", "8725"} or "8725" in {c["rfc"], c["rfc2"]},
                                "conflicts must involve RFC 8725 vs RFC 7519")

    def test_claim_sections_resolve(self):
        secs = {(s["rfc"], s["section"]) for s in load_sections()}
        for c in load_claims():
            self.assertIn((c["rfc"], c["section"]), secs, f"{c['id']} primary section missing")
            if c["label"] == "real_standards_conflict":
                self.assertIn((c["rfc2"], c["section2"]), secs, f"{c['id']} secondary missing")

    def test_quotes_section_scoped(self):
        raws = {n: (SOURCES_DIR / f"rfc{n}.txt").read_text(encoding="utf-8", errors="replace") for n in RFCs}
        sec_index = {(s["rfc"], s["section"]): s for s in load_sections()}

        def section_text(rfc, section):
            s = sec_index[(rfc, section)]
            return raws[rfc][s["char_start"] : s["char_end"]]

        for c in load_claims():
            q = c.get("quote", "")
            label = c["label"]
            self.assertTrue(q, f"{c['id']} quote must be non-empty")
            primary = section_text(c["rfc"], c["section"])
            if label in ("supported", "contradicted"):
                self.assertIn(q, primary, f"{c['id']} quote must occur in cited section rfc{c['rfc']} s{c['section']}")
            elif label == "real_standards_conflict":
                secondary = section_text(c["rfc2"], c["section2"])
                self.assertTrue(
                    q in primary or q in secondary,
                    f"{c['id']} quote must occur in at least one cited section",
                )
            elif label == "wrong_section":
                self.assertIn(q, raws[c["rfc"]], f"{c['id']} quote must occur somewhere in rfc{c['rfc']}")
                self.assertNotIn(q, primary, f"{c['id']} quote must NOT occur in cited section")
            elif label in ("fabricated_quote", "unsupported"):
                self.assertNotIn(q, primary, f"{c['id']} quote must be absent from cited section")
                for n, t in raws.items():
                    self.assertNotIn(q, t, f"{c['id']} quote must be absent from rfc{n}")


class TestWiki(unittest.TestCase):
    def test_required_pages_exist(self):
        for rel in [
            "index.md",
            "log.md",
            "sources/rfc7519.md",
            "sources/rfc7515.md",
            "sources/rfc7516.md",
            "sources/rfc6749.md",
            "sources/rfc6750.md",
            "sources/rfc8725.md",
            "concepts/jwt-claims.md",
            "concepts/jose-header.md",
            "concepts/oauth-grants.md",
            "concepts/bearer-usage.md",
            "concepts/jwt-security-practices.md",
        ]:
            self.assertTrue((WIKI / rel).exists(), f"missing wiki/{rel}")
        self.assertTrue((ROOT / "AGENTS.md").exists())

    def test_citations_resolve(self):
        secs = {(s["rfc"], s["section"]) for s in load_sections()}
        md_files = sorted(WIKI.rglob("*.md"))
        self.assertGreater(len(md_files), 5)
        total = 0
        for p in md_files:
            for m in CIT_RE.finditer(p.read_text(encoding="utf-8", errors="replace")):
                total += 1
                self.assertIn((m.group(1), m.group(2)), secs, f"{p.name}: unknown citation {m.group(0)}")
        self.assertGreaterEqual(total, 40, "wiki must contain at least 40 resolvable citations")

    def test_log_format(self):
        log = (WIKI / "log.md").read_text(encoding="utf-8")
        headings = [l for l in log.splitlines() if l.startswith("## [")]
        self.assertGreaterEqual(len(headings), 1)
        for h in headings:
            self.assertRegex(h, r"^## \[\d{4}-\d{2}-\d{2}\] \w+ \| .+")


if __name__ == "__main__":
    unittest.main()
