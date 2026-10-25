# F4: tańsze odświeżanie rekonstrukcji — komentarze, czas i powtórzenia — 2026-10-25

Decyzja człowieka (2026-10-25): sprawdzić odświeżanie po zmianie samych komentarzy (punkt 1), skrócić czas
odświeżania (punkt 2), potem powtórzyć test zmiany w logice po 2 przebiegi na repozytorium (punkt 3). Zmiana, która
pogarsza jakość, nie wchodzi. Dane: `docs/evals/2026-10-24-f4b/odswiezenie-komentarze/` i
`docs/evals/2026-10-24-f4b/odswiezenie-logika/v5/`–`v10/`. Narzędzia: `refresh_comments.sh`, `refresh_logic.sh`
(z numerem przebiegu) i `refcheck.py` w `docs/evals/2026-10-24-f4b/narzedzia/`.

## Zmiany w skillach
| Wersja | Zmiana |
|---|---|
| v5 | `recon_refresh.py prep` bierze poprzednią wersję zmienionego pliku z gita (commit manifestu albo HEAD, sprawdzoną hashem z manifestu). Z niej: zmiany tylko w komentarzach i pustych liniach nie dostają zleceń; numery linii dowodów w kartach i dokumentach są przeliczane (raz na manifest); zlecenie zawiera diff pliku. Bez zleceń `prep` sam uruchamia `finish`. `finish` wpisuje datę i commit odświeżenia pod nagłówkiem raportu. |
| v6 | `finish` wypisuje pełną treść linii do sprawdzenia i oznacza linie składane z kart. Dwa nowe sygnały: dowód w zmienionej linii kodu i opis podobny do zmienionej reguły. `apply` zamienia wskazane linie i od razu uruchamia `finish`. `card` to kontrola jednej karty dla wykonawcy: sama poprawia przesunięte numery linii, a złe dowody wypisuje z treścią linii kodu. |
| v7 | `apply` czyta poprawki z `raw/refresh/fixes.md`, bo Claude Code przy liście dozwolonych poleceń blokuje heredoc w Bash. |
| v8 | Zlecenie i `card` przypominają o opisie modułu (`purpose`), który `finish` przenosi do raportu. |
| v9 | Usuniętą regułę zastępuje się zdaniem o stanie obecnym („… nie jest już sprawdzane”), zamiast ją kasować. |
| v10 | Przy opisie podobnym do zmienionej reguły `finish` podaje nową treść reguły; niepełne streszczenie (np. sama dolna granica) się uzupełnia. |

## Punkt 1: zmiana tylko w komentarzach
Warunki: bazy jak w teście logiki (nasz v6, maister v1), pliki śledzone przywrócone do commitu bazowego. Dwa warianty:
- **na końcu pliku:** komentarz dopisany na końcu co 20. pliku z kodem, jak w v1 (eShopOnWeb 12 plików,
  spring-petclinic 2);
- **w środku pliku:** dwie linie komentarza przed pierwszą deklaracją typu, co przesuwa numery linii. Ten wariant
  tylko dla naszego skilla.

| | Nasz skill (v5) | maister |
|---|---|---|
| Koszt, na końcu pliku (eShopOnWeb + petclinic) | **0,24 USD** (0,12 + 0,12) | 0,48 USD (0,23 + 0,25) |
| Czas | **25 s** (13 + 12) | 57 s (23 + 34) |
| Tury | 4 + 4 | 6 + 8 |
| Koszt, w środku pliku | 0,24 USD (0,12 + 0,12) | — |
| Zmiany w dokumentacji | linia z datą odświeżenia, manifest; w środku pliku też numery linii | daty w stopkach (eShopOnWeb); w petclinic dopisana uwaga o stronicowaniu |
| Dowody do zmienionych plików po przesunięciu linii | 31/31 i 9/9 wskazują tę samą treść (`refcheck.py`) | brak dowodów z numerem linii |

- Nasz skill nie uruchamia wykonawców: `prep` rozpoznaje zmiany tylko w komentarzach, przelicza numery linii
  i od razu kończy kontrolą i manifestem.
- W v1 (stara wersja) ten test kosztował u nas 0,25 USD i 62 s na samym eShopOnWeb, a u maistera 0,22 USD i 31 s.
- Skrypt mutacji zapisał jeden plik (`Index.cshtml.cs`) z LF zamiast CRLF. Nasz skill słusznie uznał to za zmianę
  bez znaczenia; maister to zauważył i opisał.

## Punkt 3: zmiana w logice, 2 przebiegi na repozytorium
Warunki jak w `2026-10-24-f4-odswiezenie-logika.md`. Jedna różnica: kopia każdego przebiegu ma pliki śledzone
przywrócone do commitu bazowego. W v1–v4 kopia maistera zawierała jeszcze 12 plików ze zmianą komentarzy z testu
v1 i dlatego kosztowała więcej (0,66 USD). Maistera zmierzono raz, w 4 przebiegach (v5); jego dokumenty z tych
przebiegów porównywano z każdą wersją naszego skilla. Ocena ślepa jak wcześniej (Sonnet, A/B losowane osobno dla
każdej pary).

