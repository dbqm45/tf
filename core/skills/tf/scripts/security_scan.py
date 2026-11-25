#!/usr/bin/env python3
"""
Security scan of a slice: semgrep (OWASP Top 10 rules, the product's .semgrep.yml and the overlays' semgrep.yml) on the files changed
by the slice, dependency audit only when a manifest or lockfile changes, SARIF in the result directory, a verdict like
SEC-001 in ci_for_sdlc. A missing scanner is a FAIL with an install command, never a silent PASS.

  python3 .claude/skills/tf/scripts/security_scan.py scan [--base REF] [--out DIR]
                                                                       [--slice S<n> --attempt k] [--json]
  python3 .claude/skills/tf/scripts/security_scan.py verdict FILE.sarif... [--json]
  python3 .claude/skills/tf/scripts/security_scan.py cooldown [--fix]
  python3 .claude/skills/tf/scripts/security_scan.py scanner        # is semgrep here, or did the project decide without it

scan     — without --base: uncommitted changes and new files (the slice loop); with --base: also commits since the base (CI on a PR).
           Writes to --out (default reports/security): semgrep.sarif, npm-audit.sarif, pip-audit.sarif,
           verdict.json, summary.md (a section of the run report) and feedback.md (findings for the next attempt).
           With --slice the attempt's result goes to --out/attempt-<k>/ (attempts do not overwrite each other), and --out/feedback.md is
           a copy of the last attempt's feedback.md.
verdict  — a verdict from ready SARIF files.
cooldown — version cooldown (N10): npm min-release-age, pnpm minimumReleaseAge, Yarn npmMinimalAgeGate,
           uv exclude-newer ≥ 7 days and a lockfile in git. --fix writes the missing or too short settings itself
           (.npmrc; pnpm-workspace.yaml when the project has one, else .npmrc; .yarnrc.yml; [tool.uv] in pyproject.toml),
           keeps every other line, then checks again. A lockfile outside git is only reported (git add is yours).
           Run by the human (`tf cooldown --fix`, `tf onboard --yes`): the agent does not change these settings.

A missing scanner with the project's decision (`tf config security.scanner off --by human:<id> --reason "<why>"`,
`security.scanner` in .tf/config/config.yaml) is recorded in the verdict's notes ("scanner off by decision (who, when)")
instead of a FAIL.

Blocking: level error or warning with a CWE from OWASP Top 10 2021 or 2025; result level → the rule's default level →
warning; level none is skipped. The rest goes into the report. Exit code: 0 PASS, 1 FAIL, 2 bad call.
Scanners are looked up in PATH, or only in TF_SCAN_PATH if set. Semgrep rules: TF_SEMGREP_CONFIG
(default p/owasp-top-ten from the semgrep.dev registry; the host must be on the container's allowlist).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

OWASP_2021 = {
    "A01": [22, 23, 35, 59, 200, 201, 219, 264, 275, 276, 284, 285, 352, 359, 377, 402, 425, 441, 497, 538, 540, 548,
            552, 566, 601, 639, 651, 668, 706, 862, 863, 913, 922, 1275],
    "A02": [259, 261, 296, 310, 319, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 335, 336, 337, 338, 340,
            347, 523, 720, 757, 759, 760, 780, 818, 916],
    "A03": [20, 74, 75, 77, 78, 79, 80, 83, 87, 88, 89, 90, 91, 93, 94, 95, 96, 97, 98, 99, 100, 113, 116, 138, 184,
            470, 471, 564, 610, 643, 644, 652, 917],
    "A04": [73, 183, 209, 213, 235, 256, 257, 266, 269, 280, 311, 312, 313, 316, 419, 430, 434, 444, 451, 472, 501,
            522, 525, 539, 579, 598, 602, 642, 646, 650, 653, 656, 657, 799, 807, 840, 841, 927, 1021, 1173],
    "A05": [2, 11, 13, 15, 16, 260, 315, 520, 526, 537, 541, 547, 611, 614, 756, 776, 942, 1004, 1032, 1174],
    "A06": [937, 1035, 1104],
    "A07": [255, 259, 287, 288, 290, 294, 295, 297, 300, 302, 304, 306, 307, 346, 384, 521, 613, 620, 640, 798, 940,
            1216],
    "A08": [345, 353, 426, 494, 502, 565, 784, 829, 830, 915],
    "A09": [117, 223, 532, 778],
    "A10": [918],
}
OWASP_2025 = {
    "A01": [22, 23, 36, 59, 61, 65, 200, 201, 219, 276, 281, 282, 283, 284, 285, 352, 359, 377, 379, 402, 424, 425,
            441, 497, 538, 540, 548, 552, 566, 601, 615, 639, 668, 732, 749, 862, 863, 918, 922, 1275],
    "A02": [5, 11, 13, 15, 16, 260, 315, 489, 526, 547, 611, 614, 776, 942, 1004, 1174],
    "A03": [447, 1035, 1104, 1329, 1357, 1395],
    "A04": [261, 296, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 334, 335, 336, 337, 338,
            340, 342, 347, 523, 757, 759, 760, 780, 916, 1240, 1241],
    "A05": [20, 74, 76, 77, 78, 79, 80, 83, 86, 88, 89, 90, 91, 93, 94, 95, 96, 97, 98, 99, 103, 104, 112, 113, 114,
            115, 116, 129, 159, 470, 493, 500, 564, 610, 643, 644, 917],
    "A06": [73, 183, 256, 266, 269, 286, 311, 312, 313, 316, 362, 382, 419, 434, 436, 444, 451, 454, 472, 501, 522,
            525, 539, 598, 602, 628, 642, 646, 653, 656, 657, 676, 693, 799, 807, 841, 1021, 1022, 1125],
    "A07": [258, 259, 287, 288, 289, 290, 291, 293, 294, 295, 297, 298, 299, 300, 302, 303, 304, 305, 306, 307, 308,
            309, 346, 350, 384, 521, 613, 620, 640, 798, 940, 941, 1390, 1391, 1392, 1393],
    "A08": [345, 353, 426, 427, 494, 502, 506, 509, 565, 784, 829, 830, 915, 926],
    "A09": [117, 221, 223, 532, 778],
    "A10": [209, 215, 234, 235, 248, 252, 274, 280, 369, 390, 391, 394, 396, 397, 460, 476, 478, 484, 550, 636, 703,
            754, 755, 756],
}
OWASP_CWES = {c for table in (OWASP_2021, OWASP_2025) for cwes in table.values() for c in cwes}
CWE = re.compile(r"^(?:external/cwe/)?cwe[-:]?\s*0*(\d+)\b", re.I)

INSTALL = {
    "semgrep": "pipx install semgrep  (or: python3 -m pip install semgrep)",
    "npm": "zainstaluj Node.js z npm (https://nodejs.org/)",
    "pip-audit": "pip install pip-audit  (or: pipx install pip-audit)",
}
SEMGREP_DEFAULT = "p/owasp-top-ten"
NPM_LEVEL = {"critical": "error", "high": "error", "moderate": "warning", "low": "note", "info": "note"}
PY_MANIFEST = re.compile(r"(^|/)(requirements[^/]*\.txt|pyproject\.toml|uv\.lock|poetry\.lock|Pipfile\.lock)$")
NODE_MANIFEST = re.compile(r"(^|/)(package\.json|package-lock\.json|npm-shrinkwrap\.json|pnpm-lock\.yaml|yarn\.lock)$")
COOLDOWN_DAYS = 7


class ScanError(Exception):
    pass


# ── SARIF and verdict ────────────────────────────────────────────────────────────────────────────────────────────────

def empty_sarif(tool: str) -> dict:
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": tool, "rules": []}}, "results": []}]}


def cwes_of(*props) -> list[int]:
    out = []
    for p in props:
        if not isinstance(p, dict):
            continue
        for key in ("tags", "cwe"):
            vals = p.get(key)
            for v in (vals if isinstance(vals, list) else [vals] if vals else []):
                m = CWE.match(str(v).strip())
                if m and int(m.group(1)) not in out:
                    out.append(int(m.group(1)))
    return out


def findings(sarif: dict) -> list[dict]:
    """Findings from a SARIF log: rule, file, line, level, CWE, message (level none skipped)."""
    out = []
    for run in sarif.get("runs") or []:
        driver = ((run.get("tool") or {}).get("driver") or {})
        rules = driver.get("rules") or []
        by_id = {r.get("id"): r for r in rules if isinstance(r, dict)}
        for res in run.get("results") or []:
            idx = res.get("ruleIndex")
            rule = rules[idx] if isinstance(idx, int) and 0 <= idx < len(rules) else by_id.get(res.get("ruleId"), {})
            level = res.get("level") or ((rule.get("defaultConfiguration") or {}).get("level")) or "warning"
            if level == "none":
                continue
            loc = ((res.get("locations") or [{}])[0].get("physicalLocation") or {})
            uri = (loc.get("artifactLocation") or {}).get("uri")
            if uri and uri.startswith("file://"):
                uri = uri[len("file://"):]
            out.append({"rule": res.get("ruleId") or rule.get("id") or "?", "file": uri,
                        "line": (loc.get("region") or {}).get("startLine"), "level": level,
                        "cwe": cwes_of(rule.get("properties"), res.get("properties")),
                        "message": ((res.get("message") or {}).get("text") or "").strip(),
                        "tool": driver.get("name") or "?"})
    return out


def is_blocking(f: dict) -> bool:
    return f["level"] == "error" or (f["level"] == "warning" and any(c in OWASP_CWES for c in f["cwe"]))


def verdict(paths: list[Path], errors: list[str] | None = None) -> dict:
    errors = list(errors or [])
    blocking, other = [], []
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("runs"), list):
                raise ValueError("no runs")
        except (OSError, ValueError) as e:
            errors.append(f"{p}: not a SARIF log ({e})")
            continue
        for f in findings(data):
            (blocking if is_blocking(f) else other).append(f)
    return {"status": "FAIL" if blocking or errors else "PASS", "blocking": blocking, "other": other,
            "errors": errors}


def where(f: dict) -> str:
    if not f.get("file"):
        return "(no location)"
    return f"{f['file']}:{f['line']}" if f.get("line") else f["file"]


def item(f: dict) -> str:
    cwe = ", ".join(f"CWE-{c}" for c in f["cwe"])
    msg = f" — {f['message'].splitlines()[0][:160]}" if f.get("message") else ""
    return f"- {f['rule']} {where(f)} ({', '.join(x for x in (cwe, f['level']) if x)}){msg}"


def render(v: dict) -> list[str]:
    head = (f"SCAN: {v['status']} — blocking: {len(v['blocking'])}, below the threshold: {len(v['other'])}"
            + (f", scan errors: {len(v['errors'])}" if v["errors"] else ""))
    lines = [head]
    if v["errors"]:
        lines += ["Scan errors (the scan did not run — this is not a clean result):", *(f"- {e}" for e in v["errors"])]
    if v["blocking"]:
        lines += ["Blocking (fix before the commit):", *map(item, v["blocking"])]
    if v["other"]:
        lines += ["Below the threshold (for the run report):", *map(item, v["other"])]
    if v.get("skipped"):
        lines += ["Dependency audit skipped:", *(f"- {s}" for s in v["skipped"])]
    return lines


# ── changed files ────────────────────────────────────────────────────────────────────────────────────────────────

def git(*args, cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise ScanError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def changed_files(root: Path, base: str | None, skip: list[str]) -> list[str]:
    # -z: names exactly as on disk — without it git quotes non-ASCII letters, quotes and tabs and the file would drop out
    names = set(git("diff", "--name-only", "-z", "HEAD", cwd=root).split("\0"))
    names |= set(git("ls-files", "--others", "--exclude-standard", "-z", cwd=root).split("\0"))
    if base:
        names |= set(git("diff", "--name-only", "-z", f"{base}...HEAD", cwd=root).split("\0"))
    # The factory's work output (.tf/: runs, reports, logs) outside the scan.
    prefixes = [".tf/", *(s.rstrip("/") + "/" for s in skip if s)]
    return sorted(n for n in names if n and (root / n).is_file() and not any(n.startswith(p) for p in prefixes))


# ── scanners ────────────────────────────────────────────────────────────────────────────────────────────────────────

def tool(name: str) -> str | None:
    return shutil.which(name, path=os.environ.get("TF_SCAN_PATH") or None)


def engine_module(root: Path, name: str):
    """A module of the project's engine (`.tf/factory/<name>.py`); None when it is absent or broken."""
    import importlib.util
    path = root / ".tf" / "factory" / f"{name}.py"
    if not path.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location(f"tf_scan_{name}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:  # noqa: BLE001 — without the engine: no decision, the default patterns
        return None


def scanner_decision(root: Path) -> dict | None:
    """The project's recorded decision to work without a scanner (`security.scanner: off`, by a human); None — no decision,
    a missing scanner is a FAIL."""
    packs = engine_module(root, "packs")
    dec = packs.scanner_decision(root) if packs and hasattr(packs, "scanner_decision") else None
    # a decision is a human's, with a reason (as `tf config security.scanner off` requires); anything less stays strict
    return dec if (isinstance(dec, dict) and str(dec.get("by", "")).startswith("human:")
                   and str(dec.get("reason") or "").strip()) else None


def decision_text(dec: dict) -> str:
    return (f"scanner off by decision ({dec.get('by')}, {dec.get('at') or 'no date'})"
            + (f": {' '.join(str(dec['reason']).split())[:200]}" if dec.get("reason") else ""))


SEMGREP_STATE = Path(".tf") / "cache" / "semgrep"
SEMGREP_STATE_VARS = {"SEMGREP_SETTINGS_FILE": "settings.yml", "SEMGREP_LOG_FILE": "semgrep.log",
                      "SEMGREP_VERSION_CACHE_PATH": "version-cache"}


def semgrep_env(root: Path) -> dict[str, str]:
    """Semgrep state in the clone instead of in $HOME (PRB-32): in the Bash sandbox of the pdi phase container HOME is not writable
    and semgrep 1.183.0 fails with FileNotFoundError at mkdir (reproduced 2026-11-05). The directory has its own .gitignore
    with `*`, so it does not dirty the tree; variables set by a human stay."""
    state = root / SEMGREP_STATE
    state.mkdir(parents=True, exist_ok=True)
    ignore = state / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n", encoding="utf-8")
    env = dict(os.environ)
    for name, leaf in SEMGREP_STATE_VARS.items():
        env.setdefault(name, str(state / leaf))
    return env


def run_semgrep(root: Path, files: list[str], out: Path) -> None:
    target = out / "semgrep.sarif"
    if not files:
        target.write_text(json.dumps(empty_sarif("Semgrep"), indent=2) + "\n", encoding="utf-8")
        return
    cmd = [tool("semgrep"), "scan", "--metrics=off", "--sarif", "--output", str(target),
           "--config", os.environ.get("TF_SEMGREP_CONFIG") or SEMGREP_DEFAULT]
    if (root / ".semgrep.yml").is_file():
        cmd += ["--config", ".semgrep.yml"]
    for rules in sorted((root / ".tf" / "factory" / "packs").glob("*/semgrep.yml")):   # overlay rules (e.g. the company's)
        cmd += ["--config", rules.relative_to(root).as_posix()]
    try:
        r = subprocess.run([*cmd, *files], cwd=root, capture_output=True, text=True, env=semgrep_env(root))
    except OSError as e:   # cannot start (a broken install, a command line too long on Windows): a FAIL, never a PASS
        raise ScanError(f"semgrep could not be started: {e}") from None
    if r.returncode != 0 or not target.is_file():
        tail = (r.stderr or r.stdout).strip().splitlines()[-5:]
        target.unlink(missing_ok=True)
        raise ScanError(f"semgrep ended with code {r.returncode}: {' | '.join(tail) or 'no message'}")


def line_of(text: str, pred) -> int | None:
    return next((i for i, line in enumerate(text.splitlines(), 1) if pred(line)), None)


def npm_audit_sarif(audit, lock_rel: str, lock_text: str | None) -> dict:
    """`npm audit --json` (auditReportVersion 2) as SARIF — a port of scripts/lib/npm-audit-sarif.mjs from ci_for_sdlc."""
    if not isinstance(audit, dict):
        raise ScanError("npm audit: this is not an audit report (auditReportVersion 2)")
    if audit.get("error"):
        e = audit["error"] if isinstance(audit["error"], dict) else {}
        raise ScanError(f"npm audit did not run: {' '.join(str(x) for x in (e.get('code'), e.get('summary')) if x) or 'unknown error'}")
    if audit.get("auditReportVersion") != 2:
        raise ScanError(f"npm audit: auditReportVersion {audit.get('auditReportVersion', 'none')} (expected 2)")
    rules, index, results, seen = [], {}, [], set()
    for pkg, v in (audit.get("vulnerabilities") or {}).items():
        for a in (v or {}).get("via") or []:
            if not isinstance(a, dict):
                continue
            ghsa = re.search(r"GHSA(-[a-z0-9]{4}){3}", str(a.get("url") or ""), re.I)
            rid = f"npm-audit/{ghsa.group(0) if ghsa else a.get('source') or a.get('title') or 'advisory'}"
            node = ((v.get("nodes") or [None])[0]) or f"node_modules/{pkg}"
            if (rid, node) in seen:
                continue
            seen.add((rid, node))
            level = NPM_LEVEL.get(a.get("severity"), "warning")
            if rid not in index:
                index[rid] = len(rules)
                rules.append({"id": rid, "shortDescription": {"text": str(a.get("title") or rid)},
                              **({"helpUri": str(a["url"])} if a.get("url") else {}),
                              "defaultConfiguration": {"level": level},
                              "properties": {"tags": ["security", *map(str, a.get("cwe") or [])]}})
            needle = json.dumps(node) + ":"
            line = line_of(lock_text, lambda s: s.lstrip().startswith(needle)) if lock_text else None
            results.append({"ruleId": rid, "ruleIndex": index[rid], "level": level,
                            "message": {"text": f"{a.get('name') or pkg} {a.get('range') or v.get('range') or ''}".strip()
                                        + f": {a.get('title') or rid} ({a.get('severity') or 'unknown'}, {node})"},
                            "locations": [{"physicalLocation": {"artifactLocation": {"uri": lock_rel},
                                                                **({"region": {"startLine": line}} if line else {})}}]})
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": "npm audit", "informationUri": "https://docs.npmjs.com/cli/commands/npm-audit",
                                          "rules": rules}}, "results": results}]}


