# Cena dla kierowcy — ad hoc, kontrakt, dynamika, przepisy

## 1. Dwie ścieżki ceny
| | Ad hoc | Kontrakt |
|---|---|---|
| Umowa | brak; kierowca płaci kartą, kodem lub aplikacją CPO | umowa z eMSP |
| Rozliczenie | CPO z kierowcą (przez operatora płatności) | eMSP z kierowcą; CPO z eMSP po CDR |
| OCPI | taryfa `AD_HOC_PAYMENT` opisuje cenę; CDR do eMSP nie powstaje | taryfy `REGULAR`/`PROFILE_*` i CDR |
| Dowód zakupu | CPO | eMSP |

Terminal płatniczy i preautoryzacja karty: dom-ev-payments. Ten skill
dostarcza cenę sesji z taryfy; w 2.3.0 pole `preauthorize_amount` w Tariff podpowiada, ile zablokować na karcie.
Granice ról: dom-ev-market-roles; przebieg sesji z kartą: dom-ev-session-lifecycle.

## 2. Cena CPO a cena eMSP
- Taryfa OCPI to cena **CPO**. Kontrakt kierowcy z eMSP może dodawać marżę, abonament lub opłaty własne; różnicę ustala umowa
  CPO↔eMSP i eMSP↔kierowca, a nie OCPI.
- Dlatego `tariff_alt_text` obok `elements` nie powinien powtarzać cen: eMSP musi móc dołożyć swoje opłaty.
- Zasady niewyrażalne w modelu (np. rabat dla grupy użytkowników) opisz tekstem i rozlicz osobno.

## 3. Ceny dynamiczne
Co OCPI daje (2.2.1-d2/2.3.0, `mod_tariffs`):
- Nową wersję taryfy wysyłasz PUT (po stronie eMSP) albo jako kolejną taryfę z `start_date_time`/`end_date_time`; stara i nowa
  mogą być przypisane do konektora jednocześnie, więc zamiana następuje sama.
- Cena zależna od rynku energii nie ma dedykowanych pól. Przykład w spec: `PROFILE_CHEAP` z `tariff_alt_url` do strony z
  bieżącymi cenami; `elements` opisują cenę zapowiedzianą, a faktyczny koszt może być inny.
- Zmiana ceny w trakcie trwającej sesji: OCPI nie zabrania, ale w wielu krajach prawo konsumenckie tak. Zasada
  ostrożna: taryfa z chwili startu obowiązuje do końca sesji.

Do ustalenia z prawem i partnerem (nie wynika ze spec): jak często cena może się zmieniać, jak długo musi być stabilna po
pokazaniu kierowcy, jak zapisać cenę zmienną w CDR (okresy z różnymi `tariff_id`).

## 4. Co pokazać kierowcy przed startem
Minimalny zestaw, który wynika z modelu taryfy (praktyka, nie przepis):
- stawki wszystkich wymiarów aktywnych na starcie (kWh, godzina ładowania, godzina postoju, opłata stała),
- od kiedy zaczyna się naliczanie postoju i czy po czasie darmowym,
- krok `step_size`, jeśli większy niż 1, oraz `min_price` / `max_price`,
- czy kwoty są brutto i jaka waluta; w USA czy dojdą podatki (`tax_included`),
- zmiany ceny w trakcie dnia (okna godzinowe, progi mocy) i kwota blokowana na karcie (ad hoc).

Wymogi przejrzystości cen, sposób ich udostępniania (ekran, aplikacja, dane otwarte) i terminy — przepisy (AFIR)
**[do weryfikacji]**: sprawdź aktualny tekst i krajowe wdrożenie przez `researcher`, zanim wpiszesz je jako wymagania.
Import z 2024–2025 (`.claude/skills/dom-ev-charging/references/ocpi.md`, §7) łączy AFIR z transparentnością taryf i płatnością
ad hoc; to nie jest sprawdzone źródło.

## 5. USA i Kanada (2.3.0)
- Podatek zależy od jurysdykcji i zwykle nie jest znany CPO przy tworzeniu taryfy, więc `vat` zostaje puste.
- `tax_included`: `YES` (ceny zawierają podatek), `NO` (podatek dojdzie), `N/A` (brak podatku). Pole jest wymagane w
  Tariff 2.3.0.
- `min_price`/`max_price` jako `PriceLimit`: `before_taxes` (wymagane) i `after_taxes` (opcjonalne); oba warunki obowiązują.
- Kto i jak wylicza podatek po stronie CDR — dom-ev-cdr-settlement oraz przepisy lokalne [do weryfikacji].

## 6. Waluta
Taryfa i CDR niosą jedną walutę (ISO 4217, `currency`). Kwoty w polu `Price` mają `excl_vat` i `incl_vat`. Przeliczanie walut
nie jest częścią modułu Tariffs [założenie — nie znalazłem w sprawdzonych plikach]. Nie mieszaj walut w jednej sesji; kurs i
moment przeliczenia ustalają strony poza OCPI.

## 7. Źródła
`mod_tariffs.asciidoc` (d2 i 2.3.0, sprawdzone 2026-10-20), `230/changelog.asciidoc`; `.claude/skills/dom-ev-charging/references/ocpi.md`
(import). Wszystko o przepisach: [do weryfikacji].
