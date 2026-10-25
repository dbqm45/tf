# F4: test odświeżenia po zmianie w logice — eng-project-reconstruction wobec maistera — 2026-10-24

Decyzja człowieka (2026-10-24): powtórzyć test odświeżenia ze zmianą w logice. W v1 zmiana dotyczyła tylko
komentarzy i nie rozróżniła narzędzi. Dane: `docs/evals/2026-10-24-f4b/odswiezenie-logika/`. Skrypty
`mutate_logic.py` i `refresh_logic.sh` są w `docs/evals/2026-10-24-f4b/narzedzia/`.

## Warunki
- **Punkt wyjścia:**
  - nasz skill: raporty v6 (bieżąca wersja skilla, z manifestem do odświeżania przyrostowego);
  - maister: dokumenty z v1.
  - Oba odświeżały kopię, więc dane bazowe benchmarku zostały nietknięte.
- **Zmiany w kodzie:** te same dla obu narzędzi, po trzy w repozytorium:
  - zmieniona reguła;
  - nowa reguła;
  - usunięta reguła, która sprawdza, czy narzędzie usuwa nieaktualny opis.

  | Repo | Zmieniona | Nowa | Usunięta |
  |---|---|---|---|
  | eShopOnWeb | ilość w koszyku 0..int.Max → 0..99 | cena pozycji katalogu 0,01..10000 | odrzucanie duplikatu nazwy (409) przy tworzeniu pozycji |
  | spring-petclinic | telefon `\d{10}` → `\d{9}` | imię zwierzaka bez cyfr | odrzucanie daty wizyty, która nie jest po dzisiejszej |

- **Polecenia** jak w v1:
  - nasz skill: „odśwież przyrostowo według sekcji Odświeżanie przyrostowe”;
  - maister: `/maister:init` z wyborem „Update existing documentation”;
  - oba w trybie wsadowym, Sonnet, limit 4 USD.
- **Ocena ślepa (Sonnet):** dla każdej zmiany
  - czy dokumentacja podaje stan po zmianie (tak / częściowo / nie);
  - lista miejsc, które nadal twierdzą stan sprzed zmiany.

## Wyniki
| | Nasz skill | maister |
|---|---|---|
| Stan po zmianie podany (z 6) | **6 / 6** | 5,5 / 6 (P3 częściowo) |
| Miejsca nieaktualne | 2 | **0** |
| Zmienione pliki dokumentacji | 7–8 na repo: karty modułów, reguły, wymagania, raport, manifest | 3 na repo: architecture, roadmap, INDEX |
| Koszt (2 repo) | 1,02 USD (0,45 + 0,57) | **0,66 USD** (0,39 + 0,27) |
| Czas (2 repo) | 269 s | **111 s** |

- **Nieaktualne miejsca u nas:**
  - eShopOnWeb `requirements.md:25`: „Duplikat nazwy przy tworzeniu → 409” z dowodem w niezmienionym
    `ExceptionMiddleware.cs`;
  - petclinic `modules/owner.md:96`: niewiadoma „brak testów dla formatu telefonu (10 cyfr)” przepisana ze starej
    karty.
  - W obu przypadkach to tekst opisowy, a nie dowód do zmienionej linii, więc `recon_check` ich nie wyłapuje.
- **Sposób opisu zmian:**
  - nasz skill wprowadza zmiany w miejscach, gdzie dana reguła jest opisana: karta modułu, `rules.md`,
    `requirements.md`, raport, z dowodem `plik:linia`;
  - maister w petclinic opisał zmiany głównie w `roadmap.md`, czyli jak dziennik zmian, a nie w opisie reguł. Stąd
    0 nieaktualnych miejsc, ale też mniej treści do sprawdzenia.

## Wnioski
1. **Oba narzędzia wychwytują zmiany w logice.** Nasz skill opisuje je pełniej i w miejscach, gdzie dana reguła
   występuje; maister jest tańszy i szybszy.
2. **Nasza słabość:** więcej miejsc do aktualizacji, więc łatwiej o pozostałości. Odświeżanie przyrostowe
   przepisuje karty zmienionych partii, ale tekst syntezy (`requirements.md`) i niewiadome w kartach mogą zachować
   stary opis.
3. **Możliwa poprawka** (do decyzji, nie wdrożona): przy odświeżaniu porównać stare i nowe karty zmienionych partii
   (reguły usunięte i zmienione) i przeszukać całą dokumentację po ich treści. Dziś ani `recon_check`, ani prosty grep
   po usuniętych identyfikatorach z kodu tych dwóch miejsc by nie złapały.
4. **Ograniczenia:** jeden przebieg na repo, dwa repozytoria, jeden oceniający na repo (Sonnet). Oceniający nie
   czytali kodu, tylko porównali dokumenty z opisem zmian.

## Powtórka po poprawce `--prev` (2026-10-25)
Po PR #71 (`recon_cards.py --prev`: porównanie starych i nowych kart, lista miejsc do przejrzenia) test powtórzono dla
naszego skilla na tych samych zmianach i bazie v6, z bieżącą wersją skilli. Dokumenty maistera zostały te same.
Ocena ślepa i prompt jak wyżej, nowe losowanie A/B. Dane: `odswiezenie-logika/v2/`.

| | Nasz v1 | Nasz v2 (z `--prev`) | maister |
|---|---|---|---|
| Stan po zmianie podany (z 6) | 6 | **6** | 6 (w tej ocenie) |
| Miejsca nieaktualne | 2 | **0 prawdziwych**, 2 graniczne | 0 |
| Koszt (2 repo) | 1,02 USD | 1,13 USD (0,53 + 0,60) | 0,66 USD |
| Czas (2 repo) | 269 s | 418 s | 111 s |

