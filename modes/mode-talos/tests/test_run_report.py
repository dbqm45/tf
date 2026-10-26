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
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cfg)}
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

        # start: katalog przebiegu z szablonami, slug bez polskich znaków
        r = run(["start", "Import rozliczeń CDR", "--story", "Jako operator chcę importować CDR."], proj, cfg)
        runs = sorted((proj / ".claude" / "runs").glob("*-import-rozliczen-cdr"))
        check(r.returncode == 0 and len(runs) == 1, f"R-1: start tworzy katalog przebiegu: {r.stdout} {r.stderr}")
        if runs:
            d = runs[0]
            check(all((d / f).is_file() for f in ("run.json", "story.md", "plan.md", "parked.md")),
                  f"R-2: pliki przebiegu: {sorted(x.name for x in d.iterdir())}")
            check("importować CDR" in (d / "story.md").read_text(encoding="utf-8"), "R-3: treść story zapisana")
            check(re.match(r"\d{4}-\d{2}-\d{2}-", d.name) is not None, f"R-4: data w nazwie katalogu: {d.name}")

        # finish: transkrypty sesji i podagenta od chwili startu
        run_dir = proj / ".claude" / "runs" / "2026-10-21-test"
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
        tr = sorted((proj / ".claude" / "runs").glob("*tsk-58*"))
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
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        (run_dir / "run.json").write_text(json.dumps({**meta, "change": "CHG-12", "task": "TSK-58"}), encoding="utf-8")
        r = run(["finish", str(run_dir)], proj, cfg)
        kept = chg / "runs" / "TSK-58.md"
        text = kept.read_text(encoding="utf-8") if kept.is_file() else ""
        check(r.returncode == 0 and "USD" in text and "TSK-58" in text and "changes/CHG-12/runs/TSK-58.md" in r.stdout,
              f"R-18: finish przebiegu cięcia zapisuje raport w dzienniku zmiany: {r.stdout[-300:]} {text[:300]}")

        # brak transkryptów → czytelny komunikat, nie wyjątek
        empty = Path(t) / "inny"
        empty.mkdir()
        r = run(["finish", str(run_dir)], empty, Path(t) / "pusty-cfg")
        check(r.returncode == 2 and "Traceback" not in r.stderr, f"R-13: brak transkryptów: {r.returncode} {r.stderr[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {18 - len(fails)}/18 testów raportu przebiegu")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
