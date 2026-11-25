#!/usr/bin/env python3
"""Add-on mechanism (core/factory/addons.py, contract 1) and the dna add-on wired through it.
python3 tests/test_addons.py

Every test builds a throw-away project (git repository + factory manifest) and runs addons.py in it as `tf addon`
would. Key property: a project without add-ons is left exactly as it was.
"""
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
ADDONS_PY = ROOT / "core" / "factory" / "addons.py"
DNA = ROOT / "addons" / "dna"


def project(mode: str = "private", files: dict | None = None) -> Path:
    p = Path(tempfile.mkdtemp(prefix="tf-addons-test-"))
    subprocess.run(["git", "init", "-q", str(p)], check=True)
    (p / ".claude").mkdir()
    (p / ".claude" / "factory-manifest.json").write_text(json.dumps({"mode": mode, "source": str(ROOT)}),
                                                         encoding="utf-8")
    # like a real installation: the engine's vendored PyYAML in .tf/factory/_vendor (tf install puts it there)
    import shutil
    shutil.copytree(ROOT / "core" / "factory" / "_vendor", p / ".tf" / "factory" / "_vendor")
    for rel, text in (files or {}).items():
        f = p / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")
    return p


def addon(name="demo", contract=1, provides=None, extra: dict | None = None) -> Path:
    d = Path(tempfile.mkdtemp(prefix="tf-addon-src-")) / name
    d.mkdir()
    meta = {"name": name, "version": "1.0.0", "contract": contract, "provides": provides or {}}
    (d / "addon.yaml").write_text(json.dumps(meta), encoding="utf-8")   # JSON is valid YAML
    for rel, text in (extra or {}).items():
        f = d / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
    return d


