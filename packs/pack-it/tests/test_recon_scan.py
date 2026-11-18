#!/usr/bin/env python3
"""Tests of eng-codebase-mapping/scripts/recon_scan.py: reconstruction step 1 in one command — five scans into raw/
and a concise summary for the model (without the full results in the context). python3 .claude/tests/test_recon_scan.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "eng-codebase-mapping" / "scripts" / "recon_scan.py"

REPO = {
    "pyproject.toml": "[project]\nname = 'shop'\nrequires-python = '>=3.11'\n[tool.pytest.ini_options]\n",
    ".github/workflows/ci.yml": "name: ci\non: push\njobs:\n  t:\n    runs-on: ubuntu-latest\n",
    "shop/billing/invoice.py": "from shop.customers.model import Customer\n\n\ndef total(lines):\n    if not lines:\n"
                               "        raise ValueError('empty')\n    return sum(lines)\n",
    "shop/customers/model.py": "from dataclasses import dataclass\n\n\n@dataclass\nclass Customer:\n    name: str\n",
    "shop/main.py": "from shop.billing.invoice import total\n\nif __name__ == '__main__':\n    print(total([1]))\n",
    "tests/test_invoice.py": "import pytest\nfrom shop.billing.invoice import total\n\n\n"
                             "@pytest.mark.parametrize('x', [[1]])\ndef test_total(x):\n    assert total(x) == 1\n",
    "db/V1__init.sql": "CREATE TABLE invoice (id INT PRIMARY KEY, amount INT NOT NULL);\n",
    "web/owner/OwnerController.java": "class OwnerController {}\n",
    "web/owner/OwnerRepository.java": "interface OwnerRepository {}\n",
    "web/model/BaseEntity.java": "class BaseEntity {}\n",
    "web/util/Strings.java": "class Strings {}\n",
}
RAW = ("inventory.json", "graph.json", "territory.json", "standards.json", "schema.json")


def write(root: Path, files: dict) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=120,
                          stdin=subprocess.DEVNULL, cwd=cwd)


def git(repo: Path, *args) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args], check=True,
                   capture_output=True)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        repo, out = Path(d) / "repo", Path(d) / "raw"
        write(repo, REPO)
        git(repo, "init", "-q")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "init")
        r = run(str(repo), "--out", str(out))
        check(r.returncode == 0 and all((out / f).is_file() for f in RAW),
              f"RS-1: five results in raw/: rc={r.returncode} {sorted(p.name for p in out.glob('*'))} {r.stderr[-300:]}")
        inv = json.loads((out / "inventory.json").read_text()) if (out / "inventory.json").is_file() else {}
        check(inv.get("budget_tokens") == 12000, f"RS-2: small repo → batch budget 12000: {inv.get('budget_tokens')}")
        s = r.stdout
        check(len(s.splitlines()) <= 60, f"RS-3: summary ≤ 60 lines: {len(s.splitlines())}")
        check("Languages: Python" in s and "Build files: pyproject.toml" in s and "CI: .github/workflows/ci.yml" in s,
              f"RS-4: languages, build files, CI: {s[:800]}")
        check("Batches (" in s and "shop/billing" in s, f"RS-5: the list of batches: {s[:800]}")
        check("Tables: invoice" in s, f"RS-6: tables from the schema: {s[:1200]}")
        check("@pytest.mark.parametrize" in s, f"RS-7: standards signals with idioms: {s[-1200:]}")
        check("layout · Java · packages by feature" in s, f"RS-11: package layout in the summary despite a share < 50%: {s[-1200:]}")
        check("raw/" in s or str(out) in s, f"RS-8: where the full results are: {s[-400:]}")

        # without git: history skipped, the rest works
        plain, out2 = Path(d) / "plain", Path(d) / "raw2"
        write(plain, REPO)
        r = run(str(plain), "--out", str(out2), "--budget-tokens", "60000")
        inv2 = json.loads((out2 / "inventory.json").read_text()) if (out2 / "inventory.json").is_file() else {}
        check(r.returncode == 0 and "history: no git" in r.stdout and inv2.get("budget_tokens") == 60000
              and not (out2 / "territory.json").exists(), f"RS-9: without git and with an explicit budget: rc={r.returncode} {r.stdout[-500:]}")
        r = run(str(Path(d) / "nie-ma"), "--out", str(out2))
        check(r.returncode == 2, f"RS-10: no repo → code 2: {r.returncode}")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of recon_scan")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
