#!/usr/bin/env python3
"""tools/hint_holdout.py: hint accuracy on the tuning scenarios and the holdout in a small workspace."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools" / "hint_holdout.py"


def main() -> int:
    fails = []
    with tempfile.TemporaryDirectory() as t:
        ws = Path(t)
        (ws / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy(REPO / "core" / "hooks" / "skill_hint.py", ws / ".claude" / "hooks" / "skill_hint.py")
        sk = ws / ".claude" / "skills" / "core-ledger"
        sk.mkdir(parents=True)
        (sk / "SKILL.md").write_text("---\nname: core-ledger\ndescription: Use for ledger postings — double entry.\nmetadata:\n"
                                     "  keywords: \"księgowanie, zaksięgować fakturę, dekretacja, ledger posting\"\n---\n"
                                     "# Ledger\nPost each invoice to the ledger with double entry.\n", encoding="utf-8")
        ev = ws / ".claude" / "tests" / "skill_evals"
        (ev / "holdout").mkdir(parents=True)
        (ev / "core-ledger.json").write_text(json.dumps({"skill": "core-ledger", "scenarios": [
            {"id": "a", "expect": "trigger", "prompt": "Jak zaksięgować fakturę zakupu, dekretacja na kontach?"},
            {"id": "b", "expect": "no-trigger", "prompt": "Jaka jest stolica Francji?"}]}, ensure_ascii=False))
        (ev / "holdout" / "core-ledger.json").write_text(json.dumps({"skill": "core-ledger", "scenarios": [
            {"id": "h", "expect": "trigger", "prompt": "Zrób dekretację tej faktury i zaksięguj ją."}]}, ensure_ascii=False))
        r = subprocess.run([sys.executable, str(TOOL), "--out", str(ws), "--json"], capture_output=True, text=True)
        try:
            res = json.loads(r.stdout)["core-ledger"]
        except (ValueError, KeyError):
            res = {}
        if res.get("tuning") != {"ok": 2, "all": 2} or res.get("holdout", {}).get("all") != 1:
            fails.append(f"HH-1: tuning 2/2 and one holdout scenario counted: {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(TOOL), "--out", str(ws / "brak")], capture_output=True, text=True)
        if r.returncode != 2:
            fails.append(f"HH-2: a bad workspace → code 2: {r.returncode}")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {2 - len(fails)}/2 hint_holdout tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
