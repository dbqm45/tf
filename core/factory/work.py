#!/usr/bin/env python3
"""Unattended work (step H19): `tf work --once` takes one task that a human marked with the Auto mode
(`tf task mode <KEY> auto`), and runs it with the `/tf-task` loop in a separate worktree with a spending limit. It does not merge or deploy:
the result is a `story/<key>` branch with a PR or a STOP block in the task's worktree.

  tf work --once --budget <USD> [--key <KEY>] [--base <branch>] [--dry-run]

A task that can be taken: Auto mode, light or normal weight, stage before PR, not waiting for a human, no worktree yet
(resuming in an existing worktree only via `--key`) and not taken by another run (`.tf/locks/<KEY>.json`).
Exit code: 0 — run finished, 2 — refusal, 3 — no task to take, other — the agent's code.
Agent: `claude -p "/tf-task <KEY> --auto --budget <USD>" --max-budget-usd <USD> --permission-mode <mode, default acceptEdits>
--permission-prompts none --output-format json --strict-mcp-config`, only with allowed environment variables; before the start
the files controlling the agent in the worktree must be the same as in the human's copy. The `TF_WORK_AGENT` variable replaces
the `claude` command (tests). Journal: `.tf/logs/work.jsonl`.

`--permission-prompts none` (Claude Code >= 2.1.259): a call that would wait on a permission prompt is denied instead, and the
run goes on; permission rules, the factory's hooks and the permission mode still decide first
(https://code.claude.com/docs/en/headless#turn-off-permission-prompts-in-unattended-runs).
Cost: `--output-format json` returns `total_cost_usd` (https://code.claude.com/docs/en/headless). The end entry records it as
`cost_usd` with `cost_source: "claude"`; without the field (an older CLI, a run that printed no JSON) the run's limit is
recorded instead, with `cost_source: "estimate"`. The task's total limit (`work.task_budget_usd`) sums these.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import math
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
for _stream in (sys.stdout, sys.stderr):  # Windows: the code page lacks “✓” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

CHANGES = Path("docs") / "project" / "changes"
LOCKS = Path(".tf") / "locks"
WORKTREES = Path(".tf") / "worktrees"
LOG = Path(".tf") / "logs" / "work.jsonl"
MANIFEST = Path(".claude") / "factory-manifest.json"
OWN_CONFIG = Path(".tf") / "config"
OPEN_STAGES = ("intake", "spec", "plan", "implementation", "review")
DEFAULTS = {"budget_usd": 0, "task_budget_usd": 20, "permission_mode": "acceptEdits", "lock_hours": 6, "timeout_minutes": 180, "model": ""}
# unattended, nobody answers a permission question: in -p mode a tool outside the allowed list is rejected.
# acceptEdits (default) accepts file edits in the working directory (worktree) — without it the loop cannot write code, because
# the factory settings do not allow Edit/Write (pilot 2026-11-15); dontAsk rejects edits too; broader modes are out
MODES = ("acceptEdits", "dontAsk", "plan")
COPY_PREFIXES = (".claude/", ".tf/factory/")   # from the manifest only factory files are copied
MAX_RUN_USD = 500
# files that control the agent (permissions, hooks, instructions, MCP servers): in the worktree they must be the same as in the
# human's copy — otherwise a task branch (e.g. from someone else's push) would run its own hook or instruction without asking
CONTROL_FILES = (".claude/settings.json", ".claude/settings.local.json", ".mcp.json", "CLAUDE.md", "CLAUDE.local.md",
                 "AGENTS.md", ".claude/CLAUDE.md", ".claude/rules", ".claude/output-styles", ".claude/hooks",
                 ".claude/agents", ".claude/skills", ".claude/commands", ".tf/factory", ".tf/config",
                 ".tf/plugin")   # factory mode (install --layout plugin): the plugin the agent loads
INSTRUCTION_NAMES = ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md")     # also nested in project directories
# environment variables passed to the agent: system, proxy and certificates, Claude authentication; the rest (GitHub,
# cloud, database tokens) only from the human's list in the TF_WORK_ENV_ALLOW variable
ENV_ALLOW = {"PATH", "HOME", "USER", "LOGNAME", "SHELL", "LANG", "LANGUAGE", "TERM", "TMPDIR", "TMP", "TEMP", "TZ",
             "PWD", "PYTHONUTF8", "PYTHONIOENCODING", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "https_proxy",
             "http_proxy", "no_proxy", "ALL_PROXY", "all_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
             "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "GIT_SSL_CAINFO", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
             "ANTHROPIC_BASE_URL", "CLAUDE_CONFIG_DIR", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME",
             "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT", "APPDATA", "LOCALAPPDATA", "USERPROFILE",
             "HOMEDRIVE", "HOMEPATH", "PROGRAMFILES", "PROGRAMDATA", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE",
             "TF_WORK_AGENT"}
ENV_PREFIXES = ("LC_", "CLAUDE_CODE_", "ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_")   # without TF_: Terraform keeps secrets there
ENV_EXTRA = "TF_WORK_ENV_ALLOW"   # extra variables (e.g. GITHUB_TOKEN) are given by the human in their own environment, not the repository
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def config(root: Path) -> dict:
    """The `work` section: engine ← organization (company overlay) ← project; without configuration — default values."""
    try:
        spec = importlib.util.spec_from_file_location("tf_packs_cfg", Path(__file__).resolve().with_name("packs.py"))
        packs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packs)
        cfg = packs.load_yaml(Path(__file__).resolve().with_name("config.yaml"))
        for _label, layer in packs.config_layers(root)[1:]:   # organization (company overlay), then project
            cfg = packs.deep_merge(cfg, layer)
        section = cfg.get("work") if isinstance(cfg.get("work"), dict) else {}
    except Exception:  # noqa: BLE001 — no configuration means the default settings
        section = {}
    return {**DEFAULTS, **section}


def load_task(root: Path, key: str) -> dict | None:
    try:
        data = json.loads((root / CHANGES / key / "task.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def waits_for_human(root: Path, key: str) -> bool:
    try:
        run = json.loads((root / ".tf" / "runs" / key / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if not (isinstance(run, dict) and run.get("stage") == "needs"):
        return False
    # A plan waiting for approval (after `/tf-task … --plan`) is answered by the human setting the Auto mode: that is the
    # consent to unsupervised work (tf stress W2: otherwise the documented path deadlocks). The full weight still waits.
    if run.get("needs") == "plan":
        task = load_task(root, key) or {}
        if task.get("mode") == "auto" and task.get("mode_by") == "human" and task.get("weight") != "full":
            return False
    return True


def clean(text, limit: int = 120) -> str:
    return CONTROL.sub(" ", str(text or ""))[:limit]


def refusal(root: Path, task: dict, folder: str) -> str | None:
    """Why the task must not be taken unattended; None — allowed. The key is the task folder name, and the `key` field
    in task.json must match it (task.json comes from the repository, e.g. from someone else's PR)."""
    if not KEY.fullmatch(folder) or task.get("key") != folder:
        return f"{clean(folder)}: the key in task.json does not match the task folder name. Task skipped"
    key = folder
    if task.get("closed") or task.get("stage") not in OPEN_STAGES:
        return f"{key}: stage {clean(task.get('stage'), 30)}. Unattended work takes a task only as far as a PR"
    if task.get("weight") == "full":
        return f"{key}: weight full. Unattended work takes only light and normal tasks (full needs a panel and a human)"
    if task.get("mode") != "auto":
        return (f"{key}: mode {clean(task.get('mode') or 'normal', 30)}, not auto. A human must allow unattended work: "
                f"tf task mode {key} auto")
    if waits_for_human(root, key):
        return f"{key}: waits for a human (tf status). It returns to the queue after the answer"
    return None


def candidates(root: Path) -> list[dict]:
    """Tasks that can be taken, oldest first; skips those with a worktree (resuming only via --key)."""
    out = []
    for f in sorted((root / CHANGES).glob("*/task.json")):
        task = load_task(root, f.parent.name)
        if task and refusal(root, task, f.parent.name) is None and not (root / WORKTREES / f.parent.name).exists():
            out.append(task)
    return sorted(out, key=lambda t: str(t.get("created") or ""))


def alive(pid) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True            # no permission or a system without signals — treat as alive
    return True


def claim(root: Path, key: str, hours: float) -> tuple[bool, str]:
    """Takes the task atomically (`O_CREAT|O_EXCL`). Takes over a dead lock of this host older than `hours`."""
    folder = root / LOCKS
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{key}.json"
    note = ""
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            try:
                held = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                held = {}
            held = held if isinstance(held, dict) else {}
            at = held.get("at") if isinstance(held.get("at"), (int, float)) else path.stat().st_mtime
            stale = (time.time() - at > hours * 3600 and held.get("host") == socket.gethostname()
                     and not alive(held.get("pid")))
            if not stale:
                return False, ""
            note = (f"⚠ took over the lock on {key} held by dead process {held.get('pid')} since {datetime.fromtimestamp(at).isoformat(timespec='minutes')}")
            if not take_over(path, held, hours):
                return False, ""
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "host": socket.gethostname(), "at": time.time()}, f)
        return True, note
    return False, ""


