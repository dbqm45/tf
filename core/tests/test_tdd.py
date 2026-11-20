#!/usr/bin/env python3
"""Tests of the TDD gate (tdd_guard hook): production code only after a red test."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
HOOK = ROOT / ".claude" / "hooks" / "tdd_guard.py"


def main() -> int:
    fails, total = [], 0
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        (proj / "src").mkdir()
        (proj / "src" / "price.test.ts").write_text("test('rabat', () => expect(rabat(100)).toBe(90))\n")
        (proj / "src" / "legacy.test.ts").write_text("describe('[charakteryzujący] stary cennik', () => {})\n")

        def call(event, tool, inp=None, resp=None, agent=None, env_extra=None, session="s1"):
            data = {"hook_event_name": event, "tool_name": tool, "tool_input": inp or {}, "session_id": session,
                    "cwd": str(proj)}
            if resp is not None:
                data["tool_response"] = resp
            if agent:
                data["agent_id"] = agent
            env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj), **(env_extra or {})}
            env.pop("CLAUDE_TDD", None) if "CLAUDE_TDD" not in (env_extra or {}) else None
            out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(data), capture_output=True, text=True,
                                 env=env, timeout=20).stdout
            return json.loads(out)["hookSpecificOutput"] if out.strip() else None

        def pre(path, **kw):
            return call("PreToolUse", "Edit", {"file_path": str(proj / path)}, **kw)

        def post_edit(path, **kw):
            return call("PostToolUse", "Edit", {"file_path": str(proj / path)}, **kw)

        def run_tests(failed: bool, cmd="npx vitest run", **kw):
            if failed:
                return call("PostToolUseFailure", "Bash", {"command": cmd}, {"stdout": "Tests  1 failed"}, **kw)
            return call("PostToolUse", "Bash", {"command": cmd}, {"stdout": "Tests  3 passed", "exit_code": 0}, **kw)

        def check(cond, msg):
            nonlocal total
            total += 1
            if not cond:
                fails.append(msg)

        # 1. code before a test → blocked
        r = pre("src/price.ts")
        check(r and r["permissionDecision"] == "deny" and "write a test" in r["permissionDecisionReason"],
              f"code before a test should be blocked: {r}")
        # 2. test → red → code allowed
        post_edit("src/price.test.ts")
        run_tests(failed=True)
        check(pre("src/price.ts") is None, "after a red test the code should be allowed")
        # 2-log. a red run after a test edit leaves a durable entry (for the criterion → test trace, step D3)
        red_log = proj / ".tf" / "logs" / "tdd-red.jsonl"

        def red_rows():
            return [json.loads(ln) for ln in red_log.read_text(encoding="utf-8").splitlines()] if red_log.is_file() else []

        rows = red_rows()
        check(len(rows) == 1 and rows[0].get("tests") == ["src/price.test.ts"] and rows[0].get("at")
              and "vitest" in rows[0].get("command", ""),
              f"red test after a test edit → entry in tdd-red.jsonl with the test file: {rows}")
        post_edit("src/legacy.test.ts", session="rl")
        call("PostToolUseFailure", "Bash", {"command": "npx vitest run"}, {"stdout": "No test files found"}, session="rl")
        check(len(red_rows()) == 1, f"a 'red' without an executed assertion is not an entry: {red_rows()}")
        run_tests(failed=True, session="rl")
        check(len(red_rows()) == 2 and red_rows()[-1].get("tests") == ["src/legacy.test.ts"],
              f"prawdziwy czerwony w innej sesji → drugi wpis: {red_rows()}")
        run_tests(failed=False, session="rl")
        run_tests(failed=True, session="rl")
        check(len(red_rows()) == 2, f"red without a new test edit (after green) does not add an entry: {red_rows()}")
        # 2a. a "red" without an executed assertion → warning (2.6.0; no change to the gate decision)
        for out in ("No test files found, exiting with code 1", "collected 0 items\n no tests ran",
                    "src/price.test.ts(3,5): error TS1005: ';' expected."):
            r = call("PostToolUseFailure", "Bash", {"command": "npx vitest run"}, {"stdout": out})
            check(r and "executed no assertions" in r.get("additionalContext", ""), f"empty red → warning: {out!r}: {r}")
        for out in ("Error: Cannot find module '../src/price' imported from src/price.test.ts", "Tests  1 failed"):
            r = call("PostToolUseFailure", "Bash", {"command": "npx vitest run"}, {"stdout": out})
            check(r is None, f"real red without a warning: {out!r}: {r}")
        # 3. files outside the gate
        ok = all(pre(p, session="s2") is None for p in ("src/price.test.ts", "vite.config.ts", "src/types.d.ts",
                                                          "src/app.css", "docs/a.md", "src/app.component.html",
                                                          ".claude/hooks/x.py", ".tf/factory/build.py", "package.json"))
        check(ok, "tests, configuration, styles, documentation and factory files are not subject to the gate")
        # 4. green new test → one warning; a characterization test allows refactoring
        post_edit("src/price.test.ts", session="s3")
        run_tests(failed=False, session="s3")
        r = pre("src/price.ts", session="s3")
        check(r and "PASSED" in r["permissionDecisionReason"], f"green new test: warning {r}")
        post_edit("src/legacy.test.ts", session="s4")
        run_tests(failed=False, session="s4")
        check(pre("src/legacy.ts", session="s4") is None, "a marked characterization test allows refactoring")
        # 5. rule B: edit limit without a new test
        env = {"CLAUDE_TDD_MAX_EDITS": "3"}
        post_edit("src/price.test.ts", session="s5", env_extra=env)
        run_tests(failed=True, session="s5", env_extra=env)
        for _ in range(3):
            pre("src/price.ts", session="s5", env_extra=env)
            post_edit("src/price.ts", session="s5", env_extra=env)
        r = pre("src/price.ts", session="s5", env_extra=env)
        post_edit("src/price.test.ts", session="s5", env_extra=env)
        r2 = pre("src/price.ts", session="s5", env_extra=env)
        check(r and "without a new test" in r["permissionDecisionReason"] and r2 is None,
              f"rule B: edit limit and reset after a new test — {r} / {r2}")
        # 6. separate state for a subagent
        r = pre("src/price.ts", agent="a1")          # session s1 is "started", subagent a1 is not
        check(r and r["permissionDecision"] == "deny", "a subagent has its own TDD state")
        # 7. tryby
        check(pre("src/x.ts", session="s6", env_extra={"CLAUDE_TDD": "off"}) is None, "CLAUDE_TDD=off disables the gate")
        r = pre("src/x.ts", session="s7", env_extra={"CLAUDE_TDD": "ask"})
        check(r and r["permissionDecision"] == "ask", "CLAUDE_TDD=ask leaves the decision to the human")
        # 8. recognising the test result: exit code, pytest result, a non-test command
        post_edit("tests/test_cart.py", session="s8")
        call("PostToolUse", "Bash", {"command": "ls -la"}, {"stdout": "FAILED", "exit_code": 1}, session="s8")
        check(pre("app/cart.py", session="s8") is not None, "a command that does not run tests does not count")
        call("PostToolUse", "Bash", {"command": "python -m pytest -q"}, {"stdout": "1 failed, 4 passed", "exit_code": 1},
             session="s8")
        check(pre("app/cart.py", session="s8") is None, "pytest with a failure = red")
        post_edit("src/test/java/shop/CartTest.java", session="s9")
        call("PostToolUse", "Bash", {"command": "./mvnw -q test"}, {"stdout": "BUILD FAILURE"}, session="s9")
        check(pre("src/main/java/shop/Cart.java", session="s9") is None, "Maven: BUILD FAILURE = czerwony; testy Javy rozpoznane")
        # 8a. tests as standalone scripts (python3 tests/test_*.py, as in the factory and .claude/tests after installation)
        for i, cmd in enumerate(("python3 tests/test_cart.py", "python tests/test_cart.py",
                                 "py -3 .claude\\tests\\test_cart.py", "python3 -I .claude/tests/test_cart.py",
                                 'for t in tests/test_*.py; do python3 "$t" || exit 1; done',
                                 "cd app && python3 test_cart.py")):
            sess = f"s8a{i}"
            post_edit("tests/test_cart.py", session=sess)
            call("PostToolUse", "Bash", {"command": cmd}, {"stdout": "✗ 1/2 tests", "exit_code": 1}, session=sess)
            check(pre("app/cart.py", session=sess) is None, f"a test script with a failure = red: {cmd}")
        for i, cmd in enumerate(("python3 scripts/release.py", "python3 tests/helpers.py", "python3 -c 'print(1)'")):
            sess = f"s8b{i}"
            post_edit("tests/test_cart.py", session=sess)
            call("PostToolUse", "Bash", {"command": cmd}, {"stdout": "FAILED", "exit_code": 1}, session=sess)
            check(pre("app/cart.py", session=sess) is not None, f"a script that is not a test does not count: {cmd}")
        post_edit("tests/test_cart.py", session="s8c")
        call("PostToolUse", "Bash", {"command": "python3 tests/test_cart.py"}, {"stdout": "✓ 2/2", "exit_code": 0},
             session="s8c")
        r = pre("app/cart.py", session="s8c")
        check(r and "PASSED" in r["permissionDecisionReason"], f"a green test script = green: {r}")

        # 9. rule C: weakening a test (fewer assertions, removed test, skip/xfail) — a warning by default
        def raw(tool, inp, env_extra=None):
            data = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": inp, "session_id": "w1",
                    "cwd": str(proj)}
            env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj), **(env_extra or {})}
            if "CLAUDE_TDD" not in (env_extra or {}):
                env.pop("CLAUDE_TDD", None)
            if "CLAUDE_TDD_WEAKEN" not in (env_extra or {}):
                env.pop("CLAUDE_TDD_WEAKEN", None)
            out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(data), capture_output=True, text=True,
                                 env=env, timeout=20).stdout
            return json.loads(out) if out.strip() else {}

        t = str(proj / "tests" / "test_rabat.py")
        (proj / "tests").mkdir(exist_ok=True)
        (proj / "tests" / "test_rabat.py").write_text(
            "def test_progi():\n    assert rabat(199) == 0\n    assert rabat(200) == 10\n\n"
            "def test_ujemne():\n    assert rabat(-1) == 0\n")
        fewer = {"file_path": t, "old_string": "    assert rabat(199) == 0\n    assert rabat(200) == 10\n",
                 "new_string": "    assert rabat(200) == 10\n"}
        r = raw("Edit", fewer)
        hso = r.get("hookSpecificOutput", {})
        check("systemMessage" in r and "weaken" in r["systemMessage"] and "permissionDecision" not in hso
              and "weaken" in hso.get("additionalContext", ""),
              f"fewer assertions → by default a warning for the human and context for the model, no block: {r}")
        r = raw("Edit", fewer, {"CLAUDE_TDD_WEAKEN": "ask"})
        check(r.get("hookSpecificOutput", {}).get("permissionDecision") == "ask", f"CLAUDE_TDD_WEAKEN=ask: {r}")
        r = raw("Edit", {"file_path": t, "old_string": "def test_ujemne():",
                         "new_string": "@pytest.mark.skip\ndef test_ujemne():"}, {"CLAUDE_TDD_WEAKEN": "deny"})
        check(r.get("hookSpecificOutput", {}).get("permissionDecision") == "deny", f"dopisany skip → deny: {r}")
        r = raw("Write", {"file_path": t, "content": "def test_progi():\n    assert rabat(200) == 10\n"})
        check("systemMessage" in r, f"Write removing a test and assertions → warning: {r}")
        more = {"file_path": t, "old_string": "    assert rabat(-1) == 0\n",
                "new_string": "    assert rabat(-1) == 0\n    assert rabat(0) == 0\n"}
        check(raw("Edit", more) == {}, "adding an assertion is not weakening")
        check(raw("Edit", fewer, {"CLAUDE_TDD_WEAKEN": "off"}) == {}, "CLAUDE_TDD_WEAKEN=off disables rule C")
        check(raw("Edit", fewer, {"CLAUDE_TDD": "off"}) == {}, "CLAUDE_TDD=off also disables rule C")
        js = str(proj / "src" / "price.test.ts")
        r = raw("Edit", {"file_path": js, "old_string": "test('rabat'", "new_string": "test.skip('rabat'"})
        check("systemMessage" in r, f"test.skip in JS → warning: {r}")

        # 10. writing code through Bash before execution (guard_bash, D-012): the same rules as Edit
        guard = ROOT / ".claude" / "hooks" / "guard_bash.py"

        def gb(cmd, session, env_extra=None):
            data = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": cmd},
                    "session_id": session, "cwd": str(proj)}
            env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj), **(env_extra or {})}
            if "CLAUDE_TDD" not in (env_extra or {}):
                env.pop("CLAUDE_TDD", None)
            out = subprocess.run([sys.executable, str(guard)], input=json.dumps(data), capture_output=True, text=True,
                                 env=env, timeout=20).stdout
            return json.loads(out)["hookSpecificOutput"] if out.strip() else None

        writes = ["sed -i 's/90/80/' src/price.ts", "echo 'export {}' > src/price.ts", "echo x >> src/price.ts",
                  "printf x | tee -a src/price.ts", "cat <<'EOF' > src/nowy.ts\nexport const a = 1 // it's\nEOF",
                  "cp /tmp/x.ts src/", "mv draft.py app/cart.py", "python3 -c \"open('src/price.ts','w').write('x')\"",
                  "python3 -c \"from pathlib import Path; Path('app/cart.py').write_text('x')\"",
                  "node -e \"require('fs').writeFileSync('src/price.ts', 'x')\"", "cd src && ls; sed -i.bak s/a/b/ src/price.ts"]
        for cmd in writes:
            r = gb(cmd, "b1")
            check(r and r["permissionDecision"] == "deny" and "TDD" in r["permissionDecisionReason"],
                  f"zapis kodu przez Bash bez czerwonego testu → deny: {cmd!r}: {r}")
        for cmd in ("echo x > src/price.test.ts", "echo x > notes.txt", "npx vitest run > out.log 2>&1",
                    "sed -n 1,5p src/price.ts", "cat src/price.ts > /dev/null", "cp src/price.ts /tmp/kopia.ts",
                    "git commit -m 'fix: rabat > 0'", "echo x > docs/a.ts", "grep -c x src/price.ts"):
            check(gb(cmd, "b1") is None, f"writing non-code or reading through Bash → no decision: {cmd!r}")
        check((gb("sed -i s/a/b/ src/price.ts", "b2", {"CLAUDE_TDD": "ask"}) or {}).get("permissionDecision") == "ask",
              "CLAUDE_TDD=ask → ask also for a write through Bash")
        check(gb("sed -i s/a/b/ src/price.ts", "b3", {"CLAUDE_TDD": "off"}) is None, "CLAUDE_TDD=off → bez bramki")
        post_edit("src/price.test.ts", session="b4")
        run_tests(failed=True, session="b4")
        check(gb("sed -i s/a/b/ src/price.ts", "b4") is None, "after a red test a write through Bash is allowed")

        # 11. after execution: production code changed by a command without a red test → a message with the file name, once
        git = lambda *a: subprocess.run(["git", "-C", str(proj), *a], capture_output=True, text=True, timeout=20)
        git("init", "-q")
        (proj / "src" / "price.ts").write_text("export const rabat = (x: number) => x\n")
        git("add", "-A")
        git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")

        def post_bash(cmd, session, env_extra=None):
            return call("PostToolUse", "Bash", {"command": cmd}, {"stdout": "", "exit_code": 0}, session=session,
                        env_extra=env_extra)

        check(post_bash("ls", "p1") is None, "the first command only records the initial state")
        (proj / "src" / "price.ts").write_text("export const rabat = (x: number) => x * 0.9\n")
        r = post_bash("python3 gen.py", "p1")
        ctx = (r or {}).get("additionalContext", "")
        check("src/price.ts" in ctx and "TDD" in ctx, f"a code change by a command without a red test → message: {r}")
        check(post_bash("ls", "p1") is None, "the same state → the message is not repeated")
        (proj / "src" / "price.test.ts").write_text("test('rabat', () => expect(rabat(100)).toBe(80))\n")
        (proj / "notes.txt").write_text("x\n")
        check(post_bash("python3 gen.py", "p1") is None, "a change to a test or notes → no message")
        post_bash("ls", "p2")
        post_edit("src/price.test.ts", session="p2")
        run_tests(failed=True, session="p2")
        (proj / "src" / "price.ts").write_text("export const rabat = (x: number) => x * 0.8\n")
        check(post_bash("npx prettier --write src", "p2") is None, "after a red test (e.g. a formatter) → no message")
        (proj / "src" / "price.ts").write_text("export const rabat = (x: number) => x * 0.7\n")
        check(call("PostToolUse", "Edit", {"file_path": str(proj / "src" / "price.ts")}, session="p3") is None
              and post_bash("ls", "p3") is None, "a change through Edit (after the gate) is not reported as a write through Bash")
        (proj / "src" / "price.ts").write_text("export const rabat = (x: number) => x * 0.6\n")
        check(post_bash("python3 gen.py", "p1", {"CLAUDE_TDD_BASH": "off"}) is None, "CLAUDE_TDD_BASH=off disables the post-execution check")
        state = (proj / ".tf" / "logs" / "tdd-state.json").read_text(encoding="utf-8")
        check("rabat" not in state and "gen.py" not in state, "the state contains neither file contents nor commands")

        # 12. loop of the same failure (D-013): 3× the same test and exception type → message; green or another failure resets
        def fail(out, session):
            return call("PostToolUseFailure", "Bash", {"command": "pytest"}, {"stdout": out}, session=session)

        a1 = "FAILED tests/test_rabat.py::test_progi - AssertionError: assert 9 == 10"
        a2 = "FAILED tests/test_rabat.py::test_progi - AssertionError: assert 8 == 10 (after the fix)"
        b = "FAILED tests/test_rabat.py::test_ujemne - ValueError: x"
        check(fail(a1, "l1") is None and fail(a2, "l1") is None, "1st and 2nd repetition → no message")
        r = fail(a1, "l1")
        check(r and "change the approach" in r.get("additionalContext", ""), f"3rd repetition → message: {r}")
        check(r and "permissionDecision" not in r, "the loop does not block")
        fail(a1, "l2"), fail(a1, "l2"), fail(b, "l2")
        check(fail(a1, "l2") is None, "another failure resets the counter")
        fail(a1, "l3"), fail(a1, "l3")
        call("PostToolUse", "Bash", {"command": "pytest"}, {"stdout": "3 passed", "exit_code": 0}, session="l3")
        check(fail(a1, "l3") is None, "zielony zeruje licznik")
        for i in range(3):
            r = fail("Tests  1 failed", "l4")
        check(r is None, "a failure without a recognised test and exception does not count")
        vit = "FAIL  src/price.test.ts > rabat > progi\nAssertionError: expected 90 to be 80"
        for i in range(3):
            r = fail(vit, "l5")
        check(r and "change the approach" in r.get("additionalContext", ""), f"vitest: 3× the same test → message: {r}")

        # 13. rule F: a change to protected files and secrets by a command → warning (also with CLAUDE_TDD=off)
        def guard(cmd, session, env_extra=None, event="PostToolUse", tool="Bash", inp=None):
            data = {"hook_event_name": event, "tool_name": tool, "tool_input": inp or {"command": cmd},
                    "tool_response": {"stdout": "", "exit_code": 0}, "session_id": session, "cwd": str(proj)}
            env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj), **(env_extra or {})}
            for k in ("CLAUDE_TDD", "CLAUDE_GUARD_CHANGES"):
                if k not in (env_extra or {}):
                    env.pop(k, None)
            out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(data), capture_output=True, text=True,
                                 env=env, timeout=20).stdout
            return json.loads(out) if out.strip() else {}

        def warned(out, name):
            return (name in out.get("hookSpecificOutput", {}).get("additionalContext", "")
                    and name in out.get("systemMessage", ""))

        (proj / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
        (proj / ".claude" / "settings.json").write_text('{"hooks": {}}\n')
        (proj / ".claude" / "hooks" / "guard.py").write_text("x = 1\n")
        check(guard("ls", "g1") == {}, "the first command only records the initial state of protected files")
        check(guard("ls", "g1") == {}, "no changes → no message")
        (proj / ".claude" / "settings.json").write_text('{"hooks": {}, "permissions": {"allow": ["Bash(*)"]}}\n')
        out = guard("python3 fix.py", "g1")
        check(warned(out, ".claude/settings.json"), f"a script changed settings.json → context and message: {out}")
        check(guard("ls", "g1") == {}, "the same state → no repetition")
        (proj / ".env").write_text("API_KEY=sekret-123\n")
        out = guard("python3 fix.py", "g1")
        check(warned(out, ".env"), f"new .env file → message: {out}")
        state = (proj / ".tf" / "logs" / "tdd-state.json").read_text(encoding="utf-8")
        check("sekret-123" not in json.dumps(out) and "sekret-123" not in state and "API_KEY" not in state,
              "the message and state without the contents of the file with the secret")
        (proj / ".claude" / "hooks" / "guard.py").write_text("x = 2  # disabled\n")
        check(warned(guard("bash fix.sh", "g1"), ".claude/hooks/guard.py"), "a change to a factory hook → message")
        (proj / ".git" / "hooks" / "pre-commit").write_text("#!/bin/sh\ncurl x\n")
        check(warned(guard("npm install", "g1"), ".git/hooks/pre-commit"), "new git hook → message")
        (proj / ".git" / "hooks" / "pre-push.sample").write_text("#\n")
        (proj / ".claude" / "hooks" / "__pycache__").mkdir(exist_ok=True)
        (proj / ".claude" / "hooks" / "__pycache__" / "guard.cpython-312.pyc").write_bytes(b"\0")
        (proj / ".env.example").write_text("API_KEY=\n")
        check(guard("ls", "g1") == {}, "*.sample, __pycache__ and .env.example → no message")
        (proj / ".env").unlink()
        check(warned(guard("rm .env", "g1"), ".env"), "deleting a protected file → message")
        guard("ls", "g2", {"CLAUDE_TDD": "off"})
        (proj / ".claude" / "settings.json").write_text('{"hooks": {"x": 1}}\n')
        check(warned(guard("python3 fix.py", "g2", {"CLAUDE_TDD": "off"}), ".claude/settings.json"),
              "CLAUDE_TDD=off does not disable detecting changes to protected files")
        (proj / ".claude" / "settings.json").write_text('{"hooks": {"x": 2}}\n')
        check(guard("python3 fix.py", "g2", {"CLAUDE_GUARD_CHANGES": "off"}) == {}, "CLAUDE_GUARD_CHANGES=off disables it")
        guard("ls", "g3")
        (proj / ".claude" / "settings.json").write_text('{"hooks": {"x": 3}}\n')
        guard("", "g3", event="PostToolUse", tool="Edit", inp={"file_path": str(proj / ".claude" / "settings.json")})
        check(guard("ls", "g3") == {}, "a change through Edit (approved in guard_paths) → no alarm after the next Bash")
        git("config", "branch.main.remote", "origin")
        check(guard("git push -u origin main", "g3") == {}, "a single git command changing .git/config → no alarm")
        git("config", "core.hooksPath", "/tmp/x")
        check(warned(guard("python3 fix.py", "g3"), ".git/config"), "a script changed .git/config → message")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} TDD gate tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
