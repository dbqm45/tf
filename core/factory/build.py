#!/usr/bin/env python3
"""
Fabryka zespołów: rdzeń + nakładki (pack-*) → skille → role → persony → pliki agentów.

  python3 factory/build.py            # zbuduj .claude/agents/_generated/ i .claude/catalog.md
  python3 factory/build.py check      # walidacja + wykrycie nieaktualnych plików (CI)
  python3 factory/build.py list       # podsumowanie zespołów
  python3 factory/build.py new-skill fw-react "Użyj przy ... Nie do ..."

Źródłem prawdy są factory/config.yaml (rdzeń), factory/packs/<id>/ (nakładki) i własne pliki projektu
w factory/{roles,personas,traits}/; składanie opisuje factory/packs.py. Plików w .claude/agents/_generated/
nie edytuj ręcznie.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import packs as packs_mod  # noqa: E402  (factory/packs.py — nakładki i składanie konfiguracji)
yaml = packs_mod.yaml
FACTORY = ROOT / "factory"
SKILLS_DIR = ROOT / ".claude" / "skills"
OUT_DIR = ROOT / ".claude" / "agents" / "_generated"

KNOWN_TOOLS = {
    "Read", "Grep", "Glob", "Edit", "Write", "Bash", "Skill", "WebFetch",
    "WebSearch", "NotebookEdit", "LSP", "TodoWrite", "Agent", "Monitor", "AskUserQuestion",
}
HEADER = "<!-- WYGENEROWANO przez factory/build.py — nie edytuj ręcznie. Źródło: {src} -->\n"


# ───────────────────────── ładowanie ─────────────────────────

def skill_prefixes(cfg: dict) -> tuple[str, ...]:
    return tuple(f["prefix"] for f in cfg["facets"])


def facet_of(skill: str, cfg: dict) -> dict:
    for f in cfg["facets"]:
        if skill.startswith(f["prefix"]):
            return f
    return {"prefix": "", "name": "inne", "question": ""}


def expand_requires(names: list[str], cfg: dict) -> list[str]:
    """Dokłada skille wymagane przez inne (np. fw-angular → lang-typescript), rekurencyjnie."""
    out = list(dict.fromkeys(names))
    i = 0
    while i < len(out):
        for req in (cfg.get("skill_requires") or {}).get(out[i], []):
            if req not in out:
                out.append(req)
        i += 1
    return out


def team_skills(persona: dict, role: dict, cfg: dict) -> list[str]:
    """Skille wykonawcy = rola (dyscyplina) + persona: methods, stack, skills (cały zespół),
    role_skills[rola] (tylko ta rola), core_skills + always_skills; minus drop_skills; plus wymagane (skill_requires)."""
    names: list[str] = list(role.get("skills") or [])
    for key in ("methods", "stack", "skills", "core_skills"):
        names = _union(names, persona.get(key))
    names = _union(names, (persona.get("role_skills") or {}).get(role["name"]))
    drop = set(persona.get("drop_skills") or [])
    names = [n for n in names if n not in drop]
    return expand_requires(_union(names, always_for(persona, cfg)), cfg)


def persona_skills(persona: dict, roles: dict, cfg: dict) -> list[str]:
    acc: list[str] = []
    for r in persona.get("roles", []):
        if r in roles:
            acc = _union(acc, team_skills(persona, roles[r], cfg))
    for key in ("methods", "stack", "skills"):
        acc = _union(acc, [n for n in (persona.get(key) or []) if n not in set(persona.get("drop_skills") or [])])
    return expand_requires(_union(acc, always_for(persona, cfg)), cfg)


def always_for(persona: dict, cfg: dict) -> list[str]:
    """Skille zawsze dokładane: rdzenia (wszystkim) + nakładki, z której pochodzi persona (tylko jej personom)."""
    pack = (cfg.get("_packs") or {}).get(persona.get("_pack"), {})
    return _union(cfg.get("always_skills"), pack.get("always_skills"))

def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


PROFILE_FILE = ROOT / ".claude" / "factory-profile.json"


def active_profile(cfg: dict) -> str:
    """Profil kosztów: z .claude/factory-profile.json (ustawia factory/profile.py), inaczej default_profile."""
    name = cfg.get("default_profile")
    if PROFILE_FILE.exists():
        try:
            name = json.loads(PROFILE_FILE.read_text(encoding="utf-8")).get("profile") or name
        except (json.JSONDecodeError, OSError):
            pass
    return name if name in (cfg.get("profiles") or {}) else cfg.get("default_profile")


def load_config() -> dict:
    """config.yaml rdzenia złożony z nakładkami (factory/packs.py) i z nałożonym profilem kosztów (pola tierów)."""
    cfg = packs_mod.compose(ROOT, load_yaml(FACTORY / "config.yaml"))
    name = active_profile(cfg)
    cfg["_profile"] = name
    for tier, over in (((cfg.get("profiles") or {}).get(name) or {}).get("tiers") or {}).items():
        if tier in cfg.get("tiers", {}):
            cfg["tiers"][tier] = {**cfg["tiers"][tier], **(over or {})}
    return cfg


TESTS_REL = "tests" if (ROOT / "tests" / "run_skill_evals.py").exists() else ".claude/tests"
PROJECT_GATE = ROOT / ".claude" / "skill-gate.json"


def gate_registries_factory() -> list[Path]:
    """Rejestry bramki dostarczone z rdzeniem i nakładkami (`.claude/tests/skill_gate/<id>.json`) oraz starszy układ."""
    out = [ROOT / "tests" / "skill_gate.json", ROOT / ".claude" / "tests" / "skill_gate.json"]
    for d in (ROOT / "tests" / "skill_gate", ROOT / ".claude" / "tests" / "skill_gate"):
        out += sorted(d.glob("*.json")) if d.is_dir() else []
    return out


def evals_file(name: str) -> Path:
    for d in (ROOT / "tests", ROOT / ".claude" / "tests"):
        if (d / "skill_evals" / f"{name}.json").exists():
            return d / "skill_evals" / f"{name}.json"
    return ROOT / TESTS_REL / "skill_evals" / f"{name}.json"


def skill_fingerprint(name: str) -> str:
    """Odcisk treści skilla do bramki jakości (factory/skill_gate.py): pliki skilla i jego scenariusze. Ścieżki względne,
    spis treści i ścieżki testów po instalacji normalizowane — ten sam skill ma ten sam odcisk w fabryce i w projekcie."""
    import hashlib
    h = hashlib.sha256()
    d = SKILLS_DIR / name
    files = [(p.relative_to(d).as_posix(), p) for p in sorted(d.rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    ev = evals_file(name)
    if ev.exists():
        files.append(("evals.json", ev))
    for rel, p in files:
        data = p.read_bytes()
        if p.suffix in (".md", ".json", ".yml"):
            text = data.decode("utf-8", errors="ignore").replace(" .claude/tests/test_", " tests/test_") \
                .replace("(python3 .claude/tests/", "(python3 tests/")
            if p.suffix == ".md" and rel.startswith("references/"):
                text = with_toc(text)
            if rel == "SKILL.md":   # termin przeglądu (factory/freshness.py) nie zmienia treści — bramka zostaje ważna
                text = re.sub(r"^  przeglad:.*\n", "", text, count=1, flags=re.M)
            data = text.encode("utf-8")
        h.update(rel.encode() + b"\0" + data + b"\0")
    return h.hexdigest()[:16]


def check_review_date(name: str, meta: dict) -> tuple[list[str], list[str]]:
    """`metadata.przeglad`: termin przeglądu skilla w formacie RRRR-MM-DD (factory/freshness.py)."""
    raw = meta.get("przeglad")
    if raw is None:
        return [], [f"skill {name}: brak metadata.przeglad (termin przeglądu treści) — "
                    f"python3 factory/freshness.py --reviewed {name}"]
    try:
        import datetime as _dt
        ok = re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(raw)) and _dt.date.fromisoformat(str(raw))
    except ValueError:
        ok = False
    return ([] if ok else [f"skill {name}: metadata.przeglad '{raw}' nie jest datą RRRR-MM-DD"]), []


def gate_registry_factory() -> dict:
    """Rejestr dostarczony z fabryką (bez wpisów projektu)."""
    reg: dict = {}
    for p in gate_registries_factory():
        try:
            reg.update(json.loads(p.read_text(encoding="utf-8")) if p.exists() else {})
        except json.JSONDecodeError:
            pass
    return reg


def gate_registry() -> dict:
    reg: dict = {}
    for p in [*gate_registries_factory(), PROJECT_GATE]:
        try:
            reg.update(json.loads(p.read_text(encoding="utf-8")) if p.exists() else {})
        except json.JSONDecodeError:
            pass
    return reg


def load_dir(sub: str) -> dict[str, dict]:
    """Role albo persony z nakładek i własne projektu (factory/packs.py → load_items)."""
    return packs_mod.load_items(ROOT, sub)[0]


def load_traits() -> dict[str, str]:
    return packs_mod.load_traits(ROOT)


def load_skills() -> dict[str, dict]:
    skills = {}
    for p in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = p.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        meta = yaml.safe_load(m.group(1)) if m else {}
        meta = meta or {}
        meta["_dir"] = p.parent.name
        meta["_lines"] = text.count("\n")
        meta["_chars"] = len(text)
        skills[meta.get("name", p.parent.name)] = meta
    return skills


def _union(a: list, b: list) -> list:
    return list(dict.fromkeys([*(a or []), *(b or [])]))


def resolve_persona(name: str, personas: dict, seen: tuple = ()) -> dict:
    """Rozwiązuje `extends`: listy są łączone, pola skalarne nadpisywane, drop_* usuwa."""
    if name in seen:
        raise ValueError(f"Cykl w extends: {' -> '.join(seen + (name,))}")
    p = dict(personas[name])
    parent_name = p.pop("extends", None)
    if not parent_name:
        return p
    if parent_name not in personas:
        raise ValueError(f"Persona {name}: extends nieznanej persony '{parent_name}'")
    base = resolve_persona(parent_name, personas, seen + (name,))
    merged = {**base, **{k: v for k, v in p.items() if k not in ("roles", "traits", "core_skills", "methods", "stack", "skills", "drop_skills", "role_skills", "priorities")}}
    for key in ("roles", "traits", "core_skills", "methods", "stack", "skills", "drop_skills"):
        merged[key] = _union(base.get(key, []), p.get(key, []))
    merged["priorities"] = p.get("priorities") or base.get("priorities", [])
    merged["roles"] = [r for r in merged["roles"] if r not in (p.get("drop_roles") or [])]
    merged["traits"] = [t for t in merged["traits"] if t not in (p.get("drop_traits") or [])]
    merged["stack"] = [t for t in merged.get("stack", []) if t not in (p.get("drop_stack") or [])]
    merged["role_skills"] = {**(base.get("role_skills") or {})}
    for r, extra in (p.get("role_skills") or {}).items():
        merged["role_skills"][r] = _union(merged["role_skills"].get(r), extra)
    merged["name"] = name
    return merged


PERSONA_SKILL_KEYS = ("methods", "stack", "skills", "core_skills", "drop_skills")


def load_team(cfg: dict) -> tuple[dict, dict, dict, dict, list[str]]:
    """Role, persony (rozwiązane `extends`), cechy i skille po złożeniu z nakładkami:
    - wkład nakładek (`contributes`): skille ról, cechy i skille wspólne wszystkich person;
    - odwołania nakładki do elementów nakładek opcjonalnych (`optional_packs`), których nie zainstalowano, są pomijane
      (lista w `_dropped`; pokazuje ją `build.py list`).
    Zwraca (role, persony, cechy, skille, błędy)."""
    roles, personas_raw, traits, skills = load_dir("roles"), load_dir("personas"), load_traits(), load_skills()
    packs = cfg.get("_packs") or {}
    rc, pc = cfg.get("_role_contrib") or {}, cfg.get("_persona_contrib") or {}
    errors: list[str] = []

    def optional_gap(item: dict) -> bool:
        return bool(packs_mod.missing_optional(packs.get(item.get("_pack")), packs))

    out_roles = {}
    for n, r in roles.items():
        r = dict(r, skills=_union(r.get("skills"), (rc.get(n) or {}).get("skills")))
        if optional_gap(r):
            r["_dropped"] = [x for k in ("skills", "preload") for x in r.get(k) or [] if x not in skills]
            for k in ("skills", "preload"):
                r[k] = [x for x in r.get(k) or [] if x in skills]
        out_roles[n] = r
    out_personas = {}
    for name in personas_raw:
        try:
            p = resolve_persona(name, personas_raw)
        except ValueError as e:
            errors.append(str(e))
            continue
        for k in ("traits", "core_skills", "skills"):
            p[k] = _union(p.get(k), pc.get(k))
        if optional_gap(personas_raw[name]):
            dropped = [x for k in PERSONA_SKILL_KEYS for x in p.get(k) or [] if x not in skills]
            dropped += [f"rola {x}" for x in p.get("roles") or [] if x not in out_roles]
            dropped += [f"cecha {x}" for x in p.get("traits") or [] if x not in traits]
            dropped += [f"agent {x}" for x in p.get("extra_agents") or [] if x.split("-", 1)[0] not in personas_raw]
            for k in PERSONA_SKILL_KEYS:
                p[k] = [x for x in p.get(k) or [] if x in skills]
            p["role_skills"] = {r: [x for x in v if x in skills] for r, v in (p.get("role_skills") or {}).items()
                                if r in out_roles}
            p["roles"] = [x for x in p.get("roles") or [] if x in out_roles]
            p["traits"] = [x for x in p.get("traits") or [] if x in traits]
            p["extra_agents"] = [x for x in p.get("extra_agents") or [] if x.split("-", 1)[0] in personas_raw]
            p["_dropped"] = dropped
        out_personas[name] = p
    return out_roles, out_personas, traits, skills, errors


# ───────────────────────── renderowanie ─────────────────────────

def q(s: str) -> str:
    """Bezpieczny skalar YAML (JSON-owy string jest poprawnym YAML)."""
    return json.dumps(" ".join(str(s).split()), ensure_ascii=False)


def frontmatter(fields: dict) -> str:
    lines = ["---"]
    for k, v in fields.items():
        if v in (None, "", []):
            continue
        if k == "description":
            lines.append(f"{k}: {q(v)}")
        elif isinstance(v, list):
            if k == "skills":
                lines.append(f"{k}:")
                lines += [f"  - {x}" for x in v]
            else:
                lines.append(f"{k}: {', '.join(v)}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def tier_fields(cfg: dict, tier: str) -> dict:
    t = cfg["tiers"][tier]
    return {"model": t["model"], "effort": t.get("effort"), "maxTurns": t.get("maxTurns")}


def numbered(items: list[str]) -> str:
    return "\n".join(f"{i}. {x}" for i, x in enumerate(items, 1))


def skills_line(names: list[str]) -> str:
    return ", ".join(f"`{s}`" for s in names)


def dimension_table(skills: list[str], cfg: dict) -> str:
    rows = []
    for f in cfg["facets"]:
        mine = [x for x in skills if x.startswith(f["prefix"])]
        if mine:
            rows.append(f"| {f['name']} | {f['question']} | {skills_line(mine)} |")
    return "| Wymiar | Pytanie | Twoje skille |\n|---|---|---|\n" + "\n".join(rows)


def language_section(cfg: dict) -> str:
    """Język pracy i commitów z ustawień projektu (`tf language`, `tf commit-language`)."""
    langs, st = cfg.get("languages") or {}, cfg.get("_settings") or {}
    work = (langs.get(st.get("language")) or {}).get("work", "")
    commits = (langs.get(st.get("commit_language")) or {}).get("commits", "")
    lines = [x for x in (work, commits, cfg.get("code_language_note", "")) if x]
    return "## Język\n" + "\n".join(f"- {x.strip()}" for x in lines) + "\n" if lines else ""


def consultants_for(persona: dict, cfg: dict) -> dict[str, dict]:
    """Konsultanci innych nakładek niż nakładka persony (docs/insights.md)."""
    return {n: c for n, c in (cfg.get("consultants") or {}).items() if c.get("_pack") != persona.get("_pack")}


def shared_for(persona: dict, cfg: dict) -> list[str]:
    """Agenci wspólni dostępni personie. `only_for`: nazwy person albo `@dispatcher` (persony z `dispatcher: true`);
    `main_only`: agent uruchamiany jako sesja główna, nie wykonawca."""
    out = []
    for n, a in cfg["shared_agents"].items():
        if n == "Explore" or a.get("main_only"):
            continue
        only = a.get("only_for") or []
        if only and persona["name"] not in only and not ("@dispatcher" in only and persona.get("dispatcher")):
            continue
        out.append(n)
    return out


COMPOSE_HINT = (
    "Skille są niezależne — każdy odpowiada na inne pytanie. Przy każdym zadaniu: rozłóż je na wymiary, "
    "wczytaj (narzędziem Skill) `core-skill-composition` oraz po jednym skillu z każdego potrzebnego wymiaru "
    "i połącz je wg protokołu z `core-skill-composition` (CO → GDZIE → JAK, wspólny słownik pojęć). "
    "Nie odpowiadaj z pamięci ogólnej w obszarze, który pokrywa Twój skill. "
    "Możesz też wczytać skill spoza fabryki (projektu, osobisty, z wtyczki), gdy jego opis pokrywa lukę lub zawiera "
    "ustalenia tego projektu — zasady pierwszeństwa są w `core-skill-composition`."
)


def render_worker(persona: dict, role: dict, cfg: dict, traits: dict) -> tuple[str, str]:
    name = f"{persona['name']}-{role['name']}"
    fm = frontmatter({
        "name": name,
        "description": f"{role['title']} w zespole {persona['name']}. Deleguj: {role['triggers']}.",
        "tools": role["tools"],
        **tier_fields(cfg, role["tier"]),
        "skills": role.get("preload") or [],
        "color": persona.get("color"),
    })
    trait_txt = "\n\n".join(traits[t] for t in persona["traits"])
    verify = (role.get("verify") or "").strip()
    body = f"""