def tf_addon(proj: Path, *args) -> subprocess.CompletedProcess:
    env = {**os.environ, "DNA_OFFLINE": "1", "STANDARDS_OFFLINE": "1"}   # add-ons must not reach the network here
    return subprocess.run([sys.executable, str(ADDONS_PY), *args], cwd=proj, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def snapshot(p: Path) -> dict:
    return {f.relative_to(p).as_posix(): f.read_bytes() for f in p.rglob("*") if f.is_file()}


# ----------------------------------------------------------------

def test_no_addons_changes_nothing():
    p = project(files={"CLAUDE.local.md": "# mine\n"})
    before = snapshot(p)
    assert tf_addon(p, "sync").returncode == 0
    assert tf_addon(p, "list").returncode == 0
    assert tf_addon(p, "check").returncode == 0
    assert snapshot(p) == before


def test_add_wires_context_rules_and_overrides_then_remove_unwires():
    src = addon(provides={"context": "out/INDEX.md", "rules": "out/rules", "skill_overrides": "out/so.json",
                          "plan": "out/k.json"},
                extra={"out/INDEX.md": "# idx\n", "out/rules/ui.md": "---\npaths: [\"src/**\"]\n---\n- rule\n",
                       "out/so.json": '{"acme-fe-standards": "name-only", "other": "name-only"}',
                       "out/k.json": "{}", "tests/test_x.py": "", "lib/x.py": "x = 1\n"})
    p = project(files={"CLAUDE.local.md": "# mine\n", ".claude/settings.local.json": '{"skillOverrides": {"other": "off"}}'})
    r = tf_addon(p, "add", str(src))
    assert r.returncode == 0, r.stdout + r.stderr
    d = p / ".tf" / "addons" / "demo"
    assert (d / "lib" / "x.py").is_file() and not (d / "tests").exists()
    assert not (d / "out").exists()                      # output is not copied: it is built in the project
    # the output appears (e.g. after `learn`), sync wires it in
    for rel, text in {"out/INDEX.md": "# idx\n", "out/rules/ui.md": "---\npaths: [\"src/**\"]\n---\n- rule\n",
                      "out/so.json": '{"acme-fe-standards": "name-only", "other": "name-only"}', "out/k.json": "{}"}.items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(text, encoding="utf-8")
    r = tf_addon(p, "sync")
    assert "your value 'off' kept" in r.stdout, r.stdout
    instr = (p / "CLAUDE.local.md").read_text(encoding="utf-8")
    assert instr.startswith("# mine\n") and "@.tf/addons/demo/out/INDEX.md" in instr
    assert (p / ".claude" / "rules" / "addon-demo-ui.md").read_text(encoding="utf-8").endswith("- rule\n")
    so = json.loads((p / ".claude" / "settings.local.json").read_text(encoding="utf-8"))["skillOverrides"]
    assert so == {"acme-fe-standards": "name-only", "other": "off"}
    listed = json.loads(tf_addon(p, "list", "--json").stdout)
    assert listed[0]["plan"] == ".tf/addons/demo/out/k.json" and listed[0]["ok"]
    exclude = (p / ".git" / "info" / "exclude").read_text(encoding="utf-8")
    assert ".tf/addons/" in exclude and ".claude/rules/addon-*.md" in exclude
    # sync is idempotent
    before = snapshot(p)
    tf_addon(p, "sync")
    assert snapshot(p) == before
    assert tf_addon(p, "remove", "demo").returncode == 0
    assert (p / "CLAUDE.local.md").read_text(encoding="utf-8") == "# mine\n"
    assert not (p / ".claude" / "rules" / "addon-demo-ui.md").exists()
    so = json.loads((p / ".claude" / "settings.local.json").read_text(encoding="utf-8")).get("skillOverrides")
    assert so == {"other": "off"}
    assert not (p / ".tf" / "addons" / ".applied.json").exists()


def test_team_install_uses_claude_md_and_gitignore():
    src = addon(provides={"context": "out/INDEX.md"})
    p = project(mode="shared")
    tf_addon(p, "add", str(src))
    d = p / ".tf" / "addons" / "demo"
    (d / "out").mkdir()
    (d / "out" / "INDEX.md").write_text("x\n", encoding="utf-8")
    tf_addon(p, "sync")
    assert "@.tf/addons/demo/out/INDEX.md" in (p / "CLAUDE.md").read_text(encoding="utf-8")
    assert ".tf/addons/*/cache/" in (p / ".gitignore").read_text(encoding="utf-8")
    assert not (p / "CLAUDE.local.md").exists()


def test_incompatible_contract_is_refused_and_skipped():
    p = project()
    assert tf_addon(p, "add", str(addon(contract=2))).returncode == 2
    # a copy put there by hand is skipped, not fatal
    bad = p / ".tf" / "addons" / "demo"
    bad.mkdir(parents=True)
    (bad / "addon.yaml").write_text('{"name": "demo", "contract": 2, "provides": {"context": "x.md"}}')
    (bad / "x.md").write_text("x\n")
    r = tf_addon(p, "sync")
    assert r.returncode == 0 and "skipped — contract 2" in r.stdout
    assert not (p / "CLAUDE.local.md").exists()


def test_check_aggregates_and_failing_command_does_not_crash():
    blocker = addon("blocker", provides={"check": "chk.py --base {base}"},
                    extra={"chk.py": "import json,sys\nprint(json.dumps({'args': sys.argv[1:]}))\nsys.exit(1)\n"})
    broken = addon("broken", provides={"check": "missing.py"})
    p = project()
    tf_addon(p, "add", str(blocker))
    tf_addon(p, "add", str(broken))
    r = tf_addon(p, "check", "--base", "main", "--json")
    assert r.returncode == 1, r.stdout + r.stderr
    res = {e["addon"]: e for e in json.loads(r.stdout)}
    assert res["blocker"]["blocking"] and res["blocker"]["report"]["args"] == ["--base", "main"]
    assert not res["broken"]["blocking"] and res["broken"]["exit"] not in (0, 1)


def test_readd_keeps_output_and_declared_files():
    src = addon(provides={}, extra={"conf.yaml": "default\n"})
    meta = json.loads((src / "addon.yaml").read_text())
    meta["keep"] = ["conf.yaml"]
    (src / "addon.yaml").write_text(json.dumps(meta))
    p = project()
    tf_addon(p, "add", str(src))
    d = p / ".tf" / "addons" / "demo"
    (d / "out").mkdir()
    (d / "out" / "INDEX.md").write_text("built\n")
    (d / "conf.yaml").write_text("mine\n")
    tf_addon(p, "add", str(src))
    assert (d / "out" / "INDEX.md").read_text() == "built\n"
    assert (d / "conf.yaml").read_text() == "mine\n"


def test_dna_by_name_learn_and_wire():
    p = project(files={"package.json": '{"dependencies": {"react": "^18.2.0"}}',
                       "package-lock.json": '{"packages": {"node_modules/react": {"version": "18.3.1"}}}'})
    r = tf_addon(p, "add", "dna")                        # bare name: from the factory source in the manifest
    assert r.returncode == 0, r.stdout + r.stderr
    r = tf_addon(p, "learn")
    assert r.returncode == 0, r.stdout + r.stderr
    index = p / ".tf" / "addons" / "dna" / "out" / "INDEX.md"
    assert "React 18.3.1" in index.read_text(encoding="utf-8")
    assert "@.tf/addons/dna/out/INDEX.md" in (p / "CLAUDE.local.md").read_text(encoding="utf-8")
    assert subprocess.run([sys.executable, str(p / ".tf/addons/dna/dna.py"), "verify", "--root", str(p)],
                          capture_output=True).returncode == 0


def test_incomplete_addon_is_reinstalled_by_learn():
    # only addon.yaml left (e.g. the scripts were not on the checked-out branch): learn reinstalls it from the factory
    # source, keeping the add-on's own data, instead of failing with "can't open file"
    p = project(files={"package.json": '{"dependencies": {"react": "^18.2.0"}}'})
    assert tf_addon(p, "add", "dna").returncode == 0
    d = p / ".tf" / "addons" / "dna"
    (d / "dna.py").unlink()
    r = tf_addon(p, "list")
    assert "dna.py" in r.stdout and "missing" in r.stdout, r.stdout
    r = tf_addon(p, "learn")
    out = r.stdout + r.stderr
    assert r.returncode == 0 and "reinstall" in out and "can't open file" not in out, out
    assert (d / "dna.py").is_file()


def test_add_by_name_from_a_git_source_with_a_branch():
    # `tf install --repo <url>#<branch>` stores the source with `#<branch>`; git must get the URL and --branch,
    # not "url#branch" (git: "unable to update url base from redirection")
    repo = Path(tempfile.mkdtemp(prefix="tf-addon-repo-")) / "factory"
    import shutil
    shutil.copytree(ROOT / "addons" / "dna", repo / "addons" / "dna", ignore=shutil.ignore_patterns("__pycache__", "out", "cache"))
    g = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.test"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run([*g, "commit", "-q", "--allow-empty", "-m", "base"], check=True)
    subprocess.run([*g, "switch", "-q", "-c", "next"], check=True)
    subprocess.run([*g, "add", "-A"], check=True)
    subprocess.run([*g, "commit", "-q", "-m", "addons on a branch"], check=True)
    p = project()
    (p / ".claude" / "factory-manifest.json").write_text(
        json.dumps({"mode": "private", "source": f"{repo.as_uri()}#next"}), encoding="utf-8")
    r = tf_addon(p, "add", "dna")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (p / ".tf" / "addons" / "dna" / "addon.yaml").is_file()


def test_refresh_only_when_inputs_change_and_session_hook():
    p = project(files={"package.json": '{"dependencies": {"react": "^18.2.0"}}',
                       "package-lock.json": '{"packages": {"node_modules/react": {"version": "18.3.1"}}}'})
    assert tf_addon(p, "add", "dna").returncode == 0
    assert tf_addon(p, "learn").returncode == 0
    k = p / ".tf" / "addons" / "dna" / "out" / "knowledge.json"
    before = k.stat().st_mtime_ns
    assert tf_addon(p, "refresh").returncode == 0
    assert k.stat().st_mtime_ns == before                                    # nothing changed: nothing rebuilt
    (p / "package-lock.json").write_text('{"packages": {"node_modules/react": {"version": "18.3.2"}}}')
    # the SessionStart hook, in the foreground for the test
    (p / ".tf" / "factory").mkdir(parents=True, exist_ok=True)
    (p / ".tf" / "factory" / "addons.py").write_text(ADDONS_PY.read_text(encoding="utf-8"), encoding="utf-8")
    env = {**os.environ, "DNA_OFFLINE": "1", "TF_ADDON_REFRESH_SYNC": "1", "CLAUDE_PROJECT_DIR": str(p)}
    r = subprocess.run([sys.executable, str(ROOT / "core" / "hooks" / "addons_refresh.py")], cwd=p, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout == ""
    assert "React 18.3.2" in (p / ".tf/addons/dna/out/INDEX.md").read_text(encoding="utf-8")
    assert (p / ".tf" / "logs" / "addons-refresh.log").is_file()


def test_session_hook_without_addons_does_nothing():
    p = project()
    before = snapshot(p)
    r = subprocess.run([sys.executable, str(ROOT / "core" / "hooks" / "addons_refresh.py")], cwd=p,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)}, capture_output=True, text=True)
    assert r.returncode == 0 and snapshot(p) == before


