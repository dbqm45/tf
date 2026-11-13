#!/usr/bin/env python3
"""Testy raportu przebiegu Talosa (tryb mode-talos, skill talos-story-run, scripts/run_report.py).
python3 .claude/tests/test_run_report.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "talos-story-run" / "scripts" / "run_report.py"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL).is_file())
SCRIPT = ROOT / REL


PLAN_MD = """---
artifact: plan
phase: plan
status: accepted
version: 1
created: 2026-10-25
updated: 2026-10-25
change: CHG-12
tasks: [TSK-57, TSK-58]
---
# Plan zmiany CHG-12

| Cięcie | Wydanie | Flaga | Wartość | Pliki | Weryfikacja |
|---|---|---|---|---|---|
| TSK-57 | R1 | payment-retry | klient ponawia nieudaną płatność | src/payments/retry.ts | `npm test -- retry` |
| TSK-58 | R1 | payment-retry | brak podwójnego obciążenia | src/payments/charge.ts | `npm test -- charge` |
"""
INTENT_MD = """---
artifact: intent
phase: discovery
status: accepted
version: 1
created: 2026-10-25
updated: 2026-10-25
change: CHG-12
---
# Zamiar zmiany CHG-12

## Problem
Klient nie może ponowić nieudanej płatności i porzuca zamówienie.

