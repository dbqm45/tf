# Hooki gita — gotowe konfiguracje

Wersje sprawdzone 2026-10-10 w rejestrach: Husky 9.1.7, lint-staged 17.6.0, Lefthook 2.2.1 (npm), pre-commit 4.6.2,
pytest-testmon 2.2.0 (PyPI). Konfiguracje Lefthook i pre-commit przeszły walidację (`lefthook validate`,
`pre-commit validate-config`) i instalację w pustym repozytorium.

Mechanizm jest wszędzie ten sam: sprawdzenia na plikach w stage, kod wyjścia ≠ 0 odrzuca commit lub push.

## Wybór narzędzia
| Projekt | Narzędzie | Dlaczego |
|---|---|---|
| Node/TS, w repo już jest `.husky/` | Husky + lint-staged | nie migruj działającej konfiguracji |
| Node/TS, nowy | Husky + lint-staged albo Lefthook | Lefthook: jeden plik YAML, równoległość, bez skryptu `prepare` |
| Python | framework pre-commit | standard ekosystemu, środowiska hooków izolowane |
| kilka języków, monorepo | Lefthook | jeden binarny program, `glob` i `root` per polecenie |

## Husky + lint-staged (Node)
```bash
npm i -D husky lint-staged
npx husky init            # dopisuje "prepare": "husky" do package.json i tworzy .husky/pre-commit
```
`.husky/pre-commit` (zastąp domyślną treść `npm test`):
```sh
npx lint-staged
```
`.husky/pre-push`:
```sh
npx tsc --noEmit && npx vitest run
```
`package.json`:
```json
"lint-staged": {
  "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
  "*.{json,md,css}": "prettier --write"
}
```
lint-staged sam dopisuje ścieżki plików z stage na końcu polecenia i dodaje poprawione pliki z powrotem.
Przydatne flagi (17.x): `--concurrent <n|false>`, `--fail-on-changes` (porażka, gdy zadanie zmieniło pliki — np. w CI).

## Lefthook (dowolny język)
```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    lint:
      glob: "*.{ts,tsx}"
      run: npx eslint --fix {staged_files}
      stage_fixed: true          # poprawione pliki wracają do stage
    types:
      run: npx tsc --noEmit
pre-push:
  commands:
    tests:
      run: npx vitest run
```
Instalacja: `npx lefthook install`; kontrola: `npx lefthook check-install`, `npx lefthook validate`.
Inne podstawienia: `{all_files}`, `{push_files}`.

## pre-commit (Python)
`.pre-commit-config.yaml` z hookami `repo: local`, `language: system` (narzędzia ze środowiska projektu, bez
przypinania zewnętrznych repozytoriów hooków): `ruff check --fix` na commit, `pytest -q` z `stages: [pre-push]`
i `pass_filenames: false`. `default_install_hook_types: [pre-commit, pre-push]` sprawia, że `pre-commit install`
instaluje oba hooki. Testy powiązane: `pytest --testmon` (pytest-testmon, dane w `.testmondata`).

## Sprawdzenie, że hook działa
1. Wprowadź celowy błąd (nieużywany import, zła typizacja) w pliku, `git add`, `git commit` → commit odrzucony,
   komunikat wskazuje plik.
2. Popraw, commit przechodzi; poprawki formatera trafiły do commita (`git show --stat`).
3. Push z czerwonym testem → odrzucony.
Wynik zapisz jednym zdaniem w raporcie kroku.

## Obejście bramki
`git commit --no-verify`, `HUSKY=0`, `LEFTHOOK=0` wyłączają hooki. Agent ich nie używa; padła bramka → poprawka
przyczyny i nowy commit (core-git-workflow). Wyłączenie na stałe to decyzja człowieka zapisana w strategii testów.
