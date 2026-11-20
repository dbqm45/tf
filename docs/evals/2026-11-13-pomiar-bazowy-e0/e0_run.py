#!/usr/bin/env python3
"""Pomiar bazowy E0: od instalacji fabryki do gałęzi z zielonymi testami na repozytorium testowym.

  python3 docs/evals/2026-11-13-pomiar-bazowy-e0/e0_run.py <historyjka: S1|S2|S3|S4> <powtórzenie>
          [--model sonnet] [--budget 3] [--timeout 2400]
  E0_CONFIG="loop:\n  blocked_slices: true" python3 … e0_run.py S2 1    # z ustawieniem projektu na czas pomiaru
  E0_LAYOUT=plugin python3 … e0_run.py S1 1    # tryb fabryki: instalacja --layout plugin, claude z --plugin-dir

Przebieg jest płatny (wywołuje `claude -p`) — uruchamiaj tylko za zgodą człowieka. Katalog roboczy i wyniki:
zmienna E0_OUT (domyślnie katalog tymczasowy), żeby kopie repozytorium nie trafiały do repozytorium fabryki.

Jeden przebieg = świeża kopia repozytorium → instalacja fabryki → tf onboard → pętla /tf bez nadzoru (claude -p)
(do 2026-11-13 polecenie nazywało się /talos-story-run i wymagało trybu mode-talos).
Wynik dopisywany do $E0_OUT/results.jsonl. Sprawdzenia akceptacji są ukryte przed agentem (leżą tutaj, nie w repozytorium).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FACTORY = HERE.parents[2]   # repozytorium fabryki, z którego instalujemy
OUT = Path(os.environ.get("E0_OUT") or tempfile.mkdtemp(prefix="e0-"))
STORIES = {"S1": "S1-limit-dobowy.md", "S2": "S2-abonament.md", "S3": "S3-mieszkancy.md",
           "S4": "S4-paragon-i-zgubiony-bilet.md"}   # S4 (po kroku G): jedna część jasna, druga z otwartym pytaniem
ACCEPT = {
    "S1": """
from parking.fees import fee
assert fee(12 * 60) == 4500, fee(12 * 60)
assert fee(11 * 60) == 4400, fee(11 * 60)
assert fee(24 * 60 + 61) == 4500 + 800, fee(24 * 60 + 61)
assert fee(30) == 0 and fee(61) == 800
""",
    "S2": """
import io, contextlib
from parking.fees import fee
from parking.cli import main
assert fee(61, subscriber=True) == 600, fee(61, subscriber=True)
assert fee(180, subscriber=True) == 800, fee(180, subscriber=True)
assert fee(180) == 1200 and fee(61) == 800 and fee(180, subscriber=False) == 1200
assert fee(30, subscriber=True) == 0
assert fee(24 * 60 - 1, subscriber=True) <= 4000
assert fee(40 * 60, subscriber=True) >= 4000
out = io.StringIO()
with contextlib.redirect_stdout(out):
    code = main(["cli", "180", "--subscriber"])
assert code == 0 and out.getvalue().strip() == "8,00 zł", out.getvalue()
out = io.StringIO()
with contextlib.redirect_stdout(out):
    main(["cli", "180"])
assert out.getvalue().strip() == "12,00 zł", out.getvalue()
""",
    # S4: część jasna (paragon) zrobiona, bez zmiany dotychczasowego wyniku
    "S4": """
import io, contextlib
from parking.cli import main
out = io.StringIO()
with contextlib.redirect_stdout(out):
    code = main(["cli", "125", "--receipt"])
assert code == 0 and out.getvalue().strip().splitlines() == ["Czas postoju: 2 h 5 min", "Do zapłaty: 12,00 zł"], out.getvalue()
out = io.StringIO()
with contextlib.redirect_stdout(out):
    main(["cli", "125"])
assert out.getvalue().strip() == "12,00 zł", out.getvalue()
""",
}
# S4: czy pętla zgadła kwotę, której nikt nie podał (źle) — funkcja zwraca liczbę
GUESS = {"S4": """
import sys
try:
    from parking.fees import lost_ticket_fee
except ImportError:
    sys.exit(0)
try:
    value = lost_ticket_fee()
except Exception:
    sys.exit(0)
