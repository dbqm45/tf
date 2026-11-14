#!/usr/bin/env python3
"""
tf task — stan zadania w jednym miejscu: `docs/project/changes/<KEY>/task.json` i indeks zadań. Jedyny pisarz
tych plików; model woła polecenia, nie edytuje stanu ręcznie. Bez modelu i bez sieci.

  tf task start <KEY> --title "<tytuł>" [--weight lekka|zwykla|pelna] [--mode plan|zwykly|auto]
  tf task stage <KEY> <etap> [--force]
  tf task status <KEY> [--json]
  tf task slice <KEY> K1 planned|implemented|blocked [--title "<wartość>"] [--reason "<powód blokady>"]
  tf task verify <KEY> K1 --files <plik>[,<plik>…] [--command "<polecenie>"] [--timeout <s>]
  tf task artifact <KEY> <plik> --stage <etap> --by <wykonawca> [--inputs <plik>[,<plik>…]]
  tf task approve <KEY> <plik> --by human:<id>
  tf task check <KEY>
  tf task weight <KEY> [--apply | --set lekka|zwykla|pelna] [--by human:<id> --reason "<dlaczego>"] [--json]

`tf status` (czyli `task_state.py list [--json]`) wypisuje wszystkie zadania: etap, ile kawałków ma aktualny dowód
i które pliki trzeba odświeżyć — stan liczony przy odczycie, nie z INDEX.md.

Klucz: numer z trackera (PROJ-123), klucz pdi (CHG-12, TSK-57) albo T-<RRRRMMDD>-<slug>. Etapy idą w kolejności:
przyjecie → specyfikacja → plan → realizacja → przeglad → pr → wdrozenie → zamkniecie; cofnięcie wymaga --force.
`start` w istniejącym katalogu zmiany (np. z trybu pdi) dokłada sam `task.json` i nie rusza innych plików.
Każdy zapis odświeża `docs/project/changes/INDEX.md` — jeden wiersz na zadanie, żeby agent nie przeglądał folderów.

Kawałek jest „zweryfikowany” tylko wtedy, gdy ma dowód. `verify` samo uruchamia polecenie (domyślnie to z
`.claude/quality-gate.json`), więc kodu wyjścia nie da się zadeklarować, i zapisuje `evidence/K1-<n>.json`
(polecenie, kod wyjścia, SHA commita, czas, skróty plików kawałka); pełne wyjście idzie do `.tf/runs/<KEY>/`. Stan jest wyliczany przy każdym odczycie: brak dowodu albo zmiana
pliku po dowodzie → niezweryfikowany; kod wyjścia inny niż 0 → czerwony. Do etapu `przeglad` i dalszych zadanie
przechodzi dopiero, gdy wszystkie kawałki są zweryfikowane (albo z --force). Gdy zadanie ma `spec.md`, do etapu `plan`
i dalszych przechodzi dopiero ze specyfikacją bez błędów (`tf spec check <KEY>`), a do etapu `przeglad` i dalszych —
gdy każde kryterium ma test (`tf trace <KEY>`); zadanie bez `spec.md` działa jak dotąd.

Waga zadania (`weight`, reguły w `task_weight.py`): bez opcji pokazuje obecną wagę i propozycję z powodem; `--apply`
przydziela propozycję (pierwszy raz dowolną, potem tylko wyższą; po decyzji człowieka nic nie zmienia); `--set` podnosi swobodnie, a obniża tylko z
`--by human:<id>` i `--reason`. Skutki: zadanie o wadze `pelna` wchodzi do etapu `realizacja` dopiero z planem
zatwierdzonym przez człowieka (`approve <KEY> plan.md`); zadanie o wadze `lekka` ma w planie najwyżej jeden kawałek.

Pliki zadania (`spec.md`, `plan.md`…) rejestruje `artifact`: kto je wygenerował i z których plików powstały (skróty
wejść). Zatwierdza tylko człowiek (`approve --by human:<id>`). Stan pliku jest wyliczany: zmiana wejścia → nieaktualny;
zmiana pliku po zatwierdzeniu → do ponownego zatwierdzenia. Stan jest w `task.json`, nie w nagłówkach plików — plików
skrypt nigdy nie zmienia (nagłówki kontraktu pdi zostają nietknięte). Wykonawca: `<narzędzie>/<wersja>`,
`human:<id>` albo `process:<id>` (jak w OKF 0.2). `check` kończy się kodem 1, gdy któryś plik nie jest aktualny.

Wyrocznia zadania: `freeze <KEY> <plik>[,<plik>…] --by human:<id>` zamraża pliki spoza katalogu zadania (np. testy
akceptacyjne) — hook `guard_paths` pyta człowieka przed zapisem do nich, do zatwierdzonych plików zadania i do
`spec.md` od etapu realizacji, a zmiana zamrożonego pliku inną drogą blokuje `check` i etap `przeglad`.
`reopen <KEY> <plik> --by human:<id> --reason "<powód>"` zdejmuje zatwierdzenie albo zamrożenie i zapisuje powód.

Flaga funkcji: `flag <KEY> set <klucz> [--remove-by RRRR-MM-DD]` zapisuje flagę, za którą chowa się nowe zachowanie;
`flag <KEY> none --reason "bez flagi, bo …"` — jawny brak flagi; `flag <KEY> allow <środowisko> --by human:<id>` —
zgodę człowieka na włączenie poza środowiskiem testowym. Zadanie ze `spec.md` przechodzi do etapu `pr` dopiero
z flagą albo powodem jej braku i bez błędu `tf flag check <KEY>` (flaga włączona poza testem bez zgody).

Kod wyjścia: 0 — zrobione; 1 — odmowa (zadanie istnieje, nie ma go, etap wstecz); 2 — błąd wywołania.
Tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne też piszą i czytają UTF-8

SCHEMA = 1
CHANGES = Path("docs") / "project" / "changes"
KEY = re.compile(r"[A-Z][A-Z0-9]*-[A-Za-z0-9][A-Za-z0-9-]*")
STAGES = ("przyjecie", "specyfikacja", "plan", "realizacja", "przeglad", "pr", "wdrozenie", "zamkniecie")
WEIGHTS = ("lekka", "zwykla", "pelna")
MODES = ("plan", "zwykly", "auto")
SLICE = re.compile(r"K[1-9][0-9]?")
SLICE_STATES = ("planned", "implemented", "blocked")
GATED = STAGES[STAGES.index("przeglad"):]   # etapy, do których nie wchodzi zadanie z niezweryfikowanym kawałkiem
ACTOR = re.compile(r"(human|process):[\w.@-]+|[\w.-]+/[\w.-]+")
INDEX_HEAD = ("# Zadania\n\nGenerowany przez `tf task` — nie edytuj ręcznie. Szczegóły zadania: "
              "`docs/project/changes/<klucz>/`.\n\n| Klucz | Tytuł | Etap | Zmieniono |\n|---|---|---|---|\n")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fail(msg: str, code: int = 1) -> int:
    print(f"✗ {msg}")
    return code


def task_path(root: Path, key: str) -> Path:
    return root / CHANGES / key / "task.json"


def load(root: Path, key: str) -> dict | None:
    try:
        data = json.loads(task_path(root, key).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_atomic(path: Path, text: str) -> None:
    """Zapis przez plik tymczasowy i zamianę — przerwany zapis nie zostawia połowy pliku."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def save(root: Path, task: dict) -> None:
    write_atomic(task_path(root, task["key"]), json.dumps(task, ensure_ascii=False, indent=1) + "\n")
    write_index(root)


