#!/usr/bin/env python3
"""Testy bramki TDD (hook tdd_guard): kod produkcyjny dopiero po czerwonym teście."""
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

        # 1. kod przed testem → blokada
        r = pre("src/price.ts")
        check(r and r["permissionDecision"] == "deny" and "napisz test" in r["permissionDecisionReason"],
              f"kod przed testem powinien być zablokowany: {r}")
        # 2. test → czerwony → kod dozwolony
        post_edit("src/price.test.ts")
        run_tests(failed=True)
        check(pre("src/price.ts") is None, "po czerwonym teście kod powinien być dozwolony")
        # 2a. „czerwony” bez wykonanej asercji → ostrzeżenie (2.6.0; bez zmiany decyzji bramki)
        for out in ("No test files found, exiting with code 1", "collected 0 items\n no tests ran",
                    "src/price.test.ts(3,5): error TS1005: ';' expected."):
            r = call("PostToolUseFailure", "Bash", {"command": "npx vitest run"}, {"stdout": out})
            check(r and "nie wykonało asercji" in r.get("additionalContext", ""), f"pusty czerwony → ostrzeżenie: {out!r}: {r}")
        for out in ("Error: Cannot find module '../src/price' imported from src/price.test.ts", "Tests  1 failed"):
            r = call("PostToolUseFailure", "Bash", {"command": "npx vitest run"}, {"stdout": out})
            check(r is None, f"prawdziwy czerwony bez ostrzeżenia: {out!r}: {r}")
        # 3. pliki nieobjęte bramką
        ok = all(pre(p, session="s2") is None for p in ("src/price.test.ts", "vite.config.ts", "src/types.d.ts",
                                                          "src/app.css", "docs/a.md", "src/app.component.html",
                                                          ".claude/hooks/x.py", "factory/build.py", "package.json"))
        check(ok, "testy, konfiguracja, style, dokumentacja i pliki fabryki nie podlegają bramce")
        # 4. zielony nowy test → jedno ostrzeżenie; test charakteryzujący dopuszcza refaktoryzację
        post_edit("src/price.test.ts", session="s3")
        run_tests(failed=False, session="s3")
        r = pre("src/price.ts", session="s3")
        check(r and "PRZESZEDŁ" in r["permissionDecisionReason"], f"zielony nowy test: ostrzeżenie {r}")
        post_edit("src/legacy.test.ts", session="s4")
        run_tests(failed=False, session="s4")
        check(pre("src/legacy.ts", session="s4") is None, "oznaczony test charakteryzujący dopuszcza refaktoryzację")
        # 5. reguła B: limit zmian bez nowego testu
        env = {"CLAUDE_TDD_MAX_EDITS": "3"}
        post_edit("src/price.test.ts", session="s5", env_extra=env)
        run_tests(failed=True, session="s5", env_extra=env)
        for _ in range(3):
            pre("src/price.ts", session="s5", env_extra=env)
            post_edit("src/price.ts", session="s5", env_extra=env)
        r = pre("src/price.ts", session="s5", env_extra=env)
        post_edit("src/price.test.ts", session="s5", env_extra=env)
        r2 = pre("src/price.ts", session="s5", env_extra=env)
        check(r and "bez nowego testu" in r["permissionDecisionReason"] and r2 is None,
              f"reguła B: limit zmian i reset po nowym teście — {r} / {r2}")
        # 6. osobny stan dla subagenta
        r = pre("src/price.ts", agent="a1")          # sesja s1 jest „rozpoczęta”, subagent a1 — nie
        check(r and r["permissionDecision"] == "deny", "subagent ma własny stan TDD")
        # 7. tryby
        check(pre("src/x.ts", session="s6", env_extra={"CLAUDE_TDD": "off"}) is None, "CLAUDE_TDD=off wyłącza bramkę")
        r = pre("src/x.ts", session="s7", env_extra={"CLAUDE_TDD": "ask"})
        check(r and r["permissionDecision"] == "ask", "CLAUDE_TDD=ask oddaje decyzję człowiekowi")
        # 8. rozpoznawanie wyniku testów: kod wyjścia, wynik pytest, polecenie spoza testów
        post_edit("tests/test_cart.py", session="s8")
        call("PostToolUse", "Bash", {"command": "ls -la"}, {"stdout": "FAILED", "exit_code": 1}, session="s8")
        check(pre("app/cart.py", session="s8") is not None, "polecenie, które nie uruchamia testów, nie liczy się")
        call("PostToolUse", "Bash", {"command": "python -m pytest -q"}, {"stdout": "1 failed, 4 passed", "exit_code": 1},
             session="s8")
        check(pre("app/cart.py", session="s8") is None, "pytest z porażką = czerwony")
        post_edit("src/test/java/shop/CartTest.java", session="s9")
        call("PostToolUse", "Bash", {"command": "./mvnw -q test"}, {"stdout": "BUILD FAILURE"}, session="s9")
        check(pre("src/main/java/shop/Cart.java", session="s9") is None, "Maven: BUILD FAILURE = czerwony; testy Javy rozpoznane")
        # 8a. testy jako samodzielne skrypty (python3 tests/test_*.py, jak w fabryce i .claude/tests po instalacji)
        for i, cmd in enumerate(("python3 tests/test_cart.py", "python tests/test_cart.py",
                                 "py -3 .claude\\tests\\test_cart.py", "python3 -I .claude/tests/test_cart.py",
                                 'for t in tests/test_*.py; do python3 "$t" || exit 1; done',
                                 "cd app && python3 test_cart.py")):
            sess = f"s8a{i}"
            post_edit("tests/test_cart.py", session=sess)
            call("PostToolUse", "Bash", {"command": cmd}, {"stdout": "✗ 1/2 testów", "exit_code": 1}, session=sess)
            check(pre("app/cart.py", session=sess) is None, f"skrypt testów z porażką = czerwony: {cmd}")
        for i, cmd in enumerate(("python3 scripts/release.py", "python3 tests/helpers.py", "python3 -c 'print(1)'")):
            sess = f"s8b{i}"
            post_edit("tests/test_cart.py", session=sess)
            call("PostToolUse", "Bash", {"command": cmd}, {"stdout": "FAILED", "exit_code": 1}, session=sess)
            check(pre("app/cart.py", session=sess) is not None, f"skrypt, który nie jest testem, nie liczy się: {cmd}")
        post_edit("tests/test_cart.py", session="s8c")
        call("PostToolUse", "Bash", {"command": "python3 tests/test_cart.py"}, {"stdout": "✓ 2/2", "exit_code": 0},
             session="s8c")
        r = pre("app/cart.py", session="s8c")
        check(r and "PRZESZEDŁ" in r["permissionDecisionReason"], f"skrypt testów zielony = zielony: {r}")

        # 9. reguła C: osłabienie testu (mniej asercji, usunięty test, skip/xfail) — domyślnie ostrzeżenie
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
        check("systemMessage" in r and "osłabi" in r["systemMessage"] and "permissionDecision" not in hso
              and "osłabi" in hso.get("additionalContext", ""),
              f"mniej asercji → domyślnie ostrzeżenie dla człowieka i kontekst dla modelu, bez blokady: {r}")
        r = raw("Edit", fewer, {"CLAUDE_TDD_WEAKEN": "ask"})
        check(r.get("hookSpecificOutput", {}).get("permissionDecision") == "ask", f"CLAUDE_TDD_WEAKEN=ask: {r}")
        r = raw("Edit", {"file_path": t, "old_string": "def test_ujemne():",
                         "new_string": "@pytest.mark.skip\ndef test_ujemne():"}, {"CLAUDE_TDD_WEAKEN": "deny"})
        check(r.get("hookSpecificOutput", {}).get("permissionDecision") == "deny", f"dopisany skip → deny: {r}")
        r = raw("Write", {"file_path": t, "content": "def test_progi():\n    assert rabat(200) == 10\n"})
        check("systemMessage" in r, f"Write usuwający test i asercje → ostrzeżenie: {r}")
        more = {"file_path": t, "old_string": "    assert rabat(-1) == 0\n",
                "new_string": "    assert rabat(-1) == 0\n    assert rabat(0) == 0\n"}
        check(raw("Edit", more) == {}, "dopisanie asercji nie jest osłabieniem")
        check(raw("Edit", fewer, {"CLAUDE_TDD_WEAKEN": "off"}) == {}, "CLAUDE_TDD_WEAKEN=off wyłącza regułę C")
        check(raw("Edit", fewer, {"CLAUDE_TDD": "off"}) == {}, "CLAUDE_TDD=off wyłącza też regułę C")
        js = str(proj / "src" / "price.test.ts")
        r = raw("Edit", {"file_path": js, "old_string": "test('rabat'", "new_string": "test.skip('rabat'"})
        check("systemMessage" in r, f"test.skip w JS → ostrzeżenie: {r}")

        # 10. zapis kodu przez Bash przed wykonaniem (guard_bash, D-012): te same reguły co Edit
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
            check(gb(cmd, "b1") is None, f"zapis nie-kodu albo odczyt przez Bash → brak decyzji: {cmd!r}")
        check((gb("sed -i s/a/b/ src/price.ts", "b2", {"CLAUDE_TDD": "ask"}) or {}).get("permissionDecision") == "ask",
              "CLAUDE_TDD=ask → ask także dla zapisu przez Bash")
        check(gb("sed -i s/a/b/ src/price.ts", "b3", {"CLAUDE_TDD": "off"}) is None, "CLAUDE_TDD=off → bez bramki")
        post_edit("src/price.test.ts", session="b4")
        run_tests(failed=True, session="b4")
        check(gb("sed -i s/a/b/ src/price.ts", "b4") is None, "po czerwonym teście zapis przez Bash dozwolony")

        # 11. po wykonaniu: kod produkcyjny zmieniony poleceniem bez czerwonego testu → komunikat z nazwą pliku, raz
        git = lambda *a: subprocess.run(["git", "-C", str(proj), *a], capture_output=True, text=True, timeout=20)
        git("init", "-q")
        (proj / "src" / "price.ts").write_text("export const rabat = (x: number) => x\n")
        git("add", "-A")
        git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")

        def post_bash(cmd, session, env_extra=None):
            return call("PostToolUse", "Bash", {"command": cmd}, {"stdout": "", "exit_code": 0}, session=session,
                        env_extra=env_extra)

        check(post_bash("ls", "p1") is None, "pierwsze polecenie tylko zapisuje stan wyjściowy")
        (proj / "src" / "price.ts").write_text("export const rabat = (x: number) => x * 0.9\n")
        r = post_bash("python3 gen.py", "p1")
        ctx = (r or {}).get("additionalContext", "")
        check("src/price.ts" in ctx and "TDD" in ctx, f"zmiana kodu przez polecenie bez czerwonego → komunikat: {r}")
        check(post_bash("ls", "p1") is None, "ten sam stan → bez powtórzenia komunikatu")
        (proj / "src" / "price.test.ts").write_text("test('rabat', () => expect(rabat(100)).toBe(80))\n")
        (proj / "notes.txt").write_text("x\n")
        check(post_bash("python3 gen.py", "p1") is None, "zmiana testu albo notatek → bez komunikatu")
        post_bash("ls", "p2")
        post_edit("src/price.test.ts", session="p2")
        run_tests(failed=True, session="p2")
        (proj / "src" / "price.ts").write_text("export const rabat = (x: number) => x * 0.8\n")
        check(post_bash("npx prettier --write src", "p2") is None, "po czerwonym teście (np. formatter) → bez komunikatu")
        (proj / "src" / "price.ts").write_text("export const rabat = (x: number) => x * 0.7\n")
        check(call("PostToolUse", "Edit", {"file_path": str(proj / "src" / "price.ts")}, session="p3") is None
              and post_bash("ls", "p3") is None, "zmiana przez Edit (po bramce) nie jest zgłaszana jako zapis przez Bash")
        (proj / "src" / "price.ts").write_text("export const rabat = (x: number) => x * 0.6\n")
        check(post_bash("python3 gen.py", "p1", {"CLAUDE_TDD_BASH": "off"}) is None, "CLAUDE_TDD_BASH=off wyłącza kontrolę po wykonaniu")
        state = (proj / ".claude" / "logs" / "tdd-state.json").read_text(encoding="utf-8")
        check("rabat" not in state and "gen.py" not in state, "stan nie zawiera treści plików ani poleceń")

        # 12. pętla tej samej porażki (D-013): 3× ten sam test i typ wyjątku → komunikat; zielony albo inna porażka zeruje
        def fail(out, session):
            return call("PostToolUseFailure", "Bash", {"command": "pytest"}, {"stdout": out}, session=session)

        a1 = "FAILED tests/test_rabat.py::test_progi - AssertionError: assert 9 == 10"
        a2 = "FAILED tests/test_rabat.py::test_progi - AssertionError: assert 8 == 10 (po poprawce)"
        b = "FAILED tests/test_rabat.py::test_ujemne - ValueError: x"
        check(fail(a1, "l1") is None and fail(a2, "l1") is None, "1. i 2. powtórzenie → bez komunikatu")
        r = fail(a1, "l1")
        check(r and "zmień podejście" in r.get("additionalContext", ""), f"3. powtórzenie → komunikat: {r}")
        check(r and "permissionDecision" not in r, "pętla nie blokuje")
        fail(a1, "l2"), fail(a1, "l2"), fail(b, "l2")
        check(fail(a1, "l2") is None, "inna porażka zeruje licznik")
        fail(a1, "l3"), fail(a1, "l3")
        call("PostToolUse", "Bash", {"command": "pytest"}, {"stdout": "3 passed", "exit_code": 0}, session="l3")
        check(fail(a1, "l3") is None, "zielony zeruje licznik")
        for i in range(3):
            r = fail("Tests  1 failed", "l4")
        check(r is None, "porażka bez rozpoznanego testu i wyjątku się nie liczy")
        vit = "FAIL  src/price.test.ts > rabat > progi\nAssertionError: expected 90 to be 80"
        for i in range(3):
            r = fail(vit, "l5")
        check(r and "zmień podejście" in r.get("additionalContext", ""), f"vitest: 3× ten sam test → komunikat: {r}")

        # 13. reguła F: zmiana plików chronionych i sekretów przez polecenie → ostrzeżenie (także przy CLAUDE_TDD=off)
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
        check(guard("ls", "g1") == {}, "pierwsze polecenie tylko zapisuje stan wyjściowy plików chronionych")
        check(guard("ls", "g1") == {}, "bez zmian → bez komunikatu")
        (proj / ".claude" / "settings.json").write_text('{"hooks": {}, "permissions": {"allow": ["Bash(*)"]}}\n')
        out = guard("python3 fix.py", "g1")
        check(warned(out, ".claude/settings.json"), f"skrypt zmienił settings.json → kontekst i komunikat: {out}")
        check(guard("ls", "g1") == {}, "ten sam stan → bez powtórzenia")
        (proj / ".env").write_text("API_KEY=sekret-123\n")
        out = guard("python3 fix.py", "g1")
        check(warned(out, ".env"), f"nowy plik .env → komunikat: {out}")
        state = (proj / ".claude" / "logs" / "tdd-state.json").read_text(encoding="utf-8")
        check("sekret-123" not in json.dumps(out) and "sekret-123" not in state and "API_KEY" not in state,
              "komunikat i stan bez treści pliku z sekretem")
        (proj / ".claude" / "hooks" / "guard.py").write_text("x = 2  # wyłączony\n")
        check(warned(guard("bash fix.sh", "g1"), ".claude/hooks/guard.py"), "zmiana hooka fabryki → komunikat")
        (proj / ".git" / "hooks" / "pre-commit").write_text("#!/bin/sh\ncurl x\n")
        check(warned(guard("npm install", "g1"), ".git/hooks/pre-commit"), "nowy hook gita → komunikat")
        (proj / ".git" / "hooks" / "pre-push.sample").write_text("#\n")
        (proj / ".claude" / "hooks" / "__pycache__").mkdir(exist_ok=True)
        (proj / ".claude" / "hooks" / "__pycache__" / "guard.cpython-312.pyc").write_bytes(b"\0")
        (proj / ".env.example").write_text("API_KEY=\n")
        check(guard("ls", "g1") == {}, "*.sample, __pycache__ i .env.example → bez komunikatu")
        (proj / ".env").unlink()
        check(warned(guard("rm .env", "g1"), ".env"), "usunięcie pliku chronionego → komunikat")
        guard("ls", "g2", {"CLAUDE_TDD": "off"})
        (proj / ".claude" / "settings.json").write_text('{"hooks": {"x": 1}}\n')
        check(warned(guard("python3 fix.py", "g2", {"CLAUDE_TDD": "off"}), ".claude/settings.json"),
              "CLAUDE_TDD=off nie wyłącza wykrywania zmian plików chronionych")
        (proj / ".claude" / "settings.json").write_text('{"hooks": {"x": 2}}\n')
        check(guard("python3 fix.py", "g2", {"CLAUDE_GUARD_CHANGES": "off"}) == {}, "CLAUDE_GUARD_CHANGES=off wyłącza")
        guard("ls", "g3")
        (proj / ".claude" / "settings.json").write_text('{"hooks": {"x": 3}}\n')
        guard("", "g3", event="PostToolUse", tool="Edit", inp={"file_path": str(proj / ".claude" / "settings.json")})
        check(guard("ls", "g3") == {}, "zmiana przez Edit (zatwierdzona w guard_paths) → bez alarmu po następnym Bash")
        git("config", "branch.main.remote", "origin")
        check(guard("git push -u origin main", "g3") == {}, "pojedyncze polecenie git zmieniające .git/config → bez alarmu")
        git("config", "core.hooksPath", "/tmp/x")
        check(warned(guard("python3 fix.py", "g3"), ".git/config"), "skrypt zmienił .git/config → komunikat")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów bramki TDD")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
