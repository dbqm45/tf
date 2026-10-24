#!/usr/bin/env python3
"""Testy eng-codebase-mapping/scripts/recon_cards.py: karta modułu (JSON) → modules/<karta>.md z dowodami plik:linia,
skrótem treści karty i propozycją sekcji „Moduły” raportu. python3 .claude/tests/test_recon_cards.py"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPTS = ROOT / ".claude" / "skills" / "eng-codebase-mapping" / "scripts"

CODE = {
    "services/billing/api.py": "from fastapi import APIRouter\nrouter = APIRouter()\n\n@router.post('/invoices')\ndef create():\n    pass\n",
    "services/billing/service.py": "from customers import find\n\ndef issue(lines):\n    if not lines:\n        raise EmptyInvoice()\n",
    "services/billing/model.py": "class CreditNote:\n    pass\n",
}

CARD = {
    "module": "billing",
    "batch": "services/billing",
    "purpose": "Wystawia i koryguje faktury dla klientów abonamentowych.",
    "entry_points": [{"what": "POST /invoices", "evidence": "services/billing/api.py:4"}],
    "depends_on": [{"module": "customers", "evidence": "services/billing/service.py:1"}],
    "data": [{"table": "invoice", "access": "write"}],
    "rules": [{"rule": "Faktura bez pozycji jest odrzucana.", "evidence": "services/billing/service.py:5",
               "quote": "raise EmptyInvoice", "confidence": "test"}],
    "terms": [{"term": "korekta", "code_name": "CreditNote", "evidence": "services/billing/model.py:1"}],
    "deviations": [],
    "unknowns": ["Kolejka 'invoices.created' — konsument poza repo"],
}


def write(root: Path, files: dict) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True, timeout=60,
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
        write(repo, CODE)
        mods = repo / "docs/project/00-reconstruction/modules"
        raw = json.dumps(CARD, ensure_ascii=False, indent=1)
        write(mods, {"billing.json": raw})
        r = run("recon_cards.py", str(mods), cwd=d)
        md_path = mods / "billing.md"
        md = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
        check(r.returncode == 0 and md.startswith(f"<!-- karta: modules/billing.json sha256:{h} -->"),
              f"C-1: modules/billing.md ze skrótem karty: rc={r.returncode} {md[:200]!r} {r.stderr[-300:]}")
        check("POST /invoices — `services/billing/api.py:4`" in md, f"C-2: wejście z dowodem: {md}")
        check('`services/billing/service.py:5` "raise EmptyInvoice" (pewność: test)' in md, f"C-3: reguła z cytatem: {md}")
        check("[niezweryfikowane] Kolejka 'invoices.created'" in md, f"C-4: niewiadoma oznaczona: {md}")
        check("invoice (write) [niezweryfikowane: brak dowodu w karcie]" in md, f"C-5: element bez dowodu oznaczony: {md}")

        # wygenerowany .md przechodzi kontrolę dowodów: dowody istnieją, cytaty się zgadzają, nic bez dowodu
        r = run("recon_check.py", str(md_path), "--repo", str(repo), "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("bad") == [] and out.get("unsupported") == [] and out.get("refs") == 4,
              f"C-6: .md z karty przechodzi recon_check: {r.stdout[-500:]}")

        # propozycja sekcji Moduły: cel, kluczowe elementy, odnośnik do .md, dowód
        r = run("recon_cards.py", str(mods), "--summary", cwd=d)
        line = next((ln for ln in r.stdout.splitlines() if ln.startswith("- billing:")), "")
        check("Wystawia i koryguje faktury" in line and "POST /invoices" in line and "CreditNote" in line
              and "(szczegóły: modules/billing.md)" in line and "`services/billing/api.py:4`" in line,
              f"C-7: wpis do sekcji Moduły: {r.stdout[-500:]}")

        # bez zmian w karcie drugi przebieg nie zmienia pliku; zła karta → kod 1, pozostałe karty i tak powstają
        before = md_path.read_text(encoding="utf-8") if md_path.exists() else None
        write(mods, {"broken.json": "{nie json", "vet.json": json.dumps({"module": "vet", "purpose": "Lista weterynarzy."})})
        r = run("recon_cards.py", str(mods), cwd=d)
        after = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
        check(before is not None and after == before, "C-8: przebieg bez zmian w karcie nie zmienia .md")
        check(r.returncode == 1 and "broken.json" in r.stdout and (mods / "vet.md").exists(),
              f"C-9: zła karta zgłoszona, reszta wygenerowana: rc={r.returncode} {r.stdout[-300:]}")
        vet = (mods / "vet.md").read_text(encoding="utf-8") if (mods / "vet.md").exists() else ""
        r = run("recon_cards.py", str(mods), "--summary", cwd=d)
        check("- vet: Lista weterynarzy. [niezweryfikowane: brak dowodu w karcie] (szczegóły: modules/vet.md)" in r.stdout
              and "# vet" in vet, f"C-10: karta bez dowodów: {r.stdout[-300:]} {vet[:200]!r}")

        # --repo: dowód ze ścieżką względną wobec partii → ścieżka od korzenia repo, gdy w partii jest jeden taki plik
        write(repo, {"services/billing/sub/util.py": "x = 1\n", "services/billing/a/dup.py": "y = 1\n",
                     "services/billing/b/dup.py": "y = 2\n"})
        write(mods, {"rel.json": json.dumps({"module": "rel", "batch": "services/billing", "entry_points": [
            {"what": "wprost", "evidence": "api.py:4"}, {"what": "głębiej", "evidence": "util.py:1"},
            {"what": "dwuznaczny", "evidence": "dup.py:1"}, {"what": "od korzenia", "evidence": "services/billing/model.py:1"}],
            "unknowns": ["Czy rejestracja w api.py:4 jest używana?"]})})
        (mods / "broken.json").unlink()
        r = run("recon_cards.py", str(mods), "--repo", str(repo), cwd=d)
        rel = (mods / "rel.md").read_text(encoding="utf-8") if (mods / "rel.md").exists() else ""
        check(r.returncode == 0 and "wprost — `services/billing/api.py:4`" in rel
              and "głębiej — `services/billing/sub/util.py:1`" in rel and "dwuznaczny — `dup.py:1`" in rel
              and "od korzenia — `services/billing/model.py:1`" in rel
              and "Czy rejestracja w services/billing/api.py:4 jest używana?" in rel, f"C-11: ścieżki z partii: {rel}")
        r = run("recon_cards.py", str(mods), cwd=d)
        rel = (mods / "rel.md").read_text(encoding="utf-8") if (mods / "rel.md").exists() else ""
        check("wprost — `api.py:4`" in rel, f"C-12: bez --repo dowody bez zmian: {rel}")

        # --rules: rules.md obok katalogu modules/ z reguł wszystkich kart, pogrupowanych po module, z dowodami
        r = run("recon_cards.py", str(mods), "--repo", str(repo), "--rules", cwd=d)
        rules_md = mods.parent / "rules.md"
        txt = rules_md.read_text(encoding="utf-8") if rules_md.exists() else ""
        check(r.returncode == 0 and "## billing" in txt
              and '- Faktura bez pozycji jest odrzucana. — `services/billing/service.py:5` "raise EmptyInvoice" (pewność: test)' in txt
              and "(szczegóły: modules/billing.md)" in txt, f"C-13: rules.md z kart: {txt[:600]}")
        r = run("recon_check.py", str(rules_md), "--repo", str(repo), "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("bad") == [] and out.get("unsupported") == [], f"C-14: rules.md przechodzi recon_check: {r.stdout[-400:]}")

        # --rules ponownie: sekcja „## Reguły przekrojowe” dopisana przez syntezę zostaje
        with open(rules_md, "a", encoding="utf-8") as fh:
            fh.write("\n## Reguły przekrojowe\n- [niezweryfikowane] Mapowanie błędów obejmuje cały system.\n")
        r = run("recon_cards.py", str(mods), "--repo", str(repo), "--rules", cwd=d)
        txt = rules_md.read_text(encoding="utf-8")
        check(txt.count("## Reguły przekrojowe") == 1 and "Mapowanie błędów obejmuje cały system." in txt and "## billing" in txt,
              f"C-17: --rules zachowuje reguły przekrojowe: {txt[-400:]}")

        # --into: sekcja „## Moduły” raportu podmieniona na wpisy z kart (reszta raportu bez zmian)
        rep = mods.parent / "report.md"
        rep.write_text("# R\n## Stack\nx\n## Moduły\n- stary wpis\n## Domeny\ny\n", encoding="utf-8")
        r = run("recon_cards.py", str(mods), "--repo", str(repo), "--into", str(rep), cwd=d)
        txt = rep.read_text(encoding="utf-8")
        mod_part = txt.split("## Moduły", 1)[-1].split("## Domeny")[0]
        check(r.returncode == 0 and "stary wpis" not in txt and "- billing: Wystawia" in mod_part and "- vet:" in mod_part
              and txt.startswith("# R\n## Stack\nx\n## Moduły\n") and txt.rstrip().endswith("## Domeny\ny"),
              f"C-15: sekcja Moduły z kart: {txt[:700]}")
        rep.write_text("# R\n## Stack\nx\n", encoding="utf-8")
        r = run("recon_cards.py", str(mods), "--into", str(rep), cwd=d)
        check(r.returncode == 1 and "brak sekcji" in r.stdout, f"C-16: raport bez sekcji Moduły: rc={r.returncode} {r.stdout[-200:]}")

    # --prev: stare karty kontra nowe → miejsca w dokumentacji, które mogą opisywać stan sprzed zmiany
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        rep = repo / "docs/project/00-reconstruction"
        prev, mods = rep / "raw/cards-prev", rep / "modules"
        old_owner = {"module": "owner", "rules": [
            {"rule": "Telefon właściciela musi mieć dokładnie 10 cyfr.", "quote": "@Pattern(regexp", "evidence": "Owner.java:64"},
            {"rule": "Nazwa zwierzaka jest wymagana.", "quote": "REQUIRED", "evidence": "PetValidator.java:44"}]}
        new_owner = {"module": "owner", "rules": [
            {"rule": "Telefon właściciela ma dokładnie 9 cyfr (zmiana: było 10).", "quote": '@Pattern(regexp = "\\d{9}")', "evidence": "Owner.java:64"},
            {"rule": "Nazwa zwierzaka musi być podana.", "quote": "REQUIRED", "evidence": "PetValidator.java:44"}],
            "unknowns": ["Brak testów dla formatu telefonu (10 cyfr)."]}
        old_api = {"module": "api", "rules": [
            {"rule": "Utworzenie pozycji o istniejącej nazwie kończy się DuplicateException i kodem 409.",
             "quote": "throw new DuplicateException", "evidence": "Create.cs:47"},
            {"rule": "Tworzenie pozycji wymaga roli administratora.", "quote": "Roles = Administrators", "evidence": "Create.cs:20"}]}
        new_api = {"module": "api", "rules": [   # mapowanie w middleware zostaje — znaczniki 409 nadal są w karcie
            {"rule": "Middleware mapuje DuplicateException na kod 409.", "quote": "HttpStatusCode.Conflict", "evidence": "Middleware.cs:37"},
            {"rule": "Tworzenie pozycji katalogu wymaga roli administratora.", "quote": "Roles = Administrators", "evidence": "Create.cs:20"}]}
        write(prev, {"owner.json": json.dumps(old_owner), "api.json": json.dumps(old_api)})
        write(mods, {"owner.json": json.dumps(new_owner), "api.json": json.dumps(new_api)})
        write(rep, {"requirements.md": "# Wymagania\n- Telefon: dokładnie 10 cyfr\n- Telefon: dokładnie 9 cyfr\n"
                                       "- Lista weterynarzy: 10 na stronie\n- Duplikat nazwy przy tworzeniu → 409\n"
                                       "- Brak uprawnień → 403\n- Ścieżka /owners/{ownerId}/pets/{petId} obsługuje formularz właściciela\n"
                                       "- Telefon właściciela jest wymagany — `src/Owner.java:104` \"@NotBlank\"\n",
                    "raw/notes.md": "- Telefon: 10 cyfr (surowe dane, pomijane)\n"})
        r = run("recon_cards.py", str(mods), "--prev", str(prev), cwd=d)
        out = r.stdout
        owner_md = "modules/owner.md:"
        check(r.returncode == 0 and "requirements.md:2" in out and "requirements.md:5" in out,
              f"CR-1: stary telefon i usunięta reguła duplikatu wskazane: {out[-800:]}")
        check(owner_md in out and "Brak testów dla formatu telefonu (10 cyfr)" in out,
              f"CR-2: stary opis przepisany do nowej karty wskazany: {out[-800:]}")
        check("requirements.md:3" not in out and "requirements.md:4" not in out and "requirements.md:6" not in out,
              f"CR-3: aktualny stan i inne tematy nie są wskazane: {out[-800:]}")
        check("raw/notes.md" not in out and "PetValidator" not in out.split("Do sprawdzenia")[-1].split("\n")[0],
              f"CR-4: raw/ pominięte, reguła bez zmiany znaczników nie daje miejsc: {out[-800:]}")
        check("Do sprawdzenia: 5 miejsc" in out and "modules/owner.md" in out and "modules/api.md" in out,
              f"CR-5: liczba miejsc (z wzmianką „było 10” i mapowaniem w karcie api): {out[-600:]}")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów recon_cards")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
