#!/usr/bin/env python3
"""Tests of `tf uninstall` (`.tf/factory/uninstall.py`): removes the factory files from the manifest and its entries (CLAUDE.local.md,
.git/info/exclude, Claude Code settings), leaves the human's files (own skills, .tf/config, work results, code),
`--force` removes those too; a backup before removal; `docs/project/` and the project code are never touched.
python3 tests/test_uninstall.py"""
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
INSTALL = ROOT / "core" / "factory" / "install.py"


def install(app: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(INSTALL), str(app), "--yes", "--packs", "none", *extra],
                          capture_output=True, text=True, timeout=300)


def uninstall(app: Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    script = app / ".tf" / "factory" / "uninstall.py"
    return subprocess.run([sys.executable, str(script), *args], cwd=app, capture_output=True, text=True, timeout=300,
                          env=env, stdin=subprocess.DEVNULL)


def project(base: Path, name: str, shared: bool = False) -> Path:
    app = base / name
    app.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=app, check=True)
    (app / "src").mkdir()
    (app / "src" / "main.py").write_text("print('app')\n", encoding="utf-8")
    (app / ("CLAUDE.md" if shared else "CLAUDE.local.md")).write_text("# Moje zasady\n- Testy przez make test.\n",
                                                                       encoding="utf-8")
    (app / ".claude").mkdir()
    (app / ".claude" / ("settings.json" if shared else "settings.local.json")).write_text(json.dumps({
        "permissions": {"allow": ["Bash(make test)"]},
        "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo moje"}]}]}}), encoding="utf-8")
    r = install(app, *(["--shared"] if shared else []))
    assert r.returncode == 0, (r.stdout + r.stderr)[-2000:]
    # the human's files next to the factory
    own = app / ".claude" / "skills" / "moj-skill"
    own.mkdir(parents=True)
    (own / "SKILL.md").write_text("---\nname: moj-skill\ndescription: Mój skill.\n---\n", encoding="utf-8")
    (app / ".tf" / "config").mkdir(parents=True, exist_ok=True)
    (app / ".tf" / "config" / "config.yaml").write_text("work:\n  budget_usd: 3\n", encoding="utf-8")
    (app / ".tf" / "reports").mkdir(parents=True, exist_ok=True)
    (app / ".tf" / "reports" / "security.md").write_text("# raport\n", encoding="utf-8")
    (app / "docs" / "project").mkdir(parents=True, exist_ok=True)
    (app / "docs" / "project" / "lessons.md").write_text("# lekcje\n", encoding="utf-8")
    return app