# Rola: {role['title']} — zespół „{persona['title']}”

{role['identity'].strip()}

## Priorytety zespołu (w konflikcie wygrywa wyższy)
{numbered(persona['priorities'])}

## Cechy
{trait_txt}

{language_section(cfg)}
## Skille i ich łączenie
{COMPOSE_HINT}

{dimension_table(team_skills(persona, role, cfg), cfg)}

## Zapis w docs/project/
Jeśli brief przydziela Ci artefakt w `docs/project/`, zapisz go wg `core-project-record` (TL;DR ≤ 10 linii, Otwarte pytania,
Przekazanie) i uruchom `python3 .claude/hooks/project_record.py check`. Wpisy w dzienniku i rejestrze decyzji robi orkiestrator.
Czytając wejścia, zaczynaj od TL;DR i Przekazania.

## Granice
- Pracujesz tylko w swojej domenie. Jeśli zadanie jej wykracza — nie improwizuj, zgłoś to w raporcie.
- Potrzebujesz wiedzy innej dziedziny (np. innej nakładki)? Nie zgaduj: wpisz w raporcie konkretne pytanie
  — persona zada je konsultantowi tej dziedziny i odpowie w kolejnym briefie.
- Nie commitujesz i nie pushujesz — robi to orkiestrator po weryfikacji całości.
- Nie zmieniasz konfiguracji w `.claude/` ani plików z sekretami.
{f"{chr(10)}## Weryfikacja{chr(10)}Przed raportem zweryfikuj zmianę: {verify} (komendy z CLAUDE.md projektu mają pierwszeństwo).{chr(10)}" if verify else ""}
## Raport
{cfg['report_contract'].strip()}
"""
    return name, fm + HEADER.format(src=f"{persona['_src']} + {role['_src']}") + body


def render_persona(persona: dict, roles: dict, cfg: dict, traits: dict, personas: dict | None = None) -> tuple[str, str]:
    team = [(f"{persona['name']}-{r}", roles[r]) for r in persona["roles"]]
    shared = cfg["shared_agents"]
    shared_names = shared_for(persona, cfg)
    extra = persona.get("extra_agents") or []   # wykonawcy innych person, po których ta persona może sięgnąć
    consult = consultants_for(persona, cfg)
    agent_names = [n for n, _ in team] + shared_names + extra + list(consult)
    tools = [f"Agent({', '.join(agent_names)})", "Read", "Grep", "Glob", "Edit", "Write", "Bash", "Skill"]
    tf = tier_fields(cfg, persona.get("model_tier", "std"))
    fm = frontmatter({
        "name": persona["name"],
        "description": persona["description"],
        "tools": tools,
        "model": tf["model"],
        "effort": tf["effort"],
        "memory": persona.get("memory"),
        "color": persona.get("color"),
    })
    rows = [f"| `{n}` | {r['title']} | {r['tier']} ({cfg['tiers'][r['tier']]['model']}) | {r['triggers']}. Skille: {', '.join(team_skills(persona, r, cfg))} |" for n, r in team]
    rows += [f"| `{n}` | wspólny | {shared[n]['tier']} ({cfg['tiers'][shared[n]['tier']]['model']}) | {shared[n]['description']} |" for n in shared_names]
    rows += [f"| `{n}` | z persony `{n.split('-', 1)[0]}` | — | zobacz katalog `.claude/catalog.md` |" for n in extra]
    trait_txt = "\n\n".join(traits[t] for t in persona["traits"])
    routing = (cfg["routing"].rstrip() + "\n\n" + cfg.get("routing_notes", "").strip()).replace("{persona}", persona["name"]).strip()
    consult_txt = ""
    if consult:
        crow = "\n".join(f"| `{n}` | {c['_pack']} | {c['description']} |" for n, c in consult.items())
        consult_txt = f"""
