#!/usr/bin/env python3
"""Project record tests: python3 tests/test_project_record.py"""
import json
import re
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir()) / ".claude" / "hooks" / "project_record.py"
TEMPLATES = SCRIPT.parent.parent / "skills" / "core-project-record" / "templates"


def run(root: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, text=True, env=env, timeout=30)


def artifact(root: Path, rel: str, **fields) -> Path:
    meta = {"artifact": "brief", "phase": "discovery", "status": "proposed", "version": "1", "author": "ewa",
            "created": "2026-09-27", "updated": "2026-09-27", "inputs": "[]"} | fields
    body = fields.pop("_body", "# Brief\n## TL;DR\nKrótko o wyniku.\n## Otwarte pytania\n- [ ] Pytanie → PO\n## Przekazanie\n- Dla: tomasz\n")
    p = root / "docs" / "project" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\n" + "\n".join(f"{k}: {v}" for k, v in meta.items() if not k.startswith("_")) + "\n---\n" + body)
    return p


WIP_TESTS = 8


def wip_tests() -> list[str]:
    """Work-in-progress checkpoint: start, session, snapshot, Stop reminder, completion."""
    fails = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        git_ok = subprocess.run(["git", "init", "-q", str(root)], capture_output=True).returncode == 0
        r = run(root, "wip", "start", "Logowanie przez Google", "--by", "ola")
        wip = root / ".tf/wip/logowanie-przez-google.md"
        if r.returncode != 0 or not wip.exists():
            fails.append(f"wip start: {r.stdout[-200:]}")
            return fails
        text = wip.read_text().replace("<!-- One concrete action the next session starts from: a file, a function, a command. -->",
                                       "Dopisać test callbacku w auth.service.spec.ts")
        wip.write_text(text)
        s = run(root, "--hook-session").stdout
        if "logowanie-przez-google" not in s or "Dopisać test callbacku" not in s:
            fails.append("the session hook does not show the work in progress and the next action")
        if run(root, "check").returncode != 0:
            fails.append("check should not treat wip/ like phase artifacts")
        if run(root, "wip", "start", "Logowanie przez Google").returncode == 0:
            fails.append("wip start should not overwrite an existing checkpoint")
        (root / "app.ts").write_text("x")
        before = wip.stat().st_mtime
        run(root, "--hook-snapshot", "koniec sesji")
        body = wip.read_text()
        if "event: session end" not in body or (git_ok and "`app.ts`" not in body) or wip.stat().st_mtime != before:
            fails.append("snapshot: missing automatic state, app.ts file or a changed modification time")
        old = before - 3600
        os.utime(wip, (old, old))
        out = run(root, "--hook-stop", stdin="{}").stdout
        if git_ok and '"block"' not in out:
            fails.append("Stop does not remind about a stale checkpoint")
        if run(root, "--hook-stop", stdin='{"stop_hook_active": true}').stdout.strip():
            fails.append("Stop must not block a second time (stop_hook_active)")
        r = run(root, "wip", "done", "logowanie-przez-google", "--by", "ola")
        if r.returncode != 0 or wip.exists() or not list((root / ".tf/wip/archive").glob("*logowanie-przez-google.md")) \
                or run(root, "--hook-stop", stdin="{}").stdout.strip():
            fails.append("wip done: the file did not reach the archive or Stop still reminds")
    return fails


RESUME_TESTS = 3
EN_TESTS = 6
EN_BODY = "# Brief\n## TL;DR\nShort result.\n## Open questions\n- [ ] Question for the PO\n## Handoff\n- For: tomasz\n"


