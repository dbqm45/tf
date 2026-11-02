# Luka „strojenie − holdout” po przepisaniu opisów — Haiku, 12 skilli (2026-11-02)

Trzeci pomiar z serii. Sprawdza, czy nowe pola `description` czterech skilli (`core-agent-security`, `core-grounding`,
`core-delivery-lifecycle`, `sec-llm-security`), przepisane 2026-11-01 na język sytuacji użytkownika, poprawiły
uruchamianie skilli na holdoucie.

- **Ustawienia:** jak w pomiarach 1 i 2 — `--only trigger --per-skill 2 --seed 1 --models haiku --baseline --repeats 2 --isolated`.
  Próbka strojenia jest taka sama jak w pomiarze 2 (pomiar 1 losował przed dopisaniem scenariuszy `gen-*`).
- **Liczby:** 208 przebiegów, 0 błędów, koszt **21,07 USD**.
- **Pliki:** raport z runnera `2026-11-02-luka-po-opisach.md`, surowe wyniki w `.jsonl` obok.
- Zmiana między pomiarem 2 a 3: tylko cztery pola `description`.

## Wynik — trzy pomiary

| | Pomiar 1 (stan wyjściowy) | Pomiar 2 (scenariusze `gen-*`, `slowa`) | Pomiar 3 (nowe opisy) |
|---|---|---|---|
| strojenie ze skillami / bez | 46/48 (96%) / 22/48 (46%) | 45/48 (94%) / 25/48 (52%) | 46/48 (96%) / 25/48 (52%) |
| holdout ze skillami / bez | 45/56 (80%) / 37/56 (66%) | 47/56 (84%) / 35/56 (62%) | 45/56 (80%) / 34/56 (61%) |
| luka strojenie − holdout | +15 pp | +10 pp | +15 pp |
| przewaga skilli na holdoucie | +14 pp | +21 pp | +20 pp |
| holdout: skill nieuruchomiony | 14/56 | 12/56 | **10/56** |
| holdout: zaliczone, gdy uruchomiony | 39/42 (93%) | 40/44 (91%) | 40/46 (87%) |
| holdout: zaliczone, gdy nieuruchomiony | 6/14 | 7/12 | 5/10 |
| koszt | 20,06 USD | 20,01 USD | 21,07 USD |

Uruchomienia na holdoucie w skillach, których dotyczyła zmiana (ze skillami, 2 powtórzenia):

| Skill | Pomiar 1 | Pomiar 2 | Pomiar 3 |
|---|---|---|---|
| core-delivery-lifecycle | 0/4 | 0/4 | 1/4 |
| sec-llm-security | 2/4 | 2/4 | 3/4 |
| core-agent-security | 2/4 | 2/4 | 2/4 |
| core-grounding | 2/4 | 2/4 | 2/4 |
| eng-testing (bez zmiany opisu) | 2/6 | 4/6 | 4/6 |

## Wnioski

1. **Nowe opisy poprawiły uruchamianie nieznacznie:** nieuruchomionych przebiegów na holdoucie jest 10/56 wobec 12/56.
   Zysk to po jednym przebiegu w `core-delivery-lifecycle` i `sec-llm-security`. `core-agent-security` i `core-grounding`
   bez zmian (2/4) — sam opis nie wystarcza, żeby model sięgnął po te skille na nowych sformułowaniach.
2. **Wynik na holdoucie się nie poprawił** (80% wobec 84% w pomiarze 2). Różnica dwóch przebiegów z 56 mieści się
   w rozrzucie (3–4 niestabilne scenariusze na ramię), więc nie traktujemy jej jako pogorszenia ani poprawy.
   Przewaga skilli na holdoucie trzyma się na poziomie +20 pp (+14 pp w pomiarze 1).
3. **Wg reguły przyjmowania zmian** (poprawia strojenie i nie pogarsza holdoutu) zmiana jest neutralna: strojenie
   94→96% (jeden przebieg), holdout w granicy rozrzutu. Opisy zostają — są czytelniejsze, a nie szkodzą.
4. **Luka nie jest już tylko problemem uruchamiania.** Gdy skill się uruchomi, holdout przechodzi w 87% (93% w pomiarze 1).
   Spadek wynika głównie z `sec-llm-security` (3 przebiegi), `ddd-tactical-design` (2) i `dom-ev-tariffs-pricing` (1), które się uruchamiały,
   ale nie spełniły wszystkich kryteriów. Przy 4 przebiegach na skill to może być rozrzut; treści holdoutu nie
   analizujemy pod kątem poprawek (reguła holdoutu).

## Co dalej

- **Dalsze strojenie opisów pod Haiku przestaje się opłacać:** trzy pomiary po ok. 20 USD przesunęły uruchamianie z 42 na 46
  przebiegów z 56. Kolejny krok to nowe pytania holdout (świeży zbiór, bo obecny był oglądany w trzech pomiarach
  przez wyniki zbiorcze) i pomiar na Sonnecie, który mógłby pokazać, czy problem uruchamiania dotyczy głównie Haiku.
- `core-agent-security` i `core-grounding` — sprawdzić bez modelu, czy konkurencyjne skille (np. `core-git-workflow`,
  `core-async-delegation`) mają opisy zbyt bliskie; ewentualne poprawki wyłącznie na nowych scenariuszach strojenia.
