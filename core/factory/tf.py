#!/usr/bin/env python3
"""
tf — the team factory command: install, update, packs, health check (standard library only).

  cd ~/projects/my-app
  tf                          # no factory → install the latest release; installed → update (.tf/factory/update.py)
  tf install [options]        # install (options go to install.py: --packs, --shared…)
  tf update [options]         # update (options go to update.py: --check, --yes, --source…)
  tf add <pack> [<pack>…]     # add packs or modes (e.g. tf add pack-ux, tf add mode-team)
  tf remove <pack> [<pack>…]  # remove packs (their files go to .tf/backup/)
  tf list                     # installed packs and modes, what the source offers
  tf doctor [--fix]           # check the install: core/pack versions, required packs, agents, renames
                              # and whether the quality gate is on (.claude/quality-gate.json)
  tf onboard [--yes] [--verify] [--dry-run] [--json]
                              # prepare the repository: detect test/lint/type/build commands, write verify.sh, the
                              # readiness report (.tf/reports/readiness.md) and the commands in the instructions file,
                              # turn the quality gate on; --verify runs the verification once (.tf/factory/onboard.py)
  tf cooldown [--fix]         # the package manager's 7-day version cooldown the /tf-task loop requires; --fix writes it
                              # (.npmrc, pnpm-workspace.yaml, .yarnrc.yml, [tool.uv] in pyproject.toml)
  tf addon list | add <name|path|git URL> | remove <name> | sync | check [--base <ref>]
                              # add-ons: independent packages in .tf/addons/<name>/ the factory uses through a
                              # contract (addon.yaml); e.g. tf addon add dna (.tf/factory/addons.py)
  tf learn [<name>]           # run the add-ons' `learn` (e.g. project knowledge) and wire the result in
  tf new skill <name> "<description>" [--role <role>]
                              # your own skill from the template, with a scenario file (.tf/factory/build.py new-skill)
  tf skill check <name>       # quality gate of a skill: structure, scenarios, audit (.tf/factory/skill_gate.py)
  tf skill audit <directory>  # security audit of a skill, before you use a foreign one (.tf/factory/skill_audit.py)
  tf uninstall [--dry-run] [--yes] [--force]   # remove the factory from this project (keeps your files; --force removes
                              # them too); backup in ~/.tf/backups/
  tf style [<name>] [--here]  # your work style: autonomous | step-by-step | conversation; no name — show the current one;
                              # saved in ~/.tf/preferences.yaml (all your projects) or, with --here, .tf/config/me.yaml
  tf isolation [<level>]      # isolation of agent sessions: basic | sandbox | container; no level — show the chosen
                              # one and what protects this session; a level is set only from a human's terminal
  tf config show [<key>]      # merged configuration and where each value comes from (factory or project);
                              # `tf config show steps`: who runs each /tf-task loop step, with model and effort
  tf task start <KEY> --title "<title>" | stage <KEY> <stage> | status <KEY>
  tf task start <CHG>-<TSK> --title "<title>" --change <CHG> --cut <TSK>   # task of a pdi change cut
  tf task freeze <KEY> <file> --by human:<id> | reopen <KEY> <file> --by human:<id> --reason "<why>"
  tf status [--json] [--open] [--all] # open tasks (--all: closed ones too): stage, slices with current evidence, files to refresh, what waits for you;
                              # --open opens the live view in the browser: the local live server (updates on every
                              # state change), or the file .tf/runs/dashboard.html when live mode is off or cannot start
  tf spec new <KEY> | check <KEY> [--json]   # task specification (spec.md): template, readiness check
  tf trace <KEY> [--base <branch>] [--md|--json]   # criterion → test → commit → evidence
  tf task flag <KEY> set <key> [--remove-by YYYY-MM-DD] | none --reason "<why>" | allow <env> --by human:<id>
  tf flag check <KEY> [--base <branch>] [--json]   # the task's feature flag is on outside the test environment only by human decision
  tf task weight <KEY> [--apply | --set light|normal|full [--by human:<id> --reason "<why>"]]   # task weight: proposal with a reason; lowering is a human decision
  tf task deployed <KEY> [--version X] | --rolled-back --by human:<id>   # after deployment: run the smoke test from the operations card, record the result; a red result asks whether to roll back
  tf task finding <KEY> add "<finding>" | control F1 "<control>"   # important review findings and the control that will catch each next time
  tf task close <KEY> [--lesson "<lesson>" --by human:<id>]   # close a merged task; refuses with an open rollback decision or a finding without a control
  tf task mode <KEY> [plan|normal|auto]   # who approves: plan stops after the plan, normal waits for the human's approval of the plan, auto does not
                              # one place per task: docs/project/changes/<KEY>/task.json and the task index
                              # (.tf/factory/task_state.py)
  tf code [claude arguments]  # factory session: claude with the factory plugin (.tf/plugin), its settings and the isolation
                              # level (the sandbox for `sandbox`); a plain `claude` and the Desktop app load nothing from
                              # the factory (classic layout, loaded by every session: update.py --layout default)
  tf cloud-setup [--apply]    # factory mode in a cloud environment: prints the environment's setup script; --apply
                              # enables the factory plugin and its session settings in ~/.claude/settings.json
  tf work --once --budget <USD> [--key <KEY>] [--dry-run]
                              # unattended: one task in Auto mode (light or normal weight) through the /tf-task loop in its
                              # own worktree (.tf/worktrees/<KEY>) with a spending limit; never merges (.tf/factory/work.py)
  tf init                     # create .tf/ — the one place for factory results (reports, register, cache, logs…)
  tf analyze [--only a,b] [--since <commit>] [--top N] [--list]
                              # modular project review → .tf/reports/<module>.md with a checklist (.tf/factory/analyze.py)
  tf risk [--base <branch>] [--md|--json]
                              # change risk triage of this branch: what a human must review (advisory)
                              # (.tf/factory/risk_triage.py)
  tf diff [--base <branch>] [--md|--json]
                              # system diff of this branch: what it touches beyond code lines (.tf/factory/system_diff.py)
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

for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # engine in .tf/factory/ without __pycache__ (like node_modules — code only)
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


PROJECT_TF = Path(".tf") / "factory" / "tf.py"


def is_launcher() -> bool:
    """This file is the launcher (a copy in ~/.local/bin), not the engine's tf.py in .tf/factory/ nor in the factory clone."""
    return Path(__file__).resolve().parent.name != "factory"


