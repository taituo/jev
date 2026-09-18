#!/usr/bin/env python3
"""Reproducibly fetch the pinned RFC text sources from rfc-editor.org.

Usage:
    python3 scripts/fetch_rfcs.py [--check-only]

Behavior:
    - Downloads each RFC .txt from https://www.rfc-editor.org/rfc/rfcNNNN.txt
    - Writes to raw/sources/rfcNNNN.txt (binary-exact server bytes)
    - Verifies SHA-256 against raw/sources/SHA256SUMS
    - Exits non-zero on any mismatch or download failure

No API keys, no third-party dependencies, stdlib only.
"""
from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_DIR = ROOT / "raw" / "sources"
CHECKSUMS_FILE = SOURCES_DIR / "SHA256SUMS"

RFCs = ["7519", "7515", "7516", "6749", "6750", "8725"]
BASE_URL = "https://www.rfc-editor.org/rfc/rfc{num}.txt"


def load_pinned_checksums() -> dict[str, str]:
    pinned: dict[str, str] = {}
    for line in CHECKSUMS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            raise ValueError(f"Bad checksum line: {line!r}")
        sha, name = parts
        pinned[name] = sha
    return pinned


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_one(num: str) -> bytes:
    url = BASE_URL.format(num=num)
    req = urllib.request.Request(url, headers={"User-Agent": "audited-wiki-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} for {url}")
        return resp.read()


def main() -> int:
    check_only = "--check-only" in sys.argv
    if not CHECKSUMS_FILE.exists():
        print(f"Missing {CHECKSUMS_FILE}", file=sys.stderr)
        return 2
    pinned = load_pinned_checksums()
    ok = True
    for num in RFCs:
        fname = f"rfc{num}.txt"
        dest = SOURCES_DIR / fname
        expected = pinned.get(fname)
        if expected is None:
            print(f"No pinned checksum for {fname}", file=sys.stderr)
            ok = False
            continue
        if check_only:
            if not dest.exists():
                print(f"Missing {dest}", file=sys.stderr)
                ok = False
                continue
        else:
            print(f"Fetching rfc{num} ...")
            try:
                data = fetch_one(num)
            except Exception as e:  # noqa: BLE001 - report and continue
                print(f"Fetch failed for rfc{num}: {e}", file=sys.stderr)
                ok = False
                continue
            dest.write_bytes(data)
        actual = sha256_of(dest)
        if actual != expected:
            print(
                f"Checksum mismatch for {fname}:\n  expected {expected}\n  actual   {actual}",
                file=sys.stderr,
            )
            ok = False
        else:
            print(f"OK {fname} {actual}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
