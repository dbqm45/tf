#!/usr/bin/env python3
"""
Stan przebiegu Talosa i podgląd (skill talos-story-run, tryb mode-talos): jedyny pisarz etapu i rundy w run.json
oraz generator dashboardu. Stan zapisuje skrypt, nie model — model tylko woła polecenie.

  python3 .claude/skills/talos-story-run/scripts/run_state.py stage <katalog-przebiegu> <etap> [--needs plan|stop]
        [--reason "<powód STOP>"] [--pr N] [--auto] [--effort low|medium|high]
  python3 .claude/skills/talos-story-run/scripts/run_state.py step <katalog-przebiegu> K2 R1 weryf fail
  python3 .claude/skills/talos-story-run/scripts/run_state.py step <katalog-przebiegu> PR plan_drift run
  python3 .claude/skills/talos-story-run/scripts/run_state.py verify <katalog-przebiegu> K2 --files <plik>[,<plik>…]
        [--command "<polecenie>"] [--timeout <s>]
  python3 .claude/skills/talos-story-run/scripts/run_state.py tick <katalog-przebiegu> K2
  python3 .claude/skills/talos-story-run/scripts/run_state.py park <katalog-przebiegu> "<sprawa do decyzji>"
  python3 .claude/skills/talos-story-run/scripts/run_state.py dashboard [--no-cost] [--out PLIK]

`stage` ustawia etap przebiegu: intake, plan, slices, pr, needs, done. Etap `needs` wymaga `--needs plan` (plan czeka
na akceptację) albo `--needs stop` (blok STOP; `--reason` to powód). `step` zapisuje wynik etapu pętli w rundzie
bieżącego kawałka: etapy test, kod, weryf, skan, zakres; stany run, pass, fail. Rundę zaczyna kolejna próba kawałka
po nieudanej bramce (R1, R2, …). Etapy wcześniejsze od zapisywanego, które nie mają stanu albo trwają, dostają pass —
Talos zgłasza tylko to, co zaczyna i czym kończy. Pierwszy `step` przenosi przebieg z intake/plan do slices, a po
decyzji człowieka (needs) wraca do slices. Cel `PR` zapisuje etapy plan_drift i pr.

`verify` zapisuje dowód kawałka: uruchamia polecenie weryfikacji (domyślnie to z `.claude/quality-gate.json`) przez
`tf task verify` i zapisuje wynik w `docs/project/changes/<KEY>/evidence/`. `tick` odhacza w plan.md tylko kawałek
z aktualnym dowodem, a etap `pr` przechodzi tylko wtedy, gdy każdy kawałek zadania go ma. Etap przebiegu trafia też
do `task.json` (intake → przyjecie, plan → plan, slices → realizacja, pr → pr). Przebieg w starym układzie (bez
zadania w run.json) dowodów nie zapisuje i odhacza jak dotąd.

`tick` odhacza kawałek w plan.md, `park` dopisuje sprawę na końcu parked.md — jedno polecenie z listy dozwolonych
zamiast `sed`, `>>` i heredoc w powłoce, o które Claude Code pyta człowieka (pomiar E0, 2026-11-13).

`launch` (wołane przez `run_report.py start`) buduje dashboard i otwiera go w przeglądarce; wyłączysz to w
`.claude/talos.json`: {"dashboard": false} (wcale) albo {"dashboard_open": false} (buduje, ale nie otwiera);
domyślnie oba włączone. Zmienne TALOS_DASHBOARD=0 i TALOS_DASHBOARD_OPEN=0 robią to samo bez pliku.

`dashboard` buduje samodzielny plik .tf/runs/talos/dashboard.html z wszystkich przebiegów w .tf/runs/<KEY>/ i starych
w .tf/runs/talos/ (ignorowany przez git razem z przebiegami): kolumny wg etapu, karty z rundami, panel plików. Koszt i czas liczy z transkryptów
(run_report.py) i zapamiętuje w run.json; `stage` i `step` odświeżają plik bez liczenia kosztu. Etap, którego nikt nie
zapisał, wynika z plan.md (kawałki odhaczone i nie) i report.md.
Zapis stanu służy podglądowi: błąd tego skryptu nie jest powodem do STOP przebiegu.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_report  # noqa: E402

STAGES = ("intake", "plan", "slices", "pr", "needs", "done")
STEPS = ("test", "kod", "weryf", "skan", "zakres")
STATES = ("run", "pass", "fail")
PR_STEPS = {"plan_drift": "drift", "pr": "pr"}
NEEDS = ("plan", "stop")
TASK_STAGE = {"intake": "przyjecie", "plan": "plan", "slices": "realizacja", "pr": "pr"}   # etap przebiegu → etap zadania
TASK_ORDER = ("przyjecie", "specyfikacja", "plan", "realizacja", "przeglad", "pr", "wdrozenie", "zamkniecie")
SLICE = re.compile(r"^\s*- \[([ xX])\]\s+(K\d+)\s*[—-]\s*(.+)$")
MAX_TEXT = 40000
MAX_RUNS = 40
TEMPLATE = HERE.parent / "templates" / "dashboard.html"
CONFIG = Path(".claude") / "talos.json"      # opcje trybu; plik osobisty, aktualizacja fabryki go nie rusza
DEFAULTS = {"dashboard": True, "dashboard_open": True}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_run(run_dir: Path) -> dict:
    return json.loads((run_dir / "run.json").read_text(encoding="utf-8"))


def write_run(run_dir: Path, meta: dict) -> None:
    """Zapis atomowy (plik tymczasowy i podmiana) — podgląd nigdy nie czyta połowy pliku."""
    meta["updated_at"] = now_iso()
    tmp = run_dir / "run.json.tmp"
    tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, run_dir / "run.json")


def fail(msg: str) -> int:
    print(f"✗ {msg}")
    return 2


def load(run_dir: Path) -> dict | None:
    try:
        return read_run(run_dir)
    except (OSError, ValueError):
        return None


# ---- zadanie (task.json pisze tylko `tf task`) -------------------------------------------------------------------

def sync_task(project: Path, run_dir: Path, meta: dict, stage: str) -> str | None:
    """Przenosi etap przebiegu do task.json (tylko do przodu). Zwraca odmowę wejścia do etapu `pr` (kawałek bez
    aktualnego dowodu, nieaktualny plik); inne niepowodzenia nie zatrzymują przebiegu."""
    key, target = meta.get("key"), TASK_STAGE.get(stage)
    if not key or not target:
        return None
    try:
        cur = json.loads((run_report.docs_dir(run_dir, meta) / "task.json").read_text(encoding="utf-8")).get("stage")
    except (OSError, ValueError, AttributeError):
        cur = None
    if cur in TASK_ORDER and TASK_ORDER.index(target) <= TASK_ORDER.index(cur):
        return None
    r = run_report.task_state(project, "stage", key, target)
    if r is not None and r.returncode != 0 and stage == "pr":
        return ((r.stdout + r.stderr).strip() or f"✗ zadanie {key} nie przeszło do etapu pr") \
            + f"\nDowód kawałka: run_state.py verify {run_dir} K<n> --files <pliki kawałka>"
    return None


def slice_evidence(project: Path, meta: dict, slice_id: str) -> str:
    """Stan kawałka wyliczony przez `tf task` (zweryfikowany, niezweryfikowany, czerwony…); bez wpisu — brak dowodu."""
    r = run_report.task_state(project, "status", meta["key"], "--json")
    try:
        return json.loads(r.stdout).get("slice_states", {}).get(slice_id) or "brak dowodu"
    except (AttributeError, ValueError):
        return "stan zadania nieczytelny"


def cmd_verify(run_dir: Path, slice_id: str, files: str, command: str | None, timeout: float | None, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if not meta.get("key"):
        return fail("ten przebieg jest w starym układzie (bez zadania), więc dowodów nie zapisuje — kawałek odhaczasz "
                    "przez `tick` jak dotąd.")
    args = ["verify", meta["key"], slice_id, "--files", files]
    if command:
        args += ["--command", command]
    if timeout:
        args += ["--timeout", str(timeout)]
    r = run_report.task_state(project, *args)
    if r is None:
        return fail("brak .tf/factory/task_state.py — zaktualizuj fabrykę (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    refresh(project)
    return r.returncode


# ---- zapis stanu -------------------------------------------------------------------------------------------------

def cmd_stage(run_dir: Path, stage: str, needs: str | None, reason: str | None, pr: int | None, auto: bool,
              effort: str | None, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if stage not in STAGES:
        return fail(f"etap „{stage}” nie istnieje; dozwolone: {', '.join(STAGES)}.")
    if stage == "needs" and needs not in NEEDS:
        return fail("etap needs wymaga `--needs plan` (plan czeka na akceptację) albo `--needs stop` (blok STOP).")
    if stage != "needs" and (needs or reason):
        return fail("`--needs` i `--reason` dotyczą tylko etapu needs.")
    refused = sync_task(project, run_dir, meta, stage)
    if refused:
        print(refused)
        return 2
    meta["stage"] = stage
    meta.pop("needs", None)
    meta.pop("stop_text", None)
    if stage == "needs":
        meta["needs"] = needs
        if needs == "stop" and reason:
            meta["stop_text"] = reason.strip()
    if pr is not None:
        meta["pr"] = pr
    if auto:
        meta["auto"] = True
    if effort:
        meta["effort"] = effort
    write_run(run_dir, meta)
    refresh(project)
    print(f"✓ etap: {stage}" + (f" ({needs})" if needs else ""))
    return 0


def cmd_step(run_dir: Path, target: str, rest: list[str], project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if target.upper() == "PR":
        if len(rest) != 2 or rest[0] not in PR_STEPS or rest[1] not in STATES:
            return fail(f"użycie: step <katalog> PR <{'|'.join(PR_STEPS)}> <{'|'.join(STATES)}>")
        entering = meta.get("stage") in (None, "intake", "plan", "slices", "needs")
        refused = sync_task(project, run_dir, meta, "pr") if entering else None
        if refused:
            print(refused)
            return 2
        steps = meta.setdefault("pr_steps", {})
        steps[PR_STEPS[rest[0]]] = rest[1]
        if entering:
            meta["stage"] = "pr"
            meta.pop("needs", None)
            meta.pop("stop_text", None)
        write_run(run_dir, meta)
        refresh(project)
        print(f"✓ PR: {rest[0]} = {rest[1]}")
        return 0
    if not re.fullmatch(r"K\d+", target) or len(rest) != 3 or not re.fullmatch(r"R[1-9]", rest[0]) \
            or rest[1] not in STEPS or rest[2] not in STATES:
        return fail(f"użycie: step <katalog> K<n> R<k> <{'|'.join(STEPS)}> <{'|'.join(STATES)}>")
    rnd, step, state = int(rest[0][1:]), rest[1], rest[2]
    cur = meta.get("current")
    if not isinstance(cur, dict) or cur.get("k") != target:
        cur = {"k": target, "rounds": []}      # nowy kawałek: rundy liczą się od R1
    rounds = cur.setdefault("rounds", [])
    while len(rounds) < rnd:
        rounds.append({s: "todo" for s in STEPS})
    row = rounds[rnd - 1]
    for earlier in STEPS[:STEPS.index(step)]:
        if row.get(earlier, "todo") in ("todo", "run"):
            row[earlier] = "pass"             # Talos zgłasza tylko początek i koniec — wcześniejsze przeszły
    row[step] = state
    for later in STEPS[STEPS.index(step) + 1:]:
        if state == "run" or row.get(later) not in STATES:
            row[later] = "todo"               # nowy start etapu unieważnia stany późniejszych
    meta["current"] = cur
    if meta.get("stage") in (None, "intake", "plan", "needs", "pr", "done"):
        sync_task(project, run_dir, meta, "slices")
        meta["stage"] = "slices"
        meta.pop("needs", None)
        meta.pop("stop_text", None)
    write_run(run_dir, meta)
    refresh(project)
    print(f"✓ {target} R{rnd}: {step} = {state}")
    return 0


# ---- odczyt stanu i dashboard ------------------------------------------------------------------------------------

def cmd_tick(run_dir: Path, slice_id: str, project: Path) -> int:
    """Odhacza kawałek w plan.md (`- [ ] K<n>` → `- [x] K<n>`); powtórzenie niczego nie zmienia. Przebieg z zadaniem
    odhacza tylko kawałek z aktualnym dowodem (`verify`)."""
    meta = load(run_dir) or {}
    path = run_report.docs_dir(run_dir, meta) / "plan.md"
    if not path.is_file():
        return fail(f"nie ma {path}")
    lines = path.read_text(encoding="utf-8").split("\n")
    for i, line in enumerate(lines):
        m = SLICE.match(line)
        if m and m.group(2) == slice_id and not m.group(3).lstrip().startswith("<"):   # nie wiersz szablonu
            if m.group(1) == " ":
                state = slice_evidence(project, meta, slice_id) if meta.get("key") else "zweryfikowany"
                if state != "zweryfikowany":
                    return fail(f"{slice_id} nie ma aktualnego dowodu ({state}) — najpierw: run_state.py verify "
                                f"{run_dir} {slice_id} --files <pliki kawałka>")
                lines[i] = line.replace("- [ ]", "- [x]", 1)
                path.write_text("\n".join(lines), encoding="utf-8")
            print(f"✓ {slice_id} odhaczony w {path.name}")
            refresh(project)
            return 0
    return fail(f"w {path.name} nie ma kawałka {slice_id}")


def cmd_park(run_dir: Path, item: str, project: Path) -> int:
    """Dopisuje sprawę odłożoną do decyzji człowieka na końcu parked.md (jeden wiersz)."""
    item = " ".join(item.split())
    if not item:
        return fail("pusta sprawa — podaj, co odkładasz i dlaczego")
    path = run_dir / "parked.md"
    if not run_dir.is_dir():
        return fail(f"nie ma katalogu przebiegu {run_dir}")
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    path.write_text(text.rstrip("\n") + ("\n" if text.strip() else "") + f"- {item.lstrip('- ')}\n", encoding="utf-8")
    print(f"✓ odłożono do decyzji w {path.name}")
    refresh(project)
    return 0


def parse_slices(run_dir: Path) -> list[dict]:
    path = run_report.docs_dir(run_dir) / "plan.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    out = []
    for line in text.splitlines():
        m = SLICE.match(line)
        if not m:
            continue
        value = m.group(3).split(" · ")[0].strip()
        if value.startswith("<"):               # wiersz z szablonu plan.md, jeszcze nie plan
            continue
        out.append({"id": m.group(2), "value": value, "checked": m.group(1) in "xX"})
    return out


def infer_stage(meta: dict, run_dir: Path, slices: list[dict]) -> str:
    if meta.get("stage") in STAGES:
        return meta["stage"]
    if (run_report.docs_dir(run_dir, meta) / "report.md").is_file():
        return "done"
    if not slices:
        return "intake"
    if all(s["checked"] for s in slices):
        return "pr"
    if any(s["checked"] for s in slices) or meta.get("current"):
        return "slices"
    return "plan"


def clip(text: str) -> str:
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT] + "\n…(ucięte)"


def read_text(path: Path) -> str | None:
    try:
        return clip(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None


def dot_for(text: str) -> str:
    if re.search(r"\bFAIL\b", text):
        return "bad"
    return "ok" if re.search(r"\bPASS\b", text) else "warn"


def file_groups(run_dir: Path, meta: dict, stage: str, needs: str | None, parked: list[str]) -> list[dict]:
    groups: list[dict] = []
    main = []
    docs = run_report.docs_dir(run_dir, meta)       # nowy układ: historyjka, plan i raport w katalogu zadania
    for path in (run_report.story_file(run_dir, meta), docs / "plan.md", run_dir / "parked.md"):
        name, text = path.name, read_text(path)
        if text is None:
            continue
        dot = "ok"
        if name == "plan.md":
            dot = "warn" if stage == "needs" and needs == "plan" else "ok"
        if name == "parked.md":
            dot = "warn" if parked else ""
        main.append({"name": name, "dot": dot, "text": text})
    if main:
        groups.append({"grp": "Przebieg", "items": main})
    sec_root = run_dir / "security"
    sec = []
    for f in sorted(sec_root.glob("**/summary.md")) if sec_root.is_dir() else []:
        text = read_text(f)
        if text is not None:
            sec.append({"name": f"security/{f.parent.relative_to(sec_root).as_posix()}/summary.md".replace("//", "/"),
                        "dot": dot_for(text), "text": text})
    if sec:
        groups.append({"grp": "Bezpieczeństwo", "items": sec})
    result = []
    if stage == "needs" and needs == "stop":
        cur = (meta.get("current") or {}).get("k")
        result.append({"name": "STOP", "dot": "bad", "text": "\n".join(
            [f"STOP — {cur or 'przebieg'}", f"Powód: {meta.get('stop_text') or '(brak opisu)'}",
             f"Wznowienie: od {cur or 'pierwszego nieodhaczonego kawałka'} w plan.md"])})
    report = read_text(docs / "report.md")
    if report is not None:
        result.append({"name": "report.md", "dot": "ok", "text": report})
    if result:
        groups.append({"grp": "Wynik", "items": result})
    if not groups:
        groups.append({"grp": "Przebieg", "items": [{"name": "run.json", "dot": "",
                                                       "text": json.dumps(meta, ensure_ascii=False, indent=1)}]})
    return groups


def normalize_rounds(cur: dict) -> list[dict]:
    rounds = []
    for r in cur.get("rounds") or []:
        rounds.append({s: (r.get(s) if r.get(s) in STATES else "todo") for s in STEPS})
    return rounds


def update_usage(run_dir: Path, meta: dict, project: Path) -> None:
    """Koszt, czas i modele z transkryptów (run_report.collect), zapamiętane w run.json (`usage`). Przebieg skończony
    z już policzonym kosztem nie jest liczony ponownie. Brak transkryptów nie jest błędem — karta nie pokaże kosztu."""
    if meta.get("stage") == "done" and isinstance(meta.get("usage"), dict):
        return
    since = run_report.parse_ts(meta.get("started_at", ""))
    if since is None:
        return
    try:
        data = run_report.collect(project, since, None)
    except OSError:
        return
    if not data or not data.get("requests"):
        return
    models = data["models"]
    meta["usage"] = {"cost_usd": round(sum(t.get("_cost", 0.0) for t in models.values()), 4),
                     "minutes": max(0, round((data["last"] - since).total_seconds() / 60)),
                     "models": sorted(models), "at": now_iso()}
    write_run(run_dir, meta)


def run_object(run_dir: Path, project: Path, costs: bool) -> dict | None:
    meta = load(run_dir)
    if meta is None:
        return None
    if costs:
        update_usage(run_dir, meta, project)
    slices = parse_slices(run_dir)
    stage = infer_stage(meta, run_dir, slices)
    needs = meta.get("needs") if stage == "needs" else None
    cur = meta.get("current") if isinstance(meta.get("current"), dict) else None
    out_slices = []
    first_open = next((s["id"] for s in slices if not s["checked"]), None)
    for s in slices:
        if s["checked"]:
            state = "done"
        elif cur and cur.get("k") == s["id"]:
            state = "fail" if stage == "needs" and needs == "stop" else "cur"
        elif not cur and stage == "slices" and s["id"] == first_open:
            state = "cur"
        else:
            state = "todo"
        out_slices.append({"id": s["id"], "value": s["value"], "state": state})
    parked = [ln[2:].strip() for ln in run_report.parked_items(run_dir)]
    m = re.match(r"(\d{4}-\d{2}-\d{2})-", run_dir.name)
    usage = meta.get("usage") if isinstance(meta.get("usage"), dict) else {}
    pr_steps = meta.get("pr_steps") or {}
    obj = {"slug": meta.get("slug") or run_dir.name, "title": meta.get("title") or run_dir.name,
           "date": m.group(1) if m else str(meta.get("started_at", ""))[:10],
           "stage": stage, "needs": needs, "auto": bool(meta.get("auto")), "effort": meta.get("effort"),
           "key": meta.get("task") or meta.get("key"), "change": meta.get("change"), "flag": meta.get("flag"), "pr": meta.get("pr"),
           "stopText": meta.get("stop_text"), "slices": out_slices, "parked": len(parked), "parkedList": parked,
           "cost": usage.get("cost_usd"), "min": usage.get("minutes"), "models": usage.get("models") or [],
           "started": meta.get("started_at", "")}
    if cur and stage in ("slices", "needs"):
        obj["cur"] = {"k": cur.get("k"), "rounds": normalize_rounds(cur) or [{s: "todo" for s in STEPS}]}
    if stage == "pr":
        obj["prSteps"] = {"drift": pr_steps.get("drift", "todo"), "pr": pr_steps.get("pr", "todo")}
    obj["files"] = file_groups(run_dir, meta, stage, needs, parked)
    return obj


def build_dashboard(project: Path, out: Path | None = None, costs: bool = True) -> Path:
    root = project / run_report.RUNS                # stary układ, przebiegi cięć i sam dashboard
    work = project / run_report.WORK                # nowy układ: .tf/runs/<KEY>/
    runs = []
    for d in sorted({*root.glob("*/run.json"), *work.glob("*/run.json")}):
        obj = run_object(d.parent, project, costs)
        if obj:
            runs.append(obj)
    runs.sort(key=lambda r: (r["date"], r["started"]), reverse=True)
    html = TEMPLATE.read_text(encoding="utf-8")
    data = json.dumps(runs[:MAX_RUNS], ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("/*RUNS_JSON*/[]", data, 1).replace("/*GENERATED*/", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    target = out or (root / "dashboard.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(html, encoding="utf-8")
    os.replace(tmp, target)
    return target


def options(project: Path) -> dict:
    """Opcje z `.claude/talos.json` (brak pliku albo klucza = domyślnie włączone); zmienne TALOS_DASHBOARD=0
    i TALOS_DASHBOARD_OPEN=0 wyłączają opcję bez edycji pliku."""
    opts = dict(DEFAULTS)
    try:
        data = json.loads((project / CONFIG).read_text(encoding="utf-8"))
        opts.update({k: bool(v) for k, v in data.items() if k in DEFAULTS})
    except (OSError, ValueError, AttributeError):
        pass
    for key, env in (("dashboard", "TALOS_DASHBOARD"), ("dashboard_open", "TALOS_DASHBOARD_OPEN")):
        if os.environ.get(env, "").strip().lower() in ("0", "false", "no", "off"):
            opts[key] = False
    if os.environ.get("CI"):          # CI i testy: bez otwierania przeglądarki
        opts["dashboard_open"] = False
    return opts


def launch(project: Path, open_browser: bool = True) -> str | None:
    """Start przebiegu: zbuduj dashboard i (gdy opcje i `open_browser` pozwalają) otwórz go w przeglądarce.
    Zwraca adres pliku albo None, gdy dashboard jest wyłączony. Błąd nigdy nie przerywa przebiegu."""
    opts = options(project)
    if not opts["dashboard"]:
        return None
    try:
        uri = build_dashboard(project, costs=False).resolve().as_uri()
    except Exception:  # noqa: BLE001 — podgląd nigdy nie psuje przebiegu
        return None
    if open_browser and opts["dashboard_open"]:
        try:
            webbrowser.open(uri)
        except Exception:  # noqa: BLE001 — brak przeglądarki (chmura, SSH) to nie błąd
            pass
    return uri


def refresh(project: Path) -> None:
    """Odświeżenie podglądu po zapisie stanu; bez liczenia kosztu, bez przerywania przebiegu przy błędzie."""
    try:
        build_dashboard(project, costs=False)
    except Exception:  # noqa: BLE001 — podgląd nigdy nie psuje przebiegu
        pass


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stage")
    s.add_argument("run_dir")
    s.add_argument("stage")
    s.add_argument("--needs", default=None)
    s.add_argument("--reason", default=None)
    s.add_argument("--pr", type=int, default=None)
    s.add_argument("--auto", action="store_true")
    s.add_argument("--effort", default=None, choices=["low", "medium", "high", "xhigh", "max"])
    t = sub.add_parser("step")
    t.add_argument("run_dir")
    t.add_argument("target")
    t.add_argument("rest", nargs="*")
    v = sub.add_parser("verify")
    v.add_argument("run_dir")
    v.add_argument("slice_id")
    v.add_argument("--files", default="")
    v.add_argument("--command", default=None)
    v.add_argument("--timeout", type=float, default=None)
    k = sub.add_parser("tick")
    k.add_argument("run_dir")
    k.add_argument("slice_id")
    p = sub.add_parser("park")
    p.add_argument("run_dir")
    p.add_argument("item")
    d = sub.add_parser("dashboard")
    d.add_argument("--no-cost", action="store_true")
    d.add_argument("--out", default=None)
    d.add_argument("--open", action="store_true", help="otwórz plik w przeglądarce")
    args = ap.parse_args(argv[1:])
    project = Path.cwd()
    if args.cmd == "stage":
        return cmd_stage(Path(args.run_dir), args.stage, args.needs, args.reason, args.pr, args.auto, args.effort,
                         project)
    if args.cmd == "step":
        return cmd_step(Path(args.run_dir), args.target, args.rest, project)
    if args.cmd == "verify":
        return cmd_verify(Path(args.run_dir), args.slice_id, args.files, args.command, args.timeout, project)
    if args.cmd == "tick":
        return cmd_tick(Path(args.run_dir), args.slice_id, project)
    if args.cmd == "park":
        return cmd_park(Path(args.run_dir), args.item, project)
    path = build_dashboard(project, Path(args.out) if args.out else None, costs=not args.no_cost)
    print(path.resolve().as_uri())
    if args.open:
        try:
            webbrowser.open(path.resolve().as_uri())
        except Exception:  # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
