#!/usr/bin/env python3
"""Switching layouts (docs/plans/2026-11-20-tryb-fabryki-plan.md): the plugin layout stays the default, and
`update.py --layout default|plugin` moves an install between it and the classic layout in .claude/ — the one the
Claude Desktop app loads (it cannot pass --plugin-dir, so in the plugin layout it shows no /tf). Moving back restores
skills, agents, hooks in the project settings and the rules block in CLAUDE*.md and removes .tf/plugin/; your skills
and settings survive both directions. A plain update of a plugin install keeps the plugin complete. Install, update and
`tf doctor` warn about the plugin layout.
python3 tests/test_layout_default.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
INSTALL = ROOT / "core" / "factory" / "install.py"
WARNING = "⚠ Plugin layout: only `tf code` loads the factory"
CLASSIC = "✓ Classic layout: the factory is in .claude/"


def env(base: Path) -> dict:
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(base)}


def install(p: Path, base: Path, *opts: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(INSTALL), str(p), "--yes", "--packs", "none", *opts], capture_output=True,
                          text=True, timeout=600, env=env(base))


def update(p: Path, base: Path, *opts: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(p / ".tf" / "factory" / "update.py"), "--yes", *opts], cwd=p,
                          capture_output=True, text=True, timeout=900, env=env(base))


def project(base: Path, name: str) -> Path:
    """A git project with your own skill, notes in CLAUDE.local.md and your own settings."""
    p = base / name
    (p / ".claude" / "skills" / "my-skill").mkdir(parents=True)
    (p / ".claude" / "skills" / "my-skill" / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: Mine.\n---\nX\n", encoding="utf-8")
    (p / ".claude" / "settings.local.json").write_text(json.dumps({
        "model": "opus", "env": {"MY_VAR": "1"}, "permissions": {"allow": ["Bash(make *)"]},
        "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo my-hook"}]}]}}), encoding="utf-8")
    (p / "CLAUDE.local.md").write_text("# My notes\n\n- my rule\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(p)], check=True)
    return p


def manifest(p: Path) -> dict:
    return json.loads((p / ".claude" / "factory-manifest.json").read_text(encoding="utf-8"))


def settings(p: Path) -> dict:
    return json.loads((p / ".claude" / "settings.local.json").read_text(encoding="utf-8"))


def hook_commands(s: dict) -> set[str]:
    return {" ".join([h.get("command", ""), *h.get("args", [])]) for groups in (s.get("hooks") or {}).values()
            for g in groups for h in g.get("hooks") or []}


def factory_files(p: Path) -> set[str]:
    """Factory files on disk outside the backup (what the manifest records and exists)."""
    return {r for r in manifest(p)["files"] if (p / r).is_file()}


def classic_state(p: Path) -> dict:
    s = settings(p)
    return {"files": factory_files(p), "hooks": hook_commands(s), "allow": set(s["permissions"]["allow"]),
            "env": s.get("env"), "model": s.get("model"), "sandbox": s.get("sandbox"),
            "agents": sorted(x.name for x in (p / ".claude" / "agents" / "_generated").rglob("*.md"))}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)

        # LD-0: a new install without options has the plugin layout (the default since T5), with the warning
        n = project(base, "new")
        r = install(n, base)
        check(r.returncode == 0 and manifest(n).get("layout") == "plugin"
              and (n / ".tf" / "plugin" / "skills" / "tf" / "SKILL.md").is_file() and WARNING in r.stdout,
              f"LD-0: a new install has the plugin layout and warns about Desktop: {r.returncode} {r.stdout[-400:]}")

        # LD-1: --layout default gives the classic layout
        p = project(base, "rt")
        r = install(p, base, "--layout", "default")
        check(r.returncode == 0 and manifest(p).get("layout") == "default"
              and (p / ".claude" / "skills" / "tf" / "SKILL.md").is_file() and not (p / ".tf" / "plugin").exists()
              and WARNING not in r.stdout,
              f"LD-1: --layout default gives the classic layout: {r.returncode} {r.stdout[-400:]}")
        before = classic_state(p)

        # LD-2: a plain update of a classic install stays classic (the manifest says `default`)
        r = update(p, base, "--force")
        check(r.returncode == 0 and manifest(p).get("layout") == "default"
              and (p / ".claude" / "skills" / "tf" / "SKILL.md").is_file() and not (p / ".tf" / "plugin").exists(),
              f"LD-2: a plain update of a classic install stays classic: {r.returncode} {r.stdout[-400:]}")

        # LD-3: --layout plugin still migrates classic → plugin, with the prominent warning
        r = update(p, base, "--layout", "plugin")
        check(r.returncode == 0 and manifest(p).get("layout") == "plugin"
              and (p / ".tf" / "plugin" / "skills" / "tf" / "SKILL.md").is_file()
              and not (p / ".claude" / "skills" / "tf" / "SKILL.md").exists()
              and "tdd_guard" not in json.dumps(settings(p)) and WARNING in r.stdout,
              f"LD-3: --layout plugin moves the factory to .tf/plugin/ and warns: {r.returncode} {r.stdout[-600:]}")

        # LD-4: a plain update of a plugin install stays plugin, and the plugin keeps its own files
        r = update(p, base, "--force")
        plug = p / ".tf" / "plugin"
        check(r.returncode == 0 and manifest(p).get("layout") == "plugin" and WARNING in r.stdout
              and all((plug / f).is_file() for f in (".claude-plugin/plugin.json", "hooks/hooks.json",
                                                      "session-settings.json", "RULES.md", "skills/tf/SKILL.md"))
              and (p / ".tf" / ".claude-plugin" / "marketplace.json").is_file(),
              f"LD-4: a plain update of a plugin install stays plugin, with the plugin complete: {r.returncode} "
              f"{sorted(x.relative_to(plug).as_posix() for x in plug.rglob('*') if x.is_file())[:8]} {r.stdout[-400:]}")

        # LD-5: tf doctor shows the plugin-layout warning
        r = subprocess.run([sys.executable, ".tf/factory/tf.py", "doctor"], cwd=p, capture_output=True, text=True,
                           timeout=600, env=env(base))
        check(WARNING in r.stdout and "update.py --layout default" in r.stdout,
              f"LD-5: tf doctor warns about the plugin layout: {r.stdout[:600]}")

        # your skill inside the plugin and a command entered by tf onboard in RULES.md
        (plug / "skills" / "plugin-own").mkdir(parents=True)
        (plug / "skills" / "plugin-own" / "SKILL.md").write_text("---\nname: plugin-own\ndescription: Mine.\n---\nY\n",
                                                                encoding="utf-8")
        (plug / "notes.txt").write_text("mine\n", encoding="utf-8")
        rules = (plug / "RULES.md").read_text(encoding="utf-8")
        head, tail = rules.split("### Commands\n", 1)                # the project's commands, as tf onboard writes them
        (plug / "RULES.md").write_text(head + "### Commands\n- Test: `make check-all`\n" + tail[tail.index("\n### "):],
                                       encoding="utf-8")

        # LD-6: update.py --layout default moves plugin → classic
        r = update(p, base, "--layout", "default")
        s = settings(p)
        md = (p / "CLAUDE.local.md").read_text(encoding="utf-8")
        check(r.returncode == 0 and manifest(p).get("layout") == "default" and CLASSIC in r.stdout
              and (p / ".claude" / "skills" / "tf" / "SKILL.md").is_file()
              and (p / ".claude" / "skills" / "my-skill" / "SKILL.md").is_file()
              and (p / ".claude" / "skills" / "plugin-own" / "SKILL.md").is_file(),
              f"LD-6: --layout default brings /tf back to .claude/skills/tf/, your skills stay: {r.returncode} "
              f"{r.stdout[-800:]} {r.stderr[-300:]}")
        left = sorted(x.relative_to(p).as_posix() for x in (p / ".tf" / "plugin").rglob("*") if x.is_file()) \
            if (p / ".tf" / "plugin").exists() else []
        check(left == [".tf/plugin/notes.txt"] and not (p / ".tf" / ".claude-plugin").exists()
              and ".tf/plugin/notes.txt" in r.stdout,
              f"LD-7: .tf/plugin/ is gone apart from your file, which the report names: {left}")
        check(any((p / ".claude" / "agents" / "_generated").rglob("scope-reviewer.md")),
              "LD-8: the agents are rebuilt in .claude/agents/_generated")
        check("tdd_guard" in json.dumps(s.get("hooks")) and "echo my-hook" in hook_commands(s)
              and s.get("model") == "opus" and (s.get("env") or {}).get("MY_VAR") == "1"
              and "Bash(make *)" in s["permissions"]["allow"] and (s.get("sandbox") or {}).get("enabled") is True,
              f"LD-9: the factory's hooks and the sandbox are back in settings.local.json, your entries kept: {json.dumps(s)[:600]}")
        check("team-factory:begin" in md and "my rule" in md and "make check-all" in md,
              f"LD-10: the rules block is back in CLAUDE.local.md with the project's commands, your notes kept: {md[:300]!r}")

        # LD-11: the round trip leaves the project equivalent
        (p / ".claude" / "skills" / "plugin-own").rename(base / "plugin-own")   # (not in the classic start state)
        after = classic_state(p)
        check(after["files"] == before["files"] and before["hooks"] <= after["hooks"]
              and before["allow"] <= after["allow"] and after["env"] == before["env"]
              and after["model"] == before["model"] and after["sandbox"] == before["sandbox"]
              and after["agents"] == before["agents"],
              f"LD-11: classic → plugin → classic gives the same factory files and settings: "
              f"files −{sorted(before['files'] - after['files'])[:5]} +{sorted(after['files'] - before['files'])[:5]} "
              f"hooks −{sorted(before['hooks'] - after['hooks'])[:3]} agents {len(before['agents'])}/{len(after['agents'])}")

        # LD-12: team mode back to classic: the rules block goes into CLAUDE.md, the hooks into settings.json
        q = base / "team"
        q.mkdir()
        subprocess.run(["git", "init", "-q", str(q)], check=True)
        install(q, base, "--shared", "--layout", "plugin")
        r = update(q, base, "--layout", "default")
        shared = json.loads((q / ".claude" / "settings.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and "team-factory:begin" in (q / "CLAUDE.md").read_text(encoding="utf-8")
              and "tdd_guard" in json.dumps(shared.get("hooks")) and not (q / ".tf" / "plugin").exists()
              and "sandbox" not in shared,
              f"LD-12: team mode back to classic: CLAUDE.md block, hooks in settings.json: {r.returncode} {r.stdout[-400:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} layout switching tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
