# Tokens, sessions and OAuth — how they are stolen today and how to design the defence

Summaries of Huntress analyses in our own words; sources at the end of every section. Design conclusions for a team that
builds applications and APIs are marked **Design**.

## 1. Session theft and replay
- **What happens:** data-stealing malware (an infostealer) takes session cookies and tokens from the browser.
  They reach the market for a few to a few hundred dollars, and the buyer replays them automatically. There is no login event and no
  MFA prompt.
- **Signals:** a change of country or network during a session, a mismatched device fingerprint, many parallel sessions from different places.
- **Design:** short tokens and sessions with an absolute limit; a server-side session store; binding to a device
  (DBSC, DPoP); step-up before sensitive operations; "log out everywhere" with one call.
- Source: [From Cookies to Keys](https://www.huntress.com/blog/why-hackers-don't-need-passwords-anymore)

## 2. Device code phishing
- **What happens:** the attacker starts the device authorization flow themselves and persuades the victim to enter the code on
  the real identity provider page. The victim passes MFA, and the tokens go to the attacker. In the campaign described
  in March 2026 refresh tokens worked for up to 90 days and were replayed from addresses of the Railway PaaS platform, whose good
  reputation raised no alarms in the risk assessment.
- **Signals:** new device registrations with default names; an office application token used against another resource
  (e.g. a cloud management API); token refreshes at fixed hours (automation); an internally inconsistent user agent
  (e.g. a browser version that does not exist for the declared system); logins from data centre address ranges.
- **Design:** device code only for clients that need it; a short code validity; on the approval page
  show the application name, the location and the scopes; record the ASN and the hosting provider at token issue and refresh
  and alarm when a user's token is refreshed from a data centre; check the user agent's consistency.
- Sources: [We Need to Talk About Device Code Phishing](https://www.huntress.com/blog/tradecraft-tuesday-device-code-phishing-explained),
  [Riding the Rails: Threat Actors Abuse Railway.com PaaS as Microsoft 365 Token Attack Infrastructure](https://www.huntress.com/blog/railway-paas-m365-token-replay-campaign)

## 3. Authorization code theft through a "real" login
- **What happens:** the attacker runs on the victim's computer (with developer mode on or sideloading allowed) an application package that opens the real Microsoft
  login window with the client identifier of the Office application. The victim logs in with MFA, and the authorization code goes to the attacker,
  who exchanges it for tokens with broad scopes. The refresh token works until it is revoked (by an administrator, a revocation event or CAE).
- **Design:** a public client's identifier is not proof of who is asking; PKCE mandatory; exact redirect URIs;
  a password or MFA change revokes refresh tokens; access policies requiring a managed device where possible.
- Source: [OAuth Token Theft Through Microsoft's Front Door](https://www.huntress.com/blog/stealing-oauth-tokens-through-microsofts-front-door)

## 4. Malicious OAuth applications and abused consents
- **What happens:** within half a year Huntress found more than 500 applications installed through user consent
  (without an administrator) and about 1500 cases of legitimate applications used for an attack. Typical traits: a name impersonating a user
  or a domain, names like "Test App", loopback redirect addresses, an application rare globally but with access to one
  mailbox, permissions much broader than the declared purpose.
- **Design (the authorization server):** a list of allowed scopes per client, admin consent for high-risk
  scopes, a view "applications with access to my account" with the option to revoke, a log of every consent (who, the client, the scopes,
  the redirect URI). **Design (the client):** ask for the smallest scopes and expand them gradually.
- Source: [Six Months of Researching OAuth Application Attacks](https://www.huntress.com/blog/never-just-one-termite-6-months-of-researching-oauth-application-attacks)

## 5. Privilege hygiene
- **What happens:** too many local administrators, admin accounts used for email and browsing,
  "accidental" administrators from SaaS trial versions.
- **Design:** separate admin accounts without a mailbox; permissions for a time; an access review every half year;
  requesting a permission easy, so that nobody works around the process.
- Source: [What Good Privilege Hygiene Looks Like](https://www.huntress.com/blog/privilege-hygiene-least-privilege-best-practices)

## 6. An exposed application and deserialization
- **What happens:** SolarWinds Web Help Desk before version 12.8.7 HF1 deserialized untrusted Java data, which gave
  code execution without login; the admin interface was reachable from the internet. After the break-in the application process
  started a shell, installed remote access tools and a tunnel, and disabled the system's protection.
- **Design:** no deserialization into native objects; the admin panel off the internet; the application as a user
  without privileges, in a read-only container, with restricted egress; an alarm when the application process
  starts a child process (ops-observability); an SLA for patches of internet-facing components.
- Source: [Active Exploitation of SolarWinds Web Help Desk (CVE-2025-26399)](https://www.huntress.com/blog/active-exploitation-solarwinds-web-help-desk-cve-2025-26399)

## 7. Authorization of a remote MCP server
The state of the MCP specification in version `2026-07-28` (blog.modelcontextprotocol.io, read 2026-10-29):
- the MCP server is an OAuth resource server; the client (Claude Code, a desktop application, an agent) uses **OAuth 2.1
  with PKCE**, and discovers the authorization server from metadata published by the MCP server;
- **client registration**: Client ID Metadata Documents (the client identifier is the URL of a document with its metadata).
  Dynamic Client Registration is deprecated and works for compatibility, and its removal was announced for a future version
  without a date;
- the client gives `application_type`, which allows redirects to localhost for CLI and desktop applications;
- the authorization server returns the `iss` parameter (RFC 9207), and the client checks it — it protects against mixing up servers;
- the MCP server **validates the token audience** (a token issued for another resource is rejected) and does not pass the client's token
  on to background services — for them it has its own credentials or a token exchange;
- short access tokens, refresh through an external OAuth provider, minimal scopes per tool;
- client credentials bound to the issuer.
The description and schemas of this server's tools on the client side: core-agent-security §4 and ai-agents.
