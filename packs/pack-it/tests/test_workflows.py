#!/usr/bin/env python3
"""Testy workflows nakładki (.claude/workflows/*.js): poprawny nagłówek `meta`, fazy, brak źródeł niedeterminizmu oraz
logika audytu kodu (code-audit.js) w Node z atrapami agent/parallel/pipeline — bez modelu i bez kosztu.
python3 .claude/tests/test_workflows.py"""
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude").is_dir() and (p / "factory").is_dir())
WF = ROOT / ".claude" / "workflows"

# Uruchamia skrypt workflow jak funkcję: meta bez `export`, ciało w funkcji async (skrypty kończą się `return`).
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

INVENTORY = {"path": "docs/project/07-review/2026-10-21-audyt-inwentarz.md", "stack": "python 3.12",
             "modules": ["api", "billing"], "missing_tools": ["skaner sekretów"],
             "skills_present": ["arch-quality-attributes", "eng-module-depth", "ddd-connascence-analysis",
                                "sec-appsec-devsecops", "be-auth-security", "arch-threat-modeling",
                                "eng-tech-debt-audit", "eng-clean-code"]}


def finding(**kw):
    base = {"title": "x", "file": "", "line": None, "risk": 2, "reach": 1, "cost": "S", "evidence": "",
            "proposal": "p", "blocker": ""}
    return {**base, **kw}