- **Obie pozostałości z v1 zniknęły:**
  - `requirements.md` opisuje teraz usunięcie kontroli duplikatu;
  - niewiadoma w karcie owner mówi o telefonie 9-cyfrowym i o testach z 10 cyframi jako rozjeździe.
- **Model użył nowego kroku:** w obu przebiegach powstało `raw/cards-prev/`.
- **Dwa wpisy graniczne** (eShopOnWeb, D1):
  - zakres `[Range(0, int.MaxValue)]` w widoku Web jest zgodny z kodem, a dokumentacja sama wyjaśnia rozjazd
    z domeną;
  - „ilość nie może być ujemna” w dwóch miejscach jest niepełne (brak górnej granicy 99), ale nie fałszywe.
- **Wniosek:** z `--prev` nasz skill dorównuje maisterowi w braku pozostałości i opisuje zmiany szerzej, w miejscach,
  gdzie reguły występują. Maister pozostaje tańszy i szybszy przy odświeżaniu (ok. 58% naszego kosztu).


## Powtórka 2: odświeżanie skryptem `recon_refresh.py` (2026-10-25)
Decyzja człowieka (2026-10-25): odświeżanie ma być tańsze niż w maisterze (0,66 USD za dwa repozytoria) przy
zachowanej jakości. Zmiany w skillach:
- **`recon_refresh.py prep`** porównuje manifest z kodem, kopiuje karty do `raw/cards-prev/` i pisze po jednym
  zleceniu na kartę, której dotyczą zmienione pliki (karta cytuje plik albo obejmuje jego ścieżkę). Wykonawca (Haiku)
  poprawia starą kartę tylko na podstawie zmienionych plików, zamiast skanować partię od nowa.
- **`recon_refresh.py finish`** wykonuje kroki bez modelu:
  - składa karty, `rules.md` i sekcję Moduły;
  - wypisuje zmienione reguły kart (stara → nowa) i listę miejsc ze starym opisem;
  - poprawia numery linii dowodów przesuniętych przez zmianę kodu;
  - uruchamia kontrolę końcową i zapisuje manifest, gdy kontrola przechodzi.
- **Model główny** robi tylko trzy rzeczy: uruchamia oba kroki, zleca karty i poprawia opisy wskazane przez `finish`.

Bazy, zmiany w kodzie, polecenie i ocena ślepa jak wyżej, nowe losowanie A/B. Wersja v3 to pierwsza wersja skryptu
(bez oceny jakości, tylko koszt). Wersja v4 dodaje dwie rzeczy: wykrywanie reguły zmienionej przy tym samym cytacie
i poprawianie przesuniętych dowodów. Dane: `odswiezenie-logika/v3/` (przebiegi) i `odswiezenie-logika/v4/`
(przebiegi, klucz, werdykty).

| | Nasz v2 | Nasz v3 | Nasz v4 | maister |
|---|---|---|---|---|
| Stan po zmianie podany (z 6) | 6 | nie oceniano | **6** | 6 |
| Miejsca nieaktualne | 0 (2 graniczne) | nie oceniano | **0** (wpisy graniczne jak w v2) | 0 |
| Koszt (2 repo) | 1,13 USD | 0,62 USD (0,31 + 0,30) | **0,56 USD** (0,32 + 0,24) | 0,66 USD (0,39 + 0,27) |
| W tym Sonnet / Haiku | ok. 1,0 / 0,1 | 0,54 / 0,08 | 0,48 / 0,08 | 0,66 / — |
| Tury modelu głównego | 25 / 22 | 19 / 25 | 21 / 24 | 40 / 13 |
| Czas (2 repo) | 418 s | 279 s | 280 s | 111 s |

- **Koszt:** v4 kosztuje 85% kosztu maistera.
  - Spadek wobec v2 to głównie mniej pracy modelu głównego: nie czyta całych kart ani raportu, a kroki mechaniczne
    robi skrypt.
  - Liczba tur modelu głównego prawie się nie zmieniła.
- **Jakość:**
  - oceniający przyznał „tak” wszystkim 6 zmianom u obu narzędzi; listy nieaktualnych miejsc są puste;
  - w eShopOnWeb oceniający dopisał przy naszym skillu pole „graniczne”: streszczenia z samą dolną granicą ilości
    oraz zakres `[Range(0, int.MaxValue)]` w widoku, zgodny z kodem i objaśniony w `rules.md`;
  - u maistera P3 zaliczono mimo braku wzmianki o domyślnej dacie „jutro”, a zmiany są opisane tylko w `roadmap.md`;
  - oceniający wskazali, że nasz opis jest dokładniejszy, na przykład:
    - rozdziela regułę domeny od walidacji widoku;
    - zauważa, że wyjątek duplikatu i mapowanie 409 zostały w kodzie, ale nic ich już nie zgłasza.
- **Czas:** maister jest nadal szybszy (111 s wobec 280 s), bo nie uruchamia wykonawców ani kontroli końcowej.
- **Ograniczenia:**
  - jeden przebieg na repo, a rozrzut kosztu między przebiegami to kilka centów na repo (v3 i v4 petclinic: 0,30 i
    0,24 USD);
  - po pierwszym `finish` model nadal robi kilka tur poprawek. Gdyby potrzebny był większy zapas, to miejsce można
    jeszcze skrócić.
