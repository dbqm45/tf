# Plan: tf w jednym flow SDLC z pdi

Data: 2026-10-23 · Status: **zrobione** (F0–F5 w tf; stan na 2026-10-27 w „Stan realizacji”) · Gałąź z planem: `claude/magical-dirac-wjvn8y`

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

## Stan realizacji (2026-10-27)
Wszystkie kroki tf z planu jednego flow są na `main`: F0 i F0b (`decision_record.py`: `change new`, `check`,
`decision add/pending/mark/export/gate`), F1 (#80), F2 (#83), F3 (#82, #84, #87), F4 (#79), F5 (#81, pasma kontrolne
→ `metric.breached`) i z F6 AI review w CI (#86) oraz fazę designu z tabelą ramek Figmy (#94); kopie kontraktu pdi są generowane z tagu wydania (#93). Doszły kroki z planu G1/G2 pdi (G1.1 #78, G2.4 #77), data
zgłoszenia w nagłówku zmiany (#85) i kolumny planu zmiany dla samokontroli REL-008 (#89). Stan całego ekosystemu,
także luk G1–G8: pdi `docs/plan-jeden-flow-sdlc.md`, §8. Prognoza „kiedy to będzie” (G3, decyzja D-E1) liczy się
w pdi z liczby cięć planu tf i czasu przepływu z ShipScope, więc tf nie potrzebuje do niej zmian.

## Przekazanie (jak wznowić)
1. Przeczytaj ten plik i `git status` w repo tf.
2. Plan jest zrobiony; nowe kroki tf wynikają z planów w pdi (`docs/plan-jeden-flow-sdlc.md` §8,
   `docs/plan-automatyzacja-i-konsola.md` §8: m.in. A7 `review.light`, faza designu przez Figma MCP, evale flow).
   „Polecenie startowe — F0” niżej zostaje jako zapis.
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
| **F0** | Dziennik per zmiana: `change new <CHG> [--source <PRB>]`, szablony `intent`, `plan`, `decisions`; `check` waliduje nagłówki w `changes/` — **zrobione** (`decision_record.py`) | `modes/mode-pdi/` (patrz „Architektura”) |
| **F0b** | Zapis i wypychanie decyzji z dowolnego narzędzia: `decision_record.py decision add --change CHG-n "…"` (skrypt trybu) (wpis w `decisions.md`; gdy serwer MCP pdi podłączony — od razu `record_decision` i numer `DEC-n`), kolejka bez połączenia (wpis „niewysłane”, `decision sync` wysyła później, stały identyfikator wpisu → bez duplikatów), `decision export` (JSON wszystkich decyzji projektu do indeksowania), reguła w skillu trybu: decyzja z rozmowy albo bramki idzie przez to polecenie | `modes/mode-pdi/` — **zrobione** (`decision add/pending/mark/export`) |
| F0 | Instalacja tf w pdi i ShipScope | osobne sesje w tamtych repo |
| F1 | Dopisek `Change: TSK-n`, hook commit-msg — **zrobione 2026-10-26** jako `commit_msg.py` (`check`, `install`) w core-conventional-commits (plan: `docs/plans/2026-10-26-f1-slad-w-commitach.md`) | `core/skills/core-conventional-commits`, `core-git-workflow` |
| F1 | Talos czyta cięcia z `plan.md` zmiany; raport do `changes/CHG/runs/TSK-n.md` — **zrobione 2026-10-26** (`run_report.py start --task`, `finish`) | `modes/mode-talos/` |
| F2 | Rekonstrukcja z kodu i eksport w JSON — **eksport zrobiony 2026-10-26** jako `recon_export.py` → `reconstruction.json` (plan: `docs/plans/2026-10-26-f2-eksport-rekonstrukcji.md`) | `docs/plans/2026-10-23-rekonstrukcja-z-kodu.md` |
| F3 | Triaż z wejściem `PRB` w JSON (`contract/problem.schema.json`) i rekomendacją według schematu — **zrobione 2026-10-26** jako `triage_pdi.py` (`check`, `recommend`) w `mode-pdi` (plan: `docs/plans/2026-10-26-f3-triaz-prb.md`) | `packs/pack-it/skills/proc-issue-triage`; stany pdi ↔ tf w `pdi/contract/README.md` |
| F4 | Uruchamianie person bez interakcji, stan „czeka na bramkę”, `gate.requested` do pdi, szablon `sdlc-phase.yml` — **zrobione 2026-10-26** jako `phase_run.py` w `mode-pdi` (plan: `docs/plans/2026-10-26-f4-uruchamianie-faz.md`) | `modes/mode-pdi/` |
| F5 | Pasma kontrolne na metrykach PROD z ShipScope → `metric.breached` do pdi — **zrobione 2026-10-26** jako `metric_watch.py` i szablon `metric-watch.yml` (plan: `docs/plans/2026-10-26-f5-pasma-kontrolne.md`) | `modes/mode-pdi/` |
| F6 | AI review pull requestów w CI według `REVIEW.md` — **zrobione** (#86, plan: `docs/plans/2026-10-26-przeglad-ai-w-ci.md`); faza designu z tabelą ramek Figmy i `design_check.py` — **zrobione** (#94, plan: `docs/plans/2026-10-27-faza-design-figma.md`; zostaje próba na prawdziwym pliku Figmy); evale flow — do zrobienia | `core/`, `modes/mode-pdi/`, `packs/pack-ux/` |

## Polecenie startowe — F0 (wklej w nowej sesji w repo tf)

```text
Realizujemy F0 integracji tf z pdi według docs/plans/2026-10-23-integracja-pdi.md. Przeczytaj ten plik
(TL;DR, Przekazanie, „Kontekst z pdi”, „Zakres”) oraz w repo dbqm45/pdi: contract/README.md,
contract/change.schema.json i contract/examples/change.json (gałąź main albo claude/magical-dirac-wjvn8y,
jeśli kontrakt 0.3.0 nie jest jeszcze scalony).

Cel: nowy opcjonalny tryb `modes/mode-pdi/` (kind: mode, default: false) z dziennikiem per zmiana; rdzeń
(core/hooks/project_record.py, core-project-record) bez zmian. Najpierw obejrzyj modes/mode-talos/ jako wzór trybu
(pack.yaml, skills/, hooks/, tests/) i sprawdź, jak tryb wnosi skrypt i test.
1. `python3 .claude/hooks/decision_record.py change new CHG-12 [--source PRB-34]` (skrypt trybu) tworzy
   docs/project/changes/CHG-12/ z intent.md, plan.md i decisions.md z szablonów trybu; nagłówek każdego pliku zgodny
   z contract/change.schema.json (pole change wymagane; source opcjonalne; tasks tylko w plan.md; status draft;
   version 1; created/updated = dziś). Klucze według wzorca [A-Z][A-Z0-9]+-[0-9]+; istniejący katalog → błąd bez
   nadpisywania.
2. `decision_record.py check` waliduje artefakty w docs/project/changes/*/: brak change albo change różny od nazwy
   katalogu, nieznany artifact, tasks poza plan.md, zły kształt klucza → błąd z podpowiedzią.
3. Szablony intent, plan, decisions w skillu trybu (np. modes/mode-pdi/skills/pdi-decisions/templates/) — intent:
   problem, warianty, wybrany wariant, metryki sukcesu, poza zakresem; plan: cięcia TSK z wartością, plikami
   i weryfikacją; decisions: wpisy z id DEC-n — numer z rejestru pdi przez MCP record_decision z links.chg; bez
   podłączonego serwera pole id puste, wpis oznaczony „niewysłane”.
4. SKILL.md trybu: kiedy dziennik per zmiana; decyzja z rozmowy lub bramki → zapis lokalny + record_decision przez
   MCP; brak serwera pdi → nie wypychaj, zgłoś. Scenariusze ewaluacji przed treścią (core-skill-authoring).

Zgoda człowieka: tworzysz nowy katalog modes/mode-pdi/ (pack.yaml, skill, skrypt, testy, GUIDE.md). Rdzenia, innych
nakładek, settings.json ani factory/ nie zmieniasz. claude-team-factory i ev-team-factory nietknięte.

Sposób pracy: plan (pliki, kolejność, testy) zapisany przed kodem; TDD w modes/mode-pdi/tests/ (najpierw czerwony);
bramki: `python3 tools/workspace.py check --packs all` (w tle, długi limit czasu), `python3 tools/workspace.py refs`,
`for t in tests/test_*.py; do python3 "$t" || exit 1; done`, w złożonym projekcie
`python3 factory/skill_gate.py <skill trybu>`. Wersja trybu 0.1.0 w pack.yaml. Punkt kontrolny wip.
Commit i PR — na moją prośbę; tytuł PR sprawdź scripts/check_commit_message.py.
Poza zakresem: F0b (decision add/sync/export), F1–F4.
```

## Uwagi przed startem (2026-10-23)
- Szablony zmiany w `templates/change/` — bez kolizji z istniejącymi `templates/plan.md` i `templates/decisions.md`.
- `dbqm45/pdi` jest prywatne: dodać do sesji tylko do odczytu (add_repo) przed czytaniem kontraktu.
- `tools/workspace.py check --packs all` trwa kilka minut — uruchomić w tle z długim limitem czasu.

## Architektura: osobna nakładka `mode-pdi` (decyzja właściciela 2026-10-23)
Fabryka bez nakładki działa dokładnie jak dotąd; wszystko, co dotyczy decyzji i pdi, żyje w opcjonalnym trybie
`modes/mode-pdi/` (`kind: mode`, `default: false`), instalowanym `tf add pdi` i usuwanym `tf remove pdi`.
- **Rdzeń bez zmian:** `core/hooks/project_record.py` i `core-project-record` zostają nietknięte. Dziennik zmiany
  (`changes/CHG-n/`), szablony i polecenia `change new`, `decision add/sync/export` oraz walidacja `changes/` są we
  własnym skrypcie trybu (np. `modes/mode-pdi/hooks/decision_record.py`) i jego skillu (np. `pdi-decisions`).
- **Aktywacja:** tryb działa, gdy serwer MCP pdi jest skonfigurowany (np. `.mcp.json` projektu); bez niego
  `tf doctor` zgłasza brak, a skill nie wypycha decyzji.
- **Podział pracy:** skrypt zapisuje lokalnie, waliduje i prowadzi kolejkę „niewysłane”; model (wg skilla) woła
  `record_decision` przez MCP i wpisuje zwrócony `DEC-n`. Zapis bez modelu (np. z CI) wymagałby API HTTP/CLI w pdi —
  pytanie do pdi, nie teraz.
- **Granice:** `tools/workspace.py refs` — rdzeń i inne nakładki nie znają nazwy trybu; integracje z Talosem (F1)
  tylko przez konwencję ścieżek (Talos czyta `docs/project/changes/<CHG>/plan.md`, jeśli istnieje), bez nazw skilli.
- **Do sprawdzenia przy F0:** jak nakładka dokłada polecenia do `tf doctor` i czy tryb może wnosić skrypt
  w `hooks/` bez wpisu w `settings.json` (skrypt wołany ręcznie/przez skill, nie jako hook zdarzeń).

## Zasada zgodności wstecz
Fabryka działa jak dotąd: nowe polecenia są dodatkowe, `check` zaostrza się tylko dla `docs/project/changes/`,
a wypychanie do pdi działa wyłącznie, gdy serwer MCP pdi jest podłączony. Projekt bez pdi i bez dziennika zmian
nie widzi różnicy.

## Plan kroku F0 (2026-10-23, przed kodem)
Kontrakt: `pdi/contract/` 0.3.0 na `main` pdi (gałąź `claude/magical-dirac-wjvn8y` bez różnic w `contract/`).
Pliki (kolejność):
1. `modes/mode-pdi/tests/skill_evals/pdi-decisions.json` — scenariusze (≥2 trigger, ≥1 no-trigger).
2. `modes/mode-pdi/tests/test_decision_record.py` — testy skryptu (czerwone): `change new` tworzy 3 pliki z nagłówkiem
   zgodnym z `change.schema.json`; istniejący katalog → błąd; zły klucz → błąd; `check` wykrywa: brak `change`,
   `change` ≠ katalog, nieznany `artifact`/`phase`/`status`, nieznane pole, `tasks` poza `plan.md`, zły klucz, zła data.
3. `modes/mode-pdi/skills/pdi-decisions/scripts/decision_record.py` (stdlib) + `templates/{intent,plan,decisions}.md`.
4. `modes/mode-pdi/skills/pdi-decisions/SKILL.md` — kiedy dziennik zmiany; decyzja → wpis lokalny + `record_decision`
   przez MCP pdi; bez serwera pdi: nie wypychaj, zgłoś.
5. `modes/mode-pdi/pack.yaml` (kind: mode, 0.1.0, default: false, core >=5.6.0 <6.0.0, skill dla wszystkich person
   przez `contributes`), `settings.json` (uprawnienie dla skryptu), `GUIDE.md`, `tests/test_mode_pdi.py`.
6. `.github/workflows/factory-checks.yml` — `mode-pdi` w macierzy.
Bramki: `workspace.py check --packs mode-pdi`, `--packs all`, `refs`, `tests/test_*.py`, `skill_gate.py pdi-decisions`
+ `--hints`, `sync-gate`. Bez płatnej ewaluacji.

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
