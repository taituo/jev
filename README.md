# Audited LLM Wiki (Slice 1)

A small, public, fully reproducible wiki over six RFCs, built for audit
experiments. No database, no embeddings, no UI, no API keys.

## Scope

RFCs (verbatim `.txt` from rfc-editor.org):

- 7519 JWT, 7515 JWS, 7516 JWE, 6749 OAuth 2.0, 6750 Bearer usage, 8725 JWT BCP

What Slice 1 is:

- Reproducible fetch with pinned SHA-256 (`scripts/fetch_rfcs.py`).
- Deterministic section splitter with stable IDs (`derived/sections.json`).
- Hand-reviewed wiki summaries and concepts where every factual claim
  cites `RFC NNNN §X.Y`.
- Frozen audit fixture (`fixtures/claims.jsonl`): exactly 40 claims —
  26 supported, 10 planted defects (≥2 each of fabricated_quote,
  contradicted, unsupported, wrong_section), 4 real RFC 8725 vs RFC 7519
  conflicts.
- Deterministic stdlib tests. No network. No TypeSafe/Jev calls.

What Slice 1 is not:

- Not an audit harness. No judge, no scores, no model calls.
- Not a product wiki. No crawler, no autosync, no multi-writer.

## Layout

```text
raw/sources/       immutable RFC .txt + SHA256SUMS
derived/           generated sections.json (stable IDs)
wiki/              index.md, log.md, sources/, concepts/
fixtures/          claims.jsonl (frozen 40)
scripts/           fetch_rfcs.py, split_sections.py
tests/             deterministic validation
AGENTS.md          operating policy
NOTICE-IETF.md     source provenance and rights
```

## Reproduce

```sh
python3 scripts/fetch_rfcs.py
python3 scripts/split_sections.py
python3 -m unittest discover -s tests -v
```

`fetch_rfcs.py --check-only` verifies checksums without downloading.

## Citation rule

`RFC 7519 §4.1.4` must exist in `derived/sections.json` as
`rfc7519-s4.1.4`. Conflict claims cite both sides.

## Labels

- `supported`: true and cited to the right section.
- `fabricated_quote`: invented quote, absent from all sources.
- `contradicted`: claim opposite to the cited section.
- `unsupported`: invented requirement with no basis.
- `wrong_section`: true statement filed under the wrong section.
- `real_standards_conflict`: defensible 8725-vs-7519 tightening.

## License of sources

RFC texts belong to the IETF Trust and authors; see `NOTICE-IETF.md`.
Wiki prose and code are original for audit research.

The MIT license in `LICENSE` covers original code and wiki prose only; the RFC texts in `raw/sources/` are not covered by MIT and remain under IETF Trust terms.