def run_npm_audit(root: Path, lock_rel: str, out: Path, name: str) -> None:
    lock = root / lock_rel
    r = subprocess.run([tool("npm"), "audit", "--json"], cwd=lock.parent, capture_output=True, text=True)
    try:
        audit = json.loads(r.stdout)
    except ValueError:
        raise ScanError(f"npm audit ({lock_rel}): the output is not JSON: {(r.stderr or r.stdout).strip()[:300]}")
    sarif = npm_audit_sarif(audit, lock_rel, lock.read_text(encoding="utf-8"))
    (out / name).write_text(json.dumps(sarif, indent=2) + "\n", encoding="utf-8")


def pip_audit_sarif(report, manifest_rel: str, manifest_text: str | None) -> dict:
    """The result of `pip-audit -f json` as SARIF. pip-audit does not give severity: every known vulnerability is an error
    with CWE-1104 (a component with a vulnerability, A06:2021 / A03:2025), i.e. it blocks."""
    if not isinstance(report, dict) or not isinstance(report.get("dependencies"), list):
        raise ScanError("pip-audit: the output has no dependencies list")
    rules, index, results = [], {}, []
    for dep in report["dependencies"]:
        for vuln in dep.get("vulns") or []:
            rid = f"pip-audit/{vuln.get('id') or 'advisory'}"
            if rid not in index:
                index[rid] = len(rules)
                rules.append({"id": rid, "shortDescription": {"text": (vuln.get("description") or rid)[:200]},
                              "defaultConfiguration": {"level": "error"},
                              "properties": {"tags": ["security", "CWE-1104", *(vuln.get("aliases") or [])]}})
            norm = re.sub(r"[-_.]+", "-", str(dep.get("name") or "").lower())
            line = line_of(manifest_text, lambda s: re.sub(r"[-_.]+", "-", s.strip().lower()).startswith(norm)) \
                if manifest_text and norm else None
            fix = ", ".join(vuln.get("fix_versions") or []) or "none"
            results.append({"ruleId": rid, "ruleIndex": index[rid], "level": "error",
                            "message": {"text": f"{dep.get('name')} {dep.get('version')}: {vuln.get('id')} (poprawka: {fix})"},
                            "locations": [{"physicalLocation": {"artifactLocation": {"uri": manifest_rel},
                                                                **({"region": {"startLine": line}} if line else {})}}]})
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": "pip-audit", "informationUri": "https://github.com/pypa/pip-audit",
                                          "rules": rules}}, "results": results}]}


