# F4 (część A): ewaluacja skilla eng-project-reconstruction — 2026-10-24 (Haiku)

Decyzja człowieka (2026-10-24): tylko część A — ewaluacja skilla na Haiku z porównaniem bez skilli. Benchmark vs
maister (część B) nie został uruchomiony; repozytoria dobierze Claude, gdy człowiek zdecyduje o B.

Runner: `.claude/tests/run_skill_evals.py --skills eng-project-reconstruction --models haiku --baseline --isolated
--budget-usd 4`, przestrzeń `.work/pack-it`, Claude Code 2.1.310. Koszt według `total_cost_usd`: **1,48 USD**
(16 przebiegów; prognoza runnera 2,24 USD).

## Wyniki
| Scenariusz | Rodzaj | Ze skillem | Bez skilli: treść |
|---|---|---|---|
| odswiezenie-po-zmianach | trigger | ✓ (Skill) | ✓ |
| duze-stare-repo-raport | trigger | ✓ (Skill) | ✗ (sędzia) |
| standardy-z-kodu | trigger | ✓ (Skill) | ✗ (sędzia) |
| wymagania-z-testow | trigger | ✓ (Skill) | ✓ |
| raport-do-udostepnienia | trigger | ✓ (Skill) | ✓ (sędzia) |
| wejscie-dla-automatu-historyjek | trigger | ✓ (Skill) | ✗ (2 braki, sędzia) |
| dossier-przed-refaktorem | no-trigger | ✓ (nie wczytany) | — |
| wplyw-zmiany-pliku | no-trigger | ✓ (nie wczytany) | — |
| dlug-techniczny-priorytety | no-trigger | ✓ (nie wczytany) | — |
| pelny-audyt-bezpieczenstwo | no-trigger | ✓ (nie wczytany) | — |

- Ze skillem: 10/10 — skill wczytany we wszystkich 6 scenariuszach „trigger” i w żadnym z 4 scenariuszy sąsiadów.
- Bez skilli: treść spełnia sprawdzenia w 3/6 scenariuszy. Skill wnosi wiedzę o dużych starych repozytoriach,
  standardach z kodu i wejściu dla automatu historyjek.
- Średni koszt przebiegu: ze skillem 0,102 USD, bez skilli 0,077 USD (sędzia wliczony).

## Dalej
- Część B (benchmark vs maister na 3 repozytoriach, szacunek 30–45 USD) — tylko po decyzji człowieka.
