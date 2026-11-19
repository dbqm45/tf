#!/usr/bin/env python3
"""The 11.0.0 value migration (`migrations.migrate_values`): Polish identifiers of the task state, the loop and the configuration
in the project data → English. Tasks (`task.json`), runs (`run.json`), the project and personal configuration,
the cost profile; the descriptive content (titles, reasons) unchanged. python3 .claude/tests/test_migrate_values.py"""
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "migrations.py").is_file())


def main() -> int:
    spec = importlib.util.spec_from_file_location("mv_migrations", ROOT / ".tf" / "factory" / "migrations.py")
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        task = p / "docs/project/changes/IMP-1/task.json"
        task.parent.mkdir(parents=True)
        task.write_text(json.dumps({"key": "IMP-1", "title": "Przegląd realizacji", "stage": "realizacja",
                                    "weight": "pelna", "mode": "zwykly",
                                    "stage_log": [{"from": "przyjecie", "to": "specyfikacja"}],
                                    "deploy": {"state": "czerwone", "why": "test dymny czerwony"}}, ensure_ascii=False))
        run = p / ".tf/runs/IMP-1/run.json"
        run.parent.mkdir(parents=True)
        run.write_text(json.dumps({"key": "IMP-1", "stage": "needs", "stop_code": "pytanie",
                                   "current": {"k": "K1", "rounds": [{"test": "pass", "kod": "pass", "weryf": "run",
                                                                      "zakres": "todo"}]}}))
        cfg = p / ".tf/config/config.yaml"
        cfg.parent.mkdir(parents=True)
        cfg.write_text("default_profile: oszczedny\nsteps:\n  przeglad: {tier: deep}\ntask:\n  allowed_modes: [plan, zwykly]\n",
                       encoding="utf-8")
        (p / ".tf/config/me.yaml").write_text("task:\n  default_mode: zwykly\n", encoding="utf-8")
        prof = p / ".claude/factory-profile.json"
        prof.parent.mkdir(parents=True)
        prof.write_text(json.dumps({"profile": "jakosc"}))
        plan = mig.migrate_values(p, dry=True)
        check(plan and task.read_text(encoding="utf-8").count("realizacja") == 1,
              f"MV-1: dry shows the changes and writes nothing: {plan}")
        mig.migrate_values(p, dry=False)
        tj = json.loads(task.read_text(encoding="utf-8"))
        check(tj["stage"] == "implementation" and tj["weight"] == "full" and tj["mode"] == "normal"
              and tj["stage_log"] == [{"from": "intake", "to": "spec"}] and tj["deploy"]["state"] == "red"
              and tj["title"] == "Przegląd realizacji" and tj["deploy"]["why"] == "test dymny czerwony",
              f"MV-2: task.json — stage, weight, mode, history, deployment; title and reasons unchanged: {tj}")
        rj = json.loads(run.read_text(encoding="utf-8"))
        check(rj["stop_code"] == "question" and rj["current"]["rounds"][0] == {"test": "pass", "code": "pass",
                                                                               "verify": "run", "scope": "todo"},
              f"MV-3: run.json — kod STOP i kroki rundy: {rj}")
        c = cfg.read_text(encoding="utf-8")
        check("default_profile: economy" in c and "  review: {tier: deep}" in c and "[plan, normal]" in c,
              f"MV-4: config.yaml projektu: {c}")
        check("default_mode: normal" in (p / ".tf/config/me.yaml").read_text(encoding="utf-8")
              and json.loads(prof.read_text())["profile"] == "quality", "MV-5: me.yaml and the cost profile")
        check(mig.migrate_values(p, dry=False) == [], "MV-6: migrating again changes nothing")

        dec = p / "docs/project/changes/CHG-1/decisions.md"
        dec.parent.mkdir(parents=True)
        dec.write_text("## Kto: zespół\n- ref: CHG-1/D1\n- id:\n- wyslano: nie\n- kiedy: 2026-11-01\n- kto: Ola\n"
                       "- rodzaj: product\n- dlaczego: kto pyta, dostaje odpowiedź\n- zrodlo: manual\n- szkic: ai\n"
                       "- ustalenie: DES-001:TSK-1\n- skutek: resolve\n- pochodzenie: pdi\n- pytanie: Jak?\n"
                       "- odpowiedz: Tak.\n\n## D2\n- ref: CHG-1/D2\n- wyslano: tak\n", encoding="utf-8")
        mig.migrate_values(p, dry=False)
        d = dec.read_text(encoding="utf-8")
        check("- sent: no\n- date: 2026-11-01\n- by: Ola\n- kind: product\n- why: kto pyta, dostaje odpowiedź\n"
              "- source: manual\n- drafted_by: ai\n- finding: DES-001:TSK-1\n- effect: resolve\n- origin: pdi\n"
              "- question: Jak?\n- answer: Tak.\n" in d and "## Kto: zespół" in d and "- sent: yes" in d,
              f"MV-7: decisions.md (pdi) — entry fields and sent yes/no; heading and content unchanged: {d}")
        check(mig.migrate_values(p, dry=False) == [], "MV-8: migrating decisions.md again changes nothing")

        reg = p / ".tf/register/items.jsonl"
        reg.parent.mkdir(parents=True)
        reg.write_text('{"id": "A-1", "status": "otwarte", "note": "otwarte pytanie"}\n'
                       '{"id": "A-2", "status": "rozstrzygnięte", "note": ""}\n', encoding="utf-8")
        mig.migrate_values(p, dry=False)
        rows = [json.loads(x) for x in reg.read_text(encoding="utf-8").splitlines()]
        check([r["status"] for r in rows] == ["open", "resolved"] and rows[0]["note"] == "otwarte pytanie",
              f"MV-9: the tf analyze register — status open/resolved, note unchanged: {rows}")

        # 14.0.0: the plan and spec syntax of open tasks; the approval stays valid, closed ones unchanged
        import hashlib
        import re

        def h(b: bytes) -> str:
            return hashlib.sha256(b).hexdigest()

        def approval(b: bytes) -> str:
            return h(re.sub(rb"(?m)^(\s*-\s*)\[[xX]\](\s*[KS]\d+\b)", rb"\1[ ]\2", b))

        spec_pl = ("# Specyfikacja: Limit\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 h, gdy kierowca płaci, wtedy opłata "
                   "wynosi 45 zł.\n\n## Bez zmian\n\n- Pierwsze 30 minut gratis.\n\n## Poza zakresem\n\n- Abonamenty.\n\n"
                   "## Otwarte pytania\n\n- [blokuje] Czy motocykle też?\n")
        plan_pl = ("# Plan\n- [x] K1 — opłata · kryteria: test_fee · pliki: src/fee.py · weryfikacja: `pytest` · po: brak\n"
                   "- [ ] K2 — paragon · pliki: src/receipt.py · po: K1\n")
        for key, stage in (("OPEN-1", "implementation"), ("DONE-1", "closed")):
            d = p / "docs/project/changes" / key
            d.mkdir(parents=True, exist_ok=True)
            (d / "spec.md").write_text(spec_pl, encoding="utf-8")
            (d / "plan.md").write_text(plan_pl, encoding="utf-8")
            sb, pb = spec_pl.encode(), plan_pl.encode()
            (d / "task.json").write_text(json.dumps({
                "key": key, "title": "Limit", "stage": stage,
                "artifacts": {"spec.md": {"status": "zatwierdzony", "approved_sha": h(sb)},
                              "plan.md": {"status": "zatwierdzony", "approved_sha": approval(pb), "inputs": {"spec.md": h(sb)}},
                              "notes.md": {"status": "szkic"}},
                "frozen": {f"docs/project/changes/{key}/spec.md": {"sha": h(sb), "by": "human:ola"}}}, ensure_ascii=False))
        mig.migrate_values(p, dry=False)
        od = p / "docs/project/changes/OPEN-1"
        spec, plan = (od / "spec.md").read_text(encoding="utf-8"), (od / "plan.md").read_text(encoding="utf-8")
        check(spec.startswith("# Spec: Limit") and "## Acceptance criteria" in spec and "## Unchanged" in spec
              and "## Out of scope" in spec and "## Open questions" in spec and "[blocking]" in spec
              and "- AC-1: Given postój 12 h, when kierowca płaci, then opłata wynosi 45 zł." in spec,
              f"MV-10: spec.md of an open task — sections and Given/When/Then, content unchanged: {spec}")
        check("- [x] K1 — opłata · criteria: test_fee · files: src/fee.py · verify: `pytest` · after: none" in plan
              and "- [ ] K2 — paragon · files: src/receipt.py · after: K1" in plan,
              f"MV-11: plan.md — fields in English, slice identifiers unchanged: {plan}")
        tj = json.loads((od / "task.json").read_text(encoding="utf-8"))
        a = tj["artifacts"]
        check(a["spec.md"]["approved_sha"] == h(spec.encode()) and a["plan.md"]["approved_sha"] == approval(plan.encode())
              and a["plan.md"]["inputs"]["spec.md"] == h(spec.encode())
              and tj["frozen"]["docs/project/changes/OPEN-1/spec.md"]["sha"] == h(spec.encode()),
              f"MV-12: the approval, input and freeze hashes recomputed — the human's consent stays valid: {a} {tj['frozen']}")
        check(a["spec.md"]["status"] == "approved" and a["notes.md"]["status"] == "draft",
              f"MV-13: the task file status approved/draft: {a}")
        dd = p / "docs/project/changes/DONE-1"
        check((dd / "spec.md").read_text(encoding="utf-8") == spec_pl and (dd / "plan.md").read_text(encoding="utf-8") == plan_pl,
              "MV-14: a closed task — files unchanged (history)")
        check(mig.migrate_values(p, dry=False) == [], "MV-15: migrating again changes nothing")

        # pack migrations: `.tf/factory/packs/<id>/migrations.py` with `migrate_values(root, dry)`; an error does not stop it
        pk = p / ".tf/factory/packs"
        (pk / "pack-x").mkdir(parents=True)
        (pk / "pack-x" / "migrations.py").write_text(
            "from pathlib import Path\n"
            "def migrate_values(root, dry=True):\n"
            "    f = Path(root) / 'x.txt'\n"
            "    if f.exists():\n"
            "        return []\n"
            "    if not dry:\n"
            "        f.write_text('ok')\n"
            "    return ['x.txt']\n", encoding="utf-8")
        (pk / "pack-y").mkdir()
        (pk / "pack-y" / "migrations.py").write_text("def migrate_values(root, dry=True):\n    raise RuntimeError('boom')\n",
                                                    encoding="utf-8")
        plan = mig.migrate_values(p, dry=True)
        check(plan == ["x.txt"] and not (p / "x.txt").exists(), f"MV-16: dry — the pack migration is visible, nothing written: {plan}")
        check(mig.migrate_values(p, dry=False) == ["x.txt"] and (p / "x.txt").read_text() == "ok",
              "MV-17: the pack migration done; another pack's error does not stop it")

    # 19.0.0: project files that the readers read in the Polish form from before 14.x → the English form
    with tempfile.TemporaryDirectory() as t:
        p = Path(t)

        def put(rel: str, text: str) -> Path:
            f = p / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")
            return f

        wip = put(".tf/wip/login.md", "---\nupdated: 2026-11-01\n---\n## Pułapki i ślepe uliczki\n- Pułapki i ślepe uliczki: cache\n")
        retro = put("docs/project/archive/retro/20261101-retro.json",
                    json.dumps({"date": "2026-11-01", "decisions": {"a": "tak", "b": "nie", "c": "później", "d": "yes"},
                                "evidence": [{"key": "a", "text": "tak, nie"}]}, ensure_ascii=False, indent=1) + "\n")
        doc = "<!-- plik: https://x.org/a.pdf -->\ntekst plik: zostaje\n<!-- file: https://x.org/b.pdf -->\nb\n"
        put(".claude/knowledge/src-1/doc.txt", doc)
        meta = put(".claude/knowledge/src-1/meta.json", json.dumps({"id": "src-1", "sha256": hashlib.sha256(doc.encode()).hexdigest(),
                                                                    "bytes": len(doc.encode())}, indent=1))
        corpus = put("docs/project/02-domain/corpus.md",
                     "## S1 — notes/a.md\n- **E1** > „to tylko [wzmianka] w cytacie” — l. 3 [wzmianka]\n"
                     "- **E2** > „dwa” — l. 4 [Zastąpiony] [ważne]\n- **E3** > „trzy” — l. 5 [niezweryfikowany]\n")
        md = put("CLAUDE.md", "# Mój projekt\n\n### Komendy\nmoje\n\n<!-- team-factory:begin -->\n## Agent team\n### Komendy\n"
                              "- Test: `make t` (dostosuj do swojego projektu)\n\n### Język\n- po polsku\n<!-- team-factory:end -->\n")
        put(".claude/factory-manifest.json", json.dumps({"files": {".claude/skills/tf/SKILL.md": "x"}}))
        own = put(".claude/skills/fw-own/SKILL.md", "# fw-own\n\n## Pojęcia domenowe w Pythonie\n| encja | x |\n\n"
                                                    "## Zależne od wersji\n- 3.12 [niezweryfikowane]\n\n## Źródła\n"
                                                    "- docs.python.org (odczyt 2026-10-01)\n\n## Dalej\n- odczyt zostaje\n")
        own_ref = put(".claude/skills/fw-own/references/a.md", "## Źródła\n- x (odczyt 2026-10-02)\n")
        factory_skill = put(".claude/skills/tf/SKILL.md", "## Źródła\n- [niezweryfikowane] (odczyt 2026-10-03)\n")
        persona = put(".tf/config/personas/ola.yaml", "description: Analityczka. Uruchom przez `claude --agent ola`, gdy trzeba.\n")
        ma_readme = put("managed-agents/README.md", "# Managed Agents — wygenerowane przez fabrykę\n\nPliki…\n")
        ma_agent = put("managed-agents/agents/ola.md",
                       "---\n# WYGENEROWANO przez .tf/factory/build.py — nie edytuj ręcznie. Source: x\nname: ola\n---\n"
                       "WYGENEROWANO przez .tf/factory/build.py — treść\n")
        plan = put("docs/project/changes/CHG-1/plan.md",
                   "---\nartifact: plan\ntasks: [TSK-1]\n---\n| Cięcie | Rodzaj | Wydanie | Flaga | Wartość | Wymagania | Odblokowuje "
                   "| Weryfikacja |\n|---|---|---|---|---|---|---|---|\n| TSK-1 | fundament | R1 | f-1 | wydanie | US-1 | TSK-2 | x |\n\n"
                   "## Rozważone opcje\n### Opcja A\n### Opcja B\n## Cele zmiany\n- pokrycie\n\n## Pytania do bramki\n- Czy?\n")
        req = put("docs/project/changes/CHG-1/requirements.md", "## Przegląd drugim modelem\n- ok\n\n## Uwagi\n- Pytania do bramki zostają\n")
        rec = "docs/project/00-reconstruction/"
        report = put(rec + "report.md", "# Report\nCommit abc\n\nOdświeżenie przyrostowe: 2026-10-01 · commit abc\n")
        rules = put(rec + "rules.md", "## Billing (szczegóły: modules/billing.md)\n- Limit [pytanie: czy?] (pewność: kod) "
                                      "[założenie] [Niezweryfikowane]\n")
        manifest = put(rec + "manifest.json", json.dumps({"commit": "abc", "batches": [{"name": "src (pliki)", "hash": "1"},
                                                                                       {"name": "lib", "hash": "2"}]}, indent=2))
        remap = put(rec + "raw/remap.json", json.dumps({"manifest": hashlib.sha256(manifest.read_bytes()).hexdigest(), "files": {}}))
        untouched = {f: f.read_bytes() for f in (factory_skill,)}
        plan_dry = mig.migrate_v19(p, dry=True)
        check(len(plan_dry) == 15 and "Pułapki" in wip.read_text(encoding="utf-8"),
              f"MV-18: 19.0.0 dry — lists the files, writes nothing: {plan_dry}")
        mig.migrate_values(p, dry=False)
        check(wip.read_text(encoding="utf-8").endswith("## Pitfalls and dead ends\n- Pułapki i ślepe uliczki: cache\n"),
              "MV-19: checkpoint — the traps heading in English, the content unchanged")
        rj = json.loads(retro.read_text(encoding="utf-8"))
        check(rj["decisions"] == {"a": "yes", "b": "no", "c": "later", "d": "yes"} and rj["evidence"][0]["text"] == "tak, nie",
              f"MV-20: retro decisions yes/no/later, the evidence text unchanged: {rj}")
        new_doc = "<!-- file: https://x.org/a.pdf -->\ntekst plik: zostaje\n<!-- file: https://x.org/b.pdf -->\nb\n"
        mj = json.loads(meta.read_text(encoding="utf-8"))
        check((p / ".claude/knowledge/src-1/doc.txt").read_text(encoding="utf-8") == new_doc
              and mj["sha256"] == hashlib.sha256(new_doc.encode()).hexdigest() and mj["bytes"] == len(new_doc.encode()),
              f"MV-21: kb cache — the file marker and the hash in meta.json: {mj}")
        check(corpus.read_text(encoding="utf-8") == "## S1 — notes/a.md\n- **E1** > „to tylko [wzmianka] w cytacie” — l. 3 [mention]\n"
              "- **E2** > „dwa” — l. 4 [superseded] [ważne]\n- **E3** > „trzy” — l. 5 [unverified]\n",
              f"MV-22: corpus.md — the entry tags, the quote unchanged: {corpus.read_text(encoding='utf-8')}")
        c = md.read_text(encoding="utf-8")
        check(c.startswith("# Mój projekt\n\n### Komendy\nmoje\n") and "### Commands\n- Test: `make t` (adapt to your project)" in c
              and "### Language\n- po polsku" in c, f"MV-23: CLAUDE.md — the factory block only: {c}")
        o = own.read_text(encoding="utf-8")
        check("## Domain concepts in Pythonie" in o and "## Version-dependent" in o and "[unverified]" in o
              and "## Sources\n- docs.python.org (accessed 2026-10-01)" in o and "- odczyt zostaje" in o
              and own_ref.read_text(encoding="utf-8") == "## Sources\n- x (accessed 2026-10-02)\n",
              f"MV-24: an own skill — sections, [unverified], „accessed” only in Sources: {o}")
        check(all(f.read_bytes() == b for f, b in untouched.items()), "MV-25: a factory-installed skill is left to the installer")
        check(persona.read_text(encoding="utf-8") == "description: Analityczka. Run with `claude --agent ola`, gdy trzeba.\n",
              f"MV-26: an own persona — the launch hint: {persona.read_text(encoding='utf-8')}")
        a = ma_agent.read_text(encoding="utf-8")
        check(ma_readme.read_text(encoding="utf-8").startswith("# Managed Agents — generated by the factory\n\nPliki")
              and a.startswith("---\n# GENERATED by .tf/factory/build.py — do not edit by hand. Source: x\n")
              and a.endswith("---\nWYGENEROWANO przez .tf/factory/build.py — treść\n"),
              f"MV-27: managed-agents — the README head and the marker in the header only: {a}")
        pl = plan.read_text(encoding="utf-8")
        check("| Slice | Kind | Release | Flag | Value | Requirements | Unblocks | Verification |" in pl
              and "| TSK-1 | fundament | R1 | f-1 | wydanie |" in pl and "## Options considered\n### Option A\n### Option B\n"
              "## Change targets\n" in pl and "## Gate questions\n- Czy?" in pl, f"MV-28: pdi plan.md — columns and headings: {pl}")
        check(req.read_text(encoding="utf-8") == "## Second-model review\n- ok\n\n## Uwagi\n- Pytania do bramki zostają\n",
              "MV-29: pdi artifact — the second-review heading; the text unchanged")
        check(report.read_text(encoding="utf-8").endswith("\nIncremental refresh: 2026-10-01 · commit abc\n")
              and rules.read_text(encoding="utf-8") == "## Billing (details: modules/billing.md)\n- Limit [question: czy?] "
              "(confidence: kod) [assumption] [unverified]\n", f"MV-30: reconstruction — the stamp and the marks: "
              f"{rules.read_text(encoding='utf-8')}")
        mf = json.loads(manifest.read_text(encoding="utf-8"))
        check([b["name"] for b in mf["batches"]] == ["src (files)", "lib"]
              and json.loads(remap.read_text())["manifest"] == hashlib.sha256(manifest.read_bytes()).hexdigest(),
              f"MV-31: the reconstruction manifest — batch names; the refresh mark follows the manifest: {mf}")
        check(mig.migrate_values(p, dry=False) == [] and mig.migrate_v19(p, dry=True) == [], "MV-32: migrating again changes nothing")
        installer = mig.claude_md_v19("x\n<!-- team-factory:begin -->\n### Komendy\n- a\n<!-- team-factory:end -->\n")
        check("### Commands\n- a" in installer, "MV-33: the installer's helper for the factory block")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} value migration tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
