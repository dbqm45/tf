#!/usr/bin/env python3
"""Tests of the pack workflows (.claude/workflows/*.js): a valid `meta` header, phases, no sources of nondeterminism and
the code audit logic (code-audit.js) in Node with agent/parallel/pipeline stubs — without a model and without cost.
python3 .claude/tests/test_workflows.py"""
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude").is_dir() and (p / ".tf" / "factory").is_dir())
WF = ROOT / ".claude" / "workflows"

# Runs a workflow script like a function: meta without `export`, the body in an async function (scripts end with `return`).
HARNESS = r"""
const fs = require('fs')
const [file, scenarioPath] = process.argv.slice(2)
const scenario = JSON.parse(fs.readFileSync(scenarioPath, 'utf8'))
const src = fs.readFileSync(file, 'utf8').replace('export const meta', 'const meta')
const calls = [], logs = [], phases = []
const agent = async (prompt, opts = {}) => {
  calls.push({prompt, ...opts})
  for (const r of scenario.replies) {
    if ((r.label && opts.label === r.label) || (r.contains && prompt.includes(r.contains))) return r.reply
  }
  return null
}
const parallel = async (thunks) => Promise.all(thunks.map(t => t().catch(() => null)))
const pipeline = async (items, ...stages) => Promise.all(items.map(async (item, i) => {
  let r = item
  for (const s of stages) { try { r = await s(r, item, i) } catch (e) { return null } }
  return r
}))
const phase = (t) => phases.push(t)
const log = (m) => logs.push(m)
const budget = {total: null, spent: () => 0, remaining: () => Infinity}
const run = new Function('agent', 'parallel', 'pipeline', 'phase', 'log', 'args', 'budget',
  `return (async () => { ${src}\n })()`)
run(agent, parallel, pipeline, phase, log, scenario.args, budget)
  .then(result => console.log(JSON.stringify({ok: true, result, calls, logs, phases})))
  .catch(e => console.log(JSON.stringify({ok: false, error: String(e && e.message || e), calls, logs, phases})))
"""

INVENTORY = {"path": "docs/project/07-review/2026-10-21-code-audit-inventory.md", "stack": "python 3.12",
             "modules": ["api", "billing"], "missing_tools": ["secrets scanner"],
             "skills_present": ["arch-quality-attributes", "eng-module-depth", "ddd-connascence-analysis",
                                "sec-appsec-devsecops", "be-auth-security", "arch-threat-modeling",
                                "eng-tech-debt-audit", "eng-clean-code"]}


def finding(**kw):
    base = {"title": "x", "file": "", "line": None, "risk": 2, "reach": 1, "cost": "S", "evidence": "",
            "proposal": "p", "blocker": ""}
    return {**base, **kw}


def scenario(depth="standard", limit=8, dims=("architecture", "security", "quality", "accessibility"), date="2026-10-21"):
    return {"args": {"date": date, "dimensions": list(dims), "depth": depth, "limit": limit, "modules": [],
                     "exclude": ["vendor/"]},
            "replies": [
                {"label": "inventory", "reply": INVENTORY},
                {"label": "review:architecture", "reply": {"findings": [
                    finding(title="billing-accounts cycle", file="api/a.py", line=10, risk=3, reach=2, cost="M",
                            evidence="circular import api/a.py:10")]}},
                {"label": "review:security", "reply": {"findings": [
                    finding(title="missing validation", file="api/a.py", line=10, risk=3, reach=3, cost="S",
                            evidence="api/a.py:10 no validation"),
                    finding(title="missing owner check", file="api/b.py", line=5, risk=4, reach=3, cost="S",
                            evidence="api/b.py:5", blocker="authz")]}},
                {"label": "review:quality", "reply": {"findings": [
                    finding(title="suspected dead code", risk=1, reach=1, cost="S")]}},
                {"label": "report", "reply": "docs/project/07-review/2026-10-21-code-audit.md"},
                {"contains": "Try to refute", "reply": {"refuted": False, "reason": "potwierdzone"}},
            ]}


