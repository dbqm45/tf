#!/usr/bin/env python3
"""Testy build.py: skille bez roli i persony (standalone_skills), zasada delegowania w prompcie orkiestratora."""
import importlib.util
import re
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "factory" / "build.py").is_file())


def load():
    spec = importlib.util.spec_from_file_location("ctf_build", ROOT / "factory" / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if importlib.util.find_spec("yaml") is None:          # build.py wymaga PyYAML; w projekcie bywa nieinstalowany
        print("✓ 0/0 testów build.py (brak PyYAML — pominięto)")
        return 0
    b = load()
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    skills = ["a", "b", "dom-x"]
    errors, warnings = b.skill_usage(skills, {"a"}, {})
    check(errors == [] and len(warnings) == 2 and all("nie jest używany" in w for w in warnings),
          f"SU-1: nieużywane skille → ostrzeżenia: {errors} {warnings}")
    errors, warnings = b.skill_usage(skills, {"a"}, {"standalone_skills": ["dom-x"]})
    check(errors == [] and warnings == ["skill b: nie jest używany przez żadną rolę ani personę"],
          f"SU-2: skill samodzielny bez ostrzeżenia: {errors} {warnings}")
    errors, _ = b.skill_usage(skills, {"a"}, {"standalone_skills": ["brak"]})
    check(errors == ["standalone_skills: nieznany skill 'brak'"], f"SU-3: nieznany skill samodzielny → błąd: {errors}")
    _, warnings = b.skill_usage(skills, {"a", "dom-x"}, {"standalone_skills": ["dom-x"]})
    check(any("dom-x" in w and "standalone_skills" in w for w in warnings),
          f"SU-4: skill samodzielny używany przez personę → ostrzeżenie o zbędnym wpisie: {warnings}")

    # Budżet listy skilli liczony jak w projekcie (skill_profile): technologie i dom-* bez opisu, plus rezerwa
    # na technologie wykryte w typowym projekcie (N najdłuższych wpisów technologii).
    entries = {"eng-a": 100, "core-b": 50, "dom-x": 400, "fw-angular": 300, "lang-java": 200, "tool-nx": 120}
    check(b.skill_listing(entries, 2) == 100 + 50 + 300 + 200,
          f"LB-1: opisane skille + 2 najdłuższe technologie, bez dom-*: {b.skill_listing(entries, 2)}")
    check(b.skill_listing(entries, 0) == 150, f"LB-2: bez rezerwy technologii: {b.skill_listing(entries, 0)}")

    # Termin przeglądu (metadata.przeglad): format daty sprawdzany; zmiana samego terminu nie unieważnia bramki.
    check(b.check_review_date("eng-a", {"przeglad": "2027-04-17"}) == ([], []), "RD-1: poprawna data bez uwag")
    errors, _ = b.check_review_date("eng-a", {"przeglad": "kwiecień"})
    check(len(errors) == 1 and "przeglad" in errors[0], f"RD-2: zły format daty → błąd: {errors}")
    errors, warnings = b.check_review_date("eng-a", {})
    check(errors == [] and len(warnings) == 1 and "freshness.py" in warnings[0],
          f"RD-3: brak terminu → ostrzeżenie z poleceniem: {warnings}")
    with tempfile.TemporaryDirectory() as t:
        old = b.SKILLS_DIR
        b.SKILLS_DIR = Path(t)
        md = Path(t) / "eng-odcisk" / "SKILL.md"
        md.parent.mkdir()
        head = "---\nname: eng-odcisk\nmetadata:\n  katalog: \"x\"\n  przeglad: {}\n---\n# Treść\n"
        md.write_text(head.format("2026-10-17"))
        f1 = b.skill_fingerprint("eng-odcisk")
        md.write_text(head.format("2027-10-17"))
        f2 = b.skill_fingerprint("eng-odcisk")
        md.write_text(head.format("2027-10-17") + "Nowy akapit.\n")
        f3 = b.skill_fingerprint("eng-odcisk")
        b.SKILLS_DIR = old
    check(f1 == f2 and f2 != f3, f"RD-4: odcisk bramki pomija termin przeglądu, ale nie treść: {f1} {f2} {f3}")

    # Liczby w README generowane przez build.py (linia „skills/ N skilli w M wymiarach”).
    line = "  skills/                  148 skilli w 17 wymiarach: ddd-*, arch-*"
    check(b.readme_counts(line, 149, 18) == "  skills/                  149 skilli w 18 wymiarach: ddd-*, arch-*",
          f"RC-1: build podmienia liczbę skilli i wymiarów: {b.readme_counts(line, 149, 18)}")
    check(len(b.readme_count_errors(line, 149, 18)) == 1 and b.readme_count_errors(line, 148, 17) == []
          and b.readme_count_errors("brak linii", 149, 18) == [], "RC-2: check zgłasza rozjazd liczb w README")

    # Orkiestrator robi zadanie sam; deleguje tylko, gdy przekazanie się opłaca (koszt i jakość).
    rendered = b.render_all()
    orchestrators = {k: v for k, v in rendered.items() if not k.startswith("shared/")
                     and Path(k).stem == Path(k).parent.name}
    check(orchestrators, "OR-0: są prompty orkiestratorów")
    for k, t in orchestrators.items():
        check("Resztę delegujesz" not in t, f"OR-1 {k}: nie ma już zasady „resztę delegujesz”")
        check("Domyślnie robisz zadanie sam" in t, f"OR-2 {k}: zasada domyślna — zadanie robisz sam")
        sec = re.search(r"^## Kiedy delegujesz\n(.*?)(?=^## )", t, re.M | re.S)
        body = sec.group(1) if sec else ""
        check(sec and all(w in body for w in ("scout", "równolegle", "świeże spojrzenie", "Nie dziel")),
              f"OR-3 {k}: sekcja „Kiedy delegujesz” z przypadkami, w których przekazanie się opłaca")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów build.py")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
