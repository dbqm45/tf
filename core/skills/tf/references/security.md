# Bezpieczeństwo w pętli /tf: karencja wersji i skan kawałka

Czytasz, gdy `security_scan.py` zwraca FAIL albo STOP i trzeba zrozumieć wynik. Skrypt:
`python3 .claude/skills/tf/scripts/security_scan.py` (dalej `security_scan.py`).

## Karencja wersji na starcie (N10)
`security_scan.py cooldown` — FAIL, gdy menedżer pakietów nie ma ustawionej karencji: `min-release-age=7` (npm),
`minimumReleaseAge: 10080` (pnpm), `npmMinimalAgeGate` (Yarn), `exclude-newer` (uv), albo lockfile jest poza gitem.
FAIL → STOP z linią do dodania z wyniku; ustawień nie zmieniasz sam. Nowa zależność młodsza niż 7 dni (menedżer
pakietów odmawia instalacji) → STOP z wyjaśnieniem, nie obejście.

## Skan kawałka (po zielonych testach)
`security_scan.py scan --slice K<n> --attempt <k> --out <katalog-przebiegu>/security/K<n>`:
- semgrep (OWASP Top 10 i `.semgrep.yml` produktu) na plikach kawałka; audyt zależności tylko przy zmianie manifestu
  lub lockfile'a;
- SARIF, werdykt i `summary.md` każdej próby w `security/K<n>/proba-<k>/` — próby się nie nadpisują, raport pokazuje
  wszystkie;
- **blokujące** (error albo warning z CWE z OWASP Top 10, reguła SEC-001 z ci_for_sdlc) → FAIL próby: ustalenia
  (reguła, plik:linia) z `security/K<n>/feedback.md` (zawsze z ostatniej próby) są wejściem następnej próby;
- po 2 próbach skrypt drukuje blok STOP — kawałka nie commitujesz, tak jak przy czerwonym teście;
- brak skanera to FAIL z poleceniem instalacji, nie cichy PASS;
- ustalenia poniżej progu trafiają do raportu przebiegu (sekcja „Bezpieczeństwo”).

Zmienne: `TF_SCAN_PATH` (gdzie szukać skanerów zamiast `PATH`), `TF_SEMGREP_CONFIG` (własny zestaw reguł). Stan semgrepa
(`SEMGREP_SETTINGS_FILE`, `SEMGREP_LOG_FILE`, `SEMGREP_VERSION_CACHE_PATH`) skrypt kieruje do `.tf/cache/semgrep/`,
bo bez zapisywalnego HOME semgrep kończy się błędem (PRB-32, odtworzone 2026-11-05) — zmiennych nie dopisujesz
przed poleceniem.

## Źródła
- OWASP Top 10 2021 i 2025, „List of Mapped CWEs” (github.com/OWASP/Top10, odczyt 2026-11-02): lista CWE progu
  blokującego; reguła jak SEC-001 w ci_for_sdlc (`--sarif`).
- semgrep 1.183.0 (kod pakietu, odczyt 2026-11-02): `--sarif --output`, `--metrics=off`, rejestr reguł z semgrep.dev
  (host na liście dozwolonych kontenera).
- npm 11.10.0 `min-release-age` (dni), pnpm 10.17.0 `minimumReleaseAge` (minuty), uv `exclude-newer` (czas względny)
  — szczegóły i luki: plan `docs/plans/2026-11-02-z8c-2-…`.
