#!/usr/bin/env python3
"""
Change log conforming to the pdi 0.3.0 contract (contract/change.schema.json; from 0.5.0 with `source_reported_at`) and the release plan from contract 0.4.0
(contract/release-plan.schema.json, a copy next to the script) — mode-pdi.

  python3 .claude/skills/pdi-decisions/scripts/decision_record.py change new CHG-12 [--source PRB-34] [--author NAME]
      [--source-reported-at YYYY-MM-DD]   (the report date, from pdi; contract 0.5.0)
      creates docs/project/changes/CHG-12/ with intent.md, plan.md, decisions.md and release.yaml (templates next to the script)
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py check [--change CHG-n]
      checks artifact headers and decision entries in docs/project/changes/*/, and release.yaml — against the contract schema
      and for consistency: mvp.release among the lines, TSK in a single line and matching plan.md (tasks, the Release and Flag columns),
      flag with stages (rollout) and a removal date (remove_by), flag TSKs in the lines; in plan.md the cut-plan self-check
      (a foundation whose „Unblocks” points to a TSK of this change, a cut with a requirement ID or verification — like REL-008)
      a factory task folder (with `task.json`, without `intent.md`, e.g. cut task CHG-12-TSK-57) is skipped — its
      files are not change artifacts
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py decision add CHG-12 --statement "…" --why "…" \
      --kind product --by "who" [--date YYYY-MM-DD] [--source-kind claude-cli] [--drafted-by ai]
      [--finding DES-001:TSK-1 [--effect resolve|accept_risk|dismiss|confirm]]
      appends an approved decision to decisions.md (ref CHG-12/Dn, empty id, sent: no); with --finding it is an answer
      to a ci_for_sdlc finding (field `finding`, statement = the answer), which ci_for_sdlc reads from the repo (PRB-16)
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py decision pending [--change CHG-12]
      JSON of unsent decisions with ready arguments for record_decision (pdi MCP)
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py decision mark CHG-12/D1 --id DEC-41
      records the number assigned by the pdi register and sent: yes
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py decision export
      JSON of all project decisions (with number and sent state)
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py decision gate CHG-12 --gate B1 --outcome approved \
      --id DEC-41 [--by pdi] [--date YYYY-MM-DD] [--why "…"] [--answers FILE]
      a decision from the pdi inbox (gate.decided, inputs of the sdlc-phase.yml template) as an entry with a number and sent: yes;
      a repeat with the same number appends nothing; --answers: JSON [{question, answer}] — the human's answers to
      questions from `## Gate questions` (pdi contract 0.12.0, field answers), in the entry as `question`/`answer` pairs
  python3 .claude/skills/pdi-decisions/scripts/decision_record.py decision import CHG-12 --json FILE
      decisions of the change from the pdi register (links.chg; JSON list {id, statement, why, decided_at, decided_by, kind,
      source_kind, drafted_by, answers?}) as entries with a number, sent: yes and origin: pdi; a decision whose number
      is already in decisions.md is skipped (a repeat appends nothing)

Exit code: 0 — OK, 1 — errors (with a hint), 2 — bad invocation.
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
KEYS = ("artifact", "phase", "status", "version", "author", "created", "updated", "inputs", "change", "source",
        "source_reported_at", "tasks", "superseded_by")   # change.schema.json kontraktu pdi 0.5.0
REQUIRED = ("artifact", "phase", "status", "version", "created", "updated", "change")
OUTCOMES = ("approved", "changes_requested", "rejected")   # gate.decided w kontrakcie pdi 0.4.0
KINDS = ("product", "technical", "process", "triage", "intent", "gate", "other")
# source.kind decyzji z kontraktu pdi 0.10.0 (decyzje z pdi: konsola, ci_for_sdlc, spotkania)
SOURCE_KINDS = ("claude-cli", "claude-ai", "slack", "confluence", "jira", "manual", "console", "ci_for_sdlc", "meeting",
                "tf", "shipscope")
ENTRY = ("ref", "id", "sent", "date", "by", "kind", "why", "source", "drafted_by",
         "finding", "effect",   # answer to a ci_for_sdlc finding
         "origin")           # pdi — an entry from the pdi register (decision import)
# A pair of rows of an answer to a gate question (pdi contract 0.12.0, answers); an entry may have several.
ANSWER_KEYS = ("question", "answer")
ORIGINS = ("pdi",)
TEXT_MAX = 2000   # one entry row from pdi data
# Id of a ci_for_sdlc finding (rule:element[:detail], e.g. DES-001:TSK-1) and the effect of the answer (DECISION_EFFECTS in ci_for_sdlc).
FINDING = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3}:[A-Z][A-Z0-9]+-[0-9]+(?::\S{1,80})?$")
EFFECTS = ("resolve", "accept_risk", "dismiss", "confirm")
NEW = {"intent": "discovery", "plan": "plan", "decisions": "plan"}   # artefakty `change new` i ich faza
CHANGES = Path("docs") / "project" / "changes"
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
RELEASE_SCHEMA = Path(__file__).resolve().parent / "release-plan.schema.json"   # kopia z kontraktu pdi (tools/pdi-contract.json)
EMPTY_CELL = ("", "—", "-", "–")


def parse_header(text: str) -> dict | None:
    """The YAML header in the simple form from the contract: `key: value`, lists `[a, b]` or `- a` on consecutive lines."""
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


def new_change(key: str, source: str | None, author: str, reported: str | None = None) -> int:
    bad = [f"{name} '{v}'" for name, v in (("change key", key), ("problem key", source)) if v and not KEY.match(v)]
    if bad:
        print(f"✗ bad format: {', '.join(bad)} — pattern [A-Z][A-Z0-9]+-[0-9]+, e.g. CHG-12, PRB-34")
        return 1
    if reported and not source:
        print("✗ --source-reported-at without --source — the date belongs to the problem the change came from")
        return 1
    if reported and not DATE.match(reported):
        print(f"✗ --source-reported-at '{reported}' — date YYYY-MM-DD")
        return 1
    target = CHANGES / key
    if target.exists():
        print(f"✗ {target} already exists — not overwriting; edit the existing files or use another key")
        return 1
    today = dt.date.today().isoformat()
    target.mkdir(parents=True)
    for artifact, phase in NEW.items():
        fields = {"artifact": artifact, "phase": phase, "status": "draft", "version": "1", "author": author,
                  "created": today, "updated": today, "inputs": [], "change": key}
        if source:
            fields["source"] = source
        if reported:
            fields["source_reported_at"] = reported
        if artifact == "plan":
            fields["tasks"] = []
        body = (TEMPLATES / f"{artifact}.md").read_text(encoding="utf-8").replace("{CHG}", key)
        (target / f"{artifact}.md").write_text(render(fields) + body, encoding="utf-8")
    (target / "release.yaml").write_text((TEMPLATES / "release.yaml").read_text(encoding="utf-8").replace("{CHG}", key),
                                         encoding="utf-8")
    print(f"✓ {target}/: intent.md, plan.md, decisions.md (status draft), release.yaml")
    return 0


def check_file(path: Path) -> list[str]:
    h = parse_header(path.read_text(encoding="utf-8"))
    if h is None:
        return ["no YAML header (--- … ---) at the top of the file"]
    errs = [f"missing field {k}" for k in REQUIRED if not h.get(k)]
    errs += [f"unknown field {k} (pdi contract 0.5.0 allows: {', '.join(KEYS)})" for k in h if k not in KEYS]
    for k, allowed in (("artifact", ARTIFACTS), ("phase", PHASES), ("status", STATUSES)):
        if h.get(k) and h[k] not in allowed:
            errs.append(f"{k}: '{h[k]}' not in {', '.join(allowed)}")
    if h.get("version") and not (str(h["version"]).isdigit() and int(h["version"]) >= 1):
        errs.append(f"version: '{h['version']}' — integer ≥ 1")
    for k in ("created", "updated", "source_reported_at"):
        if h.get(k) and not DATE.match(str(h[k])):
            errs.append(f"{k}: '{h[k]}' — date YYYY-MM-DD")
    for k in ("change", "source"):
        if h.get(k) and not KEY.match(str(h[k])):
            errs.append(f"{k}: '{h[k]}' — key [A-Z][A-Z0-9]+-[0-9]+, e.g. CHG-12")
    if h.get("change") and KEY.match(str(h["change"])) and h["change"] != path.parent.name:
        errs.append(f"change: '{h['change']}' differs from folder {path.parent.name}")
    if "tasks" in h:
        if h.get("artifact") != "plan":
            errs.append("tasks only in plan.md (artifact: plan)")
        tasks = h["tasks"] if isinstance(h["tasks"], list) else [h["tasks"]] if h["tasks"] else []
        errs += [f"tasks: '{t}' — cut key, e.g. TSK-57" for t in tasks if not KEY.match(t)]
    for k in ("inputs",):
        if k in h and not isinstance(h[k], list) and h[k]:
            errs.append(f"{k}: list of paths, e.g. [docs/project/changes/CHG-12/intent.md]")
    return errs


def parse_entries(path: Path) -> list[dict]:
    """Decision entries: a `## <what>` heading and a `- field: value` list; the entry pattern in the template comment is skipped."""
    text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
    out, cur = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = {"statement": line[3:].strip()}
            out.append(cur)
        elif cur is not None and line.startswith("- ") and ":" in line:
            k, _, v = line[2:].partition(":")
            if k.strip() == "question":
                cur.setdefault("answers", []).append([v.strip(), None])
            elif k.strip() == "answer":
                if cur.get("answers") and cur["answers"][-1][1] is None:
                    cur["answers"][-1][1] = v.strip()
                else:
                    cur.setdefault("answers", []).append([None, v.strip()])
            elif k.strip() in ENTRY:
                cur[k.strip()] = v.strip()
    return [e for e in out if "ref" in e]


def one_line(text, limit: int = TEXT_MAX) -> str:
    """Text from pdi in one entry row (an entry is a `- field: value` list), without comment markers."""
    s = " ".join(str(text or "").split()).replace("<!--", "<! --").replace("-->", "-- >")
    return s if len(s) <= limit else s[:limit - 1] + "…"


def answers_lines(answers: list) -> str:
    return "".join(f"- question: {one_line(q)}\n- answer: {one_line(a)}\n" for q, a in answers)


def load_answers(path: str) -> list:
    """Answers from a JSON file [{question, answer}] (pdi, contract 0.12.0) as pairs or a Refused-like error."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"--answers {path}: cannot read JSON ({e})") from e
    ok = isinstance(data, list) and all(isinstance(a, dict) and isinstance(a.get("question"), str)
                                        and isinstance(a.get("answer"), str) and a["question"].strip()
                                        and a["answer"].strip() for a in data)
    if not ok:
        raise ValueError(f"--answers {path}: expected a list [{{question, answer}}] with non-empty texts")
    return [(a["question"], a["answer"]) for a in data]


