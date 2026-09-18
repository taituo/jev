#!/usr/bin/env python3
"""Deterministic RFC section splitter with stable IDs.

Usage:
    python3 scripts/split_sections.py [--stdout]

Reads:
    raw/sources/rfcNNNN.txt for NNNN in 7519, 7515, 7516, 6749, 6750, 8725

Writes:
    derived/sections.json — one record per detected section:
      {
        "rfc": "7519",
        "section": "4.1.4",
        "stable_id": "rfc7519-s4.1.4",
        "title": "\"exp\" (Expiration Time) Claim",
        "char_start": 1234,
        "char_end": 2345,
        "sha256": "<sha256 of section text slice>"
      }

Rules (deliberately simple and deterministic):
    - A heading is a line matching ^(\\d+(?:\\.\\d+)*)\\.\\s+(\\S.*)\\s*$
    - Table-of-contents lines are excluded: any heading-looking line
      containing ". . ." (dot-leader page numbers) is skipped.
    - Page-header/footer lines are kept as section content; only headings
      define boundaries. This keeps char offsets reproducible.
    - stable_id is f"rfc{rfc}-s{section}" (dots preserved).

Stdlib only. No network. Deterministic key order in output JSON.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_DIR = ROOT / "raw" / "sources"
OUT_FILE = ROOT / "derived" / "sections.json"

RFCs = ["7519", "7515", "7516", "6749", "6750", "8725"]
HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.\s+(\S.*)\s*$")


def split_text(rfc: str, text: str) -> list[dict]:
    lines = text.splitlines(keepends=True)
    # Precompute char offset of each line start.
    offsets: list[int] = []
    pos = 0
    for ln in lines:
        offsets.append(pos)
        pos += len(ln)

    headings: list[tuple[int, str, str]] = []  # (line_idx, section, title)
    for i, ln in enumerate(lines):
        stripped = ln.rstrip("\r\n")
        # Skip TOC dot-leader lines.
        if ". . ." in stripped:
            continue
        m = HEADING_RE.match(stripped)
        if not m:
            continue
        sec, title = m.group(1), m.group(2).strip()
        # Skip the RFC boilerplate "STD 80, RFC 20" style false positives:
        # require the title to start with a non-dot char and the line to
        # not look like a reference entry (those are indented).
        if ln.startswith(" ") or ln.startswith("\t"):
            continue
        headings.append((i, sec, title))

    records: list[dict] = []
    for idx, (line_idx, sec, title) in enumerate(headings):
        start = offsets[line_idx]
        if idx + 1 < len(headings):
            end = offsets[headings[idx + 1][0]]
        else:
            end = len(text)
        body = text[start:end]
        records.append(
            {
                "rfc": rfc,
                "section": sec,
                "stable_id": f"rfc{rfc}-s{sec}",
                "title": title,
                "char_start": start,
                "char_end": end,
                "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            }
        )
    return records


def main() -> int:
    want_stdout = "--stdout" in sys.argv
    all_records: list[dict] = []
    for rfc in RFCs:
        src = SOURCES_DIR / f"rfc{rfc}.txt"
        if not src.exists():
            print(f"Missing source {src}; run scripts/fetch_rfcs.py first", file=sys.stderr)
            return 2
        text = src.read_text(encoding="utf-8", errors="replace")
        all_records.extend(split_text(rfc, text))
    all_records.sort(key=lambda r: (r["rfc"], [int(x) for x in r["section"].split(".")]))
    payload = {"generator": "scripts/split_sections.py v1", "sections": all_records}
    out = json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    if want_stdout:
        sys.stdout.write(out)
    else:
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.write_text(out, encoding="utf-8")
        print(f"Wrote {OUT_FILE} ({len(all_records)} sections)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
