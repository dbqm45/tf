#!/usr/bin/env python3
"""
tf onboard — prepares a repository to work with the factory: detects project commands from files, writes a readiness
report in plain language and turns on the quality gate.

  tf onboard                 # proposal and a question for consent (without a terminal: the proposal only)
  tf onboard --yes           # write without asking: verify.sh, .claude/quality-gate.json, .tf/reports/readiness.md,
                             # the package manager's 7-day version cooldown (.npmrc, .yarnrc.yml, pyproject.toml)
                             # and the commands in the "Commands" section of the instructions file (CLAUDE.md / CLAUDE.local.md)
  tf onboard --yes --verify  # after writing, runs verification once and says whether it passes
  tf onboard --dry-run       # proposal only, writes nothing
  tf onboard --json          # detection result for scripts, writes nothing

Detects from manifests in the root directory (Node, Python, Go, Rust, Java, .NET; Makefile as a fallback): the test,
lint, type and build commands, the version lock file, CI, the agent instructions file, .gitignore. Without --verify it runs
nothing in the project. `verify.sh` is a single verification command (lint → types → tests) for the quality gate, the `/tf` loop and CI;
on Windows the gate gets just the test command. It does not overwrite an existing verify.sh or gate configuration.
There are at most five blocking checks — the rest are warnings.

Verdict: ready / ready-with-gaps / no-tests. Exit code: 0 — tests exist; 1 — no test command (the factory cannot
check changes) or --verify is red; 2 — invocation error. Standard library only, no network.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) does not know "✓", "⚠" — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes also write and read UTF-8

KINDS = ("test", "lint", "typecheck", "build")
NAMES = {"test": "tests", "lint": "lint", "typecheck": "types", "build": "build"}
LOCKFILES = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb", "uv.lock", "poetry.lock",
             "Pipfile.lock", "pylock.toml", "go.sum", "Cargo.lock", "gradle.lockfile", "packages.lock.json")
CI_FILES = (".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile", ".circleci/config.yml", "bitbucket-pipelines.yml")
NO_TEST = re.compile(r"no test specified", re.I)
MAX_BLOCKING = 5
VERIFY = "./verify.sh"
VERIFY_KINDS = ("lint", "typecheck", "test")   # order in verify.sh: from the fastest check
MARK_BEGIN, MARK_END = "<!-- team-factory:begin -->", "<!-- team-factory:end -->"   # as in install.py
COMMANDS = re.compile(r"(### Commands\n)(.*?)(?=\n### |\n" + re.escape(MARK_END) + ")", re.S)
LABELS = {"test": "Test", "lint": "Lint", "typecheck": "Typecheck", "build": "Build"}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _json(path: Path) -> dict:
    try:
        data = json.loads(_read(path))
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _node(root: Path) -> dict:
    scripts = _json(root / "package.json").get("scripts")
    if not isinstance(scripts, dict):
        return {}
    pm = next((name for lock, name in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lock", "bun"),
                                       ("bun.lockb", "bun")) if (root / lock).is_file()), "npm")
    out = {}
    if isinstance(scripts.get("test"), str) and not NO_TEST.search(scripts["test"]):
        out["test"] = f"{pm} test"
    for kind, names in (("lint", ("lint",)), ("typecheck", ("typecheck", "type-check", "types", "tsc")),
                        ("build", ("build",))):
        name = next((n for n in names if isinstance(scripts.get(n), str)), None)
        if name:
            out[kind] = f"{pm} run {name}"
    return out


def _python(root: Path) -> dict:
    pyproject = _read(root / "pyproject.toml")
    reqs = "".join(_read(p) for p in sorted(root.glob("requirements*.txt")))
    has_tests = any((root / d).is_dir() for d in ("tests", "test"))
    if not pyproject and not reqs and not (root / "setup.py").is_file() and not (root / "pytest.ini").is_file():
        return {}
    known = pyproject + reqs
    run = "uv run " if (root / "uv.lock").is_file() else ("poetry run " if (root / "poetry.lock").is_file() else "")
    out = {}
    if "pytest" in known or (root / "pytest.ini").is_file():
        out["test"] = f"{run}pytest" if run else "python3 -m pytest"
    elif has_tests:
        out["test"] = f"{run}python -m unittest" if run else "python3 -m unittest"
    if "ruff" in known or (root / "ruff.toml").is_file():
        out["lint"] = f"{run}ruff check ."
    elif "flake8" in known or (root / ".flake8").is_file():
        out["lint"] = f"{run}flake8"
    if "mypy" in known or (root / "mypy.ini").is_file():
        out["typecheck"] = f"{run}mypy ."
    elif "pyright" in known or (root / "pyrightconfig.json").is_file():
        out["typecheck"] = f"{run}pyright"
    return out


def _go(root: Path) -> dict:
    if not (root / "go.mod").is_file():
        return {}
    return {"test": "go test ./...", "lint": "go vet ./...", "build": "go build ./..."}


def _rust(root: Path) -> dict:
    if not (root / "Cargo.toml").is_file():
        return {}
    return {"test": "cargo test", "lint": "cargo clippy", "build": "cargo build"}


def _java(root: Path) -> dict:
    if (root / "pom.xml").is_file():
        mvn = "./mvnw" if (root / "mvnw").is_file() else "mvn"
        return {"test": f"{mvn} -q test", "build": f"{mvn} -q -DskipTests package"}
    if any((root / f).is_file() for f in ("build.gradle", "build.gradle.kts")):
        gradle = "./gradlew" if (root / "gradlew").is_file() else "gradle"
        return {"test": f"{gradle} test", "build": f"{gradle} build -x test"}
    return {}


def _dotnet(root: Path) -> dict:
    if not any(root.glob("*.sln")) and not any(root.glob("*.csproj")):
        return {}
    return {"test": "dotnet test", "build": "dotnet build"}


def _make(root: Path) -> dict:
    targets = set(re.findall(r"^([A-Za-z][\w-]*)\s*:(?!=)", _read(root / "Makefile"), re.M))
    return {k: f"make {k}" for k in KINDS if k in targets}


FAMILIES = (("Node", "package.json", _node), ("Python", "pyproject.toml", _python), ("Go", "go.mod", _go),
            ("Rust", "Cargo.toml", _rust), ("Java", "pom.xml / build.gradle", _java), (".NET", "*.sln / *.csproj", _dotnet),
            ("Makefile", "Makefile", _make))


def detect(root: Path) -> dict:
    """Facts from files: commands (the first detected for each kind), files and the verdict. Runs nothing."""
    commands, families = {}, []
    for name, source, fn in FAMILIES:
        found = fn(root)
        if found:
            families.append(name)
        for kind in KINDS:
            if kind in found and kind not in commands:
                commands[kind] = {"command": found[kind], "source": source}
    workflows = root / ".github" / "workflows"
    ci = sorted(p.relative_to(root).as_posix() for p in workflows.glob("*.y*ml")) if workflows.is_dir() else []
    ci += [f for f in CI_FILES if (root / f).is_file()]
    facts = {"lockfile": [f for f in LOCKFILES if (root / f).is_file()], "ci": ci,
             "instructions": [f for f in ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md") if (root / f).is_file()],
             "gitignore": (root / ".gitignore").is_file()}
    missing = [k for k in ("lint",) if k not in commands] + [k for k in ("lockfile", "ci", "gitignore") if not facts[k]]
    verdict = "no-tests" if "test" not in commands else ("ready-with-gaps" if missing else "ready")
    return {"families": families, "commands": commands, "facts": facts, "missing": missing, "verdict": verdict}


GAPS = {   # order = order of fixing: first what the factory needs to check changes
    "test": "No test command. Without tests the factory cannot check whether a change works — this is the first thing "
            "to fix (it can be given as the first task).",
    "lockfile": "No dependency lockfile. Every installation may fetch different versions, so the same test "
                "passes once and fails another time.",
    "lint": "No lint command. Style errors and simple mistakes come out only in review.",
    "ci": "No CI. The checks run only on the author's computer; nobody checks them after the changes are pushed.",
    "gitignore": "No .gitignore. Temporary files and secrets can get into the repository.",
}
VERDICTS = {"ready": "The repository is ready for work with the factory.",
            "ready-with-gaps": "The repository is fit for work with the factory, but has the gaps described below.",
            "no-tests": "The repository is not ready: the factory has nothing to check changes with."}


FLAG_FILES = ("config/flags.json", "flags.json", "feature-flags.json", "config/feature-flags.json",
              "config/feature_flags.json", "config/flags.yaml", "config/flags.yml", "flags.yaml", "flags.yml")
TEST_ENVS = ("test", "testing", "dev", "development", "local", "staging", "stage", "qa")
ENV_NAMES = (*TEST_ENVS, "uat", "preprod", "prod", "production", "live")


def detect_flags(root: Path) -> dict:
    """Feature flags and environments file (from the keys of a JSON file); empty fields when nothing was detected."""
    for rel in FLAG_FILES:
        if not (root / rel).is_file():
            continue
        data = _json(root / rel) if rel.endswith(".json") else {}
        top = [k for k in data if isinstance(data[k], dict)]
        envs = [k for k in top if k.lower() in ENV_NAMES]
        if not envs:                        # layout flag → environment → state
            envs = sorted({e for k in top for e in data[k] if str(e).lower() in ENV_NAMES})
        test = next((e for name in TEST_ENVS for e in envs if e.lower() == name), None)
        return {"file": rel, "envs": envs, "test_env": test}
    return {"file": None, "envs": [], "test_env": None}


def detect_smoke(root: Path) -> str | None:
    """Post-deploy smoke test command, if the project has one: a script, a `smoke` script in package.json, a Makefile target."""
    if (root / "scripts" / "smoke.sh").is_file():
        return "./scripts/smoke.sh"
    scripts = _json(root / "package.json").get("scripts")
    for name in ("smoke", "test:smoke"):
        if isinstance(scripts, dict) and isinstance(scripts.get(name), str):
            return f"npm run {name}"
    if re.search(r"(?m)^smoke\s*:", _read(root / "Makefile")):
        return "make smoke"
    return None


FRAMEWORK_PORTS = (("@angular/core", 4200), ("next", 3000), ("react-scripts", 3000), ("nuxt", 3000), ("astro", 4321),
                   ("@sveltejs/kit", 5173), ("vite", 5173))   # the dev server's default port (the same list is in ui_snap.py)


def detect_preview(root: Path) -> dict | None:
    """Where the web frontend's dev server answers, for the visual check of the /tf loop (`ui_snap.py`): the address
    from the framework's default port, the start command from the dev/start/serve script. None when it is not a web frontend."""
    pkg = _json(root / "package.json")
    deps = {**(pkg.get("devDependencies") or {}), **(pkg.get("dependencies") or {})}
    port = next((p for name, p in FRAMEWORK_PORTS if name in deps), None)
    if port is None:
        return None
    scripts = pkg.get("scripts") if isinstance(pkg.get("scripts"), dict) else {}
    pm = next((n for lock, n in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lock", "bun"),
                                 ("bun.lockb", "bun")) if (root / lock).is_file()), "npm")
    name = next((n for n in ("dev", "start", "serve") if isinstance(scripts.get(n), str)), None)
    start = "" if name is None else (f"{pm} start" if name == "start" and pm == "npm" else f"{pm} run {name}")
    return {"url": f"http://localhost:{port}", "start": start, "routes": ["/"]}


