#!/usr/bin/env python3
"""
Walidator struktury rekordu OCMF (Open Charge Metering Format, S.A.F.E. e.V.) — podpisanego odczytu licznika
z ładowarki (Eichrecht, OCPP `signedMeterValue`, OCPI `signed_data`). Tylko biblioteka standardowa. Sieć: brak.

  python3 .claude/skills/dom-ev-metering-calibration/scripts/ocmf_check.py <plik|-> [--json]

Sprawdza: format `OCMF|<payload JSON>|<podpis JSON>`, pola obowiązkowe (PG, MS, IS, IT, RD; w odczycie TM, RV, RU, ST;
w podpisie SD), wartości z tabel specyfikacji (TX, RU, RT, ST, stan czasu w TM), paginację, kodowanie SD, odczyt
początkowy i końcowy transakcji, monotoniczność odczytów i czasu w rejestrze, stan licznika i flagi błędów, energię
rejestru (koniec − początek) w kWh liczoną na Decimal bez zmiany zapisu liczby.

Dziedziczenie: pole pominięte w odczycie ma wartość z poprzedniego odczytu tego rekordu (TX, RI, RU, RT, EF, ST).
TM, RV i CL się nie dziedziczą; odczyt bez RV to zdarzenie licznika (np. błąd), które nie zmienia energii.

Podpis NIE jest weryfikowany: biblioteka standardowa nie ma ECDSA, a klucz publiczny przychodzi spoza rekordu
(rejestr, transparency software). Rekord bez błędów strukturalnych nie jest jeszcze dowodem rozliczeniowym.

Kod wyjścia: 0 — brak błędów, 1 — błędy w rekordzie, 2 — nie da się odczytać pliku.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import datetime as dt
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

PAYLOAD_KEYS = {"FV", "GI", "GS", "GV", "PG", "MV", "MM", "MS", "MF", "IS", "IL", "IF", "IT", "ID", "TT", "LC", "CT", "CI", "RD"}
REQUIRED = ("PG", "MS", "IS", "IT", "RD")
SIGNATURE_KEYS = {"SA", "SE", "SM", "SD"}
INHERITED = ("TX", "RI", "RU", "RT", "EF", "ST")
TX = {"B", "C", "X", "E", "L", "R", "A", "P", "S", "T"}
TX_END = {"E", "L", "R", "A", "P"}
UNITS = {"kWh": Decimal(1), "Wh": Decimal("0.001"), "mOhm": None, "uOhm": None}
CURRENT = {"AC", "DC"}
METER_STATE = {"N": "NOT_PRESENT", "G": "OK", "T": "TIMEOUT", "D": "DISCONNECTED", "R": "NOT_FOUND", "M": "MANIPULATED",
               "X": "EXCHANGED", "I": "INCOMPATIBLE", "O": "OUT_OF_RANGE", "S": "SUBSTITUTE", "E": "OTHER_ERROR",
               "F": "READ_ERROR"}
ALGORITHMS = {f"ECDSA-{c}{h}" for c in ("secp192k1", "secp256k1", "secp192r1", "secp256r1", "brainpool256r1",
                                         "secp384r1", "brainpool384r1") for h in ("-SHA256", "")}
TM_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}),(\d{3})([+-]\d{2})(\d{2}) ([UISR])$")
PG_RE = re.compile(r"^[TF](0|[1-9]\d*)$")
FV_RE = re.compile(r"^\d+\.\d+$")


def _number(v) -> bool:
    return isinstance(v, (int, Decimal)) and not isinstance(v, bool)


def _parse_tm(v):
    m = TM_RE.match(v) if isinstance(v, str) else None
    if not m:
        return None, None
    try:
        t = dt.datetime.fromisoformat(f"{m[1]}.{m[2]}{m[3]}:{m[4]}")
    except ValueError:
        return None, None
    return t, m[5]


def split(text: str):
    """(payload, podpis) albo wyjątek ValueError z kodem 'format' / 'json'."""
    s = text.strip()
    if not s.startswith("OCMF|"):
        raise ValueError("format", "rekord musi zaczynać się od 'OCMF|'")
    dec = json.JSONDecoder(parse_float=Decimal)
    rest = s[5:].lstrip()
    try:
        payload, end = dec.raw_decode(rest)
    except json.JSONDecodeError as e:
        raise ValueError("json", f"payload nie jest poprawnym JSON: {e}") from e
    rest = rest[end:].strip()
    if not rest.startswith("|"):
        raise ValueError("format", "brak sekcji podpisu po payloadzie (OCMF|payload|podpis)")
    try:
        signature = dec.decode(rest[1:].strip())
    except json.JSONDecodeError as e:
        raise ValueError("json", f"sekcja podpisu nie jest poprawnym JSON: {e}") from e
    if not isinstance(payload, dict) or not isinstance(signature, dict):
        raise ValueError("json", "payload i podpis muszą być obiektami JSON")
    return payload, signature


def check(text: str) -> dict:
    errors, warnings = [], []

    def err(code, msg, where=""):
        errors.append({"code": code, "msg": msg, "where": where})

    def warn(code, msg, where=""):
        if not any(w["code"] == code and w["where"] == where for w in warnings):
            warnings.append({"code": code, "msg": msg, "where": where})

    result = {"errors": errors, "warnings": warnings, "readings": [], "registers": {}, "signature_verified": False}
    warn("signature-not-verified", "podpis nie był weryfikowany — potrzebny klucz publiczny licznika i narzędzie ECDSA")
    try:
        payload, signature = split(text)
    except ValueError as e:
        err(e.args[0], e.args[1])
        return result

    for k in REQUIRED:
        if k not in payload:
            err("missing", f"brak pola obowiązkowego {k}", k)
    for k in payload:
        if k not in PAYLOAD_KEYS and k[:1] not in "UVWXYZ":
            warn("unknown-field", f"nieznane pole {k} (pola producenta zaczynają się od U–Z)", k)
    if "FV" in payload and not (isinstance(payload["FV"], str) and FV_RE.match(payload["FV"])):
        err("value", f"FV ma format <major>.<minor>: {payload['FV']!r}", "FV")
    pg = payload.get("PG")
    if pg is not None and not (isinstance(pg, str) and PG_RE.match(pg)):
        err("value", f"PG to litera T lub F i numer bez zer wiodących: {pg!r}", "PG")
    if "IS" in payload and not isinstance(payload["IS"], bool):
        err("type", f"IS musi być true/false, jest {payload['IS']!r}", "IS")
    elif payload.get("IS") is False:
        warn("user-not-assigned", "IS=false: użytkownik nieprzypisany do rekordu", "IS")

    raw = payload.get("RD")
    if "RD" in payload and (not isinstance(raw, list) or not raw):
        err("missing", "RD musi być niepustą listą odczytów", "RD")
        raw = []
    readings, prev = [], {}
    for i, r in enumerate(raw or []):
        where = f"RD[{i}]"
        if not isinstance(r, dict):
            err("type", "odczyt musi być obiektem", where)
            continue
        x = {k: prev[k] for k in INHERITED if k in prev}
        x.update(r)
        prev = x
        readings.append(x)
        t, sync = _parse_tm(x.get("TM"))
        if "TM" not in x:
            err("missing", "odczyt bez TM", where)
        elif t is None:
            err("value", f"TM ma format RRRR-MM-DDThh:mm:ss,mmm±hhmm <U|I|S|R>: {x['TM']!r}", where)
        elif sync == "U":
            warn("time-unsynchronized", "czas licznika niesynchronizowany (U) — nie nadaje się do taryfy czasowej", where)
        elif sync == "I":
            warn("time-informative", "czas informacyjny (I) — nie nadaje się do taryfy czasowej", where)
        x["_t"] = t
        if "ST" not in x:
            err("missing", "odczyt bez ST", where)
        elif x["ST"] not in METER_STATE:
            err("value", f"nieznany stan licznika ST={x['ST']!r}", where)
        elif x["ST"] != "G":
            err("meter-state", f"stan licznika {x['ST']} ({METER_STATE[x['ST']]}) — odczyt nie nadaje się do rozliczenia", where)
        if "TX" in x and x["TX"] not in TX:
            err("value", f"nieznany kod TX={x['TX']!r}", where)
        if "RT" in x and x["RT"] not in CURRENT:
            err("value", f"RT musi być AC albo DC: {x['RT']!r}", where)
        if "RU" in x and x["RU"] not in UNITS:
            err("value", f"jednostka RU={x['RU']!r} spoza tabeli (kWh, Wh, mOhm, uOhm)", where)
        ef = x.get("EF", "")
        if not isinstance(ef, str) or set(ef) - {"E", "t"}:
            err("value", f"EF może zawierać tylko E i t: {ef!r}", where)
        elif "E" in ef:
            err("error-flag", "EF zawiera E — energia z tego odczytu nie nadaje się do rozliczenia", where)
        elif "t" in ef:
            warn("error-flag", "EF zawiera t — czas nie nadaje się do rozliczenia (taryfa energii nadal możliwa)", where)
        if "RV" in x:
            if not _number(x["RV"]):
                err("type", f"RV musi być liczbą: {x['RV']!r}", where)
            elif "RU" not in x:
                err("missing", "odczyt z RV bez jednostki RU", where)
        x["_i"] = i

    transactional = isinstance(pg, str) and pg.startswith("T")
    registers: dict = {}
    for x in readings:
        registers.setdefault(x.get("RI"), []).append(x)
    for ri, rows in registers.items():
        vals = [x for x in rows if _number(x.get("RV"))]
        name = ri or "(bez RI)"
        for a, b in zip(rows, rows[1:]):
            if a["_t"] and b["_t"] and b["_t"] < a["_t"]:
                err("monotonic", f"czas odczytu cofa się w rejestrze {name}", f"RD[{b['_i']}]")
        energy = [x for x in vals if UNITS.get(x.get("RU"))]
        for a, b in zip(energy, energy[1:]):
            if b["RV"] * UNITS[b["RU"]] < a["RV"] * UNITS[a["RU"]]:
                err("monotonic", f"odczyt energii maleje w rejestrze {name}", f"RD[{b['_i']}]")
        if not vals:
            continue
        first, last = vals[0], vals[-1]
        if transactional:
            if first.get("TX") != "B":
                err("transaction", f"rejestr {name}: pierwszy odczyt transakcji musi mieć TX=B", f"RD[{first['_i']}]")
            if last.get("TX") not in TX_END:
                err("transaction", f"rejestr {name}: brak odczytu końcowego (TX E, L, R, A albo P)", f"RD[{last['_i']}]")
            elif last["TX"] in ("A", "P"):
                warn("aborted", f"rejestr {name}: transakcja przerwana ({last['TX']}) — sprawdź, czy rozliczać", f"RD[{last['_i']}]")
            for x in vals:
                if x.get("TX") == "X":
                    err("exception", "TX=X — czas i energia od tego odczytu nie nadają się do rozliczenia", f"RD[{x['_i']}]")
                    break
        reg = {"unit": last.get("RU"), "begin": first["RV"], "end": last["RV"], "readings": len(rows)}
        if UNITS.get(first.get("RU")) and UNITS.get(last.get("RU")):
            reg["energy_kwh"] = last["RV"] * UNITS[last["RU"]] - first["RV"] * UNITS[first["RU"]]
        result["registers"][ri] = reg

    if "SD" not in signature:
        err("missing", "brak SD (dane podpisu) w sekcji podpisu", "SD")
    for k in signature:
        if k not in SIGNATURE_KEYS and k[:1] not in "UVWXYZABCDEF":
            warn("unknown-field", f"nieznane pole podpisu {k}", k)
    se = signature.get("SE", "hex")
    sd = signature.get("SD")
    if se not in ("hex", "base64"):
        err("value", f"SE musi być hex albo base64: {se!r}", "SE")
    elif isinstance(sd, str):
        try:
            if se == "hex":
                bytes.fromhex(sd)
            else:
                base64.b64decode(sd, validate=True)
        except (ValueError, binascii.Error):
            err("value", f"SD nie jest poprawnym zapisem {se}", "SD")
    elif sd is not None:
        err("type", "SD musi być tekstem", "SD")
    if "SA" in signature and signature["SA"] not in ALGORITHMS:
        warn("unknown-algorithm", f"algorytm spoza specyfikacji: {signature['SA']!r}", "SA")

    result["readings"] = [{k: v for k, v in x.items() if not k.startswith("_")} for x in readings]
    return result


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Walidacja struktury rekordu OCMF (bez weryfikacji podpisu).")
    ap.add_argument("record", help="plik z rekordem OCMF albo - dla stdin")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        text = sys.stdin.read() if args.record == "-" else Path(args.record).read_text(encoding="utf-8")
    except OSError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    r = check(text)
    if args.json:
        out = {**r, "registers": {str(k): v for k, v in r["registers"].items()}}
        print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    else:
        for ri, reg in r["registers"].items():
            e = f"{reg['energy_kwh']} kWh" if "energy_kwh" in reg else f"{reg['begin']} → {reg['end']} {reg['unit']}"
            print(f"  rejestr {ri or '(bez RI)'}: {e} ({reg['readings']} odczytów)")
        for mark, key in (("✗", "errors"), ("⚠", "warnings")):
            for x in r[key]:
                print(f"  {mark} [{x['code']}] " + (f"{x['where']}: " if x["where"] else "") + x["msg"])
        print("✓ struktura poprawna" if not r["errors"] else f"✗ błędów: {len(r['errors'])}")
    return 1 if r["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
