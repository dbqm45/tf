#!/usr/bin/env python3
"""
TDD gate: production code only after a red test. Standard library only; a hook error never blocks.

A red run after a test edit leaves a durable entry in `.tf/logs/tdd-red.jsonl` (test files, time) — from it
`tf task verify` and `tf trace` take the answer to "was the test red before the code".
It tracks each context separately (the main session and each subagent) in `.tf/logs/tdd-state.json`:
  - PostToolUse Edit|Write   — a test file edit;
  - PostToolUse / PostToolUseFailure Bash — a test run and its result (red / green);
  - PreToolUse Edit|Write    — a production file edit: checks the rule.

Rules:
  A. The first production code edit in a given context requires: a test edit, and AFTER it a run of tests that
     did NOT pass (a red test — proof that the test checks the missing behavior). A test that passed right away
     proves nothing — exception: a characterization test before refactoring, marked in the test file with the word
     „charakteryz…”/„characteriz…” (e.g. qa-spec-first-testing in pack-it).
  B. Later: after CLAUDE_TDD_MAX_EDITS (default 12) production code edits without a new test edit — the next
     behavior requires the next test.
  C. Weakening a test: a test file edit that reduces the number of assertions or tests, or adds a skip
     (skip, xfail, @Disabled, xit…). Mode CLAUDE_TDD_WEAKEN: warn (default: a warning for the human and context for the model, no block),
     ask (the human decides), deny (block), off. Moving assertions while refactoring tests also triggers the rule —
     that is why by default it only warns.
  D. A write through the shell: before execution guard_bash applies rule A/B to write targets (`>`, tee, sed -i, cp/mv…);
     after Bash runs, a `git status` snapshot (timeout 1.5 s, once exceeded disabled until the end of the session; paths only,
     mtime and size, no content) reports a production file changed without a red test (e.g. a script from a file).
     CLAUDE_TDD_BASH=off disables both checks.
  E. Loop: the same test failure (a sha1 digest of the test ids and the exception type) LOOP_AT times in a row → the context
     "change approach or escalate the model", no block; a green result or a different failure resets the counter.
  F. Protected files: after each Bash, a snapshot (path, mtime, size — no content) of `.claude/settings*.json`,
     `.claude/cleanroom.json`, `.claude/hooks/`, `.git/hooks/`, `.git/config` and files with secrets in the root directory
     (guard_paths patterns) → a change = the context "stop and tell the human" + a message for the human. It works
     also with CLAUDE_TDD=off; CLAUDE_GUARD_CHANGES=off disables it. It detects after the fact and does not prevent (the Bash sandbox
     does that); a change by the Edit/Write tool (which passed guard_paths) and a single `git …` on `.git/config` do not alarm.

Mode (environment variable CLAUDE_TDD): strict (default: a block with an explanation for the agent), ask (the human decides),
off (disabled — e.g. a spike, a prototype). Files not covered: tests, configuration, styles and templates, documentation, `.claude/`,
`.tf/factory/`, generated directories; extra patterns in CLAUDE_TDD_EXEMPT (comma-separated, e.g. "src/migrations/*").
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record as record_error  # hook error to .tf/logs/hook-errors.jsonl (tf doctor)
except ImportError:  # older install without the log module — the hook works as before
    def record_error(hook: str, exc: BaseException) -> None:
        return None
try:
    from hook_errors import record_block  # block to .tf/logs/hook-blocks.jsonl (warning after an update)
except ImportError:
    def record_block(hook: str, decision: str) -> None:
        return None

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".java", ".kt", ".go", ".rs", ".cs", ".rb", ".php",
              ".swift", ".scala"}
TEST_RE = re.compile(
    r"(\.(test|spec)\.[cm]?[jt]sx?$)|(/__tests__/)|(/(tests?|e2e|spec)/)|((^|/)test_[^/]+\.py$)|(_test\.(py|go)$)"
    r"|(/src/test/)|((Test|Tests|IT|Spec)\.(java|kt|cs|scala)$)|(_spec\.rb$)|(\.feature$)|(Test\.php$)", re.I)
EXEMPT_RE = re.compile(
    r"(^|/)(\.claude|factory|docs|node_modules|dist|build|out|coverage|target|vendor|\.git|generated|__generated__)/"
    r"|\.d\.ts$|(^|/)[^/]*\.config\.[cm]?[jt]s$|(^|/)(setup|conftest|manage)\.py$|(^|/)__init__\.py$", re.I)
TEST_CMD_RE = re.compile(
    r"\b((npm|pnpm|yarn|bun)( run)? (test|test:\S+)|npx (vitest|jest|playwright test|mocha)|vitest|jest|mocha"
    r"|pytest|python3? -m (pytest|unittest)|mvnw? (\S+ )*(test|verify)|gradlew? (\S+ )*test|go test|cargo test"
    r"|dotnet test|nx (test|run-many|affected)\b[^\n]*test|ng test|deno test|rspec|phpunit|tox)\b"
    # Tests as standalone scripts: python3 tests/test_x.py, py -3 .claude\tests\test_x.py, a loop over tests/test_*.py.
    r"|\b(python3?|py)(\s+-\S+)*\s+[\"']?([^\s\"';|&]*[/\\])?(test_[^\s/\\\"';|&]*|[^\s/\\\"';|&]+_test)\.py\b"
    r"|\bfor\s+\w+\s+in\s+[^;\n]*\btest_\*[^;\n]*\.py\b")
FAIL_RE = re.compile(r"\b(FAIL(ED)?|failing|failures?: [1-9]|[1-9]\d* (failed|failing)|AssertionError|"
                     r"Tests?:\s+[1-9]\d* failed|BUILD FAILURE)\b|[✗×] ", re.I)
MARK_RE = re.compile(r"charakteryz|characteriz", re.I)
ASSERT_RE = re.compile(r"\bassert\w*\b|\bexpect\s*\(|\bshould\b|\bverify\s*\(|\bpytest\.raises\b|\bassertThat\b")
TESTDEF_RE = re.compile(r"^\s*(async\s+)?def\s+test\w*|\b(it|test)\s*\(|@(Test|ParameterizedTest)\b|^\s*func\s+Test\w+",
                        re.M)
SKIP_RE = re.compile(r"\.(skip|todo)\s*\(|\b(xit|xdescribe|xtest)\s*\(|@pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\s*\("
                     r"|@(Disabled|Ignore)\b|\bt\.Skip\s*\(|@unittest\.skip", re.M)


def root_of(data: dict) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".")


def rel(path: str, root: Path) -> str:
    p = path.replace("\\", "/")
    r = str(root).replace("\\", "/").rstrip("/") + "/"
    return p[len(r):] if p.startswith(r) else p


def is_test(path: str) -> bool:
    return bool(TEST_RE.search("/" + path))


def is_production(path: str) -> bool:
    if Path(path).suffix.lower() not in SOURCE_EXT or is_test(path) or EXEMPT_RE.search("/" + path):
        return False
    extra = [g.strip() for g in os.environ.get("CLAUDE_TDD_EXEMPT", "").split(",") if g.strip()]
    return not any(fnmatch.fnmatch(path, g) for g in extra)


def load(root: Path) -> dict:
    try:
        return json.loads((root / ".tf" / "logs" / "tdd-state.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save(root: Path, state: dict) -> None:
    p = root / ".tf" / "logs" / "tdd-state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(list(state.items())[-100:]), ensure_ascii=False), encoding="utf-8")


def ctx_key(data: dict) -> str:
    return f"{data.get('session_id') or '?'}:{data.get('agent_id') or 'main'}"


ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
# A "red" that executed no assertion (no test files, a syntax error in the test, a bad runner configuration).
INVALID_RED_RE = re.compile(
    r"No test files found|No tests found|no tests ran|collected 0 items|\b0 tests? (?:passed|ran|run)\b|"
    r"No tests were executed|Transform failed with \d+ error|\[PARSE_ERROR\]|Your test suite must contain at least one test|"
    r"^(?:E\s+)?\s*(?:SyntaxError|ParseError|IndentationError)\b|"
    r"\.(?:test|spec)\.[cm]?[jt]sx?\(\d+,\d+\): error TS\d+|"
    r"Cannot find module '[^']*\.(?:test|spec)(?:\.[cm]?[jt]sx?)?'", re.I | re.M)
# A missing module or function under test is a valid red ("it does not exist yet").
VALID_MISSING_RE = re.compile(
    r"Cannot find module '(?![^']*\.(?:test|spec)\b)[^']+'|"
    r"Failed to (?:load|resolve) (?:url|import) [\"']?(?![^\s\"']*\.(?:test|spec)\.)[^\s\"']+|"
    r"No module named '(?![^']*test)[^']+'|cannot import name '[^']+'", re.I)


def response_text(data: dict) -> str:
    resp = data.get("tool_response")
    if isinstance(resp, dict):
        text = f"{resp.get('stdout', '')}\n{resp.get('stderr', '')}\n{resp.get('output', '')}"
    else:
        text = str(resp or "")
    return ANSI_RE.sub("", text[-20000:])


def red_without_assertion(data: dict) -> bool:
    text = response_text(data)
    return bool(INVALID_RED_RE.search(text)) and not VALID_MISSING_RE.search(text)


def bash_failed(data: dict) -> bool:
    if data.get("hook_event_name") == "PostToolUseFailure":
        return True
    resp = data.get("tool_response")
    if isinstance(resp, dict):
        code = resp.get("exit_code", resp.get("exitCode", resp.get("returncode")))
        if isinstance(code, int) and code != 0:
            return True
        text = f"{resp.get('stdout', '')}\n{resp.get('stderr', '')}\n{resp.get('output', '')}"
    else:
        text = str(resp or "")
    return bool(FAIL_RE.search(text[-20000:]))


def deny(reason: str) -> None:
    mode = os.environ.get("CLAUDE_TDD", "strict").lower()
    record_block("tdd_guard", "ask" if mode == "ask" else "deny")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "ask" if mode == "ask" else "deny",
                                             "permissionDecisionReason": reason}}, ensure_ascii=False))


def weakening(tool: str, inp: dict, root: Path, path: str) -> list[str]:
    """What weakens a test in this edit: fewer assertions, fewer tests, a new skip."""
    pairs: list[tuple[str, str]] = []
    if tool == "Edit":
        pairs = [(str(inp.get("old_string") or ""), str(inp.get("new_string") or ""))]
    elif tool == "MultiEdit":
        pairs = [(str(e.get("old_string") or ""), str(e.get("new_string") or "")) for e in inp.get("edits") or []]
    elif tool == "Write":
        try:
            pairs = [((root / path).read_text(encoding="utf-8", errors="ignore"), str(inp.get("content") or ""))]
        except OSError:
            return []
    old = "\n".join(a for a, _ in pairs)
    new = "\n".join(b for _, b in pairs)
    found = []
    if len(ASSERT_RE.findall(new)) < len(ASSERT_RE.findall(old)):
        found.append(f"fewer assertions ({len(ASSERT_RE.findall(old))} → {len(ASSERT_RE.findall(new))})")
    if len(TESTDEF_RE.findall(new)) < len(TESTDEF_RE.findall(old)):
        found.append("a removed test")
    if len(SKIP_RE.findall(new)) > len(SKIP_RE.findall(old)):
        found.append("an added test skip (skip/xfail/disabled)")
    return found


def weaken_check(tool: str, inp: dict, root: Path, path: str) -> None:
    mode = os.environ.get("CLAUDE_TDD_WEAKEN", "warn").lower()
    if mode == "off":
        return
    found = weakening(tool, inp, root, path)
    if not found:
        return
    reason = (f"TDD: this edit may weaken the test {path}: {', '.join(found)}. You do not weaken tests to make them pass — "
              "fix the code or justify the test change (a changed requirement, a test refactor without losing checks).")
    if mode in ("ask", "deny"):
        record_block("tdd_guard", mode)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": mode,
                                                 "permissionDecisionReason": reason}}, ensure_ascii=False))
    else:   # warn: a warning for the human and context for the model, with no permission decision
        print(json.dumps({"systemMessage": reason,
                          "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": reason}},
                         ensure_ascii=False))


def log_red(root: Path, tests: list, command: str) -> None:
    """A durable "these tests were red" entry (`.tf/logs/tdd-red.jsonl`): after a test edit the run did not pass on
    assertions. `tf task verify` moves the slice's file entries into the evidence, and `tf trace` shows them in the criterion trace."""
    import datetime as dt
    p = root / ".tf" / "logs" / "tdd-red.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    row = {"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "tests": tests, "command": command[:200]}
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def ctx_state(state: dict, key: str) -> dict:
    s = state.setdefault(key, {"seq": 0, "test_edit": -1, "red": -1, "green": -1, "prod_since_test": 0,
                               "started": False, "marked": False, "green_warned": False})
    s["seq"] += 1
    return s


