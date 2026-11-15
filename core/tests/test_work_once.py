#!/usr/bin/env python3
"""Praca bez nadzoru (krok H19): `tf work --once` bierze jedno zadanie w trybie Auto (decyzja człowieka), zajmuje je
blokadą, prowadzi pętlę `/tf` w osobnym worktree z limitem wydatku i zapisuje wynik w dzienniku. Testy używają
fałszywego agenta (`TF_WORK_AGENT`), bez wywołań modelu.
python3 .claude/tests/test_work_once.py"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
WORK = ROOT / ".tf" / "factory" / "work.py"
TASK = ROOT / ".tf" / "factory" / "task_state.py"
CHANGES = Path("docs") / "project" / "changes"
FAKE = '''import json, os, sys, time
from pathlib import Path
out = Path(os.environ["FAKE_OUT"])
with out.open("a", encoding="utf-8") as f:
    f.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd()}) + "\\n")
time.sleep(float(os.environ.get("FAKE_SLEEP", "0")))
raise SystemExit(int(os.environ.get("FAKE_EXIT", "0")))
'''


def env(project: Path, **extra: str) -> dict:
    return {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.com", "GIT_CONFIG_GLOBAL": os.devnull,
            "TF_WORK_AGENT": f"{sys.executable} {project.parent / 'fake_agent.py'}",
            "FAKE_OUT": str(project.parent / f"{project.name}-agent.jsonl"), **extra}


def git(p: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(p), "-c", "commit.gpgsign=false", *args], capture_output=True, text=True,
                          env=env(p), timeout=60)


def work(p: Path, *args: str, **extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(WORK), *args], cwd=p, capture_output=True, text=True,
                          env=env(p, **extra), timeout=120)


def task(p: Path, key: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TASK), *args], cwd=p, capture_output=True, text=True, env=env(p),
                          timeout=60)


def project(base: Path, name: str) -> Path:
    """Repozytorium z fabryką zainstalowaną prywatnie (pliki fabryki nie są w gicie) i zadaniami."""
    p = base / name
    p.mkdir()
    (base / "fake_agent.py").write_text(FAKE, encoding="utf-8")
    git(p, "init", "-q", "-b", "main")
    (p / "README.md").write_text("x\n", encoding="utf-8")
    git(p, "add", "-A")
    git(p, "commit", "-q", "-m", "chore: init")
    eng = p / ".tf" / "factory"
    eng.mkdir(parents=True)
    (eng / "marker.py").write_text("# silnik\n", encoding="utf-8")
    skill = p / ".claude" / "skills" / "tf"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# tf\n", encoding="utf-8")
    (p / ".claude" / "factory-manifest.json").write_text(json.dumps(
        {"version": "10.20.0", "files": {".tf/factory/marker.py": "x", ".claude/skills/tf/SKILL.md": "y"}}), encoding="utf-8")
    (p / ".git" / "info" / "exclude").write_text(".tf/\n.claude/\n", encoding="utf-8")
    return p


def agent_calls(p: Path) -> list[dict]:
    f = p.parent / f"{p.name}-agent.jsonl"
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()] if f.is_file() else []


def log(p: Path) -> list[dict]:
    f = p / ".tf" / "logs" / "work.jsonl"
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()] if f.is_file() else []


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = project(base, "main")
        task(p, "", "start", "IMP-1", "--title", "Literówka w stopce")                       # tryb zwykły
        task(p, "", "start", "IMP-2", "--title", "Eksport CSV", "--mode", "auto")
        task(p, "", "start", "IMP-3", "--title", "Płatności", "--weight", "pelna", "--mode", "auto")
        task(p, "", "start", "IMP-4", "--title", "Sortowanie", "--mode", "auto")

        # bez limitu wydatku: odmowa, nic nie powstaje
        r = work(p, "--once")
        check(r.returncode == 2 and "--budget" in r.stdout + r.stderr and not (p / ".tf" / "worktrees").exists()
              and not agent_calls(p), f"WO-1: bez limitu wydatku odmowa: {r.returncode} {r.stdout}{r.stderr}")

        # --dry-run: wybrane zadanie, polecenie, bez skutków
        r = work(p, "--once", "--budget", "3", "--dry-run")
        check(r.returncode == 0 and "IMP-2" in r.stdout and "--max-budget-usd 3" in r.stdout and "/tf IMP-2 --auto" in r.stdout
              and not (p / ".tf" / "worktrees").exists() and not (p / ".tf" / "locks").exists() and not agent_calls(p),
              f"WO-2: dry-run pokazuje zadanie IMP-2 (najstarsze w trybie Auto) i polecenie, niczego nie tworzy: {r.stdout}{r.stderr}")

        # przebieg: worktree na gałęzi zadania, pliki fabryki i zadania skopiowane, agent z limitem, dziennik
        r = work(p, "--once", "--budget", "3")
        calls = agent_calls(p)
        wt = p / ".tf" / "worktrees" / "IMP-2"
        check(r.returncode == 0 and len(calls) == 1 and Path(calls[0]["cwd"]).resolve() == wt.resolve(),
              f"WO-3: agent uruchomiony raz, w worktree zadania: {r.returncode} {r.stdout}{r.stderr} {calls}")
        argv = calls[0]["argv"] if calls else []
        check("-p" in argv and "/tf IMP-2 --auto --budget 3" in argv and "--max-budget-usd" in argv
              and argv[argv.index("--max-budget-usd") + 1] == "3" and "--permission-mode" in argv
              and argv[argv.index("--permission-mode") + 1] == "dontAsk",
              f"WO-4: polecenie agenta z /tf --auto, limitem wydatku i trybem dontAsk: {argv}")
        branch = git(wt, "branch", "--show-current").stdout.strip() if wt.is_dir() else ""
        check(branch == "story/imp-2" and (wt / ".tf" / "factory" / "marker.py").is_file()
              and (wt / ".claude" / "skills" / "tf" / "SKILL.md").is_file()
              and (wt / CHANGES / "IMP-2" / "task.json").is_file(),
              f"WO-5: worktree na gałęzi story/imp-2 z plikami fabryki z manifestu i folderem zadania: {branch}")
        entries = log(p)
        check(len(entries) == 1 and entries[0].get("key") == "IMP-2" and entries[0].get("exit") == 0
              and entries[0].get("started") and entries[0].get("ended") and entries[0].get("worktree"),
              f"WO-6: wpis w .tf/logs/work.jsonl: {entries}")
        check(not (p / ".tf" / "locks" / "IMP-2.json").exists(), "WO-7: blokada zwolniona po przebiegu")

        # następny przebieg: IMP-2 ma już worktree (wznowienie tylko przez --key), więc bierze IMP-4; IMP-1 i IMP-3 nigdy
        r = work(p, "--once", "--budget", "3", "--dry-run")
        check("IMP-4" in r.stdout and "IMP-1" not in r.stdout and "IMP-3" not in r.stdout,
              f"WO-8: zadanie z worktree pominięte, waga pełna i tryb zwykły nigdy: {r.stdout}")
        r = work(p, "--once", "--budget", "3", "--key", "IMP-3", "--dry-run")
        check(r.returncode == 2 and "pełn" in r.stdout + r.stderr, f"WO-9: --key zadania o wadze pełnej → odmowa: {r.stdout}{r.stderr}")
        r = work(p, "--once", "--budget", "3", "--key", "IMP-1", "--dry-run")
        check(r.returncode == 2 and "auto" in (r.stdout + r.stderr).lower(),
              f"WO-10: --key zadania bez trybu Auto → odmowa z poleceniem tf task mode: {r.stdout}{r.stderr}")
        r = work(p, "--once", "--budget", "3", "--key", "IMP-2")
        check(r.returncode == 0 and len(agent_calls(p)) == 2 and Path(agent_calls(p)[-1]["cwd"]).resolve() == wt.resolve(),
              f"WO-11: --key zadania z worktree wznawia w tym samym worktree: {r.returncode} {r.stdout}{r.stderr}")

        # błąd agenta: kod wyjścia przekazany, blokada zwolniona, wpis w dzienniku
        r = work(p, "--once", "--budget", "3", FAKE_EXIT="5")
        check(r.returncode == 5 and not (p / ".tf" / "locks" / "IMP-4.json").exists() and log(p)[-1].get("exit") == 5,
              f"WO-12: błąd agenta → kod 5, blokada zwolniona, wpis: {r.returncode} {r.stdout}{r.stderr} {log(p)[-1:]}")

        # nic do zrobienia → kod 3
        r = work(p, "--once", "--budget", "3")
        check(r.returncode == 3, f"WO-13: brak zadania do wzięcia → kod 3: {r.returncode} {r.stdout}{r.stderr}")

        # dwa równoległe przebiegi, jedno zadanie: agent uruchomiony raz
        q = project(base, "race")
        task(q, "", "start", "IMP-7", "--title", "Filtr dat", "--mode", "auto")
        procs = [subprocess.Popen([sys.executable, str(WORK), "--once", "--budget", "2"], cwd=q, env=env(q, FAKE_SLEEP="2"),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        codes = sorted(pr.wait(timeout=120) for pr in procs)
        check(codes == [0, 3] and len(agent_calls(q)) == 1, f"WO-14: dwa równoległe przebiegi → jeden bierze zadanie: {codes} {agent_calls(q)}")

        # blokada martwego procesu starsza niż próg → przejęta; blokada żywego procesu → zadanie pominięte
        z = project(base, "stale")
        task(z, "", "start", "IMP-8", "--title", "Raport", "--mode", "auto")
        locks = z / ".tf" / "locks"
        locks.mkdir(parents=True)
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        host = socket.gethostname()
        (locks / "IMP-8.json").write_text(json.dumps({"pid": os.getpid(), "host": host, "at": time.time()}), encoding="utf-8")
        r = work(z, "--once", "--budget", "2")
        check(r.returncode == 3 and not agent_calls(z), f"WO-15: zadanie zajęte przez żywy proces → pominięte: {r.returncode} {r.stdout}")
        (locks / "IMP-8.json").write_text(json.dumps({"pid": dead.pid, "host": host, "at": time.time() - 7 * 3600}),
                                          encoding="utf-8")
        r = work(z, "--once", "--budget", "2")
        check(r.returncode == 0 and len(agent_calls(z)) == 1 and "przej" in r.stdout,
              f"WO-16: martwa blokada starsza niż 6 h → przejęta z ostrzeżeniem: {r.returncode} {r.stdout}{r.stderr}")

    # tf work w launcherze i w opisie poleceń
    tf = (ROOT / ".tf" / "factory" / "tf.py").read_text(encoding="utf-8")
    check("tf work --once" in tf and '"work.py"' in tf, "WO-17: tf work --once w opisie i w dyspozytorze tf.py")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów pracy bez nadzoru")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