def test_standards_and_dna_together():
    p = project(files={
        "package.json": '{"dependencies": {"react": "^18.2.0"}}',
        "package-lock.json": '{"packages": {"node_modules/react": {"version": "18.3.1"}}}',
        ".eslintrc.json": '{"rules": {"no-restricted-imports": ["error", {"paths": [{"name": "lodash", '
                          '"message": "Use lodash-es instead."}]}]}}',
        ".claude/skills/acme-fe-standards/SKILL.md": "# FE\n- Forms must use react-hook-form.\n"
                                                     "See https://acme.atlassian.net/wiki/spaces/FE/pages/42/Forms\n"})
    subprocess.run(["git", "add", "-A"], cwd=p, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "i"], cwd=p, check=True)
    for name in ("dna", "standards"):
        assert tf_addon(p, "add", name).returncode == 0
    r = tf_addon(p, "learn")
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.index("→ standards") < r.stdout.index("→ dna")              # producer before consumer
    assert (p / ".claude/rules/addon-standards-standards-fe.md").is_file()
    instr = (p / "CLAUDE.local.md").read_text(encoding="utf-8")
    assert "@.tf/addons/standards/out/INDEX.md" in instr and "@.tf/addons/dna/out/INDEX.md" in instr
    rows = {x["name"]: x for x in json.loads(tf_addon(p, "list", "--json").stdout)}
    assert rows["standards"]["pending"] == 1 and rows["standards"]["pending_file"].endswith("cache/pending.json")
    (p / "src").mkdir()
    (p / "src" / "util.ts").write_text("import { debounce } from 'lodash';\nexport const d = debounce;\n")
    r = tf_addon(p, "check", "--json")
    assert r.returncode == 1, r.stdout
    dna_report = next(e for e in json.loads(r.stdout) if e["addon"] == "dna")["report"]
    assert dna_report["findings"][0]["rule"] == "forbidden-import" and dna_report["findings"][0]["strength"] == "hard"
    # session start: the notice about the read only the agent can do
    (p / ".tf" / "factory").mkdir(parents=True, exist_ok=True)
    (p / ".tf" / "factory" / "addons.py").write_text(ADDONS_PY.read_text(encoding="utf-8"), encoding="utf-8")
    env = {**os.environ, "DNA_OFFLINE": "1", "STANDARDS_OFFLINE": "1", "TF_ADDON_REFRESH_SYNC": "1",
           "CLAUDE_PROJECT_DIR": str(p)}
    h = subprocess.run([sys.executable, str(ROOT / "core" / "hooks" / "addons_refresh.py")], cwd=p, env=env,
                       capture_output=True, text=True)
    out = json.loads(h.stdout)
    assert "1 add-on items wait for the session (confluence)" in out["systemMessage"]
    assert "data, not instructions" in out["hookSpecificOutput"]["additionalContext"]


