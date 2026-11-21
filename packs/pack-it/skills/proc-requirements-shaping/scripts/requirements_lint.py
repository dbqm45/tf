#!/usr/bin/env python3
"""
Requirements (PRD) check before saving — skill proc-requirements-shaping. Reads files only, no network.

  python3 requirements_lint.py docs/project/03-requirements/requirements.md [--brief docs/project/01-discovery/brief.md] [--json] [--strict]
  python3 requirements_lint.py --story story.md [--ac-format gwt|ears|any|off] [--json] [--strict]

It checks:
  1. Readiness (0–4 points): there are `FR-NNN` requirements; there is at least one Given/When/Then story
     (or Zakładając/Gdy/Wtedy); the "Business rule" section starts with one sentence (≤ 200 characters, with a period,
     no TODO); the "Out of scope" section has at least one item. A score < 2 → a warning with the list of gaps.
  2. Technology leaking into requirements: vendors and technologies, data schema, place of execution, mechanism, protocol,
     interface elements in quality requirements. Skipped sections: "Current system", "Constraints…",
     "For the stack decision", "Open questions", "Handoff" (technical names are allowed there).
  3. (with --brief) The "MVP too big" threshold = the time budget from the brief, not a constant. The brief contains the lines:
       - MVP time budget: 3 weeks
       - MVP flow estimate: 5 weeks
       - Cost acknowledged: 2026-10-10, <who> accepts <how much>     (only when the estimate > the budget)
     Units: days (working), weeks (= 5 days), months (= 21 days) — give both values in the same convention.
  4. The shape of every US-NN story (a `### US-NN: title` block with `- AC-n:` scenarios or a table row
     `| US-NN | story | criteria |`) — pdi 0.4.0 contract rules, keywords from story_shape_vocabulary.json:
       AC-001 a scenario without Then/Wtedy or a criterion outside the format (default GWT) · AC-002 a weak outcome
       ("poprawnie", "działa") · AC-003 an implementation detail · AC-004 a second action in a scenario ·
       STORY-001 several actions (a conjunction between verbs in the title or goal, several actors, different main actions
       in scenarios) · STORY-002 too big (scenarios > 6 or actions > 3; without an estimate) · STORY-003 a title by
       layer (BE:, API:, migration) · AC-ID (tf) a block without AC-n identifiers.
     A table, column and endpoint in requirements (AC-003, new in the contract) — a warning.
  `--story` checks a single story from a file (`# title`, "Jako … chcę …", criteria) and prints the main actions.

Exit code: 0 — no blocking problems (warnings possible); 1 — technology leak or an estimate over budget
without a recorded cost acknowledgement, and with --strict also every story-shape warning; 2 — input error
(no file). Python 3.9+ standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

RULE_MAX = 200
SKIP_SECTIONS = ("current system", "constraints", "for the stack decision", "open questions", "handoff")

# (category, pattern, case-sensitive, quality sections only)
LEAK_PATTERNS = [
    ("dostawca", r"\b(Stripe|Supabase|Vercel|Cloudflare|AWS|Azure|GCP|Google Cloud|Firebase|OpenAI|Anthropic|Netlify|"
                 r"Heroku|PostgreSQL|Postgres|MySQL|MongoDB|Redis|Kafka|RabbitMQ|Elasticsearch|React|Angular|Vue|"
                 r"Next\.js|Django|Spring|Laravel|Rails|Auth0|Clerk|Twilio|SendGrid|Resend|S3)\w*", True, False),
    ("schemat danych", r"\(FK\)|\bFK\b|\bnullable\b|\b\w+_hash\b|\bsoft[- ]?delete\w*|\bmigracj\w*|\bmigration\w*|"
                       r"\bklucz\w* obc\w*|\bVARCHAR\b|\bforeign key\b", False, False),
    ("miejsce wykonania", r"\bpo stronie (serwera|klienta|przeglądarki|backendu|frontendu)\b|\bserver[- ]side\b|"
                          r"\bclient[- ]side\b|\bna edge\w*|\bw cache\w*|\bw pamięci podręcznej\b", False, False),
    ("mechanizm", r"\bper IP\b|\btoken bucket\b|\bsliding window\b|\bJWT\b|\bcron\w*", False, False),
    ("protokół", r"\b(WebSocket\w*|gRPC|GraphQL|webhook\w*|SSE|REST|MQTT)\b", True, False),
    ("interfejs", r"\b(spinner\w*|toast\w*|modal\w*|popup\w*|snackbar\w*)", False, True),
]

VOCABULARY = Path(__file__).resolve().parent / "story_shape_vocabulary.json"   # kopia vocabulary.json kontraktu pdi
DEFAULT_POLICY = {"acFormat": "gwt", "maxScenarios": 6, "maxActions": 3}
AC_ID = re.compile(r"^(?:[-*•]\s*)?(?:\*\*)?(AC-\d+)(?:\*\*)?\s*[:.)—–-]\s*")
BULLET = re.compile(r"^[-*•]\s+")
AC_LABEL = re.compile(r"^(?:#{1,6}\s*)?(kryteria akceptacji|acceptance criteria)\b.*$", re.I)
# the "Jako … chcę" sentence need not open the description (the description is lines joined with a space): a task's ticket.md starts with the
# source line (the /tf-task loop), so the actor may also come after the end of the previous sentence
ACTOR = re.compile(r"(?:^\s*|(?<=[.!?]\s))(?:jako|as an?|as)\s+(.+?)\s+(?:chcę|chciał\w*|i want|i would like|i'd like)\b", re.I)
GOAL = re.compile(r"\b(?:chcę|chciał\w*(?: bym)?|i want to|i would like to|i'd like to|i want)\s+(.*)", re.I | re.S)
PURPOSE = re.compile(r",?\s+(?:aby|żeby|by|so that|in order to)\b", re.I)
DETERMINERS = {"the", "a", "an", "my", "your", "his", "her", "its", "our", "their", "this", "that", "these", "those",
               "all", "some", "any", "every", "each", "no"}
SUBJECTS = DETERMINERS | {"i", "we", "you", "he", "she", "it", "they", "user", "customer", "system",
                          "użytkownik", "klient", "system", "się"}
FILLERS = DETERMINERS | {"to", "do", "na", "w", "we", "z", "ze", "o", "for", "with", "of", "on", "in", "into",
                         "it", "them", "ją", "go", "je", "jej", "jego", "ich", "swój", "swoją", "swoje", "is", "are"}
UNIT_DAYS = [(r"^day", 1.0), (r"^week|^wk", 5.0), (r"^month", 21.0)]


def sections(text: str):
    """Returns a list of (line_number, section_heading_lowercase, line), skipping the frontmatter and code blocks."""
    out, heading, in_code, in_front = [], "", False, False
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        if i == 1 and line.strip() == "---":
            in_front = True
            continue
        if in_front:
            if line.strip() == "---":
                in_front = False
            continue
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if m:
            heading = m.group(1).strip().lower()
            continue
        out.append((i, heading, line))
    return out


def section_lines(rows, needle: str):
    return [(n, l) for n, h, l in rows if needle in h]


def is_placeholder(line: str) -> bool:
    s = line.strip().lstrip("-*").strip()
    return not s or s.startswith("<") or s in ("…", "...") or s.startswith("<!--")


def readiness(text: str, rows) -> dict:
    missing = []
    if not re.search(r"\bFR-\d{3}\b", text):
        missing.append("FR-NNN requirements (\"FR-001: [actor] can [capability]. Priority: must|nice\")")
    kw = vocabulary()["keywords"]
    alt = {k: _alt({w for lang in ("en", "pl") for w in kw[lang][k] if len(w) > 1}) for k in ("given", "when", "then")}
    one_line = re.compile(rf"\b({alt['given']})\b.*\b({alt['when']})\b.*\b({alt['then']})\b", re.I)
    gwt = any(one_line.search(l) for _, _, l in rows) or any(
        u["kind"] == "gwt" and u["then"] and u["action"] for s in file_stories(text) for u in ac_units(s["ac"]))
    if not gwt:
        missing.append("a story with Given/When/Then criteria for the main flow")
    rule = [l.strip() for _, l in section_lines(rows, "business rule") if l.strip() and not is_placeholder(l)]
    first = rule[0] if rule else ""
    one_sentence = (first and len(first) <= RULE_MAX and first.endswith(".") and "TODO" not in first.upper()
                    and not re.search(r"[.!?]\s+[A-ZĄĆĘŁŃÓŚŹŻ]", first[:-1]))
    if not one_sentence:
        missing.append(f"\"Business rule\" in one sentence (≤ {RULE_MAX} characters, ending with a period, no TODO)")
    out_of_scope = [l for _, l in section_lines(rows, "out of scope") if re.match(r"\s*[-*]\s+\S", l) and not is_placeholder(l)]
    out_of_scope += [l for _, _, l in rows if re.match(r"\s*[-*]\s*out of scope\s*:\s*[^…<\s]", l, re.I)]
    if not out_of_scope:
        missing.append("\"Out of scope\" with at least one item")
    score = 4 - len(missing)
    return {"score": score, "max": 4, "missing": missing, "warning": score < 2}


def leaks(rows) -> list:
    found = []
    for n, heading, line in rows:
        if any(s in heading for s in SKIP_SECTIONS):
            continue
        quality = "quality" in heading
        for cat, pat, case, only_quality in LEAK_PATTERNS:
            if only_quality and not quality:
                continue
            for m in re.finditer(pat, line, 0 if case else re.I):
                found.append({"rule": "AC-003", "line": n, "category": cat, "match": m.group(0), "text": line.strip()[:160]})
    return found


def to_days(value: str, unit: str):
    num = float(value.replace(",", "."))
    for pat, mult in UNIT_DAYS:
        if re.match(pat, unit.lower()):
            return num * mult
    return None


def mvp_check(brief_text: str) -> dict:
    def find(label):
        m = re.search(label + r"[^:\n]*:\s*(\d+(?:[.,]\d+)?)\s*([A-Za-ząćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)", brief_text, re.I)
        return to_days(m.group(1), m.group(2)) if m else None

    budget = find(r"time budget")
    estimate = find(r"estimate")
    ack = bool(re.search(r"cost acknowledged\s*:\s*[^\s<…]", brief_text, re.I))
    res = {"budget_days": budget, "estimate_days": estimate, "too_big": None, "acknowledged": ack, "warning": None}
    if budget is None:
        res["warning"] = "the brief has no MVP time budget — agree on it with the human (\"MVP time budget: N weeks\")"
    elif estimate is None:
        res["warning"] = "the brief has no MVP flow estimate — add \"MVP flow estimate: …\""
    else:
        res["too_big"] = estimate > budget
    return res


# --- story shape (pdi contract rules: AC-001…004, STORY-001…003) ---

@lru_cache(maxsize=1)
def vocabulary() -> dict:
    return json.loads(VOCABULARY.read_text(encoding="utf-8"))


def _words(kind: str, en_only: bool) -> list:
    kw = vocabulary()["keywords"]
    langs = ["en"] if en_only else ["en", "pl"]
    return sorted({w for lang in langs for w in kw[lang][kind]}, key=len, reverse=True)


def _alt(words) -> str:
    return "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))


def keyword(line: str, en_only: bool):
    """A GWT keyword at the start of a line → (kind, rest). The single-letter "I" only in upper case."""
    for kind in ("given", "when", "then", "and", "but"):
        for w in _words(kind, en_only):
            head = line[:len(w)]
            if (head == w if len(w) == 1 else head.lower() == w.lower()) and \
                    (len(line) == len(w) or not line[len(w)].isalnum()):
                return kind, line[len(w):].lstrip(" ,:")
    return None, line


def _inline():
    kw = vocabulary()["keywords"]
    lower = lambda kind: {w.lower() for lang in ("en", "pl") for w in kw[lang][kind]}
    when = _alt(lower("when"))
    return (re.compile(rf"\b({when})\b", re.I), re.compile(rf"\b({_alt(lower('then'))})\b", re.I),
            re.compile(rf"\b({_alt(lower('and'))})\s+({when})\b", re.I))


def ac_units(ac: str) -> list:
    """AC units per the pdi set README: a GWT scenario from Given (or When) to the end of the Then block; an EARS sentence;
    a list item with free text. A blank line and an `AC-n` identifier start a new unit."""
    when_in, then_in, second_in = _inline()
    lines = (ac or "").replace("<br>", "\n").splitlines()
    en_only = any(keyword(BULLET.sub("", AC_ID.sub("", l.strip())), True)[0] for l in lines)
    units, cur = [], None

    def close():
        nonlocal cur
        if cur:
            units.append(cur)
        cur = None

    def act(u, text):   # the When step (also on one line: „Gdy … i gdy …, wtedy …”)
        s, t = second_in.search(text), then_in.search(text)
        if u["action"] is None:
            u["action"] = text[:min(m.start() for m in (s, t) if m)] if s or t else text
        else:
            u["second_action"] = True
        if s and (not t or s.start() < t.start()):
            u["second_action"] = True
        u["phase"] = "then" if t else "when"
        u["then"] = u["then"] or bool(t)

    for raw in lines:
        line = raw.strip()
        if not line or AC_LABEL.match(line):
            close()
            continue
        m = AC_ID.match(line)
        ac_id = m.group(1) if m else None
        if m:
            close()
            line = line[m.end():].strip()
        bullet = bool(not m and BULLET.match(line))
        line = BULLET.sub("", line)
        kind, rest = keyword(line, en_only)
        new = lambda k: {"kind": k, "id": ac_id, "text": line, "action": None, "second_action": False,
                         "then": False, "phase": None}
        if re.search(r"\bshall\b", line, re.I) and kind in (None, "given", "when") and not then_in.search(rest):
            close()
            units.append(new("ears"))
            continue
        if kind is None:
            if cur and not bullet and not ac_id:
                cur["text"] += " " + line
            else:
                close()
                cur = new("free")
            continue
        if kind in ("given", "when") and (bullet or cur is None or cur["kind"] != "gwt" or cur["phase"] == "then"
                                          or (kind == "given" and cur["phase"] == "when")):
            close()
            cur = new("gwt")
        elif cur is None:
            cur = new("gwt")
        else:
            cur["text"] += " " + line
        if kind == "given":
            cur["phase"] = "given"
            w = when_in.search(rest)
            if w:
                act(cur, rest[w.end():].lstrip(" ,"))
            elif then_in.search(rest):
                cur["phase"], cur["then"] = "then", True
        elif kind == "when":
            act(cur, rest)
        elif kind == "then":
            cur["phase"], cur["then"] = "then", True
        elif kind == "and" and cur["phase"] == "when" and cur["kind"] == "gwt":
            cur["second_action"] = True
    close()
    return units


def _tokens(text: str) -> list:
    return re.findall(r"[^\W\d_][\w'’-]*|,", text)


def actor_of(description: str) -> str:
    m = ACTOR.search(description or "")
    return m.group(1).strip() if m else ""


def action_key(text: str, actor_words: set):
    """Action = a verb + object from the When step (without the subject and data variants); the key compares stems."""
    words = [w.lower() for w in _tokens(text) if w != ","]
    while words and (words[0] in SUBJECTS or words[0] in actor_words):
        words.pop(0)
    if not words:
        return None
    verb = words[0]
    obj = next((w for w in words[1:] if w not in FILLERS), "")
    return f"{verb[:4]} {obj[:4]}", f"{verb} {obj}".strip()


def _conj_chain(tokens: list, i: int, conj: set) -> bool:
    """From position i: word (, word)* conjunction word — an enumeration of verbs, e.g. „dodać, edytować i usunąć” (add, edit and delete)."""
    j = i
    while j + 2 < len(tokens) and tokens[j] != ",":
        nxt, after = tokens[j + 1].lower(), tokens[j + 2]
        if after == ",":
            return False
        if nxt == ",":
            j += 2
            continue
        return nxt in conj and after.lower() not in DETERMINERS
    return False


def mixing_signals(title: str, description: str) -> list:
    """STORY-001 signals in the title and goal: a conjunction between verbs, a slash between words, several actors."""
    v = vocabulary()["action_conjunctions"]
    conj = {c.lower() for c in v["pl"] + v["en"]}
    out = []
    goal_m = GOAL.search(description or "")
    goal = PURPOSE.split(goal_m.group(1) if goal_m else (description or ""), 1)[0]
    tt, gt = _tokens(title or ""), _tokens(goal)
    tw = [k for k, t in enumerate(tt) if t != ","][:2]
    if any(_conj_chain(tt, k, conj) for k in tw):
        out.append(f"title joins actions with a conjunction: \"{title}\"")
    if gt and (_conj_chain(gt, 0, conj) or any(
            t.lower() in v["pl"] and k + 1 < len(gt) and gt[k + 1].lower().endswith("ć") for k, t in enumerate(gt))):
        out.append(f"goal joins actions with a conjunction: \"{goal.strip()}\"")
    if v.get("slash_between_words"):
        for where, text in (("title", title or ""), ("goal", goal)):
            m = re.search(r"(?<![\w/])[^\W\d_]+/[^\W\d_]+(?![\w/])", text)
            if m:
                out.append(f"{where} joins actions with a slash: \"{m.group(0)}\"")
                break
    actor = actor_of(description)
    if actor and (re.search(r"\b(" + "|".join(map(re.escape, conj)) + r")\b", actor, re.I) or "," in actor or "/" in actor):
        out.append(f"several actors: \"{actor}\"")
    return out


def check_story(title: str, description: str, ac: str, story_points=None, policy=None) -> dict:
    """The shape of a single story. story_points accepted but not evaluated (STORY-002 in tf without an estimate)."""
    pol = {**DEFAULT_POLICY, **(policy or {})}
    voc = vocabulary()
    units = ac_units(ac)
    text = ac or ""
    actor_words = {w.lower() for w in _tokens(actor_of(description)) if w != ","}
    actions = {}
    for u in units:
        if u["kind"] == "gwt" and u["action"]:
            key = action_key(u["action"], actor_words)
            if key:
                actions.setdefault(key[0], key[1])
    findings = []

    def add(rule, msg):
        findings.append({"rule": rule, "message": msg})

    fmt = pol.get("acFormat", "gwt")
    if units and fmt in ("gwt", "ears"):
        bad = [u for u in units if not ((u["kind"] == "gwt" and u["then"]) if fmt == "gwt" else u["kind"] == "ears")]
        if bad:
            what = "scenario without Then/Wtedy, or a criterion outside the GWT format" if fmt == "gwt" else "criterion outside the EARS format"
            add("AC-001", f"{what}: " + "; ".join(f"\"{(u['id'] + ': ') if u['id'] else ''}{u['text'][:60]}\"" for u in bad))
    weak = sorted({w for lang in ("pl", "en") for w in voc["weak_results"][lang] if w.lower() in text.lower()})
    if weak:
        add("AC-002", "weak result instead of an observable one: " + ", ".join(f"\"{w}\"" for w in weak))
    impl = [(t["category"], m.group(0)) for t in voc["implementation_terms"]
            for m in [re.search(t["pattern"], text, 0 if t["case_sensitive"] else re.I)] if m]
    if impl:
        add("AC-003", "implementation detail in the criteria: " + ", ".join(f"{c} \"{m}\"" for c, m in impl))
    second = [u for u in units if u["second_action"]]
    if second:
        add("AC-004", "second action in a scenario: " + "; ".join(f"\"{u['text'][:60]}\"" for u in second))
    signals = mixing_signals(title, description)
    if len(actions) >= 2:
        signals.append("different main actions across scenarios: " + ", ".join(actions.values()))
    if signals:
        add("STORY-001", "the story mixes features — " + "; ".join(signals))
    big = []
    if len(units) > pol["maxScenarios"]:
        big.append(f"scenarios {len(units)} > {pol['maxScenarios']}")
    if len(actions) > pol["maxActions"]:
        big.append(f"actions {len(actions)} > {pol['maxActions']}")
    if big:
        add("STORY-002", "too big: " + ", ".join(big))
    lt = voc["layer_terms"]
    layer = [w.rstrip(":") for w in (title or "").split()
             if w.rstrip(":") in lt["case_sensitive"] or w.rstrip(":").lower() in {x.lower() for x in lt["case_insensitive"]}]
    if layer:
        add("STORY-003", "title names a technical layer instead of user value: " + ", ".join(f"\"{w}\"" for w in layer))
    return {"scenarios": len(units), "actions": list(actions.values()), "findings": findings,
            "ac_ids": [u["id"] for u in units], "story_points": story_points}


STORY_HEAD = re.compile(r"^#{2,6}\s+(US-\d+)\s*[:.—–-]?\s*(.*)$")
TABLE_STORY = re.compile(r"^\s*\|\s*(US-\d+)\s*\|")


def split_story(lines: list):
    """Story content → (description, criteria): the description up to the first criterion line (AC-n, a list item, a GWT word, a label)."""
    desc, ac, in_ac = [], [], False
    for l in lines:
        s = l.strip()
        if not in_ac and (AC_LABEL.match(s) or AC_ID.match(s) or BULLET.match(s) or keyword(s, False)[0]):
            in_ac = True
            if AC_LABEL.match(s):
                continue
        (ac if in_ac else desc).append(l)
    return " ".join(x.strip() for x in desc if x.strip() and not x.lstrip().startswith("#")), "\n".join(ac)


def file_stories(text: str) -> list:
    """US-NN stories from requirements.md: `### US-NN: title` blocks and table rows `| US-NN | story | criteria |`."""
    out, cur, in_code = [], None, False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
        if in_code:
            continue
        m = STORY_HEAD.match(line)
        if m or re.match(r"^#{1,6}\s", line):
            if cur:
                out.append(cur)
            cur = {"id": m.group(1), "title": m.group(2).strip(), "line": n, "body": [], "block": True} if m else None
            continue
        t = TABLE_STORY.match(line)
        if t:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            story = cells[1] if len(cells) > 1 else ""
            out.append({"id": t.group(1), "title": story, "description": story, "line": n, "block": False,
                        "ac": cells[2] if len(cells) > 2 else ""})
            continue
        if cur:
            cur["body"].append(line)
    if cur:
        out.append(cur)
    for s in out:
        if s.get("block"):
            s["description"], s["ac"] = split_story(s.pop("body"))
    return sorted(out, key=lambda s: s["line"])


def lint_file_stories(text: str, policy=None) -> list:
    res = []
    for s in file_stories(text):
        r = check_story(s["title"], s["description"], s["ac"], None, policy)
        r["findings"] = [f for f in r["findings"] if f["rule"] != "AC-003"]   # AC-003 in a file: the leak scan
        if s["block"] and r["scenarios"] and not all(r["ac_ids"]):
            r["findings"].append({"rule": "AC-ID", "message": "scenarios without AC-n identifiers (e.g. \"- AC-1: Given …\")"})
        res.append({"id": s["id"], "line": s["line"], "title": s["title"], **r})
    return res


def new_leak_warnings(rows) -> list:
    """AC-003: categories new in the contract (e.g. table, column, endpoint) — a warning, not a block."""
    known = {c for c, *_ in LEAK_PATTERNS}
    found = []
    for n, heading, line in rows:
        if any(s in heading for s in SKIP_SECTIONS):
            continue
        for t in vocabulary()["implementation_terms"]:
            if t["category"] in known:
                continue
            for m in re.finditer(t["pattern"], line, 0 if t["case_sensitive"] else re.I):
                found.append({"rule": "AC-003", "line": n, "category": t["category"], "match": m.group(0),
                              "text": line.strip()[:160]})
    return found


def read_story(text: str):
    lines = text.splitlines()
    title = ""
    for k, l in enumerate(lines):
        if l.strip():
            title = re.sub(r"^#+\s*", "", l.strip())
            lines = lines[k + 1:]
            break
    desc, ac = split_story(lines)
    return title, desc, ac


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Requirements check (PRD): readiness, technology leaks, MVP threshold from the brief, "
                                             "story shape (GWT, one action, AC identifiers).")
    ap.add_argument("requirements", nargs="?", help="requirements file, e.g. docs/project/03-requirements/requirements.md")
    ap.add_argument("--brief", help="brief with the MVP time budget (the \"MVP too big\" threshold)")
    ap.add_argument("--story", help="a single story from a file (`# title`, \"As … I want …\", acceptance criteria)")
    ap.add_argument("--ac-format", choices=["gwt", "ears", "any", "off"], default="gwt", help="criteria format (AC-001)")
    ap.add_argument("--max-scenarios", type=int, default=DEFAULT_POLICY["maxScenarios"], help="STORY-002 threshold")
    ap.add_argument("--max-actions", type=int, default=DEFAULT_POLICY["maxActions"], help="STORY-002 threshold")
    ap.add_argument("--strict", action="store_true", help="story shape warnings exit with code 1")
    ap.add_argument("--json", action="store_true", help="output as JSON")
    a = ap.parse_args(argv)
    policy = {"acFormat": a.ac_format, "maxScenarios": a.max_scenarios, "maxActions": a.max_actions}
    if a.story:
        return story_main(a, policy)
    if not a.requirements:
        ap.print_usage(sys.stderr)
        print("✗ give a requirements file or --story FILE", file=sys.stderr)
        return 2

    path = Path(a.requirements)
    try:
        text = path.read_text(encoding="utf-8")
        brief_text = Path(a.brief).read_text(encoding="utf-8") if a.brief else None
    except OSError as e:
        print(f"✗ cannot read the file: {e}", file=sys.stderr)
        return 2

    rows = sections(text)
    result = {"file": str(path), "readiness": readiness(text, rows), "leaks": leaks(rows),
              "warnings": new_leak_warnings(rows), "stories": lint_file_stories(text, policy)}
    if brief_text is not None:
        result["mvp"] = mvp_check(brief_text)
    mvp = result.get("mvp") or {}
    blocking = bool(result["leaks"]) or (mvp.get("too_big") is True and not mvp.get("acknowledged"))
    result["ok"] = not blocking
    n_warn = len(result["warnings"]) + sum(len(s["findings"]) for s in result["stories"])

    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        rd = result["readiness"]
        print(f"Readiness: {rd['score']}/{rd['max']}" + (" — warning" if rd["warning"] else ""))
        for m in rd["missing"]:
            print(f"  · missing: {m}")
        for l in result["leaks"]:
            print(f"{path}:{l['line']} — AC-003 {l['category']}: \"{l['match']}\" → describe behaviour visible from outside "
                  f"or move it to \"For the stack decision\"")
        for w in result["warnings"]:
            print(f"{path}:{w['line']} — ⚠ AC-003 {w['category']}: \"{w['match']}\" → describe behaviour visible from outside")
        for st in result["stories"]:
            for f in st["findings"]:
                print(f"{path}:{st['line']} — ⚠ {st['id']} {f['rule']}: {f['message']}")
        if mvp:
            if mvp["warning"]:
                print(f"MVP: ⚠ {mvp['warning']}")
            elif mvp["too_big"]:
                state = "cost acknowledged" if mvp["acknowledged"] else "cost NOT acknowledged — propose cuts"
                print(f"MVP: estimate {mvp['estimate_days']:g} days > budget {mvp['budget_days']:g} days — {state}")
            else:
                print(f"MVP: estimate {mvp['estimate_days']:g} days fits the budget of {mvp['budget_days']:g} days")
        print("✓ no blocking problems" if result["ok"] else "✗ there are blocking problems")
        if n_warn:
            print(f"⚠ story shape warnings: {n_warn}" + (" — --strict: exit code 1" if a.strict else ""))
    return 1 if blocking or (a.strict and n_warn) else 0


def story_main(a, policy) -> int:
    try:
        text = Path(a.story).read_text(encoding="utf-8")
    except OSError as e:
        print(f"✗ cannot read the file: {e}", file=sys.stderr)
        return 2
    title, desc, ac = read_story(text)
    r = check_story(title, desc, ac, None, policy)
    if a.json:
        print(json.dumps({"file": a.story, "story": {"title": title, **r}, "ok": not r["findings"]},
                         ensure_ascii=False, indent=2))
    else:
        print(f"Story: {title} — scenarios: {r['scenarios']}, main actions: {', '.join(r['actions']) or '—'}")
        for f in r["findings"]:
            print(f"⚠ {f['rule']}: {f['message']}")
        if any(f["rule"] == "STORY-001" for f in r["findings"]) and len(r["actions"]) >= 2:
            print("Suggested split: one story per action — " + " · ".join(r["actions"]))
        print("✓ story shape has no remarks" if not r["findings"] else f"⚠ remarks: {len(r['findings'])}")
    return 1 if a.strict and r["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
