#!/usr/bin/env python3
"""Hooki działają na Windows: kodowanie UTF-8 niezależne od strony kodowej i limit czasu.

python3 tests/test_hook_portability.py

Na Windows Python domyślnie koduje stdin/stdout stroną kodową systemu (np. cp1250), a Claude Code wysyła i czyta
JSON w UTF-8. Symulujemy to przez PYTHONIOENCODING=cp1250. Drugi problem: `git` zawieszony przez proces potomny
(np. fsmonitor na Windows trzyma potok) przekraczał limit hooka — Claude Code zabijał proces i zgłaszał
„Stop hook error … No stderr output”. Hook ma skończyć się sam, z kodem 0, przed limitem.
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
HOOKS = ROOT / ".claude" / "hooks"
POLISH = "Zażółć gęślą jaźń — „cudzysłów” i zależności"


def hook_commands() -> list[tuple[str, list[str], int]]:
    # tryb zespołowy: settings.json; prywatny (domyślny): settings.local.json
    path = next(p for p in (ROOT / ".claude" / "settings.json", ROOT / ".claude" / "settings.local.json") if p.exists())
    settings = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for event, groups in settings["hooks"].items():
        for g in groups:
            for h in g["hooks"]:
                args = [a.replace("${CLAUDE_PROJECT_DIR}", "") .lstrip("/") for a in h.get("args", [])]
                out.append((event, args, h.get("timeout") or 60))
    return out


def run(args: list[str], root: Path, stdin: bytes, extra_env: dict | None = None, timeout: float = 30):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root), "PYTHONIOENCODING": "cp1250", "PYTHONUTF8": "0",
           **(extra_env or {})}
    script = ROOT / args[0]
    t0 = time.monotonic()
    r = subprocess.run([sys.executable, str(script), *args[1:]], input=stdin, capture_output=True, env=env,
                       cwd=root, timeout=timeout)
    return r, time.monotonic() - t0


def payload(event: str) -> bytes:
    data = {"hook_event_name": event, "session_id": "s", "cwd": "", "prompt": POLISH,
            "tool_name": "Write", "tool_input": {"file_path": "notatki.md", "content": POLISH, "command": f"echo '{POLISH}'"},
            "last_assistant_message": POLISH, "stop_hook_active": False}
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def project(d: str) -> Path:
    """Kopia `.claude/` fabryki w pustym repo — hooki mają skille i szablony, a zapisy nie trafiają do fabryki."""
    root = Path(d)
    shutil.copytree(ROOT / ".claude", root / ".claude", ignore=shutil.ignore_patterns("__pycache__", "*.jsonl"))
    subprocess.run(["git", "init", "-q", str(root)], capture_output=True)
    return root


def encoding_tests() -> list[str]:
    fails = []
    with tempfile.TemporaryDirectory() as d:
        root = project(d)
        run([".claude/hooks/project_record.py", "wip", "start", "Zażółć gęślą jaźń"], root, b"",
            {"PYTHONIOENCODING": "utf-8"})
        for event, args, _ in hook_commands():
            r, _ = run(args, root, payload(event))
            name = " ".join(args)
            if r.returncode not in (0, 2):
                fails.append(f"{event} {name}: kod wyjścia {r.returncode}, stderr: {r.stderr[-200:]!r}")
            try:
                r.stdout.decode("utf-8")
            except UnicodeDecodeError:
                fails.append(f"{event} {name}: stdout nie jest w UTF-8 przy stronie kodowej cp1250")
    return fails


def hint_test() -> list[str]:
    """Polski prompt czytany przy cp1250 nie może się rozjechać (skill_hint dopasowuje rdzenie słów)."""
    with tempfile.TemporaryDirectory() as d:
        root = project(d)
        prompt = "Podnieś zależności npm i zaktualizuj lockfile, Renovate czy Dependabot?"
        data = json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": prompt}, ensure_ascii=False).encode("utf-8")
        r, _ = run([".claude/hooks/skill_hint.py"], root, data)
        r_utf, _ = run([".claude/hooks/skill_hint.py"], root, data, {"PYTHONIOENCODING": "utf-8"})
        if "ops-dependency-upgrades" not in r_utf.stdout.decode("utf-8", "replace"):
            return ["skill_hint: brak oczekiwanej podpowiedzi (test nieważny)"]
        if r.stdout != r_utf.stdout:
            return ["skill_hint daje inny wynik przy cp1250 niż przy UTF-8 (prompt źle zdekodowany)"]
    return []


def hanging_git_test() -> list[str]:
    """Zawieszony `git` nie może przetrzymać hooka Stop do limitu Claude Code."""
    if os.name == "nt":
        return []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        subprocess.run(["git", "init", "-q", str(root)], capture_output=True)
        r, _ = run([".claude/hooks/project_record.py", "wip", "start", "Długie zadanie"], root, b"")
        wip = root / "docs/project/wip/dlugie-zadanie.md"
        if not wip.exists():
            return [f"wip start: {r.stdout[-200:]!r}"]
        (root / "app.ts").write_text("x", encoding="utf-8")
        old = time.time() - 3600
        os.utime(wip, (old, old))
        fake = root / "fakebin"
        fake.mkdir()
        g = fake / "git"
        g.write_text("#!/bin/sh\nsleep 30\n", encoding="utf-8")
        g.chmod(g.stat().st_mode | stat.S_IEXEC)
        env = {"PATH": f"{fake}{os.pathsep}{os.environ.get('PATH', '')}", "CLAUDE_HOOK_DEADLINE": "1.5"}
        r, took = run([".claude/hooks/project_record.py", "--hook-stop"], root, b"{}", env, timeout=40)
        fails = []
        if r.returncode != 0:
            fails.append(f"Stop przy zawieszonym git: kod {r.returncode}")
        if took > 4:
            fails.append(f"Stop przy zawieszonym git trwał {took:.1f} s (limit własny 1.5 s)")
    return fails


def main() -> int:
    tests = [("kodowanie", encoding_tests), ("skill_hint", hint_test), ("zawieszony git", hanging_git_test)]
    fails = []
    for name, fn in tests:
        f = fn()
        print(f"{'OK ' if not f else 'BŁĄD'} {name}" + ("" if not f else "\n  " + "\n  ".join(f)))
        fails += f
    print(f"\n{len(tests)} grupy testów, błędów: {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