## Konsultacje z innymi zespołami
Gdy zadanie wymaga wiedzy innej dziedziny, zapytaj jej konsultanta (narzędzie Agent): konkretne pytanie, kontekst
(pliki, ustalenia), czego oczekujesz. Konsultant tylko odpowiada — ze źródłem i z tym, czego nie wie; decyzję
podejmujesz Ty albo człowiek. Pytanie do persony innej nakładki, które wymaga jej pracy w osobnej sesji albo decyzji
człowieka, zapisz w `docs/project/questions.md` (kto pyta, do kogo, pytanie, kontekst). Twoi wykonawcy nie wywołują
konsultantów — potrzebę konsultacji zgłaszają w raporcie.

| Konsultant | Nakładka | Kiedy |
|---|---|---|
{crow}
"""
    body = f"""
# Jesteś: {persona['title']}

{persona['identity'].strip()}

Prowadzisz zespół. Domyślnie robisz zadanie sam, we własnym kontekście: wczytujesz pasujące skille
(narzędziem Skill) i pracujesz jak najlepszy specjalista w tym obszarze. Twój kontekst zna już kod i rozmowę,
a jego dalsze użycie jest tanie (cache). Nowy wykonawca zaczyna od zera: czyta te same pliki jeszcze raz
i dostaje tylko streszczenie, więc delegujesz wtedy, gdy przekazanie się opłaca (sekcja „Kiedy delegujesz”).

## Priorytety (w konflikcie wygrywa wyższy)
{numbered(persona['priorities'])}

## Cechy
{trait_txt}

{language_section(cfg)}
## Twój zespół
| Agent | Rola | Tier (model) | Kiedy |
|---|---|---|---|
{chr(10).join(rows)}

## Routing i koszty
{routing}
{consult_txt}
## Jak łączysz skille
{COMPOSE_HINT}
Ten sam zestaw wymiarów przekazujesz w briefie wykonawcy: napisz, które skille ma połączyć.

{dimension_table(persona_skills(persona, roles, cfg), cfg)}

## Kiedy delegujesz
Przekazanie kosztuje (nowy kontekst czyta pliki od nowa) i gubi szczegóły, więc delegujesz tylko wtedy, gdy:
- **dużo czytania, krótki wynik** — „gdzie jest…”, przegląd wielu plików, logi, wersje i fakty → `scout`,
  `researcher` (tani model, a Twój kontekst nie puchnie);
