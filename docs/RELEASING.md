# Wersjonowanie i wydania fabryki

Fabryka ma jeden numer wersji zgodny z [Semantic Versioning 2.0.0](https://semver.org/lang/pl/) (`MAJOR.MINOR.PATCH`)
w pliku `factory/VERSION`. Wydaną wersję oznacza tag git `vX.Y.Z` (np. `v2.7.0`), a do każdego tagu powstaje GitHub
Release z wpisem z `factory/CHANGELOG.md`. Najwyższy tag jest domyślnym źródłem `python3 factory/update.py` z repozytorium git (`<repo>#vX.Y.Z` przypina wersję).
Co należy do publicznego API (a więc wpływa na rodzaj podbicia), opisuje [factory/PUBLIC_API.md](../factory/PUBLIC_API.md).

## Commity: Conventional Commits

Commity i **tytuły PR** mają format [Conventional Commits 1.0.0](https://www.conventionalcommits.org/pl/v1.0.0/).
PR-y łączymy przez *squash merge*, więc to tytuł PR staje się commitem na `main` i decyduje o kolejnej wersji.
Opis z tytułu trafia wprost do CHANGELOG, dlatego piszemy go po angielsku (tak jak tytuły PR).

```
<typ>(<zakres>)!: <opis>

[treść: dlaczego, nie co]

[stopki, np. Refs: #21  albo  BREAKING CHANGE: <co i jak migrować>]
```

- **Opis**: po angielsku, w trybie rozkazującym (`add`, `fix`, nie `added`), bez kropki na końcu, maks. 72 znaki (dopisek ` (#NN)` z squash merge się nie liczy).
- **Zakres** (opcjonalny), małymi literami, np. `install`, `update`, `build`, `hooks`, `skills`, `release`, `deps`.

| Typ | Kiedy | Wpływ na wersję |
|---|---|---|
| `feat` | nowa funkcja (skill, persona, cecha, flaga, polecenie) | MINOR |
| `fix` | poprawka błędu | PATCH |
| `perf` | szybciej, bez zmiany zachowania | PATCH |
| `refactor`, `test`, `docs`, `style`, `build`, `ci`, `chore`, `revert` | bez zmiany zachowania dla użytkownika | brak |
| `!` po typie/zakresie albo stopka `BREAKING CHANGE:` | zmiana niezgodna wstecz (dowolny typ) | MAJOR |

Przykłady:

```
feat(skills): add eng-repo-readiness skill with a repo readiness audit
fix(hooks): detect git -C outside the project in guard_bash
feat(install)!: write --shared workflows to .github instead of .claude
docs: describe the release process
chore(release): 2.7.0
```

Sprawdzanie:

- **CI**: workflow `pr-title` (`.github/workflows/pr-title.yml`) odrzuca tytuł PR niezgodny z formatem. Działa też po
  edycji tytułu.
- **Lokalnie** (opcjonalnie, raz na klon): `git config core.hooksPath .githooks` włącza hook `commit-msg`.
  Pojedynczy komunikat sprawdzisz poleceniem `python3 scripts/check_commit_message.py "feat(install): …"`.
- Komunikaty generowane przez git (`Merge …`, `Revert "…"`, `fixup!`, `squash!`, `amend!`) nie są sprawdzane.

## Które podbicie (SemVer)

Decyduje **najpoważniejsza** zmiana od ostatniego tagu.

| Zmiana w publicznym API | Od 1.0.0 | W fazie 0.y.z |
|---|---|---|
| niezgodna wstecz (stopka `BREAKING CHANGE:` lub `!`) | MAJOR | MINOR |
| nowa funkcja zgodna wstecz (`feat`) | MINOR | PATCH |
| poprawka (`fix`, `perf`) | PATCH | PATCH |
| tylko dokumentacja, testy, CI, refaktoryzacja | bez wydania | bez wydania |

Fabryka jest już po 1.0.0, więc obowiązuje lewa kolumna. Liczenie (także fazy 0.y.z) robi
`.claude/skills/core-semver/scripts/semver.py`; skrypty wydań tylko z niego korzystają.

## Jak podbijana jest wersja (automatycznie)

Po każdym merge'u do `main` workflow `release` (`.github/workflows/release.yml`) robi kolejno:

1. **Liczy wersję** (`python3 scripts/release.py --ci`): bierze commity od ostatniego tagu `vX.Y.Z` i stosuje tabele
   wyżej.
   - Brak `feat`, `fix`, `perf` i zmian niezgodnych oznacza brak nowej wersji — przebieg kończy się bez zmian.
   - W przeciwnym razie skrypt zapisuje nową wersję w `factory/VERSION` i dopisuje wpis na górze
     `factory/CHANGELOG.md` (sekcje *Breaking*, *Added*, *Fixed* z tytułów commitów; nazwy po angielsku jak w [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), starsze wpisy mają nazwy polskie i zostają bez zmian). Sekcje są zgodne
     z kontrolą `build.py check` (rodzaj podbicia ↔ sekcje), którą job uruchamia przed commitem.
2. **Commituje** te zmiany na `main` jako `github-actions[bot]` z komunikatem `chore(release): X.Y.Z`. Push tokenem
   `GITHUB_TOKEN` nie uruchamia kolejnych workflow, więc commit wydania nie wywołuje następnego wydania.
3. **Tworzy tag** `vX.Y.Z` z adnotacją na commicie wydania.
4. **Tworzy GitHub Release** `vX.Y.Z` z treścią wpisu z CHANGELOG (`python3 scripts/release_notes.py X.Y.Z`).
   Istniejący Release zostaje bez zmian. Brakujący (np. przebieg padł po utworzeniu tagu) dorobi kolejny przebieg na
   `main` albo ręczne uruchomienie workflow (*Run workflow*).

Kilka PR-ów zmergowanych szybko po sobie: przebiegi czekają w kolejce (`concurrency: release`), więc nie policzą tej
samej wersji dwa razy. Gdy w trakcie wydania na `main` trafi nowy commit, push commitu wydania zostanie odrzucony,
a wszystkie zmiany wyda przebieg uruchomiony dla nowszego commitu.

W zwykłym PR **nie zmieniasz** `factory/VERSION` ani nagłówków w CHANGELOG — robi to CI.

### Kiedy wydać ręcznie

Ręczny PR jest potrzebny tylko wtedy, gdy wynik z commitów trzeba nadpisać: commit był źle oznaczony, chcesz
przeredagować CHANGELOG (np. dopisać sekcję *Deprecated*) albo wydajesz MAJOR świadomie.

1. Na świeżej gałęzi od `main` uruchom `python3 scripts/release.py --dry-run`, a potem
   `python3 scripts/release.py minor` (lub `major` / `patch` / `X.Y.Z`).
2. Przejrzyj i przeredaguj `factory/CHANGELOG.md`, potem `python3 factory/build.py check`.
3. Wykonaj commit `chore(release): X.Y.Z` i otwórz PR o tym samym tytule.
4. Po merge'u workflow zauważa w `factory/VERSION` wersję bez tagu i wydaje ją bez ponownego liczenia: sprawdza wpis
   `## [X.Y.Z]` w CHANGELOG (bez niego nic nie zostanie otagowane), a dalej postępuje jak w krokach 3–4 wyżej.

Zasady:

- **Wydanej wersji się nie zmienia.** Taga nie przesuwamy ani nie usuwamy. Błąd w wydaniu naprawia kolejna wersja.
- **Wycofywanie**: najpierw MINOR z sekcją *Deprecated* i aliasem, usunięcie dopiero w kolejnym MAJOR
  (factory/PUBLIC_API.md).

## Ustawienia repozytorium na GitHubie

- *Settings → General → Pull Requests*: włączony **squash merge** (tytuł PR jako komunikat commita).
- *Settings → Actions → General → Workflow permissions*: workflow `release` potrzebuje `contents: write` (deklaruje
  je sam); reguła ochrony `main` musi pozwalać `github-actions[bot]` na push commitu wydania.

## Aktualizacje zależności (Dependabot)

`.github/dependabot.yml` co tydzień otwiera jeden PR z nowymi wersjami akcji GitHub Actions. Tytuł ma postać
`ci(deps): bump …`, więc przechodzi sprawdzanie `pr-title`, a po scaleniu nie podbija wersji fabryki (typ `ci`).
