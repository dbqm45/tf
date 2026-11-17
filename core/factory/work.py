#!/usr/bin/env python3
"""Praca bez nadzoru (krok H19): `tf work --once` bierze jedno zadanie, które człowiek oznaczył trybem Auto
(`tf task mode <KEY> auto`), i prowadzi je pętlą `/tf` w osobnym worktree z limitem wydatku. Nie scala i nie wdraża:
wynikiem jest gałąź `story/<key>` z PR albo blok STOP w worktree zadania.

  tf work --once --budget <USD> [--key <KEY>] [--base <gałąź>] [--dry-run]

Zadanie do wzięcia: tryb Auto, waga lekka albo zwykła, etap przed PR, nie czeka na człowieka, nie ma jeszcze worktree
(wznowienie w istniejącym worktree tylko przez `--key`) i nie jest zajęte przez inny przebieg (`.tf/locks/<KEY>.json`).
Kod wyjścia: 0 — przebieg zakończony, 2 — odmowa, 3 — nie ma zadania do wzięcia, inny — kod agenta.
Agent: `claude -p "/tf <KEY> --auto --budget <USD>" --max-budget-usd <USD> --permission-mode <tryb, domyślnie acceptEdits>
--strict-mcp-config`, tylko z dozwolonymi zmiennymi środowiskowymi; przed startem pliki sterujące agentem w worktree
muszą być takie jak w kopii człowieka. Zmienna `TF_WORK_AGENT` podmienia polecenie `claude` (testy). Dziennik:
`.tf/logs/work.jsonl`.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa nie zna „✓” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

CHANGES = Path("docs") / "project" / "changes"
LOCKS = Path(".tf") / "locks"
WORKTREES = Path(".tf") / "worktrees"
LOG = Path(".tf") / "logs" / "work.jsonl"
MANIFEST = Path(".claude") / "factory-manifest.json"
OWN_CONFIG = Path(".tf") / "config"
OPEN_STAGES = ("intake", "spec", "plan", "implementation", "review")
DEFAULTS = {"budget_usd": 0, "task_budget_usd": 20, "permission_mode": "acceptEdits", "lock_hours": 6, "timeout_minutes": 180}
# bez nadzoru nikt nie odpowie na pytanie o zgodę: w trybie -p narzędzie spoza listy dozwolonych jest odrzucane.
# acceptEdits (domyślny) przyjmuje edycje plików w katalogu roboczym (worktree) — bez tego pętla nie napisze kodu, bo
# ustawienia fabryki nie dopuszczają Edit/Write (pilotaż 2026-11-15); dontAsk odrzuca też edycje; szersze tryby odpadają
MODES = ("acceptEdits", "dontAsk", "plan")
COPY_PREFIXES = (".claude/", ".tf/factory/")   # z manifestu kopiowane są tylko pliki fabryki
MAX_RUN_USD = 500
# pliki, które sterują agentem (uprawnienia, hooki, instrukcje, serwery MCP): w worktree muszą być takie jak w kopii
# człowieka — inaczej gałąź zadania (np. z cudzego pusha) wykonałaby bez pytania własny hook albo instrukcję
CONTROL_FILES = (".claude/settings.json", ".claude/settings.local.json", ".mcp.json", "CLAUDE.md", "CLAUDE.local.md",
                 "AGENTS.md", ".claude/CLAUDE.md", ".claude/rules", ".claude/output-styles", ".claude/hooks",
                 ".claude/agents", ".claude/skills", ".claude/commands", ".tf/factory", ".tf/config")
INSTRUCTION_NAMES = ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md")     # także zagnieżdżone w katalogach projektu
# zmienne środowiskowe przekazywane agentowi: system, proxy i certyfikaty, uwierzytelnianie Claude; reszta (tokeny
# GitHuba, chmury, bazy) tylko z listy człowieka w zmiennej TF_WORK_ENV_ALLOW
ENV_ALLOW = {"PATH", "HOME", "USER", "LOGNAME", "SHELL", "LANG", "LANGUAGE", "TERM", "TMPDIR", "TMP", "TEMP", "TZ",
             "PWD", "PYTHONUTF8", "PYTHONIOENCODING", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "https_proxy",
             "http_proxy", "no_proxy", "ALL_PROXY", "all_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
             "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "GIT_SSL_CAINFO", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
             "ANTHROPIC_BASE_URL", "CLAUDE_CONFIG_DIR", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME",
             "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT", "APPDATA", "LOCALAPPDATA", "USERPROFILE",
             "HOMEDRIVE", "HOMEPATH", "PROGRAMFILES", "PROGRAMDATA", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE",
             "TF_WORK_AGENT"}
ENV_PREFIXES = ("LC_", "CLAUDE_CODE_", "ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_")   # bez TF_: Terraform trzyma tam sekrety
ENV_EXTRA = "TF_WORK_ENV_ALLOW"   # dodatkowe zmienne (np. GITHUB_TOKEN) podaje człowiek w swoim środowisku, nie repozytorium
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def config(root: Path) -> dict:
    """Sekcja `work`: silnik ← organizacja (nakładka firmowa) ← projekt; bez konfiguracji — wartości domyślne."""
    try:
        spec = importlib.util.spec_from_file_location("tf_packs_cfg", Path(__file__).resolve().with_name("packs.py"))
        packs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packs)
        cfg = packs.load_yaml(Path(__file__).resolve().with_name("config.yaml"))
        for _label, layer in packs.config_layers(root)[1:]:   # organizacja (nakładka firmowa), potem projekt
            cfg = packs.deep_merge(cfg, layer)
        section = cfg.get("work") if isinstance(cfg.get("work"), dict) else {}
    except Exception:  # noqa: BLE001 — brak konfiguracji to ustawienia domyślne
        section = {}
    return {**DEFAULTS, **section}


def load_task(root: Path, key: str) -> dict | None:
    try:
        data = json.loads((root / CHANGES / key / "task.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def waits_for_human(root: Path, key: str) -> bool:
    try:
        run = json.loads((root / ".tf" / "runs" / key / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(run, dict) and run.get("stage") == "needs"


def clean(text, limit: int = 120) -> str:
    return CONTROL.sub(" ", str(text or ""))[:limit]


def refusal(root: Path, task: dict, folder: str) -> str | None:
    """Dlaczego zadania nie wolno wziąć bez nadzoru; None — wolno. Klucz to nazwa folderu zadania, a pole `key`
    w task.json musi się z nią zgadzać (task.json przychodzi z repozytorium, np. z cudzego PR)."""
    if not KEY.fullmatch(folder) or task.get("key") != folder:
        return f"{clean(folder)}: the key in task.json does not match the task folder name. Task skipped"
    key = folder
    if task.get("closed") or task.get("stage") not in OPEN_STAGES:
        return f"{key}: stage {clean(task.get('stage'), 30)}. Unattended work takes a task only as far as a PR"
    if task.get("weight") == "full":
        return f"{key}: weight full. Unattended work takes only light and normal tasks (full needs a panel and a human)"
    if task.get("mode") != "auto":
        return (f"{key}: mode {clean(task.get('mode') or 'normal', 30)}, not auto. A human must allow unattended work: "
                f"tf task mode {key} auto")
    if waits_for_human(root, key):
        return f"{key}: waits for a human (tf status). It returns to the queue after the answer"
    return None


def candidates(root: Path) -> list[dict]:
    """Zadania do wzięcia, najstarsze pierwsze; pomija te z worktree (wznowienie tylko przez --key)."""
    out = []
    for f in sorted((root / CHANGES).glob("*/task.json")):
        task = load_task(root, f.parent.name)
        if task and refusal(root, task, f.parent.name) is None and not (root / WORKTREES / f.parent.name).exists():
            out.append(task)
    return sorted(out, key=lambda t: str(t.get("created") or ""))


def alive(pid) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True            # brak uprawnień albo system bez sygnałów — traktuj jak żywy
    return True


def claim(root: Path, key: str, hours: float) -> tuple[bool, str]:
    """Zajmuje zadanie atomowo (`O_CREAT|O_EXCL`). Martwą blokadę tego hosta starszą niż `hours` przejmuje."""
    folder = root / LOCKS
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{key}.json"
    note = ""
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            try:
                held = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                held = {}
            held = held if isinstance(held, dict) else {}
            at = held.get("at") if isinstance(held.get("at"), (int, float)) else path.stat().st_mtime
            stale = (time.time() - at > hours * 3600 and held.get("host") == socket.gethostname()
                     and not alive(held.get("pid")))
            if not stale:
                return False, ""
            note = (f"⚠ took over the lock on {key} held by dead process {held.get('pid')} since {datetime.fromtimestamp(at).isoformat(timespec='minutes')}")
            if not take_over(path, held, hours):
                return False, ""
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "host": socket.gethostname(), "at": time.time()}, f)
        return True, note
    return False, ""


def take_over(path: Path, seen: dict, hours: float) -> bool:
    """Usuwa martwą blokadę pod osobnym muteksem (`<KEY>.json.takeover`, `O_EXCL`): przejmuje jeden proces, a przed
    usunięciem sprawdza, że blokada to nadal ta sama martwa, którą odczytał (nie świeża blokada innego procesu)."""
    mutex = path.with_name(path.name + ".takeover")
    try:
        if time.time() - mutex.stat().st_mtime > hours * 3600:
            mutex.unlink(missing_ok=True)          # muteks po przerwanym przejęciu
    except OSError:
        pass
    try:
        fd = os.open(mutex, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except OSError:
        return False
    os.close(fd)
    try:
        try:
            now_held = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return True
        except (OSError, ValueError):
            now_held = {}
        if (now_held if isinstance(now_held, dict) else {}) != seen:
            return False
        path.unlink(missing_ok=True)
        return True
    finally:
        mutex.unlink(missing_ok=True)


def release(root: Path, key: str) -> None:
    (root / LOCKS / f"{key}.json").unlink(missing_ok=True)


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=120)


def inside(root: Path, rel: str) -> Path | None:
    p = (root / rel).resolve()
    return p if not Path(rel).is_absolute() and root.resolve() in p.parents else None


def within(base: Path, path: Path) -> bool:
    try:
        return base.resolve() in path.resolve().parents
    except OSError:
        return False


def copy_missing(src: Path, dst: Path, src_root: Path, dst_root: Path) -> int:
    """Kopiuje plik albo katalog, pomijając to, co w miejscu docelowym już jest, symlinki i ścieżki wychodzące poza
    katalogi źródłowy i docelowy; zwraca liczbę plików."""
    if src.is_symlink() or not within(src_root, src) or not within(dst_root, dst.parent / "x"):
        return 0
    if src.is_file():
        if dst.exists() or dst.is_symlink():
            return 0
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return 1
    n = 0
    for f in sorted(src.rglob("*")) if src.is_dir() else []:
        if f.is_file() and "__pycache__" not in f.parts:
            n += copy_missing(f, dst / f.relative_to(src), src_root, dst_root)
    return n


def prepare_worktree(root: Path, key: str, base: str) -> tuple[Path | None, str]:
    """Worktree zadania na gałęzi `story/<key>`; przy instalacji prywatnej pliki fabryki nie są w gicie, więc kopiuje
    pliki z manifestu, konfigurację projektu i folder zadania, których w worktree brakuje."""
    wt = root / WORKTREES / key
    if not within(root / WORKTREES, wt):
        return None, "worktree path is outside .tf/worktrees"
    if not wt.exists():
        branch = f"story/{key.lower()}"
        has = git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0
        r = git(root, "worktree", "add", "-q", str(wt), branch) if has else \
            git(root, "worktree", "add", "-q", "-b", branch, str(wt), base)
        if r.returncode != 0:
            return None, f"git worktree add failed: {(r.stdout + r.stderr).strip()}"
    try:
        files = json.loads((root / MANIFEST).read_text(encoding="utf-8")).get("files") or {}
    except (OSError, ValueError, AttributeError):
        files = {}
    referenced = sorted(r for r in settings_paths(root)            # bez sekretów, nawet gdy polecenie je wskazuje
                        if not any(part.startswith((".env", ".git")) for part in Path(r).parts))
    rels = [MANIFEST.as_posix(), *CONTROL_FILES, *referenced, (CHANGES / key).as_posix(),
            (Path(".tf") / "runs" / key).as_posix(),
            *[r for r in files if isinstance(r, str) and r.startswith(COPY_PREFIXES) and ".." not in Path(r).parts]]
    # brakujące w worktree pliki sterujące (niezatwierdzone albo poza gitem) pochodzą z kopii człowieka; pliki, które
    # gałąź ma inne niż ta kopia, nie są nadpisywane — wykrywa je control_drift i przebieg jest odrzucany
    copied = sum(copy_missing(src, wt / rel, root, wt) for rel in dict.fromkeys(rels)
                 if (src := inside(root, rel)) and src.exists())
    return wt, f"copied {copied} factory and task files to the worktree" if copied else ""


def agent_command(key: str, budget: str, mode: str) -> list[str]:
    agent = shlex.split(os.environ.get("TF_WORK_AGENT") or "claude")
    return [*agent, "-p", f"/tf {key} --auto --budget {budget}", "--max-budget-usd", budget, "--permission-mode", mode,
            "--strict-mcp-config"]        # bez --mcp-config: żadnych serwerów MCP z repozytorium ani z konfiguracji


def agent_env() -> dict:
    """Środowisko agenta: zmienne z listy dozwolonych i te, które człowiek wymienił w `TF_WORK_ENV_ALLOW` swojego
    środowiska (konfiguracja z repozytorium nie może tej listy rozszerzyć — przyszłaby z cudzym PR)."""
    allow = set(ENV_ALLOW) | {x.strip() for x in (os.environ.get(ENV_EXTRA) or "").split(",") if x.strip()}
    return {k: v for k, v in os.environ.items() if k in allow or k.startswith(ENV_PREFIXES)}


def files_of(base: Path, rel: str) -> dict[str, str]:
    """Pliki ścieżki sterującej (plik albo katalog) z ich skrótem; symlink dostaje znacznik, nie treść."""
    import hashlib
    top = base / rel
    paths = [top] if top.is_file() or top.is_symlink() else (sorted(top.rglob("*")) if top.is_dir() else [])
    out = {}
    for f in paths:
        if "__pycache__" in f.parts or f.suffix == ".pyc" or (f.is_dir() and not f.is_symlink()):
            continue
        name = f.relative_to(base).as_posix()
        try:
            out[name] = (f"symlink:{os.readlink(f)}" if f.is_symlink() else
                         f"{hashlib.sha256(f.read_bytes()).hexdigest()}:{f.stat().st_mode & 0o111:o}")
        except OSError:
            out[name] = "unreadable"
    return out


def settings_paths(base: Path) -> set[str]:
    """Pliki projektu, które wskazują polecenia w ustawieniach (hooki, statusLine, apiKeyHelper…) i polecenie bramki
    jakości (`.claude/quality-gate.json`, np. `./verify.sh` z tf onboard): wykonują je claude i hooki, więc należą do
    plików sterujących. Bierze każdy napis z ustawień i każde jego słowo, które jest plikiem projektu."""
    out: set[str] = set()

    def strings(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for v in x.values():
                yield from strings(v)
        elif isinstance(x, list):
            for v in x:
                yield from strings(v)

    for name in (".claude/settings.json", ".claude/settings.local.json", ".claude/quality-gate.json"):
        f = base / name
        try:
            if f.is_symlink() or not f.is_file() or f.stat().st_size > 1_000_000:
                continue                   # symlink i plik nienaturalnej wielkości trafią do różnic przez files_of
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for text in strings(data):
            try:
                words = shlex.split(text)
            except ValueError:
                words = text.split()
            for w in words:
                w = re.sub(r"^\$\{?CLAUDE_PROJECT_DIR\}?/", "", w.strip("\"'"))
                if w and not w.startswith(("-", "/")) and ".." not in Path(w).parts and (base / w).is_file():
                    out.add(Path(w).as_posix())
    return out


def instruction_files(base: Path) -> set[str]:
    """Zatwierdzone pliki instrukcji w całym projekcie (także zagnieżdżone `CLAUDE.md` modułów)."""
    pats = [f":(glob)**/{n}" for n in INSTRUCTION_NAMES]
    out: set[str] = set()
    for extra in ([], ["-o", "--exclude-standard"]):          # zatwierdzone i nowe, niezignorowane
        r = git(base, "ls-files", "-z", *extra, "--", *pats)
        out |= {p for p in r.stdout.split("\0") if p} if r.returncode == 0 else set()
    return out


def control_set(root: Path, wt: Path) -> list[str]:
    return sorted(set(CONTROL_FILES) | settings_paths(root) | settings_paths(wt) | instruction_files(root)
                  | instruction_files(wt))


def snapshot(base: Path, rels: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in rels:
        out.update(files_of(base, rel))
    return out


def control_drift(root: Path, wt: Path) -> list[str]:
    """Pliki sterujące agentem, które w worktree różnią się od kopii człowieka (brak po jednej stronie też)."""
    diff = [f"{d} (symlink)" for d in (".claude", ".tf") if (wt / d).is_symlink()]
    rels = control_set(root, wt)
    mine, theirs = snapshot(root, rels), snapshot(wt, rels)
    return diff + sorted(n for n in set(mine) | set(theirs) if mine.get(n) != theirs.get(n))


def budget_text(value) -> str | None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return f"{v:g}" if 0 < v <= MAX_RUN_USD else None


def spent(root: Path, key: str) -> float:
    """Suma limitów wcześniejszych przebiegów zadania z dziennika (górne oszacowanie wydatku)."""
    total = 0.0
    try:
        lines = (root / LOG).read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0.0
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if isinstance(e, dict) and e.get("key") == key and isinstance(e.get("budget_usd"), (int, float)):
            total += float(e["budget_usd"])
    return total


def write_log(root: Path, entry: dict) -> None:
    f = root / LOG
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as h:
        h.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_once(root: Path, key: str | None, budget_arg: str | None, base: str | None, dry: bool) -> int:
    cfg = config(root)
    budget = budget_text(budget_arg if budget_arg is not None else cfg.get("budget_usd"))
    if budget is None:
        print(f"✗ give a spending limit above 0 and up to {MAX_RUN_USD} USD: tf work --once --budget <USD> (or work.budget_usd "
              "in .tf/config/config.yaml). Unattended work does not start without a limit")
        return 2
    mode = str(cfg.get("permission_mode") or DEFAULTS["permission_mode"])
    if mode not in MODES:
        print(f"✗ work.permission_mode \"{clean(mode, 40)}\": unattended work allows only: {', '.join(MODES)}")
        return 2
    if base is not None and (not base or base.startswith("-") or CONTROL.search(base)):
        print("✗ --base: give a branch name or a commit")
        return 2
    try:
        cap = float(cfg.get("task_budget_usd"))        # 0 — świadomie bez łącznego limitu
        cap = cap if cap >= 0 and cap == cap else float(DEFAULTS["task_budget_usd"])
    except (TypeError, ValueError):
        cap = float(DEFAULTS["task_budget_usd"])       # zepsuta wartość nie wyłącza limitu
    if key:
        task = load_task(root, key) if KEY.fullmatch(key) else None
        if task is None:
            print(f"✗ no task {clean(key, 64)}")
            return 2
        why = refusal(root, task, key)
        if why:
            print(f"✗ {why}")
            return 2
        queue = [task]
    else:
        queue = candidates(root)
    for task in queue:
        k = task["key"]
        if cap and spent(root, k) + float(budget) > cap:
            msg = (f"{k}: total task limit work.task_budget_usd = {cap:g} USD. Earlier runs "
                   f"{spent(root, k):g} USD + this run {budget} USD. A human decides on more spending")
            if key:
                print(f"✗ {msg}")
                return 2
            print(f"• {msg}")
            continue
        if dry:
            print(f"• task: {k} — {clean(task.get('title'))}")
            print(f"• worktree: {(root / WORKTREES / k).as_posix()} (branch story/{k.lower()} from {base or 'HEAD'})")
            print(f"• command: {shlex.join(agent_command(k, budget, mode))}")
            return 0
        ok, note = claim(root, k, float(cfg.get("lock_hours") or 6))
        if not ok:
            continue
        if note:
            print(note)
        started = now()
        try:
            wt, info = prepare_worktree(root, k, base or "HEAD")
            if wt is None:
                print(f"✗ {k}: {info}")
                write_log(root, {"key": k, "started": started, "ended": now(), "exit": 2, "error": info})
                return 2
            if info:
                print(f"• {info}")
            drift = control_drift(root, wt)
            if drift:
                shown = ", ".join(drift[:12]) + (f" and {len(drift) - 12} more" if len(drift) > 12 else "")
                print(f"✗ {k}: agent control files in the worktree differ from your copy of the project: {shown}. Unattended, "
                      "the agent does not run another person's hook, instructions or MCP server. Review the differences (git diff "
                      f"in {wt.relative_to(root).as_posix()}), commit your changes, or remove the worktree and the task branch")
                write_log(root, {"key": k, "event": "refused", "started": started, "ended": now(), "exit": 2,
                                 "drift": drift[:50]})
                return 2
            watched = control_set(root, wt)
            before = snapshot(root, [*watched, ".git/hooks", ".git/config"])
            print(f"• {k}: /tf loop in {wt.as_posix()}, limit {budget} USD")
            write_log(root, {"key": k, "event": "start", "started": started, "budget_usd": float(budget),
                             "worktree": wt.relative_to(root).as_posix()})   # przed agentem: przerwanie też się liczy
            try:
                code = subprocess.run(agent_command(k, budget, mode), cwd=wt, env=agent_env(),
                                      timeout=float(cfg.get("timeout_minutes") or 180) * 60).returncode
            except FileNotFoundError:
                print("✗ the claude command (Claude Code) is not in PATH")
                code = 127
            except subprocess.TimeoutExpired:
                print(f"✗ {k}: run stopped after {cfg.get('timeout_minutes')} min")
                code = 124
            after = load_task(wt, k) or {}
            now_root = snapshot(root, [*sorted(set(watched) | instruction_files(root)), ".git/hooks", ".git/config"])
            changed = sorted(n for n in set(before) | set(now_root) if before.get(n) != now_root.get(n))
            if changed:
                print(f"⚠ {k}: control files in your copy of the project (outside the worktree) changed during the run: "
                      f"{', '.join(changed[:12])}. Review them before the next session (git diff)")
            entry = {"key": k, "event": "end", "started": started, "ended": now(), "exit": code,
                     "stage": after.get("stage"), "worktree": wt.relative_to(root).as_posix(),
                     **({"root_changed": changed[:50]} if changed else {})}
            write_log(root, entry)
            print(f"{'✓' if code == 0 else '✗'} {k}: exit code {code}, stage {after.get('stage') or '?'}. Result in "
                  f"{entry['worktree']} (tf status in the worktree). A human does the merge")
            return code
        finally:
            release(root, k)
    print("• no task to take. A task needs mode Auto (tf task mode <KEY> auto), weight light or normal, no worktree, "
          "and no lock" + (". All matching tasks are locked" if queue else ""))
    return 3


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tf work", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--once", action="store_true", help="one task, then stop (the only mode for now)")
    ap.add_argument("--key", default=None)
    ap.add_argument("--budget", default=None)
    ap.add_argument("--base", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv[1:])
    if not args.once:
        print("✗ usage: tf work --once --budget <USD> [--key <KEY>] [--base <branch>] [--dry-run]")
        return 2
    return run_once(Path.cwd(), args.key, args.budget, args.base, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
