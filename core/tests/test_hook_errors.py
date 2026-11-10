#!/usr/bin/env python3
"""Hooki nie przerywają sesji przy własnym błędzie, ale błąd zostaje zapisany (.tf/logs/hook-errors.jsonl).

python3 tests/test_hook_errors.py

Hook, który wywraca się po cichu (`except Exception: pass`), wyłącza swoją ochronę bez śladu — np. strażnik TDD
przestaje blokować, a `onFailure: "block"` nie zadziała, bo proces kończy się kodem 0. Zasada (decyzja człowieka
2026-11-10): zachowanie zostaje (hook nie przerywa sesji), ale każdy taki wyjątek trafia do dziennika, a
`tf doctor` pokazuje podsumowanie. Zapis błędu sam nigdy nie rzuca wyjątku.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
HOOKS = ROOT / ".claude" / "hooks"
LOG = Path(".tf") / "logs" / "hook-errors.jsonl"


def load():
    spec = importlib.util.spec_from_file_location("hook_errors", HOOKS / "hook_errors.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_hook(name: str, project: Path, stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HOOKS / f"{name}.py")], input=stdin, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=30,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def entries(project: Path) -> list[dict]:
    p = project / LOG
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.is_file() else []


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        proj = t / "proj"
        proj.mkdir()
        os.environ["CLAUDE_PROJECT_DIR"] = str(proj)
        try:
            he = load()
        except Exception as e:  # moduł jeszcze nie istnieje — reszta testu i tak ma się wykonać
            he = None
            check(False, f"H-0: .claude/hooks/hook_errors.py da się wczytać: {e}")
        if he:
            # H-1: wpis z nazwą hooka, typem wyjątku, miejscem (plik:linia); komunikat przycięty
            try:
                raise ValueError("x" * 1000)
            except ValueError as e:
                he.record("demo_hook", e)
            got = entries(proj)
            check(len(got) == 1 and got[0].get("hook") == "demo_hook" and got[0].get("type") == "ValueError"
                  and re.search(r"test_hook_errors\.py:\d+", got[0].get("where", "")) and len(got[0].get("msg", "")) <= 200
                  and isinstance(got[0].get("ts"), (int, float)), f"H-1: wpis błędu: {got}")
            # H-2: zapis nie rzuca, gdy katalogu dziennika nie da się utworzyć
            blocker = t / "plik"
            blocker.write_text("x")
            os.environ["CLAUDE_PROJECT_DIR"] = str(blocker)
            try:
                he.record("demo_hook", RuntimeError("y"))
                ok = True
            except Exception:
                ok = False
            check(ok, "H-2: record nie rzuca wyjątku przy niezapisywalnym katalogu")
            os.environ["CLAUDE_PROJECT_DIR"] = str(proj)
            # H-3: rozmiar dziennika ograniczony
            for i in range(3000):
                he.record("spam", RuntimeError(f"błąd {i} " + "z" * 150))
            size = (proj / LOG).stat().st_size
            check(size <= he.MAX_BYTES, f"H-3: dziennik ograniczony do {he.MAX_BYTES} B: {size}")
            # H-4: podsumowanie dla tf doctor — liczba błędów z ostatnich dni i hooki
            (proj / LOG).write_text("\n".join(json.dumps(x) for x in [
                {"ts": time.time() - 3600, "hook": "tdd_guard", "type": "KeyError", "where": "tdd_guard.py:1", "msg": "a"},
                {"ts": time.time() - 7200, "hook": "tdd_guard", "type": "KeyError", "where": "tdd_guard.py:1", "msg": "a"},
                {"ts": time.time() - 30 * 86400, "hook": "skill_hint", "type": "OSError", "where": "x:1", "msg": "b"},
            ]) + "\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(HOOKS / "hook_errors.py"), "--summary", "--days", "7"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
                               env={**os.environ, "CLAUDE_PROJECT_DIR": str(proj)})
            check(r.returncode == 0 and "2" in r.stdout and "tdd_guard" in r.stdout and "skill_hint" not in r.stdout,
                  f"H-4: --summary: {r.stdout}{r.stderr}")
            (proj / LOG).unlink()
            r = subprocess.run([sys.executable, str(HOOKS / "hook_errors.py"), "--summary"], capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=30,
                               env={**os.environ, "CLAUDE_PROJECT_DIR": str(proj)})
            check(r.returncode == 0 and r.stdout.strip() == "", f"H-4: bez błędów --summary nic nie wypisuje: {r.stdout}")
        # H-5: prawdziwe hooki przy uszkodzonym wejściu: kod 0, nic na stdout, błąd w dzienniku (jev_guard bez
        # klucza API kończy pracę przed odczytem wejścia — jego miejsce obejmuje sprawdzenie statyczne H-6)
        for name in ("skill_hint", "skill_change_guard", "context_guard", "tdd_guard"):
            p = t / f"p-{name}"
            p.mkdir()
            r = run_hook(name, p, "{to nie jest json")
            hooks = {e.get("hook") for e in entries(p)}
            check(r.returncode == 0 and not r.stdout.strip() and name in hooks,
                  f"H-5: {name} przy uszkodzonym wejściu: kod {r.returncode}, stdout {r.stdout[:120]!r}, "
                  f"dziennik {sorted(hooks)}")
    # H-6: w hookach rdzenia nie ma cichego połknięcia szerokiego wyjątku (pass / return 0 bez zapisu)
    silent = []
    for f in sorted(HOOKS.glob("*.py")):
        lines = f.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines[:-1]):
            if re.match(r"^\s*except\s*(?:\(?\s*(?:Exception|BaseException)\b[^:]*)?:\s*(#.*)?$", line) \
                    and re.match(r"^\s*(pass|return 0|return)\s*(#.*)?$", lines[i + 1]) and "record(" not in lines[i + 1]:
                silent.append(f"{f.name}:{i + 1}")
    check(not silent, f"H-6: ciche połknięcie wyjątku w hookach: {silent}")
    # H-7: tf doctor pokazuje podsumowanie błędów hooków
    tf = (ROOT / ".tf" / "factory" / "tf.py").read_text(encoding="utf-8")
    check("hook_errors.py" in tf and "--summary" in tf, "H-7: tf doctor woła hook_errors.py --summary")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} błędy hooków zapisywane: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