def take_over(path: Path, seen: dict, hours: float) -> bool:
    """Removes a dead lock under a separate mutex (`<KEY>.json.takeover`, `O_EXCL`): one process takes over, and before
    removing it checks that the lock is still the same dead one it read (not a fresh lock of another process)."""
    mutex = path.with_name(path.name + ".takeover")
    try:
        if time.time() - mutex.stat().st_mtime > hours * 3600:
            mutex.unlink(missing_ok=True)          # mutex left after an interrupted takeover
    except OSError:
        pass
    try:
        fd = os.open(mutex, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except OSError:
        return False
    os.close(fd)
    try:
        try:
            now_held = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return True
        except (OSError, ValueError):
            now_held = {}
        if (now_held if isinstance(now_held, dict) else {}) != seen:
            return False
        path.unlink(missing_ok=True)
        return True
    finally:
        mutex.unlink(missing_ok=True)


def release(root: Path, key: str) -> None:
    (root / LOCKS / f"{key}.json").unlink(missing_ok=True)


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=120)


def inside(root: Path, rel: str) -> Path | None:
    p = (root / rel).resolve()
    return p if not Path(rel).is_absolute() and root.resolve() in p.parents else None


def within(base: Path, path: Path) -> bool:
    try:
        return base.resolve() in path.resolve().parents
    except OSError:
        return False


