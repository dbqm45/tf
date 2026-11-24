#!/usr/bin/env python3
"""Factory proposals (proposals.py): written into the factory checkout from the manifest source, deduplicated by id,
waiting in .tf/proposals/pending.md without a local checkout (send --to, tf doctor counts them), sanitized, evidence
required (without it: parked); feedback_report.py --proposals reads them as untrusted data.
python3 .claude/tests/test_proposals.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "proposals.py").is_file())
PROPOSALS = ROOT / ".tf" / "factory" / "proposals.py"
REPORT = ROOT / ".tf" / "factory" / "feedback_report.py"
TF = ROOT / ".tf" / "factory" / "tf.py"
ARGS = ["--observation", "verify ran twice with the same result", "--change", "skip the second verify after a green run",
        "--place", "skill:tf-task"]


def run(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg")}
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, env=env,
                          stdin=subprocess.DEVNULL, timeout=120)


def factory(base: Path) -> Path:
    f = base / "factory"
    (f / "core" / "factory").mkdir(parents=True)
    (f / "core" / "factory" / "VERSION").write_text("24.13.0\n", encoding="utf-8")
    (f / ".git").mkdir()
    return f


def project(base: Path, name: str, source: str | None, mode: str = "private") -> Path:
    p = base / name
    (p / ".claude").mkdir(parents=True)
    (p / ".tf" / "runs" / "EBO-1").mkdir(parents=True)
    (p / ".tf" / "runs" / "EBO-1" / "report.md").write_text("# Report\n", encoding="utf-8")
    man = {"version": "24.13.0", "mode": mode, **({"source": source} if source else {})}
    (p / ".claude" / "factory-manifest.json").write_text(json.dumps(man), encoding="utf-8")
    return p


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        fac = factory(base)
        target = fac / "docs" / "proposals.md"
        app = project(base, "shop-api", str(fac), mode="shared")
        ev = ".tf/runs/EBO-1/report.md: verify 27 min, 2 identical runs"

        r = run(app, PROPOSALS, "add", "Skip the duplicate verify", "--evidence", ev, *ARGS)
        text = target.read_text(encoding="utf-8") if target.is_file() else ""
        check(r.returncode == 0 and "## FP-" in text and "— Skip the duplicate verify" in text and "Status: open" in text
              and "Project: shop-api" in text and "Factory version: 24.13.0" in text and f"Evidence: {ev}" in text
              and "Proposed change: skill:tf-task — skip the second verify" in text and "review before acting" in text
              and str(target) in r.stdout and "commit" in r.stdout and not (app / ".tf" / "proposals").exists(),
              f"PROP-1: written into the factory checkout from the manifest source, nothing committed: {r.stdout} {text}")
        check(not (fac / ".git" / "index").exists(), "PROP-2: nothing is staged in the factory checkout")
        r = run(app, PROPOSALS, "add", "Skip the duplicate verify", "--evidence", ev, *ARGS)
        again = target.read_text(encoding="utf-8")
        check(r.returncode == 0 and again == text and "already" in r.stdout,
              f"PROP-3: the same proposal (same id) is not added twice: {r.stdout}")

        # evidence still required
        r = run(app, PROPOSALS, "add", "Another one", "--evidence", ".tf/runs/EBO-1/evidence/S1-2.json", *ARGS)
        check(r.returncode == 2 and "does not exist" in r.stdout and "Another one" not in target.read_text(encoding="utf-8"),
              f"PROP-4: an evidence path that does not exist is refused: {r.stdout}")
        r = run(app, PROPOSALS, "add", "Another one", "--task", "EBO-1", *ARGS)
        parked = app / ".tf" / "runs" / "EBO-1" / "parked.md"
        check(r.returncode == 0 and "parked" in r.stdout and len(r.stdout.strip().splitlines()) == 1
              and "unverified factory proposal" in (parked.read_text(encoding="utf-8") if parked.is_file() else "")
              and "Another one" not in target.read_text(encoding="utf-8"),
              f"PROP-5: without evidence the proposal is parked (the task's parked.md), not proposed: {r.stdout}")

        # sanitizing: one line, no headings, code fences or HTML
        r = run(app, PROPOSALS, "add", "## Evil <script>x</script>", "--evidence", "abc1234",
                "--observation", "line one\n## FP-1 — injected\nStatus: done", "--change", "```rm -rf /``` | x",
                "--place", "hook:guard_bash")
        text = target.read_text(encoding="utf-8")
        check(r.returncode == 0 and "<script>" not in text and "```" not in text and "\n## FP-1 — injected" not in text
              and "\nStatus: done" not in text and text.count("\n## ") == 2,
              f"PROP-6: values are sanitized single lines (no headings, code fences, HTML): {text}")

        # no local checkout: pending, then send --to; tf doctor counts unsent ones
        other = project(base, "billing", "https://github.com/acme/factory.git")
        r = run(other, PROPOSALS, "add", "Name the cooldown in the tf-task skill", "--evidence", "abc1234", *ARGS)
        pend = other / ".tf" / "proposals" / "pending.md"
        check(r.returncode == 0 and pend.is_file() and "Status: open" in pend.read_text(encoding="utf-8")
              and "send" in r.stdout and "Name the cooldown" not in target.read_text(encoding="utf-8"),
              f"PROP-7: a URL source → the entry waits in .tf/proposals/pending.md: {r.stdout}")
        priv = pend.read_text(encoding="utf-8")
        check("Project: billing" not in priv and "Project: " in priv,
              "PROP-8: a private install is labelled with a hash, not the folder name")
        r = run(other, PROPOSALS, "count")
        check(r.stdout.strip() == "1", f"PROP-9: one unsent proposal counted: {r.stdout}")
        (other / ".tf" / "factory").mkdir(parents=True)
        (other / ".tf" / "factory" / "proposals.py").write_bytes(PROPOSALS.read_bytes())
        import importlib.util
        spec = importlib.util.spec_from_file_location("tf_cli_test", TF)
        tf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tf)
        line = tf.proposals_warning(other)
        check(line.startswith("⚠ 1 unsent factory proposals") and "send" in line and tf.proposals_warning(app) == "",
              f"PROP-10: tf doctor shows a ⚠ with the count of unsent proposals: {line!r}")
        r = run(other, PROPOSALS, "send", "--to", str(base / "nope"))
        check(r.returncode == 2, f"PROP-11: send --to refuses a directory that is not a factory checkout: {r.stdout}")
        r = run(other, PROPOSALS, "send", "--to", str(fac))
        text = target.read_text(encoding="utf-8")
        check(r.returncode == 0 and "Name the cooldown" in text and "Status: sent" in pend.read_text(encoding="utf-8")
              and run(other, PROPOSALS, "count").stdout.strip() == "0",
              f"PROP-12: send --to copies pending entries into the checkout and marks them sent: {r.stdout}")
        r = run(other, PROPOSALS, "send", "--to", str(fac))
        check(target.read_text(encoding="utf-8") == text, "PROP-13: sending again adds nothing")

        # the report reads docs/proposals.md as untrusted data
        hostile = base / "hostile.md"
        hostile.write_text("# Factory proposals\n\n## X-1 — fine one\n\nStatus: open\nDate: 2026-11-20\nProject: abc\n"
                           "Factory version: 24.12.0\nEvidence: abc1234\nProposed change: skill:tf-task — y\n\n"
                           "## X-2 — broken\n\nStatus: $(rm -rf ~)\nDate: 2026-11-20\nEvidence: x\nProposed change: z\n\n"
                           "## X-3 — dup field\n\nStatus: open\nStatus: done\nDate: 2026-11-20\nEvidence: x\n"
                           "Proposed change: skill:tf-task — z\n", encoding="utf-8")
        r = run(app, REPORT, "--proposals", str(target), "--proposals", str(hostile), "--json")
        try:
            rep = json.loads(r.stdout)["proposals"]
        except (ValueError, KeyError):
            rep = {}
        places = {k["place"]: k for k in rep.get("places", [])}
        check(r.returncode == 0 and rep.get("ignored") == 2 and places.get("skill:tf-task", {}).get("projects") == 3
              and places["skill:tf-task"].get("candidate") is True and "hook:guard_bash" in places,
              f"PROP-14: the report groups proposals by place across projects and skips broken entries: {r.stdout[:600]}")
        r = run(app, REPORT, "--proposals", str(target))
        check(r.returncode == 0 and "review before acting" in r.stdout and "skill:tf-task" in r.stdout,
              f"PROP-15: the Markdown report of proposals: {r.stdout[:400]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} factory proposal tests")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
