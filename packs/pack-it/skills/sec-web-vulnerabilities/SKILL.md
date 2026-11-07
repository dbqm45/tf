---
name: sec-web-vulnerabilities
description: Użyj, gdy piszesz lub audytujesz kod aplikacji webowej pod kątem podatności — IDOR, XSS, CSRF, SSRF, upload, wstrzyknięcia, obejścia filtrów, moduły zaawansowane.
metadata:
  przeglad: "2027-05-07"
  katalog: "Użyj, gdy piszesz, przeglądasz albo audytujesz kod aplikacji webowej lub API (także napisany szybko z pomocą AI) i trzeba myśleć jak łowca błędów: gdzie dana klasa podatności się chowa, jak atakujący omija typowy filtr, jaka obrona jest skuteczna i jaki test to udowadnia. Klasy podstawowe: kontrola dostępu (IDOR/BOLA, BFLA), XSS, CSRF, sekrety po stronie klienta, open redirect, SSRF, upload plików, wstrzyknięcia SQL/NoSQL/poleceń, XXE, path traversal, nagłówki bezpieczeństwa, błędy JWT. Moduły zaawansowane do wyboru: logika biznesowa i wyścigi, warstwa HTTP (smuggling, zatruwanie i oszukiwanie cache, nagłówek Host), parsery i serializacja (prototype pollution, SSTI, deserializacja, ReDoS, normalizacja Unicode), przeglądarka (CORS, postMessage, WebSocket, obejścia CSP, XS-Leaks), API (mass assignment, GraphQL, limity), otoczenie aplikacji (przejęcie subdomeny, DNS rebinding, publiczne zasobniki). Raport z werdyktem, CWE, plik:linia, dowodem i testem. Nie do projektu sesji, tokenów i OAuth (be-auth-security), programu AppSec, skanerów i SLA (sec-appsec-devsecops), szukania wariantów znalezionego błędu (sec-variant-analysis), pisania reguł Semgrep (tool-semgrep), modelu zagrożeń (arch-threat-modeling) ani aplikacji z LLM (sec-llm-security)."
  slowa: "czy ten kod jest bezpieczny, podatności w aplikacji webowej, vibe coding bezpieczeństwo, kod od AI bezpieczny, audyt bezpieczeństwa aplikacji, przegląd bezpieczeństwa kodu, jak atakujący to obejdzie, obejście filtra, bug bounty, łowca błędów, idor, bola, cudze dane po zmianie id, xss, stored xss, reflected xss, dom xss, location.hash w innerhtml, csrf, ssrf, podgląd linku, pobieranie url od użytkownika, upload plików, wgrywanie plików, sql injection, nosql injection, command injection, xxe, path traversal, open redirect, klucz api w frontendzie, nagłówki bezpieczeństwa, csp, jwt alg none, wyścig, race condition, kupon użyty kilka razy, podwójne naliczenie, request smuggling, cache poisoning, web cache deception, prototype pollution, ssti, mass assignment, graphql introspekcja, cors, postmessage, websocket origin, przejęcie subdomeny"
---

# Podatności aplikacji webowej — pisanie i audyt oczami atakującego

Cel: kod aplikacji webowej nie zawiera znanych klas podatności, a każda obrona ma test, który pokazuje, że działa.
Myślisz jak łowca błędów: przy każdym wejściu pytasz „co jeśli to kontroluje atakujący” i „jak ominąłbym tę
kontrolę”. Pracujesz tylko na kodzie, który jest Twój albo do którego masz zgodę; dowód podatności to test
w repozytorium albo żądanie do lokalnej instancji, nigdy atak na cudzy lub produkcyjny system (core-agent-security).

