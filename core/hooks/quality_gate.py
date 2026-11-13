#!/usr/bin/env python3
"""
Stop / SubagentStop: bramka jakości — tura nie kończy się z czerwonym buildem i testami („prompt prosi, hook pilnuje”).

Działa tylko z konfiguracją projektu `.claude/quality-gate.json` (fabryka nie zna poleceń projektu):
  {"command": "npm test", "watch": ["src/", "test/"], "timeout": 600, "max_blocks": 3}
- `command` — build i testy (napis albo lista argumentów, bez powłoki), uruchamiane pod blokadą test_lock.py;
- `watch` — ścieżki, których zmiana uruchamia bramkę (domyślnie całe repozytorium);
- `timeout` — sekundy; przekroczenie to wynik czerwony;
- `max_blocks` — po tylu blokadach tego samego stanu kodu bramka przepuszcza z komunikatem dla człowieka (ochrona
  przed pętlą, domyślnie 3).
Polecenie biegnie tylko, gdy zmienił się kod w `watch` względem HEAD (odcisk diffu i nowych plików); po zielonym
przebiegu ten sam odcisk nie uruchamia testów drugi raz. Świadomie czerwona partia (TDD, test przed kodem): plik
`.claude/quality-gate.expected-red` z powodem — bramka przepuszcza; usuń go po partii. `QG_GATE_DISABLE=1` wyłącza
bramkę (np. w `.claude/settings.local.json`). Stan: `.tf/logs/quality-gate.json`. Tylko biblioteka standardowa.
Długie wyjście polecenia agent dostaje jako początek i koniec; całość ostatniego przebiegu jest w
`.tf/logs/quality-gate-output.txt`.

  python3 .claude/hooks/quality_gate.py --status [--quiet-ok]   # czy bramka działa i dlaczego nie (tf doctor, start sesji)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shlex
import signal
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
HEAD, TAIL = 1000, 2000   # tyle znaków początku i końca wyjścia trafia do agenta
OUTPUT = "quality-gate-output.txt"


def clip(out: str, saved: str) -> str:
    """Wyjście dla agenta: krótkie w całości, długie jako początek i koniec z informacją, ile pominięto i gdzie jest
    całość. Pierwszy błąd bywa na początku logu, podsumowanie na końcu — sam koniec gubi przyczynę."""
    if len(out) <= HEAD + TAIL:
        return out
    return (out[:HEAD] + f"\n… [pominięto {len(out) - HEAD - TAIL} znaków; całość: {saved}] …\n" + out[-TAIL:])


def save_output(root: Path, name: str, out: str) -> str:
    """Zapisuje pełne wyjście ostatniego przebiegu w .tf/logs/ i zwraca ścieżkę względną (błąd zapisu nie przerywa)."""
    rel = f".tf/logs/{name}"
    try:
        (root / ".tf" / "logs").mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(out, encoding="utf-8")
    except OSError:
        pass
    return rel


def _lock():
    spec = importlib.util.spec_from_file_location("test_lock", HERE / "test_lock.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(root: Path, *args: str) -> bytes:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=30)
    return r.stdout if r.returncode == 0 else b""


def fingerprint(root: Path, watch: list[str]) -> str | None:
    """Odcisk zmian w `watch` względem HEAD; None, gdy nic się nie zmieniło."""
    paths = ["--", *watch] if watch else []
    diff = git(root, "diff", "HEAD", "--binary", *paths)
    new = git(root, "ls-files", "--others", "--exclude-standard", *paths).decode(errors="replace").split()
    if not diff and not new:
        return None
    h = hashlib.sha256(diff)
    for rel in sorted(new):
        p = root / rel
        h.update(rel.encode())
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


def load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def run(root: Path, cmd, timeout: float) -> tuple[bool | None, str]:
    """(zielone?, wyjście przycięte do początku i końca); None = blokada testów zajęta. Pełne wyjście: .tf/logs/."""
    argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
    with _lock().held(root) as ok:
        if not ok:
            return None, ""
        proc = subprocess.Popen(argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                errors="replace", start_new_session=True,
                                env={**os.environ, "TF_TEST_LOCK_HELD": "1"})
        try:
            out, _ = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (OSError, AttributeError):
                proc.kill()
            out, _ = proc.communicate()
            saved = save_output(root, OUTPUT, out or "")
            return False, f"przekroczony limit czasu {timeout:g} s\n" + clip(out or "", saved)
    saved = save_output(root, OUTPUT, out or "")
    return proc.returncode == 0, clip(out or "", saved)


def decide(root: Path, data: dict) -> dict | None:
    if os.environ.get("QG_GATE_DISABLE") == "1":
        return None
    cfg_path = root / ".claude" / "quality-gate.json"
    if not cfg_path.is_file():
        return None
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if not cfg.get("command"):
        return None
    fp = fingerprint(root, list(cfg.get("watch") or []))
    if fp is None:
        return None
    state_path = root / ".tf" / "logs" / "quality-gate.json"
    state = load_state(state_path)
    if state.get("green") == fp:
        return None
    marker = root / ".claude" / "quality-gate.expected-red"
    if marker.is_file():
        print(f"bramka jakości: zadeklarowana czerwona partia — {marker.read_text(encoding='utf-8').strip()[:200]}",
              file=sys.stderr)
        return None
    max_blocks = int(cfg.get("max_blocks", 3))
    red = state.get("red") or {}
    if red.get("fp") == fp and red.get("count", 0) >= max_blocks:
        return {"systemMessage": f"Bramka jakości: testy wciąż czerwone po {max_blocks} próbach na tym samym stanie "
                                 f"kodu — przepuszczam, decyzja należy do człowieka (`{cfg['command']}`)."}
    ok, tail = run(root, cfg["command"], float(cfg.get("timeout", 600)))
    if ok is None:
        print("bramka jakości: inne testy tego repozytorium trwają (blokada zajęta) — pomijam", file=sys.stderr)
        return None
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if ok:
        state_path.write_text(json.dumps({"green": fp}), encoding="utf-8")
        return None
    count = red.get("count", 0) + 1 if red.get("fp") == fp else 1
    state_path.write_text(json.dumps({"green": state.get("green"), "red": {"fp": fp, "count": count}}),
                          encoding="utf-8")
    who = "podagenta" if data.get("hook_event_name") == "SubagentStop" else "tury"
    return {"decision": "block",
            "reason": f"Bramka jakości: `{cfg['command']}` nie przechodzi — popraw przed zakończeniem {who} "
                      f"(próba {count}/{max_blocks}). Jeśli czerwony test jest zamierzony (TDD), zapisz powód w "
                      f".claude/quality-gate.expected-red.\n--- wyjście (całość: .tf/logs/{OUTPUT}) ---\n{tail}"}


OFF = "Fabryka nie zablokuje czerwonych testów."


def _disabled_by(root: Path, env) -> str | None:
    """Skąd pochodzi wyłącznik QG_GATE_DISABLE=1: środowisko sesji albo plik ustawień projektu."""
    for name in ("settings.local.json", "settings.json"):
        try:
            cfg = json.loads((root / ".claude" / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if str((cfg.get("env") or {}).get("QG_GATE_DISABLE", "")) == "1":
            return f"w .claude/{name}"
    return "w środowisku sesji" if env.get("QG_GATE_DISABLE") == "1" else None


def gate_status(root: Path, env=None) -> tuple[str, str]:
    """Stan bramki w zwykłym języku: (stan, komunikat). Stany: on, expected-red, disabled, no-config, invalid,
    no-command. Niczego nie uruchamia."""
    env = os.environ if env is None else env
    where = _disabled_by(root, env)
    if where:
        return "disabled", (f"⚠ Bramka jakości wyłączona zmienną QG_GATE_DISABLE=1 ({where}). {OFF} "
                            "Włącz: usuń tę zmienną.")
    cfg_path = root / ".claude" / "quality-gate.json"
    hint = 'Włącz: tf onboard --yes (wykryje polecenie testów) albo wpisz je do tego pliku, np. {"command": "npm test"}.'
    if not cfg_path.is_file():
        return "no-config", f"⚠ Bramka jakości wyłączona: brak pliku .claude/quality-gate.json. {OFF} {hint}"
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cfg = None
    if not isinstance(cfg, dict):
        return "invalid", (f"⚠ Bramka jakości wyłączona: plik .claude/quality-gate.json nie jest poprawnym JSON-em. "
                           f"{OFF} Popraw plik.")
    if not cfg.get("command"):
        return "no-command", (f"⚠ Bramka jakości wyłączona: w .claude/quality-gate.json brakuje pola „command”. "
                              f"{OFF} {hint}")
    command = cfg["command"] if isinstance(cfg["command"], str) else " ".join(map(str, cfg["command"]))
    marker = root / ".claude" / "quality-gate.expected-red"
    if marker.is_file():
        try:
            reason = marker.read_text(encoding="utf-8").strip()[:200]
        except OSError:
            reason = ""
        return "expected-red", ("⚠ Bramka jakości przepuszcza czerwone testy: plik .claude/quality-gate.expected-red"
                                + (f" ({reason})" if reason else "") + ". Usuń go po zakończeniu partii.")
    return "on", f"✓ Bramka jakości włączona: `{command}`."


def main() -> int:
    if "--status" in sys.argv[1:]:   # tf doctor i start sesji: jedno zdanie o stanie bramki, zawsze kod 0
        state, text = gate_status(Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve())
        if state != "on" or "--quiet-ok" not in sys.argv[1:]:
            print(text)
        return 0
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    try:
        out = decide(root, data)
    except Exception as e:  # noqa: BLE001 — bramka nie może wywrócić sesji
        print(f"bramka jakości: błąd ({e}) — pomijam", file=sys.stderr)
        return 0
    if out:
        print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
