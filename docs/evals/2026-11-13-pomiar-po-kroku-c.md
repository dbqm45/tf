# Pomiar po kroku C: Talos z zadaniem i dowodami

Data: 2026-11-13. Powtórka pomiaru z `2026-11-13-pomiar-bazowy-e0.md` po scaleniu kroku C (tf#226–#230). Ten sam
zestaw: 3 historyjki × 5 powtórzeń, `claude -p "/talos-story-run … --auto --budget 3" --model sonnet`, świeża kopia
repozytorium testowego na każdy przebieg. Fabryka: `1a8742c` (wersja 9.27.0) z poprawką hooka dziennika z tego
samego PR. Surowe wyniki: `2026-11-13-pomiar-po-kroku-c.jsonl`; poprzedni pomiar:
`2026-11-13-pomiar-po-poprawkach-talosa.jsonl`. Za zgodą człowieka; koszt 7,44 USD i 0,50 USD przebiegu próbnego.

## Wynik

| Historyjka | Koszt śr. (było → jest) | Czas śr. | Akceptacja | Dowody | Commit zadania |
|---|---|---|---|---|---|
| S1 limit dobowy (1 kawałek) | 0,45 → 0,51 USD | 69 → 82 s | 5/5 | 5/5 przebiegów, K1 zweryfikowany | 5/5 |
| S2 abonament (2 kawałki) | 0,59 → 0,68 USD | 112 → 126 s | 5/5 | 5/5 przebiegów, K1 i K2 zweryfikowane | 5/5 |
| S3 niejasna (oczekiwany STOP) | 0,26 → 0,30 USD | 26 → 36 s | STOP 5/5, kod bez zmian | nie dotyczy | 4/5 na gałęzi historyjki, 1/5 na `main` |

- Łącznie 7,44 USD wobec 6,47 USD poprzednio (+15%). Odmów uprawnień: 0 (poprzednio 1).
- Każdy kawałek w S1 i S2 ma dowód w `evidence/`, jest odhaczony w planie i ma stan „zweryfikowany” po zakończeniu
  przebiegu. Drzewo robocze po każdym przebiegu jest czyste, `./verify.sh` zielony 15/15.
- Zadanie doszło do etapu `pr` w 9 z 10 przebiegów S1 i S2; w jednym (S1, powtórzenie 4) zostało na etapie `plan`,
  bo Talos pominął polecenia `stage`. Kod, dowód i commit były poprawne.

## Co znalazł pomiar

1. **Nieśledzony `docs/project/README.md` po przebiegu** (przebieg próbny). Hook dziennika projektu przebudowywał
   indeks po zapisie planu zadania, więc kolejny przebieg zatrzymałby się na warunku czystego drzewa. Poprawione
   w tym samym PR (pliki zadania bez nagłówka artefaktu nie należą do dziennika); w 15 przebiegach nie wystąpiło.
2. **Commit plików zadania na gałęzi domyślnej** (S3, powtórzenie 3). Po STOP przed planem Talos raz zapisał
   `docs(task): record …` na `main` zamiast na gałęzi historyjki. W skillu dopisane jedno zdanie; skuteczność
   tej poprawki nie była mierzona.
3. **Etap zadania zależy od poleceń `stage`** (S1, powtórzenie 4). Gdy Talos ich nie wywoła, `task.json` pokazuje
   wcześniejszy etap. Bez poprawki — do rozważenia przy pozycji 9 planu (pętla w sesji głównej).

## Ograniczenia

- Pięć powtórzeń na historyjkę i jedno małe repozytorium w Pythonie: różnice kosztu rzędu 10–15% mieszczą się
  w rozrzucie między przebiegami, którego tu nie szacowano.
- Repozytorium testowe nie ma zdalnego źródła, więc push i otwarcie PR nie są sprawdzane.
- Przebieg cięcia pdi (`--task`) nie był mierzony; zostaje w starym układzie.