def copy_missing(src: Path, dst: Path, src_root: Path, dst_root: Path) -> int:
    """Copies a file or directory, skipping what already exists at the destination, symlinks and paths leading outside
    the source and destination directories; returns the number of files."""
    if src.is_symlink() or not within(src_root, src) or not within(dst_root, dst.parent / "x"):
        return 0
    if src.is_file():
        if dst.exists() or dst.is_symlink():
            return 0
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return 1
    n = 0
    for f in sorted(src.rglob("*")) if src.is_dir() else []:
        if f.is_file() and "__pycache__" not in f.parts:
            n += copy_missing(f, dst / f.relative_to(src), src_root, dst_root)
    return n


def prepare_worktree(root: Path, key: str, base: str) -> tuple[Path | None, str]:
    """The task worktree on the `story/<key>` branch; in a private installation the factory files are not in git, so it copies
    the files from the manifest, the project configuration and the task folder that are missing in the worktree."""
    wt = root / WORKTREES / key
    if not within(root / WORKTREES, wt):
        return None, "worktree path is outside .tf/worktrees"
    if not wt.exists():
        branch = f"story/{key.lower()}"
        has = git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0
        r = git(root, "worktree", "add", "-q", str(wt), branch) if has else \
            git(root, "worktree", "add", "-q", "-b", branch, str(wt), base)
        if r.returncode != 0:
            return None, f"git worktree add failed: {(r.stdout + r.stderr).strip()}"
    try:
        files = json.loads((root / MANIFEST).read_text(encoding="utf-8")).get("files") or {}
    except (OSError, ValueError, AttributeError):
        files = {}
    referenced = sorted(r for r in settings_paths(root)            # without secrets, even when the command points to them
                        if not any(part.startswith((".env", ".git")) for part in Path(r).parts))
    rels = [MANIFEST.as_posix(), *CONTROL_FILES, *referenced, (CHANGES / key).as_posix(),
            (Path(".tf") / "runs" / key).as_posix(),
            *[r for r in files if isinstance(r, str) and r.startswith(COPY_PREFIXES) and ".." not in Path(r).parts]]
    # control files missing in the worktree (uncommitted or outside git) come from the human's copy; files that
    # the branch has different from that copy are not overwritten — control_drift detects them and the run is rejected
    copied = sum(copy_missing(src, wt / rel, root, wt) for rel in dict.fromkeys(rels)
                 if (src := inside(root, rel)) and src.exists())
    return wt, f"copied {copied} factory and task files to the worktree" if copied else ""


