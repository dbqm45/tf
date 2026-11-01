# Luka „strojenie − holdout” po poprawkach `slowa` (2026-11-01, Haiku)

Powtórzenie pomiaru `2026-11-01-luka-strojenie-holdout-podsumowanie.md` z tymi samymi ustawieniami po PR z nowymi
scenariuszami strojenia `gen-*` i dopisanymi `slowa` dla 5 skilli (`core-delivery-lifecycle`, `eng-testing`,
`core-agent-security`, `sec-llm-security`, `core-grounding`).

**Ustawienia:**
- polecenie: `--only trigger --per-skill 2 --seed 1 --models haiku --baseline --repeats 2 --isolated`;
- 208 przebiegów, 0 błędów, koszt **20,01 USD**;
- holdout jest identyczny jak w pierwszym pomiarze;
- losowanie strojenia z tym samym ziarnem objęło też część nowych scenariuszy `gen-*` (4 z 24), więc zbiór strojenia
  nie jest identyczny.

## Przed i po

| | Przed | Po |
|---|---|---|
| Strojenie ze skillami / bez | 96% / 46% | 94% / 52% |
| Holdout ze skillami / bez | 80% / 66% | **84%** / 62% |
| Przewaga skilli: strojenie | +50 pp | +42 pp |
| Przewaga skilli: holdout | +14 pp | **+21 pp** |
| Luka strojenie − holdout (ze skillami) | +15 pp | **+10 pp** |
| Holdout: skill nieuruchomiony | 14/56 | 12/56 |
| Holdout: zaliczone, gdy skill uruchomiony | 39/42 (93%) | 40/44 (91%) |

Uruchomienia na holdoucie dla 5 poprawianych skilli (przed → po):

| Skill | Uruchomienie | Holdout ze skillami / bez |
|---|---|---|
| eng-testing | 2/6 → **4/6** | 4/6 → **6/6** / 4/6 |
| sec-llm-security | 2/4 → 2/4 | 2/4 → 3/4 / 2/4 |
| core-grounding | 2/4 → 2/4 | 2/4 → 2/4 / 1/4 |
| core-agent-security | 2/4 → 2/4 | 2/4 → 2/4 / 3/4 |
| core-delivery-lifecycle | 0/4 → 0/4 | 2/4 → 3/4 / 2/4 |

## Wnioski

1. **Kierunek jest dobry:** holdout ze skillami nie spadł (80% → 84%), luka zmalała (+15 → +10 pp), a przewaga na holdoucie
   wzrosła (+14 → +21 pp). Reguła przyjęcia zmiany z `core-skill-authoring` jest spełniona.
2. **Skala zmiany mieści się w szumie:** 56 przebiegów holdoutu, 3–5 niestabilnych scenariuszy na ramię. Różnica
   kilku punktów nie jest przesądzająca. Wyraźna zmiana dotyczy tylko `eng-testing` (uruchomienia 2/6 → 4/6).
3. **`slowa` (hook podpowiedzi) to za słaba dźwignia dla skilli rdzenia.** Trzy z pięciu (`core-agent-security`,
   `sec-llm-security`, `core-grounding`) uruchamiają się na holdoucie tak samo rzadko jak przedtem, a
   `core-delivery-lifecycle` wciąż 0/4. Model wybiera skill przede wszystkim po polu `description`. Hook tylko podpowiada,
   a model może tę podpowiedź pominąć.
4. **Gdy skill się uruchomi, wynik pozostaje wysoki (91%).** Treść skilli działa. Problemem jest decyzja o uruchomieniu.

## Co dalej
- **Opisy (`description`) tych czterech skilli w języku sytuacji użytkownika**, np. „gdy pytasz, czy podana wersja albo
  liczba jest prawdziwa” zamiast „przy każdym twierdzeniu o faktach”. Zmiana opisu trafia do każdej sesji (model widzi
  opisy wszystkich skilli), więc wymaga sprawdzenia, czy nie podkrada pytań sąsiednim skillom (`--hints` i scenariusze
  `no-trigger`).
- `core-delivery-lifecycle`: granica z `core-async-delegation` jest już rozstrzygnięta (decyzja 2026-10-30). Holdout ma
  jeden scenariusz oznaczony jako niejednoznaczny. Przy następnym uzupełnieniu holdoutu warto dodać pytania o fazy
  i bramki z człowiekiem.
- Następny pomiar dopiero po zmianie opisów, z tym samym ziarnem.
