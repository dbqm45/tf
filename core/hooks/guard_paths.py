#!/usr/bin/env python3
"""
PreToolUse (Read|Edit|Write|NotebookEdit|Grep|Glob): protects files with secrets
and the security configuration from being changed by the agent itself.

It also protects the task "oracle" (docs/project/changes/<KEY>/): a write with the Edit/Write tool requires human approval for
`spec.md` from the implementation stage on, a task file approved by a human, a frozen file (`tf task freeze`,
e.g. an acceptance test) and files written only by a script (task.json, INDEX.md, evidence/). Approval or
freezing is lifted by `tf task reopen <KEY> <file> --by human:<id> --reason "…"`. A closed task protects nothing.
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

# Context economy: dependencies, artifacts and lockfiles do not enter the model window. Here rather than in permissions.deny,
# because the Bash sandbox turns Read(...) deny rules into a read ban for programs (npm test, build).
CONTEXT_ANY = re.compile(r"(^|/)node_modules(/|$)")
CONTEXT_ROOT = re.compile(r"^(dist|build|coverage)(/|$)")
LOCKFILES = re.compile(r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock)$")
CONTEXT_TOOLS = ("Read", "Grep", "Glob")


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
        if tool in ("Edit", "Write", "NotebookEdit") and GUARDRAILS.search(norm):
            decide("ask", f"A change to the safeguards' configuration or .git ({p}) needs a human's consent.")
        if tool in ("Edit", "Write", "NotebookEdit"):
            root = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "")
            rel = project_relative(norm, root)
            why = oracle_reason(rel, root or ".") if rel is not None else None
            if why:
                decide("ask", why)
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
