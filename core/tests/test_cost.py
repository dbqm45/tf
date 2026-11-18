#!/usr/bin/env python3
"""Tests of the cost mechanisms: profiles (tiers and session settings), the status line, executors' self-assessment in the log,
tier recommendations in the cost report, merging settings in the installer."""
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

    # ── profiles: a copy of the factory in a temporary directory so the repository is not touched ──
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "f"
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns("__pycache__", "logs", ".git", "*.zip"))
        (root / ".claude" / "factory-profile.json").unlink(missing_ok=True)
        (root / ".claude" / "settings.local.json").write_text(json.dumps({"model": "opus"}))   # the user's own setting
        prof = str(root / ".tf" / "factory" / "profile.py")

        total += 1
        r = run([prof, "economy"], cwd=root)
        local = json.loads((root / ".claude" / "settings.local.json").read_text())
        if r.returncode != 0 or agent_model(root, "shared/architect.md") != "sonnet" \
                or local.get("effortLevel") != "low" or local.get("autoCompactWindow") != 150000:
            fails.append(f"profile economy: architect on sonnet, effort low, compaction 150k — {r.stdout[-400:]} {local}")

        total += 1
        r = run([prof, "quality"], cwd=root)
        local = json.loads((root / ".claude" / "settings.local.json").read_text())
        if agent_model(root, "shared/architect.md") != "opus" or local.get("advisorModel") != "opus":
            fails.append(f"profile quality: architect on opus and advisor opus — {local}")

        total += 1
        run([prof, "balanced"], cwd=root)
        local = json.loads((root / ".claude" / "settings.local.json").read_text())
        if "advisorModel" in local or local.get("model") != "opus" or local.get("effortLevel") != "medium":
            fails.append(f"profile: returning to balanced should remove the advisor and keep the user's own `model` — {local}")

        total += 1
        before = (root / ".claude" / "settings.local.json").read_text()
        r = run([prof, "economy", "--dry-run"], cwd=root)
        if (root / ".claude" / "settings.local.json").read_text() != before or "dry-run" not in r.stdout:
            fails.append("profile --dry-run changed the settings")

        total += 1
        if run([prof, "nieznany"], cwd=root).returncode != 2:
            fails.append("profile: an unknown profile should return code 2")

    # ── status line ──
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
    r = run([str(HOOKS / "statusline.py")], stdin="not json")
    if r.returncode != 0:
        fails.append("statusline: bad input must not crash it")

    # ── log_usage: executor self-assessment ──
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
        rec = json.loads((root / ".tf" / "logs" / "usage.jsonl").read_text().splitlines()[-1])
        if rec.get("tier_feedback") != "niski":
            fails.append(f"log_usage: no tier_feedback — {rec}")
        total += 1     # 14.x: the English signal recorded with the same value as the former Polish one
        tr.write_text(json.dumps({"type": "assistant", "message": {"id": "m2", "model": "claude-haiku-4-5",
                      "usage": {"input_tokens": 10, "output_tokens": 50},
                      "content": [{"type": "text", "text": "**Done:** …\n**Tier:** `Tier: too high — a rename only`"}]}}) + "\n")
        run([str(HOOKS / "log_usage.py")], env, json.dumps({"hook_event_name": "SubagentStop", "agent_type": "scout",
                                                             "agent_transcript_path": str(tr), "session_id": "s"}))
        rec = json.loads((root / ".tf" / "logs" / "usage.jsonl").read_text().splitlines()[-1])
        if rec.get("tier_feedback") != "wysoki":
            fails.append(f"log_usage: „Tier: too high” (14.x) → tier_feedback wysoki — {rec}")
        total += 1
        run([str(HOOKS / "log_usage.py")], env, json.dumps({"hook_event_name": "SubagentStop", "agent_type": "scout",
                                                             "agent_id": "a1", "agent_transcript_path": str(tr)}))
        rec = json.loads((root / ".tf" / "logs" / "usage.jsonl").read_text().splitlines()[-1])
        if rec.get("agent_id") != "a1":
            fails.append(f"log_usage: SubagentStop without agent_id (joining with delegation.jsonl) — {rec}")

    # ── log_usage: harness fingerprint (step H20) — the Claude Code, factory and pack versions and a hash of the installed files ──
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        tr = root / "main.jsonl"
        tr.write_text(json.dumps({"type": "user", "version": "2.1.325", "message": {"content": "x"}}) + "\n"
                      + json.dumps({"type": "assistant", "version": "2.1.325", "message": {
                          "id": "m1", "model": "claude-sonnet-5-5", "usage": {"input_tokens": 10, "output_tokens": 5},
                          "content": [{"type": "text", "text": "ok"}]}}) + "\n")
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
        man = root / ".claude" / "factory-manifest.json"
        man.parent.mkdir(parents=True)
        files = {".claude/skills/tf/SKILL.md": "aa11", ".tf/factory/tf.py": "bb22"}
        man.write_text(json.dumps({"version": "10.11.0", "packs": {"pack-it": "1.0.2"}, "files": files}))

        def harness():
            run([str(HOOKS / "log_usage.py")], env, json.dumps({"hook_event_name": "SessionEnd", "transcript_path": str(tr),
                                                                 "session_id": "s"}))
            return json.loads((root / ".tf" / "logs" / "usage.jsonl").read_text().splitlines()[-1]).get("harness") or {}

        h1 = harness()
        total += 1
        if not (h1.get("claude_code") == "2.1.325" and h1.get("factory") == "10.11.0"
                and h1.get("packs") == {"pack-it": "1.0.2"} and len(h1.get("files") or "") == 12):
            fails.append(f"log_usage: an entry without the harness fingerprint (Claude Code, factory, packs, file hash) — {h1}")
        man.write_text(json.dumps({"version": "10.11.0", "packs": {"pack-it": "1.0.2"},
                                   "files": {**files, ".tf/factory/tf.py": "cc33"}}))
        h2 = harness()
        total += 1
        if not h2.get("files") or h2.get("files") == h1.get("files"):
            fails.append(f"log_usage: changing an installed file does not change the hash in the fingerprint — {h1} {h2}")
        man.unlink()
        h3 = harness()
        total += 1
        if h3 != {"claude_code": "2.1.325"}:
            fails.append(f"log_usage: without a manifest the fingerprint has only what can be determined — {h3}")

    # ── log_usage: the delegation log (PostToolUse of the Agent tool) ──
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}

        def delegate(prompt, tool="Agent", **extra):
            inp = {"subagent_type": "scout", "model": "haiku", "prompt": prompt, "run_in_background": False, **extra}
            run([str(HOOKS / "log_usage.py")], env, json.dumps({
                "hook_event_name": "PostToolUse", "tool_name": tool, "session_id": "s", "tool_input": inp,
                "tool_response": {"agentId": "a1", "content": [{"type": "text", "text": "raport"}]}}))
            p = root / ".tf" / "logs" / "delegation.jsonl"
            return json.loads(p.read_text(encoding="utf-8").splitlines()[-1]) if p.exists() else {}

        total += 1
        brief = "Klasa: Czytanie\nZnajdź miejsca użycia."
        rec = delegate(brief)
        want = {"agent": "scout", "model": "haiku", "klass": "reading", "brief_chars": len(brief),
                "result_chars": len("raport"), "agent_id": "a1", "background": False, "session": "s"}
        if any(rec.get(k) != v for k, v in want.items()):
            fails.append(f"log_usage: wpis delegowania — {rec}")
        total += 1
        if delegate("Znajdź miejsca użycia.").get("klass", "?") is not None:
            fails.append("log_usage: brief bez linii Klasa → klass None")
        total += 1
        if delegate("**Klasa:** Przegląd — świeże spojrzenie\n…").get("klass") != "review":
            fails.append("log_usage: klasa z diakrytykami i formatowaniem → review")
        total += 1
        if delegate("**Class:** review — a fresh look\n…").get("klass") != "review":
            fails.append("log_usage: linia „Class:” (14.x) → review")
        total += 1
        if delegate("Klasa: coś innego\n…").get("klass") != "other":
            fails.append("log_usage: nieznana klasa → inne")
        total += 1
        if delegate("Klasa: mechaniczna", tool="Task").get("klass") != "mechanical":
            fails.append("log_usage: the Task tool (the old name) also goes to the log")
        total += 1     # background: the hooks documentation (2026-10-18) — status async_launched, without usage; resolvedModel
        run([str(HOOKS / "log_usage.py")], env, json.dumps({
            "hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_input": {"subagent_type": "scout", "prompt": "x"},
            "tool_response": {"status": "async_launched", "agentId": "a9", "resolvedModel": "claude-haiku-5-5",
                              "prompt": "x", "description": "d"}}))
        rec = json.loads((root / ".tf" / "logs" / "delegation.jsonl").read_text().splitlines()[-1])
        if rec.get("background") is not True or rec.get("resolved_model") != "claude-haiku-5-5" \
                or rec.get("result_chars") != 0:
            fails.append(f"log_usage: delegowanie w tle (async_launched) — {rec}")
        total += 1
        dl = root / ".tf" / "logs" / "delegation.jsonl"
        n = len(dl.read_text().splitlines()) if dl.exists() else 0
        run([str(HOOKS / "log_usage.py")], env, json.dumps({"hook_event_name": "PostToolUse", "tool_name": "Bash",
                                                             "tool_input": {"command": "ls"}}))
        if (len(dl.read_text().splitlines()) if dl.exists() else 0) != n \
                or (root / ".tf" / "logs" / "usage.jsonl").exists():
            fails.append("log_usage: PostToolUse of another tool must not write anything")

    # ── cost_report: tier recommendations ──
    total += 1
    cr = load(ROOT / ".tf" / "factory" / "cost_report.py", "cost_report")
    cfg = {"shared_agents": {"quick-fixer": {}}}

    def rec(ts, session, agent, model, fb=None):
        return {"ts": ts, "session": session, "event": "SubagentStop", "agent": agent,
                "models": {model: 100}, "tier_feedback": fb}
    records = [rec("1", "a", "quick-fixer", "claude-haiku-4-5"), rec("2", "a", "quick-fixer", "claude-sonnet-5-5"),
               rec("3", "b", "quick-fixer", "claude-haiku-4-5", "niski"), rec("4", "c", "quick-fixer", "claude-haiku-4-5"),
               rec("5", "d", "architect", "claude-opus-5-5", "wysoki"), rec("6", "e", "architect", "claude-opus-5-5", "wysoki"),
               rec("7", "f", "architect", "claude-opus-5-5")]
    adv = "\n".join(cr.tier_advice(records, cfg))
    if "quick-fixer" not in adv or "raise" not in adv or "architect" not in adv or "lower" not in adv:
        fails.append(f"cost_report: tier recommendations — {adv!r}")

    # ── cost_report --delegation: delegation cost by task class ──
    total += 1
    deleg = [{"klass": "reading", "agent_id": "a1", "brief_chars": 100, "result_chars": 50},
             {"klass": "reading", "agent_id": "a2", "brief_chars": 300, "result_chars": 150},
             {"klass": "reading", "agent_id": "a3", "brief_chars": 200, "result_chars": 100},
             {"klass": None, "agent_id": "a4", "brief_chars": 10, "result_chars": 10},
             {"klass": "mechanical", "agent_id": None, "brief_chars": 40, "result_chars": 20}]
    usage = [{"event": "SubagentStop", "agent_id": "a1", "input": 1000, "output": 0, "cache_read": 0, "cache_write": 0,
              "models": {"claude-haiku-4-5": 1}},
             {"event": "SubagentStop", "agent_id": "a2", "input": 3000, "output": 0, "cache_read": 0, "cache_write": 0,
              "models": {"claude-haiku-4-5": 1}},
             {"event": "SubagentStop", "agent_id": "a3", "input": 2000, "output": 1000, "cache_read": 0,
              "cache_write": 0, "models": {"claude-haiku-4-5": 1}},
             {"event": "SessionEnd", "agent": "main", "input": 9, "output": 9, "models": {}}]
    prices = {"haiku": {"input": 1, "output": 5, "cache_read": 0.1, "cache_write": 1.25}}
    rows = {r["klass"]: r for r in cr.delegation_summary(deleg, usage, prices)}
    c = rows.get("reading", {})
    if c.get("n") != 3 or c.get("joined") != 3 or c.get("median_tokens") != 3000 or c.get("median_brief") != 200 \
            or c.get("median_result") != 100 or abs((c.get("median_usd") or 0) - 0.003) > 1e-9 \
            or rows.get(None, {}).get("n") != 1 or rows.get("mechanical", {}).get("joined") != 0 \
            or rows.get("mechanical", {}).get("median_tokens") is not None:
        fails.append(f"cost_report.delegation_summary — {rows}")
    total += 1
    with tempfile.TemporaryDirectory() as d:
        dl, ul = Path(d) / "delegation.jsonl", Path(d) / "usage.jsonl"
        dl.write_text("\n".join(json.dumps({"ts": "2026-10-18T12:00:00+00:00", **x}) for x in deleg), encoding="utf-8")
        ul.write_text("\n".join(json.dumps({"ts": "2026-10-18T12:00:00+00:00", **x}) for x in usage), encoding="utf-8")
        r = run([str(ROOT / ".tf" / "factory" / "cost_report.py"), "--delegation", "--log", str(ul), "--delegation-log", str(dl)])
        if r.returncode != 0 or "reading" not in r.stdout or "no class" not in r.stdout:
            fails.append(f"cost_report --delegation: {r.returncode} {r.stdout[-400:]} {r.stderr[-400:]}")

    # ── installer: merging top-level keys and the Python command in the status line ──
    total += 1
    inst = load(ROOT / ".tf" / "factory" / "install.py", "install")
    sp = ROOT / ".claude" / "settings.json"
    sp = sp if sp.exists() else ROOT / ".claude" / "settings.local.json"     # w projekcie (instalacja prywatna)
    src = json.loads(sp.read_text(encoding="utf-8"))
    if not str(src.get("statusLine", {}).get("command", "")).startswith("python3 "):
        src["statusLine"] = {"type": "command", "command": "python3 .claude/hooks/statusline.py"}
    merged = inst.merge_settings(src, {"autoCompactWindow": 500000})
    py = inst.apply_python(json.loads(json.dumps(merged)), "py")
    if merged.get("autoCompactWindow") != 500000 or "statusLine" not in merged \
            or not py["statusLine"]["command"].startswith("py .claude/hooks/statusline.py"):
        fails.append(f"install: merging settings — {merged.get('autoCompactWindow')} {py.get('statusLine')}")

    # ── installer: the withdrawn Read(...) context-economy rules (the sandbox turns them into denyRead for programs, so
    # npm test would not read node_modules) — guard_paths takes care of it. The Bash sandbox is opt-in: the template does not
    # enable it (it breaks `git add -A`, localhost services) nor override the user's setting ──
    total += 1
    old = {"permissions": {"deny": ["Read(./node_modules/**)", "Read(**/yarn.lock)", "Read(./vendor/**)"]}}
    merged = inst.merge_settings(src, old)
    deny = merged["permissions"]["deny"]
    mine = inst.merge_settings(src, {"sandbox": {"enabled": True}})
    if any(r in deny for r in ("Read(./node_modules/**)", "Read(**/yarn.lock)")) or "Read(./vendor/**)" not in deny \
            or "sandbox" in merged or mine.get("sandbox") != {"enabled": True}:
        fails.append(f"install: the sandbox and withdrawn rules — deny={deny} sandbox={merged.get('sandbox')} "
                     f"own={mine.get('sandbox')}")

    # ── protective hooks block the action when they fail themselves (onFailure: block, Claude Code ≥ 2.1.295); an update adds
    # the missing field to a hook that is already in the project, but does not override the user's choice ──
    total += 1
    guards = ("guard_bash.py", "guard_paths.py", "cleanroom_guard.py")
    def guard_hooks(settings):
        return {a.rsplit("/", 1)[-1]: h for e in settings["hooks"]["PreToolUse"] for h in e["hooks"]
                for a in h.get("args") or [] if a.rsplit("/", 1)[-1] in guards}
    in_src = guard_hooks(src)
    old_proj = json.loads(json.dumps(src))
    for h in guard_hooks(old_proj).values():
        h.pop("onFailure", None)
    guard_hooks(old_proj)["guard_paths.py"]["onFailure"] = "continue"     # a deliberate user choice
    upd = guard_hooks(inst.merge_settings(src, old_proj))
    if sorted(in_src) != sorted(guards) or any(h.get("onFailure") != "block" for h in in_src.values()) \
            or upd["guard_bash.py"].get("onFailure") != "block" or upd["cleanroom_guard.py"].get("onFailure") != "block" \
            or upd["guard_paths.py"].get("onFailure") != "continue":
        fails.append(f"hooki ochronne: onFailure — szablon {in_src}, po aktualizacji {upd}")

    # ── one-off explanation files (HTML, diagrams) in .claude/scratch/ do not go to git (core-problem-routing) ──
    total += 1
    gi = ROOT / ".tf" / "factory" / "gitignore"
    for ign in (".claude/scratch/",):
        if ign not in inst.ignored_paths() or (gi.exists() and ign not in gi.read_text(encoding="utf-8")):
            fails.append(f"install: {ign} is outside the ignored paths")
    # the factory's work results: privately the whole .tf/, in the .gitignore template (a team installation) the reproducible directories
    if ".tf/" not in inst.ignored_paths() or (gi.exists() and not all(
            f".tf/{d}/" in gi.read_text(encoding="utf-8") for d in ("cache", "logs", "runs", "backup"))):
        fails.append("install: .tf/ (prywatnie) albo .tf/{cache,logs,runs,backup}/ (szablon .gitignore) nieignorowane")

    # ── a ready opt-in sandbox configuration: only the sandbox key, no loopholes ──
    total += 1
    sb_file = ROOT / ".tf" / "factory" / "templates" / "sandbox.settings.json"
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
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} cost mechanism tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
