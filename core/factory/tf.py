#!/usr/bin/env python3
"""
tf — the team factory command: install, update, packs, languages, health check (standard library only).

  cd ~/projects/my-app
  tf                          # no factory → install the latest release; installed → update (.tf/factory/update.py)
  tf install [options]        # install (options go to install.py: --packs, --language, --commit-language, --shared…)
  tf update [options]         # update (options go to update.py: --check, --yes, --source…)
  tf add <pack> [<pack>…]     # add packs or modes (e.g. tf add pack-ev, tf add mode-team)
  tf remove <pack> [<pack>…]  # remove packs (their files go to .tf/backup/)
  tf list                     # installed packs and modes, languages, what the source offers
  tf language <code>          # working language (conversation, documentation); pl installs pack-editorial-pl
  tf commit-language <code>   # language of commit messages, PR titles and descriptions
  tf doctor [--fix]           # check the install: core/pack versions, required packs, language pack, agents, renames
                              # and whether the quality gate is on (.claude/quality-gate.json)
  tf onboard [--yes] [--verify] [--dry-run] [--json]
                              # prepare the repository: detect test/lint/type/build commands, write verify.sh, the
                              # readiness report (.tf/reports/readiness.md) and the commands in the instructions file,
                              # turn the quality gate on; --verify runs the verification once (.tf/factory/onboard.py)
  tf new skill <name> "<description>" [--role <role>]
                              # your own skill from the template, with a scenario file (.tf/factory/build.py new-skill)
  tf skill check <name>       # quality gate of a skill: structure, scenarios, audit (.tf/factory/skill_gate.py)
  tf skill audit <directory>  # security audit of a skill, before you use a foreign one (.tf/factory/skill_audit.py)
  tf config show [<key>]      # merged configuration and where each value comes from (factory or project)
  tf task start <KEY> --title "<title>" | stage <KEY> <stage> | status <KEY>
  tf task freeze <KEY> <file> --by human:<id> | reopen <KEY> <file> --by human:<id> --reason "<why>"
  tf status [--json]          # all tasks: stage, slices with current evidence, files to refresh
  tf spec new <KEY> | check <KEY> [--json]   # task specification (spec.md): template, readiness check
  tf trace <KEY> [--base <branch>] [--md|--json]   # criterion → test → commit → evidence
  tf task flag <KEY> set <key> [--remove-by YYYY-MM-DD] | none --reason "<why>" | allow <env> --by human:<id>
  tf flag check <KEY> [--base <branch>] [--json]   # the task's feature flag is on outside the test environment only by human decision
                              # one place per task: docs/project/changes/<KEY>/task.json and the task index
                              # (.tf/factory/task_state.py)
  tf init                     # create .tf/ — the one place for factory results (reports, register, cache, logs…)
  tf analyze [--only a,b] [--since <commit>] [--top N] [--list]
                              # modular project review → .tf/reports/<module>.md with a checklist (.tf/factory/analyze.py)
  tf risk [--base <branch>] [--md|--json]
                              # change risk triage of this branch: what a human must review (advisory)
                              # (.tf/factory/risk_triage.py)
  tf metrics [--weeks N] [--revert-days N] [--no-gh]
                              # factory effectiveness: revert rate, cost per accepted change, cycle time,
                              # rework causes → .tf/reports/metrics.md (.tf/factory/metrics.py)
  tf --repo <url>             # another factory repository (also <url>#branch-or-tag)

Install the launcher once, from a factory clone or from a project that already has the factory:

  python3 core/factory/tf.py --install-launcher [--bin ~/.local/bin] [--repo <url>]    # in a factory clone
  python3 .tf/factory/tf.py --install-launcher [--bin ~/.local/bin] [--repo <url>]         # in a project

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

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne (build.py, testy, hooki) też piszą i czytają UTF-8

sys.dont_write_bytecode = True   # silnik w .tf/factory/ bez __pycache__ (jak node_modules — tylko kod)
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
        clone = Path(t) / ".tf" / "factory"
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
    return subprocess.run([sys.executable, str((Path(".tf") / "factory") / "update.py"), *args]).returncode


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
    """A module from the project's .tf/factory/ (packs.py, build.py, migrations.py)."""
    path = (Path(".tf") / "factory") / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"tf_project_{name}", path.resolve())
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.resolve().parent))
    spec.loader.exec_module(mod)
    return mod


def need_project() -> bool:
    if MANIFEST.exists() and not (Path(".tf") / "factory").is_dir() and Path("factory").is_dir():
        print("✗ This project has the old layout (factory/ in the project root). The engine now lives in .tf/factory/ "
              "and your configuration in .tf/config/ — reinstall: remove factory/, .claude/factory-manifest.json "
              "and the factory files, then run tf install.")
        return False
    if MANIFEST.exists():
        return True
    print("✗ No factory in this directory. Install it first: tf install")
    return False


