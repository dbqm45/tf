#!/usr/bin/env python3
"""Registers the factory plugin (.tf/plugin/) for this project folder in Claude Code, local scope (standard library only).

In the plugin layout only `tf code` passes `--plugin-dir .tf/plugin`. Registered with the Claude Code CLI, the plugin
loads in EVERY Claude Code session in the folder: a plain `claude`, `tf code` and the Claude Desktop app. The factory's
files stay in .tf/; the CLI writes `enabledPlugins` and `extraKnownMarketplaces` to `.claude/settings.local.json`
(per developer, git-ignored — never the shared settings.json) and records the install in the user's Claude config.

The marketplace is a file per folder, `.tf/.claude-plugin/local-marketplace.json` (git-ignored), named
`tf-<folder>-<hash of its path>`: Claude Code keeps one path per marketplace name for the whole machine, so a shared name
would make a second project (or a git worktree) redirect the first one's plugin, and removing it in one folder would
uninstall it in the other. The plugin keeps its name `tf`, so the commands are `/tf:tf`, `/tf:tf-task`, `/tf:tf-design`.

  python3 .tf/factory/plugin_register.py status|register|unregister [--root <dir>]
TF_NO_PLUGIN_REGISTER=1 (or CI) skips the CLI calls: install and update then print the two commands instead.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (the claude CLI) also write and read UTF-8

PLUGIN_NAME = "tf"
MARKET_FILE = Path(".tf") / ".claude-plugin" / "local-marketplace.json"   # git-ignored (core/gitignore)
LEGACY_MARKET = "tf-project"     # the shared name of .tf/.claude-plugin/marketplace.json (tf cloud-setup, user scope)
TIMEOUT = 60
DESCRIPTION = ("Team factory: skills, agents, hooks and rules of the /tf-task loop, registered for this folder: every "
               "Claude Code session here loads it.")
REGISTERED = ("✓ Plugin registered for this folder (local scope): every Claude Code session here — claude, tf code, the "
              "Desktop app — loads the factory; commands /tf:tf, /tf:tf-task, /tf:tf-design.")
PLUGIN_WARNING = ("⚠ Plugin layout: only `tf code` loads the factory; a plain `claude` and the Claude Desktop app see no "
                  "/tf. Back to the classic layout: python3 .tf/factory/update.py --layout default")


def skipped() -> str | None:
    """Why the CLI is not called (TF_NO_PLUGIN_REGISTER, CI), or None."""
    if os.environ.get("TF_NO_PLUGIN_REGISTER", "").strip() not in ("", "0"):
        return "TF_NO_PLUGIN_REGISTER is set"
    if os.environ.get("CI", "").strip().lower() not in ("", "0", "false"):
        return "CI is set"
    return None


def market_name(root: Path) -> str:
    root = Path(root).resolve()
    slug = re.sub(r"[^a-z0-9]+", "-", root.name.lower()).strip("-")[:24].strip("-") or "project"
    return f"tf-{slug}-{hashlib.sha256(str(root).encode('utf-8')).hexdigest()[:8]}"


def plugin_id(root: Path) -> str:
    return f"{PLUGIN_NAME}@{market_name(root)}"


def market_path(root: Path) -> Path:
    return Path(root).resolve() / MARKET_FILE


def plugin_path(root: Path) -> Path:
    return Path(root).resolve() / ".tf" / "plugin"


def write_market(root: Path) -> Path:
    """The folder's marketplace file (the plugin source `./plugin` is .tf/plugin/); written only when it changes."""
    p = market_path(root)
    data = json.dumps({"name": market_name(root), "owner": {"name": "team factory"},
                       "plugins": [{"name": PLUGIN_NAME, "source": "./plugin", "description": DESCRIPTION}]},
                      indent=2) + "\n"
    if not p.is_file() or p.read_text(encoding="utf-8") != data:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data, encoding="utf-8")
    return p


def commands(root: Path) -> list[str]:
    """The two commands that register the plugin by hand (run in the project folder)."""
    return [f"claude plugin marketplace add {shlex.quote(str(market_path(root)))} --scope local",
            f"claude plugin install {plugin_id(root)} --scope local"]


def claude() -> list[str] | None:
    """The Claude Code command (TF_CLAUDE, as `tf code`; default `claude`) resolved on PATH, or None."""
    cmd = shlex.split(os.environ.get("TF_CLAUDE") or "claude")
    exe = shutil.which(cmd[0]) if cmd else None
    return [exe, *cmd[1:]] if exe else None


