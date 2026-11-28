#!/usr/bin/env python3
"""Tests of input recognition for the /tf-task command (the tf skill, scripts/intake.py): input kind, key, tracker
from a URL or from the operations card, a cut from a change plan, resume, options.
python3 .claude/tests/test_intake.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "tf" / "scripts" / "intake.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills" / "tf").is_dir()), None)
SCRIPT = (ROOT / REL) if ROOT else REL
CHANGES = Path("docs") / "project" / "changes"
CARD = Path(".tf") / "config" / "operations.json"

PLAN = """---
artifact: plan
change: {change}
tasks: [{tasks}]
---
# Plan zmiany {change}

| Slice | Release | Flag | Value | Files | Verification |
|---|---|---|---|---|---|
{rows}
"""


def run(project: Path, *args: str):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=project, capture_output=True, text=True,
                          timeout=60, env=env)


def resolve(project: Path, *words: str) -> tuple[int, dict, str]:
    r = run(project, "resolve", "--json", *words)
    try:
        return r.returncode, json.loads(r.stdout), r.stdout + r.stderr
    except ValueError:
        return r.returncode, {}, r.stdout + r.stderr


def snapshot(project: Path) -> dict:
    return {p.relative_to(project).as_posix(): p.read_bytes() for p in sorted(project.rglob("*")) if p.is_file()}


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if not SCRIPT.is_file():
        print(f"✗ missing script {REL}")
        return 1

    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        for change, tasks in (("CHG-12", ("TSK-57", "TSK-58")), ("CHG-13", ("TSK-58",))):
            d = p / CHANGES / change
            d.mkdir(parents=True)
            rows = "\n".join(f"| {k} | R1 | — | wartość {k} | src/a.ts | `npm test` |" for k in tasks)
            (d / "plan.md").write_text(PLAN.format(change=change, tasks=", ".join(tasks), rows=rows), encoding="utf-8")
        for key, stage in (("PROJ-7", "implementation"), ("PROJ-8", "closed")):
            d = p / CHANGES / key
            d.mkdir(parents=True)
            (d / "task.json").write_text(json.dumps({"key": key, "title": f"Zadanie {key}", "stage": stage}),
                                         encoding="utf-8")
        (p / "docs" / "story.md").write_text("# Eksport\n\nJako operator chcę eksport.\n", encoding="utf-8")
        (p / CARD).parent.mkdir(parents=True)
        (p / CARD).write_text(json.dumps({"flags": {"file": "config/flags.json", "envs": ["test", "prod"],
                                                    "test_env": "test"}}), encoding="utf-8")

        # a ticket by key: unknown tracker → a question, and the paste route is always given
        before = snapshot(p)
        code, out, raw = resolve(p, "EBO-1236")
        check(code == 0 and out.get("kind") == "issue" and out.get("key") == "EBO-1236"
              and out.get("tracker") is None and out.get("ask") == "tracker" and "paste" in out.get("next", "").lower(),
              f"I-1: a key without a tracker in the card → a ticket, a tracker question, the paste route: {raw}")
        check(snapshot(p) == before, "I-2: resolve writes nothing (the card and project files unchanged)")
        code, out, raw = resolve(p, "ebo-1236")
        check(out.get("kind") == "issue" and out.get("key") == "EBO-1236", f"I-3: a lowercase key: {raw}")

        # a tracker remembered in the card is not asked about again; the card keeps the flags section
        r = run(p, "tracker", "jira", "--prefix", "EBO")
        card = json.loads((p / CARD).read_text(encoding="utf-8"))
        check(r.returncode == 0 and card.get("tracker", {}).get("prefixes") == {"EBO": "jira"}
              and card.get("flags", {}).get("test_env") == "test",
              f"I-4: tracker <type> --prefix writes the card and leaves the flags alone: {r.stdout}{r.stderr} {card}")
        code, out, raw = resolve(p, "EBO-1236")
        check(out.get("tracker") == "jira" and out.get("tracker_from") == "card" and out.get("ask") is None
              and "EBO-1236" in out.get("next", "") and "--key EBO-1236" in out.get("next", ""),
              f"I-5: the tracker from the card → no question, the next step with the key: {raw}")
        code, out, raw = resolve(p, "ENG-5")
        check(out.get("tracker") is None and out.get("ask") == "tracker", f"I-6: another prefix is still unknown: {raw}")
        r = run(p, "tracker", "linear")
        code, out, raw = resolve(p, "ENG-5")
        code2, out2, _ = resolve(p, "EBO-1")
        check(r.returncode == 0 and out.get("tracker") == "linear" and out2.get("tracker") == "jira",
              f"I-7: a default tracker for the remaining prefixes, the prefix wins: {raw}")
        r = run(p, "tracker")
        check(r.returncode == 0 and "linear" in r.stdout and "EBO" in r.stdout and "jira" in r.stdout,
              f"I-8: tracker without arguments shows the setting: {r.stdout}")
        r = run(p, "tracker", "Jira Cloud!")
        check(r.returncode == 2, f"I-9: a tracker name outside the pattern → code 2: {r.returncode} {r.stdout}")


        # ticket URL: tracker and key from the URL, the URL as the source
        for url, tracker, key in (
                ("https://acme.atlassian.net/browse/EBO-1236", "jira", "EBO-1236"),
                ("https://jira.acme.example/browse/OPS-9?focusedId=1", "jira", "OPS-9"),
                ("https://linear.app/acme/issue/ENG-42/add-csv-export", "linear", "ENG-42"),
                ("https://github.com/acme/app/issues/17", "github", "GH-17"),
                ("https://gitlab.com/acme/app/-/issues/9", "gitlab", "GL-9")):
            code, out, raw = resolve(p, url)
            check(out.get("kind") == "issue" and out.get("tracker") == tracker and out.get("key") == key
                  and out.get("source") == url and out.get("tracker_from") == "address" and out.get("ask") is None,
                  f"I-10: URL {url} → {tracker} {key}: {raw}")
        code, out, raw = resolve(p, "https://tracker.example.com/t/ABC-5")
        check(out.get("kind") == "issue" and out.get("key") == "ABC-5" and out.get("tracker") == "linear"
              and out.get("tracker_from") == "card",
              f"I-11: an unknown host with a key in the URL → the key, the tracker from the card: {raw}")
        code, out, raw = resolve(p, "https://tracker.example.com/tickets/5512")
        check(out.get("kind") == "issue" and out.get("key") is None and out.get("ask") == "content"
              and "paste" in out.get("next", "").lower(),
              f"I-12: a URL without a recognised key → a request to paste the content: {raw}")

        # a cut from a change plan
        code, out, raw = resolve(p, "TSK-57")
        check(out.get("kind") == "cut" and out.get("key") == "TSK-57" and out.get("changes") == ["CHG-12"]
              and out.get("ask") is None and "start --task TSK-57 --change CHG-12" in out.get("next", "")
              and ".claude/skills/tf-task/references/pdi-cuts.md" in out.get("next", ""),
              f"I-13: a key from the tasks heading → a cut: first the cut rules (references), then a ready command: {raw}")
        code, out, raw = resolve(p, "TSK-58")
        check(out.get("kind") == "cut" and out.get("changes") == ["CHG-12", "CHG-13"] and out.get("ask") == "change",
              f"I-14: a key in two plans → a question about the change: {raw}")
        code, out, raw = resolve(p, "TSK-58", "--change", "CHG-13", "--auto", "--budget", "3")
        check(out.get("changes") == ["CHG-13"] and out.get("ask") is None
              and out.get("options") == {"auto": True, "plan": False, "design": False, "refresh": False, "budget": 3.0, "change": "CHG-13"},
              f"I-15: --change selects the change; options cut off and returned: {raw}")
        r = run(p, "resolve", "TSK-99", "--change", "CHG-12")
        check(r.returncode == 2 and "TSK-99" in r.stdout and "CHG-12" in r.stdout,
              f"I-16: a key outside the plan of the given change → code 2: {r.returncode} {r.stdout}")

        # resume, file, content
        code, out, raw = resolve(p, "PROJ-7")
        check(out.get("kind") == "resume" and out.get("stage") == "implementation" and "PROJ-7" in out.get("next", ""),
              f"I-17: the key of an existing task → resume with the stage: {raw}")
        check(out.get("story") is None and "Story:" not in run(p, "resolve", "PROJ-7").stdout,
              f"I-17b: a task without ticket.md → no cached story claimed: {raw}")
        (p / CHANGES / "PROJ-7" / "ticket.md").write_text("# Zadanie PROJ-7\n\nSource: jira PROJ-7\n\nAC1.\n", encoding="utf-8")
        code, out, raw = resolve(p, "PROJ-7")
        plain = run(p, "resolve", "PROJ-7").stdout
        check(out.get("story") == "docs/project/changes/PROJ-7/ticket.md" and "do not read the tracker again" in out.get("next", "")
              and "Story: cached docs/project/changes/PROJ-7/ticket.md" in plain,
              f"I-17c: a re-run reads the cached story (ticket.md), not the tracker: {raw} {plain}")
        code, out, raw = resolve(p, "PROJ-7", "--refresh")
        check(out.get("options", {}).get("refresh") is True and "read it from the tracker (read-only)" in out.get("next", "")
              and "do not read the tracker again" not in out.get("next", ""),
              f"I-17d: --refresh reads the issue again (read-only) and replaces the content in ticket.md: {raw}")
        (p / CHANGES / "PROJ-7" / "task.json").write_text(json.dumps(
            {"key": "PROJ-7", "title": "Zadanie PROJ-7", "stage": "plan", "mode": "plan"}), encoding="utf-8")
        code, out, raw = resolve(p, "PROJ-7", "--auto")
        check(out.get("kind") == "resume" and "run_state.py mode .tf/runs/PROJ-7 auto" in out.get("next", ""),
              f"I-17a: resuming a task from Plan mode — the next step sets the mode from the command: {raw}")
        code, out, raw = resolve(p, "docs/story.md")
        check(out.get("kind") == "file" and out.get("file") == "docs/story.md"
              and "--story-file docs/story.md" in out.get("next", ""), f"I-18: the path of an existing file: {raw}")
        code, out, raw = resolve(p, "PROJ-12: Eksport sesji do CSV\nJako operator chcę pobrać sesje.")
        check(out.get("kind") == "content" and out.get("key") == "PROJ-12" and out.get("title") == "Eksport sesji do CSV"
              and "--key PROJ-12" in out.get("next", ""), f"I-19: key and content → content with the key and title: {raw}")
        code, out, raw = resolve(p, "dodaj", "eksport", "sesji", "do", "CSV")
        check(out.get("kind") == "content" and out.get("key") is None and out.get("title") == "dodaj eksport sesji do CSV"
              and out.get("intent") is None, f"I-20: a plain sentence → content without a key: {raw}")

        code, out, raw = resolve(p, "X-ray")
        check(out.get("kind") == "content" and out.get("key") is None and out.get("title") == "X-ray",
              f"I-20a: a single hyphenated word that is neither a task nor a ticket number → content without a key: {raw}")
        code, out, raw = resolve(p, "PROJ-7", "dokończ", "eksport")
        check(out.get("kind") == "resume" and out.get("text") == "dokończ eksport",
              f"I-20b: the key of an existing task with an addendum → resume, the addendum kept: {raw}")

        # no input: tasks in progress to resume (closed ones skipped)
        code, out, raw = resolve(p)
        keys = [x.get("key") for x in out.get("tasks", [])]
        check(out.get("kind") == "none" and keys == ["PROJ-7"], f"I-21: no input → a list of tasks in progress: {raw}")

        # a word forcing the way of working
        code, out, raw = resolve(p, "question", "jak", "działa", "logowanie?")
        check(out.get("intent") == "question" and out.get("kind") == "content" and out.get("title") == "jak działa logowanie?",
              f"I-22: “pytanie …” → a forced answer without the loop: {raw}")
        code, out, raw = resolve(p, "szybko", "popraw", "literówkę", "w", "README")
        check(out.get("intent") == "quick" and "without" in out.get("next", "").lower(), f"I-23: “szybko …”: {raw}")
        for word, want in (("pytanie", "question"), ("szybko", "quick"), ("zadanie", "task"), ("quick", "quick")):   # both languages
            code, out, raw = resolve(p, word, "popraw", "literówkę", "w", "README")
            check(out.get("intent") == want, f"I-23b: “{word} …” recognised as {want}: {raw}")
        code, out, raw = resolve(p, "zadanie", "EBO-1236")
        check(out.get("intent") == "task" and out.get("kind") == "issue" and out.get("key") == "EBO-1236",
              f"I-24: “zadanie <key>”: {raw}")
        code, out, raw = resolve(p, "--design", "mechanizm", "uprawnień")   # a design session with the developer
        nxt = out.get("next", "")
        check(out.get("intent") == "design" and out.get("options", {}).get("design") and "tf-design" in nxt
              and "run_report.py start" not in nxt and out.get("text") == "mechanizm uprawnień",
              f"I-25: “--design …” → a design session, no task created: {raw}")
        for word in ("Projekt", "design"):   # a sentence starting with these words stays a task (no forcing word)
            code, out, raw = resolve(p, word, "ma", "błąd", "w", "logowaniu")
            check(out.get("intent") is None and "tf-design" not in out.get("next", ""),
                  f"I-25b: “{word} ma błąd…” → an ordinary task, not a design session: {raw}")
        code, out, raw = resolve(p)
        check("tf-design" in out.get("next", ""), f"I-26: no input → the design session among the options: {raw}")

        # several issue keys → a batch: one task after another (/tf-task EBO-1 EBO-2 EBO-3)
        code, out, raw = resolve(p, "EBO-11", "EBO-22", "--auto", "EBO-33")
        nxt = out.get("next", "")
        check(code == 0 and out.get("kind") == "batch" and out.get("keys") == ["EBO-11", "EBO-22", "EBO-33"]
              and out.get("options", {}).get("auto") and nxt.find("EBO-11") < nxt.find("EBO-22") < nxt.find("EBO-33")
              and "one PR" in nxt, f"I-27: several keys → a batch in the given order, the options kept: {raw}")
        code, out, raw = resolve(p, "EBO-11", "dokończ", "eksport")
        check(out.get("kind") != "batch", f"I-27b: one key and text is not a batch: {raw}")
        r = run(p, "resolve", "EBO-11", "EBO-22")
        check(r.returncode == 0 and "Input: batch" in r.stdout and "Keys: EBO-11, EBO-22" in r.stdout,
              f"I-27c: text output of a batch: {r.stdout}")
        code, out, raw = resolve(p, "EBO-11,", "EBO-22,", "EBO-33")
        check(out.get("kind") == "batch" and out.get("keys") == ["EBO-11", "EBO-22", "EBO-33"],
              f"I-27d: keys separated with commas are a batch too: {raw}")

        # output for a human and invocation errors
        r = run(p, "resolve", "EBO-1236")
        check(r.returncode == 0 and all(s in r.stdout for s in ("Input: issue", "Key: EBO-1236",
                                                                "Tracker: jira", "Next: ")),
              f"I-25: text output with fixed fields: {r.stdout}")
        r = run(p, "nieznane")
        check(r.returncode == 2 and "Traceback" not in r.stderr, f"I-26: an unknown command → code 2: {r.returncode} {r.stderr[-200:]}")
        (p / CARD).write_text("{nie json", encoding="utf-8")
        code, out, raw = resolve(p, "EBO-1236")
        check(code == 0 and out.get("tracker") is None and "Traceback" not in raw,
              f"I-27: a corrupt card does not crash the script: {raw}")

    # I-org: the organisation's default tracker from the company overlay (org_defaults.operations.tracker); the project card wins
    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        f = p / ".tf" / "factory" / "packs" / "pack-firma" / "pack.yaml"
        f.parent.mkdir(parents=True)
        f.write_text("id: pack-firma\nversion: 0.1.0\ntitle: Firma\norg_defaults:\n  operations:\n    tracker:\n"
                     "      type: linear\n      prefixes: {ACME: jira}\n", encoding="utf-8")
        code, out, raw = resolve(p, "ACME-3")
        check(out.get("tracker") == "jira" and out.get("tracker_from") == "organisation" and out.get("ask") is None,
              f"I-org-1: a prefix from the company overlay → no question, the source “organisation”: {raw}")
        code, out, raw = resolve(p, "OPS-1")
        check(out.get("tracker") == "linear", f"I-org-2: the organisation's default tracker type: {raw}")
        (p / CARD).parent.mkdir(parents=True, exist_ok=True)
        (p / CARD).write_text(json.dumps({"tracker": {"prefixes": {"ACME": "github"}}}), encoding="utf-8")
        code, out, raw = resolve(p, "ACME-3")
        check(out.get("tracker") == "github" and out.get("tracker_from") == "card",
              f"I-org-3: the project card overrides the organisation: {raw}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} /tf input recognition tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
