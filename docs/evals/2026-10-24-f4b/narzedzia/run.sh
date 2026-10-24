#!/bin/bash
# F4-B: jeden przebieg rekonstrukcji. Użycie: run.sh <tf|maister> <repo> [budżet_usd]
set -u
B=${F4B_DIR:?ustaw F4B_DIR: katalog z repos/, gold/, vendor/maister, runs/, logs/}
WS=${TF_WS:?ustaw TF_WS: workspace pack-it (tools/workspace.py assemble)}
TOOL=$1; REPO=$2; BUDGET=${3:-8}
RUN=$B/runs/$TOOL-$REPO
rm -rf "$RUN"; mkdir -p "$B/runs" "$B/logs"
cp -r "$B/repos/$REPO" "$RUN"
NOBUILD="Nie budujesz i nie uruchamiasz kodu projektu (żadnych mvn, gradle, dotnet, go build/test, npm), nie używasz sieci."
if [ "$TOOL" = tf ]; then
  mkdir -p "$RUN/.claude"
  cp -r "$WS/.claude/skills" "$WS/.claude/hooks" "$RUN/.claude/"
  cp "$WS/.claude/settings.json" "$WS/.claude/catalog.md" "$RUN/.claude/" 2>/dev/null
  cp "$WS/CLAUDE.md" "$RUN/" 2>/dev/null
  find "$RUN/.claude" -name __pycache__ -prune -exec rm -rf {} +
  PROMPT="Zrekonstruuj ten projekt z samego kodu według skilla eng-project-reconstruction (wczytaj go narzędziem Skill i wykonaj całą procedurę). Zakres: całe repozytorium, budżet ${BUDGET} USD. Pracujesz w trybie wsadowym bez człowieka: nie zadawaj pytań, przyjmuj rozsądne domyślne decyzje i zapisz je w raporcie. Bez wersji HTML. $NOBUILD"
  EXTRA=()
  SYS="Tryb wsadowy (benchmark): nikt nie odpowie na pytania. $NOBUILD"
else
  PROMPT="/maister:init"
  EXTRA=(--plugin-dir "$B/vendor/maister/plugins/maister")
  SYS="Tryb wsadowy (benchmark): nikt nie odpowie na pytania ani bramki. Przy każdym pytaniu lub bramce wybierz opcję domyślną/rekomendowaną i kontynuuj do końca: wygeneruj wszystkie dokumenty projektu (Vision, Roadmap, Tech Stack, Architecture), standardy według inteligentnych ustawień domyślnych i odkrywanie standardów (standards-discover) z akceptacją wszystkich znalezionych standardów; w .maister/config.yml ustaw html_output: false. $NOBUILD"
fi
cd "$RUN"
START=$(date +%s)
ALLOWED=(Read Glob Grep Write Edit Skill Task Agent TodoWrite TaskCreate TaskUpdate TaskList TaskGet "Bash(python3 *)" "Bash(git log *)" "Bash(git ls-files *)" "Bash(git rev-parse *)" "Bash(git show *)" "Bash(ls *)" "Bash(wc *)" "Bash(find *)" "Bash(mkdir *)" "Bash(head *)" "Bash(grep *)")
claude -p "$PROMPT" --model sonnet --permission-mode acceptEdits --allowedTools "${ALLOWED[@]}" --disallowedTools WebFetch WebSearch --max-budget-usd "$BUDGET" \
  --append-system-prompt "$SYS" "${EXTRA[@]}" --output-format stream-json --verbose > "$B/logs/$TOOL-$REPO.jsonl" 2> "$B/logs/$TOOL-$REPO.err"
RC=$?
END=$(date +%s)
python3 - "$B/logs/$TOOL-$REPO.jsonl" "$TOOL" "$REPO" "$RC" "$((END-START))" >> "$B/logs/summary.tsv" <<'EOF'
import json, sys
path, tool, repo, rc, secs = sys.argv[1:]
res = {}
for line in open(path, encoding="utf-8", errors="replace"):
    try:
        e = json.loads(line)
    except ValueError:
        continue
    if e.get("type") == "result":
        res = e
print("\t".join(map(str, [tool, repo, rc, secs, res.get("total_cost_usd"), res.get("num_turns"), res.get("subtype"), res.get("is_error")])))
EOF
