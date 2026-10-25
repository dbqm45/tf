# Plan: tf w jednym flow SDLC z pdi

Data: 2026-10-23 · Status: **do startu** (F0 w tf) · Gałąź z planem: `claude/magical-dirac-wjvn8y`

## TL;DR
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

Kontrakt 0.3.0 jest na `main` w pdi (scalony 2026-10-23).

**Decyzje pdi wiążące dla tf:**
- **D2/R1 — podział rejestru decyzji:** decyzje o konkretnej zmianie (B1–B6, odpowiedzi na pytania ci_for_sdlc)
  mają źródło prawdy w repo projektu, w `docs/project/changes/CHG-n/decisions.md`; pdi je indeksuje. Decyzje bez
  zmiany (triaż, odrzucenia) żyją w pdi.
- **R7 — stany zgłoszenia:** biznesowe w pdi (`new`, `clarifying`, `ready_for_triage`, `accepted`, `rejected`,
  `parked`, `duplicate`); tf **nie** dostaje tych stanów, tłumaczenie tylko na granicy (tabela w kontrakcie).
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
| F0 | Instalacja tf w pdi i ShipScope | osobne sesje w tamtych repo |
| F1 | Dopisek `Change: TSK-n`, hook commit-msg | `core/skills/core-conventional-commits`, `core-git-workflow` |
| F1 | Talos czyta cięcia z `plan.md` zmiany; raport do `changes/CHG/runs/TSK-n.md` | `modes/mode-talos/` |
| F2 | Rekonstrukcja z kodu i eksport w JSON | `docs/plans/2026-10-23-rekonstrukcja-z-kodu.md` (osobny plan, w toku) |
| F3 | Triaż z wejściem `PRB` w JSON (`contract/problem.schema.json`) i rekomendacją według schematu | `packs/pack-it/skills/proc-issue-triage`; **tf zachowuje swoje stany** — przy triażu dla pdi rekomendacja w stanach pdi wg tabeli w `pdi/contract/README.md` (decyzja R7 w pdi) |
| F4 | Uruchamianie person bez interakcji (`tf run <persona> --change CHG-12 --phase …`), stan „czeka na bramkę” | sygnał `gate.requested` do pdi |

## Polecenie startowe — F0 (wklej w nowej sesji w repo tf)

```text
Realizujemy F0 integracji tf z pdi według docs/plans/2026-10-23-integracja-pdi.md. Przeczytaj ten plik
(TL;DR, Przekazanie, „Kontekst z pdi”, „Zakres”) oraz w repo dbqm45/pdi: contract/README.md,
contract/change.schema.json i contract/examples/change.json (gałąź main).

Cel: dziennik per zmiana w core-project-record.
1. `project_record.py change new CHG-12 [--source PRB-34]` tworzy docs/project/changes/CHG-12/ z intent.md,
   plan.md i decisions.md z szablonów; nagłówek każdego pliku zgodny z contract/change.schema.json (pole change
   wymagane; source opcjonalne; tasks tylko w plan.md; status draft; version 1; created/updated = dziś). Klucze według
   wzorca [A-Z][A-Z0-9]+-[0-9]+; istniejący katalog → błąd bez nadpisywania.
2. `project_record.py check` sprawdza też artefakty w docs/project/changes/*/: brak change albo change różny od nazwy
   katalogu, nieznany artifact, tasks poza plan.md, zły kształt klucza → błąd z podpowiedzią.
3. Szablony intent, plan, decisions w core/skills/core-project-record/templates/ (intent: problem, warianty, wybrany
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

## Polecenie startowe — G2.4 (autor historyjek; plan G1/G2 w pdi)

Krok G2.4 z planu G1/G2 (pdi: `docs/plan-g1-g2.md`; kontrakt 0.4.0 z zestawem wzorcowym
`contract/fixtures/story-shape/` jest na `main` pdi). Niezależny od F0 — może iść przed nim albo po nim.
Źródło polecenia: pdi `docs/polecenia-startowe-fala-2.md`.

```text
Realizujemy krok G2.4 planu G1/G2 z repo dbqm45/pdi (docs/plan-g1-g2.md, §4.2 reguły, §4.5 zmiany w tf, §4.7 kroki).
Przeczytaj też w pdi (main, kontrakt 0.4.0): contract/README.md (sekcja „Konwencje”) i cały katalog
contract/fixtures/story-shape/ (README.md — jak oznaczono przypadki; stories.json; expected.json; vocabulary.json).

