#!/usr/bin/env python3
"""
tf — the team factory command: install, update, packs, languages, health check (standard library only).

  cd ~/projects/my-app
  tf                          # no factory → install the latest release; installed → update (factory/update.py)
  tf install [options]        # install (options go to install.py: --packs, --language, --commit-language, --shared…)
  tf update [options]         # update (options go to update.py: --check, --yes, --source…)
  tf add <pack> [<pack>…]     # add packs or modes (e.g. tf add pack-ev, tf add mode-talos)
  tf remove <pack> [<pack>…]  # remove packs (their files go to .claude/factory-backup/)
  tf list                     # installed packs and modes, languages, what the source offers
  tf language <code>          # working language (conversation, documentation); pl installs pack-editorial-pl
  tf commit-language <code>   # language of commit messages, PR titles and descriptions
  tf doctor [--fix]           # check the install: core/pack versions, required packs, language pack, agents, renames
  tf --repo <url>             # another factory repository (also <url>#branch-or-tag)

Install the launcher once, from a factory clone or from a project that already has the factory:

  python3 core/factory/tf.py --install-launcher [--bin ~/.local/bin] [--repo <url>]    # in a factory clone
  python3 factory/tf.py --install-launcher [--bin ~/.local/bin] [--repo <url>]         # in a project

It copies this script to `--bin` (default ~/.local/bin; on Windows also tf.cmd) and writes the repository URL into
it: from `--repo`, the `TF_REPO` variable, the git source in the project manifest or the `origin` of the factory clone.

Repository URL on install: `--repo`, `TF_REPO`, the URL in the launcher. Without `#ref` the latest release is used
(highest vX.Y.Z tag); without tags — the default branch. On update the source saved in the manifest wins unless it
is not a git repository — then tf passes its own repository to update.py. Install and update run code from the
repository — only use one you trust.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Factory repository URL — written by --install-launcher (without credentials).
REPO = ""
MANIFEST = Path(".claude") / "factory-manifest.json"


def is_git(src: str) -> bool:
    return src.startswith(("https://", "http://", "git@", "ssh://")) or src.split("#")[0].endswith(".git")


def public(url: str) -> str:
    """URL without credentials (https://user:token@host/… → https://host/…), so they never reach files or logs."""
    return re.sub(r"^([a-z+]+://)[^/@]*@", r"\1", url)


def latest_tag(url: str) -> str | None:
    """Highest release tag vX.Y.Z (no pre-releases); None when there are no tags or on error."""
    try:
        r = subprocess.run(["git", "ls-remote", "--tags", "--refs", url, "v*"], capture_output=True, text=True)
    except OSError:
        return None
    tags = re.findall(r"refs/tags/(v(\d+)\.(\d+)\.(\d+))$", r.stdout, re.M) if r.returncode == 0 else []
    return max(tags, key=lambda t: tuple(int(x) for x in t[1:]))[0] if tags else None


def install(repo: str, args: list[str]) -> int:
    url, _, ref = repo.partition("#")
    ref = ref or latest_tag(url) or ""
    print(f"ℹ Installing the factory from {public(url)}" + (f" ({ref})" if ref else " (default branch — no release tags)"))
    args = ["--dry-run" if a == "--check" else a for a in args]
    with tempfile.TemporaryDirectory(prefix="tf-") as t:
        clone = Path(t) / "factory"
        r = subprocess.run(["git", "clone", "--depth", "1", "--quiet", *(["--branch", ref] if ref else []), url,
                            str(clone)], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"✗ Could not fetch {public(repo)}:\n{r.stderr.strip()}")
            return 1
        installer = clone / "core" / "factory" / "install.py"
        if not installer.is_file():
            print(f"✗ No factory in {public(repo)} (core/factory/install.py is missing).")
            return 1
        return subprocess.run([sys.executable, str(installer), "--source", public(repo), *args]).returncode


def saved_source() -> str:
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8")).get("source") or ""
    except (OSError, ValueError):
        return ""


def update(repo: str | None, args: list[str]) -> int:
    args = ["--check" if a == "--dry-run" else a for a in args]
    if repo and not is_git(saved_source()) and "--source" not in args:
        args = ["--source", public(repo), *args]
    return subprocess.run([sys.executable, str(Path("factory") / "update.py"), *args]).returncode


def origin_of(path: Path) -> str:
    r = subprocess.run(["git", "-C", str(path), "remote", "get-url", "origin"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def install_launcher(repo: str | None, bin_dir: Path) -> int:
    if not repo:
        saved = saved_source()
        here = Path(__file__).resolve().parent
        clone = here.parent.parent if (here.parent.name == "core") else here.parent
        repo = saved if is_git(saved) else origin_of(clone)
    if not repo:
        print("✗ The factory repository URL is unknown. Pass it: --repo https://github.com/<you>/tf.git")
        return 2
    url = public(repo.partition("#")[0])               # the launcher always takes the latest release
    text = Path(__file__).read_text(encoding="utf-8")
    text = re.sub(r"^REPO = .*$", lambda m: f"REPO = {url!r}", text, count=1, flags=re.M)
    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / "tf"
    target.write_text(text, encoding="utf-8")
    target.chmod(0o755)
    if os.name == "nt":
        (bin_dir / "tf.cmd").write_text(f'@"{sys.executable}" "%~dp0tf" %*\r\n', encoding="utf-8")
    print(f"✓ Installed {target} (repository: {url})")
    on_path = [Path(p).expanduser().resolve() for p in os.environ.get("PATH", "").split(os.pathsep) if p]
    if bin_dir.resolve() not in on_path:
        print(f"⚠ {bin_dir} is not on PATH — add it in your shell profile, e.g. export PATH=\"{bin_dir}:$PATH\"")
    return 0


# ───────────── commands inside an installed project ─────────────

def project_module(name: str):
    """A module from the project's factory/ (packs.py, build.py, migrations.py)."""
    path = Path("factory") / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"tf_project_{name}", path.resolve())
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.resolve().parent))
    spec.loader.exec_module(mod)
    return mod


