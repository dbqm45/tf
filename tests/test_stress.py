#!/usr/bin/env python3
"""Tests of tf stress (tools/stress.py) without a model: the library and corpora are valid, the mechanical engine
finds a planted edge case, the model engine runs end to end with the fake claude (tools/stress/fake_claude.py) and
its profiler sees phases, categories and wasted calls, the evaluator passes and fails as it should, the comparison
flags regressions and the JUnit report is well formed. python3 tests/test_stress.py"""
import json
import subprocess
import sys
import tempfile
import xml.dom.minidom
from argparse import Namespace
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
sys.path.insert(0, str(ROOT / "tools" / "stress" / "lib"))
import common  # noqa: E402
import mech  # noqa: E402
import model  # noqa: E402
import report  # noqa: E402

FAKE = ROOT / "tools" / "stress" / "fake_claude.py"


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    # S-1: the library loads without errors; every scenario has a category, engine and known faults
    errors = []
    lib = common.load_library(errors)
    check(not errors, f"S-1 library errors: {errors}")
    check(len(lib) >= 40, f"S-1 the library has {len(lib)} scenarios")
    ids = [s["id"] for s in lib]
    check(len(ids) == len(set(ids)), "S-1 scenario ids are unique")
    for s in lib:
        if s["engine"] == "mech":
            check(s["probe"] in mech.PROBES, f"S-1 {s['id']}: unknown probe {s.get('probe')}")
        if (s.get("expect") or {}).get("check"):
            c = s["expect"]["check"]
            check((common.CHECKS / f"{c}.test.mjs").exists() or (common.CHECKS / f"{c}.py").exists(),
                  f"S-1 {s['id']}: missing hidden check {c}")

    # S-2: a typo in a scenario is an error, not a silently skipped check
    bad = common.LIBRARY / "zz_test_bad.yaml"
    bad.write_text("id: BAD-1\nname: x\ncategory: Nope\nengine: model\nexpect: {outcom: delivered}\nsetup: [{fault: nope}]\n")
    try:
        errs = []
        common.load_library(errs)
        joined = " ".join(errs)
        check("unknown expect keys" in joined and "unknown fault" in joined and "unknown category" in joined,
              f"S-2 library errors not reported: {errs}")
    finally:
        bad.unlink()

    # S-3: corpora: ids unique per file, every guard case names an existing hook
    for name in ("weight", "intake", "guards", "tdd"):
        cases = common.load_yaml(common.CORPUS / f"{name}.yaml")["cases"]
        cids = [c["id"] for c in cases]
        check(len(cids) == len(set(cids)), f"S-3 {name}: duplicate case ids")
        if name == "guards":
            for c in cases:
                check((ROOT / "core" / "hooks" / f"{c['hook']}.py").exists(), f"S-3 {c['id']}: no hook {c['hook']}")

    with tempfile.TemporaryDirectory() as t:
        work = Path(t)
        # S-4: the mechanical engine on the bench fixture: intake corpus runs and reports cases with timings
        res = mech.run_mech({"id": "T-MECH", "probe": "intake", "fixture": "py-shop"}, work)
        cases = res.get("cases", [])
        check(len(cases) >= 25, f"S-4 intake cases: {len(cases)} {cases[:1]}")
        check(all(c.get("ms") is not None for c in cases), "S-4 every case is timed")
        check(sum(c["ok"] for c in cases) >= len(cases) * 0.8, f"S-4 intake mostly recognised: "
              f"{[c['reason'] for c in cases if not c['ok']][:5]}")

        # S-5: a hook call is classified: a dangerous command is denied, a safe one allowed
        tpl = common.template("py-shop", work, "default", "none")
        deny = mech.call_hook(tpl, "guard_bash.py", mech._payload(tpl, "PreToolUse", "Bash", {"command": "rm -rf /"}))
        allow = mech.call_hook(tpl, "guard_bash.py", mech._payload(tpl, "PreToolUse", "Bash", {"command": "git status"}))
        check(deny["decision"] == "deny" and allow["decision"] == "allow", f"S-5 hook decisions: {deny} {allow}")

        # S-6: the model engine end to end with the fake claude (node fixture): PASS, profile, probe log
        sc = {"id": "T-MODEL", "name": "fake typo", "category": "Loop speed", "engine": "model", "fixture": "node-tasks",
              "input": "typo", "budget": 1, "tags": [],
              "expect": {"outcome": "delivered", "check": "typo", "max_wall": "60s", "max_cost": 0.5, "max_tool_errors": 1}}
        o = Namespace(claude=f"{sys.executable} {FAKE}", model=None, timeout=2, _rep=0)
        node_ok = subprocess.run(["node", "--version"], capture_output=True).returncode == 0
        if node_ok:
            r = model.run_model(sc, work, o)
            check(r["verdict"] == "PASS", f"S-6 fake run verdict {r['verdict']}: {r['checks']}")
            p = r["profile"]
            check(p["tool_calls"] == 5 and p["tool_errors"] == 1, f"S-6 tool calls/errors: {p['tool_calls']} {p['tool_errors']}")
            check("model (main)" in p["by_category"] and "factory scripts" in p["by_category"] and "git" in p["by_category"],
                  f"S-6 categories: {p['by_category']}")
            check("intake" in p["by_phase"], f"S-6 the run_state.py stage call starts a phase: {p['by_phase']}")
            check(p["wasted"] and "missing.py" in p["wasted"][0]["detail"], f"S-6 wasted call recorded: {p['wasted']}")
            check(p["cost_usd"] == 0.12 and p["turns"] == 6, "S-6 cost and turns from the result event")
            check(p["hooks"] == {} or isinstance(p["hooks"], dict), "S-6 hook stats present")
            # S-7: the evaluator fails a run against a stricter expectation, with the reason
            sc2 = dict(sc, expect={"outcome": "stop:plan-approval", "max_cost": 0.05})
            col = model.collect(Path(r["project"]))
            checks, _ = model.evaluate(sc2, p, col, Path(r["project"]))
            failed = {c["name"] for c in checks if not c["ok"]}
            check(failed == {"outcome", "cost"}, f"S-7 failed checks: {failed}")
            data = {"meta": {"date": "x", "factory_version": "1", "factory_sha": "a"},
                    "scenarios": [dict(r, id="T-MODEL", name="fake", category="Loop speed", engine="model", tags=[],
                                       why=report.why(dict(r, engine="model")))]}
            data["hotspots"] = report.hotspots(data["scenarios"])
            check(any(h["area"].startswith("time: model") for h in data["hotspots"]), "S-7 hotspots rank model time")
            check(any(h["area"].startswith("wasted:") for h in data["hotspots"]), "S-7 hotspots list wasted calls")
            # S-8: compare flags a slower, failing candidate; junit is well formed
            worse = json.loads(json.dumps(data))
            worse["scenarios"][0]["verdict"] = "FAIL"
            worse["scenarios"][0]["profile"]["wall_s"] = p["wall_s"] + 100
            regs = report.compare(data, worse)
            check(any("PASS → FAIL" in x for x in regs) and any("slower" in x for x in regs), f"S-8 regressions: {regs}")
            xml.dom.minidom.parseString(report.junit(worse))
            report.write_all(work / "out", data)
            check((work / "out" / "report.md").read_text().startswith("# tf stress"), "S-8 report.md written")
        else:
            print("ℹ node not found — S-6..S-8 skipped")

    print(f"{total - len(fails)}/{total} checks passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
