#!/usr/bin/env python3
"""
PreToolUse (Read|Edit|Write|NotebookEdit|Grep|Glob): protects files with secrets
and the security configuration from being changed by the agent itself.

It also protects the task "oracle" (docs/project/changes/<KEY>/): a write with the Edit/Write tool requires human approval for
`spec.md` from the implementation stage on, a task file approved by a human, a frozen file (`tf task freeze`,
e.g. an acceptance test) and files written only by a script (task.json, INDEX.md, evidence/). Approval or
freezing is lifted by `tf task reopen <KEY> <file> --by human:<id> --reason "…"`. A closed task protects nothing.

It keeps agents out of the sweep archive (docs/project/archive/sweep/, the core-sweep skill): notes found no longer true.
Read and Edit/Write inside it are denied, and Grep/Glob only when their path or pattern points into it — a repo-wide search
is not blocked (the `.ignore` file in the archive keeps it out of ripgrep results). TF_ARCHIVE_READ=1 lifts the block.

It keeps the isolation level out of the agent's reach (plan docs/plans/2026-11-20-poziomy-izolacji.md, slice I3): an
Edit/Write that changes the `isolation` key of .tf/config/config.yaml, the `sandbox` key of .claude/settings*.json, or
writes the session settings (.tf/plugin|cache/session-settings.json) or the sandbox template is refused — a human changes
the level in a terminal (`tf isolation <level>`).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record_block  # block to .tf/logs/hook-blocks.jsonl (warning after an update)
except ImportError:  # older install without the block log — the hook works as before
    def record_block(hook: str, decision: str) -> None:
        return None

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SECRET_PATHS = re.compile(
    r"(^|/)(\.env(\.[\w-]+)?|id_rsa|id_ed25519|credentials(\.json)?|\.npmrc|\.pypirc|\.netrc|"
    r"[\w.-]+\.(pem|key|p12|pfx|jks|tfstate(\.backup)?)|secrets?(/|$)|"
    r"\.ssh/|\.aws/|\.kube/config|\.git-credentials|\.docker/config\.json|\.config/gh/hosts\.yml|\.config/gcloud/|\.azure/)",
    re.IGNORECASE,
)
SAFE_ENV = re.compile(r"\.env\.(example|sample|template|dist)$", re.IGNORECASE)

# Self-modification of the safeguards requires human approval
GUARDRAILS = re.compile(r"(^|/)\.claude/(settings(\.local)?\.json|hooks/|cleanroom\.json)|(^|/)\.git/")

# The isolation level: only a human lowers it (tf isolation in a terminal)
ISOLATION_FILES = re.compile(r"^\.tf/(cache|plugin)/session-settings\.json$|^\.tf/factory/templates/sandbox\.settings\.json$")
SETTINGS_FILES = re.compile(r"^\.claude/settings(\.local)?\.json$")
ISOLATION_CONFIG = ".tf/config/config.yaml"
ISOLATION_KEY = re.compile(r"^isolation\s*:\s*['\"]?([\w-]*)", re.M)
ISOLATION_MSG = ("The isolation level is changed by a human in a terminal (`tf isolation <level>`), not from inside a "
                 "session")


def after_edit(tool: str, ti: dict, current: str | None) -> str | None:
    """The file's text after this Edit/Write/MultiEdit, or None when it cannot be worked out."""
    if tool == "Write":
        return ti.get("content") if isinstance(ti.get("content"), str) else None
    if current is None:
        return None
    edits = ti.get("edits") if tool == "MultiEdit" else [ti]
    text = current
    for e in edits if isinstance(edits, list) else []:
        old, new = e.get("old_string"), e.get("new_string")
        if not isinstance(old, str) or not isinstance(new, str) or old not in text:
            return None
        text = text.replace(old, new) if e.get("replace_all") else text.replace(old, new, 1)
    return text


def sandbox_of(text: str | None):
    try:
        data = json.loads(text) if text is not None else None
    except ValueError:
        return "?"
    return data.get("sandbox") if isinstance(data, dict) else "?"


def isolation_reason(tool: str, rel: str, ti: dict, root: str) -> str | None:
    """Why this write lowers (or may lower) the isolation level, or None."""
    if ISOLATION_FILES.search(rel):
        return f"{rel} carries the session's isolation (the sandbox). {ISOLATION_MSG}."
    if rel != ISOLATION_CONFIG and not SETTINGS_FILES.search(rel):
        return None
    try:
        current = (Path(root) / rel).read_text(encoding="utf-8")
    except OSError:
        current = None
    new = after_edit(tool, ti, current)
    if rel == ISOLATION_CONFIG:
        before = ISOLATION_KEY.search(current or "")
        after = ISOLATION_KEY.search(new) if new is not None else None
        if new is None:
            changed = any("isolation" in str(v) for v in (ti.get("old_string"), ti.get("new_string"), ti.get("edits")))
        else:
            changed = (before.group(1) if before else None) != (after.group(1) if after else None)
        return f"the `isolation` key of {rel}. {ISOLATION_MSG}." if changed else None
    if new is None:
        changed = any("sandbox" in str(v) for v in (ti.get("old_string"), ti.get("new_string"), ti.get("edits")))
    else:
        changed = sandbox_of(current) != sandbox_of(new)
    return f"the `sandbox` key of {rel}. {ISOLATION_MSG}." if changed else None