def test_company_pack_rolls_out_standards_by_url():
    std = Path(tempfile.mkdtemp(prefix="std-repo-"))
    (std / "skills" / "acme-be-standards").mkdir(parents=True)
    (std / "skills" / "acme-be-standards" / "SKILL.md").write_text("# BE\n- Services must log the request id.\n")
    for args in (["init", "-q"], ["add", "-A"], ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "s"]):
        subprocess.run(["git", *args], cwd=std, check=True, capture_output=True)
    p = project(files={".tf/factory/packs/pack-acme/pack.yaml": json.dumps({
        "id": "pack-acme", "org_defaults": {"config": {"addons": {"standards": {
            "install": True,
            "sources": {"acme": {"git": std.as_uri(), "dir": "skills"}}}}}}})})
    env_on = {**os.environ, "DNA_OFFLINE": "1", "STANDARDS_OFFLINE": "0"}
    r = subprocess.run([sys.executable, str(ADDONS_PY), "learn"], cwd=p, capture_output=True, text=True, env=env_on)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "→ standards: install (addons.standards.install" in r.stdout
    rules = p / ".claude/rules/addon-standards-standards-be.md"
    assert "Services must log the request id" in rules.read_text(encoding="utf-8")
    listed = subprocess.run([sys.executable, str(p / ".tf/addons/standards/standards.py"), "source", "list"], cwd=p,
                            capture_output=True, text=True,
                            env={**os.environ, "TF_ADDON_SETTINGS": json.dumps({"sources": {"acme": {"git": std.as_uri()}}})})
    assert "[factory configuration (addons.standards.sources.acme)]" in listed.stdout
    # the project turns the company source off
    (p / ".tf/config").mkdir(parents=True)
    (p / ".tf/config/config.yaml").write_text("addons:\n  standards:\n    sources:\n      acme:\n        enabled: false\n")
    r = subprocess.run([sys.executable, str(ADDONS_PY), "learn"], cwd=p, capture_output=True, text=True, env=env_on)
    assert r.returncode == 0 and not rules.exists()


