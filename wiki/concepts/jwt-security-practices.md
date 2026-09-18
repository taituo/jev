---
type: concept
status: reviewed
created: 2026-09-18
updated: 2026-09-18
sources: [rfc7519, rfc7515, rfc8725]
tags: [jwt, security, bcp]
---

# JWT security practices

RFC 7519 leaves algorithm choice largely to applications
(RFC 7519 §7.2). RFC 8725 tightens that space without rewriting the
base spec.

- Enforce an explicit algorithm allow-list; never use others, and bind
  each key to exactly one algorithm (RFC 8725 §3.1).
- Only cryptographically current algorithms are acceptable
  (RFC 8725 §3.2). Avoid RSA PKCS1 v1.5 encryption even though
  RFC 7519 lists `RSA1_5` as MUST-implement for capable stacks
  (RFC 7519 §8, RFC 8725 §3.2).
- Treat `none` as exceptional: RFC 7519 permits unsecured JWTs
  (RFC 7519 §6) and requires `none` support (RFC 7519 §8), while
  RFC 8725 says do not generate or consume `none` unless explicitly
  requested and otherwise protected (RFC 8725 §3.2).
- Validate every cryptographic operation and reject on any failure
  (RFC 8725 §3.3). JWS validation details sit in the base spec
  (RFC 7515 §5.2).
- Never use human passwords directly as HS256 keys (RFC 8725 §3.5).
- Validate `iss`, `sub`, and `aud` strictly where RFC 7519 left them
  OPTIONAL or application-specific (RFC 7519 §4.1.1, RFC 7519 §4.1.3,
  RFC 8725 §3.8, RFC 8725 §3.9).
- Do not trust `kid`, `jku`, or `x5u` blindly (RFC 8725 §3.10).
