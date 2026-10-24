#!/usr/bin/env python3
"""
Target `managed-agents`: persony, wykonawcy i agenci wspólni fabryki jako pliki dla `ant apply`
(Claude Managed Agents). Włączasz go w `.claude/factory-settings.json`: `"targets": ["claude", "managed-agents"]`;
`python3 factory/build.py` zapisuje wtedy katalog `managed-agents/`:

  managed-agents/agents/<agent>.md        frontmatter YAML = konfiguracja agenta, treść = prompt systemowy
  managed-agents/environments/default.yaml środowisko chmurowe z ograniczoną siecią
  managed-agents/README.md                jak wgrać (`ant apply`) i czym ten target różni się od Claude Code

Skille nie są kopiowane: agent wskazuje katalogi `.claude/skills/<skill>` ścieżką względną, a `ant apply` wgrywa je
jako skille własne. Persona jest koordynatorem z rosterem podagentów (`multiagent`), wykonawcy i agenci wspólni są
członkami rosteru (jeden poziom delegowania). Moduł tylko renderuje; zapis i kontrolę aktualności robi build.py.
Format: skill `claude-api` (shared/anthropic-cli.md, managed-agents-core.md, -tools.md, -multiagent.md), 2026-10-24.
"""
from __future__ import annotations

import re
import shutil
import subprocess

OUT = "managed-agents"
SKILLS_FROM_AGENT = "../../.claude/skills"   # z managed-agents/agents/<plik>.md do .claude/skills/
MARK = "WYGENEROWANO przez factory/build.py — nie edytuj ręcznie."
ROSTER_LIMIT = 20                             # maks. pozycji `predefined_agents`
SKILLS_LIMIT = 500                            # maks. skilli na sesję, liczone raz dla wszystkich agentów
TOOLSET = "agent_toolset_20260401"
TOOL_NAMES = ["bash", "read", "write", "edit", "glob", "grep", "web_fetch", "web_search"]
CLAUDE_TOOLS = {"Bash": "bash", "Read": "read", "Write": "write", "Edit": "edit", "Glob": "glob", "Grep": "grep",
                "WebFetch": "web_fetch", "WebSearch": "web_search"}
MODEL_IDS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5",
             "fable": "claude-fable-5-1", "inherit": "claude-opus-5-5"}

ENVIRONMENT = """# {mark} Źródło: factory/target_managed.py
name: tf-default
config:
  type: cloud
  networking:
    type: limited
    allow_package_managers: true
"""

ENV_NOTE = """## Środowisko Managed Agents
Pracujesz jako agent Claude Managed Agents, nie w Claude Code. Różnice wobec reszty tego promptu:
- Skille z listy są dołączone do Ciebie i wczytujesz je, gdy zadanie ich dotyczy — nie ma narzędzia Skill.
- Delegujesz do agentów z Twojego rosteru podagentów (nazwy jak w tabeli zespołu); agenta spoza rosteru nie ma.
  Podagent nie widzi tej rozmowy — w zadaniu podajesz ścieżki, ograniczenia i format raportu.
- Pliki projektu są w kontenerze sesji tylko wtedy, gdy sesja zamontowała repozytorium. Skrypty z `.claude/hooks/`
  uruchamiasz sam, jeśli są w kontenerze; hooki fabryki (TDD, ochrona ścieżek, logi) tu nie działają — testy,
  bramki i weryfikację uruchamiasz sam przed raportem.
- Commit, push i publikację robisz tylko wtedy, gdy zadanie sesji wprost o to prosi.
"""

README = """# Managed Agents — wygenerowane przez fabrykę

Pliki w `agents/`, `environments/default.yaml` i ten README generuje `python3 factory/build.py` (target
`managed-agents` w `.claude/factory-settings.json`). Nie edytuj ich ręcznie — zmiany wprowadzaj w `factory/`.
`claude-lock.json`, który zapisuje `ant apply`, należy do Ciebie: commitujesz go, fabryka go nie zmienia.

## Wgranie
Wymaga `ant` ≥ 1.40.0 (ścieżki plików w `predefined_agents`). Budowa fabryki niczego nie wysyła — wgranie na
konto organizacji to osobne, jawne polecenie (z katalogu głównego projektu):

```sh
python3 factory/build.py managed-apply         # plan: agenci, środowisko i skille z .claude/skills/ — nic nie wysyła
python3 factory/build.py managed-apply --yes   # wgranie, po przejrzeniu planu
```

To samo bezpośrednio: `cd managed-agents && ant apply --dry-run agents environments` (plan),
`ant apply --yes agents environments` (wgranie). W CI uruchamiaj tylko plan.

Sesja z personą (identyfikatory z `claude-lock.json`):

```sh
AGENT_ID=$(jq -r '.resources["./agents/{example}.md"].id' claude-lock.json)
ENV_ID=$(jq -r '.resources["./environments/default.yaml"].id' claude-lock.json)
ant beta:sessions create --agent "$AGENT_ID" --environment-id "$ENV_ID" --title "Zadanie"
```

Pliki projektu agent widzi po zamontowaniu repozytorium jako zasobu sesji (`github_repository`); skille z
`.claude/skills/` tego repozytorium są wtedy dostępne także bez wgrywania.

## Różnice wobec Claude Code
- Persona jest koordynatorem z rosterem podagentów (maks. {roster} pozycji, jeden poziom delegowania); wykonawcy
  i agenci wspólni nie delegują dalej. Pozycje ponad limit pomija `build.py check` z ostrzeżeniem.
- Dynamiczne workflows są wyłączone (koszt). Włączenie: `workflows: {{type: enabled}}` w pliku persony przez
  zmianę w fabryce, z budżetem sesji.
- Hooki fabryki (TDD, ochrona ścieżek, logi, start sesji) nie działają; agent uruchamia testy i bramki sam.
- Modele z tierów: {models}.
- Narzędzia: `{toolset}` z polityką `auto`; narzędzia sieciowe tylko tam, gdzie rola ma WebFetch/WebSearch.
"""


