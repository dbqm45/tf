#!/bin/bash
# F4: odświeżenie po zmianie w logice (zmieniona, nowa i usunięta reguła). Użycie: refresh_logic.sh <tf|maister> <repo> [budżet] [przebieg]
set -u
B=${F4B_DIR:?ustaw F4B_DIR}
TOOL=$1; REPO=$2; BUDGET=${3:-4}; SUF=${4:+-$4}
RUN=$B/rf/$TOOL-$REPO$SUF
rm -rf "$RUN"; mkdir -p "$B/rf" "$B/logs"
cp -r "$B/runs/$TOOL-$REPO" "$RUN"          # kopia wyniku bazowego — dane benchmarku zostają nietknięte
git -C "$RUN" checkout -q -- .              # pliki śledzone jak w commicie bazowym (maister ma tu zmianę z v1)
if [ "$TOOL" = tf ] && [ -n "${TF_WS:-}" ]; then   # bieżąca wersja skilli z workspace zamiast tej z przebiegu bazowego
  rm -rf "$RUN/.claude/skills" && cp -r "$TF_WS/.claude/skills" "$RUN/.claude/skills"
  find "$RUN/.claude" -name __pycache__ -prune -exec rm -rf {} +
fi
python3 "$B/mutate_logic.py" "$REPO" "$RUN" > "$B/logs/rl-mutate-$TOOL-$REPO$SUF.txt" || exit 3
cd "$RUN"
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
  --append-system-prompt "$SYS" "${EXTRA[@]}" --output-format stream-json --verbose > "$B/logs/rl-$TOOL-$REPO$SUF.jsonl" 2> "$B/logs/rl-$TOOL-$REPO$SUF.err"
RC=$?; END=$(date +%s)
python3 - "$B/logs/rl-$TOOL-$REPO$SUF.jsonl" "$TOOL" "$REPO$SUF" "$RC" "$((END-START))" >> "$B/logs/rl.tsv" <<'PY'
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
print("\t".join(map(str, [tool, repo, rc, secs, res.get("total_cost_usd"), res.get("num_turns"), res.get("subtype")])))
PY
