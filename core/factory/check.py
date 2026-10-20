#!/usr/bin/env python3
"""
Cała lokalna pętla sprawdzeń fabryki jednym poleceniem — krótki wynik zamiast kilku długich wyjść (tańszy kontekst).

  python3 factory/check.py              # build check, testy, scenariusze, bramka, dziennik
  python3 factory/check.py -k skill     # tylko testy, których nazwa zawiera „skill” (plus pozostałe kroki)
  python3 factory/check.py --json       # wynik dla automatu
  --root <katalog> (domyślnie repozytorium tej fabryki)

Na wyjściu: linia na krok (zielone tylko z liczbą), szczegóły wyłącznie przy błędach (ostatnie linie wyjścia), ostatnia
linia to werdykt. Kod 1, gdy któryś krok jest czerwony. Krok bez skryptu (np. w projekcie bez docs/project/) jest
pomijany z adnotacją. Termin przeglądu skilli (freshness.py) jest informacją, nie błędem. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAIL = 12


def run(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        r = subprocess.run([sys.executable, *cmd], cwd=cwd, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return False, "przekroczony limit czasu (900 s)"
    return r.returncode == 0, (r.stdout + ("\n" + r.stderr if r.stderr.strip() else "")).strip()


def last_line(out: str) -> str:
    return next((ln for ln in reversed(out.splitlines()) if ln.strip()), "")


def failure_lines(out: str) -> list[str]:
    lines = [ln for ln in out.splitlines() if ln.strip()]
    marked = [ln for ln in lines if ln.lstrip().startswith(("✗", "Traceback", "Error", "E ")) or "Error:" in ln]
    return (marked or lines)[-TAIL:]


def steps(root: Path, pattern: str | None) -> list[dict]:
    tests_dir = root / "tests" if (root / "tests").is_dir() else root / ".claude" / "tests"
    out: list[dict] = []

    def step(name: str, script: Path, *args: str, info: bool = False) -> None:
        if not script.is_file():
            out.append({"name": name, "ok": True, "skipped": True, "summary": "pominięto (brak skryptu)"})
            return
        ok, text = run([str(script), *args], root)
        out.append({"name": name, "ok": ok or info, "info": info, "summary": last_line(text),
                    "details": [] if ok else failure_lines(text)})

    step("build check", root / "factory" / "build.py", "check")
    tests = sorted(p for p in tests_dir.glob("test_*.py") if not pattern or pattern in p.name)
    for t in tests:
        step(t.relative_to(root).as_posix(), t)
    step("scenariusze", tests_dir / "run_skill_evals.py", "--validate")
    step("bramka skilli", root / "factory" / "skill_gate.py", "--status", "--strict")
    step("podpowiedzi wszystkich skilli", root / "factory" / "skill_gate.py", "--hints")
    if (root / "docs" / "project").is_dir():
        step("dziennik", root / ".claude" / "hooks" / "project_record.py", "check")
    else:
        out.append({"name": "dziennik", "ok": True, "skipped": True, "summary": "pominięto (brak docs/project/)"})
    step("terminy przeglądu", root / "factory" / "freshness.py", "--root", str(root), info=True)
    step("hooki fabryki", root / "factory" / "hooks_status.py", "--root", str(root), info=True)
    return out


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv[1:])
    for a in it:
        if a in ("--root", "-k"):
            opts[a] = next(it, "")
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            opts[a] = True
    root = Path(opts.get("--root") or ROOT).resolve()
    res = steps(root, opts.get("-k") or None)
    ok = all(s["ok"] for s in res)
    if opts.get("--json"):
        print(json.dumps({"ok": ok, "steps": res}, ensure_ascii=False, indent=1))
        return 0 if ok else 1
    tests = [s for s in res if s["name"].split("/")[-1].startswith("test_")]
    for s in res:
        if s in tests and s["ok"]:
            continue
        mark = "·" if s.get("skipped") else ("ℹ" if s.get("info") else ("✓" if s["ok"] else "✗"))
        print(f"{mark} {s['name']}: {s['summary']}")
        for ln in s.get("details", []):
            print(f"    {ln}")
    green = sum(s["ok"] for s in tests)
    print(f"{'✓' if green == len(tests) else '✗'} testy: {green}/{len(tests)} plików zielonych")
    bad = [s["name"] for s in res if not s["ok"]]
    print(f"✓ wszystko zielone ({len(res)} kroków)" if ok else f"✗ czerwone: {', '.join(bad)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
