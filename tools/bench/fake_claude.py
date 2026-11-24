#!/usr/bin/env python3
"""
A fake `claude` for `tools/bench.py run --fake-claude tools/bench/fake_claude.py`: no model, no network, no cost.

It plays a canned /tf-task run in the current directory (the bench fixture with the factory installed): a story
branch, the task files (`docs/project/changes/<KEY>/task.json`, `plan.md`, `report.md`, evidence), the run directory
(`.tf/runs/<KEY>/run.json`), quality-gate log rows, and for `simple` and `medium` the code change itself (commits);
for `sensitive` the full weight and a `plan-approval` STOP without code. On stdout it prints a result shaped like
`claude -p --output-format json` (`type`, `is_error`, `duration_ms`, `num_turns`, `total_cost_usd`, `result`).
The task comes from TF_BENCH_TASK and the side from TF_BENCH_SIDE (the bench sets both).

TF_BENCH_FAKE (JSON) changes the behaviour per side, for the tests of the comparison:
  {"cand": {"slow": 2.0,         # durations (result, evidence, gate rows) × 2
            "turns": 1.5,        # turns and requests × 1.5
            "cost": 1.5,         # cost × 1.5
            "weight": "normal",  # a different weight in task.json (e.g. the sensitive task losing its full weight)
            "no_gate": true,     # sensitive: no STOP and no review — the code goes straight in
            "slices": 3,         # a different number of plan slices
            "red": true,         # the code change breaks the tests
            "gate_s": 120}}      # one quality-gate hook run of this many seconds (the whole-suite regression)
Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = {"simple": {"s": 300, "turns": 20, "cost": 1.2, "slices": 1, "weight": "quick"},
        "medium": {"s": 900, "turns": 45, "cost": 3.5, "slices": 2, "weight": "normal"},
        "sensitive": {"s": 240, "turns": 15, "cost": 0.9, "slices": 2, "weight": "full"}}


def git(*args: str) -> None:
    subprocess.run(["git", "-c", "user.name=fake", "-c", "user.email=fake@example.invalid", *args], check=True,
                   capture_output=True)


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def edit(path: str, old: str, new: str) -> None:
    p = Path(path)
    p.write_text(p.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def solve_simple() -> None:
    edit("app/components/button.py", 'classes = f"{BASE_CLASS} {BASE_CLASS}-{kind}"',
         'classes = f"{BASE_CLASS} {BASE_CLASS}-{kind} btn-block"')
    for page in Path("app/pages").glob("*.py"):
        edit(str(page), ', style="width: 100%"', "")
    for page in ("cart", "orders"):
        edit(f"app/pages/{page}.py", '"Proceed"', '"Continue"')
    for page in ("profile", "wishlist"):
        edit(f"app/pages/{page}.py", '"Discard"', '"Remove"')
    edit("tests/test_pages.py", ">Proceed<", ">Continue<")
    edit("tests/test_pages.py", ">Discard<", ">Remove<")
    edit("tests/test_button.py", 'class="btn btn-primary"', 'class="btn btn-primary btn-block"')


def solve_medium_logic() -> None:
    edit("app/pricing.py", '''def order_total(lines: list[tuple[int, int]]) -> int:
    """The total of the order's lines: (unit price in cents, quantity) pairs."""
    return sum(line_total(price, qty) for price, qty in lines)''', '''def subtotal(lines: list[tuple[int, int]]) -> int:
    return sum(line_total(price, qty) for price, qty in lines)


def order_discount(lines: list[tuple[int, int]]) -> int:
    """AC-1: 5% from 10 items, 10% from 50 items, rounded down to whole cents."""
    items = sum(qty for _, qty in lines)
    rate = 10 if items >= 50 else 5 if items >= 10 else 0
    return subtotal(lines) * rate // 100


def order_total(lines: list[tuple[int, int]]) -> int:
    """AC-2: the total of the order's lines after the discount."""
    return subtotal(lines) - order_discount(lines)''')
    Path("tests/test_discount.py").write_text('''import unittest

from app.pricing import order_discount, order_total


class DiscountTest(unittest.TestCase):
    def test_ac1_discount(self):
        self.assertEqual(order_discount([(100, 9)]), 0)
        self.assertEqual(order_discount([(999, 10)]), 499)
        self.assertEqual(order_discount([(100, 50)]), 500)

    def test_ac2_total(self):
        self.assertEqual(order_total([(1000, 10)]), 9500)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")


def solve_medium_cart() -> None:
    edit("app/pages/cart.py", "from app.pricing import order_total", "from app.pricing import order_discount, order_total")
    edit("app/pages/cart.py", '    total = f"<p>Total: {money(order_total(list(lines)))}</p>"',
         '    discount = order_discount(list(lines))\n'
         '    total = (f"<p>Discount: -{money(discount)}</p>" if discount else "") + '
         'f"<p>Total: {money(order_total(list(lines)))}</p>"')


def solve_sensitive() -> None:
    edit("app/auth/permissions.py", '    "admin":', '    "manager": {"orders:read", "orders:write", "refunds:issue"},\n    "admin":')