| Wersja | Koszt seria 1 / seria 2 | Średnio (2 repo) | % maistera | Czas średnio | Ocena zmian (12): tak / częściowo | Miejsca nieaktualne |
|---|---|---|---|---|---|---|
| maister | 0,52 / 0,49 USD | 0,51 USD | 100% | 74 s | 12 / 0 (w każdej ocenie) | 0 |
| v5 | 0,48 / 0,54 USD | 0,51 USD | 101% | 195 s | 12 / 0 | 2 (słabe: streszczenia bez górnej granicy 99) |
| v6 | 0,39 / 0,51 USD | 0,45 USD | 90% | 241 s | nie oceniano | — |
| v7 | 0,43 / 0,35 USD | 0,39 USD | 77% | 185 s | 12 / 0 | 3 (2 z jednego opisu modułu, 1 graniczne w słowniczku) |
| v8 | 0,37 / 0,28 USD | 0,32 USD | 64% | 167 s | 11 / 1 | 0 |
| v9 | 0,39 / 0,36 USD | 0,38 USD | 75% | 199 s | 12 / 0 | 1 (słabe: to samo streszczenie bez górnej granicy 99) |
| v10 | 0,36 / 0,40 USD | **0,38 USD** | **74%** | 192 s | **12 / 0** | **0** |

- **Koszt:** wersja końcowa (v10) kosztuje średnio 74% kosztu maistera. W 4 przebiegach rozrzut wynosi 0,36–0,40 USD
  za dwa repozytoria, u maistera 0,49–0,52 USD; v9 dała podobny wynik (0,36–0,39 USD).
  - Spadek wobec v5 to mniej tur głównego modelu: nie czyta miejsc do poprawy osobno i nie pisze skryptów poprawek.
  - Wykonawcy kosztują mniej, bo dostają diff i sprawdzają kartę jednym poleceniem.
  - v8 było tańsze od v9 i v10, bo model kasował linie o usuniętej regule zamiast je przepisać. Oceniający uznał
    to za niepełne (P3 „częściowo”), dlatego od v9 model zapisuje stan obecny, co kosztuje kilka centów.
- **Jakość:**
  - w wersji końcowej (v10) oba narzędzia mają 12/12 „tak” i 0 miejsc nieaktualnych; we wcześniejszych wersjach
    wszystkie zmiany były opisane („tak”) z wyjątkiem jednej w v8;
  - oceniający wielokrotnie wskazywali, że nasz opis jest dokładniejszy (domena a widok, limit argumentu a suma,
    wyjątek i mapowanie 409, które zostały w kodzie);
  - maister opisuje zmiany w jednym lub dwóch miejscach (`architecture.md`, `roadmap.md`), więc ma mniej miejsc, które
    mogą się zestarzeć; u nas pozostałości wynikały z kart (opis modułu, słowniczek) i streszczeń, co poprawiły v6,
    v8 i v10;
  - kontrola końcowa przechodzi w każdym przebiegu, a manifest jest zgodny z kodem.
- **Czas (punkt 2):** nasz skill skrócił odświeżanie z 280 s (v4) do ok. 170–200 s na dwa repozytoria (v7–v10). Maister
  nadal jest szybszy (74 s). U nas większość czasu zajmują wykonawcy na kartach (35–70 s na repozytorium),
  których maister nie ma. Przy zmianie samych komentarzy jesteśmy szybsi (25 s wobec 57 s).

## Wnioski
1. Przy zmianie samych komentarzy nasz skill jest dwa razy tańszy i dwa razy szybszy od maistera, a numery linii
   dowodów pozostają trafne.
2. Przy zmianie w logice nasz skill jest o ok. 26% tańszy przy tym samym wyniku ocen (12/12, 0 pozostałości)
   i dokładniejszym opisie. Wolniejszy jest o ok. 2,5 raza.
3. Pozostałości starego opisu u nas pochodziły z bogatszej dokumentacji (karty, słowniczek, streszczenia). Lista
   `finish` wskazuje je teraz z nową treścią reguły, ale decyzję podejmuje model, więc pojedyncze miejsca mogą się
   jeszcze trafić (w v5–v9: 0–3 na 4 przebiegi).

## Ograniczenia
- Dwa repozytoria, po 2 przebiegi każdej wersji (v5–v10) i 4 przebiegi maistera; jeden oceniający na parę.
- Przebiegi maistera pochodzą z v5, a oceniający porównywali je z każdą wersją naszego skilla. Maister się nie
  zmieniał, ale każda ocena to nowe losowanie A/B i inny oceniający.
- Wersje v6–v10 zmieniały się po wynikach poprzednich ocen, więc v10 jest dopasowana do tych dwóch repozytoriów
  i trzech rodzajów zmian [założenie: zmiany są ogólne, ale nie sprawdzono ich na innym repozytorium].
