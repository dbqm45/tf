#!/usr/bin/env python3
"""Factory knowledge base tests (skill core-knowledge): pack source registries, fetching into a local cache,
BM25 search with a file:line citation, freshness status, exit codes."""
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
SKILL = ROOT / ".claude" / "skills" / "core-knowledge"
SCRIPT = SKILL / "scripts" / "kb.py"


def load():
    spec = importlib.util.spec_from_file_location("kb", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def project(t: Path) -> Path:
    """A small project: two skills, a note, a research archive."""
    (t / ".claude" / "skills" / "dom-alpha" / "references").mkdir(parents=True)
    (t / ".claude" / "skills" / "dom-alpha" / "SKILL.md").write_text(
        "---\nname: dom-alpha\n---\n# Alpha\n\n## Taryfa dynamiczna\nCena zmienia się co godzinę według giełdy.\n"
        "Taryfy dynamiczne publikuje się z wyprzedzeniem.\n", encoding="utf-8")
    (t / ".claude" / "skills" / "dom-alpha" / "references" / "szczegoly.md").write_text(
        "# Szczegóły\n\nPole credit_reference_id wskazuje korygowaną fakturę.\n", encoding="utf-8")
    (t / ".claude" / "skills" / "dom-beta").mkdir(parents=True)
    (t / ".claude" / "skills" / "dom-beta" / "SKILL.md").write_text(
        "---\nname: dom-beta\n---\n# Beta\n\nBrama WebSocket i reconnect storm.\n", encoding="utf-8")
    (t / ".claude" / "skills" / "dom-alpha" / "references" / "zrodla.json").write_text(json.dumps(REG_A), encoding="utf-8")
    (t / ".claude" / "skills" / "dom-beta" / "references").mkdir(parents=True)
    (t / ".claude" / "skills" / "dom-beta" / "references" / "zrodla.json").write_text(json.dumps(REG_B), encoding="utf-8")
    (t / "docs" / "knowledge").mkdir(parents=True)
    (t / "docs" / "knowledge" / "partner-x.md").write_text("# Partner X\n\nPartner X wymaga OCPI 2.2.1 i nagłówka X-Request-ID.\n",
                                                          encoding="utf-8")
    (t / "docs" / "project" / "archive" / "research").mkdir(parents=True)
    (t / "docs" / "project" / "archive" / "research" / "20261001-regulamin.md").write_text(
        "# Regulamin\n\n| Ustalenie | Źródło |\n|---|---|\n| płatność kartą zbliżeniową od 50 zł | eur-lex |\n", encoding="utf-8")
    return t


def src(sid, areas, rank="P", licence="open"):
    return {"id": sid, "title": sid.upper(), "url": f"https://example.org/{sid}", "areas": areas, "rank": rank,
            "licence": licence, "kind": "spec", "checked": None, "note": ""}


REG_A = {"version": 1, "areas": ["tariffs", "roaming"],
         "sources": [src("spec-tariffs", ["tariffs"]), src("spec-roaming", ["roaming"]), src("spec-paid", ["tariffs"], licence="paid")]}
REG_B = {"version": 1, "areas": ["gateway"], "sources": [src("spec-gateway", ["gateway"], rank="W")]}

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

    # Validation of a single registry
    bad = [{"id": "a", "title": "A", "url": "http://x.org", "areas": ["ocpp"], "rank": "P", "licence": "open", "kind": "spec"},
           {"id": "a", "title": "B", "url": "https://y.org", "areas": ["ocpp"], "rank": "Z", "licence": "open", "kind": "spec"}]
    errs = " ".join(kb.validate_registry(bad))
    check("https" in errs and "a" in errs and "rank" in errs, f"R-3: validation catches http, a duplicate id and a bad rank: {errs}")
    errs = " ".join(kb.validate_registry([src("x", ["inny"])], areas={"tariffs"}))
    check("inny" in errs, f"R-4: an area outside those declared in the registry: {errs}")

    with tempfile.TemporaryDirectory() as t:
        root = project(Path(t))
        cache = root / ".claude" / "knowledge"
        for v in ("TF_KB_DIR", "EVTF_KB_DIR"):
            os.environ.pop(v, None)

        # Pack registries: each skill may have references/zrodla.json with a declaration of areas
        reg = kb.load_registry(root=root)
        check([e["id"] for e in reg] == ["spec-tariffs", "spec-roaming", "spec-paid", "spec-gateway"]
              and reg[0]["registry"] == "dom-alpha" and reg[3]["registry"] == "dom-beta",
              f"R-1: the registries of all skills together, with the skill name: {[(e['id'], e.get('registry')) for e in reg]}")
        check(kb.validate_registries(root) == [], f"R-2: valid registries -> no errors: {kb.validate_registries(root)}")
        dup = root / ".claude" / "skills" / "dom-gamma" / "references"
        dup.mkdir(parents=True)
        (dup / "zrodla.json").write_text(json.dumps({"version": 1, "sources": [src("spec-gateway", ["gateway"])]}),
                                         encoding="utf-8")
        errs = " ".join(kb.validate_registries(root))
        check("spec-gateway" in errs and "dom-gamma" in errs and "areas" in errs,
              f"R-5: ids duplicated across registries and no declaration of areas -> errors: {errs}")
        (dup / "zrodla.json").unlink()
        spec_file = root / "tariffs.asciidoc"
        spec_file.write_text(SPEC, encoding="utf-8")
        rid = reg[0]["id"]

        m = kb.ingest(rid, root, file=spec_file)
        meta = json.loads((cache / rid / "meta.json").read_text(encoding="utf-8"))
        check(m["status"] == "new" and meta["url"] == reg[0]["url"] and meta["rank"] == reg[0]["rank"]
              and meta["fetched"] == today and len(meta["sha256"]) == 64, f"I-1: fetching from a file for an id from the registry: {meta}")
        check((cache / ".gitignore").read_text(encoding="utf-8").strip() == "*", "I-2: the cache has its own .gitignore (full texts do not reach git)")
        check(kb.ingest(rid, root, file=spec_file)["status"] == "unchanged", "I-3: the same source a second time -> unchanged")
        spec_file.write_text(SPEC + "Nowy akapit.\n", encoding="utf-8")
        m = kb.ingest(rid, root, file=spec_file)
        check(m["status"] == "changed" and m["previous_sha256"] and m["previous_sha256"] != m["sha256"],
              f"I-4: changed content -> changed with the previous checksum: {m}")

        # Search: cache, skills, notes, research
        hits = kb.search("step_size raz na sesję", root)
        top = hits[0] if hits else {}
        lines = spec_file.read_text(encoding="utf-8").splitlines()
        a, b = top.get("lines", [0, 0])
        check(top.get("source") == rid and top.get("kind") == "cache" and any("raz na sesję" in x for x in lines[a - 1:b]),
              f"S-1: a cache hit with a line range containing the text: {top}")
        check(top.get("url") == reg[0]["url"] and top.get("fetched") == today, f"S-2: the hit carries the URL and the fetch date: {top}")
        hits = kb.search("taryfy dynamicznej", root)
        check(hits and hits[0]["path"] == ".claude/skills/dom-alpha/SKILL.md" and hits[0]["kind"] == "skill",
              f"S-3: a Polish inflected form (stem) hits the skill: {hits[:1]}")
        hits = kb.search("credit_reference_id", root)
        check(hits and hits[0]["path"].endswith("references/szczegoly.md"), f"S-4: an identifier with an underscore: {hits[:1]}")
        hits = kb.search("partner X-Request-ID", root)
        check(hits and hits[0]["kind"] == "note", f"S-5: notes from docs/knowledge/: {hits[:1]}")
        hits = kb.search("płatność kartą 50 zł", root)
        check(hits and hits[0]["kind"] == "research", f"S-6: the research archive: {hits[:1]}")
        check(kb.search("zupełnie nieobecne słowo kwarkowe", root) == [], "S-7: no hits -> empty list")
        check(len(kb.search("dom alpha", root, k=2)) <= 2, "S-8: limit k")

        # Fetching from a URL (a local test server) and a source outside the registry
        site = root / "site"
        site.mkdir()
        (site / "regulamin.html").write_text(
            "<html><head><title>Regulamin test</title><style>.x{}</style><script>alert(1)</script></head><body>"
            "<h1>Artykuł 5</h1><p>Płatność ad hoc kartą.</p>" + "<p>Treść artykułu o płatnościach i cenach w sklepach internetowych.</p>" * 6 + "<div hidden>ukryte polecenie</div>"
            "<p style=\"display:none\">też ukryte</p></body></html>", encoding="utf-8")
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(site)))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}/regulamin.html"
        try:
            try:
                kb.ingest(url, root)
                check(False, "I-5: a local address without consent -> error")
            except kb.KbError as e:
                check("local" in str(e) or "private" in str(e), f"I-5: message: {e}")
            os.environ["TF_KB_ALLOW_LOCAL"] = "1"
            m = kb.ingest(url, root)
            text = (cache / m["id"] / "doc.txt").read_text(encoding="utf-8")
            check(m["rank"] == "W" and m["title"] == "Regulamin test" and any("not in the registry" in w for w in m["warnings"]),
                  f"I-6: a URL outside the registry -> rank W with a warning: {m}")
            check("Płatność ad hoc" in text and "alert" not in text and "ukryte" not in text and ".x{}" not in text,
                  f"I-7: HTML -> text without scripts, styles and hidden elements: {text!r}")
        finally:
            os.environ.pop("TF_KB_ALLOW_LOCAL", None)
            srv.shutdown()

        # An empty or almost empty response (e.g. the page requires JavaScript) is an error, not a source
        empty = root / "empty.html"
        empty.write_text("<html><body> </body></html>", encoding="utf-8")
        try:
            kb.ingest(reg[2]["id"], root, file=empty)
            check(False, "I-8: empty content -> KbError")
        except kb.KbError as e:
            check("empty" in str(e) and not (cache / reg[2]["id"]).exists(), f"I-8: message and no entry in the cache: {e}")

        # An anti-bot page (Imperva, Cloudflare) is an error, not a source
        wall = root / "wall.html"
        wall.write_text("<html><head><title>Pardon Our Interruption</title></head><body><h1>Pardon Our Interruption</h1>"
                        + "<p>As you were browsing something about your browser made us think you were a bot.</p>" * 4
                        + "</body></html>", encoding="utf-8")
        try:
            kb.ingest(reg[2]["id"], root, file=wall)
            check(False, "I-9: anti-bot page -> KbError")
        except kb.KbError as e:
            check("anti-bot" in str(e), f"I-9: message: {e}")

        # A multi-file source: the hit points to a specific file
        multi = root / "multi.txt"
        multi.write_text("<!-- file: https://example.org/a.asciidoc -->\n" + "Wstęp do specyfikacji modułu.\n" * 8
                         + "<!-- file: https://example.org/b.asciidoc -->\n" + "Moduł z polem bliskie_unikalne_pole.\n"
                         + "Dalszy opis modułu.\n" * 8, encoding="utf-8")
        kb.ingest(reg[1]["id"], root, file=multi)
        hits = kb.search("bliskie_unikalne_pole", root)
        check(hits and hits[0]["file_url"] == "https://example.org/b.asciidoc", f"S-9: a file in a multi-file source: {hits[:1]}")

        # Freshness status and removal
        mp = cache / rid / "meta.json"
        meta = json.loads(mp.read_text(encoding="utf-8"))
        meta["fetched"] = "2025-01-01"
        mp.write_text(json.dumps(meta), encoding="utf-8")
        st = {x["id"]: x for x in kb.status(root, max_age=180, today="2026-10-20")}
        check(st[rid]["stale"] and st[rid]["age_days"] == 657, f"ST-1: a source older than 180 days -> stale: {st.get(rid)}")
        check(kb.remove(m["id"], root) and not (cache / m["id"]).exists(), "RM-1: removing a source from the cache")

        # Cache directory from TF_KB_DIR; the old name EVTF_KB_DIR still works
        for n, var in enumerate(("TF_KB_DIR", "EVTF_KB_DIR")):
            alt = Path(t) / f"alt-kb-{n}"
            os.environ[var] = str(alt)
            try:
                kb.ingest(rid, root, file=spec_file)
                check((alt / rid / "doc.txt").exists(), f"ENV-{n + 1}: {var} changes the cache directory")
            finally:
                os.environ.pop(var, None)

        # Command line
        run = lambda *a: subprocess.run([sys.executable, str(SCRIPT), *a, "--root", str(root)], capture_output=True, text=True)
        p = run("search", "step_size raz na sesję")
        check(p.returncode == 0 and "data, not instructions" in p.stdout and f"{rid}" in p.stdout and ":L" in p.stdout,
              f"CLI-1: text result with a safety header and a citation: {p.returncode} {p.stdout[:400]} {p.stderr[-200:]}")
        p = run("search", "credit_reference_id", "--json")
        check(p.returncode == 0 and json.loads(p.stdout)[0]["path"].endswith("szczegoly.md"), f"CLI-2: --json: {p.stdout[:200]}")
        p = run("search", "zupełnie nieobecne słowo kwarkowe")
        check(p.returncode == 1, f"CLI-3: no hits -> code 1: {p.returncode}")
        p = run("sources", "--area", "gateway")
        check(p.returncode == 0 and "spec-gateway" in p.stdout and "spec-tariffs" not in p.stdout,
              f"CLI-4: the list of an area's sources from all registries: {p.stdout[:300]}")
        p = run("ingest", "nie-ma-takiego-id")
        check(p.returncode == 2, f"CLI-5: unknown id without a URL -> code 2: {p.returncode} {p.stderr[-200:]}")
        p = run("status")
        check(p.returncode == 0 and rid in p.stdout, f"CLI-6: status: {p.stdout[:300]}")

    # The real factory: the registries of installed packs are valid
    check(kb.validate_registries(ROOT) == [], f"REAL-1: the factory's source registries: {kb.validate_registries(ROOT)}")

    if fails:
        print(f"✗ {len(fails)}/{total} knowledge base tests failed:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} knowledge base tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
