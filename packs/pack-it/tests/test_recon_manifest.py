#!/usr/bin/env python3
"""Testy eng-codebase-mapping/scripts/recon_manifest.py: manifest rekonstrukcji (commit, partie z hashami, pliki)
i różnica po zmianach — które partie odświeżyć (odświeżanie przyrostowe). python3 .claude/tests/test_recon_manifest.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "eng-codebase-mapping" / "scripts" / "recon_manifest.py"

REPO = {
    "billing/pom.xml": "<project/>",
    "billing/src/main/java/a/Invoice.java": "class Invoice {}\n" * 40,
    "billing/src/test/java/a/InvoiceTest.java": "class InvoiceTest {}\n",
    "web/package.json": '{"name": "web"}',
    "web/src/app.ts": "export const x = 1;\n" * 30,
    "svc/go.mod": "module example.com/svc\n",
    "svc/main.go": "package main\n" * 20,
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
        repo, out = Path(d) / "repo", Path(d) / "manifest.json"
        write(repo, REPO)
        r = run("write", str(repo), "--out", str(out), "--budget-tokens", "60000", "--cost-usd", "1.25")
        check(r.returncode == 0 and out.is_file(), f"M-1: write działa: {r.stdout}{r.stderr}")
        m = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {}
        check(m.get("budget_tokens") == 60000 and m.get("cost_usd") == 1.25 and m.get("date"),
              f"M-2: budżet, koszt, data: {m}")
        check("commit" in m, f"M-3: pole commit (puste bez gita): {m.get('commit')!r}")
        names = {b["name"]: b for b in m.get("batches", [])}
        check({"billing", "web", "svc"} <= set(names) and all(len(b.get("hash", "")) == 64 for b in names.values()),
              f"M-4: partie z hashem sha256: {names}")
        check(m.get("files", {}).get("web/src/app.ts") and "billing/src/test/java/a/InvoiceTest.java" not in m.get("files", {}),
              f"M-5: hashe plików produkcyjnych, bez testów: {sorted(m.get('files', {}))}")

        r = run("diff", str(repo), "--manifest", str(out), "--json")
        d0 = json.loads(r.stdout) if r.returncode == 0 else {}
        check(r.returncode == 0 and d0.get("refresh") == [] and d0.get("changed_files") == [],
              f"M-6: bez zmian nic do odświeżenia: {r.stdout}{r.stderr}")

        write(repo, {"web/src/app.ts": "export const x = 2;\n", "svc/handler.go": "package main\n"})
        (repo / "billing/src/main/java/a/Invoice.java").unlink()
        write(repo, {"billing/src/main/java/a/Tax.java": "class Tax {}\n"})
        write(repo, {"billing/src/test/java/a/InvoiceTest.java": "class InvoiceTest { void t() {} }\n"})
        r = run("diff", str(repo), "--manifest", str(out), "--json")
        d1 = json.loads(r.stdout) if r.returncode == 0 else {}
        check(r.returncode == 0, f"M-7: diff działa: {r.stderr}")
        check(sorted(d1.get("refresh", [])) == ["billing", "svc", "web"], f"M-8: partie do odświeżenia: {d1.get('refresh')}")
        ch = d1.get("changed_files", [])
        check(ch == sorted(ch) and set(ch) == {"web/src/app.ts", "svc/handler.go", "billing/src/main/java/a/Invoice.java",
                                               "billing/src/main/java/a/Tax.java"},
              f"M-9: zmienione, dodane i usunięte pliki produkcyjne (bez testów): {ch}")
        check(d1.get("added_files") == ["billing/src/main/java/a/Tax.java", "svc/handler.go"]
              and d1.get("removed_files") == ["billing/src/main/java/a/Invoice.java"],
              f"M-10: dodane i usunięte osobno: {d1}")
        check(d1.get("tests_changed") == ["billing/src/test/java/a/InvoiceTest.java"],
              f"M-11: zmienione testy osobno (wymagania z testów): {d1.get('tests_changed')}")
        check(d1.get("unchanged") == [] and isinstance(d1.get("share"), (int, float)),
              f"M-12: unchanged i udział zmian: {d1}")

        write(repo, {"web/src/app.ts": "export const x = 1;\n" * 30, "svc/main.go": "package main\n" * 20})
        (repo / "svc/handler.go").unlink()
        r = run("diff", str(repo), "--manifest", str(out))
        line = next((x for x in r.stdout.splitlines() if x.startswith("Odśwież")), "")
        check(r.returncode == 0 and "billing" in line and "web" not in line and "svc" not in line,
              f"M-13: tekst: odświeżyć tylko billing: {r.stdout}")

        renamed = dict(m)
        renamed["batches"] = [b for b in m.get("batches", []) if b["name"] != "svc"]
        out2 = Path(d) / "m2.json"
        out2.write_text(json.dumps(renamed), encoding="utf-8")
        r = run("diff", str(repo), "--manifest", str(out2), "--json")
        d2 = json.loads(r.stdout) if r.returncode == 0 else {}
        check("svc" in d2.get("new_batches", []) and "svc" in d2.get("refresh", []), f"M-14: nowa partia do zrobienia: {d2}")
        check(d2.get("removed_batches") == [], f"M-15: usunięte partie: {d2.get('removed_batches')}")

        r = run("diff", str(repo), "--manifest", str(Path(d) / "nie-ma.json"))
        check(r.returncode == 2, "M-16: brak manifestu → kod 2")
        r = run("bzdura")
        check(r.returncode == 2, "M-17: złe polecenie → kod 2")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów recon_manifest")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