def uses_verify(root: Path, det: dict) -> bool:
    """Whether the gate runs verify.sh: it is already in the repository or can be generated (not on Windows)."""
    return os.name != "nt" and ((root / "verify.sh").is_file() or "test" in det["commands"])


def verify_script(det: dict) -> str:
    lines = ["#!/usr/bin/env bash",
             "# One command to verify the project: lint, types, tests. Generated by `tf onboard`.",
             "# The factory's quality gate runs it (.claude/quality-gate.json); the same command fits CI.",
             "# When the project's commands change, fix them here.",
             "set -euo pipefail", 'cd "$(dirname "$0")"', ""]
    for kind in VERIFY_KINDS:
        if kind in det["commands"]:
            lines += [f'echo "== {NAMES[kind]}"', det["commands"][kind]["command"]]
    return "\n".join(lines) + "\n"


def blocking(det: dict, verify: bool = False) -> list[str]:
    """Checks that stop work (at most MAX_BLOCKING). The rest are warnings."""
    out = []
    for kind in (VERIFY_KINDS if verify else ("test",)):
        if kind in det["commands"]:
            out.append(f"{NAMES[kind].capitalize()}: `{det['commands'][kind]['command']}` — the work does not finish "
                       "until they pass.")
    out.append("Secrets: writing keys and passwords to files is stopped.")
    out.append("Test before code: production code without a prior failing test is stopped.")
    return out[:MAX_BLOCKING]