def decisions_file(key: str) -> Path | None:
    f = CHANGES / key / "decisions.md"
    return f if f.is_file() else None


def as_record(e: dict, change_header: dict) -> dict:
    """Argumenty record_decision (kontrakt pdi 0.3.0, decision.schema.json) z wpisu w decisions.md."""
    chg = e["ref"].split("/")[0]
    links = {"chg": chg}
    if change_header.get("source"):
        links["prb"] = change_header["source"]
    return {"statement": e["statement"], "why": e.get("why", ""), "kind": e.get("kind", ""),
            "source": {"kind": e.get("source", "")}, "drafted_by": e.get("drafted_by", ""),
            "decided_by": e.get("by", ""), "decided_at": e.get("date", ""), "links": links}


def all_entries(change: str | None = None) -> list[tuple[dict, dict]]:
    files = sorted(CHANGES.glob(f"{change or '*'}/decisions.md")) if CHANGES.is_dir() else []
    return [(e, parse_header(f.read_text(encoding="utf-8")) or {}) for f in files for e in parse_entries(f)]


def decision_add(a) -> int:
    f = decisions_file(a.key) if KEY.match(a.key) else None
    if f is None:
        print(f"✗ no {CHANGES / a.key / 'decisions.md'} — first run: decision_record.py change new {a.key}")
        return 1
    errs = [f"--kind '{a.kind}' not in {', '.join(KINDS)}" for _ in [0] if a.kind not in KINDS]
    errs += [f"--source-kind '{a.source_kind}' not in {', '.join(SOURCE_KINDS)}" for _ in [0]
             if a.source_kind not in SOURCE_KINDS]
    errs += [f"--date '{a.date}' — YYYY-MM-DD" for _ in [0] if a.date and not DATE.match(a.date)]
    errs += [f"--{n} is empty" for n, v in (("statement", a.statement), ("why", a.why), ("by", a.by)) if not v.strip()]
    if a.finding and not FINDING.match(a.finding):
        errs.append(f"--finding '{a.finding}' — ci_for_sdlc finding id, e.g. DES-001:TSK-1")
    elif a.finding and a.finding.split(":")[1] not in items_of(a.key):
        errs.append(f"--finding '{a.finding}' refers to {a.finding.split(':')[1]}, which is neither {a.key} nor one of its cuts (plan.md)")
    if a.effect and not a.finding:
        errs.append("--effect only with --finding")
    if errs:
        print("✗ " + "; ".join(errs))
        return 1
    n = 1 + max([int(e["ref"].rsplit("D", 1)[1]) for e in parse_entries(f) if re.search(r"/D\d+$", e["ref"])] or [0])
    ref = f"{a.key}/D{n}"
    entry = (f"\n## {a.statement.strip()}\n- ref: {ref}\n- id:\n- sent: no\n- date: {a.date or dt.date.today().isoformat()}\n"
             f"- by: {a.by.strip()}\n- kind: {a.kind}\n- why: {a.why.strip()}\n- source: {a.source_kind}\n"
             f"- drafted_by: {a.drafted_by}\n")
    if a.finding:
        entry += f"- finding: {a.finding}\n" + (f"- effect: {a.effect}\n" if a.effect else "")
    f.write_text(f.read_text(encoding="utf-8").rstrip("\n") + "\n" + entry, encoding="utf-8")
    print(f"✓ {ref} in {f} (sent: no)")
    return 0


