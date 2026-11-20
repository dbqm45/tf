# Pomiar trybu fabryki (krok T6)

Data: 2026-11-20. Krok T6 planu `docs/plans/2026-11-20-tryb-fabryki-plan.md`: czy pętla `/tf` działa w układzie
wtyczki tak samo jak przed zmianą.

**Jak mierzone:**
- historyjki S1–S4 po 5 przebiegów;
- `claude -p "/tf … --auto --budget 3" --model sonnet` z `--plugin-dir .tf/plugin --settings
  .tf/plugin/session-settings.json` (`E0_LAYOUT=plugin`);
- świeża kopia repozytorium testowego i instalacja z nakładką pack-it na każdy przebieg;
- fabryka `5cc8616` (plik wersji 20.9.0, gałąź PR tf#369, uruchomiona z osobnej kopii roboczej).

Porównanie: `2026-11-15-pomiar-po-kroku-h.md` (układ domyślny, fabryka 10.21.0). Surowe wyniki:
`2026-11-20-pomiar-tryb-fabryki.jsonl`.

Za zgodą właściciela z 2026-11-20. Koszt:
- seria: 9,67 USD;
- przerwany pierwszy przebieg: 0,42 USD (niżej);
- sprawdzanie flag i próby na żywo przy T1–T5: około 0,09 USD.

Razem około 10,2 USD [suma `cost_usd` serii i przebiegu przerwanego; próby na żywo z wyjścia `claude -p`]. Żaden
przebieg nie zakończył się błędem.

**Przerwany start.** Pierwszy przebieg zatrzymał się na skanie bezpieczeństwa, bo w nowym kontenerze nie było
`semgrep`. Pętla traktuje brak skanera jako FAIL, zgodnie z regułą. Po zgodzie właściciela `semgrep` 1.186.0
zainstalowano przez `python3 -m pip install semgrep`, a serię uruchomiono od nowa. Przy pomiarze po kroku H skaner
był w kontenerze [założenie: tamten kontener już nie istnieje, więc nie da się tego sprawdzić].

## Wynik

| Historyjka | Koszt śr. (po H → teraz) | Tury śr. (po H → teraz) | Czas śr. (po H → teraz) | Akceptacja |
|---|---|---|---|---|
| S1 limit dobowy | 0,63 → 0,53 USD | 15,2 → 16,2 | 113 → 94 s | 5/5 |
| S2 abonament | 0,80 → 0,69 USD | 18,2 → 24,8 | 154 → 138 s | 5/5 |
| S3 niejasna (oczekiwany STOP) | 0,29 → 0,24 USD | 15,0 → 11,2 | 37 → 30 s | STOP z pytaniem 5/5 |
| S4 paragon i zgubiony bilet | 0,65 → 0,47 USD | 12,6 → 11,2 | 125 → 86 s | 5/5 część jasna; kwota zgadnięta 0/5 |

- **Jakość:**
  - akceptacja 15/15, jak po kroku H;
  - `./verify.sh` zielony 20/20;
  - S3 kończy się pytaniem 5/5;
  - w S4 żadnej kwoty nie zgadnięto.
- **Koszt** spadł z 11,84 do 9,67 USD (−18%). Spadek jest większy niż rozrzut między powtórzeniami. Między pomiarami
  zmieniła się jednak nie tylko lokalizacja fabryki: wersja 10.21 → 20.9 przepisała skille i dodała weryfikację
  powiązanych testów. Spadku nie da się więc przypisać samemu trybowi fabryki [wniosek, bez osobnego pomiaru].
- **Hooki fabryki działają w sesji z wtyczką.** W przebiegach są ich ślady w `.tf/logs/`: `tdd-red.jsonl`,
  `quality-gate.json`, `skill-hints.jsonl` i `usage.jsonl`. Reguły z `RULES.md` dochodzą przez hook `SessionStart`.
- **Przegląd zakresu** zapisany w 14 z 15 przebiegów z kawałkami (po kroku H: 15/15).
- **Odmowy uprawnień:** 4 we wszystkich przebiegach (po H: 2). Wszystkie dotyczą poleceń spoza listy dozwolonych:
  `python3 -m unittest` i `python3 -m parking.cli`.

## Odchyłka: S4-r1

Pętla przyjęła zadanie, ale pominęła swoje kroki:
- zrobiła część jasną (AC1) jednym commitem;
- nie napisała specyfikacji, nie zrobiła przeglądu zakresu ani śladu kryteriów;
- zatrzymała się poprawnie na otwartym pytaniu o kwotę i niczego nie zgadła.

W tym przebiegu dwa uruchomienia `python3 -m unittest` zostały odrzucone. W pomiarze po kroku H żaden przebieg nie
pominął kroków pętli. Przyczyny nie ustaliłem [niezweryfikowane]: przebieg nie zapisuje wywołań narzędzi, a jeden
przypadek na 20 to za mało, żeby przypisać go trybowi fabryki.

## Wnioski

- Tryb fabryki działa w pętli: wtyczka się ładuje, a hooki, reguły i skille są w sesji. Jakość jest taka jak przed
  zmianą, więc tf#369 (tryb fabryki domyślnie) scalono po tym pomiarze.
- Do obserwacji przy kolejnym pomiarze:
  - czy pomijanie kroków pętli (S4-r1) się powtarza;
  - odmowy `python3 -m unittest` — pętla powinna uruchamiać testy przez `test_lock.py`.
