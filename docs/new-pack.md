# Nowa nakładka lub tryb

Przewodnik dla autora fabryki (repozytorium tf). Pełna lista kluczy `pack.yaml` i plików nakładki należy do
publicznego API: `core/factory/PUBLIC_API.md`.

## Nakładka czy tryb
- **Nakładka** (`packs/pack-<nazwa>/`, `id: pack-<nazwa>`) — wiedza dziedzinowa: skille, role, persony,
  konsultanci. Instalowana, gdy projekt jej potrzebuje.
- **Tryb** (`modes/mode-<nazwa>/`, `id: mode-<nazwa>`, `kind: mode`) — sposób pracy włączany przez człowieka:
  agent sesji głównej, skill procesowy, skrypty, uprawnienia, przewodnik `GUIDE.md`.
Ten sam format i loader; instalator sprawdza, że `kind: mode` leży w `modes/`, a nakładka w `packs/`.

W sesji Claude Code uruchomionej w repo tf prowadzi przez to skill `tf-new-pack` (`.claude/skills/tf-new-pack/`,
nie trafia do projektów): dopytuje o zakres, prefiks, zależności i role, proponuje scenariusze, woła generator
i bramki.

## Szkielet jednym poleceniem
```
python3 tools/workspace.py new-pack <nazwa> [--kind pack|mode] [--prefix abc-] [--title "…"] [--description "…"]
                                    [--skill abc-nazwa] [--role nazwa-roli] [--no-check]
```
Tworzy:
- `pack.yaml` z wersją `0.1.0`, `default: false`, `requires.core` od bieżącej wersji rdzenia do następnego MAJOR
  i jednym wymiarem (`facets`) z prefiksem;
- szkielet skilla `skills/<prefiks>…/SKILL.md` i scenariuszy `tests/skill_evals/<skill>.json`;
- opcjonalnie rolę `roles/<rola>.yaml` z tym skillem; dla trybu `GUIDE.md`;
- wpis w macierzy CI (`.github/workflows/factory-checks.yml`, przed `all`).

Potem uruchamia `workspace.py check --packs <id>` i `refs` i wypisuje listę do zrobienia (bez `--no-check`).
Istniejący katalog, zajęty prefiks, zła nazwa albo skill spoza prefiksu → kod 2 bez zmian na dysku.
**Szkielet scenariuszy celowo nie przechodzi bramki** (`skill_gate.py --status` i trafienia podpowiedzi), dopóki
nie powstaną prawdziwe scenariusze i treść.

## Kolejność pracy
1. **Zakres i granice** — jakie pytania ma obsłużyć nakładka i które należą do istniejących skilli (sprawdź
   `python3 tools/workspace.py assemble --packs all` i `.claude/catalog.md` w workspace).
2. **Prefiks** — krótki, jeden na nakładkę lub wymiar (`facets`); nie może kolidować z rdzeniem ani inną nakładką.
   `order` ustawia kolejność wymiarów na liście skilli.
3. **Zależności** — `requires.packs` (nakładka nie działa bez innej) albo `optional_packs` (odwołania pomijane,
   gdy nakładki nie ma). Tylko do tych nakładek wolno odwoływać się z treści skilli — pilnuje tego `refs`.
4. **Scenariusze przed treścią** (core-skill-authoring): 2× trigger z luką, 1× no-trigger z sąsiadem.
5. **Treść skilli**, role i persony (`roles/`, `personas/`); przy wielu rzadko używanych skillach rozważ
   `skill_visibility.name_only_prefixes` — opis nie zabiera budżetu listy skilli.
6. **Bramki** w workspace: `python3 factory/skill_gate.py <skill>` i `--hints` (także na `--packs all`), potem
   `python3 tools/workspace.py sync-gate --out .work/<id>`.
7. **Sprawdzenie**: `python3 tools/workspace.py check --packs <id>`, `check --packs all`, `refs`; PR z tytułem
   `feat(<id>): …`.