def run_build() -> int:
    r = subprocess.run([sys.executable, str((Path(".tf") / "factory") / "build.py")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("✓ Rebuilt the agents and the catalog (.tf/factory/build.py)" if r.returncode == 0
          else "⚠ .tf/factory/build.py reported problems:\n" + r.stdout[-1500:] + r.stderr[-500:])
    return r.returncode


def set_language(kind: str, code: str, repo: str | None) -> int:
    """`kind`: language | commit_language. Language with a pack missing in the project goes through the installer."""
    if not need_project():
        return 2
    pm = project_module("packs")
    cfg = pm.load_config(Path.cwd())
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
    r = subprocess.run([sys.executable, str((Path(".tf") / "factory") / "packs.py")])
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


def engine(script: str, args: list[str]) -> int:
    """Run a script of the project's engine (.tf/factory/) with the given arguments."""
    if not need_project():
        return 2
    return subprocess.run([sys.executable, str((Path(".tf") / "factory") / script), *args]).returncode


def cmd_config_show(key: str | None) -> int:
    """Merged configuration and where each top-level key comes from: the factory default or the project override."""
    packs = project_module("packs")
    root = Path.cwd()
    own_path = root / ".tf" / "config" / "config.yaml"
    own = packs.load_yaml(own_path) if own_path.is_file() else {}
    cfg = packs.load_config(root)
    if key is not None:
        if key not in cfg:
            print(f"✗ Nie ma klucza „{key}”. Lista kluczy: tf config show")
            return 2
        print(json.dumps(cfg[key], ensure_ascii=False, indent=2))
        return 0
    print("# Konfiguracja fabryki. Swoje wartości wpisujesz w .tf/config/config.yaml — aktualizacja ich nie rusza.")
    for k in sorted(cfg):
        shown = json.dumps(cfg[k], ensure_ascii=False)
        shown = shown if len(shown) <= 70 else shown[:67] + "…"
        print(f"{k:<28} {'projekt' if k in own else 'fabryka':<8} {shown}")
    print("# Cała wartość jednego klucza: tf config show <klucz>")
    return 0


def cmd_doctor(fix: bool, repo: str | None) -> int:
    """Install health: build check (versions, required packs, references), renames from core migrations."""
    if not need_project():
        return 2
    mig = project_module("migrations")
    changes = mig.apply(Path.cwd(), dry=not fix)
    for c in changes:
        print(("✓ fixed: " if fix else "⚠ to fix (tf doctor --fix): ") + c)
    r = subprocess.run([sys.executable, str((Path(".tf") / "factory") / "build.py"), "check"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stdout
    print("\n".join(ln for ln in out.splitlines() if not ln.startswith("⚠ skill ")) or "?")
    hook_log = Path(".claude") / "hooks" / "hook_errors.py"
    if hook_log.is_file():   # błędy hooków z ostatnich 7 dni — informacja, nie zmienia wyniku doctora
        h = subprocess.run([sys.executable, str(hook_log), "--summary", "--days", "7"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env={**os.environ, "CLAUDE_PROJECT_DIR": str(Path.cwd())})
        if h.stdout.strip():
            print(h.stdout.strip())
    gate = Path(".claude") / "hooks" / "quality_gate.py"
    if gate.is_file():   # czy bramka jakości działa (komunikat w zwykłym języku) — informacja, nie zmienia wyniku
        g = subprocess.run([sys.executable, str(gate), "--status"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env={**os.environ, "CLAUDE_PROJECT_DIR": str(Path.cwd())})
        if g.stdout.strip():
            print(g.stdout.strip())
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
    if cmd in ("init", "analyze"):
        if not need_project():
            return 2
        sub = ["init"] if cmd == "init" else (["list"] if "--list" in rest else ["run", *rest])
        return subprocess.run([sys.executable, str((Path(".tf") / "factory") / "analyze.py"), *sub]).returncode
    if cmd == "risk":
        if not need_project():
            return 2
        return subprocess.run([sys.executable, str((Path(".tf") / "factory") / "risk_triage.py"), *rest]).returncode
    if cmd == "new":
        if len(rest) < 3 or rest[0] != "skill":
            print('✗ Usage: tf new skill <name> "<description>" [--role <role>] [--name-only]\n'
                  '  e.g. tf new skill app-faktury "Użyj przy fakturach korygujących — numeracja, stawki. Nie do płatności."')
            return 2
        return engine("build.py", ["new-skill", *rest[1:]])
    if cmd == "skill":
        scripts = {"check": "skill_gate.py", "audit": "skill_audit.py"}
        if len(rest) < 2 or rest[0] not in scripts:
            print("✗ Usage: tf skill check <name> [--model haiku,sonnet --yes]   # quality gate (model runs cost money)\n"
                  "         tf skill audit <skill directory>                     # security audit, before using a foreign skill")
            return 2
        return engine(scripts[rest[0]], rest[1:])
    if cmd == "config":
        if not rest or rest[0] != "show" or len(rest) > 2:
            print("✗ Usage: tf config show [<key>]")
            return 2
        return cmd_config_show(rest[1] if len(rest) == 2 else None) if need_project() else 2
    if cmd == "task":
        return engine("task_state.py", rest)
    if cmd == "status":
        return engine("task_state.py", ["list", *rest])
    if cmd == "spec":
        return engine("spec_check.py", rest)
    if cmd == "trace":
        return engine("trace_check.py", rest)
    if cmd == "flag":
        if not rest or rest[0] != "check":
            print("✗ Usage: tf flag check <KEY> [--base <branch>] [--json]   (set the flag with: tf task flag <KEY> set <key>)")
            return 2
        return engine("flag_check.py", rest)
    if cmd == "onboard":
        if not need_project():
            return 2
        return subprocess.run([sys.executable, str((Path(".tf") / "factory") / "onboard.py"), *rest]).returncode
    if cmd == "metrics":
        if not need_project():
            return 2
        return subprocess.run([sys.executable, str((Path(".tf") / "factory") / "metrics.py"), *rest]).returncode
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