def english_tests() -> list[str]:
    """14.x syntax in English: Handoff / Open questions sections, a Steps / Next step checkpoint, domain areas
    (Evidence, Named by the human, Candidates below the threshold); the Polish names keep working."""
    fails = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        run(root, "init")
        artifact(root, "01-discovery/brief.md", _body=EN_BODY)
        chk = run(root, "check")
        if chk.returncode != 0:
            fails.append(f"EN-1: an artifact with ## Handoff and ## Open questions passes check: {chk.stdout[-300:]}")
        artifact(root, "01-discovery/brief.md", _body=EN_BODY.replace("For: tomasz", "**For:** <persona>"))
        if run(root, "check").returncode == 0:
            fails.append("EN-2: an unfilled ## Handoff detected like the old Przekazanie")
        artifact(root, "01-discovery/brief.md", _body=EN_BODY)
        run(root, "report")
        exports = list((root / "docs/project/exports").glob("report-*.md"))
        if not exports or "Question for the PO" not in exports[0].read_text():
            fails.append("EN-3: the report collects ## Open questions")
        r = run(root, "wip", "start", "Google login", "--by", "ola")
        wip = root / ".tf/wip/google-login.md"
        if r.returncode != 0 or not wip.exists():
            fails.append(f"EN-4: wip start: {r.stdout[-200:]}")
        else:
            body = wip.read_text()
            body = re.sub(r"(?ms)^## (Kroki|Steps)\b.*?(?=^## )", "## Steps\n- [ ] 1. Callback test ← next\n\n", body)
            body = re.sub(r"(?ms)^## (Następna czynność|Next step)\b.*?(?=^## )", "## Next step\nWrite the callback test in auth.spec.ts\n\n", body)
            wip.write_text(body)
            s = run(root, "--hook-session").stdout
            if "Write the callback test" not in s:
                fails.append(f"EN-4: the session hook reads ## Next step from the checkpoint: {s[-300:]}")
        (root / "input").mkdir()
        (root / "input/a.md").write_text("The manager picks people.\nNobody knows who is free.\n")
        (root / "input/b.md").write_text("The planner books specialists.\n")
        dom = root / "docs/project/02-domain"
        (dom / "corpus.md").write_text("# Bank\n## TL;DR\nok\n## S1 — input/a.md\n"
                                       "- **E1** > \"The manager picks people.\" — L1\n"
                                       "- **E2** > \"Nobody knows who is free.\" — L2\n"
                                       "## S2 — input/b.md\n- **E3** > \"The planner books specialists.\" — L1\n")
        area = ("# Areas\n## TL;DR\nok\n## Areas\n### A1 — Assignment\n- **Evidence:** E1, E2, E3\n"
                "## Candidates below the threshold\n### A9 — Leave\n- **Evidence:** E1\n")
        (dom / "areas.md").write_text(area)
        if run(root, "evidence").returncode != 0:
            fails.append("EN-5: an area with **Evidence:** and candidates below the threshold (in English) " + run(root, "evidence").stdout[-200:])
        (dom / "areas.md").write_text(area.replace("E1, E2, E3", "E1, E2\n- **Named by the human:** yes"))
        r = run(root, "evidence")
        if r.returncode != 0 or "named by the human" not in r.stdout:
            fails.append(f"EN-6: **Named by the human:** yes gives a warning, not an error: {r.stdout[-200:]}")
    return fails


def resume_tests() -> list[str]:
    """Resume: the repo state saved in the checkpoint compared with the current one (branch, commit)."""
    fails = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)

        def g(*a: str) -> int:
            return subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                  capture_output=True).returncode

        if g("init", "-q", "-b", "main") != 0:
            return fails                                   # without git there is nothing to compare
        (root / "a.txt").write_text("1")
        g("add", "a.txt")
        g("commit", "-q", "-m", "start")
        run(root, "wip", "start", "Eksport zamówień", "--by", "ola")
        run(root, "--hook-snapshot", "koniec sesji")
        if "różni się od punktu kontrolnego" in run(root, "--hook-session").stdout:
            fails.append("resume: a drift warning although the repo state has not changed")
        (root / "a.txt").write_text("2")
        g("commit", "-q", "-am", "zmiana spoza sesji")
        s = run(root, "--hook-session").stdout
        if "differs from the checkpoint" not in s or "1 commit" not in s:
            fails.append(f"resume: no warning about a new commit since the save: {s[-300:]}")
        g("checkout", "-q", "-b", "inna")
        s = run(root, "--hook-session").stdout
        if "branch" not in s or "inna" not in s:
            fails.append(f"resume: no warning about a different branch: {s[-300:]}")
    return fails