def decision_gate(a) -> int:
    """A decision made in the pdi inbox: the register already assigned the number, so the entry is sent right away."""
    f = decisions_file(a.key) if KEY.match(a.key) else None
    if f is None:
        print(f"✗ no {CHANGES / a.key / 'decisions.md'} — first run: decision_record.py change new {a.key}")
        return 1
    errs = [f"--outcome '{a.outcome}' not in {', '.join(OUTCOMES)}" for _ in [0] if a.outcome not in OUTCOMES]
    errs += [f"--id '{a.id}' — number from the pdi registry, e.g. DEC-41" for _ in [0] if not KEY.match(a.id)]
    errs += [f"--date '{a.date}' — YYYY-MM-DD" for _ in [0] if a.date and not DATE.match(a.date)]
    errs += [f"--{n} is empty" for n, v in (("gate", a.gate), ("by", a.by)) if not v.strip()]
    if errs:
        print("✗ " + "; ".join(errs))
        return 1
    try:
        answers = load_answers(a.answers) if a.answers else []
    except ValueError as e:
        print(f"✗ {e}")
        return 1
    entries = parse_entries(f)
    same = next((e for e in entries if e.get("id") == a.id), None)
    if same:
        print(f"✓ {same['ref']} already has {a.id} — nothing to add")
        return 0
    n = 1 + max([int(e["ref"].rsplit("D", 1)[1]) for e in entries if re.search(r"/D\d+$", e["ref"])] or [0])
    ref = f"{a.key}/D{n}"
    # The finding and rationale from pdi (PRB-3) in one row, because an entry is a `- field: value` list.
    why = " ".join((a.why or "").split())
    why = f"{why} (decision in the pdi gate inbox, {a.id})" if why else (
        f"decision in the pdi gate inbox ({a.id}); rationale in the pdi registry")
    entry = (f"\n## Gate {a.gate.strip()}: {a.outcome}\n- ref: {ref}\n- id: {a.id}\n- sent: yes\n"
             f"- date: {a.date or dt.date.today().isoformat()}\n- by: {a.by.strip()}\n- kind: gate\n"
             f"- why: {one_line(why)}\n- source: manual\n- drafted_by: human\n" + answers_lines(answers))
    f.write_text(f.read_text(encoding="utf-8").rstrip("\n") + "\n" + entry, encoding="utf-8")
    told = f", answers to questions: {len(answers)}" if answers else ""
    print(f"✓ {ref} in {f} ({a.id}, sent: yes{told})")
    return 0