## Poza zakresem
- płatności cykliczne
"""


def run(args, cwd, cfg):
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cfg), "TALOS_DASHBOARD_OPEN": "0"}   # testy nie otwierają przeglądarki
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, env=env,
                          timeout=60)


def assistant(ts, mid, model, **usage):
    u = {"input_tokens": usage.get("i", 0), "output_tokens": usage.get("o", 0),
         "cache_read_input_tokens": usage.get("cr", 0),
         "cache_creation_input_tokens": usage.get("w5", 0) + usage.get("w1", 0),
         "cache_creation": {"ephemeral_5m_input_tokens": usage.get("w5", 0),
                            "ephemeral_1h_input_tokens": usage.get("w1", 0)}}
    return {"type": "assistant", "timestamp": ts, "message": {"id": mid, "model": model, "usage": u}}


def write_jsonl(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def main() -> int:
    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        proj.mkdir()

        # start (krok C4): zadanie ma katalog trwały docs/project/changes/<KEY>/ (ticket.md, plan.md, task.json — do gita)
        # i roboczy .tf/runs/<KEY>/ (run.json, parked.md — poza gitem; nie `.claude/runs/`, chroniony przez Claude Code);
        # klucz T-<RRRRMMDD>-<slug>, slug bez polskich znaków; w .tf/runs/talos/ nowy przebieg już nie powstaje
        r = run(["start", "Import rozliczeń CDR", "--story", "Jako operator chcę importować CDR."], proj, cfg)
        runs = sorted((proj / ".tf" / "runs").glob("T-*-import-rozliczen-cdr"))
        old = sorted((proj / ".tf" / "runs" / "talos").glob("*-import-rozliczen-cdr"))
        check(r.returncode == 0 and len(runs) == 1 and not old and not (proj / ".claude" / "runs").exists()
              and r.stdout.strip() == f".tf/runs/{runs[0].name if runs else '?'}",
              f"R-1: start tworzy .tf/runs/<KEY>/ i drukuje jego ścieżkę, bez .tf/runs/talos/<slug>: {r.stdout} {r.stderr}")
        if runs:
            d = runs[0]
            doc = proj / "docs" / "project" / "changes" / d.name
            check(all((d / f).is_file() for f in ("run.json", "parked.md"))
                  and all((doc / f).is_file() for f in ("ticket.md", "plan.md", "task.json"))
                  and not (d / "plan.md").exists() and not (d / "story.md").exists(),
                  f"R-2: pliki robocze i trwałe: {sorted(x.name for x in d.iterdir())} "
                  f"{sorted(x.name for x in doc.iterdir()) if doc.is_dir() else '—'}")
            check(doc.is_dir() and "importować CDR" in (doc / "ticket.md").read_text(encoding="utf-8"),
                  "R-3: treść historyjki zapisana w ticket.md")
            check(re.fullmatch(r"T-\d{8}-import-rozliczen-cdr", d.name) is not None, f"R-4: klucz z datą i slugiem: {d.name}")
            meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
            index = proj / "docs" / "project" / "changes" / "INDEX.md"
            check(meta.get("key") == d.name and meta.get("task_dir") == f"docs/project/changes/{d.name}"
                  and index.is_file() and d.name in index.read_text(encoding="utf-8"),
                  f"R-4a: run.json wskazuje zadanie, zadanie jest w indeksie: {meta}")
        # PRB-32 — klon produktu bez `.tf/runs/talos/` w .gitignore ma „?? tmp/” w statusie po pierwszym start i hook
        # „czyste drzewo robocze” Talosa (SKILL §0.1) oraz dispatch_local pdi uznają klon za brudny. Skrypt zakłada
        # `.tf/runs/talos/.gitignore` z `*`, tak jak docs/plugins.md opisuje dla samodzielnych instalacji trybu.
        gi = proj / ".tf" / "runs" / ".gitignore"
        check(gi.is_file() and gi.read_text(encoding="utf-8").strip() == "*",
              f"R-1a: start zakłada .tf/runs/.gitignore z `*`: istnieje={gi.is_file()}, "
              f"treść={gi.read_text(encoding='utf-8') if gi.is_file() else '—'!r}")
        import subprocess as _sp
        _sp.run(["git", "init", "-q", "-b", "main", str(proj)], check=True, capture_output=True)
        for _k, _v in (("user.name", "t"), ("user.email", "t@t"), ("commit.gpgsign", "false")):
            _sp.run(["git", "-C", str(proj), "config", _k, _v], check=True, capture_output=True)
        porcelain = _sp.run(["git", "-C", str(proj), "status", "--porcelain", ".tf/runs/"],
                            capture_output=True, text=True).stdout
        check(porcelain == "", f"R-1b: po start git status pusty w .tf/runs/: {porcelain!r}")

        # klucz z trackera, powtórny start, zły klucz; finish w nowym układzie zapisuje raport w katalogu zadania
        r = run(["start", "Limit dobowy", "--key", "PROJ-123", "--story", "x"], proj, cfg)
        pdoc = proj / "docs" / "project" / "changes" / "PROJ-123"
        check(r.returncode == 0 and r.stdout.strip() == ".tf/runs/PROJ-123" and (pdoc / "task.json").is_file(),
              f"R-25: --key nadaje klucz z trackera: {r.stdout} {r.stderr}")
        r = run(["start", "Limit dobowy", "--key", "PROJ-123", "--story", "x"], proj, cfg)
        check(r.returncode == 2 and "już istnieje" in r.stdout + r.stderr, f"R-26: powtórny start tego samego klucza: {r.stdout}")
        r = run(["start", "Zły klucz", "--key", "proj 1", "--story", "x"], proj, cfg)
        check(r.returncode == 2 and not (proj / ".tf" / "runs" / "proj 1").exists(),
              f"R-27: klucz spoza wzorca odrzucony, nic nie powstaje: {r.returncode} {r.stdout}")
        (pdoc / "plan.md").write_text("# Plan\n- [x] K1 — limit\n- [ ] K2 — druga doba\n", encoding="utf-8")
        prun = proj / ".tf" / "runs" / "PROJ-123"
        r = run(["finish", str(prun)], proj, Path(t) / "cfg-pusty")
        rep = (pdoc / "report.md").read_text(encoding="utf-8") if (pdoc / "report.md").is_file() else ""
        check(r.returncode == 2 and "1/2" in rep and not (prun / "report.md").exists(),
              f"R-28: finish czyta plan z katalogu zadania i tam zapisuje raport: {r.returncode} {rep[:200]}")
        check("docs(task): record PROJ-123" in r.stdout and "docs/project/changes/PROJ-123" in r.stdout,
              f"R-29: finish podpowiada jeden commit plików zadania: {r.stdout[-300:]}")

        # finish: transkrypty sesji i podagenta od chwili startu (przebieg w .tf/runs/talos/)
        run_dir = proj / ".tf" / "runs" / "talos" / "2026-10-21-test"
        run_dir.mkdir(parents=True)
        (run_dir / "run.json").write_text(json.dumps({"slug": "test", "started_at": "2026-10-21T10:00:00+00:00"}))
        (run_dir / "plan.md").write_text("# Plan\n- [x] K1 import\n- [x] K2 walidacja\n- [ ] K3 raport\n")
        (run_dir / "parked.md").write_text("# Odłożone\n- duplikaty CDR — do decyzji\n- strefy czasowe — do decyzji\n")
        slug = re.sub(r"[^A-Za-z0-9]", "-", str(proj.resolve()))
        sess = cfg / "projects" / slug / "S1.jsonl"
        write_jsonl(sess, [
            assistant("2026-10-21T09:59:00Z", "m0", "claude-opus-5-5", i=100, o=100),     # przed startem
            {"type": "user", "timestamp": "2026-10-21T10:00:05Z", "message": {"content": "story"}},
            assistant("2026-10-21T10:01:00Z", "m1", "claude-opus-5-5", i=10, o=5, cr=1000, w1=200),
            assistant("2026-10-21T10:01:01Z", "m1", "claude-opus-5-5", i=10, o=50, cr=1000, w1=200),  # pełny zapis
            assistant("2026-10-21T10:02:00Z", "m2", "claude-haiku-5-5", i=20, o=10),
        ])
        sub = cfg / "projects" / slug / "S1" / "subagents" / "agent-x.jsonl"
        write_jsonl(sub, [assistant("2026-10-21T10:05:00Z", "s1", "claude-haiku-5-5", i=30, o=15, w5=100)])
        (sub.parent / "agent-x.meta.json").write_text(json.dumps({"agentType": "scout"}))

        r = run(["finish", str(run_dir), "--json"], proj, cfg)
        try:
            rep = json.loads(r.stdout)
        except json.JSONDecodeError:
            rep = {}
            fails.append(f"R-5: finish --json zwraca JSON: {r.stdout[-500:]} {r.stderr[-500:]}")
        if rep:
            opus, haiku = rep["models"].get("opus", {}), rep["models"].get("haiku", {})
            check((opus.get("input"), opus.get("output"), opus.get("cache_read"), opus.get("cache_write_1h")) == (10, 50, 1000, 200),
                  f"R-6: opus — bez wpisu sprzed startu, ostatni zapis strumienia: {opus}")
            check((haiku.get("input"), haiku.get("output"), haiku.get("cache_write_5m")) == (50, 25, 100),
                  f"R-7: haiku — sesja i podagent razem: {haiku}")
            # opus: 10×4 + 50×20 + 1000×0,20 + 200×8 (zapis 1 h = 2× wejście); haiku: 50×0,10 + 25×0,50 + 100×0,125
            check(abs(rep["cost_usd"] - (2840 + 30) / 1e6) < 1e-9, f"R-8: koszt łączny: {rep.get('cost_usd')}")
            check(rep.get("duration_s") == 300, f"R-9: czas od startu do ostatniego wpisu: {rep.get('duration_s')}")
            check(rep.get("agents", {}).get("scout", {}).get("output") == 15 and "main" in rep.get("agents", {}),
                  f"R-10: podział na agentów (typ z meta podagenta): {rep.get('agents')}")
            check(rep.get("plan") == {"done": 2, "total": 3} and rep.get("parked") == 2,
                  f"R-11: postęp planu i liczba odłożonych: {rep.get('plan')} {rep.get('parked')}")
        md = (run_dir / "report.md").read_text(encoding="utf-8") if (run_dir / "report.md").exists() else ""
        check("opus" in md and "haiku" in md and "USD" in md and "2/3" in md, f"R-12: report.md: {md[:400]}")
        check("## Bezpieczeństwo" in md and "brak wyniku skanu" in md, f"R-14: bez skanu sekcja mówi o braku: {md[-300:]}")

        # R-11a: kawałek z commitem liczy się jako zrobiony, nawet gdy Talos nie odhaczył go w plan.md (CHG-4, 2026-11-07:
        # „Plan: 0/1” przy gotowym commicie). Baza: gałąź fazy pdi/<CHG>-delivery, gdy przebieg ma zmianę, inaczej main.
        def git(*a: str) -> None:
            _sp.run(["git", "-C", str(proj), *a], check=True, capture_output=True)
        (proj / "README.md").write_text("x\n")
        git("add", "README.md")
        git("commit", "-q", "-m", "chore: base")
        git("switch", "-q", "-c", "pdi/CHG-90-delivery")
        (proj / "decisions.md").write_text("d\n")
        git("add", "decisions.md")
        git("commit", "-q", "-m", "docs(CHG-90): decyzje przed realizacją (pdi)")
        git("switch", "-q", "-c", "story/k")
        (proj / "a.py").write_text("a = 1\n")
        git("add", "a.py")
        git("commit", "-q", "-m", "feat: a\n\nChange: TSK-90")
        cut_dir = proj / ".tf" / "runs" / "talos" / "2026-10-21-cut"
        cut_dir.mkdir(parents=True)
        (cut_dir / "run.json").write_text(json.dumps({"slug": "cut", "started_at": "2026-10-21T10:00:00+00:00",
                                                      "change": "CHG-90", "task": "TSK-90"}))
        (cut_dir / "plan.md").write_text("# Plan\n- [ ] K1 a\n- [ ] K2 b\n")
        r = run(["finish", str(cut_dir), "--json"], proj, cfg)
        try:
            got = json.loads(r.stdout).get("plan")
        except json.JSONDecodeError:
            got = r.stdout[-300:]
        check(got == {"done": 1, "total": 2},
              f"R-11a: commit kawałka liczy się mimo braku odhaczenia, commit decyzji pdi nie: {got}")
        git("switch", "-q", "main")
        import shutil as _sh
        _sh.rmtree(proj / "docs" / "project" / "changes" / "CHG-90", ignore_errors=True)

        # sekcja „Bezpieczeństwo” z summary.md skanów kawałków (security_scan.py --out <przebieg>/security/K<n>)
        sec = run_dir / "security" / "K2"
        sec.mkdir(parents=True)
        (sec / "summary.md").write_text("## Bezpieczeństwo\n\nSkan: PASS (blokujące: 0, poniżej progu: 1, błędy skanu: 0).\n\n"
                                        "Poniżej progu:\n- r.note src/a.py:3 (note) — drobiazg\n", encoding="utf-8")
        run(["finish", str(run_dir)], proj, cfg)
        md = (run_dir / "report.md").read_text(encoding="utf-8")
        check(md.count("## Bezpieczeństwo") == 1 and "### K2" in md and "r.note src/a.py:3" in md
              and "brak wyniku skanu" not in md, f"R-15: sekcja bezpieczeństwa z wyniku skanu: {md[-400:]}")
        # każda próba kawałka (security/K<n>/proba-<k>/summary.md): FAIL z ustaleniami, potem PASS — w kolejności prób
        for k, body in ((1, "Skan: FAIL (blokujące: 1, poniżej progu: 0, błędy skanu: 0).\n\nPoniżej progu: brak.\n\n"
                            "Blokujące i błędy:\n- node-sqlite-sql-from-string src/deployments.js:14 (CWE-89, warning)\n"),
                        (2, "Skan: PASS (blokujące: 0, poniżej progu: 0, błędy skanu: 0).\n\nPoniżej progu: brak.\n")):
            (sec.parent / "K1" / f"proba-{k}").mkdir(parents=True)
            (sec.parent / "K1" / f"proba-{k}" / "summary.md").write_text("## Bezpieczeństwo\n\n" + body, encoding="utf-8")
        (sec.parent / "K1" / "feedback.md").write_text("# Skan bezpieczeństwa\n\n- brak blokujących\n", encoding="utf-8")
        run(["finish", str(run_dir)], proj, cfg)
        md = (run_dir / "report.md").read_text(encoding="utf-8")
        i = {k: md.find(k) for k in ("### K1", "#### Próba 1", "node-sqlite-sql-from-string src/deployments.js:14",
                                     "#### Próba 2", "### K2")}
        check(all(v >= 0 for v in i.values()) and list(i.values()) == sorted(i.values()) and md.count("## Bezpieczeństwo") == 1
              and md.count("### K1") == 1 and "Skan: FAIL" in md, f"R-15a: wszystkie próby kawałka w raporcie: {i} {md[-900:]}")

        # status: jedna linia do kontroli budżetu po każdym kawałku (mało kontekstu), bez zapisu report.md
        (run_dir / "report.md").unlink()
        r = run(["status", str(run_dir)], proj, cfg)
        line = r.stdout.strip()
        check(r.returncode == 0 and line.count("\n") == 0 and "0.0029 USD" in line and "2/3" in line
              and not (run_dir / "report.md").exists(), f"R-14: status w jednej linii: {line!r}")

        # F1: przebieg od klucza cięcia zmiany (TSK z plan.md w docs/project/changes/CHG-n/), raport w repo
        chg = proj / "docs" / "project" / "changes" / "CHG-12"
        chg.mkdir(parents=True)
        (chg / "plan.md").write_text(PLAN_MD, encoding="utf-8")
        (chg / "intent.md").write_text(INTENT_MD, encoding="utf-8")
        r = run(["start", "--task", "TSK-58"], proj, cfg)
        tr = sorted((proj / ".tf" / "runs" / "talos").glob("*tsk-58*"))
        meta = json.loads((tr[0] / "run.json").read_text(encoding="utf-8")) if tr else {}
        story = (tr[0] / "story.md").read_text(encoding="utf-8") if tr else ""
        check(r.returncode == 0 and meta.get("change") == "CHG-12" and meta.get("task") == "TSK-58"
              and meta.get("flag") == "payment-retry",
              f"R-15: start --task — katalog przebiegu, run.json z change/task/flag: {r.stdout} {r.stderr} {meta}")
        check("TSK-58" in story and "brak podwójnego obciążenia" in story and "R1" in story
              and "Klient nie może ponowić" in story and "docs/project/changes/CHG-12" in story,
              f"R-16: story z wiersza planu i zamiaru zmiany: {story[:600]}")
        r = run(["start", "--task", "TSK-99"], proj, cfg)
        check(r.returncode == 2 and "TSK-99" in r.stdout + r.stderr and "Traceback" not in r.stderr,
              f"R-17: TSK spoza planów zmian → kod 2 z komunikatem: {r.returncode} {r.stdout} {r.stderr[-300:]}")

        # PRB-33: ten sam TSK w dwóch zmianach → błąd z listą zmian; --change rozstrzyga; zły --change → błąd
        chg2 = proj / "docs" / "project" / "changes" / "CHG-13"
        chg2.mkdir(parents=True)
        plan2 = (PLAN_MD.replace("change: CHG-12", "change: CHG-13")
                 .replace("# Plan zmiany CHG-12", "# Plan zmiany CHG-13")
                 # inna wartość w CHG-13, żeby slug nie kolidował z katalogiem z R-15
                 .replace("brak podwójnego obciążenia", "ponowienie w CHG-13"))
        (chg2 / "plan.md").write_text(plan2, encoding="utf-8")
        (chg2 / "intent.md").write_text(INTENT_MD.replace("CHG-12", "CHG-13"), encoding="utf-8")
        r = run(["start", "--task", "TSK-58"], proj, cfg)
        check(r.returncode == 2 and "CHG-12" in r.stdout + r.stderr and "CHG-13" in r.stdout + r.stderr
              and "--change" in r.stdout + r.stderr and "Traceback" not in r.stderr,
              f"R-33a: dwa dziennika z TSK-58 → kod 2 z listą zmian i podpowiedzią --change: {r.returncode} "
              f"{r.stdout} {r.stderr[-400:]}")
        r = run(["start", "--task", "TSK-58", "--change", "CHG-13"], proj, cfg)
        tr13 = sorted((proj / ".tf" / "runs" / "talos").glob("*tsk-58*"))
        meta13 = json.loads((tr13[-1] / "run.json").read_text(encoding="utf-8")) if tr13 else {}
        check(r.returncode == 0 and meta13.get("change") == "CHG-13",
              f"R-33b: --change CHG-13 wybiera CHG-13: {r.returncode} {r.stdout} {r.stderr} {meta13}")
        r = run(["start", "--task", "TSK-58", "--change", "CHG-77"], proj, cfg)
        check(r.returncode == 2 and ("CHG-77" in r.stdout + r.stderr) and "Traceback" not in r.stderr,
              f"R-33c: zły --change → kod 2: {r.returncode} {r.stdout} {r.stderr[-300:]}")
        # usuwamy drugi dziennik, żeby reszta testów miała jeden wpis
        import shutil as _sh
        _sh.rmtree(chg2)
        for leftover in sorted((proj / ".tf" / "runs" / "talos").glob("*tsk-58*"))[1:]:
            _sh.rmtree(leftover)
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        (run_dir / "run.json").write_text(json.dumps({**meta, "change": "CHG-12", "task": "TSK-58"}), encoding="utf-8")
        with (run_dir / "parked.md").open("a", encoding="utf-8") as f:
            f.write("- .gitignore dla config/build.json — config/build.json — plik z placeholderem w repo — dodać do "
                    ".gitignore — do decyzji\n")
        r = run(["finish", str(run_dir)], proj, cfg)
        kept = chg / "runs" / "TSK-58.md"
        text = kept.read_text(encoding="utf-8") if kept.is_file() else ""
        check(r.returncode == 0 and "USD" in text and "TSK-58" in text and "changes/CHG-12/runs/TSK-58.md" in r.stdout,
              f"R-18: finish przebiegu cięcia zapisuje raport w dzienniku zmiany: {r.stdout[-300:]} {text[:300]}")
        check("## Odłożone do decyzji" in text and "placeholderem w repo" in text and "- <" not in text,
              f"R-19: raport w repo ma pozycje z parked.md (PRB-14: parked.md jest poza gitem): {text[-600:]}")

        # R-35 (PRB-34): w kontenerze fazy pdi transkrypty bywają niedostępne (sandbox) — finish i tak zapisuje raport
        # cięcia (plan, odłożone, bezpieczeństwo) z adnotacją o braku danych o koszcie; kod 2 jak dotąd (R-13)
        kept.unlink()
        r = run(["finish", str(run_dir)], proj, Path(t) / "brak-transkryptow")
        text = kept.read_text(encoding="utf-8") if kept.is_file() else ""
        check(r.returncode == 2 and "brak danych o koszcie" in text and "placeholderem w repo" in text
              and "brak danych o koszcie" in r.stdout,
              f"R-35: finish bez transkryptów zapisuje raport z adnotacją: {r.returncode} {r.stdout[-400:]} {text[:400]}")
        r = run(["status", str(run_dir)], proj, Path(t) / "brak-transkryptow")
        check(r.returncode == 2, f"R-36: status bez transkryptów → kod 2: {r.returncode} {r.stdout[-300:]}")

        # sesja uruchomiona w katalogu nadrzędnym (chmura z kilkoma repozytoriami, start z /home/user): transkrypty są
        # w katalogu projektu przodka, nie repozytorium — finish bez --session znajduje je i mówi, skąd wziął
        ws = Path(t) / "ws"
        repo = ws / "repo"
        rdir = repo / ".tf" / "runs" / "talos" / "2026-11-03-nested"
        rdir.mkdir(parents=True)
        (rdir / "run.json").write_text(json.dumps({"slug": "nested", "started_at": "2026-11-03T10:00:00+00:00"}))
        (rdir / "plan.md").write_text("# Plan\n- [x] K1 lista\n")
        (rdir / "parked.md").write_text("# Odłożone\n")
        cfg2 = Path(t) / "cfg2"
        ws_slug = re.sub(r"[^A-Za-z0-9]", "-", str(ws.resolve()))
        write_jsonl(cfg2 / "projects" / ws_slug / "W1.jsonl",
                    [assistant("2026-11-03T10:01:00Z", "w1", "claude-opus-5-5", i=10, o=20)])
        r = run(["finish", str(rdir), "--json"], repo, cfg2)
        try:
            nested = json.loads(r.stdout)
        except json.JSONDecodeError:
            nested = {}
        check(r.returncode == 0 and nested.get("requests") == 1,
              f"R-21: transkrypty sesji z katalogu nadrzędnego: {r.returncode} {r.stdout[-300:]} {r.stderr[-300:]}")
        check(ws_slug in str(nested.get("transcripts", "")), f"R-22: raport mówi, skąd wziął transkrypty: {nested.get('transcripts')}")

        # --session szuka sesji we wszystkich katalogach projektów (identyfikator sesji jest unikalny)
        other_slug = "-gdzie-indziej"
        write_jsonl(cfg2 / "projects" / other_slug / "X9.jsonl",
                    [assistant("2026-11-03T10:02:00Z", "x9", "claude-haiku-5-5", i=5, o=5)])
        r = run(["finish", str(rdir), "--session", "X9", "--json"], repo, cfg2)
        try:
            by_id = json.loads(r.stdout)
        except json.JSONDecodeError:
            by_id = {}
        check(r.returncode == 0 and by_id.get("requests") == 1 and "haiku" in by_id.get("models", {}),
              f"R-23: --session znajduje sesję w innym katalogu projektu: {r.returncode} {r.stdout[-300:]} {r.stderr[-300:]}")

        # nic nie znaleziono → komunikat z przeszukanymi katalogami i wskazówką, nie zgadywanie
        r = run(["finish", str(rdir)], repo, Path(t) / "cfg3")
        out = r.stdout + r.stderr
        check(r.returncode == 2 and "Traceback" not in r.stderr and ws_slug in out and "--session" in out
              and "katalogami nadrzędnymi" in out,
              f"R-24: komunikat wymienia przeszukane katalogi i podpowiada --session: {out[-600:]}")

        # brak transkryptów → czytelny komunikat, nie wyjątek
        empty = Path(t) / "inny"
        empty.mkdir()
        r = run(["finish", str(run_dir)], empty, Path(t) / "pusty-cfg")
        check(r.returncode == 2 and "Traceback" not in r.stderr, f"R-13: brak transkryptów: {r.returncode} {r.stderr[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {35 - len(fails)}/35 testów raportu przebiegu")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
