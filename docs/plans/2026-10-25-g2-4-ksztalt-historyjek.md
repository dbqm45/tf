# Plan: G2.4 — kształt historyjek (GWT, jedna ścieżka, identyfikatory AC)

Data: 2026-10-25 · Status: zrobione (kroki 1–6), commit i PR na prośbę człowieka · Gałąź: `claude/great-hypatia-angvam`
Źródło: pdi `docs/plan-g1-g2.md` (§4.2 reguły, §4.5 zmiany w tf, §4.7 kroki, §4.8 cel), kontrakt pdi 0.4.0
(`contract/README.md` „Konwencje”, `contract/fixtures/story-shape/`). Poza zakresem: G1.1 i reguły REL, zmiany kontraktu.

## TL;DR
`requirements_lint.py` dostaje funkcję `check_story()` dla jednej historyjki (tytuł, opis, surowe AC, opcjonalnie
story points) z regułami kontraktu AC-001…004 i STORY-001…003. Lint pliku `requirements.md` używa jej dla każdej
historyjki `US-NN`; nowe problemy są ostrzeżeniami (kod 0), `--strict` zamienia je w kod 1. Test na kopii zestawu
wzorcowego pdi porównuje wynik z `expected.json` i raportuje precyzję i czułość per reguła. Skille: faza 4
proc-requirements-shaping, sygnały mieszania w mapa-i-dzielenie.md, przyjęcie historyjki w talos-story-run, nazwa
testu akceptacyjnego w qa-spec-first-testing.

## Decyzje
- **Słownik:** kopia `vocabulary.json` obok skryptu (`scripts/story_shape_vocabulary.json`), bo zainstalowany skill
  nie widzi `tests/`. Test pilnuje, że jest identyczna z kopią zestawu (`tests/fixtures/pdi-story-shape/`).
- **Kopia zestawu** bez zmian etykiet; `VERSION` = 0.4.0. Rozbieżność z `expected.json` = błąd lintera albo
  zgłoszenie do pdi.
- **STORY-002 bez estymaty** (decyzja człowieka): tylko liczba scenariuszy > `maxScenarios` albo akcji >
  `maxActions`. Przypadki, w których `expected.json` oczekuje STORY-002 wyłącznie ze story points (SS-07, SS-31),
  test wyłącza z porównania i wypisuje jako „niezaimplementowane w tf”. `check_story` przyjmuje story points, ale
  ich nie ocenia.
- **AC-003 w pliku:** istniejące `LEAK_PATTERNS` zostają blokujące (kod 1, jak dziś), oznaczone AC-003. Kategorie
  nowe w kontrakcie (struktura danych: tabela/kolumna; interfejs techniczny: endpoint) — ostrzeżenie. W historyjce
  pliku AC-003 nie jest liczone drugi raz.
- **Format historyjki w pliku:** blok `### US-NN: <tytuł>` z linią „Jako … chcę …” i scenariuszami `- AC-n:` w GWT;
  wiersz tabeli `| US-NN | historia | kryteria | … |` nadal czytany. Brak identyfikatorów `AC-n` w bloku → ostrzeżenie
  (reguła tf, nie kontraktu).
- **Jedna historyjka z CLI:** `--story PLIK` (np. `story.md` Talosa: `# tytuł`, opis, kryteria) — dla talos-story-run.
  Wynik wypisuje różne akcje główne jako podstawę propozycji podziału.
- **Talos** wymaga tylko rdzenia, więc lint uruchamia warunkowo (gdy skrypt jest zainstalowany, pack-it).

## Kolejność i testy
1. Kopia zestawu + `VERSION` (bez kodu).
2. Czerwone testy:
   - `packs/pack-it/tests/test_story_shape.py` — zestaw wzorcowy: zgodność z `expected.json` dla reguł tf,
     liczba jednostek AC = `scenarios`, precyzja i czułość per reguła (cel §4.8: ≥ 0,8 / ≥ 0,7), słownik obok
     skryptu = słownik zestawu, `VERSION` = `contract_version`.
   - `test_requirements_lint.py` — nowe przypadki: historyjka `US-NN` łamiąca STORY-001 w pliku → ostrzeżenie
     i kod 0, z `--strict` kod 1; tabela/kolumna w FR → ostrzeżenie AC-003 (nie blokuje); `--story` na pliku
     Talosa; GOOD bez ostrzeżeń także z `--strict`; polskie warianty (Mając/Kiedy) w gotowości.
3. Kod: słownik obok skryptu, parser jednostek AC, `check_story`, historyjki z pliku, `--strict`, `--story`.
4. Scenariusze ewaluacji (przed treścią): proc-requirements-shaping, proc-agile (mapa-i-dzielenie),
   qa-spec-first-testing; talos-story-run ma `disable-model-invocation` — tylko scenariusze no-trigger, więc
   zmianę Talosa pilnuje test treści w `modes/mode-talos/tests/test_mode_talos.py`.
5. Treść skilli.
6. Bramki: `python3 tools/workspace.py check --packs all`, `refs`, `tests/test_*.py`, `skill_gate` zmienionych skilli
   w złożonym projekcie, `scripts/check_commit_message.py`.