def write_index(root: Path) -> None:
    rows = []
    base = root / CHANGES
    for f in sorted(base.glob("*/task.json")):
        t = load(root, f.parent.name)
        if not t:
            continue
        title = str(t.get("title", "")).replace("|", "\\|").replace("\n", " ")
        rows.append(f"| {t.get('key', f.parent.name)} | {title} | {t.get('stage', '?')} | {str(t.get('updated', ''))[:10]} |")
    write_atomic(base / "INDEX.md", INDEX_HEAD + "\n".join(rows) + ("\n" if rows else ""))


def sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def evidence_of(root: Path, key: str, sl: dict) -> dict | None:
    rel = sl.get("evidence")
    if not rel:
        return None
    try:
        data = json.loads((root / CHANGES / key / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def slice_state(root: Path, key: str, sl: dict) -> tuple[str, str]:
    """(stan, powód) wyliczony z dowodu i bieżących plików — nie z deklaracji."""
    if sl.get("state") == "blocked":
        return "zablokowany", sl.get("reason") or "bez podanego powodu"
    ev = evidence_of(root, key, sl)
    if ev is None:
        return ("zaplanowany", "") if sl.get("state") == "planned" else ("niezweryfikowany", "brak dowodu")
    if ev.get("exit_code") != 0:
        return "czerwony", f"`{ev.get('command')}` zakończone kodem {ev.get('exit_code')}"
    changed = [f for f, h in (ev.get("files") or {}).items() if sha256(root / f) != h]
    if changed:
        return "niezweryfikowany", "pliki zmienione po dowodzie: " + ", ".join(changed)
    return "zweryfikowany", ""


def slice_states(root: Path, task: dict) -> dict[str, tuple[str, str]]:
    return {k: slice_state(root, task["key"], v) for k, v in sorted((task.get("slices") or {}).items())}


def inside(folder: Path, name: str) -> Path | None:
    """Plik zadania po nazwie względem katalogu zadania; None, gdy wskazuje poza katalog albo nie istnieje."""
    target = (folder / name).resolve()
    if Path(name).is_absolute() or folder.resolve() not in target.parents or not target.is_file():
        return None
    return target


def artifact_state(root: Path, key: str, art: dict, name: str) -> tuple[str, str]:
    """(stan, powód) pliku zadania wyliczony ze skrótów: szkic / zatwierdzony / nieaktualny / zmieniony po zatwierdzeniu."""
    folder = root / CHANGES / key
    changed = [f for f, h in (art.get("inputs") or {}).items() if sha256(folder / f) != h]
    if changed:
        return "nieaktualny", "zmienione wejścia: " + ", ".join(changed)
    if art.get("status") == "zatwierdzony":
        if sha256(folder / name) != art.get("approved_sha"):
            return "zmieniony po zatwierdzeniu", "wymaga ponownego zatwierdzenia przez człowieka"
        return "zatwierdzony", ""
    return "szkic", ""


def artifact_states(root: Path, task: dict) -> dict[str, tuple[str, str]]:
    return {n: artifact_state(root, task["key"], a, n) for n, a in sorted((task.get("artifacts") or {}).items())}


def frozen_changed(root: Path, task: dict) -> list[str]:
    """Zamrożone pliki, których treść różni się od zapisanej przy zamrożeniu (albo których już nie ma)."""
    return [rel for rel, f in sorted((task.get("frozen") or {}).items()) if sha256(root / rel) != f.get("sha")]


def cmd_freeze(root: Path, key: str, files: list[str], by: str) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    entries = {}
    for rel in files:
        target = inside(root, rel)
        if target is None:
            return fail(f"„{rel}” nie jest plikiem w projekcie — podaj ścieżkę względem katalogu głównego", 2)
        entries[target.relative_to(root).as_posix()] = {"sha": sha256(target), "by": by, "at": now()}
    task.setdefault("frozen", {}).update(entries)
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key}: zamrożone {', '.join(entries)} — zmiana wymaga: tf task reopen {key} <plik> --by human:<id> --reason \"…\"")
    return 0