def run_pip_audit(root: Path, manifest_rel: str, out: Path, name: str) -> None:
    raw = out / (Path(name).stem + ".json")
    raw.unlink(missing_ok=True)
    path = root / manifest_rel
    if path.name.startswith("requirements"):
        cmd = [tool("pip-audit"), "-r", manifest_rel, "-f", "json", "-o", str(raw)]
    else:  # project (pyproject.toml / lockfile): pip-audit resolves the project directory's dependencies
        cmd = [tool("pip-audit"), "-f", "json", "-o", str(raw), str(path.parent.relative_to(root) or ".")]
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if r.returncode not in (0, 1) or not raw.is_file():  # 1 = vulnerabilities found
        raise ScanError(f"pip-audit ({manifest_rel}) ended with code {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}")
    try:
        report = json.loads(raw.read_text(encoding="utf-8"))
    except ValueError:
        raise ScanError(f"pip-audit ({manifest_rel}): the output is not JSON")
    manifest = root / manifest_rel if path.name.startswith("requirements") else path.parent / "pyproject.toml"
    text = manifest.read_text(encoding="utf-8") if manifest.is_file() else None
    sarif = pip_audit_sarif(report, str(manifest.relative_to(root)), text)
    (out / name).write_text(json.dumps(sarif, indent=2) + "\n", encoding="utf-8")


