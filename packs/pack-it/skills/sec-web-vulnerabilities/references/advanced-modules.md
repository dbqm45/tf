# Moduły zaawansowane — wybierane po cechach aplikacji

Każdy moduł: kiedy go włączyć, czego szukać w kodzie, jak atakujący to wykorzystuje, obrona i test. Dowody tylko
lokalnie albo w testach.

## A1. Logika biznesowa i wyścigi
**Włącz, gdy:** pieniądze, kredyty, kupony, limity (głosy, zaproszenia, próby), stany zamówień, zwroty.

| Problem | W kodzie | Obrona | Test |
|---|---|---|---|
| wyścig „sprawdź, potem zapisz” (CWE-362, TOCTOU) | `if (!coupon.used) { …; coupon.used = true }`, saldo czytane i zapisywane osobno | jeden atomowy zapis warunkowy: `UPDATE coupons SET used = true WHERE id = ? AND used = false` i sprawdzenie liczby zmienionych wierszy; albo `SELECT … FOR UPDATE` w transakcji; ograniczenie unikalności (np. `UNIQUE(user_id, coupon_id)`) | N równoległych żądań (`Promise.all`, pula wątków) → dokładnie jedno udane |
| powtórzenie żądania płatności | brak klucza idempotencji | `Idempotency-Key` zapisany z wynikiem w tej samej transakcji (be-api-design) | dwa identyczne żądania → jedno obciążenie |
| przeskok stanu | `status` z body, brak maszyny stanów | dozwolone przejścia w jednym miejscu, przejście jako warunek w `UPDATE … WHERE status = 'paid'` | `shipped` → `created` → 409 |
| wartości ujemne i graniczne | ilość, kwota, rabat z klienta | walidacja zakresu na serwerze, cena z serwera, nie z formularza | ilość −1, 0, 10⁹; cena zmieniona w żądaniu → odrzucenie lub cena z bazy |
| limit obchodzony równolegle | licznik czytany przed zapisem | atomowy inkrement z warunkiem albo limiter z atomowym licznikiem | N żądań naraz → najwyżej limit udanych |
| zaokrąglenia | wiele małych operacji zaokrąglanych w dół na korzyść klienta | kwoty w groszach (liczby całkowite), zaokrąglenie raz, w jednym miejscu | 1000 operacji po 0,004 → suma zgodna z regułą |

Wyścig potwierdzasz tylko testem równoległym; jedno żądanie w teście go nie pokaże.

## A2. Warstwa HTTP (CDN, proxy, cache)
**Włącz, gdy:** CDN, reverse proxy, load balancer, cache odpowiedzi, kilka serwerów w łańcuchu.

| Problem | Mechanizm | Obrona | Test |
|---|---|---|---|
| request smuggling (CWE-444) | front i backend różnie liczą długość ciała (`Content-Length` vs `Transfer-Encoding`, HTTP/2 → HTTP/1.1) | HTTP/2 do backendu albo normalizacja na froncie, odrzucanie żądań z oboma nagłówkami i niejednoznacznym `Transfer-Encoding`, aktualne proxy | lokalny łańcuch proxy + backend, żądanie z oboma nagłówkami → 400 |
| zatruwanie cache (web cache poisoning) | nagłówek spoza klucza cache (`X-Forwarded-Host`, `X-Original-URL`) zmienia odpowiedź | ignoruj nieoczekiwane nagłówki albo dodaj je do klucza (`Vary`), host z konfiguracji | żądanie z `X-Forwarded-Host: evil.example` → odpowiedź bez tego hosta, cache nie zapisuje |
| oszukiwanie cache (web cache deception) | adres /konto/profil.css trafia do dynamicznej strony, a CDN cache'uje po rozszerzeniu | cache tylko dla ścieżek statycznych z allowlisty, `Cache-Control: no-store, private` na stronach z danymi, ścisły routing (404 dla nieznanych sufiksów) | adres /account/x.css z sesją → `no-store`, brak `HIT` dla innej sesji |
| zatruwanie nagłówkiem Host | link w e-mailu resetu z `Host` żądania | adres bazowy z konfiguracji, allowlista hostów | reset z `Host: evil.example` → link z domeną z konfiguracji |
| rozdzielenie odpowiedzi (CRLF, CWE-113) | wejście w nagłówku odpowiedzi | biblioteki odrzucające `\r\n`, bez sklejania nagłówków | wartość z `%0d%0a` → odrzucenie |

