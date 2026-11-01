# Luka „strojenie − holdout” — Haiku, 12 skilli (2026-11-01)

Wariant B pomiaru „wynik czy koszt” (pozycje w `docs/todo.md`: „Skille fabryki: wynik czy tylko koszt”, „Fabryka sama
tuninguje na egzaminie”).

- **Zbiory:**
  - **holdout:** wszystkie 28 scenariuszy (24 z pomiaru 2026-10-30 i 4 dopisane na reguły specyficzne dla fabryki);
  - **strojenie:** po 2 losowe scenariusze trigger na skill (`--per-skill 2 --seed 1`), razem 24.
- **Ramiona:** ze skillami i bez, po 2 powtórzenia, tylko Haiku, tryb `--isolated`.
- **Liczby:** 208 przebiegów, 0 błędów, koszt **20,06 USD**.
- **Polecenie:** `run_skill_evals.py --skills <12 skilli> --only trigger --per-skill 2 --seed 1 --models haiku --baseline --repeats 2 --isolated`.
- **Pliki:** raport z runnera `2026-11-01-luka-strojenie-holdout.md`, surowe wyniki w `.jsonl` obok.

## Wynik

| Zbiór | Ze skillami | Bez skilli | Przewaga skilli |
|---|---|---|---|
| strojenie | 46/48 (96%) | 22/48 (46%) | **+50 pp** |
| holdout | 45/56 (80%) | 37/56 (66%) | **+14 pp** |
| luka (strojenie − holdout) | **+15 pp** | | |

Skąd luka — uruchomienie skilla ze skillami:

| Zbiór | Skill uruchomiony: zaliczone | Skill nieuruchomiony: zaliczone |
|---|---|---|
| holdout | 39/42 (93%) | 6/14 (43%) |
| strojenie | 45/46 (98%) | 1/2 |

Według skilla (holdout ze skillami / bez, strojenie ze skillami / bez; uruchomienia na holdoucie):

| Skill | H+ | H− | S+ | S− | Uruchomienie (H) |
|---|---|---|---|---|---|
| core-async-delegation | 4/4 | 0/4 | 4/4 | 1/4 | 4/4 |
| dom-ev-tariffs-pricing | 4/4 | 2/4 | 4/4 | 0/4 | 4/4 |
| ai-evals | 6/6 | 4/6 | 4/4 | 2/4 | 6/6 |
| be-database | 4/4 | 3/4 | 4/4 | 1/4 | 4/4 |
| ddd-tactical-design | 3/4 | 2/4 | 4/4 | 2/4 | 4/4 |
| core-grounding | 2/4 | 1/4 | 3/4 | 1/4 | 2/4 |
| be-api-design | 6/6 | 6/6 | 4/4 | 2/4 | 6/6 |
| dom-ev-ocpp-16 | 6/6 | 6/6 | 4/4 | 4/4 | 6/6 |
| core-delivery-lifecycle | 2/4 | 2/4 | 3/4 | 2/4 | **0/4** |
| sec-llm-security | 2/4 | 2/4 | 4/4 | 2/4 | 2/4 |
| eng-testing | 4/6 | 5/6 | 4/4 | 1/4 | **2/6** |
| core-agent-security | 2/4 | 4/4 | 4/4 | 4/4 | 2/4 |

## Wnioski

1. **Skille nadal wnoszą wynik na holdoucie (+14 pp),** ale mniej niż 2026-10-30, kiedy na Haiku było +35 pp.
   Ze skillami wynik jest podobny (80% wobec 85%). Wzrosło ramię bez skilli (66% wobec 50%): częściowo przez 4 nowe
   scenariusze, częściowo przez rozrzut (5 niestabilnych scenariuszy bez skilli). Przy 28 scenariuszach i 2 powtórzeniach
   różnica 14–35 pp mieści się w niepewności. Obu liczb nie traktujemy jak dokładnej wartości.
2. **Luka +15 pp to głównie problem uruchamiania, nie treści.**
   - Gdy skill się uruchomi, holdout przechodzi w 93%, prawie jak strojenie (98%).
   - Gdy się nie uruchomi, wynik spada do poziomu ramienia bez skilli (43%).
   - Na holdoucie skill nie uruchomił się w 14 z 56 przebiegów, na strojeniu w 2 z 48.
   - Opisy i `slowa` skilli dopasowały się więc do sformułowań scenariuszy strojenia. To dokładnie ten sygnał uczenia
     się egzaminu, który miał wykazać pomiar.
3. **Przewaga na strojeniu (+50 pp) jest zawyżona** także przez kryteria: scenariusze strojenia pisano na podstawie
   treści skilli, więc ramię bez skilli rzadziej trafia w ich sformułowania (46% wobec 66% na holdoucie).
4. **Skille do przeglądu (bez strojenia pod pytania holdout):**
   - `core-delivery-lifecycle`: 0/4 uruchomień, znany niejednoznaczny scenariusz;
   - `eng-testing`: 2/6 uruchomień;
   - `core-agent-security` i `sec-llm-security`: po 2/4;
   - `core-grounding`: 2/4.

   Przy `core-agent-security` ramię bez skilli wypadło lepiej (4/4 wobec 2/4) — gdy skill się nie uruchamia, odpowiedź
   ze skillami nic nie zyskuje.

## Co dalej (zgodnie z regułą holdoutu)

- **Nie poprawiamy opisów pod pytania holdout.**
- **Generalizację uruchamiania** poprawiamy na nowych scenariuszach strojenia, napisanych innymi słowami niż istniejące
  (inny autor albo agent bez dostępu do treści skilla). Następnie powtarzamy ten pomiar z tym samym ziarnem i sprawdzamy,
  czy luka maleje, a holdout nie spada.
- **Holdout uzupełniamy nowymi pytaniami** (zwłaszcza dla skilli z 2 scenariuszami), a starych nie poprawiamy.
- **Pomiar powtarzamy na Sonnecie** dopiero przy następnej większej zmianie opisów (koszt podobny, około 20 USD).
