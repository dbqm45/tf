#!/usr/bin/env python3
"""Testy eng-codebase-mapping/scripts/standards_scan.py: konwencje z kodu z udziałem, przykładami plik:linia
i wyjątkami — sygnały do standardów rekonstrukcji. python3 .claude/tests/test_standards_scan.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "eng-codebase-mapping" / "scripts" / "standards_scan.py"

REPO = {
    ".editorconfig": "root = true\n[*]\nindent_style = space\n",
    "eslint.config.js": "export default [];\n",
    "pyproject.toml": "[tool.ruff]\nline-length = 100\n[tool.pytest.ini_options]\n",
    "app/user_service.py": "import logging\nlog = logging.getLogger(__name__)\n\ndef f():\n    try:\n        pass\n"
                           "    except Exception:\n        log.exception('x')\n",
    "app/order_service.py": "import logging\n\ndef g():\n    try:\n        pass\n    except:\n        pass\n",
    "app/PaymentGateway.py": "def h():\n    print('debug')\n",
    "app/tests/test_user.py": "import pytest\n\ndef test_x():\n    assert True\n",
    "app/tests/test_order.py": "import pytest\n\ndef test_y():\n    assert True\n",
    "web/src/user-card.ts": "export const a = 1;\n// TODO: usunąć\n",
    "web/src/order-list.ts": "export const b = 2;\n",
    "web/src/OrderItem.ts": "export const c = 3;\n",
    "web/src/user-card.test.ts": "import { test } from 'vitest';\ntest('x', () => {});\n",
}


def write(root: Path, files: dict) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60,
                          stdin=subprocess.DEVNULL)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        write(repo, REPO)
        r = run(str(repo), "--json")
        check(r.returncode == 0, f"S-1: działa: {r.stderr[-300:]}")
        out = json.loads(r.stdout) if r.returncode == 0 else {}
        tools = {(t["tool"], t["file"]) for t in out.get("tools", [])}
        check({("editorconfig", ".editorconfig"), ("eslint", "eslint.config.js"), ("ruff", "pyproject.toml"),
               ("pytest", "pyproject.toml")} <= tools, f"S-2: narzędzia z konfiguracji: {sorted(tools)}")
        sig = {(s["area"], s["language"], s["rule"]): s for s in out.get("signals", [])}
        py = sig.get(("nazwy plików", "Python", "snake_case"))
        check(py and py["count"] == 2 and py["total"] == 3 and py["share"] == 67
              and any(e.startswith("app/PaymentGateway.py") for e in py["exceptions"]),
              f"S-3: nazwy plików Python 2/3 snake_case, wyjątek PaymentGateway.py: {py}")
        ts = sig.get(("nazwy plików", "TypeScript", "kebab-case"))
        check(ts and ts["count"] == 2 and ts["total"] == 3 and any("OrderItem.ts" in e for e in ts["exceptions"]),
              f"S-4: nazwy plików TS kebab-case 2/3: {ts}")
        tf = sig.get(("testy", "Python", "pytest"))
        check(tf and tf["count"] == 2 and any(e.startswith("app/tests/test_user.py:1") for e in tf["examples"]),
              f"S-5: framework testów z przykładem plik:linia: {tf}")
        check(("testy", "TypeScript", "vitest") in sig, f"S-6: vitest: {[k for k in sig if k[0] == 'testy']}")
        loc = sig.get(("testy", "Python", "osobny katalog tests/"))
        check(loc and loc["count"] == 2, f"S-7: położenie testów Python: {loc}")
        bare = sig.get(("błędy", "Python", "except bez typu"))
        check(bare and bare["count"] == 1 and any(e.startswith("app/order_service.py:6") for e in bare["examples"]),
              f"S-8: goły except z miejscem: {bare}")
        lg = sig.get(("logowanie", "Python", "logging"))
        check(lg and lg["count"] == 2, f"S-9: logging w 2 plikach: {lg}")
        pr = sig.get(("logowanie", "Python", "print"))
        check(pr and pr["count"] == 1, f"S-10: print jako logowanie: {pr}")
        todo = sig.get(("dług", "TypeScript", "TODO/FIXME"))
        check(todo and any(e.startswith("web/src/user-card.ts:2") for e in todo["examples"]), f"S-11: TODO: {todo}")
        r = run(str(repo))
        check(r.returncode == 0 and "snake_case" in r.stdout and "67%" in r.stdout, f"S-12: tekst: {r.stdout[:400]}")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów standards_scan")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
