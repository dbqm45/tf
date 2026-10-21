#!/usr/bin/env python3
"""
Przebieg Talosa („story → PR”, skill core-story-run): katalog przebiegu i raport kosztu.

  python3 factory/run_report.py start "<tytuł>" [--story "<treść>" | --story-file PLIK]
  python3 factory/run_report.py status <katalog-przebiegu> [--session ID]   # jedna linia: koszt, czas, plan
  python3 factory/run_report.py finish <katalog-przebiegu> [--session ID] [--json]

`start` zakłada `.claude/runs/<RRRR-MM-DD>-<slug>/` (ignorowany przez git): run.json (czas startu), story.md,
plan.md, parked.md. `finish` sumuje zużycie z transkryptów Claude Code — sesji i jej podagentów — od czasu startu:
czas, tokeny (wejście, wyjście, odczyt cache, zapis cache 5 min i 1 h), koszt wg `prices_usd_per_mtok`
z factory/config.yaml, modele i agenci; dopisuje postęp planu i liczbę odłożonych spraw, zapisuje report.md.

Liczy skrypt, nie model — raport nie zużywa tokenów poza wklejeniem kilkunastu linii wyniku. Transkrypty:
`$CLAUDE_CONFIG_DIR/projects/<ścieżka projektu>/` (domyślnie `~/.claude`); bez `--session` liczą się wszystkie sesje
projektu z wpisami po starcie (także równoległe — wtedy podaj `--session`). Koszt jest szacunkiem z cennika API
(przy subskrypcji to równowartość, nie faktura); zapis cache 1 h liczony jako 2× cena wejścia (platform.claude.com,
„Prompt caching”). Typ agenta podagenta pochodzi z pliku `*.meta.json` obok transkryptu, jeśli Claude Code go zapisał.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # dołączona kopia PyYAML (factory/_vendor)
    sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
    import yaml

ROOT = Path(__file__).resolve().parent.parent
RUNS = Path(".claude") / "runs"
KEYS = ("input", "output", "cache_read", "cache_write_5m", "cache_write_1h")
FAMILIES = ("haiku", "sonnet", "opus", "fable", "mythos")

PLAN_TEMPLATE = """# Plan: {title}

Kawałki pionowe: każdy niesie wartość, przechodzi testy i jest osobnym commitem (skill core-story-run).

- [ ] K1 — <wartość dla użytkownika> · kryteria: <testy> · pliki: <ścieżki> · weryfikacja: `<polecenie>`
"""
PARKED_TEMPLATE = """# Odłożone do decyzji: {title}

