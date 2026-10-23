#!/usr/bin/env python3
"""
Zgodność zmian z planem przebiegu Talosa: pliki zmienione na gałęzi historyjki vs pliki kawałków w plan.md.

  python3 .claude/skills/talos-story-run/scripts/plan_drift.py <katalog przebiegu> [--base main] [--json]

Kawałek w plan.md: `- [x] K<n> — <wartość> · … · pliki: <ścieżki po przecinku> · …` (ścieżka może być katalogiem
albo wzorcem glob). Wynik: per kawałek pliki ruszone i nietknięte, zmiany spoza planu (bez .claude/runs/),
pokrycie diffu planem w % i liczba zmienionych plików testów. Skrypt tylko raportuje (kod 0); 2 — złe wywołanie.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
import sys

SLICE = re.compile(r"^\s*-\s*\[( |x|X)\]\s*(K\d+)\b(.*)$")
TEST = re.compile(r"(^|/)(tests?|__tests__|e2e|spec)/|\.(test|spec)\.|(^|/)test_[^/]*\.py$|_test\.(py|go)$|"
                  r"(Test|Tests)\.(java|cs)$")


def parse_plan(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        m = SLICE.match(line)
        if not m:
            continue
        files = []
        for part in m.group(3).split("·"):
            k, _, v = part.strip().partition(":")
            if k.strip().lower() == "pliki":
                files = [f.strip().strip("`") for f in v.split(",") if f.strip()]
        out.append({"id": m.group(2), "done": m.group(1).lower() == "x", "files": files})
    return out


def matches(path: str, spec: str) -> bool:
    if spec.endswith("/"):
        return path.startswith(spec)
    return path == spec or fnmatch.fnmatch(path, spec) or path.startswith(spec.rstrip("/") + "/")


def changed_files(base: str) -> list[str]:
    r = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], capture_output=True, text=True)
    if r.returncode != 0:
        r = subprocess.run(["git", "diff", "--name-only", base], capture_output=True, text=True)
    return sorted(f for f in r.stdout.splitlines() if f and not f.startswith(".claude/runs/"))


def drift(plan: list[dict], changed: list[str]) -> dict:
    slices, covered = [], set()
    for s in plan:
        touched = sorted(f for f in changed if any(matches(f, spec) for spec in s["files"]))
        missing = [spec for spec in s["files"] if not any(matches(f, spec) for f in changed)]
        covered |= set(touched)
        slices.append({**s, "touched": touched, "missing": missing})
    unplanned = [f for f in changed if f not in covered]
    return {"slices": slices, "changed": changed, "unplanned": unplanned,
            "coverage": round(100 * len(covered) / len(changed)) if changed else 100,
            "tests_changed": sum(1 for f in changed if TEST.search(f))}


def render(r: dict) -> str:
    done = sum(s["done"] for s in r["slices"])
    L = [f"Zgodność z planem: kawałki {done}/{len(r['slices'])}, pokrycie diffu planem {r['coverage']}%, "
         f"zmienione pliki {len(r['changed'])}, w tym testy {r['tests_changed']}"]
    for s in r["slices"]:
        L.append(f"  - {s['id']} [{'x' if s['done'] else ' '}]: ruszone {len(s['touched'])}"
                 + (f"; nietknięte z planu: {', '.join(s['missing'])}" if s["missing"] else ""))
    if r["unplanned"]:
        L.append("Zmiany spoza planu (sprawdź zakres albo dopisz do planu): " + ", ".join(r["unplanned"]))
    return "\n".join(L)


def main(argv: list[str]) -> int:
    base, as_json, args = "main", False, []
    it = iter(argv)
    for a in it:
        if a == "--base":
            base = next(it, "main")
        elif a == "--json":
            as_json = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            args.append(a)
    plan_md = os.path.join(args[0], "plan.md") if args else ""
    if len(args) != 1 or not os.path.isfile(plan_md):
        print(f"✗ podaj katalog przebiegu z plan.md (jest: {args})", file=sys.stderr)
        return 2
    with open(plan_md, encoding="utf-8") as fh:
        r = drift(parse_plan(fh.read()), changed_files(base))
    print(json.dumps(r, ensure_ascii=False, indent=2) if as_json else render(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
