"""Reports of tf stress: hotspots (where the time goes and what to improve), report.md, junit.xml, the console summary,
and the comparison of two result.json files (regressions)."""
from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from common import stats


def _model(results):
    return [r for r in results if r["engine"] == "model" and r.get("profile")]


def hotspots(results: list[dict], capacity: list[dict] | None = None) -> list[dict]:
    """Ranked findings: each with the area, the measured impact, the evidence and a direction for the fix."""
    out = []
    mr = _model(results)
    if mr:
        wall = sum(r["profile"]["wall_s"] for r in mr) or 1
        cats = {}
        for r in mr:
            for k, v in r["profile"]["by_category"].items():
                cats[k] = cats.get(k, 0) + v
        hooks = sum(r["profile"]["hooks_total_s"] for r in mr)
        for k, v in sorted(cats.items(), key=lambda kv: -kv[1]):
            out.append({"area": f"time: {k}", "impact_s": round(v, 1), "share": round(100 * v / wall, 1),
                        "evidence": f"{len(mr)} model runs, {wall:.0f} s wall in total", "kind": "share"})
        out.append({"area": "time: hooks (inside tool calls)", "impact_s": round(hooks, 1),
                    "share": round(100 * hooks / wall, 1), "evidence": "sum of every hook call measured by the probe",
                    "kind": "share"})
        labels = {}
        for r in mr:
            for k, v in r["profile"]["by_label"].items():
                x = labels.setdefault(k, {"n": 0, "s": 0.0, "errors": 0, "cat": v["cat"]})
                x["n"] += v["n"]
                x["s"] += v["s"]
                x["errors"] += v["errors"]
        top = sorted(labels.items(), key=lambda kv: -kv[1]["s"])[:15]
        for k, v in top:
            out.append({"area": f"call: {k}", "impact_s": round(v["s"], 1), "share": round(100 * v["s"] / wall, 1),
                        "evidence": f"{v['n']} calls, {v['s'] / max(v['n'], 1):.1f} s each, {v['errors']} errors",
                        "kind": "call", "n": v["n"], "cat": v["cat"]})
        wasted = {}
        for r in mr:
            for w in r["profile"]["wasted"]:
                key = w["label"]
                x = wasted.setdefault(key, {"n": 0, "examples": []})
                x["n"] += 1
                if len(x["examples"]) < 3:
                    x["examples"].append(f"{r['id']}: {w['detail'][:80]} → {w['out'][:90]}")
        for k, v in sorted(wasted.items(), key=lambda kv: -kv[1]["n"]):
            out.append({"area": f"wasted: {k}", "impact_s": None, "n": v["n"], "evidence": " | ".join(v["examples"]),
                        "kind": "wasted"})
        hk = {}
        for r in mr:
            for k, v in r["profile"]["hooks"].items():
                x = hk.setdefault(k, {"n": 0, "s": 0.0, "max": 0, "blocked": 0})
                x["n"] += v["n"]
                x["s"] += v["total_s"]
                x["max"] = max(x["max"], v["max_ms"])
                x["blocked"] += v["blocked"]
        for k, v in sorted(hk.items(), key=lambda kv: -kv[1]["s"])[:10]:
            out.append({"area": f"hook: {k}", "impact_s": round(v["s"], 1), "share": round(100 * v["s"] / wall, 1),
                        "evidence": f"{v['n']} calls, avg {1000 * v['s'] / max(v['n'], 1):.0f} ms, max {v['max']:.0f} ms, "
                                    f"blocked {v['blocked']}", "kind": "hook"})
        mc = [x for r in mr for x in [r["profile"]["model_call_s"]] if x.get("n")]
        if mc:
            calls = sum(x["n"] for x in mc)
            out.append({"area": "model calls per run", "impact_s": None, "kind": "model",
                        "evidence": f"{calls / len(mr):.0f} main-thread model calls per run, p50 "
                                    f"{stats([x['p50'] for x in mc])['p50']} s each; first tool after "
                                    f"{stats([r['profile']['first_tool_s'] for r in mr])['p50']} s"})
    for r in results:
        if r["engine"] == "mech":
            bad = [c for c in r.get("cases", []) if not c["ok"]]
            if bad:
                out.append({"area": f"edge cases: {r['id']} {r.get('name', '')}", "impact_s": None, "n": len(bad),
                            "kind": "edge", "evidence": " | ".join(f"{c['id']}: {c['reason']}" for c in bad[:8])})
    for c in capacity or []:
        out.append({"area": f"capacity: {c['scenario']}", "kind": "capacity", "impact_s": None,
                    "evidence": "; ".join(f"{x['size']}× → p50 {x['wall_p50']} s, ok {x['ok']}/{x['size']}" for x in c["rows"])
                    + (f"; breaking point {c['breaking']}" if c.get("breaking") else "")})
    return out


def console(results: list[dict]) -> str:
    lines = []
    w = max([len(r["id"]) for r in results] + [6])
    for r in results:
        extra = ""
        if r["engine"] == "model" and r.get("profile"):
            p = r["profile"]
            extra = f"{p['wall_s']:7.1f}s ${p.get('cost_usd') or 0:5.2f} turns {p.get('turns') or 0:3}"
        elif r.get("cases"):
            ok = sum(c["ok"] for c in r["cases"])
            extra = f"{ok:4}/{len(r['cases'])} cases {r.get('wall_s', 0):6.1f}s"
        icon = {"PASS": "✓", "FAIL": "✗", "ERROR": "!", "SKIP": "-"}.get(r["verdict"], "?")
        lines.append(f"{icon} {r['id']:{w}} {r['verdict']:5} {extra}  {r.get('name', '')}")
        for why in r.get("why", [])[:4]:
            lines.append(f"    {why}")
    return "\n".join(lines)