def cmd_reopen(root: Path, key: str, name: str, by: str, reason: str) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    art = (task.get("artifacts") or {}).get(name)
    if art is not None and art.get("status") == "zatwierdzony":
        art["status"] = "szkic"
        art.pop("approved_sha", None)
        what = "zatwierdzenie zdjęte"
    elif name in (task.get("frozen") or {}):
        del task["frozen"][name]
        what = "zamrożenie zdjęte"
    else:
        return fail(f"{name} nie jest ani zatwierdzonym plikiem zadania {key}, ani plikiem zamrożonym — nie ma czego otwierać")
    task.setdefault("reopened", []).append({"file": name, "by": by, "at": now(), "reason": reason})
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key} {name}: {what} ({reason}). Po zmianie zarejestruj i zatwierdź plik ponownie.")
    return 0


def cmd_artifact(root: Path, key: str, name: str, stage: str, by: str, inputs: list[str]) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    folder = root / CHANGES / key
    if inside(folder, name) is None:
        return fail(f"nie ma pliku {name} w {CHANGES / key}/ — rejestrujesz istniejący plik zadania", 2)
    hashes = {}
    for f in inputs:
        target = inside(folder, f)
        if target is None:
            return fail(f"wejście „{f}” nie jest plikiem w {CHANGES / key}/", 2)
        hashes[f] = sha256(target)
    task.setdefault("artifacts", {})[name] = {"stage": stage, "status": "szkic", "generated": {"by": by, "at": now()},
                                              "inputs": hashes}
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key} {name}: szkic (etap {stage}" + (f"; wejścia: {', '.join(hashes)}" if hashes else "") + ")")
    return 0


def cmd_approve(root: Path, key: str, name: str, by: str) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    art = (task.get("artifacts") or {}).get(name)
    if art is None:
        return fail(f"plik {name} nie jest zarejestrowany — najpierw: tf task artifact {key} {name} --stage … --by …", 2)
    state, why = artifact_state(root, key, art, name)
    if state == "nieaktualny":
        return fail(f"{name} jest nieaktualny ({why}) — odśwież go i zarejestruj ponownie przed zatwierdzeniem")
    art["status"] = "zatwierdzony"
    art["approved_sha"] = sha256(root / CHANGES / key / name)
    art["verified"] = [{"by": by, "at": now()}]
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key} {name}: zatwierdzony przez {by}")
    return 0


def cmd_check(root: Path, key: str) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    bad = {n: (s, w) for n, (s, w) in artifact_states(root, task).items() if s in ("nieaktualny", "zmieniony po zatwierdzeniu")}
    for n, (s, w) in bad.items():
        print(f"⚠ {n}: {s} ({w})")
    changed = frozen_changed(root, task)
    for rel in changed:
        print(f"⚠ {rel}: zamrożony plik zmieniony bez decyzji człowieka — cofnij zmianę albo: tf task reopen {key} {rel} "
              "--by human:<id> --reason \"…\"")
    if not bad and not changed:
        print(f"✓ {key}: pliki zadania są aktualne")
    return 1 if bad or changed else 0


def cmd_slice(root: Path, key: str, slice_id: str, state: str, title: str | None, reason: str | None) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    sl = task.setdefault("slices", {}).setdefault(slice_id, {})
    sl["state"] = state
    if title:
        sl["title"] = title.strip()
    if state == "blocked":
        sl["reason"] = (reason or "").strip()
    else:
        sl.pop("reason", None)
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key} {slice_id}: {slice_state(root, key, sl)[0]}")
    return 0