def refresh_launcher() -> None:
    """After a project update the launcher adopts the project engine's tf.py (keeping the repo address) so that it knows
    the new commands. It does nothing when this is not the launcher or the project has no .tf/factory/tf.py."""
    if not is_launcher() or not PROJECT_TF.is_file():
        return
    me = Path(__file__).resolve()
    text = PROJECT_TF.read_text(encoding="utf-8")
    text = re.sub(r"^REPO = .*$", lambda m: f"REPO = {REPO!r}", text, count=1, flags=re.M)
    try:
        if text != me.read_text(encoding="utf-8"):
            me.write_text(text, encoding="utf-8")
            print(f"✓ Launcher {me} updated to the project's factory version")
    except OSError as e:
        print(f"⚠ Could not update the launcher {me}: {e} — run: python3 .tf/factory/tf.py --install-launcher")


def engine(script: str, args: list[str]) -> int:
    """Run a script of the project's engine (.tf/factory/) with the given arguments."""
    if not need_project():
        return 2
    return subprocess.run([sys.executable, str((Path(".tf") / "factory") / script), *args]).returncode


def cmd_config_show(key: str | None) -> int:
    """Merged configuration and where each top-level key comes from: factory default, organization pack or project."""
    packs = project_module("packs")
    root = Path.cwd()
    own_path = root / ".tf" / "config" / "config.yaml"
    own = packs.load_yaml(own_path) if own_path.is_file() else {}
    layers = packs.config_layers(root) if hasattr(packs, "config_layers") else []
    org = next((d for label, d in layers if "org_defaults" in label), {})   # company overlay
    team = next((d for label, d in layers if "team_defaults" in label), {})   # team overlay
    person = next((d for label, d in layers if label.endswith("(person)")), {})   # preferencje osoby (tf style)
    cfg = packs.load_config(root)
    if key == "steps" and cfg.get("steps"):     # steps of the /tf-task loop with model and effort after the cost profile is applied
        full = project_module("build").load_config()
        print(f"# /tf-task loop steps (cost profile: {full.get('_profile')}). To change: steps in .tf/config/config.yaml, "
              "then python3 .tf/factory/build.py")
        print(f"{'step':<16} {'what':<38} {'who':<18} {'tier':<5} {'model':<8} effort")
        for sid, step in full["steps"].items():
            tier = full["tiers"].get(step.get("tier"), {})
            print(f"{sid:<16} {step.get('label', ''):<38} {step.get('who', ''):<18} {step.get('tier', ''):<5} "
                  f"{tier.get('model', '?'):<8} {tier.get('effort', '?')}")
        return 0
    if key is not None:
        if key not in cfg:
            print(f"✗ No key \"{key}\". List of keys: tf config show")
            return 2
        print(json.dumps(cfg[key], ensure_ascii=False, indent=2))
        return 0
    print("# Factory configuration. You put your own values in .tf/config/config.yaml. An update does not touch them.")
    for k in sorted(cfg):
        shown = json.dumps(cfg[k], ensure_ascii=False)
        shown = shown if len(shown) <= 70 else shown[:67] + "…"
        src = ("person" if k in person else "project" if k in own else "team" if k in team
               else "organisation" if k in org else "factory")
        print(f"{k:<28} {src:<12} {shown}")
    for w in (packs.work_style(root).get("warnings") or []) if hasattr(packs, "work_style") else []:
        print(f"⚠ personal preferences: {w}")
    print("# The full value of one key: tf config show <key>")
    return 0