def why(r: dict) -> list[str]:
    if r["engine"] == "model":
        return [f"{c['name']}: {c['actual']} (expected {c['expected']})" for c in r.get("checks", []) if not c["ok"]]
    return [f"{c['id']}: {c['reason']}" for c in r.get("cases", []) if not c["ok"]][:12] + list(r.get("threshold_fails", []))


def markdown(data: dict) -> str:
    res = data["scenarios"]
    m = data["meta"]
    n_pass = sum(r["verdict"] == "PASS" for r in res)
    out = [f"# tf stress — {m['date']}", "",
           f"Factory {m.get('factory_version')} ({m.get('factory_sha')}) · {len(res)} scenarios · PASS {n_pass} · "
           f"FAIL {sum(r['verdict'] == 'FAIL' for r in res)} · ERROR {sum(r['verdict'] == 'ERROR' for r in res)} · "
           f"model cost ${sum((r.get('profile') or {}).get('cost_usd') or 0 for r in res):.2f}", "",
           "## Scenarios", "", "| | ID | Category | Scenario | Result | Why |", "|---|---|---|---|---|---|"]
    for r in res:
        if r["engine"] == "model" and r.get("profile"):
            p = r["profile"]
            got = f"{p['wall_s']} s · ${p.get('cost_usd') or 0:.2f} · {p.get('turns')} turns"
        else:
            got = f"{sum(c['ok'] for c in r.get('cases', []))}/{len(r.get('cases', []))} cases"
        out.append(f"| {r['verdict']} | {r['id']} | {r['category']} | {r.get('name', '')} | {got} | "
                   f"{'<br>'.join(x.replace('|', '/') for x in r.get('why', [])[:4])} |")
    out += ["", "## Hotspots (where the time goes, what to improve)", "", "| Area | Seconds | Share | Evidence |",
            "|---|---|---|---|"]
    for h in data.get("hotspots", []):
        out.append(f"| {h['area']} | {h.get('impact_s') if h.get('impact_s') is not None else ''} | "
                   f"{str(h.get('share', '')) + '%' if h.get('share') is not None else ''} | {h['evidence'].replace('|', '/')} |")
    for r in res:
        if r["engine"] == "model" and r.get("profile") and r["verdict"] != "PASS":
            out += ["", f"### {r['id']} timeline", "", "```"]
            for s in r["profile"]["timeline"][:60]:
                out.append(f"{s['t']:8.1f}s +{s['dur']:5.1f}s [{s['phase']:>8}] {'✗ ' if s['error'] else ''}{s['label']}: "
                           f"{s['detail'][:90]}")
            out.append("```")
    return "\n".join(out) + "\n"


def junit(data: dict) -> str:
    res = data["scenarios"]
    x = [f'<?xml version="1.0" encoding="UTF-8"?>',
         f'<testsuite name="tf-stress" tests="{len(res)}" failures="{sum(r["verdict"] == "FAIL" for r in res)}" '
         f'errors="{sum(r["verdict"] == "ERROR" for r in res)}">']
    for r in res:
        t = (r.get("profile") or {}).get("wall_s") or r.get("wall_s") or 0
        x.append(f'  <testcase classname="{escape(r["category"])}" name="{escape(r["id"] + " " + r.get("name", ""))}" time="{t}">')
        if r["verdict"] in ("FAIL", "ERROR"):
            tag = "failure" if r["verdict"] == "FAIL" else "error"
            x.append(f'    <{tag} message="{escape("; ".join(r.get("why", [])[:3]), {chr(34): "&quot;"})}"/>')
        x.append("  </testcase>")
    x.append("</testsuite>")
    return "\n".join(x) + "\n"


def compare(a: dict, b: dict, max_slower: float = 0.25, max_costlier: float = 0.25, min_s: float = 15) -> list[str]:
    """Regressions of b against a: verdicts that got worse, model runs slower/costlier beyond the thresholds,
    mech cases that broke, mech latencies that grew."""
    regs = []
    A = {r["id"]: r for r in a["scenarios"]}
    for r in b["scenarios"]:
        o = A.get(r["id"])
        if not o:
            continue
        if o["verdict"] == "PASS" and r["verdict"] != "PASS":
            regs.append(f"{r['id']}: {o['verdict']} → {r['verdict']} ({'; '.join(r.get('why', [])[:2])})")
        if r["engine"] == "model" and o.get("profile") and r.get("profile"):
            pa, pb = o["profile"], r["profile"]
            if pb["wall_s"] > pa["wall_s"] * (1 + max_slower) and pb["wall_s"] - pa["wall_s"] > min_s:
                regs.append(f"{r['id']}: slower {pa['wall_s']} → {pb['wall_s']} s")
            ca, cb = pa.get("cost_usd") or 0, pb.get("cost_usd") or 0
            if ca and cb > ca * (1 + max_costlier):
                regs.append(f"{r['id']}: costlier ${ca:.2f} → ${cb:.2f}")
        if r["engine"] == "mech":
            oc = {c["id"]: c for c in o.get("cases", [])}
            for c in r.get("cases", []):
                if c["id"] in oc and oc[c["id"]]["ok"] and not c["ok"]:
                    regs.append(f"{r['id']}/{c['id']}: broke — {c['reason']}")
                ms_a, ms_b = (oc.get(c["id"]) or {}).get("ms"), c.get("ms")
                if ms_a and ms_b and ms_b > ms_a * 1.5 and ms_b - ms_a > 50:
                    regs.append(f"{r['id']}/{c['id']}: slower {ms_a:.0f} → {ms_b:.0f} ms")
    return regs


def write_all(out: Path, data: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(data, indent=1, ensure_ascii=False, default=str))
    (out / "report.md").write_text(markdown(data))
    (out / "junit.xml").write_text(junit(data))
