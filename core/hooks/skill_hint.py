#!/usr/bin/env python3
"""
UserPromptSubmit hook: suggests to the model 1–3 factory skills matching the user's prompt.

Why: Claude Code keeps skill descriptions in ~1% of the context window. With a 200k-token window (e.g. Haiku) the factory
skill descriptions drop out of the list and the model sees names only, and even with full descriptions the model often answers from general knowledge,
without loading the skill (measurement: tests/run_skill_evals.py). The hook matches the prompt to skill descriptions (description
and metadata.catalog) by simple word-stem matching weighted by rarity, and appends a short hint to the context.

  python3 .claude/hooks/skill_hint.py --explain "Jak zrobić paginację GET /orders?"   # ranking with scores

In a project with a detected stack (detect_stack) the hook skips framework and language skills (`fw-`, `lang-`) that
the project does not have, unless the prompt mentions them; to disable the filter: CLAUDE_SKILL_HINT_STACK=0.

Disable: the variable CLAUDE_SKILL_HINT=0. Standard library only; an error never blocks the command.

Log: each decision goes to .tf/logs/skill-hints.jsonl (time, session, suggested skills, the 5 highest-
scored with their score). The prompt content is NOT recorded — unless CLAUDE_SKILL_HINT_LOG_PROMPT=1 (the first 200
characters, for tuning keywords on your own machine). Report: python3 .tf/factory/hint_report.py
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record as record_error  # hook error to .tf/logs/hook-errors.jsonl (tf doctor)
except ImportError:  # older install without the log module — the hook works as before
    def record_error(hook: str, exc: BaseException) -> None:
        return None

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

_PROJECT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
SKILLS = _PROJECT / ".claude" / "skills"
PLUGIN_SKILLS = _PROJECT / ".tf" / "plugin" / "skills"   # factory mode: the factory's skills live in the plugin
STEM = 5                  # stem length: Polish inflection mostly changes the endings
MIN_SCORE = 8.0           # relevance threshold (tuned on the scenarios in tests/skill_evals)
MAX_HINTS = 3
CLEAR_SCORE = 16.0          # clear leader: a score of at least this …
CLEAR_LEAD = 1.3            # … and 30% better than the second skill → a stronger hint (calibration: 176 correct, 2 wrong on 283 scenarios)
STRONG_SCORE = 12.0       # above this score the leader need not stand out from the second
MARGIN = 1.15             # otherwise the leader must be 15% better than the second skill
RATIO = 0.6               # we suggest only skills close to the best score
BODY_NORM = 0.5           # normalization of the body score by its length (measured on tests/skill_evals)
HEAD_WEIGHT = 2.0         # a word from the skill description weighs more than a word from the SKILL.md body
STOP = set("""
aby albo ale bez być będzie bo by czy dla do gdy go i ich ile im jak jaki jakie jako je jest jeśli już kiedy który
która które ma mam mamy może można mnie na nad nam nas nie niż o od oraz po pod przez przy się są ta tak także te
też to tu tym w we więc z za ze że żeby co ten tej tego temu tych tę ja ty my wy on ona ono oni one mój nasz wasz
odpowiedz zwięźle krótko proszę chcę chcemy potrzebuję jak zrobić czy warto użyj nie do robi robić the and for with how what
""".split())
NEG_RE = re.compile(r"\b(Nie do|Not for)\b.*$", re.S)


# Names of tools that are stop words in Polish („Jest” = the tool, „jest” = the verb "is"). A capital letter
# mid-sentence, or a name with a version/dot, means the tool.
TOOL_ALIASES = [(re.compile(r"(?<=[^.!?\s] )Jest\b|\bJest(?=\s*\d)|\bjest(?=\.config|\.mock|\.fn|\.use)"), "jestjs")]


def stems(text: str) -> list[str]:
    for rx, alias in TOOL_ALIASES:
        text = rx.sub(alias, text)
    words = re.findall(r"[a-ząćęłńóśźż0-9][a-ząćęłńóśźż0-9+#.\-]*", text.lower())
    out = []
    for w in words:
        w = w.strip(".-")
        if len(w) < 3 or w in STOP:
            continue
        out.append(w[:STEM])
    return out


PL_INDEX = "hint.pl.txt"   # Polish index of a skill translated into English (tools/hint_pl_index.py); the model does not read it


def clean_body(text: str) -> str:
    """Body for the index: without code examples and without the list of sources."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    return re.sub(r"^## (Źródła|Sources)\b.*?(?=^# |\Z)", " ", text, flags=re.S | re.M)