def run_command(root: Path, command: str, timeout: float) -> tuple[int, str]:
    """Uruchamia polecenie weryfikacji (bez powłoki; przez blokadę testów, gdy fabryka ją ma): (kod wyjścia, wyjście)."""
    argv = shlex.split(command)
    lock = root / ".claude" / "hooks" / "test_lock.py"
    if lock.is_file():
        argv = [sys.executable, str(lock), "--", *argv]
    try:
        r = subprocess.run(argv, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, env={**os.environ, "CLAUDE_PROJECT_DIR": str(root)})
    except subprocess.TimeoutExpired as e:
        out = e.stdout if isinstance(e.stdout, str) else (e.stdout or b"").decode("utf-8", "replace")
        return 124, f"przekroczony limit czasu {timeout:g} s\n{out}"
    except OSError as e:
        return 127, str(e)
    return r.returncode, r.stdout + r.stderr


def clip(out: str, saved: str) -> str:
    if len(out) <= 3000:
        return out
    return out[:1000] + f"\n… [pominięto {len(out) - 3000} znaków; całość: {saved}] …\n" + out[-2000:]


def red_tests(root: Path, files: list[str]) -> dict[str, str]:
    """Pliki kawałka, które hook TDD widział jako czerwony test (`.tf/logs/tdd-red.jsonl`): plik → czas pierwszego
    czerwonego uruchomienia. Dziennik jest poza gitem, więc wpis trafia do dowodu kawałka."""
    out: dict[str, str] = {}
    try:
        lines = (root / ".tf" / "logs" / "tdd-red.jsonl").read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        for rel in (row.get("tests") or []) if isinstance(row, dict) else []:
            if rel in files and str(row.get("at", "")) < out.get(rel, "~"):
                out[rel] = str(row.get("at", ""))
    return out


def cmd_verify(root: Path, key: str, slice_id: str, command: str, files: list[str], timeout: float) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    hashes = {}
    for f in files:
        target = (root / f).resolve()
        if Path(f).is_absolute() or root not in target.parents:
            return fail(f"plik „{f}” jest poza projektem — podaj ścieżki względne plików kawałka", 2)
        digest = sha256(target)
        if digest is None:
            return fail(f"nie ma pliku {f} — dowód wiąże się z istniejącymi plikami kawałka", 2)
        hashes[f] = digest
    folder = root / CHANGES / key / "evidence"
    n = 1 + max([int(m.group(1)) for m in (re.fullmatch(rf"{slice_id}-(\d+)\.json", x.name) for x in folder.glob(f"{slice_id}-*.json")) if m]
                or [0]) if folder.is_dir() else 1
    try:
        head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=20)
        commit = head.stdout.strip() if head.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        commit = None
    code, out = run_command(root, command, timeout)
    log = Path(".tf") / "runs" / key / f"{slice_id}-{n}.log"
    try:   # pełne wyjście poza gitem; w dowodzie zostaje tylko ścieżka
        (root / log).parent.mkdir(parents=True, exist_ok=True)
        (root / log).write_text(out, encoding="utf-8")
    except OSError:
        pass
    rel = f"evidence/{slice_id}-{n}.json"
    write_atomic(root / CHANGES / key / rel, json.dumps(
        {"slice": slice_id, "command": command, "exit_code": code, "sha": commit, "at": now(), "files": hashes,
         "log": str(log), **({"red_tests": red} if (red := red_tests(root, list(hashes))) else {})},
        ensure_ascii=False, indent=1) + "\n")
    sl = task.setdefault("slices", {}).setdefault(slice_id, {})
    if sl.get("state") != "implemented":
        sl["state"] = "implemented"
        sl.pop("reason", None)
    sl["evidence"] = rel
    task["updated"] = now()
    save(root, task)
    state, why = slice_state(root, key, sl)
    print(f"{'✓' if code == 0 else '✗'} {key} {slice_id}: {state} (dowód: {CHANGES / key / rel})"
          + (f" — {why}" if why else ""))
    if code != 0:
        print(f"--- wyjście ---\n{clip(out, str(log))}")
    return 0 if code == 0 else 1


def cmd_start(root: Path, key: str, title: str, weight: str, mode: str) -> int:
    if load(root, key) is not None:
        return fail(f"zadanie {key} już istnieje ({CHANGES / key / 'task.json'}) — stan: tf task status {key}")
    stamp = now()
    save(root, {"schema": SCHEMA, "key": key, "title": title, "stage": STAGES[0], "weight": weight, "mode": mode,
                "created": stamp, "updated": stamp})
    print(f"✓ zadanie {key} założone: {CHANGES / key}/ (etap: {STAGES[0]})")
    return 0


