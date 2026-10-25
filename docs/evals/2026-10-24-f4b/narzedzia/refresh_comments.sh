#!/bin/bash
# F4: odświeżenie po zmianie tylko w komentarzach. Użycie: refresh_comments.sh <tf|maister> <repo> <end|mid> [budżet]
# end — komentarz dopisany na końcu co 20. pliku z kodem (jak w v1); mid — dwie linie komentarza przed pierwszą
# deklaracją typu (przesuwa numery linii).
set -u
B=${F4B_DIR:?ustaw F4B_DIR}
TOOL=$1; REPO=$2; MODE=$3; BUDGET=${4:-4}
RUN=$B/rc/$MODE-$TOOL-$REPO
rm -rf "$RUN"; mkdir -p "$B/rc" "$B/logs"
cp -r "$B/runs/$TOOL-$REPO" "$RUN"
git -C "$RUN" checkout -q -- .      # pliki śledzone jak w commicie bazowym (maister ma tu zmianę z v1)
if [ "$TOOL" = tf ] && [ -n "${TF_WS:-}" ]; then
  rm -rf "$RUN/.claude/skills" && cp -r "$TF_WS/.claude/skills" "$RUN/.claude/skills"
  find "$RUN/.claude" -name __pycache__ -prune -exec rm -rf {} +
fi
cd "$RUN"
git ls-files | grep -E '\.(cs|java|go)$' | awk 'NR % 20 == 0' > "$B/logs/rc-files-$MODE-$REPO.txt"
python3 - "$MODE" "$B/logs/rc-files-$MODE-$REPO.txt" <<'PY'
import re, sys
mode, lst = sys.argv[1:]
for f in open(lst, encoding="utf-8").read().split():
    text = open(f, encoding="utf-8").read()
    if mode == "end":
        text += "\n// F4: zmiana testowa — odświeżenie dokumentacji\n"
    else:
        lines = text.split("\n")
        at = next((i for i, l in enumerate(lines) if re.match(r"\s*(public|internal|class|interface|record|enum|type|func|namespace|@|\[)", l)), 0)
        lines[at:at] = ["// F4: zmiana testowa", "// odświeżenie dokumentacji"]
        text = "\n".join(lines)
    open(f, "w", encoding="utf-8").write(text)
PY
NOBUILD="Nie budujesz i nie uruchamiasz kodu projektu, nie używasz sieci."
if [ "$TOOL" = tf ]; then
  PROMPT="Kod zmienił się od ostatniej rekonstrukcji. Odśwież rekonstrukcję przyrostowo według skilla eng-project-reconstruction (sekcja Odświeżanie przyrostowe): tylko zmienione partie, potem raport i kontrola. Tryb wsadowy, bez pytań. $NOBUILD"
  EXTRA=(); SYS="Tryb wsadowy (benchmark): nikt nie odpowie na pytania. $NOBUILD"
else
  PROMPT="/maister:init"
  EXTRA=(--plugin-dir "$B/vendor/maister/plugins/maister")
  SYS="Tryb wsadowy (benchmark): nikt nie odpowie na pytania ani bramki. Kod zmienił się od ostatniej inicjalizacji. Na pytanie o istniejący katalog .maister wybierz \"Update existing documentation\"; przy każdym innym pytaniu wybierz opcję domyślną i kontynuuj do końca. $NOBUILD"
fi
ALLOWED=(Read Glob Grep Write Edit Skill Task Agent TodoWrite TaskCreate TaskUpdate TaskList TaskGet "Bash(python3 *)" "Bash(git log *)" "Bash(git ls-files *)" "Bash(git rev-parse *)" "Bash(git show *)" "Bash(git diff *)" "Bash(git status *)" "Bash(ls *)" "Bash(wc *)" "Bash(find *)" "Bash(mkdir *)" "Bash(head *)" "Bash(grep *)")
START=$(date +%s)
claude -p "$PROMPT" --model sonnet --permission-mode acceptEdits --allowedTools "${ALLOWED[@]}" --disallowedTools WebFetch WebSearch --max-budget-usd "$BUDGET" \
  --append-system-prompt "$SYS" "${EXTRA[@]}" --output-format stream-json --verbose > "$B/logs/rc-$MODE-$TOOL-$REPO.jsonl" 2> "$B/logs/rc-$MODE-$TOOL-$REPO.err"
RC=$?; END=$(date +%s)
python3 - "$B/logs/rc-$MODE-$TOOL-$REPO.jsonl" "$TOOL" "$REPO" "$MODE" "$RC" "$((END-START))" "$(wc -l < "$B/logs/rc-files-$MODE-$REPO.txt")" >> "$B/logs/rc.tsv" <<'PY'
import json, sys
path, tool, repo, mode, rc, secs, nfiles = sys.argv[1:]
res = {}
for line in open(path, encoding="utf-8", errors="replace"):
    try:
        e = json.loads(line)
    except ValueError:
        continue
    if e.get("type") == "result":
        res = e
print("\t".join(map(str, [tool, repo, mode, nfiles, rc, secs, res.get("total_cost_usd"), res.get("num_turns"), res.get("subtype")])))
PY
