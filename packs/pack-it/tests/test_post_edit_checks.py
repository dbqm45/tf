#!/usr/bin/env python3
"""Tests of the post_edit_checks hook template (skill eng-local-quality-gates): post-edit gates from .claude/quality-gates.json."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
HOOK = ROOT / ".claude" / "skills" / "eng-local-quality-gates" / "templates" / "post_edit_checks.py"
PY = sys.executable


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        (proj / "src" / "billing").mkdir(parents=True)
        (proj / "src" / "ui" / "deep").mkdir(parents=True)
        (proj / ".claude").mkdir()
        for rel in ("src/a.ts", "src/a.js", "src/ui/deep/b.tsx", "src/billing/invoice.ts", "src/z ze spacją.ts"):
            (proj / rel).write_text("x\n", encoding="utf-8")
        cfg_path = proj / ".claude" / "quality-gates.json"

        def write_cfg(checks, **extra):
            cfg_path.write_text(json.dumps({"checks": checks, **extra}, ensure_ascii=False), encoding="utf-8")

        def run(rel, tool="Edit", env_extra=None, args=(), stdin=None):
            data = {"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": str(proj),
                    "tool_input": {"file_path": str(proj / rel) if not os.path.isabs(rel) else rel}}
            env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj), **(env_extra or {})}
            env.pop("CLAUDE_QUALITY_GATES", None) if "CLAUDE_QUALITY_GATES" not in (env_extra or {}) else None
            t0 = time.monotonic()
            r = subprocess.run([PY, str(HOOK), *args], input=(stdin if stdin is not None else json.dumps(data)).encode(),
                               capture_output=True, env=env, timeout=60, cwd=str(proj))
            return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace"), \
                time.monotonic() - t0

        def py(code):
            return f'"{PY}" -c "{code}"'

        # 1. no configuration → silence
        code, out, err, _ = run("src/a.ts")
        check(code == 0 and not out.strip() and not err.strip(), f"no configuration → nothing: {code} {out!r} {err!r}")

        # 2. the file does not match the glob → silence
        write_cfg([{"glob": "src/**/*.{ts,tsx}", "cmd": py("import sys; sys.exit(3)")}])
        code, out, err, _ = run("src/a.js")
        check(code == 0 and not err.strip(), f"a file outside the glob → nothing: {code} {err!r}")

        # 3. glob with ** and {ts,tsx}: matches shallow and deep
        code, _, err, _ = run("src/a.ts")
        check(code == 2, f"src/a.ts matches src/**/*.{{ts,tsx}} → command failure → 2: {code} {err!r}")
        code, _, _, _ = run("src/ui/deep/b.tsx")
        check(code == 2, f"src/ui/deep/b.tsx matches src/**/*.{{ts,tsx}}: {code}")

        # 4. the command passes → code 0, no output
        write_cfg([{"glob": "src/**/*.ts", "cmd": py("print('ok')")}])
        code, out, err, _ = run("src/a.ts")
        check(code == 0 and not err.strip(), f"a green command → 0 without stderr: {code} {err!r}")

        # 5. failure → code 2, the name and the tail of the output on stderr (line limit)
        many = "import sys\nfor i in range(200): print('line', i)\nsys.exit(1)"
        (proj / "fail.py").write_text(many, encoding="utf-8")
        write_cfg([{"name": "related tests", "glob": "src/billing/**", "cmd": f'"{PY}" fail.py', "max_lines": 20}])
        code, out, err, _ = run("src/billing/invoice.ts")
        check(code == 2 and "related tests" in err and "line 199" in err and "line 100" not in err,
              f"failure → 2, output tail ≤ max_lines: {code} {err[-400:]!r}")
        check("src/billing/invoice.ts" in err, f"the message points to the file: {err[:200]!r}")

        # 6. {file} substituted as one argument, without a shell (spaces in the name)
        (proj / "argv.py").write_text(
            "import sys, json\nopen('argv.json', 'w', encoding='utf-8').write(json.dumps(sys.argv[1:]))\n",
            encoding="utf-8")
        write_cfg([{"glob": "src/*.ts", "cmd": f'"{PY}" argv.py --file {{file}}'}])
        code, _, err, _ = run("src/z ze spacją.ts")
        argv = json.loads((proj / "argv.json").read_text(encoding="utf-8")) if (proj / "argv.json").exists() else None
        check(code == 0 and argv == ["--file", "src/z ze spacją.ts"], f"{{file}} as one argument: {code} {argv} {err!r}")

        # 7. environment variables from the configuration reach the command
        write_cfg([{"glob": "src/a.ts", "cmd": py("import os,sys; sys.exit(0 if os.environ.get('AI_AGENT')=='1' else 5)"),
                    "env": {"AI_AGENT": "1"}}])
        code, _, err, _ = run("src/a.ts")
        check(code == 0, f"env from the configuration passed on: {code} {err!r}")

        # 8. UTF-8 on the output regardless of the console encoding
        (proj / "pl.py").write_text("import sys\nsys.stdout.buffer.write('zażółć gęślą jaźń\\n'.encode('utf-8'))\n"
                                    "sys.exit(1)\n", encoding="utf-8")
        write_cfg([{"glob": "src/a.ts", "cmd": f'"{PY}" pl.py'}])
        code, _, err, _ = run("src/a.ts", env_extra={"PYTHONIOENCODING": "ascii"})
        check(code == 2 and "zażółć gęślą jaźń" in err, f"Polish characters in UTF-8 despite PYTHONIOENCODING=ascii: {err!r}")
        data_pl = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(proj / "src" / "z ze spacją.ts")}},
                             ensure_ascii=False)
        write_cfg([{"glob": "src/*.ts", "cmd": py("import sys; sys.exit(1)")}])
        code, _, err, _ = run("", env_extra={"PYTHONIOENCODING": "ascii"}, stdin=data_pl)
        check(code == 2 and "spacją" in err, f"JSON input with Polish characters read as UTF-8: {code} {err!r}")

        # 9. command timeout exceeded → no block, a "pre-commit" advice, the hook finishes quickly
        write_cfg([{"glob": "src/a.ts", "cmd": py("import time; time.sleep(20)"), "timeout": 1}])
        code, out, err, dt = run("src/a.ts")
        ctx = json.loads(out).get("hookSpecificOutput", {}).get("additionalContext", "") if out.strip() else ""
        check(code == 0 and "pre-commit" in ctx and dt < 10, f"command timeout → 0 + advice: {code} {out!r} {dt:.1f}s")

        # 10. the hook's own overall limit (CLAUDE_QG_DEADLINE) — it ends by itself before the Claude Code limit
        write_cfg([{"glob": "src/a.ts", "cmd": py("import time; time.sleep(30)"), "timeout": 60}])
        code, out, err, dt = run("src/a.ts", env_extra={"CLAUDE_QG_DEADLINE": "1"})
        check(code == 0 and dt < 8, f"hook limit → code 0 in ~1 s: {code} {dt:.1f}s {err!r}")

        # 11. invalid configuration → no block, a message for the human
        cfg_path.write_text("{ this is not json", encoding="utf-8")
        code, out, err, _ = run("src/a.ts")
        check(code == 0 and "quality-gates.json" in out, f"bad JSON → 0 + systemMessage: {code} {out!r}")

        # 12. missing program → no block, a warning
        write_cfg([{"glob": "src/a.ts", "cmd": "program-that-does-not-exist-123 {file}"}])
        code, out, err, _ = run("src/a.ts")
        check(code == 0 and "program-that-does-not-exist-123" in out, f"missing program → 0 + warning: {code} {out!r}")

        # 13. switching off, other tools, a file outside the project
        write_cfg([{"glob": "**", "cmd": py("import sys; sys.exit(1)")}])
        code, _, _, _ = run("src/a.ts", env_extra={"CLAUDE_QUALITY_GATES": "off"})
        check(code == 0, f"CLAUDE_QUALITY_GATES=off → nothing: {code}")
        code, _, _, _ = run("src/a.ts", tool="Read")
        check(code == 0, f"Read tool → nothing: {code}")
        outside = Path(tempfile.gettempdir()) / "outside-project.ts"
        code, _, _, _ = run(str(outside))
        check(code == 0, f"file outside the project → nothing: {code}")
        code, _, _, _ = run("src/a.ts", tool="Write")
        check(code == 2, f"Write is covered too: {code}")

        # 14. several checks: all matching ones run, failures collected
        write_cfg([{"name": "format", "glob": "src/*.ts", "cmd": py("import sys; sys.exit(0)")},
                   {"name": "lint", "glob": "src/*.ts", "cmd": py("import sys; print('E1 missing semicolon'); sys.exit(1)")},
                   {"name": "types", "glob": "src/*.ts", "cmd": py("import sys; print('TS2322'); sys.exit(2)")}])
        code, _, err, _ = run("src/a.ts")
        check(code == 2 and "lint" in err and "types" in err and "E1 missing semicolon" in err and "TS2322" in err,
              f"failures of several checks collected: {err!r}")

        # 15. the --dry-run / --json mode: a list of matching checks without running them
        code, out, err, _ = run("", args=("--dry-run", "src/a.ts"), stdin="")
        check(code == 0 and "lint" in out and "types" in out, f"--dry-run prints the matching ones: {code} {out!r} {err!r}")
        code, out, err, _ = run("", args=("--dry-run", "src/a.ts", "--json"), stdin="")
        try:
            parsed = json.loads(out)
            ok = isinstance(parsed.get("checks"), list) and len(parsed["checks"]) == 3
        except ValueError:
            ok = False
        check(code == 0 and ok, f"--json returns a list of checks: {out!r}")
        code, out, _, _ = run("", args=("--help",), stdin="")
        check(code == 0 and "quality-gates.json" in out, f"--help: {code}")

        # 16. the example configuration from the skill is valid and routes files to the right checks
        example = HOOK.parent / "quality-gates.example.json"
        cfg_path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        code, out, err, _ = run("", args=("--dry-run", "src/billing/invoice.ts", "--json"), stdin="")
        names = [c["name"] for c in json.loads(out)["checks"]] if code == 0 else []
        check(len(names) == 2 and any("eslint" in n for n in names) and any("powiązane" in n or "related" in n for n in names),
              f"example: a billing file → eslint + related tests: {names} {err!r}")
        code, out, err, _ = run("", args=("--dry-run", "src/ui/deep/b.tsx", "--json"), stdin="")
        names = [c["name"] for c in json.loads(out)["checks"]] if code == 0 else []
        check(len(names) == 1 and "eslint" in names[0], f"example: a UI component → eslint only: {names}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of the post_edit_checks hook")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
