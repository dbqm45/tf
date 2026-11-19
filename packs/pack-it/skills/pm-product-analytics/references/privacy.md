# Privacy and consent

## When consent is needed
- Storing or reading information on the user's device (cookies, localStorage, an identifier in a script)
  requires consent, unless it is strictly necessary for a service the user asks for (Art. 5(3) ePrivacy; in Poland
  Art. 399 of the Prawo komunikacji elektronicznej (Electronic Communications Law)). Analytics and session recording are usually not necessary.
- Consent must be active (not a pre-ticked box, not "continued use means consent"), and just as easy to
  refuse as to give, and to withdraw.
- Personal data in events (including a pseudonymous ID linked to a person) is processing under the GDPR: purpose, basis,
  retention, a processing agreement with the tool vendor, transfer outside the EEA. Details: arch-privacy-compliance.

## A variant when there is no consent
- Business events from the server (account created, payment) — no script on the device; it is still personal data,
  so a legal basis and minimisation apply.
- Analytics without an identifier on the device, aggregated only (visit counts, no tracking of a person between
  visits) — whether it needs consent in a given country you leave to a lawyer; you do not promise compliance.

## Session recording and autocapture
- Only after consent; all text fields masked by default, pages with sensitive data switched off
  (payments, health data, an admin panel with customer data).
- Short retention of recordings (e.g. 30 days) and access only for named people.
- Autocapture switched off or limited to a list of elements; it collects on-screen text, including personal data.

## Minimisation
- Ranges instead of exact values, country instead of an IP address, an internal ID instead of an email.
- The retention period of raw events set in the tool, not "forever".
- A data erasure request (GDPR Art. 17) also covers the analytics tool — a deletion procedure by `user_id`.
