#!/usr/bin/env python3
"""The 14.0.0 plan syntax: slices `S<n>`, the fields `files:`, `criteria:`, `verify:`, `after:` (`none`) and the commit footer
`Slice S<n>:`; since 19.0.0 the old slice id `K<n>` and the Polish fields (`pliki:`, `po:`, `brak`) are not read (the
19.0.0 and 14.0.0 migrations rewrite them in open tasks; old commit footers `Kawałek K<n>` stay history).
python3 .claude/tests/test_plan_syntax.py"""
import importlib.util
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "task_state.py").is_file())
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / ".tf" / "factory"))


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


NEW = """# Plan
- [x] S1 — płatność kartą · criteria: test_card · files: src/pay.py, tests/test_pay.py · verify: `pytest` · after: none
- [ ] S2 — zwrot · criteria: test_refund · files: src/refund.py · after: S1
- [ ] S3 — raport · files: src/report.py · after: none
"""
OLD = """# Plan
- [x] K1 — płatność kartą · criteria: test_card · files: src/pay.py · verify: `pytest` · after: none
- [ ] K2 — zwrot · files: src/refund.py · after: K1
"""
POLISH = """# Plan
- [x] S1 — płatność kartą · kryteria: test_card · pliki: src/pay.py · weryfikacja: `pytest` · po: brak
"""


def main() -> int:
    rs = load(SCRIPTS / "run_state.py", "ps_run_state")
    pd = load(SCRIPTS / "plan_drift.py", "ps_plan_drift")
    tw = load(ROOT / ".tf" / "factory" / "task_weight.py", "ps_task_weight")
    ts = load(ROOT / ".tf" / "factory" / "task_state.py", "ps_task_state")
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    s = rs.plan_with_deps(NEW)
    check([(x["id"], x["checked"], x["deps"]) for x in s] == [("S1", True, []), ("S2", False, ["S1"]), ("S3", False, [])],
          f"PS-1: slices S<n> with `after:` and `none`: {s}")
    check(rs.next_slice(s, set())["id"] == "S2", "PS-2: the next slice after dependencies")
    o = rs.plan_with_deps(OLD)
    check(o == [], f"PS-3: the old slice id K<n> is no longer read: {o}")
    p = pd.parse_plan(NEW)
    check([x["files"] for x in p] == [["src/pay.py", "tests/test_pay.py"], ["src/refund.py"], ["src/report.py"]]
          and p[0]["done"], f"PS-4: plan_drift czyta `files:`: {p}")
    check(pd.parse_plan(OLD) == [] and pd.parse_plan(POLISH)[0]["files"] == [],
          "PS-5: plan_drift does not read a K<n> plan nor the Polish `pliki:`")
    w = tw.plan_slices(NEW)
    check([x["id"] for x in w] == ["S1", "S2", "S3"] and w[0]["files"] == ["src/pay.py", "tests/test_pay.py"],
          f"PS-6: waga zadania czyta S<n> i `files:`: {w}")
    check(ts.SLICE.fullmatch("S12") and not ts.SLICE.fullmatch("K3") and not ts.SLICE.fullmatch("X1"),
          "PS-7: the slice identifier S<n> (not the old K<n>) in tf task commands")
    check(ts.TICKED.sub(rb"\1[ ]\2", NEW.encode()) == NEW.replace("[x] S1", "[ ] S1").encode(),
          "PS-8: ticking S<n> does not change the approved plan hash")
    msg = rs.commit_message("feat(pay): card payment", "S1", "płatność kartą", [])
    check("\n\nSlice S1: płatność kartą\n" in msg, f"PS-9: the commit footer `Slice S<n>:`: {msg!r}")
    old_msg = "feat(pay): card payment\n\nSlice S1: płatność kartą"
    check(rs.commit_message(old_msg, "S1", "płatność kartą", []).count("S1:") == 1,
          "PS-10: the footer `Slice S<n>:` is not added a second time")
    check(tw.plan_slices(OLD) == [], "PS-11: task_weight does not read K<n> slices")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} plan syntax tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
