#!/bin/bash
# F4-B: odświeżenie po zmianie ok. 5% plików kodu. Użycie: refresh.sh <tf|maister> <repo> [budżet]
set -u
B=${F4B_DIR:?ustaw F4B_DIR: katalog z repos/, gold/, vendor/maister, runs/, logs/}
TOOL=$1; REPO=$2; BUDGET=${3:-4}
RUN=$B/runs/$TOOL-$REPO
cd "$RUN"
# ta sama, deterministyczna pula plików dla obu narzędzi: co 20. plik .cs/.java/.go z git ls-files
git ls-files | grep -E '\.(cs|java|go)$' | awk 'NR % 20 == 0' > "$B/logs/refresh-files-$REPO.txt"
while read -r f; do printf '\n// F4: zmiana testowa — odświeżenie dokumentacji\n' >> "$f"; done < "$B/logs/refresh-files-$REPO.txt"
NOBUILD="Nie budujesz i nie uruchamiasz kodu projektu, nie używasz sieci."
if [ "$TOOL" = tf ]; then
  PROMPT="Kod zmienił się od ostatniej rekonstrukcji. Odśwież rekonstrukcję przyrostowo według skilla eng-project-reconstration (sekcja Odświeżanie przyrostowe): tylko zmienione partie, potem raport i kontrola. Tryb wsadowy, bez pytań. $NOBUILD"
  PROMPT=${PROMPT/reconstration/reconstruction}
  EXTRA=(); SYS="Tryb wsadowy (benchmark): nikt nie odpowie na pytania. $NOBUILD"
else
  PROMPT="/maister:init"
  EXTRA=(--plugin-dir "$B/vendor/maister/plugins/maister")
  SYS="Tryb wsadowy (benchmark): nikt nie odpowie na pytania ani bramki. Kod zmienił się od ostatniej inicjalizacji. Na pytanie o istniejący katalog .maister wybierz \"Update existing documentation\"; przy każdym innym pytaniu wybierz opcję domyślną i kontynuuj do końca. $NOBUILD"
fi
ALLOWED=(Read Glob Grep Write Edit Skill Task Agent TodoWrite TaskCreate TaskUpdate TaskList TaskGet "Bash(python3 *)" "Bash(git log *)" "Bash(git ls-files *)" "Bash(git rev-parse *)" "Bash(git show *)" "Bash(git diff *)" "Bash(git status *)" "Bash(ls *)" "Bash(wc *)" "Bash(find *)" "Bash(mkdir *)" "Bash(head *)" "Bash(grep *)")
START=$(date +%s)
claude -p "$PROMPT" --model sonnet --permission-mode acceptEdits --allowedTools "${ALLOWED[@]}" --disallowedTools WebFetch WebSearch --max-budget-usd "$BUDGET" \
  --append-system-prompt "$SYS" "${EXTRA[@]}" --output-format stream-json --verbose > "$B/logs/refresh-$TOOL-$REPO.jsonl" 2> "$B/logs/refresh-$TOOL-$REPO.err"
RC=$?; END=$(date +%s)
python3 - "$B/logs/refresh-$TOOL-$REPO.jsonl" "$TOOL" "$REPO" "$RC" "$((END-START))" "$(wc -l < "$B/logs/refresh-files-$REPO.txt")" >> "$B/logs/refresh.tsv" <<'EOF'
import json, sys
path, tool, repo, rc, secs, nfiles = sys.argv[1:]
res = {}
for line in open(path, encoding="utf-8", errors="replace"):
    try:
        e = json.loads(line)
    except ValueError:
        continue
    if e.get("type") == "result":
        res = e
print("\t".join(map(str, [tool, repo, nfiles, rc, secs, res.get("total_cost_usd"), res.get("subtype")])))
EOF