def run_node(script: Path, sc: dict, tmp: Path) -> dict:
    (tmp / "harness.cjs").write_text(HARNESS, encoding="utf-8")
    (tmp / "scenario.json").write_text(json.dumps(sc, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(["node", str(tmp / "harness.cjs"), str(script), str(tmp / "scenario.json")],
                       capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"ok": False, "error": (r.stdout + r.stderr)[-800:], "calls": [], "logs": [], "phases": []}


def main() -> int:
    import tempfile
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    scripts = sorted(WF.glob("*.js")) if WF.is_dir() else []
    for f in scripts:
        text = f.read_text(encoding="utf-8")
        m = re.match(r"export const meta = \{(.*?)\n\}\n", text, re.S)
        check(m is not None, f"W-1 {f.name}: the file starts with `export const meta = {{…}}`")
        head = m.group(1) if m else ""
        check(re.search(rf"name: '{re.escape(f.stem)}'", head) and "description:" in head
              and not re.search(r"\$\{|\.\.\.|\w\(", head),
              f"W-2 {f.name}: meta is a pure literal with name = the file name and a description")
        titles = re.findall(r"title: '([^']+)'", head)
        used = set(re.findall(r"phase\('([^']+)'\)", text)) | set(re.findall(r"phase: '([^']+)'", text))
        check(titles and set(titles) == used, f"W-3 {f.name}: phases in meta = phases used in the script: {titles} / {sorted(used)}")
        check(not re.search(r"Date\.now\(|Math\.random\(|new Date\(\)", text),
              f"W-4 {f.name}: no Date.now / Math.random / new Date() (resuming a run)")

    audit = WF / "code-audit.js"
    check(audit.is_file(), "W-5: the code-audit workflow installed (/code-audit; /eng-code-audit is a skill)")
    if not shutil.which("node"):
        print(f"ℹ no Node — the workflow logic is checked by the factory CI; only static tests here")
    elif audit.is_file():
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            out = run_node(audit, scenario(), tmp)
            res = out.get("result") or {}
            check(out.get("ok"), f"W-6: a run without an error: {out.get('error')}")
            types = {c.get("label"): c.get("agentType") for c in out.get("calls", [])}
            check(types.get("review:architecture") == "architect" and types.get("review:security") ==
                  "security-reviewer" and types.get("review:quality") == "specialist",
                  f"W-7: dimension executors: {types}")
            inv = next((c for c in out.get("calls", []) if c.get("label") == "inventory"), {})
            check(inv.get("model") == "haiku" and "2026-10-21-code-audit-inventory.md" in inv.get("prompt", ""),
                  "W-8: the inventory on the cheapest model, to a file with the date from the arguments")
            ranking = res.get("ranking", [])
            merged = next((r for r in ranking if r.get("file") == "api/a.py"), {})
            check(len([r for r in ranking if r.get("file") == "api/a.py"]) == 1
                  and sorted(merged.get("dimensions", [])) == ["architecture", "security"],
                  f"W-9: a duplicate by file:line merged with the dimension labels: {ranking}")
            # risk 3 × reach 3 ÷ cost M (2) — the most cautious values of the duplicates
            check(merged.get("score") == 4.5 and merged.get("id") == "A-01", f"W-10: ranking risk × reach ÷ cost: {merged}")
            check([b.get("file") for b in res.get("blockers", [])] == ["api/b.py"]
                  and all(r.get("file") != "api/b.py" for r in ranking), f"W-11: the blocker outside the ranking: {res.get('blockers')}")
            check([h.get("title") for h in res.get("hypotheses", [])] == ["suspected dead code"],
                  f"W-12: a finding without evidence → hypotheses: {res.get('hypotheses')}")
            nc = " ".join(res.get("not_checked", []))
            check("accessibility" in nc and "ux-accessibility" in nc, f"W-13: a dimension without skills skipped and recorded: {nc}")
            check(res.get("report") == "docs/project/07-review/2026-10-21-code-audit.md"
                  and any("2026-10-21-code-audit.md" in c.get("prompt", "") for c in out.get("calls", [])
                          if c.get("label") == "report"), "W-14: the report to a file with the date")
            check(not any("Try to refute" in c.get("prompt", "") for c in out.get("calls", [])),
                  "W-15: standard without verification (full only)")

            out = run_node(audit, scenario(limit=2), tmp)
            res = out.get("result") or {}
            reviews = [c for c in out.get("calls", []) if str(c.get("label", "")).startswith("review:")]
            check(len(reviews) == 2 and "quality" in " ".join(res.get("not_checked", [])),
                  f"W-16: the executor limit — surplus dimensions skipped explicitly: {[c.get('label') for c in reviews]}")

            out = run_node(audit, scenario(depth="full"), tmp)
            calls = out.get("calls", [])
            models = {c.get("label"): c.get("model") for c in calls}
            check(models.get("review:architecture") == "opus" and models.get("review:security") == "opus"
                  and models.get("review:quality") is None, f"W-17: full — architecture and security on opus: {models}")
            check(any("Try to refute" in c.get("prompt", "") for c in calls), "W-18: full — verification of blockers and the top")

            out = run_node(audit, scenario(date=""), tmp)
            check(not out.get("ok") and "date" in out.get("error", "") and not out.get("calls"),
                  f"W-19: no date in the arguments → an error before the first agent: {out.get('error')}")
            out = run_node(audit, scenario(dims=("architecture", "magic")), tmp)
            check(not out.get("ok") and "magic" in out.get("error", ""), f"W-20: an unknown dimension → error: {out.get('error')}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of workflows")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
