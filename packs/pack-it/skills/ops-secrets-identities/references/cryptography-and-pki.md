# Cryptography in practice, KMS and PKI

The overriding rule: do not invent cryptography and do not assemble it from primitives if a ready high-level construction
exists (the platform library, libsodium/Tink, KMS, TLS).

## Choosing the tool
| Need | Use | Do not use |
|---|---|---|
| data encryption | AES-256-GCM or ChaCha20-Poly1305 (authenticated encryption), a random nonce, never repeated with the same key | AES-ECB, CBC without a MAC, custom schemes |
| integrity and authenticity of messages between parties with a shared secret | HMAC-SHA-256, constant-time comparison | a plain hash with the secret appended (`sha256(secret+msg)`) |
| signature, identity, key exchange | Ed25519 / ECDSA P-256, RSA ≥ 3072 (2048 only for compatibility), X25519 / ECDHE | RSA without OAEP/PSS padding, keys < 2048 |
| data fingerprint, deduplication, checksum | SHA-256 / SHA-3 | MD5, SHA-1 (collisions) |
| passwords | argon2id or bcrypt (be-auth-security) | SHA-256 even with a salt — too fast |
| randomness | the platform CSPRNG (`crypto.randomBytes`, `SecureRandom`) | `Math.random`, `Random` |
| transport | TLS 1.3 (1.2 with modern ciphers), mTLS between services | a custom protocol over TCP |

## KMS and envelope encryption
- The master key (KEK) lives in the KMS or HSM and never leaves it. You encrypt data with a data key (DEK) generated
  per object or batch. You store the DEK encrypted by the KMS next to the data.
- KEK rotation does not require re-encrypting the data (the KMS keeps old versions for decryption); a DEK compromise affects
  one object.
- KMS permissions separated: who can encrypt, who can decrypt, who can administer the key (these are three different roles).
  Every use of the key in the audit log.
- Deleting a key = data loss (crypto-shredding) — with a waiting period and human approval.

## Certificate lifecycle
- An inventory (CBOM, section 5 in SKILL.md): where the certificates are, who issued them, when they expire, who the owner is.
- Automatic issuance and renewal (ACME, cert-manager); expiry monitoring independent of the automation
  (ops-observability). The validity of public certificates is shrinking to 47 days (CA/B Forum, by 2029).
- Revocation: Let's Encrypt turned off OCSP on 6.08.2025 and publishes only CRLs. A short certificate lifetime
  increasingly replaces revocation, so check whether clients in your infrastructure require OCSP.
- The private key generated where it will be used (or in an HSM/KMS), never sent by e-mail or through a repository.

## Your own PKI (internal mTLS, devices, signing)
- Hierarchy: **an offline root CA** (HSM, used rarely, a two-person procedure) → **online intermediate CAs**
  per use or environment → short-lived end-entity certificates (hours–days for services).
- A certificate policy: who can get which certificate (names, extensions, lifetime), how identity is verified.
- **Failure resilience**: at least two intermediate CAs issuing certificates (in different zones or regions), high
  availability of CRL distribution, a time buffer — certificates renewed at half their validity, so a CA outage of a few hours
  does not stop services. The CA compromise procedure (revoking the intermediate, replacing the trust) rehearsed.
- Ready solutions instead of your own CA from scratch: the cloud provider's managed CA, step-ca, HashiCorp Vault PKI,
  a service mesh with a built-in CA.

## Post-quantum cryptography
An attacker can record traffic today and decrypt it in the future ("harvest now, decrypt later"). For data
with a long confidentiality period: a cryptography inventory, a review of where you use key exchange, and turning on hybrid
modes (e.g. ML-KEM with X25519 in TLS) when the libraries and clients in your stack support them.

## Sources
- [roadmap.sh — DevSecOps](https://roadmap.sh/devsecops) (symmetric, asymmetric, hashing, SHA-256, bcrypt, KMS,
  certificate lifecycle, PKI design and failover, TLS)
- [AWS KMS — concepts](https://docs.aws.amazon.com/kms/latest/developerguide/overview.html);
  [Let's Encrypt: Ending OCSP support in 2025](https://community.letsencrypt.org/t/ending-ocsp-support-in-2025/229786)
- NIST FIPS 203 (ML-KEM, 2024)
Described in our own words.