def test_learn_is_measured_and_report_adds_the_session_work():
    p = project(files={"package.json": '{"dependencies": {"react": "^18.2.0"}}',
                       "package-lock.json": '{"packages": {"node_modules/react": {"version": "18.3.1"}}}',
                       ".tf/config/config.yaml": "prices_usd_per_mtok:\n  haiku: {input: 1, output: 5, cache_read: 0.1, "
                                                 "cache_write: 1.25}\n"})
    tf_addon(p, "add", "dna")
    r = tf_addon(p, "learn")
    assert r.returncode == 0 and "learn: " in r.stdout and "(dna " in r.stdout and "no model calls" in r.stdout
    rec = json.loads((p / ".tf/logs/addons.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert rec["event"] == "learn" and rec["addons"][0]["name"] == "dna" and rec["addons"][0]["seconds"] >= 0
    rep = json.loads(tf_addon(p, "report", "--json").stdout)[0]
    assert rep["session_agents"] == 0 and rep["tokens_total"] == 0
    # the session work after learn, as the factory's log_usage hook records it
    import datetime as _dt
    later = (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(seconds=5)).isoformat(timespec="seconds")
    logs = p / ".tf/logs"
    (logs / "delegation.jsonl").write_text(
        json.dumps({"ts": later, "klass": "addon", "agent_id": "a1", "duration_ms": 12000}) + "\n"
        + json.dumps({"ts": later, "klass": "code", "agent_id": "a2"}) + "\n", encoding="utf-8")
    (logs / "usage.jsonl").write_text(
        json.dumps({"ts": later, "event": "SubagentStop", "agent_id": "a1", "models": {"claude-haiku-x": 3},
                    "input": 10000, "output": 2000, "cache_read": 50000, "cache_write": 0}) + "\n"
        + json.dumps({"ts": later, "event": "SubagentStop", "agent_id": "a2", "models": {"claude-haiku-x": 1},
                      "input": 999999, "output": 0, "cache_read": 0, "cache_write": 0}) + "\n", encoding="utf-8")
    rep = json.loads(tf_addon(p, "report", "--json").stdout)[0]
    assert rep["session_agents"] == 1 and rep["tokens_total"] == 62000 and rep["session_seconds"] == 12.0
    assert abs(rep["cost_usd"] - (10000 * 1 + 2000 * 5 + 50000 * 0.1) / 1e6) < 1e-9
    text = tf_addon(p, "report").stdout
    assert "tokens 62,000" in text and "total: " in text and "62,000 tokens, $0.0250" in text


def test_log_usage_keeps_the_addon_class():
    import importlib.util
    spec = importlib.util.spec_from_file_location("lu", ROOT / "core" / "hooks" / "log_usage.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.task_class("Class: addon\nRead the pages in pending.json") == "addon"   # not folded into "other"
    assert mod.task_class("Class: something-else\n") == "other"


def test_core_names_no_addon():
    for f in (ROOT / "core").rglob("*"):
        if f.is_file() and f.suffix in (".py", ".md", ".yaml", ".json"):
            text = f.read_text(encoding="utf-8", errors="replace")
            assert "addons/dna" not in text and "addons/standards" not in text, f


def main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"✗ {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - fails}/{len(tests)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
