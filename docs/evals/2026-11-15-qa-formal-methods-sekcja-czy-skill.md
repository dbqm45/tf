# Metody formalne: sekcja w istniejącym skillu czy osobny skill (K1) — 2026-11-15

Pytanie człowieka: czy treść o metodach formalnych dać jako sekcję w `qa-spec-first-testing` (wariant A), czy jako
osobny skill `qa-formal-methods` (wariant B). Ta sama treść w obu wariantach (sekcja = procedura skilla B, wspólna
referencja `metody-formalne.md` z uruchomionym przykładem Z3), te same scenariusze `fm-*`, modele haiku i sonnet,
po jednym przebiegu. Workspace `--packs pack-it`; wariant B: jedno strojenie `metadata.slowa` po bramce bez modelu
(podpowiedź 3/4 → 4/4), przed ewaluacją. Koszt: A z przebiegiem bez skilli 2,09 USD, B 1,48 USD (razem 3,57 USD).

## Wynik (scenariusze `trigger`, 4 × 2 modele)

| Wariant | Skill wczytany | Treść zaliczona |
|---|---|---|
| A: sekcja w `qa-spec-first-testing` | 1/8 | 6/8 |
| B: osobny skill `qa-formal-methods` | 8/8 | 8/8 |
| bez skilli fabryki | — | 4/8 |

Scenariusz `no-trigger` (`fm-agregat-niezmiennik`, sąsiad `ddd-tactical-design`): oba warianty bez fałszywego
uruchomienia (haiku i sonnet).

Czego brakuje bez skilla (pominięte grupy sprawdzeń): kontrprzykład jako test `AC-n`, granice modelu w raporcie,
model trzymany obok kodu (rozjazd), solver SMT przy wyborze, co weryfikować. Wiedza ogólna (TLA+, TLC, Z3 przy
regułach rabatowych, dopytanie przy braku opisu) jest w modelu i bez skilla.

## Wniosek
Sekcja przegrywa na wczytywaniu: opis `qa-spec-first-testing` („testy mają sprawdzać wymaganie”) nie prowadzi
modelu do pytań o weryfikację formalną, mimo że hook podpowiadał go 9/9 w bramce bez modelu. Decyzja: osobny skill
(wariant B), a w `qa-spec-first-testing` odnośnik. Wcześniejszy ręczny pomiar (4 pytania, haiku, ocena bez
sprawdzeń) zawyżał wynik bez skilla — nie sprawdzał elementów specyficznych dla fabryki.

Surowe wyniki: `2026-11-15-qa-formal-methods-sekcja-czy-skill.jsonl` (pole `baseline`: przebieg bez skilli;
`skill`: wariant A = `qa-spec-first-testing`, wariant B = `qa-formal-methods`).

## Dopisek: przykłady TLA+ i Alloy (tego samego dnia)
Po dodaniu uruchomionych przykładów TLA+ (TLC) i Alloy oraz ich skrótu w sekcji „Przykład” SKILL.md: ewaluacja
haiku 4/5, sonnet 4/5 (1,33 USD) — `fm-caly-modul-fakturowania` bez testów właściwości jako tańszego szczebla.
Przyczyna: przykład w SKILL.md pokazywał tylko narzędzia formalne, a drabina kosztu była wyłącznie w referencji.
Poprawka: krok 0 procedury (najtańszy szczebel, który wyraża właściwość). Po niej haiku 5/5, sonnet 5/5 (1,66 USD):
`2026-11-15-bramka-qa-formal-methods.md`. Łączny koszt ewaluacji K1: 6,56 USD.
