#!/usr/bin/env python3
"""
Kontrola wymagań (PRD) przed zapisem — skill proc-requirements-shaping. Tylko odczyt plików, bez sieci.

  python3 requirements_lint.py docs/project/03-requirements/requirements.md [--brief docs/project/01-discovery/brief.md] [--json] [--strict]
  python3 requirements_lint.py --story story.md [--ac-format gwt|ears|any|off] [--json] [--strict]

Sprawdza:
  1. Gotowość (0–4 punkty): są wymagania `FR-NNN`; jest co najmniej jedna historyjka Given/When/Then
     (albo Zakładając/Gdy/Wtedy); sekcja „Reguła biznesowa” zaczyna się jednym zdaniem (≤ 200 znaków, z kropką,
     bez TODO); sekcja „Poza zakresem” ma co najmniej jedną pozycję. Wynik < 2 → ostrzeżenie z listą braków.
  2. Wyciek techniki do wymagań: dostawcy i technologie, schemat danych, miejsce wykonania, mechanizm, protokół,
     elementy interfejsu w wymaganiach jakości. Pomijane sekcje: „Obecny system”, „Ograniczenia…”,
     „Do decyzji o stacku”, „Otwarte pytania”, „Przekazanie” (tam nazwy techniczne są dozwolone).
  3. (z --brief) Próg „MVP za duże” = budżet czasu z briefu, nie stała. Brief zawiera linie:
       - Budżet czasu MVP: 3 tygodnie
       - Szacunek przepływu MVP: 5 tygodni
       - Koszt potwierdzony: 2026-10-10, <kto> przyjmuje <ile>     (tylko gdy szacunek > budżet)
     Jednostki: dni (robocze), tygodnie (= 5 dni), miesiące (= 21 dni) — podawaj obie wartości w tej samej konwencji.
  4. Kształt każdej historyjki US-NN (blok `### US-NN: tytuł` ze scenariuszami `- AC-n:` albo wiersz tabeli
     `| US-NN | historia | kryteria |`) — reguły kontraktu pdi 0.4.0, słowa kluczowe ze story_shape_vocabulary.json:
       AC-001 scenariusz bez Then/Wtedy albo kryterium poza formatem (domyślnie GWT) · AC-002 słaby wynik
       („poprawnie”, „działa”) · AC-003 szczegół implementacji · AC-004 druga akcja w scenariuszu ·
       STORY-001 kilka akcji (spójnik między czasownikami w tytule lub celu, kilku aktorów, różne akcje główne
       w scenariuszach) · STORY-002 za duża (scenariuszy > 6 albo akcji > 3; bez estymaty) · STORY-003 tytuł od
       warstwy (BE:, API:, migracja) · AC-ID (tf) blok bez identyfikatorów AC-n.
     Tabela, kolumna i endpoint w wymaganiach (AC-003, nowe w kontrakcie) — ostrzeżenie.
  `--story` sprawdza jedną historyjkę z pliku (`# tytuł`, „Jako … chcę …”, kryteria) i wypisuje akcje główne.

Kod wyjścia: 0 — brak blokujących problemów (ostrzeżenia możliwe); 1 — wyciek techniki albo szacunek ponad budżet
bez zapisanego potwierdzenia kosztu, a z --strict także każde ostrzeżenie kształtu historyjki; 2 — błąd wejścia
(brak pliku). Tylko biblioteka standardowa Pythona 3.9+.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

RULE_MAX = 200
SKIP_SECTIONS = ("obecny system", "ograniczenia", "do decyzji o stacku", "otwarte pytania", "przekazanie")

# (kategoria, wzorzec, rozróżniaj wielkość liter, tylko w sekcjach jakości)
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
ACTOR = re.compile(r"^\s*(?:jako|as an?|as)\s+(.+?)\s+(?:chcę|chciał\w*|i want|i would like|i'd like)\b", re.I)
GOAL = re.compile(r"\b(?:chcę|chciał\w*(?: bym)?|i want to|i would like to|i'd like to|i want)\s+(.*)", re.I | re.S)
PURPOSE = re.compile(r",?\s+(?:aby|żeby|by|so that|in order to)\b", re.I)
DETERMINERS = {"the", "a", "an", "my", "your", "his", "her", "its", "our", "their", "this", "that", "these", "those",
               "all", "some", "any", "every", "each", "no"}
SUBJECTS = DETERMINERS | {"i", "we", "you", "he", "she", "it", "they", "user", "customer", "system",
                          "użytkownik", "klient", "system", "się"}
FILLERS = DETERMINERS | {"to", "do", "na", "w", "we", "z", "ze", "o", "for", "with", "of", "on", "in", "into",
                         "it", "them", "ją", "go", "je", "jej", "jego", "ich", "swój", "swoją", "swoje", "is", "are"}
UNIT_DAYS = [(r"^dni|^dzie|^dnia", 1.0), (r"^tydz|^tyg", 5.0), (r"^mies", 21.0)]


def sections(text: str):
    """Zwraca listę (numer_linii, nagłówek_sekcji_małymi, linia) z pominięciem frontmattera i bloków kodu."""
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
        missing.append("wymagania FR-NNN („FR-001: [aktor] może [zdolność]. Priorytet: must|nice”)")
    kw = vocabulary()["keywords"]
    alt = {k: _alt({w for lang in ("en", "pl") for w in kw[lang][k] if len(w) > 1}) for k in ("given", "when", "then")}
    one_line = re.compile(rf"\b({alt['given']})\b.*\b({alt['when']})\b.*\b({alt['then']})\b", re.I)
    gwt = any(one_line.search(l) for _, _, l in rows) or any(
        u["kind"] == "gwt" and u["then"] and u["action"] for s in file_stories(text) for u in ac_units(s["ac"]))
    if not gwt:
        missing.append("historyjka z kryteriami Given/When/Then dla głównego przepływu")
    rule = [l.strip() for _, l in section_lines(rows, "reguła") if l.strip() and not is_placeholder(l)]
    first = rule[0] if rule else ""
    one_sentence = (first and len(first) <= RULE_MAX and first.endswith(".") and "TODO" not in first.upper()
                    and not re.search(r"[.!?]\s+[A-ZĄĆĘŁŃÓŚŹŻ]", first[:-1]))
    if not one_sentence:
        missing.append(f"„Reguła biznesowa” jednym zdaniem (≤ {RULE_MAX} znaków, z kropką, bez TODO)")
    out_of_scope = [l for _, l in section_lines(rows, "poza zakresem") if re.match(r"\s*[-*]\s+\S", l) and not is_placeholder(l)]
    out_of_scope += [l for _, _, l in rows if re.match(r"\s*[-*]\s*poza zakresem\s*:\s*[^…<\s]", l, re.I)]
    if not out_of_scope:
        missing.append("„Poza zakresem” z co najmniej jedną pozycją")
    score = 4 - len(missing)
    return {"score": score, "max": 4, "missing": missing, "warning": score < 2}


def leaks(rows) -> list:
    found = []
    for n, heading, line in rows:
        if any(s in heading for s in SKIP_SECTIONS):
            continue
        quality = "jakoś" in heading or "jakos" in heading
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

    budget = find(r"budżet czasu")
    estimate = find(r"szacunek")
    ack = bool(re.search(r"koszt potwierdzony\s*:\s*[^\s<…]", brief_text, re.I))
    res = {"budget_days": budget, "estimate_days": estimate, "too_big": None, "acknowledged": ack, "warning": None}
    if budget is None:
        res["warning"] = "brief nie ma budżetu czasu MVP — ustal go z człowiekiem („Budżet czasu MVP: N tygodni”)"
    elif estimate is None:
        res["warning"] = "brief nie ma szacunku przepływu MVP — dopisz „Szacunek przepływu MVP: …”"
    else:
        res["too_big"] = estimate > budget
    return res


# --- kształt historyjki (reguły kontraktu pdi: AC-001…004, STORY-001…003) ---

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
    """Słowo kluczowe GWT na początku linii → (rodzaj, reszta). Jednoliterowe „I” tylko wielką literą."""
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
    """Jednostki AC wg README zestawu pdi: scenariusz GWT od Given (albo When) do końca bloku Then; zdanie EARS;
    punkt listy z wolnym tekstem. Pusta linia i identyfikator `AC-n` zaczynają nową jednostkę."""
    when_in, then_in, second_in = _inline()
    lines = (ac or "").replace("<br>", "\n").splitlines()
    en_only = any(keyword(BULLET.sub("", AC_ID.sub("", l.strip())), True)[0] for l in lines)
    units, cur = [], None

    def close():
        nonlocal cur
        if cur:
            units.append(cur)
        cur = None

    def act(u, text):   # krok When (także w jednej linii: „Gdy … i gdy …, wtedy …”)
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
    """Akcja = czasownik + obiekt z kroku When (bez podmiotu i wariantów danych); klucz porównuje rdzenie."""
    words = [w.lower() for w in _tokens(text) if w != ","]
    while words and (words[0] in SUBJECTS or words[0] in actor_words):
        words.pop(0)
    if not words:
        return None
    verb = words[0]
    obj = next((w for w in words[1:] if w not in FILLERS), "")
    return f"{verb[:4]} {obj[:4]}", f"{verb} {obj}".strip()


def _conj_chain(tokens: list, i: int, conj: set) -> bool:
    """Od pozycji i: słowo (, słowo)* spójnik słowo — wyliczenie czasowników, np. „dodać, edytować i usunąć”."""
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
    """Sygnały STORY-001 w tytule i celu: spójnik między czasownikami, ukośnik między słowami, kilku aktorów."""
    v = vocabulary()["action_conjunctions"]
    conj = {c.lower() for c in v["pl"] + v["en"]}
    out = []
    goal_m = GOAL.search(description or "")
    goal = PURPOSE.split(goal_m.group(1) if goal_m else (description or ""), 1)[0]
    tt, gt = _tokens(title or ""), _tokens(goal)
    tw = [k for k, t in enumerate(tt) if t != ","][:2]
    if any(_conj_chain(tt, k, conj) for k in tw):
        out.append(f"tytuł łączy akcje spójnikiem: „{title}”")
    if gt and (_conj_chain(gt, 0, conj) or any(
            t.lower() in v["pl"] and k + 1 < len(gt) and gt[k + 1].lower().endswith("ć") for k, t in enumerate(gt))):
        out.append(f"cel łączy akcje spójnikiem: „{goal.strip()}”")
    if v.get("slash_between_words"):
        for where, text in (("tytuł", title or ""), ("cel", goal)):
            m = re.search(r"(?<![\w/])[^\W\d_]+/[^\W\d_]+(?![\w/])", text)
            if m:
                out.append(f"{where} łączy akcje ukośnikiem: „{m.group(0)}”")
                break
    actor = actor_of(description)
    if actor and (re.search(r"\b(" + "|".join(map(re.escape, conj)) + r")\b", actor, re.I) or "," in actor or "/" in actor):
        out.append(f"kilku aktorów: „{actor}”")
    return out


def check_story(title: str, description: str, ac: str, story_points=None, policy=None) -> dict:
    """Kształt jednej historyjki. story_points przyjmowane, ale nieoceniane (STORY-002 w tf bez estymaty)."""
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
            what = "scenariusz bez Then/Wtedy albo kryterium poza formatem GWT" if fmt == "gwt" else "kryterium poza formatem EARS"
            add("AC-001", f"{what}: " + "; ".join(f"„{(u['id'] + ': ') if u['id'] else ''}{u['text'][:60]}”" for u in bad))
    weak = sorted({w for lang in ("pl", "en") for w in voc["weak_results"][lang] if w.lower() in text.lower()})
    if weak:
        add("AC-002", "słaby wynik zamiast obserwowalnego: " + ", ".join(f"„{w}”" for w in weak))
    impl = [(t["category"], m.group(0)) for t in voc["implementation_terms"]
            for m in [re.search(t["pattern"], text, 0 if t["case_sensitive"] else re.I)] if m]
    if impl:
        add("AC-003", "szczegół implementacji w kryteriach: " + ", ".join(f"{c} „{m}”" for c, m in impl))
    second = [u for u in units if u["second_action"]]
    if second:
        add("AC-004", "druga akcja w scenariuszu: " + "; ".join(f"„{u['text'][:60]}”" for u in second))
    signals = mixing_signals(title, description)
    if len(actions) >= 2:
        signals.append("różne akcje główne w scenariuszach: " + ", ".join(actions.values()))
    if signals:
        add("STORY-001", "historyjka miesza funkcjonalności — " + "; ".join(signals))
    big = []
    if len(units) > pol["maxScenarios"]:
        big.append(f"scenariuszy {len(units)} > {pol['maxScenarios']}")
    if len(actions) > pol["maxActions"]:
        big.append(f"akcji {len(actions)} > {pol['maxActions']}")
    if big:
        add("STORY-002", "za duża: " + ", ".join(big))
    lt = voc["layer_terms"]
    layer = [w.rstrip(":") for w in (title or "").split()
             if w.rstrip(":") in lt["case_sensitive"] or w.rstrip(":").lower() in {x.lower() for x in lt["case_insensitive"]}]
    if layer:
        add("STORY-003", "tytuł od warstwy technicznej zamiast wartości dla użytkownika: " + ", ".join(f"„{w}”" for w in layer))
    return {"scenarios": len(units), "actions": list(actions.values()), "findings": findings,
            "ac_ids": [u["id"] for u in units], "story_points": story_points}


STORY_HEAD = re.compile(r"^#{2,6}\s+(US-\d+)\s*[:.—–-]?\s*(.*)$")
TABLE_STORY = re.compile(r"^\s*\|\s*(US-\d+)\s*\|")


def split_story(lines: list):
    """Treść historyjki → (opis, kryteria): opis do pierwszej linii kryterium (AC-n, punkt listy, słowo GWT, etykieta)."""
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
    """Historyjki US-NN z requirements.md: bloki `### US-NN: tytuł` i wiersze tabeli `| US-NN | historia | kryteria |`."""
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
        r["findings"] = [f for f in r["findings"] if f["rule"] != "AC-003"]   # AC-003 w pliku: skan wycieków
        if s["block"] and r["scenarios"] and not all(r["ac_ids"]):
            r["findings"].append({"rule": "AC-ID", "message": "scenariusze bez identyfikatorów AC-n (np. „- AC-1: Zakładając, że …”)"})
        res.append({"id": s["id"], "line": s["line"], "title": s["title"], **r})
    return res


def new_leak_warnings(rows) -> list:
    """AC-003: kategorie nowe w kontrakcie (np. tabela, kolumna, endpoint) — ostrzeżenie, nie blokada."""
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
    ap = argparse.ArgumentParser(description="Kontrola wymagań (PRD): gotowość, wyciek techniki, próg MVP z briefu, "
                                             "kształt historyjek (GWT, jedna akcja, identyfikatory AC).")
    ap.add_argument("requirements", nargs="?", help="plik wymagań, np. docs/project/03-requirements/requirements.md")
    ap.add_argument("--brief", help="brief z budżetem czasu MVP (próg „MVP za duże”)")
    ap.add_argument("--story", help="jedna historyjka z pliku (`# tytuł`, „Jako … chcę …”, kryteria akceptacji)")
    ap.add_argument("--ac-format", choices=["gwt", "ears", "any", "off"], default="gwt", help="format kryteriów (AC-001)")
    ap.add_argument("--max-scenarios", type=int, default=DEFAULT_POLICY["maxScenarios"], help="próg STORY-002")
    ap.add_argument("--max-actions", type=int, default=DEFAULT_POLICY["maxActions"], help="próg STORY-002")
    ap.add_argument("--strict", action="store_true", help="ostrzeżenia kształtu historyjek kończą się kodem 1")
    ap.add_argument("--json", action="store_true", help="wynik jako JSON")
    a = ap.parse_args(argv)
    policy = {"acFormat": a.ac_format, "maxScenarios": a.max_scenarios, "maxActions": a.max_actions}
    if a.story:
        return story_main(a, policy)
    if not a.requirements:
        ap.print_usage(sys.stderr)
        print("✗ podaj plik wymagań albo --story PLIK", file=sys.stderr)
        return 2

    path = Path(a.requirements)
    try:
        text = path.read_text(encoding="utf-8")
        brief_text = Path(a.brief).read_text(encoding="utf-8") if a.brief else None
    except OSError as e:
        print(f"✗ nie mogę odczytać pliku: {e}", file=sys.stderr)
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
        print(f"Gotowość: {rd['score']}/{rd['max']}" + (" — ostrzeżenie" if rd["warning"] else ""))
        for m in rd["missing"]:
            print(f"  · brak: {m}")
        for l in result["leaks"]:
            print(f"{path}:{l['line']} — AC-003 {l['category']}: „{l['match']}” → opisz zachowanie widoczne z zewnątrz "
                  f"albo przenieś do „Do decyzji o stacku”")
        for w in result["warnings"]:
            print(f"{path}:{w['line']} — ⚠ AC-003 {w['category']}: „{w['match']}” → opisz zachowanie widoczne z zewnątrz")
        for st in result["stories"]:
            for f in st["findings"]:
                print(f"{path}:{st['line']} — ⚠ {st['id']} {f['rule']}: {f['message']}")
        if mvp:
            if mvp["warning"]:
                print(f"MVP: ⚠ {mvp['warning']}")
            elif mvp["too_big"]:
                state = "koszt potwierdzony" if mvp["acknowledged"] else "BRAK potwierdzenia kosztu — zaproponuj cięcia"
                print(f"MVP: szacunek {mvp['estimate_days']:g} dni > budżet {mvp['budget_days']:g} dni — {state}")
            else:
                print(f"MVP: szacunek {mvp['estimate_days']:g} dni mieści się w budżecie {mvp['budget_days']:g} dni")
        print("✓ bez blokujących problemów" if result["ok"] else "✗ są blokujące problemy")
        if n_warn:
            print(f"⚠ ostrzeżenia kształtu historyjek: {n_warn}" + (" — --strict: kod 1" if a.strict else ""))
    return 1 if blocking or (a.strict and n_warn) else 0


def story_main(a, policy) -> int:
    try:
        text = Path(a.story).read_text(encoding="utf-8")
    except OSError as e:
        print(f"✗ nie mogę odczytać pliku: {e}", file=sys.stderr)
        return 2
    title, desc, ac = read_story(text)
    r = check_story(title, desc, ac, None, policy)
    if a.json:
        print(json.dumps({"file": a.story, "story": {"title": title, **r}, "ok": not r["findings"]},
                         ensure_ascii=False, indent=2))
    else:
        print(f"Historyjka: {title} — scenariusze: {r['scenarios']}, akcje główne: {', '.join(r['actions']) or '—'}")
        for f in r["findings"]:
            print(f"⚠ {f['rule']}: {f['message']}")
        if any(f["rule"] == "STORY-001" for f in r["findings"]) and len(r["actions"]) >= 2:
            print("Propozycja podziału: jedna historyjka na akcję — " + " · ".join(r["actions"]))
        print("✓ kształt historyjki bez uwag" if not r["findings"] else f"⚠ uwag: {len(r['findings'])}")
    return 1 if a.strict and r["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