def has_plugin(root: Path) -> bool:
    """Factory mode (install --layout plugin): the factory lives in .tf/plugin/ and the agent must load it."""
    return (root / ".tf" / "plugin" / ".claude-plugin" / "plugin.json").is_file()


def session_settings(wt: Path) -> Path:
    """The worktree's factory session settings with the isolation level (isolation.py launch), as in `tf code`."""
    iso = Path(__file__).resolve().parent / "isolation.py"
    plain = wt / ".tf" / "plugin" / "session-settings.json"
    if not iso.is_file() or not plain.is_file():
        return plain
    spec = importlib.util.spec_from_file_location("tf_isolation_work", iso)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.launch_settings(wt)


MODEL = re.compile(r"[A-Za-z][A-Za-z0-9.\[\]_-]{1,63}")   # an alias (sonnet, opus) or a model id


def agent_command(key: str, budget: str, mode: str, wt: Path | None = None, plugin_layout: bool = False,
                  model: str | None = None) -> list[str]:
    agent = shlex.split(os.environ.get("TF_WORK_AGENT") or "claude")
    plugin = []
    if wt is not None and plugin_layout:
        plugin = ["--plugin-dir", str(wt / ".tf" / "plugin"), "--settings", str(session_settings(wt))]
    # --permission-prompts none: nobody answers a prompt unattended, so it is denied and the run goes on (the guard hooks
    # and permission rules still apply); --output-format json: the run's cost (total_cost_usd) for the journal
    return [*agent, *plugin, "-p", f"/tf-task {key} --auto --budget {budget}", "--max-budget-usd", budget, "--permission-mode",
            mode, "--permission-prompts", "none", "--output-format", "json", *(["--model", model] if model else []),
            "--strict-mcp-config"]   # without --mcp-config: no MCP servers from the repository or from configuration


def agent_env() -> dict:
    """The agent's environment: variables from the allowed list and those the human named in `TF_WORK_ENV_ALLOW` of their
    environment (configuration from the repository cannot extend this list — it would arrive with someone else's PR)."""
    allow = set(ENV_ALLOW) | {x.strip() for x in (os.environ.get(ENV_EXTRA) or "").split(",") if x.strip()}
    return {k: v for k, v in os.environ.items() if k in allow or k.startswith(ENV_PREFIXES)}


