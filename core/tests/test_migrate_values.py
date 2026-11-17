#!/usr/bin/env python3
"""Migracja wartości 11.0.0 (`migrations.migrate_values`): polskie identyfikatory stanu zadania, pętli i konfiguracji
w danych projektu → angielskie. Zadania (`task.json`), przebiegi (`run.json`), konfiguracja projektu i osoby,
profil kosztów; treść opisów (tytuły, powody) bez zmian. python3 .claude/tests/test_migrate_values.py"""
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
              f"MV-1: dry pokazuje zmiany i niczego nie zapisuje: {plan}")
        mig.migrate_values(p, dry=False)
        tj = json.loads(task.read_text(encoding="utf-8"))
        check(tj["stage"] == "implementation" and tj["weight"] == "full" and tj["mode"] == "normal"
              and tj["stage_log"] == [{"from": "intake", "to": "spec"}] and tj["deploy"]["state"] == "red"
              and tj["title"] == "Przegląd realizacji" and tj["deploy"]["why"] == "test dymny czerwony",
              f"MV-2: task.json — etap, waga, tryb, historia, wdrożenie; tytuł i powody bez zmian: {tj}")
        rj = json.loads(run.read_text(encoding="utf-8"))
        check(rj["stop_code"] == "question" and rj["current"]["rounds"][0] == {"test": "pass", "code": "pass",
                                                                               "verify": "run", "scope": "todo"},
              f"MV-3: run.json — kod STOP i kroki rundy: {rj}")
        c = cfg.read_text(encoding="utf-8")
        check("default_profile: economy" in c and "  review: {tier: deep}" in c and "[plan, normal]" in c,
              f"MV-4: config.yaml projektu: {c}")
        check("default_mode: normal" in (p / ".tf/config/me.yaml").read_text(encoding="utf-8")
              and json.loads(prof.read_text())["profile"] == "quality", "MV-5: me.yaml i profil kosztów")
        check(mig.migrate_values(p, dry=False) == [], "MV-6: ponowna migracja nic nie zmienia")

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
              f"MV-7: decisions.md (pdi) — pola wpisu i sent yes/no; nagłówek i treść bez zmian: {d}")
        check(mig.migrate_values(p, dry=False) == [], "MV-8: ponowna migracja decisions.md nic nie zmienia")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów migracji wartości")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
