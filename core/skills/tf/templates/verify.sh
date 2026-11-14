#!/usr/bin/env bash
# Jedno polecenie weryfikacji produktu (N3): format, lint, typy, testy i skan bezpieczeństwa.
# Ten sam skrypt uruchamia fabryka (pętla kawałka) i CI (change-check / sdlc-phase) — bez zmian.
# Nazwij go w pierwszej linii CLAUDE.md produktu, np.: „Weryfikacja: `./verify.sh`”.
#
#   ./verify.sh                 # zmiany nieskomitowane (pętla kawałka)
#   BASE=origin/main ./verify.sh   # CI na PR: także commity od bazy
#
# Wypełnij sekcje komendami stosu (przykłady w komentarzach); pustą sekcję usuń, nie zostawiaj `true`.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "== format"
# npx prettier --check .          | ruff format --check .
echo "== lint"
# npx eslint .                    | ruff check .
echo "== typy"
# npx tsc --noEmit                | mypy .
echo "== testy"
# npm test                        | pytest -q

echo "== skan bezpieczeństwa"
python3 .claude/skills/tf/scripts/security_scan.py cooldown
python3 .claude/skills/tf/scripts/security_scan.py scan ${BASE:+--base "$BASE"} --out "${SCAN_OUT:-reports/security}"
