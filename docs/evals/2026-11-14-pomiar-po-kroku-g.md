# Pomiar po kroku G: Jira, opis PR ze skryptu, karta wdrożenia, zamknięcie zadania i historyjka z otwartym pytaniem

Data: 2026-11-14. Powtórka pomiaru z `2026-11-14-pomiar-po-kroku-f.md` po kroku G (tf#252–#255) i nowa historyjka S4,
która sprawdza, co pętla robi, gdy jedna część zadania jest jasna, a druga ma otwarte pytanie. Ten sam układ:
`claude -p "/tf … --auto --budget 3" --model sonnet`, świeża kopia repozytorium testowego na każdy przebieg,
instalacja z nakładką pack-it, **przełącznik `loop.blocked_slices` włączony** w każdym przebiegu. Fabryka: `3efffbf`
(plik wersji 10.11.0), uruchomiona z osobnej kopii roboczej. Surowe wyniki: `2026-11-14-pomiar-po-kroku-g.jsonl`.

Za zgodą właściciela z 2026-11-14. Koszt: 12,03 USD za 20 przebiegów serii, 0,63 USD za przebieg próbny S4
i 0,004 USD za sprawdzenie dostępu — razem 12,67 USD (sumy `cost_usd`). Żaden przebieg nie zakończył się błędem.

## Wynik

| Historyjka | Koszt śr. (po F → teraz), rozrzut | Czas śr. (po F → teraz) | Akceptacja | Specyfikacja i ślad |
|---|---|---|---|---|
| S1 limit dobowy (1 kawałek) | 0,61 → 0,64 USD (0,57–0,72) | 114 → 113 s | 5/5 | 5/5: 3 kryteria, każde z testem i zapisem czerwonego testu |
| S2 abonament (2 kawałki) | 0,87 → 0,84 USD (0,79–0,92) | 166 → 165 s | 5/5 | 5/5: 4 kryteria, każde z testem i zapisem czerwonego testu |
| S3 niejasna (oczekiwany STOP) | 0,32 → 0,29 USD (0,28–0,31) | 42 → 34 s | STOP 5/5 z kodem `pytanie` | `spec.md` nie powstaje (5/5) |
| S4 paragon i zgubiony bilet (nowa) | — → 0,64 USD (0,61–0,65) | — → 119 s | 5/5 część jasna; kwota zgadnięta 0/5 | 5/5: pytanie w „Poza zakresem” i „Otwarte pytania” |

- S1–S3 razem: 8,85 USD wobec 9,00 USD po kroku F, 8,93 USD po E3 i 8,12 USD po E1. Różnice średnich S1–S3 między
  serią po F a tą (±0,03 USD) mieszczą się w rozrzucie między powtórzeniami tej samej historyjki (0,03–0,15 USD) —
  to szum, nie zmiana.
- Drzewo robocze czyste i `./verify.sh` zielony 20/20. Zadanie doszło do etapu `pr` w 15/15 przebiegów S1, S2 i S4.
- Repozytorium testowe nie ma zdalnego źródła, więc przebiegi kończą się zatrzymaniem przed otwarciem PR (kod
  `srodowisko`, `uprawnienia` albo — w S4 — `pytanie`).
- W trakcie serii robiłem na maszynie lekkie prace (pojedyncze testy, edycje). Czasy są orientacyjne.

## Co widać z kroku G

- **Opis PR ze skryptu (G2):** `run_state.py pr-body` wywołany w 12 z 15 przebiegów, które doszły do etapu `pr`.
  W pozostałych trzech (S1-r1 i dwa S4 zakończone pytaniem) pętla zatrzymała się, zanim złożyła opis.
- **Zapis ważnego ustalenia (G4):** w S2-r5 przegląd zakresu znalazł ustalenie `[ważne]` (zmieniony komunikat użycia
  wbrew specyfikacji). Pętla zapisała je poleceniem `run_state.py finding`, wycofała zmianę i zrobiła drugą rundę.
  Komunikat po zapisie każe od razu podać kontrolę, więc pętla próbowała ją zapisać sama: najpierw złym poleceniem,
  potem przez `tf`, którego w środowisku nie ma uprawnień. Kontrola ma powstać przy zamknięciu zadania — do poprawy.
- **Jira (G1), karta wdrożenia (G3), zamknięcie (G4):** nie były mierzone. Repozytorium testowe nie ma Jiry
  ani wdrożenia, a przebieg kończy się przed scaleniem.

## Historyjka z otwartym pytaniem (S4) i kawałek zablokowany (F3)

We wszystkich 5 przebiegach pętla zrobiła jasną część, a o resztę zapytała:
- kryterium bez kwoty trafiło do sekcji „Poza zakresem” i „Otwarte pytania” specyfikacji z dopiskiem, że nie blokuje
  części jasnej;
- plan miał jeden kawałek (paragon);
- `lost_ticket_fee()` nie powstała (0/5 zgadniętych kwot);
- pytanie jest w raporcie końcowym i w sprawach odłożonych.

**Mechanizm kawałka zablokowanego nie był potrzebny** (`block`: 0 wywołań, `events.jsonl`: 0 plików). Pytanie widać
już w treści zgłoszenia, więc specyfikacja wyłącza tę część, zanim powstanie plan. F3 dotyczy pytań, które wychodzą
dopiero w trakcie kawałka. Tego ten zestaw nadal nie sprawdza, a przełącznik zostaje domyślnie wyłączony.

## Co wyszło do sprawdzenia

1. **Wynik przeglądu zakresu zapisany tylko w 7 z 15 przebiegów z kawałkami.** `scope-reviewer` był wywołany
   w 15/15, ale polecenie `run_state.py step … zakres` pętla pominęła w 8 przebiegach. W 2 z nich (S2-r5, S4-r2) nie
   zapisała żadnego kroku kawałka. Bez tego zapisu nie działają limit rund ani odmowa „`zakres fail` bez
   ustalenia”, a podgląd pokazuje przegląd jako nieuruchomiony. Po kroku F było podobnie (3/5 S2 bez zapisu).
   Instrukcja w treści skilla nie wystarcza — potrzebny mechanizm: `tick` nie odhacza kawałka bez zapisanego wyniku
   przeglądu.
2. **Rozpoznanie wejścia pominięte w 6 z 20 przebiegów** (`intake.py resolve`; po F 3/15, po E3 0/15). Przebiegi
   mimo to skończyły się poprawnie, bo `run_report.py start` zakłada zadanie i bez tego.
3. **Odmowy uprawnień: 5 w 4 przebiegach** (po F: 0 w 15):
   - `git push` bez sprawdzenia, czy jest zdalne repozytorium (2 przebiegi);
   - polecenie złożone z `&&`;
   - `tf task finding … control` (patrz wyżej);
   - raz zapis zatrzymania `run_state.py stage … --reason "…git push…"`, choć to polecenie ma regułę zgody.
   Przyczyny ostatniej odmowy nie ustaliłem [niezweryfikowane]. Przy drugiej próbie zapis przeszedł.
4. **Trzy przebiegi S2 miały 32–40 tur zamiast 16–18**: odmowy uprawnień (r2), dodatkowe kroki (r4) i druga runda
   po ustaleniu przeglądu (r5). Koszt mimo to w rozrzucie (0,79–0,92 USD).

## Wniosek

- Krok G nie pogorszył wyniku: akceptacja 15/15 (S1, S2, S4), STOP 5/5, koszt S1–S3 bez zmiany poza szumem.
- Nowa historyjka S4 pokazuje zachowanie, o które chodziło w F3, choć innym mechanizmem: jasna część zrobiona,
  bez zgadywania, z pytaniem do człowieka.
- Do poprawy, w tej kolejności: zapis wyniku przeglądu zakresu (mechanizm w `tick`), komunikat po zapisie
  ustalenia (kontrola przy zamknięciu, nie od razu), próba `git push` bez zdalnego repozytorium.

## Ograniczenia

- Pięć powtórzeń na historyjkę i jedno małe repozytorium w Pythonie.
- Liczby wywołań policzone z transkryptów (wywołania narzędzia Bash i Agent), orientacyjnie.
- Jira, wdrożenie, zamknięcie zadania, tryby zwykły i Plan, waga lekka i pełna oraz cięcia pdi nie były mierzone —
  pokrywają je testy skryptów.
- Pytania, które wychodzą dopiero w trakcie kawałka (F3), nadal niezmierzone.