def load_index() -> list[dict]:
    items = []
    seen: set[str] = set()
    for p in [*sorted(PLUGIN_SKILLS.glob("*/SKILL.md")), *sorted(SKILLS.glob("*/SKILL.md"))]:
        if p.parent.name in seen:          # the same skill in both places: the plugin copy wins
            continue
        seen.add(p.parent.name)
        text = p.read_text(encoding="utf-8", errors="ignore")
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        fm = m.group(1) if m else ""
        if re.search(r"^disable-model-invocation:\s*true", fm, re.M):
            continue                       # skill invoked only manually
        desc = (re.search(r"^description:\s*(.*)$", fm, re.M) or [None, ""])[1]
        kat = (re.search(r"^\s+catalog:\s*(.*)$", fm, re.M) or [None, ""])[1].strip().strip('"')
        kat = NEG_RE.sub("", kat)          # the „Nie do …” boundaries describe neighbors, not this skill
        keywords = (re.search(r"^\s+keywords:\s*(.*)$", fm, re.M) or [None, ""])[1].strip().strip('"')
        name = p.parent.name
        name_words = name.split("-", 1)[-1].replace("-", " ")
        body = text[m.end() if m else 0:]
        excerpt = re.sub(r"<!--.*?-->|\s+", " ", body, flags=re.S).strip()[:700]
        pl_index = p.parent / PL_INDEX       # pre-translation text: Polish prompts match as before
        pl_head = ""
        if pl_index.is_file():
            pl_text = pl_index.read_text(encoding="utf-8", errors="ignore")
            if pl_text.startswith("head: "):     # the former Polish description and catalog — description weight, not body
                first, _, pl_text = pl_text.partition("\n")
                pl_head = NEG_RE.sub("", first[6:])
        else:
            pl_text = ""
        head = set(stems(f"{desc} {kat} {name_words} {keywords} {pl_head}"))
        en_stems, pl_stems = set(stems(clean_body(body))) - head, set(stems(clean_body(pl_text))) - head
        # language versions separately: a prompt is in one language, so the body is scored by the version that fits better,
        # normalized by its own length; summing the versions would inflate the average length (higher scores
        # for untranslated skills, noise), and matching on the sum with a single length would favor the translated ones
        items.append({"name": name, "desc": desc.strip(), "kat": kat.strip(), "excerpt": excerpt,
                      "head": head, "body": en_stems | pl_stems, "blen": max(len(en_stems), len(pl_stems)),
                      "langs": [s for s in (en_stems, pl_stems) if s]})
    return items


QUOTED_RE = re.compile(r"„[^”]{20,}”|\"[^\"]{20,}\"|```.*?```", re.S)


def intent(prompt: str) -> str:
    """The prompt content without quoted material (text to edit, a code fragment) — the request decides the skill choice."""
    rest = QUOTED_RE.sub(" ", prompt)
    return rest if len(stems(rest)) >= 2 else prompt


REF_SKILLS = 150   # thresholds were calibrated on ~150 skills; a smaller install (core + 1 overlay) computes IDF as for 150,
                   # otherwise all scores are lower and even correct hints fall below MIN_SCORE


def rank(prompt: str, items: list[dict]) -> list[tuple[float, dict]]:
    n = max(len(items), REF_SKILLS)
    df: dict[str, int] = {}
    for it in items:
        for t in it["head"] | it["body"]:
            df[t] = df.get(t, 0) + 1
    avg = sum(it.get("blen", len(it["body"])) for it in items) / (len(items) or 1)
    q = set(stems(intent(prompt)))
    scored = []
    for it in items:
        idf = lambda t: math.log(1 + n / df[t])
        # a long skill does not win on sheer number of generic words: each language version is normalized by its own length
        body = max(((avg / max(1, len(b))) ** BODY_NORM * sum(idf(t) for t in q & b)
                    for b in it.get("langs") or [it["body"]]), default=0.0)
        score = HEAD_WEIGHT * sum(idf(t) for t in q & it["head"]) + body
        scored.append((round(score, 2), it))
    scored.sort(key=lambda x: -x[0])
    return scored


