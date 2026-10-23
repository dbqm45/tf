# Plan: tf w jednym flow SDLC z pdi

Data: 2026-10-23 · Status: **do startu** (F0 w tf) · Gałąź z planem: `claude/magical-dirac-wjvn8y`

## TL;DR
**Cel nadrzędny:** jedno źródło decyzji — decyzje z różnych narzędzi (sesje Claude Code, tf, pdi, kolejne) można
wypchnąć i zapisać w jednym miejscu, zgodnie ze wspólnym kontraktem; to element większego workflow AI SDLC, a nie
integracja dla samej integracji. Dziennik zmiany w tf (F0) jest pierwszym krokiem: lokalny zapis decyzji
(`decisions.md`) w formacie, który rejestr może zaindeksować.

pdi (repo `dbqm45/pdi`, prywatne) to warstwa decyzji w procesie AI-native SDLC: zgłoszenia `PRB`, triaż, rejestr
decyzji `DEC`, skrzynka bramek, orkiestracja i ślad od zgłoszenia do wydania. tf jest „mózgiem” procesu (fazy,
persony, bramki B1–B6); pdi wywołuje tf, nie kopiuje jego logiki. Wspólny **kontrakt** żyje w `pdi/contract/`
(wersja 0.3.0): schematy decyzji, zgłoszenia, nagłówka artefaktu zmiany, cięcia i zdarzeń; klucze w kształcie Jiry
(`PRB-34`, `CHG-12`, `TSK-57`, `DEC-41`), numeracja globalna, prefiksy konfigurowalne.

**Pierwszy krok w tf (F0):** dziennik per zmiana — `project_record.py change new CHG-12 --source PRB-34` tworzy
`docs/project/changes/CHG-12/` z artefaktami, których nagłówek jest zgodny z `pdi/contract/change.schema.json`.
Polecenie startowe sesji: sekcja „Polecenie startowe — F0”. Kroki F1–F4 są tu tylko jako zakres.

## Przekazanie (jak wznowić)
1. Przeczytaj ten plik i `git status` w repo tf.
2. Następny krok: **F0** — wklej „Polecenie startowe — F0” w nowej sesji w repo tf.
3. Zasady repo (jak w planie rekonstrukcji): repo publiczne — bez README opisującego fabrykę; `claude-team-factory`
   i `ev-team-factory` nietknięte; merge do `main` po zielonym CI; odpowiedzi po polsku.
4. Bramki przed PR: `python3 tools/workspace.py check --packs all`, `python3 tools/workspace.py refs`,
   `for t in tests/test_*.py; do python3 "$t" || exit 1; done`; tytuł PR: `python3 scripts/check_commit_message.py "<tytuł>"`.

## Kontekst z pdi (stan 2026-10-23)

| Co | Gdzie w pdi | Znaczenie dla tf |
|---|---|---|
| Plan jednego flow (fazy F0–F6, decyzje D1–D7) | `docs/plan-jeden-flow-sdlc.md`, §5 „tf — zmiany w fabryce” | lista zmian w tf |
| Rola pdi, rozbieżności R1–R7 | `docs/13-rola-pdi-w-sdlc.md` | co pdi posiada, a co wywołuje w tf |
| Decyzje właściciela | `docs/decyzje.md` | D1 (kontrakt w pdi), D2/R1 (podział rejestru), D3 (format ID) |
| Kontrakt 0.3.0 | `contract/` (`README.md`, `*.schema.json`, `examples/`) | nagłówek artefaktu zmiany, klucze, zdarzenia |

Kontrakt 0.3.0 jest na gałęzi `claude/magical-dirac-wjvn8y` w pdi do czasu scalenia z `main` — sprawdź przed startem.

**Decyzje pdi wiążące dla tf:**
- **D2/R1 — podział rejestru decyzji:** decyzje o konkretnej zmianie (B1–B6, odpowiedzi na pytania ci_for_sdlc)
  mają źródło prawdy w repo projektu, w `docs/project/changes/CHG-n/decisions.md`; pdi je indeksuje. Decyzje bez
  zmiany (triaż, odrzucenia) żyją w pdi.
