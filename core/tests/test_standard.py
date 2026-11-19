#!/usr/bin/env python3
"""T2: `tf standard` — jeden wynik standardu repozytorium z istniejących kontroli fabryki.

python3 tests/test_standard.py

`.tf/factory/standard.py` zbiera: instalację (`build.py check`), dziennik projektu (`project_record.py check`),
pliki instrukcji agenta (`instructions_lint.py`), gotowość repo (`readiness_check.py` z pack-it, jeśli jest) i ślady
hooków (`hooks_status.py`). Każda kontrola ma status ok / warn / fail / skip; kod wyjścia 1 przy `fail` (z `--strict`
także przy `warn`). Plan: docs/plans/2026-11-11-program-ai-luki-w-fabryce.md (repozytorium fabryki), krok 2.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "build.py").is_file())
STANDARD = ROOT / ".tf" / "factory" / "standard.py"
READINESS = ROOT / ".claude" / "skills" / "eng-repo-readiness" / "scripts" / "readiness_check.py"


def load():
    spec = importlib.util.spec_from_file_location("tf_standard_test", STANDARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_py(script: Path, *args: str, cwd: Path):
    return subprocess.run([sys.executable, str(script), *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=600, env={**os.environ, "CLAUDE_PROJECT_DIR": str(cwd)})


def bare(base: Path, name: str) -> Path:
    """Projekt z hookami i skillami rdzenia tej instalacji, bez dziennika i bez plików instrukcji."""
    p = base / name
    shutil.copytree(ROOT / ".claude" / "hooks", p / ".claude" / "hooks", ignore=shutil.ignore_patterns("__pycache__"))
    for skill in ("core-project-record", "core-agent-instructions"):
        shutil.copytree(ROOT / ".claude" / "skills" / skill, p / ".claude" / "skills" / skill)
    shutil.copytree(ROOT / ".tf" / "factory", p / ".tf" / "factory", ignore=shutil.ignore_patterns("packs", "__pycache__", "analyzers"))
    return p


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    st = load()
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        p = bare(t, "bare")

        # ST-1: dziennik projektu
        r = st.check_journal(p)
        check(r["id"] == "journal" and r["status"] == "fail" and "docs/project" in r["summary"],
              f"ST-1: brak docs/project/ → fail z nazwą katalogu: {r}")
        init = run_py(p / ".claude" / "hooks" / "project_record.py", "init", cwd=p)
        r = st.check_journal(p)
        check(init.returncode == 0 and r["status"] in ("ok", "warn"), f"ST-1b: po init dziennik poprawny: {r} {init.stderr[-200:]}")
        brief = p / "docs" / "project" / "01-discovery" / "brief.md"
        brief.write_text("---\nartifact: brief\nphase: discovery\nstatus: proposed\nauthor: test\ndate: 2026-11-11\n---\n"
                         "# Brief\n\nTreść bez wymaganych sekcji.\n", encoding="utf-8")
        r = st.check_journal(p)
        check(r["status"] == "fail" and any("TL;DR" in d for d in r["details"]),
              f"ST-1c: artefakt bez TL;DR → fail ze szczegółem: {r}")
        index = p / "docs" / "project" / "README.md"
        before = index.read_text(encoding="utf-8") if index.exists() else None
        st.check_journal(p)
        check((index.read_text(encoding="utf-8") if index.exists() else None) == before,
              "ST-1d: kontrola dziennika niczego nie zapisuje (tylko odczyt, bez przebudowy indeksu)")
        brief.unlink()

        # ST-2: pliki instrukcji
        r = st.check_instructions(p)
        check(r["id"] == "instructions" and r["status"] == "fail" and "CLAUDE.md" in r["summary"],
              f"ST-2: brak pliku instrukcji → fail: {r}")
        (p / "CLAUDE.md").write_text("# Zasady projektu\n\n## Komendy\n- Test: `npm test`\n\n## Zasady stałe\n"
                                     "- Nigdy nie commituj sekretów.\n", encoding="utf-8")
        r = st.check_instructions(p)
        check(r["status"] == "ok", f"ST-2b: krótki CLAUDE.md → ok: {r}")
        (p / "CLAUDE.md").write_text("# Zasady\n\n- Nigdy nie commituj sekretów.\n\n## Reguły\n"
                                     + "".join(f"- reguła numer {i}\n" for i in range(600)), encoding="utf-8")
        r = st.check_instructions(p)
        check(r["status"] == "fail" and any("dlugosc" in d for d in r["details"]),
              f"ST-2c: CLAUDE.md powyżej progu długości → fail: {r}")
        (p / "CLAUDE.md").write_text("# Zasady projektu\n\n## Zasady stałe\n- Nigdy nie commituj sekretów.\n", encoding="utf-8")

        # ST-3: gotowość repo (pack-it) — pominięta bez skryptu, policzona ze skryptem
        r = st.check_readiness(p)
        check(r["id"] == "readiness" and r["status"] == "skip" and "pack-it" in r["summary"],
              f"ST-3: bez skryptu gotowości → skip z nazwą nakładki: {r}")
        if READINESS.is_file():
            shutil.copytree(READINESS.parents[1], p / ".claude" / "skills" / "eng-repo-readiness")
            r = st.check_readiness(p)
            check(r["status"] == "fail" and r["details"],
                  f"ST-3b: repo bez runnera testów i lockfile → fail z ustaleniami: {r}")

        # ST-4: ślady hooków — bez logów nie ma czego oceniać
        r = st.check_hooks(p)
        check(r["id"] == "hooks" and r["status"] in ("skip", "ok"), f"ST-4: bez logów hooków → skip (albo ok): {r}")

        # ST-5: werdykt i kod wyjścia
        mk = lambda *statuses: [{"id": f"c{i}", "status": s, "summary": "", "details": []} for i, s in enumerate(statuses)]
        check(st.verdict(mk("ok", "skip")) == "ok" and st.verdict(mk("ok", "warn")) == "warn"
              and st.verdict(mk("warn", "fail", "ok")) == "fail", "ST-5: werdykt = najgorszy status (skip nie pogarsza)")
        check(st.exit_code(mk("ok", "warn"), strict=False) == 0 and st.exit_code(mk("ok", "warn"), strict=True) == 1
              and st.exit_code(mk("fail"), strict=False) == 1 and st.exit_code(mk("ok", "skip"), strict=True) == 0,
              "ST-5b: kod 1 przy fail; przy warn tylko ze --strict")

        # ST-6: CLI w minimalnym projekcie — wybór kontroli, JSON, kod wyjścia
        cli = run_py(p / ".tf" / "factory" / "standard.py", "--json", "--only", "journal,instructions,hooks", cwd=p)
        try:
            data = json.loads(cli.stdout)
        except json.JSONDecodeError:
            data = {}
        check(cli.returncode == 0 and [c["id"] for c in data.get("checks", [])] == ["journal", "instructions", "hooks"]
              and data.get("verdict") in ("ok", "warn"),
              f"ST-6: --json --only: trzy kontrole w kolejności, werdykt ok/warn, kod 0: rc={cli.returncode} {cli.stdout[:300]} {cli.stderr[-200:]}")
        (p / "CLAUDE.md").unlink()
        cli = run_py(p / ".tf" / "factory" / "standard.py", "--only", "instructions", cwd=p)
        check(cli.returncode == 1 and "instructions" in cli.stdout and "✗" in cli.stdout,
              f"ST-6b: tekst: kontrola z fail → kod 1 i znacznik ✗: rc={cli.returncode} {cli.stdout[:300]}")
        cli = run_py(p / ".tf" / "factory" / "standard.py", "--only", "nieznana", cwd=p)
        check(cli.returncode == 2, f"ST-6c: nieznana kontrola w --only → kod 2: rc={cli.returncode} {cli.stdout[:200]}")

        # ST-7: pełny przebieg w kopii tego projektu — kontrola instalacji zgodna z build.py check
        proj = t / "proj"
        shutil.copytree(ROOT, proj, ignore=shutil.ignore_patterns("__pycache__", "logs", ".git", "*.zip", ".work"))
        rc_build = run_py(proj / ".tf" / "factory" / "build.py", "check", cwd=proj).returncode
        cli = run_py(proj / ".tf" / "factory" / "standard.py", "--json", cwd=proj)
        try:
            data = json.loads(cli.stdout)
        except json.JSONDecodeError:
            data = {}
        by_id = {c["id"]: c for c in data.get("checks", [])}
        check(list(by_id) == ["install", "journal", "instructions", "readiness", "hooks"],
              f"ST-7: pełny przebieg ma pięć kontroli w stałej kolejności: {list(by_id)} {cli.stderr[-300:]}")
        check(by_id.get("install", {}).get("status") == ("ok" if rc_build == 0 else "fail"),
              f"ST-7b: kontrola instalacji zgodna z build.py check (rc {rc_build}): {by_id.get('install')}")
        check(cli.returncode == (1 if data.get("verdict") == "fail" else 0),
              f"ST-7c: kod wyjścia zgodny z werdyktem: rc={cli.returncode} werdykt={data.get('verdict')}")

        # ST-8: `tf standard` przekazuje argumenty do silnika
        tf = run_py(proj / ".tf" / "factory" / "tf.py", "standard", "--json", "--only", "hooks", cwd=proj)
        try:
            ids = [c["id"] for c in json.loads(tf.stdout).get("checks", [])]
        except json.JSONDecodeError:
            ids = None
        check(tf.returncode == 0 and ids == ["hooks"], f"ST-8: tf standard --json --only hooks: rc={tf.returncode} {tf.stdout[:200]} {tf.stderr[-200:]}")

    print(f"test_standard: {total - len(fails)}/{total} OK")
    for f in fails:
        print(f"  ✗ {f}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
