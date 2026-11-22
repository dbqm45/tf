#!/usr/bin/env python3
"""
PreToolUse (Read|Bash): reading a large file whole costs context — the hook says so before it happens.

A `Read` without `offset`/`limit`, or a plain `cat <file>` in Bash, of a text file longer than `read_gate.max_lines`
(350 by default) lines:
- `read_gate.mode: warn` (the default) — the read goes on under the usual permissions; the agent gets a hint: read the needed part with offset/limit,
  find it with Grep, or ask the `scout` agent for a summary; before an Edit, read the exact lines (a summary moves the
  line numbers, and reasoning about the code should not be delegated to a cheaper model);
- `deny` — the read is refused with the same hint; a read with a range always passes;
- `off` — nothing.
A small, missing or binary file, `head`/`tail`, a `cat` in a pipe and an unreadable configuration always pass: the
hook never blocks because of its own error (the error goes to `.tf/logs/hook-errors.jsonl`).

The values come from the configuration layers (engine ← company ← team ← project ← person), e.g. in
`.tf/config/config.yaml`:  read_gate: {mode: deny, max_lines: 500}
"""
import importlib.util
import json
import os
import re
import shlex
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record, record_block
except ImportError:  # an install without the hook logs — the hook works as before
    def record(hook: str, exc: BaseException) -> None:
        return None

    def record_block(hook: str, decision: str) -> None:
        return None

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: the code page (cp1250) ≠ Claude Code's UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DEFAULTS = {"mode": "warn", "max_lines": 350}
MODES = ("warn", "deny", "off")
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".pdf", ".ipynb", ".zip", ".gz", ".tgz", ".woff",
          ".woff2", ".ttf", ".mp4", ".mov", ".mp3", ".wav", ".so", ".dll", ".exe", ".bin", ".pyc"}
CAT = re.compile(r"^\s*cat\s+([^|;&<>`$()]+?)\s*$")


def settings(project: Path) -> dict:
    """`read_gate` after all configuration layers; the defaults when the engine is not there."""
    out = dict(DEFAULTS)
    packs_py = next((c for c in (project / ".tf" / "factory" / "packs.py",
                                 Path(__file__).resolve().parents[2] / ".tf" / "factory" / "packs.py") if c.is_file()), None)
    if not packs_py:
        return out
    spec = importlib.util.spec_from_file_location("tf_packs_read_gate", packs_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for _src, data in mod.config_layers(project):
        part = (data or {}).get("read_gate") if isinstance(data, dict) else None
        if isinstance(part, dict):
            out.update({k: v for k, v in part.items() if k in DEFAULTS})
    if out["mode"] is False:                # YAML reads a bare `off` as false
        out["mode"] = "off"
    if str(out["mode"]).lower() not in MODES:
        out["mode"] = DEFAULTS["mode"]
    try:
        out["max_lines"] = max(1, int(out["max_lines"]))
    except (TypeError, ValueError):
        out["max_lines"] = DEFAULTS["max_lines"]
    out["mode"] = str(out["mode"]).lower()
    return out


def line_count(path: Path) -> int | None:
    """Lines of a text file; None for a missing or binary file (a NUL byte)."""
    if path.suffix.lower() in BINARY or not path.is_file():
        return None
    n = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            if b"\0" in chunk:
                return None
            n += chunk.count(b"\n")
    return n


def target(tool: str, ti: dict, cwd: Path) -> Path | None:
    """The file read whole by this call, or None."""
    if tool == "Read":
        if ti.get("offset") is not None or ti.get("limit") is not None or not isinstance(ti.get("file_path"), str):
            return None
        p = Path(ti["file_path"])
    elif tool == "Bash" and isinstance(ti.get("command"), str):
        m = CAT.match(ti["command"])
        if not m:
            return None
        try:
            args = shlex.split(m.group(1))
        except ValueError:
            return None
        if len(args) != 1 or args[0].startswith("-"):
            return None
        p = Path(args[0])
    else:
        return None
    return p if p.is_absolute() else cwd / p


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        sys.exit(0)
    if not isinstance(data, dict) or not isinstance(data.get("tool_input"), dict):
        sys.exit(0)
    cwd = Path(data["cwd"]) if isinstance(data.get("cwd"), str) else Path(os.getcwd())
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or cwd)
    try:
        path = target(str(data.get("tool_name") or ""), data["tool_input"], cwd)
        if path is None:
            sys.exit(0)
        conf = settings(project)
        if conf["mode"] == "off":
            sys.exit(0)
        n = line_count(path)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 — the hook's own error never blocks a read
        record("read_gate", e)
        sys.exit(0)
    if n is None or n <= conf["max_lines"]:
        sys.exit(0)
    text = (f"[read_gate] {path.name} has {n} lines (above {conf['max_lines']}): reading it whole fills the context. "
            "Read the part you need with offset/limit, find it with Grep, or ask the `scout` agent for a summary. "
            "Before an Edit read the exact lines yourself — a summary moves the line numbers.")
    if conf["mode"] == "deny":
        record_block("read_gate", "deny")
        out = {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": text}
    else:
        out = {"hookEventName": "PreToolUse", "additionalContext": text}   # no decision: the usual permissions apply
    print(json.dumps({"hookSpecificOutput": out}, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
