#!/usr/bin/env python3
"""Testy generatora standardów z dokumentów firmy (`org/standards_from_docs.py`): podział dokumentów na sekcje
(Markdown, HTML, Word), kontrola przypisania bez modelu (cytaty, pokrycie sekcji, przykłady reguł, sprzeczności),
generowanie plików nakładki i odświeżanie po zmianie dokumentu. python3 tests/test_standards_from_docs.py"""
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
TOOL = ROOT / "org" / "standards_from_docs.py"
API_MD = """# Standard API

## Błędy
Każdy endpoint zwraca błędy w formacie application/problem+json zgodnie z RFC 9457.

## Wersje
Ścieżka każdego endpointu publicznego zaczyna się od /v1/ albo wyższej wersji.

## Ogólne
Kod powinien być czytelny i dobrze nazwany.
"""
UI_HTML = """<html><body><h1>Interfejs</h1><h2>Kolory</h2>
<p>Kolory bierzemy wyłącznie z tokenów biblioteki komponentów, nigdy wpisane na sztywno.</p></body></html>"""


def docx(path: Path, paragraphs: list[tuple[str | None, str]]) -> None:
    """Minimalny plik Word: akapity z opcjonalnym stylem nagłówka."""
    body = "".join(
        f'<w:p>{f"<w:pPr><w:pStyle w:val=\"{st}\"/></w:pPr>" if st else ""}<w:r><w:t>{tx}</w:t></w:r></w:p>'
        for st, tx in paragraphs)
    xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document '
           'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + body + "</w:body></w:document>")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", xml)


def tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, timeout=120)


