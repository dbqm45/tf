# Plan: przegląd PR przez AI w CI — gotowy workflow i REVIEW.md z rekonstrukcji (F6, pierwszy element)

Data: 2026-10-26 · Status: zrobione (kroki 1–5), commit i PR na prośbę człowieka · Gałąź: `claude/great-hypatia-angvam`
Źródło: pdi `docs/plan-jeden-flow-sdlc.md` §5 (wiersz „AI review w CI — szablon workflow z claude-code-action
i `REVIEW.md` z rekonstrukcji”, F6); tf `core/skills/core-git-workflow/references/przeglad-ai-w-ci.md` (wzorzec),
`references/review-md.md` (szablon zasad), pack-it `ops-ci-cd/references/przyklady.md` przykład 4 (szkielet YAML),
`eng-project-reconstruction/references/szkice.md` (`REVIEW.draft.md`). SHA akcji sprawdzone `git ls-remote`
2026-10-26: `actions/checkout` v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1`, `anthropics/claude-code-action`
v1.0.262 = `925afb53776cf1a2b738c6bdbed37b4d4000ef13`.

## TL;DR
Wiedza o przeglądzie AI w CI jest, gotowego artefaktu nie ma. `ai_review.py install` (rdzeń, core-git-workflow)
zapisuje `.github/workflows/ai-review.yml`: przegląd PR z etykietą `ai-review` (albo każdego, `--all-prs`) według
`REVIEW.md`, agent tylko czyta i zwraca JSON (werdykt, podsumowanie, do 10 ustaleń), a osobny krok workflow ustawia
status `ai-review/verdict` i jeden komentarz zbiorczy (aktualizowany, nie dublowany). Etykieta `ai-review-override`
dodana przez człowieka zmienia status na zielony bez nowego przeglądu. `ai_review.py review-md` przenosi zatwierdzony
`REVIEW.draft.md` z rekonstrukcji do `REVIEW.md`.

## Decyzje
- **Rdzeń:** przegląd PR i `REVIEW.md` opisuje core-git-workflow; workflow nie zależy od nakładek.
- **Agent nie komentuje sam:** wynik przez `--json-schema` (wyjście `structured_output`), komentarz i status pisze
  krok workflow (`gh api`). Bramka żyje w workflow (wzorzec §6); brak poprawnego JSON = czerwony status.
- **Bezpieczeństwo (ops-ci-cd):** `permissions: {}` na górze, w jobach minimum; blokada PR z forka; akcje przypięte
  do pełnych SHA; dane PR tylko przez `env:`, żadnego `${{ … }}` w `run:`; `concurrency` per PR; `fetch-depth: 0`.
- **Koszt:** domyślnie tylko PR z etykietą `ai-review`; model `sonnet`, `--max-turns 30`, `timeout-minutes: 20`.
- **REVIEW.md:** brak pliku → przegląd według domyślnych przebiegów z promptu, a `install` mówi, jak go założyć.
  `review-md` nie nadpisuje istniejącego `REVIEW.md` bez `--force`; szkic zatwierdza człowiek (polecenie wydaje on).
- **Weryfikowalne lokalnie:** test wyciąga skrypt kroku werdyktu z zainstalowanego YAML i uruchamia go z atrapą `gh`.
  Działania samej akcji `claude-code-action` na GitHubie nie sprawdzam w tej sesji [niezweryfikowane: uprawnienia
  tokenu akcji — wg wzorca: contents read, pull-requests write, statuses write; sprawdzić na PR testowym].

## Kolejność i testy
1. Czerwone testy `core/tests/test_ai_review.py`: install (plik, odmowa nadpisania, `--force`, `--all-prs` bez warunku
   etykiety, podpowiedź o braku `REVIEW.md`), właściwości bezpieczeństwa YAML (permissions, fork, SHA, brak `${{`
   w `run:`, fetch-depth, concurrency), krok werdyktu z atrapą `gh` (ODRZUCONE → failure, ZATWIERDZONE i WYMAGA_UWAGI →
   success, brak JSON → failure, obejście → success, komentarz ze znacznikiem: nowy POST, istniejący PATCH), job
   obejścia; review-md (kopia szkicu, odmowa nadpisania, brak szkicu → 1).
2. Kod: szablon `core/skills/core-git-workflow/templates/ai-review.yml`, skrypt `scripts/ai_review.py`.
3. Scenariusze ewaluacji (przed treścią): core-git-workflow, eng-project-reconstruction.
4. Treść: core-git-workflow (SKILL + `przeglad-ai-w-ci.md`: gotowy szablon), eng-project-reconstruction (szkic →
   `review-md`), pack-it ops-ci-cd przykład 4 (odesłanie do gotowego szablonu), `PUBLIC_API.md` jeśli dotyczy.
5. Bramki: `workspace.py check --packs all` i `none`; `refs`; `tests/test_*.py`; `skill_gate`, `sync-gate`; tytuł.
