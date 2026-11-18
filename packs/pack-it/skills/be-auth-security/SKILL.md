---
name: be-auth-security
description: Use for authentication and authorization — sessions, tokens, OAuth/OIDC, passwords, validation, OWASP.
metadata:
  review: "2027-10-17"
  catalog: "Use for authentication, authorization, sessions and tokens (theft and replay, rotation, revocation), OAuth/OIDC (PKCE, consents, device code), passwords, secrets, input validation, deserialization, admin panels and the backend security review (OWASP). Not for network and cloud configuration or dependencies (ops-supply-chain-security)."
---

# Auth and backend security

## Authentication
- Do not write your own cryptography or your own login system if the project has a library/IdP.
- Passwords: argon2id (or bcrypt with a cost ≥ 12). Never MD5/SHA-* without a salt and stretching.
- Rate limiting and delays for login, password reset, OTP. The same message for "wrong login" and "wrong password".
- MFA protects the login, but **it does not protect a stolen session**: attackers buy cookies and tokens stolen by
  malware and replay them without logging in. That is why the design of sessions and tokens matters.

## Sessions and tokens
- Session cookies `HttpOnly; Secure; SameSite=Lax` (or `Strict`), rotating the ID after login, sessions in a store
  on the server side, so that they can be revoked.
- A short access token (≤ 15 min); verify `alg`, `iss`, `aud`, `exp` — **`aud` strictly**: a token issued for one service
  does not work in another.
- A refresh token with rotation; reuse of an already used refresh token = theft → revoke the whole token family.
- A change of the password, MFA or email revokes all of the user's sessions and refresh tokens. The "log out everywhere" operation
  is one API call, rehearsed before an incident.
- An idle limit and an absolute session limit; re-authentication (step-up) before sensitive operations: changing
  the email or MFA, a payout, permissions, data export.
- Where possible, bind the token to a device or a key (DPoP, mTLS between services, DBSC in the browser).
Details and abuse signals: `references/tokens-sessions-oauth.md`.

## OAuth / OIDC
- Authorization Code + **PKCE** for every client; redirect URIs registered and compared exactly (no patterns,
  no arbitrary loopback port for a confidential client).
- A public client's identifier is not proof of identity — an attacker will use the identifier of a known application.
- Minimal scopes; a list of allowed scopes per client; admin consent for high-risk scopes
  (mail, files, the directory). The user sees the consents and can revoke them.
- The device code flow **disabled**, unless the client really needs it (a device without a keyboard) — it is a
  popular phishing method today that bypasses MFA.
- **A remote MCP server** is an OAuth resource server: OAuth 2.1 with PKCE, authorization server discovery from metadata,
  client registration through Client ID Metadata Documents (Dynamic Client Registration deprecated), validation of
  the token audience and `iss` — `references/tokens-sessions-oauth.md` §7.

## Authorization
- Checked on the server **per resource and per action** (not only "is logged in"). The most common bug: IDOR — `GET /invoices/{id}` without checking the owner.
- Deny by default; permissions in one module, not scattered across controllers.
- Choosing the model (RBAC, ABAC, ReBAC, PBAC, DAC, MAC) and an authorization test matrix: `references/authorization-models.md`.
- Service accounts: one identity per service, its own credentials with a minimal scope; never a shared database superuser.
- The admin panel and management endpoints: a separate host, SSO with MFA, access from a VPN/the company network — not from the internet.
  Admin permissions granted just in time and recorded in the audit log.

## Input and output
- Schema validation at the boundary; body and file size limits.
- SQL only parameterized (be-database). System commands without interpolating input.
- **Deserialization:** never turn untrusted data into native objects (Java `ObjectInputStream`, similar
  mechanisms in other languages and frameworks). Only data formats (JSON) with a schema or an allowlist of classes.
  Examples of attacks without login: SolarWinds Web Help Desk (Java), React2Shell (the React Server Components protocol).
- Upload: a whitelist of types (check the content, not the extension), random names, storage outside the webroot.
- SSRF: requests to user-supplied URLs only through a host allowlist; block internal addresses and cloud metadata
  (`169.254.169.254`).

## Secrets
- Only from environment variables / a secrets manager. Never in the repo, logs, error messages or API responses.
- A secret found in the repo = rotating the secret, not just removing it from the file.

## Logging security events
Log: logins (success/failure), token issue and refresh (client, scopes, IP, ASN, user agent), OAuth consents,
permission changes, password and MFA resets — without passwords, tokens and full personal data. Retention long enough to
answer the question "did someone have access" (ops-observability).

## Headers
`Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, CORS with an explicit list of origins (never `*` with credentials).

The full checklist before an API release (authentication, JWT with a fixed algorithm and JWKS, transport and HSTS, XXE
and "billion laughs", upload through a signed URL, response headers, CI/CD, monitoring):
`references/api-security-checklist.md`.

## Review checklist
- [ ] every new endpoint has a per-resource authorization check + a test for 403
- [ ] tokens: short, `aud` checked, refresh rotation with reuse detection, revocation after a credential change
- [ ] OAuth: PKCE, exact redirect URIs, minimal scopes, device code disabled when not needed
- [ ] no deserialization of untrusted data into native objects
- [ ] the admin panel and management endpoints not reachable from the internet
- [ ] no secrets in the diff and logs; security events logged
- [ ] input validation and limits; dependencies without known critical CVEs (ops-supply-chain-security)
