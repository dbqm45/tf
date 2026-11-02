# Plan: Z8c-2 — skaner bezpieczeństwa w pętli kawałka talosa i w CI (2026-11-02)

Źródło: pdi `docs/polecenia-startowe-zespol.md`, sekcja „Z8c-2”. Cel: talos nie commituje kawałka z blokującym
ustaleniem bezpieczeństwa, a CI repo produktu robi ten sam skan na każdym PR i przekazuje SARIF do ci_for_sdlc
(`--sarif`, Z8c-1, ci_for_sdlc PR #109).

## Pliki i kolejność

| # | Plik | Zmiana | Test (najpierw czerwony) |
|---|---|---|---|
| 1 | `modes/mode-talos/skills/talos-story-run/scripts/security_scan.py` (nowy, stdlib) | `scan`: semgrep (`p/owasp-top-ten` + `.semgrep.yml` produktu, albo `TALOS_SEMGREP_CONFIG`) tylko na zmienionych plikach; audyt zależności (npm/pnpm/yarn audit, pip-audit) tylko przy zmianie manifestu lub lockfile; SARIF + `verdict.json`, `summary.md`, `feedback.md` w katalogu przebiegu; brak skanera = FAIL z poleceniem instalacji. `verdict`: odczyt werdyktu. `cooldown`: karencja 7 dni (N10) | `tests/test_security_scan.py` (38 przypadków; skanery jako atrapy w `PATH`) |
| 2 | ten sam skrypt | próg blokujący jak SEC-001: `error` albo `warning` z CWE z OWASP Top 10 (2021 lub 2025); ustalenia poniżej progu do raportu; próba ≥ 2 z blokującymi → blok STOP | `test_security_scan.py` (progi, STOP) |
| 3 | `scripts/run_report.py` | sekcja „Bezpieczeństwo” w raporcie przebiegu z werdyktów `security/K<n>` | `tests/test_run_report.py` |
| 4 | `SKILL.md` talos-story-run | 1.1: `cooldown`; 3.3: skan po testach, `feedback.md` do następnej próby, STOP po 2 próbach, brak skanera = FAIL | `tests/test_mode_talos.py` T-10, bramka skilla (`skill_gate.py`, `sync-gate`) |
| 5 | `templates/verify.sh` (N3) | jeden skrypt weryfikacji: format, lint, typy, testy, karencja, skan; nazwany w pierwszej linii CLAUDE.md produktu | T-10 |
| 6 | `settings.json`, `pack.yaml` (1.2.0), `GUIDE.md` | uprawnienie do skryptu; sekcja „Bezpieczeństwo i karencja wersji” | `test_mode_talos.py` |
| 7 | `modes/mode-pdi/skills/pdi-decisions/templates/change-check.yml` (nowy) | workflow PR: instalacja skanerów (przypięte wersje), skan przed checkoutem ci_for_sdlc, krok „Błędy skanu”, ci_for_sdlc z `--sarif reports/security` | `tests/test_phase_run.py` W-15…W-18 |
| 8 | `templates/sdlc-phase.yml`, `scripts/phase_run.py` | skanery w fazie delivery; `workflow install --workflow change-check` | W-19, W-15 |
| 9 | `pack.yaml` (0.7.0), `GUIDE.md` mode-pdi | punkt „Skan bezpieczeństwa na każdym PR (Z8c-2)”, allowlista semgrep.dev (Z8a) | `test_mode_pdi.py` |

Kolejność: 1 → 2 → 3 → 4/5/6 → 7 → 8 → 9. Na końcu `python3 tools/workspace.py check --packs pack-it`.
CHANGELOG generuje `release.yml` — nie edytujemy ręcznie.

## Próg i pętla

- Blokujące: `error`; `warning` z CWE z OWASP Top 10 2021 lub 2025 (ta sama lista co SEC-001).
- Próba 1 z blokującymi: FAIL, `feedback.md` trafia do następnej próby. Próba 2: STOP z powodem i wznowieniem.
- Błąd skanera (np. audyt nie zadziałał) bez blokujących ustaleń: STOP — nie przepuszczamy po częściowym skanie.

## Karencja zależności (N10)

| Menedżer | Ustawienie | Jednostka | Wersja minimalna |
|---|---|---|---|
| npm | `min-release-age` w `.npmrc` | dni | npm ≥ 11.10.0 |
| pnpm | `minimumReleaseAge` | minuty (7 dni = 10080) | pnpm ≥ 10.17.0 |
| uv | `exclude-newer` | czas względny („7 days”) | — |
| Yarn | `npmMinimalAgeGate` | **niezweryfikowane** | — |
| Dependabot | `cooldown.default-days: 7` | dni | — |

Uwaga pnpm 11 + Dependabot: pnpm/pnpm#11203, #12450, PR #11583 — Dependabot może nie respektować ustawień
pnpm 11; karencję trzymamy też w `dependabot.yml`.

## Niezweryfikowane

- Pobranie reguł `p/owasp-top-ten` z rejestru semgrep bez logowania: semgrep.dev z tego środowiska zwraca 403.
  Obejście: `TALOS_SEMGREP_CONFIG` (lokalny plik reguł). Opcja na później: vendorowanie reguł — wymaga sprawdzenia
  licencji Semgrep Rules License.
- Jednostka `npmMinimalAgeGate` w Yarn.
- pip-audit nie ma wyjścia SARIF — wynik audytu Pythona idzie do `verdict.json`/`summary.md`, nie do SARIF.

## Allowlista sieci (Z8a)

`semgrep.dev` jest już w `modes/mode-pdi/.../sandbox_settings.py` (test S-2). Runner CI potrzebuje dostępu do
`semgrep.dev` i rejestru pakietów (PyPI dla pipx).

## Weryfikacja lokalna (2026-11-02)

Repo próbne z celowym SQL injection (`conn.execute("... '" + name + "'")`), lokalna reguła CWE-89 (ERROR),
semgrep 1.183.0: próba 1 → `BRAMKA K1: FAIL`, próba 2 → blok STOP; w katalogu skanu `semgrep.sarif`,
`verdict.json`, `summary.md`, `feedback.md`. Przebieg talosa na dbqm45/sdlc-proba i wpis w pdi
`docs/przebieg-lokalny.md` — do zrobienia przy dostępie do tych repo.

## Źródła (dostęp 2026-11-02)

- npm `min-release-age`: dokumentacja npm config (npm 11.10.0).
- pnpm `minimumReleaseAge`: pnpm.io/settings (pnpm 10.17.0).
- pnpm/Dependabot: github.com/pnpm/pnpm/issues/11203, /issues/12450, /pull/11583.
- Dependabot `cooldown`: docs.github.com, dependabot.yml options.
- uv `exclude-newer`: docs.astral.sh/uv, settings.
- Semgrep CLI, rejestr i SARIF: semgrep.dev/docs (strona niedostępna z tego środowiska — 403).
- pip-audit formaty wyjścia: github.com/pypa/pip-audit README.
