#!/usr/bin/env python3
"""Testy komunikatów zatrzymań pętli /tf (skill tf, templates/stop_messages.json): każdy kod ma komunikat w prostym
języku — co się stało, czego potrzeba, jedno pytanie z opcjami i rekomendacją. python3 .claude/tests/test_stop_messages.py"""
import json
import re
import sys
from pathlib import Path

SKILL = Path(".claude") / "skills" / "tf"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / SKILL / "scripts" / "run_state.py").is_file())
MESSAGES = ROOT / SKILL / "templates" / "stop_messages.json"
# słowa z budowy fabryki, których człowiek nie musi znać (dokument osi, §1a reguła 2)
JARGON = ("tier", "hook", "bramk", "kawał", "triaż", "harness", "slice", "gate", "artefakt", "stop", "spec.md",
          "plan.md", "run_state", "task.json", "commit", "diff", "skan", "agent")


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
        print(f"✗ brak albo błędny {MESSAGES}: {e}")
        return 1
    check(len(codes) >= 10 and sorted(data) == sorted(codes),
          f"K-1: plik komunikatów ma dokładnie kody ze skryptu: brak {sorted(set(codes) - set(data))}, "
          f"nadmiar {sorted(set(data) - set(codes))}")
    for code in codes:
        m = data.get(code) or {}
        texts = [str(m.get(k, "")) for k in ("co", "potrzeba", "pytanie", "potem")]
        options = m.get("opcje") if isinstance(m.get("opcje"), list) else []
        check(all(t.strip() for t in texts), f"K-2 {code}: pola co, potrzeba, pytanie i potem są wypełnione")
        check(str(m.get("pytanie", "")).strip().endswith("?") and str(m.get("pytanie", "")).count("?") == 1,
              f"K-3 {code}: jedno pytanie, zakończone znakiem zapytania: {m.get('pytanie')}")
        check(2 <= len(options) <= 3 and all(isinstance(o, dict) and str(o.get("opcja", "")).strip()
                                              and str(o.get("skutek", "")).strip() for o in options),
              f"K-4 {code}: 2–3 opcje, każda ze skutkiem: {options}")
        check(sum(1 for o in options if isinstance(o, dict) and o.get("rekomendowana") is True) == 1,
              f"K-5 {code}: dokładnie jedna opcja rekomendowana")
        blob = " ".join(texts + [f"{o.get('opcja', '')} {o.get('skutek', '')}" for o in options if isinstance(o, dict)]).lower()
        hits = [w for w in JARGON if re.search(rf"(?<![a-ząćęłńóśźż]){re.escape(w)}", blob)]
        check(not hits, f"K-6 {code}: komunikat bez słów z budowy fabryki: {hits}")
        check(all(len(t) <= 220 for t in texts), f"K-7 {code}: każde pole mieści się w dwóch liniach (≤220 znaków)")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów komunikatów zatrzymań")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
