#!/usr/bin/env python3
"""Isolation level in the session (plan docs/plans/2026-11-20-poziomy-izolacji.md, slice I3): the SessionStart hook
`isolation_notice` names the level and what it does not protect, the status line shows the level, and guard_bash and
guard_paths block lowering it from inside a session (`tf isolation <level>`, `--isolation`, the `isolation` key in
.tf/config/config.yaml, the session settings files, the `sandbox` key of .claude/settings*.json).
python3 .claude/tests/test_isolation_hooks.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
os.environ["TF_NO_PLUGIN_REGISTER"] = "1"   # installs here never call the real Claude Code CLI (plugin_register.py)

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
HOOKS = ROOT / ".claude" / "hooks"
SESSION_VARS = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "TF_ISOLATION", "TF_CONTAINER")
CLEAN = {k: v for k, v in os.environ.items() if k not in SESSION_VARS}


def project(base: Path, name: str, config: str | None = None, plugin: bool = True) -> Path:
    p = base / name
    shutil.copytree(ROOT / ".tf" / "factory", p / ".tf" / "factory", ignore=shutil.ignore_patterns("__pycache__", "packs"))
    (p / ".claude").mkdir(parents=True)
    (p / ".claude" / "factory-manifest.json").write_text(json.dumps({"layout": "plugin" if plugin else "default"}),
                                                         encoding="utf-8")
    (p / ".tf" / "config").mkdir(parents=True)
    (p / ".tf" / "config" / "config.yaml").write_text(config or "isolation: sandbox\nloop:\n  blocked_slices: true\n",
                                                     encoding="utf-8")
    return p


def run(hook: str, p: Path, payload: dict | None, env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HOOKS / hook), *args], input=json.dumps(payload or {"cwd": str(p)}),
                          cwd=p, capture_output=True, text=True, timeout=60, env={**env, "CLAUDE_PROJECT_DIR": str(p)})


def decision(r: subprocess.CompletedProcess) -> str:
    try:
        return json.loads(r.stdout)["hookSpecificOutput"].get("permissionDecision") or "none"
    except (ValueError, KeyError, TypeError):
        return "none" if not r.stdout.strip() else "?"


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    check((HOOKS / "isolation_notice.py").is_file(), "IH-0: the hook .claude/hooks/isolation_notice.py is installed")
    if fails:
        print(f"✗ {fails[0]}")
        return 1
    session = {**CLEAN, "CLAUDECODE": "1"}
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = project(base, "sbx")
        r = run("isolation_notice.py", p, None, {**session, "TF_ISOLATION": "sandbox"})
        try:
            out = json.loads(r.stdout)
        except ValueError:
            out = {}
        msg = out.get("systemMessage", "")
        ctx = (out.get("hookSpecificOutput") or {}).get("additionalContext", "")
        check(r.returncode == 0 and "Isolation: sandbox" in msg and "outside" in msg and msg == ctx,
              f"IH-1: session start names the level and what it does not protect: {r.stdout}{r.stderr}")
        r = run("isolation_notice.py", p, None, session)
        check("not enabled" in r.stdout or "without" in r.stdout,
              f"IH-2: a session without tf code (no TF_ISOLATION) → the gap is named at the start: {r.stdout}")
        q = project(base, "basic", "isolation: basic\n")
        r = run("isolation_notice.py", q, None, {**session, "TF_ISOLATION": "basic"})
        check("not isolation" in r.stdout, f"IH-3: basic → said to be no isolation: {r.stdout}")
        e = base / "empty"
        e.mkdir()
        r = run("isolation_notice.py", e, None, session)
        check(r.returncode == 0 and not r.stdout.strip(), f"IH-4: without the engine — silence: {r.stdout}{r.stderr}")

        # status line: the level that protects this session
        def status(env: dict, cwd: Path) -> str:
            return subprocess.run([sys.executable, str(HOOKS / "statusline.py")],
                                  input=json.dumps({"model": {"display_name": "Opus"}, "workspace": {"project_dir": str(cwd)}}),
                                  capture_output=True, text=True, timeout=30, env={**env, "CLAUDE_PROJECT_DIR": str(cwd)}).stdout
        check("sandbox" in status({**session, "TF_ISOLATION": "sandbox"}, p), "IH-5: status line with TF_ISOLATION=sandbox")
        check("container" in status({**session, "TF_CONTAINER": "1"}, p), "IH-6: status line in the container")
        d = project(base, "dflt", plugin=False)
        check("no sandbox" in status(session, d), f"IH-7: status line without a sandbox says so: {status(session, d)}")
        (d / ".claude" / "settings.local.json").write_text(json.dumps({"sandbox": {"enabled": True}}), encoding="utf-8")
        got = status(session, d)
        check("sandbox" in got and "no sandbox" not in got, f"IH-8: status line, sandbox from settings.local.json: {got}")

        # guard_bash: no lowering of the level from inside a session
        def bash(cmd: str) -> str:
            return decision(run("guard_bash.py", p, {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(p)}, session))
        for cmd in ("tf isolation basic", "python3 .tf/factory/tf.py isolation basic",
                    "python3 .tf/factory/isolation.py set basic", "env -u CLAUDECODE tf isolation basic",
                    "python3 .tf/factory/install.py . --isolation basic",
                    "sed -i 's/isolation: sandbox/isolation: basic/' .tf/config/config.yaml",
                    "echo '{}' > .tf/cache/session-settings.json",
                    "python3 -c \"open('.tf/plugin/session-settings.json','w')\" > .tf/plugin/session-settings.json"):
            check(bash(cmd) == "deny", f"IH-9: `{cmd}` is blocked inside a session: {bash(cmd)}")
        for cmd in ("tf isolation", "tf isolation --json", "python3 .tf/factory/isolation.py show --json",
                    "cat .tf/config/config.yaml", "grep sandbox .claude/settings.local.json"):
            check(bash(cmd) == "none", f"IH-10: `{cmd}` (reading the level) passes: {bash(cmd)}")

        # guard_paths: the isolation key and the session settings
        def edit(tool: str, rel: str, **ti) -> str:
            return decision(run("guard_paths.py", p, {"tool_name": tool, "tool_input": {"file_path": str(p / rel), **ti},
                                                       "cwd": str(p)}, session))
        cfg = ".tf/config/config.yaml"
        check(edit("Edit", cfg, old_string="isolation: sandbox", new_string="isolation: basic") == "deny",
              "IH-11: Edit of the isolation key → refused")
        check(edit("Edit", cfg, old_string="blocked_slices: true", new_string="blocked_slices: false") == "none",
              "IH-12: Edit of another key of the configuration passes")
        check(edit("Write", cfg, content="isolation: basic\n") == "deny", "IH-13: Write that changes the level → refused")
        check(edit("Write", cfg, content="isolation: sandbox\nloop:\n  blocked_slices: false\n") == "none",
              "IH-14: Write that keeps the level passes")
        check(edit("Write", cfg, content="loop: {}\n") == "deny", "IH-14b: Write that drops the isolation key → refused")
        for rel in (".tf/cache/session-settings.json", ".tf/plugin/session-settings.json"):
            check(edit("Write", rel, content="{}") == "deny", f"IH-15: the session settings {rel} → refused")
        loc = ".claude/settings.local.json"
        (p / loc).write_text(json.dumps({"permissions": {"allow": []}, "sandbox": {"enabled": True}}), encoding="utf-8")
        check(edit("Edit", loc, old_string='"enabled": true', new_string='"enabled": false') == "deny",
              "IH-16: Edit that switches the sandbox off in settings.local.json → refused")
        check(edit("Edit", loc, old_string='"sandbox": {"enabled": true}', new_string='"sandbox": {}') == "deny",
              "IH-16b: Edit naming the sandbox key → refused (not only asked)")
        check(edit("Edit", loc, old_string='"allow": []', new_string='"allow": ["Bash(ls *)"]') == "ask",
              "IH-17: another change of the settings still asks a human (as before)")

    settings = next((json.loads(f.read_text(encoding="utf-8")) for f in (ROOT / ".claude" / "settings.json",
                                                                         ROOT / ".claude" / "settings.local.json")
                     if f.is_file() and "isolation_notice" in f.read_text(encoding="utf-8")), {})
    start = json.dumps((settings.get("hooks") or {}).get("SessionStart") or [])
    check("isolation_notice.py" in start, "IH-18: isolation_notice is registered for SessionStart")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} isolation hook tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