Przypadki brzegowe, pomysły i ryzyka spoza kryteriów akceptacji — nie trafiają do kodu w tym przebiegu.
Format: `- <co> — <gdzie: plik:linia> — <skutek> — <propozycja> — do decyzji`
"""


def slugify(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.lower().replace("ł", "l"))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60] or "przebieg"


def parse_ts(value: str) -> datetime | None:
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def family(model: str) -> str:
    return next((f for f in FAMILIES if f in model.lower()), model)


def projects_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "projects"


def transcript_dir(project: Path) -> Path:
    """Katalog transkryptów projektu: ścieżka z każdym znakiem spoza [A-Za-z0-9] zamienionym na „-”."""
    return projects_dir() / re.sub(r"[^A-Za-z0-9]", "-", str(project.resolve()))


def usage_entries(path: Path, since: datetime) -> dict[str, tuple[datetime, str, dict]]:
    """Odpowiedzi modelu po `since`: ta sama odpowiedź (message.id) bywa zapisana kilka razy podczas streamingu —
    zostaje zapis z największym `output_tokens`."""
    out: dict[str, tuple[datetime, str, dict]] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = e.get("message") if isinstance(e, dict) else None
        if e.get("type") != "assistant" or not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
            continue
        ts = parse_ts(e.get("timestamp", ""))
        if ts is None or ts < since:
            continue
        mid = msg.get("id") or e.get("uuid") or f"{path}:{len(out)}"
        prev = out.get(mid)
        if prev is None or (msg["usage"].get("output_tokens") or 0) >= (prev[2].get("output_tokens") or 0):
            out[mid] = (ts, msg.get("model") or "unknown", msg["usage"])
    return out


def split_usage(u: dict) -> dict[str, int]:
    cc = u.get("cache_creation") or {}
    w1 = cc.get("ephemeral_1h_input_tokens") or 0
    w5 = cc.get("ephemeral_5m_input_tokens")
    if w5 is None:                         # starszy zapis bez podziału: cały zapis jako 5 min
        w5 = max((u.get("cache_creation_input_tokens") or 0) - w1, 0)
    return {"input": u.get("input_tokens") or 0, "output": u.get("output_tokens") or 0,
            "cache_read": u.get("cache_read_input_tokens") or 0, "cache_write_5m": w5, "cache_write_1h": w1}


def cost(tokens: dict, price: dict | None) -> float | None:
    if not price:
        return None
    return (tokens["input"] * price.get("input", 0) + tokens["output"] * price.get("output", 0)
            + tokens["cache_read"] * price.get("cache_read", 0)
            + tokens["cache_write_5m"] * price.get("cache_write", 0)
            + tokens["cache_write_1h"] * 2 * price.get("input", 0)) / 1e6


def prices() -> dict:
    try:
        cfg = yaml.safe_load((ROOT / "factory" / "config.yaml").read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
    return cfg.get("prices_usd_per_mtok") or {}


def collect(project: Path, since: datetime, session: str | None) -> dict:
    tdir = transcript_dir(project)
    mains = [tdir / f"{session}.jsonl"] if session else sorted(tdir.glob("*.jsonl"))
    files: list[tuple[str, Path]] = []
    for m in mains:
        if not m.is_file():
            continue
        files.append(("main", m))
        for sub in sorted((m.with_suffix("") / "subagents").glob("agent-*.jsonl")):
            try:
                agent = json.loads(sub.with_suffix(".meta.json").read_text(encoding="utf-8")).get("agentType")
            except (OSError, ValueError, AttributeError):
                agent = None
            files.append((agent or "subagent", sub))
    table = prices()
    models: dict[str, dict] = {}
    agents: dict[str, dict] = {}
    model_ids: set[str] = set()
    last = since
    requests = 0
    for agent, path in files:
        for ts, model, usage in usage_entries(path, since).values():
            requests += 1
            last = max(last, ts)
            model_ids.add(model)
            tok = split_usage(usage)
            fam = family(model)
            for bucket in (models.setdefault(fam, dict.fromkeys(KEYS, 0)), agents.setdefault(agent, dict.fromkeys(KEYS, 0))):
                for k in KEYS:
                    bucket[k] += tok[k]
            agents[agent].setdefault("_cost", 0.0)
            c = cost(tok, table.get(model) or table.get(fam))
            if c is not None:
                agents[agent]["_cost"] += c
                models[fam]["_cost"] = models[fam].get("_cost", 0.0) + c
            else:
                models[fam]["_unpriced"] = True
    return {"files": len(files), "requests": requests, "last": last, "models": models, "agents": agents,
            "model_ids": sorted(model_ids)}


def plan_progress(run_dir: Path) -> dict:
    text = (run_dir / "plan.md").read_text(encoding="utf-8") if (run_dir / "plan.md").exists() else ""
    done = len(re.findall(r"^\s*- \[[xX]\]", text, re.M))
    return {"done": done, "total": done + len(re.findall(r"^\s*- \[ \]", text, re.M))}


def parked_count(run_dir: Path) -> int:
    text = (run_dir / "parked.md").read_text(encoding="utf-8") if (run_dir / "parked.md").exists() else ""
    return len([ln for ln in text.splitlines() if ln.startswith("- ") and not ln.startswith("- <")])


def fmt_tokens(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def report_md(slug: str, rep: dict) -> str:
    mins, secs = divmod(rep["duration_s"], 60)
    lines = [f"# Raport przebiegu: {slug}", "",
             f"- Czas: {int(mins)} min {int(secs)} s (od startu do ostatniej odpowiedzi modelu)",
             f"- Koszt: {rep['cost_usd']:.4f} USD (szacunek z cennika API; przy subskrypcji — równowartość)",
             f"- Zapytania do modelu: {rep['requests']} · modele: {', '.join(rep['model_ids']) or '—'}",
             f"- Plan: {rep['plan']['done']}/{rep['plan']['total']} kawałków · odłożone do decyzji: {rep['parked']}", "",
             "| Model | Wejście | Wyjście | Odczyt cache | Zapis cache 5 min | Zapis cache 1 h | Koszt USD |",
             "|---|---|---|---|---|---|---|"]
    for fam, t in sorted(rep["models"].items()):
        c = "brak ceny" if t.get("_unpriced") else f"{t.get('_cost', 0):.4f}"
        lines.append(f"| {fam} | " + " | ".join(fmt_tokens(t[k]) for k in KEYS) + f" | {c} |")
    lines += ["", "| Agent | Wejście | Wyjście | Odczyt cache | Koszt USD |", "|---|---|---|---|---|"]
    for agent, t in sorted(rep["agents"].items(), key=lambda kv: -kv[1].get("_cost", 0)):
        lines.append(f"| {agent} | {fmt_tokens(t['input'])} | {fmt_tokens(t['output'])} | {fmt_tokens(t['cache_read'])} | "
                     f"{t.get('_cost', 0):.4f} |")
    return "\n".join(lines) + "\n"


def cmd_start(title: str, story: str | None, project: Path) -> int:
    slug = slugify(title)
    now = datetime.now(timezone.utc)
    run_dir = project / RUNS / f"{now:%Y-%m-%d}-{slug}"
    if run_dir.exists():
        print(f"✗ Przebieg już istnieje: {run_dir} — dokończ go albo nadaj inny tytuł.")
        return 2
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text(json.dumps({"slug": slug, "title": title,
                                                  "started_at": now.isoformat(timespec="seconds")},
                                                 ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (run_dir / "story.md").write_text(f"# {title}\n\n{(story or '').strip()}\n", encoding="utf-8")
    (run_dir / "plan.md").write_text(PLAN_TEMPLATE.format(title=title), encoding="utf-8")
    (run_dir / "parked.md").write_text(PARKED_TEMPLATE.format(title=title), encoding="utf-8")
    print(run_dir.relative_to(project) if run_dir.is_relative_to(project) else run_dir)
    return 0


def cmd_finish(run_dir: Path, session: str | None, as_json: bool, project: Path, status: bool = False) -> int:
    try:
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        since = parse_ts(meta["started_at"])
    except (OSError, ValueError, KeyError):
        print(f"✗ Brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
        return 2
    data = collect(project, since, session)
    if not data["requests"]:
        print(f"✗ Brak odpowiedzi modelu po {since:%Y-%m-%d %H:%M} w transkryptach {transcript_dir(project)} "
              "(inny CLAUDE_CONFIG_DIR? podaj --session).")
        return 2
    rep = {"slug": meta.get("slug"), "duration_s": int((data["last"] - since).total_seconds()),
           "requests": data["requests"], "model_ids": data["model_ids"], "models": data["models"],
           "agents": data["agents"],
           "cost_usd": round(sum(t.get("_cost", 0.0) for t in data["models"].values()), 9),
           "plan": plan_progress(run_dir), "parked": parked_count(run_dir)}
    if status:   # kontrola budżetu po kawałku: jedna linia, bez zapisu raportu
        print(f"koszt: {rep['cost_usd']:.4f} USD · czas: {rep['duration_s'] // 60} min · plan: "
              f"{rep['plan']['done']}/{rep['plan']['total']} · odłożone: {rep['parked']}")
        return 0
    md = report_md(meta.get("slug") or run_dir.name, rep)
    (run_dir / "report.md").write_text(md, encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, default=str) if as_json else md, end="" if not as_json else "\n")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("title")
    s.add_argument("--story", default=None)
    s.add_argument("--story-file", default=None)
    for name in ("status", "finish"):
        f = sub.add_parser(name)
        f.add_argument("run_dir")
        f.add_argument("--session", default=None)
        f.add_argument("--json", action="store_true")
    args = ap.parse_args(argv[1:])
    project = Path.cwd()
    if args.cmd == "start":
        story = Path(args.story_file).read_text(encoding="utf-8") if args.story_file else args.story
        return cmd_start(args.title, story, project)
    return cmd_finish(Path(args.run_dir), args.session, args.json, project, status=args.cmd == "status")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
