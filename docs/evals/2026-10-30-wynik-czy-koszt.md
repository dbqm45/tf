# Wynik czy koszt — zamknięty zbiór, Haiku i Sonnet (2026-10-30)

Pomiar zgodny z protokołem z `tests/skill_evals/README.md`:
- 24 scenariusze holdout dla 12 skilli (rdzeń, pack-it, pack-ev);
- ramiona ze skillami i bez, każde w 2 powtórzeniach na Haiku i na Sonnecie;
- `run_skill_evals.py --holdout only --baseline --repeats 2 --isolated`;
- 192 przebiegi, 0 błędów, koszt 19,59 USD (pilotaż Haiku 5,19 USD + reszta 14,40 USD).

Szczegóły: `2026-10-30-wynik-czy-koszt-holdout.md`, surowe wyniki w `.jsonl` obok.

## Wynik

| Model | Ramię | Pełna odpowiedź (wszystkie kryteria) | Średnia kryteriów | Koszt na rozwiązane | Niestabilne |
|---|---|---|---|---|---|
| Haiku | ze skillami | **41/48 (85%)** | 94% | 0,160 USD | 3 |
| Haiku | bez skilli | 24/48 (50%) | 80% | 0,150 USD | 2 |
| Sonnet | ze skillami | **43/48 (90%)** | 96% | 0,152 USD | 3 |
| Sonnet | bez skilli | 28/48 (58%) | 84% | 0,102 USD | 8 |

Pełne odpowiedzi według skilla (Haiku ze skillami / bez, Sonnet ze skillami / bez, każde na 4):

| Skill | H+ | H− | S+ | S− |
|---|---|---|---|---|
| core-async-delegation | 4 | 0 | 4 | 1 |
| dom-ev-tariffs-pricing | 4 | 0 | 4 | 0 |
| sec-llm-security | 4 | 1 | 4 | 2 |
| core-delivery-lifecycle | 2 | 0 | 3 | 1 |
| ddd-tactical-design | 3 | 2 | 4 | 3 |
| be-database | 4 | 4 | 4 | 2 |
| core-agent-security | 3 | 2 | 3 | 3 |
| eng-testing | 4 | 3 | 4 | 3 |
| dom-ev-ocpp-16 | 4 | 4 | 4 | 3 |
| ai-evals | 4 | 4 | 4 | 4 |
| be-api-design | 4 | 4 | 4 | 4 |
| core-grounding | 1 | 0 | 1 | 2 |

## Wnioski

1. **Skille wnoszą wynik, nie tylko koszt.** Pełnych odpowiedzi przybywa o 35 punktów procentowych na Haiku
   i o 32 na Sonnecie. Przewaga prawie nie maleje na mocniejszym modelu. Według reguły z TODO („jeśli przewaga
   maleje z mocą modelu, inwestować w hooki i ewaluacje”) treść skilli nadal jest warta inwestycji.
2. **Haiku ze skillami (85%) jest lepszy niż Sonnet bez skilli (58%)** przy podobnym koszcie na rozwiązane zadanie
   (0,160 wobec 0,102 USD). Wspiera to obecną kaskadę modeli w `core-cost-control`.
3. **Wartość jest skupiona w procedurach specyficznych dla fabryki lub dziedziny.** To przede wszystkim praca bez
   nadzoru, taryfy OCPI, bezpieczeństwo LLM i fazy dostarczania. W ogólnej inżynierii (ewaluacje, API HTTP, testy,
   OCPP 1.6) model zna odpowiedź sam. Te skille warto odchudzić testem „no-op” (pozycja w TODO), a nie rozbudowywać.
4. **Słabe miejsca:**
   - `core-grounding`: 1/4 ze skillem na obu modelach, a Sonnet bez skilla ma 2/4; skill rzadko się uruchamia;
   - `core-delivery-lifecycle`: 2–3/4.

   Zgodnie z regułą holdoutu nie stroimy opisów pod te pytania. Przyczyny trzeba szukać na scenariuszach strojenia
   i w treści skilla.
5. **Skille zmniejszają rozrzut.** Sonnet bez skilli ma 8 scenariuszy z różnym wynikiem między powtórzeniami,
   ze skillami 3.

## Ograniczenia

- 24 scenariusze, po 2 powtórzenia — mała próba.
- Kryteria sprawdzane wyrażeniami regularnymi, a w razie braku trafienia sędzią modelowym.
- Scenariusze napisali agenci na podstawie treści skilli. Kryteria mogą więc faworyzować sformułowania ze skilli:
  odpowiedź poprawna, ale ujęta inaczej, może nie przejść w ramieniu bez skilli. Część przewagi może z tego wynikać.
- Nie zmierzono jeszcze, o ile zawyżony jest wynik na scenariuszach strojenia (wariant B).
