#!/usr/bin/env python3
"""Edge cases of the hooks under real Claude Code hook inputs: python3 tests/test_hooks_edge.py

Each check names the hook and the edge: malformed or foreign input, an unwritable `.tf/logs`, a project directory below the
repository root or a session `cwd` below the project, non-ASCII paths, an interrupted tool call, shell commands that dress
up a blocked operation (quotes, `bash -c`, substitutions, split flags, global options), output limits and the hook
registration (event budgets, PreCompact stdout). A hook that only logs or advises must exit 0 on any input; a guard ends in
a decision, never in a crash. Standard library only.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
HOOKS = ROOT / ".claude" / "hooks"
FAILS: list[str] = []
COUNT = [0]


def check(ok: bool, msg: str) -> None:
    COUNT[0] += 1
    if not ok:
        FAILS.append(msg)
        print(f"✗ {msg}")


def run(hook: str, payload, project: Path, *args: str, env: dict | None = None, cwd: Path | None = None):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    base = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE_", "TF_", "QG_"))}
    return subprocess.run([sys.executable, str(HOOKS / hook), *args], input=text, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60, cwd=cwd or project,
                          env={**base, "CLAUDE_PROJECT_DIR": str(project), **(env or {})})


def decision(stdout: str) -> str:
    if not stdout.strip():
        return "none"
    return json.loads(stdout).get("hookSpecificOutput", {}).get("permissionDecision", "none")


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.email=t@example.org", "-c", "user.name=t", *args], cwd=repo, check=True,
                   capture_output=True)


def new_repo(tmp: Path, name: str) -> Path:
    repo = tmp / name
    repo.mkdir(parents=True)
    git(repo, "init", "-q")
    return repo


def unwritable_logs(project: Path) -> None:
    """`.tf/logs` that cannot be created or written (a file in its place) — works also for root, unlike chmod."""
    (project / ".tf").mkdir(parents=True, exist_ok=True)
    shutil.rmtree(project / ".tf" / "logs", ignore_errors=True)
    (project / ".tf" / "logs").write_text("not a directory", encoding="utf-8")


def module(name: str):
    spec = importlib.util.spec_from_file_location(f"edge_{name}", HOOKS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- logging hooks: any input and an unwritable log directory end in exit 0 ------------------------------------------

ODD = ["", "not json", "[]", "null", "42", '"text"', "{}", json.dumps({"tool_input": None, "tool_response": None}),
       json.dumps({"tool_input": "ls", "transcript_path": 3, "cwd": 5}), json.dumps({"hook_event_name": "Bogus"})]


def test_logging_hooks_fail_safe(tmp: Path) -> None:
    project = tmp / "logs-proj"
    project.mkdir()
    transcript = project / "t.jsonl"
    transcript.write_text(json.dumps({"type": "assistant", "message": {"id": "m", "model": "x", "content": [],
                                                                       "usage": {"input_tokens": 5, "output_tokens": 1}}})
                          + "\n", encoding="utf-8")
    for hook, event in (("log_usage.py", "SessionEnd"), ("log_usage.py", "SubagentStop"), ("log_usage.py", "PostToolUse"),
                        ("scan_secrets.py", "PostToolUse")):
        for raw in ODD:
            try:
                data = json.loads(raw)
            except ValueError:
                data = None
            text = json.dumps({**data, "hook_event_name": data.get("hook_event_name", event)}) \
                if isinstance(data, dict) else raw
            r = run(hook, text, project)
            check(r.returncode == 0, f"{hook} {event}: input {raw[:30]!r} → exit {r.returncode} "
                                     f"{r.stderr.strip().splitlines()[-1:]}")
    unwritable_logs(project)
    for event, extra in (("SessionEnd", {"transcript_path": str(transcript)}),
                         ("SubagentStop", {"agent_transcript_path": str(transcript), "agent_id": "a"}),
                         ("PostToolUse", {"tool_name": "Agent", "tool_input": {"prompt": "p"}, "tool_response": "r"})):
        r = run("log_usage.py", {"hook_event_name": event, "session_id": "s", **extra}, project)
        check(r.returncode == 0, f"log_usage {event}: an unwritable .tf/logs → exit {r.returncode} "
                                 f"{r.stderr.strip().splitlines()[-1:]}")


# --- scan_secrets ---------------------------------------------------------------------------------------------------

def test_scan_secrets(tmp: Path) -> None:
    project = tmp / "secrets-proj"
    project.mkdir()
    cases = [
        ("pgp.asc", "-----BEGIN PGP PRIVATE KEY BLOCK-----\n\nlQOYBF0\n-----END PGP PRIVATE KEY BLOCK-----\n", 2),
        ("pkcs8.pem.txt", "-----BEGIN ENCRYPTED PRIVATE KEY-----\nMIIFHz\n-----END ENCRYPTED PRIVATE KEY-----\n", 2),
        ("rsa.txt", "-----BEGIN RSA PRIVATE KEY-----\nMIIE\n", 2),
        ("crlf.py", 'x = 1\r\nAWS = "AKIA' + "Q" * 16 + '"\r\n', 2),
        ("bin.dat", "\x00\x01\x02 token ghp_" + "a" * 36 + " \x00", 2),
        ("ok.py", "password = os.environ['DB_PASSWORD']\n", 0),
        ("pub.txt", "-----BEGIN PUBLIC KEY-----\nMIIB\n", 0),
    ]
    for name, content, want in cases:
        p = project / name
        p.write_bytes(content.encode("utf-8"))
        r = run("scan_secrets.py", {"hook_event_name": "PostToolUse", "tool_name": "Write",
                                    "tool_input": {"file_path": str(p)}}, project)
        check(r.returncode == want, f"scan_secrets {name}: expected exit {want}, got {r.returncode} {r.stderr[-120:]}")
    r = run("scan_secrets.py", {"hook_event_name": "PostToolUse", "tool_name": "Write",
                                "tool_input": {"file_path": 7}}, project)
    check(r.returncode == 0, f"scan_secrets: a non-text file_path → exit {r.returncode}")


# --- quality_gate -----------------------------------------------------------------------------------------------------

def gate_repo(tmp: Path, name: str, cfg: dict, sub: str = "") -> tuple[Path, Path]:
    repo = new_repo(tmp, name)
    project = repo / sub if sub else repo
    (project / "src").mkdir(parents=True)
    (project / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "init")
    (project / ".claude").mkdir()
    (project / ".claude" / "quality-gate.json").write_text(json.dumps(cfg), encoding="utf-8")
    (project / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
    return repo, project


def test_quality_gate(tmp: Path) -> None:
    py = sys.executable
    # an unwritable .tf/logs: the red verdict still blocks (saving the state is a side effect, not the verdict)
    _, project = gate_repo(tmp, "qg-ro", {"command": [py, "-c", "import sys; sys.exit(1)"]})
    unwritable_logs(project)
    r = run("quality_gate.py", {"hook_event_name": "Stop", "stop_hook_active": False}, project)
    out = json.loads(r.stdout) if r.stdout.strip() else {}
    check(r.returncode == 0 and out.get("decision") == "block",
          f"quality_gate: red tests with an unwritable .tf/logs must still block: {r.stdout[:120]!r} {r.stderr[-160:]!r}")
    # ...and on a repeated stop (stop_hook_active) without a saved counter it lets the turn end with a message
    r = run("quality_gate.py", {"hook_event_name": "Stop", "stop_hook_active": True}, project)
    out = json.loads(r.stdout) if r.stdout.strip() else {}
    check(r.returncode == 0 and out.get("decision") != "block" and out.get("systemMessage"),
          f"quality_gate: no saved counter and stop_hook_active → no endless block: {r.stdout[:160]!r}")
    # CLAUDE_PROJECT_DIR below the repository root (a monorepo package): `related` gets the changed files
    probe = [py, "-c", "import sys, pathlib; pathlib.Path('args.txt').write_text(' '.join(sys.argv[1:])); sys.exit(1)"]
    _, project = gate_repo(tmp, "qg-sub", {"command": [py, "-c", "pass"], "related": probe + ["{files}"]},
                           sub="packages/app")
    (project / "src" / "new.py").write_text("y = 1\n", encoding="utf-8")
    r = run("quality_gate.py", {"hook_event_name": "Stop"}, project)
    args = (project / "args.txt").read_text(encoding="utf-8").split() if (project / "args.txt").is_file() else []
    check(sorted(args) == ["src/a.py", "src/new.py"],
          f"quality_gate: a project below the repository root → related gets its changed files, got {args} "
          f"{r.stdout[:100]!r}")
    # the time budget: lock wait + test timeout stay inside the Stop/SubagentStop hook timeout (no orphaned tests)
    qg = module("quality_gate")
    hook_timeouts = []
    settings = json.loads((ROOT / ".claude" / ("settings.json" if (ROOT / ".claude" / "settings.json").is_file()
                                               else "settings.local.json")).read_text(encoding="utf-8"))
    for event in ("Stop", "SubagentStop"):
        for group in settings["hooks"].get(event, []):
            hook_timeouts += [h.get("timeout", 600) for h in group["hooks"] if "quality_gate.py" in " ".join(h.get("args", []))]
    check(bool(hook_timeouts) and hasattr(qg, "budget"), "quality_gate: a time budget function exists and the hook is registered")
    if hasattr(qg, "budget") and hook_timeouts:
        for cfg_timeout, lock_wait in ((600, 900), (5000, 900), (10, 0), (899, 899)):
            wait, timeout = qg.budget(cfg_timeout, lock_wait)
            check(0 <= wait and 0 < timeout <= cfg_timeout and wait + timeout < min(hook_timeouts),
                  f"quality_gate: budget({cfg_timeout}, {lock_wait}) = ({wait}, {timeout}) exceeds the hook timeout "
                  f"{min(hook_timeouts)}")
    # no git at all: nothing to fingerprint, the gate runs nothing and exits 0
    plain = tmp / "qg-nogit"
    (plain / ".claude").mkdir(parents=True)
    (plain / ".claude" / "quality-gate.json").write_text(json.dumps({"command": [py, "-c", "import sys; sys.exit(1)"]}),
                                                          encoding="utf-8")
    r = run("quality_gate.py", {"hook_event_name": "Stop"}, plain)
    check(r.returncode == 0 and not r.stdout.strip(), f"quality_gate: a project without git → no block: {r.stdout[:80]!r}")
    # a detached HEAD still compares against HEAD
    repo, project = gate_repo(tmp, "qg-detached", {"command": [py, "-c", "import sys; sys.exit(1)"]})
    git(repo, "stash", "-q")
    git(repo, "checkout", "-q", "--detach")
    git(repo, "stash", "pop", "-q")
    r = run("quality_gate.py", {"hook_event_name": "SubagentStop"}, project)
    check('"block"' in r.stdout, f"quality_gate: a detached HEAD with a red change → block: {r.stdout[:80]!r}")


# --- tdd_guard --------------------------------------------------------------------------------------------------------

def tdd_project(tmp: Path, name: str) -> Path:
    project = tmp / name
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    return project


def test_tdd_interrupt(tmp: Path) -> None:
    project = tdd_project(tmp, "tdd-int")
    base = {"session_id": "s", "cwd": str(project)}
    test_file = str(project / "tests" / "test_a.py")
    run("tdd_guard.py", {**base, "hook_event_name": "PostToolUse", "tool_name": "Write",
                         "tool_input": {"file_path": test_file, "content": "def test_a():\n    assert f()\n"}}, project)
    # the human interrupted the test run (Esc / Ctrl+C): PostToolUseFailure with is_interrupt — not a red test
    run("tdd_guard.py", {**base, "hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
                         "tool_input": {"command": "pytest -q"}, "error": "Interrupted by user", "is_interrupt": True},
        project)
    r = run("tdd_guard.py", {**base, "hook_event_name": "PreToolUse", "tool_name": "Edit",
                             "tool_input": {"file_path": str(project / "src" / "a.py"), "old_string": "a",
                                            "new_string": "b"}}, project)
    check(decision(r.stdout) == "deny", f"tdd_guard: an interrupted test run is not a red test: {r.stdout[:120]!r}")
    # a real failure after that opens the gate
    run("tdd_guard.py", {**base, "hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
                         "tool_input": {"command": "pytest -q"}, "error": "Exit code 1\nFAILED tests/test_a.py::test_a",
                         "is_interrupt": False}, project)
    r = run("tdd_guard.py", {**base, "hook_event_name": "PreToolUse", "tool_name": "Edit",
                             "tool_input": {"file_path": str(project / "src" / "a.py"), "old_string": "a",
                                            "new_string": "b"}}, project)
    check(decision(r.stdout) == "none", f"tdd_guard: a red run after the test edit opens the gate: {r.stdout[:120]!r}")


def test_tdd_shell_write_unwritable_state(tmp: Path) -> None:
    """guard_bash asks tdd_guard about a shell write; a state that cannot be saved must not turn the deny into a pass."""
    project = tdd_project(tmp, "tdd-ro")
    unwritable_logs(project)
    r = run("guard_bash.py", {"session_id": "s", "cwd": str(project), "hook_event_name": "PreToolUse", "tool_name": "Bash",
                              "tool_input": {"command": "echo 'x = 1' > src/a.py"}}, project)
    check(decision(r.stdout) == "deny", f"guard_bash: a shell write to production code with an unwritable .tf/logs "
                                        f"→ still the TDD deny: {r.stdout[:120]!r} {r.stderr[-120:]!r}")


# --- guard_paths --------------------------------------------------------------------------------------------------------

def test_guard_paths(tmp: Path) -> None:
    project = tmp / "paths-proj"
    (project / "sub").mkdir(parents=True)
    (project / ".tf" / "config").mkdir(parents=True)
    cfg = project / ".tf" / "config" / "config.yaml"
    cfg.write_text("isolation: sandbox\n", encoding="utf-8")
    write = {"hook_event_name": "PreToolUse", "tool_name": "Write",
             "tool_input": {"file_path": str(cfg), "content": "isolation: none\n"}}
    for label, cwd in (("cwd = the project", project), ("cwd below the project", project / "sub")):
        r = run("guard_paths.py", {**write, "cwd": str(cwd)}, project, cwd=cwd)
        check(decision(r.stdout) == "deny", f"guard_paths: lowering isolation, {label} → deny, got {decision(r.stdout)}")
    for ti, want in (({"pattern": "KEY", "glob": ".env"}, "deny"), ({"pattern": "KEY", "glob": "**/.env*"}, "deny"),
                     ({"pattern": "KEY", "glob": "*.ts"}, "none"), ({"pattern": "KEY", "path": "src"}, "none")):
        r = run("guard_paths.py", {"hook_event_name": "PreToolUse", "tool_name": "Grep", "tool_input": ti,
                                   "cwd": str(project)}, project)
        check(decision(r.stdout) == want, f"guard_paths: Grep {ti} → expected {want}, got {decision(r.stdout)}")
    for path, want in (("C:\\proj\\.env", "deny"), ("C:\\proj\\src\\zażółć.ts", "none"), ("src/ünï.env.example", "none")):
        r = run("guard_paths.py", {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {"file_path": path},
                                   "cwd": str(project)}, project)
        check(decision(r.stdout) == want, f"guard_paths: Read {path!r} → expected {want}, got {decision(r.stdout)}")


# --- guard_bash: commands that dress up a blocked operation -------------------------------------------------------------

BASH_EDGE = [
    ('bash -c "rm -rf /"', "deny"), ("sh -c 'rm -rf ~'", "deny"), ("echo $(rm -rf /)", "deny"), ("echo `rm -rf ~`", "deny"),
    ('"rm" -rf /', "deny"), ("r\\m -rf /", "deny"), ("rm -r -f /", "deny"), ("rm -f -r ~", "deny"),
    ("rm --recursive --force /", "deny"), ('rm -rf "$HOME"', "deny"), ("rm -rf ${HOME}", "deny"),
    ("ls\nrm -rf /", "deny"), ("env X=1 rm -rf /", "deny"), ("git -C . push --force", "deny"),
    ("terraform -chdir=infra destroy", "deny"), ("terraform -chdir=infra apply -auto-approve", "deny"),
    ("terraform -chdir=infra apply tfplan", "ask"), ("grep -r KEY .env", "deny"), ("awk 1 .env", "deny"),
    ("sed -n p .env.local", "deny"), ("export", "deny"), ("export -p", "deny"), ("declare -px", "deny"),
    ("sudo -u root git push -f", "deny"), ("git push origin main && echo ok", "ask"),
    # the same words in harmless commands
    ("rm -rf ./dist", "none"), ("rm -r -f build/", "none"), ("rm -rf node_modules .cache", "none"),
    ("export FOO=1", "none"), ("set -e", "none"), ("grep -r KEY src/", "none"), ("grep KEY .env.example", "none"),
    ("terraform -chdir=infra plan", "none"), ("git commit -m 'docs: rm -r -f is risky'", "none"),
    ("echo $(git rev-parse HEAD)", "none"), ("bash -c 'npm test'", "none"),
]


def test_guard_bash_edges(tmp: Path) -> None:
    project = tmp / "bash-proj"
    project.mkdir()
    for cmd, want in BASH_EDGE:
        r = run("guard_bash.py", {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": cmd},
                                  "cwd": str(project)}, project, env={"CLAUDE_TDD": "off"})
        got = decision(r.stdout) if r.returncode == 0 else f"exit {r.returncode}"
        check(got == want, f"guard_bash {cmd!r}: expected {want}, got {got}")


# --- project_record: the Stop reminder sees non-ASCII paths -------------------------------------------------------------

def test_project_record_non_ascii(tmp: Path) -> None:
    repo = new_repo(tmp, "rec-proj")
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "init")
    wip = repo / ".tf" / "wip"
    wip.mkdir(parents=True)
    cp = wip / "w.md"
    cp.write_text("---\nstatus: active\n---\n# w\n", encoding="utf-8")
    os.utime(cp, (1_000_000, 1_000_000))
    (repo / "zażółć gęślą.py").write_text("x = 1\n", encoding="utf-8")
    r = run("project_record.py", {"hook_event_name": "Stop", "stop_hook_active": False}, repo, "--hook-stop")
    check('"block"' in r.stdout, f"project_record --hook-stop: a non-ASCII changed file newer than the checkpoint "
                                 f"→ reminder: {r.stdout[:100]!r} {r.stderr[-100:]!r}")
    r = run("project_record.py", {"hook_event_name": "Stop", "stop_hook_active": True}, repo, "--hook-stop")
    check(not r.stdout.strip(), "project_record --hook-stop: stop_hook_active → no second block")
    # PreCompact: stdout on exit 0 becomes compaction instructions — the snapshot prints nothing
    r = run("project_record.py", {"hook_event_name": "PreCompact", "trigger": "auto", "custom_instructions": None}, repo,
            "--hook-snapshot", "context compaction")
    check(r.returncode == 0 and not r.stdout.strip(), f"project_record PreCompact: no stdout, exit 0: {r.stdout[:80]!r}")


# --- start-of-session hooks: bad environment values ---------------------------------------------------------------------

def test_session_start_env(tmp: Path) -> None:
    project = tmp / "start-proj"
    project.mkdir()
    for raw in ("[]", "null", "{}"):
        r = run("detect_stack.py", raw, project, "--hook", env={"CLAUDE_HOOK_DEADLINE": "soon"})
        check(r.returncode == 0, f"detect_stack --hook: CLAUDE_HOOK_DEADLINE=soon, input {raw} → exit {r.returncode} "
                                 f"{r.stderr.strip().splitlines()[-1:]}")
    r = run("test_lock.py", "", project, "--", sys.executable, "-c", "pass", env={"QG_LOCK_WAIT": "abc"})
    check(r.returncode == 0, f"test_lock: QG_LOCK_WAIT=abc → the default wait, exit {r.returncode} {r.stderr[-120:]!r}")


# --- registration: event budgets and blocking guards ---------------------------------------------------------------------

def test_registration() -> None:
    name = "settings.json" if (ROOT / ".claude" / "settings.json").is_file() else "settings.local.json"
    settings = json.loads((ROOT / ".claude" / name).read_text(encoding="utf-8"))
    for event, groups in settings["hooks"].items():
        for group in groups:
            for h in group["hooks"]:
                script = Path(h["args"][0].replace("${CLAUDE_PROJECT_DIR}", str(ROOT)))
                check(script.is_file(), f"{event}: the registered hook {script.name} exists")
                if event == "SessionEnd":   # SessionEnd hooks share a budget capped at 60 s
                    check(h.get("timeout", 0) and h["timeout"] <= 60, f"SessionEnd {script.name}: timeout ≤ 60 s")
                if h.get("onFailure") == "block":   # a guard that fails closed: only the documented security guards
                    check(script.name in ("guard_bash.py", "guard_paths.py", "cleanroom_guard.py"),
                          f"{event} {script.name}: onFailure block only on the security guards")


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        test_logging_hooks_fail_safe(tmp)
        test_scan_secrets(tmp)
        test_quality_gate(tmp)
        test_tdd_interrupt(tmp)
        test_tdd_shell_write_unwritable_state(tmp)
        test_guard_paths(tmp)
        test_guard_bash_edges(tmp)
        test_project_record_non_ascii(tmp)
        test_session_start_env(tmp)
    test_registration()
    if FAILS:
        print(f"✗ {COUNT[0] - len(FAILS)}/{COUNT[0]} hook edge cases")
        return 1
    print(f"✓ {COUNT[0]}/{COUNT[0]} hook edge cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
