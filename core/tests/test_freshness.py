#!/usr/bin/env python3
"""Tests of .tf/factory/freshness.py: skill review deadlines (metadata.review) and [unverified] markers."""
import datetime as dt
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "freshness.py").is_file())
SCRIPT = ROOT / ".tf" / "factory" / "freshness.py"
TODAY = dt.date(2026, 10, 17)


def load():
    spec = importlib.util.spec_from_file_location("ctf_freshness", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def skill(root: Path, name: str, due: str | None, body: str = "", meta: bool = True) -> Path:
    d = root / ".claude" / "skills" / name
    d.mkdir(parents=True)
    lines = ["---", f"name: {name}", f"description: Use for {name}."]
    if meta:
        lines += ["metadata:", f'  catalog: "Use for {name}. Not for others (eng-x)."']
        if due:
            lines.append(f"  review: {due}")
    lines += ["---", f"# {name}", body]
    (d / "SKILL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return d / "SKILL.md"


def main() -> int:
    fr = load()
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # the core policy + the intervals a pack adds (pack.yaml -> freshness), e.g. pack-it and pack-ux
    pol = {"default_months": fr.DEFAULT_POLICY["default_months"],
           "prefixes": {**fr.DEFAULT_POLICY["prefixes"], "sec-": 6, "ai-": 6},
           "skills": {**fr.DEFAULT_POLICY["skills"], "sec-eu-regulations": 3, "ai-governance-compliance": 3,
                      "ux-accessibility": 6}}
    check(fr.DEFAULT_POLICY["prefixes"] == {"fw-": 3, "tool-": 3, "lang-": 6} and fr.DEFAULT_POLICY["skills"] == {},
          f"FR-0: the core knows only the technology dimensions: {fr.DEFAULT_POLICY}")
    got = {n: fr.interval(n, pol) for n in ("fw-angular", "tool-nx", "lang-java", "sec-eu-regulations", "ai-evals",
                                            "eng-testing", "ai-governance-compliance", "ux-accessibility")}
    check(got == {"fw-angular": 3, "tool-nx": 3, "lang-java": 6, "sec-eu-regulations": 3, "ai-evals": 6,
                  "eng-testing": 12, "ai-governance-compliance": 3, "ux-accessibility": 6},
          f"FR-1: the interval (months) from the skill's exception, then from the prefix, then the default: {got}")
    check(fr.add_months(dt.date(2026, 11, 30), 3) == dt.date(2027, 2, 28)
          and fr.add_months(dt.date(2026, 10, 17), 12) == dt.date(2027, 10, 17),
          "FR-2: adding months clips the day to the end of the month")

    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        skill(root, "eng-stary", "2026-09-30", "Fakt [unverified]. Drugi [unverified: no source].")
        skill(root, "eng-wkrotce", "2026-11-10")
        skill(root, "eng-aktualny", "2027-06-01")
        skill(root, "eng-bez-daty", None)
        skill(root, "eng-zla-data", "jutro")
        ref = root / ".claude" / "skills" / "eng-aktualny" / "references"
        ref.mkdir()
        (ref / "a.md").write_text("Liczba [unverified]. Number [unverified].\n", encoding="utf-8")
        rows = {r["skill"]: r for r in fr.scan(root, TODAY)}
        check({k: v["status"] for k, v in rows.items()} == {
            "eng-stary": "overdue", "eng-wkrotce": "soon", "eng-aktualny": "ok", "eng-bez-daty": "missing",
            "eng-zla-data": "invalid"}, f"FR-3: states overdue / <=30 days / ok / missing / bad format: {rows}")
        check(rows["eng-stary"]["unverified"] == 2 and rows["eng-aktualny"]["unverified"] == 2,
              f"FR-4: counts [unverified] in SKILL.md and references/: {rows}")

        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--today", "2026-10-17", "--json"],
                           capture_output=True, text=True)
        try:
            data = json.loads(r.stdout)
        except ValueError:
            data = {}
        check(r.returncode == 0 and data.get("summary", {}).get("overdue") == 1
              and len(data.get("skills", [])) == 5, f"FR-5: --json with a summary: {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--today", "2026-10-17", "--strict"],
                           capture_output=True, text=True)
        check(r.returncode == 1 and "eng-stary" in r.stdout, f"FR-6: --strict -> code 1 with overdue skills: {r.stdout}")

        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--today", "2026-10-17",
                            "--reviewed", "eng-stary", "eng-bez-daty"], capture_output=True, text=True)
        a = (root / ".claude" / "skills" / "eng-stary" / "SKILL.md").read_text(encoding="utf-8")
        b = (root / ".claude" / "skills" / "eng-bez-daty" / "SKILL.md").read_text(encoding="utf-8")
        check(r.returncode == 0 and "  review: \"2027-10-17\"\n" in a and a.count("review:") == 1
              and "  review: \"2027-10-17\"\n" in b and "catalog:" in b and b.endswith("# eng-bez-daty\n\n"),
              f"FR-7: --reviewed sets a new deadline (today + the interval), the rest of the file unchanged: {r.stdout}{r.stderr}\n{b}")
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--reviewed", "eng-wkrotce",
                            "--date", "2026-10-03"], capture_output=True, text=True)
        c = (root / ".claude" / "skills" / "eng-wkrotce" / "SKILL.md").read_text(encoding="utf-8")
        check(r.returncode == 0 and "  review: \"2027-10-03\"\n" in c, f"FR-8: --date gives the review day: {c}")
        nometa = skill(root, "eng-bez-metadata", None, meta=False)
        fr.mark_reviewed(nometa, TODAY, 12)
        txt = nometa.read_text(encoding="utf-8")
        check("metadata:\n  review: \"2027-10-17\"\n---\n" in txt, f"FR-9: no metadata section -> added: {txt}")
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--reviewed", "brak"],
                           capture_output=True, text=True)
        check(r.returncode == 2 and "brak" in r.stdout + r.stderr, f"FR-10: unknown skill -> code 2: {r.stdout}{r.stderr}")

    man = ROOT / ".claude" / "factory-manifest.json"     # after installation: only the factory's skills, not the project's own
    ours = {Path(f).parent.name for f in json.loads(man.read_text(encoding="utf-8")).get("files", {})
            if f.startswith(".claude/skills/")} if man.is_file() else None
    real = [r for r in fr.scan(ROOT, TODAY) if r["status"] in ("missing", "invalid")
            and (ours is None or r["skill"] in ours)]
    check(not real, f"FR-11: every factory skill has a valid review deadline: {[r['skill'] for r in real]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} freshness tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