def need_project() -> bool:
    if MANIFEST.exists():
        return True
    print("✗ No factory in this directory. Install it first: tf install")
    return False


def run_build() -> int:
    r = subprocess.run([sys.executable, str(Path("factory") / "build.py")], capture_output=True, text=True)
    print("✓ Rebuilt the agents and the catalog (factory/build.py)" if r.returncode == 0
          else "⚠ factory/build.py reported problems:\n" + r.stdout[-1500:] + r.stderr[-500:])
    return r.returncode


def set_language(kind: str, code: str, repo: str | None) -> int:
    """`kind`: language | commit_language. Language with a pack missing in the project goes through the installer."""
    if not need_project():
        return 2
    pm = project_module("packs")
    cfg = pm.load_yaml(Path("factory") / "config.yaml")
    langs = cfg.get("languages") or {}
    if code not in langs:
        print(f"✗ Unknown language '{code}'. Available: {', '.join(langs)}")
        return 2
    root = Path.cwd()
    current = pm.load_settings(root, cfg)
    flag = "--" + kind.replace("_", "-")
    installed = pm.installed_packs(root)
    if kind == "language":
        need = (langs[code] or {}).get("pack")
        if need and need not in installed:
            print(f"ℹ Language {code} needs {need} — installing it.")
            return update(repo, [flag, code])
        old_pack = (langs.get(current["language"]) or {}).get("pack")
        if old_pack and old_pack != need and old_pack in installed and sys.stdin.isatty():
            if input(f"Remove {old_pack} (tools for {current['language']})? [y/N] ").strip().lower() in ("y", "yes"):
                return update(repo, [flag, code, "--remove", old_pack])
    pm.save_settings(root, **{kind: code})
    settings = pm.load_settings(root, cfg)
    for name in ("CLAUDE.local.md", "CLAUDE.md"):
        if pm.write_language_lines(root / name, cfg, settings):
            print(f"✓ {name}: language section updated")
    print(f"✓ {kind.replace('_', ' ')}: {current[kind]} → {code}")
    return run_build()


