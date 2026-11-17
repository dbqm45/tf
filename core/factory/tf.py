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
  tf new skill <name> "<description>" [--role <role>]
                              # your own skill from the template, with a scenario file (.tf/factory/build.py new-skill)
  tf skill check <name>       # quality gate of a skill: structure, scenarios, audit (.tf/factory/skill_gate.py)
  tf skill audit <directory>  # security audit of a skill, before you use a foreign one (.tf/factory/skill_audit.py)
  tf uninstall [--dry-run] [--yes] [--force]   # remove the factory from this project (keeps your files; --force removes
                              # them too); backup in ~/.tf/backups/
  tf style [<name>] [--here]  # your work style: autonomous | step-by-step | conversation; no name — show the current one;
                              # saved in ~/.tf/preferences.yaml (all your projects) or, with --here, .tf/config/me.yaml
  tf config show [<key>]      # merged configuration and where each value comes from (factory or project);
                              # `tf config show steps`: who runs each /tf loop step, with model and effort
  tf task start <KEY> --title "<title>" | stage <KEY> <stage> | status <KEY>
  tf task start <CHG>-<TSK> --title "<title>" --change <CHG> --cut <TSK>   # task of a pdi change cut
  tf task freeze <KEY> <file> --by human:<id> | reopen <KEY> <file> --by human:<id> --reason "<why>"
  tf status [--json] [--open] [--all] # open tasks (--all: closed ones too): stage, slices with current evidence, files to refresh, what waits for you;
                              # --open builds the live view (.tf/runs/dashboard.html) and opens it in the browser
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
  tf work --once --budget <USD> [--key <KEY>] [--dry-run]
                              # unattended: one task in Auto mode (light or normal weight) through the /tf loop in its
                              # own worktree (.tf/worktrees/<KEY>) with a spending limit; never merges (.tf/factory/work.py)
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
    """Ten plik to launcher (kopia w ~/.local/bin), a nie tf.py silnika w .tf/factory/ ani w klonie fabryki."""
    return Path(__file__).resolve().parent.name != "factory"


def refresh_launcher() -> None:
    """Po aktualizacji projektu launcher przejmuje tf.py silnika projektu (z zachowanym adresem repo), żeby znał
    nowe polecenia. Nic nie robi, gdy to nie launcher albo projekt nie ma .tf/factory/tf.py."""
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
    org = next((d for label, d in layers if "org_defaults" in label), {})   # nakładka firmowa
    team = next((d for label, d in layers if "team_defaults" in label), {})   # nakładka zespołu
    person = next((d for label, d in layers if label.endswith("(osoba)")), {})   # preferencje osoby (tf style)
    cfg = packs.load_config(root)
    if key == "steps" and cfg.get("steps"):     # kroki pętli /tf z modelem i effortem po nałożeniu profilu kosztów
        full = project_module("build").load_config()
        print(f"# Kroki pętli /tf (profil kosztów: {full.get('_profile')}). Zmiana: steps w .tf/config/config.yaml, "
              "potem python3 .tf/factory/build.py")
        print(f"{'krok':<16} {'co':<38} {'kto':<18} {'tier':<5} {'model':<8} effort")
        for sid, step in full["steps"].items():
            tier = full["tiers"].get(step.get("tier"), {})
            print(f"{sid:<16} {step.get('label', ''):<38} {step.get('who', ''):<18} {step.get('tier', ''):<5} "
                  f"{tier.get('model', '?'):<8} {tier.get('effort', '?')}")
        return 0
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
        src = ("osoba" if k in person else "projekt" if k in own else "zespół" if k in team
               else "organizacja" if k in org else "fabryka")
        print(f"{k:<28} {src:<11} {shown}")
    for w in (packs.work_style(root).get("warnings") or []) if hasattr(packs, "work_style") else []:
        print(f"⚠ preferencje osoby: {w}")
    print("# Cała wartość jednego klucza: tf config show <klucz>")
    return 0


def cmd_style(rest: list[str]) -> int:
    """Styl pracy osoby: pokaż albo zapisz w ~/.tf/preferences.yaml (--here: .tf/config/me.yaml, poza repozytorium)."""
    here = "--here" in rest
    names = [a for a in rest if a != "--here"]
    packs = project_module("packs")
    root = Path.cwd()
    if not hasattr(packs, "work_style"):
        print("✗ Silnik w .tf/factory/ nie zna stylów pracy — zaktualizuj fabrykę: tf update")
        return 2
    styles = packs.load_config(root).get("styles") or {}
    if not names:
        ws = packs.work_style(root)
        print(f"Styl pracy: {ws.get('style') or 'brak (ustawienia projektu)'}")
        for m in packs.apply_style_permissions(root) if hasattr(packs, "apply_style_permissions") else []:
            print(f"• {m}")
        print(f"  domyślny tryb zadania: {ws['default_mode']} (dozwolone: {', '.join(ws['allowed_modes'])})")
        print(f"  pytanie wstrzymuje tylko swój kawałek: {'tak' if ws['blocked_slices'] else 'nie'}")
        print(f"  zgoda człowieka po każdym kawałku: {'tak' if ws['confirm_each_slice'] else 'nie'}")
        for w in ws.get("warnings") or []:
            print(f"⚠ {w}")
        print(f"Zmiana: tf style <{'|'.join(styles)}> [--here]")
        return 0
    if len(names) != 1 or names[0] not in styles:
        print(f"✗ Nieznany styl „{' '.join(names)}”. Do wyboru: {', '.join(styles)}")
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
    print(f"✓ styl {names[0]} zapisany w {path if not here else '.tf/config/me.yaml'} — domyślny tryb zadania: "
          f"{ws['default_mode']}, zgoda po każdym kawałku: {'tak' if ws['confirm_each_slice'] else 'nie'}")
    for m in perm_msgs:
        print(f"• {m}")
    for w in ws.get("warnings") or []:
        print(f"⚠ {w}")
    return 0