def model_spec(cfg: dict, tier: str) -> dict:
    t = cfg["tiers"][tier]
    ids = {**MODEL_IDS, **((cfg.get("managed_agents") or {}).get("models") or {})}
    m = str(t["model"])
    out = {"id": m if m.startswith("claude-") else ids.get(m, ids["inherit"])}
    if t.get("effort") and m != "inherit":
        out["effort"] = t["effort"]
    return out


def toolset(tools: list[str]) -> list[dict]:
    on = {CLAUDE_TOOLS[t] for t in tools if t in CLAUDE_TOOLS}
    return [{"type": TOOLSET, "default_config": {"enabled": False, "permission_policy": {"type": "auto"}},
             "configs": [{"name": n, "enabled": n in on} for n in TOOL_NAMES]}]


def skill_paths(skills: list[str]) -> list[str]:
    return [f"{SKILLS_FROM_AGENT}/{s}" for s in skills]


def roster(groups: list[list[str]], limit: int = ROSTER_LIMIT) -> tuple[list[str], list[str]]:
    seen = list(dict.fromkeys(n for g in groups for n in g))
    return seen[:limit], seen[limit:]


def description(text: str) -> str:
    """Opis bez wskazówki uruchomienia w Claude Code („Uruchom przez `claude --agent …`” do końca zdania)."""
    return re.sub(r"\s*Uruchom przez `claude --agent [^`]*`[^.]*\.", "", text).strip()


def system_prompt(claude_doc: str) -> str:
    """Treść pliku agenta Claude Code bez frontmattera i komentarza nagłówka."""
    body = claude_doc.split("\n---\n", 1)[1] if claude_doc.startswith("---\n") else claude_doc
    body = re.sub(r"^<!-- WYGENEROWANO przez factory/build\.py[^\n]*-->\n", "", body)
    return body.lstrip("\n")


def agent_doc(fields: dict, system: str, src: str, yaml=None) -> str:
    if yaml is None:
        import packs as packs_mod   # factory/packs.py: PyYAML systemowy albo z factory/_vendor
        yaml = packs_mod.yaml
    head = yaml.safe_dump({k: v for k, v in fields.items() if v not in (None, "", [], {})},
                          allow_unicode=True, sort_keys=False, width=1000)
    return f"---\n# {MARK} Źródło: {src}\n{head}---\n{system}"


def apply(d, yes: bool = False, run=subprocess.run, which=shutil.which) -> int:
    """Jedyne miejsce, które wysyła coś na konto: `ant apply` w katalogu targetu. Bez `yes` — tylko plan
    (`--dry-run`), z `yes` — wgranie. Budowa (`build.py`) i kontrola (`build.py check`) nigdy tego nie wywołują."""
    if not ((d / "agents").is_dir() and (d / "environments").is_dir()):
        print(f"✗ brak plików targetu w {d} — włącz target managed-agents i uruchom: python3 factory/build.py")
        return 2
    ant = which("ant")
    if not ant:
        print("✗ brak polecenia ant (Anthropic CLI ≥ 1.40.0) — instalacja: managed-agents/README.md")
        return 2
    argv = [ant, "apply", "--yes" if yes else "--dry-run", "agents", "environments"]
    if not yes:
        print("Plan (nic nie zostanie wysłane). Wgranie: python3 factory/build.py managed-apply --yes")
    return run(argv, cwd=d).returncode


def _generated(d) -> dict[str, str]:
    """Pliki fabryki w katalogu targetu: ze znacznikiem w treści albo README tego targetu."""
    out = {}
    for p in sorted(d.rglob("*")) if d.exists() else []:
        if p.is_file() and p.suffix in (".md", ".yaml"):
            text = p.read_text(encoding="utf-8")
            if MARK in text.split("\n---\n", 1)[0] or text.startswith(README.split("\n", 1)[0]):
                out[p.relative_to(d).as_posix()] = text
    return out