def import_problems(d, n: int) -> list[str]:
    """Braki jednej decyzji z pdi do importu (pola z contract/decision.schema.json kontraktu pdi 0.12.0)."""
    if not isinstance(d, dict):
        return [f"[{n}]: expected a decision object"]
    errs = [f"[{n}]: id '{d.get('id')}' — number from the pdi registry, e.g. DEC-41" for _ in [0]
            if not (isinstance(d.get("id"), str) and KEY.match(d["id"]))]
    errs += [f"[{n}]: missing field {k}" for k in ("statement", "why", "decided_by")
             if not (isinstance(d.get(k), str) and d[k].strip())]
    errs += [f"[{n}]: decided_at '{d.get('decided_at')}' — YYYY-MM-DD" for _ in [0]
             if not (isinstance(d.get("decided_at"), str) and DATE.match(d["decided_at"]))]
    errs += [f"[{n}]: kind '{d.get('kind')}' not in {', '.join(KINDS)}" for _ in [0] if d.get("kind") not in KINDS]
    errs += [f"[{n}]: drafted_by must be ai or human" for _ in [0] if d.get("drafted_by") not in ("ai", "human")]
    answers = d.get("answers") or []
    if not (isinstance(answers, list) and all(isinstance(x, dict) and isinstance(x.get("question"), str)
                                              and isinstance(x.get("answer"), str) for x in answers)):
        errs.append(f"[{n}]: answers — a list [{{question, answer}}]")
    return errs


def decision_import(a) -> int:
    """Change decisions from the pdi register (Z1, PRB-3): appends those whose number is not yet in decisions.md."""
    f = decisions_file(a.key) if KEY.match(a.key) else None
    if f is None:
        print(f"✗ no {CHANGES / a.key / 'decisions.md'} — first run: decision_record.py change new {a.key}")
        return 1
    try:
        data = json.loads(Path(a.json).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"✗ --json {a.json}: cannot read JSON ({e})")
        return 1
    if not isinstance(data, list):
        print(f"✗ --json {a.json}: expected a list of decisions from pdi")
        return 1
    errs = [e for n, d in enumerate(data) for e in import_problems(d, n)]
    if errs:
        print("✗ " + "; ".join(errs))
        return 1
    entries = parse_entries(f)
    known = {e.get("id") for e in entries if e.get("id")}
    n = max([int(e["ref"].rsplit("D", 1)[1]) for e in entries if re.search(r"/D\d+$", e["ref"])] or [0])
    added, text = [], ""
    for d in data:
        if d["id"] in known:
            continue
        known.add(d["id"])
        n += 1
        ref = f"{a.key}/D{n}"
        source = d.get("source_kind") if d.get("source_kind") in SOURCE_KINDS else "manual"
        text += (f"\n## {one_line(d['statement'], 300)}\n- ref: {ref}\n- id: {d['id']}\n- sent: yes\n"
                 f"- date: {d['decided_at']}\n- by: {one_line(d['decided_by'], 200)}\n- kind: {d['kind']}\n"
                 f"- why: {one_line(d['why'])}\n- source: {source}\n- drafted_by: {d['drafted_by']}\n"
                 f"- origin: pdi\n"
                 + answers_lines([(x["question"], x["answer"]) for x in d.get("answers") or []
                                  if x["question"].strip() and x["answer"].strip()]))
        added.append(f"{ref} ({d['id']})")
    if added:
        f.write_text(f.read_text(encoding="utf-8").rstrip("\n") + "\n" + text, encoding="utf-8")
    skipped = len(data) - len(added)
    print(f"✓ {f}: imported from pdi {len(added)}" + (f" — {', '.join(added)}" if added else "")
          + (f"; skipped (number already present): {skipped}" if skipped else ""))
    return 0