def may_start(s: dict) -> bool:
    """Rule A satisfied: red after a test edit, or green for a marked characterization test."""
    red_after_test = s["test_edit"] >= 0 and s["red"] > s["test_edit"]
    green_after_test = s["test_edit"] >= 0 and s["green"] > s["test_edit"] and s["red"] < s["test_edit"]
    return red_after_test or (green_after_test and s["marked"])


def gate(s: dict, path: str) -> str | None:
    """Rules A and B for a production file change (Edit or a write through Bash); None = allowed."""
    if not s["started"]:
        if may_start(s):
            s["started"] = True
            return None
        green_after_test = s["test_edit"] >= 0 and s["green"] > s["test_edit"] and s["red"] < s["test_edit"]
        if green_after_test and not s["green_warned"]:
            s["green_warned"] = True
            return ("TDD: the new test PASSED at once, so it proves nothing. Fix the test so that it checks "
                    "the missing behaviour and fails (red for the right reason), run it, and only "
                    "then write the code. If it is a characterization test before a refactor, mark it in the test file "
                    "as [characterization].")
        return (f"TDD: before you change production code ({path}), write a test describing the expected behaviour "
                "(for a bug: a test reproducing the bug), run the tests and show that this test does NOT pass "
                "for the right reason. Then minimal code → green → refactor. Exceptions: "
                "configuration, styles, docs; a spike — a human sets CLAUDE_TDD=off.")
    limit = int(os.environ.get("CLAUDE_TDD_MAX_EDITS", "12") or 12)
    if s["prod_since_test"] >= limit:
        return (f"TDD: {s['prod_since_test']} production code changes without a new test. The next behaviour = "
                "the next test: add a test (red), then the code. If it is only a refactor with green "
                "tests, run the tests and add/update the test that guards it.")
    return None


