#!/usr/bin/env python3
"""
Zgłoszenie do repozytorium fabryki z zapisanej retrospektywy (skill core-agent-retro) — tylko biblioteka standardowa.

  python3 .claude/skills/core-agent-retro/scripts/factory_feedback.py              # link „nowe zgłoszenie” z treścią
  ... --item "skill:fe-css: brak przykładu siatki formularza"                    # własna uwaga o skillu/agencie fabryki
  ... --gh                                                                       # plan wysyłki przez gh (nic nie wysyła)
  ... --gh --yes                                                                 # wyślij przez `gh issue create`
  ... --mark-sent                                                                # po wysłaniu z linku: zapamiętaj klucze
  --date RRRR-MM-DD (retrospektywa; domyślnie najnowsza) · --repo właściciel/repo · --force (także już zgłoszone)
  --json (tytuł, treść, link i blok danych) · --root <katalog projektu>

Co trafia do zgłoszenia: wyłącznie sygnały o skillach i agentach FABRYKI z pliku retrospektywy
(`hint-missed:<skill>`, `hint-ignored:<skill>`, `tier:<agent>:<sygnał>`) z liczbami, decyzją projektu (bez odrzuconych),
wersją fabryki i anonimowym identyfikatorem projektu. Pułapki, dziennik, koszty, ścieżki i nazwy projektu — nigdy.
Własne uwagi (`--item`) są sprawdzane: ścieżka, adres, e-mail albo cel spoza fabryki → odmowa (kod 2).
Repozytorium: `--repo`, inaczej `source` z manifestu (adres GitHub). Wysyłka przez gh tylko z `--yes`.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

RETRO_DIR = Path("docs") / "project" / "archive" / "retro"
SIGNAL = re.compile(r"^(hint-missed|hint-ignored):([a-z0-9][a-z0-9-]*)$|^tier:([a-z0-9][a-z0-9-]*):(za niski|za wysoki)$")
GITHUB = re.compile(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?(?:#.*)?$")
LEAK = [(re.compile(r"(?:^|\s)(?:~|[A-Za-z]:\\|\.{0,2}/)[\w.-]+[/\\]"), "ścieżka"),
        (re.compile(r"https?://|www\.", re.I), "adres"), (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "e-mail")]
URL_MAX = 7000


def factory_names(root: Path, manifest: dict) -> tuple[set, set]:
    files = manifest.get("files") or {}
    if files:
        skills = {m.group(1) for f in files if (m := re.match(r"\.claude/skills/([^/]+)/SKILL\.md$", f))}
        agents = {m.group(1) for f in files if (m := re.match(r"\.claude/agents/_generated/([^/]+)\.md$", f))}
        return skills, agents
    return ({p.parent.name for p in (root / ".claude" / "skills").glob("*/SKILL.md")},     # repozytorium fabryki
            {p.stem for p in (root / ".claude" / "agents" / "_generated").glob("*.md")})


def retro_file(root: Path, date: str | None) -> Path | None:
    if date:
        p = root / RETRO_DIR / f"{date.replace('-', '')}-retro.json"
        return p if p.is_file() else None
    files = sorted((root / RETRO_DIR).glob("*-retro.json"))
    return files[-1] if files else None


def signals(retro: dict, skills: set, agents: set, force: bool) -> list[dict]:
    dec, sent = retro.get("decisions") or {}, retro.get("reported") or {}
    out = []
    for e in retro.get("evidence", []):
        k = e.get("key", "")
        m = SIGNAL.match(k)
        if not m or dec.get(k) == "nie" or (k in sent and not force):
            continue
        if (m.group(2) and m.group(2) not in skills) or (m.group(3) and m.group(3) not in agents):
            continue
        out.append({"key": k, "n": int(e.get("n") or 1), "decision": dec.get(k, "—")})
    return out


def check_item(raw: str, skills: set, agents: set) -> tuple[dict | None, str]:
    m = re.match(r"^(skill|agent):([a-z0-9][a-z0-9-]*):\s*(.+)$", raw.strip(), re.S)
    if not m:
        return None, "postać: skill:<nazwa>: <uwaga> albo agent:<nazwa>: <uwaga>"
    kind, name, text = m.groups()
    if name not in (skills if kind == "skill" else agents):
        return None, f"{kind} {name} nie pochodzi z fabryki"
    if len(text) > 300:
        return None, "uwaga dłuższa niż 300 znaków"
    for rx, what in LEAK:
        if rx.search(text):
            return None, f"uwaga zawiera {what} — usuń dane projektu"
    return {"target": f"{kind}:{name}", "text": text.strip()}, ""


HINT = {"hint-missed": "dopisać słowa do metadata.slowa", "hint-ignored": "zawęzić słowa lub opis",
        "tier": "zmienić tier roli lub podział zadań"}


def compose(payload: dict) -> tuple[str, str]:
    sig, items = payload["signals"], payload["items"]
    title = f"Sygnały z retrospektywy projektu (fabryka {payload['factory_version']}): " + \
            ", ".join(s["key"].split(":")[1] for s in sig[:3]) + (" …" if len(sig) > 3 else "") if sig else \
            f"Uwagi z retrospektywy projektu (fabryka {payload['factory_version']})"
    lines = ["Zgłoszenie z retrospektywy pracy agentów (core-agent-retro). Zawiera tylko nazwy skilli i agentów fabryki "
             "oraz liczby — bez danych projektu. To sygnał z jednego projektu: sprawdź go na innych zgłoszeniach "
             "(`python3 factory/feedback_report.py`) i scenariuszach ewaluacji przed zmianą.", ""]
    if sig:
        lines += ["| Klucz | Ile | Decyzja w projekcie | Co sugeruje |", "|---|---|---|---|"]
        lines += [f"| `{s['key']}` | {s['n']} | {s['decision']} | {HINT[s['key'].split(':')[0]]} |" for s in sig]
    if items:
        lines += ["", "Uwagi:"] + [f"- `{i['target']}`: {i['text']}" for i in items]
    w = payload.get("window") or {}
    lines += ["", f"Wersja fabryki: {payload['factory_version']} · okno: {w.get('since', '?')} – {w.get('until', '?')} · "
                  f"projekt (anonimowo): {payload['project']}", "",
              "```json", json.dumps(payload, ensure_ascii=False), "```", "<!-- factory-feedback -->"]
    return title, "\n".join(lines) + "\n"


def link(repo: str, title: str, body: str) -> str:
    url = f"https://github.com/{repo}/issues/new?" + urllib.parse.urlencode({"title": title, "body": body})
    if len(url) > URL_MAX:   # przeglądarki i GitHub tną długie adresy — zostaje sam blok danych
        short = body.split("```json", 1)[1]
        url = f"https://github.com/{repo}/issues/new?" + urllib.parse.urlencode({"title": title, "body": "```json" + short})
    return url


def main(argv: list[str]) -> int:
    opts, items_raw, it = {}, [], iter(argv[1:])
    for a in it:
        if a in ("--root", "--date", "--repo"):
            opts[a] = next(it, "")
        elif a == "--item":
            items_raw.append(next(it, ""))
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            opts[a] = True
    root = Path(opts.get("--root") or os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    man_p = root / ".claude" / "factory-manifest.json"
    manifest = json.loads(man_p.read_text(encoding="utf-8")) if man_p.is_file() else {}
    version = manifest.get("version") or ((root / "factory" / "VERSION").read_text(encoding="utf-8").strip()
                                          if (root / "factory" / "VERSION").is_file() else "?")
    repo = opts.get("--repo") or ""
    if not repo:
        m = GITHUB.search(str(manifest.get("source") or os.environ.get("CLAUDE_TEAM_FACTORY") or ""))
        repo = f"{m.group(1)}/{m.group(2)}" if m else ""
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        print("✗ Nie znam repozytorium fabryki na GitHubie (źródło w manifeście nie jest adresem GitHub). "
              "Podaj --repo właściciel/repo.")
        return 2
    skills, agents = factory_names(root, manifest)
    items = []
    for raw in items_raw:
        item, err = check_item(raw, skills, agents)
        if not item:
            print(f"✗ --item „{raw[:60]}”: {err}")
            return 2
        items.append(item)
    rf = retro_file(root, opts.get("--date"))
    retro = json.loads(rf.read_text(encoding="utf-8")) if rf else {}
    if not rf and not items:
        print("✗ Brak zapisanej retrospektywy — najpierw retro_data.py --save (albo podaj --item).")
        return 2
    sig = signals(retro, skills, agents, bool(opts.get("--force")))
    if not sig and not items:
        print("✓ Brak: nic nowego do zgłoszenia fabryce (sygnały już zgłoszone, odrzucone albo spoza fabryki; --force zgłosi ponownie).")
        return 0
    payload = {"factory_feedback": 1, "project": hashlib.sha256(str(root).encode()).hexdigest()[:10],
               "factory_version": version, "window": retro.get("window") or {}, "signals": sig, "items": items}
    title, body = compose(payload)
    url = link(repo, title, body)

    def remember(where: str) -> None:
        if rf:
            retro.setdefault("reported", {}).update({s["key"]: where for s in sig})
            rf.write_text(json.dumps(retro, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    if opts.get("--json"):
        print(json.dumps({"repo": repo, "title": title, "body": body, "url": url, "payload": payload}, ensure_ascii=False))
        return 0
    if opts.get("--mark-sent"):
        remember("link")
        print(f"✓ Zapamiętano jako zgłoszone: {', '.join(s['key'] for s in sig) or '—'}")
        return 0
    print(f"Tytuł: {title}\n\n{body}")
    if opts.get("--gh"):
        gh = os.environ.get("CTF_GH") or shutil.which("gh") or ""
        cmd = [gh or "gh", "issue", "create", "--repo", repo, "--title", title, "--body-file", "-"]
        if not opts.get("--yes"):
            print(f"Plan: gh issue create --repo {repo} --title \"{title}\" --body-file - (treść wyżej).\n"
                  "Wyślij: dodaj --yes. Albo otwórz link i wyślij sam:\n" + url)
            return 0
        if not gh or not os.access(gh, os.X_OK):
            print(f"✗ Brak gh — otwórz link i wyślij zgłoszenie sam (potem --mark-sent):\n{url}")
            return 1
        r = subprocess.run(cmd, input=body, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print(f"✗ gh zwrócił błąd: {r.stderr.strip()[:300]}\nOtwórz link i wyślij sam (potem --mark-sent):\n{url}")
            return 1
        created = (r.stdout.strip().splitlines() or ["gh"])[-1]
        remember(created)
        print(f"✓ Zgłoszenie założone: {created}")
        return 0
    print(f"Otwórz, sprawdź treść i wyślij (potem --mark-sent, żeby nie zgłaszać drugi raz):\n{url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