## A3. Parsery i serializacja
**Włącz, gdy:** głębokie łączenie obiektów z JSON, szablony z treścią użytkownika, własne formaty, deserializacja,
wyrażenia regularne na wejściu, porównywanie nazw/e-maili.

| Problem | W kodzie | Obrona | Test |
|---|---|---|---|
| prototype pollution (CWE-1321) | `merge(target, req.body)`, `lodash.set` z kluczem od użytkownika | odrzucaj `__proto__`, `constructor`, `prototype`; `Object.create(null)` lub `Map`; walidacja schematem z `additionalProperties: false` | `{"__proto__": {"isAdmin": true}}` → `({}).isAdmin === undefined` |
| SSTI (CWE-1336) | szablon budowany z wejścia (`render_template_string(user)`, `new Function`, `eval`) | wejście tylko jako dane do szablonu, nigdy jako szablon; sandbox nie jest obroną | `{{7*7}}`, `${7*7}`, `<%= 7*7 %>` → wyświetlone dosłownie |
| deserializacja (CWE-502) | `pickle`, `ObjectInputStream`, `BinaryFormatter`, YAML z tagami typów | tylko formaty danych ze schematem (be-auth-security) | ładunek z gadżetem w teście → odrzucenie przed deserializacją |
| ReDoS (CWE-1333) | wyrażenia z zagnieżdżonymi kwantyfikatorami (`(a+)+`, `(\w+\s?)*$`) na wejściu | silnik liniowy (RE2, `re2`), limit długości wejścia, proste wyrażenia | 50 000 znaków `a` + `!` → odpowiedź < 100 ms |
| normalizacja Unicode | porównanie e-maili/loginów przed normalizacją; `ﬀ`, `İ`, znaki pełnej szerokości | NFKC + case folding przed porównaniem i przed zapisem unikalnym; ta sama normalizacja wszędzie | rejestracja `Admin` i `Ａｄｍｉｎ` → konflikt |
| zanieczyszczenie parametrów (HPP) | `?role=user&role=admin` różnie czytane przez warstwy | jedna biblioteka parsująca, odrzucanie powtórzonych parametrów krytycznych | powtórzony parametr → 400 |

## A4. Przeglądarka
**Włącz, gdy:** CORS z poświadczeniami, `postMessage`, WebSocket, osadzanie w iframe, własna CSP, dane wrażliwe
w odpowiedziach GET.

| Problem | W kodzie | Obrona | Test |
|---|---|---|---|
| CORS z odbiciem `Origin` (CWE-942) | `Access-Control-Allow-Origin: <origin z żądania>` + `Allow-Credentials: true`, dopasowanie `endsWith('example.com')`, `null` dozwolone | dokładna allowlista originów, bez `null`, bez wzorców sufiksowych | `Origin: https://example.com.evil.example` i `null` → brak nagłówków CORS |
| `postMessage` | `addEventListener('message', e => …)` bez sprawdzenia `e.origin`; `postMessage(data, '*')` | sprawdzaj `event.origin` dokładnie, docelowy origin zamiast `*`, dane jako dane, nie HTML | wiadomość z obcego originu → zignorowana |
| WebSocket bez sprawdzenia Origin (CSWSH, CWE-1385) | uwierzytelnianie ciasteczkiem przy handshake | sprawdzaj `Origin` przy handshake albo token w pierwszej wiadomości; autoryzacja per wiadomość | handshake z obcym `Origin` → odrzucony |
| obejścia CSP | `'unsafe-inline'`, allowlista CDN z JSONP lub bibliotekami z gadżetami, brak `base-uri`, `object-src` | strict CSP z nonce i `strict-dynamic`, `base-uri 'none'`, `object-src 'none'` | ładunek z `<base href>` i skryptem z dozwolonego CDN → zablokowany (raport CSP) |
| DOM clobbering | `window.config || {}`, odwołania do globali, które może nadpisać `<form id=config>` | jawne zmienne modułów, sanitizer z ochroną przed clobberingiem | HTML z `id=config` → bez wpływu na logikę |
| clickjacking | brak `frame-ancestors` | `frame-ancestors 'none'` lub lista | strona w iframe z obcej domeny → zablokowana |
| XS-Leaks | odpowiedź zależna od stanu użytkownika, różniąca się czasem, rozmiarem, liczbą ramek | `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy: same-origin`, ciasteczka `SameSite`, `Sec-Fetch-*` po stronie serwera (fetch metadata) | żądanie z `Sec-Fetch-Site: cross-site` do wrażliwego GET → odmowa |

