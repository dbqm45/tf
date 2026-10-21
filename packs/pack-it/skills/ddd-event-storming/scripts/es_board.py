#!/usr/bin/env python3
"""
Tablica Event Storming prowadzonego przez agenta (skill ddd-event-storming). Tylko biblioteka standardowa, zero
tokenów: dziennik zdarzeń tablicy (z cofnięciem), kartki dozwolone w fazie, kontrola struktury fazy, zapis tablicy.

  es_board.py init --id <id> --topic "<temat>" [--question "<pytanie sesji>"]
  es_board.py add <typ> "<tekst>" --id <id> [--causes E1,E2] [--actor X] [--by S1] [--on E1] [--issues C1]
                                          [--for C1] [--at E1] [--handles C1,C2] [--contains A1] [--kind core]
                                          [--from K1 --to K2 --pattern customer-supplier] [--pivotal]
  es_board.py edit <kartka> --id <id> [tekst] [te same pola co add]
  es_board.py remove <kartka> --id <id>          es_board.py move <kartka> --after <kartka> --id <id>
  es_board.py resolve <hot spot> "<odpowiedź>" --id <id>
  es_board.py phase <1-5> --id <id>              es_board.py undo --id <id>
  es_board.py show --id <id>                      # Markdown (stdout i board.md) z diagramem Mermaid
  es_board.py check --id <id>                     # luki struktury bieżącej fazy; kod 1, gdy faza nie jest domknięta

Typy kartek i fazy (kartka późniejszej fazy jest odrzucana — mieszanie poziomów):
  1 kontekst sesji: actor, system, hotspot, opportunity · 2 zdarzenia: + event · 3 komendy i polityki: + command,
  policy, readmodel · 4 agregaty: + aggregate · 5 konteksty i mapa: + context, link
Katalog: $CLAUDE_PROJECT_DIR/docs/project/02-domain/event-storming/<id>/ (board.jsonl, board.md).
Struktura to warunek konieczny, nie wystarczający: treść (czas przeszły, język biznesu, sens agregatów) ocenia
człowiek i przegląd fazy (references/fazy-agenta.md).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

TYPES = {  # typ: (prefiks identyfikatora, faza, w której wolno go dodać)
    "actor": ("X", 1), "system": ("S", 1), "hotspot": ("H", 1), "opportunity": ("O", 1),
    "event": ("E", 2), "command": ("C", 3), "policy": ("P", 3), "readmodel": ("R", 3),
    "aggregate": ("A", 4), "context": ("K", 5), "link": ("L", 5),
}
PHASES = {1: "kontekst sesji", 2: "zdarzenia", 3: "komendy i polityki", 4: "agregaty", 5: "konteksty i mapa"}
KINDS = ("core", "supporting", "generic")
PATTERNS = ("customer-supplier", "conformist", "acl", "open-host-service", "published-language", "shared-kernel",
            "partnership", "separate-ways")
LIST_FIELDS = ("causes", "issues", "handles", "contains")   # listy identyfikatorów
REF_FIELDS = ("by", "on", "for", "at", "from", "to")        # pojedyncze identyfikatory
BIG_AGGREGATE = 7   # tyle komend w jednym agregacie to sygnał do podziału (małe agregaty)


class BoardError(Exception):
    pass


def board_dir(bid: str) -> Path:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    return root / "docs" / "project" / "02-domain" / "event-storming" / bid


def read_log(bid: str) -> list[dict]:
    p = board_dir(bid) / "board.jsonl"
    if not p.exists():
        raise BoardError(f"brak tablicy {bid} — zacznij od `init --id {bid}`")
    ops = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            ops.append(json.loads(line))
        except ValueError:
            raise BoardError(f"{p}:{n}: uszkodzona linia dziennika — popraw ją albo usuń") from None
    return ops


def append(bid: str, op: dict) -> None:
    p = board_dir(bid) / "board.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(op, ensure_ascii=False) + "\n")


def replay(ops: list[dict]) -> dict:
    """Stan tablicy z dziennika; `undo` cofa ostatnią wykonaną operację (poza init)."""
    applied: list[dict] = []
    for op in ops:
        if op["op"] == "undo":
            if applied and applied[-1]["op"] != "init":
                applied.pop()
        else:
            applied.append(op)
    state = {"meta": {}, "phase": 1, "notes": {}, "order": []}
    for op in applied:
        kind = op["op"]
        if kind == "init":
            state["meta"] = {k: op.get(k) for k in ("topic", "question")}
        elif kind == "phase":
            state["phase"] = op["n"]
        elif kind == "add":
            state["notes"][op["id"]] = {k: v for k, v in op.items() if k not in ("op",)}
            state["order"].append(op["id"])
        elif kind == "edit" and op["id"] in state["notes"]:
            state["notes"][op["id"]].update(op["fields"])
        elif kind == "remove":
            state["notes"].pop(op["id"], None)
            state["order"] = [i for i in state["order"] if i != op["id"]]
        elif kind == "move" and op["id"] in state["order"] and op["after"] in state["order"]:
            state["order"].remove(op["id"])
            state["order"].insert(state["order"].index(op["after"]) + 1, op["id"])
        elif kind == "resolve" and op["id"] in state["notes"]:
            state["notes"][op["id"]]["resolved"] = op["answer"]
    return state


def fields_from(a) -> dict:
    out = {}
    for f in LIST_FIELDS:
        v = getattr(a, f, None)
        if v is not None:
            out[f] = [x.strip() for x in v.split(",") if x.strip()]
    for f in REF_FIELDS + ("actor", "kind", "pattern"):
        v = getattr(a, f.replace("from", "from_"), None)
        if v is not None:
            out[f] = v
    if getattr(a, "pivotal", False):
        out["pivotal"] = True
    return out


def validate(fields: dict, state: dict) -> None:
    known = set(state["notes"])
    refs = [x for f in LIST_FIELDS for x in fields.get(f, [])] + [fields[f] for f in REF_FIELDS if f in fields]
    unknown = [r for r in refs if r not in known]
    if unknown:
        raise BoardError(f"nieznane kartki: {', '.join(unknown)}")
    if "kind" in fields and fields["kind"] not in KINDS:
        raise BoardError(f"typ subdomeny: {', '.join(KINDS)}")
    if "pattern" in fields and fields["pattern"] not in PATTERNS:
        raise BoardError(f"wzorzec mapy kontekstów: {', '.join(PATTERNS)} (skill ddd-context-mapping)")


def gaps(state: dict) -> tuple[list[str], list[str]]:
    """Luki (blokują zamknięcie fazy) i ostrzeżenia dla bieżącej fazy i wcześniejszych."""
    notes, phase = state["notes"], state["phase"]
    by_type = {t: [i for i in state["order"] if notes[i]["type"] == t] for t in TYPES}
    g, w = [], []
    if phase >= 3:
        caused = {e for c in by_type["command"] for e in notes[c].get("causes", [])}
        for e in by_type["event"]:
            if e not in caused and "by" not in notes[e]:
                g.append(f"{e} „{notes[e]['text']}”: zdarzenie bez wyzwalacza (komenda --causes albo --by system)")
        for c in by_type["command"]:
            if not notes[c].get("causes"):
                g.append(f"{c} „{notes[c]['text']}”: komenda bez zdarzenia (--causes)")
        for p in by_type["policy"]:
            if "on" not in notes[p] or not notes[p].get("issues"):
                g.append(f"{p} „{notes[p]['text']}”: polityka potrzebuje „kiedy” (--on) i „wtedy” (--issues)")
    if phase >= 4:
        handled = {c for a in by_type["aggregate"] for c in notes[a].get("handles", [])}
        for c in by_type["command"]:
            if c not in handled and "to" not in notes[c]:
                g.append(f"{c} „{notes[c]['text']}”: komenda bez agregatu (--handles) ani systemu (--to)")
        for a in by_type["aggregate"]:
            n = len(notes[a].get("handles", []))
            if not n:
                g.append(f"{a} „{notes[a]['text']}”: agregat bez komend")
            elif n > BIG_AGGREGATE:
                w.append(f"{a} „{notes[a]['text']}”: duży agregat ({n} komend) — sprawdź, co musi być spójne natychmiast")
    if phase >= 5:
        placed = {a for k in by_type["context"] for a in notes[k].get("contains", [])}
        for a in by_type["aggregate"]:
            if a not in placed:
                g.append(f"{a} „{notes[a]['text']}”: agregat poza kontekstem (--contains)")
        for k in by_type["context"]:
            if "kind" not in notes[k]:
                g.append(f"{k} „{notes[k]['text']}”: kontekst bez typu subdomeny (--kind {'|'.join(KINDS)})")
            if not notes[k].get("contains"):
                g.append(f"{k} „{notes[k]['text']}”: kontekst bez agregatów")
        for link in by_type["link"]:
            if not {"from", "to", "pattern"} <= set(notes[link]):
                g.append(f"{link}: relacja potrzebuje --from, --to i --pattern")
    open_hs = [h for h in by_type["hotspot"] if "resolved" not in notes[h]]
    if open_hs:
        w.append(f"otwarte hot spoty: {', '.join(open_hs)} — pytania do ludzi, nie do zgadywania")
    return g, w


def render(state: dict) -> str:
    notes, order = state["notes"], state["order"]
    t = lambda i: notes[i]["text"] if i in notes else i
    of = lambda typ: [i for i in order if notes[i]["type"] == typ]
    meta = state["meta"]
    out = [f"# Event Storming: {meta.get('topic') or '—'}", "",
           f"Pytanie sesji: {meta.get('question') or '—'} · Faza {state['phase']}: {PHASES[state['phase']]}", ""]
    out += ["## Oś czasu", "", "| # | Aktor/System | Komenda | Zdarzenie | Polityka | Read model | Agregat |",
            "|---|---|---|---|---|---|---|"]
    for n, e in enumerate(of("event"), 1):
        cmds = [c for c in of("command") if e in notes[c].get("causes", [])]
        who = [notes[c].get("actor", "") for c in cmds] + ([t(notes[e]["by"])] if "by" in notes[e] else [])
        pols = [p for p in of("policy") if notes[p].get("on") == e]
        rms = [r for r in of("readmodel") if notes[r].get("for") in cmds]
        aggs = [a for a in of("aggregate") if set(notes[a].get("handles", [])) & set(cmds)]
        star = " ★" if notes[e].get("pivotal") else ""
        row = [str(n), ", ".join(x for x in who if x), ", ".join(f"{c} {t(c)}" for c in cmds), f"{e} {t(e)}{star}",
               ", ".join(f"{p} {t(p)}" for p in pols), ", ".join(t(r) for r in rms), ", ".join(t(a) for a in aggs)]
        out.append("| " + " | ".join(row) + " |")
    if of("hotspot"):
        out += ["", "## Hot spoty", ""]
        for h in of("hotspot"):
            at = f" (przy {notes[h]['at']})" if "at" in notes[h] else ""
            ans = f" → {notes[h]['resolved']}" if "resolved" in notes[h] else ""
            out.append(f"- [{'x' if ans else ' '}] {h}: {t(h)}{at}{ans}")
    if of("opportunity"):
        out += ["", "## Szanse", ""] + [f"- {o}: {t(o)}" for o in of("opportunity")]
    if of("context"):
        out += ["", "## Konteksty", "", "| Kontekst | Typ subdomeny | Agregaty |", "|---|---|---|"]
        out += [f"| {k} {t(k)} | {notes[k].get('kind', '—')} | {', '.join(t(a) for a in notes[k].get('contains', []))} |"
                for k in of("context")]
    if of("link"):
        out += ["", "## Mapa kontekstów", "", "| Z (upstream) | Do (downstream) | Wzorzec | Opis |", "|---|---|---|---|"]
        out += [f"| {t(notes[x].get('from', '?'))} | {t(notes[x].get('to', '?'))} | {notes[x].get('pattern', '—')} | "
                f"{t(x)} |" for x in of("link")]
    flow = []
    for c in of("command"):
        flow += [f"  {c}[/{t(c)}/]:::cmd --> {e}([{t(e)}]):::evt" for e in notes[c].get("causes", []) if e in notes]
    for p in of("policy"):
        if notes[p].get("on") in notes:
            flow.append(f"  {notes[p]['on']} --> {p}{{{{{t(p)}}}}}:::pol")
        flow += [f"  {p} --> {c}" for c in notes[p].get("issues", []) if c in notes]
    if flow:
        out += ["", "## Diagram", "", "```mermaid", "flowchart LR", *flow,
                "  classDef evt fill:#f9a03f,color:#000", "  classDef cmd fill:#7ab8f5,color:#000",
                "  classDef pol fill:#c8a2e8,color:#000", "```"]
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("init", "add", "edit", "remove", "move", "resolve", "phase", "undo", "show", "check"))
    ap.add_argument("args", nargs="*")
    ap.add_argument("--id", required=True)
    for f in ("topic", "question", "causes", "actor", "by", "on", "issues", "for", "at", "handles", "contains", "kind",
              "to", "pattern", "after"):
        ap.add_argument(f"--{f}")
    ap.add_argument("--from", dest="from_")
    ap.add_argument("--pivotal", action="store_true")
    a = ap.parse_args(argv[1:])
    if a.cmd == "init":
        if (board_dir(a.id) / "board.jsonl").exists():
            raise BoardError(f"tablica {a.id} już istnieje")
        append(a.id, {"op": "init", "topic": a.topic, "question": a.question})
        print(f"✓ {board_dir(a.id) / 'board.jsonl'} · faza 1: {PHASES[1]}")
        return 0
    state = replay(read_log(a.id))
    if a.cmd == "add":
        if len(a.args) != 2 or a.args[0] not in TYPES:
            raise BoardError(f"add <typ> \"<tekst>\"; typy: {', '.join(TYPES)}")
        typ, text = a.args
        prefix, need = TYPES[typ]
        if need > state["phase"]:
            raise BoardError(f"kartka „{typ}” należy do fazy {need} ({PHASES[need]}), a trwa faza {state['phase']} — "
                             f"przejdź dalej (`phase {need}`) albo zapisz to jako hot spot")
        fields = fields_from(a)
        validate(fields, state)
        n = 1 + max([int(i[1:]) for i in state["notes"] if i[0] == prefix and i[1:].isdigit()] +
                    [int(o["id"][1:]) for o in read_log(a.id) if o.get("op") == "add" and o["id"][0] == prefix] + [0])
        nid = f"{prefix}{n}"
        append(a.id, {"op": "add", "id": nid, "type": typ, "text": text, **fields})
        print(nid)
        return 0
    if a.cmd in ("edit", "remove", "move", "resolve"):
        if not a.args or a.args[0] not in state["notes"]:
            raise BoardError(f"nieznana kartka: {a.args[0] if a.args else '—'}")
        nid = a.args[0]
        if a.cmd == "edit":
            fields = fields_from(a)
            validate(fields, state)
            if len(a.args) > 1:
                fields["text"] = a.args[1]
            append(a.id, {"op": "edit", "id": nid, "fields": fields})
        elif a.cmd == "remove":
            append(a.id, {"op": "remove", "id": nid})
        elif a.cmd == "move":
            if a.after not in state["notes"]:
                raise BoardError(f"move {nid} --after <kartka>: nieznana kartka {a.after}")
            append(a.id, {"op": "move", "id": nid, "after": a.after})
        else:
            if state["notes"][nid]["type"] != "hotspot" or len(a.args) != 2:
                raise BoardError("resolve <hot spot> \"<odpowiedź>\"")
            append(a.id, {"op": "resolve", "id": nid, "answer": a.args[1]})
        print(f"✓ {a.cmd} {nid}")
        return 0
    if a.cmd == "phase":
        n = int(a.args[0]) if a.args and a.args[0].isdigit() else 0
        if n not in PHASES:
            raise BoardError("phase <1-5>")
        append(a.id, {"op": "phase", "n": n})
        print(f"✓ faza {n}: {PHASES[n]}")
        return 0
    if a.cmd == "undo":
        append(a.id, {"op": "undo"})
        print("✓ cofnięto ostatnią zmianę")
        return 0
    if a.cmd == "show":
        md = render(state)
        (board_dir(a.id) / "board.md").write_text(md, encoding="utf-8")
        sys.stdout.write(md)
        return 0
    g, w = gaps(state)
    for line in g:
        print(f"✗ {line}")
    for line in w:
        print(f"⚠ {line}")
    print(f"{'✓' if not g else '✗'} faza {state['phase']} ({PHASES[state['phase']]}): luk {len(g)}, ostrzeżeń {len(w)}")
    return 1 if g else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except BoardError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(2)