def scenario(depth="standard", limit=8, dims=("architektura", "bezpieczenstwo", "jakosc", "dostepnosc"), date="2026-10-21"):
    return {"args": {"date": date, "dimensions": list(dims), "depth": depth, "limit": limit, "modules": [],
                     "exclude": ["vendor/"]},
            "replies": [
                {"label": "inwentarz", "reply": INVENTORY},
                {"label": "przegląd:architektura", "reply": {"findings": [
                    finding(title="cykl billing-accounts", file="api/a.py", line=10, risk=3, reach=2, cost="M",
                            evidence="import cykliczny api/a.py:10")]}},
                {"label": "przegląd:bezpieczenstwo", "reply": {"findings": [
                    finding(title="brak walidacji", file="api/a.py", line=10, risk=3, reach=3, cost="S",
                            evidence="api/a.py:10 bez walidacji"),
                    finding(title="brak sprawdzenia właściciela", file="api/b.py", line=5, risk=4, reach=3, cost="S",
                            evidence="api/b.py:5", blocker="autoryzacja")]}},
                {"label": "przegląd:jakosc", "reply": {"findings": [
                    finding(title="podejrzenie martwego kodu", risk=1, reach=1, cost="S")]}},
                {"label": "raport", "reply": "docs/project/07-review/2026-10-21-audyt-kodu.md"},
                {"contains": "Spróbuj obalić", "reply": {"refuted": False, "reason": "potwierdzone"}},
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
        check(m is not None, f"W-1 {f.name}: plik zaczyna się od `export const meta = {{…}}`")
        head = m.group(1) if m else ""
        check(re.search(rf"name: '{re.escape(f.stem)}'", head) and "description:" in head
              and not re.search(r"\$\{|\.\.\.|\w\(", head),
              f"W-2 {f.name}: meta to czysty literał z name = nazwa pliku i description")
        titles = re.findall(r"title: '([^']+)'", head)
        used = set(re.findall(r"phase\('([^']+)'\)", text)) | set(re.findall(r"phase: '([^']+)'", text))
        check(titles and set(titles) == used, f"W-3 {f.name}: fazy w meta = fazy użyte w skrypcie: {titles} / {sorted(used)}")
        check(not re.search(r"Date\.now\(|Math\.random\(|new Date\(\)", text),
              f"W-4 {f.name}: bez Date.now / Math.random / new Date() (wznowienie przebiegu)")

    audit = WF / "code-audit.js"
    check(audit.is_file(), "W-5: workflow code-audit zainstalowany (/code-audit; /eng-code-audit to skill)")
    if not shutil.which("node"):
        print(f"ℹ brak Node — logikę workflows sprawdza CI fabryki; tu tylko testy statyczne")
    elif audit.is_file():
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            out = run_node(audit, scenario(), tmp)
            res = out.get("result") or {}
            check(out.get("ok"), f"W-6: przebieg bez błędu: {out.get('error')}")
            types = {c.get("label"): c.get("agentType") for c in out.get("calls", [])}
            check(types.get("przegląd:architektura") == "architect" and types.get("przegląd:bezpieczenstwo") ==
                  "security-reviewer" and types.get("przegląd:jakosc") == "specialist",
                  f"W-7: wykonawcy wymiarów: {types}")
            inv = next((c for c in out.get("calls", []) if c.get("label") == "inwentarz"), {})
            check(inv.get("model") == "haiku" and "2026-10-21-audyt-inwentarz.md" in inv.get("prompt", ""),
                  "W-8: inwentarz na najtańszym modelu, do pliku z datą z argumentów")
            ranking = res.get("ranking", [])
            merged = next((r for r in ranking if r.get("file") == "api/a.py"), {})
            check(len([r for r in ranking if r.get("file") == "api/a.py"]) == 1
                  and sorted(merged.get("dimensions", [])) == ["architektura", "bezpieczenstwo"],
                  f"W-9: duplikat po plik:linia scalony z etykietami wymiarów: {ranking}")
            # ryzyko 3 × zasięg 3 ÷ koszt M (2) — wartości najostrożniejsze z duplikatów
            check(merged.get("score") == 4.5 and merged.get("id") == "A-01", f"W-10: ranking ryzyko × zasięg ÷ koszt: {merged}")
            check([b.get("file") for b in res.get("blockers", [])] == ["api/b.py"]
                  and all(r.get("file") != "api/b.py" for r in ranking), f"W-11: bloker poza rankingiem: {res.get('blockers')}")
            check([h.get("title") for h in res.get("hypotheses", [])] == ["podejrzenie martwego kodu"],
                  f"W-12: ustalenie bez dowodu → hipotezy: {res.get('hypotheses')}")
            nc = " ".join(res.get("not_checked", []))
            check("dostepnosc" in nc and "ux-accessibility" in nc, f"W-13: wymiar bez skilli pominięty i zapisany: {nc}")
            check(res.get("report") == "docs/project/07-review/2026-10-21-audyt-kodu.md"
                  and any("2026-10-21-audyt-kodu.md" in c.get("prompt", "") for c in out.get("calls", [])
                          if c.get("label") == "raport"), "W-14: raport do pliku z datą")
            check(not any("Spróbuj obalić" in c.get("prompt", "") for c in out.get("calls", [])),
                  "W-15: standard bez weryfikacji (tylko pełny)")

            out = run_node(audit, scenario(limit=2), tmp)
            res = out.get("result") or {}
            reviews = [c for c in out.get("calls", []) if str(c.get("label", "")).startswith("przegląd:")]
            check(len(reviews) == 2 and "jakosc" in " ".join(res.get("not_checked", [])),
                  f"W-16: limit wykonawców — nadmiarowe wymiary pominięte jawnie: {[c.get('label') for c in reviews]}")

            out = run_node(audit, scenario(depth="pelny"), tmp)
            calls = out.get("calls", [])
            models = {c.get("label"): c.get("model") for c in calls}
            check(models.get("przegląd:architektura") == "opus" and models.get("przegląd:bezpieczenstwo") == "opus"
                  and models.get("przegląd:jakosc") is None, f"W-17: pełny — architektura i bezpieczeństwo na opus: {models}")
            check(any("Spróbuj obalić" in c.get("prompt", "") for c in calls), "W-18: pełny — weryfikacja blokerów i top")

            out = run_node(audit, scenario(date=""), tmp)
            check(not out.get("ok") and "date" in out.get("error", "") and not out.get("calls"),
                  f"W-19: bez daty w argumentach → błąd przed pierwszym agentem: {out.get('error')}")
            out = run_node(audit, scenario(dims=("architektura", "magia")), tmp)
            check(not out.get("ok") and "magia" in out.get("error", ""), f"W-20: nieznany wymiar → błąd: {out.get('error')}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów workflows")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
