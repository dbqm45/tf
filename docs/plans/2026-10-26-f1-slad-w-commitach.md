# Plan: F1 w tf — ślad w commitach (`Change:`), Talos na cięciach zmiany, raport przebiegu w repo

Data: 2026-10-26 · Status: zrobione (kroki 1–5), commit i PR na prośbę człowieka · Gałąź: `claude/great-hypatia-angvam`
Źródło: pdi `docs/plan-jeden-flow-sdlc.md` §5 (tabela tf, wiersze F1) i „F1 — Ślad w commitach”; `contract/README.md`
„Identyfikatory” (D3: klucz `^[A-Z][A-Z0-9]+-[0-9]+$`, TSK ma rodzica CHG; ShipScope wyciąga klucze z commitów);
tf `docs/plans/2026-10-23-integracja-pdi.md` (zakres F1). Poza zakresem: strona ShipScope (sync z repo, hierarchia
CHG → TSK), F2 (eksport JSON rekonstrukcji), F3 (triaż PRB).

## TL;DR
Commit niesie klucz zmiany w stopce `Change: TSK-57` (albo `CHG-12`), a commit cięcia za flagą — `Flag: <klucz>`.
Hook `commit-msg` w rdzeniu (skrypt skilla core-conventional-commits, instalowany na żądanie) sprawdza nagłówek
Conventional Commits i stopki, a na gałęzi z kluczem w nazwie (`story/tsk-57-…`) wymaga `Change:` z tym kluczem.
Talos przyjmuje klucz cięcia (`/talos-story-run TSK-57`, tak już woła go F4): `run_report.py start --task TSK-57`
składa story z wiersza `plan.md` zmiany i `intent.md`, gałąź ma klucz, każdy commit — `Change: TSK-57`, a `finish`
zapisuje raport do `docs/project/changes/CHG-n/runs/TSK-57.md` (ślad audytowy w repo).

## Decyzje
- **Rdzeń, nie tryb:** stopka `Change:` to ogólna konwencja (klucz w kształcie Jiry) i plan F1 przypisuje ją do
  core-conventional-commits i core-git-workflow; bez pdi też działa (np. klucze Jiry). Rdzeń nie nazywa skilli nakładek.
- **Hook na żądanie:** `commit_msg.py install` zapisuje `commit-msg` w katalogu hooków gita (`git rev-parse
  --git-path hooks`, więc szanuje `core.hooksPath`); istniejący obcy hook → nie nadpisuje, podaje, jak go połączyć.
  Katalog `.git/hooks` chroni `tdd_guard`, więc instaluje człowiek (albo agent poleceniem za jego zgodą).
- **Reguły hooka:** nagłówek `<typ>(<zakres>)!: <opis>` (typ małymi literami, opis ≤ 72 znaki, bez kropki), pusta linia
  po nagłówku, `BREAKING CHANGE` wielkimi; zakres dowolny (szablon F4 commituje `docs(CHG-12): …`). Wiadomości gita
  (`Merge`, `Revert "…"`, `fixup!`, `squash!`, `amend!`) przechodzą. Stopki: `Change:` — klucze rozdzielone przecinkiem,
  każdy w kształcie D3; `Flag:` — jeden klucz flagi `[A-Za-z0-9._-]+`. Gałąź z kluczem w nazwie (bez względu na
  wielkość liter, np. `story/tsk-57-ponowienie`) → wymagany `Change:` z tym kluczem.
- **Talos:** `start` przyjmuje `--task TSK-n` (tytuł opcjonalny), szuka `docs/project/changes/*/plan.md` z tym TSK
  w `tasks`; story = wiersz tabeli planu (wartość, wydanie, flaga, pliki, weryfikacja) + sekcje `intent.md`;
  `run.json` ma `change`, `task`, `flag` (z kolumny „Flaga” albo `release.yaml`). Brak TSK w żadnym planie → kod 2.
  `finish` przy przebiegu z `task` zapisuje kopię raportu w `changes/CHG-n/runs/TSK-n.md` (katalog przebiegu
  `.claude/runs/` zostaje ignorowany przez git).

## Kolejność i testy
1. Czerwone testy:
   - `core/tests/test_commit_msg.py`: poprawny commit; `Change:` z TSK i CHG, kilka kluczy; zły klucz; `Flag:` pusty
     i ze spacją; nagłówek bez typu, z kropką, za długi, bez pustej linii; `Merge …` przechodzi; komentarze gita
     pominięte; gałąź `story/tsk-57-x` bez `Change:` → błąd z podpowiedzią, z `Change: TSK-57` → OK; `install`
     w świeżym repo, hook działa w `git commit`; obcy hook nie jest nadpisywany; `docs(CHG-12): …` z F4 przechodzi.
   - `modes/mode-talos/tests/test_run_report.py`: `start --task TSK-58` składa story z planu i intentu, `run.json` ma
     change/task/flag; nieznany TSK → kod 2; `finish` zapisuje `changes/CHG-12/runs/TSK-58.md`.
   - `test_mode_talos.py` T-9: SKILL — wejście TSK, `--task`, gałąź z kluczem, `Change:` w każdym commicie, raport
     w `changes/…/runs/`.
2. Kod: `core/skills/core-conventional-commits/scripts/commit_msg.py`; `run_report.py`.
3. Scenariusze ewaluacji (przed treścią): core-conventional-commits, core-git-workflow.
4. Treść: core-conventional-commits (stopki `Change:`/`Flag:`, hook), core-git-workflow (gałąź z kluczem),
   talos-story-run (wejście TSK, raport w repo).
5. Bramki: `workspace.py check --packs all` i osobno `none`, `mode-talos`, `mode-pdi`; `refs`; `tests/test_*.py`;
   `skill_gate` zmienionych skilli i `sync-gate`; tytuł przez `check_commit_message.py`.
