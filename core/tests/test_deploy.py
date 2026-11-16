#!/usr/bin/env python3
"""Karta wdrożenia i sprawdzenie po scaleniu (krok G3): sekcja `deploy` karty operacyjnej, `tf task deployed` z testem
dymnym, pytanie „wycofać?” po czerwonym wyniku i lista „czeka na Ciebie”.
python3 .claude/tests/test_deploy.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
ONBOARD = ROOT / ".tf" / "factory" / "onboard.py"
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
CHANGES = Path("docs") / "project" / "changes"
CARD = Path(".tf") / "config" / "operations.json"
GREEN = f'{sys.executable} -c "print(\'smoke ok\')"'
RED = f'{sys.executable} -c "print(\'HTTP 500 /health\'); raise SystemExit(7)"'
SLOW = f'{sys.executable} -c "import time; time.sleep(30)"'
ROLLBACK = "Wdróż poprzednią wersję: ./deploy.sh --previous"
LOGS = "kubectl logs deploy/parking --since=10m"
NODE = {"scripts": {"test": "vitest run", "smoke": "node scripts/smoke.mjs"}}


def call(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
           "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, env=env,
                          stdin=subprocess.DEVNULL, timeout=120)


def card(project: Path, deploy: dict | None, **rest) -> None:
    f = project / CARD
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({**rest, **({"deploy": deploy} if deploy is not None else {})}, ensure_ascii=False),
                 encoding="utf-8")


def task(project: Path, key: str = "IMP-1") -> dict:
    return json.loads((project / CHANGES / key / "task.json").read_text(encoding="utf-8"))


def new_task(project: Path, stage: str = "pr") -> None:
    project.mkdir(parents=True)
    call(project, TASK, "start", "IMP-1", "--title", "Limit dobowy")
    if stage != "intake":
        call(project, TASK, "stage", "IMP-1", stage, "--force")


def waiting(project: Path) -> list[dict]:
    r = call(project, TASK, "list", "--json")
    try:
        return next(x for x in json.loads(r.stdout) if x["key"] == "IMP-1")["waiting"]
    except (ValueError, KeyError, StopIteration, TypeError):
        return [{"error": r.stdout + r.stderr}]


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        # zadanie przed PR: wdrożenia nie da się zapisać
        p = Path(t) / "early"
        new_task(p, "intake")
        card(p, {"smoke": GREEN})
        r = call(p, TASK, "deployed", "IMP-1")
        check(r.returncode != 0 and "pr" in r.stdout and task(p)["stage"] == "intake" and "deploy" not in task(p),
              f"DP-1: wdrożenie zapisuje się po etapie pr; wcześniej odmowa: {r.returncode} {r.stdout}")

        # bez karty i bez testu dymnego: komunikat, nie błąd; etap bez zmian
        p = Path(t) / "nocard"
        new_task(p)
        r = call(p, TASK, "deployed", "IMP-1")
        check(r.returncode == 0 and "deploy.smoke" in r.stdout and "kończy na scaleniu" in r.stdout
              and task(p)["stage"] == "pr" and not list((p / CHANGES / "IMP-1").glob("evidence/deploy-*.json")),
              f"DP-2: bez karty fabryka kończy na scaleniu i mówi to wprost (kod 0, bez dowodu): {r.returncode} {r.stdout}")
        card(p, {"smoke": "", "rollback": ROLLBACK})
        r = call(p, TASK, "deployed", "IMP-1")
        check(r.returncode == 0 and "deploy.smoke" in r.stdout and task(p)["stage"] == "pr",
              f"DP-3: karta bez polecenia testu dymnego — to samo: {r.returncode} {r.stdout}")

        # zielony test dymny → dowód i etap deploy
        p = Path(t) / "green"
        new_task(p)
        card(p, {"smoke": GREEN, "rollback": ROLLBACK, "rollback_minutes": 5, "logs": LOGS,
                 "approval": "wdrożenie na produkcję zatwierdza kierownik zmiany"})
        r = call(p, TASK, "deployed", "IMP-1", "--version", "2.4.0")
        ev = p / CHANGES / "IMP-1" / "evidence" / "deploy-1.json"
        data = json.loads(ev.read_text(encoding="utf-8")) if ev.is_file() else {}
        check(r.returncode == 0 and task(p)["stage"] == "deploy" and data.get("exit_code") == 0
              and data.get("command") == GREEN and data.get("version") == "2.4.0" and data.get("at")
              and data.get("kind") == "deploy",
              f"DP-4: zielony test dymny zapisuje dowód (polecenie, kod, wersja, data) i etap deploy: {r.stdout} {data}")
        check(task(p).get("deploy", {}).get("state") == "ok" and task(p)["deploy"].get("evidence") == "evidence/deploy-1.json"
              and not waiting(p) and set(data) == {"kind", "command", "exit_code", "version", "sha", "at", "log"}
              and "smoke ok" in (p / ".tf" / "runs" / "IMP-1" / "deploy-1.log").read_text(encoding="utf-8"),
              f"DP-5: stan wdrożenia „ok” w task.json, nic nie czeka, a wyjście polecenia nie trafia do gita: {task(p).get('deploy')}")
        check("zatwierdza kierownik zmiany" in r.stdout,
              f"DP-6: komunikat przypomina, co zatwierdza człowiek (z karty): {r.stdout}")
        r = call(p, TASK, "status", "IMP-1")
        check("wdrożenie" in r.stdout and "2.4.0" in r.stdout,
              f"DP-7: tf task status pokazuje wynik wdrożenia i wersję: {r.stdout}")

        # czerwony test dymny → pytanie „wycofać?”, krok cofania, logi; zadanie czeka na człowieka
        p = Path(t) / "red"
        new_task(p)
        card(p, {"smoke": RED, "rollback": ROLLBACK, "rollback_minutes": 5, "logs": LOGS})
        r = call(p, TASK, "deployed", "IMP-1", "--version", "2.4.0")
        check(r.returncode == 1 and "ycofać" in r.stdout and ROLLBACK in r.stdout and "5 min" in r.stdout
              and LOGS in r.stdout and "HTTP 500 /health" in r.stdout and "kodem 7" in r.stdout,
              f"DP-8: czerwony test: pytanie o wycofanie, krok i czas cofania, polecenie logów, wyjście testu: "
              f"{r.returncode} {r.stdout}")
        check(task(p)["stage"] == "pr" and task(p).get("deploy", {}).get("state") == "red"
              and (p / CHANGES / "IMP-1" / "evidence" / "deploy-1.json").is_file(),
              f"DP-9: czerwony wynik zapisany z dowodem; etap nie przechodzi do deploy: {task(p).get('deploy')}")
        w = waiting(p)
        check(len(w) == 1 and w[0].get("kind") == "deploy" and "ycofać" in (w[0].get("question") or "")
              and w[0].get("recommended") and any(ROLLBACK in (o.get("skutek") or "") for o in w[0].get("options") or [])
              and "--rolled-back" in (w[0].get("how") or ""),
              f"DP-10: lista „czeka na Ciebie”: pytanie o wycofanie z opcjami, rekomendacją i poleceniem: {w}")
        r = call(p, TASK, "list")
        check("czeka na Ciebie" in r.stdout and "ycofać" in r.stdout,
              f"DP-11: tf status pokazuje zadanie czekające na decyzję o wycofaniu: {r.stdout}")

        # decyzja o wycofaniu należy do człowieka
        r = call(p, TASK, "deployed", "IMP-1", "--rolled-back")
        check(r.returncode == 2 and "human:" in r.stdout and waiting(p),
              f"DP-12: wycofanie zapisuje człowiek (--by human:<id>): {r.returncode} {r.stdout}")
        r = call(p, TASK, "deployed", "IMP-1", "--rolled-back", "--by", "human:anna")
        d = task(p).get("deploy", {})
        check(r.returncode == 0 and d.get("state") == "rolled-back" and d.get("decided_by") == "human:anna"
              and d.get("decided_at") and not waiting(p),
              f"DP-13: zapis decyzji o wycofaniu zdejmuje zadanie z listy: {r.returncode} {r.stdout} {d}")

        # po naprawie ponowny zielony test → deploy, drugi dowód
        card(p, {"smoke": GREEN, "rollback": ROLLBACK})
        r = call(p, TASK, "deployed", "IMP-1", "--version", "2.4.1")
        check(r.returncode == 0 and task(p)["stage"] == "deploy" and task(p)["deploy"].get("state") == "ok"
              and task(p)["deploy"].get("evidence") == "evidence/deploy-2.json" and not waiting(p),
              f"DP-14: ponowny zielony test po naprawie: etap deploy i drugi dowód: {r.stdout} {task(p).get('deploy')}")

        # przekroczony czas testu dymnego to wynik czerwony, nie ślad wyjątku
        p = Path(t) / "slow"
        new_task(p)
        card(p, {"smoke": SLOW})
        r = call(p, TASK, "deployed", "IMP-1", "--timeout", "1")
        check(r.returncode == 1 and "Traceback" not in r.stdout + r.stderr and "limit czasu" in r.stdout
              and "git revert" in r.stdout and task(p)["deploy"].get("state") == "red",
              f"DP-15: limit czasu → czerwony wynik; bez kroku w karcie podany jest krok domyślny: {r.returncode} {r.stdout} {r.stderr}")

        # karta nieczytelna albo o złym kształcie nie wywraca polecenia
        p = Path(t) / "broken"
        new_task(p)
        (p / CARD).parent.mkdir(parents=True, exist_ok=True)
        (p / CARD).write_text("{nie json", encoding="utf-8")
        r = call(p, TASK, "deployed", "IMP-1")
        check(r.returncode == 0 and "Traceback" not in r.stdout + r.stderr and "deploy.smoke" in r.stdout,
              f"DP-16: nieczytelna karta = brak testu dymnego, bez śladu wyjątku: {r.returncode} {r.stdout} {r.stderr}")
        card(p, {"smoke": ["rm", "-rf", "x"]})
        r = call(p, TASK, "deployed", "IMP-1")
        check(r.returncode == 0 and "deploy.smoke" in r.stdout and task(p)["stage"] == "pr",
              f"DP-17: test dymny, który nie jest tekstem, nie jest uruchamiany: {r.returncode} {r.stdout}")

        # ustalenia przeglądu bezpieczeństwa: wrogie wartości w karcie i w zadaniu nie wywracają poleceń
        p = Path(t) / "hostile"
        new_task(p)
        (p / CARD).parent.mkdir(parents=True, exist_ok=True)
        (p / CARD).write_text('{"deploy": {"smoke": %s, "rollback": "cofnij", "rollback_minutes": 1%s, '
                              '"logs": "logi \\u001b[2J tu"}}' % (json.dumps(RED), "0" * 400), encoding="utf-8")
        r = call(p, TASK, "deployed", "IMP-1")
        r2 = call(p, TASK, "list")
        check(r.returncode == 1 and "Traceback" not in r.stdout + r.stderr + r2.stdout + r2.stderr
              and "czeka na Ciebie" in r2.stdout and "cofnij" in r.stdout,
              f"DP-24: ogromna liczba w rollback_minutes nie wywraca deployed ani tf status: {r.stderr[-300:]} {r2.stderr[-300:]}")
        check("\x1b" not in r.stdout and "logi" in r.stdout,
              f"DP-25: znaki sterujące z karty nie trafiają na terminal: {r.stdout!r}")
        for bad in ("nan", "inf", "1e20", "0"):
            r = call(p, TASK, "deployed", "IMP-1", "--timeout", bad)
            check(r.returncode == 2 and "Traceback" not in r.stdout + r.stderr,
                  f"DP-26: limit czasu {bad} jest odrzucany z kodem 2: {r.returncode} {r.stdout} {r.stderr[-200:]}")
        p = Path(t) / "noRed"
        new_task(p)
        r = call(p, TASK, "deployed", "IMP-1", "--rolled-back", "--by", "human:anna")
        check(r.returncode != 0 and "deploy" not in task(p),
              f"DP-27: wycofanie da się zapisać tylko po czerwonym teście dymnym: {r.returncode} {r.stdout}")
        f = p / CHANGES / "IMP-1" / "task.json"
        f.write_text(json.dumps({**task(p), "deploy": {"state": ["ok"]}}), encoding="utf-8")
        r = call(p, TASK, "status", "IMP-1")
        check(r.returncode == 0 and "Traceback" not in r.stderr,
              f"DP-28: nietypowy zapis wdrożenia w task.json nie wywraca tf task status: {r.stderr[-200:]}")

        # tf onboard dopisuje sekcję deploy i wykrywa test dymny; istniejących pól nie zmienia
        p = Path(t) / "onb"
        p.mkdir()
        (p / "package.json").write_text(json.dumps(NODE), encoding="utf-8")
        (p / "package-lock.json").write_text("{}", encoding="utf-8")
        card(p, None, tracker={"type": "jira", "prefix": "EBO"})
        r = call(p, ONBOARD, "--yes")
        c = json.loads((p / CARD).read_text(encoding="utf-8"))
        check(r.returncode == 0 and c.get("tracker") == {"type": "jira", "prefix": "EBO"} and "flags" in c
              and c.get("deploy", {}).get("smoke") == "npm run smoke"
              and all(k in c.get("deploy", {}) for k in ("rollback", "rollback_minutes", "smoke", "approval", "logs")),
              f"DP-18: onboard dopisuje sekcję deploy z wykrytym testem dymnym i nie rusza trackera: {c}")
        check("deploy" in r.stdout and "rollback" in r.stdout and "npm run smoke" in r.stdout,
              f"DP-19: onboard mówi, co wykrył i co uzupełnić w części o wdrożeniu: {r.stdout}")
        c.setdefault("deploy", {})["rollback"] = ROLLBACK
        (p / CARD).write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
        call(p, ONBOARD, "--yes")
        check(json.loads((p / CARD).read_text(encoding="utf-8")) == c,
              "DP-20: ponowny onboard nie nadpisuje uzupełnionej karty")
        p = Path(t) / "onb2"
        (p / "scripts").mkdir(parents=True)
        (p / "scripts" / "smoke.sh").write_text("#!/bin/sh\ncurl -fsS localhost/health\n", encoding="utf-8")
        (p / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")
        call(p, ONBOARD, "--yes")
        c = json.loads((p / CARD).read_text(encoding="utf-8")) if (p / CARD).is_file() else {}
        check(c.get("deploy", {}).get("smoke") == "./scripts/smoke.sh",
              f"DP-21: scripts/smoke.sh wykryty jako test dymny: {c.get('deploy')}")

        # zakończenie przebiegu podaje następny krok po scaleniu
        p = Path(t) / "finish"
        p.mkdir()
        call(p, SCRIPTS / "run_report.py", "start", "Limit dobowy", "--key", "IMP-1", "--story", "Popraw literówkę w README.")
        d = str(p / ".tf" / "runs" / "IMP-1")
        r = call(p, SCRIPTS / "run_report.py", "finish", d)
        check("deploy.smoke" in r.stdout and "tf task deployed" not in r.stdout,
              f"DP-22: finish bez testu dymnego w karcie mówi, że fabryka kończy na scaleniu: {r.stdout}")
        card(p, {"smoke": GREEN})
        r = call(p, SCRIPTS / "run_report.py", "finish", d)
        check("tf task deployed IMP-1" in r.stdout,
              f"DP-23: finish z testem dymnym w karcie podaje polecenie po wdrożeniu: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów karty wdrożenia")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
