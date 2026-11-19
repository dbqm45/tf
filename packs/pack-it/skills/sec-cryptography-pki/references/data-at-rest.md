# Data at rest: data classes, encryption layers, the lifecycle

It answers "do we encrypt data at rest" in a way that can be defended before an auditor and an attacker.
Choosing algorithms, the KMS and envelope encryption: SKILL.md and `references/key-lifecycle-and-pki.md`. Retention
and deletion of personal data (RODO, the Polish name of the GDPR): `arch-privacy-compliance`. Backups and restore: `ops-sre-incidents`.

## 1. Data classes
Classification first, then safeguards — otherwise everything is "confidential" or nothing is.

| Class | Examples | Minimum at rest |
|---|---|---|
| public | marketing content, public documentation | integrity (who can change it) |
| internal | configuration, operational data without people | media encryption (the provider), access control |
| confidential | customer data, contracts, logs with identifiers | database/object encryption with a key in the organization's KMS, key usage logs, encrypted backups |
| strictly confidential | special categories of data, document numbers, payment data, secrets | additionally field/application-level encryption, a separate key, decryption access only for a selected service |

The class is an attribute of a data set (a table, a bucket, a column), recorded next to it (a tag, a data catalog). Derived
data (an export, a copy, a test environment, logs) inherits the class, unless it has been anonymized.

## 2. Encryption layers and what they protect against

| Layer | Example | Protects against | Does not protect against |
|---|---|---|---|
| media / volume | disk encryption at the provider, LUKS, BitLocker | theft or removal of the media, bad decommissioning of a disk | anyone with access to the running system, the database, the API |
| database / object store | TDE, server-side encryption with a key from the KMS (e.g. SSE-KMS) | access to database files and snapshots without permissions to the key; gives a key usage log | a user or application with access to the database |
| field / application | encrypting the value before writing (AEAD, a key from the KMS) | the database administrator, a leak of a backup or a dump, SQL injection reading the table | a takeover of the application itself, which has the right to decrypt |

The answer "the disks are encrypted by the provider" closes only the first row. For confidential data add a key
managed by the organization (a key policy, separation of roles, a usage log, the ability to cut off access), and for strictly confidential data
field-level encryption.

## 3. Keys
- KMS/HSM, envelope encryption (the DEK with the data, the KEK in the KMS), separate keys per environment and data class.
- Separated roles: who administers the key, who encrypts, who decrypts. The permission to decrypt is
  rarer than access to the encrypted data.
- KEK rotation according to the policy; key usage logs in the SIEM (unusual decryptions are a signal of a leak).
- Key lifetimes and states: NIST SP 800-57 part 1 (rev. 5; rev. 6 is a draft from 12.2025).

## 4. Backups
- Backups have the class of their source: encrypted, with a key other than the production one, in another account or region, at least one
  immutable (`ops-sre-incidents`).
- A restore test also checks access to the keys — a backup without a key does not exist.

## 5. The data lifecycle
Creation (class assigned) → storage (the class's safeguards) → use (minimal access, masking in
non-production environments) → archive (retention with a justification; personal data: `arch-privacy-compliance`) →
deletion.
- **Secure deletion** per NIST SP 800-88 rev. 2: for cloud media and encrypted data the practical method
  is cryptographic erasure (destroying the key with which the data was encrypted) — which is why separate keys per data set
  or per customer make deletion easier. For your own hardware: erasure or physical destruction of the media with a record.
- Deletion covers backups, replicas, exports and test environments; record after what time the data disappears from the backups.

## Example
**Input:** "The auditor asks about encryption at rest. Postgres in the cloud, S3 with customer files, nightly backups; the disks
are encrypted by the provider."
**Result:** classes — the customer files and the `customers` table confidential, the column with the document number strictly confidential. Postgres:
storage encryption with the organization's key in the KMS (not the provider's default key), the key usage log to the SIEM. S3:
SSE-KMS with a key per environment, the bucket policy requires encryption and TLS. The column with the document number:
AES-256-GCM in the application (the example in SKILL.md). Backups: a separate key, a separate account, an immutable backup, a quarterly
restore test with the key. Deleting a customer: the data in the database and S3 + the backup retention expiring; for exports a key per
export and crypto-erase.

## Sources
- NIST SP 800-111 *Guide to Storage Encryption Technologies for End User Devices* (final, 11.2007):
  https://csrc.nist.gov/pubs/sp/800/111/final
- NIST SP 800-88 rev. 2 *Guidelines for Media Sanitization* (final, 09.2025; supersedes rev. 1):
  https://csrc.nist.gov/pubs/sp/800/88/r2/final
- NIST SP 800-57 part 1 rev. 5 (final, 05.2020); rev. 6 — a draft (12.2025)
- OWASP Cryptographic Storage Cheat Sheet:
  https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
Statuses per a search in the nist.gov and owasp.org domains on 2026-10-27; the csrc.nist.gov and owasp.org pages unavailable
from the sandbox — the page content [unverified]. Described in our own words.
