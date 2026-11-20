#!/usr/bin/env python3
"""Tests of sweep_scan.py (the core-sweep skill): candidates of stale notes, plans and rules, and the archive move.
python3 .claude/tests/test_sweep_scan.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / ".claude" / "skills" / "core-sweep" / "scripts" / "sweep_scan.py").is_file())
SCRIPT = ROOT / ".claude" / "skills" / "core-sweep" / "scripts" / "sweep_scan.py"
HOOK = ROOT / ".claude" / "hooks" / "guard_paths.py"
OLD = "2024-01-15T10:00:00+00:00"


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", timeout=60, cwd=cwd)


def git(repo: Path, *args, when: str | None = None):
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.com"}
    if when:
        env.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True, encoding="utf-8")


def write(repo: Path, rel: str, text: str):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def commit(repo: Path, msg: str, when: str | None = None):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg, when=when)


def build(repo: Path):
    git(repo, "init", "-q")
    # history: an old TODO, a products page later moved to catalog, a removed function
    write(repo, "src/legacy.go", "package legacy\n// TODO rewrite the retry loop\nfunc Retry() {}\n")
    write(repo, "apps/web/products/page.tsx", "export const Page = 1\n")
    write(repo, "lib/tools.rb", "def parse_invoice_total\nend\n")
    commit(repo, "initial", when=OLD)
    git(repo, "mv", "apps/web/products", "apps/web/catalog")
    commit(repo, "refactor: rename products to catalog", when="2026-03-01T10:00:00+00:00")
    write(repo, "lib/tools.rb", "def sum_lines\nend\n")
    commit(repo, "refactor: drop parse_invoice_total", when="2026-04-01T10:00:00+00:00")
    write(repo, "src/billing.py", "def refund(amount):  # TODO(EBO-812): partial refunds\n    return amount\n"
                                  "# do not remove this check, bug X returns\n")
    write(repo, "package.json", json.dumps({"scripts": {"test": "jest", "lint": "eslint ."}}))
    write(repo, "Makefile", "build:\n\tgo build ./...\n")
    write(repo, "CLAUDE.md",
          "# Rules\n"
          "- The products page lives in `apps/web/products`.\n"
          "- Run `npm run typecheck` before a commit; tests: `npm test`, lint `npm run lint`.\n"
          "- Release with `make release`; build with `make build`.\n"
          "- Totals are computed by `parse_invoice_total` in `lib/tools.rb`.\n"
          "- Do not read `dist/` (it may not exist).\n"
          "- The new module `src/payments/` (planned).\n"
          "```\nsrc/inside_fence.py\n```\n")
    write(repo, "docs/project/changes/T-1/task.json", json.dumps({"key": "T-1", "stage": "closed"}))
    write(repo, "docs/project/changes/T-1/spec.md", "# Spec\n")
    write(repo, "docs/project/changes/T-2/task.json", json.dumps({"key": "T-2", "stage": "implementation"}))
    write(repo, "docs/project/05-plan/plan-v1.md", "---\nartifact: plan\nstatus: superseded\nversion: 1\n---\n# Plan\n")
    write(repo, "docs/project/05-plan/plan.md", "---\nartifact: plan\nstatus: accepted\nversion: 2\n---\n# Plan\n")
    write(repo, "docs/project/parked.md",
          "# Parked\n\n- 2026-05-01 handle `retryBudget` in the client\n  details on a second line\n"
          "- 2026-05-02 a vague idea without any code name\n- 2026-05-03 waiting for PROJ-9\n")
    commit(repo, "docs: notes", when="2026-05-03T10:00:00+00:00")
    write(repo, "src/client.ts", "export const retryBudget = 3\n")
    commit(repo, "feat: add retryBudget to the client", when="2026-06-01T10:00:00+00:00")


def main() -> int:
    fails, total = [], 0

    def ok(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        repo = Path(d) / "proj"
        repo.mkdir()
        build(repo)
        r = run("scan", "--root", repo, "--json")
        ok(r.returncode == 0, f"scan: code {r.returncode}: {r.stderr}")
        data = json.loads(r.stdout)
        cands = data["candidates"]
        kinds = {}
        for c in cands:
            kinds.setdefault(c["kind"], []).append(c)

        def find(kind, claim_part):
            return next((c for c in kinds.get(kind, []) if claim_part in c["claim"]), None)

        # 1. TODOs: a tracker key → todo-tracker; old by git blame → todo-old (the word "old", not "stale")
        t = find("todo-tracker", "EBO-812")
        ok(t and t["file"] == "src/billing.py" and t["line"] == 1 and t["tracker_keys"] == ["EBO-812"],
           f"todo-tracker EBO-812: {t}")
        o = find("todo-old", "retry loop")
        ok(o and o["facts"].get("age_months", 0) > 12 and "old" in o["why"] and "stale" not in o["why"].split(" — ")[0]
           .replace("not proven stale", ""), f"todo-old: {o}")
        ok("EBO-812" in data["tracker_keys"] and "PROJ-9" in data["tracker_keys"], f"tracker keys: {data['tracker_keys']}")
        ok(not find("todo-old", "do not remove"), "a plain comment without a TODO tag is not a candidate")

        # 2. a missing path with the rename from git → evidence of a conflict (rule vs code)
        p = find("missing-path", "apps/web/products")
        ok(p and p["file"] == "CLAUDE.md" and p["line"] == 2 and p["facts"].get("moved_to") == "apps/web/catalog",
           f"missing path moved: {p}")
        ok(p and "catalog" in p["facts"].get("parent_now_has", []), f"parent listing: {p}")
        # commands: a missing npm script and make target; defined ones are not candidates
        ok(find("missing-command", "npm run typecheck") is not None, f"npm run typecheck: {kinds.get('missing-command')}")
        ok(find("missing-command", "make release") is not None, "make release")
        ok(not find("missing-command", "npm run lint") and not find("missing-command", "make build")
           and not find("missing-command", "npm test"), f"defined commands: {kinds.get('missing-command')}")
        # an identifier that is in no tracked file outside the notes, with the commit that removed it
        i = find("missing-identifier", "parse_invoice_total")
        ok(i and any("drop parse_invoice_total" in h for h in i["facts"].get("last_commits_with_name", [])),
           f"missing identifier: {i}")
        ok(not find("missing-path", "lib/tools.rb"), "an existing path is not a candidate")
        ok(not find("missing-path", "dist/") and not find("missing-path", "src/payments")
           and not find("missing-path", "inside_fence"), "negative lines, planned paths and code fences are skipped")
        ok(not find("missing-identifier", "retryBudget"), "a name present in the code is not a candidate")

        # 3. records: a closed task folder, a superseded artifact, a parked entry handled later, an entry with a key
        c = find("closed-task", "T-1")
        ok(c and c["archive"] == {"type": "folder", "path": "docs/project/changes/T-1"}, f"closed task: {c}")
        ok(not find("closed-task", "T-2"), "an open task is not a candidate")
        s = next((x for x in kinds.get("superseded-artifact", []) if x["file"].endswith("plan-v1.md")), None)
        ok(s and s["archive"]["type"] == "file", f"superseded artifact: {s}")
        ok(not any(x["file"].endswith("05-plan/plan.md") for x in kinds.get("superseded-artifact", [])), "accepted plan")
        e = find("record-entry", "retryBudget")
        ok(e and any("retryBudget" in h for h in e["facts"].get("later_commits", [])) and e["archive"]["end"] == 4,
           f"parked entry handled later: {e}")
        ok(not find("record-entry", "vague idea"), "an entry without evidence is left alone")
        k = find("record-entry", "PROJ-9")
        ok(k and "PROJ-9" in k["tracker_keys"], f"entry with a tracker key: {k}")
        ids = [x["id"] for x in cands]
        ok(ids == [f"S-{n:02d}" for n in range(1, len(ids) + 1)], f"ids: {ids}")
        ok("\\" not in json.dumps([x["file"] for x in cands]), "paths with /")

        # 4. --write: the evidence JSON and the report skeleton, every candidate under "Uncertain"
        r = run("scan", "--root", repo, "--write")
        ok(r.returncode == 0, f"scan --write: {r.stdout}{r.stderr}")
        reports = sorted((repo / ".tf" / "reports").glob("sweep-*.md"))
        ok(len(reports) == 1, f"report skeleton: {reports}")
        md = reports[0].read_text(encoding="utf-8") if reports else ""
        ok(md.startswith("# Sweep report — ") and "\nScan: .tf/reports/sweep-" in md
           and f"Verdict: 0 stale · 0 conflicts · {len(cands)} uncertain" in md, f"skeleton header: {md[:300]}")

        # 5. apply: only ids in "## Stale" move; code items are by hand; the entry is cut out of parked.md
        stale_ids = [c["id"], s["id"], e["id"], t["id"]]
        lines = [ln for ln in md.splitlines() if any(ln.startswith(f"- [{x}]") for x in stale_ids)]
        md2 = md.replace("## Stale\n\n- none\n", "## Stale\n\n" + "\n".join(lines) + "\n")
        reports[0].write_text(md2, encoding="utf-8")
        r = run("apply", reports[0], "--approve", f"{i['id']}", "--root", repo)
        ok(r.returncode == 1 and "not in the report's" in r.stdout, f"apply outside Stale refused: {r.stdout}")
        ok((repo / "docs/project/changes/T-1").is_dir(), "a refused apply moves nothing")
        r = run("apply", reports[0], "--approve", ",".join(stale_ids), "--root", repo)
        ok(r.returncode == 0, f"apply: {r.returncode} {r.stdout}")
        day = data["date"]
        arch = repo / "docs/project/archive/sweep" / day
        ok(not (repo / "docs/project/changes/T-1").exists() and (arch / "docs/project/changes/T-1/spec.md").is_file(),
           "closed task folder moved")
        ok((arch / "docs/project/05-plan/plan-v1.md").is_file() and (repo / "docs/project/05-plan/plan.md").is_file(),
           "superseded artifact moved, the current one stays")
        parked = (repo / "docs/project/parked.md").read_text(encoding="utf-8")
        ok("retryBudget" not in parked and "details on a second line" not in parked and "vague idea" in parked,
           f"entry cut out: {parked}")
        ok("retryBudget" in (arch / "docs/project/parked.md").read_text(encoding="utf-8"), "entry archived")
        ok("by hand" in r.stdout and "src/billing.py" in r.stdout, f"a TODO is a by-hand edit: {r.stdout}")
        ok("chore(sweep): archive stale notes" in r.stdout, "the commit message is suggested")
        ok((repo / "docs/project/archive/sweep/.ignore").read_text(encoding="utf-8").strip() == "*", ".ignore written")
        ok("## Applied" in reports[0].read_text(encoding="utf-8"), "the report records what was applied")
        # the archive is not scanned again
        r = run("scan", "--root", repo, "--json")
        again = json.loads(r.stdout)["candidates"]
        ok(not any(x["file"].startswith("docs/project/archive/") for x in again), "the archive is not scanned")
        # a document changed since the scan is not moved
        r = run("apply", reports[0], "--approve", e["id"], "--root", repo)
        ok(r.returncode == 1, f"apply again after the change: {r.stdout}")

        # 6. the hook keeps agents out of the archive; TF_ARCHIVE_READ=1 lets a human-asked read through
        def hook(tool, ti, env=None):
            p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"tool_name": tool, "tool_input": ti,
                                                                              "cwd": str(repo)}),
                               capture_output=True, text=True, encoding="utf-8", timeout=10,
                               env={**{k: v for k, v in os.environ.items() if k != "TF_ARCHIVE_READ"}, **(env or {})})
            return json.loads(p.stdout)["hookSpecificOutput"] if p.stdout.strip() else {}
        target = str(arch / "docs/project/parked.md")
        h = hook("Read", {"file_path": target})
        ok(h.get("permissionDecision") == "deny" and "archived — not current" in h.get("permissionDecisionReason", "")
           and "TF_ARCHIVE_READ=1" in h.get("permissionDecisionReason", ""), f"hook Read: {h}")
        ok(hook("Edit", {"file_path": "docs/project/archive/sweep/x.md"}).get("permissionDecision") == "deny", "hook Edit")
        ok(hook("Grep", {"pattern": "x", "path": "docs/project/archive/sweep"}).get("permissionDecision") == "deny",
           "hook Grep into the archive")
        ok(hook("Glob", {"pattern": "docs/project/archive/sweep/**/*.md"}).get("permissionDecision") == "deny",
           "hook Glob into the archive")
        ok(hook("Grep", {"pattern": "retryBudget"}) == {}, "a repo-wide Grep is not blocked")
        ok(hook("Glob", {"pattern": "**/*.md"}) == {}, "a repo-wide Glob is not blocked")
        ok(hook("Read", {"file_path": str(repo / "docs/project/archive/research/x.md")}) == {},
           "the rest of docs/project/archive/ (research, retro) stays readable")
        ok(hook("Read", {"file_path": target}, {"TF_ARCHIVE_READ": "1"}) == {}, "TF_ARCHIVE_READ=1 lets the read through")

        # 7. ripgrep respects the archive's .ignore (the Grep tool runs ripgrep without --no-ignore)
        try:
            rg = subprocess.run(["rg", "-l", "retryBudget", "."], cwd=repo, capture_output=True, text=True,
                                encoding="utf-8", timeout=20)
            ok("archive" not in rg.stdout and "src/client.ts" in rg.stdout.replace("\\", "/"), f"rg: {rg.stdout}")
        except OSError:
            pass                                     # no ripgrep on this machine — nothing to check

        # 8. outside git: no git facts, no crash
        plain = Path(d) / "plain"
        write(plain, "AGENTS.md", "- Code lives in `src/gone/module.py`.\n")
        r = run("scan", "--root", plain, "--json")
        res = json.loads(r.stdout) if r.returncode == 0 else {}
        ok(res.get("git") is False and any(x["claim"] == "src/gone/module.py" for x in res.get("candidates", [])),
           f"no git: {r.stdout[:300]}{r.stderr}")
        ok(run("apply", plain / "nope.md", "--approve", "S-01", "--root", plain).returncode == 2, "apply without a report")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} test_sweep_scan: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
