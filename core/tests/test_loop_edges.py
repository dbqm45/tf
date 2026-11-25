#!/usr/bin/env python3
"""Edge cases of the /tf-task loop scripts and their state: `tf task verify` evidence reuse (the tree fingerprint, outside
git, untracked, binary, renamed and non-ASCII files, `--force`), `tf task start`/`approach` on odd task files (floors,
limits, Windows paths, a declared slice count), `run_state.py` on a corrupted run.json (verify, fetch, gate-related,
finish-slice), `run_report.py finish` time breakdown (bad durations, open waits, time zones, a clock going backwards),
`intake.py` keys and addresses, the scanner's changed files (non-ASCII names, a broken scanner, a decision without a
reason), plan_drift and ui_snap on non-ASCII names, and hostile proposals files.
python3 .claude/tests/test_loop_edges.py"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS_REL = Path(".claude") / "skills" / "tf" / "scripts"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / SCRIPTS_REL / "run_state.py").is_file())
SCRIPTS = ROOT / SCRIPTS_REL
STATE = SCRIPTS / "run_state.py"
REPORT = SCRIPTS / "run_report.py"
INTAKE = SCRIPTS / "intake.py"
SCAN = SCRIPTS / "security_scan.py"
DRIFT = SCRIPTS / "plan_drift.py"
TASK = ROOT / ".tf" / "factory" / "task_state.py"
PROPOSALS = ROOT / ".tf" / "factory" / "proposals.py"
HOOK = ROOT / ".claude" / "hooks" / "quality_gate.py"
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'1 passed\')"'
RED = f'{sys.executable} -c "raise SystemExit(1)"'
NO_CONNECTION = ("no tracker is connected", "not connected", "no connection", "no tracker connected", "no mcp")


def env(project: Path, **extra) -> dict:
    base = {k: v for k, v in os.environ.items() if not k.startswith(("JIRA_", "TF_SCAN_PATH"))}
    return {**base, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
            "TF_DASHBOARD_OPEN": "0", "TF_DASHBOARD_LIVE": "0", "GIT_AUTHOR_NAME": "T",
            "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.com",
            "GIT_CONFIG_GLOBAL": os.devnull, **extra}


def call(project: Path, script: Path, *args: str, **extra) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env(project, **extra), stdin=subprocess.DEVNULL,
                          timeout=180)


def git(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(project), "-c", "commit.gpgsign=false", *args], capture_output=True,
                          text=True, env=env(project), timeout=60)


def repo(p: Path) -> Path:
    p.mkdir(parents=True)
    git(p, "init", "-q", "-b", "main")
    (p / "README.md").write_text("x\n", encoding="utf-8")
    (p / ".gitignore").write_text(".tf/\n", encoding="utf-8")
    git(p, "add", "-A")
    git(p, "commit", "-q", "-m", "chore: init")
    return p


def module(path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def evidence(p: Path, key: str) -> list[str]:
    folder = p / CHANGES / key / "evidence"
    return sorted(f.name for f in folder.glob("S*.json")) if folder.is_dir() else []


def task(p: Path, key: str) -> dict:
    return json.loads((p / CHANGES / key / "task.json").read_text(encoding="utf-8"))


def traceback_free(r: subprocess.CompletedProcess) -> bool:
    return "Traceback" not in r.stdout + r.stderr


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)

        # ---- tf task verify: evidence reuse -----------------------------------------------------------------------
        p = base / "nogit"
        p.mkdir()
        call(p, TASK, "start", "EV-1", "--title", "outside git")
        (p / "a.py").write_text("A = 1\n", encoding="utf-8")
        r1 = call(p, TASK, "verify", "EV-1", "S1", "--files", "a.py", "--command", OK)
        r2 = call(p, TASK, "verify", "EV-1", "S1", "--files", "a.py", "--command", OK)
        ev = json.loads((p / CHANGES / "EV-1" / "evidence" / "S1-1.json").read_text(encoding="utf-8"))
        check(r1.returncode == 0 and r2.returncode == 0 and "already verified" not in r2.stdout
              and evidence(p, "EV-1") == ["S1-1.json", "S1-2.json"] and "tree" not in ev and ev.get("sha") is None,
              f"LE-1: outside git there is no fingerprint, so verify never reuses evidence: {r2.stdout} {evidence(p, 'EV-1')}")

        p = repo(base / "reuse")
        call(p, TASK, "start", "EV-2", "--title", "reuse")
        names = ["src/my file.py", "src/zażółć.py"]
        (p / "src").mkdir()
        for n in names:
            (p / n).write_text("X = 1\n", encoding="utf-8")
        files = ",".join(names)
        r1 = call(p, TASK, "verify", "EV-2", "S1", "--files", files, "--command", OK)
        r2 = call(p, TASK, "verify", "EV-2", "S1", "--files", files, "--command", OK)
        check(r1.returncode == 0 and r2.returncode == 0 and "already verified" in r2.stdout
              and evidence(p, "EV-2") == ["S1-1.json"],
              f"LE-2: slice files with a space and non-ASCII letters: the second verify reuses: {r1.stdout}{r2.stdout}")

        def rerun(label: str, change, expect_reuse: bool = False) -> None:
            before = evidence(p, "EV-2")
            change()
            r = call(p, TASK, "verify", "EV-2", "S1", "--files", files, "--command", OK)
            reused = "already verified" in r.stdout and evidence(p, "EV-2") == before
            check(r.returncode == 0 and reused == expect_reuse,
                  f"{label}: {'reuse' if expect_reuse else 'a new run'} expected: {r.stdout} {before} → {evidence(p, 'EV-2')}")

        rerun("LE-3: an untracked file outside the slice changes the tree → run again",
              lambda: (p / "helper.py").write_text("H = 1\n", encoding="utf-8"))
        rerun("LE-3a: the same tree again → reuse", lambda: None, expect_reuse=True)
        rerun("LE-4: a binary untracked file changes → run again",
              lambda: (p / "logo.bin").write_bytes(bytes(range(256))))
        rerun("LE-4a: its bytes change, the size stays → run again",
              lambda: (p / "logo.bin").write_bytes(bytes(reversed(range(256)))))
        git(p, "add", "-A")
        git(p, "commit", "-q", "-m", "chore: snapshot")
        rerun("LE-5: a new commit (the same files) → run again", lambda: None)
        rerun("LE-5a: a tracked file renamed → run again", lambda: git(p, "mv", "helper.py", "helper2.py"))
        rerun("LE-5b: a tracked file deleted → run again", lambda: (p / "README.md").unlink())
        rerun("LE-6: only whitespace in a slice file → run again (the hash is of bytes)",
              lambda: (p / names[0]).write_text("X = 1 \n", encoding="utf-8"))
        rerun("LE-6a: only the line endings of a slice file → run again",
              lambda: (p / names[0]).write_bytes(b"X = 1 \r\n"))
        rerun("LE-6b: only the line endings of a tracked file outside the slice → run again",
              lambda: (p / "logo.bin").write_bytes(bytes(reversed(range(256))) + b"\r\n"))
        rerun("LE-6c: task files and .tf/ do not count → reuse",
              lambda: ((p / CHANGES / "EV-2" / "notes.md").write_text("x\n", encoding="utf-8"),
                       (p / ".tf" / "x.log").write_text("x\n", encoding="utf-8")), expect_reuse=True)
        before = evidence(p, "EV-2")
        r = call(p, TASK, "verify", "EV-2", "S1", "--files", files, "--command", OK, "--force")
        check(r.returncode == 0 and "already verified" not in r.stdout and len(evidence(p, "EV-2")) == len(before) + 1,
              f"LE-7: --force runs again on the same code: {r.stdout} {before} → {evidence(p, 'EV-2')}")
        r = call(p, TASK, "verify", "EV-2", "S1", "--files", files, "--command", f'{sys.executable} -c "print(2)"')
        check(r.returncode == 0 and "already verified" not in r.stdout,
              f"LE-7a: another command → run again: {r.stdout}")
        r1 = call(p, TASK, "verify", "EV-2", "S2", "--files", files, "--command", RED)
        r2 = call(p, TASK, "verify", "EV-2", "S2", "--files", files, "--command", RED)
        check(r1.returncode == 1 and r2.returncode == 1 and "already verified" not in r2.stdout
              and [n for n in evidence(p, "EV-2") if n.startswith("S2-")] == ["S2-1.json", "S2-2.json"],
              f"LE-8: red evidence is never reused: {r2.stdout}")
        newest = sorted((p / CHANGES / "EV-2" / "evidence").glob("S1-*.json"), key=lambda f: int(f.stem.split("-")[1]))[-1]
        data = json.loads(newest.read_text(encoding="utf-8"))
        data.pop("tree", None)
        newest.write_text(json.dumps(data), encoding="utf-8")
        r = call(p, TASK, "verify", "EV-2", "S1", "--files", files, "--command", f'{sys.executable} -c "print(2)"')
        check(r.returncode == 0 and "already verified" not in r.stdout,
              f"LE-9: evidence of the old schema (no tree) is not reused: {r.stdout}")
        newest = sorted((p / CHANGES / "EV-2" / "evidence").glob("S1-*.json"), key=lambda f: int(f.stem.split("-")[1]))[-1]
        newest.write_text('{"slice": "S1", "exit_c', encoding="utf-8")
        n = int(newest.stem.split("-")[1])
        r = call(p, TASK, "verify", "EV-2", "S1", "--files", files, "--command", f'{sys.executable} -c "print(2)"')
        check(r.returncode == 0 and "already verified" not in r.stdout and f"S1-{n + 1}.json" in evidence(p, "EV-2")
              and traceback_free(r),
              f"LE-10: a truncated newest evidence file is not reused and not overwritten: {r.stdout}{r.stderr}")

        # the gate's `related` gets the slice's files as separate arguments, never through a shell
        p = repo(base / "related")
        (p / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy(HOOK, p / ".claude" / "hooks" / "quality_gate.py")
        probe = f"{sys.executable} -c \"import sys; open('argv.json', 'w').write(repr(sys.argv[1:]))\" {{files}}"
        (p / ".claude" / "quality-gate.json").write_bytes(
            json.dumps({"command": OK, "related": probe}, indent=1).replace("\n", "\r\n").encode("utf-8"))
        call(p, TASK, "start", "EV-3", "--title", "related")
        evil = "x; touch pwned.py"
        (p / evil).write_text("E = 1\n", encoding="utf-8")
        r = call(p, TASK, "verify", "EV-3", "S1", "--files", evil)
        argv = (p / "argv.json").read_text(encoding="utf-8") if (p / "argv.json").is_file() else ""
        check(r.returncode == 0 and not (p / "pwned.py").exists() and argv == repr([evil]),
              f"LE-11: a file name with `;` goes to `related` as one argument, no shell (CRLF config read): "
              f"{r.stdout}{r.stderr} {argv}")

        # ---- tf task start / approach -----------------------------------------------------------------------------
        p = base / "approach"
        p.mkdir()
        call(p, TASK, "start", "AP-1", "--title", "approach")
        tj = p / CHANGES / "AP-1" / "task.json"
        good = tj.read_text(encoding="utf-8")
        tj.write_text(good[: len(good) // 2], encoding="utf-8")
        r = call(p, TASK, "start", "AP-1", "--title", "again")
        check(r.returncode != 0 and tj.read_text(encoding="utf-8") == good[: len(good) // 2],
              f"LE-12: start does not overwrite an unreadable task.json (the slices and evidence links): {r.stdout}")
        tj.write_text(good, encoding="utf-8")

        plan = p / CHANGES / "AP-1" / "plan.md"

        def approach(*args: str) -> subprocess.CompletedProcess:
            return call(p, TASK, "approach", "AP-1", *args, "--rationale", "evidence from the files")

        plan.write_text("# Plan\n\n- [ ] S1 — login fix · files: src\\auth\\login.py\n", encoding="utf-8")
        r = approach("--weight", "quick")
        check(r.returncode != 0 and "full" in r.stdout and task(p, "AP-1").get("weight") == "normal",
              f"LE-13: a sensitive path written with backslashes (Windows) keeps the full floor: {r.stdout}")
        plan.write_text("# Plan\n\n- [ ] S1 — login fix · files: src/auth/login.py\n", encoding="utf-8")
        r = approach("--weight", "quick")
        check(r.returncode != 0 and "full" in r.stdout, f"LE-13a: the same with slashes: {r.stdout}")
        fifteen = ", ".join(f"web/f{i}.ts" for i in range(15))
        plan.write_text(f"# Plan\n\n- [ ] S1 — rename · files: {fifteen}\n", encoding="utf-8")
        r = approach("--weight", "quick")
        check(r.returncode == 0 and task(p, "AP-1").get("weight") == "quick",
              f"LE-14: exactly 15 files fit the quick weight: {r.stdout}")
        plan.write_text(f"# Plan\n\n- [ ] S1 — rename · files: {fifteen}, web/f15.ts\n", encoding="utf-8")
        r = approach("--weight", "quick")
        check(r.returncode != 0 and "16 files" in r.stdout, f"LE-14a: 16 files do not: {r.stdout}")
        plan.write_text("# Plan\n\n- [ ] S1 — a · files: a.py\n- [ ] S2 — b · files: b.py\n", encoding="utf-8")
        r = approach("--weight", "quick")
        check(r.returncode != 0 and "2 slices" in r.stdout, f"LE-14b: 2 slices do not fit quick: {r.stdout}")
        r = approach("--weight", "light")
        check(r.returncode != 0 and "2 slices" in r.stdout, f"LE-14c: 2 slices do not fit light: {r.stdout}")
        plan.write_text("# Plan\n\n- [ ] S1 — a · files: a.py\n", encoding="utf-8")
        r = approach("--weight", "light")
        check(r.returncode == 0, f"LE-14d: 1 slice and 1 file fit light: {r.stdout}")
        plan.write_text("# Plan\n\n- [ ] S1 — <value> · files: <paths>\n", encoding="utf-8")
        r = approach("--weight", "quick", "--slices", "3")
        check(r.returncode != 0 and "3" in r.stdout and task(p, "AP-1").get("weight") == "light",
              f"LE-15: a declared slice count above the weight's limit is refused before the plan exists: {r.stdout}")
        r = approach("--weight", "quick", "--slices", "1")
        check(r.returncode == 0, f"LE-15a: --slices 1 fits quick: {r.stdout}")

        d = task(p, "AP-1")
        d["stage"] = "implementation"
        tj.write_text(json.dumps(d), encoding="utf-8")
        r = approach("--weight", "light")
        check(r.returncode != 0 and "human" in r.stdout and task(p, "AP-1").get("weight") == "quick",
              f"LE-16: lowering the weight after the loop started needs --by human: {r.stdout}")
        r1 = approach("--weight", "normal")
        r2 = approach("--weight", "normal")
        d = task(p, "AP-1")
        log = d.get("approach_log") or []
        to_normal = [w for w in d.get("weight_log") or [] if w.get("to") == "normal"]
        check(r1.returncode == 0 and r2.returncode == 0 and "escalated" in r1.stdout and "escalated" not in r2.stdout
              and log[-2].get("escalated") is True and not log[-1].get("escalated") and len(to_normal) == 1,
              f"LE-17: an escalation recorded twice: marked once, one weight change: {r1.stdout}{r2.stdout} {log[-2:]}")
        r = call(p, TASK, "approach", "AP-1", "--weight", "light", "--rationale", "the human says so", "--by", "human:anna")
        check(r.returncode == 0 and task(p, "AP-1").get("weight") == "light",
              f"LE-17a: the human lowers it after the start: {r.stdout}")
        d = task(p, "AP-1")
        d["stage"] = "zombie"
        tj.write_text(json.dumps(d), encoding="utf-8")
        r = approach("--weight", "normal")
        check(r.returncode in (0, 1) and traceback_free(r),
              f"LE-18: an unknown stage in task.json (an old or hand-edited file) does not crash approach: {r.stderr[-300:]}")

        # ---- run_state.py on a corrupted run.json -----------------------------------------------------------------
        p = repo(base / "runjson")
        (p / ".claude").mkdir()
        (p / ".claude" / "quality-gate.json").write_text(json.dumps({"command": OK}), encoding="utf-8")
        call(p, REPORT, "start", "Corrupted run", "--key", "RJ-1", "--story", "a story")
        d = p / ".tf" / "runs" / "RJ-1"
        rj = d / "run.json"
        good = rj.read_text(encoding="utf-8")
        cmds = [("verify", str(d), "S1", "--files", "README.md", "--command", OK),
                ("fetch", str(d), "begin", "--what", "intake"),
                ("gate-related", str(d), "--not-found", "--rationale", "no tool"),
                ("approach", str(d), "--weight", "normal", "--rationale", "x"),
                ("finish-slice", str(d), "S1", "--files", "README.md", "--message", "feat(x): y"),
                ("stage", str(d), "plan"), ("step", str(d), "S1", "R1", "test", "run"), ("next", str(d))]
        for label, broken in (("truncated", good[:20]), ("a list", "[1, 2]"), ("a string", '"run"'), ("empty", "")):
            rj.write_text(broken, encoding="utf-8")
            bad = [(c[0], r.returncode, (r.stdout + r.stderr)[-200:]) for c in cmds
                   if (r := call(p, STATE, *c)).returncode == 0 or not traceback_free(r)]
            check(not bad, f"LE-19: run.json {label}: every command refuses with a message, no traceback: {bad}")
        rj.write_text(good, encoding="utf-8")

        meta = json.loads(good)
        meta["fetches"] = None
        rj.write_text(json.dumps(meta), encoding="utf-8")
        r1 = call(p, STATE, "fetch", str(d), "begin", "--what", "intake")
        r2 = call(p, STATE, "fetch", str(d), "begin", "--what", "intake")
        r3 = call(p, STATE, "fetch", str(d), "end", "--what", "intake")
        r4 = call(p, STATE, "fetch", str(d), "end", "--what", "intake")
        spans = json.loads(rj.read_text(encoding="utf-8")).get("fetches")
        check(r1.returncode == 0 and "already open" in r2.stdout and r3.returncode == 0 and r4.returncode == 2
              and isinstance(spans, list) and len(spans) == 1 and spans[0].get("to") and traceback_free(r1),
              f"LE-20: fetch on an old run.json (fetches: null): one span, a second begin does not open another, an end "
              f"without an open read is refused: {r1.stdout}{r1.stderr[-300:]} {r2.stdout} {r4.stdout} {spans}")
        r = call(p, STATE, "fetch", str(d), "begin", "--what", "Intake; rm -rf /")
        check(r.returncode == 2, f"LE-20a: fetch --what is a short lowercase name: {r.stdout}")

        # gate-related
        gq = p / ".claude" / "quality-gate.json"
        gq.write_bytes(json.dumps({"command": OK, "watch": ["src"]}, indent=1).replace("\n", "\r\n").encode("utf-8"))
        r = call(p, STATE, "gate-related", str(d), "--command", "pytest", "--rationale", "pyproject")
        check(r.returncode == 2 and "placeholder" in r.stdout, f"LE-21: no placeholder → refused: {r.stdout}")
        for bad in ("pytest {files}; rm -rf /", "cd web && npx jest {files}", "pytest {files} | tee log",
                    "pytest $(cat list) {files}", "pytest `x` {files}", "pytest {files} > out.txt"):
            r = call(p, STATE, "gate-related", str(d), "--command", bad, "--rationale", "pyproject")
            cfg = json.loads(gq.read_text(encoding="utf-8"))
            check(r.returncode == 2 and "related" not in cfg,
                  f"LE-22: a shell operator never works without a shell, so it is refused ({bad!r}): {r.stdout} {cfg}")
        r1 = call(p, STATE, "gate-related", str(d), "--not-found", "--rationale", "no per-file runner")
        r2 = call(p, STATE, "gate-related", str(d), "--command", "pytest -q {files}", "--rationale", "found pytest")
        cfg = json.loads(gq.read_text(encoding="utf-8"))
        check(r1.returncode == 0 and r2.returncode == 0 and cfg.get("related") == "pytest -q {files}"
              and cfg.get("related_decision", {}).get("state") == "set" and cfg.get("watch") == ["src"]
              and cfg.get("command") == OK,
              f"LE-23: not-found then found: the decision is replaced, the other keys stay (a CRLF file): {r1.stdout}{r2.stdout} {cfg}")

        # ---- finish-slice: the scan fails, then a resume ----------------------------------------------------------
        p = repo(base / "scanfail")
        call(p, REPORT, "start", "Scan fail", "--key", "SF-1", "--story", "a story")
        d = p / ".tf" / "runs" / "SF-1"
        (p / CHANGES / "SF-1" / "plan.md").write_text("# Plan\n\n- [ ] S1 — one · files: a.py\n", encoding="utf-8")
        call(p, STATE, "approach", str(d), "--weight", "light", "--rationale", "one file")
        call(p, STATE, "stage", str(d), "plan", "--auto")
        (p / "a.py").write_text("A = 1\n", encoding="utf-8")
        empty = base / "nobin"
        empty.mkdir()
        r = call(p, STATE, "finish-slice", str(d), "S1", "--files", "a.py", "--command", OK, "--message", "feat(a): one",
                 TF_SCAN_PATH=str(empty))
        rounds = (json.loads((d / "run.json").read_text(encoding="utf-8")).get("current") or {}).get("rounds") or []
        log = git(p, "log", "--format=%s").stdout.splitlines()
        check(r.returncode == 1 and len(log) == 1 and rounds and rounds[-1].get("scan") == "fail"
              and rounds[-1].get("verify") == "pass",
              f"LE-24: a failed scan stops before the commit, recorded as fail: {r.returncode} {r.stdout} {rounds}")
        fake = base / "bin"
        fake.mkdir()
        (fake / "semgrep").write_text(f"#!{sys.executable}\nimport json, sys\na = sys.argv[1:]\n"
                                      "json.dump({'version': '2.1.0', 'runs': [{'tool': {'driver': {'name': 'f', 'rules': []}}, "
                                      "'results': []}]}, open(a[a.index('--output') + 1], 'w'))\n", encoding="utf-8")
        (fake / "semgrep").chmod(0o755)
        r = call(p, STATE, "finish-slice", str(d), "S1", "--files", "a.py", "--command", OK, "--message", "feat(a): one",
                 TF_SCAN_PATH=str(fake))
        log = git(p, "log", "--format=%s").stdout.splitlines()
        check(r.returncode == 0 and "already verified" in r.stdout and "(R2)" in r.stdout and log[0] == "feat(a): one",
              f"LE-24a: the resume reuses the green evidence, works in the next round and commits: {r.stdout}{r.stderr}")
        r = call(p, STATE, "finish-slice", str(d), "S1", "--files", "a.py", "--command", OK, "--message", "feat(a): one",
                 TF_SCAN_PATH=str(fake))
        check(len(git(p, "log", "--format=%s").stdout.splitlines()) == 2 and traceback_free(r),
              f"LE-24b: finish-slice again after the commit makes no empty commit: {r.returncode} {r.stdout}")

        # ---- run_report.py finish and the time breakdown ----------------------------------------------------------
        p = base / "report"
        d = p / ".tf" / "runs" / "RP-1"
        d.mkdir(parents=True)
        for label, broken in (("started_at garbage", json.dumps({"started_at": "yesterday"})),
                              ("started_at null", json.dumps({"started_at": None})),
                              ("a list", "[]"), ("truncated", '{"started_at": "2026-')):
            (d / "run.json").write_text(broken, encoding="utf-8")
            r = call(p, REPORT, "finish", str(d))
            check(r.returncode == 2 and traceback_free(r) and "run.json" in r.stdout,
                  f"LE-25: finish with run.json {label}: code 2 and a message: {r.returncode} {r.stdout}{r.stderr[-300:]}")
        rr = module(REPORT, "le_run_report")
        since = datetime(2026, 11, 25, 10, 0, tzinfo=timezone.utc)
        last = since + timedelta(hours=1)
        (d / "evidence").mkdir()
        rows = [{"duration_s": -500, "at": "2026-11-25T10:10:00Z"}, {"duration_s": float("inf"), "at": "2026-11-25T10:11:00Z"},
                {"duration_s": float("nan"), "at": "2026-11-25T10:12:00Z"}, {"duration_s": 1e300, "at": "2026-11-25T10:13:00Z"},
                {"duration_s": 60, "at": "2026-11-25T12:15:00+02:00"}, {"duration_s": 30, "at": "2026-11-25T09:00:00Z"},
                {"duration_s": True, "at": "2026-11-25T10:20:00Z"}, {"duration_s": "60", "at": "2026-11-25T10:21:00Z"}]
        for i, row in enumerate(rows, 1):
            (d / "evidence" / f"S1-{i}.json").write_text(json.dumps(row), encoding="utf-8")
        meta = {"started_at": since.isoformat(), "fetches": [{"what": "intake", "from": "2026-11-25T10:50:00Z", "to": None},
                                                              {"what": "addon", "from": "2026-11-25T10:05:00Z",
                                                               "to": "2026-11-25T10:00:00Z"}, "junk", None],
                "waits": [{"from": "2026-11-25T10:30:00Z", "to": "2026-11-25T10:20:00Z"},
                          {"from": "2026-11-25T08:00:00Z", "to": "2026-11-25T10:05:00Z"}, {"from": "garbage"}, 7],
                "stage": "needs", "needs_at": "2026-11-25T12:40:00+02:00"}
        try:
            tb = rr.time_breakdown(p, d, meta, since, last)
        except Exception as e:  # noqa: BLE001 — the report must never crash on a bad row
            tb = {"error": repr(e)}
        check(tb.get("verify_s") == 60 and tb.get("verify_runs") == 1,
              f"LE-26: verify time counts only finite, non-negative durations after the start (a +02:00 time counts): {tb}")
        check(tb.get("wait_s") == 5 * 60 + 20 * 60 and tb.get("fetch_s") == 10 * 60 and tb.get("fetch_runs") == 2
              and all(isinstance(v, int) and v >= 0 for v in tb.values() if not isinstance(v, str)),
              f"LE-27: waits: a backwards span is 0, one from before the start is clipped, an open needs_at counts up to "
              f"the end (a time zone change), a fetch without an end runs to the end: {tb}")
        check(tb.get("total_s") == 3600 and tb.get("model_s") == 3600 - 60 - tb.get("wait_s", 0),
              f"LE-27a: the rest is the total minus the measured parts: {tb}")
        try:
            tb = rr.time_breakdown(p, d, {"waits": {"from": "x"}, "fetches": 5}, since, since - timedelta(minutes=5))
        except Exception as e:  # noqa: BLE001
            tb = {"error": repr(e)}
        check(tb.get("total_s") == 0 and tb.get("model_s") == 0 and tb.get("wait_s") == 0,
              f"LE-28: the clock went backwards (the last answer before the start), waits/fetches of a wrong type: {tb}")

        # ---- intake: keys, addresses, the cached story, no "no connection" claims ---------------------------------
        p = base / "intake"
        p.mkdir()

        def resolve(*words: str, **extra) -> dict:
            r = call(p, INTAKE, "resolve", "--json", *words, **extra)
            try:
                return json.loads(r.stdout)
            except ValueError:
                return {"error": r.stdout + r.stderr}

        for raw, kind, key in (("abc-1", "issue", "ABC-1"), ("EBO-0", "issue", "EBO-0"), ("ABC-١٢", "content", None),
                               ("ĄBC-1", "content", None), ("EBO-１２", "content", None)):
            out = resolve(raw)
            check(out.get("kind") == kind and out.get("key") == key,
                  f"LE-29: the key {raw!r} → {kind} {key}: {out.get('kind')} {out.get('key')} {out.get('error', '')}")
        for url, key in (("https://acme.atlassian.net/browse/EBO-12?focusedCommentId=5&page=x", "EBO-12"),
                         ("https://acme.atlassian.net/jira/software/projects/EBO/boards/3?selectedIssue=EBO-7", "EBO-7"),
                         ("https://jira.acme.com/secure/RapidBoard.jspa?rapidView=1&selectedIssue=ebo-8#x", "EBO-8")):
            out = resolve(url)
            check(out.get("kind") == "issue" and out.get("key") == key and out.get("ask") is None,
                  f"LE-30: a tracker address with a query → the key {key}, no question: {out}")
        jira = {"JIRA_BASE_URL": "https://acme.atlassian.net", "JIRA_TOKEN": "t0ken"}
        out = resolve("https://acme.atlassian.net/browse/EBO-12", **jira)
        check("--from-tracker" in out.get("next", "") and out.get("ask") is None,
              f"LE-31: a Jira address with the credentials in the environment → the script fetches it: {out.get('next')}")
        out = resolve("https://other.atlassian.net/browse/EBO-12", **jira)
        check("--from-tracker" not in out.get("next", ""),
              f"LE-31a: an address on another Jira host than JIRA_BASE_URL is not fetched by the script: {out.get('next')}")
        for words, extra in ((["EBO-12"], {}), (["EBO-12"], jira), (["https://acme.atlassian.net/browse/EBO-12"], {}),
                             (["https://github.com/acme/app/issues/5"], {}), (["https://example.com/x"], {}),
                             (["https://linear.app/acme/issue/LIN-3"], {}), ([], {}), (["EBO-1", "EBO-2"], {})):
            r = call(p, INTAKE, "resolve", *words, **extra)
            low = r.stdout.lower()
            check(r.returncode == 0 and not any(s in low for s in NO_CONNECTION),
                  f"LE-32: resolve {words} never claims on its own that no tracker is connected: {r.stdout}")
        r = call(p, INTAKE, "fetch", "EBO-12")
        low = r.stdout.lower()
        check(r.returncode == 2 and not any(s in low for s in NO_CONNECTION) and "connected in the session" in low,
              f"LE-33: a refused script fetch points to the tracker tool connected in the session before pasting: {r.stdout}")
        r = call(p, REPORT, "start", "--key", "EBO-12", "--from-tracker")
        low = r.stdout.lower()
        check(r.returncode == 2 and not any(s in low for s in NO_CONNECTION) and "connected in the session" in low,
              f"LE-33a: the same for run_report.py start --from-tracker: {r.stdout}")

        call(p, TASK, "start", "EBO-5", "--title", "cached")
        ticket = p / CHANGES / "EBO-5" / "ticket.md"
        ticket.write_text("", encoding="utf-8")
        out = resolve("EBO-5")
        check(out.get("kind") == "resume" and out.get("story") is None and "do not read the tracker" not in out.get("next", ""),
              f"LE-34: an empty cached ticket.md is not a cached story: {out}")
        r = call(p, REPORT, "start", "--key", "EBO-5", "--from-tracker")
        check("story cached" not in r.stdout and r.returncode == 2,
              f"LE-34a: run_report start --from-tracker does not claim an empty ticket.md as the cached story: {r.stdout}")
        ticket.write_bytes(b"# T\n\n\xff\xfe broken \x00 bytes\n")
        out = resolve("EBO-5")
        check(out.get("story") == f"{CHANGES.as_posix()}/EBO-5/ticket.md",
              f"LE-34b: a ticket.md with broken bytes but content is still the cached story (data): {out}")
        r = call(p, REPORT, "start", "--key", "EBO-5", "--from-tracker")
        check(r.returncode == 2 and "story cached" in r.stdout and traceback_free(r),
              f"LE-34c: …and run_report does not read the tracker again: {r.stdout}{r.stderr}")

        # ---- security_scan: changed files ---------------------------------------------------------------------------
        p = repo(base / "scan")
        argv_log = base / "semgrep-argv.json"
        sem = base / "sembin"
        sem.mkdir()
        (sem / "semgrep").write_text(
            f"#!{sys.executable}\nimport json, sys\na = sys.argv[1:]\n"
            f"open({str(argv_log)!r}, 'w').write(json.dumps(a))\n"
            "json.dump({'version': '2.1.0', 'runs': [{'tool': {'driver': {'name': 'f', 'rules': []}}, "
            "'results': []}]}, open(a[a.index('--output') + 1], 'w'))\n", encoding="utf-8")
        (sem / "semgrep").chmod(0o755)
        r = call(p, SCAN, "scan", "--out", str(base / "out0"), "--json", TF_SCAN_PATH=str(empty))
        v = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and v.get("status") == "PASS" and v.get("files") == [],
              f"LE-35: no changed files → PASS without needing a scanner: {r.returncode} {r.stdout[-400:]}")
        names = ["src/café.py", "src/my file.py", 'src/q"uote.py', "src/tab\there.py"]
        (p / "src").mkdir()
        for n in names:
            (p / n).write_text("X = 1\n", encoding="utf-8")
        git(p, "add", "src/café.py")
        git(p, "commit", "-q", "-m", "feat: café")
        (p / "src" / "café.py").write_text("X = 2\n", encoding="utf-8")
        r = call(p, SCAN, "scan", "--out", str(base / "out1"), "--json", TF_SCAN_PATH=str(sem))
        v = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        passed = json.loads(argv_log.read_text(encoding="utf-8")) if argv_log.is_file() else []
        check(r.returncode == 0 and sorted(v.get("files") or []) == sorted(names) and all(n in passed for n in names),
              f"LE-36: changed files with non-ASCII letters, spaces, quotes and tabs are all scanned: {v.get('files')} {passed}")
        broken = base / "brokenbin"
        broken.mkdir()
        (broken / "semgrep").write_text("#!/nonexistent/interpreter\n", encoding="utf-8")
        (broken / "semgrep").chmod(0o755)
        r = call(p, SCAN, "scan", "--out", str(base / "out2"), TF_SCAN_PATH=str(broken))
        check(r.returncode == 1 and "SCAN: FAIL" in r.stdout and traceback_free(r),
              f"LE-37: a scanner that cannot start is a FAIL with a message, not a traceback: {r.stdout}{r.stderr[-300:]}")
        engine = p / ".tf" / "factory"
        engine.mkdir(parents=True)
        for name in ("packs.py", "task_weight.py"):
            if (ROOT / ".tf" / "factory" / name).is_file():
                shutil.copy(ROOT / ".tf" / "factory" / name, engine / name)
        if (ROOT / ".tf" / "factory" / "_vendor").is_dir():
            shutil.copytree(ROOT / ".tf" / "factory" / "_vendor", engine / "_vendor", dirs_exist_ok=True)
        (p / ".tf" / "config").mkdir(parents=True)
        cfg = p / ".tf" / "config" / "config.yaml"
        cfg.write_text('security:\n  scanner: {"state": "off", "by": "human:anna", "at": "2026-11-25"}\n', encoding="utf-8")
        r = call(p, SCAN, "scan", "--out", str(base / "out3"), TF_SCAN_PATH=str(empty))
        r2 = call(p, SCAN, "scanner", TF_SCAN_PATH=str(empty))
        check(r.returncode == 1 and "by decision" not in r.stdout and r2.returncode == 1,
              f"LE-38: an off decision without a reason is no decision: the missing scanner is a FAIL: {r.stdout}{r2.stdout}")
        cfg.write_text('security:\n  scanner: {"state": "off", "by": "human:anna", "at": "2026-11-25", '
                       '"reason": "no semgrep here"}\n', encoding="utf-8")
        r = call(p, SCAN, "scan", "--out", str(base / "out4"), TF_SCAN_PATH=str(empty))
        check(r.returncode == 0 and "by decision" in r.stdout, f"LE-38a: with a reason it is recorded: {r.stdout}")
        cfg.write_text('security:\n  scanner: {"state": "off", "by": "process:tf", "reason": "x"}\n', encoding="utf-8")
        r = call(p, SCAN, "scan", "--out", str(base / "out5"), TF_SCAN_PATH=str(empty))
        check(r.returncode == 1, f"LE-38b: a decision not made by a human is no decision: {r.stdout}")

        # ---- plan_drift and ui_snap: non-ASCII names in the diff --------------------------------------------------
        p = repo(base / "drift")
        git(p, "checkout", "-q", "-b", "story/x")
        d = p / ".tf" / "runs" / "DR-1"
        d.mkdir(parents=True)
        (d / "run.json").write_text(json.dumps({"task_dir": "docs/project/changes/DR-1"}), encoding="utf-8")
        (p / CHANGES / "DR-1").mkdir(parents=True)
        (p / CHANGES / "DR-1" / "plan.md").write_text(
            "# Plan\n\n- [x] S1 — widok · files: web/żółw.tsx, web/my view.tsx\n", encoding="utf-8")
        (p / "web").mkdir()
        (p / "web" / "żółw.tsx").write_text("export const A = 1\n", encoding="utf-8")
        (p / "web" / "my view.tsx").write_text("export const B = 1\n", encoding="utf-8")
        git(p, "add", "-A")
        git(p, "commit", "-q", "-m", "feat: views")
        r = subprocess.run([sys.executable, str(DRIFT), str(d), "--base", "main", "--json"], cwd=p, capture_output=True,
                           text=True, encoding="utf-8", env=env(p), timeout=60)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(out.get("unplanned") == [] and out.get("coverage") == 100
              and sorted(out.get("changed") or []) == ["web/my view.tsx", "web/żółw.tsx"],
              f"LE-39: plan_drift reads non-ASCII names from the diff (no git quoting): {r.stdout}{r.stderr}")
        ui = module(SCRIPTS / "ui_snap.py", "le_ui_snap")
        stat = ui.diff_stat(p, "main")
        check(stat.get("web/żółw.tsx") == 1 and stat.get("web/my view.tsx") == 1,
              f"LE-40: ui_snap's diff stat keys are the real paths (worth counts the UI file): {stat}")

        # ---- proposals: hostile files --------------------------------------------------------------------------------
        p = base / "proposals"
        (p / ".tf" / "proposals").mkdir(parents=True)
        pending = p / ".tf" / "proposals" / "pending.md"
        pending.write_bytes(b"# Factory proposals\n\n## FP-1 \xe2\x80\x94 ok\nStatus: open\nDate: 2026-11-25\n"
                            b"Evidence: abc1234\nProposed change: skill:tf \xe2\x80\x94 x\n\n## FP-2 \xff\xfe broken\n")
        r = call(p, PROPOSALS, "list")
        r2 = call(p, PROPOSALS, "count")
        check(r.returncode == 0 and "FP-1" in r.stdout and r2.stdout.strip() == "1" and traceback_free(r),
              f"LE-41: a pending.md with invalid UTF-8 is read as data, not a crash: {r.stdout}{r.stderr[-300:]}")
        pr = module(PROPOSALS, "le_proposals")
        s = pr.sanitize("ok‮gnp.exe​ ⁦x⁩﻿ ## Status: done <b>|", 200)
        check(not any(c in s for c in "‮​⁦⁩﻿<>|") and "##" not in s,
              f"LE-42: sanitize removes bidi and zero-width characters too (a reviewer reads what is there): {s!r}")
        items, ignored = pr.parse("## FP-3 — t\nStatus: open\nStatus: done\nDate: 2026-11-25\nEvidence: x\n"
                                  "Proposed change: skill:a — b\n## FP-4 — t\nStatus: open; rm -rf /\nDate: 2026-11-25\n"
                                  "Evidence: x\nProposed change: skill:a — b\n")
        check(items == [] and ignored == 2, f"LE-43: a repeated or malformed field drops the entry: {items} {ignored}")

    if fails:
        print(f"✗ {len(fails)}/{total} loop edge-case tests failed:")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"✓ {total}/{total} loop edge-case tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
