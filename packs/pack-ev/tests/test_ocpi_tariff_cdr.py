#!/usr/bin/env python3
"""Test end-to-end przykładu examples/ocpi-tariff-cdr: taryfa → CDR → CDR kredytowy → nowy CDR → rozliczenie eMSP.
Pomija się w projekcie bez examples/."""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
EXAMPLE = ROOT / "examples" / "ocpi-tariff-cdr"
CALC = ROOT / ".claude" / "skills" / "dom-ev-tariffs-pricing" / "scripts" / "ocpi_tariff_calc.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if not EXAMPLE.is_dir():
        print("✓ 0/0 testów ocpi-tariff-cdr (pominięte: brak examples/ — przykład nie jest instalowany w projekcie)")
        return 0
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    flow, calc = load("cdr_flow", EXAMPLE / "cdr_flow.py"), load("ocpi_tariff_calc", CALC)
    data = EXAMPLE / "data"
    tariff = json.loads((data / "tariff.json").read_text(encoding="utf-8"))
    fixed = json.loads((data / "tariff-corrected.json").read_text(encoding="utf-8"))
    session = json.loads((data / "session.json").read_text(encoding="utf-8"))

    cdr = flow.make_cdr(tariff, session, "CDR-1001", tz="Europe/Warsaw")
    expected = calc.calculate(tariff, session, "Europe/Warsaw")
    check(cdr["total_cost"] == expected["total_cost"] and cdr["tariffs"] == [tariff] and "credit" not in cdr
          and cdr["charging_periods"] == session["charging_periods"], f"CDR-1: CDR z kosztami z kalkulatora i kopią taryfy: {cdr.get('total_cost')}")
    check(calc.compare(calc.calculate(cdr["tariffs"][0], cdr, "Europe/Warsaw"), cdr) == [],
          "CDR-2: kalkulator potwierdza koszty CDR (--cdr bez rozbieżności)")
    check(cdr["total_parking_cost"] is not None and cdr["total_parking_cost"]["excl_vat"] > 0,
          f"CDR-3: taryfa z błędem nalicza postój w okresie bezpłatnym: {cdr.get('total_parking_cost')}")

    credit = flow.credit_cdr(cdr)
    same = {k: v for k, v in credit.items() if k not in ("id", "credit", "credit_reference_id", "total_cost", "last_updated")}
    check(credit["id"] == "CDR-1001-C" and credit["credit"] is True and credit["credit_reference_id"] == "CDR-1001",
          f"CR-1: CDR kredytowy: nowe id, credit, credit_reference_id: {credit.get('id')}")
    check(credit["total_cost"] == {"excl_vat": -cdr["total_cost"]["excl_vat"], "incl_vat": -cdr["total_cost"]["incl_vat"]}
          and same == {k: v for k, v in cdr.items() if k in same}, "CR-2: ujemny tylko total_cost, reszta danych jak w oryginale")
    check(cdr.get("credit") is None and cdr["total_cost"]["excl_vat"] > 0, "CR-3: oryginał niezmieniony (CDR jest niezmienny)")

    credit2, new = flow.correct(cdr, fixed, tz="Europe/Warsaw")
    check({k: v for k, v in credit2.items() if k != "last_updated"} == {k: v for k, v in credit.items() if k != "last_updated"}
          and new["id"] not in (cdr["id"], credit["id"]) and "credit" not in new
          and new["total_parking_cost"] is None and new["total_cost"]["excl_vat"] < cdr["total_cost"]["excl_vat"],
          f"CR-4: korekta = CDR kredytowy + nowy CDR z poprawną taryfą: {new.get('id')} {new.get('total_cost')}")

    led = flow.EmspLedger()
    check([led.receive(x) for x in (cdr, cdr, credit, new)] == ["accepted", "duplicate", "accepted", "accepted"],
          "EMSP-1: odbiór idempotentny po (country_code, party_id, id)")
    check(led.balance() == new["total_cost"], f"EMSP-2: saldo po korekcie = koszt nowego CDR: {led.balance()}")
    orphan = flow.credit_cdr({**cdr, "id": "NIEZNANY"})
    check(led.receive(orphan) == "rejected: credit_reference_id NIEZNANY nieznany", f"EMSP-3: kredyt do nieznanego CDR odrzucony")
    check(led.receive(flow.credit_cdr(cdr, suffix="-C2")) == "rejected: CDR-1001 już skredytowany",
          "EMSP-4: drugi kredyt tego samego CDR odrzucony")

    with tempfile.TemporaryDirectory() as t:
        out = Path(t) / "cdr.json"
        p = subprocess.run([sys.executable, str(EXAMPLE / "cdr_flow.py"), "make", str(data / "tariff.json"), str(data / "session.json"),
                            "--id", "CDR-2002", "--tz", "Europe/Warsaw"], capture_output=True, text=True)
        out.write_text(p.stdout, encoding="utf-8")
        q = subprocess.run([sys.executable, str(CALC), str(data / "tariff.json"), str(out), "--cdr", str(out), "--tz", "Europe/Warsaw"],
                           capture_output=True, text=True)
        check(p.returncode == 0 and q.returncode == 0, f"CLI-1: cdr_flow.py make → ocpi_tariff_calc.py --cdr zgodne: {p.stderr[-200:]} {q.stdout[-300:]}")
        p = subprocess.run([sys.executable, str(EXAMPLE / "cdr_flow.py"), "credit", str(out)], capture_output=True, text=True)
        check(p.returncode == 0 and json.loads(p.stdout)["credit_reference_id"] == "CDR-2002", f"CLI-2: credit: {p.stderr[-200:]}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów ocpi-tariff-cdr nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów ocpi-tariff-cdr (end-to-end)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