- **części są naprawdę niezależne** — osobne moduły bez wspólnych decyzji → wykonawcy równolegle;
- **potrzebne jest świeże spojrzenie** — przegląd bezpieczeństwa, testy z wymagań bez patrzenia w kod (clean-room),
  przegląd planu lub diffu: brak Twojego kontekstu jest tu zaletą, bo recenzent nie powtarza Twoich założeń;
- **zmiana mechaniczna z pełną specyfikacją i poleceniem weryfikacji** → `quick-fixer` (najtańszy model);
- **decyzja trudna do odwrócenia** → `architect` albo doradca tylko do analizy opcji, wykonanie wraca do Ciebie;
- Twój kontekst jest bliski zapełnienia, a zadanie ma wyraźną, samodzielną część.

Nie dziel jednej spójnej zmiany (wspólne pliki, typy, decyzje) między kilku wykonawców — zrób ją sam.

## Jak delegujesz
- Wykonawca NIE widzi tej rozmowy. Brief ma być samowystarczalny: cel, konkretne ścieżki i fakty, które już
  ustaliłeś (żeby nie szukał od nowa), skille do wczytania, kryteria akceptacji, komenda weryfikacji.
- Niezależne kroki uruchamiaj równolegle, zależne — po kolei. Nie deleguj tego samego dwa razy.
- Po raportach: uruchom weryfikację całości, przejrzyj `git diff`, dopiero wtedy commit.
- Jeśli wykonawca zgłosi blokadę — eskaluj o jeden poziom (parametr `model` narzędzia Agent) albo zapytaj użytkownika.
  Linia `Tier: za niski/za wysoki` w raporcie to sygnał dla kolejnych podobnych zadań.

## Zapis przebiegu projektu (docs/project/)
- **W trakcie sesji** ciągłość zapewnia Twój kontekst, a przy delegowaniu — brief. **Artefakt zapisujesz na końcu fazy** (brief, domena, wymagania,
  stack, plan, realizacja kroku, przegląd) albo gdy praca ma być kontynuowana w innej sesji — nie po każdej drobnej zmianie.
- **Punkt kontrolny pracy w toku** (`project_record.py wip start "<cel>" --by {persona['name']}`) zakładasz dla zadania dłuższego
  niż kilka kroków i aktualizujesz krótko po każdym zakończonym kroku: odhaczony krok z dowodem, następna czynność,
  ustalenia z rozmowy. Hook sesji pokazuje aktywne zadania. Wznawiając, czytasz punkt kontrolny i `git status`,
  zanim zrobisz cokolwiek innego. Koniec zadania: `wip done <nazwa>`.
- **Start:** hook sesji pokazuje skrót stanu; w razie potrzeby `python3 .claude/hooks/project_record.py status`.
  Z artefaktów wejściowych czytaj tylko **TL;DR + Przekazanie** i sekcje, które wskazuje przekazanie.
- **Koniec fazy:** artefakt wg `core-project-record` (TL;DR, Otwarte pytania, Przekazanie) → `project_record.py log --by {persona['name']} --phase <faza> "…"`
  → `project_record.py check`. Gdy treść jest już ustalona w rozmowie, zapis zleć najtańszemu wykonawcy (tier fast).
- Status `accepted` ustawiasz tylko po wyraźnej akceptacji użytkownika.

## Nawyki
{persona.get('habits', '').strip()}

## Skille wspólne
{skills_line(persona.get('core_skills') or []) or '—'} — wczytuj je, gdy commitujesz lub piszesz dokumentację.
"""
    return persona["name"], fm + HEADER.format(src=persona["_src"]) + body


def render_shared(name: str, spec: dict, cfg: dict) -> tuple[str, str]:
    fm = frontmatter({
        "name": name,
        "description": spec["description"],
        "tools": spec["tools"],
        **tier_fields(cfg, spec["tier"]),
        "skills": spec.get("skills") or [],
        "memory": spec.get("memory"),
    })
    body = "\n" + spec["prompt"].strip() + "\n"
    if cfg.get("grounding_note") and spec.get("grounding", True):
        body += "\n## Rzetelność\n" + cfg["grounding_note"].strip() + "\n"
        body += "\n" + language_section(cfg)
    if "Edit" in spec["tools"] or "Write" in spec["tools"]:
        body += "\n## Raport\n" + cfg["report_contract"].strip() + "\n"
    src = "factory/config.yaml" if spec.get("_pack", "core") == "core" else f"factory/packs/{spec['_pack']}/pack.yaml"
    return name, fm + HEADER.format(src=src) + body


CONSULT_TOOLS = ["Read", "Grep", "Glob", "Skill"]


def render_consultant(name: str, spec: dict, cfg: dict) -> tuple[str, str]:
    """Konsultant nakładki: tylko do odczytu, wczytuje skille swojej dziedziny i odpowiada ze źródłem."""
    fm = frontmatter({
        "name": name,
        "description": spec["description"],
        "tools": CONSULT_TOOLS,
        **tier_fields(cfg, spec.get("tier", "std")),
        "skills": spec.get("skills") or [],
    })
    pack = (cfg.get("_packs") or {}).get(spec["_pack"], {})
    body = f"""
Jesteś konsultantem dziedziny „{pack.get('title', spec['_pack'])}” (nakładka {spec['_pack']}). Pyta Cię persona innego
zespołu, która nie zna tej dziedziny. Odpowiadasz na jej pytanie, niczego nie zmieniasz w plikach.

1. Wczytaj skille z listy (narzędzie Skill) i tylko te pliki projektu, które są potrzebne do odpowiedzi.
2. Odpowiedz konkretnie na zadane pytanie, w języku tej dziedziny, ale zrozumiale dla osoby spoza niej
   (rozwiń skróty przy pierwszym użyciu).
3. Każde twierdzenie oprzyj na źródle: skill (`nazwa`, plik referencyjny), plik projektu (`plik:linia`) albo standard
   lub przepis z wersją. Czego nie wiesz albo nie sprawdziłeś — napisz wprost.
4. Gdy pytanie wymaga decyzji (biznesowej, prawnej, architektonicznej), podaj opcje z konsekwencjami i zaznacz, kto
   powinien zdecydować. Gdy wykracza poza Twoją dziedzinę — powiedz, której.

Format (maks. ~25 linii): **Odpowiedź** · **Źródła** · **Założenia i luki** · **Do decyzji** (jeśli są).
Skille: {skills_line(spec.get('skills') or [])}

## Rzetelność
{cfg.get('grounding_note', '').strip()}