def snapshot(app: Path) -> dict[str, bytes]:
    return {p.relative_to(app).as_posix(): p.read_bytes() for p in app.rglob("*") if p.is_file() and ".git" not in p.parts}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        env = {**os.environ, "TF_BACKUP_DIR": str(base / "backups"), "TF_PREFERENCES": str(base / "prefs.yaml")}
        app = project(base, "private")
        manifest = json.loads((app / ".claude" / "factory-manifest.json").read_text(encoding="utf-8"))
        files = list(manifest["files"])
        check(isinstance(manifest.get("settings"), dict) and manifest["settings"].get("hooks"),
              "UN-0: the installer records in the manifest the Claude Code settings entries added by the factory")

        before = snapshot(app)
        r = uninstall(app, env, "--dry-run")
        check(r.returncode == 0 and snapshot(app) == before and ".tf/factory/" in r.stdout and "moj-skill" in r.stdout,
              f"UN-1: --dry-run shows the plan, changes nothing: {r.stdout[-800:]}{r.stderr}")
        r = uninstall(app, env)
        check(r.returncode == 1 and snapshot(app) == before,
              f"UN-2: without --yes and without a terminal — refusal, nothing changed: {r.returncode} {r.stdout[-400:]}")

        # the conversation style set the planning mode — uninstall gives the previous one back
        (base / "prefs.yaml").write_text("style: conversation\n", encoding="utf-8")
        subprocess.run([sys.executable, str(app / ".tf/factory/tf.py"), "style"], cwd=app, env=env, capture_output=True)
        local = app / ".claude" / "settings.local.json"
        planned = json.loads(local.read_text(encoding="utf-8"))["permissions"].get("defaultMode") == "plan"

        r = uninstall(app, env, "--yes")
        check(r.returncode == 0, f"UN-3: uninstall --yes: {r.stdout[-1500:]}{r.stderr}")
        left = [f for f in files if (app / f).exists()]
        check(not left, f"UN-3: the factory files from the manifest removed: {left[:5]}")
        gone = [".tf/factory", ".claude/agents/_generated", ".claude/catalog.md", ".claude/factory-manifest.json",
                ".claude/factory-settings.json", ".claude/tests", ".claude/hooks"]
        check(not [g for g in gone if (app / g).exists()],
              f"UN-3: generated directories and files removed: {[g for g in gone if (app / g).exists()]}")
        md = (app / "CLAUDE.local.md").read_text(encoding="utf-8") if (app / "CLAUDE.local.md").exists() else ""
        check("team-factory" not in md and "Testy przez make test" in md,
              f"UN-4: the factory block removed from CLAUDE.local.md, your rules stay: {md}")
        exclude = (app / ".git" / "info" / "exclude").read_text(encoding="utf-8")
        check("team-factory" not in exclude, f"UN-4: the factory block removed from .git/info/exclude: {exclude}")
        s = json.loads(local.read_text(encoding="utf-8")) if local.exists() else {}
        hooks = json.dumps(s.get("hooks", {}))
        check(s.get("permissions", {}).get("allow") == ["Bash(make test)"] and "echo moje" in hooks
              and ".claude/hooks" not in hooks and "statusLine" not in s,
              f"UN-5: settings: your permissions and hooks stay, the factory entries removed: {s}")
        check(planned and s.get("permissions", {}).get("defaultMode") in (None, "default"),
              f"UN-5: the planning mode set by the style given back: {planned} {s.get('permissions')}")
        kept = [".claude/skills/moj-skill/SKILL.md", ".tf/config/config.yaml", ".tf/reports/security.md",
                "docs/project/lessons.md", "src/main.py"]
        check(all((app / k).is_file() for k in kept), f"UN-6: the human's files stay: {[k for k in kept if not (app / k).is_file()]}")
        zips = sorted((base / "backups").glob("*.zip"))
        names = set()
        if zips:
            with zipfile.ZipFile(zips[-1]) as z:
                names = set(z.namelist())
        check(zips and ".claude/factory-manifest.json" in names and "CLAUDE.local.md" in names
              and ".claude/settings.local.json" in names and str(zips[-1]) in r.stdout,
              f"UN-7: a backup of removed and changed files, the path in the message: {zips} {sorted(names)[:5]}")
        r = uninstall(app, env, "--yes") if (app / ".tf/factory/uninstall.py").exists() else None
        check(r is None, "UN-8: after uninstall the factory engine is gone")

        # --force: own skills too, .tf/ entirely; docs/project and the code stay
        app2 = project(base, "force")
        r = uninstall(app2, env, "--yes", "--force")
        check(r.returncode == 0 and not (app2 / ".tf").exists() and not (app2 / ".claude/skills/moj-skill").exists()
              and (app2 / "docs/project/lessons.md").is_file() and (app2 / "src/main.py").is_file(),
              f"UN-9: --force removes own skills and .tf/ too, leaves docs/project and the code: {r.stdout[-800:]}{r.stderr}")

        # team install: CLAUDE.md, .gitignore, settings.json
        app3 = project(base, "shared", shared=True)
        r = uninstall(app3, env, "--yes")
        md = (app3 / "CLAUDE.md").read_text(encoding="utf-8")
        gi = (app3 / ".gitignore").read_text(encoding="utf-8") if (app3 / ".gitignore").exists() else ""
        st = json.loads((app3 / ".claude/settings.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and "team-factory" not in md and "Testy przez make test" in md and "team-factory" not in gi
              and st.get("permissions", {}).get("allow") == ["Bash(make test)"],
              f"UN-10: team install: CLAUDE.md, .gitignore and settings.json without the factory entries: {r.stdout[-600:]} {st}")

        empty = base / "empty"
        empty.mkdir()
        r = subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "uninstall.py")], cwd=empty,
                           capture_output=True, text=True, env=env)
        check(r.returncode == 2, f"UN-11: no factory in the directory — code 2: {r.stdout}{r.stderr}")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} uninstall tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
