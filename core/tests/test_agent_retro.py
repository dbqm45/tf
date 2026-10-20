#!/usr/bin/env python3
"""Testy skryptu retro_data.py (skill core-agent-retro): dowody do retrospektywy pracy agentów."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / ".claude" / "skills" / "core-agent-retro" / "scripts" / "retro_data.py").is_file())
SCRIPT = ROOT / ".claude" / "skills" / "core-agent-retro" / "scripts" / "retro_data.py"


def jl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def git(cwd: Path, *args: str, date: str = "2026-10-15T10:00:00") -> None:
    env = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date, "PATH": "/usr/bin:/bin"}
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                   cwd=cwd, check=True, capture_output=True, env=env)


def commit(root: Path, files: dict[str, str], msg: str, date: str) -> None:
    for f, body in files.items():
        (root / f).parent.mkdir(parents=True, exist_ok=True)
        (root / f).write_text(body, encoding="utf-8")
    git(root, "add", "-A", date=date)
    git(root, "commit", "-qm", msg, date=date)


def make(root: Path, with_git: bool = True) -> None:
    logs = root / ".claude" / "logs"
    jl(logs / "usage.jsonl", [
        {"ts": "2026-10-01T10:00:00+00:00", "session": "s0", "agent": "main", "output": 999999, "requests": 9,
         "cache_read": 1, "models": {"claude-opus": 999999}, "skills": [], "tier_feedback": None},
        {"ts": "2026-10-15T10:00:00+00:00", "session": "s1", "agent": "main", "output": 5000, "requests": 20,
         "cache_read": 900000, "models": {"claude-opus": 5000}, "skills": ["fw-angular"], "tier_feedback": None},
        {"ts": "2026-10-15T11:00:00+00:00", "session": "s1", "agent": "ola-frontend", "output": 12000, "requests": 30,
         "cache_read": 100000, "models": {"claude-sonnet": 12000}, "skills": ["fe-css"], "tier_feedback": "za niski"},
        {"ts": "2026-10-16T11:00:00+00:00", "session": "s2", "agent": "ola-frontend", "output": 8000, "requests": 10,
         "cache_read": 50000, "models": {"claude-sonnet": 8000}, "skills": [], "tier_feedback": "za niski"},
    ])
    jl(logs / "skill-hints.jsonl", [
        {"ts": "2026-10-15T10:00:00+00:00", "session": "s1", "hinted": ["fw-angular", "tool-nx"]},
        {"ts": "2026-10-16T10:00:00+00:00", "session": "s2", "hinted": ["tool-nx"]},
    ])
    proj = root / "docs" / "project"
    (proj / "archive" / "wip").mkdir(parents=True)
    (proj / "journal.md").write_text(
        "# Dziennik\n\n| Kiedy | Kto | Faza | Zdarzenie |\n|---|---|---|---|\n"
        "| 2026-10-01 09:00 | claude | plan | Stary wpis spoza okna — błąd |\n"
        "| 2026-10-15 09:00 | claude | realizacja | Dodano formularz |\n"
        "| 2026-10-16 09:00 | claude | realizacja | Test nie zadziałał w CI, cofnięto zmianę |\n", encoding="utf-8")
    (proj / "archive" / "wip" / "20261016-formularz.md").write_text(
        "---\ntask: formularz\nupdated: 2026-10-16 12:00\n---\n# Formularz\n\n## Pułapki i ślepe uliczki\n"
        "- Vitest w trybie watch zawiesza hook — uruchamiaj z --run.\n\n## Otwarte pytania\n", encoding="utf-8")
    (proj / "archive" / "wip" / "20260901-stary.md").write_text(
        "---\ntask: stary\nupdated: 2026-09-01 12:00\n---\n# Stary\n\n## Pułapki i ślepe uliczki\n- Stara pułapka.\n",
        encoding="utf-8")
    (proj / "lessons.md").write_text(
        "# Lekcje\n\n## Wykonanie i weryfikacja\n"
        "- 2026-10-02 **Uruchamiaj Vitest z --run w hookach** — Kontekst: hooki · Zamiast tego: --run · Dotyczy: realizacja\n",
        encoding="utf-8")
    if with_git:
        git(root, "init", "-q", "-b", "main")
        commit(root, {"src/a.ts": "a\n"}, "feat(web): add form", "2026-10-15T10:00:00")
        commit(root, {"src/a.ts": "a2\n"}, "fix(web): correct form validation", "2026-10-15T12:00:00")
        commit(root, {"src/b.ts": "b\n"}, "feat(web): draft list (wip)", "2026-10-16T10:00:00")
        commit(root, {"src/b.ts": "b2\n"}, 'Revert "feat(web): draft list (wip)"', "2026-10-16T11:00:00")


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--since", "2026-10-10",
                           "--until", "2026-10-17", *args], capture_output=True, text=True, timeout=60)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        make(root, with_git=bool(shutil.which("git")))
        r = run(root, "--json")
        try:
            d = json.loads(r.stdout)
        except ValueError:
            d = {}
        check(r.returncode == 0 and d.get("window") == {"since": "2026-10-10", "until": "2026-10-17"},
              f"AR-1: okno czasu w wyniku: {r.stdout[:300]}{r.stderr[-300:]}")
        agents = {a["agent"]: a for a in d.get("tokens", {}).get("agents", [])}
        check(set(agents) == {"main", "ola-frontend"} and agents["ola-frontend"]["output"] == 20000
              and agents["ola-frontend"]["sessions"] == 2 and agents["main"]["output"] == 5000,
              f"AR-2: tokeny per agent tylko z okna (wpis sprzed okna pominięty): {agents}")
        check(d.get("tokens", {}).get("agents", [{}])[0].get("agent") == "ola-frontend",
              "AR-3: agenci posortowani malejąco po tokenach wyjścia")
        check(agents.get("ola-frontend", {}).get("tier_feedback") == {"za niski": 2},
              f"AR-4: sygnały „Tier: za niski/za wysoki” zliczone per agent: {agents.get('ola-frontend')}")
        h = d.get("hints", {})
        check(h.get("missed") == {"fe-css": 1} and h.get("ignored") == {"tool-nx": 2},
              f"AR-5: podpowiedzi — użyte bez podpowiedzi (przeoczone) i podpowiadane bez użycia: {h}")
        j = d.get("journal", {})
        check(j.get("entries") == 2 and len(j.get("flagged", [])) == 1 and "cofnięto" in j["flagged"][0],
              f"AR-6: dziennik z okna, wpisy z sygnałem problemu wyróżnione: {j}")
        traps = d.get("traps", [])
        check(len(traps) == 1 and "Vitest" in traps[0]["text"] and traps[0]["file"].endswith("20261016-formularz.md"),
              f"AR-7: pułapki z punktów kontrolnych z okna: {traps}")
        les = d.get("lessons", [])
        check(les == ["Uruchamiaj Vitest z --run w hookach"], f"AR-8: istniejące lekcje (reguły) do wykrycia powtórek: {les}")
        if shutil.which("git"):
            g = d.get("git", {})
            check(g.get("commits") == 4 and g.get("wip") == 1 and len(g.get("reverts", [])) == 1,
                  f"AR-9: commity w oknie, commity WIP i cofnięcia: {g}")
            rw = g.get("rework", [])
            check(len(rw) == 1 and rw[0]["file"] == "src/a.ts" and len(rw[0]["commits"]) == 2,
                  f"AR-10: poprawka po własnym feat w tym samym pliku (praca od nowa): {rw}")
        ev = d.get("evidence", [])
        check(ev and ev[0]["id"] == "E-1" and all(e["id"] == f"E-{i + 1}" for i, e in enumerate(ev))
              and {"tier", "hint", "journal", "trap"} <= {e["kind"] for e in ev},
              f"AR-11: dowody ponumerowane E-n z rodzajem: {ev}")

        r = run(root)
        check(r.returncode == 0 and r.stdout.startswith("# Dane do retrospektywy") and "E-1" in r.stdout
              and "ola-frontend" in r.stdout, f"AR-12: raport markdown dla agenta: {r.stdout[:400]}")

    # Pamięć retrospektyw: stabilne klucze, zapis JSON, decyzje człowieka, trendy i propozycje liczone z logów.
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        make(root, with_git=bool(shutil.which("git")))
        retro = root / "docs" / "project" / "archive" / "retro"
        retro.mkdir(parents=True)
        (retro / "20261001-retro.json").write_text(json.dumps({
            "date": "2026-10-01", "window": {"since": "2026-09-20", "until": "2026-10-01"},
            "evidence": [{"key": "tier:ola-frontend:za niski"}, {"key": "hint-missed:fe-css"}, {"key": "rework:src/old.ts"}],
            "decisions": {"tier:ola-frontend:za niski": "tak", "hint-missed:fe-css": "nie", "rework:src/old.ts": "tak"}}),
            encoding="utf-8")
        d = json.loads(run(root, "--json").stdout or "{}")
        keys = {e.get("key") for e in d.get("evidence", [])}
        check({"tier:ola-frontend:za niski", "hint-missed:fe-css", "cost:ola-frontend"} <= keys
              and all(e.get("key") for e in d.get("evidence", [])),
              f"AR-14: każdy dowód ma stabilny klucz do porównań między retrospektywami: {sorted(keys)}")
        tr = d.get("trend", {})
        rec = {x["key"]: x for x in tr.get("recurring", [])}
        check(rec.get("tier:ola-frontend:za niski", {}).get("seen") == 1, f"AR-15: powtórka z poprzedniej retrospektywy: {tr}")
        meas = {x["key"]: x["status"] for x in tr.get("measured", [])}
        check(meas == {"tier:ola-frontend:za niski": "wraca", "rework:src/old.ts": "zniknęło"},
              f"AR-16: skutek zatwierdzonych zmian — zniknęło albo wraca: {meas}")
        check([x["key"] for x in tr.get("rejected_again", [])] == ["hint-missed:fe-css"],
              f"AR-17: sygnał odrzucony wcześniej wraca — oznaczony, żeby nie proponować bez nowych dowodów: {tr}")
        sug = {x["key"]: x for x in d.get("suggestions", [])}
        check("tier:ola-frontend:za niski" in sug and sug["tier:ola-frontend:za niski"]["place"] == "tier roli"
              and "hint-missed:fe-css" not in sug,
              f"AR-18: propozycje z logów — tier przy ≥2 sygnałach, słowa skilla dopiero przy ≥2 sesjach: {sug}")

        r = run(root, "--save")
        saved = retro / "20261017-retro.json"
        data = json.loads(saved.read_text(encoding="utf-8")) if saved.is_file() else {}
        check(r.returncode == 0 and data.get("window", {}).get("until") == "2026-10-17" and data.get("evidence")
              and data.get("decisions") == {}, f"AR-19: --save zapisuje JSON retrospektywy z dnia --until: {r.stdout}{r.stderr}")
        r = run(root, "--decide", "tier:ola-frontend:za niski=tak", "--decide", "trap:x=może")
        data = json.loads(saved.read_text(encoding="utf-8")) if saved.is_file() else {}
        check(r.returncode == 2 and data.get("decisions") == {}, f"AR-20: zła decyzja → kod 2, nic nie zapisane: {r.stdout}{r.stderr}")
        r = run(root, "--decide", "tier:ola-frontend:za niski=tak", "--decide", "hint-ignored:tool-nx=później")
        data = json.loads(saved.read_text(encoding="utf-8")) if saved.is_file() else {}
        check(r.returncode == 0 and data.get("decisions") == {"tier:ola-frontend:za niski": "tak",
                                                              "hint-ignored:tool-nx": "później"},
              f"AR-21: --decide zapisuje decyzje człowieka w pliku retrospektywy: {data.get('decisions')} {r.stderr}")
        run(root, "--save")
        data = json.loads(saved.read_text(encoding="utf-8")) if saved.is_file() else {}
        check(len(data.get("decisions", {})) == 2, f"AR-22: ponowny --save nie kasuje decyzji: {data.get('decisions')}")
        d = json.loads(run(root, "--json").stdout or "{}")
        check(not any(x["key"] == "tier:ola-frontend:za niski" and x.get("date") == "2026-10-17"
                      for x in d.get("trend", {}).get("measured", [])),
              "AR-23: bieżąca retrospektywa (z dnia --until) nie jest historią samej siebie")
        r = run(root)
        check("## Trend" in r.stdout and "wraca" in r.stdout and "## Propozycje z danych" in r.stdout,
              f"AR-24: raport markdown z sekcjami trendu i propozycji: {r.stdout[-600:]}")

    # Nachodzące okna: to samo zdarzenie (klucz i treść jak w poprzedniej retrospektywie) to „już ocenione”, nie powtórka.
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        make(root, with_git=bool(shutil.which("git")))
        cur = json.loads(run(root, "--json").stdout or "{}")
        ev = [e for e in cur.get("evidence", []) if e.get("key") and e.get("text")]
        same, other = ev[0], ev[1]
        since = cur.get("window", {}).get("since", "2026-10-03")
        retro = root / "docs" / "project" / "archive" / "retro"
        retro.mkdir(parents=True)
        (retro / "20261010-retro.json").write_text(json.dumps({
            "date": "2026-10-10", "window": {"since": "2026-10-01", "until": "2026-10-10"},
            "evidence": [{"key": same["key"], "text": same["text"]},
                         {"key": other["key"], "text": other["text"] + " (inne zdarzenie)"}],
            "decisions": {same["key"]: "tak"}}), encoding="utf-8")
        d = json.loads(run(root, "--json").stdout or "{}")
        tr = d.get("trend", {})
        rec = {x["key"] for x in tr.get("recurring", [])}
        check(same["key"] in tr.get("assessed", []) and same["key"] not in rec,
              f"AR-30: identyczny dowód z poprzedniej retrospektywy → już ocenione, nie powtórka: {tr}")
        check(other["key"] in rec, f"AR-31: ten sam klucz, inna treść → nadal powtórka: {tr}")
        meas = {x["key"]: x["status"] for x in tr.get("measured", [])}
        check(meas.get(same["key"]) == "bez nowych dowodów", f"AR-32: zatwierdzona zmiana bez nowych dowodów: {meas}")
        check(same["key"] not in {x["key"] for x in d.get("suggestions", [])}, "AR-33: brak propozycji z już ocenionych")
        ov = d.get("overlap") or {}
        check(ov.get("previous_until") == "2026-10-10" and since <= "2026-10-10",
              f"AR-34: okno nachodzi na poprzednią retrospektywę → ostrzeżenie: {ov}")
        r = run(root)
        check("nachodzi" in r.stdout and "już ocenione" in r.stdout, f"AR-35: ostrzeżenie w raporcie: {r.stdout[:900]}")

    # Luka w logach: commity po ostatnim wpisie logów → ostrzeżenie „dane niepełne” (hooki mogły być nieaktywne).
    if shutil.which("git"):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            make(root)
            d = json.loads(run(root, "--json").stdout or "{}")
            check(d.get("gaps") == [], f"AR-25: logi pokrywają commity → brak luki: {d.get('gaps')}")
            commit(root, {"src/c.ts": "c\n"}, "feat(web): add c", "2026-10-17T15:00:00")
            commit(root, {"src/d.ts": "d\n"}, "fix(web): fix d", "2026-10-17T16:00:00")
            d = json.loads(run(root, "--json").stdout or "{}")
            gaps = d.get("gaps", [])
            check(len(gaps) == 1 and gaps[0]["after_commits"] == 2 and gaps[0]["last_log"].startswith("2026-10-16")
                  and any(e["key"] == "data-gap:logs" for e in d.get("evidence", [])),
                  f"AR-26: commity po ostatnim wpisie logów → luka z liczbą commitów i dowód data-gap:logs: {gaps}")
            r = run(root)
            check("Dane niepełne" in r.stdout.split("## Tokeny", 1)[0], f"AR-27: ostrzeżenie na górze raportu: {r.stdout[:400]}")

    with tempfile.TemporaryDirectory() as t:
        r = run(Path(t), "--json")
        try:
            d = json.loads(r.stdout)
        except ValueError:
            d = {}
        check(r.returncode == 0 and {"usage.jsonl", "journal.md"} <= set(d.get("missing", [])),
              f"AR-13: brak źródeł → lista braków, kod 0: {r.stdout[:300]}{r.stderr[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów retro_data")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
