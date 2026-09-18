---
type: concept
status: reviewed
created: 2026-09-18
updated: 2026-09-18
sources: [rfc7519, rfc7515, rfc7516, rfc8725]
tags: [jose, header, typ]
---

# JOSE header

The JOSE header describes the cryptographic operations on a JWT, JWS,
or JWE (RFC 7519 §5).

- JWS `alg` MUST be present and processed (RFC 7515 §4.1.1). JWE uses
  `alg` plus `enc` for content encryption (RFC 7516 §4.1.1,
  RFC 7516 §4.1.2).
- JWT `typ` is OPTIONAL, RECOMMENDED as `JWT`, and ignored by JWT
  implementations (RFC 7519 §5.1).
- JWT `cty` MUST be `JWT` when nested signing/encryption is used;
  otherwise it is NOT RECOMMENDED (RFC 7519 §5.2).
- JWS `crit` lists extensions that MUST be understood
  (RFC 7515 §4.1.11).
- Replicated claims in encrypted JWTs SHOULD be checked for equality
  (RFC 7519 §5.3).
- RFC 8725 adds typing discipline: explicit `typ` is RECOMMENDED for
  new uses and MUST appear in the inner JWT when nesting is typed
  (RFC 8725 §3.11). Different JWT kinds MUST have mutually exclusive
  validation rules (RFC 8725 §3.12).
