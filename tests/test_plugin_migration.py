#!/usr/bin/env python3
"""Tryb fabryki, krok T5 (docs/plans/2026-11-20-tryb-fabryki-plan.md): układ wtyczki na żądanie (od 2026-11-23 domyślny
jest znowu układ klasyczny — tests/test_layout_default.py). `update.py --layout plugin` przenosi instalację w starym
układzie do .tf/plugin/ i sprząta po niej: SKILL.md fabryki z .claude/skills,
jej hooki, env, pasek i uprawnienia z ustawień projektu, blok w CLAUDE.local.md i agentów z .claude/agents/_generated.
Twoje skille, ustawienia i treść CLAUDE.md zostają; `update.py --rollback` wraca do starego układu.
`--layout default` zostawia stary układ.
python3 tests/test_plugin_migration.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
INSTALL = ROOT / "core" / "factory" / "install.py"


def env(base: Path) -> dict:
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(base)}


def install(p: Path, base: Path, *opts: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(INSTALL), str(p), "--yes", "--packs", "none", *opts], capture_output=True,
                          text=True, timeout=600, env=env(base))


def old_install(base: Path, name: str) -> Path:
    """Instalacja w starym układzie (sprzed T5: manifest bez pola layout) z Twoimi plikami obok fabryki."""
    p = base / name
    (p / ".claude" / "skills" / "moj-skill").mkdir(parents=True)
    (p / ".claude" / "skills" / "moj-skill" / "SKILL.md").write_text("---\nname: moj-skill\ndescription: Mój.\n---\nX\n",
                                                                     encoding="utf-8")
    (p / "CLAUDE.local.md").write_text("# Moje notatki\n\n- moja reguła\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(p)], check=True)
    r = install(p, base, "--layout", "default")
    assert r.returncode == 0, r.stdout[-500:] + r.stderr[-500:]
    man_p = p / ".claude" / "factory-manifest.json"
    man = json.loads(man_p.read_text(encoding="utf-8"))
    man.pop("layout", None)
    man_p.write_text(json.dumps(man), encoding="utf-8")
    s_p = p / ".claude" / "settings.local.json"
    s = json.loads(s_p.read_text(encoding="utf-8"))
    s["model"] = "opus"
    s.setdefault("env", {})["MOJA_ZMIENNA"] = "1"
    s.setdefault("permissions", {}).setdefault("allow", []).append("Bash(make *)")
    s.setdefault("hooks", {}).setdefault("Stop", []).append({"hooks": [{"type": "command", "command": "echo moj-hook"}]})
    s_p.write_text(json.dumps(s), encoding="utf-8")
    return p


def hooks_text(settings: dict) -> str:
    return json.dumps(settings.get("hooks") or {})


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = old_install(base, "old")
        check((p / ".claude" / "skills" / "tf" / "SKILL.md").is_file() and "tdd_guard" in (p / ".claude" / "settings.local.json").read_text(encoding="utf-8"),
              "MG-0: przygotowanie — stara instalacja ma skille i hooki fabryki w .claude")
        r = subprocess.run([sys.executable, str(p / ".tf" / "factory" / "update.py"), "--layout", "plugin", "--yes"], cwd=p,
                           capture_output=True, text=True, timeout=900, env=env(base))   # the real update path (with backup)
        check(r.returncode == 0 and "tf code" in r.stdout, f"MG-1: aktualizacja przenosi do układu wtyczki i mówi o tf code: "
                                                          f"{r.returncode} {r.stdout[-600:]} {r.stderr[-300:]}")
        check(json.loads((p / ".claude" / "factory-manifest.json").read_text(encoding="utf-8")).get("layout") == "plugin",
              "MG-2: manifest w układzie wtyczki")
        check(not (p / ".claude" / "skills" / "tf" / "SKILL.md").exists() and (p / ".tf" / "plugin" / "skills" / "tf" / "SKILL.md").is_file()
              and (p / ".claude" / "skills" / "moj-skill" / "SKILL.md").is_file(),
              "MG-3: SKILL.md fabryki przeniesione do wtyczki, Twój skill został")
        s = json.loads((p / ".claude" / "settings.local.json").read_text(encoding="utf-8"))
        check("tdd_guard" not in hooks_text(s) and "moj-hook" in hooks_text(s) and s.get("model") == "opus"
              and (s.get("env") or {}).get("MOJA_ZMIENNA") == "1" and "CLAUDE_CODE_SUBAGENT_MODEL" not in (s.get("env") or {})
              and "statusLine" not in s and "Bash(make *)" in (s.get("permissions") or {}).get("allow", [])
              and "Bash(git status *)" not in (s.get("permissions") or {}).get("allow", []),
              f"MG-4: z ustawień projektu znikają wpisy fabryki, Twoje zostają: {json.dumps(s)[:600]}")
        md = (p / "CLAUDE.local.md").read_text(encoding="utf-8")
        check("team-factory:begin" not in md and "moja reguła" in md, f"MG-5: blok fabryki usunięty z CLAUDE.local.md, Twoja treść została: {md[:300]!r}")
        gen = p / ".claude" / "agents" / "_generated"
        check(not gen.exists() or not any(gen.rglob("*.md")), "MG-6: agenci fabryki zniknęli z .claude/agents/_generated")
        check(any((p / ".tf" / "plugin" / "agents").rglob("scope-reviewer.md")), "MG-7: agenci fabryki we wtyczce")

        r = subprocess.run([sys.executable, str(p / ".tf" / "factory" / "update.py"), "--rollback"], cwd=p, capture_output=True,
                           text=True, timeout=300, env=env(base))
        s = json.loads((p / ".claude" / "settings.local.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and (p / ".claude" / "skills" / "tf" / "SKILL.md").is_file() and "tdd_guard" in hooks_text(s)
              and "team-factory:begin" in (p / "CLAUDE.local.md").read_text(encoding="utf-8")
              and any((p / ".claude" / "agents" / "_generated").rglob("*.md"))
              and json.loads((p / ".claude" / "factory-manifest.json").read_text(encoding="utf-8")).get("layout") == "default",
              f"MG-8: --rollback wraca do starego układu (skille, hooki, blok reguł, agenci) i go zapamiętuje: {r.returncode} {r.stdout[-400:]} {r.stderr[-300:]}")

        q = old_install(base, "keep")
        r = install(q, base, "--layout", "default")
        check(r.returncode == 0 and (q / ".claude" / "skills" / "tf" / "SKILL.md").is_file() and not (q / ".tf" / "plugin").exists(),
              f"MG-9: --layout default zostawia stary układ: {r.returncode} {r.stdout[-300:]}")

        # tf onboard wpisuje polecenia projektu do reguł fabryki we wtyczce, a aktualizacja ich nie kasuje
        o = base / "onboard"
        o.mkdir()
        subprocess.run(["git", "init", "-q", str(o)], check=True)
        (o / "package.json").write_text(json.dumps({"name": "x", "scripts": {"test": "node -e 1"}}), encoding="utf-8")
        install(o, base, "--layout", "plugin")
        r = subprocess.run([sys.executable, ".tf/factory/tf.py", "onboard", "--yes"], cwd=o, capture_output=True, text=True,
                           timeout=600, env=env(base))
        rules = (o / ".tf" / "plugin" / "RULES.md").read_text(encoding="utf-8")
        check("npm test" in rules and not (o / "CLAUDE.local.md").exists(),
              f"MG-11: tf onboard wpisuje polecenia do .tf/plugin/RULES.md, nie tworzy CLAUDE.local.md: {r.stdout[-300:]} {rules[:300]!r}")
        install(o, base)
        check("npm test" in (o / ".tf" / "plugin" / "RULES.md").read_text(encoding="utf-8"),
              "MG-12: aktualizacja zachowuje polecenia projektu w RULES.md")

        # odinstalowanie w układzie wtyczki sprząta wtyczkę, Twój skill zostaje
        r = subprocess.run([sys.executable, ".tf/factory/uninstall.py", "--yes"], cwd=o, capture_output=True, text=True,
                           timeout=600, env=env(base))
        check(r.returncode == 0 and not (o / ".tf" / "plugin").exists() and not (o / ".tf" / ".claude-plugin").exists(),
              f"MG-13: uninstall usuwa wtyczkę i marketplace fabryki: {r.returncode} {r.stdout[-300:]}")

        n = base / "new"
        n.mkdir()
        subprocess.run(["git", "init", "-q", str(n)], check=True)
        r = install(n, base)
        check(r.returncode == 0 and (n / ".claude" / "skills" / "tf" / "SKILL.md").is_file()
              and not (n / ".tf" / "plugin").exists(),
              f"MG-10: a new install without options has the classic layout: {r.returncode} {r.stdout[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów przejścia na układ wtyczki")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
