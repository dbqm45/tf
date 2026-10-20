#!/usr/bin/env python3
"""
Kontrola wymagań (PRD) przed zapisem — skill proc-requirements-shaping. Tylko odczyt plików, bez sieci.

  python3 requirements_lint.py docs/project/03-requirements/requirements.md [--brief docs/project/01-discovery/brief.md] [--json]

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

Kod wyjścia: 0 — brak blokujących problemów (ostrzeżenia możliwe); 1 — wyciek techniki albo szacunek ponad budżet
bez zapisanego potwierdzenia kosztu; 2 — błąd wejścia (brak pliku). Tylko biblioteka standardowa Pythona 3.9+.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
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
    gwt = any(re.search(r"\bgiven\b.*\bwhen\b.*\bthen\b", l, re.I) or
              re.search(r"\bzakładając\b.*\bgdy\b.*\bwtedy\b", l, re.I) for _, _, l in rows)
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
                found.append({"line": n, "category": cat, "match": m.group(0), "text": line.strip()[:160]})
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Kontrola wymagań (PRD): gotowość, wyciek techniki, próg MVP z briefu.")
    ap.add_argument("requirements", help="plik wymagań, np. docs/project/03-requirements/requirements.md")
    ap.add_argument("--brief", help="brief z budżetem czasu MVP (próg „MVP za duże”)")
    ap.add_argument("--json", action="store_true", help="wynik jako JSON")
    a = ap.parse_args(argv)

    path = Path(a.requirements)
    try:
        text = path.read_text(encoding="utf-8")
        brief_text = Path(a.brief).read_text(encoding="utf-8") if a.brief else None
    except OSError as e:
        print(f"✗ nie mogę odczytać pliku: {e}", file=sys.stderr)
        return 2

    rows = sections(text)
    result = {"file": str(path), "readiness": readiness(text, rows), "leaks": leaks(rows)}
    if brief_text is not None:
        result["mvp"] = mvp_check(brief_text)
    mvp = result.get("mvp") or {}
    blocking = bool(result["leaks"]) or (mvp.get("too_big") is True and not mvp.get("acknowledged"))
    result["ok"] = not blocking

    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        rd = result["readiness"]
        print(f"Gotowość: {rd['score']}/{rd['max']}" + (" — ostrzeżenie" if rd["warning"] else ""))
        for m in rd["missing"]:
            print(f"  · brak: {m}")
        for l in result["leaks"]:
            print(f"{path}:{l['line']} — {l['category']}: „{l['match']}” → opisz zachowanie widoczne z zewnątrz "
                  f"albo przenieś do „Do decyzji o stacku”")
        if mvp:
            if mvp["warning"]:
                print(f"MVP: ⚠ {mvp['warning']}")
            elif mvp["too_big"]:
                state = "koszt potwierdzony" if mvp["acknowledged"] else "BRAK potwierdzenia kosztu — zaproponuj cięcia"
                print(f"MVP: szacunek {mvp['estimate_days']:g} dni > budżet {mvp['budget_days']:g} dni — {state}")
            else:
                print(f"MVP: szacunek {mvp['estimate_days']:g} dni mieści się w budżecie {mvp['budget_days']:g} dni")
        print("✓ bez blokujących problemów" if result["ok"] else "✗ są blokujące problemy")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
