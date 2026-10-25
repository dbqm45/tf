#!/usr/bin/env python3
"""Testy eng-codebase-mapping/scripts/recon_refresh.py: odświeżanie rekonstrukcji w dwóch krokach bez modelu —
prep (diff manifestu, kopia kart, zlecenia dla wykonawców z diffem, zmiany tylko w komentarzach bez zleceń,
przeliczenie przesuniętych linii) i finish (karty → .md, rules.md, sekcja Moduły, lista
miejsc ze starym opisem, kontrola końcowa, manifest). python3 .claude/tests/test_recon_refresh.py"""
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
- Faktura bez pozycji jest odrzucana przez system — `svc/billing/tax.py:1`
## Wymagania
- Pusta faktura jest odrzucana kodem 422; dotyczy faktur sprzedaży i korekt, wystawianych ręcznie w panelu oraz automatycznie z zamówień sklepu, także po imporcie z systemu księgowego — `svc/billing/invoice.py:4`
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
        check("z systemu księgowego — `svc/billing/invoice.py:4`" in out,
              f"RF-24: miejsce do poprawy z pełnym tekstem linii: {out[-900:]}")
        check(any("podobn" in ln and "Faktura bez pozycji jest odrzucana przez system" in ln and "co najmniej dwie pozycje" in ln
                  for ln in out.splitlines()),
              f"RF-30: opis podobny do zmienionej reguły karty na liście, z nową treścią reguły: {out[-900:]}")
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

    # repozytorium git: poprzednia wersja pliku z commitu manifestu (hash zgodny z manifestem)
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

        # zmiana tylko w komentarzach (nowa linia komentarza w środku pliku przesuwa dowody) → bez zleceń, finish od razu
        write(repo, {"svc/billing/invoice.py": CODE["svc/billing/invoice.py"].replace(
                         "    if not lines:", "    # pozycje sprawdzamy na początku\n    if not lines:"),
                     "svc/billing/Rate.java": JAVA.replace("// VAT", "// VAT w Polsce").replace("/* Stawki */", "/* Stawki podatku */")})
        r = run("recon_refresh.py", "prep", str(repo), cwd=d)
        out = r.stdout
        bj = (rep / "modules/billing.json").read_text(encoding="utf-8")
        rp = (rep / "report.md").read_text(encoding="utf-8")
        check(not (rep / "raw/refresh/billing.md").exists() and "tylko komentarze" in out.lower()
              and "svc/billing/Rate.java" in out, f"RF-14: zmiana tylko w komentarzach bez zlecenia: {out[-700:]}")
        check('"svc/billing/invoice.py:5"' in bj and '"svc/billing/invoice.py:4"' in bj and "`svc/billing/invoice.py:5`" in rp
              and "`svc/billing/invoice.py:4`" not in rp, f"RF-15: numery linii przeliczone w kartach i raporcie: {bj} {rp[-500:]}")
        check(r.returncode == 0 and "Kontrola końcowa: ✓" in out and "✓ manifest" in out,
              f"RF-16: bez zleceń prep uruchamia finish: rc={r.returncode} {out[-700:]}")
        stamp = [ln for ln in rp.splitlines() if ln.startswith("Odświeżenie przyrostowe:")]
        check(len(stamp) == 1 and str(__import__("datetime").date.today()) in stamp[0],
              f"RF-17: data odświeżenia w raporcie: {rp[:400]}")
        r = run("recon_refresh.py", "prep", str(repo), cwd=d)
        check("Nic do odświeżenia" in r.stdout, f"RF-18: po odświeżeniu nic do zrobienia: {r.stdout[-300:]}")

        # zmiana w kodzie po commicie odświeżenia: zlecenie z diffem, przesunięcie przeliczone raz, data nie dubluje się
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "refresh")
        write(repo, {"svc/billing/invoice.py": (repo / "svc/billing/invoice.py").read_text(encoding="utf-8").replace(
            "    if not lines:", "    if len(lines) < 2:\n        log('za mało')")})
        rp = (rep / "report.md").read_text(encoding="utf-8")
        write(rep, {"report.md": rp.replace("## Domeny\n", "## Domeny\n- Sprawdzenie liczby pozycji — `svc/billing/invoice.py:4`\n")})
        r = run("recon_refresh.py", "prep", str(repo), cwd=d)
        task = rep / "raw/refresh/billing.md"
        body = task.read_text(encoding="utf-8") if task.exists() else ""
        check("-    if not lines:" in body and "+    if len(lines) < 2:" in body and "Kontrola końcowa" not in r.stdout,
              f"RF-19: zlecenie z diffem zmienionego pliku: {body[-700:]} {r.stdout[-300:]}")
        run("recon_refresh.py", "prep", str(repo), cwd=d)
        bj = (rep / "modules/billing.json").read_text(encoding="utf-8")
        check('"svc/billing/invoice.py:6"' in bj and '"svc/billing/invoice.py:7"' not in bj,
              f"RF-20: przesunięcie przeliczone raz mimo dwóch prep: {bj}")
        r = run("recon_refresh.py", "finish", str(repo), cwd=d)
        check(any("zmienion" in ln and "Sprawdzenie liczby pozycji" in ln for ln in r.stdout.splitlines()),
              f"RF-31: opis z dowodem w zmienionej linii kodu na liście do sprawdzenia: {r.stdout[-900:]}")
        rp = (rep / "report.md").read_text(encoding="utf-8")
        check(sum(ln.startswith("Odświeżenie przyrostowe:") for ln in rp.splitlines()) == 1,
              f"RF-21: jedna linia z datą odświeżenia po kolejnym finish: {rp[:500]}")

        # dowód z cytatem, którego w kodzie już nie ma: finish pokazuje linię, apply ją poprawia i od razu kończy
        bad = '- Pusta lista pozycji jest odrzucana — `svc/billing/invoice.py:4` "if not lines:"'
        write(rep, {"report.md": rp.replace("## Reguły\n", "## Reguły\n" + bad + "\n")})
        n = (rep / "report.md").read_text(encoding="utf-8").split("\n").index(bad) + 1
        r = run("recon_refresh.py", "finish", str(repo), cwd=d)
        check(r.returncode == 1 and f"report.md:{n}" in r.stdout and bad in r.stdout,
              f"RF-25: zły dowód z treścią linii dokumentu: {r.stdout[-700:]}")
        r = run("recon_refresh.py", "apply", str(repo), cwd=d,
                input="@@ modules/billing.md:3\n- cokolwiek\n")
        check(r.returncode == 2 and "modules/billing.json" in (r.stdout + r.stderr) and bad in (rep / "report.md").read_text(encoding="utf-8"),
              f"RF-26: apply nie zmienia .md składanych z kart, wskazuje kartę: {r.stdout[-300:]} {r.stderr[-300:]}")
        fixed = '- Faktura z mniej niż dwiema pozycjami jest odrzucana — `svc/billing/invoice.py:4` "if len(lines) < 2:"'
        r = run("recon_refresh.py", "apply", str(repo), cwd=d, input=f"@@ report.md:{n}\n{fixed}\n")
        rp = (rep / "report.md").read_text(encoding="utf-8")
        check(r.returncode == 0 and fixed in rp and bad not in rp and "Kontrola końcowa: ✓" in r.stdout and "✓ manifest" in r.stdout,
              f"RF-27: apply poprawia linię i uruchamia finish: rc={r.returncode} {r.stdout[-600:]}")

        # poprawki z pliku raw/refresh/fixes.md (Write zamiast heredoc w Bash), po użyciu plik nie zostaje do ponownego użycia
        n2 = rp.split("\n").index(fixed) + 1
        again = fixed.replace("jest odrzucana", "jest odrzucana przez system")
        write(rep, {"raw/refresh/fixes.md": f"@@ {DOCS}/report.md:{n2}\n{again}\n"})
        r = run("recon_refresh.py", "apply", str(repo), cwd=d)
        rp = (rep / "report.md").read_text(encoding="utf-8")
        check(r.returncode == 0 and again in rp and not (rep / "raw/refresh/fixes.md").exists() and "Kontrola końcowa: ✓" in r.stdout,
              f"RF-32: apply czyta raw/refresh/fixes.md (też ze ścieżką od korzenia repo): rc={r.returncode} {r.stdout[-500:]}")

        # wykonawca sprawdza kartę jednym poleceniem: przesunięty dowód poprawiony w JSON, brakujący cytat z linią kodu
        cj = json.loads((rep / "modules/billing.json").read_text(encoding="utf-8"))
        cj["rules"][0]["evidence"] = "svc/billing/invoice.py:1"                    # cytat jest jednoznacznie w linii 6
        cj["rules"].append({"rule": "Brak pozycji to błąd.", "evidence": "svc/billing/invoice.py:4",
                            "quote": "if not lines:", "confidence": "kod"})        # takiego kodu już nie ma
        write(rep, {"modules/billing.json": json.dumps(cj, ensure_ascii=False)})
        r = run("recon_refresh.py", "card", str(repo), "billing", cwd=d)
        cj = json.loads((rep / "modules/billing.json").read_text(encoding="utf-8"))
        check(cj["rules"][0]["evidence"] == "svc/billing/invoice.py:6" and r.returncode == 1 and "if len(lines) < 2:" in r.stdout
              and "Brak pozycji to błąd." in r.stdout and len(r.stdout.splitlines()) <= 25,
              f"RF-28: kontrola karty: przesunięty dowód poprawiony, zły z linią kodu: rc={r.returncode} {r.stdout[-700:]} {cj['rules']}")
        cj["rules"].pop()
        write(rep, {"modules/billing.json": json.dumps(cj, ensure_ascii=False)})
        r = run("recon_refresh.py", "card", str(repo), "billing", cwd=d)
        check(r.returncode == 0 and r.stdout.startswith("✓"), f"RF-29: poprawna karta → ✓: {r.stdout[-300:]}")
        check("Liczy faktury." in r.stdout and "opis modułu" in r.stdout.lower(),
              f"RF-33: kontrola karty przypomina o opisie modułu (purpose): {r.stdout[-400:]}")
        check("purpose" in body and "opis modułu" in body.lower(), f"RF-34: zlecenie każe sprawdzić opis modułu: {body[-900:]}")
        check("nie jest już" in body and "usunięt" in body, f"RF-35: zlecenie: usunięta reguła → wpis o stanie obecnym: {body[-900:]}")

    # rozpoznawanie zmian tylko w komentarzach (zachowawczo: w razie wątpliwości to zmiana kodu)
    co = recon_refresh.comment_only
    check(co("int a = 1;\n", "// nowy\nint a = 1;\n", "A.java") and co("/* x */ int a = 1;\n", "/* y */ int a = 1;\n", "A.cs")
          and co("x = 1\n", "# opis\nx = 1\n\n", "a.py") and co("/**\n * stary\n */\nclass A {}\n", "/**\n * nowy\n */\nclass A {}\n", "A.java"),
          "RF-22: komentarze liniowe, blokowe i puste linie")
    check(not co("/* x */ int a = 1;\n", "/* x */ int a = 2;\n", "A.cs") and not co("#if DEBUG\nx();\n#endif\n", "#if RELEASE\nx();\n#endif\n", "A.cs")
          and not co('def f():\n    """stary"""\n', 'def f():\n    """nowy"""\n', "a.py") and not co("<p>a</p>\n", "<!-- k --><p>a</p>\n", "a.cshtml")
          and not co("int a;\n", "/* bez końca\nint a;\n", "A.java") and not co("a = 1;\n", "a = 1; // k\n", "a.ts"),
          "RF-23: kod, dyrektywy, docstringi, nieznane rozszerzenia, niedomknięty blok i komentarz za kodem to zmiana kodu")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów recon_refresh")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
