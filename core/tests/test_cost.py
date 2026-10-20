#!/usr/bin/env python3
"""Testy mechanizmów kosztowych: profile (tiery i ustawienia sesji), pasek stanu, samoocena wykonawców w logu,
rekomendacje tierów w raporcie kosztów, scalanie ustawień w instalatorze."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
HOOKS = ROOT / ".claude" / "hooks"


def run(cmd, env=None, stdin="", cwd=None):
    return subprocess.run([sys.executable, *cmd], input=stdin, capture_output=True, text=True,
                          env=env or os.environ, cwd=cwd, timeout=120)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def agent_model(root: Path, rel: str) -> str:
    text = (root / ".claude" / "agents" / "_generated" / rel).read_text(encoding="utf-8")
    return next(ln.split(":", 1)[1].strip() for ln in text.splitlines() if ln.startswith("model:"))


def main() -> int:
    fails, total = [], 0

    # ── profile: kopia fabryki w katalogu tymczasowym, żeby nie ruszać repozytorium ──
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "f"
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns("__pycache__", "logs", ".git", "*.zip"))
        (root / ".claude" / "factory-profile.json").unlink(missing_ok=True)
        (root / ".claude" / "settings.local.json").write_text(json.dumps({"model": "opus"}))   # własne ustawienie
        prof = str(root / "factory" / "profile.py")

        total += 1
        r = run([prof, "oszczedny"], cwd=root)
        local = json.loads((root / ".claude" / "settings.local.json").read_text())
        if r.returncode != 0 or agent_model(root, "shared/architect.md") != "sonnet" \
                or local.get("effortLevel") != "low" or local.get("autoCompactWindow") != 150000:
            fails.append(f"profile oszczedny: architect na sonnet, effort low, kompaktowanie 150k — {r.stdout[-400:]} {local}")

        total += 1
        r = run([prof, "jakosc"], cwd=root)
        local = json.loads((root / ".claude" / "settings.local.json").read_text())
        if agent_model(root, "shared/architect.md") != "opus" or local.get("advisorModel") != "opus":
            fails.append(f"profile jakosc: architect na opus i doradca opus — {local}")

        total += 1
        run([prof, "zrownowazony"], cwd=root)
        local = json.loads((root / ".claude" / "settings.local.json").read_text())
        if "advisorModel" in local or local.get("model") != "opus" or local.get("effortLevel") != "medium":
            fails.append(f"profile: powrót do zrownowazony powinien zdjąć doradcę i zostawić własne `model` — {local}")

        total += 1
        before = (root / ".claude" / "settings.local.json").read_text()
        r = run([prof, "oszczedny", "--dry-run"], cwd=root)
        if (root / ".claude" / "settings.local.json").read_text() != before or "dry-run" not in r.stdout:
            fails.append("profile --dry-run zmienił ustawienia")

        total += 1
        if run([prof, "nieznany"], cwd=root).returncode != 2:
            fails.append("profile: nieznany profil powinien zwrócić kod 2")

    # ── pasek stanu ──
    total += 1
    sample = {"model": {"display_name": "Opus"}, "effort": {"level": "high"},
              "context_window": {"used_percentage": 60, "current_usage": {"input_tokens": 2000,
                                 "cache_read_input_tokens": 110000, "cache_creation_input_tokens": 8000}},
              "prompt_cache": {"hit_ratio": 0.91, "warm": False, "requests": 5},
              "cost": {"total_cost_usd": 0.4234}, "rate_limits": {"five_hour": {"used_percentage": 85}}}
    out = run([str(HOOKS / "statusline.py")], stdin=json.dumps(sample)).stdout
    if not all(x in out for x in ("Opus · high", "⚠ kontekst 60% 120k", "cache 91% zimny", "$0.42", "⚠ 5h 85%")):
        fails.append(f"statusline: {out!r}")
    total += 1
    r = run([str(HOOKS / "statusline.py")], stdin="nie json")
    if r.returncode != 0:
        fails.append("statusline: błędne wejście nie może przerywać")

    # ── log_usage: samoocena wykonawcy ──
    total += 1
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        tr = root / "agent.jsonl"
        tr.write_text(json.dumps({"type": "assistant", "message": {"id": "m1", "model": "claude-haiku-4-5",
                      "usage": {"input_tokens": 10, "output_tokens": 50},
                      "content": [{"type": "text", "text": "**Zrobione:** …\n**Tier:** `Tier: za niski — wymaga decyzji`"}]}}) + "\n")
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
        run([str(HOOKS / "log_usage.py")], env, json.dumps({"hook_event_name": "SubagentStop", "agent_type": "scout",
                                                             "agent_transcript_path": str(tr), "session_id": "s"}))
        rec = json.loads((root / ".claude" / "logs" / "usage.jsonl").read_text().splitlines()[-1])
        if rec.get("tier_feedback") != "niski":
            fails.append(f"log_usage: brak tier_feedback — {rec}")
        total += 1
        run([str(HOOKS / "log_usage.py")], env, json.dumps({"hook_event_name": "SubagentStop", "agent_type": "scout",
                                                             "agent_id": "a1", "agent_transcript_path": str(tr)}))
        rec = json.loads((root / ".claude" / "logs" / "usage.jsonl").read_text().splitlines()[-1])
        if rec.get("agent_id") != "a1":
            fails.append(f"log_usage: SubagentStop bez agent_id (łączenie z delegation.jsonl) — {rec}")

    # ── log_usage: dziennik delegowań (PostToolUse narzędzia Agent) ──
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}

        def delegate(prompt, tool="Agent", **extra):
            inp = {"subagent_type": "scout", "model": "haiku", "prompt": prompt, "run_in_background": False, **extra}
            run([str(HOOKS / "log_usage.py")], env, json.dumps({
                "hook_event_name": "PostToolUse", "tool_name": tool, "session_id": "s", "tool_input": inp,
                "tool_response": {"agentId": "a1", "content": [{"type": "text", "text": "raport"}]}}))
            p = root / ".claude" / "logs" / "delegation.jsonl"
            return json.loads(p.read_text(encoding="utf-8").splitlines()[-1]) if p.exists() else {}

        total += 1
        brief = "Klasa: Czytanie\nZnajdź miejsca użycia."
        rec = delegate(brief)
        want = {"agent": "scout", "model": "haiku", "klass": "czytanie", "brief_chars": len(brief),
                "result_chars": len("raport"), "agent_id": "a1", "background": False, "session": "s"}
        if any(rec.get(k) != v for k, v in want.items()):
            fails.append(f"log_usage: wpis delegowania — {rec}")
        total += 1
        if delegate("Znajdź miejsca użycia.").get("klass", "?") is not None:
            fails.append("log_usage: brief bez linii Klasa → klass None")
        total += 1
        if delegate("**Klasa:** Przegląd — świeże spojrzenie\n…").get("klass") != "przeglad":
            fails.append("log_usage: klasa z diakrytykami i formatowaniem → przeglad")
        total += 1
        if delegate("Klasa: coś innego\n…").get("klass") != "inne":
            fails.append("log_usage: nieznana klasa → inne")
        total += 1
        if delegate("Klasa: mechaniczna", tool="Task").get("klass") != "mechaniczna":
            fails.append("log_usage: narzędzie Task (stara nazwa) też trafia do dziennika")
        total += 1     # tło: dokumentacja hooków (2026-10-18) — status async_launched, bez usage; resolvedModel
        run([str(HOOKS / "log_usage.py")], env, json.dumps({
            "hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_input": {"subagent_type": "scout", "prompt": "x"},
            "tool_response": {"status": "async_launched", "agentId": "a9", "resolvedModel": "claude-haiku-5-5",
                              "prompt": "x", "description": "d"}}))
        rec = json.loads((root / ".claude" / "logs" / "delegation.jsonl").read_text().splitlines()[-1])
        if rec.get("background") is not True or rec.get("resolved_model") != "claude-haiku-5-5" \
                or rec.get("result_chars") != 0:
            fails.append(f"log_usage: delegowanie w tle (async_launched) — {rec}")
        total += 1
        dl = root / ".claude" / "logs" / "delegation.jsonl"
        n = len(dl.read_text().splitlines()) if dl.exists() else 0
        run([str(HOOKS / "log_usage.py")], env, json.dumps({"hook_event_name": "PostToolUse", "tool_name": "Bash",
                                                             "tool_input": {"command": "ls"}}))
        if (len(dl.read_text().splitlines()) if dl.exists() else 0) != n \
                or (root / ".claude" / "logs" / "usage.jsonl").exists():
            fails.append("log_usage: PostToolUse innego narzędzia nie może nic zapisać")

    # ── cost_report: rekomendacje tierów ──
    total += 1
    cr = load(ROOT / "factory" / "cost_report.py", "cost_report")
    cfg = {"shared_agents": {"quick-fixer": {}}}

    def rec(ts, session, agent, model, fb=None):
        return {"ts": ts, "session": session, "event": "SubagentStop", "agent": agent,
                "models": {model: 100}, "tier_feedback": fb}
    records = [rec("1", "a", "quick-fixer", "claude-haiku-4-5"), rec("2", "a", "quick-fixer", "claude-sonnet-5-5"),
               rec("3", "b", "quick-fixer", "claude-haiku-4-5", "niski"), rec("4", "c", "quick-fixer", "claude-haiku-4-5"),
               rec("5", "d", "architect", "claude-opus-5-5", "wysoki"), rec("6", "e", "architect", "claude-opus-5-5", "wysoki"),
               rec("7", "f", "architect", "claude-opus-5-5")]
    adv = "\n".join(cr.tier_advice(records, cfg))
    if "quick-fixer" not in adv or "podnieś" not in adv or "architect" not in adv or "obniż" not in adv:
        fails.append(f"cost_report: rekomendacje tierów — {adv!r}")

    # ── cost_report --delegation: koszt delegowania wg klasy zadania ──
    total += 1
    deleg = [{"klass": "czytanie", "agent_id": "a1", "brief_chars": 100, "result_chars": 50},
             {"klass": "czytanie", "agent_id": "a2", "brief_chars": 300, "result_chars": 150},
             {"klass": "czytanie", "agent_id": "a3", "brief_chars": 200, "result_chars": 100},
             {"klass": None, "agent_id": "a4", "brief_chars": 10, "result_chars": 10},
             {"klass": "mechaniczna", "agent_id": None, "brief_chars": 40, "result_chars": 20}]
    usage = [{"event": "SubagentStop", "agent_id": "a1", "input": 1000, "output": 0, "cache_read": 0, "cache_write": 0,
              "models": {"claude-haiku-4-5": 1}},
             {"event": "SubagentStop", "agent_id": "a2", "input": 3000, "output": 0, "cache_read": 0, "cache_write": 0,
              "models": {"claude-haiku-4-5": 1}},
             {"event": "SubagentStop", "agent_id": "a3", "input": 2000, "output": 1000, "cache_read": 0,
              "cache_write": 0, "models": {"claude-haiku-4-5": 1}},
             {"event": "SessionEnd", "agent": "main", "input": 9, "output": 9, "models": {}}]
    prices = {"haiku": {"input": 1, "output": 5, "cache_read": 0.1, "cache_write": 1.25}}
    rows = {r["klass"]: r for r in cr.delegation_summary(deleg, usage, prices)}
    c = rows.get("czytanie", {})
    if c.get("n") != 3 or c.get("joined") != 3 or c.get("median_tokens") != 3000 or c.get("median_brief") != 200 \
            or c.get("median_result") != 100 or abs((c.get("median_usd") or 0) - 0.003) > 1e-9 \
            or rows.get(None, {}).get("n") != 1 or rows.get("mechaniczna", {}).get("joined") != 0 \
            or rows.get("mechaniczna", {}).get("median_tokens") is not None:
        fails.append(f"cost_report.delegation_summary — {rows}")
    total += 1
    with tempfile.TemporaryDirectory() as d:
        dl, ul = Path(d) / "delegation.jsonl", Path(d) / "usage.jsonl"
        dl.write_text("\n".join(json.dumps({"ts": "2026-10-18T12:00:00+00:00", **x}) for x in deleg), encoding="utf-8")
        ul.write_text("\n".join(json.dumps({"ts": "2026-10-18T12:00:00+00:00", **x}) for x in usage), encoding="utf-8")
        r = run([str(ROOT / "factory" / "cost_report.py"), "--delegation", "--log", str(ul), "--delegation-log", str(dl)])
        if r.returncode != 0 or "czytanie" not in r.stdout or "bez klasy" not in r.stdout:
            fails.append(f"cost_report --delegation: {r.returncode} {r.stdout[-400:]} {r.stderr[-400:]}")

    # ── instalator: scalanie kluczy najwyższego poziomu i polecenie Pythona w pasku stanu ──
    total += 1
    inst = load(ROOT / "factory" / "install.py", "install")
    sp = ROOT / ".claude" / "settings.json"
    sp = sp if sp.exists() else ROOT / ".claude" / "settings.local.json"     # w projekcie (instalacja prywatna)
    src = json.loads(sp.read_text(encoding="utf-8"))
    if not str(src.get("statusLine", {}).get("command", "")).startswith("python3 "):
        src["statusLine"] = {"type": "command", "command": "python3 .claude/hooks/statusline.py"}
    merged = inst.merge_settings(src, {"autoCompactWindow": 500000})
    py = inst.apply_python(json.loads(json.dumps(merged)), "py")
    if merged.get("autoCompactWindow") != 500000 or "statusLine" not in merged \
            or not py["statusLine"]["command"].startswith("py .claude/hooks/statusline.py"):
        fails.append(f"install: scalanie ustawień — {merged.get('autoCompactWindow')} {py.get('statusLine')}")

    # ── instalator: wycofane reguły Read(...) ekonomii kontekstu (piaskownica robi z nich denyRead dla programów, więc
    # npm test nie przeczytałby node_modules) — pilnuje tego guard_paths. Piaskownica Bash jest opt-in: szablon jej nie
    # włącza (psuje `git add -A`, usługi na localhost) ani nie nadpisuje ustawienia użytkownika ──
    total += 1
    old = {"permissions": {"deny": ["Read(./node_modules/**)", "Read(**/yarn.lock)", "Read(./vendor/**)"]}}
    merged = inst.merge_settings(src, old)
    deny = merged["permissions"]["deny"]
    mine = inst.merge_settings(src, {"sandbox": {"enabled": True}})
    if any(r in deny for r in ("Read(./node_modules/**)", "Read(**/yarn.lock)")) or "Read(./vendor/**)" not in deny \
            or "sandbox" in merged or mine.get("sandbox") != {"enabled": True}:
        fails.append(f"install: piaskownica i wycofane reguły — deny={deny} sandbox={merged.get('sandbox')} "
                     f"własna={mine.get('sandbox')}")

    # ── hooki ochronne blokują akcję, gdy same zawiodą (onFailure: block, Claude Code ≥ 2.1.295); aktualizacja dopisuje
    # brakujące pole do hooka, który już jest w projekcie, ale nie nadpisuje wyboru użytkownika ──
    total += 1
    guards = ("guard_bash.py", "guard_paths.py", "cleanroom_guard.py")
    def guard_hooks(settings):
        return {a.rsplit("/", 1)[-1]: h for e in settings["hooks"]["PreToolUse"] for h in e["hooks"]
                for a in h.get("args") or [] if a.rsplit("/", 1)[-1] in guards}
    in_src = guard_hooks(src)
    old_proj = json.loads(json.dumps(src))
    for h in guard_hooks(old_proj).values():
        h.pop("onFailure", None)
    guard_hooks(old_proj)["guard_paths.py"]["onFailure"] = "continue"     # świadomy wybór użytkownika
    upd = guard_hooks(inst.merge_settings(src, old_proj))
    if sorted(in_src) != sorted(guards) or any(h.get("onFailure") != "block" for h in in_src.values()) \
            or upd["guard_bash.py"].get("onFailure") != "block" or upd["cleanroom_guard.py"].get("onFailure") != "block" \
            or upd["guard_paths.py"].get("onFailure") != "continue":
        fails.append(f"hooki ochronne: onFailure — szablon {in_src}, po aktualizacji {upd}")

    # ── jednorazowe pliki objaśnień (HTML, diagramy) w .claude/scratch/ nie trafiają do gita (core-problem-routing) ──
    total += 1
    gi = ROOT / "factory" / "gitignore"
    if ".claude/scratch/" not in inst.ignored_paths() or (gi.exists() and ".claude/scratch/" not in gi.read_text(encoding="utf-8")):
        fails.append("install: .claude/scratch/ poza ignorowanymi ścieżkami")

    # ── gotowa konfiguracja piaskownicy opt-in: tylko klucz sandbox, bez furtek ──
    total += 1
    sb_file = ROOT / "factory" / "templates" / "sandbox.settings.json"
    try:
        sb_all = json.loads(sb_file.read_text(encoding="utf-8"))
        sb = sb_all["sandbox"]
        net = sb.get("network", {})
        problems = [k for k, bad in (
            ("klucze", set(sb_all) != {"sandbox"}),
            ("enabled", sb.get("enabled") is not True),
            ("allowUnsandboxedCommands", sb.get("allowUnsandboxedCommands") is not False),
            ("autoAllowBashIfSandboxed", sb.get("autoAllowBashIfSandboxed") is not False),
            ("excludedCommands", not set(sb.get("excludedCommands", [])) <= {"git push *", "git fetch *", "git pull *"}),
            ("denyRead", not {"~/.ssh", "~/.aws"} <= set(sb.get("filesystem", {}).get("denyRead", []))),
            ("allowedDomains", any("*" == d or d.startswith("*.") and d.count(".") < 2
                                   for d in net.get("allowedDomains", []))),
            ("unixSockets", bool(net.get("allowUnixSockets")) or net.get("allowAllUnixSockets") is True),
        ) if bad]
    except (OSError, ValueError, KeyError, TypeError) as e:
        problems = [repr(e)]
    if problems:
        fails.append(f"szablon piaskownicy {sb_file.name}: {problems}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów mechanizmów kosztowych")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