{language_section(cfg)}"""
    return name, fm + HEADER.format(src=f"factory/packs/{spec['_pack']}/pack.yaml") + body


def render_all() -> dict[str, str]:
    cfg = load_config()
    roles, personas, traits, _skills, _errors = load_team(cfg)
    out: dict[str, str] = {}
    for name, spec in cfg["shared_agents"].items():
        n, txt = render_shared(name, spec, cfg)
        out[f"shared/{n}.md"] = txt
    for name, spec in cfg["consultants"].items():
        n, txt = render_consultant(name, spec, cfg)
        out[f"consult/{n}.md"] = txt
    for pname, persona in personas.items():
        n, txt = render_persona(persona, roles, cfg, traits, personas)
        out[f"{pname}/{n}.md"] = txt
        for r in persona["roles"]:
            n, txt = render_worker(persona, roles[r], cfg, traits)
            out[f"{pname}/{n}.md"] = txt
    return out


CATALOG = ROOT / ".claude" / "catalog.md"
TOC_MARK = "> **Spis treści:**"
TOC_MIN_LINES = 100   # Anthropic: plik referencyjny > 100 linii ma spis treści (model czyta czasem tylko początek)


def with_toc(text: str) -> str:
    """Plik referencyjny z aktualnym spisem treści (jedna linia pod tytułem) albo bez zmian, gdy krótki."""
    lines = []
    for l in text.splitlines():
        if l.startswith(TOC_MARK):
            if lines and not lines[-1].strip():
                lines.pop()   # pusta linia wstawiona razem ze spisem
            continue
        lines.append(l)
    body = "\n".join(lines)
    in_code, heads = False, []
    for l in lines:
        if l.startswith("```"):
            in_code = not in_code
        elif not in_code and l.startswith("## ") and l[3:].strip() not in ("Źródła", "Spis treści"):
            h = l[3:].strip()
            heads.append(h if len(h) <= 60 else h[:60].rsplit(" ", 1)[0] + "…")
    if len(lines) <= TOC_MIN_LINES or len(heads) < 3:
        return body + ("\n" if text.endswith("\n") else "")
    toc = f"{TOC_MARK} " + " · ".join(heads)
    i = next((k for k, l in enumerate(lines) if l.startswith("# ")), -1)
    out = lines[:i + 1] + ["", toc] + lines[i + 1:] if i >= 0 else [toc, ""] + lines
    # bez podwójnych pustych linii wokół spisu
    res = "\n".join(out).replace(f"\n\n\n{TOC_MARK}", f"\n\n{TOC_MARK}").replace(toc + "\n\n\n", toc + "\n\n")
    return res + "\n"


def reference_files() -> list[Path]:
    return sorted(p for p in SKILLS_DIR.glob("*/references/**/*.md") if p.is_file())


def render_catalog() -> str:
    """Zwięzły katalog skilli, person i agentów — czyta go dyspozytor (core-problem-routing), zamiast wszystkich skilli."""
    cfg = load_config()
    roles, personas, _traits, skills, _errors = load_team(cfg)
    def short(d: str) -> str:
        d = re.sub(r"^Użyj( zawsze)?,?\s*(przy|gdy|by|do|w)?\s*", "", d.strip())
        head, _, tail = d.strip().rstrip(".").partition(" Nie do ")
        cut = lambda s, n: s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"
        return cut(head, 200) + (f" Nie do {cut(tail, 110)}" if tail else "")
    def entry(s: dict) -> str:
        """Krótki opis (co i kiedy) + granice „Nie do …” z metadata.katalog."""
        katalog = (s.get("metadata") or {}).get("katalog", "")
        tail = katalog.rstrip(".").partition(" Nie do ")[2]
        if not tail:
            return short(s.get("description", ""))
        return s.get("description", "").rstrip(".") + ". Nie do " + (tail if len(tail) <= 110 else tail[:110].rsplit(" ", 1)[0] + "…")
    lines = ["# Katalog zespołu (generowany przez factory/build.py — nie edytuj)", "",
             "Do doboru skilli i person do problemu (skill core-problem-routing). Skill wczytujesz narzędziem Skill po nazwie.", ""]
    installed = cfg.get("_packs") or {}
    lines += ["Nakładki: " + (", ".join(f"`{pid}` ({p.get('title', '')})" for pid, p in installed.items()) or "brak — sam rdzeń"), ""]
    for f in cfg["facets"]:
        names = sorted(n for n in skills if n.startswith(f["prefix"]))
        if not names:
            continue
        lines += [f"## {f['name']} (`{f['prefix']}`) — {f['question']}", ""]
        lines += [f"- `{n}` — {entry(skills[n])}" for n in names] + [""]
    lines += ["## Persony (`claude --agent <nazwa>`) i ich wykonawcy", "",
              "| Persona | Nakładka | Kim jest | Wykonawcy (`persona-rola`) | Skille wiodące |", "|---|---|---|---|---|"]
    for pname in sorted(personas):
        p = personas[pname]
        workers = ", ".join(f"`{pname}-{r}`" for r in p["roles"]) or "—"
        lead = ", ".join((p.get("methods") or []) + (p.get("stack") or []) + (p.get("skills") or [])[:4]) or "—"
        lines.append(f"| `{pname}` | {p.get('_pack', '')} | {p['title']} | {workers} | {lead} |")
    lines += ["", "## Agenci wspólni", ""]
    for n, sp in cfg["shared_agents"].items():
        if n != "Explore":
            lines.append(f"- `{n}` ({sp['tier']}) — {sp['description']}")
    if cfg.get("consultants"):
        lines += ["", "## Konsultanci nakładek (tylko odpowiedź, bez zmian w plikach; wywołuje ich persona)", ""]
        lines += [f"- `{n}` ({sp['_pack']}, {sp['tier']}) — {sp['description']}" for n, sp in cfg["consultants"].items()]
    return "\n".join(lines) + "\n"


# ───────────────────────── walidacja ─────────────────────────

def _skill_profile():
    """factory/skill_profile.py — te same reguły widoczności opisów, które instalacja stosuje w projekcie."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ctf_skill_profile", FACTORY / "skill_profile.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def skill_listing(entries: dict[str, int], stack_slots: int, marked: set[str] = frozenset(),
                  name_only: tuple[str, ...] = ()) -> int:
    """Rozmiar listy skilli w typowym projekcie: wpisy z opisem wg skill_profile (stack pusty) + `stack_slots`
    najdłuższych wpisów technologii (fw-/lang-/tool-), które projekt może wykryć. `entries`: nazwa → znaki wpisu;
    `marked`: skille z `metadata.widocznosc: nazwa`."""
    sp = _skill_profile()
    base = sum(n for name, n in entries.items() if sp.desired(name, set(), name in marked, (), name_only) == "on")
    stack = sorted((n for name, n in entries.items() if name.startswith(sp.STACK_PREFIXES)), reverse=True)
    return base + sum(stack[:stack_slots])


def skill_usage(skills, used: set, cfg: dict) -> tuple[list[str], list[str]]:
    """Skille bez roli i persony. Wpisane w `standalone_skills` (wywoływane ręcznie, np. wiedza branżowa) nie
    dostają ostrzeżenia; nieznany wpis to błąd, a wpis skilla, którego persona już używa, jest zbędny."""
    standalone = cfg.get("standalone_skills") or []
    errors = [f"standalone_skills: nieznany skill '{s}'" for s in standalone if s not in skills]
    warnings = [f"skill {s}: nie jest używany przez żadną rolę ani personę" for s in skills
                if s not in used and s not in standalone and not s.startswith("core-")]   # core-* to biblioteka dla nakładek
    warnings += [f"skill {s}: używany przez rolę lub personę — zbędny wpis w standalone_skills" for s in standalone
                 if s in skills and s in used]
    return errors, warnings


def version_ok(version: str, spec: str) -> bool:
    """Prosty zakres SemVer: warunki `>=X.Y.Z`, `>X.Y.Z`, `<X.Y.Z`, `<=X.Y.Z`, `==X.Y.Z` oddzielone spacją."""
    def t(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in re.findall(r"\d+", v)[:3])
    ops = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b,
           "<": lambda a, b: a < b, "==": lambda a, b: a == b}
    for cond in str(spec).split():
        op = next((o for o in (">=", "<=", "==", ">", "<") if cond.startswith(o)), "==")
        if not ops[op](t(version), t(cond[len(op):] if cond.startswith(op) else cond)):
            return False
    return True


def check_packs(cfg: dict) -> tuple[list[str], list[str]]:
    """Zgodność nakładek z rdzeniem i między sobą: wersja rdzenia, wymagane nakładki, nakładka języka."""
    errors, warnings = [], []
    packs = cfg.get("_packs") or {}
    core_version = (FACTORY / "VERSION").read_text(encoding="utf-8").strip() if (FACTORY / "VERSION").exists() else "0.0.0"
    for pid, p in packs.items():
        if p.get("_dir") and p["_dir"].name != pid:
            errors.append(f"nakładka {pid}: katalog factory/packs/{p['_dir'].name} ≠ id")
        spec = (p.get("requires") or {}).get("core")
        if spec and not version_ok(core_version, spec):
            errors.append(f"nakładka {pid}: wymaga rdzenia {spec}, a zainstalowany jest {core_version} — "
                          f"zaktualizuj fabrykę (tf update) albo nakładkę")
        for dep in (p.get("requires") or {}).get("packs") or []:
            if dep not in packs:
                errors.append(f"nakładka {pid}: wymaga nakładki {dep} — tf add {dep}")
    lang = (cfg.get("_settings") or {}).get("language")
    need = ((cfg.get("languages") or {}).get(lang) or {}).get("pack")
    if need and need not in packs:
        warnings.append(f"język pracy {lang}: brak nakładki {need} (narzędzia redakcji) — tf add {need}")
    return errors, warnings


