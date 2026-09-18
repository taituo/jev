# Wiki index

Catalog of maintained pages. Each entry links to the page and states its
scope. Start here before opening individual pages.

## Sources

- [RFC 7519 — JSON Web Token](sources/rfc7519.md) — JWT claims, headers,
  validation, and implementation requirements.
- [RFC 7515 — JSON Web Signature](sources/rfc7515.md) — JWS headers,
  signing, and serializations.
- [RFC 7516 — JSON Web Encryption](sources/rfc7516.md) — JWE headers,
  encryption, and serializations.
- [RFC 6749 — OAuth 2.0](sources/rfc6749.md) — roles, grants, tokens,
  endpoints.
- [RFC 6750 — Bearer usage](sources/rfc6750.md) — token transmission,
  errors, TLS.
- [RFC 8725 — JWT BCP](sources/rfc8725.md) — current security guidance.

## Concepts

- [JWT claims](concepts/jwt-claims.md) — registered claims and their
  validation tightening.
- [JOSE header](concepts/jose-header.md) — `alg`, `enc`, `typ`, `cty`,
  and typing discipline.
- [OAuth grants](concepts/oauth-grants.md) — the four grants plus
  refresh.
- [Bearer usage](concepts/bearer-usage.md) — one method per request,
  header-first, TLS-only.
- [JWT security practices](concepts/jwt-security-practices.md) —
  allow-lists, `none`, key hygiene, audience and issuer checks.

## Operations

- `log.md` records ingests and maintenance in chronological order.
- `../fixtures/claims.jsonl` freezes 40 labelled audit claims.
- `../derived/sections.json` resolves every `RFC NNNN §X.Y` citation.