def ensure_excluded(root: Path, rel: str) -> None:
    """Plik osoby nie trafia do repozytorium: wpis w .git/info/exclude, jeśli git go jeszcze nie ignoruje."""
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
    """Jedna linia o plikach instrukcji projektu (CLAUDE.md, AGENTS.md…): kontrole z uwagami albo „bez uwag”."""
    try:
        r = subprocess.run([sys.executable, str(lint), "--root", ".", "--json"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        files = json.loads(r.stdout).get("files") or []
    except (OSError, ValueError, subprocess.SubprocessError, AttributeError):
        return "⚠ instrukcje: karty plików instrukcji nie udało się policzyć"
    if not files:
        return "• instrukcje: projekt nie ma pliku CLAUDE.md ani AGENTS.md"
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
        return f"✓ instrukcje: {len(files)} plik(i) bez uwag"
    return ("⚠ instrukcje: " + "; ".join(notes) + f"\n  szczegóły: python3 {lint.as_posix()} --root .")


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
    models = Path(".tf") / "factory" / "model_check.py"
    if models.is_file():   # nazwy modeli w konfiguracji (krok H20) — informacja, nie zmienia wyniku doctora
        m = subprocess.run([sys.executable, str(models)], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env={**os.environ, "CLAUDE_PROJECT_DIR": str(Path.cwd())})
        if m.stdout.strip():
            print(m.stdout.strip())
    health = Path(".tf") / "factory" / "metrics.py"
    if health.is_file():   # pogorszenie po aktualizacji fabryki (krok H29, D13) — tylko ostrzeżenie, kod bez zmian
        u = subprocess.run([sys.executable, str(health), "--after-update"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env={**os.environ, "CLAUDE_PROJECT_DIR": str(Path.cwd())})
        if u.stdout.startswith("⚠"):
            print(u.stdout.strip())
    lint = Path(".claude") / "skills" / "core-agent-instructions" / "scripts" / "instructions_lint.py"
    if lint.is_file():   # karta plików instrukcji projektu (krok H21) — informacja, nie zmienia wyniku doctora
        print(instructions_summary(lint))
    gate = Path(".claude") / "hooks" / "quality_gate.py"
    if gate.is_file():   # czy bramka jakości działa (komunikat w zwykłym języku) — informacja, nie zmienia wyniku
        g = subprocess.run([sys.executable, str(gate), "--status"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env={**os.environ, "CLAUDE_PROJECT_DIR": str(Path.cwd())})
        if g.stdout.strip():
            print(g.stdout.strip())
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
    if cmd in ("language", "commit-language"):   # 12.0.0: język bez ustawień, jak w Claude
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
    if cmd == "uninstall":
        return engine("uninstall.py", rest) if need_project() else 2
    if cmd == "style":
        return cmd_style(rest) if need_project() else 2
    if cmd == "task":
        return engine("task_state.py", rest)
    if cmd == "status":
        if "--open" in rest:          # build the live view and open it in the browser, then print the list
            rest = [a for a in rest if a != "--open"]
            view = Path(".claude") / "skills" / "tf" / "scripts" / "run_state.py"
            if need_project() and view.is_file():
                subprocess.run([sys.executable, str(view), "dashboard", "--open"])
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
    if cmd == "work":
        return engine("work.py", rest)
    if cmd == "metrics":
        if not need_project():
            return 2
        return subprocess.run([sys.executable, str((Path(".tf") / "factory") / "metrics.py"), *rest]).returncode
    if cmd not in (None, "install", "update"):
        if is_launcher() and PROJECT_TF.is_file():   # polecenie nowsze niż launcher — zna je silnik projektu
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
    """Po instalacji i aktualizacji: tryb uprawnień Claude Code ze stylu pracy osoby w tym projekcie (np. `plan` dla
    `conversation`) — styl ustawiony raz w ~/.tf/preferences.yaml działa w każdym projekcie po `tf update`."""
    try:
        packs = project_module("packs")
        for m in packs.apply_style_permissions(Path.cwd()) if hasattr(packs, "apply_style_permissions") else []:
            print(f"• {m}")
    except Exception as e:  # noqa: BLE001 — instalacja się udała; styl to dodatek
        print(f"⚠ styl pracy: nie udało się uzgodnić trybu uprawnień Claude Code ({e})")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