def weight_rules():
    """Reguły wagi zadania z `task_weight.py` obok tego skryptu; None, gdy pliku nie ma (starsza instalacja)."""
    script = Path(__file__).resolve().with_name("task_weight.py")
    if not script.is_file():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_task_weight", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def weight_gate(root: Path, task: dict, stage: str) -> str | None:
    """Skutki wagi przy zmianie etapu: `lekka` — plan z jednym kawałkiem; `pelna` — plan zatwierdzony przez człowieka
    przed realizacją. Zwraca powód odmowy albo None."""
    key, weight = task["key"], task.get("weight")
    rules = weight_rules()
    if weight == "lekka" and rules and STAGES.index(stage) >= STAGES.index("plan"):
        try:
            slices = rules.plan_slices((root / CHANGES / key / "plan.md").read_text(encoding="utf-8", errors="replace"))
        except OSError:
            slices = []
        if len(slices) > 1:
            return (f"zadanie ma wagę lekką, czyli jeden kawałek, a plan ma ich {len(slices)} — połącz kawałki albo "
                    f"podnieś wagę: tf task weight {key} --set zwykla")
    if weight == "pelna" and STAGES.index(stage) >= STAGES.index("realizacja"):
        art = (task.get("artifacts") or {}).get("plan.md")
        state = artifact_state(root, key, art, "plan.md")[0] if art else "brak"
        if state != "zatwierdzony":
            return (f"zadanie ma wagę pełną (obszar wrażliwy), więc do etapu {stage} przechodzi dopiero z planem "
                    f"zatwierdzonym przez człowieka (stan planu: {state}): pokaż plan człowiekowi, a po jego zgodzie "
                    f"tf task approve {key} plan.md --by human:<id>. Przebieg bez nadzoru (--auto) kończy się tu "
                    "blokiem STOP — zgody człowieka nie da się zastąpić")
    return None


def cmd_weight(root: Path, key: str, apply: bool, new: str | None, by: str | None, reason: str, as_json: bool) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    rules = weight_rules()
    if rules is None:
        return fail("brak .tf/factory/task_weight.py — zaktualizuj fabrykę (tf update)", 2)
    if new is not None and new not in WEIGHTS:
        return fail(f"nieznana waga „{new}” — do wyboru: {', '.join(WEIGHTS)}", 2)
    current = task.get("weight") if task.get("weight") in WEIGHTS else "zwykla"
    assigned = bool(task.get("weight_log"))
    prop = rules.propose(root, key)
    note = ""

    def record(weight: str, who: str, **extra) -> None:
        task.setdefault("weight_log", []).append({"from": current, "to": weight, "by": who, "at": now(), **extra})
        task["weight"], task["updated"] = weight, now()
        save(root, task)

    if new is not None:
        who = by or "process:tf"
        if not ACTOR.fullmatch(who):
            return fail(f"wykonawca „{who}” — oczekiwany zapis: human:<id> albo process:<id>", 2)
        if rules.rank(new) < rules.rank(current):
            if not who.startswith("human:"):
                return fail(f"obniżenie wagi ({rules.LABEL[current]} → {rules.LABEL[new]}) to decyzja człowieka: "
                            f"tf task weight {key} --set {new} --by human:<id> --reason \"<dlaczego>\"")
            if not reason.strip():
                return fail("podaj powód obniżenia: --reason \"<dlaczego mniejsza waga wystarczy>\"", 2)
        if new != current or not assigned:
            record(new, who, **({"reason": " ".join(reason.split())} if reason.strip() else {}))
        current, assigned = new, True
    elif apply:
        last = (task.get("weight_log") or [{}])[-1]
        if str(last.get("by", "")).startswith("human:"):      # decyzja człowieka zostaje; fabryka tylko mówi, co widzi
            if prop["weight"] != current:
                note = (f"wagę ustawił człowiek ({last['by']}) — fabryka jej nie zmienia; jej propozycja to "
                        f"{rules.LABEL[prop['weight']]}")
        elif not assigned or rules.rank(prop["weight"]) > rules.rank(current):
            record(prop["weight"], "process:tf", reasons=prop["reasons"])
            current, assigned = prop["weight"], True
        elif rules.rank(prop["weight"]) < rules.rank(current):
            note = (f"propozycja ({rules.LABEL[prop['weight']]}) jest niższa niż przydzielona waga — zostaje "
                    f"{rules.LABEL[current]}; obniżyć może tylko człowiek: tf task weight {key} --set {prop['weight']} "
                    "--by human:<id> --reason \"<dlaczego>\"")
    if as_json:
        print(json.dumps({"key": key, "weight": current, "assigned": assigned, "proposal": prop["weight"],
                          "reasons": prop["reasons"], "effect": rules.EFFECT[current], "note": note},
                         ensure_ascii=False, indent=1))
        return 0
    state = "" if assigned else " (domyślna, jeszcze nieprzydzielona)"
    print(f"{key}: waga {rules.LABEL[current]}{state} · propozycja: {rules.LABEL[prop['weight']]}")
    for r in prop["reasons"]:
        print(f"  powód: {r}")
    print(f"  skutek: {rules.EFFECT[current]}")
    if note:
        print(f"  {note}")
    elif not assigned:
        print(f"  Przydziel: tf task weight {key} --apply")
    return 0


def spec_errors(root: Path, key: str) -> list[dict]:
    """Błędy spec.md zadania wg `spec_check.py` obok tego skryptu; pusta lista, gdy pliku albo skryptu nie ma."""
    script = Path(__file__).resolve().with_name("spec_check.py")
    if not script.is_file() or not (root / CHANGES / key / "spec.md").is_file():
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_spec_check", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = mod.check_task(root, key)
    return result["errors"] if result else []


