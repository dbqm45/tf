# Dangerous APIs and default configurations — a review list

> **Contents:** Common patterns · Python · JavaScript and Node.js · Java · C# and .NET · Go · Default configurations and environment settings

A list of questions for code and configuration review. A hit is a candidate, not a verdict: you check whether the data is
untrusted and whether there is a control along the way. A found occurrence → look for variants (sec-variant-analysis).

## Contents
- Common patterns
- Python · JavaScript and Node.js · Java · C# and .NET · Go
- Default configurations and environment settings

## Common patterns
- **An interpreter fed from input**: `eval`, template execution, expressions (SpEL, OGNL), a shell command concatenated from
  a string — data as code (CWE-94, CWE-78).
- **Deserialization of typed formats** from an untrusted source (CWE-502) — use formats without types (JSON to a DTO).
- **Queries concatenated from strings** — SQL, LDAP, XPath, NoSQL (CWE-89, CWE-90, CWE-643); identifiers (columns,
  sort direction) only from an allow-list.
- **XML parsers with external entities** (XXE, CWE-611).
- **Non-cryptographic randomness** for tokens, passwords, session identifiers (CWE-338).
- **Weak hashes and ciphers**: MD5, SHA-1 for passwords or signatures, ECB, home-made cryptography; passwords only through
  Argon2id, scrypt or bcrypt (sec-cryptography-pki).
- **Disabled TLS or hostname verification** (CWE-295).
- **Fail-open**: an exception in a permission check ends in access; an empty role list = everyone.
- **Comparing secrets with a plain `==`** instead of a constant-time comparison.
- **Regular expressions with nested quantifiers** on user input (ReDoS, CWE-1333).

## Python
| Candidate | Safer |
|---|---|
| `pickle.loads`, `shelve`, `marshal` on external data | JSON + schema validation |
| `yaml.load` without a safe loader | `yaml.safe_load` |
| `eval`, `exec`, `compile` with input | a parser or a map of allowed operations |
| `subprocess.*(..., shell=True)`, `os.system` | an argument list without a shell |
| `random` for tokens | `secrets` |
| `hashlib.md5/sha1` for passwords | Argon2id / scrypt / bcrypt |
| `requests.*(verify=False)` | a correct CA chain |
| `xml.etree`, `lxml` on untrusted XML | `defusedxml` |
| `tempfile.mktemp` | `tempfile.mkstemp` / `NamedTemporaryFile` |
| Django: `DEBUG = True`, `SECRET_KEY` in the repo, `ALLOWED_HOSTS = ['*']` | environment variables, a host list |
| Flask: `app.run(debug=True)`; Jinja2 `autoescape=False` | debug only locally; autoescape enabled |

## JavaScript and Node.js
| Candidate | Safer |
|---|---|
| `eval`, `new Function`, `setTimeout("code")` | functions, not strings |
| `child_process.exec` with a concatenated command | `execFile` / `spawn` with an argument array |
| the `vm` module as a "sandbox" | it is not a security boundary — a separate process or isolation |
| `innerHTML`, `dangerouslySetInnerHTML`, `v-html` with data | text or sanitization (DOMPurify) |
| `Math.random` for tokens | `crypto.randomBytes`, `crypto.randomUUID` |
| merging objects from input (`__proto__`, `constructor`) | schema validation, prototype-less objects |
| JWT: verification without an algorithm list | an explicit algorithm list, checking `aud` and `iss` |
| `NODE_TLS_REJECT_UNAUTHORIZED=0` | a correct CA chain |

## Java
| Candidate | Safer |
|---|---|
| `ObjectInputStream.readObject` on external data | JSON to a DTO; if it must stay — a deserialization filter (`ObjectInputFilter`) |
| `DocumentBuilderFactory`, `SAXParserFactory`, `XMLInputFactory` with default settings | DTDs and external entities disabled |
| `Runtime.exec(String)` with a concatenated command | `ProcessBuilder` with an argument list |
| `java.util.Random` for tokens | `SecureRandom` |
| a `TrustManager` that accepts everything, a `HostnameVerifier` returning `true` | default verification |
| SpEL or templates from input | no evaluation of user data |
| Spring Boot Actuator exposed publicly | only `health` public, the rest behind authentication |

## C# and .NET
| Candidate | Safer |
|---|---|
| `BinaryFormatter`, `NetDataContractSerializer`, `LosFormatter` | `System.Text.Json` to a DTO |
| Newtonsoft.Json `TypeNameHandling` other than `None` | `None` or an explicit `SerializationBinder` |
| `SqlCommand` with concatenated SQL, `FromSqlRaw` with string interpolation | parameters, `FromSqlInterpolated` |
| `Process.Start` with `cmd /c` and data | arguments without a shell |
| `System.Random` for tokens | `RandomNumberGenerator` |
| `ServerCertificateCustomValidationCallback` returning `true` | default verification |
| `XmlDocument`/`XmlTextReader` with an entity resolver (older .NET Framework) | `XmlResolver = null`, `DtdProcessing.Prohibit` |

## Go
| Candidate | Safer |
|---|---|
| `text/template` for HTML | `html/template` |
| `math/rand` for tokens | `crypto/rand` |
| `tls.Config{InsecureSkipVerify: true}` | default verification |
| `exec.Command("sh", "-c", ...)` with data | the command and arguments separately |
| `fmt.Sprintf` for SQL | `?` / `$1` parameters |
| `http.ListenAndServe` without timeouts | `http.Server` with `ReadHeaderTimeout` and the other limits |
| the `unsafe` package, `reflect` on external data | a justification in the review |

## Default configurations and environment settings
- Default accounts and passwords (admin panel, database, broker, camera, device), test accounts left
  after deployment.
- Secrets from examples (`changeme`, `secret`, a JWT key from the documentation) in the production configuration; secrets
  in the repository (ops-secrets-identities).
- Debug mode and error pages with a stack trace in production.
- CORS `*` together with cookies or an authentication header; session cookies without `Secure`, `HttpOnly`,
  `SameSite`.
- Services without authentication listening on all interfaces (e.g. Redis, Elasticsearch, management
  panels, debug ports).
- Public object stores, network rules `0.0.0.0/0` on administrative ports (sec-cloud-security).
- Logs with sensitive data (passwords, tokens, personal data).
- No limits: request and file size, time, number of login attempts.

Check the library version: defaults change between versions — the description concerns the default
behaviour, which must be confirmed in the documentation of the version in use.

## Sources
- MITRE CWE, cwe.mitre.org (accessed 2026-10-23); OWASP Cheat Sheet Series: Deserialization, XML External Entity
  Prevention, OS Command Injection Defense, Cryptographic Storage, cheatsheetseries.owasp.org (accessed 2026-10-23).
- Language and library documentation: Python (`secrets`, `subprocess`, PyYAML), Node.js (`crypto`, `vm`), Java
  (`ObjectInputFilter`), .NET (BinaryFormatter — migration guide), Go (`html/template`, `crypto/rand`).
- Topic inspiration: Trail of Bits, the `sharp-edges` and `insecure-defaults` skills (CC BY-SA 4.0 — no content taken over).
Described in our own words.
