---
type: concept
status: reviewed
created: 2026-09-18
updated: 2026-09-18
sources: [rfc7519, rfc8725]
tags: [jwt, claims, validation]
---

# JWT claims

JWT claims are statements about a subject encoded as a JSON object
(RFC 7519 §1). No registered claim is mandatory in every context
(RFC 7519 §4.1).

- `iss` is OPTIONAL and identifies the issuer (RFC 7519 §4.1.1). When
  present, RFC 8725 requires the keys to belong to that issuer
  (RFC 8725 §3.8).
- `sub` is OPTIONAL and identifies the subject (RFC 7519 §4.1.2). When
  present, RFC 8725 requires a valid subject or issuer-subject pair
  (RFC 8725 §3.8).
- `aud` is OPTIONAL in RFC 7519 but MUST be rejected when present and
  unmatched (RFC 7519 §4.1.3). RFC 8725 strengthens this for
  multi-audience issuers: `aud` MUST be present and MUST be validated
  (RFC 8725 §3.9).
- `exp` and `nbf` gate acceptance by time with OPTIONAL small leeway
  (RFC 7519 §4.1.4, RFC 7519 §4.1.5).
- `iat` marks issuance time for age calculations (RFC 7519 §4.1.6).
- `jti` gives a unique ID for replay prevention (RFC 7519 §4.1.7).
- Unknown claims MUST be ignored absent application rules
  (RFC 7519 §4).