def decision_pending(change: str | None) -> int:
    items = [{"ref": e["ref"], "record_decision": as_record(e, h)} for e, h in all_entries(change)
             if e.get("sent") != "yes"]
    print(json.dumps(items, ensure_ascii=False, indent=2))
    return 0


def decision_mark(ref: str, dec_id: str) -> int:
    if not KEY.match(dec_id):
        print(f"✗ --id '{dec_id}' — number from the pdi registry, e.g. DEC-41")
        return 1
    f = decisions_file(ref.split("/")[0])
    entry = next((e for e in parse_entries(f) if e["ref"] == ref), None) if f else None
    if entry is None:
        print(f"✗ no decision {ref}")
        return 1
    if entry.get("id"):
        print(f"✗ {ref} already has number {entry['id']} — not overwriting")
        return 1
    text = f.read_text(encoding="utf-8")
    comments = [m.span() for m in re.finditer(r"<!--.*?-->", text, flags=re.S)]
    block = next((m for m in re.finditer(rf"^- ref: {re.escape(ref)}\n- id:[ \t]*\n- sent: no$", text, flags=re.M)
                  if not any(a <= m.start() < b for a, b in comments)), None)
    if not block:
        print(f"✗ {ref}: the entry has no `- id:` and `- sent: no` lines right after `- ref:` — fix it by hand")
        return 1
    f.write_text(text[:block.start()] + f"- ref: {ref}\n- id: {dec_id}\n- sent: yes" + text[block.end():],
                 encoding="utf-8")
    print(f"✓ {ref} → {dec_id} (sent: yes)")
    return 0


def decision_export() -> int:
    out = [{"ref": e["ref"], "id": e.get("id") or None, "sent": e.get("sent") == "yes", **as_record(e, h)}
           for e, h in all_entries()]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def items_of(key: str) -> set[str]:
    """The change and its cuts (`tasks` in the plan.md header and the TSKs of its table): the elements its findings concern."""
    plan = CHANGES / key / "plan.md"
    text = plan.read_text(encoding="utf-8") if plan.is_file() else ""
    tasks = (parse_header(text) or {}).get("tasks") or []
    return {key, *(tasks if isinstance(tasks, list) else []), *re.findall(r"\|\s*(TSK-[0-9]+)\s*\|", text)}


def check_entries(path: Path) -> list[str]:
    errs, seen = [], set()
    items = items_of(path.parent.name)
    for e in parse_entries(path):
        r = e["ref"]
        if not re.fullmatch(rf"{re.escape(path.parent.name)}/D\d+", r):
            errs.append(f"{r}: ref must look like {path.parent.name}/Dn")
        if r in seen:
            errs.append(f"{r}: duplicate ref")
        seen.add(r)
        if e.get("id") and not KEY.match(e["id"]):
            errs.append(f"{r}: id '{e['id']}' — number from the pdi registry, e.g. DEC-41")
        if e.get("sent") not in ("yes", "no"):
            errs.append(f"{r}: sent must be yes or no")
        if e.get("sent") == "yes" and not e.get("id"):
            errs.append(f"{r}: sent: yes without an id number")
        if e.get("kind") not in KINDS:
            errs.append(f"{r}: kind '{e.get('kind')}' not in {', '.join(KINDS)}")
        if e.get("source") not in SOURCE_KINDS:
            errs.append(f"{r}: source '{e.get('source')}' not in {', '.join(SOURCE_KINDS)}")
        if e.get("drafted_by") not in ("ai", "human"):
            errs.append(f"{r}: drafted_by must be ai or human")
        if not DATE.match(e.get("date", "")):
            errs.append(f"{r}: date YYYY-MM-DD")
        errs += [f"{r}: missing field {k}" for k in ("by", "why") if not e.get(k)]
        finding = e.get("finding")
        if finding is not None and not FINDING.match(finding):
            errs.append(f"{r}: finding '{finding}' — ci_for_sdlc finding id, e.g. DES-001:TSK-1")
        elif finding and finding.split(":")[1] not in items:
            errs.append(f"{r}: finding {finding} refers to an item outside {path.parent.name} and its cuts")
        if e.get("effect") is not None and (not finding or e["effect"] not in EFFECTS):
            errs.append(f"{r}: effect {'/'.join(EFFECTS)} and only with the finding field")
        if e.get("origin") is not None and e["origin"] not in ORIGINS:
            errs.append(f"{r}: origin '{e['origin']}' — only {', '.join(ORIGINS)} (decision import)")
        if e.get("origin") == "pdi" and not e.get("id"):
            errs.append(f"{r}: origin: pdi without an id number")
        for q, ans in e.get("answers") or []:
            if not q or not ans:
                errs.append(f"{r}: `- question:` and `- answer:` lines go in pairs, both non-empty")
    return errs