def bash_pre(data: dict, paths: list[str]) -> str | None:
    """For guard_bash: writing production files through a shell command is subject to the same rules as Edit."""
    if os.environ.get("CLAUDE_TDD", "strict").lower() == "off" or not paths:
        return None
    root = root_of(data)
    state = load(root)
    s = ctx_state(state, ctx_key(data))
    reason = gate(s, paths[0])
    s["ts"] = int(time.time())
    save(root, state)
    return reason


SNAP_MAX = 300   # we track this many production files changed at once in the working tree; more → the check is disabled


def bash_changes(root: Path, state: dict, data: dict) -> list[str]:
    """Production files changed since the previous command (git status + mtime and size, no content).
    The first call in a session only records the baseline state. Timeout or no git → disabled until the end of the session."""
    if not (root / ".git").exists():
        return []
    snap = state.setdefault("snap:" + str(data.get("session_id") or "?"), {})
    if snap.get("off"):
        return []
    try:
        out = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all", "-z"],
                             capture_output=True, timeout=1.5).stdout.decode("utf-8", "replace")
    except (OSError, subprocess.SubprocessError):
        snap["off"] = True
        return []
    entries, cur = out.split("\0"), {}
    skip = False
    for e in entries:
        if skip:
            skip = False
            continue
        if len(e) < 4:
            continue
        skip = e[0] in "RC"   # on a rename the next entry is the old path
        path = e[3:]
        if is_production(path):
            try:
                st = (root / path).stat()
                cur[path] = [st.st_mtime_ns, st.st_size]
            except OSError:
                pass
    if len(cur) > SNAP_MAX:
        snap.clear()
        snap["off"] = True
        return []
    prev = snap.get("files")
    snap["files"] = cur
    if not isinstance(prev, dict):
        return []
    return sorted(p for p, v in cur.items() if prev.get(p) != v)