def report(det: dict, verify: bool = False) -> str:
    cmds, facts = det["commands"], det["facts"]
    lines = ["# Repository readiness for work with the factory", "", VERDICTS[det["verdict"]], "", "## What is there"]
    for kind in KINDS:
        if kind in cmds:
            lines.append(f"- {NAMES[kind]}: `{cmds[kind]['command']}` (from: {cmds[kind]['source']})")
    if facts["lockfile"]:
        lines.append(f"- dependency lockfile: {', '.join(facts['lockfile'])}")
    if facts["ci"]:
        lines.append(f"- CI: {', '.join(facts['ci'])}")
    if facts["instructions"]:
        lines.append(f"- agent instructions file: {', '.join(facts['instructions'])}")
    if facts["gitignore"]:
        lines.append("- .gitignore")
    if lines[-1] == "## What is there":
        lines.append("- no project commands or configuration files detected")
    lines += ["", "## What is missing (in the order of fixing)"]
    gaps = [GAPS[k] for k in GAPS if (k == "test" and "test" not in cmds) or k in det["missing"]]
    lines += [f"{i}. {g}" for i, g in enumerate(gaps, 1)] or ["Nothing significant."]
    lines += ["", "## What the factory blocks"] + [f"- {b}" for b in blocking(det, verify)]
    warn = [f"{NAMES[k]} (`{cmds[k]['command']}`)" for k in (("build",) if verify else ("lint", "typecheck", "build"))
            if k in cmds]
    if warn:
        lines += ["", "Only warns (does not stop the work): " + ", ".join(warn) + "."]
    lines += ["", "## When a human should look",
              "- when the tests do not pass after three fix attempts — the factory stops trying and asks;",
              "- before merging a change — a human merges, not the agent;",
              "- when this report says something is missing — gaps are fixed once, best before the first task.", ""]
    return "\n".join(lines)


