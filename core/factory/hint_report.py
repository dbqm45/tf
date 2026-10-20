#!/usr/bin/env python3
"""
Raport skuteczności podpowiedzi skilli (hook skill_hint) na prawdziwej pracy w projekcie.

  python3 factory/hint_report.py               # wszystkie sesje z logów
  python3 factory/hint_report.py --days 7      # ostatnie 7 dni

Łączy dwa logi z .claude/logs/:
- skill-hints.jsonl (hook skill_hint): co podpowiedziano przy każdym poleceniu,
- usage.jsonl (hook log_usage): jakie skille sesja faktycznie wczytała (wątek główny i wykonawcy).

Wynik per skill:
- trafione: podpowiedziany i użyty w tej samej sesji,
- zignorowane: podpowiedziany, a w sesji nieużyty (szum albo model uznał, że niepotrzebny),
- przeoczone: użyty, a w sesji ani razu niepodpowiedziany (kandydat na `metadata.slowa` w SKILL.md).
Porównanie jest na poziomie sesji, nie pojedynczego polecenia — to przybliżenie. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / ".claude" / "logs"


def read_jsonl(path: Path, since: datetime | None) -> list[dict]:
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if since and r.get("ts"):
            try:
                if datetime.fromisoformat(r["ts"]) < since:
                    continue
            except ValueError:
                pass
        out.append(r)
    return out


def analyse(hints: list[dict], usage: list[dict]) -> dict:
    hinted: dict[str, set] = defaultdict(set)
    prompts: Counter = Counter()
    with_hint: Counter = Counter()
    for h in hints:
        s = h.get("session") or "?"
        prompts[s] += 1
        if h.get("hinted"):
            with_hint[s] += 1
        hinted[s].update(h.get("hinted") or [])
    used: dict[str, set] = defaultdict(set)
    for u in usage:
        used[u.get("session") or "?"].update(u.get("skills") or [])
    sessions = set(prompts) & set(used) if used else set(prompts)
    hit, ignored, missed = Counter(), Counter(), Counter()
    for s in sessions:
        for sk in hinted[s] & used[s]:
            hit[sk] += 1
        for sk in hinted[s] - used[s]:
            ignored[sk] += 1
        for sk in used[s] - hinted[s]:
            missed[sk] += 1
    return {"sessions": len(sessions), "prompts": sum(prompts[s] for s in sessions),
            "prompts_with_hint": sum(with_hint[s] for s in sessions), "hit": hit, "ignored": ignored, "missed": missed}


def render(r: dict) -> str:
    lines = [f"Sesje: {r['sessions']} · polecenia: {r['prompts']} · z podpowiedzią: {r['prompts_with_hint']}"]
    if not r["sessions"]:
        lines.append("Brak danych: potrzebne logi .claude/logs/skill-hints.jsonl i usage.jsonl z tych samych sesji.")
        return "\n".join(lines)
    total_hit, total_ign, total_miss = sum(r["hit"].values()), sum(r["ignored"].values()), sum(r["missed"].values())
    lines.append(f"Podpowiedzi trafione: {total_hit} · zignorowane: {total_ign} · skille użyte bez podpowiedzi: {total_miss}")
    names = sorted(set(r["hit"]) | set(r["ignored"]) | set(r["missed"]),
                   key=lambda n: -(r["missed"][n] + r["ignored"][n]))
    lines += ["", f"{'skill':<36} {'trafione':>8} {'zignor.':>8} {'przeocz.':>8}"]
    lines += [f"{n:<36} {r['hit'][n]:>8} {r['ignored'][n]:>8} {r['missed'][n]:>8}" for n in names]
    tips = []
    for n in names:
        if r["missed"][n] >= 2:
            tips.append(f"- {n}: używany bez podpowiedzi w {r['missed'][n]} sesjach — dopisz słowa użytkowników do "
                        f"metadata.slowa (z CLAUDE_SKILL_HINT_LOG_PROMPT=1 zobaczysz brzmienie poleceń)")
        if r["ignored"][n] >= 3 and r["hit"][n] == 0:
            tips.append(f"- {n}: podpowiadany {r['ignored'][n]}× i ani razu nie użyty — sprawdź, czy opis nie łapie "
                        f"cudzych słów (python3 .claude/hooks/skill_hint.py --explain \"<polecenie>\")")
    if tips:
        lines += ["", "Co poprawić:"] + tips
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=0)
    ap.add_argument("--logs", default=str(LOGS))
    a = ap.parse_args(argv[1:])
    since = datetime.now(timezone.utc) - timedelta(days=a.days) if a.days else None
    logs = Path(a.logs)
    r = analyse(read_jsonl(logs / "skill-hints.jsonl", since), read_jsonl(logs / "usage.jsonl", since))
    print(render(r))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
