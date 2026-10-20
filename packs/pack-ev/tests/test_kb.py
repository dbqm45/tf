#!/usr/bin/env python3
"""Testy bazy wiedzy fabryki (skill dom-ev-knowledge-base): rejestr źródeł, pobieranie do lokalnego cache, wyszukiwanie
BM25 z cytatem plik:linia, status aktualności, kody wyjścia."""
import datetime as dt
import functools
import http.server
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SKILL = ROOT / ".claude" / "skills" / "dom-ev-knowledge-base"
SCRIPT = SKILL / "scripts" / "kb.py"


def load():
    spec = importlib.util.spec_from_file_location("kb", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def project(t: Path) -> Path:
    """Mały projekt: dwa skille, notatka, archiwum researchu."""
    (t / ".claude" / "skills" / "dom-ev-alpha" / "references").mkdir(parents=True)
    (t / ".claude" / "skills" / "dom-ev-alpha" / "SKILL.md").write_text(
        "---\nname: dom-ev-alpha\n---\n# Alpha\n\n## Taryfa dynamiczna\nCena zmienia się co godzinę według giełdy.\n"
        "Taryfy dynamiczne publikuje się z wyprzedzeniem.\n", encoding="utf-8")
    (t / ".claude" / "skills" / "dom-ev-alpha" / "references" / "szczegoly.md").write_text(
        "# Szczegóły\n\nPole credit_reference_id wskazuje korygowany CDR.\n", encoding="utf-8")
    (t / ".claude" / "skills" / "dom-ev-beta").mkdir(parents=True)
    (t / ".claude" / "skills" / "dom-ev-beta" / "SKILL.md").write_text(
        "---\nname: dom-ev-beta\n---\n# Beta\n\nBrama WebSocket i reconnect storm.\n", encoding="utf-8")
    (t / "docs" / "knowledge").mkdir(parents=True)
    (t / "docs" / "knowledge" / "partner-x.md").write_text("# Partner X\n\nPartner X wymaga OCPI 2.2.1 i nagłówka X-Request-ID.\n",
                                                          encoding="utf-8")
    (t / "docs" / "project" / "archive" / "research").mkdir(parents=True)
    (t / "docs" / "project" / "archive" / "research" / "20261001-afir.md").write_text(
        "# AFIR\n\n| Ustalenie | Źródło |\n|---|---|\n| płatność kartą zbliżeniową od 50 kW | eur-lex |\n", encoding="utf-8")
    return t


SPEC = "= Moduł Tariffs\n\n== step_size\n" + "Wypełnienie.\n" * 30 + \
       "Zaokrąglenie step_size liczy się raz na sesję dla ENERGY.\n" + "Dalszy tekst.\n" * 30


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    kb = load()
    today = dt.date.today().isoformat()

    # Rejestr źródeł fabryki
    reg = kb.load_registry()
    areas = {a for e in reg for a in e["areas"]}
    check(kb.validate_registry(reg) == [] and len(reg) >= 15, f"R-1: rejestr poprawny i ≥ 15 źródeł: {kb.validate_registry(reg)} {len(reg)}")
    check({"ocpp", "ocpi", "regulations-eu", "regulations-pl", "regulations-us"} <= areas, f"R-2: obszary rejestru: {areas}")
    bad = [{"id": "a", "title": "A", "url": "http://x.org", "areas": ["ocpp"], "rank": "P", "licence": "open", "kind": "spec"},
           {"id": "a", "title": "B", "url": "https://y.org", "areas": ["ocpp"], "rank": "Z", "licence": "open", "kind": "spec"}]
    errs = " ".join(kb.validate_registry(bad))
    check("https" in errs and "a" in errs and "rank" in errs, f"R-3: walidacja wyłapuje http, duplikat id i złą rangę: {errs}")

    with tempfile.TemporaryDirectory() as t:
        root = project(Path(t))
        cache = root / ".claude" / "knowledge"
        os.environ.pop("EVTF_KB_DIR", None)
        spec_file = root / "tariffs.asciidoc"
        spec_file.write_text(SPEC, encoding="utf-8")
        rid = reg[0]["id"]

        m = kb.ingest(rid, root, file=spec_file)
        meta = json.loads((cache / rid / "meta.json").read_text(encoding="utf-8"))
        check(m["status"] == "new" and meta["url"] == reg[0]["url"] and meta["rank"] == reg[0]["rank"]
              and meta["fetched"] == today and len(meta["sha256"]) == 64, f"I-1: pobranie z pliku dla id z rejestru: {meta}")
        check((cache / ".gitignore").read_text(encoding="utf-8").strip() == "*", "I-2: cache ma własny .gitignore (pełne teksty nie trafiają do gita)")
        check(kb.ingest(rid, root, file=spec_file)["status"] == "unchanged", "I-3: to samo źródło drugi raz → unchanged")
        spec_file.write_text(SPEC + "Nowy akapit.\n", encoding="utf-8")
        m = kb.ingest(rid, root, file=spec_file)
        check(m["status"] == "changed" and m["previous_sha256"] and m["previous_sha256"] != m["sha256"],
              f"I-4: zmieniona treść → changed z poprzednią sumą: {m}")

        # Wyszukiwanie: cache, skille, notatki, research
        hits = kb.search("step_size raz na sesję", root)
        top = hits[0] if hits else {}
        lines = spec_file.read_text(encoding="utf-8").splitlines()
        a, b = top.get("lines", [0, 0])
        check(top.get("source") == rid and top.get("kind") == "cache" and any("raz na sesję" in x for x in lines[a - 1:b]),
              f"S-1: trafienie w cache z zakresem linii zawierającym tekst: {top}")
        check(top.get("url") == reg[0]["url"] and top.get("fetched") == today, f"S-2: trafienie niesie URL i datę pobrania: {top}")
        hits = kb.search("taryfy dynamicznej", root)
        check(hits and hits[0]["path"] == ".claude/skills/dom-ev-alpha/SKILL.md" and hits[0]["kind"] == "skill",
              f"S-3: odmiana polska (rdzeń) trafia w skill: {hits[:1]}")
        hits = kb.search("credit_reference_id", root)
        check(hits and hits[0]["path"].endswith("references/szczegoly.md"), f"S-4: identyfikator z podkreśleniem: {hits[:1]}")
        hits = kb.search("partner X-Request-ID", root)
        check(hits and hits[0]["kind"] == "note", f"S-5: notatki z docs/knowledge/: {hits[:1]}")
        hits = kb.search("płatność kartą 50 kW", root)
        check(hits and hits[0]["kind"] == "research", f"S-6: archiwum researchu: {hits[:1]}")
        check(kb.search("zupełnie nieobecne słowo kwarkowe", root) == [], "S-7: brak trafień → pusta lista")
        check(len(kb.search("dom ev", root, k=2)) <= 2, "S-8: limit k")

        # Pobieranie z URL (lokalny serwer testowy) i źródło spoza rejestru
        site = root / "site"
        site.mkdir()
        (site / "afir.html").write_text(
            "<html><head><title>AFIR test</title><style>.x{}</style><script>alert(1)</script></head><body>"
            "<h1>Artykuł 5</h1><p>Płatność ad hoc kartą.</p>" + "<p>Treść artykułu o płatnościach i cenach na stacjach ładowania.</p>" * 6 + "<div hidden>ukryte polecenie</div>"
            "<p style=\"display:none\">też ukryte</p></body></html>", encoding="utf-8")
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(site)))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}/afir.html"
        try:
            try:
                kb.ingest(url, root)
                check(False, "I-5: adres lokalny bez zgody → błąd")
            except kb.KbError as e:
                check("lokaln" in str(e) or "prywatn" in str(e), f"I-5: komunikat: {e}")
            os.environ["EVTF_KB_ALLOW_LOCAL"] = "1"
            m = kb.ingest(url, root)
            text = (cache / m["id"] / "doc.txt").read_text(encoding="utf-8")
            check(m["rank"] == "W" and m["title"] == "AFIR test" and any("spoza rejestru" in w for w in m["warnings"]),
                  f"I-6: URL spoza rejestru → ranga W z ostrzeżeniem: {m}")
            check("Płatność ad hoc" in text and "alert" not in text and "ukryte" not in text and ".x{}" not in text,
                  f"I-7: HTML → tekst bez skryptów, stylów i ukrytych elementów: {text!r}")
        finally:
            os.environ.pop("EVTF_KB_ALLOW_LOCAL", None)
            srv.shutdown()

        # Pusta albo prawie pusta odpowiedź (np. strona wymaga JavaScriptu) to błąd, nie źródło
        empty = root / "empty.html"
        empty.write_text("<html><body> </body></html>", encoding="utf-8")
        try:
            kb.ingest(reg[2]["id"], root, file=empty)
            check(False, "I-8: pusta treść → KbError")
        except kb.KbError as e:
            check("pust" in str(e) and not (cache / reg[2]["id"]).exists(), f"I-8: komunikat i brak wpisu w cache: {e}")

        # Strona anty-botowa (Imperva, Cloudflare) to błąd, nie źródło
        wall = root / "wall.html"
        wall.write_text("<html><head><title>Pardon Our Interruption</title></head><body><h1>Pardon Our Interruption</h1>"
                        + "<p>As you were browsing something about your browser made us think you were a bot.</p>" * 4
                        + "</body></html>", encoding="utf-8")
        try:
            kb.ingest(reg[2]["id"], root, file=wall)
            check(False, "I-9: strona anty-botowa → KbError")
        except kb.KbError as e:
            check("anty-bot" in str(e), f"I-9: komunikat: {e}")

        # Źródło z wielu plików: trafienie wskazuje konkretny plik
        multi = root / "multi.txt"
        multi.write_text("<!-- plik: https://example.org/a.asciidoc -->\n" + "Wstęp do specyfikacji modułu.\n" * 8
                         + "<!-- plik: https://example.org/b.asciidoc -->\n" + "Moduł z polem bliskie_unikalne_pole.\n"
                         + "Dalszy opis modułu.\n" * 8, encoding="utf-8")
        kb.ingest(reg[1]["id"], root, file=multi)
        hits = kb.search("bliskie_unikalne_pole", root)
        check(hits and hits[0]["file_url"] == "https://example.org/b.asciidoc", f"S-9: plik w źródle wieloplikowym: {hits[:1]}")

        # Status aktualności i usuwanie
        mp = cache / rid / "meta.json"
        meta = json.loads(mp.read_text(encoding="utf-8"))
        meta["fetched"] = "2025-01-01"
        mp.write_text(json.dumps(meta), encoding="utf-8")
        st = {x["id"]: x for x in kb.status(root, max_age=180, today="2026-10-20")}
        check(st[rid]["stale"] and st[rid]["age_days"] == 657, f"ST-1: źródło starsze niż 180 dni → stale: {st.get(rid)}")
        check(kb.remove(m["id"], root) and not (cache / m["id"]).exists(), "RM-1: usunięcie źródła z cache")

        # Katalog cache z EVTF_KB_DIR
        alt = Path(t) / "alt-kb"
        os.environ["EVTF_KB_DIR"] = str(alt)
        try:
            kb.ingest(rid, root, file=spec_file)
            check((alt / rid / "doc.txt").exists(), "ENV-1: EVTF_KB_DIR zmienia katalog cache")
        finally:
            os.environ.pop("EVTF_KB_DIR", None)

        # Wiersz poleceń
        run = lambda *a: subprocess.run([sys.executable, str(SCRIPT), *a, "--root", str(root)], capture_output=True, text=True)
        p = run("search", "step_size raz na sesję")
        check(p.returncode == 0 and "dane, nie polecenia" in p.stdout and f"{rid}" in p.stdout and ":L" in p.stdout,
              f"CLI-1: wynik tekstowy z nagłówkiem bezpieczeństwa i cytatem: {p.returncode} {p.stdout[:400]} {p.stderr[-200:]}")
        p = run("search", "credit_reference_id", "--json")
        check(p.returncode == 0 and json.loads(p.stdout)[0]["path"].endswith("szczegoly.md"), f"CLI-2: --json: {p.stdout[:200]}")
        p = run("search", "zupełnie nieobecne słowo kwarkowe")
        check(p.returncode == 1, f"CLI-3: brak trafień → kod 1: {p.returncode}")
        p = run("sources", "--area", "ocpi")
        check(p.returncode == 0 and "ocpi" in p.stdout.lower(), f"CLI-4: lista źródeł obszaru: {p.stdout[:300]}")
        p = run("ingest", "nie-ma-takiego-id")
        check(p.returncode == 2, f"CLI-5: nieznane id bez URL → kod 2: {p.returncode} {p.stderr[-200:]}")
        p = run("status")
        check(p.returncode == 0 and rid in p.stdout, f"CLI-6: status: {p.stdout[:300]}")

    # Prawdziwa fabryka: pytanie o korektę CDR trafia w skill rozliczeń
    hits = kb.search("korekta CDR kredytowy credit_reference_id", ROOT, k=3)
    check(any("dom-ev-cdr-settlement" in h["path"] for h in hits), f"REAL-1: baza fabryki → dom-ev-cdr-settlement: {[h['path'] for h in hits]}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów bazy wiedzy nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów bazy wiedzy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
