#!/usr/bin/env python3
"""
Kopie kontraktu pdi w tf: przypięte do wersji, generowane z tagu wydania, nigdy edytowane ręcznie.

  python3 tools/sync_contract.py sync  [--pin tools/pdi-contract.json] [--source DIR]
      pobiera pliki z tagu contract-v<wersja> w repo z przypięcia (albo z katalogu DIR = katalog contract/)
      i zapisuje je we wszystkich miejscach z przypięcia; pliki z version_files dostają numer wersji
  python3 tools/sync_contract.py check [--pin …] [--source DIR]
      porównuje kopie bajt w bajt ze źródłem; kod 1 i lista rozjazdów, gdy coś się różni

Aktualizacja kontraktu: zmień "version" w przypięciu, uruchom sync, testy, PR. Kod wyjścia: 0 — zgodne/zapisane,
1 — rozjazd albo brak pliku w źródle, 2 — złe przypięcie lub wywołanie. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIN = ROOT / "tools" / "pdi-contract.json"
KEYS = {"repo", "version", "files", "version_files"}
RAW = "https://raw.githubusercontent.com/{repo}/contract-v{version}/contract/{name}"


class PinError(Exception):
    pass


def load_pin(path: Path) -> dict:
    try:
        pin = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise PinError(f"nie mogę odczytać przypięcia {path}: {e}") from e
    extra = set(pin) - KEYS
    if extra or not {"repo", "version", "files"} <= set(pin):
        raise PinError(f"{path}: klucze {sorted(KEYS)} (nieznane: {sorted(extra)})")
    if not isinstance(pin["files"], dict) or not all(isinstance(v, list) and v for v in pin["files"].values()):
        raise PinError(f"{path}: files to mapa plik kontraktu → lista miejsc w repo")
    return pin


def fetch(pin: dict, name: str, source: Path | None) -> bytes | None:
    if source is not None:
        f = source / name
        return f.read_bytes() if f.is_file() else None
    url = RAW.format(repo=pin["repo"], version=pin["version"], name=name)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:  # noqa: S310 — stały adres GitHuba z przypięcia
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def expected(pin: dict, source: Path | None, base: Path) -> tuple[dict[Path, bytes], list[str]]:
    want, missing = {}, []
    for name, dests in pin["files"].items():
        data = fetch(pin, name, source)
        if data is None:
            missing.append(name)
            continue
        for d in dests:
            want[base / d] = data
    for d in pin.get("version_files", []):
        want[base / d] = f"{pin['version']}\n".encode()
    return want, missing


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["sync", "check"])
    ap.add_argument("--pin", type=Path, default=PIN)
    ap.add_argument("--source", type=Path, help="katalog contract/ zamiast pobierania z tagu (testy, praca bez sieci)")
    a = ap.parse_args(argv)
    try:
        pin = load_pin(a.pin)
    except PinError as e:
        print(f"✗ {e}")
        return 2
    # ścieżki w przypięciu tf są względem katalogu głównego repo; inne przypięcie (testy) — względem swojego katalogu
    base = ROOT if a.pin.resolve() == PIN else a.pin.resolve().parent
    where = a.source or f"tag contract-v{pin['version']} w {pin['repo']}"
    want, missing = expected(pin, a.source, base)
    if missing:
        print(f"✗ brak w źródle ({where}): {', '.join(missing)}")
        return 1
    if a.cmd == "sync":
        for path, data in want.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        print(f"✓ zapisano {len(want)} kopii kontraktu {pin['version']} ({where})")
        return 0
    bad = [str(p.relative_to(base)) for p, data in want.items() if not p.is_file() or p.read_bytes() != data]
    if bad:
        print(f"✗ kopie różne od kontraktu {pin['version']} ({where}) — nie edytuj ich ręcznie, uruchom "
              f"`python3 tools/sync_contract.py sync`:")
        for b in bad:
            print(f"  - {b}")
        return 1
    print(f"✓ {len(want)} kopii zgodnych z kontraktem {pin['version']} ({where})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
