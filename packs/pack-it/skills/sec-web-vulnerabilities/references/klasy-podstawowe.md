# Klasy podstawowe — sygnały, obejścia, poprawna obrona, dowód

> **Spis treści:** 1. Kontrola dostępu — IDOR/BOLA (CWE-639), BFLA (CWE-285) · 2. XSS (CWE-79) · 3. CSRF (CWE-352) · 4. Sekrety i nadmiar danych po stronie klienta (CWE-798,… · 5. Open redirect (CWE-601) · 6. Hasła · 7. SSRF (CWE-918) · 8. Upload plików (CWE-434) · 9. Wstrzyknięcia — SQL (CWE-89), NoSQL (CWE-943), polecenia… · 10. XXE (CWE-611) · 11. Path traversal (CWE-22) · 12. Nagłówki bezpieczeństwa · 13. JWT (CWE-347)

Każda klasa w tym samym układzie:
- **Sygnały** — czego szukasz w kodzie;
- **Obejścia** — jak atakujący pokonuje typową, niepełną obronę;
- **Poprawnie** — obrona, która działa;
- **Dowód** — test, który bez poprawki nie przechodzi.

Zasada wspólna: każde wejście jest pod kontrolą atakującego, dopóki serwer nie udowodni inaczej. Obrona stoi na
serwerze, jest w jednym module i przy błędzie odmawia. Walidacja w przeglądarce to tylko wygoda dla użytkownika.

## 1. Kontrola dostępu — IDOR/BOLA (CWE-639), BFLA (CWE-285)
**Sygnały:** `findById(req.params.id)`, `WHERE id = ?` bez kolumny właściciela, identyfikator z body lub nagłówka
(`X-User-Id`, `tenantId` w JSON), endpointy eksportu, wyszukiwania, załączników i operacji masowych. Także zasób
podrzędny sprawdzany bez rodzica (komentarz bez posta, plik bez projektu) oraz rola odczytana z tokenu klienta lub
z body.

**Obejścia:**
- zmiana liczby w URL, a przy UUID — identyfikator z innego miejsca, w którym wycieka (lista, e-mail, log);
- metoda, której nikt nie zabezpieczył (`PUT` obok chronionego `GET`);
- stara wersja API (`/v1/` bez kontroli, gdy `/v2/` ją ma);
- parametr dopisany do body (`"ownerId": "…"`).

**Poprawnie:**
- filtr własności w samym zapytaniu, z identyfikatorem użytkownika lub najemcy wziętym z sesji;
- jedna funkcja w stylu `loadOwned(model, id, user)`, a nie warunek dopisywany w każdym kontrolerze;
- domyślnie odmowa;
- odpowiedź 404 i dla obiektu nieistniejącego, i dla cudzego.

Niezgadywalne identyfikatory utrudniają wyliczanie, ale nie są kontrolą dostępu. Utrata członkostwa w organizacji
odbiera dostęp od razu (unieważnianie sesji: be-auth-security).

**Dowód:**
- zasób użytkownika A, żądanie z sesją B → 404;
- funkcja administratora z sesją zwykłego użytkownika → 403/404;
- te same przypadki dla każdej metody HTTP na ścieżce.

## 2. XSS (CWE-79)
**Sygnały — ujścia:** `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `dangerouslySetInnerHTML`,
`v-html`, `[innerHTML]`, `bypassSecurityTrust*`, `|safe`, `{!! !!}`, `href`/`src` z danych oraz `eval` i `setTimeout`
z napisem.

**Sygnały — źródła poza formularzem:**
- query string i fragment `#`;
- nazwa wgranego pliku;
- nagłówki pokazywane w panelu (User-Agent w logach);
- dane z zewnętrznego API;
- wiadomości WebSocket i `postMessage`;
- wartości z `localStorage`;
- treść Markdown z dopuszczonym HTML;
- pliki SVG;
- szablony e-maili i PDF generowane z HTML;
- komunikaty błędów, które powtarzają wejście.

**Obejścia:**
- kontekst inny niż zakładany: wartość wstawiona do atrybutu bez cudzysłowu albo do skryptu inline;
- link `javascript:` w polu „strona WWW”;
- filtr czarnej listy omijany wielkością liter, kodowaniem albo innym zdarzeniem (`onfocus`, `ontoggle`);
- sanitizer uruchomiony przed dalszą obróbką tekstu (mutation XSS).

**Poprawnie:**
- escapowanie frameworka zostaje włączone; każde ujście z listy wyżej przechodzi przegląd;
- HTML od użytkownika tylko przez sanitizer z allowlistą (np. DOMPurify), uruchamiany **ostatni**, tuż przed
  wstawieniem;
- URL z danych tylko ze schematem `https:` (ewentualnie `mailto:`);
- druga linia obrony: CSP z nonce lub hash, bez `'unsafe-inline'` i `'unsafe-eval'` w `script-src`, z `object-src 'none'`
  i `base-uri 'none'` (moduł A4);
- `X-Content-Type-Options: nosniff`.

**Dowód:**
- ładunek dla każdego kontekstu (`<img src=x onerror=alert(1)>`, `" autofocus onfocus=alert(1) x="`,
  `javascript:alert(1)`) zapisany i wyświetlony → w DOM jako tekst, bez wykonania;
- typ testu: test renderowania komponentu albo e2e.

## 3. CSRF (CWE-352)
**Sygnały:**
- sesja w ciasteczku i endpoint zmieniający stan bez tokenu;
- `GET`, który coś zmienia (`/unsubscribe?id=`, `/approve?id=`);
- walidacja tokenu tylko wtedy, gdy przyszedł w żądaniu;
- logowanie, rejestracja, reset hasła, zmiana e-maila i callback OAuth bez ochrony — atak działa także przed
  zalogowaniem: ofiara zostaje zalogowana na konto atakującego.

**Obejścia:**
- JSON wysłany formularzem jako `text/plain`, a serwer parsuje go bez sprawdzenia typu;
- ciasteczko `SameSite=Lax` przy zmianie stanu przez `GET`;
- subdomena atakującego (albo przejęta) ustawia ciasteczko tokenu w wariancie double submit;
- CORS z poświadczeniami i odbitym originem (moduł A4).

**Poprawnie:**
- token losowy, związany z sesją, w nagłówku, wymagany zawsze — brak tokenu oznacza odrzucenie;
- nowy token po zalogowaniu;
- ciasteczka sesji `SameSite=Lax` lub `Strict`, `Secure`, `HttpOnly`, z prefiksem `__Host-`;
- serwer sprawdza `Origin` lub `Sec-Fetch-Site`;
- zmiana stanu tylko metodami innymi niż `GET`;
- `state` w OAuth związany z sesją.

**Dowód:** zmiana stanu z ważnym ciasteczkiem i bez tokenu → 403; z `Origin: https://evil.example` → 403; `GET` na
endpoint zmieniający → 405.

## 4. Sekrety i nadmiar danych po stronie klienta (CWE-798, CWE-200)
**Sygnały:**
- zmienne publiczne narzędzi budowania (`NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*`, `PUBLIC_*`) z kluczami, które dają
  zapis albo płatności;
- import modułu serwerowego w komponencie klienckim;
- mapy źródeł (`*.map`) wdrożone na produkcję;
- stan hydracji (`__NEXT_DATA__`, `window.__INITIAL_STATE__`) z całymi rekordami;
- odpowiedzi API zwracające całą encję (hash hasła, token resetu, pełny PESEL, numer karty);
- stack trace i wersje serwera w odpowiedziach błędów;
- komentarze HTML i atrybuty `data-*` z wewnętrznymi adresami.

**Obejścia:** to nie są obejścia, tylko odczyt: atakujący otwiera paczkę JS albo narzędzia deweloperskie przeglądarki.

**Poprawnie:**
- wywołania wymagające sekretu tylko z backendu (route handler, akcja serwera, BFF);
- sekret w menedżerze sekretów albo w zmiennej środowiska serwera, w repo tylko `.env.example` (ops-secrets-identities);
- odpowiedzi przez DTO z jawną listą pól;
- klucz z założenia publiczny (publishable key, klucz map) ograniczony u dostawcy do domeny i zakresu;
- dane wrażliwe maskowane w UI (`***-***-123`);
- błędy w produkcji bez szczegółów technicznych.

**Dowód:** grep po zbudowanej paczce i mapach źródeł (`sk_live_`, `AKIA`, `-----BEGIN`, `secret`, nazwy zmiennych
z `.env.example`); test snapshotu odpowiedzi API bez pól wrażliwych.

## 5. Open redirect (CWE-601)
**Sygnały:** `res.redirect(req.query.next)`, `window.location = params.get('returnUrl')`, `redirect_uri` sprawdzany
przez `startsWith` albo `includes`.

**Obejścia:**
| Wejście | Co się dzieje |
|---|---|
| `//evil.example` | URL względny wobec schematu: przeglądarka idzie na obcy host |
| `/\evil.example`, `\/evil.example` | przeglądarki traktują `\` jak `/` |
| `https://app.example@evil.example` | część przed `@` to nazwa użytkownika, host to `evil.example` |
| `https://app.example.evil.example` | `startsWith('https://app.example')` przepuszcza cudzą domenę |
| `https://app.example#@evil.example`, `?@` | różne parsery różnie rozumieją host |
| `%2f%2fevil.example`, `%252f%252f…` | walidacja przed dekodowaniem, przekierowanie po dekodowaniu (raz lub dwa razy) |
| `%09`, `%0a`, `%00` w adresie | znaki usuwane przez przeglądarkę albo ucinające napis |
| `javascript:…`, `data:text/html,…` | przekierowanie staje się XSS |
| `аpp.example` (cyrylickie „а”) | homograf IDN, wygląda jak zaufana domena |

**Poprawnie (od najlepszej):**
1. Referencja pośrednia — `?to=settings` mapowane na stałą ścieżkę.
2. Tylko ścieżka względna: po zdekodowaniu zaczyna się od jednego `/`, nie zawiera `//`, `\`, `@` ani znaków
   sterujących.
3. Pełny URL tylko po sparsowaniu standardowym parserem WHATWG, z dokładnym porównaniem hosta z allowlistą po
   konwersji do Punycode i ze schematem `https:`.

**Dowód:** test parametryzowany, w którym każdy wiersz tabeli daje przekierowanie na stronę domyślną.

## 6. Hasła
Wymagania wg NIST SP 800-63B-4 (2025) [niezweryfikowane]:
- długość minimalna 15 znaków, gdy hasło jest jedynym składnikiem logowania, albo 8 przy MFA;
- maksimum co najmniej 64 znaki;
- dozwolone wszystkie znaki, także spacje i Unicode;
- bez reguł składu i bez wymuszonej okresowej zmiany;
- sprawdzenie na liście haseł wyciekłych.

Przechowywanie: Argon2id, scrypt albo bcrypt; nigdy MD5, SHA-1 ani pojedynczy SHA-256. Limity prób, reset hasła
i MFA: be-auth-security.

## 7. SSRF (CWE-918)
**Sygnały:**
- serwer pobiera URL z wejścia: webhook, podgląd linku, import z URL, awatar z adresu, RSS, integracja z endpointem
  klienta, proxy;
- render HTML do PDF lub obrazu — przeglądarka bez okna pobiera każdy `<img>` i `<iframe>` z treści;
- parser XML z encjami zewnętrznymi (sekcja 10).

**Obejścia:**
| Technika | Przykład |
|---|---|
| zapis IPv4 inny niż kropkowy | `2130706433`, `0177.0.0.1`, `0x7f000001`, `127.1` |
| IPv6 | `[::1]`, `[::]`, `[::ffff:127.0.0.1]`, `[fe80::1%25eth0]` |
| nazwa rozwiązywana na adres wewnętrzny | `127.0.0.1.nip.io`, CNAME na `db.internal` |
| DNS rebinding | sprawdzenie widzi adres publiczny, połączenie — wewnętrzny (krótki TTL) |
| przekierowanie | publiczny URL odpowiada `302 Location: http://169.254.169.254/` |
| różnice parserów | `http://evil.example#@internal`, `http://internal\@evil.example` |
| inny schemat | `file://`, `gopher://`, `dict://` w bibliotekach, które je obsługują |

**Poprawnie:**
1. Allowlista hostów, gdy integracja na to pozwala.
2. Inaczej:
   - tylko `http`/`https` na dozwolonych portach;
   - rozwiązanie DNS po stronie aplikacji i odrzucenie adresów prywatnych, loopback, link-local, `0.0.0.0/8`, ULA IPv6
     i mapowanych IPv4;
   - **połączenie z tym samym adresem, który sprawdzono** (przypięcie IP w kliencie HTTP, np. własny `lookup`
     w agencie Node), żeby zamknąć DNS rebinding.
3. Przekierowania wyłączone albo każdy przeskok sprawdzany od nowa.
4. Limit czasu i rozmiaru odpowiedzi; użytkownik nie dostaje surowej odpowiedzi ani szczegółów błędów (ślepy SSRF
   też jest SSRF).
5. Pobieranie w osobnej usłudze lub sieci bez dostępu do zasobów wewnętrznych.
6. Metadane chmury zablokowane jawnie: `169.254.169.254`, `fd00:ec2::254`, `metadata.google.internal`; na AWS
   IMDSv2 z limitem przeskoków 1.

**Dowód:**
- każdy wiersz tabeli → odmowa **przed** nawiązaniem połączenia (test z atrapą resolvera i lokalnym serwerem
  sprawdzającym, że nie dostał żądania);
- przekierowanie na `169.254.169.254` → odmowa.

## 8. Upload plików (CWE-434)
**Sygnały:**
- zapis pod nazwą od użytkownika;
- katalog uploadu serwowany przez ten sam serwer, który wykonuje skrypty;
- sprawdzanie tylko `Content-Type` z żądania albo tylko rozszerzenia;
- rozpakowywanie archiwów;
- przetwarzanie obrazów zewnętrznym programem z nazwą pliku w poleceniu.

**Obejścia:**
| Sztuczka | Przykład | Co zatrzymuje |
|---|---|---|
| dwa rozszerzenia | `faktura.pdf.php`, `foto.php.jpg` | jedno rozszerzenie z allowlisty, nazwa losowa |
| bajt zerowy, spacja, kropka na końcu | `shell.php%00.png`, `shell.php.` | losowa nazwa nadawana przez serwer |
| fałszywy typ MIME | skrypt wysłany jako `image/png` | sprawdzenie sygnatury i parsowanie |
| poliglota | plik jednocześnie poprawnym GIF-em i skryptem | ponowne zakodowanie obrazu (np. przeskalowanie) |
| SVG z JavaScriptem | `<svg onload=…>` | sanitizer SVG, konwersja do PNG albo zakaz |
| dokument biurowy z XML | DOCX/XLSX z encją zewnętrzną | parser bez DTD (sekcja 10) |
| archiwum z `../` | Zip Slip | kanonizacja ścieżki każdego wpisu (sekcja 11) |
| bomba dekompresyjna | mały ZIP, gigabajty po rozpakowaniu | limit łącznego rozmiaru i liczby wpisów |
| nazwa pliku w poleceniu | `a.jpg; curl …` | wywołanie bez powłoki, nazwa losowa |
| zgadywanie typu przez przeglądarkę | HTML serwowany jako „obraz” | `nosniff`, `Content-Type` z wykrytego typu |

Sygnatury do sprawdzenia: JPEG `FF D8 FF`, PNG `89 50 4E 47 0D 0A 1A 0A`, GIF `47 49 46 38`, PDF `25 50 44 46`,
ZIP oraz DOCX/XLSX/PPTX `50 4B 03 04`.

**Poprawnie:**
- allowlista typów potwierdzona sygnaturą **i** parsowaniem biblioteką danego formatu;
- limity rozmiaru w aplikacji i na proxy;
- losowa nazwa;
- magazyn obiektów albo katalog poza webrootem, bez prawa wykonania;
- serwowanie z osobnej domeny z `Content-Disposition: attachment`, `nosniff` i poprawnym `Content-Type`;
- biblioteki obrazów aktualne, w osobnym procesie (ImageMagick z restrykcyjną polityką zasobów (policy.xml));
- dokumenty z makrami odrzucane albo skanowane.

**Dowód:** każdy wiersz tabeli jako plik w katalogu testowym → odrzucenie albo bezpieczne serwowanie (pobranie
zamiast wykonania).

## 9. Wstrzyknięcia — SQL (CWE-89), NoSQL (CWE-943), polecenia systemowe (CWE-78)
**Sygnały — SQL:**
- sklejanie napisów i szablony literałów w zapytaniu;
- metody „raw” ORM-ów z interpolacją (`$queryRawUnsafe`, `sequelize.literal`, `knex.raw` z `${}`, `extra()`
  w Django);
- `ORDER BY`, nazwy kolumn i tabel, kierunek sortowania z parametru;
- `LIMIT` bez rzutowania na liczbę;
- listy `IN` budowane ręcznie;
- `LIKE` bez escapowania `%` i `_`.

**Sygnały — NoSQL:** obiekt z JSON trafia wprost do filtra (`{ email, password: req.body.password }`), operatory
`$where` i `$regex` z wejścia.

**Sygnały — polecenia:** `exec`, `system`, `shell=True`, `child_process.exec` z napisem, nazwy plików i URL-e
w poleceniu.

**Obejścia:**
- wstrzyknięcie tam, gdzie nie działa parametryzacja (sortowanie);
- drugi rząd: wartość zapisana bezpiecznie, później użyta w sklejonym zapytaniu raportu;
- `{"password": {"$ne": null}}` zamiast napisu;
- wstrzyknięcie opcji polecenia (`--output=/etc/…`) bez użycia znaków powłoki.

**Poprawnie:**
- zawsze zapytania parametryzowane;
- identyfikatory (kolumny, kierunek) tylko z allowlisty;
- wejście NoSQL rzutowane na typy proste albo walidowane schematem;
- polecenia przez `execFile`/`spawn`/`subprocess.run([...])` z listą argumentów, z `--` przed argumentami od
  użytkownika;
- użytkownik bazy z minimalnymi uprawnieniami (be-database);
- błędy bazy nie trafiają do odpowiedzi.

**Dowód:** `' OR '1'='1`, `1) OR (1=1`, sortowanie `name; DROP TABLE x`, `{"$ne": null}`, nazwa pliku `a; id` →
odrzucenie albo wynik identyczny jak dla zwykłego wejścia.

## 10. XXE (CWE-611)
**Sygnały:**
- jawne: endpointy SOAP i XML-RPC, import XML, kanały RSS/Atom, konfiguracja w XML od klienta;
- ukryte: DOCX/XLSX/PPTX (ZIP z XML), SVG, asercje SAML, konwersje innych formatów do XML.

**Obejścia:**
- encja zewnętrzna czytająca plik (`file:///etc/passwd`) albo wywołująca żądanie (SSRF);
- encje parametryczne i zewnętrzny DTD, gdy wyniku nie widać (wyciek poza pasmem);
- encje zagnieżdżone wykładniczo („billion laughs”).

**Poprawnie:**
- przetwarzanie DTD wyłączone w całości (bez encji zewnętrznych, zewnętrznych DTD i XInclude), parser aktualny;
- gdzie się da — JSON zamiast XML;
- ustawienia per język:

| Język | Ustawienie |
|---|---|
| Java | `DocumentBuilderFactory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)` (to samo dla SAX i StAX) |
| Python | `defusedxml` zamiast `xml.etree`/`lxml` dla danych z zewnątrz |
| .NET | `XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null }` |
| PHP 8+ | libxml ≥ 2.9 domyślnie nie ładuje encji; nie przekazuj `LIBXML_NOENT` ani `LIBXML_DTDLOAD` |
| Node.js | parser bez obsługi DTD; w libxmljs `noent: false`, `dtdload: false` |

**Dowód:** dokument z `<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>` → błąd parsowania albo
encja nierozwinięta.

## 11. Path traversal (CWE-22)
**Sygnały:** `path.join(UPLOADS, req.query.file)`, `open(base + name)`, `res.sendFile(name)`, nazwa szablonu
z parametru, rozpakowanie archiwum z nazwami wpisów.

**Obejścia:**
- `../`, a także `..%2f`, `%2e%2e/`, `....//` (gdy filtr usuwa `../` jeden raz) i `..\` na Windows;
- ścieżka bezwzględna (`/etc/passwd`, `C:\…`), którą `path.join` w niektórych językach przyjmuje jako nowy korzeń
  (Python `os.path.join`);
- dowiązanie symboliczne wewnątrz katalogu, które wychodzi poza niego.

**Poprawnie:**
- referencja pośrednia (identyfikator → ścieżka z bazy albo mapy);
- inaczej kanonizacja (`realpath`) i sprawdzenie, czy wynik leży w katalogu bazowym, a do tego allowlista znaków
  i rozszerzeń.
```python
def inside(base_dir: str, name: str) -> str:
    base = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base, name))
    if os.path.commonpath([base, target]) != base:
        raise PermissionError(name)
    return target