GUARD_FILES = (".claude/settings.json", ".claude/settings.local.json", ".claude/cleanroom.json", ".git/config")
GUARD_DIRS = (".claude/hooks", ".git/hooks")
GUARD_MAX = 200   # we track at most this many protected files (stat, no content)
GIT_ONLY_RE = re.compile(r"^\s*git\s[^;&|`$()<>\n]*$")


def _secret_res():
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_guard_paths", Path(__file__).with_name("guard_paths.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.SECRET_PATHS, mod.SAFE_ENV
    except Exception:
        return (re.compile(r"(^|/)\.env(\.[\w-]+)?$|\.(pem|key)$", re.I),
                re.compile(r"\.env\.(example|sample|template|dist)$", re.I))


def guarded_snapshot(root: Path) -> dict:
    """Path → [mtime_ns, size] of protected files and files with secrets in the root directory; does not read content."""
    paths = [root / f for f in GUARD_FILES]
    for d in GUARD_DIRS:
        try:
            for dirpath, dirs, files in os.walk(root / d):
                dirs[:] = [x for x in dirs if x != "__pycache__"]
                paths += [Path(dirpath) / f for f in files if not f.endswith(".sample")]
        except OSError:
            pass
    secret, safe = _secret_res()
    try:
        paths += [e for e in root.iterdir() if secret.search(e.name) and not safe.search(e.name)]
    except OSError:
        pass
    cur = {}
    for p in paths[:GUARD_MAX]:
        try:
            st = p.stat()
            if p.is_file():
                cur[p.relative_to(root).as_posix()] = [st.st_mtime_ns, st.st_size]
        except (OSError, ValueError):
            pass
    return cur