def main() -> int:
    fails = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        if run(root, "init").returncode != 0 or not (root / "docs/project/journal.md").exists():
            fails.append("init")
        if run(root, "check").returncode != 0:
            fails.append("check of an empty record")
        artifact(root, "01-discovery/brief.md")
        if run(root, "check").returncode != 0:
            fails.append("valid brief")
        artifact(root, "03-requirements/requirements.md", artifact="requirements", phase="requirements",
                 inputs="[docs/project/01-discovery/brief.md]")
        if run(root, "check").returncode != 0:
            fails.append("requirements with valid input")
        artifact(root, "05-plan/test-plan.md", artifact="test-plan", phase="plan",
                 inputs="[docs/project/03-requirements/requirements.md]")
        chk = run(root, "check")
        if chk.returncode != 0 or "brak głównego" in chk.stdout + chk.stderr or "test-plan" not in (root / "docs/project/README.md").read_text():
            fails.append(f"test plan as a plan-phase artifact: {chk.stdout[-200:]}")
        artifact(root, "07-review/2026-09-27-retro.md", artifact="review", phase="review",
                 _body="# Retro\n## TL;DR\nWiem że zespół napewno zdąży.\n## Otwarte pytania\n## Przekazanie\n- Dla: ewa\n")
        chk = run(root, "check")
        lint = SCRIPT.parent.parent / "skills" / "txt-polish-correctness" / "scripts" / "polish_lint.py"   # pack-editorial-pl
        if chk.returncode != 0 or (lint.exists() and "language remarks" not in chk.stdout):
            fails.append(f"check: a language warning for an artifact in Polish: {chk.stdout[-300:]}")
        (root / "docs/project/07-review/2026-09-27-retro.md").unlink()
        artifact(root, "08-operations/2026-10-03-review-utrzymania.md", artifact="operations-review", phase="operations",
                 _body="# Przegląd utrzymania\n## TL;DR\nTrzy łatki wdrożone.\n## Otwarte pytania\n## Przekazanie\n- Dla: piotr\n")
        chk = run(root, "check")
        idx = (root / "docs/project/README.md").read_text() if (root / "docs/project/README.md").exists() else ""
        if chk.returncode != 0 or "Operations" not in idx:
            fails.append(f"phase 9 (operations, 08-operations/) as a record artifact: {chk.stdout[-300:]}")
        (root / "docs/project/08-operations/2026-10-03-review-utrzymania.md").unlink()
        bad = [
            ("missing TL;DR", dict(_body="# X\n## Przekazanie\n- Dla: a\n")),
            ("wrong phase vs directory", dict(phase="plan")),
            ("nonexistent input", dict(inputs="[docs/project/nie-ma.md]")),
            ("nieznany status", dict(status="done")),
            ("unfilled handoff", dict(_body="# X\n## TL;DR\nok\n## Przekazanie\n- **Dla:** <persona>\n")),
            ("superseded without superseded_by", dict(status="superseded")),
        ]
        for name, fields in bad:
            p = artifact(root, "01-discovery/brief.md", **fields)
            if run(root, "check").returncode == 0:
                fails.append(f"not detected: {name}")
        artifact(root, "01-discovery/brief.md")
        run(root, "log", "--by", "ewa", "--phase", "discovery", "Brief | gotowy")
        if "Brief \\| gotowy" not in (root / "docs/project/journal.md").read_text():
            fails.append("log with | escaping")
        readme = (root / "docs/project/README.md").read_text()
        if "Requirements" not in readme or "Krótko o wyniku" not in readme:
            fails.append("README index")
        hook = run(root, "--hook-session").stdout
        if "current phase:" not in hook:
            fails.append(f"session hook: {hook!r}")
        (root / "docs/project/README.md").unlink()
        run(root, "--hook-index", stdin=json.dumps({"tool_input": {"file_path": str(root / "docs/project/01-discovery/brief.md")}}))
        if not (root / "docs/project/README.md").exists():
            fails.append("index hook after a write")
        # task files (docs/project/changes/<KEY>/, without an artifact header) do not belong to the record: writing the plan
        # of a task does not rebuild README (the loop would leave an untracked file) and the file does not reach the index
        chg = root / "docs/project/changes/T-20261113-limit"
        chg.mkdir(parents=True)
        (chg / "plan.md").write_text("# Plan: limit dobowy\n\n- [ ] K1 — limit\n", encoding="utf-8")
        (root / "docs/project/README.md").unlink()
        run(root, "--hook-index", stdin=json.dumps({"tool_input": {"file_path": str(chg / "plan.md")}}))
        if (root / "docs/project/README.md").exists():
            fails.append("the index hook rebuilt README after a task file was written")
        run(root, "index")
        if "limit dobowy" in (root / "docs/project/README.md").read_text() or "changes/T-20261113-limit" in (root / "docs/project/README.md").read_text():
            fails.append("a task file without a header reached the record index")
        rep = run(root, "report").stdout
        exports = list((root / "docs/project/exports").glob("report-*.md"))
        if not exports or "Pytanie → PO" not in exports[0].read_text():
            fails.append(f"report: {rep!r}")
    # ── evidence ──
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        run(root, "init")
        (root / "input").mkdir()
        (root / "input/wywiad.md").write_text("Wstęp.\nKierownik sam wybiera ludzi,\nale nie wie, kto jest wolny.\nKara to 2% za tydzień.\n")
        (root / "input/notatki.md").write_text("Planista blokuje specjalistów na etapy.\nUrlop wyklucza przydział.\n")
        dom = root / "docs/project/02-domain"
        corpus = ("# Bank\n## TL;DR\nok\n## S1 — input/wywiad.md\n"
                  "- **E1** > „Kierownik sam wybiera ludzi, ale nie wie, kto jest wolny.” — L2-3\n"
                  "- **E2** > „Kara to 2% za tydzień.” — L4\n"
                  "## S2 — input/notatki.md\n"
                  "- **E3** > „Planista blokuje specjalistów na etapy.” — L1\n"
                  "- **E4** > „Urlop wyklucza przydział.” — L2 [wzmianka]\n")
        (dom / "corpus.md").write_text(corpus)
        area = "# Obszary\n## TL;DR\nok\n## Obszary\n### A1 — Przydział\n- **Dowody:** E1, E2, E3\n"
        (dom / "areas.md").write_text(area)
        if run(root, "evidence").returncode != 0:
            fails.append("evidence: a valid bank and area " + run(root, "evidence").stdout[-200:])
        (dom / "corpus.md").write_text(corpus + "- **E5** > „Zmyślony cytat o fakturach.” — L9\n")
        if run(root, "evidence").returncode == 0:
            fails.append("evidence: a fabricated quote was not detected")
        (dom / "corpus.md").write_text(corpus)
        (dom / "areas.md").write_text(area.replace("E1, E2, E3", "E1, E2, E4"))
        if run(root, "evidence").returncode == 0:
            fails.append("evidence: an area below the threshold (a mention and one source) was not detected")
        (dom / "corpus.md").write_text(corpus.replace("[wzmianka]", "[mention]"))
        if run(root, "evidence").returncode == 0:
            fails.append("evidence: the [mention] tag (14.x) does not count toward the threshold like the old [wzmianka]")
        (dom / "corpus.md").write_text(corpus)
        (dom / "areas.md").write_text(area.replace("E1, E2, E3", "E1, E3") + "- **Wskazany przez człowieka:** tak\n")
        r = run(root, "evidence")
        if r.returncode != 0 or "named by the human" not in r.stdout:
            fails.append("evidence: an area named by the human should give a warning, not an error")
    fails += english_tests()
    with tempfile.TemporaryDirectory() as d:
        if run(Path(d), "--hook-session").stdout.strip():
            fails.append("the session hook should be silent without docs/project")
    fails += wip_tests()
    fails += resume_tests()
    total = 18 + WIP_TESTS + RESUME_TESTS + EN_TESTS + len(bad)
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} project record tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