## Nakładka poza repozytorium fabryki
Nakładka może żyć w innym repozytorium (np. wiedza domenowa razem z jej źródłami). Kontrakt jest ten sam co w `packs/`:
`pack.yaml` z `kind` i prefiksem id (`pack-`/`mode-`), `requires.core`, scenariusze i rejestr bramki w `tests/`.
- Instalacja w projekcie: `install.py --pack-dir <katalog|adres git> --add <id>` (albo `update.py`/`tf` z tymi flagami).
  Źródło to katalog z `pack.yaml`, katalog z `*/pack.yaml` albo repozytorium git (`#<tag|gałąź>`; bez tego najnowszy
  tag `vX.Y.Z`, a bez tagów gałąź domyślna). Manifest (i lock zespołowy) zapamiętuje źródło w `pack_dirs`, więc
  aktualizacja pobiera nakładkę ponownie; `--drop-pack-dir <źródło>` je zapomina.
- Instalator odmawia, gdy id zajmuje nakładka fabryki, gdy źródła nie ma, a nakładka z niego jest wybrana (podaj nowe
  położenie `--pack-dir`), i gdy `skill_audit.py` zgłasza wysoką wagę w skillach nakładki.
- Sprawdzenie z fabryką: `python3 tools/workspace.py check --packs pack-it,<id> --pack-dir <katalog>` (przestrzeń
  `.work/<nakładki>+ext`); `sync-gate --out <ta przestrzeń> --pack-dir <katalog>` zapisuje wyniki bramki do
  `<katalog>/tests/skill_gate/<id>.json`.

## Nakładka firmowa
Standardy i domyślne ustawienia jednej organizacji: osobny zestaw w katalogu `org/` (generator `org/new_org_pack.py`,
szablon `org/template/`, przewodnik `org/README.md`). Nakładka firmowa to zwykła nakładka z kluczem `org_defaults`:
- `config` — domyślne organizacji między silnikiem a projektem (`autonomy`, `tiers`, `profiles`, `default_profile`,
  `work`, `loop`, `steps`, `task`, `commit_language`); czytają je `build.py`, `guard_bash`
  (polityka autonomii nadal tylko zaostrza), `tf risk`, `tf work` i `tf config show` (źródło „organizacja”);
- `operations.tracker` — domyślny tracker, prefiksy i `fields` karty operacyjnej; bez adresu (`url`).
W projekcie najwyżej jedna nakładka z `org_defaults`; klucz spoza listy to błąd `build.py check` bez skutku.
Moduł reguł z `tier0.rules` wykonuje skaner rdzenia `.tf/factory/rules_scan.py`; `semgrep.yml` nakładki trafia do
`.tf/factory/packs/<id>/` i do skanu kawałka pętli.

## Wersjonowanie
- Wersję rdzenia i CHANGELOG liczy workflow wydania z Conventional Commits (`docs/RELEASING.md`). Wersji nakładki
  (`version` w `pack.yaml`) nic nie podbija automatycznie — zmieniasz ją ręcznie według SemVer [zalecenie, nie
  reguła sprawdzana w CI]: nowy skill lub rola — MINOR, zmiana nazwy albo usunięcie skilla, roli lub persony —
  MAJOR z wpisem w `factory/migrations.py` (zmiana nazwy skilla jako MAJOR — decyzja z 2026-10-21).
- `requires.core` zawęża zakres, gdy nakładka zaczyna używać funkcji nowszego rdzenia.

## Migracje danych projektu
Gdy nowa wersja nakładki zmienia format plików, które jej skille zakładają w projekcie (np. nagłówki dokumentu
sprawdzanego skryptem), dodaj `packs/<id>/migrations.py` z funkcją `migrate_values(root, dry) -> list[str]`: zwraca
zmienione ścieżki, przy `dry=True` niczego nie zapisuje, a ponowne wywołanie po migracji zwraca pustą listę. Instalator
kopiuje plik do `.tf/factory/packs/<id>/`, a `migrations.migrate_values` rdzenia wywołuje go przy aktualizacji — rdzeń
nie wymienia skilli nakładek. Przykład: `packs/pack-it/migrations.py` (dossier legacy).
