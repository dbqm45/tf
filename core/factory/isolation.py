#!/usr/bin/env python3
"""Isolation level of agent sessions (plan docs/plans/2026-11-20-poziomy-izolacji.md, slice I1).

The `isolation` key in the configuration layers (engine ← company ← team ← project ← person):
- `basic`     — permissions and the factory's hooks only; not isolation: a command can read and send what the user can;
- `sandbox`   — (the default) Claude Code's sandbox limits the files and the network of commands;
- `container` — the session runs in a container (`tf code --container`), with only the project mounted.

  isolation.py show [--json]   # the chosen level, where it comes from, and what actually protects this session
  isolation.py set <level>     # writes `isolation: <level>` into .tf/config/config.yaml — only from a human's terminal

`set` refuses inside an agent session (the variables CLAUDECODE / CLAUDE_CODE_ENTRYPOINT): an agent does not lower its
own isolation. Until slice I2 the factory does not turn the sandbox on by itself; `show` says so honestly.
"""
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("PYTHONUTF8", "1")  # child processes also write and read UTF-8
for _stream in (sys.stdout, sys.stderr):  # Windows: the code page ≠ UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

LEVELS = ("basic", "sandbox", "container")
DEFAULT = "sandbox"
SESSION_VARS = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")
SETTINGS = (Path(".claude") / "settings.local.json", Path(".claude") / "settings.json",
            Path(".tf") / "plugin" / "session-settings.json")   # the first one with `sandbox.enabled` decides
CONFIG = Path(".tf") / "config" / "config.yaml"
KEY_LINE = re.compile(r"^isolation\s*:.*$", re.M)


def packs_module(root: Path):
    path = Path(__file__).resolve().parent / "packs.py"
    spec = importlib.util.spec_from_file_location("tf_packs_isolation", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def source_name(label: str) -> str:
    if label.endswith("(person)"):
        return "person"
    if "(org_defaults)" in label:
        return "organization"
    if "(team_defaults)" in label:
        return "team"
    return "project" if label.startswith(".tf/config/") else "factory"


def configured(root: Path) -> tuple[str, str]:
    """(level, source) after all layers; an unknown value → the default with the source "factory"."""
    level, source = DEFAULT, "factory"
    for label, data in packs_module(root).config_layers(root):
        value = (data or {}).get("isolation") if isinstance(data, dict) else None
        if isinstance(value, str) and value.lower() in LEVELS:
            level, source = value.lower(), source_name(label)
    return level, source


def sandbox_state(root: Path) -> tuple[bool, str | None]:
    """(enabled, the file that says so) — the first settings file that sets `sandbox.enabled`."""
    for rel in SETTINGS:
        f = root / rel
        try:
            data = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else None
        except (OSError, ValueError):
            continue
        sb = data.get("sandbox") if isinstance(data, dict) else None
        if isinstance(sb, dict) and isinstance(sb.get("enabled"), bool):
            return sb["enabled"], rel.as_posix()
    return False, None


def in_container() -> bool:
    """The factory's container image sets TF_CONTAINER=1 (slice I4)."""
    return os.environ.get("TF_CONTAINER") == "1"


def state(root: Path) -> dict:
    level, source = configured(root)
    enabled, where = sandbox_state(root)
    container = in_container()
    gaps = []
    if level == "basic":
        gaps.append("basic is not isolation: a command run by the agent can read and send whatever your user account can")
    elif level == "sandbox" and not enabled:
        gaps.append("the sandbox is not enabled in this project's settings (sandbox.enabled) — commands run without it")
    elif level == "container" and not container:
        gaps.append("container chosen, but this session does not run in the factory's container (tf code --container)")
    return {"level": level, "source": source, "sandbox_enabled": enabled, "sandbox_where": where,
            "in_container": container, "gaps": gaps}


def cmd_show(root: Path, as_json: bool) -> int:
    s = state(root)
    if as_json:
        print(json.dumps(s, ensure_ascii=False))
        return 0
    actual = ("container" if s["in_container"] else
              f"sandbox enabled ({s['sandbox_where']})" if s["sandbox_enabled"] else "sandbox not enabled")
    mark = "⚠" if s["gaps"] else "✓"
    print(f"{mark} Isolation: {s['level']} (from {s['source']}); this session: {actual}")
    for g in s["gaps"]:
        print(f"  - {g}")
    return 0


def write_level(root: Path, level: str) -> Path:
    """`isolation: <level>` in the project configuration; the rest of the file (comments too) stays."""
    f = root / CONFIG
    text = f.read_text(encoding="utf-8") if f.is_file() else ""
    line = f"isolation: {level}"
    if KEY_LINE.search(text):
        text = KEY_LINE.sub(line, text, count=1)
    else:
        text = (text if not text or text.endswith("\n") else text + "\n") + line + "\n"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")
    return f


def cmd_set(root: Path, level: str) -> int:
    if level not in LEVELS:
        print(f"✗ unknown level {level!r}; choose one of: {', '.join(LEVELS)}", file=sys.stderr)
        return 2
    if any(os.environ.get(v) for v in SESSION_VARS):
        print("✗ the isolation level is changed by a human in a terminal, not by an agent session "
              "(run `tf isolation <level>` outside Claude Code)", file=sys.stderr)
        return 2
    f = write_level(root, level)
    print(f"✓ isolation: {level} → {f.relative_to(root).as_posix()}")
    return cmd_show(root, False)


def main(argv: list[str]) -> int:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    if not argv or argv[0] == "show":
        return cmd_show(root, "--json" in argv)
    if argv[0] == "set" and len(argv) == 2:
        return cmd_set(root, argv[1])
    if argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
