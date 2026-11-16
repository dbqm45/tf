# Wyłączone skille

Skille, które pomiar uznał za zbędne: model bez skilla odpowiada tak samo dobrze. **Nie są usunięte.** Zostają
w repozytorium i w instalacji, ale:
- model nie wczytuje ich sam (`disable-model-invocation: true`), a hook `skill_hint` ich nie podpowiada;
- `build.py` usuwa je z list skilli ról, person, agentów wspólnych, konsultantów i `always_skills`, a w katalogu
  (`.claude/catalog.md`) są w osobnej sekcji „Wyłączone skille”; pliki YAML nakładek się nie zmieniają;
- człowiek może wywołać skill ręcznie: `/<nazwa>`;
- scenariusze `trigger` są w `tests/skill_evals/inactive/<skill>.json`, w pliku głównym zostają scenariusze
  `no-trigger`;
- aktywne skille i prompty agentów nie odsyłają do nich po nazwie: `build.py check` ostrzega o każdym takim
  odsyłaczu, a test `IN-11` w `test_build.py` nie przechodzi, dopóki odsyłacz zostaje w treści fabryki.

Przy wyłączaniu kolejnego skilla usuń odsyłacze do niego: zostaw temat, usuń nazwę albo wskaż aktywny skill.

Skill jest wyłączony, gdy w nagłówku SKILL.md ma `disable-model-invocation: true` i `metadata.status: "nieaktywny"`.

## Jak włączyć skill z powrotem
1. W SKILL.md usuń `disable-model-invocation: true` i `status: "nieaktywny"`.
2. Przenieś scenariusze z `tests/skill_evals/inactive/<skill>.json` z powrotem do `tests/skill_evals/<skill>.json`.
3. `python3 .tf/factory/skill_gate.py <skill>` i `python3 .tf/factory/build.py`.
4. Usuń wiersz z tej listy i dopisz powód powrotu (np. nowy pomiar z przewagą, nowa reguła fabryki w treści).
5. Odsyłacze usunięte przy wyłączaniu (commit z 2026-11-16) możesz przywrócić tam, gdzie skill znów coś wnosi.

Kiedy warto wrócić: skill dostał wiedzę, której modele nie mają (reguła fabryki, świeża wersja narzędzia), albo
pomiar na Haiku albo na holdoucie pokazał przewagę.

## Lista

Pomiar: 2026-11-16, Sonnet, ze skillami fabryki i bez (`--baseline`), `--isolated`, jeden przebieg na scenariusz,
scenariusze strojenia `trigger`. Raport: `docs/evals/2026-11-16-podejrzane-skille-podsumowanie.md`, surowe wyniki:
`docs/evals/2026-11-16-podejrzane-skille.jsonl`. Scenariusze napisano na podstawie treści skilli, więc sprzyjają
skillom — brak przewagi mimo to jest mocnym sygnałem dublowania.

„✓” = odpowiedź spełnia wszystkie sprawdzenia treści.

| Skill | Nakładka | Wyłączony | Ze skillem | Bez skilla | Powód |
|---|---|---|---|---|---|
| `eng-algorithms-data-structures` | pack-it | 2026-11-16 | 2/2 | 2/2 | złożoność, struktury danych — wiedza podręcznikowa |
| `fe-technical-seo` | pack-it | 2026-11-16 | 3/3 | 3/3 | robots.txt, hreflang, soft 404 — model zna sam |
| `ops-iac-terraform` | pack-it | 2026-11-16 | 2/2 | 2/2 | blokada stanu, dryf — model zna sam |
| `pm-saas-metrics` | pack-it | 2026-11-16 | 4/4 | 4/4 | NRR, burn multiple, Rule of 40, LTV — model zna sam |
| `proc-lean` | pack-it | 2026-11-16 | 2/2 | 2/2 | prawo Little'a, WSJF — model zna sam |
| `tool-nx` | pack-it | 2026-11-16 | 3/3 | 3/3 | granice modułów, migracja Nx 23 — model zna sam, także nową wersję |
| `eng-design-patterns` | pack-it | 2026-11-16 | 2/3 | 3/3 | ze skillem gorzej (`dekorator-vs-proxy`) |

### Wyniki na scenariusz

| Skill | Scenariusz | Ze skillem | Bez skilla | Skill wczytany |
|---|---|---|---|---|
| eng-algorithms-data-structures | `kolejka-shift` | ✓ | ✓ | tak |
| eng-algorithms-data-structures | `top-k-sortowanie` | ✓ | ✓ | tak |
| fe-technical-seo | `robots-txt-a-indeks` | ✓ | ✓ | tak |
| fe-technical-seo | `sklep-jezyki-i-filtry` | ✓ | ✓ | tak |
| fe-technical-seo | `spa-soft-404-i-dane-produktu` | ✓ | ✓ | tak |
| ops-iac-terraform | `blokada-stanu` | ✓ | ✓ | tak |
| ops-iac-terraform | `dryf-i-ochrona` | ✓ | ✓ | tak |
| pm-saas-metrics | `burn-multiple-rule-of-40` | ✓ | ✓ | tak |
| pm-saas-metrics | `edge-ltv-bez-danych` | ✓ | ✓ | tak |
| pm-saas-metrics | `nrr-maskuje-churn` | ✓ | ✓ | tak |
| pm-saas-metrics | `zdrowie-ekonomiki` | ✓ | ✓ | tak |
| proc-lean | `prawo-little` | ✓ | ✓ | tak |
| proc-lean | `wsjf-priorytet` | ✓ | ✓ | tak |
| tool-nx | `bez-plikow-granice` | ✓ | ✓ | tak |
| tool-nx | `granice-modulow` | ✓ | ✓ | tak |
| tool-nx | `migracja-nx23` | ✓ | ✓ | tak |
| eng-design-patterns | `dekorator-vs-proxy` | ✗ (brak: „nie dubluj tego, co już robi”) | ✓ | tak |
| eng-design-patterns | `role-object` | ✓ | ✓ | tak |
| eng-design-patterns | `switch-strategia` | ✓ | ✓ | tak |

## Zmierzone, ale niewyłączone

| Skill | Ze skillem | Bez skilla | Dlaczego zostaje |
|---|---|---|---|
| `eng-design-principles` | 2/3 | 2/3 | remis z dwóch różnych scenariuszy: ze skillem zalicza `agent-przeinzynierowuje-mimo-regul` (reguła fabryki „drabina minimalizmu”, bez skilla ✗), bez skilla — `dry-przypadkowe`; skill jest w `always_skills` każdej persony pack-it |

## Ograniczenia
- Tylko Sonnet: Haiku bez skilla może wypaść gorzej. Tańsi wykonawcy (tier `fast`) też tracą te skille.
- Jeden przebieg na scenariusz; scenariusze strojenia, nie holdout.