def main() -> int:
    task = os.environ.get("TF_BENCH_TASK") or "simple"
    side = os.environ.get("TF_BENCH_SIDE") or "ref"
    knobs = (json.loads(os.environ.get("TF_BENCH_FAKE") or "{}") or {}).get(side) or {}
    prompt = sys.argv[sys.argv.index("-p") + 1] if "-p" in sys.argv else ""
    if not re.match(r"/(tf:)?tf-task\b", prompt):
        print(json.dumps({"type": "result", "is_error": True, "result": "fake claude: not a /tf-task prompt"}))
        return 1
    b = BASE.get(task, BASE["simple"])
    slow, slices = float(knobs.get("slow", 1)), int(knobs.get("slices", b["slices"]))
    weight = knobs.get("weight", b["weight"])
    key = f"T-FAKE-{task.upper()}"
    start = datetime.now(timezone.utc) - timedelta(seconds=b["s"] * slow)
    tdir, rdir = Path("docs/project/changes") / key, Path(".tf/runs") / key
    for d in (tdir / "evidence", rdir, Path(".tf/logs")):
        d.mkdir(parents=True, exist_ok=True)
    git("switch", "-q", "-c", f"story/{task}")
    stop = task == "sensitive" and weight == "full" and not knobs.get("no_gate")
    plan = [f"- [{' ' if stop else 'x'}] S{i} — slice {i} · criteria: AC-{i} · files: app/ · verify: `python3 run_tests.py`"
            for i in range(1, slices + 1)]
    (tdir / "plan.md").write_text(f"# Plan: {task}\n\n" + "\n".join(plan) + "\n", encoding="utf-8")
    approach = {"weight": weight, "rationale": "fake", "by": "process:approach", "at": iso(start)}
    task_json = {"key": key, "weight": weight, "mode": "normal" if weight == "full" else "auto", "approach": approach,
                 "approach_log": [{**approach, "from": "normal"}]}
    gate_rows = []
    if not stop:
        if task == "simple":
            solve_simple()
        elif task == "medium":
            solve_medium_logic()
        elif task == "sensitive":
            solve_sensitive()
        if knobs.get("red"):
            Path("tests/test_red.py").write_text("import unittest\n\n\nclass Red(unittest.TestCase):\n"
                                                 "    def test_red(self):\n        self.fail('red')\n", encoding="utf-8")
        git("add", "-A", "app", "tests")
        git("commit", "-qm", f"feat: {task} S1")
        if task == "medium":
            solve_medium_cart()
            git("add", "-A", "app", "tests")
            git("commit", "-qm", f"feat: {task} S2")
        for i in range(1, slices + 1):
            (tdir / "evidence" / f"S{i}-verify.json").write_text(json.dumps(
                {"at": iso(start + timedelta(seconds=30 * i)), "duration_s": round(4 * slow, 1), "ok": True}),
                encoding="utf-8")
        gate_rows.append({"at": iso(start + timedelta(seconds=40)), "duration_s": round(2 * slow, 1), "ok": True,
                          "related": True, "command": "python3 run_tests.py app/x.py"})
        task_json["reviews"] = {"security-reviewer": {"verdict": "PASS"}} if weight == "full" else {}
    if knobs.get("gate_s"):
        gate_rows.append({"at": iso(start + timedelta(seconds=60)), "duration_s": float(knobs["gate_s"]), "ok": True,
                          "related": False, "command": "python3 run_tests.py"})
    with (Path(".tf/logs") / "quality-gate-runs.jsonl").open("a", encoding="utf-8") as fh:
        for row in gate_rows:
            fh.write(json.dumps(row) + "\n")
    (tdir / "task.json").write_text(json.dumps(task_json, indent=1), encoding="utf-8")
    meta = {"slug": task, "key": key, "task_dir": tdir.as_posix(), "started_at": iso(start), "auto": True,
            "stage": "needs" if stop else "done"}
    if stop:
        meta.update(needs="stop", stop_code="plan-approval", stop_text="the full weight: the human approves the plan")
    else:
        meta["current"] = {"k": f"S{slices}", "rounds": [{"test": "pass", "code": "pass", "verify": "pass",
                                                          "scan": "pass", "scope": "pass"}]}
    (rdir / "run.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    secs = int(b["s"] * slow)
    turns = int(round(b["turns"] * float(knobs.get("turns", 1))))
    (tdir / "report.md").write_text(
        f"# Run report: {task}\n\n- Time: {secs // 60} min {secs % 60} s (from the start to the model's last answer)\n"
        f"- Model requests: {turns + 3} · models: fake\n\n## Where the time went\n\n"
        f"- Verification commands (`verify`, {0 if stop else slices} run(s)): 0 min 4 s\n", encoding="utf-8")
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "duration_ms": secs * 1000,
                      "num_turns": turns, "total_cost_usd": round(b["cost"] * float(knobs.get("cost", 1)), 4),
                      "result": "STOP — plan-approval" if stop else f"done: {task}", "session_id": "fake"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
