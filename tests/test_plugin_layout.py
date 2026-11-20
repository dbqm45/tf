#!/usr/bin/env python3
"""Tryb fabryki, krok T1 (docs/plans/2026-11-20-tryb-fabryki-plan.md): `install.py --layout plugin` składa fabrykę
w lokalnej wtyczce `.tf/plugin/` — skille, agenci, rejestracja hooków, reguły i ustawienia sesji — tak, żeby zwykły
`claude` w projekcie nie ładował niczego z fabryki. Twoje skille, ustawienia i CLAUDE.md zostają nietknięte.
Domyślny układ (bez opcji) się nie zmienia.
python3 tests/test_plugin_layout.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
INSTALL = ROOT / "core" / "factory" / "install.py"
CORE_SKILLS = sorted(p.parent.name for p in (ROOT / "core" / "skills").glob("*/SKILL.md"))


def install(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(INSTALL), str(project), "--yes", "--packs", "none", *args],
                          capture_output=True, text=True, timeout=600, env={"PATH": "/usr/bin:/bin", "HOME": str(project.parent)})


def project(base: Path, name: str) -> Path:
    p = base / name
    (p / ".claude" / "skills" / "moj-skill").mkdir(parents=True)
    (p / ".claude" / "skills" / "moj-skill" / "SKILL.md").write_text(
        "---\nname: moj-skill\ndescription: Mój skill.\n---\nTreść.\n", encoding="utf-8")
    (p / ".claude" / "settings.local.json").write_text(json.dumps({"model": "opus", "permissions": {"allow": ["Bash(make *)"]}}),
                                                       encoding="utf-8")
    (p / "CLAUDE.md").write_text("# Moje zasady\n\n- Piszę po swojemu.\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(p)], check=True)
    return p


def hook_commands(settings: dict) -> list[str]:
    out = []
    for groups in (settings.get("hooks") or {}).values():
        for g in groups:
            for h in g.get("hooks") or []:
                out.append(" ".join([h.get("command", ""), *h.get("args", [])]))
    return out


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = project(base, "plugin")
        r = install(p, "--layout", "plugin")
        check(r.returncode == 0, f"PL-1: instalacja w układzie wtyczki: {r.returncode} {r.stdout[-800:]} {r.stderr[-800:]}")
        plug = p / ".tf" / "plugin"
        try:
            meta = json.loads((plug / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            meta = {}
        check(meta.get("name") == "tf" and meta.get("version"), f"PL-2: plugin.json wtyczki tf z wersją: {meta}")
        in_plugin = [s for s in CORE_SKILLS if (plug / "skills" / s / "SKILL.md").is_file()]
        in_claude = [s for s in CORE_SKILLS if (p / ".claude" / "skills" / s / "SKILL.md").is_file()]
        check(in_plugin == CORE_SKILLS and not in_claude,
              f"PL-3: SKILL.md skilli fabryki tylko we wtyczce (zwykły claude ich nie widzi): we wtyczce {len(in_plugin)}/"
              f"{len(CORE_SKILLS)}, w .claude/skills {in_claude}")
        check((p / ".claude" / "skills" / "tf" / "scripts" / "run_state.py").is_file()
              and (plug / "skills" / "tf" / "scripts" / "run_state.py").is_file()
              and (plug / "skills" / "tf" / "references").is_dir(),
              "PL-4: skrypty skilli zostają pod dotychczasową ścieżką (polecenia w treści działają), a wtyczka ma pełny skill")
        check((p / ".claude" / "skills" / "moj-skill" / "SKILL.md").read_text(encoding="utf-8").startswith("---\nname: moj-skill"),
              "PL-5: Twój skill w .claude/skills nietknięty")
        try:
            local = json.loads((p / ".claude" / "settings.local.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            local = {}
        check(local.get("model") == "opus" and "Bash(make *)" in (local.get("permissions") or {}).get("allow", [])
              and not hook_commands(local) and "statusLine" not in local and "env" not in local,
              f"PL-6: .claude/settings.local.json bez hooków, env i paska fabryki, Twoje wpisy zostają: {json.dumps(local)[:400]}")
        try:
            hooks = json.loads((plug / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            hooks = {}
        cmds = hook_commands(hooks)
        check(any("tdd_guard.py" in c for c in cmds) and any("guard_paths.py" in c for c in cmds)
              and any("factory_rules.py" in c for c in (" ".join(hook_commands({"hooks": {"SessionStart": (hooks.get("hooks") or {}).get("SessionStart") or []}})),)),
              f"PL-7: rejestracja hooków fabryki we wtyczce, z hookiem reguł przy starcie sesji: {cmds[:6]}")
        try:
            sess = json.loads((plug / "session-settings.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            sess = {}
        check(sess.get("env") and sess.get("statusLine") and (sess.get("permissions") or {}).get("deny")
              and not sess.get("hooks"),
              f"PL-8: ustawienia sesji fabryki (env, pasek, uprawnienia) w session-settings.json, bez hooków: {list(sess)}")
        md = (p / "CLAUDE.md").read_text(encoding="utf-8")
        local_md = (p / "CLAUDE.local.md").read_text(encoding="utf-8") if (p / "CLAUDE.local.md").exists() else ""
        rules = (plug / "RULES.md").read_text(encoding="utf-8") if (plug / "RULES.md").exists() else ""
        check(md == "# Moje zasady\n\n- Piszę po swojemu.\n" and "team-factory" not in local_md and "TDD" in rules,
              f"PL-9: reguły fabryki w RULES.md wtyczki, CLAUDE.md i CLAUDE.local.md bez bloku fabryki: {local_md[:200]!r}")
        r = subprocess.run([sys.executable, str(p / ".claude" / "hooks" / "factory_rules.py")], input="{}", cwd=p,
                           capture_output=True, text=True, timeout=30, env={"PATH": "/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(p)})
        try:
            ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        except (ValueError, KeyError, TypeError):
            ctx = ""
        check("TDD" in ctx, f"PL-10: hook reguł podaje treść RULES.md jako kontekst sesji: {r.stdout[:200]} {r.stderr[-200:]}")
        agents = sorted(x.name for x in (plug / "agents").rglob("*.md")) if (plug / "agents").is_dir() else []
        old_agents = list((p / ".claude" / "agents" / "_generated").rglob("*.md")) if (p / ".claude" / "agents" / "_generated").is_dir() else []
        check("scope-reviewer.md" in agents and not old_agents,
              f"PL-11: agenci fabryki we wtyczce, nie w .claude/agents: {agents[:5]} {old_agents[:3]}")
        man = json.loads((p / ".claude" / "factory-manifest.json").read_text(encoding="utf-8"))
        check(man.get("layout") == "plugin", f"PL-12: manifest zapisuje układ: {man.get('layout')}")
        cat = (p / ".claude" / "catalog.md").read_text(encoding="utf-8") if (p / ".claude" / "catalog.md").is_file() else ""
        check("`moj-skill`" in cat and "`core-grounding`" in cat and "tf:" in cat,
              f"PL-15: katalog w układzie wtyczki pokazuje skille fabryki (z przedrostkiem tf: w sesji) i Twoje: {cat[:300]!r}")
        r = install(p)
        check(r.returncode == 0 and not (p / ".claude" / "skills" / "tf" / "SKILL.md").exists()
              and (plug / "skills" / "tf" / "SKILL.md").is_file()
              and json.loads((p / ".claude" / "factory-manifest.json").read_text(encoding="utf-8")).get("layout") == "plugin",
              f"PL-13: aktualizacja bez opcji zostaje w układzie wtyczki: {r.returncode} {r.stdout[-400:]}")

        # stary układ na żądanie (od T5 domyślny jest układ wtyczki — tests/test_plugin_migration.py)
        q = project(base, "default")
        r = install(q, "--layout", "default")
        check(r.returncode == 0 and (q / ".claude" / "skills" / "tf" / "SKILL.md").is_file() and not (q / ".tf" / "plugin").exists(),
              f"PL-14: --layout default daje stary układ: {r.returncode} {r.stdout[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów układu wtyczki")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