NODE_DEP_KEYS = ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")
NO_DEPS = "package.json without dependencies (dependencies, devDependencies, optionalDependencies, peerDependencies)"


def node_has_deps(manifest: Path) -> bool:
    """Whether package.json declares dependencies. An unreadable manifest counts as having dependencies (never a silent PASS);
    a missing file (a deleted manifest) — no dependencies."""
    if not manifest.is_file():
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return True
    return not isinstance(data, dict) or any(data.get(k) for k in NODE_DEP_KEYS)


def audit_jobs(root: Path, files: list[str]) -> tuple[list[tuple], list[str], list[str]]:
    """Audits to run when a manifest or lockfile changed: (tool, file). Errors: a stack without an audit.
    Skipped: manifests without dependencies and without a lockfile — nothing to audit."""
    jobs, errors, skipped, dirs_node, dirs_py = [], [], [], set(), set()
    for f in files:
        if NODE_MANIFEST.search(f):
            dirs_node.add(str(Path(f).parent))
        elif PY_MANIFEST.search(f):
            if Path(f).name.startswith("requirements"):
                jobs.append(("pip-audit", f))
            else:
                dirs_py.add(str(Path(f).parent))
    for d in sorted(dirs_node):
        base = root / d
        lock = next((n for n in ("package-lock.json", "npm-shrinkwrap.json") if (base / n).is_file()), None)
        if lock:
            jobs.append(("npm", str(Path(d) / lock) if d != "." else lock))
        elif (base / "pnpm-lock.yaml").is_file() or (base / "yarn.lock").is_file():
            errors.append(f"{d}: the scan does not support a pnpm/Yarn dependency audit — run `pnpm audit` "
                          "or `yarn npm audit` and decide (STOP), or add package-lock.json")
        elif not node_has_deps(base / "package.json"):
            skipped.append(f"{d}: {NO_DEPS} and without a lockfile — there is nothing to audit")
        else:
            errors.append(f"{d}: a changed package.json without a lockfile — the lockfile must be in the repo (N10)")
    for d in sorted(dirs_py):
        jobs.append(("pip-audit", str(Path(d) / "pyproject.toml") if d != "." else "pyproject.toml"))
    return jobs, errors, skipped