def validate() -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    cfg = load_config()
    lim = cfg["limits"]
    roles, personas, traits, skills, team_errors = load_team(cfg)
    personas_raw = load_dir("personas")
    errors += cfg.get("_errors") or []
    errors += team_errors
    for sub in ("roles", "personas"):
        warnings += packs_mod.load_items(ROOT, sub)[1]
    e, w = check_packs(cfg)
    errors += e
    warnings += w

    vocab = [v.lower() for v in cfg.get("vocabulary", [])]
    contract_prefixes = tuple(f["prefix"] for f in cfg["facets"] if f.get("contract"))
    for name, s in skills.items():
        if name.startswith(contract_prefixes):
            body = (SKILLS_DIR / s["_dir"] / "SKILL.md").read_text(encoding="utf-8")
            refs = " ".join(x.read_text(encoding="utf-8") for x in (SKILLS_DIR / s["_dir"]).glob("references/*.md"))
            if "## Pojęcia domenowe" not in body:
                errors.append(f"skill {name}: brak sekcji „## Pojęcia domenowe w …” (kontrakt skilli technologicznych)")
            else:
                missing = [v for v in vocab if v not in (body + refs).lower()]
                if missing:
                    warnings.append(f"skill {name}: słownik nie pokrywa pojęć: {', '.join(missing)}")
    versioned_prefixes = tuple(f["prefix"] for f in cfg["facets"] if f.get("versioned"))
    for name, s in skills.items():
        if name.startswith(versioned_prefixes) and name != "lang-javascript":
            meta_path = SKILLS_DIR / s["_dir"] / "skill.meta.json"
            if not meta_path.exists():
                errors.append(f"skill {name}: brak skill.meta.json (based_on, min_supported, sources) — potrzebny do synchronizacji wersji")
                continue
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f"skill {name}: skill.meta.json niepoprawny JSON ({e})"); continue
            for key in ("based_on", "min_supported", "sources", "verified"):
                if not meta.get(key):
                    errors.append(f"skill {name}: skill.meta.json bez pola '{key}'")
            if "## Zależne od wersji" not in (SKILLS_DIR / s["_dir"] / "SKILL.md").read_text(encoding="utf-8"):
                errors.append(f"skill {name}: brak sekcji „## Zależne od wersji” (co działa od której wersji)")
    registry = SKILLS_DIR / "core-stack-sync" / "references" / "technologies.json"
    if registry.exists():
        for t in json.loads(registry.read_text(encoding="utf-8")).get("technologies", []):
            if not t["skill"].startswith(skill_prefixes(cfg)):
                errors.append(f"technologies.json: skill '{t['skill']}' bez prefiksu wymiaru")
    for req_owner, reqs in (cfg.get("skill_requires") or {}).items():
        for r in [req_owner, *reqs]:
            if r not in skills:
                errors.append(f"skill_requires: nieznany skill '{r}'")
    for pname, prof in (cfg.get("profiles") or {}).items():
        for tier, over in ((prof or {}).get("tiers") or {}).items():
            if tier not in cfg["tiers"]:
                errors.append(f"profiles.{pname}: nieznany tier '{tier}'")
            elif (over or {}).get("model") and over["model"] not in ("haiku", "sonnet", "opus", "fable", "inherit") \
                    and not str(over["model"]).startswith("claude-"):
                errors.append(f"profiles.{pname}.{tier}: nieznany model '{over['model']}'")
    if cfg.get("profiles") and cfg.get("default_profile") not in cfg["profiles"]:
        errors.append(f"default_profile '{cfg.get('default_profile')}' nie ma w profiles")
    for a in cfg.get("always_skills") or []:
        if a not in skills:
            errors.append(f"always_skills: nieznany skill '{a}'")
    listing: dict[str, int] = {}
    gate = gate_registry()
    for name, s in skills.items():
        if name != s["_dir"]:
            errors.append(f"skill {s['_dir']}: name '{name}' ≠ nazwa folderu")
        if not name.startswith(skill_prefixes(cfg)):   # skill projektu spoza fabryki — nie oceniamy go regułami fabryki
            warnings.append(f"skill {name}: spoza fabryki (brak prefiksu wymiaru) — pominięty w walidacji; "
                            "żeby persona mogła go użyć, nadaj prefiks z factory/config.yaml → facets")
            continue
        d = s.get("description", "")
        katalog = (s.get("metadata") or {}).get("katalog", "")
        if not d:
            errors.append(f"skill {name}: brak description")
        elif len(d) > lim["skill_description_max_chars"]:
            errors.append(f"skill {name}: description ma {len(d)} znaków (> {lim['skill_description_max_chars']}) — "
                          "krótko co i kiedy; granice („Nie do …”) w metadata.katalog")
        if d and not re.search(r"\b(Użyj|użyj|gdy|kiedy|przy\s)", d):
            warnings.append(f"skill {name}: description nie jest regułą wyboru — zacznij od „Użyj, gdy/przy …”; Claude Code "
                            "pokazuje modelowi tylko description (pole metadata pomija)")
        e, w = check_review_date(name, s.get("metadata") or {})
        errors += e
        warnings += w
        if not katalog:
            warnings.append(f"skill {name}: brak metadata.katalog (pełny opis z granicami dla katalogu dyspozytora)")
        elif "nie" not in katalog.lower():
            warnings.append(f"skill {name}: metadata.katalog nie określa granic (czego skill NIE obejmuje)")
        if not s.get("disable-model-invocation"):
            listing[name] = len(name) + len(d) + 4
        if s.get("paths"):
            warnings.append(f"skill {name}: pole paths ukrywa skill przed modelem, dopóki w sesji nie ma pasującego pliku "
                            "(„Unknown skill” także przy jawnym wywołaniu) — usuń je; uruchamianie zapewnia hook skill_hint")
        if not any((ROOT / d / "skill_evals" / f"{name}.json").exists() for d in ("tests", ".claude/tests")):
            warnings.append(f"skill {name}: brak scenariuszy ewaluacji (tests/skill_evals/{name}.json, co najmniej 3) — "
                            "format w tests/skill_evals/README.md")
        if s.get("_chars", 0) > lim.get("skill_body_max_chars", 10**9):
            warnings.append(f"skill {name}: SKILL.md ma {s['_chars']} znaków (> {lim['skill_body_max_chars']}) — po "
                            "kompaktowaniu Claude Code przywraca najwyżej ~5000 tokenów skilla; przenieś szczegóły do references/")
        rec = gate.get(name)
        if not rec:
            warnings.append(f"skill {name}: nie przeszedł bramki jakości — python3 factory/skill_gate.py {name}")
        elif rec.get("fingerprint") != skill_fingerprint(s["_dir"]):
            warnings.append(f"skill {name}: zmieniony po ostatniej bramce — python3 factory/skill_gate.py {name}")
        if s["_lines"] > 300:
            warnings.append(f"skill {name}: SKILL.md ma {s['_lines']} linii — przenieś szczegóły do references/")

    marked = {n for n, s in skills.items() if (s.get("metadata") or {}).get("widocznosc") == "nazwa"}
    size = skill_listing(listing, lim.get("skill_listing_stack_slots", 6), marked,
                         tuple(cfg["skill_visibility"]["name_only_prefixes"]))
    if size > lim.get("skill_listing_max_chars", 10**9):
        warnings.append(f"lista skilli z opisem w typowym projekcie ma ≈{size} znaków (> {lim['skill_listing_max_chars']}): "
                        "skille z opisem wg factory/skill_profile.py + rezerwa na wykryte technologie. Claude Code trzyma listę "
                        "w ~1% okna kontekstu i przy przepełnieniu usuwa opisy najrzadziej używanych skilli — skróć opisy, "
                        "przenieś rzadko potrzebne skille do sam-nazwa (reguły w skill_profile.py) albo ustaw "
                        "disable-model-invocation dla skilli uruchamianych ręcznie (`/doctor` pokaże koszt)")
    for t, body in traits.items():
        if body.count("\n") + 1 > lim["trait_max_lines"]:
            errors.append(f"trait {t}: za długi (> {lim['trait_max_lines']} linii) — cechy mają być krótkie")

    def check_skills(owner: str, names: list[str]):
        for s in names or []:
            if s not in skills:
                errors.append(f"{owner}: nieznany skill '{s}'")

    def check_tools(owner: str, tools: list[str]):
        for t in tools or []:
            base = t.split("(")[0]
            if base not in KNOWN_TOOLS and not base.startswith("mcp__"):
                errors.append(f"{owner}: nieznane narzędzie '{t}'")

    for tier_owner, tier in [(f"rola {n}", r.get("tier")) for n, r in roles.items()] + \
                            [(f"shared {n}", s.get("tier")) for n, s in cfg["shared_agents"].items()] + \
                            [(f"konsultant {n}", s.get("tier", "std")) for n, s in cfg["consultants"].items()]:
        if tier not in cfg["tiers"]:
            errors.append(f"{tier_owner}: nieznany tier '{tier}'")

    for n, r in roles.items():
        check_skills(f"rola {n}", r.get("skills"))
        check_skills(f"rola {n} (preload)", r.get("preload"))
        check_tools(f"rola {n}", r.get("tools"))
        if "Agent" in (r.get("tools") or []):
            warnings.append(f"rola {n}: wykonawca z narzędziem Agent może zagnieżdżać subagentów (koszt)")
    for n, s in cfg["shared_agents"].items():
        check_skills(f"shared {n}", s.get("skills"))
        check_tools(f"shared {n}", s.get("tools"))
        for pn in s.get("only_for") or []:
            if pn not in personas_raw and pn != "@dispatcher" and s.get("_pack") in ("core", None):
                errors.append(f"shared {n}: only_for wskazuje nieznaną personę '{pn}'")
            elif pn not in personas_raw and pn != "@dispatcher":
                warnings.append(f"shared {n} ({s['_pack']}): only_for wskazuje personę '{pn}', której nie ma w projekcie")
    for n, c in cfg["consultants"].items():
        check_skills(f"konsultant {n} ({c['_pack']})", c.get("skills"))
        if not c.get("description"):
            errors.append(f"konsultant {n}: brak description")
        if n in cfg["shared_agents"]:
            errors.append(f"konsultant {n}: ta sama nazwa co agent wspólny")

    used = set()
    for pname, p in personas.items():
        for r in p.get("roles", []):
            if r not in roles:
                errors.append(f"persona {pname}: nieznana rola '{r}'")
            else:
                used.update(roles[r]["skills"])
        for t in p.get("traits", []):
            if t not in traits:
                errors.append(f"persona {pname}: nieznana cecha '{t}'")
        check_skills(f"persona {pname}", p.get("core_skills"))
        check_skills(f"persona {pname} (methods)", p.get("methods"))
        check_skills(f"persona {pname} (stack)", p.get("stack"))
        check_skills(f"persona {pname} (skills)", p.get("skills"))
        check_skills(f"persona {pname} (drop_skills)", p.get("drop_skills"))
        for r, extra in (p.get("role_skills") or {}).items():
            if r not in p.get("roles", []):
                errors.append(f"persona {pname}: role_skills dla roli '{r}', której persona nie ma")
            check_skills(f"persona {pname} (role_skills.{r})", extra)
        used.update((p.get("skills") or []) + (p.get("methods") or []) + (p.get("stack") or []) + (p.get("core_skills") or []))
        if not any(r in roles for r in p.get("roles", [])):
            continue
        used.update(persona_skills(p, roles, cfg))
        if not p.get("priorities"):
            errors.append(f"persona {pname}: brak priorities (potrzebne do rozstrzygania konfliktów)")
    for s in [*cfg["shared_agents"].values(), *cfg["consultants"].values()]:
        used.update(s.get("skills") or [])
    used.update(cfg.get("always_skills") or [])
    e, w = skill_usage(skills, used, cfg)
    errors += e
    warnings += w

    if not errors:
        rendered = render_all()
        names = [re.search(r"^name: (.+)$", t, re.M).group(1) for t in rendered.values()]
        for rel, t in rendered.items():
            if not t.startswith("---\n"):
                errors.append(f"{rel}: frontmatter musi zaczynać się w 1. linii (inaczej Claude Code pominie plik)")
        dup = {n for n in names if names.count(n) > 1}
        if dup:
            errors.append(f"zduplikowane nazwy agentów: {sorted(dup)}")
        desc_chars = sum(len(m.group(1)) for t in rendered.values()
                         for m in [re.search(r"^description: (.+)$", t, re.M)] if m)
        est = int(desc_chars / 3.5)
        hard = lim.get("agent_descriptions_hard_tokens", 15000)
        if est > hard:
            errors.append(f"opisy agentów ≈{est} tokenów (> {hard}, limit Claude Code) — skróć description albo "
                          "zainstaluj mniej nakładek")
        elif est > lim["agent_descriptions_max_tokens"]:
            warnings.append(f"opisy agentów ≈{est} tokenów (> zapasu {lim['agent_descriptions_max_tokens']}) — każda "
                            "nakładka dokłada person i konsultantów; rozważ mniej nakładek albo krótsze description")
        # nieaktualne pliki
        on_disk = {str(p.relative_to(OUT_DIR)): p.read_text(encoding="utf-8")
                   for p in OUT_DIR.rglob("*.md")} if OUT_DIR.exists() else {}
        if on_disk != rendered:
            errors.append("pliki w .claude/agents/_generated są nieaktualne — uruchom: python3 factory/build.py")
        if not CATALOG.exists() or CATALOG.read_text(encoding="utf-8") != render_catalog():
            errors.append(".claude/catalog.md jest nieaktualny — uruchom: python3 factory/build.py")
        stale = [p.relative_to(ROOT).as_posix() for p in reference_files()
                 if with_toc(p.read_text(encoding="utf-8")) != p.read_text(encoding="utf-8")]
        if stale:
            errors.append(f"brak lub nieaktualny spis treści w {len(stale)} plikach referencyjnych (np. {stale[0]}) — "
                          "uruchom: python3 factory/build.py")
        for pname, p in personas.items():
            for x in p.get("extra_agents") or []:
                if not any(k.endswith(f"/{x}.md") for k in rendered):
                    errors.append(f"persona {pname}: extra_agents wskazuje nieznanego agenta '{x}'")
    # Archetypy w stylu mappera: stałe sekcje, w stałej kolejności (poza blokami kodu)
    arch_dir = SKILLS_DIR / "ddd-archetypes" / "references"
    required = ["Test dopasowania", "Model (istota)", "Pytania", "Kroki mapowania", "Decyzje do kontroli (R/A/X)",
                "Format wyniku", "Wzorce i pułapki", "Kontrola jakości", "Przykład (skrócony)"]
    if arch_dir.exists():
        for f in sorted(arch_dir.glob("*.md")):
            if f.name == "layers.md":
                continue
            heads, fence = [], False
            for ln in f.read_text(encoding="utf-8").splitlines():
                if ln.startswith("```"):
                    fence = not fence
                elif not fence and ln.startswith("## "):
                    heads.append(ln[3:].strip())
            found = [h for h in heads if h in required]
            if found != required:
                missing = [h for h in required if h not in heads]
                errors.append(f"ddd-archetypes/references/{f.name}: sekcje mappera "
                              + (f"brakujące {missing}" if missing else "w złej kolejności"))

    # wersja fabryki wg SemVer 2.0.0 (factory/PUBLIC_API.md): VERSION, kolejność CHANGELOG, rodzaj podbicia od 1.35.0
    sv_path = SKILLS_DIR / "core-semver" / "scripts" / "semver.py"
    if sv_path.exists() and (FACTORY / "CHANGELOG.md").exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("ctf_semver", sv_path)
        sv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sv)
        version = (FACTORY / "VERSION").read_text(encoding="utf-8").strip() if (FACTORY / "VERSION").exists() else None
        if version:
            try:
                sv.Version(version)
            except ValueError as e:
                errors.append(f"factory/VERSION: {e}")
        for p in sv.check_changelog((FACTORY / "CHANGELOG.md").read_text(encoding="utf-8"), version,
                                    cfg.get("semver_strict_from")):
            errors.append(f"factory/CHANGELOG.md: {p}")
    return errors, warnings


