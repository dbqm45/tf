# Plan: faza projektowania z Figmą (etap 07 flow, F6)

Data: 2026-10-27 · Status: kroki 1–3 zrobione (pdi #41, tf #94, ci_for_sdlc #87); krok 4 czeka na plik Figmy (D-F3) · Decyzje D-F1, D-F2 przyjęte · Gałąź: `claude/great-hypatia-angvam`
Źródło: pdi `docs/plan-jeden-flow-sdlc.md` §2 etap 07 („Design [B] — tf + Figma MCP — ramki per journey i stan, linki
w `design.md`”) i §F6 („tf: faza designu przez Figma MCP”; „ci_for_sdlc: porównanie ekranów z ramkami Figmy”).

## TL;DR
Faza `design` w tf już istnieje, ale kończy się prozą: persona `natalia` opisuje przepływy, stany i „linki do makiet”
w `design.md`, a nikt nie sprawdza, czy każde wymaganie z interfejsem ma ramkę dla każdego stanu. ci_for_sdlc łączy
ramki Figmy z wymaganiami tylko po podobieństwie treści. Plan: (1) `design.md` dostaje maszynowo czytelną tabelę
**wymaganie → ścieżka → stan → ramka (link Figmy z `node-id`)**, której format trafia do kontraktu pdi; (2) skill
pack-ux opisuje pracę z Figma MCP w dwóch trybach — **linkowanie ramek projektanta** (domyślnie) i **szkic ramek
przez agenta** (za zgodą, do poprawy przez projektanta); (3) skrypt sprawdza pokrycie przed bramką `design-review`;
(4) ci_for_sdlc czyta tabelę i bierze ramki z linków zamiast zgadywać.

## Stan dziś (sprawdzone 2026-10-27)
- tf `modes/mode-pdi/skills/pdi-decisions/scripts/phase_run.py`: faza `design` → persona `natalia`, artefakt
  `design.md`, bramka `design-review`; prompt: „projekt doświadczenia: przepływy, stany, makiety kluczowych ekranów
  i linki do nich”. Brak szablonu `design.md` w `templates/` (są `intent.md`, `plan.md`, `release.yaml`…).
- tf pack-ux: `ux-feature-design` (przepływy ze stanami, handoff z tabelą stanów), `ux-visual-design`,
  `ux-design-systems` wspominają Figmę (zmienne do kodu, auto layout), ale bez procedury Figma MCP.
- ci_for_sdlc: konektor Figmy (`connectors/figma.ts`, REST, ramki najwyższego poziomu z tekstami i przejściami),
  analiza stanów (`analysis/states.ts`: stany wymagane z wymagań vs stany znalezione w ramkach); konektor repo
  (`connectors/repo.ts`) czyta `intent.md`, `plan.md`, `release.yaml` — `design.md` nie.
- Kontrakt pdi: `change.schema.json` zna `design` jako fazę; formatu treści `design.md` nie ma.

## Zakres

### 1. Format `design.md` (kontrakt pdi 0.9.0)
Nagłówek jak inne artefakty zmiany (`artifact: design`, `change`, `phase`, `status`), w treści tabela:

| Wymaganie | Ścieżka | Stan | Ramka | Uwagi |
|---|---|---|---|---|
| US-3 / AC-2 | zmiana taryfy zbiorczo | błąd częściowy | https://www.figma.com/design/KEY/Plik?node-id=12-34 | 3 z 200 ładowarek offline |

- Stany ze stałej listy (zgodnej z `STATE_PATTERNS` ci_for_sdlc — do uzgodnienia w kroku 1): `idle`, `loading`,
  `empty`, `error`, `partial`, `success`, `disabled`, `offline`… Stan „nie dotyczy” zapisany wprost z powodem.
- Link musi mieć `fileKey` i `node-id`; bez ramki — `brak` i pytanie w „Uwagach” (bramka tego nie przepuści).
- W kontrakcie: opis formatu w README („Artefakt zmiany”) + przykład `examples/design.md` + reguły parsowania;
  konsumenci synchronizują jak schematy (tf `tools/pdi-contract.json`, ci_for_sdlc `scripts/pdi-contract.json`).

### 2. Skill (pack-ux): praca z Figma MCP
Nowa sekcja w `ux-feature-design` (albo osobny `references/figma-mcp.md`), scenariusze ewaluacji najpierw:
- **Tryb A — linkowanie (domyślny):** projektant robi ramki; agent przez Figma MCP czyta plik (`get_metadata`,
  `get_screenshot`), dopasowuje ramki do wymagań i stanów, wypełnia tabelę, wskazuje brakujące stany jako pytania.
- **Tryb B — szkic przez agenta (za zgodą):** agent zakłada ramki per ścieżka i stan z komponentów i tokenów systemu
  projektowego (`search_design_system`, `use_figma` wg skilla `figma-use`), oznacza je jako szkic; projektant
  poprawia, dopiero potem bramka. Nigdy nie nadpisuje ramek projektanta.
- **Bez Figmy:** tabela z opisem stanów i makietą tekstową, ramka `brak` — faza działa, bramka pokazuje braki.
- Granice: dostępność ramek (ux-accessibility), treści (ux-content-design), tokeny (ux-design-systems).

### 3. Sprawdzenie przed bramką (tf, mode-pdi)
`design_check.py changes/CHG-n` (TDD): każde wymaganie z interfejsem z `requirements.md` ma wiersze dla stanów
wymaganych (lista minimalna: `idle`, `success`, `error`; plus stany wynikające z wymagania, np. `empty`, `loading`);
linki poprawne (domena figma.com, `node-id`); brak duplikatów. Wynik w raporcie fazy i w prośbie o bramkę
(`gate.requested` z listą braków jako pytaniami). Szablon `templates/design.md`, prompt fazy w `phase_run.py`.

### 4. ci_for_sdlc: ramki z linków
Konektor repo czyta tabelę z `design.md` → jawne powiązania wymaganie ↔ ramka (`fileKey`, `node-id`); konektor
Figmy pobiera te ramki; analiza stanów używa ich z pewnością wysoką zamiast dopasowania po treści. Reguła: stan
wymagany bez ramki → luka z pytaniem do skrzynki pdi (etap 08).

## Kolejność
1. pdi: format `design.md` w kontrakcie 0.9.0 (przykład, reguły, lista stanów uzgodniona z ci_for_sdlc), tag.
2. tf: kopia przykładu, szablon, `design_check.py` (TDD), prompt fazy, skill pack-ux (scenariusze → treść → bramka).
3. ci_for_sdlc: parsowanie tabeli w konektorze repo, ramki z linków, reguła brakującego stanu (TDD).
4. Próba na prawdziwym pliku Figmy (tryb A, potem B) — wymaga konta i pliku wskazanego przez człowieka.

## Ustalenia z realizacji
- Stany minimalne (`idle`, `success`, stan błędu) liczone **per historyjka**: `US-3`, `US-3/AC-2` i `US-3/AC-3`
  to jeden przepływ; wymaganie ich od każdego kryterium dawałoby fałszywe braki.
- `design.md` bywa też miejscem ADR z fazy architektury — parser bierze pierwszą tabelę z nagłówkiem ramek,
  reszta pliku nie przeszkadza.
- Kontrakt 0.9.0 (pdi): `conventions.design`, `design-links.schema.json`, para przykładów i parser referencyjny
  `pdi.design`; tf ma własny parser w `design_check.py` sprawdzany tą samą parą.

## Decyzje (przyjęte 2026-10-27: D-F1 i D-F2 wg rekomendacji)
- **D-F1 Tryb domyślny:** A (agent linkuje ramki projektanta) czy B (agent szkicuje ramki)? Rekomendacja: A
  domyślnie, B na żądanie — ramki agenta bez projektanta łatwo uznać za gotowy projekt.
- **D-F2 Miejsce formatu:** kontrakt pdi (rekomendacja; spójne z decyzją z 2026-10-27 o jednym źródle formatów)
  czy tylko tf.
- **D-F3 Plik do próby:** konto i plik Figmy do weryfikacji kroku 4 (serwer Figma MCP jest dostępny w sesji;
  bez pliku kroki 1–3 da się zrobić i przetestować na danych przykładowych).
