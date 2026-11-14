# Tryby pracy i zatrzymania w pętli /tf

Czytasz, gdy człowiek podał `--plan` albo `--auto`, gdy skrypt odmawia wejścia w pętlę kawałka („zgoda człowieka na
plan”, „tryb Plan”) albo gdy kończysz blokiem STOP i musisz dobrać kod.

## Tryby
Tryb wybiera człowiek w poleceniu; Ty go tylko zapisujesz przy pierwszym `run_state.py stage <katalog> intake`
(`--plan` albo `--auto`; bez opcji — tryb zwykły). Sam trybu nie zmieniasz, żeby ominąć zgodę.

| Tryb | Polecenie człowieka | Co robisz po planie |
|---|---|---|
| Plan | `/tf <zadanie> --plan` | kończysz: `run_state.py stage <katalog> needs --needs plan`, pokazujesz specyfikację i plan, potem `run_report.py finish` i commit plików zadania. Kodu nie ruszasz. |
| zwykły | `/tf <zadanie>` | `run_state.py stage <katalog> needs --needs plan`, pokazujesz specyfikację i plan i czekasz. Po zgodzie człowieka: `run_state.py approve <katalog>` — dopiero wtedy `step` wpuści pętlę kawałka. Jedna zgoda obejmuje plan i specyfikację. |
| Auto | `/tf <zadanie> --auto` | idziesz dalej bez zgody; plan i założenia trafiają do opisu PR. Przy wadze pełnej tryb Auto nie działa — zostaje zwykły (`references/waga.md`). |

- **Wznowienie po trybie Plan:** człowiek pisze `/tf <KLUCZ>`; zmieniasz tryb na ten z polecenia
  (`run_state.py mode <katalog> zwykly` albo `auto`) i idziesz od zgody na plan.
- `run_state.py approve` zapisuje zgodę z identyfikatorem człowieka z gita. Wywołujesz je tylko po wyraźnej zgodzie
  człowieka w rozmowie („tak”, „akceptuję plan”); w trybie Auto skrypt odmawia, bo nie ma kogo zapytać.
- Zmiana planu albo specyfikacji po zgodzie wymaga nowej zgody; odhaczanie kawałków jej nie unieważnia.
- Podgląd trybu: `run_state.py mode <katalog>`.

## Kody zatrzymań
Blok STOP zapisujesz zawsze z kodem z tej listy:
`run_state.py stage <katalog> needs --needs stop --code <kod> --reason "<powód z dowodem>"`. Kod spoza listy albo
brak kodu to błąd polecenia. Wybierasz kod, który mówi, **czego potrzeba od człowieka**:

| Kod | Kiedy | Czego potrzeba od człowieka |
|---|---|---|
| `pytanie` | brakuje kryteriów akceptacji albo odpowiedzi na pytanie `[blokuje]` | odpowiedzi na pytania (do 3, konkretne) |
| `podzial` | więcej niż 5 kawałków albo kilka akcji w jednej historyjce (STORY-001) | wyboru podziału z Twojej propozycji |
| `zrodlo` | nie ma treści zadania albo dostępu do zgłoszenia | wklejenia treści albo połączenia z trackerem |
| `zgoda-na-plan` | waga pełna w przebiegu z `--auto`; plan czeka na zgodę | zgody na plan albo uwag |
| `testy` | weryfikacja czerwona po dwóch próbach naprawy | decyzji: inna droga, zmiana kryterium albo przerwanie |
| `skan` | skan bezpieczeństwa blokuje po dwóch próbach | decyzji o ustaleniu skanu (poprawka, wyjątek z uzasadnieniem) |
| `budzet` | koszt powyżej `--budget` | zgody na dalszy koszt albo zakończenia |
| `srodowisko` | niezacommitowane zmiany, brak zdalnego repozytorium, brak skanera albo narzędzia | przygotowania repozytorium lub narzędzia |
| `zaleznosc` | nowa zależność, karencja wersji (pakiet młodszy niż 7 dni), brak ustawień karencji | decyzji o zależności albo dodania ustawienia |
| `kontrakt` | zmiana publicznego API, schematu danych, migracja albo decyzja biznesowa, której nie ma w zadaniu | decyzji; wariantu zachowawczego nie wybierasz sam |
| `uprawnienia` | operacja zastrzeżona dla człowieka: produkcja, publikacja, flaga poza środowiskiem testowym, scalenie PR | wykonania operacji albo wyraźnej zgody |

„To za trudne” nie jest kodem: zatrzymujesz się na dowodzie (polecenie i wynik), nie na własnej ocenie trudności.
