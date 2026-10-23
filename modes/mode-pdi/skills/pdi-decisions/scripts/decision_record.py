#!/usr/bin/env python3
"""
Dziennik zmiany zgodny z kontraktem pdi 0.3.0 (contract/change.schema.json) — tryb mode-pdi.

  python3 .claude/skills/pdi-decisions/scripts/decision_record.py change new CHG-12 [--source PRB-34] [--author NAME]
      tworzy docs/project/changes/CHG-12/ z intent.md, plan.md i decisions.md (szablony obok skryptu)
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py check
      sprawdza nagłówki artefaktów w docs/project/changes/*/

Kod wyjścia: 0 — w porządku, 1 — błędy (z podpowiedzią), 2 — złe wywołanie.
"""
import argparse
import datetime as dt
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


def check() -> int:
    files = sorted(CHANGES.glob("*/*.md")) if CHANGES.is_dir() else []
    if not files:
        print(f"Brak artefaktów zmian w {CHANGES} — nic do sprawdzenia.")
        return 0
    bad = 0
    for f in files:
        for e in check_file(f):
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
    args = ap.parse_args(argv)
    if args.cmd == "check":
        return check()
    return new_change(args.key, args.source, args.author)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
