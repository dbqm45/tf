#!/usr/bin/env python3
"""Testy bramki jakości `.claude/hooks/quality_gate.py` (Stop/SubagentStop: build i testy zielone przed zakończeniem)
i blokady testów `.claude/hooks/test_lock.py` w tymczasowym repozytorium git. python3 tests/test_quality_gate.py"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
GATE = ROOT / ".claude" / "hooks" / "quality_gate.py"
LOCK = ROOT / ".claude" / "hooks" / "test_lock.py"

CHECK = """import pathlib, sys, time
p = pathlib.Path(__file__).parent
(p / "runs.log").open("a").write("run\\n")
mode = (p / "mode.txt").read_text().strip() if (p / "mode.txt").exists() else "pass"
if mode == "slow":
    time.sleep(5)
if mode == "long":   # długi log: pierwszy błąd na początku, podsumowanie na końcu
    print("PIERWSZY BLAD test_start: oczekiwano 1, jest 2")
    for i in range(400):
        print(f"linia {i:04d} " + ("SRODEK " if i == 200 else "") + "x" * 30)
    print("PODSUMOWANIE 1 failed, 399 passed")
    sys.exit(1)
if mode == "fail":
    print("FAILED test_suma: oczekiwano 4, jest 5")
    sys.exit(1)
