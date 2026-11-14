#!/usr/bin/env python3
"""
Stan przebiegu zadania i podgląd (skill tf): jedyny pisarz etapu i rundy w run.json
oraz generator dashboardu. Stan zapisuje skrypt, nie model — model tylko woła polecenie.

  python3 .claude/skills/tf/scripts/run_state.py stage <katalog-przebiegu> <etap> [--needs plan|stop] [--code <kod>] [--auto|--plan]
  python3 .claude/skills/tf/scripts/run_state.py mode <katalog-przebiegu> [plan|zwykly|auto]   # tryb zadania
  python3 .claude/skills/tf/scripts/run_state.py approve <katalog-przebiegu>                   # zgoda człowieka na plan
  python3 .claude/skills/tf/scripts/run_state.py message <kod> [--json]                        # komunikat zatrzymania dla człowieka
        [--reason "<powód STOP>"] [--pr N] [--auto] [--effort low|medium|high]
  python3 .claude/skills/tf/scripts/run_state.py step <katalog-przebiegu> K2 R1 weryf fail
  python3 .claude/skills/tf/scripts/run_state.py step <katalog-przebiegu> PR plan_drift run
  python3 .claude/skills/tf/scripts/run_state.py spec <katalog-przebiegu> [new]
  python3 .claude/skills/tf/scripts/run_state.py flag <katalog-przebiegu> mode      # auto | manual
  python3 .claude/skills/tf/scripts/run_state.py flag <katalog-przebiegu> set <klucz> [--remove-by RRRR-MM-DD]
  python3 .claude/skills/tf/scripts/run_state.py flag <katalog-przebiegu> none --reason "bez flagi, bo …"
  python3 .claude/skills/tf/scripts/run_state.py trace <katalog-przebiegu> [--base <gałąź>]
  python3 .claude/skills/tf/scripts/run_state.py pr-body <katalog-przebiegu> [--base <gałąź>]   # opis PR do --body-file
  python3 .claude/skills/tf/scripts/run_state.py verify <katalog-przebiegu> K2 --files <plik>[,<plik>…]
        [--command "<polecenie>"] [--timeout <s>]
  python3 .claude/skills/tf/scripts/run_state.py tick <katalog-przebiegu> K2
  python3 .claude/skills/tf/scripts/run_state.py park <katalog-przebiegu> "<sprawa do decyzji>"
  python3 .claude/skills/tf/scripts/run_state.py block <katalog-przebiegu> K2 --question "<pytanie do człowieka>"
  python3 .claude/skills/tf/scripts/run_state.py answer <katalog-przebiegu> K2 "<odpowiedź>" --by human:<id>
  python3 .claude/skills/tf/scripts/run_state.py next <katalog-przebiegu>
  python3 .claude/skills/tf/scripts/run_state.py dashboard [--no-cost] [--out PLIK]

`stage` ustawia etap przebiegu: intake, plan, slices, pr, needs, done. Etap `needs` wymaga `--needs plan` (plan czeka
na akceptację) albo `--needs stop --code <kod>` (blok STOP; kod z zamkniętej listy `STOP_CODES`, `--reason` to powód
z dowodem; bez kodu albo z kodem spoza listy polecenie kończy się kodem 2 i wypisuje listę). `--auto` i `--plan`
zapisują tryb zadania (`tf task mode`): Plan kończy przebieg na planie, zwykły (domyślny) wpuszcza pętlę kawałka po
zgodzie człowieka na plan (`approve`), Auto — bez zgody, chyba że waga jest pełna. `step` zapisuje wynik etapu pętli w rundzie
bieżącego kawałka: etapy test, kod, weryf, skan, zakres; stany run, pass, fail. Rundę zaczyna kolejna próba kawałka
po nieudanej bramce (R1, R2). Trzeciej rundy skrypt odmawia: kawałek kończy się blokiem STOP, a po decyzji człowieka
(etap `needs`) dostaje dwie kolejne. Etapy wcześniejsze od zapisywanego, które nie mają stanu albo trwają, dostają pass —
pętla zgłasza tylko to, co zaczyna i czym kończy. Pierwszy `step` przenosi przebieg z intake/plan do slices, a po
decyzji człowieka (needs) wraca do slices. Cel `PR` zapisuje etapy plan_drift i pr.

`spec <katalog> new` zakłada szablon `spec.md` (dopiero wtedy, gdy pętla zaczyna specyfikację — po wczesnym STOP
w repozytorium nie zostaje pusty plik). `spec` sprawdza `spec.md` zadania (`tf spec check`): kryteria AC-n z Zakładając / Gdy / Wtedy, sekcje „Bez zmian”
i „Poza zakresem”, brak pytań [blokuje]. Etap `plan` (i każdy dalszy) jest odrzucany, dopóki specyfikacja ma błędy;
`stage plan` zapisuje też, z których plików powstał plan — zmiana `spec.md` po planie blokuje etap `pr`, dopóki
`stage plan` nie zostanie wywołane ponownie.

`flag mode` mówi, kto prowadzi flagi: `auto` (domyślnie — fabryka, po zapytaniu człowieka o nazwę) albo `manual`
(`feature_flags.auto: false` w `.tf/config/config.yaml` — człowiek dodaje flagi sam, pętla ich nie zakłada).
`flag` zapisuje flagę funkcji historyjki (`tf task flag`) albo jawny powód jej braku; bez tego, albo z flagą włączoną
poza środowiskiem testowym bez zgody człowieka, etap `pr` jest odrzucany. Zgody na inne środowisko pętla nie zapisuje.

`weight` pokazuje wagę zadania (lekka / zwykła / pełna) z powodem i skutkami. Wagę przydziela `run_report.py start`
z treści zgłoszenia, a etapy `intake` i `plan` ponawiają przydział (`tf task weight --apply`: tylko w górę, np. gdy
plan dotyka migracji; decyzji człowieka nie zmieniają); `weight --set <waga>` podnosi wagę, a obniżyć może tylko człowiek (`tf task weight … --by
human:<id>`). Zadanie o wadze lekkiej nie potrzebuje `spec.md`; zadanie o wadze pełnej nie wejdzie w pętlę kawałka
bez planu zatwierdzonego przez człowieka.

`trace` drukuje tabelę kryterium → test → commit → dowód (`tf trace --md`) do opisu PR; kryterium bez testu albo
test z `AC-n` spoza specyfikacji to kod 1 i odmowa etapu `pr`.

`pr-body` składa opis PR z plików zadania i zapisuje go w `<katalog-przebiegu>/pr-body.md`: historyjka, kawałki
z commitami, ślad kryteriów, **Jak sprawdzono** (dowody, skan, plan_drift), **Ryzyko** (waga i `tf risk`), **Jak
cofnąć** (karta operacyjna `deploy.rollback`, `git revert`, flaga), odłożone sprawy i założenia. Kawałek bez
zielonego dowodu jest w opisie nazwany wprost. Skrypt niczego nie wypycha i nie zakłada PR.

`verify` zapisuje dowód kawałka: uruchamia polecenie weryfikacji (domyślnie to z `.claude/quality-gate.json`) przez
`tf task verify` i zapisuje wynik w `docs/project/changes/<KEY>/evidence/`. `tick` odhacza w plan.md tylko kawałek
z aktualnym dowodem, a etap `pr` przechodzi tylko wtedy, gdy każdy kawałek zadania go ma. Etap przebiegu trafia też
do `task.json` (intake → przyjecie, plan → plan, slices → realizacja, pr → pr). Katalog przebiegu bez zadania w run.json
(stary układ cięć `.tf/runs/cuts/`) nie przyjmuje poleceń zadania (`spec`, `flag`, `verify`, `trace`, `mode`, `weight`,
`approve`) — polecenie mówi, jak zacząć cięcie od nowa.

`tick` odhacza kawałek w plan.md, `park` dopisuje sprawę na końcu parked.md — jedno polecenie z listy dozwolonych
zamiast `sed`, `>>` i heredoc w powłoce, o które Claude Code pyta człowieka (pomiar E0, 2026-11-13).

`block`, `answer` i `next` działają z przełącznikiem `loop.blocked_slices` (`.tf/config/config.yaml`, domyślnie
wyłączony): pytanie blokuje tylko swój kawałek (`block`), skrypt mówi, który kawałek można robić dalej (`Dalej: K3`
albo `Dalej: STOP`, gdy żaden nie jest niezależny), a `answer` zapisuje odpowiedź człowieka i odblokowuje kawałek.
Zależności kawałków zapisuje plan (`· po: K1`, `· po: brak`; bez dopisku — po poprzednim), pytania i odpowiedzi —
`events.jsonl` zadania (jeden wpis w wierszu: `at`, `type` — `question`
albo `answer`, `slice`, `text`, `by`; plik zapisuje decyzje, stanem przebiegu nie steruje). Z włączonym przełącznikiem STOP z kodem `pytanie` dla bieżącego kawałka
jest odrzucany, gdy został kawałek niezależny; pytanie o całe zadanie przechodzi z `--task`.

`launch` (wołane przez `run_report.py start`) buduje dashboard i otwiera go w przeglądarce; wyłączysz to w
`.claude/tf.json`: {"dashboard": false} (wcale) albo {"dashboard_open": false} (buduje, ale nie otwiera);
domyślnie oba włączone. Zmienne TF_DASHBOARD=0 i TF_DASHBOARD_OPEN=0 robią to samo bez pliku.

`dashboard` buduje samodzielny plik .tf/runs/dashboard.html z wszystkich przebiegów w .tf/runs/<KEY>/ i przebiegów cięć
w .tf/runs/cuts/ (ignorowany przez git razem z przebiegami): kolumny wg etapu, karty z rundami, panel plików. Koszt i czas liczy z transkryptów
(run_report.py) i zapamiętuje w run.json; `stage` i `step` odświeżają plik bez liczenia kosztu. Karta zadania
pokazuje etap z task.json i pasek kawałków; kawałek odhaczony, który stracił aktualny dowód, ma osobny stan (`stale`).
Zadanie bez przebiegu (samo `tf task`, świeży klon bez `.tf/runs/`) też dostaje kartę. Panel plików dzieli
pliki na katalog zadania (git), katalog roboczy i dowody. Etap, którego nikt nie
zapisał, wynika z plan.md (kawałki odhaczone i nie) i report.md.
Zapis stanu służy podglądowi: błąd tego skryptu nie jest powodem do STOP przebiegu.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
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
# Zamknięta lista kodów zatrzymań (`stage … needs --needs stop --code <kod>`): kod → co się stało, zwykłym zdaniem.
STOP_CODES = {
    "pytanie": "brakuje informacji, bez której nie da się zacząć",
    "podzial": "zadanie jest za duże albo łączy kilka akcji — trzeba je podzielić",
    "zrodlo": "nie ma treści zadania albo dostępu do zgłoszenia",
    "zgoda-na-plan": "plan czeka na zgodę człowieka",
    "testy": "testy albo weryfikacja nie przechodzą po dwóch próbach naprawy",
    "skan": "skan bezpieczeństwa blokuje po dwóch próbach",
    "budzet": "przekroczony budżet przebiegu",
    "srodowisko": "repozytorium nie jest gotowe (niezacommitowane zmiany, brak zdalnego repozytorium albo narzędzia)",
    "zaleznosc": "nowa zależność albo karencja wersji wymaga decyzji",
    "kontrakt": "zmiana kontraktu albo decyzja biznesowa (publiczne API, schemat danych, migracja)",
    "uprawnienia": "operacja zastrzeżona dla człowieka (produkcja, publikacja, flaga poza środowiskiem testowym)",
}
TASK_STAGE = {"intake": "przyjecie", "plan": "plan", "slices": "realizacja", "pr": "pr"}   # etap przebiegu → etap zadania
TASK_ORDER = ("przyjecie", "specyfikacja", "plan", "realizacja", "przeglad", "pr", "wdrozenie", "zamkniecie")
BARE_STAGE = {"przyjecie": "intake", "specyfikacja": "intake", "plan": "plan", "realizacja": "slices",
              "przeglad": "slices", "pr": "pr", "wdrozenie": "done", "zamkniecie": "done"}   # zadanie bez przebiegu
PROOF_STATE = {"zweryfikowany": "done", "czerwony": "fail", "zablokowany": "fail", "zaplanowany": "todo"}
_TASK_API = None
SLICE = re.compile(r"^\s*- \[([ xX])\]\s+(K\d+)\s*[—-]\s*(.+)$")
MAX_TEXT = 40000
MAX_RUNS = 40
MAX_ROUNDS = 2      # rundy jednego kawałka bez decyzji człowieka (pierwsza próba i jedna naprawa); potem blok STOP
TEMPLATE = HERE.parent / "templates" / "dashboard.html"
MESSAGES = HERE.parent / "templates" / "stop_messages.json"   # komunikaty zatrzymań dla człowieka, jeden na kod
CONFIG = Path(".claude") / "tf.json"         # opcje podglądu; plik osobisty, aktualizacja fabryki go nie rusza
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

def task_api(project: Path):
    """`task_state.py` silnika jako moduł — odczyt stanu zadań bez podprocesu na każdą kartę; None, gdy go nie ma."""
    global _TASK_API
    if _TASK_API is None:
        _TASK_API = False
        for base in (run_report.ROOT, project):
            f = base / ".tf" / "factory" / "task_state.py"
            if f.is_file():
                spec = importlib.util.spec_from_file_location("tf_task_state", f)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                _TASK_API = mod
                break
    return _TASK_API or None


def task_view(project: Path, key: str) -> dict | None:
    """Zadanie i wyliczone stany jego kawałków; None, gdy zadania nie ma albo nie da się go odczytać."""
    try:
        api = task_api(project)
        root = project.resolve()
        task = api.load(root, key) if api else None
        if not task:
            return None
        return {"task": task, "slices": {k: s for k, (s, _) in api.slice_states(root, task).items()}}
    except Exception:  # noqa: BLE001 — podgląd nigdy nie psuje przebiegu
        return None


def task_field(run_dir: Path, meta: dict, name: str) -> str | None:
    """Pole zadania z task.json (np. weight, mode); None, gdy przebieg nie ma zadania."""
    try:
        return json.loads((run_report.docs_dir(run_dir, meta) / "task.json").read_text(encoding="utf-8")).get(name)
    except (OSError, ValueError, AttributeError):
        return None


def task_weight(run_dir: Path, meta: dict) -> str | None:
    """Waga zadania (lekka / zwykla / pelna); None, gdy przebieg nie ma zadania."""
    return task_field(run_dir, meta, "weight")


def sync_task(project: Path, run_dir: Path, meta: dict, stage: str) -> str | None:
    """Przenosi etap przebiegu do task.json (tylko do przodu). Zwraca odmowę `tf task` (specyfikacja z błędami,
    kawałek bez aktualnego dowodu, nieaktualny plik) — to bramka, nie błąd podglądu."""
    key, target = meta.get("key"), TASK_STAGE.get(stage)
    if not key or not target:
        return None
    try:
        cur = json.loads((run_report.docs_dir(run_dir, meta) / "task.json").read_text(encoding="utf-8")).get("stage")
    except (OSError, ValueError, AttributeError):
        cur = None
    if TASK_ORDER.index(target) >= TASK_ORDER.index("plan") and task_weight(run_dir, meta) != "lekka" \
            and not (run_report.docs_dir(run_dir, meta) / "spec.md").is_file():
        return (f"✗ zadanie {key} nie ma jeszcze specyfikacji — załóż szablon: run_state.py spec {run_dir} new, "
                f"wypełnij go i sprawdź: run_state.py spec {run_dir}")
    if cur in TASK_ORDER and TASK_ORDER.index(target) <= TASK_ORDER.index(cur):
        return None
    r = run_report.task_state(project, "stage", key, target)
    if r is not None and r.returncode != 0:
        hint = (f"Flaga: run_state.py flag {run_dir} set <klucz> albo none --reason \"bez flagi, bo …\" · "
                f"specyfikacja: run_state.py spec {run_dir} · dowód kawałka: run_state.py verify {run_dir} K<n> "
                f"--files <pliki kawałka> · plan po zmianie specyfikacji: run_state.py stage {run_dir} plan")
        return ((r.stdout + r.stderr).strip() or f"✗ zadanie {key} nie przeszło do etapu {target}") + "\n" + hint
    return None


def register_plan(project: Path, run_dir: Path, meta: dict) -> None:
    """Zapisuje w task.json, z których plików powstał plan (skróty spec.md i ticket.md) — zmiana specyfikacji po
    planie oznacza plan jako nieaktualny, co wykrywa `tf task`, nie model."""
    docs = run_report.docs_dir(run_dir, meta)
    inputs = [n for n in ("spec.md", "ticket.md") if (docs / n).is_file()]
    if meta.get("key") and inputs and (docs / "plan.md").is_file():
        run_report.task_state(project, "artifact", meta["key"], "plan.md", "--stage", "plan", "--by", "process:tf",
                              "--inputs", ",".join(inputs))


def no_task(meta: dict) -> int:
    """Katalog przebiegu bez zadania (stary układ cięć `.tf/runs/cuts/`): poleceń zadania nie da się na nim wykonać."""
    again = f"/tf {meta['task']}" + (f" --change {meta['change']}" if meta.get("change") else "") if meta.get("task") \
        else "/tf <TSK-n>"
    return fail(f"ten katalog przebiegu jest w starym układzie (bez zadania) — zacznij cięcie od nowa: {again}")


def cmd_flag(run_dir: Path, action: str, value: str | None, remove_by: str | None, reason: str, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if not meta.get("key"):
        return no_task(meta)
    if action == "mode":
        r = run_report.engine(project, "flag_check.py", meta["key"], "--json")
        try:
            auto = json.loads(r.stdout).get("auto", True)
        except (AttributeError, ValueError):
            auto = True
        print("auto — fabryka prowadzi flagę historyjki; o nazwę zapytaj człowieka" if auto else
              "manual — flagi dodaje człowiek samodzielnie (feature_flags.auto: false); nie zakładasz flagi i jej nie zapisujesz")
        return 0
    args = ["flag", meta["key"], action, *([value] if value else [])]
    if remove_by:
        args += ["--remove-by", remove_by]
    if reason:
        args += ["--reason", reason]
    r = run_report.task_state(project, *args)
    if r is None:
        return fail("brak .tf/factory/task_state.py — zaktualizuj fabrykę (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    return r.returncode


def stop_message(code: str | None) -> dict | None:
    """Komunikat zatrzymania dla człowieka (prosty język): co, potrzeba, pytanie, opcje, potem. None, gdy go nie ma."""
    try:
        msg = json.loads(MESSAGES.read_text(encoding="utf-8")).get(code or "")
    except (OSError, ValueError, AttributeError):
        return None
    return msg if isinstance(msg, dict) and isinstance(msg.get("opcje"), list) else None


def message_lines(msg: dict, reason: str | None = None) -> list[str]:
    lines = [f"Co się stało: {msg.get('co', '')}"] + ([f"Szczegóły: {reason.strip()}"] if reason and reason.strip() else [])
    lines += [f"Czego potrzeba: {msg.get('potrzeba', '')}", f"Pytanie: {msg.get('pytanie', '')}"]
    for n, o in enumerate(msg.get("opcje") or [], 1):
        lines.append(f"  {n}. {o.get('opcja', '')} — {o.get('skutek', '')}" + (" (rekomendowana)" if o.get("rekomendowana") else ""))
    return lines + [f"Potem: {msg.get('potem', '')}"]


def cmd_message(code: str, as_json: bool) -> int:
    msg = stop_message(code) if code in STOP_CODES else None
    if msg is None:
        return fail(f"nie ma komunikatu dla kodu „{code}”. Kody: {', '.join(STOP_CODES)}.")
    print(json.dumps({"kod": code, **msg}, ensure_ascii=False, indent=1) if as_json else "\n".join(message_lines(msg)))
    return 0


def cmd_mode(run_dir: Path, new: str | None, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if not meta.get("key"):
        return no_task(meta)
    r = run_report.task_state(project, "mode", meta["key"], *([new] if new else []))
    if r is None:
        return fail("brak .tf/factory/task_state.py — zaktualizuj fabrykę (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    if r.returncode == 0 and new:
        mode = task_field(run_dir, meta, "mode")
        meta["auto"], meta["plan_only"] = mode == "auto", mode == "plan"
        write_run(run_dir, meta)
        refresh(project)
    return r.returncode


def human_id(project: Path) -> str:
    """Identyfikator człowieka do zapisu zgody: nazwa z gita (zmienna albo konfiguracja), inaczej użytkownik systemu."""
    name = os.environ.get("GIT_AUTHOR_NAME") or ""
    if not name:
        try:
            name = subprocess.run(["git", "config", "user.name"], cwd=project, capture_output=True, text=True,
                                  timeout=10).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            name = ""
    name = name or os.environ.get("USER") or os.environ.get("USERNAME") or "czlowiek"
    return "human:" + (run_report.slugify(name) or "czlowiek")


def cmd_approve(run_dir: Path, project: Path) -> int:
    """Zgoda człowieka na plan (i specyfikację, z której powstał). W trybie Auto nie ma człowieka — odmowa."""
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if not meta.get("key"):
        return no_task(meta)
    if task_field(run_dir, meta, "mode") == "auto":
        return fail("przebieg jest w trybie Auto — nie ma człowieka, który zatwierdziłby plan. Zgodę zapisujesz tylko "
                    "po odpowiedzi człowieka w rozmowie; wtedy najpierw: run_state.py mode <katalog> zwykly.")
    r = run_report.task_state(project, "approve", meta["key"], "plan.md", "--by", human_id(project))
    if r is None:
        return fail("brak .tf/factory/task_state.py — zaktualizuj fabrykę (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    return 0 if r.returncode == 0 else 2


def cmd_weight(run_dir: Path, new: str | None, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if not meta.get("key"):
        return no_task(meta)
    r = run_report.task_state(project, "weight", meta["key"], *(["--set", new] if new else ["--apply"]))
    if r is None:
        return fail("brak .tf/factory/task_state.py — zaktualizuj fabrykę (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    return r.returncode


def cmd_trace(run_dir: Path, base: str | None, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if not meta.get("key"):
        return no_task(meta)
    r = run_report.engine(project, "trace_check.py", meta["key"], "--md", *(["--base", base] if base else []))
    if r is None:
        return fail("brak .tf/factory/trace_check.py — zaktualizuj fabrykę (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    return r.returncode


def cmd_spec(run_dir: Path, project: Path, new: bool = False) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if not meta.get("key"):
        return no_task(meta)
    r = run_report.engine(project, "spec_check.py", "new" if new else "check", meta["key"])
    if r is None:
        return fail("brak .tf/factory/spec_check.py — zaktualizuj fabrykę (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    return r.returncode


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
        return no_task(meta)
    args = ["verify", meta["key"], slice_id, "--files", files]
    if command:
        args += ["--command", command]
    if timeout:
        args += ["--timeout", str(timeout)]
    r = run_report.task_state(project, *args)
    if r is None:
        return fail("brak .tf/factory/task_state.py — zaktualizuj fabrykę (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    for line in criterion_hints(project, run_dir, meta, files):
        print(line)
    refresh(project)
    return r.returncode


TEST_FILE = re.compile(r"(^|/)(tests?|__tests__|e2e|spec)/|\.(test|spec)\.|(^|/)test_[^/]*\.py$|_test\.(py|go)$|"
                       r"(Test|Tests)\.(java|cs)$")          # te same wzorce co w śladzie kryteriów (trace_check.py)
CRITERION = re.compile(r"\bAC[-_ ]?\d+\b", re.I)


def criterion_hints(project: Path, run_dir: Path, meta: dict, files: str) -> list[str]:
    """Ostrzeżenia przy weryfikacji kawałka zadania ze specyfikacją: test bez identyfikatora kryterium (`AC-n`) albo
    brak pliku testu wśród plików kawałka. Dopisanie teraz trafia do commita kawałka, a nie do osobnego commita."""
    if not (run_report.docs_dir(run_dir, meta) / "spec.md").is_file():
        return []
    tests = [f.strip() for f in files.split(",") if f.strip() and TEST_FILE.search(f.strip())]
    if not tests:
        return ["⚠ wśród plików kawałka nie ma pliku testu — dodaj go do `--files`, inaczej kryterium nie będzie miało "
                "dowodu w śladzie (etap pr zostanie odrzucony)"]
    bare = []
    for rel in tests:
        try:
            text = (project / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not CRITERION.search(text):
            bare.append(rel)
    if bare:
        return [f"⚠ test bez identyfikatora kryterium: {', '.join(bare)} — dopisz AC-n w nazwie albo komentarzu testu "
                "teraz, przed commitem kawałka (i powtórz verify); dopisywanie później to osobny commit"]
    return []


# ---- zapis stanu -------------------------------------------------------------------------------------------------

def cmd_stage(run_dir: Path, stage: str, needs: str | None, reason: str | None, pr: int | None, auto: bool,
              effort: str | None, project: Path, plan_mode: bool = False, code: str | None = None,
              whole_task: bool = False) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if stage not in STAGES:
        return fail(f"etap „{stage}” nie istnieje; dozwolone: {', '.join(STAGES)}.")
    if stage == "needs" and needs not in NEEDS:
        return fail("etap needs wymaga `--needs plan` (plan czeka na akceptację) albo `--needs stop` (blok STOP).")
    if stage != "needs" and (needs or reason or code):
        return fail("`--needs`, `--code` i `--reason` dotyczą tylko etapu needs.")
    if auto and plan_mode:
        return fail("podaj jeden tryb: `--plan` (koniec na planie) albo `--auto` (bez zatwierdzania planu).")
    codes = "; ".join(f"{k} — {v}" for k, v in STOP_CODES.items())
    if stage == "needs" and needs == "stop" and code not in STOP_CODES:
        return fail(("blok STOP wymaga kodu z listy" if not code else f"kod zatrzymania „{code}” nie istnieje")
                    + f": `--needs stop --code <kod> --reason \"<powód z dowodem>\"`. Kody: {codes}.")
    if code and needs != "stop":
        return fail("`--code` dotyczy tylko `--needs stop`.")
    if code == "pytanie" and not whole_task and meta.get("key") and blocked_slices_enabled(project):
        cur_k = (meta.get("current") or {}).get("k") if meta.get("stage") == "slices" else None
        slices, blocked = plan_and_blocked(project, run_dir, meta)
        open_cur = cur_k and cur_k not in blocked and any(s["id"] == cur_k and not s["checked"] for s in slices)
        other = next_slice(slices, blocked | {cur_k}) if open_cur else None
        if other:       # pytanie o jeden kawałek nie zatrzymuje całości, gdy jest co robić dalej
            return fail(f"pytanie dotyczy kawałka {cur_k}, a {other['id']} od niego nie zależy — zablokuj tylko {cur_k}: "
                        f"run_state.py block {run_dir} {cur_k} --question \"<pytanie>\" i rób {other['id']}. Gdy pytanie "
                        "dotyczy całego zadania, dodaj `--task`.")
    if (auto or plan_mode) and meta.get("key"):               # tryb zadania wybiera człowiek w poleceniu /tf
        m = run_report.task_state(project, "mode", meta["key"], "auto" if auto else "plan")
        if m is not None and "—" in m.stdout:                  # np. Auto przy wadze pełnej: zostaje tryb zwykły
            print(m.stdout.strip())
    if stage in ("intake", "plan") and meta.get("key"):      # waga: ponowny przydział (tylko w górę) po treści i planie
        before = task_weight(run_dir, meta)
        w = run_report.task_state(project, "weight", meta["key"], "--apply")
        if w is not None and w.returncode == 0 and task_weight(run_dir, meta) != before:
            print("Waga zadania zmieniona — " + " ".join(ln.strip() for ln in w.stdout.splitlines()[:3] if ln.strip()))
    refused = sync_task(project, run_dir, meta, stage)
    if refused:
        print(refused)
        return 2
    if stage == "plan":
        register_plan(project, run_dir, meta)
    meta["stage"] = stage
    meta.pop("needs", None)
    meta.pop("stop_text", None)
    meta.pop("stop_code", None)
    meta.pop("needs_at", None)
    if stage == "needs":
        meta["needs"] = needs
        meta["needs_at"] = now_iso()                # od kiedy zadanie czeka na człowieka (lista „Czeka na Ciebie”)
        if needs == "stop":
            meta["stop_code"] = code
            if reason:
                meta["stop_text"] = reason.strip()
    if pr is not None:
        meta["pr"] = pr
    if auto:
        meta["auto"] = True
    if plan_mode:
        meta["plan_only"] = True
    if effort:
        meta["effort"] = effort
    write_run(run_dir, meta)
    refresh(project)
    print(f"✓ etap: {stage}" + (f" ({needs})" if needs else ""))
    if stage == "plan" and meta.get("key") and blocked_slices_enabled(project):
        print("Zależności kawałków: dopisz w wierszu kawałka `· po: K<n>` (po którym można go zacząć) albo `· po: brak` "
              "(niezależny); bez dopisku kawałek zależy od poprzedniego. Dzięki temu pytanie w jednym kawałku nie "
              "zatrzyma pozostałych.")
    msg = stop_message(code) if needs == "stop" else None
    if msg:     # komunikat dla człowieka: pętla pokazuje go zamiast własnego opisu
        print("Komunikat dla człowieka — pokaż go z dowodem (polecenie i wynik); w rozmowie pytanie zadaj narzędziem "
              "AskUserQuestion z tymi opcjami, w przebiegu bez nadzoru wpisz go do raportu:")
        print("\n".join(message_lines(msg, reason)))
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
    limit = cur.get("limit") or MAX_ROUNDS
    if rnd > limit and meta.get("stage") == "needs":
        limit = cur["limit"] = len(rounds) + MAX_ROUNDS     # człowiek zdecydował po STOP: kolejne próby
    if rnd > limit:                                         # limitu rund pilnuje skrypt, nie deklaracja modelu
        return fail(f"{target} miał już {limit} rundy — kolejna zaczyna się dopiero po decyzji człowieka. Zakończ "
                    f"blokiem STOP: run_state.py stage {run_dir} needs --needs stop --code <kod> --reason \"<powód "
                    "z dowodem>\" (kod: testy — weryfikacja czerwona, skan — skan blokuje, pytanie — ustalenie "
                    "przeglądu, którego nie da się usunąć w zakresie kawałka).")
    while len(rounds) < rnd:
        rounds.append({s: "todo" for s in STEPS})
    row = rounds[rnd - 1]
    for earlier in STEPS[:STEPS.index(step)]:
        if row.get(earlier, "todo") in ("todo", "run"):
            row[earlier] = "pass"             # pętla zgłasza tylko początek i koniec — wcześniejsze przeszły
    row[step] = state
    for later in STEPS[STEPS.index(step) + 1:]:
        if state == "run" or row.get(later) not in STATES:
            row[later] = "todo"               # nowy start etapu unieważnia stany późniejszych
    meta["current"] = cur
    if meta.get("stage") in (None, "intake", "plan", "needs", "pr", "done"):
        refused = sync_task(project, run_dir, meta, "slices")
        if refused:
            print(refused)
            return 2
        meta["stage"] = "slices"
        for name in ("needs", "stop_text", "stop_code", "needs_at"):
            meta.pop(name, None)
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


# ---- pytania i zależności kawałków (krok F3, przełącznik loop.blocked_slices) ---------------------------------
NO_DEPS = ("brak", "-", "—", "–", "nic")
HUMAN = re.compile(r"human:[\w.@-]+")


def blocked_slices_enabled(project: Path) -> bool:
    """`loop.blocked_slices`: domyślna silnika z nadpisaniem projektu; bez konfiguracji — wyłączone."""
    for base in (next((p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "packs.py").is_file()),
                      project), project):
        try:
            spec = importlib.util.spec_from_file_location("tf_packs_cfg", base / ".tf" / "factory" / "packs.py")
            packs = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(packs)
            cfg = packs.load_yaml(base / ".tf" / "factory" / "config.yaml")
            own = project / ".tf" / "config" / "config.yaml"
            if own.is_file():
                cfg = packs.deep_merge(cfg, packs.load_yaml(own))
            return (cfg.get("loop") or {}).get("blocked_slices") is True
        except Exception:  # noqa: BLE001 — brak konfiguracji to ustawienie domyślne, nie awaria
            continue
    return False


def plan_with_deps(text: str) -> list[dict]:
    """Kawałki planu w kolejności: `id`, `checked`, `value` i `deps` — lista kawałków, po których można zacząć."""
    out: list[dict] = []
    for line in text.splitlines():
        m = SLICE.match(line)
        if not m or m.group(3).lstrip().startswith("<"):      # wiersz szablonu planu nie jest kawałkiem
            continue
        parts = [p.strip() for p in m.group(3).split("·")]
        deps: list[str] | None = None
        for part in parts[1:]:
            k, _, v = part.partition(":")
            if k.strip().lower() == "po":
                names = [x.strip().strip("`") for x in v.split(",") if x.strip()]
                deps = [] if any(n.lower() in NO_DEPS for n in names) else [n.upper() for n in names if re.fullmatch(r"[Kk]\d+", n)]
        if deps is None:                                       # bez dopisku: po poprzednim kawałku
            deps = [out[-1]["id"]] if out else []
        out.append({"id": m.group(2), "checked": m.group(1) != " ", "value": parts[0], "deps": deps})
    return out


def next_slice(slices: list[dict], blocked: set[str]) -> dict | None:
    """Pierwszy nieodhaczony i niezablokowany kawałek, którego wszystkie zależności są odhaczone."""
    done = {s["id"] for s in slices if s["checked"]}
    for s in slices:
        if not s["checked"] and s["id"] not in blocked and all(d in done for d in s["deps"]):
            return s
    return None


def held_slices(slices: list[dict], blocked: set[str]) -> list[tuple[str, list[str]]]:
    """Nieodhaczone kawałki, które czekają na inne: (kawałek, nieodhaczone zależności)."""
    done = {s["id"] for s in slices if s["checked"]}
    return [(s["id"], [d for d in s["deps"] if d not in done]) for s in slices
            if not s["checked"] and s["id"] not in blocked and any(d not in done for d in s["deps"])]


def append_event(task_dir: Path, kind: str, slice_id: str, text: str, by: str) -> dict:
    """Dopisuje wpis do events.jsonl zadania i go zwraca."""
    event = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "type": kind, "slice": slice_id,
             "text": " ".join(text.split()), "by": by}
    with (task_dir / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def plan_and_blocked(project: Path, run_dir: Path, meta: dict) -> tuple[list[dict], set[str]]:
    """Kawałki planu z zależnościami i zbiór kawałków zablokowanych pytaniem (z task.json)."""
    try:
        text = (run_report.docs_dir(run_dir, meta) / "plan.md").read_text(encoding="utf-8")
    except OSError:
        text = ""
    view = task_view(project, meta["key"]) if meta.get("key") else None
    blocked = {k for k, s in (view["slices"] if view else {}).items() if s == "zablokowany"}
    return plan_with_deps(text), blocked


def print_next(project: Path, run_dir: Path, meta: dict) -> None:
    """`Dalej: K<n>` — kawałek, który można robić; `Dalej: STOP` — gdy każdy czeka na odpowiedź człowieka."""
    slices, blocked = plan_and_blocked(project, run_dir, meta)
    nxt = next_slice(slices, blocked)
    if nxt:
        print(f"Dalej: {nxt['id']} — {nxt['value']}")
        return
    if not blocked:
        print("Dalej: zakończenie — wszystkie kawałki planu są odhaczone." if slices and all(s["checked"] for s in slices)
              else "Dalej: brak kawałka do zrobienia — sprawdź plan.md.")
        return
    view = task_view(project, meta["key"]) or {"task": {}}
    asked = {k: ((view["task"].get("slices") or {}).get(k) or {}).get("reason") or "(bez treści pytania)"
             for k in sorted(blocked, key=lambda x: int(x[1:]))}
    print("Dalej: STOP — każdy pozostały kawałek czeka na odpowiedź człowieka.")
    for k, q in asked.items():
        print(f"  {k}: {q}")
    for k, deps in held_slices(slices, blocked):
        print(f"  {k} czeka na {', '.join(deps)}")
    print(f"Zakończ blokiem STOP: run_state.py stage {run_dir} needs --needs stop --code pytanie --reason "
          f"\"{'; '.join(f'{k}: {q}' for k, q in asked.items())}\"")


def cmd_block(run_dir: Path, slice_id: str, question: str, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if not meta.get("key"):
        return no_task(meta)
    if not blocked_slices_enabled(project):
        return fail("przełącznik `loop.blocked_slices` jest wyłączony (.tf/config/config.yaml) — pytanie kończy przebieg "
                    f"blokiem STOP: run_state.py stage {run_dir} needs --needs stop --code pytanie --reason \"<pytanie>\".")
    question = " ".join(question.split())
    slices, blocked = plan_and_blocked(project, run_dir, meta)
    found = next((s for s in slices if s["id"] == slice_id), None)
    if not question or found is None or found["checked"]:
        return fail(f"podaj pytanie i nieodhaczony kawałek z plan.md (jest: {', '.join(s['id'] for s in slices) or 'brak'}).")
    r = run_report.task_state(project, "slice", meta["key"], slice_id, "blocked", "--reason", question)
    if r is None or r.returncode != 0:
        return fail(((r.stdout + r.stderr).strip() if r else "brak .tf/factory/task_state.py — zaktualizuj fabrykę (tf update)."))
    if slice_id not in blocked:
        append_event(run_report.docs_dir(run_dir, meta), "question", slice_id, question, "process:tf")
    refresh(project)
    print(f"✓ {slice_id} czeka na odpowiedź człowieka: {question}")
    print_next(project, run_dir, meta)
    return 0


def cmd_answer(run_dir: Path, slice_id: str, text: str, by: str | None, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if not meta.get("key"):
        return no_task(meta)
    if not by or not HUMAN.fullmatch(by):
        return fail("odpowiedź zapisujesz z identyfikatorem człowieka, który jej udzielił: --by human:<id>.")
    text = " ".join(text.split())
    _, blocked = plan_and_blocked(project, run_dir, meta)
    if not text or slice_id not in blocked:
        return fail(f"podaj odpowiedź i kawałek, który czeka na człowieka (czekają: {', '.join(sorted(blocked)) or 'żaden'}).")
    r = run_report.task_state(project, "slice", meta["key"], slice_id, "planned")
    if r is None or r.returncode != 0:
        return fail(((r.stdout + r.stderr).strip() if r else "brak .tf/factory/task_state.py — zaktualizuj fabrykę (tf update)."))
    append_event(run_report.docs_dir(run_dir, meta), "answer", slice_id, text, by)
    if meta.get("stage") == "needs" and meta.get("stop_code") == "pytanie" and blocked == {slice_id}:
        meta["stage"] = "slices"            # ostatnie pytanie ma odpowiedź: przebieg już na nikogo nie czeka
        for name in ("needs", "stop_text", "stop_code", "needs_at"):
            meta.pop(name, None)
        write_run(run_dir, meta)
    refresh(project)
    print(f"✓ {slice_id} odblokowany — odpowiedź zapisana ({by}).")
    print_next(project, run_dir, meta)
    return 0


def cmd_next(run_dir: Path, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if not meta.get("key"):
        return no_task(meta)
    print_next(project, run_dir, meta)
    return 0


# --- opis PR składany z plików zadania (krok G2) -------------------------------------------------------------------
WEIGHT_PL = {"lekka": "lekka", "zwykla": "zwykła", "pelna": "pełna"}
CARD = Path(".tf") / "config" / "operations.json"
ASSUMPTION = re.compile(r"\[zało[żz]eni", re.I)
BASES = ("origin/main", "main", "origin/master", "master")


def as_data(value, limit: int = 600) -> str:
    """Tekst z plików zadania i z karty operacyjnej wstawiany do opisu PR: jedna linia bez znaków nagłówka i listy na
    początku — treść jest danymi, nie strukturą opisu. Wzmianka `@nazwa` trafia do kodu (nikogo nie powiadamia),
    a obraz staje się zwykłym odnośnikiem (opis nie pobiera niczego z obcego adresu)."""
    text = re.sub(r"^(?:[#>]+\s*|[-*+]\s+)+", "", " ".join(str(value).split()))
    text = re.sub(r"(?<![`\w])@([A-Za-z0-9][\w/-]*)", r"`@\1`", text.replace("![", "["))
    return text[:limit] + ("…" if len(text) > limit else "")


def code_span(value) -> str:
    text = " ".join(str(value).split())
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def pick_base(project: Path, base: str | None) -> str | None:
    """Gałąź bazowa do listy commitów: podana, a bez niej pierwsza istniejąca z typowych; None, gdy git jej nie zna."""
    for cand in ([base] if base else BASES):
        try:
            r = subprocess.run(["git", "-C", str(project), "rev-parse", "--verify", "--quiet", f"{cand}^{{commit}}"],
                               capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            return None
        if r.returncode == 0:
            return cand
    return None


def slice_commits(project: Path, base: str) -> dict[str, str]:
    """Kawałek → najnowszy commit ze stopką „Kawałek K<n>” na gałęzi (skrót i tytuł)."""
    try:
        r = subprocess.run(["git", "-C", str(project), "log", "--format=%h%x1f%s%x1f%b%x1e", f"{base}..HEAD"],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return {}
    out: dict[str, str] = {}
    for rec in (r.stdout.split("\x1e") if r.returncode == 0 else []):
        parts = rec.strip("\n").split("\x1f")
        if len(parts) == 3:
            for k in re.findall(r"^Kawałek (K\d+)\b", parts[2], re.M):
                out.setdefault(k, f"{parts[0]} {parts[1]}")
    return out


def last_evidence(docs: Path) -> dict[str, tuple[str, dict]]:
    """Kawałek → (ścieżka względna, treść) ostatniego dowodu `evidence/K<n>-<m>.json`."""
    best: dict[str, tuple[int, Path]] = {}
    for f in docs.glob("evidence/K*-*.json"):
        m = re.fullmatch(r"(K\d+)-(\d+)\.json", f.name)
        if m and int(m.group(2)) >= best.get(m.group(1), (0, f))[0]:
            best[m.group(1)] = (int(m.group(2)), f)
    out = {}
    for k, (_, f) in best.items():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = None
        out[k] = (f"evidence/{f.name}", data if isinstance(data, dict) else {})
    return out


def scan_status(run_dir: Path, slice_id: str) -> str | None:
    """Werdykt skanu bezpieczeństwa kawałka (ostatnia próba); None, gdy skanu nie było albo wynik jest nieczytelny."""
    base = run_dir / "security" / slice_id
    tries = sorted(base.glob("proba-*/verdict.json"), key=lambda f: int(re.sub(r"\D", "", f.parent.name) or 0))
    try:
        status = json.loads((tries[-1] if tries else base / "verdict.json").read_text(encoding="utf-8")).get("status")
    except (OSError, ValueError, AttributeError):
        return None
    return status if isinstance(status, str) and re.fullmatch(r"[A-Z]{2,12}", status) else None


def rollback_steps(project: Path) -> list[str]:
    """Kroki cofnięcia wdrożenia z karty operacyjnej (`deploy.rollback`: tekst albo lista); bez karty — pusta lista."""
    try:
        card = json.loads((project / CARD).read_text(encoding="utf-8"))
        value = card["deploy"]["rollback"]
    except (OSError, ValueError, KeyError, TypeError):
        return []
    lines = value.splitlines() if isinstance(value, str) else value if isinstance(value, list) else []
    return [s for s in (as_data(x) for x in lines if isinstance(x, str)) if s][:10]


def engine_md(project: Path, name: str, *args: str) -> str | None:
    """Wyjście skryptu silnika do wklejenia pod własny nagłówek: jego nagłówki stają się pogrubieniem."""
    r = run_report.engine(project, name, *args)
    text = (r.stdout if r is not None else "").strip("\n")
    if r is None or not text:
        return None
    return "\n".join(f"**{ln.lstrip('# ').strip()}**" if ln.startswith("#") else ln for ln in text.splitlines())


def pr_body(run_dir: Path, meta: dict, project: Path, base: str | None) -> tuple[str, list[str]]:
    """Opis PR i lista kawałków bez zielonego dowodu."""
    key, docs = meta["key"], run_report.docs_dir(run_dir, meta)
    view = task_view(project, key) or {"task": {}, "slices": {}}
    task, states = view["task"], view["slices"]
    slices, proofs = parse_slices(run_dir), last_evidence(docs)
    found = pick_base(project, base)
    commits = slice_commits(project, found) if found else {}
    base_args = ["--base", found] if found else []

    ticket = read_text(docs / "ticket.md") or ""
    source = next((ln for ln in ticket.splitlines() if ln.startswith("Źródło:")), None)
    out = ["## Historyjka", "", f"**{as_data(meta.get('title') or task.get('title') or key, 200)}** ({code_span(key)})", ""]
    if source:
        out.append(f"- {as_data(source, 300)}")
    if meta.get("change") or task.get("change"):
        out.append(f"- Zmiana pdi: {as_data(meta.get('change') or task.get('change'), 40)}"
                   + (f", cięcie {as_data(meta['task'], 40)}" if meta.get("task") else ""))
    try:
        rel_docs = docs.resolve().relative_to(project.resolve()).as_posix()
    except ValueError:
        rel_docs = str(docs)
    out.append(f"- Pliki zadania: `{rel_docs}/` (zgłoszenie, specyfikacja, plan, dowody)")

    out += ["", "## Kawałki", ""]
    for s in slices:
        out.append(f"- [{'x' if s['checked'] else ' '}] **{s['id']}** — {as_data(s['value'], 200)} · stan: "
                   f"{states.get(s['id'], 'bez wpisu w zadaniu')} · commit: "
                   + (code_span(commits[s['id']]) if s['id'] in commits else "brak"))
    if not slices:
        out.append("- brak planu (`plan.md`)")
    if not found:
        out.append(f"- Commitów kawałków nie ustalono: git nie zna gałęzi bazowej {code_span(base or ', '.join(BASES))}.")

    out += ["", "## Ślad kryteriów", ""]
    if (docs / "spec.md").is_file():
        out.append(engine_md(project, "trace_check.py", key, "--md", *base_args)
                   or "- Śladu nie udało się policzyć (`tf trace`).")
    else:
        out.append("- Zadanie nie ma specyfikacji (`spec.md`) — waga lekka jej nie wymaga, więc śladu kryteriów nie ma.")

    out += ["", "## Jak sprawdzono", ""]
    missing = []
    for s in slices:
        rel, ev = proofs.get(s["id"], (None, {}))
        scan = scan_status(run_dir, s["id"]) or "brak wyniku"
        if rel is None:
            line, why = "**brak dowodu weryfikacji**", "brak dowodu"
        else:
            code = ev.get("exit_code")
            green = code == 0
            why = None if green else f"czerwony dowód, kod wyjścia {code}"
            line = (f"{'zielone' if green else '**czerwone**'}: {code_span(ev.get('command') or '?')} (kod wyjścia {code}, "
                    f"{as_data(ev.get('at') or 'bez daty', 40)}, dowód `{rel}`)")
            state = states.get(s["id"])
            if green and state and state != "zweryfikowany":
                line += f" — **dowód nieaktualny** (stan: {state})"
                why = f"dowód nieaktualny, stan: {state}"
        if why:
            missing.append(f"{s['id']} ({why})")
        out.append(f"- **{s['id']}** — {line} · skan bezpieczeństwa: {scan}")
    if not slices:
        out.append("- brak kawałków w planie, więc nie ma dowodów weryfikacji")
    drift = (meta.get("pr_steps") or {}).get("drift")
    out += [f"- Zgodność z planem (`plan_drift`): {drift if drift in STATES else 'nie zapisano'}",
            f"- Dowody są w `{rel_docs}/evidence/` (w tym PR); pełne wyjście poleceń zostaje poza repozytorium."]

    out += ["", "## Ryzyko", "", f"- Waga zadania: {WEIGHT_PL.get(task.get('weight'), 'nie zapisano')}", ""]
    out.append(engine_md(project, "risk_triage.py", "--md", *base_args) or "- Triażu ryzyka nie udało się policzyć (`tf risk`).")

    flag = task.get("flag") if isinstance(task.get("flag"), dict) else {}
    steps = []
    if flag.get("key"):
        steps.append(f"Wyłącz flagę {code_span(flag['key'])} — zmiana przestaje działać bez wdrożenia.")
    card_steps = rollback_steps(project)
    steps += [f"{s} _(z karty operacyjnej `{CARD.as_posix()}`)_" for s in card_steps]
    steps.append("Kod: `git revert <commit scalenia>` na gałęzi domyślnej, potem zwykłe wdrożenie.")
    out += ["", "## Jak cofnąć", "", *(f"{i}. {s}" for i, s in enumerate(steps, 1)), ""]
    if not flag.get("key"):
        out.append(f"- Flaga: brak — {as_data(flag['none'], 300)}." if flag.get("none") else
                   "- Flaga: nie zapisano w zadaniu (flagi może prowadzić człowiek).")
    if not card_steps:
        out.append(f"- Karta operacyjna (`{CARD.as_posix()}`, pole `deploy.rollback`) nie opisuje cofania wdrożenia — "
                   "powyżej krok domyślny.")

    out += ["", "## Odłożone do decyzji", "", *([f"- {as_data(x, 400)}" for x in run_report.parked_items(run_dir)] or ["- brak"])]
    notes = [as_data(ln, 400) for name in ("plan.md", "spec.md")
             for ln in (read_text(docs / name) or "").splitlines() if ASSUMPTION.search(ln)]
    out += ["", "## Założenia", "", *([f"- {n}" for n in notes] or ["- brak zapisanych założeń"])]
    usage = meta.get("usage") if isinstance(meta.get("usage"), dict) else None
    if usage and isinstance(usage.get("cost_usd"), (int, float)):
        out += ["", "## Przebieg", "", f"- Koszt do tej chwili: {usage['cost_usd']:.2f} USD (szacunek z cennika API), "
                f"czas: {usage.get('minutes', '?')} min. Pełny raport: `report.md` w katalogu zadania."]
    out += ["", "_Opis złożony skryptem `run_state.py pr-body` z plików zadania._"]
    return "\n".join(out) + "\n", missing


def cmd_pr_body(run_dir: Path, base: str | None, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"brak lub błędny {run_dir / 'run.json'} — przebieg zakłada `run_report.py start`.")
    if not meta.get("key"):
        return no_task(meta)
    try:
        update_usage(run_dir, meta, project)
    except Exception:  # noqa: BLE001 — koszt jest dodatkiem do opisu
        pass
    text, missing = pr_body(run_dir, meta, project, base)
    target = run_dir / "pr-body.md"
    target.write_text(text, encoding="utf-8")
    try:
        shown = target.resolve().relative_to(project.resolve()).as_posix()
    except ValueError:
        shown = str(target)
    print(f"✓ opis PR: {shown}\n  użyj: gh pr create --title \"<typ>(<zakres>): <opis>\" --body-file {shown}\n"
          "  własne uwagi (odstępstwa od planu, wyjątek budżetu artefaktów) dopisz na końcu pliku")
    if missing:
        print(f"⚠ bez zielonego dowodu: {', '.join(missing)} — opis mówi to wprost")
    return 0


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


def evidence_items(docs: Path) -> list[dict]:
    """Ostatni dowód każdego kawałka (evidence/K<n>-<m>.json): zielona kropka przy kodzie wyjścia 0."""
    last: dict[int, tuple[int, Path]] = {}
    for f in docs.glob("evidence/K*-*.json"):
        m = re.fullmatch(r"K(\d+)-(\d+)\.json", f.name)
        if m and int(m.group(2)) >= last.get(int(m.group(1)), (0, f))[0]:
            last[int(m.group(1))] = (int(m.group(2)), f)
    out = []
    for _, (_, f) in sorted(last.items()):
        text = read_text(f)
        if text is None:
            continue
        try:
            ok = json.loads(text).get("exit_code") == 0
        except (ValueError, AttributeError):
            ok = False
        out.append({"name": f"evidence/{f.name}", "dot": "ok" if ok else "bad", "text": text})
    return out


def code_items(run_dir: Path, proofs: list[dict]) -> list[dict]:
    """Pliki kodu każdego kawałka — z ostatniego dowodu weryfikacji, więc także te, o których agent nie wspomniał."""
    project, out = run_dir.resolve().parents[2], []
    for proof in proofs:
        m = re.match(r"evidence/(K\d+)-", proof["name"])
        try:
            files = json.loads(proof["text"]).get("files") or {}
        except (ValueError, AttributeError):
            files = {}
        for rel in sorted(files) if m else []:
            text = read_text(project / rel)
            out.append({"name": f"{m.group(1)} · {rel}", "dot": "ok" if text is not None else "warn",
                        "text": text if text is not None else "(pliku już nie ma)"})
    return out


def file_groups(run_dir: Path, meta: dict, stage: str, needs: str | None, parked: list[str]) -> list[dict]:
    groups: list[dict] = []
    main, work = [], []
    task_dir = meta.get("task_dir")
    docs = run_report.docs_dir(run_dir, meta)       # nowy układ: historyjka, plan i raport w katalogu zadania
    for path in (run_report.story_file(run_dir, meta), docs / "spec.md", docs / "plan.md", docs / "events.jsonl",
                 run_dir / "parked.md"):
        name, text = path.name, read_text(path)
        if text is None:
            continue
        dot = "ok"
        if name == "plan.md":
            dot = "warn" if stage == "needs" and needs == "plan" else "ok"
        if name == "parked.md":
            dot = "warn" if parked else ""
        (work if task_dir and name == "parked.md" else main).append({"name": name, "dot": dot, "text": text})
    if main:
        groups.append({"grp": f"Zadanie (git) · {task_dir}/" if task_dir else "Przebieg", "items": main})
    if work:
        groups.append({"grp": f"Robocze · .tf/runs/{meta.get('key')}/", "items": work})
    proofs = evidence_items(docs) if task_dir else []
    if proofs:
        groups.append({"grp": "Dowody", "items": proofs})
    code = code_items(run_dir, proofs) if task_dir else []
    if code:
        groups.append({"grp": "Kod kawałków (pliki z dowodów)", "items": code})
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
            [f"Zatrzymanie — {cur or 'przebieg'}"]
            + (message_lines(stop_message(meta.get("stop_code")), meta.get("stop_text"))
               if stop_message(meta.get("stop_code")) else [f"Powód: {meta.get('stop_text') or '(brak opisu)'}"])
            + [
             f"Wznowienie: od {cur or 'miejsca, w którym fabryka przerwała'}"])})
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
    view = task_view(project, meta["key"]) if meta.get("key") else None
    out_slices = slice_items(slices, view, cur, stage, needs)
    parked = [ln[2:].strip() for ln in run_report.parked_items(run_dir)]
    m = re.match(r"(\d{4}-\d{2}-\d{2})-", run_dir.name)
    usage = meta.get("usage") if isinstance(meta.get("usage"), dict) else {}
    pr_steps = meta.get("pr_steps") or {}
    obj = {"slug": meta.get("slug") or run_dir.name, "title": meta.get("title") or run_dir.name,
           "date": m.group(1) if m else str(meta.get("started_at", ""))[:10],
           "stage": stage, "needs": needs, "auto": bool(meta.get("auto")), "effort": meta.get("effort"),
           "key": meta.get("task") or meta.get("key"), "change": meta.get("change"), "flag": meta.get("flag"), "pr": meta.get("pr"),
           "stopText": meta.get("stop_text"), "stopCode": meta.get("stop_code"),
           "stopLabel": (stop_message(meta.get("stop_code")) or {}).get("co") or STOP_CODES.get(meta.get("stop_code") or ""),
           "stopHint": stop_hint(meta, cur) if needs == "stop" else None,
           "stopNeed": (stop_message(meta.get("stop_code")) or {}).get("potrzeba"),
           "stopQuestion": (stop_message(meta.get("stop_code")) or {}).get("pytanie"),
           "stopOptions": [{"opcja": o.get("opcja"), "skutek": o.get("skutek"), "rekomendowana": bool(o.get("rekomendowana"))}
                           for o in (stop_message(meta.get("stop_code")) or {}).get("opcje") or []],
           "slices": out_slices, "parked": len(parked), "parkedList": parked,
           "cost": usage.get("cost_usd"), "min": usage.get("minutes"), "models": usage.get("models") or [],
           "started": meta.get("started_at", ""),
           "dir": run_dir.resolve().relative_to(project.resolve()).as_posix()
           if run_dir.resolve().is_relative_to(project.resolve()) else str(run_dir),
           "taskDir": meta.get("task_dir"), "taskStage": view["task"].get("stage") if view else None,
           "waiting": waiting_items(project, view)}
    if cur and stage in ("slices", "needs"):
        obj["cur"] = {"k": cur.get("k"), "rounds": normalize_rounds(cur) or [{s: "todo" for s in STEPS}]}
    if stage == "pr":
        obj["prSteps"] = {"drift": pr_steps.get("drift", "todo"), "pr": pr_steps.get("pr", "todo")}
    obj["files"] = file_groups(run_dir, meta, stage, needs, parked)
    return obj


def sentence(text: str | None, capital: bool = False) -> str:
    """Tekst zakończony jedną kropką (bez „..”), na życzenie od wielkiej litery; pusty zostaje pusty."""
    s = (text or "").strip()
    if not s:
        return s
    return (s[0].upper() + s[1:] if capital else s) + ("" if s[-1] in ".!?…" else ".")


def stop_hint(meta: dict, cur: dict | None) -> str:
    """Opis zatrzymania na karcie: co się stało, powód z przebiegu i co zrobić — każda część osobnym zdaniem."""
    label = (stop_message(meta.get("stop_code")) or {}).get("co") or STOP_CODES.get(meta.get("stop_code") or "")
    resume = (cur or {}).get("k") or "bieżącego kawałka"
    return " ".join(x for x in (sentence(label, capital=True), sentence(meta.get("stop_text") or "STOP"),
                                f"Zdecyduj i napisz w sesji: wznów od {resume}") if x)


def waiting_items(project: Path, view: dict | None) -> list[dict]:
    """Na co zadanie czeka u człowieka — ta sama lista co w `tf status` (`task_state.waiting`)."""
    try:
        api = task_api(project)
        return api.waiting(project.resolve(), view["task"]) if api and view and hasattr(api, "waiting") else []
    except Exception:  # noqa: BLE001 — podgląd nigdy nie psuje przebiegu
        return []


def slice_items(slices: list[dict], view: dict | None, cur: dict | None, stage: str, needs: str | None) -> list[dict]:
    """Stan kawałków planu na karcie. Z zadaniem (`view`) kawałek odhaczony bez aktualnego dowodu ma stan `stale`,
    a każdy kawałek niesie `proof` — stan wyliczony przez `tf task`."""
    out = []
    first_open = next((s["id"] for s in slices if not s["checked"]), None)
    for s in slices:
        proof = (view["slices"].get(s["id"]) or "brak dowodu") if view else None
        if s["checked"]:
            state = "stale" if view and proof != "zweryfikowany" else "done"
        elif cur and cur.get("k") == s["id"]:
            state = "fail" if stage == "needs" and needs == "stop" else "cur"
        elif not cur and stage == "slices" and s["id"] == first_open:
            state = "cur"
        else:
            state = "todo"
        item = {"id": s["id"], "value": s["value"], "state": state}
        if view:
            item["proof"] = proof
        out.append(item)
    return out


def task_object(task_dir: Path, project: Path) -> dict | None:
    """Karta zadania, które nie ma przebiegu w `.tf/runs/` (samo `tf task` albo świeży klon): etap z task.json,
    kawałki z plan.md, a bez planu — z samego zadania."""
    key = task_dir.name
    view = task_view(project, key)
    if view is None:
        return None
    task = view["task"]
    stage = BARE_STAGE.get(task.get("stage"), "intake")
    rel = task_dir.resolve().relative_to(project.resolve()).as_posix()
    meta = {"key": key, "task_dir": rel}
    plan = parse_slices(task_dir)
    if plan:
        slices = slice_items(plan, view, None, stage, None)
    else:
        slices = [{"id": k, "value": (task.get("slices", {}).get(k) or {}).get("title") or "", "proof": s,
                   "state": PROOF_STATE.get(s, "stale")} for k, s in view["slices"].items()]
    work = project / run_report.WORK / key          # może nie istnieć — wtedy panel pokazuje tylko katalog zadania
    files = file_groups(work, meta, stage, None, [])
    if not any(g["grp"] != "Dowody" for g in files):
        files.insert(0, {"grp": f"Zadanie (git) · {rel}/", "items": [
            {"name": "task.json", "dot": "", "text": json.dumps(task, ensure_ascii=False, indent=1)}]})
    created = str(task.get("created", ""))
    obj = {"slug": key, "title": task.get("title") or key, "date": created[:10], "stage": stage, "needs": None,
           "auto": False, "effort": None, "key": key, "change": None, "flag": None, "pr": None, "stopText": None,
           "slices": slices, "parked": 0, "parkedList": [], "cost": None, "min": None, "models": [],
           "waiting": waiting_items(project, view),
           "started": created, "dir": None, "taskDir": rel, "taskStage": task.get("stage"), "files": files}
    if stage == "pr":
        obj["prSteps"] = {"drift": "todo", "pr": "todo"}
    return obj


def build_dashboard(project: Path, out: Path | None = None, costs: bool = True) -> Path:
    root = project / run_report.RUNS                # stary układ cięć (już nie powstaje): historia zostaje w podglądzie
    work = project / run_report.WORK                # katalogi robocze zadań: .tf/runs/<KEY>/
    runs = []
    for d in sorted({*root.glob("*/run.json"), *work.glob("*/run.json")}):
        obj = run_object(d.parent, project, costs)
        if obj:
            runs.append(obj)
    seen = {r["key"] for r in runs}
    for f in sorted((project / run_report.CHANGES).glob("*/task.json")):   # zadania bez przebiegu w .tf/runs/
        obj = task_object(f.parent, project) if f.parent.name not in seen else None
        if obj:
            runs.append(obj)
    runs.sort(key=lambda r: (r["date"], r["started"]), reverse=True)
    html = TEMPLATE.read_text(encoding="utf-8")
    data = json.dumps(runs[:MAX_RUNS], ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("/*RUNS_JSON*/[]", data, 1).replace("/*GENERATED*/", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    target = out or (work / "dashboard.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(html, encoding="utf-8")
    os.replace(tmp, target)
    return target


def options(project: Path) -> dict:
    """Opcje z `.claude/tf.json` (brak pliku albo klucza = domyślnie włączone); zmienne TF_DASHBOARD=0
    i TF_DASHBOARD_OPEN=0 wyłączają opcję bez edycji pliku."""
    opts = dict(DEFAULTS)
    try:
        data = json.loads((project / CONFIG).read_text(encoding="utf-8"))
        opts.update({k: bool(v) for k, v in data.items() if k in DEFAULTS})
    except (OSError, ValueError, AttributeError):
        pass
    for key, env in (("dashboard", "TF_DASHBOARD"), ("dashboard_open", "TF_DASHBOARD_OPEN")):
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
    s.add_argument("--plan", dest="plan_mode", action="store_true")
    s.add_argument("--code", default=None)
    s.add_argument("--task", dest="whole_task", action="store_true",
                   help="pytanie dotyczy całego zadania, nie jednego kawałka (z przełącznikiem loop.blocked_slices)")
    s.add_argument("--effort", default=None, choices=["low", "medium", "high", "xhigh", "max"])
    t = sub.add_parser("step")
    t.add_argument("run_dir")
    t.add_argument("target")
    t.add_argument("rest", nargs="*")
    sp = sub.add_parser("spec")
    sp.add_argument("run_dir")
    sp.add_argument("action", nargs="?", choices=["new"])
    fg = sub.add_parser("flag")
    fg.add_argument("run_dir")
    fg.add_argument("action", choices=["mode", "set", "none"])      # zgodę na inne środowisko zapisuje człowiek: tf task flag … allow
    fg.add_argument("value", nargs="?")
    fg.add_argument("--remove-by", default=None)
    fg.add_argument("--reason", default="")
    ms = sub.add_parser("message")
    ms.add_argument("code")
    ms.add_argument("--json", action="store_true")
    mo = sub.add_parser("mode")
    mo.add_argument("run_dir")
    mo.add_argument("new", nargs="?")
    apv = sub.add_parser("approve")
    apv.add_argument("run_dir")
    wg = sub.add_parser("weight")
    wg.add_argument("run_dir")
    wg.add_argument("--set", dest="new", default=None)      # obniżenie zapisuje człowiek: tf task weight … --by human:<id>
    tr = sub.add_parser("trace")
    tr.add_argument("run_dir")
    tr.add_argument("--base", default=None)
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
    bl = sub.add_parser("block")
    bl.add_argument("run_dir")
    bl.add_argument("slice_id")
    bl.add_argument("--question", required=True)
    an = sub.add_parser("answer")
    an.add_argument("run_dir")
    an.add_argument("slice_id")
    an.add_argument("text")
    an.add_argument("--by", default=None)
    nx = sub.add_parser("next")
    nx.add_argument("run_dir")
    pb = sub.add_parser("pr-body")
    pb.add_argument("run_dir")
    pb.add_argument("--base", default=None)
    d = sub.add_parser("dashboard")
    d.add_argument("--no-cost", action="store_true")
    d.add_argument("--out", default=None)
    d.add_argument("--open", action="store_true", help="otwórz plik w przeglądarce")
    args = ap.parse_args(argv[1:])
    project = Path.cwd()
    if args.cmd == "stage":
        return cmd_stage(Path(args.run_dir), args.stage, args.needs, args.reason, args.pr, args.auto, args.effort,
                         project, plan_mode=args.plan_mode, code=args.code, whole_task=args.whole_task)
    if args.cmd == "step":
        return cmd_step(Path(args.run_dir), args.target, args.rest, project)
    if args.cmd == "flag":
        return cmd_flag(Path(args.run_dir), args.action, args.value, args.remove_by, args.reason, project)
    if args.cmd == "weight":
        return cmd_weight(Path(args.run_dir), args.new, project)
    if args.cmd == "message":
        return cmd_message(args.code, args.json)
    if args.cmd == "mode":
        return cmd_mode(Path(args.run_dir), args.new, project)
    if args.cmd == "approve":
        return cmd_approve(Path(args.run_dir), project)
    if args.cmd == "trace":
        return cmd_trace(Path(args.run_dir), args.base, project)
    if args.cmd == "spec":
        return cmd_spec(Path(args.run_dir), project, new=args.action == "new")
    if args.cmd == "verify":
        return cmd_verify(Path(args.run_dir), args.slice_id, args.files, args.command, args.timeout, project)
    if args.cmd == "tick":
        return cmd_tick(Path(args.run_dir), args.slice_id, project)
    if args.cmd == "park":
        return cmd_park(Path(args.run_dir), args.item, project)
    if args.cmd == "block":
        return cmd_block(Path(args.run_dir), args.slice_id, args.question, project)
    if args.cmd == "answer":
        return cmd_answer(Path(args.run_dir), args.slice_id, args.text, args.by, project)
    if args.cmd == "next":
        return cmd_next(Path(args.run_dir), project)
    if args.cmd == "pr-body":
        return cmd_pr_body(Path(args.run_dir), args.base, project)
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
