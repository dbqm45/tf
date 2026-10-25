#!/usr/bin/env python3
"""Testy eng-codebase-mapping/scripts/recon_refresh.py: odświeżanie rekonstrukcji w dwóch krokach bez modelu —
prep (diff manifestu, kopia kart, zlecenia dla wykonawców) i finish (karty → .md, rules.md, sekcja Moduły, lista
miejsc ze starym opisem, kontrola końcowa, manifest). python3 .claude/tests/test_recon_refresh.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPTS = ROOT / ".claude" / "skills" / "eng-codebase-mapping" / "scripts"
DOCS = "docs/project/00-reconstruction"

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
REPORT = """# Rekonstrukcja
## TL;DR
Fakturowanie (`svc/billing/invoice.py:1`).
## Stack
| Obszar | Ustalenie | Dowód |
|---|---|---|
| Język | Python 3 [założenie] | — |
| Framework | brak [założenie] | — |
| Dane | brak [niezweryfikowane] | — |
| Build | brak [założenie] | — |
| Testy | brak [niezweryfikowane] | — |
| CI | brak [niezweryfikowane] | — |
| Konfiguracja | stała w kodzie | `svc/billing/tax.py:1` |
## Moduły
- (wstawia recon_cards)
## Domeny
- Fakturowanie — `svc/billing/invoice.py:1`
## Wymagania
- Pusta faktura jest odrzucana kodem 422 — `svc/billing/invoice.py:4`
## Reguły
- VAT 23% — `svc/billing/tax.py:1`
## Standardy
- [niezweryfikowane] snake_case
## Ryzyka
- Brak testów — `svc/billing/invoice.py:1`
## Pytania
- [pytanie] Czy VAT zależy od kraju?
## Czego nie sprawdzono
- Wdrożenie.
"""


def write(root: Path, files: dict) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True, timeout=120,
                          stdin=subprocess.DEVNULL, cwd=cwd)


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
        check(r.returncode == 0, f"RF-0: manifest bazowy: {r.stderr[-300:]}")

        # bez zmian w kodzie: nic do zrobienia
        r = run("recon_refresh.py", "prep", str(repo), cwd=d)
        check(r.returncode == 0 and "Nic do odświeżenia" in r.stdout and not (rep / "raw/refresh").exists(),
              f"RF-1: brak zmian: rc={r.returncode} {r.stdout[-400:]} {r.stderr[-300:]}")

        # zmiana w pliku cytowanym przez kartę billing + nowy plik bez karty
        write(repo, {"svc/billing/invoice.py": CODE["svc/billing/invoice.py"].replace("if not lines:", "if len(lines) < 2:"),
                     "svc/shipping/ship.py": "def ship():\n    pass\n"})
        r = run("recon_refresh.py", "prep", str(repo), cwd=d)
        out = r.stdout
        task = rep / "raw/refresh/billing.md"
        body = task.read_text(encoding="utf-8") if task.exists() else ""
        check(r.returncode == 0 and (rep / "raw/cards-prev/billing.json").exists() and (rep / "raw/cards-prev/customers.json").exists(),
              f"RF-2: kopia wszystkich kart w raw/cards-prev: {out[-400:]} {r.stderr[-300:]}")
        check("svc/billing/invoice.py" in body and "modules/billing.json" in body and "svc/billing/tax.py" not in body.split("Zmienione pliki")[-1],
              f"RF-3: zlecenie dla karty billing ze zmienionym plikiem: {body[-600:]}")
        check(not (rep / "raw/refresh/customers.md").exists(), "RF-4: karta bez zmienionych plików nie dostaje zlecenia")
        check("billing" in out and "svc/shipping/ship.py" in out and "bez karty" in out and len(out.splitlines()) <= 40,
              f"RF-5: plan z kartą, plikiem bez karty i ≤ 40 linii: {out}")

        # wykonawca zaktualizował kartę: reguła „422” zmieniona na „co najmniej dwie pozycje”
        new = dict(BILLING, rules=[{"rule": "Faktura musi mieć co najmniej dwie pozycje.", "evidence": "svc/billing/invoice.py:3",
                                    "quote": "if len(lines) < 2:", "confidence": "kod"}, BILLING["rules"][1]])
        write(rep, {"modules/billing.json": json.dumps(new, ensure_ascii=False)})
        before = json.loads((rep / "manifest.json").read_text(encoding="utf-8"))
        r = run("recon_refresh.py", "finish", str(repo), cwd=d)
        out = r.stdout
        stale = rep / "raw/refresh/STALE.md"
        check("Do sprawdzenia:" in out and "report.md:" in out and stale.exists() and "422" in stale.read_text(encoding="utf-8"),
              f"RF-6: lista miejsc ze starym opisem na ekranie i w STALE.md: {out[-800:]}")
        check("- billing:" in (rep / "report.md").read_text(encoding="utf-8") and (rep / "modules/billing.md").exists()
              and (rep / "rules.md").exists(), "RF-7: sekcja Moduły, .md kart i rules.md złożone")
        check("Kontrola końcowa:" in out and len(out.splitlines()) <= 60, f"RF-8: zwięzłe podsumowanie kontroli: {out[-600:]}")

        # po poprawce opisu kontrola przechodzi i manifest dostaje nowy stan
        rp = (rep / "report.md").read_text(encoding="utf-8").replace("odrzucana kodem 422", "odrzucana, gdy ma mniej niż dwie pozycje")
        write(rep, {"report.md": rp})
        r = run("recon_refresh.py", "finish", str(repo), cwd=d)
        after = json.loads((rep / "manifest.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and "✓ manifest" in r.stdout and after["files"] != before["files"]
              and "svc/shipping/ship.py" in after["files"], f"RF-9: manifest zapisany po przejściu kontroli: {r.stdout[-600:]}")
        r = run("recon_refresh.py", "prep", str(repo), cwd=d)
        check("Nic do odświeżenia" in r.stdout, f"RF-10: po odświeżeniu manifest zgodny z kodem: {r.stdout[-300:]}")
        # dowód przesunięty przez zmianę kodu (cytat jednoznacznie w innej linii) → finish poprawia numer linii
        write(repo, {"svc/billing/tax.py": "# stawki\n# VAT\n# PL\n# 2026\nRATE = 0.23\n"})
        rp = (rep / "report.md").read_text(encoding="utf-8")
        write(rep, {"report.md": rp.replace("- VAT 23% — `svc/billing/tax.py:1`", '- VAT 23% — `svc/billing/tax.py:1` "RATE = 0.23"')
                    .replace("| Konfiguracja | stała w kodzie | `svc/billing/tax.py:1` |", "| Konfiguracja | stała w kodzie | `svc/billing/tax.py:5` |")})
        moved = dict(new, rules=[new["rules"][0], dict(BILLING["rules"][1], evidence="svc/billing/tax.py:5")])
        write(rep, {"modules/billing.json": json.dumps(moved, ensure_ascii=False)})
        r = run("recon_refresh.py", "finish", str(repo), cwd=d)
        rp = (rep / "report.md").read_text(encoding="utf-8")
        check('`svc/billing/tax.py:5` "RATE = 0.23"' in rp and "przesunięte dowody: 1" in r.stdout and r.returncode == 0,
              f"RF-12: przesunięty dowód poprawiony automatycznie: rc={r.returncode} {r.stdout[-700:]}")
        # zmienione reguły kart na ekranie: stara → nowa
        write(rep, {"raw/cards-prev/billing.json": json.dumps(BILLING, ensure_ascii=False)})
        r = run("recon_refresh.py", "finish", str(repo), cwd=d)
        check("Zmienione reguły kart" in r.stdout and "kod 422" in r.stdout and "co najmniej dwie pozycje" in r.stdout,
              f"RF-13: zmiany reguł stara → nowa: {r.stdout[-700:]}")
        r = run("recon_refresh.py", "prep", str(repo / "nie-ma"), cwd=d)
        check(r.returncode == 2, f"RF-11: złe wywołanie → 2: {r.returncode}")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów recon_refresh")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