# ── commands ──────────────────────────────────────────────────────────────────────────────────────────────────────

def slice_lines(v: dict, slice_id: str, attempt: int) -> list[str]:
    if v["status"] == "PASS":
        return [f"GATE {slice_id}: PASS (security scan, attempt {attempt}/2)"]
    why = (f"{len(v['blocking'])} blocking" if v["blocking"] else "") + \
          (", " if v["blocking"] and v["errors"] else "") + (f"{len(v['errors'])} scan errors" if v["errors"] else "")
    lines = [f"GATE {slice_id}: FAIL (security scan: {why}, attempt {attempt}/2)"]
    if attempt >= 2 or (v["errors"] and not v["blocking"]):
        where_ = "; ".join(f"{f['rule']} {where(f)}" for f in v["blocking"]) or "; ".join(v["errors"])
        lines += ["", f"STOP — {slice_id} (security scan)",
                  f"Reason: {'the scan did not run' if not v['blocking'] else 'blocking findings after 2 attempts'}: {where_}",
                  "Done: the slice's code and tests (not committed); SARIF and the verdict in the scan directory",
                  "Needed from the human: a fix or a decision on an exception with a reason "
                  "(e.g. `nosemgrep: <rule>` on the line), or installing the missing scanner",
                  f"Resume: from {slice_id} in plan.md"]
    return lines


def write_outputs(out: Path, v: dict, lines: list[str]) -> None:
    (out / "verdict.json").write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fb = ["# Security scan — to fix in the next attempt", "",
          *(map(item, v["blocking"]) if v["blocking"] else ["- no blocking findings"]), *(f"- {e}" for e in v["errors"])]
    (out / "feedback.md").write_text("\n".join(fb) + "\n", encoding="utf-8")
    summ = ["## Security", "", f"Scan: {v['status']} (blocking: {len(v['blocking'])}, "
            f"below the threshold: {len(v['other'])}, scan errors: {len(v['errors'])}).", ""]
    summ += ["Below the threshold:", *map(item, v["other"])] if v["other"] else ["Below the threshold: none."]
    if v.get("skipped"):
        summ += ["", "Dependency audit skipped:", *(f"- {s}" for s in v["skipped"])]
    if v.get("notes"):
        summ += ["", "Notes:", *(f"- {n}" for n in v["notes"])]
    if v["blocking"] or v["errors"]:
        summ += ["", "Blocking and errors:", *map(item, v["blocking"]), *(f"- {e}" for e in v["errors"])]
    (out / "summary.md").write_text("\n".join(summ) + "\n", encoding="utf-8")


