#!/usr/bin/env python3
"""Hook SessionStart: nowsze wydanie fabryki i skille po terminie przeglądu (tylko biblioteka standardowa).

W projekcie z zainstalowaną fabryką: raz na dobę pyta źródło aktualizacji (factory/update.py → notice) i, gdy jest
nowsze wydanie, pokazuje komunikat człowiekowi (systemMessage) i agentowi. Z `update.py --auto on` (tryb prywatny)
nowe wydanie PATCH/MINOR instaluje w tle (`update.py --auto-run`), a wynik pokazuje przy starcie następnej sesji. Wszędzie, gdzie jest factory/freshness.py:
lista skilli po terminie przeglądu — agent sprawdza w nich ulotne fakty w źródłach przed użyciem. Wyłącznik
sprawdzania wydań: CTF_UPDATE_CHECK=0. Hook nigdy nie blokuje startu sesji (kod 0, cisza, gdy nie ma czego zgłosić).
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def messages(root: Path) -> list[str]:
    out = []
    up = root / "factory" / "update.py"
    if up.is_file():
        try:
            mod = load(up, "ctf_update_notice")
            out += mod.pending_messages(root) if hasattr(mod, "pending_messages") else []
            msg = (mod.start_auto(root) if hasattr(mod, "start_auto") else None) or mod.notice(root)
        except Exception:
            msg = None
        if msg:
            out.append(msg)
    fr = root / "factory" / "freshness.py"
    if fr.is_file():
        try:
            import datetime as dt
            rows = [r for r in load(fr, "ctf_freshness_notice").scan(root, dt.date.today()) if r["status"] == "overdue"]
        except Exception:
            rows = []
        if rows:
            names = ", ".join(r["skill"] for r in rows[:8]) + (" …" if len(rows) > 8 else "")
            out.append(f"Skille po terminie przeglądu ({len(rows)}): {names}. Ulotne fakty z nich (wersje, przepisy, "
                       "terminy, progi) sprawdź w źródłach przed użyciem (core-source-research). Lista: "
                       "python3 factory/freshness.py; nowsza fabryka mogła je już odświeżyć.")
    return out


def main() -> int:
    try:
        sys.stdin.read()
    except Exception:
        pass
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parent.parent.parent).resolve()
    out = messages(root)
    if out:
        text = "\n".join(out)
        print(json.dumps({"systemMessage": text,
                          "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}},
                         ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
