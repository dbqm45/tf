#!/usr/bin/env python3
"""Praca bez nadzoru (krok H19): `tf work --once` bierze jedno zadanie, które człowiek oznaczył trybem Auto
(`tf task mode <KEY> auto`), i prowadzi je pętlą `/tf` w osobnym worktree z limitem wydatku. Nie scala i nie wdraża:
wynikiem jest gałąź `story/<key>` z PR albo blok STOP w worktree zadania.

  tf work --once --budget <USD> [--key <KEY>] [--base <gałąź>] [--dry-run]

Zadanie do wzięcia: tryb Auto, waga lekka albo zwykła, etap przed PR, nie czeka na człowieka, nie ma jeszcze worktree
(wznowienie w istniejącym worktree tylko przez `--key`) i nie jest zajęte przez inny przebieg (`.tf/locks/<KEY>.json`).
Kod wyjścia: 0 — przebieg zakończony, 2 — odmowa, 3 — nie ma zadania do wzięcia, inny — kod agenta.
Agent: `claude -p "/tf <KEY> --auto --budget <USD>" --max-budget-usd <USD> --permission-mode <tryb>`; zmienna
`TF_WORK_AGENT` podmienia polecenie `claude` (testy). Dziennik: `.tf/logs/work.jsonl`.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa nie zna „✓” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

CHANGES = Path("docs") / "project" / "changes"
LOCKS = Path(".tf") / "locks"
WORKTREES = Path(".tf") / "worktrees"
LOG = Path(".tf") / "logs" / "work.jsonl"
MANIFEST = Path(".claude") / "factory-manifest.json"
OWN_CONFIG = Path(".tf") / "config"
OPEN_STAGES = ("przyjecie", "specyfikacja", "plan", "realizacja", "przeglad")
DEFAULTS = {"budget_usd": 0, "permission_mode": "dontAsk", "lock_hours": 6, "timeout_minutes": 180}
KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def config(root: Path) -> dict:
    """Sekcja `work` konfiguracji: domyślna silnika z nadpisaniem projektu; bez konfiguracji — wartości domyślne."""
    try:
        spec = importlib.util.spec_from_file_location("tf_packs_cfg", Path(__file__).resolve().with_name("packs.py"))
        packs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packs)
        cfg = packs.load_yaml(Path(__file__).resolve().with_name("config.yaml"))
        own = root / OWN_CONFIG / "config.yaml"
        if own.is_file():
            cfg = packs.deep_merge(cfg, packs.load_yaml(own))
        section = cfg.get("work") if isinstance(cfg.get("work"), dict) else {}
    except Exception:  # noqa: BLE001 — brak konfiguracji to ustawienia domyślne
        section = {}
    return {**DEFAULTS, **section}


def load_task(root: Path, key: str) -> dict | None:
    try:
        data = json.loads((root / CHANGES / key / "task.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def waits_for_human(root: Path, key: str) -> bool:
    try:
        run = json.loads((root / ".tf" / "runs" / key / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(run, dict) and run.get("stage") == "needs"


def refusal(root: Path, task: dict) -> str | None:
    """Dlaczego zadania nie wolno wziąć bez nadzoru; None — wolno."""
    key = task.get("key", "?")
    if task.get("closed") or task.get("stage") not in OPEN_STAGES:
        return f"{key}: etap {task.get('stage')} — praca bez nadzoru prowadzi zadanie tylko do PR"
    if task.get("weight") == "pelna":
        return f"{key}: waga pełna — bez nadzoru tylko zadania o wadze lekkiej i zwykłej (pełna wymaga panelu i człowieka)"
    if task.get("mode") != "auto":
        return (f"{key}: tryb {task.get('mode') or 'zwykly'}, nie auto — zgodę na pracę bez nadzoru daje człowiek: "
                f"tf task mode {key} auto")
    if waits_for_human(root, key):
        return f"{key}: czeka na człowieka (tf status) — po odpowiedzi wróci do kolejki"
    return None


def candidates(root: Path) -> list[dict]:
    """Zadania do wzięcia, najstarsze pierwsze; pomija te z worktree (wznowienie tylko przez --key)."""
    out = []
    for f in sorted((root / CHANGES).glob("*/task.json")):
        task = load_task(root, f.parent.name)
        if task and KEY.match(f.parent.name) and refusal(root, task) is None and not (root / WORKTREES / f.parent.name).exists():
            out.append(task)
    return sorted(out, key=lambda t: str(t.get("created") or ""))


def alive(pid) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True            # brak uprawnień albo system bez sygnałów — traktuj jak żywy
    return True


def claim(root: Path, key: str, hours: float) -> tuple[bool, str]:
    """Zajmuje zadanie atomowo (`O_CREAT|O_EXCL`). Martwą blokadę tego hosta starszą niż `hours` przejmuje."""
    folder = root / LOCKS
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{key}.json"
    note = ""
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            try:
                held = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                held = {}
            at = held.get("at") if isinstance(held.get("at"), (int, float)) else path.stat().st_mtime
            stale = (time.time() - at > hours * 3600 and held.get("host") == socket.gethostname()
                     and not alive(held.get("pid")))
            if not stale:
                return False, ""
            note = (f"⚠ blokada {key} martwego procesu {held.get('pid')} z {datetime.fromtimestamp(at).isoformat(timespec='minutes')} "
                    "przejęta")
            path.unlink(missing_ok=True)
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "host": socket.gethostname(), "at": time.time()}, f)
        return True, note
    return False, ""


def release(root: Path, key: str) -> None:
    (root / LOCKS / f"{key}.json").unlink(missing_ok=True)


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=120)


def inside(root: Path, rel: str) -> Path | None:
    p = (root / rel).resolve()
    return p if not Path(rel).is_absolute() and root.resolve() in p.parents else None


def copy_missing(src: Path, dst: Path) -> int:
    """Kopiuje plik albo katalog, pomijając to, co w miejscu docelowym już jest; zwraca liczbę plików."""
    if src.is_file():
        if dst.exists():
            return 0
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return 1
    n = 0
    for f in sorted(src.rglob("*")) if src.is_dir() else []:
        if f.is_file() and "__pycache__" not in f.parts:
            n += copy_missing(f, dst / f.relative_to(src))
    return n


def prepare_worktree(root: Path, key: str, base: str) -> tuple[Path | None, str]:
    """Worktree zadania na gałęzi `story/<key>`; przy instalacji prywatnej pliki fabryki nie są w gicie, więc kopiuje
    pliki z manifestu, konfigurację projektu i folder zadania, których w worktree brakuje."""
    wt = root / WORKTREES / key
    if not wt.exists():
        branch = f"story/{key.lower()}"
        has = git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0
        r = git(root, "worktree", "add", "-q", str(wt), branch) if has else \
            git(root, "worktree", "add", "-q", "-b", branch, str(wt), base)
        if r.returncode != 0:
            return None, f"git worktree add odrzucony: {(r.stdout + r.stderr).strip()}"
    try:
        files = json.loads((root / MANIFEST).read_text(encoding="utf-8")).get("files") or {}
    except (OSError, ValueError, AttributeError):
        files = {}
    rels = [MANIFEST.as_posix(), ".claude/settings.json", OWN_CONFIG.as_posix(), (CHANGES / key).as_posix(),
            *[r for r in files if isinstance(r, str)]]
    copied = sum(copy_missing(src, wt / rel) for rel in dict.fromkeys(rels) if (src := inside(root, rel)) and src.exists())
    return wt, f"{copied} plików fabryki i zadania skopiowanych do worktree" if copied else ""


def agent_command(key: str, budget: str, mode: str) -> list[str]:
    agent = shlex.split(os.environ.get("TF_WORK_AGENT") or "claude")
    return [*agent, "-p", f"/tf {key} --auto --budget {budget}", "--max-budget-usd", budget, "--permission-mode", mode]


def budget_text(value) -> str | None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return f"{v:g}" if 0 < v < 10_000 else None


def write_log(root: Path, entry: dict) -> None:
    f = root / LOG
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as h:
        h.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_once(root: Path, key: str | None, budget_arg: str | None, base: str | None, dry: bool) -> int:
    cfg = config(root)
    budget = budget_text(budget_arg if budget_arg is not None else cfg.get("budget_usd"))
    if budget is None:
        print("✗ podaj limit wydatku: tf work --once --budget <USD> (albo work.budget_usd w .tf/config/config.yaml) — "
              "bez limitu praca bez nadzoru nie rusza")
        return 2
    mode = str(cfg.get("permission_mode") or "dontAsk")
    if key:
        task = load_task(root, key) if KEY.match(key) else None
        if task is None:
            print(f"✗ nie ma zadania {key}")
            return 2
        why = refusal(root, task)
        if why:
            print(f"✗ {why}")
            return 2
        queue = [task]
    else:
        queue = candidates(root)
    for task in queue:
        k = task["key"]
        if dry:
            print(f"• zadanie: {k} — {task.get('title', '')}")
            print(f"• worktree: {(root / WORKTREES / k).as_posix()} (gałąź story/{k.lower()} od {base or 'HEAD'})")
            print(f"• polecenie: {shlex.join(agent_command(k, budget, mode))}")
            return 0
        ok, note = claim(root, k, float(cfg.get("lock_hours") or 6))
        if not ok:
            continue
        if note:
            print(note)
        started = now()
        try:
            wt, info = prepare_worktree(root, k, base or "HEAD")
            if wt is None:
                print(f"✗ {k}: {info}")
                write_log(root, {"key": k, "started": started, "ended": now(), "exit": 2, "error": info})
                return 2
            if info:
                print(f"• {info}")
            print(f"• {k}: pętla /tf w {wt.as_posix()}, limit {budget} USD")
            try:
                code = subprocess.run(agent_command(k, budget, mode), cwd=wt,
                                      timeout=float(cfg.get("timeout_minutes") or 180) * 60).returncode
            except FileNotFoundError:
                print("✗ nie ma polecenia claude (Claude Code) w PATH")
                code = 127
            except subprocess.TimeoutExpired:
                print(f"✗ {k}: przebieg przerwany po {cfg.get('timeout_minutes')} min")
                code = 124
            after = load_task(wt, k) or {}
            entry = {"key": k, "started": started, "ended": now(), "exit": code, "stage": after.get("stage"),
                     "worktree": wt.relative_to(root).as_posix(), "budget_usd": float(budget)}
            write_log(root, entry)
            print(f"{'✓' if code == 0 else '✗'} {k}: kod {code}, etap {after.get('stage') or '?'} — wynik w "
                  f"{entry['worktree']} (tf status w worktree); scalenie zostaje dla człowieka")
            return code
        finally:
            release(root, k)
    print("• nie ma zadania do wzięcia: tryb Auto (tf task mode <KEY> auto), waga lekka albo zwykła, bez worktree "
          "i niezajęte" + (" — wszystkie pasujące są zajęte" if queue else ""))
    return 3


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tf work", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--once", action="store_true", help="jedno zadanie i koniec (jedyny tryb na razie)")
    ap.add_argument("--key", default=None)
    ap.add_argument("--budget", default=None)
    ap.add_argument("--base", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv[1:])
    if not args.once:
        print("✗ użycie: tf work --once --budget <USD> [--key <KEY>] [--base <gałąź>] [--dry-run]")
        return 2
    return run_once(Path.cwd(), args.key, args.budget, args.base, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