def files_of(base: Path, rel: str) -> dict[str, str]:
    """Files of a control path (a file or directory) with their hash; a symlink gets a marker, not content."""
    import hashlib
    top = base / rel
    paths = [top] if top.is_file() or top.is_symlink() else (sorted(top.rglob("*")) if top.is_dir() else [])
    out = {}
    for f in paths:
        if "__pycache__" in f.parts or f.suffix == ".pyc" or (f.is_dir() and not f.is_symlink()):
            continue
        name = f.relative_to(base).as_posix()
        try:
            out[name] = (f"symlink:{os.readlink(f)}" if f.is_symlink() else
                         f"{hashlib.sha256(f.read_bytes()).hexdigest()}:{f.stat().st_mode & 0o111:o}")
        except OSError:
            out[name] = "unreadable"
    return out


def settings_paths(base: Path) -> set[str]:
    """Project files that the commands in settings point to (hooks, statusLine, apiKeyHelper…) and the quality gate command
    (`.claude/quality-gate.json`, e.g. `./verify.sh` from tf onboard): claude and the hooks execute them, so they belong to
    the control files. It takes every string from settings and every word of it that is a project file."""
    out: set[str] = set()

    def strings(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for v in x.values():
                yield from strings(v)
        elif isinstance(x, list):
            for v in x:
                yield from strings(v)

    for name in (".claude/settings.json", ".claude/settings.local.json", ".claude/quality-gate.json"):
        f = base / name
        try:
            if f.is_symlink() or not f.is_file() or f.stat().st_size > 1_000_000:
                continue                   # a symlink and a file of unnatural size reach the differences via files_of
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for text in strings(data):
            try:
                words = shlex.split(text)
            except ValueError:
                words = text.split()
            for w in words:
                w = re.sub(r"^\$\{?CLAUDE_PROJECT_DIR\}?/", "", w.strip("\"'"))
                if w and not w.startswith(("-", "/")) and ".." not in Path(w).parts and (base / w).is_file():
                    out.add(Path(w).as_posix())
    return out


def instruction_files(base: Path) -> set[str]:
    """Committed instruction files across the whole project (including nested module `CLAUDE.md` files)."""
    pats = [f":(glob)**/{n}" for n in INSTRUCTION_NAMES]
    out: set[str] = set()
    for extra in ([], ["-o", "--exclude-standard"]):          # committed and new, not ignored
        r = git(base, "ls-files", "-z", *extra, "--", *pats)
        out |= {p for p in r.stdout.split("\0") if p} if r.returncode == 0 else set()
    return out


def control_set(root: Path, wt: Path) -> list[str]:
    return sorted(set(CONTROL_FILES) | settings_paths(root) | settings_paths(wt) | instruction_files(root)
                  | instruction_files(wt))


def snapshot(base: Path, rels: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in rels:
        out.update(files_of(base, rel))
    return out


def control_drift(root: Path, wt: Path) -> list[str]:
    """Agent control files that differ in the worktree from the human's copy (absence on one side too)."""
    diff = [f"{d} (symlink)" for d in (".claude", ".tf") if (wt / d).is_symlink()]
    rels = control_set(root, wt)
    mine, theirs = snapshot(root, rels), snapshot(wt, rels)
    return diff + sorted(n for n in set(mine) | set(theirs) if mine.get(n) != theirs.get(n))


def budget_text(value) -> str | None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return f"{v:g}" if 0 < v <= MAX_RUN_USD else None


def money(value) -> float | None:
    """A non-negative finite amount, else None (a bool or a string is not an amount)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) and value >= 0 else None


def run_result(stdout: str) -> dict:
    """The result object of `claude -p --output-format json` (the whole output, or its last JSON line); {} without one."""
    text = (stdout or "").strip()
    for chunk in [text, *reversed(text.splitlines())]:
        try:
            data = json.loads(chunk)
        except ValueError:
            continue
        if isinstance(data, dict):
            return data
    return {}


def spent_detail(root: Path, key: str) -> tuple[float, bool]:
    """(spending of earlier task runs, whether any part is an estimate). A run counts with the cost Claude Code reported
    (`cost_usd` of its end entry, `cost_source: "claude"`); without it (an interrupted run, an older CLI, an old journal)
    with its limit (`budget_usd` of the start entry), an upper estimate."""
    try:
        lines = (root / LOG).read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0.0, False
    limits: dict[str, float] = {}
    reported: dict[str, float] = {}
    for i, line in enumerate(lines):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if not isinstance(e, dict) or e.get("key") != key:
            continue
        run = str(e.get("run") or f"#{i}")              # the start and end entries of one run share `run`
        if money(e.get("budget_usd")) is not None:
            limits[run] = money(e["budget_usd"])
        if e.get("cost_source") == "claude" and money(e.get("cost_usd")) is not None:
            reported[run] = money(e["cost_usd"])
    total = sum(reported.get(run, limit) for run, limit in limits.items())
    total += sum(cost for run, cost in reported.items() if run not in limits)
    return total, any(run not in reported for run in limits)


def spent(root: Path, key: str) -> float:
    return spent_detail(root, key)[0]


def write_log(root: Path, entry: dict) -> None:
    f = root / LOG
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as h:
        h.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_once(root: Path, key: str | None, budget_arg: str | None, base: str | None, dry: bool) -> int:
    cfg = config(root)
    budget = budget_text(budget_arg if budget_arg is not None else cfg.get("budget_usd"))
    if budget is None:
        print(f"✗ give a spending limit above 0 and up to {MAX_RUN_USD} USD: tf work --once --budget <USD> (or work.budget_usd "
              "in .tf/config/config.yaml). Unattended work does not start without a limit")
        return 2
    mode = str(cfg.get("permission_mode") or DEFAULTS["permission_mode"])
    if mode not in MODES:
        print(f"✗ work.permission_mode \"{clean(mode, 40)}\": unattended work allows only: {', '.join(MODES)}")
        return 2
    model = str(cfg.get("model") or "").strip() or None   # work.model: the session's model (empty: the CLI default)
    if model and not MODEL.fullmatch(model):
        print(f"✗ work.model \"{clean(model, 40)}\": give a model alias (sonnet, opus) or a model id")
        return 2
    if base is not None and (not base or base.startswith("-") or CONTROL.search(base)):
        print("✗ --base: give a branch name or a commit")
        return 2
    try:
        cap = float(cfg.get("task_budget_usd"))        # 0 — deliberately without a total limit
        cap = cap if cap >= 0 and cap == cap else float(DEFAULTS["task_budget_usd"])
    except (TypeError, ValueError):
        cap = float(DEFAULTS["task_budget_usd"])       # a broken value does not disable the limit
    if key:
        task = load_task(root, key) if KEY.fullmatch(key) else None
        if task is None:
            print(f"✗ no task {clean(key, 64)}")
            return 2
        why = refusal(root, task, key)
        if why:
            print(f"✗ {why}")
            return 2
        queue = [task]
    else:
        queue = candidates(root)
    for task in queue:
        k = task["key"]
        so_far, estimated = spent_detail(root, k)
        if cap and so_far + float(budget) > cap:
            msg = (f"{k}: total task limit work.task_budget_usd = {cap:g} USD. Earlier runs "
                   f"{so_far:g} USD{' (estimate: the limits of runs without a reported cost)' if estimated else ''} "
                   f"+ this run {budget} USD. A human decides on more spending")
            if key:
                print(f"✗ {msg}")
                return 2
            print(f"• {msg}")
            continue
        if dry:
            print(f"• task: {k} — {clean(task.get('title'))}")
            print(f"• worktree: {(root / WORKTREES / k).as_posix()} (branch story/{k.lower()} from {base or 'HEAD'})")
            print(f"• command: {shlex.join(agent_command(k, budget, mode, root / WORKTREES / k, has_plugin(root), model))}")
            return 0
        ok, note = claim(root, k, float(cfg.get("lock_hours") or 6))
        if not ok:
            continue
        if note:
            print(note)
        started, run_id = now(), uuid.uuid4().hex[:12]
        try:
            wt, info = prepare_worktree(root, k, base or "HEAD")
            if wt is None:
                print(f"✗ {k}: {info}")
                write_log(root, {"key": k, "started": started, "ended": now(), "exit": 2, "error": info})
                return 2
            if info:
                print(f"• {info}")
            drift = control_drift(root, wt)
            if drift:
                shown = ", ".join(drift[:12]) + (f" and {len(drift) - 12} more" if len(drift) > 12 else "")
                print(f"✗ {k}: agent control files in the worktree differ from your copy of the project: {shown}. Unattended, "
                      "the agent does not run another person's hook, instructions or MCP server. Review the differences (git diff "
                      f"in {wt.relative_to(root).as_posix()}), commit your changes, or remove the worktree and the task branch")
                write_log(root, {"key": k, "event": "refused", "started": started, "ended": now(), "exit": 2,
                                 "drift": drift[:50]})
                return 2
            watched = control_set(root, wt)
            before = snapshot(root, [*watched, ".git/hooks", ".git/config"])
            print(f"• {k}: /tf-task loop in {wt.as_posix()}, limit {budget} USD")
            write_log(root, {"key": k, "event": "start", "run": run_id, "started": started, "budget_usd": float(budget),
                             "worktree": wt.relative_to(root).as_posix()})   # before the agent: an interruption counts too
            out = ""
            try:
                proc = subprocess.run(agent_command(k, budget, mode, wt, has_plugin(wt), model), cwd=wt, env=agent_env(),
                                      stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                                      timeout=float(cfg.get("timeout_minutes") or 180) * 60)
                code, out = proc.returncode, proc.stdout or ""
            except FileNotFoundError:
                print("✗ the claude command (Claude Code) is not in PATH")
                code = 127
            except subprocess.TimeoutExpired as e:
                print(f"✗ {k}: run stopped after {cfg.get('timeout_minutes')} min")
                code = 124
                out = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            result = run_result(out)
            if isinstance(result.get("result"), str):
                print(result["result"].rstrip())
            elif out.strip() and not result:
                print(out.rstrip())                     # not JSON (an older CLI): the output as it came
            cost = money(result.get("total_cost_usd"))
            after = load_task(wt, k) or {}
            now_root = snapshot(root, [*sorted(set(watched) | instruction_files(root)), ".git/hooks", ".git/config"])
            changed = sorted(n for n in set(before) | set(now_root) if before.get(n) != now_root.get(n))
            if changed:
                print(f"⚠ {k}: control files in your copy of the project (outside the worktree) changed during the run: "
                      f"{', '.join(changed[:12])}. Review them before the next session (git diff)")
            entry = {"key": k, "event": "end", "run": run_id, "started": started, "ended": now(), "exit": code,
                     "stage": after.get("stage"), "worktree": wt.relative_to(root).as_posix(),
                     "cost_usd": cost if cost is not None else float(budget),
                     "cost_source": "claude" if cost is not None else "estimate",
                     **({"root_changed": changed[:50]} if changed else {})}
            write_log(root, entry)
            shown = (f"cost {cost:.2f} USD (reported by Claude Code)" if cost is not None else
                     f"cost up to {budget} USD (estimate: the run's limit — Claude Code reported no total_cost_usd)")
            print(f"{'✓' if code == 0 else '✗'} {k}: exit code {code}, stage {after.get('stage') or '?'}, {shown}. Result in "
                  f"{entry['worktree']} (tf status in the worktree). A human does the merge")
            return code
        finally:
            release(root, k)
    print("• no task to take. A task needs mode Auto (tf task mode <KEY> auto), weight light or normal, no worktree, "
          "and no lock" + (". All matching tasks are locked" if queue else ""))
    return 3


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tf work", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--once", action="store_true", help="one task, then stop (the only mode for now)")
    ap.add_argument("--key", default=None)
    ap.add_argument("--budget", default=None)
    ap.add_argument("--base", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv[1:])
    if not args.once:
        print("✗ usage: tf work --once --budget <USD> [--key <KEY>] [--base <branch>] [--dry-run]")
        return 2
    return run_once(Path.cwd(), args.key, args.budget, args.base, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