## A5. API
**Włącz, gdy:** automatyczne wiązanie pól, GraphQL, publiczne API, wielu klientów.

| Problem | W kodzie | Obrona | Test |
|---|---|---|---|
| mass assignment (CWE-915) | `User.update(req.body)`, `Object.assign(user, body)`, `@ModelAttribute` bez listy pól | DTO/schemat z allowlistą pól dla każdej operacji (`pick(body, ['name','email'])`) | `{"role":"admin","tenantId":"inny"}` → pola zignorowane albo 400 |
| nadmiarowe dane w odpowiedzi | serializacja całej encji | DTO odpowiedzi | snapshot bez `passwordHash`, `resetToken` |
| GraphQL: introspekcja w produkcji | domyślna konfiguracja | wyłączona albo tylko dla uwierzytelnionych narzędzi | zapytanie `__schema` bez uprawnień → błąd |
| GraphQL: głębokość, koszt, batching, aliasy | brak limitów; aliasy omijają limit prób logowania | limit głębokości, kosztu i liczby operacji/aliasów w żądaniu; autoryzacja w resolverach, nie tylko na bramie | zapytanie z 100 aliasami logowania → odrzucenie |
| brak limitów | kosztowne endpointy, eksport, wyszukiwanie | limity per użytkownik i per IP, paginacja z maksimum (be-api-design) | N+1 żądań ponad limit → 429 |
| BFLA w API | metody admina na tej samej ścieżce (`DELETE /users/{id}`) | autoryzacja per akcja w jednym module | `DELETE` z sesją zwykłego użytkownika → 403 |

## A6. Otoczenie aplikacji
**Włącz, gdy:** własne domeny i subdomeny, zasobniki plików, środowiska podglądowe, usługi wewnętrzne osiągalne
z aplikacji.

| Problem | Mechanizm | Obrona | Test lub kontrola |
|---|---|---|---|
| przejęcie subdomeny | rekord CNAME wskazuje na usuniętą usługę (strona statyczna, aplikacja w chmurze), atakujący ją zakłada | inwentarz DNS, usuwanie rekordów razem z zasobem, okresowe skanowanie wiszących rekordów | lista CNAME → każdy cel istnieje i należy do Was |
| DNS rebinding na usługi lokalne | serwer deweloperski lub panel na `localhost` bez sprawdzenia `Host` | allowlista `Host`, uwierzytelnianie także lokalnie | żądanie z `Host: evil.example` do lokalnej usługi → 403 |
| publiczny zasobnik | ACL „public”, podpisane URL-e z długim czasem życia | blokada dostępu publicznego na poziomie konta, krótkie podpisane URL-e, osobny zasobnik na treści publiczne (sec-cloud-security) | anonimowe listowanie i odczyt → odmowa |
| środowiska podglądowe i debug | `/debug`, `/actuator`, `/_next/` z mapami źródeł, Swagger z prawdziwymi danymi | wyłączone w produkcji albo za uwierzytelnieniem, podglądy bez danych produkcyjnych | skan listy znanych ścieżek na środowisku testowym → 404 |
| ciasteczka na domenę nadrzędną | `Domain=.example.com` → każda subdomena czyta i ustawia | ciasteczka bez `Domain` (tylko host), prefiks `__Host-` | nagłówek `Set-Cookie` sesji ma `__Host-` i brak `Domain` |

## Źródła
- PortSwigger Web Security Academy (portswigger.net/web-security) [niezweryfikowane, dostęp 2026-11-07] — request
  smuggling, web cache poisoning i deception, prototype pollution, SSTI, race conditions, DOM clobbering.
- OWASP API Security Top 10 2023 (owasp.org) [niezweryfikowane] — BOLA, BFLA, mass assignment, limity.
- MITRE CWE (cwe.mitre.org) — identyfikatory klas.
- W3C Fetch Metadata Request Headers, Cross-Origin-Opener-Policy (MDN) [niezweryfikowane] — obrona przed XS-Leaks.

Opisane własnymi słowami.
