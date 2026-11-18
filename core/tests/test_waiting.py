#!/usr/bin/env python3
"""'Waiting for you' (step F1): `tf status` and the preview say which task waits for a human, for what, what the
question is and which option is recommended; the files panel shows the slice's code files.
python3 .claude/tests/test_waiting.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
CTF = ROOT / ".tf" / "factory" / "tf.py"
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
OK = f'{sys.executable} -c "print(\'3 passed\')"'


def call(project: Path, cfg: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cfg), "CLAUDE_PROJECT_DIR": str(project), "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, env=env,
                          timeout=120)


def runs_json(html: str) -> list:
    m = re.search(r"const RUNS = (\[.*?\]);\n", html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</")) if m else []


def rows(project: Path, cfg: Path) -> dict:
    r = call(project, cfg, TASK, "list", "--json")
    try:
        return {x["key"]: x for x in json.loads(r.stdout)}
    except (ValueError, KeyError, TypeError):
        return {}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        p, cfg = Path(t) / "proj", Path(t) / "cfg"
        p.mkdir()
        (p / "fees.py").write_text("LIMIT = 45\n", encoding="utf-8")
        r = call(p, cfg, SCRIPTS / "run_report.py", "start", "Limit dobowy", "--key", "IMP-1", "--story",
                 "Jako kierowca chcę limit dobowy opłaty.")
        d = str(p / ".tf" / "runs" / "IMP-1")
        check(r.returncode == 0, f"setup: run start: {r.stdout} {r.stderr}")

        r = call(p, cfg, TASK, "list")
        check(r.returncode == 0 and "waiting for you" not in r.stdout and rows(p, cfg).get("IMP-1", {}).get("waiting") == [],
              f"Z-1: a task in progress waits for nobody: {r.stdout}")

        # the plan waits for a human's consent
        call(p, cfg, SCRIPTS / "run_state.py", "stage", d, "needs", "--needs", "plan")
        r = call(p, cfg, TASK, "list")
        w = rows(p, cfg).get("IMP-1", {}).get("waiting") or [{}]
        check("waiting for you" in r.stdout and "plan" in r.stdout and "approve IMP-1 plan.md" in r.stdout,
              f"Z-2: tf status says the plan waits for consent, and how to record it: {r.stdout}")
        check(len(w) == 1 and w[0].get("kind") == "plan" and re.match(r"\d{4}-\d{2}-\d{2}T", str(w[0].get("since"))),
              f"Z-3: list --json: one 'plan' entry with the time since it has been waiting: {w}")

        # a STOP block with a code: what happened, the reason, the question, the recommendation
        call(p, cfg, SCRIPTS / "run_state.py", "stage", d, "needs", "--needs", "stop", "--code", "tests", "--reason",
             "pytest: 2 failed (test_fees.py)")
        r = call(p, cfg, TASK, "list")
        w = rows(p, cfg).get("IMP-1", {}).get("waiting") or [{}]
        check("waiting for you" in r.stdout and "The tests fail" in r.stdout and "pytest: 2 failed" in r.stdout
              and "question:" in r.stdout and "recommended:" in r.stdout,
              f"Z-4: tf status shows the stop: what happened, the reason, the question and the recommendation: {r.stdout}")
        check(len(w) == 1 and w[0].get("kind") == "stop" and w[0].get("code") == "tests"
              and str(w[0].get("question", "")).endswith("?") and w[0].get("recommended")
              and len(w[0].get("options") or []) >= 2 and w[0].get("details") == "pytest: 2 failed (test_fees.py)",
              f"Z-5: list --json: a 'stop' entry with the code, the question, the options and the recommendation: {w}")

        # the preview: the 'Waiting for you' list from the same data
        html = (p / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8")
        card = next((x for x in runs_json(html) if x.get("key") == "IMP-1"), {})
        cw = card.get("waiting") or [{}]
        check(len(cw) == 1 and cw[0].get("kind") == "stop" and cw[0].get("question") == w[0].get("question")
              and cw[0].get("since") == w[0].get("since"),
              f"Z-6: the preview card has the same waiting list as tf status: {cw}")
        hint = card.get("stopHint") or ""
        check(".." not in hint and "attempts. pytest: 2 failed (test_fees.py). Decide" in hint and "r.stopHint" in html,
              f"Z-6a: the stop description on the card consists of whole sentences (no '..' and no run-together sentences): {hint!r}")
        check('id="waiting"' in html and "Waiting for you" in html and "r.waiting" in html and "rekomendowana" in html,
              "Z-7: the template draws a highlighted 'Waiting for you' list with the question and the recommendation")

        # after resuming nothing waits
        call(p, cfg, SCRIPTS / "run_state.py", "stage", d, "intake")
        r = call(p, cfg, TASK, "list")
        meta = json.loads((p / ".tf" / "runs" / "IMP-1" / "run.json").read_text(encoding="utf-8"))
        check("waiting for you" not in r.stdout and "needs_at" not in meta,
              f"Z-8: after the run resumes the task does not wait: {r.stdout} {meta}")

        # a slice blocked by a question also waits for a human
        call(p, cfg, TASK, "slice", "IMP-1", "K2", "blocked", "--reason", "nie wiadomo, czy limit dotyczy abonamentów")
        r = call(p, cfg, TASK, "list")
        w = rows(p, cfg).get("IMP-1", {}).get("waiting") or [{}]
        check("waiting for you" in r.stdout and "K2" in r.stdout and "abonamentów" in r.stdout
              and w[0].get("kind") == "slice" and w[0].get("slice") == "K2",
              f"Z-9: a blocked slice is on the waiting list with the reason: {r.stdout} {w}")

        # the files panel: the slice's code files from the verification evidence
        call(p, cfg, TASK, "verify", "IMP-1", "K1", "--files", "fees.py", "--command", OK)
        call(p, cfg, SCRIPTS / "run_state.py", "dashboard", "--no-cost")
        card = next((x for x in runs_json((p / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8"))
                     if x.get("key") == "IMP-1"), {})
        code = next((g for g in card.get("files", []) if g.get("grp", "").startswith("The slices' code")), {})
        item = next((i for i in code.get("items", []) if i.get("name") == "K1 · fees.py"), {})
        check("LIMIT = 45" in item.get("text", ""),
              f"Z-10: the files panel has a code group with the slice's files (from the evidence): {[g.get('grp') for g in card.get('files', [])]}")

        # tf status --open: builds the preview and prints the list (here without opening a browser)
        (p / ".tf" / "runs" / "dashboard.html").unlink()
        import shutil
        for rel in (Path(".tf") / "factory", Path(".claude") / "skills" / "tf"):     # a project with the factory installed
            shutil.copytree(ROOT / rel, p / rel, ignore=shutil.ignore_patterns("__pycache__"))
        (p / ".claude" / "factory-manifest.json").write_text(json.dumps({"version": "1.0.0"}), encoding="utf-8")
        env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cfg), "TF_DASHBOARD_OPEN": "0"}
        r = subprocess.run([sys.executable, str(CTF), "status", "--open"], cwd=p, capture_output=True, text=True,
                           env=env, timeout=120)
        check(r.returncode == 0 and (p / ".tf" / "runs" / "dashboard.html").is_file() and "IMP-1" in r.stdout,
              f"Z-11: tf status --open builds the preview and prints the tasks: {r.returncode} {r.stdout} {r.stderr}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of the 'Waiting for you' list")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
