# Plan: F2 w tf — eksport rekonstrukcji z kodu w JSON

Data: 2026-10-26 · Status: zrobione (kroki 1–5), commit i PR na prośbę człowieka · Gałąź: `claude/great-hypatia-angvam`
Źródło: pdi `docs/plan-jeden-flow-sdlc.md` §5 (wiersz F2: „Eksport rekonstrukcji w JSON — obok `rules.md`,
`requirements.md`, `domain.md`: te same treści z dowodami `plik:linia`; źródło dla ci_for_sdlc”) i „F2 — Spójność na
repo” (ci_for_sdlc: konektor wyniku rekonstrukcji tf — reguły i wymagania z kodu jako „stan obecny”); tf
`docs/plans/2026-10-23-rekonstrukcja-z-kodu.md` (układ `docs/project/00-reconstruction/`). Poza zakresem: konektor
po stronie ci_for_sdlc, kontrakt pdi (eksport jest formatem tf → ci_for_sdlc, nie pdi).

## TL;DR
`recon_export.py <katalog-rekonstrukcji> [--repo DIR]` zapisuje `reconstruction.json` obok `rules.md`: reguły,
wymagania i pozycje słownika domeny z tych samych plików Markdown, każda z dowodami rozbitymi na plik i linie,
cytatem, pewnością, stanem (dowód / założenie / niezweryfikowane / pytanie), sekcją i stabilnym identyfikatorem z treści
(nie zmienia się, gdy przesuną się linie). Z `--repo` każdy dowód ma `verified` (plik i linia istnieją, cytat
pasuje ±2 linie). Moduły z kart `modules/*.json`, commit z `manifest.json`. `recon_refresh.py finish` odświeża eksport,
gdy już istnieje; skill rekonstrukcji tworzy go w kroku raportu.

## Decyzje
- **Źródło:** pliki Markdown, które czyta człowiek (te same treści — wymóg planu). Format punktów jest już ustalony
  i sprawdzany przez `recon_check.py` (dowód `plik:linia`, cytat w "…" albo „…”, `(pewność: …)`, znaczniki) —
  eksport używa tych samych wyrażeń, więc oba narzędzia widzą to samo.
- **Wiersze tabel** (słownik w `domain.md`) to pozycje z polem `cells` (nagłówek → wartość).
- **Identyfikator:** `<rodzaj>-<10 znaków sha1>` z pliku i treści bez dowodów; powtórzona treść dostaje sufiks.
  ci_for_sdlc może dzięki temu śledzić regułę między odświeżeniami.
- **Schemat:** `reconstruction-export.schema.json` obok skryptu (format tf, wersja 1); test sprawdza wynik jego polami.
- **Bez modelu i bez sieci;** tylko biblioteka standardowa. Kod wyjścia: 0, 2 — brak katalogu.

## Kolejność i testy
1. Czerwone testy `packs/pack-it/tests/test_recon_export.py`: reguły z sekcji modułów (moduł z nagłówka), wymagania
   z pewnością i znacznikiem `[założenie]`, słownik z wypunktowań i tabeli, dowód zakresu `a-b`, kilka dowodów
   w punkcie, `verified` true/false z `--repo`, identyfikator stały po przesunięciu linii, commit z manifestu,
   moduły z kart, `--out`, brak katalogu → 2, wynik zgodny z polami schematu;
   `test_recon_refresh.py`: `finish` odświeża istniejący `reconstruction.json`.
2. Kod: `recon_export.py`, schemat, wywołanie w `recon_refresh.py finish`.
3. Scenariusze ewaluacji (przed treścią): eng-project-reconstruction.
4. Treść: eng-project-reconstruction (krok raportu, układ wyniku); plan integracji z pdi (F2 zrobione).
   Uprawnienia bez zmian — skrypty rekonstrukcji nie mają osobnych wpisów w `packs/pack-it/settings.json`.
5. Bramki: `workspace.py check --packs all` i `pack-it`; `refs`; `tests/test_*.py`; `skill_gate`, `sync-gate`;
   tytuł przez `check_commit_message.py`.