def cmd_scan(a) -> int:
    root = Path(git("rev-parse", "--show-toplevel", cwd=Path.cwd()).strip())
    out = Path(a.out) if os.path.isabs(a.out) else Path.cwd() / a.out
    try:
        rel_out = str(out.resolve().relative_to(root.resolve()))
    except ValueError:
        rel_out = ""
    base_out = out
    # Slice: every attempt in its own attempt-<k> directory (the report shows all of them); in --out only the last
    # attempt's feedback.md. Without --slice (CI) the result goes straight into --out.
    clean = [out]
    if a.slice:
        out = base_out / f"attempt-{a.attempt}"
        clean.append(out)
    for d in clean:
        d.mkdir(parents=True, exist_ok=True)
        for old in list(d.glob("*.sarif")) + [d / n for n in ("verdict.json", "feedback.md", "summary.md")]:
            old.unlink(missing_ok=True)
    errors, notes = [], []
    files = changed_files(root, a.base, [rel_out])
    jobs, job_errors, skipped = audit_jobs(root, files)
    errors += job_errors
    needed = (["semgrep"] if files else []) + sorted({t for t, _ in jobs})
    missing = [n for n in needed if not tool(n)]
    dec = scanner_decision(root) if missing else None
    if dec:      # the project decided once to work without it: recorded instead of a FAIL that stops the task
        notes.append(f"{', '.join(missing)}: {decision_text(dec)}")
    else:
        errors += [f"the scanner {n} is missing — install it: {INSTALL[n]}" for n in missing]
    if files and "semgrep" not in missing:
        try:
            run_semgrep(root, files, out)
        except ScanError as e:
            errors.append(str(e))
    elif not files or dec:
        run_semgrep(root, [], out)
    counts: dict[str, int] = {}
    for t, f in jobs:
        if t in missing:
            continue
        stem = "npm-audit" if t == "npm" else "pip-audit"
        counts[stem] = counts.get(stem, 0) + 1
        name = f"{stem}.sarif" if counts[stem] == 1 else f"{stem}-{counts[stem]}.sarif"
        try:
            (run_npm_audit if t == "npm" else run_pip_audit)(root, f, out, name)
        except ScanError as e:
            errors.append(str(e))
    v = verdict(sorted(out.glob("*.sarif")), errors)
    v["files"] = files
    v["audits"] = [f for _, f in jobs]
    v["skipped"] = skipped
    if notes:
        v["notes"] = notes
    lines = render(v) + [f"Note: {n}" for n in notes]
    if a.slice:
        lines += slice_lines(v, a.slice, a.attempt)
    write_outputs(out, v, lines)
    if out != base_out:
        shutil.copyfile(out / "feedback.md", base_out / "feedback.md")
    print(json.dumps(v, ensure_ascii=False, indent=2) if a.json else "\n".join(lines))
    return 0 if v["status"] == "PASS" else 1


def cmd_scanner(_a) -> int:
    """Whether the slice scan can run here: semgrep present, or the project's decision to work without it. Exit code 0 —
    ready (or decided), 1 — missing and undecided (run_report.py start asks the human once, at the start)."""
    try:
        root = Path(git("rev-parse", "--show-toplevel", cwd=Path.cwd()).strip())
    except ScanError:
        root = Path.cwd()
    if tool("semgrep"):
        print("✓ scanner: semgrep is available")
        return 0
    dec = scanner_decision(root)
    if dec:
        print(f"⚠ scanner: semgrep is missing — {decision_text(dec)}; the slice scans record this instead of a FAIL")
        return 0
    print(f"⚠ scanner: semgrep is missing — every slice scan will FAIL and stop the task. Ask the human now, once: install it "
          f"({INSTALL['semgrep']}) or record the decision to work without it: python3 .tf/factory/tf.py config "
          "security.scanner off --by human:<id> --reason \"<why>\"")
    return 1


def cmd_verdict(a) -> int:
    v = verdict([Path(p) for p in a.sarif])
    print(json.dumps(v, ensure_ascii=False, indent=2) if a.json else "\n".join(render(v)))
    return 0 if v["status"] == "PASS" else 1


# ── version cooldown (N10) ──────────────────────────────────────────────────────────────────────────────────────────

DUR = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(m|min|mins|minutes?|h|hours?|d|days?|w|weeks?)\s*$", re.I)
ISO = re.compile(r"^P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?$", re.I)


