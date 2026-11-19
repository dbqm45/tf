#!/usr/bin/env python3
"""Tests of eng-codebase-mapping/scripts/recon_refresh.py: refreshing the reconstruction in two steps without a model —
prep (the manifest diff, a copy of the cards, orders for the executors with the diff, comment-only changes without orders,
recomputing shifted lines) and finish (cards → .md, rules.md, the Modules section, a list of
places with the old description, the final check, the manifest). python3 .claude/tests/test_recon_refresh.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPTS = ROOT / ".claude" / "skills" / "eng-codebase-mapping" / "scripts"
DOCS = "docs/project/00-reconstruction"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import recon_refresh  # noqa: E402

CODE = {
    "svc/billing/invoice.py": "def total(lines):\n    # faktura bez pozycji jest błędem\n"
                              "    if not lines:\n        raise ValueError('empty')\n    return sum(lines)\n",
    "svc/billing/tax.py": "RATE = 0.23\n",
    "svc/customers/model.py": "class Customer:\n    pass\n",
}
BILLING = {"module": "billing", "batch": "svc/billing", "purpose": "Liczy faktury.",
           "rules": [{"rule": "Faktura bez pozycji jest odrzucana (kod 422).", "evidence": "svc/billing/invoice.py:4",
                      "quote": "raise ValueError('empty')", "confidence": "kod"},
                     {"rule": "VAT wynosi 23%.", "evidence": "svc/billing/tax.py:1", "quote": "RATE = 0.23", "confidence": "kod"}]}
CUSTOMERS = {"module": "customers", "batch": "svc/customers", "purpose": "Klienci.",
             "terms": [{"term": "klient", "code_name": "Customer", "evidence": "svc/customers/model.py:1"}]}
JAVA = "package billing;\n/* Stawki */\npublic class Rate {\n    // VAT\n    static final double VAT = 0.23;\n}\n"
REPORT = """# Rekonstrukcja
## TL;DR
Fakturowanie (`svc/billing/invoice.py:1`).
## Stack
| Obszar | Ustalenie | Dowód |
|---|---|---|
| Language | Python 3 [assumption] | — |
| Framework | brak [assumption] | — |
| Data | brak [unverified] | — |
| Build | brak [assumption] | — |
| Tests | brak [unverified] | — |
| CI | brak [unverified] | — |
| Configuration | stała w kodzie | `svc/billing/tax.py:1` |
## Modules
- (wstawia recon_cards)
## Domains
- Fakturowanie — `svc/billing/invoice.py:1`
- Faktura bez pozycji jest odrzucana przez system — `svc/billing/tax.py:1`
## Requirements
- Pusta faktura jest odrzucana kodem 422; dotyczy faktur sprzedaży i korekt, wystawianych ręcznie w panelu oraz automatycznie z zamówień sklepu, także po imporcie z systemu księgowego — `svc/billing/invoice.py:4`
## Rules
- VAT 23% — `svc/billing/tax.py:1`
## Standards
- [unverified] snake_case
## Risks
- Brak testów — `svc/billing/invoice.py:1`
## Questions
- [question] Czy VAT zależy od kraju?
## Not checked
- Wdrożenie.
"""


def write(root: Path, files: dict) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def git(repo: Path, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
                   check=True, capture_output=True)


def run(script, *args, cwd=None, input=None):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True, timeout=120,
                          input=input, stdin=None if input is not None else subprocess.DEVNULL, cwd=cwd)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        rep = repo / DOCS
        write(repo, CODE)
        write(rep, {"modules/billing.json": json.dumps(BILLING, ensure_ascii=False),
                    "modules/customers.json": json.dumps(CUSTOMERS, ensure_ascii=False), "report.md": REPORT})
        r = run("recon_manifest.py", "write", str(repo), "--out", str(rep / "manifest.json"), "--budget-tokens", "12000")
        check(r.returncode == 0, f"RF-0: the base manifest: {r.stderr[-300:]}")

        # no code changes: nothing to do
        r = run("recon_refresh.py", "prep", str(repo), cwd=d)
        check(r.returncode == 0 and "Nothing to refresh" in r.stdout and not (rep / "raw/refresh").exists(),
              f"RF-1: no changes: rc={r.returncode} {r.stdout[-400:]} {r.stderr[-300:]}")

        # a change in a file quoted by the billing card + a new file without a card
        write(repo, {"svc/billing/invoice.py": CODE["svc/billing/invoice.py"].replace("if not lines:", "if len(lines) < 2:"),
                     "svc/shipping/ship.py": "def ship():\n    pass\n"})
        r = run("recon_refresh.py", "prep", str(repo), cwd=d)
        out = r.stdout
        task = rep / "raw/refresh/billing.md"
        body = task.read_text(encoding="utf-8") if task.exists() else ""
        check(r.returncode == 0 and (rep / "raw/cards-prev/billing.json").exists() and (rep / "raw/cards-prev/customers.json").exists(),
              f"RF-2: a copy of all cards in raw/cards-prev: {out[-400:]} {r.stderr[-300:]}")
        check("svc/billing/invoice.py" in body and "modules/billing.json" in body and "svc/billing/tax.py" not in body.split("Changed files")[-1],
              f"RF-3: an order for the billing card with the changed file: {body[-600:]}")
        check(not (rep / "raw/refresh/customers.md").exists(), "RF-4: a card without changed files gets no order")
        check("billing" in out and "svc/shipping/ship.py" in out and "without a card" in out and len(out.splitlines()) <= 40,
              f"RF-5: a plan with a card, a file without a card and ≤ 40 lines: {out}")

        # the executor updated the card: the rule "422" changed to "at least two items" (Polish data)
        new = dict(BILLING, rules=[{"rule": "Faktura musi mieć co najmniej dwie pozycje.", "evidence": "svc/billing/invoice.py:3",
                                    "quote": "if len(lines) < 2:", "confidence": "kod"}, BILLING["rules"][1]])
        write(rep, {"modules/billing.json": json.dumps(new, ensure_ascii=False)})
        before = json.loads((rep / "manifest.json").read_text(encoding="utf-8"))
        r = run("recon_refresh.py", "finish", str(repo), cwd=d)
        out = r.stdout
        stale = rep / "raw/refresh/STALE.md"
        check("To check:" in out and "report.md:" in out and stale.exists() and "422" in stale.read_text(encoding="utf-8"),
              f"RF-6: the list of places with the old description on screen and in STALE.md: {out[-800:]}")
        check("z systemu księgowego — `svc/billing/invoice.py:4`" in out,
              f"RF-24: a place to fix with the full line text: {out[-900:]}")
        check(any("similar" in ln and "Faktura bez pozycji jest odrzucana przez system" in ln and "co najmniej dwie pozycje" in ln
                  for ln in out.splitlines()),
              f"RF-30: a description similar to the changed card rule on the list, with the new rule content: {out[-900:]}")
        check("- billing:" in (rep / "report.md").read_text(encoding="utf-8") and (rep / "modules/billing.md").exists()
              and (rep / "rules.md").exists(), "RF-7: the Modules section, the cards' .md and rules.md assembled")
        check("Final check:" in out and len(out.splitlines()) <= 60, f"RF-8: a concise check summary: {out[-600:]}")

        # after the description fix the check passes and the manifest gets the new state
        rp = (rep / "report.md").read_text(encoding="utf-8").replace("odrzucana kodem 422", "odrzucana, gdy ma mniej niż dwie pozycje")
        write(rep, {"report.md": rp, "reconstruction.json": json.dumps({"format": "tf-reconstruction", "rules": []})})
        r = run("recon_refresh.py", "finish", str(repo), cwd=d)
        after = json.loads((rep / "manifest.json").read_text(encoding="utf-8"))
        exported = json.loads((rep / "reconstruction.json").read_text(encoding="utf-8"))
        check(any(i.get("text") == "Faktura musi mieć co najmniej dwie pozycje." for i in exported.get("rules", []))
              and exported.get("commit") == after.get("commit"),
              f"RF-31: finish refreshes the existing JSON export (a new rule, the commit from the manifest): {exported.get('rules')}")
        check(r.returncode == 0 and "✓ manifest" in r.stdout and after["files"] != before["files"]
              and "svc/shipping/ship.py" in after["files"], f"RF-9: the manifest saved after the check passes: {r.stdout[-600:]}")
        r = run("recon_refresh.py", "prep", str(repo), cwd=d)
        check("Nothing to refresh" in r.stdout, f"RF-10: after the refresh the manifest matches the code: {r.stdout[-300:]}")
        # evidence shifted by a code change (the quote unambiguously on another line) → finish fixes the line number
        write(repo, {"svc/billing/tax.py": "# stawki\n# VAT\n# PL\n# 2026\nRATE = 0.23\n"})
        rp = (rep / "report.md").read_text(encoding="utf-8")
        write(rep, {"report.md": rp.replace("- VAT 23% — `svc/billing/tax.py:1`", '- VAT 23% — `svc/billing/tax.py:1` "RATE = 0.23"')
                    .replace("| Configuration | stała w kodzie | `svc/billing/tax.py:1` |", "| Configuration | stała w kodzie | `svc/billing/tax.py:5` |")})
        moved = dict(new, rules=[new["rules"][0], dict(BILLING["rules"][1], evidence="svc/billing/tax.py:5")])
        write(rep, {"modules/billing.json": json.dumps(moved, ensure_ascii=False)})
        r = run("recon_refresh.py", "finish", str(repo), cwd=d)
        rp = (rep / "report.md").read_text(encoding="utf-8")
        check('`svc/billing/tax.py:5` "RATE = 0.23"' in rp and "shifted evidence: 1" in r.stdout and r.returncode == 0,
              f"RF-12: the shifted evidence fixed automatically: rc={r.returncode} {r.stdout[-700:]}")
        # changed card rules on screen: old → new
        write(rep, {"raw/cards-prev/billing.json": json.dumps(BILLING, ensure_ascii=False)})
        r = run("recon_refresh.py", "finish", str(repo), cwd=d)
        check("Changed card rules" in r.stdout and "kod 422" in r.stdout and "co najmniej dwie pozycje" in r.stdout,
              f"RF-13: rule changes old → new: {r.stdout[-700:]}")
        r = run("recon_refresh.py", "prep", str(repo / "nie-ma"), cwd=d)
        check(r.returncode == 2, f"RF-11: a bad call → 2: {r.returncode}")

    # a git repository: the previous file version from the manifest commit (the hash matches the manifest)
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        rep = repo / DOCS
        write(repo, dict(CODE, **{"svc/billing/Rate.java": JAVA}))
        card = dict(BILLING, terms=[{"term": "pozycja", "code_name": "lines", "evidence": "svc/billing/invoice.py:3"}])
        write(rep, {"modules/billing.json": json.dumps(card, ensure_ascii=False),
                    "modules/customers.json": json.dumps(CUSTOMERS, ensure_ascii=False), "report.md": REPORT})
        git(repo, "init", "-q")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "base")
        run("recon_manifest.py", "write", str(repo), "--out", str(rep / "manifest.json"), "--budget-tokens", "12000")

        # a comment-only change (a new comment line in the middle of the file shifts the evidence) → no orders, finish right away
        write(repo, {"svc/billing/invoice.py": CODE["svc/billing/invoice.py"].replace(
                         "    if not lines:", "    # we check the items at the start\n    if not lines:"),
                     "svc/billing/Rate.java": JAVA.replace("// VAT", "// VAT w Polsce").replace("/* Stawki */", "/* Stawki podatku */")})
        r = run("recon_refresh.py", "prep", str(repo), cwd=d)
        out = r.stdout
        bj = (rep / "modules/billing.json").read_text(encoding="utf-8")
        rp = (rep / "report.md").read_text(encoding="utf-8")
        check(not (rep / "raw/refresh/billing.md").exists() and "only comments" in out.lower()
              and "svc/billing/Rate.java" in out, f"RF-14: a comment-only change without an order: {out[-700:]}")
        check('"svc/billing/invoice.py:5"' in bj and '"svc/billing/invoice.py:4"' in bj and "`svc/billing/invoice.py:5`" in rp
              and "`svc/billing/invoice.py:4`" not in rp, f"RF-15: line numbers recomputed in the cards and the report: {bj} {rp[-500:]}")
        check(r.returncode == 0 and "Final check: ✓" in out and "✓ manifest" in out,
              f"RF-16: with no orders prep runs finish: rc={r.returncode} {out[-700:]}")
        stamp = [ln for ln in rp.splitlines() if ln.startswith("Incremental refresh:")]
        check(len(stamp) == 1 and str(__import__("datetime").date.today()) in stamp[0],
              f"RF-17: the refresh date in the report: {rp[:400]}")
        r = run("recon_refresh.py", "prep", str(repo), cwd=d)
        check("Nothing to refresh" in r.stdout, f"RF-18: after the refresh nothing to do: {r.stdout[-300:]}")

        # a code change after the refresh commit: an order with the diff, the shift recomputed once, the date does not duplicate
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "refresh")
        write(repo, {"svc/billing/invoice.py": (repo / "svc/billing/invoice.py").read_text(encoding="utf-8").replace(
            "    if not lines:", "    if len(lines) < 2:\n        log('too few')")})
        rp = (rep / "report.md").read_text(encoding="utf-8")
        write(rep, {"report.md": rp.replace("## Domains\n", "## Domains\n- Sprawdzenie liczby pozycji — `svc/billing/invoice.py:4`\n")
})
        r = run("recon_refresh.py", "prep", str(repo), cwd=d)
        task = rep / "raw/refresh/billing.md"
        body = task.read_text(encoding="utf-8") if task.exists() else ""
        check("-    if not lines:" in body and "+    if len(lines) < 2:" in body and "Final check" not in r.stdout,
              f"RF-19: an order with the diff of the changed file: {body[-700:]} {r.stdout[-300:]}")
        run("recon_refresh.py", "prep", str(repo), cwd=d)
        bj = (rep / "modules/billing.json").read_text(encoding="utf-8")
        check('"svc/billing/invoice.py:6"' in bj and '"svc/billing/invoice.py:7"' not in bj,
              f"RF-20: the shift recomputed once despite two preps: {bj}")
        r = run("recon_refresh.py", "finish", str(repo), cwd=d)
        check(any("changed" in ln and "Sprawdzenie liczby pozycji" in ln for ln in r.stdout.splitlines()),
              f"RF-31: a description with evidence on a changed code line on the list to check: {r.stdout[-900:]}")
        rp = (rep / "report.md").read_text(encoding="utf-8")
        check(sum(ln.startswith("Incremental refresh:") for ln in rp.splitlines()) == 1,
              f"RF-21: one line with the refresh date after another finish: {rp[:500]}")

        # evidence with a quote that is no longer in the code: finish shows the line, apply fixes it and finishes right away
        bad = '- Pusta lista pozycji jest odrzucana — `svc/billing/invoice.py:4` "if not lines:"'
        write(rep, {"report.md": rp.replace("## Rules\n", "## Rules\n" + bad + "\n")})
        n = (rep / "report.md").read_text(encoding="utf-8").split("\n").index(bad) + 1
        r = run("recon_refresh.py", "finish", str(repo), cwd=d)
        check(r.returncode == 1 and f"report.md:{n}" in r.stdout and bad in r.stdout,
              f"RF-25: bad evidence with the document line content: {r.stdout[-700:]}")
        r = run("recon_refresh.py", "apply", str(repo), cwd=d,
                input="@@ modules/billing.md:3\n- cokolwiek\n")
        check(r.returncode == 2 and "modules/billing.json" in (r.stdout + r.stderr) and bad in (rep / "report.md").read_text(encoding="utf-8"),
              f"RF-26: apply does not change the .md assembled from cards, it points to the card: {r.stdout[-300:]} {r.stderr[-300:]}")
        fixed = '- Faktura z mniej niż dwiema pozycjami jest odrzucana — `svc/billing/invoice.py:4` "if len(lines) < 2:"'
        r = run("recon_refresh.py", "apply", str(repo), cwd=d, input=f"@@ report.md:{n}\n{fixed}\n")
        rp = (rep / "report.md").read_text(encoding="utf-8")
        check(r.returncode == 0 and fixed in rp and bad not in rp and "Final check: ✓" in r.stdout and "✓ manifest" in r.stdout,
              f"RF-27: apply fixes the line and runs finish: rc={r.returncode} {r.stdout[-600:]}")

        # fixes from the file raw/refresh/fixes.md (Write instead of a heredoc in Bash), after use the file is not left for reuse
        n2 = rp.split("\n").index(fixed) + 1
        again = fixed.replace("jest odrzucana", "jest odrzucana przez system")
        write(rep, {"raw/refresh/fixes.md": f"@@ {DOCS}/report.md:{n2}\n{again}\n"})
        r = run("recon_refresh.py", "apply", str(repo), cwd=d)
        rp = (rep / "report.md").read_text(encoding="utf-8")
        check(r.returncode == 0 and again in rp and not (rep / "raw/refresh/fixes.md").exists() and "Final check: ✓" in r.stdout,
              f"RF-32: apply reads raw/refresh/fixes.md (also with a path from the repo root): rc={r.returncode} {r.stdout[-500:]}")

        # the executor checks the card with one command: the shifted evidence fixed in the JSON, the missing quote with a code line
        cj = json.loads((rep / "modules/billing.json").read_text(encoding="utf-8"))
        cj["rules"][0]["evidence"] = "svc/billing/invoice.py:1"                    # cytat jest jednoznacznie w linii 6
        cj["rules"].append({"rule": "Brak pozycji to błąd.", "evidence": "svc/billing/invoice.py:4",
                            "quote": "if not lines:", "confidence": "kod"})        # no such code exists any more
        write(rep, {"modules/billing.json": json.dumps(cj, ensure_ascii=False)})
        r = run("recon_refresh.py", "card", str(repo), "billing", cwd=d)
        cj = json.loads((rep / "modules/billing.json").read_text(encoding="utf-8"))
        check(cj["rules"][0]["evidence"] == "svc/billing/invoice.py:6" and r.returncode == 1 and "if len(lines) < 2:" in r.stdout
              and "Brak pozycji to błąd." in r.stdout and len(r.stdout.splitlines()) <= 25,
              f"RF-28: card check: the shifted evidence fixed, the bad one with a code line: rc={r.returncode} {r.stdout[-700:]} {cj['rules']}")
        cj["rules"].pop()
        write(rep, {"modules/billing.json": json.dumps(cj, ensure_ascii=False)})
        r = run("recon_refresh.py", "card", str(repo), "billing", cwd=d)
        check(r.returncode == 0 and r.stdout.startswith("✓"), f"RF-29: a valid card → ✓: {r.stdout[-300:]}")
        check("Liczy faktury." in r.stdout and "module description" in r.stdout.lower(),
              f"RF-33: the card check reminds about the module description (purpose): {r.stdout[-400:]}")
        check("purpose" in body and "module description" in body.lower(), f"RF-34: the order tells to check the module description: {body[-900:]}")
        check("no longer" in body and "removed" in body, f"RF-35: the order: a removed rule → an entry about the current state: {body[-900:]}")

    # recognizing comment-only changes (conservatively: when in doubt, it is a code change)
    co = recon_refresh.comment_only
    check(co("int a = 1;\n", "// nowy\nint a = 1;\n", "A.java") and co("/* x */ int a = 1;\n", "/* y */ int a = 1;\n", "A.cs")
          and co("x = 1\n", "# opis\nx = 1\n\n", "a.py") and co("/**\n * stary\n */\nclass A {}\n", "/**\n * nowy\n */\nclass A {}\n", "A.java"),
          "RF-22: line comments, block comments and blank lines")
    check(not co("/* x */ int a = 1;\n", "/* x */ int a = 2;\n", "A.cs") and not co("#if DEBUG\nx();\n#endif\n", "#if RELEASE\nx();\n#endif\n", "A.cs")
          and not co('def f():\n    """stary"""\n', 'def f():\n    """nowy"""\n', "a.py") and not co("<p>a</p>\n", "<!-- k --><p>a</p>\n", "a.cshtml")
          and not co("int a;\n", "/* bez końca\nint a;\n", "A.java") and not co("a = 1;\n", "a = 1; // k\n", "a.ts"),
          "RF-23: code, directives, docstrings, unknown extensions, an unclosed block and a comment after code are a code change")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of recon_refresh")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