def run(cmd: list[str], args: list[str], root: Path) -> tuple[int, str]:
    try:
        r = subprocess.run([*cmd, *args], cwd=str(Path(root).resolve()), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=TIMEOUT, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return 124, f"`claude {' '.join(args)}` did not finish in {TIMEOUT} s"
    except OSError as e:
        return 127, f"`claude {' '.join(args)}`: {e}"
    return r.returncode, (r.stdout + r.stderr).strip()


def same(a, b) -> bool:
    try:
        return a is not None and Path(a).resolve() == Path(b).resolve()
    except (OSError, TypeError, ValueError):
        return False


def local_settings(root: Path) -> dict:
    p = Path(root) / ".claude" / "settings.local.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def configured(root: Path) -> bool:
    """Quick check without the CLI: this folder's settings.local.json enables this folder's plugin, whose marketplace
    is this folder's file (`tf code` then does not pass --plugin-dir, so the plugin does not load twice)."""
    s = local_settings(root)
    src = ((s.get("extraKnownMarketplaces") or {}).get(market_name(root)) or {}).get("source") or {}
    return (s.get("enabledPlugins") or {}).get(plugin_id(root)) is True and same(src.get("path"), market_path(root)) \
        and market_path(root).is_file()


def stale(root: Path) -> list[str]:
    """Factory marketplaces in this folder's settings.local.json that are not this folder's: copied along when the
    project moved, or `tf-project` registered by hand."""
    out = []
    for name, m in ((local_settings(root).get("extraKnownMarketplaces") or {}).items()):
        path = str(((m or {}).get("source") or {}).get("path") or "")
        if name == market_name(root):
            continue
        if name == LEGACY_MARKET or (name.startswith("tf-") and path.replace("\\", "/").endswith(MARKET_FILE.as_posix())):
            out.append(name)
    return out


def drop_keys(root: Path, names: list[str]) -> None:
    """Removes these marketplaces and their `tf@…` plugins from this folder's settings.local.json (only those keys)."""
    p = Path(root) / ".claude" / "settings.local.json"
    s = local_settings(root)
    if not s:
        return
    new = json.loads(json.dumps(s))
    for name in names:
        (new.get("extraKnownMarketplaces") or {}).pop(name, None)
        (new.get("enabledPlugins") or {}).pop(f"{PLUGIN_NAME}@{name}", None)
    for k in ("extraKnownMarketplaces", "enabledPlugins"):
        if k in new and not new[k]:
            new.pop(k)
    if new != s:
        p.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def status(root: Path) -> dict:
    """{state: registered | disabled | wrong-path | absent | no-claude | error | skipped, detail}."""
    root = Path(root).resolve()
    why = skipped()
    if why:
        return {"state": "skipped", "detail": why}
    cmd = claude()
    if not cmd:
        return {"state": "no-claude", "detail": "the `claude` command is not in PATH"}
    rc, out = run(cmd, ["plugin", "list", "--json"], root)
    try:
        items = json.loads(out[out.index("["):]) if rc == 0 else None
    except ValueError:
        items = None
    if not isinstance(items, list):
        return {"state": "error", "detail": f"`claude plugin list --json` failed: {out[-300:]}"}
    mine = [x for x in items if isinstance(x, dict) and x.get("id") == plugin_id(root) and x.get("scope") == "local"
            and same(x.get("projectPath"), root)]
    if not mine:
        return {"state": "absent", "detail": f"{plugin_id(root)} is not installed for this folder"}
    x = mine[0]
    if not same(x.get("readFromFolder"), plugin_path(root)) or not configured(root):
        return {"state": "wrong-path", "detail": f"{plugin_id(root)} reads {x.get('readFromFolder')}, "
                                                 f"not {plugin_path(root)}"}
    if x.get("enabled") is False:
        return {"state": "disabled", "detail": f"{plugin_id(root)} is disabled — "
                                               f"claude plugin enable {plugin_id(root)} --scope local"}
    return {"state": "registered", "detail": f"{plugin_id(root)}, local scope, reads {plugin_path(root)}"}


def register(root: Path) -> tuple[bool, str]:
    """Registers (or re-registers) the plugin for the folder; idempotent. Never raises: (ok, what happened)."""
    root = Path(root).resolve()
    try:
        if not (plugin_path(root) / ".claude-plugin" / "plugin.json").is_file():
            return False, "the plugin .tf/plugin/ is incomplete"
        write_market(root)
        st = status(root)
        if st["state"] in ("registered", "disabled"):
            return True, st["detail"]
        if st["state"] in ("skipped", "no-claude", "error"):
            return False, st["detail"]
        cmd = claude()
        for name in stale(root):     # copied along from another folder: never remove another folder's marketplace
            run(cmd, ["plugin", "uninstall", f"{PLUGIN_NAME}@{name}", "--scope", "local"], root)
            path = (((local_settings(root).get("extraKnownMarketplaces") or {}).get(name) or {}).get("source")
                    or {}).get("path")
            if name != LEGACY_MARKET and path and not Path(path).exists():   # its folder is gone (the project moved)
                run(cmd, ["plugin", "marketplace", "remove", name, "--scope", "local"], root)
            drop_keys(root, [name])
        if st["state"] == "wrong-path":
            run(cmd, ["plugin", "uninstall", plugin_id(root), "--scope", "local"], root)
            run(cmd, ["plugin", "marketplace", "remove", market_name(root), "--scope", "local"], root)
        for args in (["plugin", "marketplace", "add", str(market_path(root)), "--scope", "local"],
                     ["plugin", "install", plugin_id(root), "--scope", "local"]):
            rc, out = run(cmd, args, root)
            if rc != 0:
                return False, f"`claude {' '.join(args)}` failed ({rc}): {out[-300:]}"
        st = status(root)
        return st["state"] in ("registered", "disabled"), st["detail"]
    except Exception as e:  # noqa: BLE001 — the registration never breaks an install
        return False, f"{type(e).__name__}: {e}"


def unregister(root: Path) -> tuple[bool, str]:
    """Removes this folder's registration (back to the classic layout, uninstall): the CLI's uninstall and marketplace
    removal (local scope), then the keys in settings.local.json and the marketplace file. Never raises."""
    root = Path(root).resolve()
    try:
        names = [market_name(root), *stale(root)]
        have = [n for n in names if n in (local_settings(root).get("extraKnownMarketplaces") or {})
                or f"{PLUGIN_NAME}@{n}" in (local_settings(root).get("enabledPlugins") or {})]
        cmd = None if skipped() else claude()
        note = ""
        if cmd and (have or market_path(root).is_file()):
            run(cmd, ["plugin", "uninstall", plugin_id(root), "--scope", "local"], root)
            run(cmd, ["plugin", "marketplace", "remove", market_name(root), "--scope", "local"], root)
            for name in stale(root):
                run(cmd, ["plugin", "uninstall", f"{PLUGIN_NAME}@{name}", "--scope", "local"], root)
        elif have:
            note = (f" (without the CLI: also run `claude plugin uninstall {plugin_id(root)} --scope local` and "
                    f"`claude plugin marketplace remove {market_name(root)} --scope local` here)")
        drop_keys(root, names)
        market_path(root).unlink(missing_ok=True)
        if not have:
            return True, "no registration for this folder"
        return True, f"{plugin_id(root)} unregistered for this folder{note}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def warning_block(root: Path, reason: str = "") -> str:
    """The plugin layout's warning, framed, with the two commands that register the plugin for this folder."""
    rule = "⚠ " + "─" * 70
    lines = [rule, PLUGIN_WARNING]
    if reason:
        lines.append(f"  Not registered for this folder: {reason}.")
    lines.append("  Register it (then every session here loads the factory, as /tf:tf …) — in the project folder:")
    lines += [f"    {c}" for c in commands(root)]
    lines += ["  or `tf doctor --fix`. Meanwhile start the factory with `tf code` (e.g. `tf code --continue`).", rule]
    return "\n".join(lines)


def report(root: Path) -> str:
    """Registers and returns the message for the install report: ✓ registered, or the warning with the commands."""
    ok, detail = register(root)
    return REGISTERED if ok else warning_block(root, detail)


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path.cwd()
    if argv[0] == "status":
        st = status(root)
        print(f"{st['state']}: {st['detail']}")
        return 0 if st["state"] == "registered" else 1
    if argv[0] == "register":
        print(report(root))
        return 0
    if argv[0] == "unregister":
        ok, detail = unregister(root)
        print(("✓ " if ok else "⚠ ") + detail)
        return 0 if ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
