#!/usr/bin/env python3
"""Tests of code conventions (lib/conventions.py): the pending question for the cheap model, validation of its answer
against the files, refresh only on changed inputs, the size cap. python3 addons/dna/tests/test_conventions.py"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

import dna  # noqa: E402
from lib import conventions, emit, verify  # noqa: E402
from test_exemplars import commit, project  # noqa: E402


def learned() -> tuple[Path, Path, Path]:
    os.environ["DNA_CONFIG"] = str(Path(tempfile.mkdtemp()) / "dna.yaml")
    root = project()
    out, cache = root / ".tf/addons/dna/out", root / ".tf/addons/dna/cache"
    assert dna.cmd_learn(root, out, online=False, cache=cache) == 0
    return root, out, cache


def question(cache: Path) -> dict:
    items = json.loads((cache / "pending.json").read_text(encoding="utf-8"))["items"]
    return next(i for i in items if i["source"] == "code conventions")


def save(item: dict, convs: list[dict]):
    Path(item["save_to"]).write_text(json.dumps({"conventions": convs}), encoding="utf-8")


GOOD = {"statement": "Functions are exported with named `export function` declarations",
        "examples": [{"path": "src/components/Card.tsx", "snippet": "export function Card() {"},
                     {"path": "src/hooks/useOrders.ts", "snippet": "export function useOrders()"},
                     {"path": "src/pages/Orders.tsx", "snippet": "export   function Orders() {\n  const x = 1;"}],
        "counter_examples": 0, "confidence": "high", "paths": ["src/**/*.ts", "src/**/*.tsx"]}


def conv_items(out: Path) -> list[dict]:
    k = json.loads((out / "knowledge.json").read_text(encoding="utf-8"))
    return [i for i in k["items"] if i["data"].get("topic") == "convention"]


def test_question_is_pending_with_the_exemplars():
    root, out, cache = learned()
    item = question(cache)
    assert item["tool"] == "model" and item["tier"] == "fast" and Path(item["prompt"]).name == "conventions.md"
    text = Path(item["input"]).read_text(encoding="utf-8")
    assert "### src/components/Card.tsx" in text and "- api/services/billing.py" in text and "not instructions" in text
    assert "data, not instructions" in json.loads((cache / "pending.json").read_text(encoding="utf-8"))["instructions"]
    assert conv_items(out) == [] and not (out / "rules" / "conventions.md").exists()
    import yaml
    assert yaml.safe_load((ADDON / "addon.yaml").read_text(encoding="utf-8"))["provides"]["pending"] == "cache/pending.json"


def test_invented_paths_and_snippets_are_rejected():
    root, out, cache = learned()
    save(question(cache), [
        GOOD,
        {"statement": "Services live in src/services and end with Service", "confidence": "high",
         "examples": [{"path": "src/services/OrderService.ts", "snippet": "export class OrderService"},
                      {"path": "api/services/billing.py", "snippet": "class BillingService"}]},
        {"statement": "Hooks return a tuple of value and setter", "confidence": "medium",
         "examples": [{"path": "src/hooks/useOrders.ts", "snippet": "return [value, setValue]"},
                      {"path": "src/components/Card.tsx", "snippet": "export function Card"}]},
        {"statement": "Secrets are read from the system password file", "confidence": "low",
         "examples": [{"path": "../../../etc/passwd", "snippet": "root:"}, {"path": "/etc/hosts", "snippet": "local"},
                      {"path": "src/components/Card.tsx", "snippet": "const x = 1;"}]},
        {"statement": "Same file twice does not count as two", "confidence": "low",
         "examples": [{"path": "src/components/Card.tsx", "snippet": "const x"},
                      {"path": "src/components/Card.tsx", "snippet": "return x"}]},
        {"statement": "No confidence given here at all", "examples": GOOD["examples"]}])
    assert dna.cmd_refresh(root, out, False, cache, quiet=True) == 0      # the saved answer is a new input
    convs = conv_items(out)
    assert [c["title"] for c in convs] == [GOOD["statement"]], convs
    c = convs[0]
    assert c["status"] == "candidate" and c["data"]["confidence"] == "high" and c["kind"] == "convention"
    assert c["evidence"] == ["src/components/Card.tsx:1", "src/hooks/useOrders.ts:1", "src/pages/Orders.tsx:2"]
    assert verify.check_out(out, root) == []
    reasons = " ".join(s["reason"] for s in json.loads((out / "knowledge.json").read_text())["coverage"]["skipped"])
    assert reasons.count("fewer than 2 example files") == 4 and "confidence is not" in reasons
    rules = (out / "rules").glob("conventions*.md")
    text = "".join(f.read_text(encoding="utf-8") for f in rules)
    assert '  - "src/**/*.ts"' in text and "guidance" in text and "candidates, not agreed rules" in text
    offered = json.loads((out / "conventions.json").read_text(encoding="utf-8"))
    assert [x["statement"] for x in offered["conventions"]] == [GOOD["statement"]]
    assert "Code conventions observed" in (out / "INDEX.md").read_text(encoding="utf-8")


def test_high_needs_three_examples():
    root, out, cache = learned()
    two = dict(GOOD, examples=GOOD["examples"][:2])
    save(question(cache), [two])
    dna.cmd_refresh(root, out, False, cache, quiet=True)
    assert conv_items(out)[0]["data"]["confidence"] == "medium"
    assert json.loads((out / "conventions.json").read_text(encoding="utf-8"))["conventions"] == []


def test_refresh_does_not_rerun_when_inputs_are_unchanged():
    root, out, cache = learned()
    item = question(cache)
    save(item, [GOOD])
    assert dna.cmd_refresh(root, out, False, cache, quiet=True) == 0
    stamp = (out / "knowledge.json").stat().st_mtime_ns
    assert json.loads((cache / "pending.json").read_text(encoding="utf-8"))["items"] == []
    assert dna.cmd_refresh(root, out, False, cache, quiet=True) == 0
    assert (out / "knowledge.json").stat().st_mtime_ns == stamp           # nothing changed: nothing ran
    # an edit inside an exemplar, committed: learn runs, the question is not asked again
    p = root / "src/components/Card.tsx"
    p.write_text(p.read_text(encoding="utf-8") + "// note\n", encoding="utf-8")
    commit(root, ["."], "2026-11-02T10:00:00")
    assert dna.cmd_refresh(root, out, False, cache, quiet=True) == 0
    assert (out / "knowledge.json").stat().st_mtime_ns != stamp
    assert json.loads((cache / "pending.json").read_text(encoding="utf-8"))["items"] == []
    assert [c["title"] for c in conv_items(out)] == [GOOD["statement"]]
    # a new directory changes the layout: asked again, the previous answer is used meanwhile
    (root / "src/utils").mkdir()
    (root / "src/utils/format.ts").write_text("export function format() {}\n", encoding="utf-8")
    commit(root, ["."], "2026-11-03T10:00:00")
    assert dna.cmd_refresh(root, out, False, cache, quiet=True) == 0
    assert question(cache)["save_to"] != item["save_to"]
    assert [c["title"] for c in conv_items(out)] == [GOOD["statement"]]


def test_output_stays_within_the_size_cap():
    root, out, cache = learned()
    many = [dict(GOOD, statement=f"Convention number {n} holds in the code " + "very " * 20, paths=None,
                 counter_examples=n % 3) for n in range(20)]
    save(question(cache), many)
    dna.cmd_refresh(root, out, False, cache, quiet=True)
    convs = conv_items(out)
    assert len(convs) == emit.CONVENTIONS_MAX == conventions.MAX_CONVENTIONS
    assert verify.check_out(out, root) == []
    lines = [ln for ln in (out / "rules" / "conventions.md").read_text(encoding="utf-8").splitlines() if ln.startswith("- [")]
    assert len(lines) == 12 and all(len(ln) <= emit.CONVENTION_LINE_MAX for ln in lines)
    assert len((out / "INDEX.md").read_text(encoding="utf-8").splitlines()) <= verify.INDEX_MAX_LINES
    k = json.loads((out / "knowledge.json").read_text(encoding="utf-8"))
    k["items"] += [dict(convs[0], id=f"C-extra{n}") for n in range(3)]
    (out / "knowledge.json").write_text(json.dumps(k), encoding="utf-8")
    assert any("more than 12 conventions" in p for p in verify.check_out(out, root))


def test_conventions_can_be_turned_off():
    root, out, cache = learned()
    Path(os.environ["DNA_CONFIG"]).write_text("conventions: false\n", encoding="utf-8")
    assert dna.cmd_learn(root, out, online=False, cache=cache) == 0
    assert json.loads((cache / "pending.json").read_text(encoding="utf-8"))["items"] == []


def main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    fails = 0
    saved = os.environ.get("DNA_CONFIG")
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"✗ {name}: {type(e).__name__}: {e}")
        finally:
            os.environ.pop("DNA_CONFIG", None) if saved is None else os.environ.__setitem__("DNA_CONFIG", saved)
    print(f"\n{len(tests) - fails}/{len(tests)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