def minutes(value) -> float | None:
    """Time in minutes: a number (minutes), „7 days”, „1w”, „P7D”; None when unreadable."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    s = str(value).strip().strip("'\"")
    if re.fullmatch(r"\d+", s):
        return float(s)
    m = DUR.match(s)
    if m:
        n, u = float(m.group(1)), m.group(2).lower()
        return n * (1 if u.startswith("m") else 60 if u.startswith("h") else 1440 if u.startswith("d") else 10080)
    m = ISO.match(s)
    if m and any(m.groups()):
        w, d, h, mi = (int(x or 0) for x in m.groups())
        return w * 10080 + d * 1440 + h * 60 + mi
    return None


def kv(text: str, key: str, sep: str) -> str | None:
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*{sep}\s*(.+?)\s*$", text)
    return m.group(1).split(" #")[0].strip() if m else None


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def write_keeping_eol(path: Path, text: str) -> None:
    """A project config file in the line ending it already has (LF by default): a text-mode write on Windows would turn
    it into CRLF, and the project's lint (endOfLine: lf) would fail on it."""
    try:
        crlf = b"\r\n" in path.read_bytes()
    except OSError:
        crlf = False
    path.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))


def _set_line(path: Path, key: str, sep: str, value: str, allow=None) -> bool:
    """Set `key<sep>value` in a line-based config file (.npmrc, YAML top level); keep the rest. True when changed."""
    if allow is not None and not allow(path):
        return False
    text = read(path)
    line = f"{key}{sep}{value}" if sep == "=" else f"{key}: {value}"
    pat = re.compile(rf"(?m)^\s*{re.escape(key)}\s*{re.escape(sep)}.*$")
    new = pat.sub(line, text, count=1) if pat.search(text) else (text + ("" if not text or text.endswith("\n") else "\n")
                                                                  + line + "\n")
    if new == text:
        return False
    write_keeping_eol(path, new)
    return True


def _set_uv(path: Path, value: str, allow=None) -> bool:
    """exclude-newer in [tool.uv] of pyproject.toml (the section is added when missing)."""
    if allow is not None and not allow(path):
        return False
    text = read(path)
    line = f'exclude-newer = "{value}"'
    sec = re.search(r"(?m)^\[tool\.uv\]\s*$", text)
    if sec:
        end = re.search(r"(?m)^\[", text[sec.end():])
        body_end = sec.end() + (end.start() if end else len(text) - sec.end())
        body = text[sec.end():body_end]
        if re.search(r"(?m)^\s*exclude-newer\s*=", body):
            nbody = re.sub(r"(?m)^\s*exclude-newer\s*=.*$", line, body, count=1)
        else:
            nbody = "\n" + line + body if not body.startswith("\n") else "\n" + line + body
        new = text[:sec.end()] + nbody + text[body_end:]
    else:
        new = text + ("" if not text or text.endswith("\n") else "\n") + f"\n[tool.uv]\n{line}\n"
    if new == text:
        return False
    write_keeping_eol(path, new)
    return True


def fix_cooldown(root: Path, allow=None) -> list[str]:
    """Write the missing or too short cooldown settings; the names of the files changed. `allow(path)` may refuse a
    file (a private install writes only new, untracked files)."""
    changed = []
    need_min = COOLDOWN_DAYS * 1440
    if (root / "package-lock.json").is_file() or (root / "npm-shrinkwrap.json").is_file():
        val = kv(read(root / ".npmrc"), "min-release-age", "=")
        if not (val and re.fullmatch(r"\d+(\.\d+)?", val) and float(val) >= COOLDOWN_DAYS):
            if _set_line(root / ".npmrc", "min-release-age", "=", str(COOLDOWN_DAYS), allow):
                changed.append(".npmrc (npm min-release-age)")
    if (root / "pnpm-lock.yaml").is_file() or (root / "pnpm-workspace.yaml").is_file():
        val = kv(read(root / "pnpm-workspace.yaml"), "minimumReleaseAge", ":") or kv(read(root / ".npmrc"), "minimum-release-age", "=")
        if (minutes(val) if val else None) is None or minutes(val) < need_min:
            if (root / "pnpm-workspace.yaml").is_file():
                if _set_line(root / "pnpm-workspace.yaml", "minimumReleaseAge", ":", str(need_min), allow):
                    changed.append("pnpm-workspace.yaml (pnpm minimumReleaseAge)")
            elif _set_line(root / ".npmrc", "minimum-release-age", "=", str(need_min), allow):
                changed.append(".npmrc (pnpm minimum-release-age)")
    if (root / "yarn.lock").is_file():
        val = kv(read(root / ".yarnrc.yml"), "npmMinimalAgeGate", ":")
        if (minutes(val) if val else None) is None or minutes(val) < need_min:
            if _set_line(root / ".yarnrc.yml", "npmMinimalAgeGate", ":", f'"{COOLDOWN_DAYS}d"', allow):
                changed.append(".yarnrc.yml (Yarn npmMinimalAgeGate)")
    if (root / "uv.lock").is_file() and (root / "pyproject.toml").is_file():
        val = None
        try:
            import tomllib
            val = ((tomllib.loads(read(root / "pyproject.toml")).get("tool") or {}).get("uv") or {}).get("exclude-newer")
        except Exception:  # noqa: BLE001
            val = None
        absolute = bool(val) and minutes(val) is None and re.match(r"^\d{4}-\d{2}-\d{2}", str(val))
        if not absolute and ((minutes(val) if val else None) is None or minutes(val) < need_min):
            if _set_uv(root / "pyproject.toml", f"{COOLDOWN_DAYS} days", allow):
                changed.append("pyproject.toml ([tool.uv] exclude-newer)")
    return changed


