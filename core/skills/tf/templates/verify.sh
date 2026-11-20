#!/usr/bin/env bash
# One product verification command (N3): format, lint, types, tests and security scan.
# The same script is run by the factory (the slice loop) and by CI (change-check / sdlc-phase) — unchanged.
# Name it in the first line of the product's CLAUDE.md, e.g.: „Weryfikacja: `./verify.sh`” ("Verification: `./verify.sh`").
#
#   ./verify.sh                 # uncommitted changes (the slice loop)
#   BASE=origin/main ./verify.sh   # CI on a PR: also commits since the base
#
# Fill in the sections with the stack's commands (examples in the comments); remove an empty section, do not leave `true`.
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

echo "== security scan"
python3 .claude/skills/tf/scripts/security_scan.py cooldown
python3 .claude/skills/tf/scripts/security_scan.py scan ${BASE:+--base "$BASE"} --out "${SCAN_OUT:-reports/security}"
