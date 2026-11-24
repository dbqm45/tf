#!/usr/bin/env python3
"""The plugin layout writes the factory's agents flat in .tf/plugin/agents/ (Claude Code skips subfolders); the build
check must still find the agents a persona names in `extra_agents` (pack-it's maja names 30 of them).
python3 tests/test_plugin_extra_agents.py"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
INSTALL = ROOT / "core" / "factory" / "install.py"


def main() -> int:
    fails = []
    env = {**os.environ, "TF_NO_PLUGIN_REGISTER": "1", "CLAUDE_TDD": "off"}
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        p.mkdir()
        subprocess.run(["git", "init", "-q", str(p)], check=True)
        r = subprocess.run([sys.executable, str(INSTALL), str(p), "--yes", "--packs", "pack-it"], capture_output=True,
                           text=True, timeout=900, env=env)
        if r.returncode != 0:
            fails.append(f"PE-0: plugin-layout install with pack-it: {r.returncode} {r.stdout[-600:]} {r.stderr[-300:]}")
        else:
            agents = p / ".tf" / "plugin" / "agents"
            if not (agents / "tomasz-solution-architect.md").is_file():
                fails.append(f"PE-1: a persona's executor lies flat in the plugin's agents/: "
                             f"{sorted(x.name for x in agents.glob('*.md'))[:8]}")
            c = subprocess.run([sys.executable, ".tf/factory/build.py", "check"], cwd=p, capture_output=True,
                               text=True, timeout=600, env=env)
            out = c.stdout + c.stderr
            if "extra_agents points to an unknown agent" in out:
                fails.append("PE-2: build check finds the flat agents named in extra_agents: "
                             + next(ln for ln in out.splitlines() if "unknown agent" in ln))
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {3 - len(fails)}/3 plugin extra_agents tests")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
