#!/usr/bin/env python3
"""No AI co-author in the commits and PRs of a factory project: the author is only the person logged into git.

Claude Code adds a `Co-Authored-By` trailer to commits, a "Generated with Claude Code" line to PR descriptions and, in
cloud and Remote Control sessions, a `Claude-Session` link, unless the settings key `attribution` hides them
(code.claude.com/docs/en/settings-reference#attribution, read 2026-11-25: `commit: ""` and `pr: ""` hide the text,
`sessionUrl: false` drops the link; `includeCoAuthoredBy` is deprecated and ignored once `commit` or `pr` is set).
Both layouts get it: the classic one in the project settings, the plugin one in the factory session's settings
(`tf code --settings`), and the factory rules (CLAUDE.md block / the plugin's RULES.md) say it for any session, because
Claude Code ranks the project's own instructions about attribution above its default lines. A value you set stays.
python3 tests/test_no_ai_attribution.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ["TF_NO_PLUGIN_REGISTER"] = "1"   # installs here never call the real Claude Code CLI (plugin_register.py)

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
INSTALL = ROOT / "core" / "factory" / "install.py"
HIDDEN = {"commit": "", "pr": "", "sessionUrl": False}
RULE = "no AI co-author"


def install(p: Path, *opts: str) -> subprocess.CompletedProcess:
    p.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(p)], check=False)
    return subprocess.run([sys.executable, str(INSTALL), str(p), "--yes", "--packs", "none", *opts], capture_output=True,
                          text=True, timeout=600, env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                                                       "HOME": str(p.parent), "TF_NO_PLUGIN_REGISTER": "1"})


def read(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    core = read(ROOT / "core" / "settings.json")
    check(core.get("attribution") == HIDDEN and "includeCoAuthoredBy" not in core,
          f"NA-1: core/settings.json hides the commit and PR attribution and the session link: {core.get('attribution')}")
    check(RULE in (ROOT / "core" / "CLAUDE.md").read_text(encoding="utf-8"),
          "NA-2: the factory rules (core/CLAUDE.md) say commits and PRs carry no AI co-author")

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        classic = base / "classic"
        r = install(classic, "--layout", "default")
        s = read(classic / ".claude" / "settings.local.json")
        check(r.returncode == 0 and s.get("attribution") == HIDDEN,
              f"NA-3: the classic layout puts attribution in the project settings: {r.returncode} {s.get('attribution')} "
              f"{r.stdout[-300:]}")
        check(RULE in (classic / "CLAUDE.local.md").read_text(encoding="utf-8"),
              "NA-4: the classic layout's rules block names the no-AI-co-author rule")

        plugin = base / "plugin"
        r = install(plugin)
        s = read(plugin / ".tf" / "plugin" / "session-settings.json")
        check(r.returncode == 0 and s.get("attribution") == HIDDEN,
              f"NA-5: the plugin layout puts attribution in the factory session's settings: {r.returncode} "
              f"{s.get('attribution')} {r.stdout[-300:]}")
        check(RULE in (plugin / ".tf" / "plugin" / "RULES.md").read_text(encoding="utf-8"),
              "NA-6: the plugin's RULES.md (SessionStart) names the no-AI-co-author rule")

        mine = base / "mine"
        (mine / ".claude").mkdir(parents=True)
        (mine / ".claude" / "settings.local.json").write_text(json.dumps({"attribution": {"commit": "Team: X"}}),
                                                             encoding="utf-8")
        r = install(mine, "--layout", "default")
        s = read(mine / ".claude" / "settings.local.json")
        check(r.returncode == 0 and s.get("attribution") == {"commit": "Team: X"},
              f"NA-7: your own attribution value stays: {s.get('attribution')}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} no-AI-attribution tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
