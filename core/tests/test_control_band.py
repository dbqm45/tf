#!/usr/bin/env python3
"""Testy pasm kontrolnych (core-delivery-lifecycle/scripts/control_band.py): reguły Western Electric i poziom reakcji."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "core-delivery-lifecycle" / "scripts" / "control_band.py"

# linia bazowa: średnia 10, odchylenie standardowe populacji dokładnie 1
BASE = [9, 11] * 10


def run(values, *args):
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "m.csv"
        f.write_text("wartosc\n" + "\n".join(str(v) for v in values) + "\n")
        out = subprocess.run([sys.executable, str(SCRIPT), str(f), "--baseline", str(len(BASE)), *args],
                             capture_output=True, text=True, timeout=30)
        return out.returncode, json.loads(out.stdout) if out.stdout.strip() else {"stderr": out.stderr}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    code, r = run(BASE + [10, 10.5, 9.5])
    check(code == 0 and r.get("tier") == "ok" and abs(r["mean"] - 10) < 1e-9 and abs(r["sd"] - 1) < 1e-9,
          f"stabilny proces → ok, średnia 10, sd 1: {r}")
    code, r = run(BASE + [10, 13.5])
    check(r.get("tier") == "act" and any(v["rule"] == 1 for v in r["violations"]),
          f"punkt poza 3σ → reguła 1, poziom act: {r}")
    code, r = run(BASE + [12.5, 10, 12.4])
    check(r.get("tier") == "diagnose" and any(v["rule"] == 2 for v in r["violations"]),
          f"2 z 3 poza 2σ po tej samej stronie → reguła 2, diagnose: {r}")
    code, r = run(BASE + [11.5, 11.2, 10.5, 11.4, 11.6])
    check(r.get("tier") == "log" and any(v["rule"] == 3 for v in r["violations"]),
          f"4 z 5 poza 1σ po tej samej stronie → reguła 3, log: {r}")
    code, r = run(BASE + [10.2] * 8)
    check(r.get("tier") == "log" and any(v["rule"] == 4 for v in r["violations"]),
          f"8 kolejnych po jednej stronie średniej → reguła 4, log: {r}")
    code, r = run(BASE + [6.0], "--side", "upper")
    check(r.get("tier") == "ok", f"--side upper ignoruje spadek (np. mniej błędów 5xx): {r}")
    code, r = run(BASE + [6.0])
    check(r.get("tier") == "act", f"bez --side spadek poza 3σ też jest naruszeniem: {r}")
    code, r = run([5, 5, 5, 5, 5] * 4 + [5])
    check(code == 2 and "sd" not in r, f"zerowe odchylenie linii bazowej → kod 2 i komunikat: {r}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów pasm kontrolnych")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
