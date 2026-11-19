#!/usr/bin/env python3
"""Tests of update.py: fetching a new version (from a git repository the latest release by default, tag vX.Y.Z) and the message
about a newer release at session start (notice, the update_notice.py hook)."""
import importlib.util
import json
import os
import zipfile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "update.py").is_file())


def load():
    spec = importlib.util.spec_from_file_location("ctf_update_fetch", ROOT / ".tf" / "factory" / "update.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "-c",
                    "tag.gpgsign=false", *args], cwd=cwd, check=True, capture_output=True)


def make_repo(base: Path, name: str, versions: list[tuple[str, str | None]]) -> str:
    """Repozytorium fabryki: kolejne commity z core/factory/VERSION = wersja, opcjonalnie otagowane; zwraca adres *.git."""
    work = base / f"{name}-work"
    (work / "core" / "factory").mkdir(parents=True)
    (work / "core" / "factory" / "install.py").write_text("")
    (work / "core" / "factory" / "CHANGELOG.md").write_text("# Changelog\n")
    (work / "docs").mkdir()
    (work / "docs" / "notes.md").write_text("a big directory that --check does not fetch\n")
    git(work, "init", "-q", "-b", "main")
    for version, tag in versions:
        (work / "core" / "factory" / "VERSION").write_text(version + "\n")
        git(work, "add", "-A")
        git(work, "commit", "-qm", f"wersja {version}")
        if tag:
            git(work, "tag", "-a", tag, "-m", tag)
    bare = base / f"{name}.git"
    git(base, "clone", "-q", "--bare", str(work), str(bare))
    return str(bare)


def project(base: Path, name: str, version: str, source: str | None) -> Path:
    p = base / name
    (p / ".claude").mkdir(parents=True)
    man = {"version": version, "files": {}}
    if source:
        man["source"] = source
    (p / ".claude" / "factory-manifest.json").write_text(json.dumps(man))
    return p


def factory_dir(base: Path, name: str, version: str) -> Path:
    """A factory source (a directory) in the repository layout: core/factory/install.py and core/factory/VERSION."""
    d = base / name
    (d / "core" / "factory").mkdir(parents=True)
    (d / "core" / "factory" / "install.py").write_text("")
    (d / "core" / "factory" / "VERSION").write_text(version + "\n")
    return d


