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

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów recon_cards")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
