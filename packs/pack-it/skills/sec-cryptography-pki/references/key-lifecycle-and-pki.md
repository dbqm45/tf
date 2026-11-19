# The key lifecycle, certificates and PKI

Contents: the key lifecycle · envelope encryption · public certificates · internal PKI · decisions

## The key lifecycle
| Phase | Requirement |
|---|---|
| generation | a CSPRNG, in the KMS/HSM or where the key will be used; a private key does not travel by email or through a repository |
| storage | master keys in the KMS/HSM and non-exportable; access through a role, not through a file |
| use | one key = one purpose (encryption, signing, MAC separately); usage limits (number of messages, age) |
| rotation | planned (periodic) and emergency (after a suspicion); the old version stays only for decryption |
| revocation | compromise → immediate withdrawal, notifying dependants, an assessment of what was signed or decrypted |
| destruction | after a waiting period and with a human's consent; deleting the key = cryptographic deletion of the data |
Operations on secrets (inventory, a leak, rotation in CI): `ops-secrets-identities`.

## Envelope encryption
The KEK in the KMS/HSM does not leave the module; a DEK per object or batch, encrypted with the KEK and stored next to the data.
KEK rotation does not require re-encrypting the data, only re-wrapping the DEK (rewrap). Separate three roles:
encryption, decryption and key administration. The encryption context binds the DEK to a tenant
or a resource. Every use of the key in the audit log (ops-observability).

## Public certificates
- The CA/Browser Forum schedule (SC-081v3): maximum validity of 200 days from 2026-03-15, 100 days from 2027-03-15,
  47 days from 2029-03-15; the domain validation reuse period also shortens (to 10 days in the last phase)
  [unverified in the Forum's primary register; secondary sources 2026-10-17]. Today is 2026-10-17, so the 200-day phase applies.
- The conclusion: uploading certificates by hand stops being feasible. ACME automation (certbot, cert-manager,
  built into the server/CDN), one challenge channel (HTTP-01 or DNS-01 with an account with minimal permissions), an alarm on
  certificates close to expiry independent of the automation, and an inventory of devices that do not support ACME
  (old appliances, VPN, IoT) — these need a replacement plan or TLS termination at a gateway.
- Revocation: rely less and less on OCSP (Let's Encrypt ended OCSP in 2025 according to
  `ops-secrets-identities`); short validity replaces revocation. Verify the clients that require OCSP stapling.
- Always CAA in DNS, Certificate Transparency monitoring of your own domains.

## Internal PKI
- The root CA offline in an HSM (a ceremony with two people), intermediate CAs online per environment or use,
  short-lived end-entity certificates (hours–days for services), issued after authenticating the identity of the
  workload (SPIFFE, a cloud identity, attestation).
- Name constraints and certificate policies, separate hierarchies for people, services and code signing.
- Resilience: ≥ 2 intermediate CAs in different zones, highly available CRL distribution, a CA compromise plan
  (revoking the intermediate, replacing the trust bundle) rehearsed as a dry run.
- Instead of a CA from scratch: the cloud provider's managed CA, step-ca, Vault PKI, a service mesh. Deployment and operation:
  `ops-secrets-identities`, mTLS in the cluster: `ops-kubernetes`.

## Decisions to record in an ADR
The certificate lifetime per class, who owns the CA, where the root lives, how we renew, what we do with
devices without ACME, when we rotate the KEK, how fast we can replace an algorithm.
