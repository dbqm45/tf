#!/usr/bin/env python3
"""Task weight tests (`tf task weight`, .tf/factory/task_weight.py): a proposal from the ticket text and plan paths,
who may change the weight, the effects of the weight in stage gates. python3 .claude/tests/test_task_weight.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
CHANGES = Path("docs") / "project" / "changes"
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given postój 12 godzin, when kierowca płaci, then opłata wynosi 45 zł.\n"
        "\n## Unchanged\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Out of scope\n\n- Abonamenty.\n")
TICKETS = {
    "LOG-1": "# Reset hasła\n\nJako użytkownik chcę zresetować hasło linkiem z maila. AC1: link ważny 30 minut.\n",
    "TYP-1": "# Literówka w README\n\nPopraw literówkę w README: „instlacja” na „instalacja”.\n",
    "REG-1": ("# Limit dobowy 45 zł\n\nJako operator parkingu chcę podnieść limit dobowy opłaty z 40 zł do 45 zł. "
              "AC1: 12 h = 45 zł. AC2: 11 h = 44 zł.\n"),
    "CSV-1": ("# Eksport sesji\n\nJako operator chcę wyeksportować sesje ładowania z wybranego dnia do CSV. "
              "Kryteria akceptacji: plik ma nagłówek i jeden wiersz na sesję.\n"),
    "ENG-1": "# Fix typo in README\n\nFix a typo in the README heading.\n",
    "ENG-2": "# Password reset\n\nAs a user I want to reset my password by email. AC: the link expires after 30 minutes.\n",
    # sensitive changes the old vocabulary judged normal (tf stress, tools/stress/corpus/weight.yaml)
    "SEN-1": "# Cookie\n\nChange the session cookie to SameSite=Strict.\n",
    "SEN-2": "# CSRF\n\nAdd CSRF protection to all POST forms.\n",
    "SEN-3": "# XSS\n\nNapraw podatność XSS w polu tytułu zadania.\n",
    "SEN-4": "# Role\n\nDodaj role admin/użytkownik: tylko admin może usuwać zadania.\n",
    "SEN-5": "# Profil\n\nStore the user's IBAN and date of birth in the profile.\n",
    "SEN-6": "# Klient\n\nPOST /api/tasks przyjmuje pola customerEmail i customerPhone. Kryteria akceptacji: GET zwraca pola.\n",
    "SEN-7": "# Webhook\n\nDodaj webhook do bramki płatniczej PayU.\n",
    "SEN-8": "# Kolumna\n\nAdd an ALTER TABLE adding NOT NULL column email_verified.\n",
    "SEN-9": "# Backup\n\nEncrypt the backups with a new KMS key.\n",
}


def tf(project: Path, *args: str):
    return subprocess.run([sys.executable, str(TASK), *args], cwd=project, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def weight(project: Path, key: str, *args: str) -> tuple[int, dict, str]:
    r = tf(project, "weight", key, *args, "--json")
    try:
        return r.returncode, json.loads(r.stdout), r.stdout + r.stderr
    except ValueError:
        return r.returncode, {}, r.stdout + r.stderr


def task(project: Path, key: str) -> dict:
    return json.loads((project / CHANGES / key / "task.json").read_text(encoding="utf-8"))


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        for key, text in TICKETS.items():
            tf(p, "start", key, "--title", text.splitlines()[0].lstrip("# "))
            (p / CHANGES / key / "ticket.md").write_text(text, encoding="utf-8")

        # a proposal from the ticket text, always with a reason; merely asking about the weight writes nothing
        before = (p / CHANGES / "LOG-1" / "task.json").read_text(encoding="utf-8")
        code, out, raw = weight(p, "LOG-1")
        check(code == 0 and out.get("proposal") == "full" and any("hasł" in r for r in out.get("reasons", []))
              and out.get("weight") == "normal" and out.get("assigned") is False,
              f"W-1: a ticket about a password → proposal full with a reason; weight not yet assigned: {raw}")
        check((p / CHANGES / "LOG-1" / "task.json").read_text(encoding="utf-8") == before,
              "W-2: tf task weight without options writes nothing")
        code, out, raw = weight(p, "TYP-1")
        check(out.get("proposal") == "light" and out.get("reasons"), f"W-3: typo → light: {raw}")
        code, out, raw = weight(p, "REG-1")
        check(out.get("proposal") == "normal", f"W-4: a new rule with criteria → normal: {raw}")
        code, out, raw = weight(p, "CSV-1")
        check(out.get("proposal") == "normal", f"W-5: “sesje ładowania” (charging sessions) is not a login — normal: {raw}")
        for key in ("SEN-1", "SEN-2", "SEN-3", "SEN-4", "SEN-5", "SEN-6", "SEN-7", "SEN-8", "SEN-9"):
            code, out, raw = weight(p, key)
            check(out.get("proposal") == "full" and out.get("reasons"), f"W-5b: {key} is a sensitive change → full: {raw}")
        code, out, raw = weight(p, "ENG-1")
        code2, out2, raw2 = weight(p, "ENG-2")
        check(out.get("proposal") == "light" and out2.get("proposal") == "full",
              f"W-6: tickets in English (typo → light, password → full): {raw} {raw2}")

        # the factory makes the first assignment; after that --apply only raises
        code, out, raw = weight(p, "TYP-1", "--apply")
        data = task(p, "TYP-1")
        check(code == 0 and data.get("weight") == "light" and data.get("weight_log")
              and data["weight_log"][-1].get("by") == "process:tf" and data["weight_log"][-1].get("reasons"),
              f"W-7: --apply assigns the proposal (even one lower than the default) and records the reason: {raw} {data.get('weight_log')}")
        (p / CHANGES / "TYP-1" / "plan.md").write_text(
            "# Plan\n- [ ] S1 — poprawka · files: README.md, db/migrations/0007_add_index.sql · verify: `make test`\n",
            encoding="utf-8")
        code, out, raw = weight(p, "TYP-1", "--apply")
        data = task(p, "TYP-1")
        check(data.get("weight") == "full" and any("db/migrations/0007_add_index.sql" in r for r in out.get("reasons", [])),
              f"W-8: the plan touches a migration → --apply raises the weight to full, the reason names the path: {raw}")
        (p / CHANGES / "TYP-1" / "plan.md").write_text("# Plan\n- [ ] S1 — poprawka · files: README.md\n", encoding="utf-8")
        code, out, raw = weight(p, "TYP-1", "--apply")
        check(code == 0 and task(p, "TYP-1").get("weight") == "full" and out.get("proposal") == "light"
              and "human:" in raw,
              f"W-9: a proposal lower than the assigned weight changes nothing; the message says who may lower it: {raw}")
        (p / CHANGES / "ENG-1" / "plan.md").write_text(
            "# Plan\n- [ ] S1 — poprawka · files: README.md, docs/a.md, docs/b.md\n", encoding="utf-8")
        code, out, raw = weight(p, "ENG-1")
        check(out.get("proposal") == "normal", f"W-10: a typo, but a plan for 3 files → normal: {raw}")
        (p / CHANGES / "ENG-1" / "plan.md").write_text(
            "# Plan\n- [ ] S1 — poprawka · files: README.md, src/a.py, src/b.py, src/c.py\n", encoding="utf-8")
        code, out, raw = weight(p, "ENG-1")
        check(out.get("proposal") == "normal", f"W-10a: a plan with 3 code files is not the fast lane → normal: {raw}")

        # the approach: the model's judgement; the script enforces only floors (no file-type rules)
        lane = ("# Search bars 280px\n\nEvery table search bar is 280px wide by default. AC1: the default width is 280px.\n")
        many = ", ".join(f"apps/x/src/app/l{i}/l{i}.component.html" for i in range(6))

        def approach(key, *args):
            return tf(p, "approach", key, *args)

        for key in ("AP-1", "AP-2", "AP-3", "AP-4"):
            tf(p, "start", key, "--title", "Search bars 280px")
            (p / CHANGES / key / "ticket.md").write_text(lane, encoding="utf-8")
        (p / CHANGES / "AP-1" / "plan.md").write_text(f"# Plan\n- [ ] S1 — 280px · files: {many}, libs/ui/search.ts\n",
                                                      encoding="utf-8")
        tf(p, "weight", "AP-1", "--apply")
        code, out, raw = weight(p, "AP-1")
        check(out.get("proposal") == "normal", f"W-AP0: the script never proposes the fast lane itself: {raw}")
        r = approach("AP-1", "--weight", "quick", "--slices", "1 (the same edit in 7 places)", "--test-strategy",
                     "one parametrized test per criterion", "--rationale", "one class in 6 templates and the shared component")
        t1 = task(p, "AP-1")
        check(r.returncode == 0 and t1.get("weight") == "quick" and t1["approach"]["test_strategy"].startswith("one param")
              and t1["weight_log"][-1]["by"] == "process:approach" and "Approach: weight quick" in r.stdout,
              f"W-AP1: a quick approach for a non-sensitive plan is accepted and recorded: {r.stdout}{r.stderr} {t1}")
        weight(p, "AP-1", "--apply")
        check(task(p, "AP-1").get("weight") == "quick", f"W-AP2: --apply keeps the approach's weight: {task(p, 'AP-1')}")
        r = approach("AP-1", "--weight", "quick")
        check(r.returncode == 2 and "rationale" in r.stdout, f"W-AP3: an approach needs a rationale: {r.stdout}")
        (p / CHANGES / "AP-2" / "plan.md").write_text(
            f"# Plan\n- [ ] S1 — 280px · files: {many}, src/auth/login.component.html\n", encoding="utf-8")
        r = approach("AP-2", "--weight", "quick", "--rationale", "small")
        check(r.returncode == 1 and "below full" in r.stdout and task(p, "AP-2").get("weight") != "quick",
              f"W-AP4: floor — a sensitive path refuses a weight below full, with the reason: {r.stdout}")
        r = approach("AP-2", "--weight", "full", "--rationale", "the login page")
        check(r.returncode == 0 and task(p, "AP-2").get("weight") == "full", f"W-AP5: full is accepted: {r.stdout}")
        (p / CHANGES / "AP-3" / "plan.md").write_text(
            "# Plan\n- [ ] S1 — a · files: " + ", ".join(f"v{i}.html" for i in range(16)) + "\n- [ ] S2 — b · files: b.css\n",
            encoding="utf-8")
        r = approach("AP-3", "--weight", "quick", "--rationale", "templates only")
        check(r.returncode == 1 and "re-assess" in r.stdout and "2 slices" in r.stdout and "17 files" in r.stdout,
              f"W-AP6: floor — a plan beyond the weight's limits is refused with re-assess: {r.stdout}")
        (p / CHANGES / "AP-4" / "plan.md").write_text("# Plan\n- [ ] S1 — a · files: a.html\n", encoding="utf-8")
        approach("AP-4", "--weight", "quick", "--rationale", "one template")
        tf(p, "stage", "AP-4", "implementation", "--force")
        r = approach("AP-4", "--weight", "full", "--rationale", "escalated: the template is also used by the login page")
        t4 = task(p, "AP-4")
        check(r.returncode == 0 and "escalated" in r.stdout and t4.get("weight") == "full"
              and t4["approach_log"][-1].get("escalated") is True and t4["approach_log"][-1].get("from") == "quick",
              f"W-AP7: a heavier weight during the loop is recorded as an escalation: {r.stdout} {t4.get('approach_log')}")
        r = approach("AP-4", "--weight", "quick", "--rationale", "smaller after all")
        check(r.returncode == 1 and "human" in r.stdout and task(p, "AP-4").get("weight") == "full",
              f"W-AP8: going back down mid-run needs the human's OK: {r.stdout}")
        r = approach("AP-4", "--weight", "quick", "--rationale", "agreed", "--by", "human:anna")
        check(r.returncode == 0 and task(p, "AP-4").get("weight") == "quick", f"W-AP9: with the human's OK: {r.stdout}")

        # manual change: anyone may raise, only a human with a reason may lower
        r = tf(p, "weight", "REG-1", "--set", "full")
        check(r.returncode == 0 and task(p, "REG-1").get("weight") == "full", f"W-11: raising without a human: {r.stdout}")
        r = tf(p, "weight", "REG-1", "--set", "normal")
        check(r.returncode == 1 and task(p, "REG-1").get("weight") == "full" and "human:" in r.stdout,
              f"W-12: lowering without a human → refusal: {r.returncode} {r.stdout}")
        r = tf(p, "weight", "REG-1", "--set", "normal", "--by", "human:anna")
        check(r.returncode == 2 and "--reason" in r.stdout, f"W-13: lowering requires a reason: {r.returncode} {r.stdout}")
        r = tf(p, "weight", "REG-1", "--set", "normal", "--by", "human:anna", "--reason", "a change only in the calculator")
        log = task(p, "REG-1").get("weight_log") or []
        check(r.returncode == 0 and task(p, "REG-1").get("weight") == "normal" and log and log[-1].get("by") == "human:anna"
              and "calculator" in log[-1].get("reason", "") and log[-1].get("from") == "full",
              f"W-14: a human lowers with a reason, recorded in the history: {r.stdout} {log[-1:]}")
        (p / CHANGES / "REG-1" / "plan.md").write_text(
            "# Plan\n- [ ] S1 — limit · files: parking/fees.py, db/migrations/0008_limit.sql\n", encoding="utf-8")
        code, out, raw = weight(p, "REG-1", "--apply")
        check(task(p, "REG-1").get("weight") == "normal" and out.get("proposal") == "full" and "human" in out.get("note", ""),
              f"W-14a: after the human's decision --apply does not change the weight, it only reports the proposal: {raw}")
        tf(p, "start", "TYP-9", "--title", "Literówka w stopce", "--weight", "full")
        (p / CHANGES / "TYP-9" / "ticket.md").write_text("# Literówka w stopce\n\nPopraw literówkę w stopce.\n", encoding="utf-8")
        code, out, raw = weight(p, "TYP-9", "--apply")
        check(task(p, "TYP-9").get("weight") == "full" and out.get("proposal") == "light",
              f"W-14b: a weight given when creating the task is not lowered by --apply: {raw}")
        r = tf(p, "weight", "REG-1", "--set", "ogromna")
        check(r.returncode == 2, f"W-15: unknown weight → code 2: {r.returncode} {r.stdout}")
        r = tf(p, "weight", "NIE-1")
        check(r.returncode != 0 and "Traceback" not in r.stderr, f"W-16: no task → an error without an exception: {r.returncode}")
        r = tf(p, "weight", "LOG-1")
        check(r.returncode == 0 and "full" in r.stdout and "hasł" in r.stdout,
              f"W-17: the text output names the proposal and the reason: {r.stdout}")

        # effect of weight full: implementation only after a human approves the plan (unattended mode cannot bypass it)
        folder = p / CHANGES / "LOG-1"
        (folder / "spec.md").write_text(SPEC, encoding="utf-8")
        (folder / "plan.md").write_text("# Plan\n- [ ] S1 — reset · files: src/reset.py\n", encoding="utf-8")
        tf(p, "weight", "LOG-1", "--apply")
        tf(p, "stage", "LOG-1", "plan")
        tf(p, "artifact", "LOG-1", "plan.md", "--stage", "plan", "--by", "process:tf", "--inputs", "spec.md")
        r = tf(p, "stage", "LOG-1", "implementation")
        check(r.returncode == 1 and "approve LOG-1 plan.md" in r.stdout and "human" in r.stdout,
              f"W-18: weight full — implementation rejected without a plan approved by a human: {r.returncode} {r.stdout}")
        tf(p, "approve", "LOG-1", "plan.md", "--by", "human:anna")
        r = tf(p, "stage", "LOG-1", "implementation")
        check(r.returncode == 0, f"W-19: after the plan is approved implementation passes: {r.stdout}")
        # ticking a slice in an approved plan does not invalidate the human's approval; changing the plan content does
        (folder / "plan.md").write_text("# Plan\n- [x] S1 — reset · files: src/reset.py\n", encoding="utf-8")
        state = json.loads(tf(p, "status", "LOG-1", "--json").stdout).get("artifact_states", {}).get("plan.md")
        r = tf(p, "stage", "LOG-1", "implementation", "--force")
        check(state == "approved", f"W-19a: a ticked slice — the plan is still approved: {state}")
        (folder / "plan.md").write_text("# Plan\n- [x] S1 — reset · files: src/reset.py\n- [ ] S2 — mail · files: src/mail.py\n",
                                        encoding="utf-8")
        state = json.loads(tf(p, "status", "LOG-1", "--json").stdout).get("artifact_states", {}).get("plan.md")
        check(state == "changed-after-approval", f"W-19b: a new slice in the plan requires approval again: {state}")
        tf(p, "artifact", "REG-1", "plan.md", "--stage", "plan", "--by", "process:tf")
        tf(p, "mode", "REG-1", "auto")
        r = tf(p, "stage", "REG-1", "implementation")
        check(r.returncode == 0, f"W-20: weight normal in Auto mode does not require plan approval: {r.stdout}")

        # effect of weight light: one slice, no spec needed
        tf(p, "start", "TYP-2", "--title", "Literówka w stopce")
        (p / CHANGES / "TYP-2" / "ticket.md").write_text("# Literówka w stopce\n\nPopraw literówkę w stopce strony.\n",
                                                         encoding="utf-8")
        tf(p, "weight", "TYP-2", "--apply")
        (p / CHANGES / "TYP-2" / "plan.md").write_text(
            "# Plan\n- [ ] S1 — stopka · files: web/footer.html\n- [ ] S2 — test · files: web/footer.test.js\n", encoding="utf-8")
        r = tf(p, "stage", "TYP-2", "plan")
        check(task(p, "TYP-2").get("weight") == "light" and r.returncode == 1 and "one slice" in r.stdout
              and "weight TYP-2 --set normal" in r.stdout,
              f"W-21: weight light with a two-slice plan → refusal with a hint: {r.returncode} {r.stdout}")
        (p / CHANGES / "TYP-2" / "plan.md").write_text("# Plan\n- [ ] S1 — stopka · files: web/footer.html\n", encoding="utf-8")
        r = tf(p, "stage", "TYP-2", "plan")
        check(r.returncode == 0 and not (p / CHANGES / "TYP-2" / "spec.md").exists(),
              f"W-22: weight light with one slice moves to plan without spec.md: {r.stdout}")
        r = tf(p, "status", "TYP-2")
        check("weight: light" in r.stdout, f"W-23: status shows the weight: {r.stdout}")

        # pdi change-cut task (step E6): the weight comes from the cut row, not from the whole change's intent attached to ticket.md
        cut_ticket = ("# TSK-59: historia prób w panelu\n\nCięcie TSK-59 zmiany CHG-12 (`docs/project/changes/CHG-12/plan.md`). "
                      "Każdy commit przebiegu ma stopki `Change: TSK-59`.\n\n| Pole | Wartość |\n|---|---|\n"
                      "| Cięcie | TSK-59 |\n| Wartość | historia prób w panelu operatora |\n| Pliki | src/history.py |\n\n"
                      "## The change's intent (`docs/project/changes/CHG-12/intent.md`)\n\n## Problem\n"
                      "Klient nie może ponowić nieudanej płatności kartą i porzuca zamówienie.\n")
        tf(p, "start", "CHG-12-TSK-59", "--title", "TSK-59: historia prób w panelu", "--change", "CHG-12", "--cut", "TSK-59")
        (p / CHANGES / "CHG-12-TSK-59" / "ticket.md").write_text(cut_ticket, encoding="utf-8")
        tf(p, "start", "HIS-1", "--title", "Historia prób w panelu")
        (p / CHANGES / "HIS-1" / "ticket.md").write_text(cut_ticket, encoding="utf-8")
        code, out, raw = weight(p, "CHG-12-TSK-59")
        code2, out2, raw2 = weight(p, "HIS-1")
        check(out.get("proposal") == "normal" and out2.get("proposal") == "full",
              f"W-24: the cut's weight does not grow from the whole change's intent; an ordinary task with the same content — full: {raw} | {raw2}")
        # W-24b: the Polish intent heading from before 14.x is no longer cut off (the 19.0.0 migration rewrites open tasks)
        (p / CHANGES / "CHG-12-TSK-59" / "ticket.md").write_text(
            cut_ticket.replace("## The change's intent", "## Zamiar zmiany"), encoding="utf-8")
        code, out, raw = weight(p, "CHG-12-TSK-59")
        check(out.get("proposal") == "full", f"W-24b: the Polish intent heading is not cut off: {raw}")
        (p / CHANGES / "CHG-12-TSK-59" / "ticket.md").write_text(cut_ticket, encoding="utf-8")
        (p / CHANGES / "CHG-12-TSK-59" / "ticket.md").write_text(cut_ticket.replace("historia prób w panelu operatora",
                                                                                   "zmiana hasła operatora"), encoding="utf-8")
        code, out, raw = weight(p, "CHG-12-TSK-59")
        check(out.get("proposal") == "full" and any("hasł" in r for r in out.get("reasons", [])),
              f"W-25: a sensitive area in the cut row raises the cut's weight to full: {raw}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} task weight tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
