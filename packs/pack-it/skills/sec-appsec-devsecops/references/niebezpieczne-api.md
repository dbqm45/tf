# Niebezpieczne API i domyślne konfiguracje — lista do przeglądu

Lista pytań do przeglądu kodu i konfiguracji. Trafienie to kandydat, nie wyrok: sprawdzasz, czy dane są
niezaufane i czy po drodze jest kontrola. Znalezione wystąpienie → poszukaj wariantów (sec-variant-analysis).

## Spis treści
- Wzorce wspólne
- Python · JavaScript i Node.js · Java · C# i .NET · Go
- Domyślne konfiguracje i ustawienia środowiska

## Wzorce wspólne
- **Interpreter z wejścia**: `eval`, wykonanie szablonu, wyrażenia (SpEL, OGNL), polecenie powłoki sklejane ze
  stringa — dane jako kod (CWE-94, CWE-78).
- **Deserializacja formatów z typami** z niezaufanego źródła (CWE-502) — używaj formatów bez typów (JSON do DTO).
- **Zapytania sklejane ze stringa** — SQL, LDAP, XPath, NoSQL (CWE-89, CWE-90, CWE-643); identyfikatory (kolumny,
  kierunek sortowania) tylko z listy dozwolonych.
- **Parsery XML z encjami zewnętrznymi** (XXE, CWE-611).
- **Losowość niekryptograficzna** do tokenów, haseł, identyfikatorów sesji (CWE-338).
- **Słabe skróty i szyfry**: MD5, SHA-1 do haseł lub podpisów, ECB, własna kryptografia; hasła tylko przez
  Argon2id, scrypt lub bcrypt (sec-cryptography-pki).
- **Wyłączona weryfikacja TLS** albo nazwy hosta (CWE-295).
- **Fail-open**: wyjątek w sprawdzeniu uprawnień kończy się dostępem; pusta lista ról = wszyscy.
- **Porównanie sekretów zwykłym `==`** zamiast porównania w stałym czasie.
- **Wyrażenia regularne z zagnieżdżonymi kwantyfikatorami** na wejściu użytkownika (ReDoS, CWE-1333).

## Python
| Kandydat | Bezpieczniej |
|---|---|
| `pickle.loads`, `shelve`, `marshal` na danych z zewnątrz | JSON + walidacja schematu |
| `yaml.load` bez bezpiecznego loadera | `yaml.safe_load` |
| `eval`, `exec`, `compile` z wejściem | parser lub mapa dozwolonych operacji |
| `subprocess.*(..., shell=True)`, `os.system` | lista argumentów bez powłoki |
| `random` do tokenów | `secrets` |
| `hashlib.md5/sha1` do haseł | Argon2id / scrypt / bcrypt |
| `requests.*(verify=False)` | poprawny łańcuch CA |
| `xml.etree`, `lxml` na niezaufanym XML | `defusedxml` |
| `tempfile.mktemp` | `tempfile.mkstemp` / `NamedTemporaryFile` |
| Django: `DEBUG = True`, `SECRET_KEY` w repo, `ALLOWED_HOSTS = ['*']` | zmienne środowiskowe, lista hostów |
| Flask: `app.run(debug=True)`; Jinja2 `autoescape=False` | debug tylko lokalnie; autoescape włączony |

## JavaScript i Node.js
| Kandydat | Bezpieczniej |
|---|---|
| `eval`, `new Function`, `setTimeout("kod")` | funkcje, nie stringi |
| `child_process.exec` ze sklejonym poleceniem | `execFile` / `spawn` z tablicą argumentów |
| moduł `vm` jako „piaskownica” | to nie jest granica bezpieczeństwa — osobny proces lub izolacja |
| `innerHTML`, `dangerouslySetInnerHTML`, `v-html` z danymi | tekst albo sanityzacja (DOMPurify) |
| `Math.random` do tokenów | `crypto.randomBytes`, `crypto.randomUUID` |
| scalanie obiektów z wejścia (`__proto__`, `constructor`) | walidacja schematu, obiekty bez prototypu |
| JWT: weryfikacja bez listy algorytmów | jawna lista algorytmów, sprawdzenie `aud` i `iss` |
| `NODE_TLS_REJECT_UNAUTHORIZED=0` | poprawny łańcuch CA |