## Tryby
| Tryb | Kiedy | Co robisz |
|---|---|---|
| **pisanie** | nowa funkcja, endpoint, formularz | przed kodem: tabela „wejście → klasa → obrona → test” (niżej); obronę piszesz od razu, test przed implementacją (TDD) |
| **przegląd** | diff, PR | tylko klasy, których dotyka diff (mapa niżej); ustalenie bez dowodu z diffu to pytanie, nie błąd |
| **audyt podstawowy** | aplikacja, moduł, przed wydaniem | wszystkie klasy z `references/klasy-podstawowe.md` po kolei, z obejściami |
| **audyt zaawansowany** | na prośbę albo gdy aplikacja ma pieniądze, wielu najemców, cache/CDN, własne parsery | audyt podstawowy + wybrane moduły z `references/moduly-zaawansowane.md` |

Moduły zaawansowane wybierasz po cechach aplikacji, nie wszystkie naraz:
- **A1 logika i wyścigi** — pieniądze, kupony, limity, stany zamówień, zaproszenia;
- **A2 warstwa HTTP** — CDN, reverse proxy, cache, kilka serwerów w łańcuchu;
- **A3 parsery i serializacja** — merge obiektów z JSON, szablony z treścią użytkownika, własne formaty, wyrażenia
  regularne na wejściu;
- **A4 przeglądarka** — CORS z poświadczeniami, `postMessage`, WebSocket, osadzanie w iframe, CSP;
- **A5 API** — automatyczne wiązanie pól, GraphQL, publiczne API z limitami;
- **A6 otoczenie** — własne domeny i subdomeny, zasobniki plików, usługi wewnętrzne osiągalne z aplikacji.

## Mapa: co w kodzie → jaka klasa
| W kodzie widzisz | Sprawdź |
|---|---|
| identyfikator z URL, body lub nagłówka użyty do odczytu/zapisu | kontrola dostępu per obiekt (IDOR, CWE-639) i per funkcja (BFLA, CWE-285) |
| HTML z danych, `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, szablon bez escapowania | XSS (CWE-79): zapisany, odbity, w DOM; kontekst wyjścia |
| zmiana stanu przez ciasteczko sesji | CSRF (CWE-352), `SameSite`, token, metoda |
| URL od użytkownika pobierany przez serwer (webhook, podgląd, import, PDF z HTML) | SSRF (CWE-918) |
| parametr `next`, `returnUrl`, `redirect` | open redirect (CWE-601) |
| plik od użytkownika | upload (CWE-434), path traversal (CWE-22), XXE w SVG/DOCX (CWE-611) |
| sklejanie SQL, filtrów NoSQL, poleceń powłoki, ścieżek | wstrzyknięcia (CWE-89, CWE-943, CWE-78), CWE-22 |
| klucz, token, URL wewnętrzny w kodzie frontu lub w zmiennej `NEXT_PUBLIC_*`/`VITE_*` | sekret w kliencie (CWE-798, CWE-200) |
| weryfikacja JWT | `alg`, klucz, `aud`/`iss`/`exp` (CWE-347) — szczegóły sesji w be-auth-security |
| „sprawdź, potem zapisz” na wspólnym zasobie | wyścig (CWE-362) — moduł A1 |
| `Object.assign(model, req.body)`, `Model.update(req.body)` | mass assignment (CWE-915) — moduł A5 |

## Procedura audytu
1. **Zakres i mapa wejść:** trasy, akcje serwera, handlery webhooków, kolejki, zadania cykliczne, upload. Dla każdego:
   kto może wywołać (anonim, użytkownik, admin, inny najemca), jakie dane przyjmuje, co zmienia.
2. **Klasy podstawowe** wg `references/klasy-podstawowe.md`: dla każdej najpierw znajdź miejsca (grep po wzorcach z
   pliku), potem sprawdź obronę i jej obejścia. Nie kończ na pierwszym znalezisku w klasie.
3. **Moduły zaawansowane** — tylko wybrane (wyżej), wg `references/moduly-zaawansowane.md`.
4. **Dowód:** dla każdego ustalenia test, który bez poprawki nie przechodzi (żądanie innego użytkownika, równoległe
   żądania, ładunek obejścia). Bez dowodu ustalenie ma wagę „do potwierdzenia”.
5. **Poprawka u źródła:** jedna wspólna funkcja (np. `loadOwned(model, id, user)`), nie łatki w każdym endpoincie.
   Ten sam błąd w wielu miejscach → sec-variant-analysis; reguła blokująca nowe wystąpienia → tool-semgrep.
6. **Raport** w formacie niżej.

## Format raportu
Pierwsza linia: `Werdykt: BLOKUJE | DO POPRAWY | BEZ USTALEŃ` (BLOKUJE przy wadze krytycznej lub wysokiej
z dowodem). Potem tabela:

| ID | Klasa (CWE) | Miejsce (plik:linia) | Dowód | Waga | Poprawka | Test |
|---|---|---|---|---|---|---|

Waga: krytyczna (zdalnie, bez logowania, cudze dane lub kod), wysoka (po zalogowaniu, cudze dane lub pieniądze),
średnia (wymaga interakcji ofiary lub rzadkiego warunku), niska (utwardzenie). Na końcu: zakres (co sprawdzono,
które moduły zaawansowane, czego nie) — brak ustaleń w niesprawdzonej części nie jest werdyktem.

## Przykład
Wejście: „Endpoint `GET /api/invoices/:id` z `requireLogin`, zwraca `Invoice.findById(req.params.id)`”.

Wynik:
```
Werdykt: BLOKUJE
| W1 | IDOR (CWE-639) | src/routes/invoices.ts:14 | użytkownik B pobiera fakturę A, zmieniając id (test) | wysoka |
  zapytanie z właścicielem: Invoice.findOne({ _id: id, tenantId: user.tenantId }), brak → 404 |
  test: faktura A, sesja B → 404; sesja A → 200 |
