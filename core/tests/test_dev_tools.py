#!/usr/bin/env python3
"""Tests of the token-saving tools: .tf/factory/check.py (the CI loop), build.py new-skill (extensions),
.tf/factory/finish.py (closing a task up to a commit, without a push)."""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "check.py").is_file())


def run(args, cwd=None, timeout=300):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, cwd=cwd, timeout=timeout)


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                          cwd=cwd, capture_output=True, text=True)


def stub(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("import sys\n" + body + "\n", encoding="utf-8")


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # ── A: check.py ──
    with tempfile.TemporaryDirectory() as t:
        r0 = Path(t)
        stub(r0 / ".tf" / "factory" / "build.py", "print('warning: x'); print('✓ OK')")
        stub(r0 / ".tf" / "factory" / "skill_gate.py", "print('✓ skills: 3, to pass through the gate: 0')")
        stub(r0 / "tests" / "test_ok.py", "print('✓ 2/2 tests ok')")
        stub(r0 / "tests" / "test_bad.py", "print('✗ something broke in step 7'); print('✗ 0/1 tests bad'); sys.exit(1)")
        stub(r0 / "tests" / "run_skill_evals.py", "print('✓ scenario files: 3, errors: 0')")
        r = run([ROOT / ".tf" / "factory" / "check.py", "--root", r0])
        lines = r.stdout.strip().splitlines()
        check(r.returncode == 1 and "something broke in step 7" in r.stdout and "test_bad.py" in r.stdout
              and "2/2 tests ok" not in r.stdout and "warning" not in r.stdout and lines and lines[-1].startswith("✗"),
              f"A-1: the error with details, green only as a number, the last line is the verdict: {r.stdout}{r.stderr}")
        check(re.search(r"tests\D+1/2", r.stdout) is not None and "project record" in r.stdout and "skipped" in r.stdout,
              f"A-2: the tests summary (green/all) and the skipped steps without scripts: {r.stdout}")
        r = run([ROOT / ".tf" / "factory" / "check.py", "--root", r0, "-k", "ok"])
        check(r.returncode == 0 and r.stdout.strip().splitlines()[-1].startswith("✓"), f"A-3: -k narrows the tests: {r.stdout}")
        r = run([ROOT / ".tf" / "factory" / "check.py", "--root", r0, "--json"])
        try:
            d = json.loads(r.stdout)
        except ValueError:
            d = {}
        check(d.get("ok") is False and any(s["name"] == "tests/test_bad.py" and not s["ok"] for s in d.get("steps", [])),
              f"A-4: --json: {r.stdout[:300]}")

    # The hints of all skills at once: a new skill must not "steal" the hint from an older one (a check.py step).
    r = run([ROOT / ".tf" / "factory" / "skill_gate.py", "--hints"], cwd=ROOT)
    check(r.returncode == 0 and "hints" in r.stdout and r.stdout.strip().splitlines()[-1].startswith("✓"),
          f"A-5: skill_gate --hints checks the hook hits for the scenarios of all skills: {r.stdout[-300:]}{r.stderr[-300:]}")
    with tempfile.TemporaryDirectory() as t:
        r0 = Path(t)
        stub(r0 / ".tf" / "factory" / "skill_gate.py", "print('✗ #x: the hook will not hint the skill'); print('✗ hints: 1 skill'); sys.exit(1)"
             if True else "")
        r = run([ROOT / ".tf" / "factory" / "check.py", "--root", r0])
        check(r.returncode == 1 and "hints of all skills" in r.stdout, f"A-6: the hints step in check.py: {r.stdout}")

    # ── B: build.py new-skill — review deadline, words, --role, --name-only ──
    with tempfile.TemporaryDirectory() as t:
        root = Path(t) / "f"
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "logs", "__pycache__", "*.zip"))
        r = run([root / ".tf" / "factory" / "build.py", "new-skill", "core-demo-x", "Użyj przy demo. Nie do niczego (core-grounding).",
                 "--role", "no-such-role"], cwd=root)
        check(r.returncode == 2 and not (root / ".claude" / "skills" / "core-demo-x").exists(),
              f"B-1: an unknown role → code 2, nothing created: {r.stdout}{r.stderr}")
        role_files = sorted(root.glob(".tf/factory/packs/*/roles/*.yaml")) or sorted(root.glob(".tf/config/roles/*.yaml"))
        if not role_files:                     # the core only: a project role for the wiring test
            (root / ".tf" / "config" / "roles").mkdir(parents=True, exist_ok=True)
            (root / ".tf" / "config" / "roles" / "demo.yaml").write_text(
                "name: demo\ntitle: Demo\ntier: std\ntriggers: demo\nidentity: demo\ntools: [Read]\nskills: [core-grounding]\n",
                encoding="utf-8")
            role_files = [root / ".tf" / "config" / "roles" / "demo.yaml"]
        role_file = role_files[0]
        r = run([root / ".tf" / "factory" / "build.py", "new-skill", "core-demo-x", "Użyj przy demo. Nie do niczego (core-grounding).",
                 "--role", role_file.stem, "--name-only"], cwd=root)
        md = (root / ".claude" / "skills" / "core-demo-x" / "SKILL.md")
        text = md.read_text(encoding="utf-8") if md.exists() else ""
        m = re.search(r"^  review: \"(\d{4}-\d{2}-\d{2})\"$", text, re.M)
        role = role_file.read_text(encoding="utf-8")
        check(r.returncode == 0 and m and "  visibility: name" in text and re.search(r"^  keywords: \"", text, re.M)
              and re.search(r"^skills: \[.*\bcore-demo-x\]$", role, re.M),
              f"B-2: review deadline, words, visibility and wiring into the role: {r.stdout[-300:]}{r.stderr[-300:]}\n{text[:400]}")
        fr = run([root / ".tf" / "factory" / "freshness.py", "--root", root, "--json"])
        rows = {x["skill"]: x["status"] for x in json.loads(fr.stdout or "{}").get("skills", [])}
        check(rows.get("core-demo-x") == "ok", f"B-3: the review deadline is valid for freshness.py: {rows.get('core-demo-x')}")

    # ── C: finish.py ──
    if shutil.which("git"):
        with tempfile.TemporaryDirectory() as t:
            repo = Path(t) / "repo"
            repo.mkdir()
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "t")          # the CI runner has no global git identity
            git(repo, "config", "user.email", "t@t")
            git(repo, "config", "commit.gpgsign", "false")
            (repo / "a.txt").write_text("a\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "chore: init")
            stub(repo / "scripts" / "check_commit_message.py",
                 "t = open(sys.argv[sys.argv.index('--file') + 1]).read()\nsys.exit(0 if t.startswith('feat') else 1)")
            msg = Path(t) / "msg.txt"
            msg.write_text("feat(x): add b\n\nCo-Authored-By: t\n")
            fin = ROOT / ".tf" / "factory" / "finish.py"
            (repo / "b.txt").write_text("b\n")
            r = run([fin, "--root", repo, "--message", msg, "--no-check"])
            n = git(repo, "rev-list", "--count", "HEAD").stdout.strip()
            check(r.returncode == 2 and n == "1", f"C-1: na main odmowa: {r.stdout}{r.stderr}")
            git(repo, "checkout", "-q", "-b", "feature")
            bad = Path(t) / "bad.txt"
            bad.write_text("bad content\n")
            r = run([fin, "--root", repo, "--message", bad, "--no-check"])
            check(r.returncode == 1 and git(repo, "rev-list", "--count", "HEAD").stdout.strip() == "1",
                  f"C-2: bad commit content → code 1, no commit: {r.stdout}{r.stderr}")
            (repo / ".env").write_text("SECRET=1\n")
            r = run([fin, "--root", repo, "--message", msg, "--no-check"])
            check(r.returncode == 2 and ".env" in r.stdout + r.stderr, f"C-3: plik .env w zmianach → odmowa: {r.stdout}{r.stderr}")
            (repo / ".env").unlink()
            stub(repo / ".tf" / "factory" / "check.py", "print('✗ testy 0/1'); sys.exit(1)")
            r = run([fin, "--root", repo, "--message", msg])
            check(r.returncode == 1 and git(repo, "rev-list", "--count", "HEAD").stdout.strip() == "1",
                  f"C-4: czerwone sprawdzenia → bez commita: {r.stdout}{r.stderr}")
            r = run([fin, "--root", repo, "--message", msg, "--no-check"])
            last = git(repo, "log", "-1", "--format=%s").stdout.strip()
            check(r.returncode == 0 and last == "feat(x): add b" and "git push -u origin feature" in r.stdout
                  and git(repo, "status", "--porcelain").stdout.strip() == "",
                  f"C-5: a commit with content from a file, the push command printed, not executed: {r.stdout}{r.stderr} {last}")
            r = run([fin, "--root", repo, "--message", msg, "--no-check"])
            check(r.returncode == 0 and "nothing to commit" in r.stdout, f"C-6: no changes → nothing to commit: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tool tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
