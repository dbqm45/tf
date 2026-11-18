#!/usr/bin/env python3
"""Tests of `scripts/sandbox_check.py` (checking the Bash sandbox on the human's machine) without model calls:
repository preparation, the probe run directly, reading the result of `claude -p` and the report. python3 tests/test_sandbox_check.py

The script belongs only to the factory repository (`scripts/` does not reach projects), so in an installed copy of the
tests (`.claude/tests/`) the test is skipped."""
import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
SCRIPT = ROOT / "scripts" / "sandbox_check.py"
TEMPLATE = ROOT / "core" / "factory" / "templates" / "sandbox.settings.json"


def load():
    spec = importlib.util.spec_from_file_location("sandbox_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if not SCRIPT.parent.is_dir():
        print("— test_sandbox_check: skipped (no scripts/ — this is a copy of the tests in a project, not the factory repository)")
        return 0
    sc = load()
    fails = []

    def check(name, cond):
        if not cond:
            fails.append(name)
            print(f"✗ {name}")

    # probe reading: "key: value" lines, noise skipped
    got = sc.parse_probe("noise\nwrite_cwd: OK\ngit_commit: DENIED fatal: x\n\n")
    check("parse_probe: keys", got == {"write_cwd": "OK", "git_commit": "DENIED fatal: x"})

    # a tool result from the stream-json stream: the content as text or a list of blocks; the first probe result counts
    events = [
        {"type": "system", "subtype": "init"},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": [
            {"type": "text", "text": "write_cwd: OK\nwrite_outside: DENIED"}]}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "write_cwd: DENIED"}]}},
        {"type": "result", "total_cost_usd": 0.0021},
    ]
    probe, cost = sc.read_stream("\n".join(json.dumps(e) for e in events))
    check("read_stream: first result", probe == {"write_cwd": "OK", "write_outside": "DENIED"})
    check("read_stream: cost", abs(cost - 0.0021) < 1e-9)
    check("read_stream: no result", sc.read_stream('{"type":"result","total_cost_usd":0}') == ({}, 0.0))

    # overhead measurement: pre/post pairs per label → median in ms
    log = "pre 1000000000 on\npost 1120000000 on\npre 2000000000 off\npost 2050000000 off\n" \
          "pre 3000000000 on\npost 3100000000 on\npre 4000000000 on\npost 4130000000 on\n"
    check("perf_medians", sc.perf_medians(log) == {"on": 120.0, "off": 50.0})

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        home = d / "home"
        home.mkdir()
        server, port = sc.serve_localhost()
        try:
            repo = sc.prepare(d / "work", TEMPLATE, port, home / ".sandbox-check-outside.tmp")
            check("prepare: probe in the root and the subdirectory",
                  (repo / "probe.sh").is_file() and (repo / "pkg" / "probe.sh").is_file())
            settings = json.loads((repo / ".claude" / "settings.json").read_text(encoding="utf-8"))
            check("prepare: settings from the template", settings == json.loads(TEMPLATE.read_text(encoding="utf-8")))
            check("prepare: no settings in the subdirectory", not (repo / "pkg" / ".claude").exists())
            clean = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True)
            check("prepare: clean repo after the commit", clean.returncode == 0 and clean.stdout == "")
            # probe without the sandbox: everything allowed, and the write outside the project lands in the given file
            out = subprocess.run(["sh", "./probe.sh"], cwd=repo / "pkg", capture_output=True, text=True, timeout=60,
                                 env={**os.environ, "HOME": str(home)}).stdout
            res = sc.parse_probe(out)
            check("probe: all keys", set(res) == set(sc.CHECKS))
            for key in ("write_cwd", "write_root", "write_outside", "write_git", "git_config", "git_hooks",
                        "git_commit", "git_add_all", "localhost"):
                check(f"probe without the sandbox: {key} = OK", res.get(key) == "OK")
            check("probe: no placeholders outside the sandbox", res.get("placeholders") == "none")
            check("probe: file outside the project", (home / ".sandbox-check-outside.tmp").exists())
        finally:
            server.shutdown()

    results = {"A_root": {"write_cwd": "OK", "write_outside": "DENIED"}, "B_subdir": {"write_cwd": "OK"}}
    md = sc.report(results, {"on": 119.0, "off": 56.0}, {"os": "Darwin", "claude": "2.1.302", "cost": 0.02})
    check("report: case header", "| A_root | B_subdir |" in md)
    check("report: missing result as —", "| write_outside | DENIED | — |" in md)
    check("report: overhead", "119" in md and "56" in md)
    check("report: system and version", "Darwin" in md and "2.1.302" in md)

    print(f"{'✓' if not fails else '✗'} test_sandbox_check: {'OK' if not fails else f'{len(fails)} errors'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
