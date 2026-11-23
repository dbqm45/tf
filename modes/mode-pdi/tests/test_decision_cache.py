#!/usr/bin/env python3
"""Tests of decision_cache.py: a read-only local copy of the suite decision index (D8), with a fake pdi-records."""
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

REL_WORK = Path(".claude") / "hooks" / "decision_cache.py"
REL_SRC = Path("modes") / "mode-pdi" / "hooks" / "decision_cache.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / REL_WORK).is_file() or (p / REL_SRC).is_file()), None)
HOOK = (ROOT / REL_WORK) if ROOT and (ROOT / REL_WORK).is_file() else ((ROOT / REL_SRC) if ROOT else None)

FAKE = textwrap.dedent('''
    """Fake `pdi-records changes`: answers from INDEX like pdi D7 (cursor <changed_at>/<id>, pages, complete)."""
    import json, os, sys
    args = sys.argv[1:]
    with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as f:
        f.write(json.dumps(args) + "\\n")
    if os.environ.get("FAKE_FAIL"):
        sys.exit(3)
    assert args[0] == "changes", args
    since = args[args.index("--since") + 1] if "--since" in args else None
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 200
    rows = json.load(open(os.environ["FAKE_INDEX"], encoding="utf-8"))
    key = lambda d: (d["changed_at"], int(d["id"].split("-")[1]))
    rows.sort(key=key)
    if since:
        at, _, ident = since.partition("/")
        rows = [d for d in rows if key(d) > (at, int(ident.split("-")[1]))]
    page = rows[:limit]
    nxt = f"{page[-1]['changed_at']}/{page[-1]['id']}" if page else since
    print(json.dumps({"decisions": page, "next": nxt, "complete": len(rows) <= limit}))
''')


def record(ident: str, statement: str, changed_at: str, status: str = "recorded", origin: dict | None = None,
           why: str = "Bo tak ustalono.", superseded_by: str | None = None) -> dict:
    head = {"record": "decision", "schema": "https://github.com/dbqm45/pdi/contract/decision.schema.json",
            "contract_version": "0.17.0", "id": ident, "statement": statement, "why": why,
            "decided_at": changed_at[:10], "decided_by": "po", "kind": "product", "status": status,
            "drafted_by": "human", "source": {"kind": "manual"}}
    if origin:
        head["origin"] = origin
    if superseded_by:
        head["superseded_by"] = superseded_by
    text = "---\n" + "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in head.items())
    text += f"\n---\n\n# {ident}: {statement}\n"
    return {**head, "changed_at": changed_at, "text": text}


def run(project: Path, env: dict, args: tuple = ()) -> subprocess.CompletedProcess:
    stdin = "" if args else json.dumps({"hook_event_name": "SessionStart", "session_id": "s-1", "cwd": str(project)})
    full = {"PATH": os.environ.get("PATH", ""), "HOME": str(project), "CLAUDE_PROJECT_DIR": str(project), **env}
    if not (HOOK.parent / "hook_errors.py").is_file():
        full["PYTHONPATH"] = str(ROOT / "core" / "hooks")   # source tree: the core hooks live apart from the mode's
    return subprocess.run([sys.executable, str(HOOK), *args], input=stdin, capture_output=True, text=True, env=full,
                          cwd=project, timeout=60)