def load_yaml(text: str):
    try:
        import yaml
    except ImportError:   # bundled PyYAML copy (.tf/factory/_vendor), as in the loop scripts (skill tf)
        vendor = next((p / ".tf" / "factory" / "_vendor" for p in Path(__file__).resolve().parents
                       if (p / ".tf" / "factory" / "_vendor").is_dir()), None)
        if vendor is None:
            raise
        sys.path.insert(0, str(vendor))
        import yaml
    try:
        return plain(yaml.safe_load(text)), None
    except yaml.YAMLError as e:
        return None, " ".join(str(e).split())[:200]


def plain(v):
    """YAML dates (`remove_by: 2026-12-31`) as text — the contract schema describes them as a string."""
    if isinstance(v, dict):
        return {str(k): plain(x) for k, x in v.items()}
    if isinstance(v, list):
        return [plain(x) for x in v]
    return v.isoformat() if isinstance(v, (dt.date, dt.datetime)) else v


def validate(v, s: dict, at: str) -> list[str]:
    """Subset of JSON Schema used in the pdi contract: type, required, additionalProperties, properties, items, pattern,
    minLength, minItems, minimum, enum, const, allOf with if/then (condition: fields required in a given state)."""
    types = {"object": dict, "array": list, "string": str, "integer": int}
    t = s.get("type")
    if t and (not isinstance(v, types[t]) or (t == "integer" and isinstance(v, bool))):
        return [f"{at or 'file'}: expected {t}, got {type(v).__name__} ({v!r})"]
    if "const" in s and v != s["const"]:
        return [f"{at or 'file'}: expected {s['const']!r}"]
    errs = []
    if isinstance(v, dict) and t in (None, "object"):
        errs += [f"{at or 'file'}: missing field {k}" for k in s.get("required", []) if k not in v]
        props = s.get("properties", {})
        if s.get("additionalProperties") is False:
            errs += [f"{at or 'file'}: unknown field {k} (allowed: {', '.join(props)})" for k in v if k not in props]
        for k, sub in props.items():
            if k in v:
                errs += validate(v[k], sub, f"{at}.{k}" if at else k)
    elif t == "array":
        if len(v) < s.get("minItems", 0):
            errs.append(f"{at}: at least {s['minItems']} items")
        for i, x in enumerate(v):
            errs += validate(x, s.get("items", {}), f"{at}[{i}]")
    elif t == "string":
        if len(v) < s.get("minLength", 0):
            errs.append(f"{at}: empty text")
        if "pattern" in s and not re.search(s["pattern"], v):
            errs.append(f"{at}: '{v}' does not match {s['pattern']}")
    elif t == "integer" and "minimum" in s and v < s["minimum"]:
        errs.append(f"{at}: {v} < {s['minimum']}")
    if "enum" in s and not isinstance(v, (dict, list)) and v not in s["enum"]:   # also without type (contract conditions)
        errs.append(f"{at}: '{v}' not in {', '.join(map(str, s['enum']))}")
    for sub in s.get("allOf", []):
        if "if" in sub:
            if not validate(v, sub["if"], at):
                errs += validate(v, sub.get("then", {}), at)
        else:
            errs += validate(v, sub, at)
    return errs


PLAN_COLUMNS = ("release", "flag", "kind", "value", "requirements", "unblocks", "verification")   # pdi contract
# Column headers (the template, like ci_for_sdlc connectors/repo.ts) → the keys above.
COLUMN_ALIASES = {"flags": "flag", "requirement": "requirements"}
FOUNDATION = re.compile(r"^(fundament|foundation|f|f-\d+)$", re.I)   # jak REL-008 w ci_for_sdlc (connectors/repo.ts)
FOUNDATION_VALUE = re.compile(r"^\((fundament|foundation)\)", re.I)
REQUIREMENT_ID = re.compile(r"\b[A-Z][A-Z0-9]*-\d+\b")
# Architect sections in plan.md (N20 and Z7b-1a; pdi contract 0.12.0 — a human reads plan.md, a machine reads release.yaml).
OPTIONS_HEADING = re.compile(r"^##+\s+Options considered\b", re.M | re.I)
OPTION_ENTRY = re.compile(r"^###+\s+Option\b", re.M)
TARGETS_HEADING = re.compile(r"^##+\s+Change targets\b", re.M | re.I)


