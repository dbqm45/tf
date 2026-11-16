# Typowe błędy kryptograficzne i jak je wychwycić

Spis treści: tryby i nonce · losowość · JWT · hasła · porównania i inne · jak testować

## Tryby i nonce
- **ECB** ujawnia powtórzenia bloków; nie używaj go do niczego. Wykrycie: `AES/ECB`, `Cipher.getInstance("AES")`
  (domyślnie ECB w Javie), `MODE_ECB`.
- **CBC bez MAC** pozwala modyfikować szyfrogram i tworzy oracle dopełnienia. Zamiast tego AEAD.
- **Powtórzony nonce w GCM lub ChaCha20-Poly1305** z tym samym kluczem łamie poufność i integralność. Stały IV,
  licznik zerowany po restarcie i losowy 96-bitowy nonce przy ogromnej liczbie wiadomości na klucz są ryzykiem.
  Środek zaradczy: nonce z licznika zapisywanego trwale, rotacja klucza po limicie, albo konstrukcja odporna na
  powtórzenie (AES-GCM-SIV, XChaCha20-Poly1305).
- Szyfrowanie bez uwierzytelnienia kontekstu: użyj AAD (id rekordu, tenant), by szyfrogram nie dał się przenieść.

## Losowość
- Tokeny, klucze, nonce, sole i identyfikatory resetu z CSPRNG, ≥ 128 bitów entropii. `Math.random`, `rand`,
  `Random`, czas jako ziarno — to błąd. Własny generator „z kilku źródeł” również.

## JWT i podpisy
- **alg confusion:** serwer wybiera algorytm z nagłówka tokenu (`alg: none` albo HS256 z kluczem publicznym RSA
  jako sekretem). Zasada: algorytm i klucz ustala konfiguracja po stronie serwera, weryfikacja z allowlistą
  algorytmów, klucz wybierany po `kid` ze zaufanego JWKS. Walidacja `iss`, `aud`, `exp` — `be-auth-security`.
- Podpis bez weryfikacji łańcucha zaufania (kopiowanie klucza z tokenu, `jku` z dowolnego adresu) to brak podpisu.

## Hasła i klucze
- Szybkie hashe (SHA-256, MD5) do haseł; sól globalna zamiast losowej per hasło.
- Klucz zaszyty w kodzie, w obrazie kontenera lub w aplikacji mobilnej; ten sam klucz w środowiskach test i produkcja.
- Brak rotacji i brak nagłówka wersji, więc zmiana algorytmu wymaga migracji „big bang”.

## Porównania i inne
- Porównanie MAC/tokenów zwykłym `==` (kanał czasowy) zamiast funkcji stałoczasowej biblioteki.
- Szyfrogram deterministyczny do wyszukiwania pól (wyciek równości) zamiast indeksu HMAC.
- Komunikaty błędów odszyfrowania zdradzające powód (padding vs MAC).
- Wyłączona walidacja TLS „na chwilę” w kodzie, który trafił na produkcję.

## Jak testować
Testy jednostkowe z wektorami testowymi biblioteki, test, że ten sam tekst jawny daje różne szyfrogramy, test
odrzucenia zmodyfikowanego szyfrogramu i tokenu z innym `alg`, analiza statyczna reguł kryptograficznych
(Semgrep lub odpowiednik) w CI (ops-ci-cd). Testy wyłącznie na własnych systemach.
