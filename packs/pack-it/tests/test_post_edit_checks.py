#!/usr/bin/env python3
"""Testy szablonu hooka post_edit_checks (skill eng-local-quality-gates): bramki po edycji z .claude/quality-gates.json."""
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

        # 1. brak konfiguracji → cisza
        code, out, err, _ = run("src/a.ts")
        check(code == 0 and not out.strip() and not err.strip(), f"brak konfiguracji → nic: {code} {out!r} {err!r}")

        # 2. plik nie pasuje do globu → cisza
        write_cfg([{"glob": "src/**/*.{ts,tsx}", "cmd": py("import sys; sys.exit(3)")}])
        code, out, err, _ = run("src/a.js")
        check(code == 0 and not err.strip(), f"plik spoza globu → nic: {code} {err!r}")

        # 3. glob z ** i {ts,tsx}: pasuje płytko i głęboko
        code, _, err, _ = run("src/a.ts")
        check(code == 2, f"src/a.ts pasuje do src/**/*.{{ts,tsx}} → porażka komendy → 2: {code} {err!r}")
        code, _, _, _ = run("src/ui/deep/b.tsx")
        check(code == 2, f"src/ui/deep/b.tsx pasuje do src/**/*.{{ts,tsx}}: {code}")

        # 4. komenda przechodzi → kod 0, bez wyjścia
        write_cfg([{"glob": "src/**/*.ts", "cmd": py("print('ok')")}])
        code, out, err, _ = run("src/a.ts")
        check(code == 0 and not err.strip(), f"zielona komenda → 0 bez stderr: {code} {err!r}")

        # 5. porażka → kod 2, na stderr nazwa i końcówka wyjścia (limit linii)
        many = "import sys\nfor i in range(200): print('linia', i)\nsys.exit(1)"
        (proj / "fail.py").write_text(many, encoding="utf-8")
        write_cfg([{"name": "testy powiązane", "glob": "src/billing/**", "cmd": f'"{PY}" fail.py', "max_lines": 20}])
        code, out, err, _ = run("src/billing/invoice.ts")
        check(code == 2 and "testy powiązane" in err and "linia 199" in err and "linia 100" not in err,
              f"porażka → 2, końcówka wyjścia ≤ max_lines: {code} {err[-400:]!r}")
        check("src/billing/invoice.ts" in err, f"komunikat wskazuje plik: {err[:200]!r}")

        # 6. {file} podstawiane jako jeden argument, bez powłoki (spacje w nazwie)
        (proj / "argv.py").write_text(
            "import sys, json\nopen('argv.json', 'w', encoding='utf-8').write(json.dumps(sys.argv[1:]))\n",
            encoding="utf-8")
        write_cfg([{"glob": "src/*.ts", "cmd": f'"{PY}" argv.py --plik {{file}}'}])
        code, _, err, _ = run("src/z ze spacją.ts")
        argv = json.loads((proj / "argv.json").read_text(encoding="utf-8")) if (proj / "argv.json").exists() else None
        check(code == 0 and argv == ["--plik", "src/z ze spacją.ts"], f"{{file}} jako jeden argument: {code} {argv} {err!r}")

        # 7. zmienne środowiskowe z konfiguracji trafiają do komendy
        write_cfg([{"glob": "src/a.ts", "cmd": py("import os,sys; sys.exit(0 if os.environ.get('AI_AGENT')=='1' else 5)"),
                    "env": {"AI_AGENT": "1"}}])
        code, _, err, _ = run("src/a.ts")
        check(code == 0, f"env z konfiguracji przekazany: {code} {err!r}")

        # 8. UTF-8 na wyjściu niezależnie od kodowania konsoli
        (proj / "pl.py").write_text("import sys\nsys.stdout.buffer.write('zażółć gęślą jaźń\\n'.encode('utf-8'))\n"
                                    "sys.exit(1)\n", encoding="utf-8")
        write_cfg([{"glob": "src/a.ts", "cmd": f'"{PY}" pl.py'}])
        code, _, err, _ = run("src/a.ts", env_extra={"PYTHONIOENCODING": "ascii"})
        check(code == 2 and "zażółć gęślą jaźń" in err, f"polskie znaki w UTF-8 mimo PYTHONIOENCODING=ascii: {err!r}")
        data_pl = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(proj / "src" / "z ze spacją.ts")}},
                             ensure_ascii=False)
        write_cfg([{"glob": "src/*.ts", "cmd": py("import sys; sys.exit(1)")}])
        code, _, err, _ = run("", env_extra={"PYTHONIOENCODING": "ascii"}, stdin=data_pl)
        check(code == 2 and "spacją" in err, f"wejście JSON z polskimi znakami czytane jako UTF-8: {code} {err!r}")

        # 9. przekroczony limit komendy → bez blokady, rada „pre-commit”, hook kończy się szybko
        write_cfg([{"glob": "src/a.ts", "cmd": py("import time; time.sleep(20)"), "timeout": 1}])
        code, out, err, dt = run("src/a.ts")
        ctx = json.loads(out).get("hookSpecificOutput", {}).get("additionalContext", "") if out.strip() else ""
        check(code == 0 and "pre-commit" in ctx and dt < 10, f"timeout komendy → 0 + rada: {code} {out!r} {dt:.1f}s")

        # 10. własny limit całego hooka (CLAUDE_QG_DEADLINE) — kończy się sam przed limitem Claude Code
        write_cfg([{"glob": "src/a.ts", "cmd": py("import time; time.sleep(30)"), "timeout": 60}])
        code, out, err, dt = run("src/a.ts", env_extra={"CLAUDE_QG_DEADLINE": "1"})
        check(code == 0 and dt < 8, f"limit hooka → kod 0 w ~1 s: {code} {dt:.1f}s {err!r}")

        # 11. błędna konfiguracja → bez blokady, komunikat dla człowieka
        cfg_path.write_text("{ to nie json", encoding="utf-8")
        code, out, err, _ = run("src/a.ts")
        check(code == 0 and "quality-gates.json" in out, f"zły JSON → 0 + systemMessage: {code} {out!r}")

        # 12. brak programu → bez blokady, ostrzeżenie
        write_cfg([{"glob": "src/a.ts", "cmd": "program-ktorego-nie-ma-123 {file}"}])
        code, out, err, _ = run("src/a.ts")
        check(code == 0 and "program-ktorego-nie-ma-123" in out, f"brak programu → 0 + ostrzeżenie: {code} {out!r}")

        # 13. wyłączenie, inne narzędzia, plik spoza projektu
        write_cfg([{"glob": "**", "cmd": py("import sys; sys.exit(1)")}])
        code, _, _, _ = run("src/a.ts", env_extra={"CLAUDE_QUALITY_GATES": "off"})
        check(code == 0, f"CLAUDE_QUALITY_GATES=off → nic: {code}")
        code, _, _, _ = run("src/a.ts", tool="Read")
        check(code == 0, f"narzędzie Read → nic: {code}")
        outside = Path(tempfile.gettempdir()) / "poza-projektem.ts"
        code, _, _, _ = run(str(outside))
        check(code == 0, f"plik spoza projektu → nic: {code}")
        code, _, _, _ = run("src/a.ts", tool="Write")
        check(code == 2, f"Write też objęty: {code}")

        # 14. kilka sprawdzeń: wszystkie pasujące uruchomione, porażki zebrane
        write_cfg([{"name": "format", "glob": "src/*.ts", "cmd": py("import sys; sys.exit(0)")},
                   {"name": "lint", "glob": "src/*.ts", "cmd": py("import sys; print('E1 brak średnika'); sys.exit(1)")},
                   {"name": "typy", "glob": "src/*.ts", "cmd": py("import sys; print('TS2322'); sys.exit(2)")}])
        code, _, err, _ = run("src/a.ts")
        check(code == 2 and "lint" in err and "typy" in err and "E1 brak średnika" in err and "TS2322" in err,
              f"zebrane porażki wielu sprawdzeń: {err!r}")

        # 15. tryb --dry-run / --json: lista pasujących sprawdzeń bez uruchamiania
        code, out, err, _ = run("", args=("--dry-run", "src/a.ts"), stdin="")
        check(code == 0 and "lint" in out and "typy" in out, f"--dry-run wypisuje pasujące: {code} {out!r} {err!r}")
        code, out, err, _ = run("", args=("--dry-run", "src/a.ts", "--json"), stdin="")
        try:
            parsed = json.loads(out)
            ok = isinstance(parsed.get("checks"), list) and len(parsed["checks"]) == 3
        except ValueError:
            ok = False
        check(code == 0 and ok, f"--json zwraca listę sprawdzeń: {out!r}")
        code, out, _, _ = run("", args=("--help",), stdin="")
        check(code == 0 and "quality-gates.json" in out, f"--help: {code}")

        # 16. przykładowa konfiguracja ze skilla jest poprawna i kieruje pliki do właściwych sprawdzeń
        example = HOOK.parent / "quality-gates.example.json"
        cfg_path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        code, out, err, _ = run("", args=("--dry-run", "src/billing/invoice.ts", "--json"), stdin="")
        names = [c["name"] for c in json.loads(out)["checks"]] if code == 0 else []
        check(len(names) == 2 and any("eslint" in n for n in names) and any("powiązane" in n for n in names),
              f"przykład: plik rozliczeń → eslint + testy powiązane: {names} {err!r}")
        code, out, err, _ = run("", args=("--dry-run", "src/ui/deep/b.tsx", "--json"), stdin="")
        names = [c["name"] for c in json.loads(out)["checks"]] if code == 0 else []
        check(len(names) == 1 and "eslint" in names[0], f"przykład: komponent UI → tylko eslint: {names}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów hooka post_edit_checks")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
