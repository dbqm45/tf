#!/usr/bin/env python3
"""
Szablon hooka PostToolUse (Write|Edit): lokalne bramki jakości po edycji pliku przez agenta.

Kopiujesz go do projektu (np. `.claude/hooks/post_edit_checks.py`) i rejestrujesz w `.claude/settings.json` projektu
dopiero za zgodą człowieka (skill eng-local-quality-gates). Bramki opisuje `.claude/quality-gates.json`:

  {
    "max_lines": 40,
    "checks": [
      {"name": "eslint", "glob": "src/**/*.{ts,tsx}", "cmd": "npx eslint --fix {file}", "timeout": 15},
      {"name": "testy powiązane", "glob": "src/billing/**/*.ts", "cmd": "npx vitest related {file} --run",
       "timeout": 30, "env": {"AI_AGENT": "1"}}
    ]
  }

  glob     wzorzec ścieżki względem katalogu projektu (`**` = dowolne katalogi, `{a,b}` = warianty); może być listą
  cmd      polecenie bez powłoki (napis dzielony jak w shellu albo lista); `{file}` = ścieżka edytowanego pliku
  timeout  limit jednego sprawdzenia w sekundach (domyślnie 20); env, name, max_lines — opcjonalne

Działanie: brak pliku konfiguracji albo brak pasującego wzorca → nic. Porażka sprawdzenia → kod 2 i końcówka wyjścia
na stderr (Claude Code przekazuje ją agentowi). Przekroczony limit, brak programu, zła konfiguracja → kod 0 i komunikat
(hook nie blokuje z własnej winy). Cały hook kończy się sam po CLAUDE_QG_DEADLINE sekund (domyślnie 50) — ustaw
`timeout` hooka w settings.json wyżej (np. 60). CLAUDE_QUALITY_GATES=off wyłącza hook.

Użycie ręczne (sprawdzenie konfiguracji, nic nie uruchamia):
  python3 post_edit_checks.py --dry-run src/billing/invoice.ts [--json]
Kody wyjścia: 0 — OK / nic do zrobienia; 2 — sprawdzenie nie przeszło (tryb hooka); 1 — zła konfiguracja (--dry-run).
Tylko biblioteka standardowa Pythona 3.9+, bez sieci.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

CONFIG = Path(".claude") / "quality-gates.json"
EDIT_TOOLS = {"Write", "Edit", "MultiEdit"}
DEFAULT_TIMEOUT = 20.0
DEFAULT_MAX_LINES = 40
MAX_CHARS = 8000          # stderr dla agenta — krótko, żeby nie zalać kontekstu
_current: dict = {"proc": None}
_t0 = time.monotonic()


# ───────────── limit całego hooka ─────────────

def deadline_seconds() -> float:
    try:
        return max(0.5, float(os.environ.get("CLAUDE_QG_DEADLINE", "50")))
    except ValueError:
        return 50.0


def remaining() -> float:
    return deadline_seconds() - (time.monotonic() - _t0)


def kill(proc) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        if os.name != "nt":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except (OSError, ProcessLookupError):
        pass


def start_deadline() -> None:
    """Hook kończy się sam (kod 0) przed limitem Claude Code — zabity proces daje niejasny błąd hooka."""
    def fire():
        kill(_current["proc"])
        try:
            msg = (f"Bramki po edycji przerwane po {deadline_seconds():.0f} s (CLAUDE_QG_DEADLINE). Sprawdzenia "
                   "są za wolne na hook po edycji — zawęź je albo przenieś do pre-commit.")
            sys.stdout.write(json.dumps({"systemMessage": msg}, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        finally:
            os._exit(0)
    timer = threading.Timer(deadline_seconds(), fire)
    timer.daemon = True
    timer.start()


# ───────────── konfiguracja i wzorce ─────────────

def expand_braces(pattern: str) -> list[str]:
    m = re.search(r"\{([^{}]*)\}", pattern)
    if not m:
        return [pattern]
    out = []
    for alt in m.group(1).split(","):
        out.extend(expand_braces(pattern[:m.start()] + alt + pattern[m.end():]))
    return out


def glob_regex(pattern: str) -> re.Pattern:
    i, n, rx = 0, len(pattern), ""
    while i < n:
        if pattern.startswith("**/", i):
            rx, i = rx + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            rx, i = rx + ".*", i + 2
        elif pattern[i] == "*":
            rx, i = rx + "[^/]*", i + 1
        elif pattern[i] == "?":
            rx, i = rx + "[^/]", i + 1
        else:
            rx, i = rx + re.escape(pattern[i]), i + 1
    return re.compile(rx + r"\Z")


def matches(rel: str, globs) -> bool:
    for g in ([globs] if isinstance(globs, str) else list(globs or [])):
        if any(glob_regex(p).match(rel) for p in expand_braces(str(g).replace("\\", "/"))):
            return True
    return False


def load_config(root: Path) -> dict | None:
    """None — brak pliku; ValueError — zła konfiguracja."""
    path = root / CONFIG
    if not path.is_file():
        return None
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict) or not isinstance(cfg.get("checks"), list):
        raise ValueError("brak listy „checks”")
    for i, c in enumerate(cfg["checks"]):
        if not isinstance(c, dict) or not c.get("glob") or not c.get("cmd"):
            raise ValueError(f"sprawdzenie nr {i + 1} bez „glob” albo „cmd”")
    return cfg


def split_cmd(cmd) -> list[str]:
    if isinstance(cmd, list):
        return [str(x) for x in cmd]
    if os.name == "nt":  # ścieżki z \ — tryb nie-POSIX, cudzysłowy zdejmujemy sami
        return [t[1:-1] if len(t) > 1 and t[0] == t[-1] == '"' else t for t in shlex.split(cmd, posix=False)]
    return shlex.split(cmd)


def build_argv(check: dict, rel: str) -> list[str]:
    return [t.replace("{file}", rel) for t in split_cmd(check["cmd"])]


def label(check: dict) -> str:
    return str(check.get("name") or (check["cmd"] if isinstance(check["cmd"], str) else " ".join(check["cmd"])))


def relative(root: Path, file_path: str) -> str | None:
    if not file_path:
        return None
    p = Path(file_path)
    p = (p if p.is_absolute() else root / p).resolve()
    try:
        return p.relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


# ───────────── uruchamianie ─────────────

def tail(text: str, max_lines: int) -> str:
    lines = text.rstrip().splitlines()
    cut = lines[-max_lines:]
    head = [f"… (pominięto {len(lines) - len(cut)} linii)"] if len(lines) > len(cut) else []
    return "\n".join(head + cut)


def run_check(check: dict, rel: str, root: Path, max_lines: int) -> tuple[str, str]:
    """→ (stan, szczegóły); stan: ok | fail | timeout | missing."""
    argv = build_argv(check, rel)
    exe = shutil.which(argv[0], path=os.environ.get("PATH")) or (
        str(root / argv[0]) if (root / argv[0]).is_file() else None)
    if not exe:
        return "missing", f"nie znaleziono programu „{argv[0]}”"
    limit = min(float(check.get("timeout", DEFAULT_TIMEOUT)), max(0.5, remaining() - 0.5))
    env = {**os.environ, **{str(k): str(v) for k, v in (check.get("env") or {}).items()}}
    kwargs = {"start_new_session": True} if os.name != "nt" else {}
    try:
        proc = subprocess.Popen([exe, *argv[1:]], cwd=str(root), env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs)
    except OSError as e:
        return "missing", f"nie udało się uruchomić „{argv[0]}”: {e}"
    _current["proc"] = proc
    try:
        out, _ = proc.communicate(timeout=limit)
    except subprocess.TimeoutExpired:
        kill(proc)
        proc.communicate()
        return "timeout", f"przekroczony limit {limit:.0f} s"
    finally:
        _current["proc"] = None
    text = out.decode("utf-8", errors="replace")
    if proc.returncode == 0:
        return "ok", ""
    return "fail", f"kod {proc.returncode}\n{tail(text, int(check.get('max_lines', max_lines)))}"


def hook(data: dict) -> int:
    if os.environ.get("CLAUDE_QUALITY_GATES", "").lower() in ("off", "0", "false"):
        return 0
    if data.get("tool_name") not in EDIT_TOOLS:
        return 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".").resolve()
    try:
        cfg = load_config(root)
    except (ValueError, OSError) as e:
        print(json.dumps({"systemMessage": f"Bramki po edycji pominięte: błąd w {CONFIG.as_posix()} ({e})."},
                         ensure_ascii=False))
        return 0
    if not cfg:
        return 0
    rel = relative(root, (data.get("tool_input") or {}).get("file_path", ""))
    if rel is None:
        return 0
    max_lines = int(cfg.get("max_lines", DEFAULT_MAX_LINES))
    failed, notes = [], []
    for check in cfg["checks"]:
        if not matches(rel, check["glob"]):
            continue
        state, detail = run_check(check, rel, root, max_lines)
        if state == "fail":
            failed.append(f"✗ {label(check)} — {detail}")
        elif state == "timeout":
            notes.append(f"⏱ {label(check)}: {detail} — za wolne na hook po edycji; zawęź albo przenieś do pre-commit")
        elif state == "missing":
            notes.append(f"? {label(check)}: {detail} — popraw {CONFIG.as_posix()}")
    if failed:
        msg = (f"Bramka po edycji nie przeszła dla {rel}:\n\n" + "\n\n".join(failed + notes) +
               "\n\nPopraw przyczynę w kodzie, nie wyłączaj sprawdzenia ani testu. Format, import, typ — popraw od "
               "razu. Test logiki pada po 1–2 próbach poprawki → przerwij i zbadaj przyczynę (eng-debugging).")
        if len(msg) > MAX_CHARS:
            msg = "… (początek pominięty)\n" + msg[-MAX_CHARS:]
        sys.stderr.write(msg + "\n")
        sys.stderr.flush()
        return 2
    if notes:
        text = f"Bramki po edycji ({rel}) — uwagi:\n" + "\n".join(notes)
        print(json.dumps({"systemMessage": text, "hookSpecificOutput": {
            "hookEventName": "PostToolUse", "additionalContext": text}}, ensure_ascii=False))
    return 0


def dry_run(args: list[str]) -> int:
    as_json = "--json" in args
    rest = [a for a in args if a not in ("--dry-run", "--json")]
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    try:
        cfg = load_config(root) or {"checks": []}
    except (ValueError, OSError) as e:
        print(f"✗ {CONFIG.as_posix()}: {e}", file=sys.stderr)
        return 1
    rel = relative(root, rest[0]) if rest else None
    found = [{"name": label(c), "glob": c["glob"], "argv": build_argv(c, rel or "{file}"),
              "timeout": float(c.get("timeout", DEFAULT_TIMEOUT))}
             for c in cfg["checks"] if rel is None or matches(rel, c["glob"])]
    if as_json:
        print(json.dumps({"file": rel, "checks": found}, ensure_ascii=False, indent=2))
    elif not found:
        print(f"Brak sprawdzeń dla {rel or '(wszystkie)'}.")
    else:
        print(f"Sprawdzenia dla {rel or '(wszystkie)'}:")
        for c in found:
            print(f"- {c['name']}: {' '.join(shlex.quote(a) for a in c['argv'])} (limit {c['timeout']:.0f} s)")
    return 0


def main(argv: list[str]) -> int:
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    if "--dry-run" in argv:
        return dry_run(argv)
    start_deadline()
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        data = json.loads(raw) if raw.strip() else {}
    except (ValueError, OSError):
        return 0
    try:
        return hook(data)
    except Exception as e:  # błąd hooka nie blokuje pracy agenta
        print(json.dumps({"systemMessage": f"Bramki po edycji: błąd hooka ({type(e).__name__}: {e})."},
                         ensure_ascii=False))
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