def digest(d: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(p for p in d.rglob("*") if p.is_file() and "sources" not in p.parts):
        h.update(f.relative_to(d).as_posix().encode() + f.read_bytes())
    return h.hexdigest()


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    spec = importlib.util.spec_from_file_location("sd_rules_scan", ROOT / "core" / "factory" / "rules_scan.py")
    rs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rs)
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        pack = base / "acme-factory"
        r = subprocess.run([sys.executable, str(ROOT / "org" / "new_org_pack.py"), "acme", "--out", str(pack)],
                           capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, r.stdout + r.stderr
        src = pack / "sources"
        src.mkdir()
        (src / "api.md").write_text(API_MD, encoding="utf-8")
        (src / "kopia-api.md").write_text("# Kopia\n\n## Błędy\nKażdy endpoint zwraca błędy w formacie "
                                          "application/problem+json zgodnie z RFC 9457.\n", encoding="utf-8")
        (src / "ui.html").write_text(UI_HTML, encoding="utf-8")
        docx(src / "wydania.docx", [("Heading1", "Wydania"), ("Heading2", "Dni wdrożeń"),
                                    (None, "Wdrożenia na produkcję tylko od poniedziałku do czwartku."),
                                    ("Heading2", "Piątek"),
                                    (None, "Wdrożenie w piątek jest możliwe po zgodzie kierownika zespołu.")])

        # SD-1: podział na sekcje
        r = tool("split", str(pack))
        man = src / "sections.jsonl"
        secs = [json.loads(ln) for ln in man.read_text(encoding="utf-8").splitlines()] if man.is_file() else []
        by_head = {s["heading"]: s for s in secs}
        check(r.returncode == 0 and {"Standard API › Błędy", "Standard API › Wersje", "Interfejs › Kolory",
                                     "Wydania › Dni wdrożeń", "Wydania › Piątek"} <= set(by_head),
              f"SD-1: sekcje z Markdown, HTML i Word z ścieżką nagłówków: {sorted(by_head)} {r.stdout}{r.stderr}")
        dup = [s for s in secs if s["file"] == "kopia-api.md"]
        check(dup and dup[0].get("duplicate_of") == by_head.get("Standard API › Błędy", {}).get("id"),
              f"SD-2: powtórzona treść oznaczona jako duplikat pierwszej sekcji: {dup}")
        check((src / "TASK.md").is_file() and "assignment.json" in (src / "TASK.md").read_text(encoding="utf-8"),
              "SD-3: polecenie dla agenta (TASK.md) z formatem przypisania")
        if fails:
            for f in fails:
                print(f"✗ {f}")
            print(f"✗ {total - len(fails)}/{total} testów standardów z dokumentów")
            return 1

        sid = lambda h: by_head[h]["id"]
        good = {
            "findings": [
                {"id": "U1", "section": sid("Standard API › Błędy"), "area": "api", "kind": "judgement",
                 "quote": "błędy w formacie application/problem+json zgodnie z RFC 9457",
                 "statement": "Błędy API w formacie problem details (RFC 9457)."},
                {"id": "U2", "section": sid("Standard API › Wersje"), "area": "api", "kind": "pattern",
                 "quote": "zaczyna się od /v1/ albo wyższej wersji",
                 "statement": "Ścieżka endpointu publicznego z wersją /vN/.",
                 "rule": {"id": "api-sciezka-bez-wersji", "title": "endpoint bez wersji w ścieżce",
                            "files": ["src/api/**"], "forbid": "@(Get|Post|Put|Delete)\\(['\"]/(?!v\\d)",
                            "severity": "medium", "suggestion": "dodaj /v1/ na początku ścieżki",
                            "violation": {"file": "src/api/orders.ts", "content": "@Get('/orders')"},
                            "compliant": {"file": "src/api/orders.ts", "content": "@Get('/v1/orders')"}}},
                {"id": "U4", "section": sid("Interfejs › Kolory"), "area": "ui", "kind": "pattern",
                 "quote": "nigdy wpisane na sztywno", "statement": "Kolory tylko z tokenów.",
                 "rule": {"id": "ui-kolor-na-sztywno", "title": "kolor wpisany na sztywno",
                            "files": ["src/components/**"], "forbid": "#[0-9a-fA-F]{6}\\b", "severity": "low",
                            "violation": {"file": "src/components/Card.css", "content": "color: #1a2b3c;"},
                            "compliant": {"file": "src/components/Card.css", "content": "color: var(--ink);"}}},
                {"id": "U5", "section": sid("Wydania › Dni wdrożeń"), "area": "releases", "kind": "judgement",
                 "quote": "tylko od poniedziałku do czwartku", "statement": "Wdrożenia produkcyjne pon.–czw.",
                 "conflicts_with": ["U6"]},
                {"id": "U6", "section": sid("Wydania › Piątek"), "area": "releases", "kind": "judgement",
                 "quote": "możliwe po zgodzie kierownika zespołu", "statement": "Piątek po zgodzie kierownika.",
                 "conflicts_with": ["U5"]},
            ],
            "skipped": [{"section": sid("Standard API › Ogólne"), "reason": "ogólna praktyka, którą zna każdy model"}],
        }
        asg = src / "assignment.json"

        def run_check(data) -> subprocess.CompletedProcess:
            asg.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            return tool("check", str(pack))

        r = run_check(good)
        check(r.returncode == 0, f"SD-4: poprawne przypisanie przechodzi kontrolę: {r.stdout}{r.stderr}")
        for name, mutate, needle in [
            ("cytat spoza sekcji", lambda d: d["findings"][0].update(quote="błędy zawsze w formacie XML"), "quote"),
            ("sekcja bez ustalenia i bez powodu pominięcia", lambda d: d.update(skipped=[]), "Ogólne"),
            ("przykład zgodny łamie regułę", lambda d: d["findings"][1]["rule"]["compliant"].update(content="@Get('/x')"),
             "compliant"),
            ("przykład naruszenia nie łamie reguły",
             lambda d: d["findings"][2]["rule"]["violation"].update(content="color: var(--x);"), "violation"),
            ("nieznany obszar", lambda d: d["findings"][0].update(area="backend"), "area"),
            ("nieznana sekcja", lambda d: d["findings"][0].update(section="nie-ma"), "section"),
            ("sprzeczność bez pary", lambda d: d["findings"][3].update(conflicts_with=["U9"]), "U9"),
            ("zły wzorzec", lambda d: d["findings"][1]["rule"].update(forbid="(["), "regex"),
        ]:
            bad = copy.deepcopy(good)
            mutate(bad)
            r = run_check(bad)
            check(r.returncode == 1 and needle in r.stdout + r.stderr,
                  f"SD-5: kontrola odrzuca: {name} (oczekiwane „{needle}”): {r.returncode} {r.stdout}{r.stderr}")

        # SD-6: generowanie plików nakładki
        run_check(good)
        r = tool("apply", str(pack))
        check(r.returncode == 0, f"SD-6: apply po zaliczonej kontroli: {r.stdout}{r.stderr}")
        refs = pack / "skills" / "acme-standards" / "references"
        api = (refs / "api.md").read_text(encoding="utf-8")
        check("RFC 9457" in api and "api.md › Standard API › Błędy" in api and "kolor" not in api.lower()
              and "[U2]" not in api,
              f"SD-6: ustalenie z cytatem i źródłem w pliku swojego obszaru, wzorce tylko w rules.yaml: {api}")
        wyd = (refs / "releases.md").read_text(encoding="utf-8")
        check("U6" in wyd and "conflicts with" in wyd.lower(), f"SD-6: sprzeczność oznaczona przy ustaleniu: {wyd}")
        mod = pack / "analyzers" / "acme-standards"
        rules = rs.load_rules(mod / "rules.yaml")
        ids = {x["id"] for x in rules}
        check({"api-sciezka-bez-wersji", "ui-kolor-na-sztywno", "przyklad-print"} <= ids,
              f"SD-7: reguły z dokumentów dopisane do rules.yaml obok istniejących: {ids}")
        found = {(f["rule"], f["file"]) for f in rs.scan(rules, mod / "fixtures/violations/repo",
                                                          rs.repo_files(mod / "fixtures/violations/repo"))}
        expected = {(e["rule"], e["file"]) for e in json.loads((mod / "fixtures/violations/expected.json").read_text())}
        clean = rs.scan(rules, mod / "fixtures/clean/repo", rs.repo_files(mod / "fixtures/clean/repo"))
        check(found == expected and ("api-sciezka-bez-wersji", "src/api/orders.ts") in expected and not clean,
              f"SD-8: przykłady reguł w fixtures, bramka modułu spełniona: {found} vs {expected}; czyste: {clean}")
        rap = (src / "REPORT.md").read_text(encoding="utf-8") if (src / "REPORT.md").is_file() else ""
        check("U5" in rap and "U6" in rap and "ogólna praktyka" in rap and "kopia-api.md" in rap,
              f"SD-9: raport: sprzeczności, pominięte z powodem, duplikaty: {rap}")
        app = base / "app"
        app.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=app, check=True)
        r = subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "install.py"), str(app), "--yes",
                            "--packs", "pack-acme", "--pack-dir", str(pack)],
                           capture_output=True, text=True, timeout=300)
        g = subprocess.run([sys.executable, str(app / ".tf/factory/analyze.py"), "gate", "--module", "acme-standards"],
                           cwd=app, capture_output=True, text=True, timeout=120) if r.returncode == 0 else r
        leaked = [str(f) for f in app.rglob("*") if f.is_file() and ".git" not in f.parts
                  and "zgodnie z RFC 9457." in f.read_text(encoding="utf-8", errors="ignore")
                  and "references" not in f.parts]
        check(r.returncode == 0 and g.returncode == 0 and not leaked,
              f"SD-13: nakładka po apply instaluje się, bramka modułu w projekcie przechodzi, dokumenty nie trafiają "
              f"do projektu: {(g.stdout + g.stderr)[-600:]} {leaked}")
        before = digest(pack)
        r = tool("apply", str(pack))
        check(r.returncode == 0 and digest(pack) == before, "SD-10: ponowne apply niczego nie zmienia")

        # SD-11: odświeżanie po zmianie dokumentu
        (src / "api.md").write_text(API_MD.replace("zgodnie z RFC 9457", "zgodnie z RFC 7807"), encoding="utf-8")
        r = tool("split", str(pack))
        check(r.returncode == 0 and "changed: 1" in r.stdout, f"SD-11: split wskazuje zmienione sekcje: {r.stdout}")
        r = tool("check", str(pack))
        check(r.returncode == 1 and "U1" in r.stdout, f"SD-11: ustalenie ze zmienionej sekcji do przejrzenia: {r.stdout}")
        r = tool("apply", str(pack))
        check(r.returncode != 0 and digest(pack) == before, "SD-12: apply bez zaliczonej kontroli niczego nie zapisuje")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów standardów z dokumentów")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
