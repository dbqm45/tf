#!/usr/bin/env python3
"""
Dziennik błędów hooków: hook nie przerywa sesji przy własnym błędzie, ale błąd zostaje zapisany.

  from hook_errors import record      # w hooku: except Exception as e: record("nazwa_hooka", e)
  python3 .claude/hooks/hook_errors.py --summary [--days 7]   # podsumowanie (woła je `tf doctor`)

Wpis w `<projekt>/.tf/logs/hook-errors.jsonl`: czas, hook, typ wyjątku, miejsce (plik:linia najgłębszej ramki),
komunikat przycięty do 200 znaków. Bez treści wejścia hooka (może zawierać kod i dane). Dziennik ma najwyżej
MAX_BYTES — po przekroczeniu zostaje nowsza połowa. `record` nigdy nie rzuca wyjątku: dziennik ma pomagać, a nie
dokładać awarii. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

MAX_BYTES = 256_000
LOG = Path(".tf") / "logs" / "hook-errors.jsonl"


def _log_path() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".") / LOG


def record(hook: str, exc: BaseException) -> None:
    """Zapisz błąd hooka; nigdy nie rzuca."""
    try:
        frames = traceback.extract_tb(exc.__traceback__) if exc.__traceback__ else []
        where = f"{Path(frames[-1].filename).name}:{frames[-1].lineno}" if frames else "?"
        entry = {"ts": round(time.time(), 3), "hook": hook, "type": type(exc).__name__, "where": where,
                 "msg": str(exc)[:200]}
        p = _log_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if p.stat().st_size > MAX_BYTES:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            keep, size = [], 0
            for line in reversed(lines):
                size += len(line.encode("utf-8")) + 1
                if size > MAX_BYTES // 2:
                    break
                keep.append(line)
            p.write_text("\n".join(reversed(keep)) + "\n", encoding="utf-8")
    except Exception:  # noqa: BLE001 — dziennik błędów nie może sam wywrócić hooka
        return None


def summary(days: int = 7) -> str:
    """Jedna linia dla `tf doctor` albo pusty napis, gdy w oknie nie było błędów."""
    p = _log_path()
    if not p.is_file():
        return ""
    since, hooks = time.time() - days * 86400, Counter()
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(e, dict) and float(e.get("ts", 0)) >= since:
            hooks[f"{e.get('hook')} ({e.get('type')} w {e.get('where')})"] += 1
    if not hooks:
        return ""
    top = ", ".join(f"{k} ×{v}" for k, v in hooks.most_common(5))
    return (f"⚠ błędy hooków w ostatnich {days} dniach: {sum(hooks.values())} — {top}. Hooki nie przerwały pracy, "
            f"ale ich ochrona mogła nie zadziałać; szczegóły: {LOG.as_posix()}")


def main(argv: list[str]) -> int:
    for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „⚠”, „×” — zawsze UTF-8
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if "--summary" in argv:
        days = 7
        if "--days" in argv and argv.index("--days") + 1 < len(argv):
            try:
                days = int(argv[argv.index("--days") + 1])
            except ValueError:
                days = 7
        text = summary(days)
        if text:
            print(text)
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
