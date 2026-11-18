# Mail sent by the application: deliverability and domain authentication

The application sends e-mails (registration, password reset, invoices, notifications) through a provider (SES, SendGrid, Postmark,
Mailgun or a company SMTP server). Without a correct domain configuration, messages land in spam or are rejected.

## Three DNS records
- **SPF**: one record per domain, at most 10 DNS lookups (every `include` counts).
- **DKIM**: keys of at least 2048 bits, rotation through a new selector.
- **DMARC**: with alignment to the `From` domain; start with `p=none` with `rua=` reports, then `p=quarantine` and `p=reject`.
- System mail from a separate subdomain (`mail.company.pl`, `notifications.company.pl`) — the reputation of marketing does not spoil
  the delivery of password resets.

## Requirements of the large mailbox providers (Gmail, Yahoo)
- All senders: SPF or DKIM, a correct reverse DNS record (PTR) for the server, TLS when sending, a correct message
  format, a low spam complaint rate.
- **Bulk senders** (Gmail: from 5000 messages a day to Gmail accounts — the status remains even after the volume drops):
  SPF **and** DKIM, DMARC at least `p=none` with alignment, **one-click unsubscribe** in marketing
  messages (the `List-Unsubscribe` and `List-Unsubscribe-Post` headers according to RFC 8058) handled within 2 days,
  a spam complaint rate below 0.1% and never above 0.3%. Since November 2025 Gmail has enforced these rules gradually:
  temporary rejections, then permanent rejections.
- You check the status in Google Postmaster Tools; the rules change — before a large send, read the current guidelines.

## On the application side
- Asynchronous sending from a queue (retries, the provider's rate limit), idempotent on retry (be-messaging-outbox).
- Handling bounces and complaints (the provider's webhook): permanently bouncing and complaining addresses — excluded from further sending.
- Content: text and HTML, links on your own domain, no URL shorteners; marketing consent (RODO, the Polish name of the GDPR) separate from transactional
  messages.
- Tests without sending to real people: a capturing SMTP server (Mailpit — qa-regression,
  `environment-and-special-data.md`).

## Protocols and ports
SMTP: 25 (between servers), 587 (submission with authentication and STARTTLS — the default for applications), 465 (SMTP over
TLS). Receiving: IMAP 993 (IMAPS), POP3 995 (POP3S). Many cloud providers block outbound port 25 — the application
sends through the provider's API or port 587. Greylisting (a temporary rejection of the first message from an unknown
sender) requires the sending server to retry — providers do it themselves.

## Sources
- RFC 7208 (SPF), RFC 6376 (DKIM), RFC 7489 (DMARC), RFC 8058 (one-click unsubscribe)
- [Google — Email sender guidelines](https://support.google.com/a/answer/81126);
  [Red Sift — Gmail enforcement for bulk senders](https://redsift.com/blog/gmails-enforcement-ramps-up-what-bulk-senders-need-to-know)
- [roadmap.sh — DevOps](https://roadmap.sh/devops) (SMTP, IMAP, POP3S, SPF, DomainKeys, DMARC, white/grey listing)
Described in our own words.
