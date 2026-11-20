#!/usr/bin/env python3
"""Tests of `dna.py check` (lib/check.py): the change against the guidelines, by the balance rule.
python3 addons/dna/tests/test_check.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

import dna  # noqa: E402
from lib import check  # noqa: E402
from test_code import FILES  # noqa: E402
from test_dna import repo  # noqa: E402


def git(root: Path, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def project() -> tuple[Path, dict]:
    root = repo(FILES)
    git(root, "init", "-q")
    git(root, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init")
    out = root / ".tf" / "addons" / "dna" / "out"
    assert dna.cmd_learn(root, out, online=False, cache=root / ".tf" / "addons" / "dna" / "cache") == 0
    return root, json.loads((out / "knowledge.json").read_text(encoding="utf-8"))


NEW = """import Button from '@mui/material/Button';
import { OldModal } from '../components/OldModal';
export function Card() { return null; }
export const New = () => <div><button onClick={go}>Pay</button><span style={{ color: '#0a66c2' }} /><OldModal /></div>;
"""


def by_rule(res) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for f in res["findings"]:
        out.setdefault(f["rule"], []).append(f)
    return out


def test_new_file_soft_findings_block():
    root, k = project()
    (root / "apps/web/src/pages/New.tsx").write_text(NEW, encoding="utf-8")
    rules = by_rule(check.check(root, k, "HEAD"))
    assert rules["raw-element"][0]["severity"] == "block"
    assert "import { Button } from '@mui/material'" in rules["raw-element"][0]["suggestion"]
    assert rules["value-with-token"][0]["message"].startswith("#0a66c2 has a token")
    assert rules["duplicate-component"][0]["severity"] == "block"
    assert rules["import-form"][0]["suggestion"] == "import { Button } from '@mui/material'"
    assert all(f["severity"] == "block" and f["strength"] == "hard" for f in rules["deprecated-component"])
    assert all(f["file"] == "apps/web/src/pages/New.tsx" for f in sum(rules.values(), []))


def test_existing_file_soft_warns_hard_blocks():
    root, k = project()
    p = root / "apps/web/src/pages/Orders.tsx"
    p.write_text(p.read_text(encoding="utf-8") + "export const X = () => <button>ok</button>;\n"
                                                 "export const Y = () => <OldModal />;\n", encoding="utf-8")
    rules = by_rule(check.check(root, k, "HEAD"))
    assert rules["raw-element"][0]["severity"] == "warn" and rules["raw-element"][0]["line"] == 6
    assert rules["deprecated-component"][0]["severity"] == "block" and rules["deprecated-component"][0]["line"] == 7


def test_styling_method_absent_from_the_code_is_rare():
    root, k = project()
    (root / "apps/web/src/pages/Styled.tsx").write_text(
        "import styled from '@emotion/styled';\nconst Box = styled.div`color: red`;\n", encoding="utf-8")
    rules = by_rule(check.check(root, k, "HEAD"))
    assert rules["styling-method"][0]["message"].startswith("styled is rare here (0%)")
    assert "css-modules" in rules["styling-method"][0]["suggestion"]


def test_clean_change_and_cli_exit_codes():
    root, _ = project()
    run = lambda: subprocess.run([sys.executable, str(ADDON / "dna.py"), "check", "--root", str(root), "--out",  # noqa: E731
                                  str(root / ".tf/addons/dna/out"), "--json"], capture_output=True, text=True)
    p = root / "apps/web/src/pages/Orders.tsx"
    p.write_text(p.read_text(encoding="utf-8") + "export const Z = () => <Stack><Button /></Stack>;\n",
                 encoding="utf-8")
    ok = run()
    assert ok.returncode == 0 and json.loads(ok.stdout)["findings"] == []
    (root / "apps/web/src/pages/New.tsx").write_text(NEW, encoding="utf-8")
    bad = run()
    assert bad.returncode == 1 and json.loads(bad.stdout)["findings"]


def test_no_guidelines_is_not_blocking():
    root = repo({"a.txt": "x\n"})
    git(root, "init", "-q")
    r = subprocess.run([sys.executable, str(ADDON / "dna.py"), "check", "--root", str(root), "--out",
                        str(root / "none")], capture_output=True, text=True)
    assert r.returncode == 0 and "no guidelines" in r.stderr


def main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"✗ {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - fails}/{len(tests)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