def cmd_style(rest: list[str]) -> int:
    """A person's work style: show or save in ~/.tf/preferences.yaml (--here: .tf/config/me.yaml, outside the repository)."""
    here = "--here" in rest
    names = [a for a in rest if a != "--here"]
    packs = project_module("packs")
    root = Path.cwd()
    if not hasattr(packs, "work_style"):
        print("✗ The engine in .tf/factory/ does not know work styles. Update the factory: tf update")
        return 2
    styles = packs.load_config(root).get("styles") or {}
    if not names:
        ws = packs.work_style(root)
        print(f"Work style: {ws.get('style') or 'none (project settings)'}")
        for m in packs.apply_style_permissions(root) if hasattr(packs, "apply_style_permissions") else []:
            print(f"• {m}")
        print(f"  default task mode: {ws['default_mode']} (allowed: {', '.join(ws['allowed_modes'])})")
        print(f"  a question pauses only its own slice: {'yes' if ws['blocked_slices'] else 'no'}")
        print(f"  human approval after each slice: {'yes' if ws['confirm_each_slice'] else 'no'}")
        for w in ws.get("warnings") or []:
            print(f"⚠ {w}")
        print(f"To change: tf style <{'|'.join(styles)}> [--here]")
        return 0
    if len(names) != 1 or names[0] not in styles:
        print(f"✗ Unknown style \"{' '.join(names)}\". Choose from: {', '.join(styles)}")
        return 2
    path = root / ".tf" / "config" / "me.yaml" if here else packs.preferences_path()
    data = packs.load_yaml(path) if path.is_file() else {}
    data = {**(data if isinstance(data, dict) else {}), "style": names[0]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(packs.yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    if here:
        ensure_excluded(root, ".tf/config/me.yaml")
    ws = packs.work_style(root)
    perm_msgs = packs.apply_style_permissions(root) if hasattr(packs, "apply_style_permissions") else []
    print(f"✓ style {names[0]} saved in {path if not here else '.tf/config/me.yaml'}. Default task mode: "
          f"{ws['default_mode']}, approval after each slice: {'yes' if ws['confirm_each_slice'] else 'no'}")
    for m in perm_msgs:
        print(f"• {m}")
    for w in ws.get("warnings") or []:
        print(f"⚠ {w}")
    return 0


def ensure_excluded(root: Path, rel: str) -> None:
    """A person's file does not go to the repository: an entry in .git/info/exclude, if git does not ignore it yet."""
    try:
        if subprocess.run(["git", "-C", str(root), "check-ignore", "-q", rel], capture_output=True).returncode == 0:
            return
        top = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-path", "info/exclude"], capture_output=True,
                             text=True)
        if top.returncode != 0:
            return
        exclude = (root / top.stdout.strip()).resolve()
        exclude.parent.mkdir(parents=True, exist_ok=True)
        old = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
        exclude.write_text(old + ("" if old.endswith("\n") or not old else "\n") + rel + "\n", encoding="utf-8")
    except OSError:
        pass


def instructions_summary(lint: Path) -> str:
    """One line about the project's instruction files (CLAUDE.md, AGENTS.md…): checks with remarks or “no remarks”."""
    try:
        r = subprocess.run([sys.executable, str(lint), "--root", ".", "--json"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        files = json.loads(r.stdout).get("files") or []
    except (OSError, ValueError, subprocess.SubprocessError, AttributeError):
        return "⚠ instructions: could not compute the instruction file report"
    if not files:
        return "• instructions: the project has no CLAUDE.md or AGENTS.md file"
    notes = []
    for f in files:
        bad = [f"{c['id']} ({len(c.get('findings') or []) or c.get('verdict')})" for c in f.get("checks") or []
               if c.get("verdict") in ("WARN", "ERROR")]
        if bad:
            try:
                name = Path(f["path"]).resolve().relative_to(Path.cwd().resolve()).as_posix()
            except ValueError:
                name = f["path"]
            notes.append(f"{name}: {', '.join(bad)}")
    if not notes:
        return f"✓ instructions: {len(files)} file(s), no findings"
    return ("⚠ instructions: " + "; ".join(notes) + f"\n  details: python3 {lint.as_posix()} --root .")


PLUGIN_DIR = Path(".tf") / "plugin"
PLUGIN_WARNING = ("⚠ Plugin layout: only `tf code` loads the factory; a plain `claude` and the Claude Desktop app see no "
                  "/tf. Back to the classic layout: python3 .tf/factory/update.py --layout default")


def plugin_warning_block() -> str:
    rule = "⚠ " + "─" * 70
    return "\n".join([rule, PLUGIN_WARNING, "  Start the factory with `tf code` (e.g. `tf code --continue`).", rule])


def factory_layout() -> str:
    """`plugin` — the factory lives in .tf/plugin/ and only a factory session (tf code) loads it; else `default`."""
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8")).get("layout") or "default"
    except (OSError, ValueError, AttributeError):
        return "default"


def claude_command() -> list[str]:
    import shlex
    return shlex.split(os.environ.get("TF_CLAUDE") or "claude")


def session_settings(plugin_settings: Path) -> Path:
    """The settings of a factory session with the isolation level (`.tf/cache/session-settings.json`); the plugin's
    own file when the engine has no isolation.py yet."""
    if not (Path(".tf") / "factory" / "isolation.py").is_file():
        return plugin_settings
    return project_module("isolation").launch_settings(Path.cwd()).resolve()


def isolation_level() -> str:
    if not (Path(".tf") / "factory" / "isolation.py").is_file():
        return "basic"
    return project_module("isolation").configured(Path.cwd())[0]


def cmd_code(rest: list[str]) -> int:
    """Factory session: `claude --plugin-dir .tf/plugin --settings .tf/cache/session-settings.json <rest>` — the plugin's
    session settings with the isolation level (the sandbox for `sandbox` and `container`); TF_ISOLATION names the level."""
    if not need_project():
        return 2
    if factory_layout() != "plugin":
        print("ℹ Classic layout (the factory in .claude/, loaded by every session, the Desktop app too) — starting "
              "claude as usual; the isolation level's sandbox is in .claude/settings.local.json.", file=sys.stderr)
        cmd = [*claude_command(), *rest]
    else:
        plugin, settings = PLUGIN_DIR.resolve(), (PLUGIN_DIR / "session-settings.json").resolve()
        missing = [str(x) for x in (plugin / ".claude-plugin" / "plugin.json", settings) if not x.is_file()]
        if missing:
            print(f"✗ The factory plugin is incomplete (missing: {', '.join(missing)}) — run `tf doctor --fix` "
                  "(or `tf` to update), then `tf code` again.")
            return 2
        cmd = [*claude_command(), "--plugin-dir", str(plugin), "--settings", str(session_settings(settings)), *rest]
    try:
        return subprocess.run(cmd, env={**os.environ, "TF_ISOLATION": isolation_level()}).returncode
    except FileNotFoundError:
        print("✗ The `claude` command (Claude Code) is not in PATH.")
        return 127
    except KeyboardInterrupt:
        return 130


def merge_user_settings(cur: dict, session: dict, market: Path) -> dict:
    """User settings with the factory marketplace and plugin enabled and the factory session settings; your values win
    (env, status line), permission lists are joined without duplicates."""
    out = json.loads(json.dumps(cur))
    out.setdefault("extraKnownMarketplaces", {})["tf-project"] = {"source": {"source": "directory", "path": str(market)}}
    out.setdefault("enabledPlugins", {})["tf@tf-project"] = True
    for k, v in (session.get("env") or {}).items():
        out.setdefault("env", {}).setdefault(k, v)
    if session.get("statusLine") and "statusLine" not in out:
        out["statusLine"] = session["statusLine"]
    for kind in ("allow", "ask", "deny"):
        add = (session.get("permissions") or {}).get(kind) or []
        if add:
            have = out.setdefault("permissions", {}).setdefault(kind, [])
            have.extend(x for x in add if x not in have)
    for k, v in session.items():
        if k not in ("env", "statusLine", "permissions", "hooks", "$schema"):
            out.setdefault(k, v)
    return out


def cmd_cloud_setup(apply: bool) -> int:
    """Factory mode in a cloud environment: the session there starts without tf code, so the factory plugin is enabled in
    the container's user settings (a directory marketplace in .tf/ and enabledPlugins), with the factory session settings."""
    if not need_project():
        return 2
    if factory_layout() != "plugin":
        print("✗ The factory mode needs the plugin layout (install.py --layout plugin).")
        return 2
    market, session_f = Path(".tf").resolve(), PLUGIN_DIR / "session-settings.json"
    if not (market / ".claude-plugin" / "marketplace.json").is_file() or not session_f.is_file():
        print("✗ The factory plugin is incomplete — run `tf doctor --fix` (or `tf` to update) first.")
        return 2
    if not apply:
        print("Setup script of the cloud environment (environment settings → setup script). It runs before Claude "
              "starts and turns the environment into a factory environment; an environment without it stays a plain one.\n"
              "The factory files must be in the repository (team install, `--shared`), otherwise the cloud clone has none.\n")
        print(f"if [ -d {Path.cwd().name} ]; then (cd {Path.cwd().name} && python3 .tf/factory/tf.py cloud-setup --apply); fi")
        return 0
    try:
        session = json.loads(session_f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"✗ {session_f} is not valid JSON — run `tf doctor --fix`.")
        return 2
    user = Path.home() / ".claude" / "settings.json"
    try:
        cur = json.loads(user.read_text(encoding="utf-8")) if user.is_file() else {}
    except ValueError:
        print(f"✗ {user} is not valid JSON — nothing changed.")
        return 2
    new = merge_user_settings(cur, session, market)
    if new != cur:
        user.parent.mkdir(parents=True, exist_ok=True)
        user.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✓ Factory plugin enabled in {user} (marketplace {market}); a Claude session in this environment loads the factory.")
    return 0


def cmd_doctor(fix: bool, repo: str | None) -> int:
    """Install health: build check (versions, required packs, references), renames from core migrations."""
    if not need_project():
        return 2
    if factory_layout() == "plugin":
        print(plugin_warning_block())
    else:
        print("✓ layout: classic (.claude/) — every Claude Code session loads the factory (also the Desktop app)")
    mig = project_module("migrations")
    changes = mig.apply(Path.cwd(), dry=not fix)
    for c in changes:
        print(("✓ fixed: " if fix else "⚠ to fix (tf doctor --fix): ") + c)
    r = subprocess.run([sys.executable, str((Path(".tf") / "factory") / "build.py"), "check"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stdout
    print("\n".join(ln for ln in out.splitlines() if not ln.startswith("⚠ skill ")) or "?")
    hook_log = Path(".claude") / "hooks" / "hook_errors.py"
    if hook_log.is_file():   # hook errors from the last 7 days — information, does not change the doctor result
        h = subprocess.run([sys.executable, str(hook_log), "--summary", "--days", "7"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env={**os.environ, "CLAUDE_PROJECT_DIR": str(Path.cwd())})
        if h.stdout.strip():
            print(h.stdout.strip())
    models = Path(".tf") / "factory" / "model_check.py"
    if models.is_file():   # model names in the configuration (step H20) — information, does not change the doctor result
        m = subprocess.run([sys.executable, str(models)], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env={**os.environ, "CLAUDE_PROJECT_DIR": str(Path.cwd())})
        if m.stdout.strip():
            print(m.stdout.strip())
    iso = Path(".tf") / "factory" / "isolation.py"
    if iso.is_file():   # isolation level and what protects the session (plan of isolation levels, I1) — information
        i = subprocess.run([sys.executable, str(iso), "show"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env={**os.environ, "CLAUDE_PROJECT_DIR": str(Path.cwd())})
        if i.stdout.strip():
            print(i.stdout.strip())
    health = Path(".tf") / "factory" / "metrics.py"
    if health.is_file():   # degradation after a factory update (step H29, D13) — a warning only, exit code unchanged
        u = subprocess.run([sys.executable, str(health), "--after-update"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env={**os.environ, "CLAUDE_PROJECT_DIR": str(Path.cwd())})
        if u.stdout.startswith("⚠"):
            print(u.stdout.strip())
    lint = Path(".claude") / "skills" / "core-agent-instructions" / "scripts" / "instructions_lint.py"
    if lint.is_file():   # the project's instruction files card (step H21) — information, does not change the doctor result
        print(instructions_summary(lint))
    gate = Path(".claude") / "hooks" / "quality_gate.py"
    if gate.is_file():   # whether the quality gate works (a plain-language message) — information, does not change the result
        g = subprocess.run([sys.executable, str(gate), "--status"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env={**os.environ, "CLAUDE_PROJECT_DIR": str(Path.cwd())})
        if g.stdout.strip():
            print(g.stdout.strip())
    addons_py = Path(".tf") / "factory" / "addons.py"
    if addons_py.is_file() and (Path(".tf") / "addons").is_dir():   # dodatki — informacja, nie zmienia wyniku
        a = subprocess.run([sys.executable, str(addons_py), "list"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        if a.stdout.strip():
            print(a.stdout.strip())
    missing = sorted(set(re.findall(r"tf add (pack-[a-z0-9-]+)", out)))
    stale = "stale" in out or "stale" in out
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
    if cmd in ("language", "commit-language"):   # 12.0.0: language without settings, as in Claude
        print(f"ℹ tf {cmd} is no longer needed: there is no language setting. The agents answer in the language you "
              "write in and write your documents in it; commit messages follow the repository's history (git log; a new "
              "repository: English, or commit_language.new_repo in the config).")
        return 2
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
    if cmd == "diff":
        if not need_project():
            return 2
        return subprocess.run([sys.executable, str((Path(".tf") / "factory") / "system_diff.py"), *rest]).returncode
    if cmd == "new":
        if len(rest) < 3 or rest[0] != "skill":
            print('✗ Usage: tf new skill <name> "<description>" [--role <role>] [--name-only]\n'
                  '  e.g. tf new skill app-invoices "Use for corrective invoices — numbering, tax rates. Not for payments."')
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
    if cmd == "uninstall":
        return engine("uninstall.py", rest) if need_project() else 2
    if cmd == "style":
        return cmd_style(rest) if need_project() else 2
    if cmd == "isolation":
        return engine("isolation.py", ["set", *rest] if rest and not rest[0].startswith("-") else ["show", *rest]) \
            if need_project() else 2
    if cmd == "task":
        return engine("task_state.py", rest)
    if cmd == "status":
        if "--open" in rest:          # open the live view (server, else the file) in the browser, then print the list
            rest = [a for a in rest if a != "--open"]
            view = Path(".claude") / "skills" / "tf" / "scripts" / "run_state.py"
            if need_project() and view.is_file():
                subprocess.run([sys.executable, str(view), "dashboard", "--live", "--open"])
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
    if cmd == "code":
        return cmd_code(rest)
    if cmd == "cloud-setup":
        return cmd_cloud_setup("--apply" in rest)
    if cmd == "work":
        return engine("work.py", rest)
    if cmd == "cooldown":   # the version cooldown the /tf-task loop requires; --fix writes the missing settings
        if not need_project():
            return 2
        script = Path(".claude") / "skills" / "tf" / "scripts" / "security_scan.py"
        return subprocess.run([sys.executable, str(script), "cooldown", *rest]).returncode
    if cmd == "addon":
        return engine("addons.py", rest)
    if cmd == "learn":
        return engine("addons.py", ["learn", *rest])
    if cmd == "metrics":
        if not need_project():
            return 2
        return subprocess.run([sys.executable, str((Path(".tf") / "factory") / "metrics.py"), *rest]).returncode
    if cmd not in (None, "install", "update"):
        if is_launcher() and PROJECT_TF.is_file():   # a command newer than the launcher — the project engine knows it
            return subprocess.run([sys.executable, str(PROJECT_TF), *argv[1:]]).returncode
        print(f"✗ Unknown command '{cmd}'.\n{__doc__}")
        return 2
    if MANIFEST.exists() and cmd != "install":
        rc = update(repo or REPO or None, rest)
        if rc == 0:
            refresh_launcher()
            sync_style_permissions()
        return rc
    repo = repo or REPO
    if not repo:
        print("✗ The factory repository URL is unknown. Pass --repo <url>, set TF_REPO or install the launcher:\n"
              "  python3 core/factory/tf.py --install-launcher --repo https://github.com/<you>/tf.git")
        return 2
    rc = install(repo, rest)
    if rc == 0 and MANIFEST.exists():
        sync_style_permissions()
    return rc


def sync_style_permissions() -> None:
    """After install and update: the Claude Code permission mode from the person's work style in this project (e.g. `plan` for
    `conversation`) — a style set once in ~/.tf/preferences.yaml works in every project after `tf update`."""
    try:
        packs = project_module("packs")
        for m in packs.apply_style_permissions(Path.cwd()) if hasattr(packs, "apply_style_permissions") else []:
            print(f"• {m}")
    except Exception as e:  # noqa: BLE001 — the installation succeeded; the style is an extra
        print(f"⚠ work style: could not sync the Claude Code permission mode ({e})")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
