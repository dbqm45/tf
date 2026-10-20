#!/usr/bin/env python3
"""Testy factory/cost_stats.py: okresy, udział modeli, koszt USD i PLN (kurs średni NBP, tabela A), skuteczność,
ocena drogo/tanio (pasmo kontrolne, warianty „wszystko na Opusie” i „bez cache”)."""
import datetime as dt
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "factory" / "cost_stats.py").is_file())
SCRIPT = ROOT / "factory" / "cost_stats.py"
PRICES = {"haiku": {"input": 0.10, "output": 0.50, "cache_read": 0.01, "cache_write": 0.125},
          "sonnet": {"input": 2, "output": 10, "cache_read": 0.20, "cache_write": 2.5},
          "opus": {"input": 4, "output": 20, "cache_read": 0.20, "cache_write": 5},
          "claude-haiku-4-5": {"input": 1, "output": 5, "cache_read": 0.10, "cache_write": 1.25}}
NBP = {"table": "A", "currency": "dolar amerykański", "code": "USD",
       "rates": [{"no": "201/A/NBP/2026", "effectiveDate": "2026-10-16", "mid": 3.6512}]}


def load():
    spec = importlib.util.spec_from_file_location("ctf_cost_stats", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rec(ts, session, agent, models, inp=0, out=0, cr=0, cw=0, event="SubagentStop", fb=None):
    return {"ts": ts, "session": session, "event": event, "agent": agent, "input": inp, "output": out,
            "cache_read": cr, "cache_write": cw, "models": models, "tier_feedback": fb}


def git(cwd: Path, *args: str, date: str) -> None:
    env = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date, "PATH": "/usr/bin:/bin"}
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                   cwd=cwd, check=True, capture_output=True, env=env)


def commit(root: Path, f: str, msg: str, date: str) -> None:
    (root / f).parent.mkdir(parents=True, exist_ok=True)
    (root / f).write_text(msg, encoding="utf-8")
    git(root, "add", "-A", date=date)
    git(root, "commit", "-qm", msg, date=date)