def main() -> int:
    if HOOK is None:
        print("✗ nie znaleziono decision_cache.py")
        return 1
    fails: list[str] = []
    total = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "sklep"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        subprocess.run(["git", "-C", str(project), "remote", "add", "origin", "https://github.com/dbqm45/sklep.git"],
                       check=True)
        (base / "fake.py").write_text(FAKE, encoding="utf-8")
        index, log = base / "index.json", base / "calls.jsonl"
        rows = [
            record("DEC-0001", "Próg darmowej dostawy 199 zł", "2026-11-20T09:00:00Z"),
            record("DEC-0002", "Kolejka zdarzeń na Postgresie", "2026-11-21T09:00:00Z",
                   origin={"app": "tf", "scope": "dbqm45/sklep", "local_id": "D-001"}),   # this repo's own: skipped
            record("DEC-0003", "Pytanie o format daty zamknięte", "2026-11-22T09:00:00Z",
                   origin={"app": "ci_for_sdlc", "scope": "acme", "local_id": "PAY-12/COV-1"}),
        ]
        index.write_text(json.dumps(rows), encoding="utf-8")
        on = {"TF_DECISION_CACHE_CMD": f"{sys.executable} {base / 'fake.py'}", "FAKE_INDEX": str(index),
              "FAKE_LOG": str(log)}
        cache = project / ".tf" / "cache" / "suite-decisions"

        # C-1: off without configuration, or with TF_DECISION_CACHE=0
        r1 = run(project, {"FAKE_LOG": str(log)})
        r2 = run(project, {**on, "TF_DECISION_CACHE": "0"})
        check(r1.returncode == 0 and r2.returncode == 0 and not log.exists() and not cache.exists(), "C-1: off")

        # C-2: first refresh — files from pdi, marked as a copy, read-only, without this repo's own decisions
        r = run(project, on)
        check(r.returncode == 0, f"C-2: exit {r.returncode} {r.stderr}")
        files = sorted(p.name for p in cache.glob("DEC-*.md"))
        check(files == ["DEC-0001.md", "DEC-0003.md"], f"C-2: files {files}")
        one = cache / "DEC-0001.md"
        text = one.read_text(encoding="utf-8") if one.exists() else ""
        check(text.startswith("---\nrecord: \"decision\"") and "kopia z indeksu suity, nie edytuj" in text,
              f"C-2: copy marker {text[:160]}")
        check(one.exists() and not (one.stat().st_mode & stat.S_IWUSR), "C-2: read-only")
        meta = json.loads((cache / "meta.json").read_text(encoding="utf-8"))
        check(meta.get("next") == "2026-11-22T09:00:00Z/DEC-0003" and meta.get("fetched_at"), f"C-2: meta {meta}")
        check("2 obowiązujące" in r.stdout and "decision_cache.py search" in r.stdout, f"C-2: context line {r.stdout}")

        # C-3: the next refresh asks only for what changed; a supersession replaces the status in the copy
        rows[0] = record("DEC-0001", "Próg darmowej dostawy 199 zł", "2026-11-23T09:00:00Z", status="superseded",
                         superseded_by="DEC-0004")
        rows.append(record("DEC-0004", "Próg darmowej dostawy 149 zł", "2026-11-23T09:00:00Z"))
        index.write_text(json.dumps(rows), encoding="utf-8")
        log.unlink()
        r = run(project, on)
        calls = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
        check(calls and calls[0][:3] == ["changes", "--since", "2026-11-22T09:00:00Z/DEC-0003"], f"C-3: since {calls}")
        check("status: \"superseded\"" in (cache / "DEC-0001.md").read_text(encoding="utf-8")
              and (cache / "DEC-0004.md").exists(), "C-3: superseded and new decision in the copy")
        check("2 obowiązujące" in r.stdout and "1 zastąpion" in r.stdout, f"C-3: counts {r.stdout}")

        # C-4: pages until complete
        many = [record(f"DEC-{n:04d}", f"Decyzja {n}", "2026-11-23T10:00:00Z") for n in range(10, 15)]
        index.write_text(json.dumps(rows + many), encoding="utf-8")
        log.unlink()
        run(project, {**on, "TF_DECISION_CACHE_PAGE": "2"})
        calls = log.read_text(encoding="utf-8").splitlines()
        check(len(calls) == 3 and all((cache / f"DEC-{n:04d}.md").exists() for n in range(10, 15)),
              f"C-4: three pages {calls}")

        # C-5: pdi unavailable — the last copy stays, the context line says it is stale, the session goes on
        r = run(project, {**on, "FAKE_FAIL": "1"})
        check(r.returncode == 0 and (cache / "DEC-0004.md").exists() and "nieaktualna" in r.stdout, f"C-5: {r.stdout}")

        # C-6: a copy edited by hand is detected and fetched again from pdi
        target = cache / "DEC-0003.md"
        target.chmod(0o644)
        target.write_text(target.read_text(encoding="utf-8").replace("zamknięte", "ZMIENIONE"), encoding="utf-8")
        log.unlink()
        run(project, on)
        calls = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
        check(calls and "--since" not in calls[0], f"C-6: full refetch {calls}")
        check("ZMIENIONE" not in target.read_text(encoding="utf-8"), "C-6: restored from pdi")
        errors = project / ".tf" / "logs" / "hook-errors.jsonl"
        check(errors.is_file() and "DEC-0003" in errors.read_text(encoding="utf-8"), "C-6: the edit is logged")

        # C-7: search over the copy and the local register together, with origin, status and the copy's age
        rec = project / "docs" / "project"
        rec.mkdir(parents=True)
        (rec / "decisions.md").write_text(
            "| ID | Date | Decision | Rationale | Status | Author | Details |\n|---|---|---|---|---|---|---|\n"
            "| D-001 | 2026-11-21 | Kolejka zdarzeń na Postgresie | Jedna baza mniej | accepted | Ola | — |\n",
            encoding="utf-8")
        r = run(project, on, args=("search", "dostaw"))
        out = r.stdout
        check(r.returncode == 0 and "DEC-0004" in out and "149" in out and "DEC-0001" in out and "zastąpiona" in out,
              f"C-7: suite hits {out}")
        check("kopia z" in out, f"C-7: age of the copy shown {out}")
        r = run(project, on, args=("search", "kolejk"))
        check("D-001" in r.stdout and "lokalnie" in r.stdout, f"C-7: local hits {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów pamięci podręcznej decyzji (mode-pdi)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
