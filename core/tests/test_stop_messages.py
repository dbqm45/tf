#!/usr/bin/env python3
"""Tests of the /tf-task loop's stop messages (the tf skill, templates/stop_messages.json): every code has a message in plain
language — what happened, what is needed, one question with options and a recommendation. python3 .claude/tests/test_stop_messages.py"""
import json
import re
import sys
from pathlib import Path

SKILL = Path(".claude") / "skills" / "tf"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / SKILL / "scripts" / "run_state.py").is_file())
MESSAGES = ROOT / SKILL / "templates" / "stop_messages.json"
# words from the factory's internals a human does not need to know (the axis document, §1a rule 2)
JARGON = ("tier", "hook", "bramk", "kawał", "triaż", "harness", "slice", "gate", "artefakt", "stop", "spec.md",
          "plan.md", "run_state", "task.json", "commit", "diff", "scan", "agent", "artifact")


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    script = (ROOT / SKILL / "scripts" / "run_state.py").read_text(encoding="utf-8")
    block = script.split("STOP_CODES = {", 1)[-1].split("}", 1)[0]
    codes = re.findall(r'^\s*"([a-z-]+)":', block, re.M)
    try:
        data = json.loads(MESSAGES.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"✗ missing or invalid {MESSAGES}: {e}")
        return 1
    check(len(codes) >= 10 and sorted(data) == sorted(codes),
          f"K-1: the messages file has exactly the script's codes: missing {sorted(set(codes) - set(data))}, "
          f"extra {sorted(set(data) - set(codes))}")
    for code in codes:
        m = data.get(code) or {}
        texts = [str(m.get(k, "")) for k in ("co", "potrzeba", "question", "potem")]
        options = m.get("opcje") if isinstance(m.get("opcje"), list) else []
        check(all(t.strip() for t in texts), f"K-2 {code}: the fields co, potrzeba, pytanie and potem are filled in")
        check(str(m.get("question", "")).strip().endswith("?") and str(m.get("question", "")).count("?") == 1,
              f"K-3 {code}: one question, ending with a question mark: {m.get('question')}")
        check(2 <= len(options) <= 3 and all(isinstance(o, dict) and str(o.get("opcja", "")).strip()
                                              and str(o.get("skutek", "")).strip() for o in options),
              f"K-4 {code}: 2–3 options, each with an effect: {options}")
        check(sum(1 for o in options if isinstance(o, dict) and o.get("rekomendowana") is True) == 1,
              f"K-5 {code}: exactly one option recommended")
        blob = " ".join(texts + [f"{o.get('opcja', '')} {o.get('skutek', '')}" for o in options if isinstance(o, dict)]).lower()
        hits = [w for w in JARGON if re.search(rf"(?<![a-ząćęłńóśźż]){re.escape(w)}", blob)]
        check(not hits, f"K-6 {code}: a message without words from the factory's internals: {hits}")
        check(all(len(t) <= 220 for t in texts), f"K-7 {code}: every field fits in two lines (≤220 characters)")

    # K-8: the commands given in the messages use names the script accepts (formerly `--code pytanie`,
    # `step … kod run`, the codes “testy/skan” — the script rejected them)
    steps = re.findall(r'^STEPS = \(([^)]*)\)', script, re.M)
    steps = set(re.findall(r'"([a-z]+)"', steps[0])) if steps else set()
    bad_codes = sorted({c for c in re.findall(r"--code ([a-z][a-z-]+)", script) if c not in codes and c != "kod"})
    bad_steps = sorted({s for s in re.findall(r"R\{k(?: \+ 1)?\} ([a-z]+) (?:run|pass|fail)", script) if s not in steps})
    check(steps and not bad_codes and not bad_steps,
          f"K-8: the messages give only existing codes and steps: codes {bad_codes}, steps {bad_steps}")
    plain = re.findall(r"\(kod: ([^)]*)\)", script)
    check(not plain, f"K-9: the list of codes in the round-limit message uses code names: {plain}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} stop message tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
