#!/usr/bin/env python3
"""Testy walidatora struktury rekordów OCMF (skill dom-ev-metering-calibration): format OCMF|payload|podpis, pola
obowiązkowe, dziedziczenie pól odczytów, TM i stan synchronizacji, TX początek/koniec, ST i EF, monotoniczność,
energia rejestru w kWh, kodowanie podpisu, kody wyjścia.

Reguły wg OCMF (S.A.F.E. e.V., OCMF-en.md, github.com/SAFE-eV/OCMF-Open-Charge-Metering-Format, dostęp 2026-10-20;
kopia w bazie wiedzy: `kb.py search OCMF`). Podpisu ECDSA skrypt nie weryfikuje: biblioteka standardowa nie ma ECDSA,
a klucz publiczny przychodzi spoza rekordu (np. z rejestru). Fixture ma własne wartości, wzorowane na przykładzie ze specyfikacji.
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "dom-ev-metering-calibration" / "scripts" / "ocmf_check.py"


def load():
    spec = importlib.util.spec_from_file_location("ocmf_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PAYLOAD = {
    "FV": "1.0", "GI": "SIM-GW", "GS": "GW-0001", "GV": "1.2", "PG": "T42",
    "MV": "SimMeter", "MM": "SM-1", "MS": "MTR-778899", "MF": "2.1",
    "IS": True, "IL": "VERIFIED", "IF": ["RFID_PLAIN"], "IT": "ISO14443", "ID": "04A1B2C3D4E5F6",
    "CT": "EVSEID", "CI": "PL*ABC*E0001",
    "RD": [
        {"TM": "2026-10-20T10:00:00,000+0200 S", "TX": "B", "RV": 1250.125, "RI": "01-0B:01.08.00*FF",
         "RU": "kWh", "RT": "AC", "EF": "", "ST": "G"},
        {"TM": "2026-10-20T10:30:00,000+0200 S", "TX": "C", "RV": 1255.500, "ST": "G"},
        {"TM": "2026-10-20T11:00:00,000+0200 S", "TX": "E", "RV": 1262.375, "ST": "G"},
    ],
}
SIGNATURE = {"SA": "ECDSA-secp256r1-SHA256", "SD": "3045022100AB" + "CD" * 30 + "0220" + "EF" * 32}


def record(payload=None, signature=None, raw_payload=None):
    p = raw_payload if raw_payload is not None else json.dumps(payload if payload is not None else PAYLOAD)
    return f"OCMF|{p}|{json.dumps(signature if signature is not None else SIGNATURE)}"


def mutate(fn):
    p = copy.deepcopy(PAYLOAD)
    fn(p)
    return record(p)


def has(r, code):
    return any(e["code"] == code for e in r["errors"])


def warns(r, code):
    return any(w["code"] == code for w in r["warnings"])


def main() -> int:
    if not SCRIPT.exists():
        print(f"✗ brak {SCRIPT.relative_to(ROOT)}")
        return 1
    m = load()
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # Poprawny rekord
    r = m.check(record())
    check(r["errors"] == [], f"OK-1: poprawny rekord bez błędów: {r['errors']}")
    reg = r["registers"].get("01-0B:01.08.00*FF", {})
    check(reg.get("energy_kwh") == Decimal("12.250"), f"OK-2: energia rejestru = koniec − początek, dokładnie (Decimal): {reg}")
    check(r["readings"][2]["RU"] == "kWh" and r["readings"][2]["RI"] == "01-0B:01.08.00*FF",
          f"OK-3: pola pominięte w kolejnych odczytach dziedziczą wartość poprzedniego: {r['readings'][2]}")
    check(r["signature_verified"] is False and warns(r, "signature-not-verified"),
          "OK-4: wynik mówi wprost, że podpis nie był weryfikowany")
    multiline = "OCMF|" + json.dumps(PAYLOAD, indent=4) + "|" + json.dumps(SIGNATURE, indent=4)
    check(m.check(multiline)["errors"] == [], "OK-5: rekord sformatowany w wielu liniach (jak w specyfikacji) jest poprawny")
    wh = copy.deepcopy(PAYLOAD)
    for x, v in zip(wh["RD"], (1000, 1500, 2500)):
        x["RV"] = v
    wh["RD"][0]["RU"] = "Wh"
    check(m.check(record(wh))["registers"]["01-0B:01.08.00*FF"]["energy_kwh"] == Decimal("1.5"),
          "OK-6: odczyty w Wh przeliczone na kWh")
    two = copy.deepcopy(PAYLOAD)
    two["RD"] = [two["RD"][0], {**two["RD"][2], "RI": "01-0B:01.08.00*FF", "RU": "kWh"},
                 {"TM": "2026-10-20T10:00:00,000+0200 S", "TX": "B", "RV": 0.0, "RI": "01-0B:B3.08.00*FF", "RU": "kWh", "ST": "G"},
                 {"TM": "2026-10-20T11:00:00,000+0200 S", "TX": "E", "RV": 12.0, "ST": "G"}]
    r = m.check(record(two))
    check(r["errors"] == [] and r["registers"]["01-0B:B3.08.00*FF"]["energy_kwh"] == Decimal("12.0"),
          f"OK-7: kilka rejestrów (RI) w jednym rekordzie liczonych osobno: {r['errors']} {r['registers']}")

    # Format
    for code, text in (("format", "OCMX|{}|{}"), ("format", "OCMF|{}"), ("json", "OCMF|{nie json}|{}"),
                       ("json", 'OCMF|[1]|{"SD":"00"}')):
        check(has(m.check(text), code), f"F-{code}: zły format rekordu {text!r} → błąd {code}")
    check(m.check(record(raw_payload=json.dumps({**PAYLOAD, "ID": "a|b"})))["errors"] == [],
          "F-5: znak | w wartości tekstowej payloadu nie psuje podziału sekcji")

    # Pola obowiązkowe
    for key in ("PG", "MS", "IS", "IT", "RD"):
        check(has(m.check(mutate(lambda p, k=key: p.pop(k))), "missing"), f"R-{key}: brak pola obowiązkowego {key}")
    check(has(m.check(record(signature={"SA": "ECDSA-secp256r1-SHA256"})), "missing"), "R-SD: brak SD w sekcji podpisu")
    check(has(m.check(mutate(lambda p: p["RD"][0].pop("TM"))), "missing"), "R-TM: odczyt bez TM")
    check(has(m.check(mutate(lambda p: p["RD"][0].pop("ST"))), "missing"), "R-ST: pierwszy odczyt bez ST (nie ma czego dziedziczyć)")
    check(has(m.check(mutate(lambda p: p["RD"][0].pop("RU"))), "missing"), "R-RU: odczyt z RV bez jednostki RU")
    check(has(m.check(mutate(lambda p: p.update(RD=[]))), "missing"), "R-RD0: pusta lista RD")
    check(has(m.check(mutate(lambda p: p.update(IS="true"))), "type"), "R-IS: IS musi być typu boolean")

    # Wartości pól
    for bad in ("X1", "T", "T01", "t5"):
        check(has(m.check(mutate(lambda p, b=bad: p.update(PG=b))), "value"), f"V-PG: zła paginacja {bad!r}")
    check(has(m.check(mutate(lambda p: p["RD"][0].update(TM="2026-10-20T10:00:00+02:00 S"))), "value"),
          "V-TM: TM musi mieć milisekundy po przecinku i strefę ±hhmm")
    check(has(m.check(mutate(lambda p: p["RD"][0].update(TM="2026-10-20T10:00:00,000+0200"))), "value"),
          "V-TM2: TM bez stanu synchronizacji")
    r = m.check(mutate(lambda p: [x.update(TM=x["TM"][:-1] + "U") for x in p["RD"]]))
    check(r["errors"] == [] and warns(r, "time-unsynchronized"), "V-TM3: czas niesynchronizowany (U) to ostrzeżenie")
    check(has(m.check(mutate(lambda p: p["RD"][1].update(TX="Q"))), "value"), "V-TX: nieznany kod TX")
    check(has(m.check(mutate(lambda p: p["RD"][0].update(RU="kW"))), "value"), "V-RU: jednostka spoza tabeli 20")
    check(has(m.check(mutate(lambda p: p["RD"][0].update(RT="3P"))), "value"), "V-RT: typ prądu spoza AC/DC")
    check(has(m.check(mutate(lambda p: p["RD"][1].update(ST="Z"))), "value"), "V-ST: nieznany stan licznika")
    check(has(m.check(record(signature={"SE": "hex", "SD": "XYZ"})), "value"), "V-SD: SD niezgodne z kodowaniem hex")
    check(m.check(record(signature={"SE": "base64", "SD": "MEUCIQ=="}))["errors"] == [], "V-SD2: SD w base64")
    check(has(m.check(record(signature={"SE": "base32", "SD": "AA"})), "value"), "V-SE: nieznane kodowanie podpisu")
    check(warns(m.check(mutate(lambda p: p.update(QQ=1))), "unknown-field"), "V-EXT: nieznane pole poza U–Z → ostrzeżenie")
    check(not warns(m.check(mutate(lambda p: p.update(XA=1))), "unknown-field"), "V-EXT2: pola producenta U–Z dozwolone")

    # Rozliczalność
    r = m.check(mutate(lambda p: p["RD"][1].update(ST="M")))
    check(has(r, "meter-state"), f"B-1: stan licznika inny niż G (tu M — manipulacja) blokuje rozliczenie: {r['errors']}")
    check(has(m.check(mutate(lambda p: p["RD"][2].update(EF="E"))), "error-flag"), "B-2: EF z E — energia nieużywalna")
    r = m.check(mutate(lambda p: p["RD"][2].update(EF="t")))
    check(not has(r, "error-flag") and warns(r, "error-flag"), "B-3: EF z t — czas nieużywalny to ostrzeżenie dla taryfy energii")
    check(has(m.check(mutate(lambda p: p["RD"][2].update(RV=1200.0))), "monotonic"), "B-4: odczyt energii maleje")
    check(has(m.check(mutate(lambda p: p["RD"][2].update(TM="2026-10-20T09:00:00,000+0200 S"))), "monotonic"),
          "B-5: czas odczytu cofa się")
    check(has(m.check(mutate(lambda p: p["RD"].pop(0))), "transaction"), "B-6: PG=T bez odczytu początkowego TX=B")
    check(has(m.check(mutate(lambda p: p["RD"].pop())), "transaction"), "B-7: PG=T bez odczytu końcowego (E/L/R/A/P)")
    r = m.check(mutate(lambda p: p["RD"][2].update(TX="A")))
    check(r["errors"] == [] and warns(r, "aborted"), "B-8: koniec przez błąd (A) — energia policzona, ostrzeżenie")
    r = m.check(mutate(lambda p: p["RD"][1].update(TX="X")))
    check(has(r, "exception"), "B-9: TX=X — energia od tego odczytu nieużywalna")
    fiscal = copy.deepcopy(PAYLOAD)
    fiscal["PG"] = "F3"
    for x in fiscal["RD"]:
        x.pop("TX")
    check(m.check(record(fiscal))["errors"] == [], "B-10: rekord fiskalny (PG=F) bez TX jest poprawny")
    event = mutate(lambda p: p["RD"].insert(2, {"TM": "2026-10-20T10:45:00,000+0200 S", "ST": "T"}))
    r = m.check(event)
    check(has(r, "meter-state") and r["registers"]["01-0B:01.08.00*FF"]["energy_kwh"] == Decimal("12.250"),
          f"B-11: odczyt-zdarzenie bez RV (tylko ST) nie zmienia energii, ale błąd licznika jest zgłoszony: {r['registers']}")

    # CLI
    with tempfile.TemporaryDirectory() as d:
        ok, bad = Path(d) / "ok.txt", Path(d) / "bad.txt"
        ok.write_text(record(), encoding="utf-8")
        bad.write_text(mutate(lambda p: p["RD"][1].update(ST="M")), encoding="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPT), str(ok)], capture_output=True, text=True)
        check(p.returncode == 0 and "12.25" in p.stdout, f"CLI-1: kod 0 i energia w wyniku: {p.returncode} {p.stdout[-300:]} {p.stderr[-200:]}")
        p = subprocess.run([sys.executable, str(SCRIPT), str(bad)], capture_output=True, text=True)
        check(p.returncode == 1, f"CLI-2: kod 1 przy błędach rekordu: {p.returncode}")
        p = subprocess.run([sys.executable, str(SCRIPT), str(Path(d) / "brak.txt")], capture_output=True, text=True)
        check(p.returncode == 2, f"CLI-3: kod 2 przy braku pliku: {p.returncode}")
        p = subprocess.run([sys.executable, str(SCRIPT), str(ok), "--json"], capture_output=True, text=True)
        try:
            out = json.loads(p.stdout)
            check(out["registers"]["01-0B:01.08.00*FF"]["energy_kwh"] == "12.250", f"CLI-4: --json z energią jako tekst: {out['registers']}")
        except (ValueError, KeyError) as e:
            check(False, f"CLI-4: --json zwraca JSON: {e} {p.stdout[:200]}")
        p = subprocess.run([sys.executable, str(SCRIPT), "-"], input=record(), capture_output=True, text=True)
        check(p.returncode == 0, f"CLI-5: rekord ze stdin: {p.returncode} {p.stderr[-200:]}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów ocmf_check nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów ocmf_check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