def notice_tests(up, check) -> None:
    env = {"PATH": os.environ.get("PATH", "")}
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        cache = base / "cache"
        src = factory_dir(base, "fabryka", "2.20.0")
        p = project(base, "app", "2.19.0", str(src))
        msg = up.notice(p, env=env, cache_dir=cache, now=1000.0)
        check(msg and "2.20.0" in msg and "2.19.0" in msg and "update.py" in msg,
              f"UN-1: a newer release in the source (directory) → a message with the versions and the command: {msg}")
        check(up.notice(project(base, "same", "2.20.0", str(src)), env=env, cache_dir=cache, now=1000.0) is None,
              "UN-2: the same version → no message")
        bare = base / "bare"
        (bare / ".claude").mkdir(parents=True)
        check(up.notice(bare, env=env, cache_dir=cache, now=1000.0) is None, "UN-3: no manifest (the factory repo) → none")
        check(up.notice(p, env={**env, "CTF_UPDATE_CHECK": "0"}, cache_dir=cache, now=1000.0) is None,
              "UN-4: CTF_UPDATE_CHECK=0 disables the check")
        (src / "core" / "factory" / "VERSION").write_text("3.0.0\n")
        msg = up.notice(p, env=env, cache_dir=cache, now=1000.0 + 3600)
        check(msg and "2.20.0" in msg, f"UN-5: within a day the result comes from the cache (no repeated query): {msg}")
        msg = up.notice(p, env=env, cache_dir=cache, now=1000.0 + 2 * 86400)
        check(msg and "3.0.0" in msg and "MAJOR" in msg, f"UN-6: after a day it checks again; a MAJOR release is marked: {msg}")
        z = base / "fabryka.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("team-factory-main/core/factory/VERSION", "2.21.0\n")
            zf.writestr("team-factory-main/core/factory/install.py", "")
        msg = up.notice(project(base, "zip", "2.19.0", str(z)), env=env, cache_dir=cache, now=1000.0)
        check(msg and "2.21.0" in msg, f"UN-7: a .zip source → the version from core/factory/VERSION in the archive: {msg}")
        envsrc = factory_dir(base, "z-env", "2.22.0")
        msg = up.notice(project(base, "env", "2.19.0", str(src)), env={**env, "TEAM_FACTORY": str(envsrc)},
                        cache_dir=cache, now=1000.0)
        check(msg and "2.22.0" in msg, f"UN-8: TEAM_FACTORY takes precedence over the manifest: {msg}")
        check(up.notice(project(base, "gone", "2.19.0", str(base / "missing")), env=env, cache_dir=cache,
                        now=1000.0) is None, "UN-9: an unavailable source → no message, no exception")

        # SessionStart hook in a project: the message is visible to the human (systemMessage) and in the agent's context.
        app = project(base, "hook-app", "2.19.0", str(factory_dir(base, "hook-src", "2.20.0")))
        (app / ".tf" / "factory").mkdir(parents=True)
        shutil.copy(ROOT / ".tf" / "factory" / "update.py", app / ".tf" / "factory" / "update.py")
        (app / ".claude" / "hooks").mkdir()
        shutil.copy(ROOT / ".claude" / "hooks" / "update_notice.py", app / ".claude" / "hooks" / "update_notice.py")
        r = subprocess.run([sys.executable, str(app / ".claude" / "hooks" / "update_notice.py")], capture_output=True,
                           text=True, env={**env, "CLAUDE_PROJECT_DIR": str(app), "XDG_CACHE_HOME": str(base / "xdg")},
                           input="{}", timeout=30)
        try:
            out = json.loads(r.stdout)
        except ValueError:
            out = {}
        check(r.returncode == 0 and "2.20.0" in out.get("systemMessage", "")
              and "2.20.0" in out.get("hookSpecificOutput", {}).get("additionalContext", ""),
              f"UN-10: the hook shows the message to the human and the agent: {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(app / ".claude" / "hooks" / "update_notice.py")], capture_output=True,
                           text=True, env={**env, "CLAUDE_PROJECT_DIR": str(bare)}, input="{}", timeout=30)
        check(r.returncode == 0 and r.stdout.strip() == "", f"UN-11: nothing to say → the hook is silent: {r.stdout}{r.stderr}")
        # the quality gate without configuration: the session start says so explicitly (only in a project with the factory)
        gated = base / "gate-app"
        (gated / ".claude" / "hooks").mkdir(parents=True)
        (gated / ".claude" / "factory-manifest.json").write_text("{}")
        for name in ("update_notice.py", "quality_gate.py"):
            shutil.copy(ROOT / ".claude" / "hooks" / name, gated / ".claude" / "hooks" / name)
        genv = {k: v for k, v in env.items() if k != "QG_GATE_DISABLE"}
        r = subprocess.run([sys.executable, str(gated / ".claude" / "hooks" / "update_notice.py")], capture_output=True,
                           text=True, env={**genv, "CLAUDE_PROJECT_DIR": str(gated), "CTF_UPDATE_CHECK": "0"},
                           input="{}", timeout=30)
        check(r.returncode == 0 and "Quality gate disabled" in r.stdout and "systemMessage" in r.stdout,
              f"UN-12: no quality-gate.json → a message at session start: {r.stdout}{r.stderr}")
        (gated / ".claude" / "quality-gate.json").write_text(json.dumps({"command": "npm test"}))
        r = subprocess.run([sys.executable, str(gated / ".claude" / "hooks" / "update_notice.py")], capture_output=True,
                           text=True, env={**genv, "CLAUDE_PROJECT_DIR": str(gated), "CTF_UPDATE_CHECK": "0"},
                           input="{}", timeout=30)
        check(r.returncode == 0 and r.stdout.strip() == "", f"UN-13: bramka skonfigurowana → hook milczy: {r.stdout}{r.stderr}")


