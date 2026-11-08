# Plan kroku 2: bramka modułów analizy i moduły `security`, `architecture`

Stan: 2026-11-08, w realizacji. Plan nadrzędny: `docs/plans/2026-11-08-tf-analyze-i-katalog-tf.md` (sekcje 3 i 6,
krok 2). Rdzeń z kroku 1: `core/factory/analyze.py` (`docs/plans/2026-11-08-krok-1-tf-analyze-rdzen.md`).

## Zmiana zakresu wobec planu nadrzędnego
Plan nadrzędny mówi „piętra 0–1”. Piętro 1 to model na miejscach wskazanych przez piętro 0 — wymaga wywołań modelu,
budżetu ze STOP i płatnego pomiaru. Dzielę krok na:
- **2a (ten plan):** bramka modułów, dołączanie modułów przez nakładki, moduły `security` i `architecture` na piętrze 0
  (bez modelu, bez kosztu).
- **2b (osobny plan, za zgodą człowieka na koszt):** piętro 1 w rdzeniu (brief dla taniego modelu z miejscami
  z piętra 0 i skillami modułu, budżet na moduł ze STOP, koszt w raporcie) i jego pomiar.

## Pliki
| Plik | Co |
|---|---|
| `core/factory/analyze.py` | `gate [--module m]` — bramka na zestawach testowych modułów |
| `core/factory/install.py` | `PACK_DIRS["analyzers"] = "factory/analyzers"` — nakładka dokłada moduły do projektu |
| `core/tests/test_analyze.py` | testy bramki (A-11…A-13) |
| `packs/pack-it/analyzers/security/` | `analyzer.yaml`, `scripts/scan.py`, `fixtures/` |
| `packs/pack-it/analyzers/architecture/` | `analyzer.yaml`, `scripts/scan.py`, `fixtures/` |
| `packs/pack-it/tests/test_analyzers.py` | bramka obu modułów w przestrzeni roboczej (`factory/analyze.py gate`) i test instalacji |
| `core/factory/PUBLIC_API.md` | `analyzers/` w plikach nakładki, `gate` w poleceniach, klucz `gate` w `analyzer.yaml` |

## Bramka modułu
`analyzer.yaml` dostaje `gate: {min_recall: 1.0, max_false_positives: 0}`. Zestaw testowy:
`fixtures/<przypadek>/repo/` (pliki) i `fixtures/<przypadek>/expected.json` — lista `{rule, file}` (pusta lista =
przypadek czysty, każde ustalenie to fałszywe trafienie). `analyze.py gate` uruchamia skrypt piętra 0 na każdym
`repo/` (bez gita), liczy czułość (znalezione oczekiwane / oczekiwane) i fałszywe trafienia (ustalenia spoza
oczekiwanych), porównuje z progami; wynik na stdout (pierwsza linia `Werdykt: OK | NIE PRZESZŁA`) i kod 0/1.
Moduł bez `fixtures/` nie przechodzi bramki (bez zestawu testowego moduł to generator szumu).

## Moduł `security` (pack-it, prefiks `SEC`, piętro 0)
Pliki z `git ls-files` (bez lockfile'ów, `node_modules`, plików > 1 MB i binarnych); reguły z podstawą (CWE):
- `secret` — wzorce i filtr atrap z hooka `scan_secrets.py` (import z `.claude/hooks/`; kopia wzorców tylko gdy hook
  nieobecny); CWE-798; krytyczna.
- `env-committed` — plik `.env`, `.env.*` w repo (poza `.env.example`, `.env.sample`, `.env.template`); CWE-538; wysoka.
- `dangerous-api` — `eval(`/`new Function(` (JS), `exec(`/`eval(` z argumentem nie-literałem (Python), `pickle.loads`,
  `yaml.load(` bez `SafeLoader`, `subprocess.*(…shell=True`, `os.system(`, `child_process.exec(` z szablonem lub
  konkatenacją, `dangerouslySetInnerHTML`, `.innerHTML =`, `bypassSecurityTrust*` (Angular); CWE-94/78/502/79;
  średnia.
- `tls-off` — `verify=False`, `rejectUnauthorized: false`, `NODE_TLS_REJECT_UNAUTHORIZED=0`; CWE-295; wysoka.
- `weak-hash` — `md5`/`sha1` w pobliżu `password`/`haslo` w tej samej linii; CWE-328; średnia.
- `no-lockfile` — `package.json` bez `package-lock.json`/`pnpm-lock.yaml`/`yarn.lock`, `pyproject.toml` bez lockfile'a
  (`uv.lock`, `poetry.lock`, `pdm.lock`) — ops-supply-chain-security; średnia.
Pliki testowe, przykłady i dokumentacja (`tests/`, `fixtures/`, `docs/`, `*.md`, `test_*`, `*.spec.*`): waga niska,
pewność 0.3, tytuł z dopiskiem — atrapy zostają widoczne, ale nie zagłuszają kodu. Pliki fabryki w projekcie
(`factory/`, `.claude/`) są pomijane. Pewność: 0.9 dla wzorców jednoznacznych (klucze, `.env`), 0.6 dla API zależnych od kontekstu. Fragment w ustaleniu
dla `secret` maskowany (bez wartości sekretu).

## Moduł `architecture` (pack-it, prefiks `ARC`, piętro 0)
Uruchamia `code_graph.py --json` z `.claude/skills/eng-codebase-mapping/scripts/` (brak skryptu = błąd modułu
z poleceniem `tf add pack-it`) i zamienia wynik na ustalenia:
- `cycle` — cykl importów wykonywanych przy imporcie (`cycles.runtime`); plik = pierwszy w cyklu, fragment = cykl;
  średnia (eng-codebase-mapping, ddd-connascence-analysis).
- `upstream` — import „pod prąd” warstw (`upstream`); średnia.
- `hub` — plik z liczbą importujących ≥ 15 i spoza `_vendor`/testów; niska (miejsce do przeglądu, nie błąd).
`incremental: false` (graf jest całościowy: `--since` nie zawęża skanu i nie łączy z poprzednim wynikiem — klucz
obsługiwany przez rdzeń, test A-13). `applies_when.files_any`: pliki `*.py`, `*.ts`, `*.tsx`, `*.js`, `*.java`, `*.cs`, `*.go`.

## Testy (najpierw czerwone)
- A-11 `gate`: moduł z zestawem, który znajduje wszystko → OK; z fałszywym trafieniem w przypadku czystym → NIE
  PRZESZŁA, kod 1; bez `fixtures/` → NIE PRZESZŁA.
- A-12 `gate --module` ogranicza do jednego modułu.
- `packs/pack-it/tests/test_analyzers.py`: oba moduły przechodzą bramkę; po instalacji z pack-it moduły są
  w `factory/analyzers/` i `tf analyze --list` je pokazuje; `security` maskuje sekret w raporcie.
Zestawy: `security` — przypadek z podłożonymi problemami każdej reguły i przypadek czysty (atrapy z `example`,
`process.env`, `.env.example`, bezpieczne `yaml.safe_load`, `subprocess.run([...])`); `architecture` — mały projekt
Python z cyklem i hubem oraz projekt czysty.

## Weryfikacja przed PR
`tools/workspace.py check --packs none`, `pack-it`, `all`; `tests/`; `refs`. Hooki fabryki nie działają w tej sesji
— testy ręcznie.