def main() -> int:
    cs = load()
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    t = dt.datetime(2026, 10, 17, 12, tzinfo=dt.timezone.utc)
    check((cs.period_key(t, "day"), cs.period_key(t, "week"), cs.period_key(t, "month")) == ("2026-10-17", "2026-W42", "2026-10"),
          "CS-1: klucze okresów: dzień, tydzień ISO, miesiąc")

    c = cs.record_cost(rec("x", "s", "main", {"claude-opus-5-5": 1000}, inp=1000, out=1000, cr=1_000_000), PRICES)
    check(abs(c["usd"] - 0.224) < 1e-9, f"CS-2: koszt rekordu = wejście + wyjście + odczyt cache wg cennika: {c}")
    c = cs.record_cost(rec("x", "s", "main", {"claude-opus-5-5": 750, "claude-haiku-5-5": 250}, out=1000), PRICES)
    check(abs(c["usd"] - (750 * 20 + 250 * 0.5) / 1e6) < 1e-12 and abs(c["tokens"]["opus"] - 750) < 1e-9,
          f"CS-3: tokeny rekordu dzielone między modele proporcjonalnie do wyjścia: {c}")
    a = cs.record_cost(rec("x", "s", "main", {"claude-haiku-4-5": 1000}, out=1000), PRICES)["usd"]
    b = cs.record_cost(rec("x", "s", "main", {"claude-haiku-5-5": 1000}, out=1000), PRICES)["usd"]
    check(abs(a - 0.005) < 1e-12 and abs(b - 0.0005) < 1e-12, f"CS-4: cena dokładnego modelu ma pierwszeństwo przed rodziną: {a} {b}")

    records = [rec("2026-10-05T10:00:00+00:00", "s1", "main", {"claude-opus-5-5": 2000}, inp=1000, out=2000, cr=500_000),
               rec("2026-10-06T10:00:00+00:00", "s1", "x-frontend", {"claude-sonnet-5-5": 4000}, inp=2000, out=4000,
                   cr=100_000, fb="niski"),
               rec("2026-10-14T10:00:00+00:00", "s2", "main", {"claude-haiku-5-5": 1000}, inp=100, out=1000)]
    per = {p["period"]: p for p in cs.aggregate(records, PRICES, "week")}
    w41, w42 = per.get("2026-W41", {}), per.get("2026-W42", {})
    check(set(per) == {"2026-W41", "2026-W42"} and w41.get("sessions") == 1 and w41.get("runs") == 2
          and w41.get("output") == 6000 and abs(sum(w41.get("models_pct", {}).values()) - 100) < 0.01
          and w41["models_pct"]["opus"] > w41["models_pct"]["sonnet"],
          f"CS-5: agregacja per tydzień — sesje, uruchomienia, tokeny, udział modeli w %: {per}")
    check(w41["usd_all_opus"] > w41["usd"] and w41["usd_no_cache"] > w41["usd"] and w41.get("tier_low") == 1
          and 0 < w41.get("cache_pct", 0) < 100, f"CS-6: warianty „wszystko na Opusie” i „bez cache”, sygnały tieru, % cache: {w41}")

    check(cs.parse_nbp(NBP) == (3.6512, "201/A/NBP/2026", "2026-10-16"), "CS-7: kurs średni z odpowiedzi NBP (tabela A)")
    with tempfile.TemporaryDirectory() as d:
        cache = Path(d)
        r = cs.usd_pln(cache, now=t, fetch=lambda: NBP)
        check(r and r["rate"] == 3.6512 and r["table"] == "201/A/NBP/2026" and not r.get("stale"),
              f"CS-8: kurs pobrany i zapamiętany: {r}")
        r = cs.usd_pln(cache, now=t + dt.timedelta(hours=1), fetch=lambda: (_ for _ in ()).throw(OSError("offline")))
        check(r and r["rate"] == 3.6512 and not r.get("stale"), f"CS-8b: w ciągu dnia z pamięci: {r}")
        r = cs.usd_pln(cache, now=t + dt.timedelta(days=3), fetch=lambda: (_ for _ in ()).throw(OSError("offline")))
        check(r and r["rate"] == 3.6512 and r.get("stale") is True, f"CS-8c: bez sieci ostatni znany kurs, oznaczony: {r}")
        r = cs.usd_pln(Path(d) / "pusty", now=t, fetch=lambda: (_ for _ in ()).throw(OSError("offline")))
        check(r is None, f"CS-8d: bez sieci i pamięci brak kursu: {r}")
        r = cs.usd_pln(cache, now=t, fetch=lambda: NBP, override=4.0)
        check(r and r["rate"] == 4.0 and r["source"] == "ręczny", f"CS-8e: kurs podany ręcznie: {r}")

    check(cs.band([10, 11, 9, 10, 30])[-1] == "drogo" and cs.band([10, 11, 9, 10, 10.5])[-1] == "w normie"
          and cs.band([10, 11, 2, 10, 10.5])[2] == "tanio" and cs.band([10, 30])[-1] == "za mało danych",
          f"CS-9: pasmo kontrolne mediana ± 3·MAD: {cs.band([10, 11, 9, 10, 30])}")

    if shutil.which("git"):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            git(repo, "init", "-q", "-b", "main", date="2026-10-05T09:00:00")
            commit(repo, "src/a.ts", "feat(web): add a", "2026-10-05T11:00:00")
            commit(repo, "src/a.ts", "fix(web): fix a", "2026-10-06T11:00:00")
            commit(repo, "docs/x.md", "docs: notes", "2026-10-06T12:00:00")
            commit(repo, "src/b.ts", "feat(web): add b", "2026-10-14T11:00:00")
            ch = cs.changes(repo, "week")
            check(ch.get("2026-W41") == {"changes": 2, "rework": 1} and ch.get("2026-W42") == {"changes": 1, "rework": 0},
                  f"CS-10: zmiany feat/fix i praca od nowa per tydzień z gita: {ch}")
            log = repo / "usage.jsonl"
            log.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), "--period", "week", "--log", str(log), "--repo-root", str(repo),
                                "--usd-pln", "4", "--json"], capture_output=True, text=True, timeout=60)
            try:
                out = json.loads(r.stdout)
            except ValueError:
                out = {}
            p41 = {p["period"]: p for p in out.get("periods", [])}.get("2026-W41", {})
            check(r.returncode == 0 and out.get("rate", {}).get("rate") == 4.0 and abs(p41.get("pln", 0) - p41.get("usd", 0) * 4) < 1e-9
                  and p41.get("changes") == 2 and abs(p41.get("rework_pct", 0) - 50) < 1e-9 and p41.get("usd_per_change"),
                  f"CS-11: CLI --json — PLN z kursu, zmiany, praca od nowa, koszt na zmianę: {r.stdout[:600]}{r.stderr[-400:]}")
            r = subprocess.run([sys.executable, str(SCRIPT), "--period", "week", "--log", str(log), "--repo-root", str(repo),
                                "--usd-pln", "4"], capture_output=True, text=True, timeout=60)
            check(r.returncode == 0 and "PLN" in r.stdout and "Udział modeli" in r.stdout and "kurs" in r.stdout.lower()
                  and "Drogo czy tanio" in r.stdout, f"CS-12: raport markdown: {r.stdout[:800]}{r.stderr[-300:]}")

            commit(repo, "src/c.ts", "feat(web): add c", "2026-10-15T15:00:00")
            r = subprocess.run([sys.executable, str(SCRIPT), "--period", "week", "--log", str(log), "--repo-root", str(repo),
                                "--usd-pln", "4", "--json"], capture_output=True, text=True, timeout=60)
            out = json.loads(r.stdout or "{}")
            per2 = {p["period"]: p for p in out.get("periods", [])}
            check(out.get("gap") and per2.get("2026-W42", {}).get("band") == "dane niepełne"
                  and per2.get("2026-W42", {}).get("incomplete") is True and not per2.get("2026-W41", {}).get("incomplete"),
                  f"CS-13: okres z luką w logach oznaczony jako niepełny i wyłączony z oceny: {per2}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów cost_stats")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