## Java
| Kandydat | Bezpieczniej |
|---|---|
| `ObjectInputStream.readObject` na danych z zewnątrz | JSON do DTO; jeśli musi zostać — filtr deserializacji (`ObjectInputFilter`) |
| `DocumentBuilderFactory`, `SAXParserFactory`, `XMLInputFactory` z ustawieniami domyślnymi | wyłączone DTD i encje zewnętrzne |
| `Runtime.exec(String)` ze sklejonym poleceniem | `ProcessBuilder` z listą argumentów |
| `java.util.Random` do tokenów | `SecureRandom` |
| `TrustManager` akceptujący wszystko, `HostnameVerifier` zwracający `true` | domyślna weryfikacja |
| SpEL lub szablony z wejścia | bez ewaluacji danych użytkownika |
| Spring Boot Actuator wystawiony publicznie | tylko `health` publicznie, reszta za uwierzytelnieniem |

## C# i .NET
| Kandydat | Bezpieczniej |
|---|---|
| `BinaryFormatter`, `NetDataContractSerializer`, `LosFormatter` | `System.Text.Json` do DTO |
| Newtonsoft.Json `TypeNameHandling` inne niż `None` | `None` albo jawny `SerializationBinder` |
| `SqlCommand` ze sklejonym SQL, `FromSqlRaw` z interpolacją stringa | parametry, `FromSqlInterpolated` |
| `Process.Start` z `cmd /c` i danymi | argumenty bez powłoki |
| `System.Random` do tokenów | `RandomNumberGenerator` |
| `ServerCertificateCustomValidationCallback` zwracający `true` | domyślna weryfikacja |
| `XmlDocument`/`XmlTextReader` z resolverem encji (starsze .NET Framework) | `XmlResolver = null`, `DtdProcessing.Prohibit` |

## Go
| Kandydat | Bezpieczniej |
|---|---|
| `text/template` do HTML | `html/template` |
| `math/rand` do tokenów | `crypto/rand` |
| `tls.Config{InsecureSkipVerify: true}` | domyślna weryfikacja |
| `exec.Command("sh", "-c", ...)` z danymi | polecenie i argumenty osobno |
| `fmt.Sprintf` do SQL | parametry `?` / `$1` |
| `http.ListenAndServe` bez limitów czasu | `http.Server` z `ReadHeaderTimeout` i pozostałymi limitami |
| pakiet `unsafe`, `reflect` na danych z zewnątrz | uzasadnienie w przeglądzie |

## Domyślne konfiguracje i ustawienia środowiska
- Domyślne konta i hasła (panel administracyjny, baza, broker, kamera, urządzenie), konta testowe zostawione
  po wdrożeniu.
- Sekrety z przykładów (`changeme`, `secret`, klucz JWT z dokumentacji) w konfiguracji produkcyjnej; sekrety
  w repozytorium (ops-secrets-identities).
- Tryb debug i strony błędów ze stosem wywołań na produkcji.
- CORS `*` razem z ciasteczkami lub nagłówkiem uwierzytelnienia; ciasteczka sesji bez `Secure`, `HttpOnly`,
  `SameSite`.
- Usługi bez uwierzytelnienia nasłuchujące na wszystkich interfejsach (np. Redis, Elasticsearch, panele
  zarządzania, porty debugowania).
- Publiczne magazyny obiektów, reguły sieci `0.0.0.0/0` na portach administracyjnych (sec-cloud-security).
- Logi z danymi wrażliwymi (hasła, tokeny, dane osobowe).
- Brak limitów: rozmiar żądania i pliku, czas, liczba prób logowania.

Sprawdzaj wersję biblioteki: domyślne ustawienia zmieniają się między wersjami — opis dotyczy zachowania
domyślnego, które trzeba potwierdzić w dokumentacji używanej wersji.

## Źródła
- MITRE CWE, cwe.mitre.org (dostęp 2026-10-23); OWASP Cheat Sheet Series: Deserialization, XML External Entity
  Prevention, OS Command Injection Defense, Cryptographic Storage, cheatsheetseries.owasp.org (dostęp 2026-10-23).
- Dokumentacja języków i bibliotek: Python (`secrets`, `subprocess`, PyYAML), Node.js (`crypto`, `vm`), Java
  (`ObjectInputFilter`), .NET (BinaryFormatter — przewodnik migracji), Go (`html/template`, `crypto/rand`).
- Inspiracja tematem: Trail of Bits, skille `sharp-edges` i `insecure-defaults` (CC BY-SA 4.0 — treści nie przejęto).
Opisane własnymi słowami.