def stale(d, files: dict[str, str]) -> list[str]:
    """Ścieżki do zapisu lub usunięcia, żeby katalog `d` odpowiadał `files`."""
    disk = _generated(d)
    changed = [k for k, v in files.items() if not (d / k).is_file() or (d / k).read_text(encoding="utf-8") != v]
    return changed + [k for k in disk if k not in files]


def write(d, files: dict[str, str]) -> None:
    """Zapisuje pliki targetu; usuwa tylko wcześniej wygenerowane, których już nie ma. Reszty nie dotyka."""
    for k in _generated(d):
        if k not in files:
            (d / k).unlink()
    for k, v in files.items():
        p = d / k
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(v, encoding="utf-8")


def render(b) -> tuple[dict[str, str], list[str], list[str]]:
    """Pliki targetu (ścieżki względem managed-agents/), ostrzeżenia i błędy. `b` — moduł build.py."""
    cfg = b.load_config()
    roles, personas, _traits, _skills, _errors = b.load_team(cfg)
    claude = b.render_all()
    files, warnings, errors = {}, [], []
    meta = {"generated_by": "tf factory/build.py"}
    agents: dict[str, dict] = {}   # nazwa → frontmatter (do liczenia skilli w sesji)

    def add(name: str, fields: dict, claude_key: str, src: str, note: bool = False) -> None:
        system = system_prompt(claude[claude_key])
        if note:
            system = system.rstrip("\n") + "\n\n" + ENV_NOTE
        fields = {"name": name, **fields, "metadata": meta}
        fields["description"] = description(fields.get("description") or "")
        agents[name] = fields
        files[f"agents/{name}.md"] = agent_doc(fields, system, src, b.yaml)

    for n, spec in cfg["shared_agents"].items():
        if n == "Explore" or spec.get("main_only"):
            continue
        add(n, {"description": spec["description"], "model": model_spec(cfg, spec["tier"]),
                "tools": toolset(spec["tools"]), "skills": skill_paths(spec.get("skills") or [])},
            f"shared/{n}.md", "factory/config.yaml")
    for n, spec in cfg["consultants"].items():
        add(n, {"description": spec["description"], "model": model_spec(cfg, spec.get("tier", "std")),
                "tools": toolset(b.CONSULT_TOOLS), "skills": skill_paths(spec.get("skills") or [])},
            f"consult/{n}.md", f"factory/packs/{spec['_pack']}/pack.yaml")
    for pname, p in personas.items():
        for r in p["roles"]:
            role = roles[r]
            add(f"{pname}-{r}", {"description": f"{role['title']} w zespole {pname}. Deleguj: {role['triggers']}.",
                                 "model": model_spec(cfg, role["tier"]), "tools": toolset(role["tools"]),
                                 "skills": skill_paths(b.team_skills(p, role, cfg))},
                f"{pname}/{pname}-{r}.md", f"{p['_src']} + {role['_src']}", note=True)
    for pname, p in personas.items():
        team = [f"{pname}-{r}" for r in p["roles"]]
        names, dropped = roster([team, b.shared_for(p, cfg), list(b.consultants_for(p, cfg)),
                                 list(p.get("extra_agents") or [])])
        unknown = [n for n in names if n not in agents]
        if unknown:
            errors.append(f"managed-agents: persona {pname} wskazuje agentów bez pliku: {', '.join(unknown)}")
        if dropped:
            warnings.append(f"managed-agents: persona {pname} — roster ponad {ROSTER_LIMIT} pozycji, pominięci: "
                            f"{', '.join(dropped)}")
        ma = {"type": "multiagent_20261001",
              "subagents": {"type": "enabled", "predefined_agents": [f"./{n}.md" for n in names],
                            "inline_agents": {"type": "disabled"}},
              "workflows": {"type": "disabled"}}
        add(pname, {"description": p["description"], "model": model_spec(cfg, p.get("model_tier", "std")),
                    "tools": toolset(["Read", "Grep", "Glob", "Edit", "Write", "Bash"]),
                    "skills": skill_paths(b.persona_skills(p, roles, cfg)), "multiagent": ma},
            f"{pname}/{pname}.md", p["_src"], note=True)
        session = {s for n in [pname, *names] if n in agents for s in agents[n].get("skills") or []}
        if len(session) > SKILLS_LIMIT:
            errors.append(f"managed-agents: persona {pname} — {len(session)} skilli w sesji (> {SKILLS_LIMIT})")
    files["environments/default.yaml"] = ENVIRONMENT.format(mark=MARK)
    tiers = ", ".join(f"{t} → `{model_spec(cfg, t)['id']}`" for t in cfg["tiers"])
    files["README.md"] = README.format(example=next(iter(personas), "persona"), roster=ROSTER_LIMIT, models=tiers,
                                       toolset=TOOLSET)
    return files, warnings, errors
