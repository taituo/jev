---
type: concept
status: reviewed
created: 2026-09-18
updated: 2026-09-18
sources: [rfc6749]
tags: [oauth2, grants]
---

# OAuth 2.0 grants

OAuth separates client from resource owner and uses access tokens with
scope and lifetime instead of passwords (RFC 6749 §1).

- The four roles are resource owner, resource server, client, and
  authorization server (RFC 6749 §1.1).
- The abstract flow moves from grant to token to protected resource
  (RFC 6749 §1.2).
- Authorization code uses redirection plus a token exchange
  (RFC 6749 §4.1). Implicit returns tokens directly (RFC 6749 §4.2).
- Password credentials trade a password for a token (RFC 6749 §4.3).
  Client credentials use the client's own identity (RFC 6749 §4.4).
- Access and refresh tokens separate short-lived access from longer
  re-authorization (RFC 6749 §1.4, RFC 6749 §1.5). Refresh uses the
  `refresh_token` grant (RFC 6749 §6).
