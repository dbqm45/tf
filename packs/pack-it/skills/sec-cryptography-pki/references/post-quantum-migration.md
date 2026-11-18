# Post-quantum migration (PQC)

Contents: standards · the threat · a step-by-step plan · deadlines · pitfalls

## Standards
- NIST FIPS 203 (ML-KEM, key encapsulation), FIPS 204 (ML-DSA, a signature), FIPS 205 (SLH-DSA, a hash-based
  signature) — published in August 2024. FIPS 206 (FN-DSA) and the HQC algorithm: status [unverified].
- Stateful hash-based (LMS, XMSS) for signing software/firmware: NIST SP 800-208; they require secure
  management of the key state.

## The threat
An attacker records traffic today and will decrypt it when a suitable quantum computer appears ("harvest now, decrypt
later"). It concerns long-horizon confidentiality (medical data, state data, intellectual property) and key exchange.
Signatures are less urgent for short-lived credentials, but urgent for long-lived trust
(firmware, root CA, legal documents). Symmetric ciphers and hashes: AES-256 and SHA-384+ stay, the key size
decides.

## The plan
1. **Inventory** (CBOM, CycloneDX): algorithms, libraries, protocols, certificates, devices, dependencies on
   vendors; priority = confidentiality period + exposure (public traffic, backups, archives).
2. **Agility:** the algorithm in configuration, versioned formats, larger fields for keys and signatures (PQ signatures
   and keys are many times larger — check the limits of protocols, headers, HSMs and certificates).
3. **Key exchange first:** the hybrid mode X25519 + ML-KEM in TLS where the library, the CDN
   and the clients support it; measure the overhead and middlebox compatibility.
4. **Signatures and PKI:** a plan for the root CA, code and firmware signing; HSM and KMS vendors with PQC.
5. **Vendors:** ask SaaS providers and manufacturers about their plan and deadlines; write it into contracts.
6. **Test and retire** the old algorithms after a compatibility assessment.

## Deadlines (all [unverified] in primary sources; secondary ones from 2026-10-17)
- NIST IR 8547 (draft, November 2024): algorithms with a strength of 112 bits (e.g. RSA-2048, ECC 256) deprecated after 2030,
  RSA/ECC disallowed after 2035.
- NSA CNSA 2.0: new acquisitions of national security systems compliant from 2027-01-01; software signing
  and network equipment targeted by 2030, browsers, servers and cloud services by 2033, everything by 2035.
- EU and national deadlines (including Polish ones) and the EU plan: check with ENISA and national documents —
  [unverified], do not give numbers without a source.

## Pitfalls
"PQC" alone without a hybrid where the new algorithm is young; forgetting backups and archives of already
intercepted traffic; size limits in protocols; a migration without an inventory.