def proposal(root: Path, det: dict) -> tuple[list[str], dict]:
    """What will be written: a description for a human and the file contents (path → text)."""
    say, files = [], {}
    verify = uses_verify(root, det)
    if verify and (root / "verify.sh").is_file():
        say.append("• verify.sh already exists — it stays unchanged.")
    elif verify:
        files[root / "verify.sh"] = verify_script(det)
        say.append("• verify.sh — one verification command: "
                   + " → ".join(NAMES[k] for k in VERIFY_KINDS if k in det["commands"]) + ".")
    command = VERIFY if verify else (det["commands"].get("test") or {}).get("command")
    gate = root / ".claude" / "quality-gate.json"
    if gate.is_file():
        say.append("• .claude/quality-gate.json already exists — it stays unchanged.")
    elif command:
        files[gate] = json.dumps({"command": command}, ensure_ascii=False, indent=2) + "\n"
        say.append(f"• .claude/quality-gate.json — the quality gate with the command `{command}`.")
    else:
        say.append("• the quality gate stays off: no test command detected.")
    line = commands_line(det, verify)
    for name in ("CLAUDE.local.md", "CLAUDE.md"):
        old = _read(root / name)
        new = with_commands(old, line) if line else old
        if new != old:
            files[root / name] = new
            say.append(f"• {name} — the project's commands in the \"Commands\" section.")
    card = root / ".tf" / "config" / "operations.json"
    try:                                  # the card may have been created earlier without flags (e.g. a tracker write by the /tf loop)
        known = json.loads(card.read_text(encoding="utf-8")) if card.exists() else {}
    except (OSError, ValueError):
        known = None                      # an unreadable card is left untouched
    added = {}
    if isinstance(known, dict) and "flags" not in known:   # how the factory knows how flags work in the project
        flags = added["flags"] = detect_flags(root)
        say.append(f"• .tf/config/operations.json — the operations card: flag file {flags['file']}, environments "
                   f"{', '.join(flags['envs'])}, test: {flags['test_env']}." if flags["file"] else
                   "• .tf/config/operations.json — the operations card: no feature flag file detected; fill in "
                   "`file`, `envs` and `test_env` if the project uses flags (without them the factory asks to check them by hand).")
    if isinstance(known, dict) and "deploy" not in known:  # how to check and roll back a deployment (tf task deployed, PR description)
        smoke = detect_smoke(root)
        added["deploy"] = {"rollback": "", "rollback_minutes": None, "smoke": smoke or "", "approval": "", "logs": ""}
        say.append("• .tf/config/operations.json — the operations card, the deployment part (`deploy`): smoke test "
                   + (f"`{smoke}` (detected)" if smoke else "not detected — write the command in `smoke`")
                   + "; fill in `rollback` (how to roll back a deployment) and `rollback_minutes` (how long it takes), `approval` "
                     "(what a human approves) and `logs` (the logs command). Without `smoke` the factory stops at the merge.")
    preview = detect_preview(root) if isinstance(known, dict) and "preview" not in known else None
    if preview:                           # the visual check of UI changes: where to take the screenshots (ui_snap.py)
        added["preview"] = preview
        say.append(f"• .tf/config/operations.json — the operations card, the visual check part (`preview`): "
                   f"`{preview['url']}`" + (f", started with `{preview['start']}`" if preview["start"] else
                                           " (no dev/start/serve script: write the command in `start`)")
                   + "; fill in `routes` with the screens that matter (the default is `/`).")
    if added:
        files[card] = json.dumps({**known, **added}, ensure_ascii=False, indent=1) + "\n"
    files[root / ".tf" / "reports" / "readiness.md"] = report(det, verify)
    say.append("• .tf/reports/readiness.md — the readiness report.")
    return say, files