Cel: wymagania pisane z agentem mają GWT, jedną ścieżkę na historyjkę i identyfikatory AC; Talos nie zaczyna
historyjki, która miesza ścieżki.

1. Zestaw wzorcowy: skopiuj contract/fixtures/story-shape/ z pdi do packs/pack-it/tests/fixtures/pdi-story-shape/
   (z plikiem VERSION = 0.4.0). Nie zmieniaj etykiet w kopii — rozbieżność z expected.json to błąd lintera albo
   zgłoszenie do pdi (zmiana kontraktu), nie poprawka kopii.
2. requirements_lint.py (packs/pack-it/skills/proc-requirements-shaping/scripts/):
   - wydziel funkcję sprawdzającą pojedynczą historyjkę (tytuł, opis, surowe AC, opcjonalnie story points) i używaj
     jej przy lincie pliku requirements.md;
   - słowa kluczowe GWT z vocabulary.json, w tym brakujące dziś polskie warianty (Zakładając, że / Mając / Kiedy /
     Jeżeli / Jeśli / Oraz / I / Ale);
   - nowe sprawdzenia z identyfikatorami reguł kontraktu: AC-001 (scenariusz bez Then/Wtedy, AC poza formatem),
     AC-002 (słaby wynik z weak_results), AC-004 (druga akcja w scenariuszu), STORY-001 (kilka akcji: spójniki
     w tytule/celu, kilku aktorów, różne akcje główne w scenariuszach), STORY-003 (tytuł od warstwy);
     istniejące LEAK_PATTERNS jako AC-003 z rozszerzeniem z vocabulary.json (tabela, kolumna, endpoint);
     STORY-002 tylko z liczby scenariuszy i akcji (bez estymaty);
   - nowe problemy jako ostrzeżenia (kod 0); --strict zamienia je w kod 1. Istniejące zachowanie bez zmian.
3. Test w packs/pack-it/tests/: na kopii zestawu, z polityką z expected.json (i nadpisaniami policy w przypadkach),
   dla reguł zaimplementowanych w tf wynik ma się zgadzać z expected.json; raportuj precyzję i czułość per reguła
   (cel z planu §4.8: precyzja ≥ 0,8, czułość ≥ 0,7). Liczba jednostek AC zgodna z polem scenarios.
4. Skille: proc-requirements-shaping (faza 4: każda US-NN ma ≥ 1 scenariusz AC-n w GWT i jedną akcję; więcej akcji →
   podział wg mapa-i-dzielenie.md), proc-agile/references/mapa-i-dzielenie.md (sekcja „Sygnały, że historyjka
   miesza funkcjonalności” — te same sygnały co STORY-001…003), talos-story-run (§1 Przyjęcie: lint historyjki;
   z --auto historyjka łamiąca STORY-001 kończy się blokiem STOP z propozycją podziału), qa-spec-first-testing
   (test akceptacyjny nazwany identyfikatorem scenariusza, np. US-02/AC-3).

Zasady repo tf: plan (pliki, kolejność, testy) zapisany przed kodem; TDD (najpierw czerwony test); skille zmieniasz
wg core-skill-authoring (najpierw scenariusze ewaluacji), płatne ewaluacje tylko za moją zgodą; claude-team-factory
i ev-team-factory nietknięte. Bramki: python3 tools/workspace.py check --packs all; python3 tools/workspace.py refs;
for t in tests/test_*.py; do python3 "$t" || exit 1; done; skill_gate dla zmienionych skilli w złożonym projekcie;
tytuł PR: python3 scripts/check_commit_message.py "<tytuł>". Commit i PR — na moją prośbę.
Poza zakresem: G1.1 (plan wydania) i reguły REL; zmiany w kontrakcie pdi.
```

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