print("2 passed")
"""


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def setup(tmp: Path, config: dict | None) -> Path:
    repo = tmp / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "docs").mkdir()
    (repo / "src" / "app.py").write_text("x = 1\n")
    (repo / "docs" / "notes.md").write_text("# n\n")
    (repo / "check.py").write_text(CHECK)
    git(repo, "init", "-q")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    (repo / ".claude").mkdir()
    if config is not None:
        (repo / ".claude" / "quality-gate.json").write_text(json.dumps(config))
    return repo


def hook(repo, event="Stop", **env):
    data = {"hook_event_name": event, "stop_hook_active": False, "session_id": "s1"}
    return subprocess.run([sys.executable, str(GATE)], input=json.dumps(data), capture_output=True, text=True,
                          timeout=60, env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo), **env})


def runs(repo) -> int:
    f = repo / "runs.log"
    return len(f.read_text().splitlines()) if f.exists() else 0


def blocked(r) -> dict | None:
    try:
        out = json.loads(r.stdout) if r.stdout.strip() else {}
    except ValueError:
        return None
    return out if out.get("decision") == "block" else None


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    for f in (GATE, LOCK):
        if not f.is_file():
            print(f"✗ brak {f}")
            return 1
    cfg = {"command": f"{sys.executable} check.py", "watch": ["src/"], "timeout": 3, "max_blocks": 2}
    with tempfile.TemporaryDirectory() as t:
        repo = setup(Path(t) / "a", None)
        (repo / "src" / "app.py").write_text("x = 2\n")
        r = hook(repo)
        check(r.returncode == 0 and not r.stdout.strip() and runs(repo) == 0, f"Q-1: bez konfiguracji nic nie robi: {r.stdout}{r.stderr}")

        repo = setup(Path(t) / "b", cfg)
        r = hook(repo)
        check(r.returncode == 0 and runs(repo) == 0, f"Q-2: bez zmian testy nie są uruchamiane: {runs(repo)}")

        (repo / "src" / "app.py").write_text("x = 2\n")
        (repo / "mode.txt").write_text("fail")
        r = hook(repo)
        b = blocked(r)
        check(b is not None and "test_suma" in b.get("reason", "") and runs(repo) == 1,
              f"Q-3: czerwone testy po zmianie w watch → blokada z końcem wyjścia: {r.stdout}{r.stderr}")

        (repo / "mode.txt").write_text("pass")
        (repo / "src" / "app.py").write_text("x = 3\n")
        r = hook(repo)
        n = runs(repo)
        r2 = hook(repo)
        check(blocked(r) is None and blocked(r2) is None and runs(repo) == n,
              f"Q-4: zielone → bez blokady, ten sam diff drugi raz bez uruchomienia: {r.stdout} {runs(repo)} vs {n}")

        (repo / "docs" / "notes.md").write_text("# zmiana\n")
        n = runs(repo)
        r = hook(repo)
        check(blocked(r) is None and runs(repo) == n, f"Q-5: zmiana poza watch nie uruchamia testów: {runs(repo)} vs {n}")

        # katalog zadania (docs/project/changes/, pisze go `tf task`) nie jest zmianą kodu — także bez `watch`
        wide = setup(Path(t) / "b2", {k: v for k, v in cfg.items() if k != "watch"})
        (wide / "mode.txt").write_text("fail")
        git(wide, "add", "-A")
        git(wide, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "konfiguracja")
        (wide / "docs" / "project" / "changes" / "T-1").mkdir(parents=True)
        (wide / "docs" / "project" / "changes" / "T-1" / "task.json").write_text("{}")
        (wide / "docs" / "project" / "changes" / "INDEX.md").write_text("# Zadania\n")
        r = hook(wide)
        check(blocked(r) is None and runs(wide) == 0, f"Q-5a: zmiana tylko w katalogu zadania nie uruchamia bramki: {r.stdout} {runs(wide)}")
        (wide / "src" / "app.py").write_text("x = 9\n")
        r = hook(wide)
        check(blocked(r) is not None and runs(wide) == 1, f"Q-5b: zmiana kodu obok plików zadania nadal uruchamia bramkę: {r.stdout} {runs(wide)}")

        (repo / "mode.txt").write_text("fail")
        (repo / "src" / "app.py").write_text("x = 4\n")
        (repo / ".claude" / "quality-gate.expected-red").write_text("partia K2: test czerwony z planu")
        r = hook(repo)
        check(blocked(r) is None, f"Q-6: zadeklarowana czerwona partia (expected-red) przepuszczona: {r.stdout}")
        (repo / ".claude" / "quality-gate.expected-red").unlink()

        r1, r2, r3 = hook(repo), hook(repo), hook(repo)
        check(blocked(r1) and blocked(r2) and blocked(r3) is None and "człowiek" in (r3.stdout + r3.stderr).lower(),
              f"Q-7: po max_blocks blokadach tego samego diffu przepuszcza z komunikatem: {r3.stdout}{r3.stderr}")

        (repo / "src" / "app.py").write_text("x = 5\n")
        n = runs(repo)
        r = hook(repo, QG_GATE_DISABLE="1")
        check(blocked(r) is None and runs(repo) == n, f"Q-8: QG_GATE_DISABLE=1 wyłącza bramkę: {r.stdout}")

        r = hook(repo, event="SubagentStop")
        check(blocked(r) is not None, f"Q-9: SubagentStop też blokuje czerwone: {r.stdout}{r.stderr}")

        (repo / "mode.txt").write_text("slow")
        (repo / "src" / "app.py").write_text("x = 6\n")
        r = hook(repo)
        b = blocked(r)
        check(b is not None and "limit" in b.get("reason", "").lower(), f"Q-10: przekroczony timeout → blokada z opisem: {r.stdout}{r.stderr}")

        # blokada testów
        holder = subprocess.Popen([sys.executable, str(LOCK), "--", sys.executable, "-c", "import time; time.sleep(4)"],
                                  cwd=repo, env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo)})
        time.sleep(1)
        r = subprocess.run([sys.executable, str(LOCK), "--", sys.executable, "-c", "print('uruchomiono')"], cwd=repo,
                           capture_output=True, text=True, timeout=30,
                           env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo), "QG_LOCK_WAIT": "1"})
        check(r.returncode == 75 and "uruchomiono" not in r.stdout and "LOCK" in (r.stdout + r.stderr).upper(),
              f"L-1: blokada zajęta dłużej niż QG_LOCK_WAIT → kod 75 bez uruchamiania: {r.returncode} {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(LOCK), "--", sys.executable, "-c", "print('uruchomiono')"], cwd=repo,
                           capture_output=True, text=True, timeout=30,
                           env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo), "QG_LOCK_WAIT": "1",
                                "TF_TEST_LOCK_HELD": "1"})
        check(r.returncode == 0 and "uruchomiono" in r.stdout, f"L-2: re-entrant (TF_TEST_LOCK_HELD) uruchamia od razu: {r.stdout}{r.stderr}")
        holder.wait(timeout=20)
        r = subprocess.run([sys.executable, str(LOCK), "--", sys.executable, "-c", "import sys; sys.exit(3)"], cwd=repo,
                           capture_output=True, text=True, timeout=30, env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo)})
        check(r.returncode == 3, f"L-3: wolna blokada → kod wyjścia polecenia: {r.returncode}")

    # ograniczone wyjście: agent dostaje początek i koniec długiego logu, całość jest w pliku
    with tempfile.TemporaryDirectory() as t:
        repo = setup(Path(t) / "o1", cfg)
        (repo / "src" / "app.py").write_text("x = 3\n")
        (repo / "mode.txt").write_text("long")
        b = blocked(hook(repo)) or {}
        reason = b.get("reason", "")
        full = repo / ".tf" / "logs" / "quality-gate-output.txt"
        saved = full.read_text(encoding="utf-8") if full.is_file() else ""
        check("PIERWSZY BLAD test_start" in reason and "PODSUMOWANIE 1 failed" in reason and "SRODEK" not in reason,
              f"B-1: długi log → w komunikacie początek i koniec, bez środka: {reason[:200]} … {reason[-200:]}")
        check(".tf/logs/quality-gate-output.txt" in reason and "pominięto" in reason and len(reason) < 5000,
              f"B-2: komunikat podaje, ile pominięto i gdzie jest całość; pozostaje krótki ({len(reason)} znaków)")
        check("PIERWSZY BLAD" in saved and "SRODEK" in saved and "PODSUMOWANIE" in saved,
              f"B-3: pełne wyjście zapisane w .tf/logs/quality-gate-output.txt ({len(saved)} znaków)")
        (repo / "src" / "app.py").write_text("x = 4\n")
        (repo / "mode.txt").write_text("fail")
        b = blocked(hook(repo)) or {}
        check("test_suma" in b.get("reason", "") and "pominięto" not in b.get("reason", ""),
              f"B-4: krótkie wyjście trafia do komunikatu w całości, bez dopisku o pominięciu: {b.get('reason', '')[-200:]}")
        now = full.read_text(encoding="utf-8") if full.is_file() else ""
        check("test_suma" in now and "SRODEK" not in now, "B-5: plik z pełnym wyjściem zawiera ostatni przebieg, nie poprzedni")

    # stan bramki w zwykłym języku (tf doctor, start sesji)
    def status(repo, *flags, **env):
        base = {k: v for k, v in os.environ.items() if k != "QG_GATE_DISABLE"}
        return subprocess.run([sys.executable, str(GATE), "--status", *flags], capture_output=True, text=True,
                              timeout=30, env={**base, "CLAUDE_PROJECT_DIR": str(repo), **env})

    with tempfile.TemporaryDirectory() as t:
        repo = setup(Path(t) / "s1", None)
        r = status(repo)
        check(r.returncode == 0 and "wyłączona" in r.stdout and "quality-gate.json" in r.stdout
              and "nie zablokuje czerwonych testów" in r.stdout, f"S-1: brak konfiguracji → wyłączona, z powodem i skutkiem: {r.stdout}{r.stderr}")
        repo = setup(Path(t) / "s2", cfg)
        r = status(repo)
        check(r.returncode == 0 and "włączona" in r.stdout and "check.py" in r.stdout and "wyłączona" not in r.stdout,
              f"S-2: konfiguracja z poleceniem → włączona, z poleceniem: {r.stdout}{r.stderr}")
        r = status(repo, "--quiet-ok")
        check(r.returncode == 0 and r.stdout.strip() == "", f"S-3: --quiet-ok milczy, gdy bramka działa: {r.stdout!r}")
        r = status(repo, "--quiet-ok", QG_GATE_DISABLE="1")
        check("wyłączona" in r.stdout and "QG_GATE_DISABLE" in r.stdout, f"S-4: wyłącznik w środowisku → wyłączona: {r.stdout}")
        (repo / ".claude" / "settings.local.json").write_text(json.dumps({"env": {"QG_GATE_DISABLE": "1"}}))
        r = status(repo)
        check("wyłączona" in r.stdout and "settings.local.json" in r.stdout, f"S-5: wyłącznik w ustawieniach → wskazany plik: {r.stdout}")
        (repo / ".claude" / "settings.local.json").unlink()
        (repo / ".claude" / "quality-gate.expected-red").write_text("partia TDD: import CDR")
        r = status(repo, "--quiet-ok")
        check("przepuszcza czerwone testy" in r.stdout and "import CDR" in r.stdout, f"S-6: znacznik czerwonej partii → ostrzeżenie z powodem: {r.stdout}")
        repo = setup(Path(t) / "s7", {"watch": ["src/"]})
        r = status(repo)
        check("wyłączona" in r.stdout and "command" in r.stdout, f"S-7: konfiguracja bez polecenia → wyłączona: {r.stdout}")
        (repo / ".claude" / "quality-gate.json").write_text("{nie json")
        r = status(repo)
        check(r.returncode == 0 and "wyłączona" in r.stdout and "JSON" in r.stdout, f"S-8: uszkodzony plik → wyłączona, bez wyjątku: {r.stdout}{r.stderr}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów bramki jakości")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
