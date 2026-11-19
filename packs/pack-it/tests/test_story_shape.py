#!/usr/bin/env python3
"""The reference set for the story shape from the pdi contract (tests/fixtures/pdi-story-shape/, a copy with labels unchanged)
against check_story() from requirements_lint.py: the rules implemented in tf must give the result from expected.json, the number
of AC units = the scenarios field; a precision and recall report per rule (pdi goal §4.8: ≥ 0.8 and ≥ 0.7).
A mismatch with expected.json is a linter bug or a report to pdi (a contract change) — not a fix of the copy.
python3 tests/test_story_shape.py"""
import importlib.util
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPTS = ROOT / ".claude" / "skills" / "proc-requirements-shaping" / "scripts"
FIX = Path(__file__).resolve().parent / "fixtures" / "pdi-story-shape"
TF_RULES = ["AC-001", "AC-002", "AC-003", "AC-004", "STORY-001", "STORY-002", "STORY-003"]
PRECISION_MIN, RECALL_MIN = 0.8, 0.7


def load_lint():
    spec = importlib.util.spec_from_file_location("requirements_lint", SCRIPTS / "requirements_lint.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def estimate_only(case: dict, story: dict, policy: dict) -> bool:
    """STORY-002 expected only from story points — in tf deliberately without an estimate (a human decision, G2.4)."""
    sp = story.get("story_points")
    return ("STORY-002" in case["fire"] and sp is not None and sp >= policy["maxStoryPoints"]
            and case["scenarios"] <= policy["maxScenarios"])


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    stories = json.loads((FIX / "stories.json").read_text(encoding="utf-8"))
    expected = json.loads((FIX / "expected.json").read_text(encoding="utf-8"))
    vocab = (FIX / "vocabulary.json").read_text(encoding="utf-8")
    check((FIX / "VERSION").read_text(encoding="utf-8").strip() == stories["contract_version"]
          == expected["contract_version"], "SS-V1: VERSION kopii = contract_version zestawu")
    near = SCRIPTS / "story_shape_vocabulary.json"
    check(near.is_file() and json.loads(near.read_text(encoding="utf-8")) == json.loads(vocab),
          "SS-V2: the dictionary next to the script is identical to the set's dictionary (a copy from pdi)")

    lint = load_lint()
    check_story = getattr(lint, "check_story", None)
    if check_story is None:
        fails.append("SS-0: requirements_lint.py has no check_story() function (title, description, ac, story_points, policy)")
        total += 1
    else:
        stats = {r: {"tp": 0, "fp": 0, "fn": 0} for r in TF_RULES}
        skipped = []
        for st in stories["stories"]:
            case = expected["cases"][st["id"]]
            policy = {**expected["policy"], **case.get("policy", {})}
            res = check_story(st["title"], st["description"], st["acceptance_criteria"], st.get("story_points"), policy)
            got = {f["rule"] for f in res["findings"]} & set(TF_RULES)
            want = set(case["fire"]) & set(TF_RULES)
            if estimate_only(case, st, policy):
                want.discard("STORY-002")
                skipped.append(st["id"])
            for r in TF_RULES:
                if r in got or r in want:
                    stats[r]["tp" if r in got and r in want else "fp" if r in got else "fn"] += 1
            check(got == want, f"{st['id']}: rules {sorted(got)} ≠ expected {sorted(want)} — {case.get('note', '')}")
            check(res["scenarios"] == case["scenarios"],
                  f"{st['id']}: jednostek AC {res['scenarios']} ≠ scenarios {case['scenarios']}")
        print("Rule       precision recall    (TP/FP/FN)")
        for r in TF_RULES:
            s = stats[r]
            p = s["tp"] / (s["tp"] + s["fp"]) if s["tp"] + s["fp"] else 1.0
            rc = s["tp"] / (s["tp"] + s["fn"]) if s["tp"] + s["fn"] else 1.0
            print(f"{r:<10} {p:8.2f} {rc:8.2f}  ({s['tp']}/{s['fp']}/{s['fn']})")
            check(p >= PRECISION_MIN and rc >= RECALL_MIN, f"{r}: precision {p:.2f} / recall {rc:.2f} below the goal")
        print(f"Not implemented in tf (STORY-002 only from the estimate): {', '.join(skipped) or '—'}")
        check(skipped == ["SS-07", "SS-31"], f"SS-E: cases only from the estimate: {skipped}")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of the story-shape reference set")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
