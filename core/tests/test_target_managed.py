#!/usr/bin/env python3
"""Testy target_managed.py: persony fabryki jako pliki `ant apply` (Claude Managed Agents)."""
import importlib.util
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "factory" / "build.py").is_file())
sys.dont_write_bytecode = True


def load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "factory" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def split(doc: str, yaml):
    """Plik agenta → (frontmatter jako dict, prompt systemowy)."""
    assert doc.startswith("---\n"), doc[:40]
    head, _, body = doc[4:].partition("\n---\n")
    return yaml.safe_load(head), body


def main() -> int:
    b = load("ctf_build_tm", "build.py")
    tm = load("ctf_target_managed", "target_managed.py")
    yaml = b.yaml
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # Model z tieru: alias → identyfikator, effort z tieru, pełny identyfikator bez zmian, nadpisanie mapy.
    cfg = {"tiers": {"fast": {"model": "haiku", "effort": "low"}, "std": {"model": "sonnet", "effort": "medium"},
                     "deep": {"model": "claude-opus-5", "effort": "high"}, "x": {"model": "inherit"}}}
    check(tm.model_spec(cfg, "fast") == {"id": "claude-haiku-5-5", "effort": "low"}, f"MO-1: {tm.model_spec(cfg, 'fast')}")
    check(tm.model_spec(cfg, "deep") == {"id": "claude-opus-5", "effort": "high"}, f"MO-2: {tm.model_spec(cfg, 'deep')}")
    check(tm.model_spec(cfg, "x") == {"id": "claude-opus-5-5"}, f"MO-3 inherit bez effort: {tm.model_spec(cfg, 'x')}")
    cfg2 = dict(cfg, managed_agents={"models": {"sonnet": "claude-sonnet-5"}})
    check(tm.model_spec(cfg2, "std")["id"] == "claude-sonnet-5", f"MO-4 nadpisanie mapy: {tm.model_spec(cfg2, 'std')}")

    # Toolset: tylko znane narzędzia włączone, web jawnie wyłączony, polityka auto.
    ts = tm.toolset(["Read", "Grep", "Glob", "Skill", "Agent"])
    check(len(ts) == 1 and ts[0]["type"] == "agent_toolset_20260401", f"TS-1: {ts}")
    conf = {c["name"]: c["enabled"] for c in ts[0]["configs"]}
    check(conf == {"bash": False, "read": True, "write": False, "edit": False, "glob": True, "grep": True,
                   "web_fetch": False, "web_search": False}, f"TS-2 jawna lista wszystkich ośmiu: {conf}")
    check(ts[0]["default_config"] == {"enabled": False, "permission_policy": {"type": "auto"}}, f"TS-3: {ts[0]}")
    conf = {c["name"]: c["enabled"] for c in tm.toolset(["Bash", "Edit", "Write", "WebFetch"])[0]["configs"]}
    check(conf["bash"] and conf["edit"] and conf["write"] and conf["web_fetch"] and not conf["web_search"],
          f"TS-4: {conf}")

    # Skille jako ścieżki względem managed-agents/agents/<plik>.md.
    check(tm.skill_paths(["lang-go", "core-grounding"]) == ["../../.claude/skills/lang-go",
                                                           "../../.claude/skills/core-grounding"],
          f"SK-1: {tm.skill_paths(['lang-go', 'core-grounding'])}")

    # Roster: kolejność grup, bez powtórzeń, limit 20 i lista pominiętych.
    names, dropped = tm.roster([["a-x", "a-y"], ["scout", "a-x"], [f"e{i}" for i in range(25)]])
    check(names[:3] == ["a-x", "a-y", "scout"] and len(names) == 20 and dropped == [f"e{i}" for i in range(17, 25)],
          f"RO-1: {names} {dropped}")

    # Prompt z pliku Claude Code: bez frontmattera i komentarza nagłówka.
    doc = "---\nname: x\ndescription: \"d\"\n---\n<!-- WYGENEROWANO przez factory/build.py — nie edytuj ręcznie. Źródło: s -->\n\n# Tytuł\ntreść\n"
    check(tm.system_prompt(doc) == "# Tytuł\ntreść\n", f"SP-1: {tm.system_prompt(doc)!r}")

    # Opis bez wskazówki uruchomienia w Claude Code.
    check(tm.description("Persona backend. Uruchom przez `claude --agent dorota`.") == "Persona backend.",
          f"DE-1: {tm.description('Persona backend. Uruchom przez `claude --agent dorota`.')!r}")
    check(tm.description("Persona X. Uruchom przez `claude --agent x`; orkiestruje zespół x-*.") == "Persona X.",
          "DE-2: wariant ze średnikiem")
    check(tm.description("Bez wskazówki.") == "Bez wskazówki.", "DE-3: bez zmian")

    # Plik agenta: frontmatter parsowalny, treść = prompt, komentarz źródła w frontmatterze.
    out = tm.agent_doc({"name": "x", "description": "Opis: z dwukropkiem", "model": {"id": "claude-haiku-5-5"}},
                       "# P\n", src="factory/x.yaml")
    fm, body = split(out, yaml)
    check(fm == {"name": "x", "description": "Opis: z dwukropkiem", "model": {"id": "claude-haiku-5-5"}}
          and body == "# P\n", f"AD-1: {fm} {body!r}")
    check("# WYGENEROWANO przez factory/build.py" in out.split("\n---\n", 1)[0], "AD-2: znacznik w frontmatterze")

    # Zapis: usuwa tylko własne wygenerowane pliki, nie rusza claude-lock.json ani plików użytkownika.
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        (d / "agents").mkdir()
        (d / "claude-lock.json").write_text("{}", encoding="utf-8")
        (d / "agents" / "moj.md").write_text("---\nname: moj\n---\nwłasny\n", encoding="utf-8")
        (d / "agents" / "stary.md").write_text(f"---\n# {tm.MARK} Źródło: x\nname: stary\n---\n", encoding="utf-8")
        new = {"agents/a.md": f"---\n# {tm.MARK} Źródło: x\nname: a\n---\nA\n", "README.md": "# R\n"}
        check(sorted(tm.stale(d, new)) == ["README.md", "agents/a.md", "agents/stary.md"],
              f"WR-1 nieaktualne przed zapisem: {sorted(tm.stale(d, new))}")
        tm.write(d, new)
        left = sorted(p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file())
        check(left == ["README.md", "agents/a.md", "agents/moj.md", "claude-lock.json"], f"WR-2 po zapisie: {left}")
        check(tm.stale(d, new) == [], f"WR-3 aktualne po zapisie: {tm.stale(d, new)}")

    # Wgranie tylko poleceniem: domyślnie sam plan (--dry-run), wgranie wyłącznie z --yes.
    calls = []
    def fake_run(argv, cwd=None, **kw):
        calls.append((argv, cwd))
        class R: returncode = 0
        return R()
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        check(tm.apply(d, yes=False, run=fake_run, which=lambda _: "/bin/ant") == 2 and calls == [],
              f"AP-1: brak plików targetu → kod 2 bez wywołania ant: {calls}")
        (d / "agents").mkdir()
        (d / "environments").mkdir()
        check(tm.apply(d, yes=False, run=fake_run, which=lambda _: "/bin/ant") == 0
              and calls == [(["/bin/ant", "apply", "--dry-run", "agents", "environments"], d)],
              f"AP-2: domyślnie tylko plan: {calls}")
        calls.clear()
        check(tm.apply(d, yes=True, run=fake_run, which=lambda _: "/bin/ant") == 0
              and calls == [(["/bin/ant", "apply", "--yes", "agents", "environments"], d)], f"AP-3: --yes wgrywa: {calls}")
        calls.clear()
        check(tm.apply(d, yes=True, run=fake_run, which=lambda _: None) == 2 and calls == [],
              f"AP-4: brak ant → kod 2: {calls}")
    def boom(*a, **k):
        raise AssertionError("render/write nie mogą uruchamiać procesów")
    old = tm.subprocess.run
    tm.subprocess.run = boom
    try:
        with tempfile.TemporaryDirectory() as t:
            tm.write(Path(t), tm.render(b)[0])
        check(True, "")
    except AssertionError as e:
        check(False, f"AP-5: {e}")
    finally:
        tm.subprocess.run = old

    # Integracja: cała fabryka tego workspace.
    files, warnings, errors = tm.render(b)
    agents = {k: v for k, v in files.items() if k.startswith("agents/")}
    personas = b.load_team(b.load_config())[1]
    check(errors == [], f"IN-0 bez błędów: {errors}")
    check({"environments/default.yaml", "README.md"} <= set(files), f"IN-1 środowisko i README: {sorted(files)[:5]}")
    env = yaml.safe_load(files["environments/default.yaml"])
    check(env["config"]["type"] == "cloud" and env["config"]["networking"]["type"] == "limited", f"IN-2: {env}")
    check(not files["README.md"].startswith("---"), "IN-3 README bez frontmattera (ant apply go pomija)")
    bad, members_with_ma, skills_missing = [], [], []
    for path, text in agents.items():
        fm, body = split(text, yaml)
        if not (fm.get("name") and fm.get("model", {}).get("id", "").startswith("claude-") and body.strip()
                and "claude --agent" not in fm.get("description", "")):
            bad.append(path)
        for s in fm.get("skills") or []:
            if not (ROOT / "managed-agents" / "agents" / s / "SKILL.md").resolve().is_file():
                skills_missing.append(f"{path}: {s}")
        ma = fm.get("multiagent")
        if ma:
            entries = ma["subagents"]["predefined_agents"]
            if len(entries) > 20:
                bad.append(f"{path}: roster {len(entries)}")
            for e in entries:
                target = f"agents/{Path(e).name}"
                if target not in agents:
                    bad.append(f"{path}: brak {e}")
                elif split(agents[target], yaml)[0].get("multiagent"):
                    members_with_ma.append(f"{path} → {e}")
    check(not bad, f"IN-4 pliki agentów poprawne: {bad[:5]}")
    check(not skills_missing, f"IN-5 skille istnieją: {skills_missing[:5]}")
    check(not members_with_ma, f"IN-6 jeden poziom delegowania: {members_with_ma[:5]}")
    for pname in personas:
        fm, body = split(agents.get(f"agents/{pname}.md", "---\n{}\n---\n"), yaml)
        if not (fm.get("multiagent") and "## Środowisko Managed Agents" in body):
            check(False, f"IN-7 persona {pname}: koordynator z rosterem i sekcją środowiska")
            break
    else:
        check(True, "")
    check(all(f"{p}-" in " ".join(agents) for p in personas), "IN-8 pliki wykonawców")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów target_managed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
