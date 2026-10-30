# Ewaluacje skilli

Po co: sprawdzić na prawdziwym modelu, czy skill **uruchamia się wtedy, kiedy powinien**, czy **nie uruchamia się,
gdy pytanie należy do sąsiedniego skilla**, i czy odpowiedź zawiera **wiedzę, którą daje skill**, a nie tylko wiedzę
ogólną modelu. Tak zaleca Anthropic w „Agent Skills — best practices”: co najmniej trzy ewaluacje na skill,
sprawdzenie na Haiku, Sonnecie i Opusie oraz porównanie z przebiegiem bez skilla.

Jeden plik `<skill>.json` na skill:

```json
{
  "skill": "be-api-design",
  "scenarios": [
    {
      "id": "idempotencja-post",
      "expect": "trigger",
      "prompt": "Projektuję POST /orders. Jak obsłużyć ponowienia, żeby nie powstały dwa zamówienia?",
      "files": {"src/orders.controller.ts": "export class OrdersController {}"},
      "checks": {
        "all": [["idempotency-key", "klucz idempotencji"], ["409|422|konflikt"]],
        "none": ["PUT zamiast POST"]
      }
    },
    {
      "id": "schemat-bazy",
      "expect": "no-trigger",
      "prompt": "Jakie indeksy dodać do tabeli orders w PostgreSQL?",
      "neighbor": "be-database"
    }
  ]
}
```

- `expect`: `trigger` (skill powinien się uruchomić) albo `no-trigger` (pytanie należy do innego skilla, podanego
  w `neighbor`). Skill z `disable-model-invocation: true` ma wyłącznie scenariusze `no-trigger`.
- `accept` (opcjonalnie): lista skilli, których wczytanie też zalicza uruchomienie — tylko tam, gdzie obszary celowo
  się pokrywają (np. connascence w `ddd-tactical-design` i `ddd-connascence-analysis`). Nie używaj go, żeby ukryć
  niejasną granicę.
- `files` (opcjonalnie): pliki tworzone w katalogu roboczym przed przebiegiem. Potrzebne skillom z `paths`
  (np. `lang-typescript`), które uruchamiają się przy pasujących plikach. W `prompt` wskaż plik z nazwy.
- `checks.all`: lista grup; każda grupa to lista alternatyw (wyrażenia regularne, wielkość liter bez znaczenia).
  Odpowiedź przechodzi, gdy w każdej grupie pasuje co najmniej jedna alternatywa. Grupy sprawdzają wiedzę
  specyficzną dla skilla (konkretna reguła, liczba, nazwa wzorca), a nie słowa, które padną w każdej odpowiedzi.
- `checks.none`: wyrażenia, których w odpowiedzi być nie powinno (np. znany błąd albo przestarzała rada).

Uruchomienie (koszt: każdy przebieg to jedno wywołanie `claude -p`; runner pokazuje liczbę przebiegów, pyta
o potwierdzenie i zatrzymuje się po przekroczeniu budżetu):

```bash
python3 tests/run_skill_evals.py --skills be-api-design --models haiku            # jeden skill, tanio
python3 tests/run_skill_evals.py --skills "be-*,qa-*" --models haiku,sonnet,opus  # grupa skilli, trzy modele
python3 tests/run_skill_evals.py --skills be-api-design --baseline                # porównanie z przebiegiem bez skilli
python3 tests/run_skill_evals.py --all --models sonnet --budget-usd 20
python3 tests/run_skill_evals.py --all --models haiku --resume docs/evals/<plik>.jsonl --out docs/evals/<plik>.md   # dokończ przerwany
```

Gdy Claude Code zgłosi limit użycia lub częstości zapytań, runner nie startuje kolejnych przebiegów i podpowiada
`--resume`. Wznowienie pomija zrobione scenariusze, powtarza przerwane limitem i przelicza raport z całości.
Wyniki przebiegów i rekomendacje trzymamy w `docs/evals/`.

Raport trafia do `evals-report-<data>.md` (tabela skill × model: uruchomienia, fałszywe uruchomienia, sprawdzenia
treści, koszt) oraz surowe wyniki do `.jsonl` obok. Przebiegi idą w trybie `plan` (bez zmian w plikach) w katalogu
tymczasowym z kopią `.claude/skills`.

Wyniki czytaj jako sygnał, nie wyrok: model może odpowiedzieć dobrze bez skilla (wtedy skill jest zbędny albo
opis za słaby), a sprawdzenia oparte na słowach mogą przepuścić lub odrzucić odpowiedź nietypowo sformułowaną.
Wątpliwe przypadki oceń, czytając odpowiedź w `.jsonl`.

## Zamknięty zbiór testowy i protokół „wynik czy koszt”

Opisy, słowa i treść skilli stroimy na scenariuszach z plików głównych, więc wynik na nich jest zawyżony. Do pomiaru,
czy skille coś wnoszą, służy osobny **zamknięty zbiór** w `skill_evals/holdout/<skill>.json`:
- ten sam format, ale tylko scenariusze `trigger` ze sprawdzeniami (granice pilnuje plik główny);
- bramka (`skill_gate.py`), podpowiedzi i `--suggest` go nie czytają, a odcisk bramki skilla go nie obejmuje;
- jego porażek nie naprawiamy zmianą opisu pod te pytania. Zbiór uzupełniamy nowymi pytaniami, a nie poprawiamy
  starych.

```bash
python3 tests/run_skill_evals.py --all --holdout only --models haiku,sonnet --baseline --repeats 2   # pomiar
python3 tests/run_skill_evals.py --skills be-api-design --holdout exclude                          # strojenie
```

Raport ma sekcję „Protokół: wynik czy koszt”. Dla każdego ramienia (model × ze skillami / bez × zbiór) pokazuje:
- **zaliczone w całości** — główny wynik: skill uruchomiony i wszystkie kryteria spełnione;
- **średnią kryteriów** — tylko diagnostyka; 8 z 10 kryteriów to nie 80% wartości;
- **koszt** i **koszt na rozwiązane zadanie** — wszystkie przebiegi ramienia, także nieudane, przez liczbę
  zaliczonych;
- **niestabilne** — scenariusze z różnym wynikiem między powtórzeniami (`--repeats`).