def plan_columns(text: str) -> dict:
    """Rows of the plan.md cut table: TSK → {column: value} for the PLAN_COLUMNS columns present in the header."""
    out, cols = {}, None
    for line in re.sub(r"<!--.*?-->", "", text, flags=re.S).splitlines():
        if not line.strip().startswith("|"):
            cols = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        low = [COLUMN_ALIASES.get(c.lower(), c.lower()) for c in cells]
        if "release" in low or "flag" in low or "unblocks" in low:
            cols = {k: low.index(k) for k in PLAN_COLUMNS if k in low}
            continue
        if cols and cells and KEY.match(cells[0]):
            out[cells[0]] = {k: (cells[i] if i < len(cells) and cells[i] not in EMPTY_CELL else None)
                             for k, i in cols.items()}
    return out


def check_plan(d: Path) -> list[str]:
    """Cut-plan self-check (core-delivery-lifecycle cut-plan.md), the same as REL-008 in ci_for_sdlc: a foundation
    with „Unblocks” pointing to the cuts of this change; a cut with a requirement ID or verification (when the plan has „Requirements”).

    From contract 0.12.0 (Z7b-1a, DZ6, DZ7, N20) a plan with a status other than `draft` must also have a section
    `## Options considered` with at least two options (`### Option ...`) and a `## Change targets` section (`targets`).
    A `draft` plan is an architect's sketch — not yet approved at B3, so we do not require these sections.
    """
    plan = d / "plan.md"
    if not plan.is_file():
        return []
    text = plan.read_text(encoding="utf-8")
    h = parse_header(text) or {}
    rows = plan_columns(text)
    known = set(rows) | set(h["tasks"] if isinstance(h.get("tasks"), list) else [h["tasks"]] if h.get("tasks") else [])
    errs = []
    for t, row in rows.items():
        if FOUNDATION.match(row.get("kind") or "") or FOUNDATION_VALUE.match(row.get("value") or ""):
            unblocks = REQUIREMENT_ID.findall(row.get("unblocks") or "")
            if not unblocks:
                errs.append(f"plan.md: {t} — foundation without „Unblocks” (the cuts of this change it unblocks); "
                            "without it this is layered work: remove it or merge it into the first cut that needs it")
            for u in unblocks:
                if u not in known:
                    errs.append(f"plan.md: {t} — „Unblocks” lists {u}, but {u} is not a cut of this change")
        elif "requirements" in row and not REQUIREMENT_ID.findall(row["requirements"] or "") and not row.get("verification"):
            errs.append(f"plan.md: {t} — cut without a requirement ID in „Requirements” and without verification")
    status = (h.get("status") or "").strip().lower() if isinstance(h.get("status"), str) else ""
    if status and status != "draft":
        if not OPTIONS_HEADING.search(text):
            errs.append("plan.md: no „## Options considered” section (N20): the architect lists at least two options "
                        "considered, with pros, cons and cost, plus the choice and the reason")
        else:
            options = OPTION_ENTRY.findall(text)
            if len(options) < 2:
                errs.append(f"plan.md: „## Options considered” has {len(options)} options — N20 needs at least two "
                            "(headings `### Option A`, `### Option B`); a plan with one option gets a finding before B3")
        if not TARGETS_HEADING.search(text):
            errs.append("plan.md: no „## Change targets (targets)” section (Z7b-1a, DZ7): the architect records "
                        "coverage and mutation targets for the changed code (N4), and eval thresholds for an AI product")
    return errs


def check_release(d: Path) -> list[str]:
    try:
        data, err = load_yaml((d / "release.yaml").read_text(encoding="utf-8"))
    except ImportError:
        return ["PyYAML missing (pip install pyyaml) — cannot check the release plan"]
    if err:
        return [f"invalid YAML: {err}"]
    if not isinstance(data, dict):
        return ["invalid YAML: expected a map with fields change, releases (release-plan contract)"]
    errs = validate(data, json.loads(RELEASE_SCHEMA.read_text(encoding="utf-8")), "")
    if errs:
        return [f"contract schema: {e}" for e in errs]
    if data["change"] != d.name:
        errs.append(f"change: '{data['change']}' differs from folder {d.name}")
    line_of: dict[str, str] = {}
    ids = [r["id"] for r in data["releases"]]
    errs += [f"release line {i} repeated" for i in sorted({i for i in ids if ids.count(i) > 1})]
    for r in data["releases"]:
        for t in r["tasks"]:
            if t in line_of:
                errs.append(f"{t} in two release lines: {line_of[t]} and {r['id']} — a cut belongs to one line")
            line_of.setdefault(t, r["id"])
    if "mvp" in data and data["mvp"]["release"] not in ids:
        errs.append(f"mvp.release {data['mvp']['release']} is not a line in releases ({', '.join(ids)})")
    flag_of: dict[str, str] = {}
    for fl in data.get("flags", []):
        k = fl["key"]
        if not fl.get("rollout"):
            errs.append(f"flag {k}: no rollout stages (rollout), e.g. internal → 10% → 100%")
        if not fl.get("remove_by"):
            errs.append(f"flag {k}: no removal date (remove_by)")
        for t in fl.get("tasks", []):
            if t not in line_of:
                errs.append(f"flag {k}: {t} is not in any release line")
            if t in flag_of and flag_of[t] != k:
                errs.append(f"{t} behind two flags: {flag_of[t]} and {k}")
            flag_of.setdefault(t, k)
    plan = d / "plan.md"
    if plan.is_file():
        text = plan.read_text(encoding="utf-8")
        h = parse_header(text) or {}
        tasks = set(h["tasks"] if isinstance(h.get("tasks"), list) else [h["tasks"]] if h.get("tasks") else [])
        only_rel, only_plan = sorted(set(line_of) - tasks), sorted(tasks - set(line_of))
        if only_rel or only_plan:
            errs.append("TSK in release lines ≠ tasks in plan.md: " + "; ".join(
                x for x in (f"only in release.yaml: {', '.join(only_rel)}" if only_rel else "",
                            f"only in plan.md: {', '.join(only_plan)}" if only_plan else "") if x))
        for t, row in plan_columns(text).items():
            if "release" in row and row["release"] != line_of.get(t):
                errs.append(f"plan.md: {t} — column „Release” is {row['release'] or 'empty'}, in release.yaml "
                            f"{line_of.get(t) or 'no line'}")
            if "flag" in row and row["flag"] != flag_of.get(t):
                errs.append(f"plan.md: {t} — column „Flag” is {row['flag'] or 'empty'}, in release.yaml "
                            f"{flag_of.get(t) or 'no flag'}")
    return errs


