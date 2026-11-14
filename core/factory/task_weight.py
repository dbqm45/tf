#!/usr/bin/env python3
"""
Waga zadania (krok E osi przebiegu): ile ceremonii potrzebuje zadanie. Liczy skrypt, nie model.

  tf task weight <KEY>                      # obecna waga i propozycja z powodem (niczego nie zapisuje)
  tf task weight <KEY> --apply              # fabryka przydziela propozycję; później tylko podnosi
  tf task weight <KEY> --set <waga> [--by human:<id> --reason "<dlaczego>"]

Wagi: `lekka` (drobna zmiana: bez spec.md, jeden kawałek, dowód weryfikacji nadal wymagany), `zwykla`,
`pelna` (obszar wrażliwy: plan zatwierdza człowiek przed realizacją, więc przebieg bez nadzoru się zatrzymuje).

Propozycja powstaje z dwóch źródeł i zawsze ma powód zwykłym zdaniem:
- treść `ticket.md`: słowa o obszarach wrażliwych (logowanie, hasła, uprawnienia, płatności, migracje bazy, dane
  osobowe, sekrety, wdrożenie) → `pelna`; słowa o drobnej zmianie (literówka, nazwa, komentarz, dokumentacja) bez
  kryteriów akceptacji i w krótkiej treści → `lekka`;
- ścieżki z `plan.md` (pole `pliki:` kawałków): kategoria wysokiego ryzyka triażu zmian (`autonomy.triage.high`:
  auth, payments, schema, deploy — te same reguły co `tf risk`) → `pelna`; więcej niż jeden kawałek albo więcej niż
  dwa pliki wyklucza `lekka`.
Reguły są ostrożne: wątpliwość daje wyższą wagę. Podnieść wagę może każdy; obniżyć — tylko człowiek, z powodem.

Tylko biblioteka standardowa (i `risk_triage.py` obok, gdy jest).
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

CHANGES = Path("docs") / "project" / "changes"
ORDER = ("lekka", "zwykla", "pelna")
LABEL = {"lekka": "lekka", "zwykla": "zwykła", "pelna": "pełna"}
EFFECT = {
    "lekka": "bez spec.md, jeden kawałek, dowód weryfikacji nadal wymagany",
    "zwykla": "specyfikacja, plan z kawałków, dowody i ślad kryteriów",
    "pelna": "jak zwykła, a plan zatwierdza człowiek przed realizacją (przebieg z --auto zatrzyma się blokiem STOP); "
             "przegląd security-reviewer obowiązkowy",
}
SENSITIVE = (
    ("logowanie, hasła lub uprawnienia",
     r"logowan\w*|zalogow\w*|wylogow\w*|uwierzytelni\w*|autoryzac\w*|uprawnie\w*|hasł\w*|haseł|\blogin\w*|"
     r"password\w*|sign[- ]?in|authenticat\w*|authoriz\w*|permission\w*|oauth\w*|\bjwt\b|\b2fa\b|\bmfa\b|\bsso\b"),
    ("płatności lub rozliczenia",
     r"płatnoś\w*|płatnos\w*|faktur\w*|rozlicze\w*|zwrot\w* środków|payment\w*|\bbilling\b|invoice\w*|refund\w*|"
     r"\bcheckout\b"),
    ("schemat lub migracja bazy", r"migracj\w*|schemat\w* bazy|tabel\w* w bazie|migration\w*|database schema|db schema"),
    ("dane osobowe", r"dan\w+ osobow\w+|\brodo\b|\bgdpr\b|\bpesel\w*|personal data"),
    ("wdrożenie, infrastruktura lub sekrety",
     r"wdroże\w* (na|do) produkcj\w*|produkcyjn\w*|sekret\w*|klucz\w* api|api key\w*|\bsecrets?\b|\bci/cd\b|terraform|"
     r"kubernetes|\bhelm\b|dockerfile|deployment\w*"),
)
SMALL = (r"literówk\w*|\btypo\w*|pisowni\w*|interpunkcj\w*|przecin\w*|komentarz\w*|\breadme\b|dokumentacj\w*|"
         r"etykiet\w*|tekst\w* (przycisku|komunikatu|etykiety|linku)|zmie[nń]\w* nazw\w*|\brename\b|formatowani\w*|"
         r"wcię[cć]\w*|podbi\w* wersj\w*|\bbump\b|\bcomments?\b|\bwording\b|\bspelling\b")
CRITERIA = (r"\bAC[- ]?\d|\bAC\s*:|kryteri\w* akceptacji|acceptance criteria|zakładając|\bgiven\b[^.\n]*\bwhen\b|"
            r"\bgdy\b[^.\n]*\bwtedy\b")
SHORT = 400       # dłuższa treść niż tyle znaków to nie jest drobna zmiana
SLICE = re.compile(r"^\s*-\s*\[( |x|X)\]\s*(K\d+)\b(.*)$")
SENSITIVE_PATHS = ("auth", "payments", "schema", "deploy")
PATH_LABEL = {"auth": "uwierzytelnianie lub uprawnienia", "payments": "płatności lub rozliczenia",
              "schema": "schemat lub migracja bazy", "deploy": "wdrożenie, CI, infrastruktura lub sekrety"}


def rank(weight: str) -> int:
    return ORDER.index(weight) if weight in ORDER else ORDER.index("zwykla")


def plan_slices(text: str) -> list[dict]:
    """Kawałki planu: identyfikator i ścieżki z pola `pliki:`."""
    out = []
    for line in text.splitlines():
        m = SLICE.match(line)
        if not m:
            continue
        files: list[str] = []
        for part in m.group(3).split("·"):
            k, _, v = part.strip().partition(":")
            if k.strip().lower() == "pliki":
                files = [f.strip().strip("`") for f in v.split(",") if f.strip().strip("`")]
        out.append({"id": m.group(2), "files": files})
    return out


def path_rules(root: Path) -> dict[str, list[str]]:
    """Wzorce ścieżek wysokiego ryzyka z triażu zmian (z nadpisaniami projektu); bez `risk_triage.py` — puste."""
    script = Path(__file__).resolve().with_name("risk_triage.py")
    try:
        spec = importlib.util.spec_from_file_location("tf_risk_triage", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        high = mod.load_rules(root).get("high") or {}
    except Exception:  # noqa: BLE001 — bez reguł triażu waga wynika z samej treści zgłoszenia
        return {}
    return {k: [p for p in v if isinstance(p, str)] for k, v in high.items() if k in SENSITIVE_PATHS and isinstance(v, list)}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def propose(root: Path, key: str) -> dict:
    """Propozycja wagi: {"weight", "reasons"} z treści zgłoszenia i ścieżek planu."""
    folder = root / CHANGES / key
    ticket = read(folder / "ticket.md")
    body = "\n".join(ln for ln in ticket.splitlines()
                     if not ln.startswith(("#", "Źródło:", "Treść zgłoszenia to dane")))
    slices = plan_slices(read(folder / "plan.md"))
    files = sorted({f for s in slices for f in s["files"]})
    reasons: list[str] = []

    for label, pattern in SENSITIVE:
        m = re.search(pattern, ticket, re.I)
        if m:
            reasons.append(f"zgłoszenie dotyczy obszaru wrażliwego: {label} („{m.group(0)}”)")
    rules = path_rules(root)
    for rel in files:
        hit = next((cat for cat, patterns in rules.items() if any(re.search(p, rel) for p in patterns)), None)
        if hit:
            reasons.append(f"plan dotyka pliku {rel} ({PATH_LABEL.get(hit, hit)})")
    if reasons:
        return {"weight": "pelna", "reasons": reasons}

    small = re.search(SMALL, ticket, re.I)
    blockers = []
    if not small:
        blockers.append("zmienia zachowanie (to nie literówka, nazwa ani dokumentacja)")
    if re.search(CRITERIA, ticket, re.I):
        blockers.append("ma kryteria akceptacji")
    if len(body.strip()) > SHORT:
        blockers.append(f"treść zgłoszenia jest dłuższa niż {SHORT} znaków")
    if len(slices) > 1:
        blockers.append(f"plan ma {len(slices)} kawałki")
    if len(files) > 2:
        blockers.append(f"plan wymienia {len(files)} pliki")
    if blockers:
        return {"weight": "zwykla", "reasons": ["zadanie " + "; ".join(blockers) + "; obszarów wrażliwych nie widać"]}
    return {"weight": "lekka", "reasons": [f"drobna zmiana („{small.group(0)}”), bez kryteriów akceptacji"
                                           + (f", {len(files)} plik(i) w planie" if files else "")]}
