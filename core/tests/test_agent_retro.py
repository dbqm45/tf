#!/usr/bin/env python3
"""Tests of the retro_data.py script (the core-agent-retro skill): evidence for a retrospective of the agents' work."""
import datetime as dt
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
    logs = root / ".tf" / "logs"
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
    proj.mkdir(parents=True)
    arch = root / ".tf" / "wip" / "archive"
    arch.mkdir(parents=True)
    (proj / "journal.md").write_text(
        "# Dziennik\n\n| Kiedy | Kto | Faza | Zdarzenie |\n|---|---|---|---|\n"
        "| 2026-10-01 09:00 | claude | plan | Stary wpis spoza okna — błąd |\n"
        "| 2026-10-15 09:00 | claude | realizacja | Dodano formularz |\n"
        "| 2026-10-16 09:00 | claude | realizacja | Test nie zadziałał w CI, cofnięto zmianę |\n"
        "| 2026-10-16 10:00 | claude | delivery | Added the export endpoint |\n"
        "| 2026-10-16 11:00 | claude | delivery | The migration failed in CI, rolled back |\n", encoding="utf-8")
    (arch / "20261016-formularz.md").write_text(
        "---\ntask: formularz\nupdated: 2026-10-16 12:00\n---\n# Formularz\n\n## Pitfalls and dead ends\n"
        "- Vitest w trybie watch zawiesza hook — uruchamiaj z --run.\n\n## Otwarte pytania\n", encoding="utf-8")
    (arch / "20261015-logowanie.md").write_text(   # 14.x: English checkpoint section name
        "---\ntask: logowanie\nupdated: 2026-10-15 12:00\n---\n# Logowanie\n\n## Pitfalls and dead ends\n"
        "- The OAuth mock keeps state between tests — reset it in afterEach.\n\n## Open questions\n", encoding="utf-8")
    (arch / "20260901-stary.md").write_text(
        "---\ntask: stary\nupdated: 2026-09-01 12:00\n---\n# Stary\n\n## Pitfalls and dead ends\n- Stara pułapka.\n",
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
              f"AR-1: the time window in the result: {r.stdout[:300]}{r.stderr[-300:]}")
        agents = {a["agent"]: a for a in d.get("tokens", {}).get("agents", [])}
        check(set(agents) == {"main", "ola-frontend"} and agents["ola-frontend"]["output"] == 20000
              and agents["ola-frontend"]["sessions"] == 2 and agents["main"]["output"] == 5000,
              f"AR-2: tokens per agent only from the window (an entry from before the window skipped): {agents}")
        check(d.get("tokens", {}).get("agents", [{}])[0].get("agent") == "ola-frontend",
              "AR-3: agents sorted descending by output tokens")
        check(agents.get("ola-frontend", {}).get("tier_feedback") == {"za niski": 2},
              f"AR-4: the “Tier: za niski/za wysoki” signals counted per agent: {agents.get('ola-frontend')}")
        h = d.get("hints", {})
        check(h.get("missed") == {"fe-css": 1} and h.get("ignored") == {"tool-nx": 2},
              f"AR-5: hints — used without a hint (missed) and hinted without use: {h}")
        j = d.get("journal", {})
        check(j.get("entries") == 4 and len(j.get("flagged", [])) == 2 and "cofnięto" in j["flagged"][0]
              and "rolled back" in j["flagged"][1],
              f"AR-6: the journal from the window, entries with a problem signal highlighted (in Polish and English): {j}")
        traps = d.get("traps", [])
        by_file = {x["file"].rsplit("/", 1)[-1]: x["text"] for x in traps}
        check(len(traps) == 2 and "Vitest" in by_file.get("20261016-formularz.md", "")
              and "OAuth mock" in by_file.get("20261015-logowanie.md", ""),
              f"AR-7: traps from checkpoints in the window (the section in two checkpoints): {traps}")
        les = d.get("lessons", [])
        check(les == ["Uruchamiaj Vitest z --run w hookach"], f"AR-8: existing lessons (rules) for detecting repeats: {les}")
        if shutil.which("git"):
            g = d.get("git", {})
            check(g.get("commits") == 4 and g.get("wip") == 1 and len(g.get("reverts", [])) == 1,
                  f"AR-9: commits in the window, WIP commits and reverts: {g}")
            rw = g.get("rework", [])
            check(len(rw) == 1 and rw[0]["file"] == "src/a.ts" and len(rw[0]["commits"]) == 2,
                  f"AR-10: a fix after one's own feat in the same file (rework): {rw}")
        ev = d.get("evidence", [])
        check(ev and ev[0]["id"] == "E-1" and all(e["id"] == f"E-{i + 1}" for i, e in enumerate(ev))
              and {"tier", "hint", "journal", "trap"} <= {e["kind"] for e in ev},
              f"AR-11: evidence numbered E-n with a kind: {ev}")

        r = run(root)
        check(r.returncode == 0 and r.stdout.startswith("# Retrospective data") and "E-1" in r.stdout
              and "ola-frontend" in r.stdout, f"AR-12: a markdown report for an agent: {r.stdout[:400]}")

    # Retrospective memory: stable keys, JSON saving, human decisions, trends and proposals computed from the logs.
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        make(root, with_git=bool(shutil.which("git")))
        retro = root / "docs" / "project" / "archive" / "retro"
        retro.mkdir(parents=True)
        (retro / "20261001-retro.json").write_text(json.dumps({
            "date": "2026-10-01", "window": {"since": "2026-09-20", "until": "2026-10-01"},
            "evidence": [{"key": "tier:ola-frontend:za niski"}, {"key": "hint-missed:fe-css"}, {"key": "rework:src/old.ts"}],
            "decisions": {"tier:ola-frontend:za niski": "yes", "hint-missed:fe-css": "no", "rework:src/old.ts": "yes"}}),
            encoding="utf-8")
        d = json.loads(run(root, "--json").stdout or "{}")
        keys = {e.get("key") for e in d.get("evidence", [])}
        check({"tier:ola-frontend:za niski", "hint-missed:fe-css", "cost:ola-frontend"} <= keys
              and all(e.get("key") for e in d.get("evidence", [])),
              f"AR-14: every piece of evidence has a stable key for comparison between retrospectives: {sorted(keys)}")
        tr = d.get("trend", {})
        rec = {x["key"]: x for x in tr.get("recurring", [])}
        check(rec.get("tier:ola-frontend:za niski", {}).get("seen") == 1, f"AR-15: a repeat from the previous retrospective: {tr}")
        meas = {x["key"]: x["status"] for x in tr.get("measured", [])}
        check(meas == {"tier:ola-frontend:za niski": "coming back", "rework:src/old.ts": "gone"},
              f"AR-16: the effect of approved changes — gone or coming back: {meas}")
        check([x["key"] for x in tr.get("rejected_again", [])] == ["hint-missed:fe-css"],
              f"AR-17: a previously rejected signal returns — marked, so it is not proposed without new evidence: {tr}")
        sug = {x["key"]: x for x in d.get("suggestions", [])}
        check("tier:ola-frontend:za niski" in sug and sug["tier:ola-frontend:za niski"]["place"] == "role tier"
              and "hint-missed:fe-css" not in sug,
              f"AR-18: proposals from the logs — a tier at ≥2 signals, skill words only at ≥2 sessions: {sug}")

        r = run(root, "--save")
        saved = retro / "20261017-retro.json"
        data = json.loads(saved.read_text(encoding="utf-8")) if saved.is_file() else {}
        check(r.returncode == 0 and data.get("window", {}).get("until") == "2026-10-17" and data.get("evidence")
              and data.get("decisions") == {}, f"AR-19: --save writes the retrospective JSON from the --until day: {r.stdout}{r.stderr}")
        r = run(root, "--decide", "tier:ola-frontend:za niski=yes", "--decide", "trap:x=może")
        data = json.loads(saved.read_text(encoding="utf-8")) if saved.is_file() else {}
        check(r.returncode == 2 and data.get("decisions") == {}, f"AR-20: a bad decision → code 2, nothing saved: {r.stdout}{r.stderr}")
        r = run(root, "--decide", "tier:ola-frontend:za niski=yes", "--decide", "hint-ignored:tool-nx=later")
        data = json.loads(saved.read_text(encoding="utf-8")) if saved.is_file() else {}
        check(r.returncode == 0 and data.get("decisions") == {"tier:ola-frontend:za niski": "yes",
                                                              "hint-ignored:tool-nx": "later"},
              f"AR-21: --decide records the human's decisions in the retrospective file: {data.get('decisions')} {r.stderr}")
        run(root, "--save")
        data = json.loads(saved.read_text(encoding="utf-8")) if saved.is_file() else {}
        check(len(data.get("decisions", {})) == 2, f"AR-22: a repeated --save does not erase the decisions: {data.get('decisions')}")
        d = json.loads(run(root, "--json").stdout or "{}")
        check(not any(x["key"] == "tier:ola-frontend:za niski" and x.get("date") == "2026-10-17"
                      for x in d.get("trend", {}).get("measured", [])),
              "AR-23: the current retrospective (from the --until day) is not the history of itself")
        r = run(root)
        check("## Trend" in r.stdout and "coming back" in r.stdout and "## Proposals from the data" in r.stdout,
              f"AR-24: a markdown report with trend and proposal sections: {r.stdout[-600:]}")

    # Overlapping windows: the same event (key and content as in the previous retrospective) is “already assessed”, not a repeat.
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
            "decisions": {same["key"]: "yes"}}), encoding="utf-8")
        d = json.loads(run(root, "--json").stdout or "{}")
        tr = d.get("trend", {})
        rec = {x["key"] for x in tr.get("recurring", [])}
        check(same["key"] in tr.get("assessed", []) and same["key"] not in rec,
              f"AR-30: identical evidence from the previous retrospective → already assessed, not a repeat: {tr}")
        check(other["key"] in rec, f"AR-31: the same key, different content → still a repeat: {tr}")
        meas = {x["key"]: x["status"] for x in tr.get("measured", [])}
        check(meas.get(same["key"]) == "no new evidence", f"AR-32: an approved change without new evidence: {meas}")
        check(same["key"] not in {x["key"] for x in d.get("suggestions", [])}, "AR-33: no proposals from already-assessed evidence")
        ov = d.get("overlap") or {}
        check(ov.get("previous_until") == "2026-10-10" and since <= "2026-10-10",
              f"AR-34: the window overlaps the previous retrospective → a warning: {ov}")
        r = run(root)
        check("overlaps" in r.stdout and "already assessed" in r.stdout, f"AR-35: the warning in the report: {r.stdout[:900]}")

    # A gap in the logs: commits after the last log entry → an “incomplete data” warning (the hooks may have been inactive).
    if shutil.which("git"):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            make(root)
            d = json.loads(run(root, "--json").stdout or "{}")
            check(d.get("gaps") == [], f"AR-25: the logs cover the commits → no gap: {d.get('gaps')}")
            commit(root, {"src/c.ts": "c\n"}, "feat(web): add c", "2026-10-17T15:00:00")
            commit(root, {"src/d.ts": "d\n"}, "fix(web): fix d", "2026-10-17T16:00:00")
            d = json.loads(run(root, "--json").stdout or "{}")
            gaps = d.get("gaps", [])
            check(len(gaps) == 1 and gaps[0]["after_commits"] == 2 and gaps[0]["last_log"].startswith("2026-10-16")
                  and any(e["key"] == "data-gap:logs" for e in d.get("evidence", [])),
                  f"AR-26: commits after the last log entry → a gap with the commit count and the data-gap:logs evidence: {gaps}")
            r = run(root)
            check("Incomplete data" in r.stdout.split("## Tokens", 1)[0], f"AR-27: the warning at the top of the report: {r.stdout[:400]}")

    with tempfile.TemporaryDirectory() as t:
        r = run(Path(t), "--json")
        try:
            d = json.loads(r.stdout)
        except ValueError:
            d = {}
        check(r.returncode == 0 and {"usage.jsonl", "journal.md"} <= set(d.get("missing", [])),
              f"AR-13: no sources → a list of what is missing, code 0: {r.stdout[:300]}{r.stderr[-300:]}")

    # Recurring agent errors from two sources the factory already records: hook blocks
    # (.tf/logs/hook-blocks.jsonl, time in epoch seconds) and the `Rework-Cause:` trailer in fix commits.
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        ep = lambda s: dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp()
        jl(root / ".tf" / "logs" / "hook-blocks.jsonl", [
            {"ts": ep("2026-10-01T10:00:00"), "hook": "guard_bash", "decision": "deny"},      # outside the window
            *[{"ts": ep(f"2026-10-1{i}T10:00:00"), "hook": "guard_bash", "decision": "deny"} for i in (2, 3, 4)],
            {"ts": ep("2026-10-15T10:00:00"), "hook": "guard_paths", "decision": "ask"},
        ])
        if shutil.which("git"):
            git(root, "init", "-q", "-b", "main")
            commit(root, {"a.py": "1\n"}, "feat: a", "2026-10-12T10:00:00")
            for i, cause in enumerate(("agent-error", "blad-agenta", "spec-gap")):   # old value → alias
                commit(root, {"a.py": f"{i + 2}\n"}, f"fix: a {i}\n\nRework-Cause: {cause}", f"2026-10-1{3 + i}T10:00:00")
        d = json.loads(run(root, "--json").stdout or "{}")
        ev = {e["key"]: e for e in d.get("evidence", [])}
        check(ev.get("block:guard_bash:deny", {}).get("n") == 3 and ev.get("block:guard_paths:ask", {}).get("n") == 1,
              f"AR-36: hook blocks from the window (epoch time) per hook and decision, an entry outside the window skipped: {sorted(ev)}")
        sug = {x["key"]: x for x in d.get("suggestions", [])}
        check("block:guard_bash:deny" in sug and "block:guard_paths:ask" not in sug,
              f"AR-37: a proposal only at ≥3 denials of the same hook: {sorted(sug)}")
        if shutil.which("git"):
            check(ev.get("rework-cause:agent-error", {}).get("n") == 2
                  and ev.get("rework-cause:spec-gap", {}).get("n") == 1,
                  f"AR-38: fix causes from the Rework-Cause trailer: {sorted(ev)}")
            check("rework-cause:agent-error" in sug and "rework-cause:spec-gap" not in sug,
                  f"AR-39: a proposal at ≥2 fixes with the same cause: {sorted(sug)}")
        md = run(root).stdout
        check("guard_bash" in md and "Hook blocks" in md, f"AR-40: the markdown report shows hook blocks: {md[:600]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} retro_data tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