# ───────────────────────── komendy ─────────────────────────

def cmd_build():
    rendered = render_all()
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    for rel, txt in rendered.items():
        p = OUT_DIR / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")
    CATALOG.write_text(render_catalog(), encoding="utf-8")
    tocs = 0
    for ref in reference_files():
        old = ref.read_text(encoding="utf-8")
        new = with_toc(old)
        if new != old:
            ref.write_text(new, encoding="utf-8")
            tocs += 1
    if tocs:
        print(f"✓ Spisy treści zaktualizowane w {tocs} plikach referencyjnych")
    print(f"✓ Wygenerowano {len(rendered)} agentów w {OUT_DIR.relative_to(ROOT)} i katalog {CATALOG.relative_to(ROOT)}"
          f" (profil kosztów: {load_config()['_profile']})")
    errors, warnings = validate()
    for w in warnings:
        print(f"  ⚠ {w}")
    for e in errors:
        print(f"  ✗ {e}")
    return 1 if errors else 0


def cmd_check():
    errors, warnings = validate()
    for w in warnings:
        print(f"⚠ {w}")
    for e in errors:
        print(f"✗ {e}")
    print("✓ OK" if not errors else f"✗ {len(errors)} błędów")
    return 1 if errors else 0


def cmd_list():
    cfg = load_config()
    roles, personas, _traits, _skills, _errors = load_team(cfg)
    st = cfg["_settings"]
    print(f"Nakładki: {', '.join(cfg['_packs']) or '— (sam rdzeń)'} · język pracy: {st['language']} · "
          f"commity: {st['commit_language']}")
    for pname, p in personas.items():
        print(f"\n{p['title']}  →  claude --agent {pname}   [{p.get('_pack')}]")
        print(f"  cechy: {', '.join(p['traits'])}")
        all_sk = persona_skills(p, roles, cfg)
        tech = [x for x in all_sk if x.startswith(("lang-", "fw-", "tool-"))]
        meth = [x for x in all_sk if x.startswith("ddd-")]
        print(f"  metody: {', '.join(meth) or '—'}")
        print(f"  stack:  {', '.join(tech) or '— (agnostyczna)'}")
        for r in p["roles"]:
            role = roles[r]
            extra = (p.get("role_skills") or {}).get(r)
            print(f"  • {pname}-{r:<12} {role['tier']:<5} {cfg['tiers'][role['tier']]['model']:<7} rola: {', '.join(role['skills'])}"
                  + (f" + {', '.join(extra)}" if extra else ""))
        if p.get("_dropped"):
            print(f"  pominięte (brak nakładki opcjonalnej): {', '.join(p['_dropped'])}")
        consult = consultants_for(p, cfg)
        if consult:
            print(f"  konsultanci: {', '.join(consult)}")
    print("\nWspólni: " + ", ".join(f"{n} ({s['tier']})" for n, s in cfg["shared_agents"].items()))
    return 0


