# Widoczność skilli dom-ev-* obok pack-it — 2026-11-15

Pytanie: jak zmieścić listę skilli projektu pack-it + EV w budżecie `limits.skill_listing_max_chars: 14000`
(`build.py`: `skill_listing()`, liczone jak w projekcie przez `skill_profile.py`). Przed zmianą: pack-it + pack-ev
≈19828 znaków (36 wpisów `dom-ev-*` = 6372, 156–195 znaków na wpis), `--packs all` ≈20132.

## Decyzja człowieka
- Mechanizm: widoczność **warunkowa w danych nakładki** — `skill_visibility.name_only_when` w `pack.yaml`
  (`with`, `prefixes`, `except`), składana w `packs.compose` i stosowana przez `skill_profile.py` i `skill_listing()`.
  Sama nakładka EV mieści się w budżecie, więc tam wszystkie `dom-ev-*` zostają z opisem.
- Obok pack-it z opisem zostaje tylko `dom-ev-knowledge-base` (punkt wejścia, w `always_skills`). Pierwsza propozycja
  (także `dom-ev-glossary` i `dom-ev-charging`) dawała pack-it + EV 13972 i `--packs all` 14276 (> 14000: pack-docs
  `docs-` 159, mode-pdi `pdi-` 145) — człowiek wybrał jeden wyjątek zamiast skracania opisów.
- Ewaluacja na modelu (płatna) **nie została uruchomiona** (decyzja człowieka); pozostała przy bramce bez modelu.

## Pomiar po zmianie (bez modelu)
| Przestrzeń | Lista skilli z opisem | Ostrzeżenie build.py |
|---|---|---|
| `--packs pack-it,pack-ev` | 13631 (w tym rezerwa technologii 813) | brak |
| `--packs pack-ev` | 9097 | brak |
| `--packs all` | 13935 | brak |

`skill_gate.py --hints`: pack-it + EV — 201 skilli, 0 nietrafionych scenariuszy (wąski zapas: 2, oba spoza EV —
core-delivery-lifecycle, proc-safe); EV — 59 skilli, 0 nietrafionych. `--status --strict`: 0 do bramki w obu.

## Ryzyko
Pomiar z 2026-11-15 (`qa-formal-methods`): skill bez pasującego opisu wczytany 1/8, z opisem 8/8. 35 skilli `dom-ev-*`
obok pack-it opiera się teraz na podpowiedzi hooka `skill_hint` (`metadata.slowa`) i na promptach person
i konsultantów EV. Przy sygnałach, że model ich nie wczytuje w projektach pack-it + EV, następny krok to płatna
ewaluacja: `python3 .claude/tests/run_skill_evals.py --skills <dom-ev-…> --models haiku,sonnet` (za zgodą człowieka).
