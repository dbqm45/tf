#!/usr/bin/env python3
"""Tests of the control bands (core-delivery-lifecycle/scripts/control_band.py): the Western Electric rules and the reaction level."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "core-delivery-lifecycle" / "scripts" / "control_band.py"

# baseline: mean 10, population standard deviation exactly 1
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
          f"a stable process → ok, mean 10, sd 1: {r}")
    code, r = run(BASE + [10, 13.5])
    check(r.get("tier") == "act" and any(v["rule"] == 1 for v in r["violations"]),
          f"a point beyond 3σ → rule 1, level act: {r}")
    code, r = run(BASE + [12.5, 10, 12.4])
    check(r.get("tier") == "diagnose" and any(v["rule"] == 2 for v in r["violations"]),
          f"2 of 3 beyond 2σ on the same side → rule 2, diagnose: {r}")
    code, r = run(BASE + [11.5, 11.2, 10.5, 11.4, 11.6])
    check(r.get("tier") == "log" and any(v["rule"] == 3 for v in r["violations"]),
          f"4 of 5 beyond 1σ on the same side → rule 3, log: {r}")
    code, r = run(BASE + [10.2] * 8)
    check(r.get("tier") == "log" and any(v["rule"] == 4 for v in r["violations"]),
          f"8 in a row on one side of the mean → rule 4, log: {r}")
    code, r = run(BASE + [6.0], "--side", "upper")
    check(r.get("tier") == "ok", f"--side upper ignores a drop (e.g. fewer 5xx errors): {r}")
    code, r = run(BASE + [6.0])
    check(r.get("tier") == "act", f"without --side a drop beyond 3σ is also a violation: {r}")
    code, r = run([5, 5, 5, 5, 5] * 4 + [5])
    check(code == 2 and "sd" not in r, f"zero baseline deviation → code 2 and a message: {r}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} control band tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