def trace_errors(root: Path, key: str) -> list[dict]:
    """Błędy śladu kryterium → test wg `trace_check.py` obok tego skryptu; pusta lista, gdy zadanie nie ma spec.md,
    skryptu nie ma albo śladu nie da się policzyć (katalog poza gitem, brak gałęzi bazowej)."""
    script = Path(__file__).resolve().with_name("trace_check.py")
    if not script.is_file() or not (root / CHANGES / key / "spec.md").is_file():
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_trace_check", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = mod.trace(root, key)
    return result["errors"] if result else []


def flag_errors(root: Path, key: str) -> list[dict]:
    """Błędy flagi zadania wg `flag_check.py` obok tego skryptu; pusta lista, gdy skryptu nie ma."""
    script = Path(__file__).resolve().with_name("flag_check.py")
    if not script.is_file():
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_flag_check", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check(root, key)["errors"]


def cmd_flag(root: Path, key: str, action: str, value: str | None, remove_by: str | None, reason: str, by: str | None) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    if action == "set":
        if not value or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value):
            return fail("podaj klucz flagi (litery, cyfry, _ . -), np. proj_123_eksport_csv", 2)
        if remove_by and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", remove_by):
            return fail("data usunięcia flagi w formacie RRRR-MM-DD", 2)
        old = task.get("flag") if isinstance(task.get("flag"), dict) else {}
        task["flag"] = {"key": value, "remove_by": remove_by or old.get("remove_by"),
                        "allowed": old.get("allowed", {}) if old.get("key") == value else {}}
        msg = f"flaga {value}" + (f", do usunięcia do {task['flag']['remove_by']}" if task["flag"]["remove_by"] else "")
    elif action == "none":
        if not reason.strip():
            return fail("podaj powód: --reason \"bez flagi, bo …\"", 2)
        task["flag"] = {"none": " ".join(reason.split())}
        msg = f"bez flagi: {task['flag']['none']}"
    else:   # allow
        flag = task.get("flag") if isinstance(task.get("flag"), dict) else None
        if not flag or not flag.get("key"):
            return fail(f"zadanie nie ma flagi — najpierw: tf task flag {key} set <klucz>")
        if not value:
            return fail("podaj środowisko, np. tf task flag <KEY> allow prod --by human:<id>", 2)
        if not by or not by.startswith("human:") or not ACTOR.fullmatch(by):
            return fail("zgodę na włączenie flagi poza środowiskiem testowym zapisuje człowiek: --by human:<id>", 2)
        flag.setdefault("allowed", {})[value] = {"by": by, "at": now()}
        msg = f"flaga {flag['key']}: zgoda {by} na środowisko „{value}”"
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key}: {msg}")
    return 0


def cmd_stage(root: Path, key: str, stage: str, force: bool) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    was = task.get("stage", STAGES[0])
    if was in STAGES and STAGES.index(stage) < STAGES.index(was) and not force:
        return fail(f"etap {stage} jest wcześniejszy niż obecny ({was}); cofnięcie wymaga --force")
    if STAGES.index(stage) >= STAGES.index("plan") and not force:
        spec = spec_errors(root, key)
        if spec:
            return fail(f"do etapu {stage} przechodzi zadanie z gotową specyfikacją; do poprawy w spec.md: "
                        + "; ".join(f"linia {e['line']} {e['rule']} {e['message']}" for e in spec[:3])
                        + (f" (i {len(spec) - 3} więcej)" if len(spec) > 3 else "") + f". Całość: tf spec check {key}")
    if not force:
        refused = weight_gate(root, task, stage)
        if refused:
            return fail(refused)
    if stage in GATED and not force:
        open_ = [f"{k} ({s}{': ' + w if w else ''})" for k, (s, w) in slice_states(root, task).items() if s != "zweryfikowany"]
        if open_:
            return fail(f"do etapu {stage} przechodzi zadanie ze zweryfikowanymi kawałkami; brakuje: " + "; ".join(open_)
                        + f". Dowód: tf task verify {key} K<n> --files <pliki kawałka>")
        stale = [f"{n} ({s})" for n, (s, _) in artifact_states(root, task).items()
                 if s in ("nieaktualny", "zmieniony po zatwierdzeniu")]
        stale += [f"{rel} (zamrożony plik zmieniony)" for rel in frozen_changed(root, task)]
        missing = trace_errors(root, key)
        if missing:
            return fail(f"do etapu {stage} przechodzi zadanie, w którym każde kryterium ma test; do poprawy: "
                        + "; ".join(e["message"] for e in missing[:3])
                        + (f" (i {len(missing) - 3} więcej)" if len(missing) > 3 else "") + f". Całość: tf trace {key}")
        if stale:
            return fail(f"do etapu {stage} przechodzi zadanie z aktualnymi plikami; do odświeżenia: " + "; ".join(stale)
                        + f". Szczegóły: tf task check {key}")
    if STAGES.index(stage) >= STAGES.index("pr") and not force:
        bad = flag_errors(root, key)
        if bad:
            return fail(f"do etapu {stage} przechodzi zadanie z uporządkowaną flagą funkcji: "
                        + "; ".join(f"{e['rule']} {e['message']}" for e in bad) + f". Całość: tf flag check {key}")
    task["stage"], task["updated"] = stage, now()
    save(root, task)
    print(f"✓ {key}: {was} → {stage}")
    return 0