Zakres: trasy /api/invoices/*; inne trasy z :id — do sprawdzenia tym samym wzorcem (sec-variant-analysis).
```
Odpowiedź 404 zamiast 403 nie zdradza, że obiekt istnieje. Sam `requireLogin` sprawdza tożsamość, nie prawo do
obiektu.

## Pisanie nowej funkcji — tabela przed kodem
| Wejście | Klasa | Obrona | Test |
|---|---|---|---|
| `invoiceId` z URL | IDOR | zapytanie zawsze z `tenantId`/`ownerId` z sesji | obcy użytkownik → 404 |
| `returnUrl` | open redirect | tylko ścieżka względna z allowlisty, bez `//` i `\` | `//evil.example`, `/\evil.example` → strona główna |
| URL webhooka | SSRF | allowlista schematów i portów, rozwiązanie DNS i blokada zakresów prywatnych przy każdym połączeniu, bez przekierowań | `http://169.254.169.254/`, nazwa rozwiązywana na `10.0.0.1` → odmowa |

## Checklista
- [ ] każde wejście ma klasę, obronę i test; obrony w jednym module, nie rozsiane
- [ ] kontrola dostępu na serwerze per obiekt i per funkcja, domyślnie odmowa
- [ ] w audycie: wszystkie klasy podstawowe i wybrane moduły zaawansowane, zakres zapisany
- [ ] raport z werdyktem w pierwszej linii, CWE, plik:linia, dowodem i testem
- [ ] dowody tylko lokalnie lub w testach; żadnych ataków na systemy bez zgody

## Źródła
- OWASP Web Security Testing Guide v4.2 (owasp.org, wersja stabilna, [niezweryfikowane] dostęp 2026-11-07) — klasy testów.
- OWASP ASVS 5.0.0 (owasp.org, maj 2025, [niezweryfikowane] dostęp 2026-11-07) — wymagania weryfikacji.
- MITRE CWE (cwe.mitre.org) — identyfikatory klas użyte w tabelach.
- PortSwigger Web Security Academy (portswigger.net/web-security, [niezweryfikowane] dostęp 2026-11-07) — techniki
  obejść i klasy zaawansowane (smuggling, cache, prototype pollution, wyścigi).

Opisane własnymi słowami.
