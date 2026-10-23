#!/usr/bin/env python3
"""
Dziennik zmiany zgodny z kontraktem pdi 0.3.0 (contract/change.schema.json) — tryb mode-pdi.

  python3 .claude/skills/pdi-decisions/scripts/decision_record.py change new CHG-12 [--source PRB-34] [--author NAME]
      tworzy docs/project/changes/CHG-12/ z intent.md, plan.md i decisions.md (szablony obok skryptu)
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py check
      sprawdza nagłówki artefaktów i wpisy decyzji w docs/project/changes/*/
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py decision add CHG-12 --statement "…" --why "…" \
      --kind product --by "kto" [--date RRRR-MM-DD] [--source-kind claude-cli] [--drafted-by ai]
      dopisuje zatwierdzoną decyzję do decisions.md (ref CHG-12/Dn, id puste, wyslano: nie)
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py decision pending [--change CHG-12]
      JSON niewysłanych decyzji z gotowymi argumentami record_decision (MCP pdi)
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py decision mark CHG-12/D1 --id DEC-41
      wpisuje numer nadany przez rejestr pdi i wyslano: tak
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py decision export
      JSON wszystkich decyzji projektu (z numerem i stanem wysłania)

Kod wyjścia: 0 — w porządku, 1 — błędy (z podpowiedzią), 2 — złe wywołanie.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

KEY = re.compile(r"^[A-Z][A-Z0-9]+-[0-9]+$")
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
ARTIFACTS = ("intent", "requirements", "design", "plan", "decisions", "run")
PHASES = ("discovery", "domain", "requirements", "architecture", "plan", "delivery", "review")
STATUSES = ("draft", "proposed", "accepted", "superseded", "rejected")
KEYS = ("artifact", "phase", "status", "version", "author", "created", "updated", "inputs", "change", "source", "tasks",
        "superseded_by")
REQUIRED = ("artifact", "phase", "status", "version", "created", "updated", "change")
KINDS = ("product", "technical", "process", "triage", "intent", "gate", "other")
SOURCE_KINDS = ("claude-cli", "claude-ai", "slack", "confluence", "jira", "manual")
ENTRY = ("ref", "id", "wyslano", "kiedy", "kto", "rodzaj", "dlaczego", "zrodlo", "szkic")   # pola wpisu w decisions.md
NEW = {"intent": "discovery", "plan": "plan", "decisions": "plan"}   # artefakty `change new` i ich faza
CHANGES = Path("docs") / "project" / "changes"
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def parse_header(text: str) -> dict | None:
    """Nagłówek YAML w prostej postaci z kontraktu: `klucz: wartość`, listy `[a, b]` albo `- a` w kolejnych wierszach."""
    if not text.startswith("---\n") or "\n---" not in text[4:]:
        return None
    out, last = {}, None
    for line in text[4:].split("\n---", 1)[0].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.lstrip().startswith("- ") and last:
            out[last] = (out[last] if isinstance(out[last], list) else []) + [line.lstrip()[2:].strip()]
            continue
        k, sep, v = line.partition(":")
        if not sep:
            continue
        v = re.sub(r"\s+#.*$", "", v).strip().strip("'\"")
        last = k.strip()
        out[last] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()] if v.startswith("[") else v
    return out


def render(fields: dict) -> str:
    lines = []
    for k in KEYS:
        if k in fields:
            v = fields[k]
            lines.append(f"{k}: [{', '.join(v)}]" if isinstance(v, list) else f"{k}: {v}")
    return "---\n" + "\n".join(lines) + "\n---\n"


def new_change(key: str, source: str | None, author: str) -> int:
    bad = [f"{name} '{v}'" for name, v in (("klucz zmiany", key), ("klucz zgłoszenia", source)) if v and not KEY.match(v)]
    if bad:
        print(f"✗ zły kształt: {', '.join(bad)} — wzorzec [A-Z][A-Z0-9]+-[0-9]+, np. CHG-12, PRB-34")
        return 1
    target = CHANGES / key
    if target.exists():
        print(f"✗ {target} już istnieje — nie nadpisuję; zmień istniejące pliki albo użyj innego klucza")
        return 1
    today = dt.date.today().isoformat()
    target.mkdir(parents=True)
    for artifact, phase in NEW.items():
        fields = {"artifact": artifact, "phase": phase, "status": "draft", "version": "1", "author": author,
                  "created": today, "updated": today, "inputs": [], "change": key}
        if source:
            fields["source"] = source
        if artifact == "plan":
            fields["tasks"] = []
        body = (TEMPLATES / f"{artifact}.md").read_text(encoding="utf-8").replace("{CHG}", key)
        (target / f"{artifact}.md").write_text(render(fields) + body, encoding="utf-8")
    print(f"✓ {target}/: intent.md, plan.md, decisions.md (status draft)")
    return 0


def check_file(path: Path) -> list[str]:
    h = parse_header(path.read_text(encoding="utf-8"))
    if h is None:
        return ["brak nagłówka YAML (--- … ---) na początku pliku"]
    errs = [f"brak pola {k}" for k in REQUIRED if not h.get(k)]
    errs += [f"nieznane pole {k} (kontrakt pdi 0.3.0 dopuszcza: {', '.join(KEYS)})" for k in h if k not in KEYS]
    for k, allowed in (("artifact", ARTIFACTS), ("phase", PHASES), ("status", STATUSES)):
        if h.get(k) and h[k] not in allowed:
            errs.append(f"{k}: '{h[k]}' spoza {', '.join(allowed)}")
    if h.get("version") and not (str(h["version"]).isdigit() and int(h["version"]) >= 1):
        errs.append(f"version: '{h['version']}' — liczba całkowita ≥ 1")
    for k in ("created", "updated"):
        if h.get(k) and not DATE.match(str(h[k])):
            errs.append(f"{k}: '{h[k]}' — data RRRR-MM-DD")
    for k in ("change", "source"):
        if h.get(k) and not KEY.match(str(h[k])):
            errs.append(f"{k}: '{h[k]}' — klucz [A-Z][A-Z0-9]+-[0-9]+, np. CHG-12")
    if h.get("change") and KEY.match(str(h["change"])) and h["change"] != path.parent.name:
        errs.append(f"change: '{h['change']}' różny od katalogu {path.parent.name}")
    if "tasks" in h:
        if h.get("artifact") != "plan":
            errs.append("tasks tylko w plan.md (artifact: plan)")
        tasks = h["tasks"] if isinstance(h["tasks"], list) else [h["tasks"]] if h["tasks"] else []
        errs += [f"tasks: '{t}' — klucz cięcia, np. TSK-57" for t in tasks if not KEY.match(t)]
    for k in ("inputs",):
        if k in h and not isinstance(h[k], list) and h[k]:
            errs.append(f"{k}: lista ścieżek, np. [docs/project/changes/CHG-12/intent.md]")
    return errs


def parse_entries(path: Path) -> list[dict]:
    """Wpisy decyzji: nagłówek `## <co>` i lista `- pole: wartość`; wzór wpisu w komentarzu szablonu jest pomijany."""
    text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
    out, cur = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = {"statement": line[3:].strip()}
            out.append(cur)
        elif cur is not None and line.startswith("- ") and ":" in line:
            k, _, v = line[2:].partition(":")
            if k.strip() in ENTRY:
                cur[k.strip()] = v.strip()
    return [e for e in out if "ref" in e]


def decisions_file(key: str) -> Path | None:
    f = CHANGES / key / "decisions.md"
    return f if f.is_file() else None


def as_record(e: dict, change_header: dict) -> dict:
    """Argumenty record_decision (kontrakt pdi 0.3.0, decision.schema.json) z wpisu w decisions.md."""
    chg = e["ref"].split("/")[0]
    links = {"chg": chg}
    if change_header.get("source"):
        links["prb"] = change_header["source"]
    return {"statement": e["statement"], "why": e.get("dlaczego", ""), "kind": e.get("rodzaj", ""),
            "source": {"kind": e.get("zrodlo", "")}, "drafted_by": e.get("szkic", ""),
            "decided_by": e.get("kto", ""), "decided_at": e.get("kiedy", ""), "links": links}


def all_entries(change: str | None = None) -> list[tuple[dict, dict]]:
    files = sorted(CHANGES.glob(f"{change or '*'}/decisions.md")) if CHANGES.is_dir() else []
    return [(e, parse_header(f.read_text(encoding="utf-8")) or {}) for f in files for e in parse_entries(f)]


def decision_add(a) -> int:
    f = decisions_file(a.key) if KEY.match(a.key) else None
    if f is None:
        print(f"✗ brak {CHANGES / a.key / 'decisions.md'} — najpierw: decision_record.py change new {a.key}")
        return 1
    errs = [f"--kind '{a.kind}' spoza {', '.join(KINDS)}" for _ in [0] if a.kind not in KINDS]
    errs += [f"--source-kind '{a.source_kind}' spoza {', '.join(SOURCE_KINDS)}" for _ in [0]
             if a.source_kind not in SOURCE_KINDS]
    errs += [f"--date '{a.date}' — RRRR-MM-DD" for _ in [0] if a.date and not DATE.match(a.date)]
    errs += [f"--{n} puste" for n, v in (("statement", a.statement), ("why", a.why), ("by", a.by)) if not v.strip()]
    if errs:
        print("✗ " + "; ".join(errs))
        return 1
    n = 1 + max([int(e["ref"].rsplit("D", 1)[1]) for e in parse_entries(f) if re.search(r"/D\d+$", e["ref"])] or [0])
    ref = f"{a.key}/D{n}"
    entry = (f"\n## {a.statement.strip()}\n- ref: {ref}\n- id:\n- wyslano: nie\n- kiedy: {a.date or dt.date.today().isoformat()}\n"
             f"- kto: {a.by.strip()}\n- rodzaj: {a.kind}\n- dlaczego: {a.why.strip()}\n- zrodlo: {a.source_kind}\n"
             f"- szkic: {a.drafted_by}\n")
    f.write_text(f.read_text(encoding="utf-8").rstrip("\n") + "\n" + entry, encoding="utf-8")
    print(f"✓ {ref} w {f} (wyslano: nie)")
    return 0


def decision_pending(change: str | None) -> int:
    items = [{"ref": e["ref"], "record_decision": as_record(e, h)} for e, h in all_entries(change)
             if e.get("wyslano") != "tak"]
    print(json.dumps(items, ensure_ascii=False, indent=2))
    return 0


def decision_mark(ref: str, dec_id: str) -> int:
    if not KEY.match(dec_id):
        print(f"✗ --id '{dec_id}' — numer z rejestru pdi, np. DEC-41")
        return 1
    f = decisions_file(ref.split("/")[0])
    entry = next((e for e in parse_entries(f) if e["ref"] == ref), None) if f else None
    if entry is None:
        print(f"✗ nie ma decyzji {ref}")
        return 1
    if entry.get("id"):
        print(f"✗ {ref} ma już numer {entry['id']} — nie nadpisuję")
        return 1
    text = f.read_text(encoding="utf-8")
    comments = [m.span() for m in re.finditer(r"<!--.*?-->", text, flags=re.S)]
    block = next((m for m in re.finditer(rf"^- ref: {re.escape(ref)}\n- id:[ \t]*\n- wyslano: nie$", text, flags=re.M)
                  if not any(a <= m.start() < b for a, b in comments)), None)
    if not block:
        print(f"✗ {ref}: wpis nie ma wierszy `- id:` i `- wyslano: nie` zaraz po `- ref:` — popraw ręcznie")
        return 1
    f.write_text(text[:block.start()] + f"- ref: {ref}\n- id: {dec_id}\n- wyslano: tak" + text[block.end():],
                 encoding="utf-8")
    print(f"✓ {ref} → {dec_id} (wyslano: tak)")
    return 0


def decision_export() -> int:
    out = [{"ref": e["ref"], "id": e.get("id") or None, "sent": e.get("wyslano") == "tak", **as_record(e, h)}
           for e, h in all_entries()]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def check_entries(path: Path) -> list[str]:
    errs, seen = [], set()
    for e in parse_entries(path):
        r = e["ref"]
        if not re.fullmatch(rf"{re.escape(path.parent.name)}/D\d+", r):
            errs.append(f"{r}: ref w postaci {path.parent.name}/Dn")
        if r in seen:
            errs.append(f"{r}: powtórzony ref")
        seen.add(r)
        if e.get("id") and not KEY.match(e["id"]):
            errs.append(f"{r}: id '{e['id']}' — numer z rejestru pdi, np. DEC-41")
        if e.get("wyslano") not in ("tak", "nie"):
            errs.append(f"{r}: wyslano tak albo nie")
        if e.get("wyslano") == "tak" and not e.get("id"):
            errs.append(f"{r}: wyslano: tak bez numeru id")
        if e.get("rodzaj") not in KINDS:
            errs.append(f"{r}: rodzaj '{e.get('rodzaj')}' spoza {', '.join(KINDS)}")
        if e.get("zrodlo") not in SOURCE_KINDS:
            errs.append(f"{r}: zrodlo '{e.get('zrodlo')}' spoza {', '.join(SOURCE_KINDS)}")
        if e.get("szkic") not in ("ai", "human"):
            errs.append(f"{r}: szkic ai albo human")
        if not DATE.match(e.get("kiedy", "")):
            errs.append(f"{r}: kiedy RRRR-MM-DD")
        errs += [f"{r}: brak pola {k}" for k in ("kto", "dlaczego") if not e.get(k)]
    return errs


def check() -> int:
    files = sorted(CHANGES.glob("*/*.md")) if CHANGES.is_dir() else []
    if not files:
        print(f"Brak artefaktów zmian w {CHANGES} — nic do sprawdzenia.")
        return 0
    bad = 0
    for f in files:
        for e in check_file(f) + (check_entries(f) if f.name == "decisions.md" else []):
            print(f"✗ {f}: {e}")
            bad += 1
    print(f"{'✓' if not bad else '✗'} {len(files)} plików w {CHANGES}, błędów: {bad}")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ch = sub.add_parser("change").add_subparsers(dest="action", required=True)
    new = ch.add_parser("new")
    new.add_argument("key")
    new.add_argument("--source")
    new.add_argument("--author", default="claude")
    sub.add_parser("check")
    dec = sub.add_parser("decision").add_subparsers(dest="action", required=True)
    add = dec.add_parser("add")
    add.add_argument("key")
    add.add_argument("--statement", required=True)
    add.add_argument("--why", required=True)
    add.add_argument("--kind", required=True)
    add.add_argument("--by", required=True)
    add.add_argument("--date")
    add.add_argument("--source-kind", default="claude-cli")
    add.add_argument("--drafted-by", default="ai", choices=("ai", "human"))
    dec.add_parser("pending").add_argument("--change")
    mark = dec.add_parser("mark")
    mark.add_argument("ref")
    mark.add_argument("--id", required=True)
    dec.add_parser("export")
    args = ap.parse_args(argv)
    if args.cmd == "check":
        return check()
    if args.cmd == "decision":
        return {"add": lambda: decision_add(args), "pending": lambda: decision_pending(args.change),
                "mark": lambda: decision_mark(args.ref, args.id), "export": decision_export}[args.action]()
    return new_change(args.key, args.source, args.author)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
