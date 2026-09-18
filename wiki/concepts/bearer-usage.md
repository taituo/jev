---
type: concept
status: reviewed
created: 2026-09-18
updated: 2026-09-18
sources: [rfc6750, rfc6749]
tags: [bearer, http, tls]
---

# Bearer token usage

Possession of a bearer token is sufficient to use it, so protection
matters (RFC 6750 §1).

- Only one transmission method per request: header, body, or query
  (RFC 6750 §2).
- The `Bearer` Authorization header is RECOMMENDED and MUST be
  supported by resource servers (RFC 6750 §2.1).
- Body transmission uses `access_token` under form-encoding rules
  (RFC 6750 §2.2). Query transmission uses `access_token` but is NOT
  RECOMMENDED (RFC 6750 §2.3).
- Errors use `WWW-Authenticate` with `invalid_request`,
  `invalid_token`, or `insufficient_scope` (RFC 6750 §3,
  RFC 6750 §3.1).
- Bearer tokens MUST use TLS in transit (RFC 6750 §5.1,
  RFC 6750 §5.2).
