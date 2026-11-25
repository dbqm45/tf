#!/usr/bin/env python3
"""Edge cases of installation and its lifecycle (install.py, update.py, uninstall.py, plugin_register.py, tf.py):
an unreadable manifest or lock (an interrupted update, a merge conflict), a read-only factory source, a project path
with spaces and non-ASCII characters outside git, a broken ignore block, an update whose plan or installer fails, an
interrupted install and a rollback after it, rollback twice and from a damaged backup, a huge `.tf/backup/`,
uninstall keeping CRLF and then a reinstall, `tf` run from a subdirectory, two pack sources with the same id, a git
pack source at a tag that is gone, `TF_NO_PLUGIN_REGISTER` values and Windows command lines (TF_CLAUDE, quoting).
python3 tests/test_install_edges.py"""
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
os.environ["TF_NO_PLUGIN_REGISTER"] = "1"   # installs here never call the real Claude Code CLI (plugin_register.py)

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
MANIFEST = ".claude/factory-manifest.json"
LOCK = ".claude/factory-lock.json"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "-c",
                    "tag.gpgsign=false", *args], cwd=cwd, check=True, capture_output=True)


def install(src: Path, proj: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(src / "core" / "factory" / "install.py"), str(proj), "--yes",
                           "--layout", "default", *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=300, env=env)


def update(proj: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(proj / ".tf" / "factory" / "update.py"), *args], cwd=proj,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600,
                          stdin=subprocess.DEVNULL)


def tf(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "tf.py"), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
                          stdin=subprocess.DEVNULL)


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def project(base: Path, name: str, git_repo: bool = True) -> Path:
    p = base / name
    p.mkdir(parents=True)
    if git_repo:
        subprocess.run(["git", "init", "-q"], cwd=p, check=True)
    return p