def guard_changes(root: Path, state: dict, data: dict) -> list[str]:
    """Rule F: protected files and files with secrets changed since the previous command. The first call in a session only
    records the baseline state; a single `git …` command may change `.git/config` (push -u, branch)."""
    key = "guard:" + str(data.get("session_id") or "?")
    prev, cur = state.get(key), guarded_snapshot(root)
    state[key] = cur
    if not isinstance(prev, dict):
        return []
    changed = []
    for p in sorted(set(prev) | set(cur)):
        if prev.get(p) == cur.get(p):
            continue
        if p == ".git/config" and GIT_ONLY_RE.match(str((data.get("tool_input") or {}).get("command") or "")):
            continue
        changed.append(f"{p} ({'new' if p not in prev else 'deleted' if p not in cur else 'changed'})")
    return changed


def guard_note(root: Path, state: dict, data: dict) -> dict:
    """Output of rule F (context for the model and a message for the human) or {}; paths only, no content."""
    if os.environ.get("CLAUDE_GUARD_CHANGES", "on").lower() == "off":
        return {}
    event, tool = data.get("hook_event_name"), data.get("tool_name") or ""
    if event == "PostToolUse" and tool in ("Edit", "Write", "MultiEdit"):
        key = "guard:" + str(data.get("session_id") or "?")
        if isinstance(state.get(key), dict):   # a change by the tool passed guard_paths — a new baseline state
            state[key] = guarded_snapshot(root)
        return {}
    if not (event in ("PostToolUse", "PostToolUseFailure") and tool == "Bash"):
        return {}
    changed = guard_changes(root, state, data)
    if not changed:
        return {}
    names = ", ".join(changed[:8])
    return {"context": (f"[tdd_guard] A command changed protected files or files with secrets: {names}. Stop and "
                        "tell a human what changed them and why; do not read their content and do not undo a human's "
                        "changes (core-agent-security)."),
            "human": f"⚠ tdd_guard: a Bash command changed protected files: {names} — check whether that was intended."}


FAIL_ID_RES = [
    re.compile(r"^FAILED (\S+::\S+)", re.M),                                                    # pytest
    re.compile(r"^\s*(?:FAIL|×|✗)\s+(\S+\.(?:test|spec)\.\S+(?:\s+>\s+.+?)?)\s*$", re.M),       # vitest
    re.compile(r"^\s*● (.+?)\s*$", re.M),                                                         # jest
    re.compile(r"--- FAIL: (\S+)"),                                                              # go
]
EXC_RE = re.compile(r"\b([A-Z]\w*(?:Error|Exception|Failure))\b")
LOOP_AT = 3


def same_failure(s: dict, text: str) -> str:
    """Failure fingerprint = a digest (ids of failing tests + exception types); only the digest is kept in the state. Every LOOP_AT repetitions
    of the same fingerprint in a row → a hint to change approach (no block)."""
    ids = sorted({m for r in FAIL_ID_RES for m in r.findall(text)})
    exc = sorted(set(EXC_RE.findall(text)))
    if not ids and not exc:
        s["fail_fp"], s["fail_n"] = None, 0
        return ""
    fp = hashlib.sha1("\n".join(ids + ["--"] + exc).encode("utf-8")).hexdigest()[:12]
    s["fail_n"] = s.get("fail_n", 0) + 1 if s.get("fail_fp") == fp else 1
    s["fail_fp"] = fp
    if s["fail_n"] % LOOP_AT:
        return ""
    return (f"[tdd_guard] The same failure {s['fail_n']} times in a row (the same test and error type) — change the approach "
            "or escalate the model (core-cost-control): name what did not work, check the assumption about the cause, "
            "instead of another similar fix.")


