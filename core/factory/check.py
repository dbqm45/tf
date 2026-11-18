#!/usr/bin/env python3
"""
The whole local factory check loop in one command — short output instead of several long ones (cheaper context).

  python3 .tf/factory/check.py              # build check, tests, scenarios, gate, journal
  python3 .tf/factory/check.py -k skill     # only tests whose name contains “skill” (plus the remaining steps)
  python3 .tf/factory/check.py --json       # machine-readable result
  --root <directory> (default: this factory's repository)

Output: one line per step (green ones only with a count), details only on failures (the last lines of output), the last
line is the verdict. Exit code 1 when any step is red. A step without a script (e.g. in a project without docs/project/) is
skipped with a note. The skill review deadline (freshness.py) is information, not an error. Standard library only.
"""
from __future__ import annotations

import json
import subprocess
import sys

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # engine in .tf/factory/ without __pycache__ (like node_modules — code only)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAIL = 12


def run(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        r = subprocess.run([sys.executable, *cmd], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
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
            out.append({"name": name, "ok": True, "skipped": True, "summary": "skipped (no script)"})
            return
        ok, text = run([str(script), *args], root)
        out.append({"name": name, "ok": ok or info, "info": info, "summary": last_line(text),
                    "details": [] if ok else failure_lines(text)})

    step("build check", root / ".tf" / "factory" / "build.py", "check")
    tests = sorted(p for p in tests_dir.glob("test_*.py") if not pattern or pattern in p.name)
    for t in tests:
        step(t.relative_to(root).as_posix(), t)
    step("scenarios", tests_dir / "run_skill_evals.py", "--validate")
    step("skill gate", root / ".tf" / "factory" / "skill_gate.py", "--status", "--strict")
    step("hints of all skills", root / ".tf" / "factory" / "skill_gate.py", "--hints")
    if (root / "docs" / "project").is_dir():
        step("project record", root / ".claude" / "hooks" / "project_record.py", "check")
    else:
        out.append({"name": "project record", "ok": True, "skipped": True, "summary": "skipped (no docs/project/)"})
    step("review dates", root / ".tf" / "factory" / "freshness.py", "--root", str(root), info=True)
    step("factory hooks", root / ".tf" / "factory" / "hooks_status.py", "--root", str(root), info=True)
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
    print(f"{'✓' if green == len(tests) else '✗'} tests: {green}/{len(tests)} files green")
    bad = [s["name"] for s in res if not s["ok"]]
    print(f"✓ all green ({len(res)} steps)" if ok else f"✗ red: {', '.join(bad)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
