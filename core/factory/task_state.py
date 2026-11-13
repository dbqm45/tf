#!/usr/bin/env python3
"""
tf task — stan zadania w jednym miejscu: `docs/project/changes/<KEY>/task.json` i indeks zadań. Jedyny pisarz
tych plików; model woła polecenia, nie edytuje stanu ręcznie. Bez modelu i bez sieci.

  tf task start <KEY> --title "<tytuł>" [--weight lekka|zwykla|pelna] [--mode plan|zwykly|auto]
  tf task stage <KEY> <etap> [--force]
  tf task status <KEY> [--json]

Klucz: numer z trackera (PROJ-123), klucz pdi (CHG-12, TSK-57) albo T-<RRRRMMDD>-<slug>. Etapy idą w kolejności:
przyjecie → specyfikacja → plan → realizacja → przeglad → pr → wdrozenie → zamkniecie; cofnięcie wymaga --force.
`start` w istniejącym katalogu zmiany (np. z trybu pdi) dokłada sam `task.json` i nie rusza innych plików.
Każdy zapis odświeża `docs/project/changes/INDEX.md` — jeden wiersz na zadanie, żeby agent nie przeglądał folderów.

Kod wyjścia: 0 — zrobione; 1 — odmowa (zadanie istnieje, nie ma go, etap wstecz); 2 — błąd wywołania.
Tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne też piszą i czytają UTF-8

SCHEMA = 1
CHANGES = Path("docs") / "project" / "changes"
KEY = re.compile(r"[A-Z][A-Z0-9]*-[A-Za-z0-9][A-Za-z0-9-]*")
STAGES = ("przyjecie", "specyfikacja", "plan", "realizacja", "przeglad", "pr", "wdrozenie", "zamkniecie")
WEIGHTS = ("lekka", "zwykla", "pelna")
MODES = ("plan", "zwykly", "auto")
INDEX_HEAD = ("# Zadania\n\nGenerowany przez `tf task` — nie edytuj ręcznie. Szczegóły zadania: "
              "`docs/project/changes/<klucz>/`.\n\n| Klucz | Tytuł | Etap | Zmieniono |\n|---|---|---|---|\n")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fail(msg: str, code: int = 1) -> int:
    print(f"✗ {msg}")
    return code


def task_path(root: Path, key: str) -> Path:
    return root / CHANGES / key / "task.json"


def load(root: Path, key: str) -> dict | None:
    try:
        data = json.loads(task_path(root, key).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_atomic(path: Path, text: str) -> None:
    """Zapis przez plik tymczasowy i zamianę — przerwany zapis nie zostawia połowy pliku."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def save(root: Path, task: dict) -> None:
    write_atomic(task_path(root, task["key"]), json.dumps(task, ensure_ascii=False, indent=1) + "\n")
    write_index(root)


def write_index(root: Path) -> None:
    rows = []
    base = root / CHANGES
    for f in sorted(base.glob("*/task.json")):
        t = load(root, f.parent.name)
        if not t:
            continue
        title = str(t.get("title", "")).replace("|", "\\|").replace("\n", " ")
        rows.append(f"| {t.get('key', f.parent.name)} | {title} | {t.get('stage', '?')} | {str(t.get('updated', ''))[:10]} |")
    write_atomic(base / "INDEX.md", INDEX_HEAD + "\n".join(rows) + ("\n" if rows else ""))


def cmd_start(root: Path, key: str, title: str, weight: str, mode: str) -> int:
    if load(root, key) is not None:
        return fail(f"zadanie {key} już istnieje ({CHANGES / key / 'task.json'}) — stan: tf task status {key}")
    stamp = now()
    save(root, {"schema": SCHEMA, "key": key, "title": title, "stage": STAGES[0], "weight": weight, "mode": mode,
                "created": stamp, "updated": stamp})
    print(f"✓ zadanie {key} założone: {CHANGES / key}/ (etap: {STAGES[0]})")
    return 0


def cmd_stage(root: Path, key: str, stage: str, force: bool) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    was = task.get("stage", STAGES[0])
    if was in STAGES and STAGES.index(stage) < STAGES.index(was) and not force:
        return fail(f"etap {stage} jest wcześniejszy niż obecny ({was}); cofnięcie wymaga --force")
    task["stage"], task["updated"] = stage, now()
    save(root, task)
    print(f"✓ {key}: {was} → {stage}")
    return 0


def cmd_status(root: Path, key: str, as_json: bool) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    if as_json:
        print(json.dumps(task, ensure_ascii=False, indent=1))
        return 0
    done = STAGES.index(task["stage"]) + 1 if task.get("stage") in STAGES else 0
    print(f"{task['key']} — {task.get('title', '')}\n"
          f"etap: {task.get('stage', '?')} ({done} z {len(STAGES)}) · waga: {task.get('weight', '?')} · "
          f"tryb: {task.get('mode', '?')} · zmieniono: {task.get('updated', '?')}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tf task", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("key")
    s.add_argument("--title", default=None)
    s.add_argument("--weight", default="zwykla")
    s.add_argument("--mode", default="zwykly")
    g = sub.add_parser("stage")
    g.add_argument("key")
    g.add_argument("stage")
    g.add_argument("--force", action="store_true")
    q = sub.add_parser("status")
    q.add_argument("key")
    q.add_argument("--json", action="store_true")
    try:
        a = ap.parse_args(argv[1:])
    except SystemExit as e:
        return 2 if e.code else 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not KEY.fullmatch(a.key):
        return fail(f"klucz „{a.key}” nie pasuje do wzorca (np. PROJ-123, CHG-12, T-20261113-limit)", 2)
    if a.cmd == "start":
        if not a.title or not a.title.strip():
            return fail("podaj tytuł: tf task start <KEY> --title \"<tytuł>\"", 2)
        if a.weight not in WEIGHTS:
            return fail(f"nieznana waga „{a.weight}” — do wyboru: {', '.join(WEIGHTS)}", 2)
        if a.mode not in MODES:
            return fail(f"nieznany tryb „{a.mode}” — do wyboru: {', '.join(MODES)}", 2)
        return cmd_start(root, a.key, a.title.strip(), a.weight, a.mode)
    if a.cmd == "stage":
        if a.stage not in STAGES:
            return fail(f"nieznany etap „{a.stage}” — kolejno: {', '.join(STAGES)}", 2)
        return cmd_stage(root, a.key, a.stage, a.force)
    return cmd_status(root, a.key, a.json)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