sys.exit(1 if isinstance(value, (int, float)) and not isinstance(value, bool) else 0)
"""}


def sh(cmd, cwd, timeout=600, **kw):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, **kw)


def git(repo, *args):
    return sh(["git", "-c", "user.name=dev", "-c", "user.email=dev@example.test", *args], repo)


def main(argv):
    story, rep = argv[1], argv[2]
    opt = dict(zip(argv[3::2], argv[4::2]))
    model, budget, timeout = opt.get("--model", "sonnet"), opt.get("--budget", "3"), int(opt.get("--timeout", "2400"))
    run_dir = OUT / "runs" / f"{story}-r{rep}"
    shutil.rmtree(run_dir, ignore_errors=True)
    repo = run_dir / "repo"
    shutil.copytree(HERE / "repo", repo, ignore=shutil.ignore_patterns("__pycache__"))
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    row = {"story": story, "rep": int(rep), "model": model, "budget_usd": float(budget),
           "factory": sh(["git", "rev-parse", "--short", "HEAD"], FACTORY).stdout.strip(),
           "factory_version": (FACTORY / "core" / "factory" / "VERSION").read_text().strip()}

    t0 = time.time()
    layout = os.environ.get("E0_LAYOUT") or "default"      # E0_LAYOUT=plugin: factory mode (tf code), plan 2026-11-20
    row["layout"] = layout
    r = sh([sys.executable, str(FACTORY / "core" / "factory" / "install.py"), ".", "--yes", "--packs",
            "pack-it", *(["--layout", "plugin"] if layout == "plugin" else [])], repo)
    row["install_ok"], row["install_s"] = r.returncode == 0, round(time.time() - t0, 1)
    t0 = time.time()
    r = sh([sys.executable, ".tf/factory/tf.py", "onboard", "--yes", "--verify"], repo)
    row["onboard_ok"], row["onboard_s"] = r.returncode == 0, round(time.time() - t0, 1)
    row["tree_clean_after_onboard"] = git(repo, "status", "--porcelain").stdout.strip() == ""
    (run_dir / "onboard.txt").write_text(r.stdout + r.stderr)
    # opcjonalne ustawienia projektu na czas pomiaru (np. E0_CONFIG="loop:\n  blocked_slices: true"): dopisane do
    # .tf/config/config.yaml i zapisane commitem, żeby pętla startowała z czystym drzewem roboczym
    extra = (os.environ.get("E0_CONFIG") or "").replace("\\n", "\n").strip()
    if extra:
        cfg = repo / ".tf" / "config" / "config.yaml"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text((cfg.read_text().rstrip("\n") + "\n\n" if cfg.is_file() else "") + extra + "\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "chore: project settings for the measurement")
        row["config_extra"] = extra

    # treść historyjki wklejona do polecenia — tak, jak zrobi to człowiek; plik poza repozytorium byłby niedostępny
    text = (HERE / "stories" / STORIES[story]).read_text()
    prompt = f"/tf {text.strip()}\n\n--auto --budget {budget}"
    t0 = time.time()
    try:
        plugin = ["--plugin-dir", str(repo / ".tf" / "plugin"), "--settings",
                  str(repo / ".tf" / "plugin" / "session-settings.json")] if layout == "plugin" else []
        r = sh(["claude", *plugin, "-p", prompt, "--model", model, "--output-format", "json", "--permission-mode", "acceptEdits"],
               repo, timeout=timeout)
        out, timed_out = r.stdout, False
    except subprocess.TimeoutExpired as e:
        out, timed_out = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or ""), True
    row["wall_s"], row["timed_out"] = round(time.time() - t0, 1), timed_out
    (run_dir / "claude.json").write_text(out)
    try:
        res = json.loads(out)
    except ValueError:
        res = {}
    row.update({"cost_usd": res.get("total_cost_usd"), "turns": res.get("num_turns"), "is_error": res.get("is_error"),
                "duration_ms": res.get("duration_ms"), "permission_denials": len(res.get("permission_denials") or []),
                "denied": sorted({(d.get("tool_input") or {}).get("command", d.get("tool_name", "?"))[:80]
                                  for d in (res.get("permission_denials") or [])})[:12],
                "models_used": sorted((res.get("modelUsage") or {}).keys())})
    (run_dir / "result.txt").write_text(str(res.get("result", "")))

    row["branch"] = git(repo, "branch", "--show-current").stdout.strip()
    row["commits"] = int(git(repo, "rev-list", "--count", "main..HEAD").stdout.strip() or 0)
    row["dirty_after"] = bool(git(repo, "status", "--porcelain").stdout.strip())
    row["code_changed"] = bool(git(repo, "diff", "--stat", "main", "--", "parking", "tests").stdout.strip())
    v = sh(["./verify.sh"], repo)
    row["verify_green"] = v.returncode == 0
    if story in ACCEPT:
        a = sh([sys.executable, "-c", ACCEPT[story]], repo)
        row["accept_ok"], row["accept_err"] = a.returncode == 0, (a.stderr.strip().splitlines() or [""])[-1][:200]
    if story in GUESS:
        row["guessed_amount"] = sh([sys.executable, "-c", GUESS[story]], repo).returncode == 1
    runs = sorted((repo / ".tf" / "runs" / "talos").glob("*/")) if (repo / ".tf" / "runs" / "talos").is_dir() else []
    if runs:
        d = runs[-1]
        row["run_files"] = sorted(p.name for p in d.iterdir())
        parked = d / "parked.md"
        row["parked_lines"] = len([ln for ln in parked.read_text().splitlines() if ln.strip().startswith(("-", "*", "1"))]) \
            if parked.is_file() else 0
    # układ z kroku C4: zadanie w docs/project/changes/<KEY>/, katalog roboczy w .tf/runs/<KEY>/
    tasks = sorted((repo / "docs" / "project" / "changes").glob("*/task.json"))
    if tasks:
        d = tasks[-1].parent
        row["task_key"] = d.name
        row["task_files"] = sorted(p.name for p in d.iterdir())
        row["evidence_files"] = len(list(d.glob("evidence/*.json")))
        st = sh([sys.executable, ".tf/factory/task_state.py", "status", d.name, "--json"], repo,
                env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo)})
        try:
            status = json.loads(st.stdout)
        except ValueError:
            status = {}
        row["task_stage"] = status.get("stage")
        row["slice_states"] = status.get("slice_states")
        plan = (d / "plan.md").read_text() if (d / "plan.md").is_file() else ""
        row["plan_ticked"] = plan.count("- [x]")
        row["plan_open"] = sum(1 for ln in plan.splitlines() if ln.strip().startswith("- [ ] K") and "<" not in ln[:12])
        row["task_commit"] = bool(git(repo, "log", "main..HEAD", "--grep", "^docs(task): record", "--oneline").stdout.strip())
        row["task_tracked"] = bool(git(repo, "ls-files", str(d.relative_to(repo))).stdout.strip())
        # krok D: specyfikacja i ślad kryterium → test → commit → dowód
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(repo)}
        for name, script, args in (("spec", "spec_check.py", ["check", d.name, "--json"]),
                                   ("trace", "trace_check.py", [d.name, "--json", "--base", "main"])):
            out = sh([sys.executable, f".tf/factory/{script}", *args], repo, env=env)
            try:
                res_ = json.loads(out.stdout)
            except ValueError:
                res_ = {}
            row[f"{name}_ok"] = res_.get("ok")
            if name == "spec":
                row["spec_criteria"] = len(res_.get("criteria") or [])
                row["spec_errors"] = [e.get("rule") for e in res_.get("errors") or []]
            else:
                rows_ = res_.get("rows") or []
                row["trace_with_test"] = sum(1 for r in rows_ if r.get("tests"))
                row["trace_red"] = sum(1 for r in rows_ if r.get("red"))
                row["trace_verified"] = sum(1 for r in rows_ if r.get("evidence") == "zweryfikowany")
                row["trace_errors"] = [e.get("rule") for e in res_.get("errors") or []]
        row["flag"] = status.get("flag")
        # kroki F3 i G: kawałek zablokowany pytaniem, zdarzenia, ważne ustalenia przeglądu, zatrzymanie przebiegu
        row["blocked_slices"] = sorted(k for k, s in (status.get("slice_states") or {}).items() if s == "zablokowany")
        ev = d / "events.jsonl"
        events = [json.loads(ln) for ln in ev.read_text().splitlines() if ln.strip()] if ev.is_file() else []
        row["events"] = [e.get("type") for e in events]
        row["findings"] = len(status.get("findings") or [])
        try:
            meta = json.loads((repo / ".tf" / "runs" / d.name / "run.json").read_text())
        except (OSError, ValueError):
            meta = {}
        row["run_stage"], row["stop_code"] = meta.get("stage"), meta.get("stop_code")
        row["plan_deps"] = sum(1 for ln in plan.splitlines() if " po: " in ln)
        work = repo / ".tf" / "runs" / d.name
        row["run_files"] = sorted(p.name for p in work.iterdir()) if work.is_dir() else []
        parked = work / "parked.md"
        row["parked_lines"] = len([ln for ln in parked.read_text().splitlines() if ln.strip().startswith(("-", "*", "1"))
                                   and not ln.startswith("- <")]) if parked.is_file() else 0
    with (OUT / "results.jsonl").open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