# Context economy: dependencies, artifacts and lockfiles do not enter the model window. Here rather than in permissions.deny,
# because the Bash sandbox turns Read(...) deny rules into a read ban for programs (npm test, build).
CONTEXT_ANY = re.compile(r"(^|/)node_modules(/|$)")
CONTEXT_ROOT = re.compile(r"^(dist|build|coverage)(/|$)")
LOCKFILES = re.compile(r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock)$")
CONTEXT_TOOLS = ("Read", "Grep", "Glob")
SWEEP_ARCHIVE = re.compile(r"^(\./)?docs/project/archive/sweep(/|$)")
GLOB_INTO_ARCHIVE = re.compile(r"^(\*\*/)+(docs/project/)?archive/sweep(/|$)")
ARCHIVE_MSG = "archived — not current; read it only when the human asks; set TF_ARCHIVE_READ=1"


def project_relative(norm: str, root: str) -> str | None:
    """Path relative to the project directory; None when it lies outside it or the directory is unknown."""
    if not norm.startswith("/") and not re.match(r"^[A-Za-z]:/", norm):
        return norm[2:] if norm.startswith("./") else norm
    root = root.replace("\\", "/").rstrip("/")
    if root and norm.startswith(root + "/"):
        return norm[len(root) + 1:]
    return None


TASKS = "docs/project/changes"
TASK_FILE = re.compile(r"^docs/project/changes/(?:INDEX\.md|([^/]+)/(.+))$")
LOCKED_FROM = ("implementation", "review", "pr", "deploy")     # stages in which the specification is the oracle
CLOSED = "closed"


def load_task(root: str, key: str) -> dict:
    try:
        with open(os.path.join(root, TASKS, key, "task.json"), encoding="utf-8") as fh:
            task = json.load(fh)
    except (OSError, ValueError):
        return {}
    return task if isinstance(task, dict) else {}


def oracle_reason(rel: str, root: str) -> str | None:
    """The reason a write to the file requires human approval (the task oracle); None when the file is not protected."""
    m = TASK_FILE.match(rel)
    if m:
        key, name = m.group(1), m.group(2)
        if key is None or name == "task.json" or name.startswith("evidence/"):
            return (f"{rel} is written only by `tf task` (the task state, evidence, index) — use tf task commands instead of editing the file.")
        task = load_task(root, key)
        stage = task.get("stage")
        if not task or stage == CLOSED:
            return None
        art = (task.get("artifacts") or {}).get(name) or {}
        if art.get("status") == "approved":
            return (f"{rel} was approved by a human in task {key}. A change needs their decision: "
                    f"tf task reopen {key} {name} --by human:<id> --reason \"<reason>\".")
        if name == "spec.md" and stage in LOCKED_FROM:
            return (f"the spec of task {key} ({rel}) is, at the stage \"{stage}\", the basis of the tests and the plan. Changing "
                    f"it changes the requirements and needs a human's consent; after the change the plan must be refreshed.")
        return None
    tasks_dir = os.path.join(root, TASKS)
    try:
        keys = sorted(os.listdir(tasks_dir))
    except OSError:
        return None
    for key in keys:
        task = load_task(root, key)
        if task and task.get("stage") != CLOSED and rel in (task.get("frozen") or {}):
            return (f"{rel} is frozen in task {key} (e.g. an approved acceptance test). A change needs a human's "
                    f"decision: tf task reopen {key} {rel} --by human:<id> --reason \"<reason>\".")
    return None


def decide(decision: str, reason: str) -> None:
    if decision in ("deny", "ask"):
        record_block("guard_paths", decision)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": f"[guard_paths] {reason}",
    }}, ensure_ascii=False))
    sys.exit(0)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if not isinstance(data, dict):   # data outside the Claude Code format: a decision, not a failure (onFailure: block)
        sys.exit(0)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    path = ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""
    pattern = ti.get("pattern") or ""  # Glob/Grep
    targets = [p for p in (path, pattern if tool == "Glob" else "") if p and isinstance(p, str)]
    if not isinstance(data.get("cwd"), (str, type(None))):
        data["cwd"] = None

    for p in targets:
        norm = p.replace("\\", "/")
        if SECRET_PATHS.search(norm) and not SAFE_ENV.search(norm):
            decide("deny", f"Access to a file with secrets ({p}) is blocked. Use environment variables and *.example files.")
        if tool in ("Edit", "Write", "MultiEdit"):
            root = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "")
            rel = project_relative(norm, root)
            why = isolation_reason(tool, rel, ti, root or ".") if rel is not None else None
            if why:
                decide("deny", f"A change to {why}")
        if tool in ("Edit", "Write", "NotebookEdit") and GUARDRAILS.search(norm):
            decide("ask", f"A change to the safeguards' configuration or .git ({p}) needs a human's consent.")
        if tool in ("Edit", "Write", "NotebookEdit"):
            root = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "")
            rel = project_relative(norm, root)
            why = oracle_reason(rel, root or ".") if rel is not None else None
            if why:
                decide("ask", why)
        if os.environ.get("TF_ARCHIVE_READ") != "1" and tool in ("Read", "Edit", "Write", "NotebookEdit", "Grep", "Glob"):
            rel = project_relative(norm, data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", ""))
            if (rel is not None and SWEEP_ARCHIVE.search(rel)) or (p == pattern and GLOB_INTO_ARCHIVE.search(norm)):
                decide("deny", f"{p}: {ARCHIVE_MSG}.")
        if tool in CONTEXT_TOOLS:
            rel = project_relative(norm, data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", ""))
            if (CONTEXT_ANY.search(norm) or (rel is not None and CONTEXT_ROOT.search(rel))
                    or (tool == "Read" and LOCKFILES.search(norm))):
                decide("deny", f"Context economy: {p} is dependencies, a build artifact or a lockfile. Search for the specific "
                               "place (Grep in a source file, grep -n for the package name in the lockfile); when you really "
                               "need this file, ask a human.")
    sys.exit(0)


if __name__ == "__main__":
    main()
