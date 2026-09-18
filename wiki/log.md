# Wiki log

Append-only record. One `## [YYYY-MM-DD] <kind> | <subject>` heading per
event, newest at the bottom. Never rewrite history.

## [2026-09-18] ingest | RFC 7519, 7515, 7516, 6749, 6750, 8725

- Fetched six RFC .txt files from rfc-editor.org and pinned SHA-256.
- Generated derived/sections.json with stable section IDs.
- Added six source summaries and five concept pages with section citations.
- Added fixtures/claims.jsonl with 40 frozen labelled claims.
- Added deterministic validation tests.

## [2026-09-18] lint | initial self-check

- Verified every RFC citation resolves to derived/sections.json.
- Verified claims fixture counts and label balance.
- Verified checksums and section index reproducibility.

## [2026-09-18] repair | section-scoped quote checks and c021

- Tightened quote tests to char_start/char_end section slices.
- Corrected c021 citation from RFC 6749 section 1.4 to section 1.
- Added fixtures/FROZEN.md, LICENSE, and analyses/impressed-but-skeptical.md.