def select(prompt: str, items: list[dict], exclude: set[str] | frozenset = frozenset()) -> list[tuple[float, dict]]:
    """Skills to suggest: a score above the threshold and a clear leader (a flat ranking is usually noise from generic words).
    `exclude` (skills outside the project stack) is dropped after ranking: word weights are computed over the whole index, as in calibration."""
    ranked = [x for x in rank(prompt, items) if x[1]["name"] not in exclude]
    if not ranked or ranked[0][0] < MIN_SCORE:
        return []
    best = ranked[0][0]
    second = ranked[1][0] if len(ranked) > 1 else 0.0
    if best < STRONG_SCORE and second and best < second * MARGIN:
        return []
    return [(s, it) for s, it in ranked[:MAX_HINTS] if s >= max(MIN_SCORE, best * RATIO)]


def log_decision(data: dict, prompt: str, items: list[dict], picks: list) -> None:
    """Record the decision to .tf/logs/skill-hints.jsonl (without the prompt content, unless explicitly enabled)."""
    try:
        top = [(it["name"], s) for s, it in rank(prompt, items)[:5]] if items else []
        rec = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "session": data.get("session_id"),
               "prompt_chars": len(prompt), "hinted": [it["name"] for _, it in picks], "top": top, "via": LAST_VIA}
        if os.environ.get("CLAUDE_SKILL_HINT_LOG_PROMPT") == "1":
            rec["prompt"] = prompt[:200]
        log_dir = SKILLS.parent.parent / ".tf" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "skill-hints.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ───────────── optional Jev: two-stage hint (TypeSafe cookbook "skill suggestion") ─────────────
JEV_GATE = 0.30          # mean of the three gate questions — below it we suggest nothing
JEV_FITS = 0.30          # "does the winner do exactly what was asked" — below it we suggest nothing
JEV_SHORTLIST = 3
LAST_VIA = "keywords"
GATE_QS = {
    "specialist": {"type": "noul", "instructions": "Would a good answer to `request` follow a documented specialist "
                   "procedure or checklist, rather than general knowledge?"},
    "project_work": {"type": "noul", "instructions": "Does `request` ask for work on software, product, process, "
                     "infrastructure or a written document, rather than small talk or trivia?"},
    "prose_enough": {"type": "noul", "instructions": "Can `request` be fully answered with a short general reply "
                     "that needs no specialist procedure?"},
}