def _freshness():
    import importlib.util
    spec = importlib.util.spec_from_file_location("ctf_freshness_build", FACTORY / "freshness.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_new_skill(name: str, description: str, role: str | None = None, name_only: bool = False):
    cfg = load_config()
    if not name.startswith(skill_prefixes(cfg)):
        print(f"✗ Nazwa musi zaczynać się od prefiksu wymiaru: {skill_prefixes(cfg)}")
        return 2
    d = SKILLS_DIR / name
    if d.exists():
        print(f"✗ Skill {name} już istnieje")
        return 2
    roles = load_dir("roles") if role else {}
    role_file = ROOT / roles[role]["_src"] if role in roles else None
    if role and not role_file:
        print(f"✗ Nie ma roli {role} (factory/roles/ ani factory/packs/*/roles/)")
        return 2
    tpl = (FACTORY / "templates" / "SKILL.template.md").read_text(encoding="utf-8")
    (d / "references").mkdir(parents=True)
    short = description.split(" Nie do ")[0].strip()[:170].replace(": ", " — ")   # do skrócenia przez autora
    body = (tpl.replace("{{name}}", name).replace("{{short}}", short)
            .replace("{{description}}", description.replace('"', "'")))
    facet = facet_of(name, cfg)
    if facet.get("contract"):
        rows = "\n".join(f"| **{v}** | … |" for v in cfg.get("vocabulary", []))
        body += (f"\n## Pojęcia domenowe w {name.split('-', 1)[1]}\n"
                 f"<!-- Kontrakt: każde pojęcie ze słownika → idiom tej technologii. Sprawdzane przez `build.py check`. -->\n"
                 f"| Pojęcie (słownik) | Idiom |\n|---|---|\n{rows}\n")
    import datetime as _dt
    fr = _freshness()
    due = fr.add_months(_dt.date.today(), fr.interval(name, fr.load_policy(ROOT))).isoformat()
    extra = f"  przeglad: {due}\n  slowa: \"\"\n" + ("  widocznosc: nazwa\n" if name_only else "")
    body = re.sub(r"^(  katalog: .*\n)", lambda m: m.group(1) + extra, body, count=1, flags=re.M)
    (d / "SKILL.md").write_text(body, encoding="utf-8")
    wired = ""
    if role_file:
        text = role_file.read_text(encoding="utf-8")
        m = re.search(r"^skills: \[(.*)\]$", text, re.M)
        if m:
            items = [x.strip() for x in m.group(1).split(",") if x.strip()]
            new_line = "skills: [" + ", ".join(items + [name]) + "]"
            role_file.write_text(text[:m.start()] + new_line + text[m.end():], encoding="utf-8")
            wired = f"✓ Dopisano do {roles[role]['_src']} (skills)\n"
        else:
            wired = f"⚠ {roles[role]['_src']} nie ma listy „skills: [...]” w jednej linii — dopisz {name} ręcznie\n"
    ev = evals_file(name)
    if not ev.exists():
        ev.parent.mkdir(parents=True, exist_ok=True)
        todo = {"skill": name, "scenarios": [
            {"id": "TODO-problem-1", "expect": "trigger",
             "prompt": "TODO: prawdziwe pytanie użytkownika, z którym model bez skilla radzi sobie źle",
             "checks": {"all": [["TODO: fraza wiedzy specyficznej dla skilla", "TODO: synonim"],
                                ["TODO: druga, niezależna rzecz, którą odpowiedź musi zawierać"]],
                        "none": ["TODO: typowy błąd, którego odpowiedź nie może zawierać"]}},
            {"id": "TODO-problem-2", "expect": "trigger",
             "prompt": "TODO: ten sam obszar, inne słowa (tak, jak pyta człowiek, nie jak opis skilla)",
             "checks": {"all": [["TODO"], ["TODO"]]}},
            {"id": "TODO-sasiad", "expect": "no-trigger", "neighbor": "TODO-nazwa-sasiedniego-skilla",
             "prompt": "TODO: pytanie z pogranicza, które należy do sąsiedniego skilla"}]}
        ev.write_text(json.dumps(todo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rel = ev.relative_to(ROOT)
    print(wired + f"""✓ Utworzono .claude/skills/{name}/SKILL.md (termin przeglądu {due}) i szkielet scenariuszy {rel}
Dalej (skill core-skill-authoring):
  1. NAJPIERW scenariusze w {rel}: 2× trigger z luką, którą model ma bez skilla, 1× no-trigger z sąsiadem.
  2. Opcjonalnie punkt odniesienia: python3 {TESTS_REL}/run_skill_evals.py --skills {name} --models sonnet --baseline
  3. Treść SKILL.md — minimum, które zamyka luki; szczegóły do references/.
  4. Dopisz skill do roli w factory/roles/ i uruchom python3 factory/build.py
  5. Bramka: python3 factory/skill_gate.py {name}   (+ --model haiku,sonnet za zgodą człowieka — płatne)""")
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "build"
    if cmd == "build":
        return cmd_build()
    if cmd == "check":
        return cmd_check()
    if cmd == "list":
        return cmd_list()
    if cmd == "new-skill" and len(argv) >= 4:
        rest = argv[4:]
        role = rest[rest.index("--role") + 1] if "--role" in rest and rest.index("--role") + 1 < len(rest) else None
        return cmd_new_skill(argv[2], argv[3], role=role, name_only="--name-only" in rest)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