def task_rows(root: Path) -> list[dict]:
    """Wszystkie zadania ze stanem wyliczonym teraz (kawałki, pliki do odświeżenia)."""
    rows = []
    for f in sorted((root / CHANGES).glob("*/task.json")):
        t = load(root, f.parent.name)
        if not t:
            continue
        slices = {k: s for k, (s, _) in slice_states(root, t).items()}
        stale = [n for n, (s, _) in artifact_states(root, t).items() if s in ("nieaktualny", "zmieniony po zatwierdzeniu")]
        rows.append({"key": t.get("key", f.parent.name), "title": t.get("title", ""), "stage": t.get("stage", "?"),
                     "updated": t.get("updated", ""), "slices": slices,
                     "verified": sum(s == "zweryfikowany" for s in slices.values()), "stale": stale})
    return rows


def cmd_list(root: Path, as_json: bool) -> int:
    rows = task_rows(root)
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    if not rows:
        print(f"Brak zadań w {CHANGES}/. Pierwsze założysz: tf task start <KEY> --title \"<tytuł>\"")
        return 0
    for r in rows:
        print(f"{r['key']}  {r['stage']}  kawałki z dowodem {r['verified']}/{len(r['slices'])}  {r['title']}")
        for k, s in r["slices"].items():
            if s != "zweryfikowany":
                print(f"    {k}: {s}")
        for name in r["stale"]:
            print(f"    {name}: do odświeżenia (tf task check {r['key']})")
    return 0