def manifest(proj: Path) -> dict:
    try:
        return json.loads((proj / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def out(r: subprocess.CompletedProcess) -> str:
    return r.stdout + r.stderr


def copy_factory(dst: Path) -> Path:
    shutil.copytree(ROOT / "core", dst / "core", ignore=shutil.ignore_patterns("__pycache__"))
    return dst


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)

        # IE-1: a manifest cut off by an interrupted update — the installer does not crash on the JSON; it updates as an
        # install without a manifest (changed files overwritten, copies in .tf/backup/) and writes a valid manifest
        p = project(base, "cut")
        r = install(ROOT, p, "--packs", "none")
        check(r.returncode == 0, f"IE-1: install: {out(r)[-600:]}")
        hook = p / ".claude" / "hooks" / "guard_paths.py"
        hook.write_text(hook.read_text(encoding="utf-8") + "# mine\n", encoding="utf-8")
        (p / MANIFEST).write_text('{"version": "24.1', encoding="utf-8")
        r = install(ROOT, p)
        check(r.returncode == 0 and "Traceback" not in out(r) and "unreadable" in r.stdout and "--rollback" in r.stdout
              and "Skipped existing files" not in r.stdout,
              f"IE-1: a cut-off manifest → an update without a manifest, with a message: {r.returncode} {out(r)[-900:]}")
        check("# mine" not in hook.read_text(encoding="utf-8") and list((p / ".tf" / "backup").rglob("guard_paths.py"))
              and manifest(p).get("files", {}).get(".claude/hooks/guard_paths.py"),
              "IE-1: the changed factory file overwritten, its copy in .tf/backup/, the manifest valid again")
        # IE-1b: an empty manifest ({}) — the same, not "your files with the same names" for every factory file
        (p / MANIFEST).write_text("{}", encoding="utf-8")
        r = install(ROOT, p)
        check(r.returncode == 0 and "Skipped existing files" not in r.stdout and manifest(p).get("files"),
              f"IE-1b: an empty manifest → updated, no factory file skipped as yours: {r.stdout[-700:]}")
        # IE-1c: update.py with a cut-off manifest: a warning with --rollback, the backup and the update go through
        (p / MANIFEST).write_text('{"version": "24.1', encoding="utf-8")
        r = update(p, "--source", str(ROOT), "--yes", "--force")
        check(r.returncode == 0 and "Traceback" not in out(r) and "unreadable" in r.stdout and "--rollback" in r.stdout
              and manifest(p).get("version"),
              f"IE-1c: update.py with a cut-off manifest: {r.returncode} {out(r)[-900:]}")

        # IE-2: a team clone whose committed lock has a merge conflict — ignored with a message, written again
        c = project(base, "conflict")
        r = install(ROOT, c, "--packs", "none", "--shared")
        (c / MANIFEST).unlink()
        (c / LOCK).write_text("<<<<<<< HEAD\n{}\n=======\n{}\n>>>>>>> other\n", encoding="utf-8")
        r = install(ROOT, c)
        lock_text = (c / LOCK).read_text(encoding="utf-8")
        check(r.returncode == 0 and "Traceback" not in out(r) and "merge conflict" in r.stdout
              and lock_text.startswith("{") and json.loads(lock_text).get("version")
              and manifest(c).get("mode") == "shared" and "pack-docs" not in manifest(c).get("packs", {}),
              f"IE-2: an unreadable lock → a message, still a team install with its packs, the lock written again: "
              f"{r.returncode} {manifest(c).get('mode')} {list(manifest(c).get('packs', {}))} {out(r)[-700:]}")

        # IE-3: a read-only factory source (a read-only share, a package store): the installed files stay writable for
        # the owner (copymode copied 0444, and the next update failed with PermissionError for a non-root user);
        # an install that already has read-only files gets them writable again on the update
        ro = copy_factory(base / "ro-src")
        for f in (ro / "core").rglob("*"):
            if f.is_file():
                f.chmod(f.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
        q = project(base, "from-ro")
        r = install(ro, q, "--packs", "none")
        files = [q / rel for rel in manifest(q).get("files", {})] if r.returncode == 0 else []
        locked = [f.relative_to(q).as_posix() for f in files if f.is_file() and not f.stat().st_mode & stat.S_IWUSR]
        check(r.returncode == 0 and files and not locked,
              f"IE-3: files from a read-only source are writable for the owner: {r.returncode} {locked[:5]}")
        exe = q / ".claude" / "hooks" / "cleanroom_guard.py"
        check(not (ROOT / "core" / "hooks" / "cleanroom_guard.py").stat().st_mode & stat.S_IXUSR
              or exe.stat().st_mode & stat.S_IXUSR, "IE-3: the source's execute bit is kept")
        engine_src = ro / "core" / "factory" / "flag_check.py"
        engine_src.chmod(0o644)
        engine_src.write_text(engine_src.read_text(encoding="utf-8") + "# v2\n", encoding="utf-8")
        engine_src.chmod(0o444)
        engine = q / ".tf" / "factory" / "flag_check.py"
        engine.chmod(0o444)                 # an install from before the fix: read-only factory files
        r = install(ro, q)
        check(r.returncode == 0 and "# v2" in engine.read_text(encoding="utf-8") and engine.stat().st_mode & stat.S_IWUSR,
              f"IE-3: an update writes over a read-only factory file and leaves it writable: {r.returncode} "
              f"{oct(engine.stat().st_mode)} {out(r)[-400:]}")
        for f in (ro / "core").rglob("*"):
            f.chmod(f.stat().st_mode | stat.S_IWUSR)   # the temporary directory can be removed

        # IE-4: a project path with spaces and Polish letters, outside git: install works, entries go to .gitignore,
        # build.py check passes, the plugin marketplace name is plain ASCII
        w = project(base / "Moje Projekty", "Aplikacja ął zażółć", git_repo=False)
        r = install(ROOT, w, "--packs", "none")
        gi = (w / ".gitignore").read_text(encoding="utf-8") if (w / ".gitignore").is_file() else ""
        check(r.returncode == 0 and "not a git repository" in r.stdout and ".tf/" in gi,
              f"IE-4: install into a non-git path with spaces and ą, ł: {r.returncode} {out(r)[-700:]}")
        b = subprocess.run([sys.executable, ".tf/factory/build.py", "check"], cwd=w, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        check(b.returncode == 0, f"IE-4: build.py check in that path: {(b.stdout + b.stderr)[-500:]}")
        reg = load("tf_reg_ie4", ROOT / "core" / "factory" / "plugin_register.py")
        name = reg.market_name(w)
        check(name.isascii() and " " not in name and name.startswith("tf-aplikacja-"),
              f"IE-4: the marketplace name is ASCII without spaces: {name}")
        cmd = reg.commands(w)[0]
        import shlex
        check(shlex.split(cmd)[4] == str(reg.market_path(w)), f"IE-4: the printed command keeps the path whole: {cmd}")
        # IE-4b: the plugin layout in the same path (the default) installs and builds its agents
        w2 = project(base / "Moje Projekty", "Wtyczka łódź", git_repo=False)
        r = subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "install.py"), str(w2), "--yes", "--packs",
                            "none"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        check(r.returncode == 0 and (w2 / ".tf" / "plugin" / ".claude-plugin" / "plugin.json").is_file()
              and list((w2 / ".tf" / "plugin" / "agents").rglob("*.md")),
              f"IE-4b: the plugin layout in a path with spaces and ł: {r.returncode} {out(r)[-500:]}")

        # IE-5: a broken factory block (start marker, no end marker) in .gitignore or .git/info/exclude: a clear refusal
        # naming the file and what to do — no traceback, no guessing where your lines start
        gi_begin = "# team-factory:begin (managed by factory/install.py)"
        g = project(base, "broken-gi")
        write(g / ".gitignore", f"node_modules\n{gi_begin}\n.tf/\nmine.log\n")
        r = install(ROOT, g, "--packs", "none")
        check(r.returncode != 0 and "Traceback" not in out(r) and ".gitignore" in out(r) and "by hand" in out(r),
              f"IE-5: .gitignore with a broken factory block: {r.returncode} {out(r)[-500:]}")
        check("mine.log" in (g / ".gitignore").read_text(encoding="utf-8"), "IE-5: .gitignore left as it was")
        x = project(base, "broken-exclude")
        write(x / ".git" / "info" / "exclude", f"{gi_begin}\n.tf/\n")
        r = install(ROOT, x, "--packs", "none")
        check(r.returncode != 0 and "Traceback" not in out(r) and ".git/info/exclude" in out(r)
              and "instructions file" not in out(r),
              f"IE-5: .git/info/exclude with a broken block names that file: {r.returncode} {out(r)[-500:]}")

        # IE-6: update.py takes a file:// git URL as a git source (install.py does for --pack-dir); before, it became
        # the path <project>/file:/… and the update said "Source not found"
        repo = copy_factory(base / "factory-repo")
        git(repo, "init", "-q", "-b", "main")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "factory")
        r = update(p, "--check", "--source", f"file://{repo}")
        check(r.returncode == 0 and "available:" in r.stdout and "Source not found" not in out(r),
              f"IE-6: update.py --source file://…: {r.returncode} {out(r)[-500:]}")
        up = load("tf_update_ie6", ROOT / "core" / "factory" / "update.py")
        tfm = load("tf_tf_ie6", ROOT / "core" / "factory" / "tf.py")
        check(up.is_git("file:///srv/tf") and tfm.is_git("file:///srv/tf") and not up.is_git("/srv/tf"),
              "IE-6: is_git knows file:// in update.py and tf.py")

        # IE-7: a plan that fails (an unknown pack) stops before the backup and the install: nothing was changed
        backups = sorted((p / ".tf" / "backup").iterdir())
        r = update(p, "--source", str(ROOT), "--yes", "--add", "pack-does-not-exist")
        check(r.returncode == 2 and "nothing was changed" in r.stdout and "Backup before the update" not in r.stdout
              and sorted((p / ".tf" / "backup").iterdir()) == backups,
              f"IE-7: a failing update plan changes nothing: {r.returncode} {r.stdout[-600:]}")

        # IE-8: the installer of the new version stops half-way (exit ≠ 0 after the backup): the message says the
        # install may be half-done and how to go back (before: a bare exit code)
        fake = base / "fake-src"
        write(fake / "core" / "factory" / "VERSION", "999.0.0\n")
        write(fake / "core" / "factory" / "install.py",
              "import sys\nprint('half-way')\nsys.exit(0 if '--dry-run' in sys.argv else 3)\n")
        r = update(p, "--source", str(fake), "--yes")
        check(r.returncode == 3 and "--rollback" in r.stdout.split("half-way")[-1] and "half-done" in r.stdout,
              f"IE-8: a failing installer → the rollback command: {r.returncode} {r.stdout[-600:]}")
        r = update(p, "--rollback")
        check(r.returncode == 0 and "Restored version" in r.stdout, f"IE-8: and the rollback works: {out(r)[-400:]}")

        # IE-9: an install interrupted half-way (Ctrl-C, a killed process) and a rollback after it: the backup from
        # before restores the old files; running the update again converges (no factory file taken for yours)
        src = copy_factory(base / "src-v2")
        i = project(base, "interrupted")
        r = install(src, i, "--packs", "none")
        check(r.returncode == 0, f"IE-9: install v1: {out(r)[-400:]}")
        old_version = manifest(i)["version"]
        hooks = sorted((src / "core" / "hooks").glob("*.py"))
        for h in hooks:
            h.write_text(h.read_text(encoding="utf-8") + "# v2\n", encoding="utf-8")
        write(src / "core" / "hooks" / "brand_new_hook.py", "print('new')\n")
        major, minor, _ = old_version.split(".")
        write(src / "core" / "factory" / "VERSION", f"{major}.{int(minor) + 1}.0\n")
        up_i = load("tf_update_ie9", i / ".tf" / "factory" / "update.py")
        up_i.backup(i)
        runner = ("import importlib.util, sys\n"
                  f"spec = importlib.util.spec_from_file_location('inst', {str(src / 'core' / 'factory' / 'install.py')!r})\n"
                  "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
                  "orig, n = m.Plan._write, [0]\n"
                  "def cut(self, dst, data, s):\n"
                  "    n[0] += 1\n"
                  "    if n[0] > 6:\n"
                  "        raise KeyboardInterrupt\n"
                  "    orig(self, dst, data, s)\n"
                  "m.Plan._write = cut\n"
                  f"sys.exit(m.main(['install.py', {str(i)!r}, '--yes', '--layout', 'default']))\n")
        r = subprocess.run([sys.executable, "-c", runner], capture_output=True, text=True, timeout=300)
        v2 = [h.name for h in (i / ".claude" / "hooks").glob("*.py") if "# v2" in h.read_text(encoding="utf-8")]
        check(r.returncode != 0 and v2 and manifest(i)["version"] == old_version,
              f"IE-9: the simulated interruption left a half-done install: {r.returncode} {len(v2)}")
        code, msg = up_i.rollback(i)
        v2 = [h.name for h in (i / ".claude" / "hooks").glob("*.py") if "# v2" in h.read_text(encoding="utf-8")]
        check(code == 0 and not v2 and manifest(i)["version"] == old_version,
              f"IE-9: the rollback after the interruption restores the old files: {code} {msg} {v2}")
        r = install(src, i)
        v1 = [h.name for h in hooks if "# v2" not in (i / ".claude" / "hooks" / h.name).read_text(encoding="utf-8")]
        check(r.returncode == 0 and not v1 and "Skipped existing files" not in r.stdout
              and ".claude/hooks/brand_new_hook.py" in manifest(i).get("files", {}),
              f"IE-9: the update run again converges: {r.returncode} {v1} {r.stdout[-600:]}")

        # IE-10: --rollback twice: the second one restores the same backup again (idempotent), it does not go further
        # back or fail; IE-10b: --rollback with no backup says so
        code1, _ = up_i.rollback(i)
        state = {f.relative_to(i).as_posix(): f.read_bytes() for f in (i / ".claude" / "hooks").glob("*.py")}
        man1 = manifest(i)
        code2, msg2 = up_i.rollback(i)
        state2 = {f.relative_to(i).as_posix(): f.read_bytes() for f in (i / ".claude" / "hooks").glob("*.py")}
        check(code1 == code2 == 0 and state == state2 and manifest(i) == man1 and man1["version"] == old_version,
              f"IE-10: rollback twice gives the same state: {code1} {code2} {msg2}")
        n = project(base, "no-backup")
        r = install(ROOT, n, "--packs", "none")
        r = update(n, "--rollback")
        check(r.returncode == 2 and "No backup" in r.stdout and "Traceback" not in out(r),
              f"IE-10b: rollback without a backup: {r.returncode} {out(r)[-300:]}")

        # IE-11: a damaged last backup (backup.json unreadable, or files missing from it): refused, nothing changed,
        # with what to do — before, a traceback half-way through restoring
        last = sorted(d for d in (i / ".tf" / "backup").iterdir() if (d / "backup.json").is_file())[-1]
        before = {f.relative_to(i).as_posix(): f.read_bytes() for f in (i / ".claude" / "hooks").glob("*.py")}
        meta = json.loads((last / "backup.json").read_text(encoding="utf-8"))
        gone = last / meta["files"][0]
        kept = gone.read_bytes()
        gone.unlink()
        code, msg = up_i.rollback(i)
        after = {f.relative_to(i).as_posix(): f.read_bytes() for f in (i / ".claude" / "hooks").glob("*.py")}
        check(code == 2 and "incomplete" in msg and "nothing was changed" in msg and before == after,
              f"IE-11: an incomplete backup → refused, nothing changed: {code} {msg}")
        gone.write_bytes(kept)
        (last / "backup.json").write_text('{"version": ', encoding="utf-8")
        code, msg = up_i.rollback(i)
        check(code == 2 and "damaged" in msg and "Traceback" not in msg, f"IE-11: a damaged backup.json: {code} {msg}")
        (last / "backup.json").write_text(json.dumps(meta), encoding="utf-8")

        # IE-12: a huge .tf/backup/ (many old copies, a stray file): a new backup copies none of the old copies, keeps
        # the last 3 marked copies, leaves the unmarked directories and the stray file
        bk = i / ".tf" / "backup"
        for k in range(6):
            d = bk / f"2020010{k}-000000"
            write(d / "big" / "blob.bin", "x" * 1000)
        (bk / "README.txt").write_text("my note\n", encoding="utf-8")
        for k in range(5):
            up_i.backup(i, now=1_800_000_000 + k)
        marked = sorted(d.name for d in bk.iterdir() if (d / "backup.json").is_file())
        newest = bk / marked[-1]
        check(len(marked) == 3 and not list(newest.rglob("blob.bin")) and not (newest / ".tf" / "backup").exists()
              and (bk / "README.txt").is_file() and len([d for d in bk.iterdir() if d.name.startswith("2020")]) == 6,
              f"IE-12: retention with a huge .tf/backup/: {marked}")
        code, msg = up_i.rollback(i)
        check(code == 0, f"IE-12: rollback with a stray file in .tf/backup/: {code} {msg}")

        # IE-13: uninstall keeps the line ending of the files it edits (a committed CRLF CLAUDE.md and .gitignore stay
        # CRLF — before, they became LF: a whole-file diff); then a reinstall is a fresh install, no file skipped
        u = project(base, "crlf")
        (u / "CLAUDE.md").write_bytes(b"# Mine\r\n- rule\r\n")
        (u / ".gitignore").write_bytes(b"node_modules\r\n")
        r = install(ROOT, u, "--packs", "none", "--shared")
        check(r.returncode == 0 and b"\r\n<!-- team-factory:begin -->" in (u / "CLAUDE.md").read_bytes(),
              f"IE-13: the install keeps CRLF: {out(r)[-300:]}")
        r = subprocess.run([sys.executable, str(u / ".tf" / "factory" / "uninstall.py"), "--yes"], cwd=u,
                           capture_output=True, text=True, timeout=300,
                           env={**os.environ, "TF_BACKUP_DIR": str(base / "zips")})
        check(r.returncode == 0 and (u / "CLAUDE.md").read_bytes() == b"# Mine\r\n- rule\r\n"
              and (u / ".gitignore").read_bytes() == b"node_modules\r\n",
              f"IE-13: uninstall keeps CRLF: {(u / 'CLAUDE.md').read_bytes()[:40]!r} "
              f"{(u / '.gitignore').read_bytes()[:40]!r} {out(r)[-300:]}")
        r = install(ROOT, u, "--packs", "none", "--shared")
        check(r.returncode == 0 and "Installed in" in r.stdout and "Updated in" not in r.stdout
              and "Skipped existing files" not in r.stdout and (u / LOCK).is_file(),
              f"IE-13: uninstall then reinstall = a fresh install: {r.returncode} {r.stdout[-500:]}")

        # IE-14: uninstall where git is not on PATH (a bare Windows machine): no crash on finding .git/info/exclude
        nogit = base / "empty-path"
        nogit.mkdir()
        r = subprocess.run([sys.executable, str(u / ".tf" / "factory" / "uninstall.py"), "--yes"], cwd=u,
                           capture_output=True, text=True, timeout=300,
                           env={**os.environ, "PATH": str(nogit), "TF_BACKUP_DIR": str(base / "zips")})
        check(r.returncode == 0 and "Traceback" not in out(r) and not (u / MANIFEST).exists(),
              f"IE-14: uninstall without git: {r.returncode} {out(r)[-500:]}")

        # IE-15: tf run in a subdirectory of an installed project: commands say where the factory is (not "install
        # it first"), and a bare `tf` does not install a second factory into the subdirectory
        sub = p / "src" / "deep"
        sub.mkdir(parents=True)
        r = tf(sub, "doctor")
        check(r.returncode == 2 and str(p) in r.stdout and "cd " in r.stdout and "Install it first" not in r.stdout,
              f"IE-15: tf doctor in a subdirectory: {r.returncode} {r.stdout[-300:]}")
        r = tf(sub)
        check(r.returncode == 2 and str(p) in r.stdout and not (sub / ".claude").exists()
              and not (p / "src" / ".claude").exists(),
              f"IE-15: a bare tf in a subdirectory installs nothing there: {r.returncode} {r.stdout[-300:]}")

        # IE-16: two pack sources that provide the same id: refused, naming both sources and what to do
        major = int((ROOT / "core" / "factory" / "VERSION").read_text(encoding="utf-8").split(".")[0])

        def make_pack(d: Path, pid: str) -> Path:
            write(d / "pack.yaml", f"id: {pid}\nversion: 1.0.0\ntitle: X\ndescription: Test.\n"
                                   f"requires: {{core: \">={major}.0.0 <{major + 1}.0.0\"}}\n"
                                   "facets:\n  - {prefix: xq-, order: 910, name: x, question: \"x\"}\n")
            write(d / "skills" / "xq-run" / "SKILL.md", "---\nname: xq-run\ndescription: Użyj przy X.\nmetadata:\n"
                                                        "  catalog: \"Użyj przy X. Nie do niczego.\"\n---\n# xq-run\n")
            return d
        one, two = make_pack(base / "team-a" / "pack", "pack-dup"), make_pack(base / "team-b" / "pack", "pack-dup")
        d2 = project(base, "dup")
        r = install(ROOT, d2, "--packs", "pack-dup", "--pack-dir", f"{one},{two}")
        check(r.returncode == 2 and str(one.resolve()) in r.stdout and str(two.resolve()) in r.stdout
              and "rename" in r.stdout and not (d2 / MANIFEST).exists(),
              f"IE-16: two sources with the same pack id: {r.returncode} {r.stdout[-500:]}")

        # IE-17: a git pack source pinned to a tag that no longer exists: a new source is refused with git's reason;
        # a remembered one whose pack is installed stops the update with the fix (new location or drop it)
        work = base / "pack-repo"
        make_pack(work / "factory-pack", "pack-tagged")
        git(work, "init", "-q", "-b", "main")
        git(work, "add", "-A")
        git(work, "commit", "-qm", "v1")
        git(work, "tag", "-a", "v1.0.0", "-m", "v1.0.0")
        url = f"file://{work}#v1.0.0"
        tg = project(base, "tagged")
        r = install(ROOT, tg, "--packs", "pack-tagged", "--pack-dir", url)
        check(r.returncode == 0 and (tg / ".claude" / "skills" / "xq-run" / "SKILL.md").is_file(),
              f"IE-17: install from the git tag: {out(r)[-500:]}")
        git(work, "tag", "-d", "v1.0.0")
        r = install(ROOT, tg)
        check(r.returncode == 2 and "pack-tagged" in r.stdout and "--pack-dir" in r.stdout and "--drop-pack-dir" in r.stdout
              and "Nothing was changed" in r.stdout and (tg / ".claude" / "skills" / "xq-run" / "SKILL.md").is_file(),
              f"IE-17: the remembered tag is gone → the update stops with the fix: {r.returncode} {r.stdout[-600:]}")
        r = install(ROOT, project(base, "tagged-new"), "--packs", "pack-tagged", "--pack-dir", f"file://{work}#v9.9.9")
        check(r.returncode == 2 and "Pack source not found" in r.stdout and "v9.9.9" in r.stdout,
              f"IE-17: a new source at a missing tag is refused: {r.returncode} {r.stdout[-400:]}")

    # IE-18: TF_NO_PLUGIN_REGISTER: "1", "yes" skip the CLI; "", "0", "false", "no", "off" do not (as CI does)
    reg = load("tf_reg_ie18", ROOT / "core" / "factory" / "plugin_register.py")
    saved = {k: os.environ.get(k) for k in ("TF_NO_PLUGIN_REGISTER", "CI")}
    try:
        os.environ.pop("CI", None)
        for value, skip in (("1", True), ("yes", True), ("", False), ("0", False), ("false", False), ("No", False),
                            ("off", False)):
            os.environ["TF_NO_PLUGIN_REGISTER"] = value
            check(bool(reg.skipped()) == skip, f"IE-18: TF_NO_PLUGIN_REGISTER={value!r} skips: {reg.skipped()}")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # IE-19: Windows command lines. TF_CLAUDE with a Windows path keeps its backslashes (POSIX splitting made
    # C:\npm\claude.cmd into C:npmclaude.cmd); a quoted path with spaces is one argument; the printed registration
    # command quotes a path for cmd.exe/PowerShell with double quotes, never '…' (cmd.exe does not take them)
    got = reg.split_command(r"C:\npm\claude.cmd --verbose", windows=True)
    check(got == [r"C:\npm\claude.cmd", "--verbose"], f"IE-19: TF_CLAUDE on Windows: {got}")
    check(reg.split_command(r'"C:\Program Files\nodejs\claude.cmd" -c', windows=True)
          == [r"C:\Program Files\nodejs\claude.cmd", "-c"], "IE-19: a quoted Windows path with spaces is one argument")
    check(reg.split_command("npx claude", windows=False) == ["npx", "claude"]
          and reg.split_command("npx.cmd claude", windows=True) == ["npx.cmd", "claude"],
          "IE-19: npx (POSIX) and npx.cmd (Windows) with an argument")
    check(reg.quote(r"C:\Users\Jan Kowalski\app\.tf\x.json", windows=True) == r'"C:\Users\Jan Kowalski\app\.tf\x.json"'
          and reg.quote(r"C:\app\x.json", windows=True) == r"C:\app\x.json"
          and reg.quote("/home/jan/My App/x.json", windows=False) == "'/home/jan/My App/x.json'",
          "IE-19: quoting for the shell of the platform")
    with tempfile.TemporaryDirectory() as t:
        exe = Path(t) / "Claude Code" / "claude"
        write(exe, "#!/bin/sh\necho '[]'\n")
        exe.chmod(0o755)
        os.environ["TF_CLAUDE"] = str(exe)
        try:
            got = reg.claude()
            check(got == [str(exe)], f"IE-19: TF_CLAUDE naming a file with a space in its path: {got}")
            tfm = load("tf_tf_ie19", ROOT / "core" / "factory" / "tf.py")
            cwd = os.getcwd()
            proj = Path(t) / "proj"
            shutil.copytree(ROOT / "core" / "factory", proj / ".tf" / "factory",
                            ignore=shutil.ignore_patterns("__pycache__"))
            os.chdir(proj)
            try:
                check(tfm.claude_command() == [str(exe)], f"IE-19: tf code splits TF_CLAUDE the same way: "
                                                          f"{tfm.claude_command()}")
            finally:
                os.chdir(cwd)
        finally:
            os.environ.pop("TF_CLAUDE", None)

    # IE-21: the Windows launcher tf.cmd: written as bytes (a text-mode write turns its CRLF into CR CR LF) in the
    # console's code page; outside Windows (no "oem" codec) UTF-8. The install itself runs with tf.py's os.name = "nt"
    tfm = load("tf_tf_ie21", ROOT / "core" / "factory" / "tf.py")
    check(tfm.cmd_bytes('@"C:\\Users\\Łukasz\\py.exe" %*\r\n').endswith(b" %*\r\n")
          and b"\r\r" not in tfm.cmd_bytes("a\r\n"), "IE-21: cmd_bytes keeps CRLF as it is")
    with tempfile.TemporaryDirectory() as t:
        import types
        real_os = tfm.os
        tfm.os = types.SimpleNamespace(name="nt", environ=os.environ, pathsep=os.pathsep)
        try:
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                rc = tfm.install_launcher("https://example.com/tf.git", Path(t) / "bin")
        finally:
            tfm.os = real_os
        data = (Path(t) / "bin" / "tf.cmd").read_bytes() if (Path(t) / "bin" / "tf.cmd").is_file() else b""
        check(rc == 0 and data.endswith(b'"%~dp0tf" %*\r\n') and b"\r\r" not in data
              and sys.executable.encode("utf-8") in data, f"IE-21: tf.cmd for Windows: {rc} {data!r}")
        src = (ROOT / "core" / "factory" / "tf.py").read_text(encoding="utf-8")
        check(not any("tf.cmd" in ln and ".write_text(" in ln for ln in src.splitlines()),
              "IE-21: tf.py writes tf.cmd with write_bytes, not a text-mode write_text")

    # IE-20: registration when `claude` is missing, or hangs (offline, a gateway that never answers): the install is
    # not broken — register() returns why, and the warning block gives the two commands to run by hand
    with tempfile.TemporaryDirectory() as t:
        root = Path(t) / "app"
        write(root / ".tf" / "plugin" / ".claude-plugin" / "plugin.json", "{}\n")
        empty, slow = Path(t) / "empty", Path(t) / "slow"
        empty.mkdir()
        write(slow / "claude", "#!/bin/sh\nsleep 5\n")
        (slow / "claude").chmod(0o755)
        saved = {k: os.environ.get(k) for k in ("TF_NO_PLUGIN_REGISTER", "CI", "PATH", "TF_CLAUDE")}
        timeout = reg.TIMEOUT
        try:
            for k in ("TF_NO_PLUGIN_REGISTER", "CI", "TF_CLAUDE"):
                os.environ.pop(k, None)
            os.environ["PATH"] = str(empty)
            ok, why = reg.register(root)
            block = reg.warning_block(root, why)
            check(not ok and "not in PATH" in why and "claude plugin install" in block and "tf code" in block,
                  f"IE-20: no claude on PATH: {ok} {why}")
            os.environ["PATH"] = str(slow) + os.pathsep + saved["PATH"]
            reg.TIMEOUT = 1
            ok, why = reg.register(root)
            check(not ok and "did not finish" in why and "claude plugin marketplace add" in reg.warning_block(root, why),
                  f"IE-20: a claude that hangs (offline): {ok} {why}")
        finally:
            reg.TIMEOUT = timeout
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} install and lifecycle edge cases")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