def commands_line(det: dict, verify: bool) -> str:
    parts = ([f"Verification: `{VERIFY}`"] if verify else []) + [
        f"{LABELS[k]}: `{det['commands'][k]['command']}`" for k in KINDS if k in det["commands"]]
    return "- " + " · ".join(parts) if parts else ""


def with_commands(text: str, line: str) -> str:
    """Replaces the content of the "Commands" subsection in the factory block; a file without the block or without the subsection stays unchanged."""
    start = text.find(MARK_BEGIN)
    end = text.find(MARK_END, start)
    if start < 0 or end < 0:
        return text
    block = text[start:end + len(MARK_END)]
    return text[:start] + COMMANDS.sub(lambda m: m.group(1) + line + "\n", block, count=1) + text[end + len(MARK_END):]


def run_verify(root: Path, command: str, timeout: float = 900) -> tuple[bool, str]:
    """Runs verification once (only with --verify): (green?, output trimmed to the beginning and end)."""
    try:
        r = subprocess.run(shlex.split(command), cwd=root, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"time limit of {timeout:g} s exceeded"
    except OSError as e:
        return False, str(e)
    out = r.stdout + r.stderr
    saved = ".tf/logs/verify-output.txt"
    try:   # full output to a file; the screen gets the beginning and end (the first error is often at the start of the log)
        (root / ".tf" / "logs").mkdir(parents=True, exist_ok=True)
        (root / saved).write_text(out, encoding="utf-8")
    except OSError:
        pass
    if len(out) > 3000:
        out = out[:1000] + f"\n… [skipped {len(out) - 3000} characters; full output: {saved}] …\n" + out[-2000:]
    return r.returncode == 0, out


LOCAL_FILES = ("verify.sh", ".claude/quality-gate.json")   # files from tf onboard that belong to the project's repository


def _git(root: Path, *args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=20)
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return r.returncode, r.stdout.strip()


def settle_files(root: Path) -> str:
    """What to do with the onboarding files in git. A private install commits nothing, so the files stay local
    (an entry in .git/info/exclude) and the working tree is clean; in a team install they go into the commit. Returns a sentence for a human."""
    code, exclude = _git(root, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude")
    if code != 0 or not exclude:
        return ""
    mine = [f for f in LOCAL_FILES + COOLDOWN_FILES[:3]
            if (root / f).is_file() and _git(root, "ls-files", "--error-unmatch", f)[0] != 0]
    if not mine:
        return ""
    if _json(root / ".claude" / "factory-manifest.json").get("mode") != "private":
        return "To commit: " + ", ".join(mine) + " — then the checks work for everyone after `git pull`."
    path = Path(exclude)
    have = _read(path).splitlines()
    new = [f for f in mine if f not in have]
    if new:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(("" if not have or have[-1] == "" else "\n") + "\n".join(new) + "\n")
    return ("Private installation: " + ", ".join(mine) + " stay local (an entry in .git/info/exclude), "
            "so the working tree is clean. For the checks to work for the whole team: tf install --shared.")


COOLDOWN_FILES = (".npmrc", ".yarnrc.yml", "pnpm-workspace.yaml", "pyproject.toml")


def cooldown_fix(root: Path) -> list[str]:
    """The version cooldown the /tf loop requires (security_scan.py cooldown --fix): written with the human's --yes.
    A private install commits nothing: it only creates files git does not track (settle_files excludes them) and
    leaves an existing file alone — `tf cooldown --fix` changes it on the human's word."""
    script = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "tf" / "scripts" / "security_scan.py"
    if not script.is_file():
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_security_scan", script)
    mod = importlib.util.module_from_spec(spec)
    private = _json(root / ".claude" / "factory-manifest.json").get("mode") == "private"
    refused = []

    def allow(path: Path) -> bool:
        if private and path.is_file():
            refused.append(path.relative_to(root).as_posix())
            return False
        return True
    try:
        spec.loader.exec_module(mod)
        done = mod.fix_cooldown(root, allow)
        if refused:
            done.append(f"not changed in a private install: {', '.join(sorted(set(refused)))} — run tf cooldown --fix")
        return done
    except Exception as e:  # noqa: BLE001 — onboarding goes on; the loop's start check says what is missing
        return [f"not written ({e})"]


def main(argv: list[str]) -> int:
    flags = set(argv[1:])
    unknown = flags - {"--yes", "--dry-run", "--json", "--verify", "-h", "--help"}
    if unknown or flags & {"-h", "--help"}:
        print(__doc__)
        return 2 if unknown else 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    det = detect(root)
    code = 1 if det["verdict"] == "no-tests" else 0
    if "--json" in flags:
        print(json.dumps(det, ensure_ascii=False, indent=2))
        return code
    print(report(det, uses_verify(root, det)))
    say, files = proposal(root, det)
    print("To write:\n" + "\n".join(say))
    if "--dry-run" in flags:
        print("\n--dry-run: nothing was written.")
        return code
    if "--yes" not in flags:
        if not sys.stdin.isatty():
            print("\nNothing was written. To write without asking: tf onboard --yes")
            return code
        if input("\nWrite? [Y/n] ").strip().lower() in ("n", "nie", "no"):
            print("Nothing was written.")
            return code
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        if path.name == "verify.sh":
            path.chmod(0o755)
    cooldown = cooldown_fix(root)
    if cooldown:
        print("✓ The package manager's version cooldown (7 days, N10): " + "; ".join(cooldown))
    print("\n✓ Written. Check the state: tf doctor")
    note = settle_files(root)
    if note:
        print(note)
    if "--verify" in flags:
        command = _json(root / ".claude" / "quality-gate.json").get("command")
        if not command:
            print("⚠ Nothing to run: the quality gate has no command.")
            return 1
        command = command if isinstance(command, str) else " ".join(map(str, command))
        ok, tail = run_verify(root, command)
        print(f"✓ Verification passes: `{command}`." if ok
              else f"✗ Verification does not pass: `{command}`. Fix it before the first task.\n"
                   f"--- output ---\n{tail}")
        return code if ok else 1
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