def cmd_cooldown(_a) -> int:
    root = Path(git("rev-parse", "--show-toplevel", cwd=Path.cwd()).strip())
    if getattr(_a, "fix", False):
        changed = fix_cooldown(root)
        print("COOLDOWN --fix: " + ("written: " + "; ".join(changed) if changed else "nothing to write"))
    tracked = set(git("ls-files", cwd=root).splitlines())
    need, ok, problems = COOLDOWN_DAYS * 1440, [], []

    def lock(name):
        if (root / name).is_file() and name not in tracked:
            problems.append(f"{name} is not in git — the lockfile must be committed (git add {name})")

    if (root / "package-lock.json").is_file() or (root / "npm-shrinkwrap.json").is_file():
        val = kv(read(root / ".npmrc"), "min-release-age", "=")
        days = float(val) if val and re.fullmatch(r"\d+(\.\d+)?", val) else None
        if days is None or days < COOLDOWN_DAYS:
            problems.append(f"npm: min-release-age={val or 'none'} — add the line `min-release-age={COOLDOWN_DAYS}` to .npmrc "
                            "(days; npm ≥ 11.10)")
        else:
            ok.append(f"npm min-release-age={val}")
        lock("package-lock.json") if (root / "package-lock.json").is_file() else lock("npm-shrinkwrap.json")
    if (root / "pnpm-lock.yaml").is_file() or (root / "pnpm-workspace.yaml").is_file():
        val = kv(read(root / "pnpm-workspace.yaml"), "minimumReleaseAge", ":") or kv(read(root / ".npmrc"), "minimum-release-age", "=")
        mins = minutes(val) if val else None
        if mins is None or mins < need:
            problems.append(f"pnpm: minimumReleaseAge={val or 'none'} — add to pnpm-workspace.yaml "
                            f"`minimumReleaseAge: {need}` (minutes; pnpm ≥ 10.17)")
        else:
            ok.append(f"pnpm minimumReleaseAge={val}")
        lock("pnpm-lock.yaml") if (root / "pnpm-lock.yaml").is_file() else problems.append(
            "pnpm-lock.yaml is missing — generate it (pnpm install) and commit it")
    if (root / "yarn.lock").is_file():
        val = kv(read(root / ".yarnrc.yml"), "npmMinimalAgeGate", ":")
        mins = minutes(val) if val else None
        if mins is None or mins < need:
            problems.append(f"Yarn: npmMinimalAgeGate={val or 'none'} — add to .yarnrc.yml `npmMinimalAgeGate: \"7d\"` (Yarn 4)")
        else:
            ok.append(f"Yarn npmMinimalAgeGate={val}")
        lock("yarn.lock")
    if (root / "uv.lock").is_file():
        val = None
        try:
            import tomllib
            for name, path in (("pyproject.toml", ("tool", "uv", "exclude-newer")), ("uv.toml", ("exclude-newer",))):
                data = tomllib.loads(read(root / name)) if (root / name).is_file() else {}
                for k in path:
                    data = data.get(k, {}) if isinstance(data, dict) else {}
                if isinstance(data, str) and data:
                    val = data
                    break
        except Exception as e:  # noqa: BLE001 — a bad TOML also means no cooldown
            problems.append(f"uv: I cannot read the configuration ({e})")
        mins = minutes(val) if val else None
        if val and mins is None and re.match(r"^\d{4}-\d{2}-\d{2}", val):
            ok.append(f"uv exclude-newer={val} (an absolute date — a frozen state, remember to move it)")
        elif mins is None or mins < need:
            problems.append(f"uv: exclude-newer={val or 'none'} — add to pyproject.toml in [tool.uv] "
                            f'`exclude-newer = "{COOLDOWN_DAYS} days"`')
        else:
            ok.append(f"uv exclude-newer={val}")
        lock("uv.lock")
    if (root / "package.json").is_file() and not any(
            (root / n).is_file() for n in ("package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock")):
        if node_has_deps(root / "package.json"):  # the same rule as audit_jobs in the scan
            problems.append("package.json has dependencies but no lockfile — generate it (npm install) "
                            "and commit package-lock.json (N10)")
        elif not ok and not problems:
            print(f"COOLDOWN: PASS — {NO_DEPS}; there is nothing to put under a cooldown")
            return 0
    if not ok and not problems:
        print("COOLDOWN: PASS — no package manager with a lockfile was detected (npm, pnpm, Yarn, uv)")
        return 0
    print(f"COOLDOWN: {'FAIL' if problems else 'PASS'} (minimum {COOLDOWN_DAYS} days)")
    for line in ok:
        print(f"- ✓ {line}")
    for line in problems:
        print(f"- ✗ {line}")
    return 1 if problems else 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="security_scan.py", description=__doc__.splitlines()[1])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--base")
    s.add_argument("--out", default="reports/security")
    s.add_argument("--slice")
    s.add_argument("--attempt", type=int, default=1)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_scan)
    sc = sub.add_parser("scanner")
    sc.set_defaults(fn=cmd_scanner)
    v = sub.add_parser("verdict")
    v.add_argument("sarif", nargs="+")
    v.add_argument("--json", action="store_true")
    v.set_defaults(fn=cmd_verdict)
    c = sub.add_parser("cooldown")
    c.add_argument("--fix", action="store_true")
    c.set_defaults(fn=cmd_cooldown)
    a = p.parse_args(argv)
    try:
        return a.fn(a)
    except ScanError as e:
        print(f"SCAN: FAIL — {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