def preflight_tests(up, check) -> None:
    """The agent's Bash sandbox blocks writes to skills, agents and settings: an update has to detect this before the first
    write, not leave the installation half done (root in tests bypasses chmod, so the block is faked by a file instead of a directory)."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for rel in (".claude/hooks", ".claude/agents/_generated", "factory"):
            (root / rel).mkdir(parents=True)
        (root / ".claude" / "settings.json").write_text("{}")
        check(up.unwritable(root) == [], f"PF-1: zapisywalny projekt → pusta lista: {up.unwritable(root)}")
        check(not list(root.rglob(".ctf-probe-*")), "PF-2: the write probe leaves no files")
        (root / ".claude" / "skills").write_text("")
        (root / "CLAUDE.md").mkdir()
        got = up.unwritable(root)
        check(got == [".claude/skills/", "CLAUDE.md"], f"PF-3: unwritable paths listed by name: {got}")
        code, msg = up.preflight(root, "python3 .tf/factory/update.py --yes")
        check(code == 2 and ".claude/skills/" in msg and "python3 .tf/factory/update.py --yes" in msg,
              f"PF-4: the message tells the human to run the command themselves: {code} {msg}")
        (root / ".claude" / "skills").unlink()
        (root / "CLAUDE.md").rmdir()
        check(up.preflight(root, "x") == (0, ""), "PF-5: without blocks the update goes on")


def main() -> int:
    up = load()
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    notice_tests(up, check)
    preflight_tests(up, check)
    if not shutil.which("git"):
        print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} update.py tests (no git — part skipped)")
        return 1 if fails else 0

    def version_of(src: str, tmp: Path) -> str:
        return (up.fetch(src, tmp) / "core" / "factory" / "VERSION").read_text().strip()

    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        repo = make_repo(base, "factory", [("1.0.0", "v1.0.0"), ("1.10.0", "v1.10.0"), ("1.9.0", "v1.9.0"),
                                           ("2.0.0-rc.1", "v2.0.0-rc.1"), ("2.0.0-dev", None)])
        check(up.latest_tag(repo) == "v1.10.0", f"the highest release by SemVer, without rc: {up.latest_tag(repo)}")
        for i, (src, want, msg) in enumerate((
                (repo, "1.10.0", "without #ref → the latest release, not the state of main"),
                (repo + "#main", "2.0.0-dev", "#main → the branch directly"),
                (repo + "#v1.0.0", "1.0.0", "#tag → that version"))):
            tmp = base / f"t{i}"
            tmp.mkdir()
            got = version_of(src, tmp)
            check(got == want, f"{msg}: {got}")
        untagged = make_repo(base, "untagged", [("0.1.0", None)])
        check(up.latest_tag(untagged) is None, "a repository without tags → no release")
        (base / "t9").mkdir()
        check(version_of(untagged, base / "t9") == "0.1.0", "without tags → the default branch")
        check(up.latest_tag(str(base / "missing.git")) is None, "an unavailable repository → None, no exception")
        cache = base / "cache"
        for i, (src, want, msg) in enumerate((
                (repo, "1.10.0", "UN-12: a git source → a message about the latest release (tag)"),
                (repo + "#v1.0.0", None, "UN-13: a source pinned to #ref → no message"),
                (str(base / "missing.git"), None, "UN-14: an unavailable repository → no message"))):
            got = up.notice(project(base, f"g{i}", "1.0.0", src), env={"PATH": os.environ.get("PATH", "")},
                            cache_dir=cache, now=1000.0)
            check((got is None) if want is None else (got and want in got), f"{msg}: {got}")

        # UP-1: --check fetches only VERSION, CHANGELOG and install.py (not the whole repository)
        (base / "m1").mkdir()
        meta = up.fetch(repo, base / "m1", meta_only=True)
        check((meta / "core/factory/VERSION").read_text().strip() == "1.10.0" and (meta / "core/factory/CHANGELOG.md").is_file()
              and not (meta / "docs" / "notes.md").exists(),
              f"UP-1: --check fetches only the version and the change list: {sorted(p.relative_to(meta).as_posix() for p in meta.rglob('*') if p.is_file() and '.git' not in p.parts)}")
        (base / "m2").mkdir()
        check((up.fetch(repo, base / "m2") / "docs" / "notes.md").is_file(), "UP-1: a full update fetches everything")

    # UP-2: factory tests in parallel — the same result, a shorter time
    import time
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        tests = root / ".claude" / "tests"
        tests.mkdir(parents=True)
        for i in range(4):
            (tests / f"test_wolny_{i}.py").write_text("import time\ntime.sleep(1)\nprint('✓ 1/1')\n")
        (tests / "test_zly.py").write_text("raise SystemExit(1)\n")
        t0 = time.time()
        failed = up.run_tests(root, workers=4)
        check(failed == ["test_zly.py"] and time.time() - t0 < 3.5,
              f"UP-2: parallel tests: red {failed}, time {time.time() - t0:.1f} s (sequentially ≥ 4 s)")

        # UP-3: a quick check after an update: build.py check and compiling the engine and hook scripts
        (root / ".tf" / "factory").mkdir(parents=True)
        (root / ".tf" / "factory" / "build.py").write_text("import sys\nsys.exit(0)\n")
        (root / ".claude" / "hooks").mkdir()
        (root / ".claude" / "hooks" / "dobry.py").write_text("x = 1\n")
        check(up.quick_check(root) == [], f"UP-3: a healthy installation — no remarks: {up.quick_check(root)}")
        (root / ".claude" / "hooks" / "zly.py").write_text("def (:\n")
        probs = up.quick_check(root)
        check(any("zly.py" in x for x in probs), f"UP-3: a syntax error in a hook detected: {probs}")
        (root / ".tf" / "factory" / "build.py").write_text("import sys\nprint('✗ brak skilla')\nsys.exit(1)\n")
        probs = up.quick_check(root)
        check(any("build.py check" in x for x in probs), f"UP-3: czerwony build.py check wykryty: {probs}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} update.py tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