```

**Dowód:** każde obejście z listy i dowiązanie symboliczne wychodzące poza katalog → odmowa.

## 12. Nagłówki bezpieczeństwa
| Nagłówek | Wartość | Po co |
|---|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (`preload` po świadomej decyzji, bo trudno go wycofać) | tylko HTTPS |
| `Content-Security-Policy` | strict CSP z nonce, `frame-ancestors 'none'`, `object-src 'none'`, `base-uri 'none'` | druga linia przeciw XSS, clickjacking |
| `X-Content-Type-Options` | `nosniff` | bez zgadywania typu |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | tokeny w URL nie wyciekają do obcych stron |
| `Cache-Control` | `no-store` na stronach i odpowiedziach z danymi użytkownika | brak kopii w cache (moduł A2) |
| `Cross-Origin-Opener-Policy` | `same-origin` | izolacja okna (moduł A4) |

`X-Frame-Options: DENY` dodajesz tylko dla bardzo starych przeglądarek.

**Dowód:** test integracyjny nagłówków na reprezentatywnej stronie z danymi i na odpowiedzi API.

## 13. JWT (CWE-347)
| Błąd | Skutek | Poprawnie |
|---|---|---|
| algorytm z nagłówka tokenu, `alg: none` | token bez podpisu przechodzi | lista algorytmów w konfiguracji weryfikacji |
| RS256 → HS256 | klucz publiczny użyty jako sekret HMAC | `algorithms: ['RS256']`, osobny typ klucza |
| krótki sekret HMAC | złamanie słownikowe offline | ≥ 256 bitów losowych |
| `kid` w ścieżce pliku lub w SQL | traversal albo wstrzyknięcie | `kid` tylko jako klucz do mapy zaufanych kluczy |
| `jku`/`x5u` z tokenu | atakujący wskazuje własny klucz | klucze z konfiguracji lub zaufanego JWKS |
| brak `exp`, `aud`, `iss` | token żyje wiecznie albo działa w innej usłudze | weryfikacja wszystkich trzech |
| `decode` zamiast `verify` | brak weryfikacji podpisu | tylko `verify` na ścieżce autoryzacji |

```javascript
jwt.verify(token, publicKey, { algorithms: ['RS256'], audience: 'api', issuer: 'https://id.example' })
```

Przechowywanie w przeglądarce:
- ciasteczko `HttpOnly; Secure; SameSite` chroni przed odczytem przez XSS, ale wymaga ochrony CSRF (sekcja 3);
- token w pamięci aplikacji z krótkim czasem życia to też poprawny wybór;
- `localStorage` odpada, gdy XSS jest realnym ryzykiem;
- rotacja i unieważnianie tokenów: be-auth-security.

**Dowód:** token z `alg: none`, podpisany kluczem publicznym jako HMAC, przeterminowany, z obcym `aud` albo `iss`
→ 401.

## Źródła
- MITRE CWE (cwe.mitre.org) — identyfikatory klas.
- OWASP Cheat Sheet Series: XSS Prevention, CSRF Prevention, SSRF Prevention, File Upload, XXE Prevention,
  JSON Web Token (cheatsheetseries.owasp.org) [niezweryfikowane, dostęp 2026-11-07].
- NIST SP 800-63B-4 (2025) [niezweryfikowane] — wymagania dla haseł.
- WHATWG URL Standard (url.spec.whatwg.org) — parsowanie adresów w przeglądarkach.

Opisane własnymi słowami.
