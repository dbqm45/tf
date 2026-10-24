#!/usr/bin/env python3
"""
Karty modułów (JSON od wykonawców) → czytelne `modules/<karta>.md` z dowodami `plik:linia`, bez modelu. Dzięki temu
dowody i cytaty z kart sprawdza `recon_check.py`, a szczegóły modułów (wejścia, dane, reguły, pojęcia) trafiają do
dokumentacji, nie tylko do JSON. Pierwsza linia .md to skrót treści karty — `recon_check.py --final` porównuje go z kartą.

  python3 recon_cards.py docs/project/00-reconstruction/modules            # zapisuje .md obok kart
  python3 recon_cards.py docs/project/00-reconstruction/modules --summary  # + propozycja sekcji „Moduły” raportu
  python3 recon_cards.py <modules/> --repo <repo>   # dowody ze ścieżką względną wobec partii → ścieżka od korzenia
  python3 recon_cards.py <modules/> --rules         # + rules.md obok modules/: reguły z kart pogrupowane po module
  python3 recon_cards.py <modules/> --into report.md   # sekcja „## Moduły” raportu = wpisy z kart (reszta bez zmian)

Z --repo: gdy pliku z dowodu nie ma od korzenia repo, a w katalogu partii (pole `batch`) jest dokładnie jeden plik
o tej końcówce ścieżki, dowód dostaje pełną ścieżkę. Dwuznaczne zostają bez zmian (zgłosi je recon_check.py).

Element karty bez dowodu dostaje oznaczenie [niezweryfikowane: brak dowodu w karcie], niewiadome — [niezweryfikowane].
Kod wyjścia: 0 — w porządku, 1 — któraś karta nie jest poprawnym JSON, 2 — złe wywołanie.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

NO_EVIDENCE = "[niezweryfikowane: brak dowodu w karcie]"
REF_IN_TEXT = re.compile(r"(?<![\w/.-])((?:[\w.@-]+/)*[\w.@-]+\.[A-Za-z0-9]+:\d+(?:-\d+)?)")


def card_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()[:12]


def resolver(repo: str | None, batch: str):
    """Funkcja poprawiająca dowód `plik:linia` względny wobec partii na ścieżkę od korzenia repo."""
    if not repo or not batch:
        return lambda e: e
    files = []
    for dp, dn, fn in os.walk(os.path.join(repo, batch)):
        dn[:] = [x for x in dn if x != ".git"]
        files += [os.path.relpath(os.path.join(dp, f), repo).replace(os.sep, "/") for f in fn]

    def fix(e: str) -> str:
        m = re.match(r"^(.+?):(\d+(?:-\d+)?)$", e)
        if not m or os.path.exists(os.path.join(repo, m.group(1))):
            return e
        path = m.group(1).lstrip("./")
        hits = [f for f in files if f.endswith("/" + path)]
        return f"{hits[0]}:{m.group(2)}" if len(hits) == 1 else e
    return fix


def ev(item: dict, fix=lambda e: e) -> str:
    e = str(item.get("evidence") or "").strip().strip("`")
    return f"— `{fix(e)}`" if e else NO_EVIDENCE


def quote(q: str) -> str:
    return f"„{q}”" if '"' in q else f'"{q}"'


def rule_line(i: dict, fix) -> str:
    line = f"- {i.get('rule', '?')} {ev(i, fix)}"
    if i.get("evidence") and i.get("quote"):
        line += f" {quote(str(i['quote']))}"
    return line + (f" (pewność: {i['confidence']})" if i.get("confidence") else "")


def render(stem: str, card: dict, digest: str, repo: str | None = None) -> str:
    fix = resolver(repo, str(card.get("batch") or ""))
    out = [f"<!-- karta: modules/{stem}.json sha256:{digest} -->", f"# {card.get('module') or stem}", ""]
    if card.get("purpose"):
        out += [str(card["purpose"]), ""]

    def section(title: str, items: list, fmt) -> None:
        rows = [fmt(i) for i in items or [] if isinstance(i, dict)]
        if rows:
            out.extend([f"## {title}", *rows, ""])

    section("Wejścia", card.get("entry_points"), lambda i: f"- {i.get('what', '?')} {ev(i, fix)}")
    section("Zależności", card.get("depends_on"), lambda i: f"- {i.get('module', '?')} {ev(i, fix)}")
    section("Dane", card.get("data"), lambda i: f"- {i.get('table', '?')} ({i.get('access', '?')}) {ev(i, fix)}")

    section("Reguły", card.get("rules"), lambda i: rule_line(i, fix))
    section("Pojęcia", card.get("terms"), lambda i: f"- {i.get('term', '?')} → {i.get('code_name', '?')} {ev(i, fix)}")
    section("Odstępstwa", card.get("deviations"), lambda i: f"- {i.get('what', '?')} {ev(i, fix)}")
    unknowns = [f"- [niezweryfikowane] {REF_IN_TEXT.sub(lambda m: fix(m.group(1)), str(u))}"
                for u in card.get("unknowns") or [] if str(u).strip()]
    if unknowns:
        out.extend(["## Niewiadome", *unknowns, ""])
    return "\n".join(out).rstrip() + "\n"


def summary(stem: str, card: dict, repo: str | None = None) -> str:
    """Wpis do sekcji „Moduły” raportu: cel, pierwszy dowód, do 4 kluczowych elementów, odnośnik do .md."""
    first = next((i for k in ("entry_points", "rules", "terms", "depends_on", "data", "deviations")
                  for i in card.get(k) or [] if isinstance(i, dict) and i.get("evidence")), None)
    keys = ([i.get("what") for i in card.get("entry_points") or [] if isinstance(i, dict)][:3]
            + [i.get("code_name") for i in card.get("terms") or [] if isinstance(i, dict)][:2]
            + [i.get("table") for i in card.get("data") or [] if isinstance(i, dict)][:2])
    keys = [str(k) for k in keys if k][:4]
    fix = resolver(repo, str(card.get("batch") or ""))
    line = f"- {card.get('module') or stem}: {card.get('purpose') or '?'} {ev(first, fix) if first else NO_EVIDENCE}"
    if keys:
        line += f" · kluczowe: {', '.join(keys)}"
    return line + f" (szczegóły: modules/{stem}.md)"


def inject(report: str, lines: list[str]) -> int:
    """Podmienia treść sekcji „## Moduły” w raporcie na wpisy z kart; zwraca 1, gdy raportu albo sekcji brak."""
    try:
        with open(report, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        print(f"✗ {report}: brak pliku raportu")
        return 1
    m = re.search(r"^## Moduły[^\n]*\n", text, re.M)
    if not m:
        print(f"✗ {report}: brak sekcji „## Moduły”")
        return 1
    nxt = re.search(r"^#{1,2} ", text[m.end():], re.M)
    end = m.end() + nxt.start() if nxt else len(text)
    body = "\n".join(lines) + "\n" + ("\n" if nxt else "")
    with open(report, "w", encoding="utf-8") as fh:
        fh.write(text[:m.end()] + body + text[end:])
    print(f"✓ {report}: sekcja Moduły — {len(lines)} wpisów z kart")
    return 0


def main(argv: list[str]) -> int:
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    repo, into, paths, it = None, None, [], iter(argv)
    for a in it:
        if a == "--repo":
            repo = next(it, None)
        elif a == "--into":
            into = next(it, None)
        elif not a.startswith("--"):
            paths.append(a)
    if len(paths) != 1 or not os.path.isdir(paths[0]) or (repo is not None and not os.path.isdir(repo)):
        print(f"✗ podaj katalog kart modules/ (jest: {paths})", file=sys.stderr)
        return 2
    d, rc, written, lines, rules = paths[0], 0, 0, [], []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"):
            continue
        stem, path = f[:-5], os.path.join(d, f)
        with open(path, "rb") as fh:
            raw = fh.read()
        try:
            card = json.loads(raw.decode("utf-8"))
            if not isinstance(card, dict):
                raise ValueError("karta nie jest obiektem JSON")
        except (ValueError, UnicodeDecodeError) as e:
            print(f"✗ {f}: niepoprawna karta ({e})")
            rc = 1
            continue
        text = render(stem, card, card_hash(raw), repo)
        md = os.path.join(d, stem + ".md")
        try:
            with open(md, encoding="utf-8") as fh:
                same = fh.read() == text
        except OSError:
            same = False
        if not same:
            with open(md, "w", encoding="utf-8") as fh:
                fh.write(text)
            written += 1
        lines.append(summary(stem, card, repo))
        fix = resolver(repo, str(card.get("batch") or ""))
        items = [rule_line(i, fix) for i in card.get("rules") or [] if isinstance(i, dict)]
        if items:
            rules += ["", f"## {card.get('module') or stem} (szczegóły: modules/{stem}.md)", *items]
    print(f"{'✓' if rc == 0 else '✗'} karty → .md: {len(lines)}, zapisane od nowa: {written}")
    if "--rules" in argv:
        head = ["# Reguły z kart modułów",
                "Złożone skryptem z `modules/*.json`; reguły przekrojowe i mapowania dopisuje synteza poniżej."]
        with open(os.path.join(os.path.dirname(os.path.abspath(d)), "rules.md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(head + rules) + "\n")
    if into:
        rc = max(rc, inject(into, lines))
    if "--summary" in argv:
        print("\n## Moduły (propozycja do raportu)")
        print("\n".join(lines))
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
