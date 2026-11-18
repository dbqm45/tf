# Common cryptographic mistakes and how to catch them

Contents: modes and nonces · randomness · JWT · passwords · comparisons and other · how to test

## Modes and nonces
- **ECB** reveals repeated blocks; do not use it for anything. Detection: `AES/ECB`, `Cipher.getInstance("AES")`
  (ECB by default in Java), `MODE_ECB`.
- **CBC without a MAC** allows modifying the ciphertext and creates a padding oracle. Use AEAD instead.
- **A repeated nonce in GCM or ChaCha20-Poly1305** with the same key breaks confidentiality and integrity. A fixed IV,
  a counter reset after a restart and a random 96-bit nonce with a huge number of messages per key are a risk.
  Remedy: a nonce from a persistently stored counter, key rotation after the limit, or a construction resistant to
  repetition (AES-GCM-SIV, XChaCha20-Poly1305).
- Encryption without authenticating the context: use AAD (the record id, the tenant), so that the ciphertext cannot be moved.

## Randomness
- Tokens, keys, nonces, salts and reset identifiers from a CSPRNG, ≥ 128 bits of entropy. `Math.random`, `rand`,
  `Random`, time as a seed — that is a mistake. A custom generator "from several sources" too.

## JWT and signatures
- **alg confusion:** the server takes the algorithm from the token header (`alg: none` or HS256 with the RSA public key
  as the secret). The rule: the algorithm and the key are set by the server-side configuration, verification with an allowlist
  of algorithms, the key chosen by `kid` from a trusted JWKS. Validation of `iss`, `aud`, `exp` — `be-auth-security`.
- A signature without verifying the chain of trust (copying the key from the token, `jku` from any address) is no signature.

## Passwords and keys
- Fast hashes (SHA-256, MD5) for passwords; a global salt instead of a random one per password.
- A key hard-coded in the code, in a container image or in a mobile app; the same key in the test and production environments.
- No rotation and no version header, so changing the algorithm requires a "big bang" migration.

## Comparisons and other
- Comparing a MAC/tokens with a plain `==` (a timing channel) instead of the library's constant-time function.
- Deterministic ciphertext for searching fields (an equality leak) instead of an HMAC index.
- Decryption error messages that reveal the reason (padding vs MAC).
- TLS validation disabled "for a moment" in code that reached production.

## How to test
Unit tests with the library's test vectors, a test that the same plaintext gives different ciphertexts, a test
of rejecting a modified ciphertext and a token with a different `alg`, static analysis of cryptographic rules
(Semgrep or an equivalent) in CI (ops-ci-cd). Tests only on your own systems.
