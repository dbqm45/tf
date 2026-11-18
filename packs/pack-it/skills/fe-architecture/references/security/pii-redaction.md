# PII Redaction

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/pii-redaction.

## Metadata

Category: Security. Level: Advanced. Framework: Native web. Author: Den Odell. Last updated:
17 June 2026.

## TLDR

Remove/mask sensitive data at the application boundary, before sending it to logs, analytics or error
reporters — the safest value is the one you never collected.

## Notes (state in 2026, corrections to the source)

- The example logger uses `process.stdout` (Node/SSR); in the browser you hook the same redactor into the logs/telemetry
  transport (e.g. Sentry's `beforeSend`, `beforeSendTransaction`, OpenTelemetry processors — ops-observability).
- Do not send PII in URLs (the query string ends up in server logs, history, `Referer`) — set
  `Referrer-Policy: strict-origin-when-cross-origin` (the default in new browsers).
- Session replay (Sentry Replay, LogRocket…) — mask all fields and text by default, unmask selectively.

## Problem

Users' sensitive data (passwords, card numbers, tokens, e-mails) reaches external systems
through logs, error reports and analytics tools. Data that was never meant to leave
the browser sits in a third-party dashboard accessible to dozens of people. Leaks arise
especially when data spreads through many systems without centralized control.

## Solution

Redaction at the application boundary — before data is transmitted:

1. **An allow-list** instead of a deny-list (fail-closed: new fields redacted by default).
2. **A centralized redactor** — one place for all sinks (logs, error reporting,
   analytics).
3. **Pattern matching** as a safety layer for free text (stack traces, messages).
4. **Integration hooks** — e.g. Sentry's `beforeSend`, wrappers for logging.

## Code examples

### The core redactor (vanilla JS)

```javascript
const SENSITIVE_KEYS = new Set([
  'password', 'pwd', 'token', 'accessToken', 'refreshToken',
  'authorization', 'cookie', 'ssn', 'creditCard', 'cardNumber',
  'cvv', 'email', 'phone',
]);

const PATTERNS = [
  [/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[EMAIL]'],
  [/\b(?:\d[ -]*?){13,16}\b/g, '[CARD]'],
  [/\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b/g, '[PHONE]'],
  [/\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g, '[TOKEN]'],
];

function redactString(value) {
  return PATTERNS.reduce((acc, [pattern, label]) => acc.replace(pattern, label), value);
}

function redact(input, { allowList } = {}) {
  if (typeof input === 'string') return redactString(input);
  if (Array.isArray(input)) return input.map((item) => redact(item, { allowList }));
  if (input && typeof input === 'object') {
    const output = {};
    for (const [key, value] of Object.entries(input)) {
      if (allowList && !allowList.has(key)) {
        output[key] = '[REDACTED]';
      } else if (SENSITIVE_KEYS.has(key)) {
        output[key] = '[REDACTED]';
      } else {
        output[key] = redact(value, { allowList });
      }
    }
    return output;
  }
  return input;
}

export { redact };
```

### Sentry integration (the `beforeSend` hook)

```javascript
import * as Sentry from '@sentry/browser';
import { redact } from './redact';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  beforeSend(event) {
    if (event.request) {
      event.request.data = redact(event.request.data);
      event.request.headers = redact(event.request.headers);
      event.request.cookies = '[REDACTED]';
    }

    if (event.extra) {
      event.extra = redact(event.extra);
    }

    if (event.breadcrumbs) {
      event.breadcrumbs = event.breadcrumbs.map((crumb) => ({
        ...crumb,
        data: crumb.data ? redact(crumb.data) : crumb.data,
      }));
    }

    return event;
  },
});
```

### Structured logging with an allow-list

```javascript
import { redact } from './redact';

const SAFE_KEYS = new Set([
  'level', 'message', 'timestamp', 'requestId', 'userId',
  'route', 'method', 'statusCode', 'durationMs',
]);

function write(level, message, context = {}) {
  const record = {
    level,
    message: redact(message),
    timestamp: new Date().toISOString(),
    ...redact(context, { allowList: SAFE_KEYS }),
  };

  process.stdout.write(JSON.stringify(record) + '\n');
}

const logger = {
  info: (message, context) => write('info', message, context),
  warn: (message, context) => write('warn', message, context),
  error: (message, context) => write('error', message, context),
};

logger.error('Checkout failed', {
  userId: 'u_123',
  route: '/checkout',
  email: 'user@example.com',
  cardNumber: '4111 1111 1111 1111',
});
// {"level":"error","message":"Checkout failed","timestamp":"...",
//  "userId":"u_123","route":"/checkout","email":"[REDACTED]","cardNumber":"[REDACTED]"}

export { logger };
```

## Advantages

- Sensitive values never leave the browser towards external systems.
- An allow-list automatically redacts new fields (fail-closed) — a new, unlisted field is
  safe by definition.
- A uniform definition of sensitive data for all sinks (logs, error reporting, analytics).
- Supports GDPR/CCPA compliance — no sensitive data in uncontrolled systems.
- Reduces the damage after a leak — the data an attacker can exploit is much
  emptier.
- Preserves the diagnostic value of records (field names, structure) — it redacts values, it does not
  throw away whole records.
- Pattern matching catches PII in free text (stack traces, error messages).

## Disadvantages / tradeoffs

- **Over-redaction** — every log becomes `[REDACTED]`, making diagnosis harder during incidents.
- **Imperfect patterns** — international number formats can slip through, false
  alarms happen on ordinary strings.
- **Performance cost** — deep cloning and scanning on every log call.
- **Maintenance** — the lists require active synchronization with the evolution of the architecture/data fields.
- **Allow-list discipline** — every useful field must be listed explicitly, otherwise it is lost.
- **A point of failure** — a bug in the redactor affects all sinks at once.
- **Hidden structures** — JSON serialized inside strings, base64 blobs can smuggle PII
  unnoticed.
- **It does not replace prevention** — the safest value is the one you never collected.
- **Third parties** — external SDKs can collect data bypassing your redaction hooks.

## Related patterns

- Error Handling — Resilience (`../resilience/error-handling.md`)
- External: [PII / GDPR](https://gdpr.eu/eu-gdpr-personal-data/),
  [Information exposure — OWASP](https://owasp.org/www-community/vulnerabilities/Information_exposure_through_query_strings_in_url),
  [CCPA Compliance — California AG](https://oag.ca.gov/privacy/ccpa)

## When to use / when NOT to use

Introduce a redactor **always** when the application sends data to any third-party system (error
reporting, analytics, centralized logs) — this is not a pattern "for later", it is a basic
compliance requirement (GDPR/CCPA) in most jurisdictions. Start with the simplest version: an allow-list on
keys for structured data — add pattern matching for free text only if you
really log raw messages/stack traces that may contain PII (do not add it upfront
"just in case", in line with YAGNI from `../principles.md`, because over-redaction has a real
diagnostic cost during incidents).