def cmd_list() -> int:
    if not need_project():
        return 2
    r = subprocess.run([sys.executable, str(Path("factory") / "packs.py")])
    src = saved_source()
    found = sorted(p for sub in ("packs", "modes") for p in (Path(src) / sub).glob("*/pack.yaml")) \
        if src and not is_git(src) else []
    if found:
        pm = project_module("packs")
        print("Available in the source:")
        for p in found:
            d = pm.load_yaml(p)
            kind = " (mode)" if d.get("kind") == "mode" else ""
            print(f"  {d.get('id', p.parent.name)} {d.get('version', '?')}{kind} — "
                  f"{d.get('description', d.get('title', ''))}")
    return r.returncode


def cmd_doctor(fix: bool, repo: str | None) -> int:
    """Install health: build check (versions, required packs, references), renames from core migrations."""
    if not need_project():
        return 2
    mig = project_module("migrations")
    changes = mig.apply(Path.cwd(), dry=not fix)
    for c in changes:
        print(("✓ fixed: " if fix else "⚠ to fix (tf doctor --fix): ") + c)
    r = subprocess.run([sys.executable, str(Path("factory") / "build.py"), "check"], capture_output=True, text=True)
    out = r.stdout
    print("\n".join(ln for ln in out.splitlines() if not ln.startswith("⚠ skill ")) or "?")
    missing = sorted(set(re.findall(r"tf add (pack-[a-z0-9-]+)", out)))
    stale = "nieaktualne" in out or "nieaktualny" in out
    if fix and stale:
        run_build()
    if fix and missing:
        return update(repo, ["--add", ",".join(missing)])
    if missing:
        print(f"→ tf doctor --fix adds: {', '.join(missing)}")
    return 0 if r.returncode == 0 or (fix and stale and not missing) else r.returncode


def main(argv: list[str]) -> int:
    args, repo, bin_dir, launcher = [], None, Path.home() / ".local" / "bin", False
    it = iter(argv[1:])
    for a in it:
        if a in ("-h", "--help"):
            print(__doc__)
            return 0
        if a == "--repo":
            repo = next(it, "")
        elif a == "--bin":
            bin_dir = Path(next(it, "")).expanduser()
        elif a == "--install-launcher":
            launcher = True
        else:
            args.append(a)
    repo = repo or os.environ.get("TF_REPO") or None
    if launcher:
        return install_launcher(repo, bin_dir)
    cmd = args[0] if args and not args[0].startswith("-") else None
    rest = args[1:] if cmd else args
    if cmd in ("add", "remove"):
        if not rest:
            print(f"✗ Usage: tf {cmd} <pack> [<pack>…]")
            return 2
        return update(repo or REPO or None, [f"--{cmd}", ",".join(rest)]) if need_project() else 2
    if cmd in ("language", "commit-language"):
        if len(rest) != 1:
            print(f"✗ Usage: tf {cmd} <code>")
            return 2
        return set_language(cmd.replace("-", "_"), rest[0], repo or REPO or None)
    if cmd == "list":
        return cmd_list()
    if cmd == "doctor":
        return cmd_doctor("--fix" in rest, repo or REPO or None)
    if cmd not in (None, "install", "update"):
        print(f"✗ Unknown command '{cmd}'.\n{__doc__}")
        return 2
    if MANIFEST.exists() and cmd != "install":
        return update(repo or REPO or None, rest)
    repo = repo or REPO
    if not repo:
        print("✗ The factory repository URL is unknown. Pass --repo <url>, set TF_REPO or install the launcher:\n"
              "  python3 core/factory/tf.py --install-launcher --repo https://github.com/<you>/tf.git")
        return 2
    return install(repo, rest)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