def emit(event: str, notes: list[str], guard: dict) -> None:
    notes = [n for n in notes + [guard.get("context", "")] if n]
    if notes:
        out = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": "\n".join(notes)}}
        if guard.get("human"):
            out["systemMessage"] = guard["human"]
        print(json.dumps(out, ensure_ascii=False))


def main() -> int:
    try:
        data = json.load(sys.stdin)
        root = root_of(data)
        event = data.get("hook_event_name")
        state = load(root)
        guard = guard_note(root, state, data)   # rule F also works with CLAUDE_TDD=off
    except Exception as e:  # the hook does not interrupt the session; the error goes to the log
        record_error("tdd_guard", e)
        return 0
    if os.environ.get("CLAUDE_TDD", "strict").lower() == "off":
        try:
            if str(event).startswith("PostToolUse"):
                emit(event, [], guard)
                save(root, state)
        except Exception as e:  # the hook does not interrupt the session; the error goes to the log
            record_error("tdd_guard", e)
        return 0
    try:
        tool = data.get("tool_name") or ""
        inp = data.get("tool_input") or {}
        key = ctx_key(data)
        s = ctx_state(state, key)
        path = rel(str(inp.get("file_path") or inp.get("notebook_path") or ""), root)

        if event in ("PostToolUse", "PostToolUseFailure") and tool == "Bash":
            notes = []
            if TEST_CMD_RE.search(str(inp.get("command") or "")):
                if bash_failed(data):
                    s["red"] = s["seq"]
                    if not red_without_assertion(data) and s.get("tests"):
                        log_red(root, s.pop("tests"), str(inp.get("command") or ""))
                    if red_without_assertion(data):
                        notes.append("[tdd_guard] This run executed no assertions (no test files, a syntax error "
                                     "or a runner configuration error) — that is not a red test. Fix "
                                     "the run and see a test failing on the missing behaviour before you write "
                                     "production code.")
                    notes.append(same_failure(s, response_text(data)))
                else:
                    s["green"] = s["seq"]
                    s["fail_fp"], s["fail_n"] = None, 0
                    s.pop("tests", None)
            if os.environ.get("CLAUDE_TDD_BASH", "on").lower() != "off":
                changed = bash_changes(root, state, data)
                if changed and not (s["started"] or may_start(s)):
                    notes.append(f"[tdd_guard] TDD: a command changed production code without a red test: "
                                 f"{', '.join(changed[:5])}. If the change came from this command, undo it or first "
                                 "write a test and show that it fails. Do not undo a human's changes.")
            emit(event, notes, guard)
        elif event == "PostToolUse" and tool in ("Edit", "Write", "MultiEdit") and path:
            if is_test(path):
                s["test_edit"], s["prod_since_test"] = s["seq"], 0
                s["tests"] = ([t for t in s.get("tests", []) if t != path] + [path])[-20:]   # for the red-test entry
                try:
                    s["marked"] = s["marked"] or bool(MARK_RE.search((root / path).read_text(encoding="utf-8",
                                                                                                errors="ignore")))
                except OSError:
                    pass
            elif is_production(path):
                s["prod_since_test"] += 1
                snap = state.get("snap:" + str(data.get("session_id") or "?"))
                if isinstance(snap, dict) and isinstance(snap.get("files"), dict):   # a change by Edit passed the gate
                    try:
                        st = (root / path).stat()
                        snap["files"][path] = [st.st_mtime_ns, st.st_size]
                    except OSError:
                        snap["files"].pop(path, None)
        elif event == "PreToolUse" and tool in ("Edit", "Write", "MultiEdit") and path and is_test(path):
            weaken_check(tool, inp, root, path)
            return 0
        elif event == "PreToolUse" and tool in ("Edit", "Write", "MultiEdit") and path and is_production(path):
            reason = gate(s, path)
            if reason:
                deny(reason)
                save(root, state)
                return 0
        s["ts"] = int(time.time())
        save(root, state)
    except Exception as e:  # a guard error does not block the edit (a false block would be worse), but in this
        record_error("tdd_guard", e)  # call TDD was not checked — the log and tf doctor show this
    return 0


if __name__ == "__main__":
    sys.exit(main())