def jev_suggest(prompt: str, items: list[dict]) -> list | None:
    """Stage 1: a pick among all skills (the descriptions the model sees) + 3 gate questions.
    Stage 2: a pick among the top 3 (full description and the start of SKILL.md) + "does it fit" for each.
    Returns [(score, skill)] (may be empty) or None when Jev is unavailable — then the word-based path remains."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import jev_client as jev
        if not jev.enabled() or len(items) > 255:
            return None
        request = intent(prompt)[:4000]
        qs = {"skill": {"type": "choice", "instructions": "Which skill best matches what `request` asks for?",
                        "criteria": {it["name"]: it["desc"] for it in items}}, **GATE_QS}
        a = jev.decide({"request": request}, qs, timeout=4)
        if not a:
            return None
        gate = (jev.p_yes(a["specialist"]) + jev.p_yes(a["project_work"]) + 1 - jev.p_yes(a["prose_enough"])) / 3
        if gate < JEV_GATE:
            return []
        probs = a["skill"].get("probabilities") or {}
        short = [n for n, _ in sorted(probs.items(), key=lambda kv: -kv[1])][:JEV_SHORTLIST] or [a["skill"].get("choice")]
        by = {it["name"]: it for it in items}
        short = [n for n in short if n in by]
        if not short:
            return []
        cands = {n: {"description": by[n]["kat"] or by[n]["desc"], "excerpt": by[n]["excerpt"]} for n in short}
        q2 = {"best": {"type": "choice", "instructions": "Which candidate skill best covers what `request` asks for?",
                       "criteria": {n: by[n]["kat"] or by[n]["desc"] for n in short}}}
        q2 |= {f"fits_{i}": {"type": "noul", "instructions": f"Does the skill `candidates.{n}` cover the specific thing "
                             "asked in `request`?"} for i, n in enumerate(short)}
        b = jev.decide({"request": request, "candidates": cands}, q2, timeout=4)
        if not b:
            return None
        win = b["best"].get("choice")
        if win not in short or jev.p_yes(b[f"fits_{short.index(win)}"]) < JEV_FITS:
            return []
        return [(round(jev.p_yes(b[f"fits_{short.index(win)}"]) * 20, 2), by[win])]
    except Exception:
        return None


STACK_PREFIXES = ("fw-", "lang-")   # stack identity; tools (tool-) can only be added by the prompt


def _mentioned(prompt: str, variants: list[str]) -> bool:
    for v in variants:
        v = v.strip()
        if not v:
            continue
        flags = re.I if len(v) >= 4 else 0   # short names (Go, C#) only capitalized — „go” is also a Polish pronoun
        if re.search(r"(?<![\w.#])" + re.escape(v) + r"(?![\w#])", prompt, flags):
            return True
    return False


def off_stack(prompt: str) -> set[str]:
    """Framework and language skills from the technology registry (detect_stack) that were not detected in the project and that
    the prompt does not mention. An empty set when no technology was detected (a new project) or with
    CLAUDE_SKILL_HINT_STACK=0. Measurement 2026-11-16 (docs/todo.md): in a Spring Boot repo the hook suggested the NestJS skill."""
    if os.environ.get("CLAUDE_SKILL_HINT_STACK") == "0":
        return set()
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import detect_stack as ds
        root = SKILLS.parent.parent
        entries = [t for t in ds.registry_entries() if str(t.get("skill", "")).startswith(STACK_PREFIXES)]
        found = {t["skill"] for t in entries if ds.detect(root, t)[0]}
        if not found:
            return set()
        out = set()
        for t in entries:
            s = t["skill"]
            if s in found:
                continue
            names = [t.get("name", ""), *str(t.get("name", "")).split("/"), s.split("-", 1)[1].replace("-", " ")]
            if not _mentioned(prompt, names):
                out.add(s)
        return out - found
    except Exception as e:   # the filter is only an optimization: on error the hint works as before
        record_error("skill_hint", e)
        return set()


def suggest(prompt: str, items: list[dict]) -> list:
    """Words (default) or Jev (CLAUDE_SKILL_HINT_JEV=1), falling back to words when Jev is unavailable."""
    global LAST_VIA
    LAST_VIA = "keywords"
    exclude = off_stack(prompt)
    if os.environ.get("CLAUDE_SKILL_HINT_JEV") == "1":
        picks = jev_suggest(prompt, [it for it in items if it["name"] not in exclude])
        if picks is not None:
            LAST_VIA = "jev"
            return picks
        LAST_VIA = "keywords (Jev unavailable)"
    return select(prompt, items, exclude)


def hint(prompt: str, data: dict | None = None) -> str:
    items = load_index()
    if not items or len(prompt.strip()) < 12 or prompt.lstrip().startswith("/"):
        return ""
    picks = suggest(prompt, items)
    if data is not None:
        log_decision(data, prompt, items, picks)
    if not picks:
        return ""
    top, rest = picks[0][0], [s for s, _ in picks[1:]]
    if top >= CLEAR_SCORE and (not rest or top >= CLEAR_LEAD * rest[0]):
        # a clear leader (evaluations 2026-10-02: with a mild hint the model was sometimes sure of its own knowledge and skipped the skill)
        lines = [f"The prompt clearly matches the factory skill {picks[0][1]['name']} (a hint from the skill_hint hook). "
                 "Load it with the Skill tool before you answer — it holds this project's rules and procedures, which "
                 "general knowledge does not have."]
    else:
        lines = ["Factory skills that probably match this prompt (a hint from the skill_hint hook):"]
    lines += [f"- {it['name']} — {it['desc']}" for _, it in picks]
    lines.append("If the task is within the scope of one of them, load it with the Skill tool before answering "
                 "and apply its rules instead of general knowledge. If none matches, ignore this hint.")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if "--explain" in argv:
        prompt = " ".join(a for a in argv[1:] if a != "--explain")
        off = off_stack(prompt)
        for s, it in rank(prompt, load_index())[:8]:
            try:
                print(f"{s:6.2f}  {it['name']}" + ("   (outside the project's stack — skipped)" if it["name"] in off else ""))
            except BrokenPipeError:
                return 0
        print("---\n" + (hint(prompt) or "(no hint — below the threshold)"))
        return 0
    if os.environ.get("CLAUDE_SKILL_HINT") == "0":
        return 0
    try:
        data = json.load(sys.stdin)
        text = hint(str(data.get("prompt") or ""), data)
        if text:
            print(text)
    except Exception as e:  # the hook does not interrupt the session; the error goes to the log
        record_error("skill_hint", e)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