- **D3 — klucze:** `[A-Z][A-Z0-9]+-[0-9]+`, globalne; `TSK` ma rodzica `CHG`. Dopisek w commitach `Change: TSK-57`
  (F1).
- **Nagłówek artefaktu zmiany** (`contract/change.schema.json`) = nagłówek z `core-project-record` (`artifact`,
  `phase`, `status`, `version`, `author`, `created`, `updated`, `inputs`) + `change` (wymagane), `source` (PRB,
  opcjonalne), `tasks` (lista TSK, tylko w `plan.md`). `artifact` ∈ `intent`, `requirements`, `design`, `plan`,
  `decisions`, `run`. Nagłówek zostaje prostym YAML (bez obiektów zagnieżdżonych), żeby parser `project_record.py`
  go czytał.

## Zakres zmian w tf (z planu jednego flow, §5)

| Faza | Zmiana | Gdzie w tf |
|---|---|---|
| **F0** | Dziennik per zmiana: `change new <CHG> [--source <PRB>]`, szablony `intent`, `plan`, `decisions`; `check` waliduje nagłówki w `changes/` | `core/hooks/project_record.py`, `core/skills/core-project-record/` — **ta sesja** |
| **F0b** | Zapis i wypychanie decyzji z dowolnego narzędzia: `project_record.py decision add --change CHG-n "…"` (wpis w `decisions.md`; gdy serwer MCP pdi podłączony — od razu `record_decision` i numer `DEC-n`), kolejka bez połączenia (wpis „niewysłane”, `decision sync` wysyła później, stały identyfikator wpisu → bez duplikatów), `decision export` (JSON wszystkich decyzji projektu do indeksowania), reguła w core-project-record („Odpowiedzi i decyzje człowieka”): decyzja z rozmowy albo bramki idzie przez to polecenie | `core/hooks/project_record.py`, `core/skills/core-project-record/` — po F0, osobny PR |
| F0 | Instalacja tf w pdi i ShipScope | osobne sesje w tamtych repo |
| F1 | Dopisek `Change: TSK-n`, hook commit-msg | `core/skills/core-conventional-commits`, `core-git-workflow` |
| F1 | Talos czyta cięcia z `plan.md` zmiany; raport do `changes/CHG/runs/TSK-n.md` | `modes/mode-talos/` |
| F2 | Rekonstrukcja z kodu i eksport w JSON | `docs/plans/2026-10-23-rekonstrukcja-z-kodu.md` (osobny plan, w toku) |
| F3 | Triaż z wejściem `PRB` w JSON (`contract/problem.schema.json`) i rekomendacją według schematu | `packs/pack-it/skills/proc-issue-triage`; stany pdi ↔ tf w `pdi/contract/README.md` |
| F4 | Uruchamianie person bez interakcji (`tf run <persona> --change CHG-12 --phase …`), stan „czeka na bramkę” | sygnał `gate.requested` do pdi |

## Polecenie startowe — F0 (wklej w nowej sesji w repo tf)

