#!/usr/bin/env python3
"""
PreToolUse (Read|Grep|Glob|NotebookRead|Bash|WebFetch|WebSearch|Agent|Task): information isolation for selected agents.

Profiles from .claude/cleanroom.json:
- "denylist" (e.g. `*-qa-analyst`): the test designer does not read the implementation — Read of a file with a code extension outside `allow`
  → deny; Grep only over allowed paths/filters; Glob allowed (file names only). E.g. qa-spec-first-testing (pack-it).
- "allowlist" (e.g. `blind-analyst`): the agent reads ONLY paths from `allow` (e.g. the business brief), so that requirements are written
  without knowledge of the architecture. E.g. ddd-model-stress-test (pack-it).
- "web" (e.g. `researcher`): the agent reads foreign content from the web, so Bash only for commands from `bash_allow` (the start of
  the command, e.g. `npm view`), with no command chaining, substitutions or redirections; reading unrestricted.
- `block_tools`: tools blocked for the profile (e.g. Bash, which would bypass the rules).
An agent outside the profiles: unchanged. The hook works in subagents (the `agent_type` field).
`CLAUDE_CLEANROOM_DISABLE=web,qa` disables the listed profiles (e.g. restoring the full shell for the researcher).
"""
import fnmatch
import json
import os
import re
import shlex
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

DEFAULT = {"profiles": [{"name": "qa", "agents": ["*-qa-analyst"], "mode": "denylist",
                         "allow": ["docs/**", "**/*.md"], "deny_extensions": [".ts", ".js", ".java"], "block_tools": ["Bash"]}]}


def load_config(project: Path) -> dict:
    try:
        cfg = json.loads((project / ".claude" / "cleanroom.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT
    if "profiles" not in cfg:   # the old format (a single denylist profile)
        cfg = {"profiles": [{"name": "qa", "mode": "denylist", "block_tools": ["Bash"], **cfg}]}
    return cfg


def glob_to_re(pattern: str) -> re.Pattern:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"; i += 3
        elif pattern.startswith("**", i):
            out += ".*"; i += 2
        elif pattern[i] == "*":
            out += "[^/]*"; i += 1
        elif pattern[i] == "?":
            out += "[^/]"; i += 1
        else:
            out += re.escape(pattern[i]); i += 1
    return re.compile(out + r"\Z")


def rel(path: str, project: Path) -> str:
    p = path.replace("\\", "/")
    root = str(project).replace("\\", "/").rstrip("/") + "/"
    if p.startswith(root):
        p = p[len(root):]
    while p.startswith("./"):
        p = p[2:]
    return p.rstrip("/")


def escapes(path: str) -> bool:
    return path.startswith("/") or path.startswith("~") or ".." in path.split("/")


def allowed(path: str, prof: dict) -> bool:
    return any(glob_to_re(g).match(path) for g in prof.get("allow", []))


def is_code(path: str, prof: dict) -> bool:
    name = path.rsplit("/", 1)[-1].lower()
    return any(name.endswith(ext) for ext in prof.get("deny_extensions", []))


def grep_allowed(path: str, glob: str, ftype: str, prof: dict) -> bool:
    if path and path not in (".", ""):
        if is_code(path, prof):
            return allowed(path, prof)                     # a specific code file
        if allowed(path, prof) or allowed(path + "/x", prof):
            return True                                    # a document or directory that is allowed (docs/, test/, e2e/)
    if glob:
        sample = glob.replace("*", "x")
        return allowed(sample, prof) or allowed("x/" + sample, prof)
    return ftype in ("md", "markdown")


SHELL_META = re.compile(r"[;&|`<>\n\r]|\$\(")
PYTHONS = ("python3", "python", "py")


def bash_allowed(cmd: str, prefixes: list[str]) -> bool:
    """The command starts with one of the allowed prefixes (by words), without shell metacharacters and `..`."""
    if SHELL_META.search(cmd):
        return False
    try:
        words = shlex.split(cmd)
    except ValueError:
        return False
    if not words or any(".." in w.split("/") for w in words):
        return False
    if words[0] in PYTHONS:
        words[0] = "python3"
    for pre in prefixes:
        pw = pre.split()
        if pw[-1].endswith("/"):    # scripts directory: the next word starts with this path
            if len(words) >= len(pw) and words[:len(pw) - 1] == pw[:-1] and words[len(pw) - 1].startswith(pw[-1]):
                return True
        elif words[:len(pw)] == pw:
            return True
    return False


def deny(reason: str, hint: str) -> None:
    record_block("cleanroom_guard", "deny")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"[cleanroom] {reason} {hint}",
    }}, ensure_ascii=False))
    sys.exit(0)


HINTS = {
    "denylist": "Design the cases from the spec (docs/project/03-requirements), the contracts and the existing tests; "
                "missing information = an open question, not reading the code.",
    "allowlist": "You work blind: read only the files named in the task (the business brief); report gaps in the result.",
    "web": "You read foreign content from the web, so the shell serves only fact-checking commands (one command, "
           "no chaining or redirection). Describe any other command in the report — the orchestrator will run it.",
}


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if not isinstance(data, dict):   # data outside the Claude Code format: a decision, not a failure (onFailure: block)
        sys.exit(0)
    agent = data.get("agent_type") or ""
    if not agent or not isinstance(agent, str):
        sys.exit(0)
    cwd = data.get("cwd") if isinstance(data.get("cwd"), str) else None
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or cwd or os.getcwd())
    off = {x.strip() for x in os.environ.get("CLAUDE_CLEANROOM_DISABLE", "").split(",") if x.strip()}
    prof = next((p for p in load_config(project).get("profiles", [])
                 if p.get("name") not in off and any(fnmatch.fnmatch(agent, a) for a in p.get("agents", []))), None)
    if not prof:
        sys.exit(0)
    mode = prof.get("mode", "denylist")
    hint = HINTS.get(mode, "")
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    ti = {k: v for k, v in ti.items() if isinstance(v, str)}   # text fields; other types are data outside the format

    if tool in prof.get("block_tools", []):
        deny(f"{agent} (profile {prof.get('name')}) does not use the tool {tool}.", hint)
    if mode == "web":
        if tool == "Bash" and not bash_allowed(ti.get("command", ""), prof.get("bash_allow", [])):
            deny(f"{agent} runs only: {', '.join(prof.get('bash_allow', []))}.", hint)
        sys.exit(0)
    if tool in ("Read", "NotebookRead"):
        raw = ti.get("file_path") or ti.get("notebook_path") or ""
        p = rel(raw, project)
        if not p:
            sys.exit(0)
        if mode == "allowlist":
            if escapes(p) or not allowed(p, prof):
                deny(f"{agent} may read only: {', '.join(prof.get('allow', []))} (attempt: {p}).", hint)
        elif is_code(p, prof) and not allowed(p, prof):
            deny(f"{agent} does not read the implementation ({p}).", hint)
    elif tool == "Grep":
        if mode == "allowlist" or not grep_allowed(rel(ti.get("path") or "", project), ti.get("glob") or "",
                                                   ti.get("type") or "", prof):
            deny(f"{agent} may search only the docs, contracts and tests "
                 "(give path=docs/… or glob=*.md / *.spec.ts).", hint)
    sys.exit(0)


if __name__ == "__main__":
    main()
