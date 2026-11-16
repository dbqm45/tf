# Nakładka zespołu {{TITLE}} (`pack-{{COMPANY}}`)

Standardy i domyślne ustawienia jednego zespołu, ponad standardami firmy (`pack-{{ORG}}`). Trzymaj ten katalog we
własnym repozytorium zespołu (albo firmy), nie w repozytorium fabryki.

Warstwy konfiguracji w projekcie zespołu: silnik ← firma ← **zespół** ← projekt ← osoba (`tf config show` pokazuje
źródło każdej wartości). Zespół **tylko zaostrza** politykę autonomii firmy i **tylko zawęża** dozwolone tryby zadania;
nie odblokuje niczego, czego firma zabroniła.

## Co uzupełnić
Wszystkie miejsca do zmiany mają znacznik `TODO`. Lista: `grep -rn TODO .`

| Plik | Co wpisać |
|---|---|
| `pack.yaml` → `description` | jedno zdanie po angielsku (pokazuje je `tf list`) |
| `pack.yaml` → `team_defaults.config` | tylko to, czym zespół różni się od firmy (te same klucze co `org_defaults` firmy) |
| `pack.yaml` → `team_defaults.operations.tracker.prefixes` | prefiksy kluczy zgłoszeń zespołu |
| `analyzers/{{COMPANY}}-standards/rules.yaml` | reguły zespołu sprawdzalne wzorcem (`tf analyze`, bez modelu), z przykładami w `fixtures/` |
| `skills/{{PREFIX}}standards/` | ustalenia zespołu wymagające oceny: `SKILL.md` to spis, obszary w `references/` — najpierw scenariusze w `tests/skill_evals/` |
| `semgrep.yml` | reguły semgrep zespołu w skanie każdego kawałka pętli `/tf` |
| `settings.json` | uprawnienia Claude Code zespołu (np. `deny` dla narzędzi, których zespół nie używa) |

Nie powtarzaj standardów firmy: działają w projekcie z nakładki `pack-{{ORG}}`. Tu trafia tylko to, co obowiązuje
w zespole ponad nimi (np. backend: zasady API i migracji; frontend: biblioteka komponentów).

## Sprawdzenie i instalacja
```
python3 tools/workspace.py check --packs pack-it,pack-{{ORG}},pack-{{COMPANY}} --pack-dir <repo firmy> --pack-dir <ten katalog>
tf install --pack-dir <repo firmy> --pack-dir <repo zespołu> --add pack-{{COMPANY}}
```
Nakładka firmy instaluje się sama (`requires.packs`). Zmiana później: popraw pliki, podbij `version` (SemVer), dodaj
tag; projekty dostaną zmianę przy `tf update`. Przewodnik całości: `org/README.md` w repozytorium fabryki.
