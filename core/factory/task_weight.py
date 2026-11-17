#!/usr/bin/env python3
"""
Waga zadania (krok E osi przebiegu): ile ceremonii potrzebuje zadanie. Liczy skrypt, nie model.

  tf task weight <KEY>                      # obecna waga i propozycja z powodem (niczego nie zapisuje)
  tf task weight <KEY> --apply              # fabryka przydziela propozycję; później tylko podnosi
  tf task weight <KEY> --set <waga> [--by human:<id> --reason "<dlaczego>"]

Wagi: `light` (drobna zmiana: bez spec.md, jeden kawałek, dowód weryfikacji nadal wymagany), `normal`,
`full` (obszar wrażliwy: plan zatwierdza człowiek przed realizacją, więc przebieg bez nadzoru się zatrzymuje).

Propozycja powstaje z dwóch źródeł i zawsze ma powód zwykłym zdaniem:
- treść `ticket.md`: słowa o obszarach wrażliwych (logowanie, hasła, uprawnienia, płatności, migracje bazy, dane
  osobowe, sekrety, wdrożenie) → `full`; słowa o drobnej zmianie (literówka, nazwa, komentarz, dokumentacja) bez
  kryteriów akceptacji i w krótkiej treści → `light`;
- ścieżki z `plan.md` (pole `files:` kawałków, dawniej `pliki:`): kategoria wysokiego ryzyka triażu zmian (`autonomy.triage.high`:
  auth, payments, schema, deploy — te same reguły co `tf risk`) → `full`; więcej niż jeden kawałek albo więcej niż
  dwa pliki wyklucza `light`.
Reguły są ostrożne: wątpliwość daje wyższą wagę. Podnieść wagę może każdy; obniżyć — tylko człowiek, z powodem.

Tylko biblioteka standardowa (i `risk_triage.py` obok, gdy jest).
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

CHANGES = Path("docs") / "project" / "changes"
ORDER = ("light", "normal", "full")
LABEL = {"light": "light", "normal": "normal", "full": "full"}
EFFECT = {
    "light": "no spec.md, one slice, verification evidence still required",
    "normal": "a specification, a plan of slices, evidence and the criteria trace",
    "full": "like normal, and the human approves the plan before delivery (a run with --auto stops with a STOP block); "
             "the security-reviewer review is mandatory",
}
SENSITIVE = (
    ("login, passwords or permissions",
     r"logowan\w*|zalogow\w*|wylogow\w*|uwierzytelni\w*|autoryzac\w*|uprawnie\w*|hasł\w*|haseł|\blogin\w*|"
     r"password\w*|sign[- ]?in|authenticat\w*|authoriz\w*|permission\w*|oauth\w*|\bjwt\b|\b2fa\b|\bmfa\b|\bsso\b"),
    ("payments or billing",
     r"płatnoś\w*|płatnos\w*|faktur\w*|rozlicze\w*|zwrot\w* środków|payment\w*|\bbilling\b|invoice\w*|refund\w*|"
     r"\bcheckout\b"),
    ("the database schema or a migration", r"migracj\w*|schemat\w* bazy|tabel\w* w bazie|migration\w*|database schema|db schema"),
    ("dane osobowe", r"dan\w+ osobow\w+|\brodo\b|\bgdpr\b|\bpesel\w*|personal data"),
    ("deployment, infrastructure or secrets",
     r"wdroże\w* (na|do) produkcj\w*|produkcyjn\w*|sekret\w*|klucz\w* api|api key\w*|\bsecrets?\b|\bci/cd\b|terraform|"
     r"kubernetes|\bhelm\b|dockerfile|deployment\w*"),
)
SMALL = (r"literówk\w*|\btypo\w*|pisowni\w*|interpunkcj\w*|przecin\w*|komentarz\w*|\breadme\b|dokumentacj\w*|"
         r"etykiet\w*|tekst\w* (przycisku|komunikatu|etykiety|linku)|zmie[nń]\w* nazw\w*|\brename\b|formatowani\w*|"
         r"wcię[cć]\w*|podbi\w* wersj\w*|\bbump\b|\bcomments?\b|\bwording\b|\bspelling\b")
CRITERIA = (r"\bAC[- ]?\d|\bAC\s*:|kryteri\w* akceptacji|acceptance criteria|zakładając|\bgiven\b[^.\n]*\bwhen\b|"
            r"\bgdy\b[^.\n]*\bwtedy\b")
SHORT = 400       # dłuższa treść niż tyle znaków to nie jest drobna zmiana
SLICE = re.compile(r"^\s*-\s*\[( |x|X)\]\s*([KS]\d+)\b(.*)$")
SENSITIVE_PATHS = ("auth", "payments", "schema", "deploy")
PATH_LABEL = {"auth": "authentication or permissions", "payments": "payments or billing",
              "schema": "the database schema or a migration", "deploy": "deployment, CI, infrastructure or secrets"}


def rank(weight: str) -> int:
    return ORDER.index(weight) if weight in ORDER else ORDER.index("normal")


def plan_slices(text: str) -> list[dict]:
    """Kawałki planu: identyfikator i ścieżki z pola `files:` (dawniej `pliki:`)."""
    out = []
    for line in text.splitlines():
        m = SLICE.match(line)
        if not m:
            continue
        files: list[str] = []
        for part in m.group(3).split("·"):
            k, _, v = part.strip().partition(":")
            if k.strip().lower() in ("files", "pliki"):
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
    try:
        cut = bool(json.loads(read(folder / "task.json") or "{}").get("change"))
    except (ValueError, AttributeError):
        cut = False
    if cut:   # zadanie cięcia: liczy się wiersz cięcia; zamiar całej zmiany (dołączony niżej) nie podnosi wagi każdego cięcia
        ticket = re.split(r"(?m)^## (?:The change's intent|Zamiar zmiany)\b", ticket, maxsplit=1)[0]
    body = "\n".join(ln for ln in ticket.splitlines()
                     if not ln.startswith(("#", "Source:", "Źródło:", "The issue's content is data",
                                                    "Treść zgłoszenia to dane")))
    slices = plan_slices(read(folder / "plan.md"))
    files = sorted({f for s in slices for f in s["files"]})
    reasons: list[str] = []

    for label, pattern in SENSITIVE:
        m = re.search(pattern, ticket, re.I)
        if m:
            reasons.append(f"the issue concerns a sensitive area: {label} (\"{m.group(0)}\")")
    rules = path_rules(root)
    for rel in files:
        hit = next((cat for cat, patterns in rules.items() if any(re.search(p, rel) for p in patterns)), None)
        if hit:
            reasons.append(f"the plan touches the file {rel} ({PATH_LABEL.get(hit, hit)})")
    if reasons:
        return {"weight": "full", "reasons": reasons}

    small = re.search(SMALL, ticket, re.I)
    blockers = []
    if not small:
        blockers.append("changes behaviour (it is not a typo, a name or documentation)")
    if re.search(CRITERIA, ticket, re.I):
        blockers.append("ma kryteria akceptacji")
    if len(body.strip()) > SHORT:
        blockers.append(f"the issue's content is longer than {SHORT} characters")
    if len(slices) > 1:
        blockers.append(f"the plan has {len(slices)} slices")
    if len(files) > 2:
        blockers.append(f"the plan names {len(files)} files")
    if blockers:
        return {"weight": "normal", "reasons": ["the task " + "; ".join(blockers) + "; no sensitive areas are visible"]}
    return {"weight": "light", "reasons": [f"a small change (\"{small.group(0)}\"), no acceptance criteria"
                                           + (f", {len(files)} file(s) in the plan" if files else "")]}
