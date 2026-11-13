#!/usr/bin/env python3
"""Testy ochrony specyfikacji i zatwierdzonych plików zadania przed zapisem w trakcie realizacji
(.claude/hooks/guard_paths.py, `tf task freeze|reopen`). python3 .claude/tests/test_task_oracle.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
GUARD = ROOT / ".claude" / "hooks" / "guard_paths.py"
CHANGES = Path("docs") / "project" / "changes"
SPEC = ("# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci, wtedy opłata wynosi 45 zł.\n"
        "\n## Bez zmian\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Poza zakresem\n\n- Abonamenty.\n")


def tf(project: Path, *args: str):
    return subprocess.run([sys.executable, str(TASK), *args], cwd=project, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def guard(project: Path, tool: str, rel: str, absolute: bool = True) -> tuple[str, str]:
    """Decyzja hooka dla narzędzia i pliku: ("ask" | "deny" | "", powód)."""
    path = str(project / rel) if absolute else rel
    data = {"tool_name": tool, "tool_input": {"file_path": path}, "cwd": str(project)}
    r = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(data), capture_output=True, text=True, timeout=30,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})
    try:
        out = json.loads(r.stdout)["hookSpecificOutput"]
        return out.get("permissionDecision", ""), out.get("permissionDecisionReason", "")
    except (ValueError, KeyError):
        return "", r.stdout + r.stderr


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        tf(p, "start", "PROJ-1", "--title", "Limit dobowy")
        folder = p / CHANGES / "PROJ-1"
        (folder / "spec.md").write_text(SPEC, encoding="utf-8")
        (folder / "plan.md").write_text("# Plan\n- [ ] K1 — limit\n", encoding="utf-8")
        (p / "tests").mkdir()
        (p / "tests" / "test_fees.py").write_text("def test_ac1_limit():  # AC-1\n    assert True\n", encoding="utf-8")
        (p / "src.py").write_text("x = 1\n", encoding="utf-8")
        spec_rel = f"{CHANGES.as_posix()}/PROJ-1/spec.md"

        # specyfikacja: przed realizacją pisze się ją swobodnie, od etapu realizacja zapis wymaga zgody człowieka
        d, why = guard(p, "Write", spec_rel)
        check(d == "", f"O-1: spec.md w etapie przyjecie — zapis bez pytania: {d} {why}")
        tf(p, "stage", "PROJ-1", "plan")
        d, why = guard(p, "Edit", spec_rel)
        check(d == "", f"O-2: spec.md w etapie plan — zapis bez pytania: {d} {why}")
        tf(p, "stage", "PROJ-1", "realizacja")
        d, why = guard(p, "Edit", spec_rel)
        check(d == "ask" and "PROJ-1" in why and "zmiana wymagań" in why, f"O-3: spec.md w etapie realizacja → ask z wyjaśnieniem: {d} {why}")
        d, why = guard(p, "Write", spec_rel, absolute=False)
        check(d == "ask", f"O-4: ścieżka względna działa tak samo: {d} {why}")
        d, why = guard(p, "Read", spec_rel)
        check(d == "", f"O-5: odczyt specyfikacji bez pytania: {d} {why}")
        d, why = guard(p, "Edit", f"{CHANGES.as_posix()}/PROJ-1/plan.md")
        check(d == "", f"O-6: plan niezatwierdzony — zapis bez pytania: {d} {why}")
        d, why = guard(p, "Edit", "src.py")
        check(d == "", f"O-7: plik spoza zadania bez zmian: {d} {why}")

        # pliki, które pisze tylko skrypt
        for rel in (f"{CHANGES.as_posix()}/PROJ-1/task.json", f"{CHANGES.as_posix()}/INDEX.md",
                    f"{CHANGES.as_posix()}/PROJ-1/evidence/K1-1.json"):
            d, why = guard(p, "Write", rel)
            check(d == "ask" and "tf task" in why, f"O-8: {rel} pisze tylko `tf task` → ask: {d} {why}")

        # plik zadania zatwierdzony przez człowieka: zapis wymaga zgody; reopen zdejmuje zatwierdzenie z powodem
        tf(p, "artifact", "PROJ-1", "plan.md", "--stage", "plan", "--by", "process:talos", "--inputs", "spec.md")
        tf(p, "approve", "PROJ-1", "plan.md", "--by", "human:anna")
        d, why = guard(p, "Edit", f"{CHANGES.as_posix()}/PROJ-1/plan.md")
        check(d == "ask" and "tf task reopen PROJ-1 plan.md" in why, f"O-9: zatwierdzony plan → ask z poleceniem reopen: {d} {why}")
        r = tf(p, "reopen", "PROJ-1", "plan.md", "--by", "process:talos", "--reason", "x")
        check(r.returncode == 2, f"O-10: reopen tylko przez człowieka: {r.returncode} {r.stdout}")
        r = tf(p, "reopen", "PROJ-1", "plan.md", "--by", "human:anna")
        check(r.returncode == 2 and "--reason" in r.stdout, f"O-11: reopen wymaga powodu: {r.returncode} {r.stdout}")
        r = tf(p, "reopen", "PROJ-1", "plan.md", "--by", "human:anna", "--reason", "zmiana wymagań: limit 50 zł")
        task = json.loads((folder / "task.json").read_text(encoding="utf-8"))
        log = task.get("reopened") or []
        check(r.returncode == 0 and task["artifacts"]["plan.md"]["status"] == "szkic"
              and log and log[-1].get("file") == "plan.md" and "limit 50" in log[-1].get("reason", "")
              and log[-1].get("by") == "human:anna",
              f"O-12: reopen zdejmuje zatwierdzenie i zapisuje powód: {r.stdout} {log}")
        d, why = guard(p, "Edit", f"{CHANGES.as_posix()}/PROJ-1/plan.md")
        check(d == "", f"O-13: po reopen zapis planu bez pytania: {d} {why}")

        # test akceptacyjny zamrożony przez człowieka (plik poza katalogiem zadania)
        r = tf(p, "freeze", "PROJ-1", "tests/test_fees.py", "--by", "process:talos")
        check(r.returncode == 2, f"O-14: freeze tylko przez człowieka: {r.returncode} {r.stdout}")
        r = tf(p, "freeze", "PROJ-1", "tests/nie-ma.py", "--by", "human:anna")
        check(r.returncode == 2, f"O-15: freeze nieistniejącego pliku → kod 2: {r.returncode} {r.stdout}")
        r = tf(p, "freeze", "PROJ-1", "tests/test_fees.py", "--by", "human:anna")
        check(r.returncode == 0, f"O-16: freeze zapisuje plik testu: {r.returncode} {r.stdout}{r.stderr}")
        d, why = guard(p, "Edit", "tests/test_fees.py")
        check(d == "ask" and "PROJ-1" in why and "reopen" in why, f"O-17: zamrożony test → ask: {d} {why}")
        r = tf(p, "check", "PROJ-1")
        check(r.returncode == 0, f"O-18: check bez zmian w zamrożonym pliku → kod 0: {r.stdout}")
        (p / "tests" / "test_fees.py").write_text("def test_ac1_limit():  # AC-1\n    assert 1\n", encoding="utf-8")
        r = tf(p, "check", "PROJ-1")
        check(r.returncode == 1 and "tests/test_fees.py" in r.stdout, f"O-19: zmiana zamrożonego pliku (np. przez powłokę) → check kod 1: {r.stdout}")
        r = tf(p, "stage", "PROJ-1", "przeglad")
        check(r.returncode == 1 and "tests/test_fees.py" in r.stdout, f"O-20: etap przeglad odrzucony przy zmienionym zamrożonym pliku: {r.stdout}")
        r = tf(p, "reopen", "PROJ-1", "tests/test_fees.py", "--by", "human:anna", "--reason", "test miał błąd w danych")
        d, why = guard(p, "Edit", "tests/test_fees.py")
        check(r.returncode == 0 and d == "" and tf(p, "check", "PROJ-1").returncode == 0,
              f"O-21: reopen zdejmuje zamrożenie: {r.stdout} {d}")
        r = tf(p, "reopen", "PROJ-1", "src.py", "--by", "human:anna", "--reason", "x")
        check(r.returncode == 1, f"O-22: reopen pliku, który nie jest zatwierdzony ani zamrożony → odmowa: {r.returncode} {r.stdout}")

        # zadanie zamknięte niczego już nie chroni; uszkodzony task.json nie wywraca hooka
        tf(p, "freeze", "PROJ-1", "tests/test_fees.py", "--by", "human:anna")
        tf(p, "stage", "PROJ-1", "zamkniecie", "--force")
        d1, _ = guard(p, "Edit", "tests/test_fees.py")
        d2, _ = guard(p, "Edit", spec_rel)
        check(d1 == "" and d2 == "", f"O-23: po zamknięciu zadania pliki nie są chronione: {d1} {d2}")
        (p / CHANGES / "PROJ-9").mkdir()
        (p / CHANGES / "PROJ-9" / "task.json").write_text("{nie json", encoding="utf-8")
        d, why = guard(p, "Edit", "src.py")
        check(d == "", f"O-24: uszkodzony task.json innego zadania nie blokuje pracy: {d} {why}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów ochrony plików zadania")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