def is_task_folder(folder: Path) -> bool:
    """A factory task folder (`task.json`, without `intent.md`): its files are not change artifacts and have no
    pdi contract header. A change in which someone also created `task.json` has `intent.md` and is checked."""
    return (folder / "task.json").is_file() and not (folder / "intent.md").is_file()


def check(change: str | None = None) -> int:
    """Headers, decision entries, the plan and the release plan. `change` narrows to one change: a pdi phase checks its own,
    and artifacts of older changes (written for an earlier contract) do not block it."""
    pattern = "*"
    if change is not None:
        if not KEY.match(change):
            print(f"✗ --change '{change}' — change key, e.g. CHG-12")
            return 2
        if not (CHANGES / change).is_dir():
            print(f"✗ no {CHANGES / change} — change {change} has no log")
            return 1
        pattern = change
    files = sorted(CHANGES.glob(f"{pattern}/*.md")) if CHANGES.is_dir() else []
    files = [f for f in files if not is_task_folder(f.parent)]
    releases = sorted(CHANGES.glob(f"{pattern}/release.yaml")) if CHANGES.is_dir() else []
    if not files and not releases:
        print(f"No change artifacts in {CHANGES} — nothing to check.")
        return 0
    bad = 0
    for f in files:
        extra = check_entries(f) if f.name == "decisions.md" else check_plan(f.parent) if f.name == "plan.md" else []
        for e in check_file(f) + extra:
            print(f"✗ {f}: {e}")
            bad += 1
    for f in releases:   # a change without release.yaml (predating the release plan) is not an error
        for e in check_release(f.parent):
            print(f"✗ {f}: {e}")
            bad += 1
    print(f"{'✓' if not bad else '✗'} {len(files) + len(releases)} files in {CHANGES}, errors: {bad}")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ch = sub.add_parser("change").add_subparsers(dest="action", required=True)
    new = ch.add_parser("new")
    new.add_argument("key")
    new.add_argument("--source")
    new.add_argument("--author", default="claude")
    new.add_argument("--source-reported-at")
    sub.add_parser("check").add_argument("--change", help="only this change (e.g. CHG-12); without it — all changes")
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
    add.add_argument("--finding", help="id of the ci_for_sdlc finding this answers (e.g. DES-001:TSK-1)")
    add.add_argument("--effect", choices=EFFECTS, help="effect of the answer; default resolve")
    dec.add_parser("pending").add_argument("--change")
    mark = dec.add_parser("mark")
    mark.add_argument("ref")
    mark.add_argument("--id", required=True)
    dec.add_parser("export")
    gate = dec.add_parser("gate")
    gate.add_argument("key")
    gate.add_argument("--gate", required=True)
    gate.add_argument("--outcome", required=True)
    gate.add_argument("--id", required=True)
    gate.add_argument("--by", default="pdi")
    gate.add_argument("--date")
    gate.add_argument("--why", help="decision statement and rationale from the pdi registry (goes into the entry)")
    gate.add_argument("--answers", help="JSON file [{question, answer}] — answers to the gate questions (pdi 0.12.0)")
    imp = dec.add_parser("import")
    imp.add_argument("key")
    imp.add_argument("--json", required=True, help="JSON file with the change decisions from the pdi registry (links.chg)")
    args = ap.parse_args(argv)
    if args.cmd == "check":
        return check(args.change)
    if args.cmd == "decision":
        return {"add": lambda: decision_add(args), "pending": lambda: decision_pending(args.change),
                "mark": lambda: decision_mark(args.ref, args.id), "export": decision_export,
                "gate": lambda: decision_gate(args), "import": lambda: decision_import(args)}[args.action]()
    return new_change(args.key, args.source, args.author, args.source_reported_at)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
