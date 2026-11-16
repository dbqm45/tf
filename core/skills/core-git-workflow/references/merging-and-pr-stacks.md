# Strategie scalania i stos PR-ów

Polecenia `gh` (GitHub CLI) to przykład. Inne platformy mają odpowiedniki: zmianę gałęzi docelowej PR i scalanie
z wyborem strategii.

## 1. Strategia scalania
| Strategia | Co trafia do gałęzi głównej | Kiedy |
|---|---|---|
| **squash** | jeden commit z całego PR | domyślnie przy małych PR-ach; historia „jeden PR = jeden commit”, łatwy revert |
| **rebase** | commity PR jeden po drugim, bez commita scalającego | commity PR są starannie podzielone i każdy przechodzi testy |
| **merge commit** | commity PR plus commit scalający | gałęzie długo żyjące albo gdy liczy się zapis, kiedy i co scalono (np. gałąź wydania) |

- W repozytorium obowiązuje jedna strategia (ustawienie repozytorium albo ochrona gałęzi). Nie zmieniaj jej dla
  pojedynczego PR bez powodu.
- Przy squash podaj tytuł commita wprost, czyli tytuł PR z numerem, np.
  `gh pr merge 42 --squash --subject "feat(api): limit zapytań (#42)"`. Bez tego narzędzie może wziąć nazwę gałęzi
  albo pierwszy commit. Format tytułu opisuje core-conventional-commits.
- Stan PR przed scaleniem: `gh pr checks <N>` (CI), `gh pr status` (twoje PR-y i prośby o przegląd),
  `gh pr view <N>` (opis, przeglądy). Scalasz tylko przy zielonym CI i wymaganych zatwierdzeniach.

## 2. Stos PR-ów (stacked PRs)
Duża zmiana podzielona na kolejne PR-y, z których każdy celuje w gałąź poprzedniego:
`main ← #1 (feat-a) ← #2 (feat-b, baza feat-a) ← #3 (feat-c, baza feat-b)`. Każdy PR jest mały i przeglądany
osobno, a kolejne mogą powstawać przed scaleniem pierwszego.

**Problem po squash:** po scaleniu #1 przez squash gałąź `main` ma jeden nowy commit, którego nie ma w historii
`feat-b`. PR #2 nadal zawiera oryginalne commity #1, więc diff względem `main` jest za duży, a przeniesienie
zwykłym `rebase` daje konflikty z własną, już scaloną zmianą.

**Procedura** (po kolei, jeden PR naraz):
1. Scal pierwszy PR (squash, tytuł wprost) i pobierz `main`: `git fetch origin main`.
2. Przenieś następny PR na `main` bez commitów poprzedniej gałęzi:
   `git rebase --onto origin/main feat-a feat-b`. Polecenie bierze commity, które są w `feat-b`, a nie ma ich
   w `feat-a`, i odtwarza je na `origin/main`. Zostają tylko zmiany #2.
3. Wypchnij przepisaną gałąź: `git push --force-with-lease origin feat-b`. To przepisanie historii, więc tylko na
   własnej gałęzi i za zgodą człowieka (sekcja „Zakazane” w SKILL.md).
4. Zmień gałąź docelową PR na `main`: `gh pr edit <N> --base main`. Bez tego PR scali się do nieaktualnej `feat-a`.
5. Poczekaj na CI na nowym commicie, potem scal (squash, tytuł wprost). Powtórz od kroku 1 dla kolejnego PR.

**Konflikty w trakcie `rebase --onto`:** zatrzymaj się i pokaż człowiekowi pliki z konfliktami. Nie rozwiązuj ich
automatycznie. Po rozwiązaniu: `git add <pliki>` i `git rebase --continue`; rezygnacja: `git rebase --abort`.

**Dlaczego nie cherry-pick:** przeniesienie bazy zachowuje PR w platformie (oznaczenie „scalony do main”,
przeglądy, dyskusję), a historia `main` zostaje liniowa, bez zdublowanych commitów.

## Źródła
- callstackincubator/agent-skills, skill `github` z plikiem stacked-pr-workflow.md (wersja sprzed commita
  3bd44da z 2026-08-07, w którym autorzy usunęli skill jako przestarzały), licencja MIT; odczyt 2026-10-21.
  Opisane własnymi słowami; tabela strategii scalania to nasze uzupełnienie.
- `git help rebase` (opcja `--onto`); `gh pr merge --help`, `gh pr edit --help`, `gh pr checks --help` w gh 2.89.0
  (sprawdzone 2026-10-21): tytuł commita przy squash ustawia `--subject` (`-t`); opcja `--title` podana w źródle
  w tej wersji nie istnieje.