```text
Realizujemy F0 integracji tf z pdi według docs/plans/2026-10-23-integracja-pdi.md. Przeczytaj ten plik
(TL;DR, Przekazanie, „Kontekst z pdi”, „Zakres”) oraz w repo dbqm45/pdi: contract/README.md,
contract/change.schema.json i contract/examples/change.json (gałąź main albo claude/magical-dirac-wjvn8y,
jeśli kontrakt 0.3.0 nie jest jeszcze scalony).

Cel: dziennik per zmiana w core-project-record.
1. `project_record.py change new CHG-12 [--source PRB-34]` tworzy docs/project/changes/CHG-12/ z intent.md,
   plan.md i decisions.md z szablonów; nagłówek każdego pliku zgodny z contract/change.schema.json (pole change
   wymagane; source opcjonalne; tasks tylko w plan.md; status draft; version 1; created/updated = dziś). Klucze według
   wzorca [A-Z][A-Z0-9]+-[0-9]+; istniejący katalog → błąd bez nadpisywania.
2. `project_record.py check` sprawdza też artefakty w docs/project/changes/*/: brak change albo change różny od nazwy
   katalogu, nieznany artifact, tasks poza plan.md, zły kształt klucza → błąd z podpowiedzią.
3. Szablony intent, plan, decisions w core/skills/core-project-record/templates/change/ (osobny podkatalog —
   templates/plan.md i templates/decisions.md już istnieją dla dziennika projektu i zostają bez zmian; intent: problem, warianty, wybrany
   wariant, metryki sukcesu, poza zakresem; plan: cięcia TSK z wartością, plikami i weryfikacją; decisions: wpisy
   z id DEC-n — numer z rejestru pdi przez MCP record_decision z links.chg, jeśli serwer pdi jest podłączony; inaczej
   pole id puste do uzupełnienia).
4. SKILL.md core-project-record: krótka sekcja „Zmiana (CHG)” — kiedy dziennik per zmiana, a kiedy per projekt.

Zgoda człowieka: w zakresie punktów 1–4 możesz zmieniać core/hooks/project_record.py i
core/skills/core-project-record/. Nie zmieniaj settings.json ani factory/ poza tym, czego wymaga przebudowa.
claude-team-factory i ev-team-factory nietknięte.

Sposób pracy: plan (pliki, kolejność, testy) zapisany przed kodem; TDD w core/tests/test_project_record.py (najpierw
czerwony); bramki: `python3 tools/workspace.py check --packs all`, `python3 tools/workspace.py refs`,
`for t in tests/test_*.py; do python3 "$t" || exit 1; done`, w złożonym projekcie
`python3 factory/skill_gate.py core-project-record`. Jeśli CLI project_record.py jest publicznym API fabryki,
nowa komenda to wersja minor (core-semver); numer liczy semver.py, bez tagu. Punkt kontrolny wip.
Commit i PR — na moją prośbę; tytuł PR sprawdź scripts/check_commit_message.py.
Poza zakresem: F1–F4 (dopisek Change:, Talos, rekonstrukcja, triaż z pdi, tryb bez interakcji).
```

## Uwagi przed startem (2026-10-23)
- Szablony zmiany w `templates/change/` — bez kolizji z istniejącymi `templates/plan.md` i `templates/decisions.md`.
- `dbqm45/pdi` jest prywatne: dodać do sesji tylko do odczytu (add_repo) przed czytaniem kontraktu.
- `tools/workspace.py check --packs all` trwa kilka minut — uruchomić w tle z długim limitem czasu.

## Zasada zgodności wstecz
Fabryka działa jak dotąd: nowe polecenia są dodatkowe, `check` zaostrza się tylko dla `docs/project/changes/`,
a wypychanie do pdi działa wyłącznie, gdy serwer MCP pdi jest podłączony. Projekt bez pdi i bez dziennika zmian
nie widzi różnicy.

## Kryteria „gotowe” dla F0
- `change new` tworzy katalog z trzema plikami; każdy nagłówek przechodzi walidację względem
  `pdi/contract/change.schema.json` (test z kopią przykładu `contract/examples/change.json` albo sprawdzenie ręczne).
- `check` wykrywa co najmniej: brak `change`, niezgodność z nazwą katalogu, `tasks` poza `plan.md`, zły klucz.
- Bramki zielone.

## Otwarte pytania
1. Skąd tf bierze numer `DEC-n` dla decyzji o zmianie, zanim pdi będzie usługą? Propozycja: z serwera MCP pdi
   (`record_decision` z `links.chg`) — działa już u właściciela; bez serwera pole puste. → właściciel
2. Czy prefiksy kluczy (D3: konfigurowalne) mają być ustawieniem tf, czy tylko pdi? Na F0 wystarczą domyślne.
   → właściciel, przy F1
