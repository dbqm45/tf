# Identity and access in Zero Trust

Contents: IAM and CIAM · phishing-resistant MFA · PAM and JIT · lifecycle · devices · signals

## Workforce IAM and customer CIAM
- One source of truth about employees (HR → IdP, automatic onboarding, role change and offboarding).
  SSO through OIDC/SAML; phase out local passwords in applications.
- CIAM (customers) is a separate system and a different threat model: registration, account recovery, consents, bots.
  Do not mix the customer directory with employees. Login code and OAuth: `be-auth-security`.
- Federation with partners instead of guest accounts without an owner; guest accounts with an expiry date.

## Phishing-resistant MFA
- Resistant: FIDO2/WebAuthn (hardware keys, passkeys), a certificate on a device with a hardware-protected key.
  Binding to the domain (origin) makes it impossible to give the credential to a fake site.
- Not resistant: SMS, voice code, TOTP, an "approve" push (MFA fatigue, real-time phishing).
  If you must keep them, push with number matching, limited attempts and anomaly monitoring.
- Order: administrators and privileged accounts → access to code and the cloud → the rest of the employees.
  Recovery procedures (a lost key) are a frequent bypass: two keys per person, identity verification.
- The session after login: stolen cookies bypass MFA — short sessions, binding to the device
  (`be-auth-security`, `.claude/skills/be-auth-security/references/tokens-sessions-oauth.md`).
- NIST requirements for authentication levels (SP 800-63B, version 4) and mapping onto risk: [unverified].

## PAM and just-in-time access
- No standing administrative privileges: elevation per task, with a justification, approval and a time limit
  (minutes–hours), session recording for critical systems.
- Separate administrative accounts (not the same account for email and for administration); privileged workstations.
- Emergency accounts ("break glass"): 2, offline, the password in a vault, an alarm on use, a review after every use.
- Machine credentials and service access: `ops-secrets-identities`.

## Lifecycle (joiner–mover–leaver)
Automatic access revocation within hours of offboarding, a quarterly access review (the resource owner
confirms), detection of accounts unused for 90 days [example], segregation of duties for high-risk actions.

## Devices
A registry (ownership, owner), MDM, encryption, updates, EDR. Posture signals: compliance, version, risk from the EDR.
Policy: full access, limited (e.g. read-only), none. Devices without an agent (IoT, OT): segmentation and monitoring
instead of posture.

## Continuous assessment signals
Login anomalies (impossible travel, a new device), risk from the IdP, EDR alerts, a permission change. Response:
forcing re-authentication, limiting the session, cutting it off. Incident handling: `ops-security-operations`.

## AI agent identity and delegation
An agent is a workload that also acts on behalf of a human. One shared service account with a long-lived token
blurs who did what, and a stolen token works everywhere.
- **Every agent and every instance of it has its own workload identity**, separate from the human's login, with a named
  owner. The standard: **SPIFFE** — the identifier `spiffe://<trust-domain>/<path>`, short-lived SVIDs
  (X.509 or JWT) fetched through the Workload API (a local socket, no secret in the code), the reference implementation
  SPIRE. Certificate rotation is automatic, so there is no long-lived key to leak.
- **Acting on behalf of the user = the user's token bound to the agent's key** (sender-constrained):
  - mTLS (RFC 8705, 2020-02): a token in JWT form carries the client certificate thumbprint in `cnf` → `x5t#S256`
    (base64url SHA-256 of the certificate DER, without `=`), and the resource server compares it with the certificate from the same
    TLS connection; a mismatch → 401 `invalid_token`;
  - DPoP (RFC 9449, 2023-09): the agent attaches to every request a `DPoP` header with a proof — a JWT signed with its
    key, with the request method and address (`htm`, `htu`) and a hash of the token (`ath`); the token is bound to the key through
    `cnf` → `jkt` (the public key thumbprint). The server rejects repeated proofs (replay protection);
  - a stolen token without the agent's key is useless.
- **Crossing between services: token exchange** (RFC 8693, 2020-01) instead of passing on the original. The new token
  is narrowed to the audience and scope. The RFC distinguishes **delegation** (the token says "A acts for B") from
  **impersonation** (A gets a token that identifies only B) — for an agent you choose delegation, because the audit then sees
  both. The `act` claim indicates the current actor; a nested `act` is the history of earlier actors,
  per the RFC **informational only** — you make the access decision based on the token's subject and the current actor.
  `act` does not record restrictions at each step; proposals for a delegation chain are IETF drafts [unverified].
- **Audit log:** "instance X of agent Y on behalf of user Z, token from exchange W, resource R". Without this you will not
  reconstruct an incident.
- **Services without support for token binding** you record explicitly as a weaker link (risk register, sec-risk-management):
  a shorter token lifetime, a narrow scope, a separate network.
- **A platform example — Google Cloud Agent Identity** (documentation, as of 2026-11-01):
  - a SPIFFE identity per agent (`spiffe://agents.global.org-<ID>.system.id.goog/resources/<service>/<path>`),
    in IAM as `principal://…`; an X.509 certificate valid for 24 h, renewed automatically;
  - unlike service accounts: not shared by default, no impersonation and no long-lived keys;
  - tokens to Google Cloud bound to the certificate; mTLS to the API and the gateway, DPoP outside the gateway ("double binding");
    the default Context-Aware Access policy does not allow replaying the token outside the agent's environment;
  - three identities: the user's, the agent's and a delegated one (the agent on behalf of the user through 3-legged OAuth from the
    "auth manager" credential store); logs show the agent and the user;
  - Principal Access Boundary narrows the agent's resources independently of other permissions;
  - **a lifecycle pitfall:** deleting an agent does not remove the IAM bindings of its identity, and a new agent (even with the
    same name) gets a new identity — you clean up and grant the bindings manually;
  - HTTP basic auth to external tools is available, but not recommended.
  Check the supported services and the status of individual features in the documentation, with a date.
- The security of the agent itself (injections, excessive agency, ASI03 Identity & Privilege Abuse):
  sec-llm-security.

Sources (checked 2026-11-01): github.com/spiffe/spiffe — `standards/SPIFFE.md`, `SPIFFE_Workload_API.md`,
README (CNCF project, graduated status); RFC 8705, 9449, 8693 — numbers, titles and the `cnf`/`x5t#S256` and `act` fields
checked in RFC texts provided by a human (RFC 8705 §3.1, RFC 8693 §1.1 and §4.1, RFC 9449 — abstract,
§4, `jkt`); docs.cloud.google.com/iam/docs/agent-identity-overview (content provided by a human
2026-11-01); G. Blaquiere, "SPIFFE:
Why Google's New Agent Identity…" (2026-06-09).