def cmd_status(root: Path, key: str, as_json: bool) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
    states = slice_states(root, task)
    if as_json:
        print(json.dumps({**task, "slice_states": {k: s for k, (s, _) in states.items()},
                          "artifact_states": {n: s for n, (s, _) in artifact_states(root, task).items()}},
                         ensure_ascii=False, indent=1))
        return 0
    done = STAGES.index(task["stage"]) + 1 if task.get("stage") in STAGES else 0
    print(f"{task['key']} — {task.get('title', '')}\n"
          f"etap: {task.get('stage', '?')} ({done} z {len(STAGES)}) · waga: {task.get('weight', '?')} · "
          f"tryb: {task.get('mode', '?')} · zmieniono: {task.get('updated', '?')}")
    for k, (state, why) in states.items():
        title = (task["slices"][k].get("title") or "").strip()
        print(f"  {k}: {state}" + (f" — {title}" if title else "") + (f" ({why})" if why else ""))
    for n, (state, why) in artifact_states(root, task).items():
        print(f"  {n}: {state}" + (f" ({why})" if why else ""))
    flag = task.get("flag") if isinstance(task.get("flag"), dict) else None
    if flag and flag.get("key"):
        print(f"  flaga: {flag['key']}" + (f" (do usunięcia do {flag['remove_by']})" if flag.get("remove_by") else "")
              + (f" — zgoda na: {', '.join(sorted(flag['allowed']))}" if flag.get("allowed") else ""))
    elif flag and flag.get("none"):
        print(f"  flaga: brak — {flag['none']}")
    changed = set(frozen_changed(root, task))
    for rel in sorted(task.get("frozen") or {}):
        print(f"  {rel}: zamrożony" + (" — zmieniony bez decyzji człowieka" if rel in changed else ""))
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tf task", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("key")
    s.add_argument("--title", default=None)
    s.add_argument("--weight", default="zwykla")
    s.add_argument("--mode", default="zwykly")
    g = sub.add_parser("stage")
    g.add_argument("key")
    g.add_argument("stage")
    g.add_argument("--force", action="store_true")
    c = sub.add_parser("slice")
    c.add_argument("key")
    c.add_argument("slice_id")
    c.add_argument("state")
    c.add_argument("--title", default=None)
    c.add_argument("--reason", default=None)
    v = sub.add_parser("verify")
    v.add_argument("key")
    v.add_argument("slice_id")
    v.add_argument("--command", default=None)
    v.add_argument("--timeout", type=float, default=900)
    v.add_argument("--files", default="")
    r = sub.add_parser("artifact")
    r.add_argument("key")
    r.add_argument("name")
    r.add_argument("--stage", required=True)
    r.add_argument("--by", required=True)
    r.add_argument("--inputs", default="")
    o = sub.add_parser("approve")
    o.add_argument("key")
    o.add_argument("name")
    o.add_argument("--by", required=True)
    k = sub.add_parser("check")
    k.add_argument("key")
    w = sub.add_parser("weight")
    w.add_argument("key")
    w.add_argument("--apply", action="store_true")
    w.add_argument("--set", dest="new", default=None)
    w.add_argument("--by", default=None)
    w.add_argument("--reason", default="")
    w.add_argument("--json", action="store_true")
    fl = sub.add_parser("flag")
    fl.add_argument("key")
    fl.add_argument("action", choices=["set", "none", "allow"])
    fl.add_argument("value", nargs="?")
    fl.add_argument("--remove-by", default=None)
    fl.add_argument("--reason", default="")
    fl.add_argument("--by", default=None)
    fz = sub.add_parser("freeze")
    fz.add_argument("key")
    fz.add_argument("files")
    fz.add_argument("--by", required=True)
    ro = sub.add_parser("reopen")
    ro.add_argument("key")
    ro.add_argument("name")
    ro.add_argument("--by", required=True)
    ro.add_argument("--reason", default="")
    q = sub.add_parser("status")
    q.add_argument("key")
    q.add_argument("--json", action="store_true")
    ls = sub.add_parser("list")
    ls.add_argument("--json", action="store_true")
    try:
        a = ap.parse_args(argv[1:])
    except SystemExit as e:
        return 2 if e.code else 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if a.cmd == "list":
        return cmd_list(root, a.json)
    if not KEY.fullmatch(a.key):
        return fail(f"klucz „{a.key}” nie pasuje do wzorca (np. PROJ-123, CHG-12, T-20261113-limit)", 2)
    if a.cmd == "start":
        if not a.title or not a.title.strip():
            return fail("podaj tytuł: tf task start <KEY> --title \"<tytuł>\"", 2)
        if a.weight not in WEIGHTS:
            return fail(f"nieznana waga „{a.weight}” — do wyboru: {', '.join(WEIGHTS)}", 2)
        if a.mode not in MODES:
            return fail(f"nieznany tryb „{a.mode}” — do wyboru: {', '.join(MODES)}", 2)
        return cmd_start(root, a.key, a.title.strip(), a.weight, a.mode)
    if a.cmd == "stage":
        if a.stage not in STAGES:
            return fail(f"nieznany etap „{a.stage}” — kolejno: {', '.join(STAGES)}", 2)
        return cmd_stage(root, a.key, a.stage, a.force)
    if a.cmd == "check":
        return cmd_check(root, a.key)
    if a.cmd == "weight":
        if a.apply and a.new is not None:
            return fail("podaj jedno: --apply (propozycja fabryki) albo --set <waga>", 2)
        return cmd_weight(root, a.key, a.apply, a.new, a.by, a.reason, a.json)
    if a.cmd == "flag":
        return cmd_flag(root, a.key, a.action, a.value, a.remove_by, a.reason, a.by)
    if a.cmd in ("freeze", "reopen"):
        if not a.by.startswith("human:") or not ACTOR.fullmatch(a.by):
            return fail(f"{a.cmd} to decyzja człowieka: --by human:<id>", 2)
        if a.cmd == "freeze":
            files = [f.strip() for f in a.files.split(",") if f.strip()]
            return cmd_freeze(root, a.key, files, a.by) if files else fail("podaj pliki do zamrożenia", 2)
        if not a.reason.strip():
            return fail("podaj powód: --reason \"<dlaczego plik się zmienia>\"", 2)
        return cmd_reopen(root, a.key, a.name, a.by, " ".join(a.reason.split()))
    if a.cmd in ("artifact", "approve"):
        if not ACTOR.fullmatch(a.by):
            return fail(f"wykonawca „{a.by}” — oczekiwany zapis: <narzędzie>/<wersja>, human:<id> albo process:<id>", 2)
        if a.cmd == "approve":
            if not a.by.startswith("human:"):
                return fail("zatwierdza tylko człowiek: --by human:<id>", 2)
            return cmd_approve(root, a.key, a.name, a.by)
        if a.stage not in STAGES:
            return fail(f"nieznany etap „{a.stage}” — kolejno: {', '.join(STAGES)}", 2)
        return cmd_artifact(root, a.key, a.name, a.stage, a.by, [f.strip() for f in a.inputs.split(",") if f.strip()])
    if a.cmd in ("slice", "verify"):
        if not SLICE.fullmatch(a.slice_id):
            return fail(f"identyfikator kawałka „{a.slice_id}” — oczekiwany K1…K99", 2)
        if a.cmd == "slice":
            if a.state not in SLICE_STATES:
                return fail(f"nieznany stan „{a.state}” — do wyboru: {', '.join(SLICE_STATES)} "
                            "(zweryfikowany wynika z dowodu: tf task verify)", 2)
            return cmd_slice(root, a.key, a.slice_id, a.state, a.title, a.reason)
        files = [f.strip() for f in a.files.split(",") if f.strip()]
        if not files:
            return fail("podaj pliki kawałka: --files <plik>[,<plik>…] — bez nich dowód nie wiąże się z kodem", 2)
        command = a.command
        if not command:   # domyślnie to samo polecenie, którego pilnuje bramka jakości
            try:
                gate = json.loads((root / ".claude" / "quality-gate.json").read_text(encoding="utf-8")).get("command")
            except (OSError, ValueError, AttributeError):
                gate = None
            command = gate if isinstance(gate, str) else (" ".join(map(shlex.quote, gate)) if gate else None)
        if not command:
            return fail("nie ma czego uruchomić: podaj --command albo ustaw polecenie w .claude/quality-gate.json "
                        "(tf onboard --yes)", 2)
        return cmd_verify(root, a.key, a.slice_id, command, files, a.timeout)
    return cmd_status(root, a.key, a.json)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
