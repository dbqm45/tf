#!/usr/bin/env python3
"""
Dane do retrospektywy pracy agentów (skill core-agent-retro) — tylko biblioteka standardowa, nic nie zmienia.

  python3 .claude/skills/core-agent-retro/scripts/retro_data.py                 # ostatnie 14 dni, markdown
  python3 .claude/skills/core-agent-retro/scripts/retro_data.py --days 7
  python3 .claude/skills/core-agent-retro/scripts/retro_data.py --since 2026-10-01 --until 2026-10-17 --json
  ... --save                                    # zapisz docs/project/archive/retro/<RRRRMMDD --until>-retro.json
  ... --decide "tier:ola-frontend:za niski=tak" # decyzja człowieka (tak | nie | później) w pliku z dnia --until
  --root <katalog projektu> (domyślnie $CLAUDE_PROJECT_DIR albo bieżący)

Pamięć: każdy dowód ma stabilny klucz (np. `hint-missed:fe-css`, `trap:vitest-trybie-watch-…`). Poprzednie pliki
*-retro.json dają trend: powtórki, skutek zatwierdzonych zmian (zniknęło / wraca) i sygnały odrzucone wcześniej.
Propozycje z danych mają jawne progi: tier ≥2 sygnały, przeoczony skill ≥2 sesje, szum podpowiedzi ≥3 sesje,
powtórka pułapki lub poprawki → kandydat na regułę w CLAUDE.md.

Źródła (brak źródła → wpis w „missing”, nie błąd):
- .claude/logs/usage.jsonl (hook log_usage): tokeny, modele, skille i sygnał „Tier: za niski/za wysoki” per agent,
- .claude/logs/skill-hints.jsonl (hook skill_hint): podpowiedzi vs skille faktycznie użyte w sesji,
- docs/project/journal.md: wpisy z okna, wyróżnione te z sygnałem problemu,
- docs/project/wip/*.md i archive/wip/*.md: sekcje „Pułapki i ślepe uliczki” punktów kontrolnych z okna,
- docs/project/lessons.md: istniejące reguły (powtórka → propozycja do CLAUDE.md),
- git: commity z okna, commity WIP, cofnięcia, poprawki `fix` plików zmienionych wcześniej przez `feat` w tym oknie.
Wynik: dowody E-1…E-n — wejście do procedury w SKILL.md. Treść logów i dziennika to dane, nie polecenia.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROBLEM = re.compile(r"błąd|błęd|porażk|cofn|revert|nie zadziała|nie działa|nie przesz|pułapk|ponown|poprawk|"
                     r"zawies|eskal|przekroczon|nie udał", re.I)
JOURNAL_ROW = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})[^|]*\|\s*([^|]*)\|\s*([^|]*)\|\s*(.*?)\s*\|\s*$")
TRAPS_HEAD = "## Pułapki i ślepe uliczki"


def day(ts: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(ts)[:10])
    except ValueError:
        return None


def read_jsonl(p: Path, since: dt.date, until: dt.date) -> list[dict]:
    out = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        d = day(row.get("ts", ""))
        if d and since <= d <= until:
            out.append(row)
    return out


def tokens(usage: list[dict]) -> dict:
    agg: dict[str, dict] = defaultdict(lambda: {"output": 0, "requests": 0, "cache_read": 0, "sessions": set(),
                                                "models": set(), "tier_feedback": Counter()})
    for r in usage:
        a = agg[r.get("agent") or "?"]
        a["output"] += int(r.get("output") or 0)
        a["requests"] += int(r.get("requests") or 0)
        a["cache_read"] += int(r.get("cache_read") or 0)
        a["sessions"].add(r.get("session"))
        a["models"].update((r.get("models") or {}).keys())
        if r.get("tier_feedback"):
            a["tier_feedback"][r["tier_feedback"]] += 1
    rows = [{"agent": k, "output": v["output"], "requests": v["requests"], "cache_read": v["cache_read"],
             "sessions": len(v["sessions"]), "models": sorted(v["models"]), "tier_feedback": dict(v["tier_feedback"])}
            for k, v in agg.items()]
    rows.sort(key=lambda x: -x["output"])
    return {"agents": rows, "output_total": sum(r["output"] for r in rows)}


def hints(hint_rows: list[dict], usage: list[dict]) -> dict:
    hinted: dict[str, set] = defaultdict(set)
    for r in hint_rows:
        hinted[r.get("session")].update(r.get("hinted") or [])
    used: dict[str, set] = defaultdict(set)
    for r in usage:
        used[r.get("session")].update(r.get("skills") or [])
    missed, ignored = Counter(), Counter()
    for s in hinted:                      # tylko sesje z działającym hookiem podpowiedzi
        missed.update(used[s] - hinted[s])
        ignored.update(hinted[s] - used[s])
    return {"missed": dict(missed.most_common()), "ignored": dict(ignored.most_common())}


def journal(p: Path, since: dt.date, until: dt.date) -> dict:
    entries, flagged = 0, []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = JOURNAL_ROW.match(line)
        if not m or not (d := day(m.group(1))) or not since <= d <= until:
            continue
        entries += 1
        if PROBLEM.search(m.group(4)):
            flagged.append(f"{m.group(1)} [{m.group(3).strip()}] {m.group(4)}")
    return {"entries": entries, "flagged": flagged}


def traps(proj: Path, since: dt.date, until: dt.date, root: Path) -> list[dict]:
    out = []
    for f in sorted([*proj.glob("wip/*.md"), *proj.glob("archive/wip/*.md")]):
        text = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^updated:\s*(\S+)", text, re.M) or re.search(r"^started:\s*(\S+)", text, re.M)
        d = day(m.group(1)) if m else None
        if not d or not since <= d <= until or TRAPS_HEAD not in text:
            continue
        body = text.split(TRAPS_HEAD, 1)[1].split("\n## ", 1)[0]
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        for line in body.splitlines():
            line = line.strip()
            if line.startswith(("- ", "* ")) and len(line) > 3:
                out.append({"file": f.relative_to(root).as_posix(), "text": line[2:].strip()})
    return out


def lessons(p: Path) -> list[str]:
    return [m.group(1) for line in p.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.lstrip().startswith("- ") and (m := re.search(r"\*\*(.+?)\*\*", line))]


def git_data(root: Path, since: dt.date, until: dt.date) -> dict | None:
    try:
        r = subprocess.run(["git", "-C", str(root), "log", "--reverse", f"--since={since.isoformat()} 00:00",
                            f"--until={until.isoformat()} 23:59:59", "--format=\x1e%h\x1f%cI\x1f%s", "--name-only"],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    commits = []
    for block in r.stdout.split("\x1e")[1:]:
        head, *files = block.strip("\n").split("\n")
        sha, when, subject = (head.split("\x1f", 2) + ["", ""])[:3]
        commits.append({"sha": sha, "time": when, "subject": subject, "files": [f for f in files if f.strip()]})
    is_revert = lambda c: re.match(r"revert\b", c["subject"], re.I)
    reverts = [f"{c['sha']} {c['subject']}" for c in commits if is_revert(c)]
    wip = [c for c in commits if not is_revert(c) and re.search(r"\(wip\)|work in progress|\bwip\b", c["subject"], re.I)]
    feat_of: dict[str, str] = {}
    rework, seen = [], set()
    for c in commits:
        kind = re.match(r"(\w+)(\([^)]*\))?!?:", c["subject"])
        kind = kind.group(1).lower() if kind else ""
        for f in c["files"]:
            if kind == "feat":
                feat_of.setdefault(f, c["sha"])
            elif kind == "fix" and f in feat_of and f not in seen:
                seen.add(f)
                rework.append({"file": f, "commits": [feat_of[f], c["sha"]], "fix": c["subject"]})
    return {"commits": len(commits), "wip": len(wip), "reverts": reverts, "rework": rework,
            "times": [c["time"] for c in commits if c["time"]]}


def collect(root: Path, since: dt.date, until: dt.date) -> dict:
    logs, proj = root / ".claude" / "logs", root / "docs" / "project"
    data: dict = {"window": {"since": since.isoformat(), "until": until.isoformat()}, "missing": []}
    usage = read_jsonl(logs / "usage.jsonl", since, until) if (logs / "usage.jsonl").is_file() else None
    if usage is None:
        data["missing"].append("usage.jsonl")
    data["tokens"] = tokens(usage or [])
    if (logs / "skill-hints.jsonl").is_file():
        data["hints"] = hints(read_jsonl(logs / "skill-hints.jsonl", since, until), usage or [])
    else:
        data["missing"].append("skill-hints.jsonl")
        data["hints"] = {"missed": {}, "ignored": {}}
    if (proj / "journal.md").is_file():
        data["journal"] = journal(proj / "journal.md", since, until)
    else:
        data["missing"].append("journal.md")
        data["journal"] = {"entries": 0, "flagged": []}
    data["traps"] = traps(proj, since, until, root) if proj.is_dir() else []
    if (proj / "lessons.md").is_file():
        data["lessons"] = lessons(proj / "lessons.md")
    else:
        data["missing"].append("lessons.md")
        data["lessons"] = []
    g = git_data(root, since, until)
    if g is None:
        data["missing"].append("git")
    data["git"] = g or {"commits": 0, "wip": 0, "reverts": [], "rework": []}
    data["gaps"] = gaps(logs, until, data["git"].get("times", []))
    data["evidence"] = evidence(data)
    hist = history(root, until)
    data["trend"] = trend(data["evidence"], hist)
    data["overlap"] = overlap(since, hist)
    data["suggestions"] = suggestions(data)
    return data


def _ts(v: str) -> dt.datetime | None:
    try:
        t = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def gaps(logs: Path, until: dt.date, commit_times: list[str]) -> list[dict]:
    """Commity późniejsze niż ostatni wpis logów hooków → dane niepełne (np. sesja, w której hooki fabryki nie działały)."""
    last = None
    for name in ("usage.jsonl", "skill-hints.jsonl"):
        f = logs / name
        if not f.is_file():
            continue
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                t = _ts(json.loads(line).get("ts", ""))
            except ValueError:
                continue
            if t and t.date() <= until and (last is None or t > last):
                last = t
    if last is None:
        return []
    after = sorted(t for t in (_ts(x) for x in commit_times) if t and t > last + dt.timedelta(hours=1))
    return [{"last_log": last.isoformat(), "after_commits": len(after), "first_after": after[0].isoformat()}] if after else []


def norm(text: str, n: int = 6) -> str:
    """Klucz z tekstu: pierwsze słowa (≥4 znaki), małe litery — ta sama pułapka innymi datami ma ten sam klucz."""
    words = [w for w in re.findall(r"[^\W\d_]+", text.lower()) if len(w) >= 4]
    return "-".join(words[:n]) or "?"


def evidence(d: dict) -> list[dict]:
    ev = []

    def add(kind: str, key: str, text: str, n: int | None = None) -> None:
        ev.append({"id": f"E-{len(ev) + 1}", "kind": kind, "key": key, "text": text, **({"n": n} if n else {})})

    for gp in d.get("gaps", []):
        add("data", "data-gap:logs", f"logi hooków kończą się {gp['last_log'][:16]}, a po nich jest {gp['after_commits']} "
            "commitów — dane o kosztach i podpowiedziach niepełne (hooki fabryki nieaktywne?)", gp["after_commits"])
    tot = d["tokens"]["output_total"]
    for a in d["tokens"]["agents"][:3]:
        if tot:
            add("cost", f"cost:{a['agent']}", f"{a['agent']}: {a['output']} tokenów wyjścia ({100 * a['output'] // tot}% "
                f"okna), {a['sessions']} sesji, modele: {', '.join(a['models']) or '?'}")
    for a in d["tokens"]["agents"]:
        for k, n in a["tier_feedback"].items():
            add("tier", f"tier:{a['agent']}:{k}", f"{a['agent']}: „Tier: {k}” × {n}", n)
    for s, n in d["hints"]["missed"].items():
        add("hint", f"hint-missed:{s}", f"{s}: użyty bez podpowiedzi w {n} sesjach (kandydat na metadata.slowa)", n)
    for s, n in d["hints"]["ignored"].items():
        if n >= 2:
            add("hint", f"hint-ignored:{s}", f"{s}: podpowiadany, a nieużyty w {n} sesjach (szum podpowiedzi?)", n)
    for line in d["journal"]["flagged"]:
        add("journal", f"journal:{norm(line.split('] ', 1)[-1])}", line)
    for t in d["traps"]:
        add("trap", f"trap:{norm(t['text'])}", f"{t['text']} ({t['file']})")
    g = d["git"]
    for rw in g["rework"]:
        add("git", f"rework:{rw['file']}", f"poprawka po własnym feat: {rw['file']} ({' → '.join(rw['commits'])}: {rw['fix']})")
    for rv in g["reverts"]:
        add("git", f"revert:{norm(rv.split(' ', 1)[-1])}", f"cofnięcie: {rv}")
    if g["wip"]:
        add("git", "wip:commits", f"commity WIP: {g['wip']} z {g['commits']}")
    return ev


DECISIONS = ("tak", "nie", "później")
RETRO_DIR = Path("docs") / "project" / "archive" / "retro"


def history(root: Path, until: dt.date) -> list[dict]:
    """Poprzednie retrospektywy (pliki *-retro.json sprzed dnia --until), od najstarszej."""
    out = []
    for f in sorted((root / RETRO_DIR).glob("*-retro.json")):
        if f.name >= f"{until.strftime('%Y%m%d')}-retro.json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        data["_date"] = data.get("date") or f.name[:8]
        out.append(data)
    return out


def trend(ev: list[dict], hist: list[dict]) -> dict:
    """Powtórka = klucz z poprzedniej retrospektywy z NOWYM zdarzeniem. Dowód o tym samym kluczu i tej samej treści
    (okno nachodzi na poprzednie) to „już ocenione” — nie daje propozycji ani wyniku „wraca”."""
    seen: Counter = Counter()
    texts: dict[str, set] = {}
    last: dict[str, tuple[str, str]] = {}
    for h in hist:
        seen.update({e.get("key") for e in h.get("evidence", []) if e.get("key")})
        for e in h.get("evidence", []):
            if e.get("key") and e.get("text"):
                texts.setdefault(e["key"], set()).add(e["text"])
        for k, v in (h.get("decisions") or {}).items():
            last[k] = (v, h["_date"])
    keys = {e["key"] for e in ev}
    fresh = {e["key"] for e in ev if e.get("text") not in texts.get(e["key"], set())}
    assessed = sorted(keys - fresh)
    recurring = [{"key": k, "seen": seen[k], "last_decision": last.get(k, ("—", ""))[0]}
                 for k in sorted(fresh) if seen[k]]
    measured = [{"key": k, "date": dte,
                 "status": "wraca" if k in fresh else ("bez nowych dowodów" if k in keys else "zniknęło")}
                for k, (v, dte) in sorted(last.items()) if v == "tak"]
    rejected = [{"key": k, "date": dte} for k, (v, dte) in sorted(last.items()) if v == "nie" and k in fresh]
    return {"retros": len(hist), "recurring": recurring, "measured": measured, "rejected_again": rejected,
            "assessed": assessed}


def overlap(since: dt.date, hist: list[dict]) -> dict | None:
    """Okno zaczyna się przed końcem poprzedniej retrospektywy — część dowodów to zdarzenia już ocenione."""
    ends = [h.get("window", {}).get("until") for h in hist if isinstance(h.get("window"), dict)]
    ends = [e for e in ends if e and e >= since.isoformat()]
    return {"previous_until": max(ends)} if ends else None


def suggestions(d: dict) -> list[dict]:
    """Propozycje liczone z danych (progi stałe, jawne) — wejście do fazy decyzji, nie decyzja."""
    out = []
    for a in d["tokens"]["agents"]:
        for k, n in a["tier_feedback"].items():
            if n >= 2:
                up = "niski" in k
                out.append({"key": f"tier:{a['agent']}:{k}", "place": "tier roli",
                            "text": f"{a['agent']}: „{k}” × {n} — " + ("podnieś tier albo kieruj trudniejsze zadania do "
                                    "mocniejszego wykonawcy" if up else "rozważ tańszy model dla tej roli")
                            + " (core-cost-control)"})
    for s, n in d["hints"]["missed"].items():
        if n >= 2:
            out.append({"key": f"hint-missed:{s}", "place": "metadata.slowa",
                        "text": f"{s}: użyty bez podpowiedzi w {n} sesjach — dopisz słowa z poleceń (core-skill-authoring)"})
    for s, n in d["hints"]["ignored"].items():
        if n >= 3:
            out.append({"key": f"hint-ignored:{s}", "place": "opis i granice skilla",
                        "text": f"{s}: podpowiadany bez użycia w {n} sesjach — zawęź słowa lub dodaj no-trigger"})
    for r in d["trend"]["recurring"]:
        kind = r["key"].split(":", 1)[0]
        if kind in ("trap", "journal", "rework", "revert") and r["last_decision"] != "nie":
            out.append({"key": r["key"], "place": "reguła w CLAUDE.md",
                        "text": f"powtórka ({r['seen'] + 1}. retrospektywa z tym sygnałem) — kandydat na regułę "
                                "(core-agent-instructions)"})
    rejected = {r["key"] for r in d["trend"]["rejected_again"]}
    return [x for x in out if x["key"] not in rejected]


def render(d: dict) -> str:
    w = d["window"]
    out = [f"# Dane do retrospektywy ({w['since']} – {w['until']})", ""]
    if d["missing"]:
        out += [f"Brak źródeł: {', '.join(d['missing'])} — wnioski tylko z pozostałych.", ""]
    for gp in d.get("gaps", []):
        out += [f"**Dane niepełne:** logi hooków kończą się {gp['last_log'][:16]}, a po nich jest {gp['after_commits']} "
                "commitów. Hooki fabryki prawdopodobnie nie działały (np. sesja z kilkoma repozytoriami albo uruchomiona "
                "z katalogu nadrzędnego) — wnioski o kosztach, tierach i podpowiedziach dotyczą tylko czasu przed luką.", ""]
    out += ["## Tokeny per agent", "| Agent | Wyjście | Żądania | Sesje | Modele | Tier |", "|---|---|---|---|---|---|"]
    for a in d["tokens"]["agents"]:
        tf = ", ".join(f"{k} × {n}" for k, n in a["tier_feedback"].items()) or "—"
        out.append(f"| {a['agent']} | {a['output']} | {a['requests']} | {a['sessions']} | "
                   f"{', '.join(a['models']) or '—'} | {tf} |")
    g = d["git"]
    out += ["", f"Dziennik: {d['journal']['entries']} wpisów · pułapki: {len(d['traps'])} · lekcje: {len(d['lessons'])} · "
                f"git: {g['commits']} commitów, WIP {g['wip']}, cofnięcia {len(g['reverts'])}, poprawki po sobie "
                f"{len(g['rework'])}", "", "## Dowody"]
    if d.get("overlap"):
        out[2:2] = [f"**Okno nachodzi** na poprzednią retrospektywę (do {d['overlap']['previous_until']}): dowody o tej "
                    "samej treści są oznaczone jako już ocenione i nie dają propozycji. Następnym razem zacznij "
                    "`--since` dzień po jej końcu.", ""]
    done = set(d["trend"].get("assessed", []))
    out += [f"- **{e['id']}** [{e['kind']}] {e['text']}" + (" _(już ocenione)_" if e["key"] in done else "")
            for e in d["evidence"]] or ["- brak sygnałów w oknie"]
    tr = d["trend"]
    out += ["", f"## Trend (poprzednich retrospektyw: {tr['retros']})"]
    out += [f"- powtórka: `{x['key']}` (było w {x['seen']}, ostatnia decyzja: {x['last_decision']})" for x in tr["recurring"]]
    out += [f"- skutek zmiany z {x['date']}: `{x['key']}` — {x['status']}" for x in tr["measured"]]
    out += [f"- odrzucone {x['date']}, znów jest: `{x['key']}` — proponuj tylko z nowymi dowodami" for x in tr["rejected_again"]]
    if tr.get("assessed"):
        out.append(f"- już ocenione w poprzedniej retrospektywie (to samo zdarzenie): {', '.join(f'`{k}`' for k in tr['assessed'])}")
    if not (tr["recurring"] or tr["measured"] or tr["rejected_again"] or tr.get("assessed")):
        out.append("- brak (pierwsza retrospektywa albo nic się nie powtarza)")
    out += ["", "## Propozycje z danych (do oceny, nie decyzje)"]
    out += [f"- `{x['key']}` → {x['place']}: {x['text']}" for x in d["suggestions"]] or ["- brak sygnałów ponad progi"]
    if d["lessons"]:
        out += ["", "## Istniejące lekcje (powtórka → propozycja do CLAUDE.md)"] + [f"- {x}" for x in d["lessons"]]
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    opts, decide, it = {}, [], iter(argv[1:])
    for a in it:
        if a in ("--root", "--since", "--until", "--days"):
            opts[a] = next(it, "")
        elif a == "--decide":
            decide.append(next(it, ""))
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            opts[a] = True
    root = Path(opts.get("--root") or os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    try:
        until = dt.date.fromisoformat(opts["--until"]) if opts.get("--until") else dt.date.today()
        since = dt.date.fromisoformat(opts["--since"]) if opts.get("--since") else \
            until - dt.timedelta(days=int(opts.get("--days") or 14))
    except ValueError as e:
        print(f"✗ Zła data lub liczba dni: {e}")
        return 2
    path = root / RETRO_DIR / f"{until.strftime('%Y%m%d')}-retro.json"
    if decide:
        pairs = [x.rpartition("=") for x in decide]
        bad = [x for x, (k, _, v) in zip(decide, pairs) if not k or v not in DECISIONS]
        if bad:
            print(f"✗ Decyzja ma postać KLUCZ=tak|nie|później: {', '.join(bad)}")
            return 2
        if not path.is_file():
            print(f"✗ Brak {path.relative_to(root)} — najpierw --save.")
            return 2
        saved = json.loads(path.read_text(encoding="utf-8"))
        saved.setdefault("decisions", {}).update({k: v for k, _, v in pairs})
        path.write_text(json.dumps(saved, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"✓ Decyzje zapisane w {path.relative_to(root)}: " + ", ".join(f"{k}={v}" for k, _, v in pairs))
        return 0
    data = collect(root, since, until)
    if opts.get("--save"):
        old = {}
        if path.is_file():
            try:
                old = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                old = {}
        snap = {"date": until.isoformat(), "window": data["window"], "evidence": data["evidence"],
                "suggestions": data["suggestions"], "decisions": old.get("decisions", {})}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(snap, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"✓ Zapisano {path.relative_to(root)} (dowodów: {len(data['evidence'])}, decyzji: {len(snap['decisions'])}). "
              "Decyzje człowieka: --decide KLUCZ=tak|nie|później")
        return 0
    print(json.dumps(data, ensure_ascii=False, indent=1) if opts.get("--json") else render(data), end="" if not
          opts.get("--json") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
