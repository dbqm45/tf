#!/usr/bin/env python3
"""
Odświeżanie rekonstrukcji projektu w dwóch krokach bez modelu. Główny model tylko zleca aktualizacje kart, poprawia
miejsca z listy i zatwierdza wynik — reszta to skrypty (mniej tur, mniejszy kontekst, niższy koszt).

  python3 recon_refresh.py prep <repo> [--dir docs/project/00-reconstruction]
  python3 recon_refresh.py finish <repo> [--dir …] [--cost-usd X]

prep: diff z manifestem (te same partie co w manifeście), kopia wszystkich kart do raw/cards-prev/, zlecenie
raw/refresh/<karta>.md dla każdej karty, której dotyczą zmienione pliki (karta cytuje plik w dowodzie albo jej
`batch` jest najdłuższym prefiksem ścieżki), lista plików bez karty, plan na ekran (≤ 40 linii).
finish: karty → .md, rules.md, sekcja Moduły raportu, zmienione reguły kart (stara → nowa), lista miejsc ze starym
opisem (recon_cards --prev) do raw/refresh/STALE.md, przesunięte dowody (cytat jednoznacznie w innej linii pliku →
nowy numer linii; poza modules/ i raw/), kontrola recon_check --final; gdy przechodzi — nowy manifest. Podsumowanie
≤ 60 linii.
Kod wyjścia: 0 — w porządku (finish: kontrola przeszła), 1 — finish: kontrola nie przeszła, 2 — złe wywołanie.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import recon_cards  # noqa: E402
import recon_check  # noqa: E402
import recon_manifest  # noqa: E402

CARD_RULES = """Zasady karty:
- Każdy element z polem evidence ma `ścieżka:linia` od korzenia repozytorium; reguła ma też quote — dosłowny fragment
  tej linii (sprawdza go skrypt).
- Reguły językiem biznesu, z wartościami: długości, wzorce, zakresy, daty, unikalność; mapowanie (błąd → kod, lista
  błędów, wartości enuma) w całości, z przypadkiem domyślnym i kodem sukcesu. Pewność: test, kod, do potwierdzenia.
- Wejścia: metoda i pełna ścieżka z klasą lub funkcją obsługującą. Dane: encja lub tabela z kluczem i relacjami.
- Czego nie widać w plikach (DI, kolejki, HTTP, konfiguracja zewnętrzna) — do unknowns, bez zgadywania."""


def evidence_paths(obj) -> set[str]:
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "evidence" and isinstance(v, str):
                out.add(re.sub(r":\d+(-\d+)?$", "", v.strip().strip("`")))
            else:
                out |= evidence_paths(v)
    elif isinstance(obj, list):
        for v in obj:
            out |= evidence_paths(v)
    return out


def batch_parts(card: dict) -> list[str]:
    parts = [p.strip().strip("/") for p in re.split(r"[+,;]", str(card.get("batch") or ""))]
    return ["" if p == "." else p for p in parts if p or p == ""]


def covers(part: str, path: str) -> bool:
    if part == "":
        return True
    if "/" not in part:   # krótka nazwa katalogu, np. "owner"
        return path.startswith(part + "/") or f"/{part}/" in path
    return path == part or path.startswith(part + "/")


def map_files(files: list[str], cards: dict) -> tuple[dict, list[str]]:
    """Plik → karty: najpierw karty cytujące plik w dowodzie, potem karta z najdłuższym pasującym `batch`."""
    ev = {stem: evidence_paths(c) for stem, c in cards.items()}
    by_card, orphans = {}, []
    for f in files:
        hit = [s for s in cards if f in ev[s]]
        if not hit:
            best = -1
            for s, c in cards.items():
                for p in batch_parts(c):
                    if covers(p, f) and len(p) > best:
                        best, hit = len(p), [s]
                    elif covers(p, f) and len(p) == best and s not in hit:
                        hit.append(s)
            hit = hit if best > 0 else []   # sam katalog główny nie wystarcza
        if not hit:
            orphans.append(f)
        for s in hit:
            by_card.setdefault(s, []).append(f)
    return by_card, orphans


def load_cards(mods: str) -> dict:
    cards = {}
    for f in sorted(os.listdir(mods)) if os.path.isdir(mods) else []:
        if f.endswith(".json"):
            try:
                with open(os.path.join(mods, f), encoding="utf-8") as fh:
                    c = json.load(fh)
                cards[f[:-5]] = c if isinstance(c, dict) else {}
            except (OSError, ValueError):
                cards[f[:-5]] = {}
    return cards


def task_text(stem: str, card: dict, files: list[str], kinds: dict, rel_dir: str, rel_scripts: str) -> str:
    lines = [f"# Aktualizacja karty modułu {card.get('module') or stem} (odświeżanie przyrostowe)",
             f"Karta: {rel_dir}/modules/{stem}.json · poprzednia wersja: {rel_dir}/raw/cards-prev/{stem}.json", "",
             "Zmienione pliki (czytasz tylko je; z usuniętego pliku reguły usuwasz):"]
    lines += [f"- {f} ({kinds.get(f, 'zmieniony')})" for f in files]
    lines += ["", "Zadanie:",
              "1. Przeczytaj kartę i zmienione pliki. Zaktualizuj tylko elementy karty dotyczące tych plików: popraw",
              "   zmienione reguły, wejścia, dane i pojęcia, dodaj nowe, usuń te, których w kodzie już nie ma. Pozostałe",
              "   elementy zostaw bez zmian (te same słowa i cytaty).",
              "2. Niewiadome i odstępstwa, które wspominają zmieniony fakt, popraw tak, by opisywały stan obecny.",
              "3. Zapisz kartę (sam JSON) i sprawdź ją:",
              f"   python3 {rel_scripts}/recon_cards.py {rel_dir}/modules --repo .",
              f"   python3 {rel_scripts}/recon_check.py {rel_dir}/modules/{stem}.md --repo .",
              "   Złe dowody i cytaty poprawiasz w karcie, aż kontrola da 0 złych.",
              "4. Odpowiadasz jedną linią: ścieżka karty, liczba reguł, wynik kontroli.", "", CARD_RULES]
    return "\n".join(lines) + "\n"


def reanchor(d: str, repo: str) -> int:
    """Dowody z cytatem, który nie pasuje do wskazanej linii, a występuje dokładnie raz w pliku — nowy numer linii."""
    fixed, cache = 0, {}
    for dp, dn, fn in os.walk(d):
        dn[:] = [x for x in dn if x not in ("raw", "modules")]
        for f in fn:
            if not f.endswith(".md"):
                continue
            path = os.path.join(dp, f)
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().split("\n")
            changed = False
            for i, line in enumerate(lines):
                for m in reversed(list(recon_check.REF.finditer(line))):
                    q = recon_check.QUOTE.search(line[m.end():])
                    rel, a = m.group(1), int(m.group(2))
                    b = int(m.group(3) or a)
                    if not q:
                        continue
                    if rel not in cache:
                        try:
                            with open(os.path.join(repo, rel), encoding="utf-8", errors="replace") as fh:
                                cache[rel] = fh.read().splitlines()
                        except OSError:
                            cache[rel] = None
                    src = cache[rel]
                    quote = recon_check.norm(q.group(1) or q.group(2))
                    if not src or quote in recon_check.norm(" ".join(src[max(0, a - 3):b + 2])):
                        continue
                    hits = [n for n, s in enumerate(src, 1) if quote in recon_check.norm(s)]
                    if len(hits) != 1:
                        continue
                    new = f"{rel}:{hits[0]}" + (f"-{hits[0] + b - a}" if m.group(3) else "")
                    line = line[:m.start(1)] + new + line[m.end(3) if m.group(3) else m.end(2):]
                    fixed, changed = fixed + 1, True
                lines[i] = line
            if changed:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("\n".join(lines))
    return fixed


def short(rule: dict | None) -> str:
    return " ".join(str((rule or {}).get("rule", "")).split())[:110]


def prep(repo: str, rel_dir: str) -> int:
    d = os.path.join(repo, rel_dir)
    man = os.path.join(d, "manifest.json")
    if not os.path.isfile(man):
        print(f"✗ brak manifestu: {man} — najpierw pełna rekonstrukcja", file=sys.stderr)
        return 2
    with open(man, encoding="utf-8") as fh:
        old = json.load(fh)
    diff = recon_manifest.diff(old, recon_manifest.snapshot(repo, int(old.get("budget_tokens") or 60000)))
    changed = sorted(set(diff["changed_files"]) | set(diff["tests_changed"]))
    if not changed:
        print("Nic do odświeżenia (manifest zgodny z kodem).")
        return 0
    kinds = {f: "nowy" for f in diff["added_files"]}
    kinds.update({f: "usunięty" for f in diff["removed_files"]})
    kinds.update({f: "test" for f in diff["tests_changed"] if f not in kinds})
    cards = load_cards(os.path.join(d, "modules"))
    by_card, orphans = map_files(changed, cards)
    prev, work = os.path.join(d, "raw", "cards-prev"), os.path.join(d, "raw", "refresh")
    for p in (prev, work):
        shutil.rmtree(p, ignore_errors=True)
        os.makedirs(p)
    for stem in cards:
        shutil.copy(os.path.join(d, "modules", stem + ".json"), os.path.join(prev, stem + ".json"))
    rel_scripts = os.path.relpath(HERE, repo).replace(os.sep, "/")
    for stem, files in sorted(by_card.items()):
        with open(os.path.join(work, stem + ".md"), "w", encoding="utf-8") as fh:
            fh.write(task_text(stem, cards[stem], files, kinds, rel_dir, rel_scripts))
    L = [f"Odświeżanie względem manifestu (commit {old.get('commit') or '—'}): zmienione pliki "
         f"{len(diff['changed_files'])} ({diff['share']}%), testy {len(diff['tests_changed'])}"]
    if diff["share"] > 50:
        L.append("⚠ zmieniło się ponad połowę plików — rozważ pełny przebieg zamiast odświeżania")
    L.append(f"Karty do aktualizacji ({len(by_card)}):")
    L += [f"  {stem} ← {', '.join(files[:4])}{' …' if len(files) > 4 else ''}" for stem, files in sorted(by_card.items())[:25]]
    if orphans:
        L.append(f"Pliki bez karty ({len(orphans)}): {', '.join(orphans[:8])}{' …' if len(orphans) > 8 else ''} "
                 "— dopisz je do najbliższej karty albo zleć nową kartę")
    L += [f"Zlecenia: {rel_dir}/raw/refresh/<karta>.md — wykonawcy (Haiku) w jednej wiadomości, na pierwszym planie;",
          "  każdy dostaje jedno zdanie: „Wykonaj zlecenie z <ścieżka zlecenia>”.",
          f"Stare karty: {rel_dir}/raw/cards-prev/ · potem: python3 {rel_scripts}/recon_refresh.py finish {repo}"]
    print("\n".join(L[:40]))
    return 0


def finish(repo: str, rel_dir: str, cost: str | None) -> int:
    d = os.path.join(repo, rel_dir)
    mods, prev, work = os.path.join(d, "modules"), os.path.join(d, "raw", "cards-prev"), os.path.join(d, "raw", "refresh")
    args = [sys.executable, os.path.join(HERE, "recon_cards.py"), mods, "--repo", repo, "--rules",
            "--into", os.path.join(d, "report.md")]
    if os.path.isdir(prev):
        args += ["--prev", prev]
    cards_out = subprocess.run(args, capture_output=True, text=True).stdout.splitlines()
    stale = [ln for ln in cards_out if ln.startswith("  ") and "[" in ln]
    os.makedirs(work, exist_ok=True)
    with open(os.path.join(work, "STALE.md"), "w", encoding="utf-8") as fh:
        fh.write("# Miejsca, które mogą opisywać stan sprzed zmiany\n"
                 "Każde poprawiasz albo zostawiasz, gdy celowo mówi o starej wartości.\n\n"
                 + "\n".join(f"- {ln.strip()}" for ln in stale) + "\n")
    L = [f"Karty: {next((ln for ln in cards_out if ln.startswith(('✓', '✗'))), '—')}"]
    if os.path.isdir(prev):
        ch = recon_cards.rule_changes(prev, mods)
        L.append(f"Zmienione reguły kart ({len(ch)}):")
        for c in ch[:15]:
            if c["kind"] == "zmieniona":
                L.append(f"  [{c['card']}] {short(c['old'])} → {short(c['new'])}")
            else:
                L.append(f"  [{c['card']}] {c['kind']}: {short(c['old'] or c['new'])}")
    L.append(f"Do sprawdzenia: {len(stale)} miejsc ({rel_dir}/raw/refresh/STALE.md)")
    L += stale[:20]
    L.append(f"przesunięte dowody: {reanchor(d, repo)} poprawionych (cytat znaleziony w innej linii)")
    chk = subprocess.run([sys.executable, os.path.join(HERE, "recon_check.py"), d, "--repo", repo, "--final", "--json"],
                         capture_output=True, text=True)
    try:
        res = json.loads(chk.stdout)
    except ValueError:
        res = {}
    ok = chk.returncode == 0
    if ok:
        L.append(f"Kontrola końcowa: ✓ (dowody {res.get('refs', '?')})")
    else:
        L.append("Kontrola końcowa: ✗ — " + ", ".join(
            f"{k} {len(res.get(k) or [])}" for k in ("bad", "unsupported", "missing_sections", "stack_missing",
                                                      "modules_missing", "cards_stale", "ci_unreferenced") if res.get(k)))
        for b in (res.get("bad") or [])[:5]:
            L.append(f"  ✗ {os.path.relpath(b['at'], d)}: `{b['ref']}` — {b['problem']}")
        for u in (res.get("unsupported") or [])[:5]:
            L.append(f"  ✗ {os.path.relpath(u['at'], d)}: bez dowodu — {u['text'][:90]}")
    man = os.path.join(d, "manifest.json")
    if ok:
        with open(man, encoding="utf-8") as fh:
            old = json.load(fh)
        budget = int(old.get("budget_tokens") or 60000)
        m = {"commit": recon_manifest.commit_of(repo), "date": datetime.date.today().isoformat(), "budget_tokens": budget,
             "cost_usd": float(cost) if cost is not None else old.get("cost_usd"), **recon_manifest.snapshot(repo, budget)}
        with open(man, "w", encoding="utf-8") as fh:
            json.dump(m, fh, ensure_ascii=False, indent=2)
        L.append(f"✓ manifest: {rel_dir}/manifest.json — stan kodu po odświeżeniu")
    else:
        L.append("Manifest bez zmian — najpierw popraw kontrolę i uruchom finish ponownie.")
    print("\n".join(L[:60]))
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    repo = rest[0] if rest and not rest[0].startswith("--") else ""
    rel_dir = recon_manifest.opt(rest, "--dir", "docs/project/00-reconstruction")
    if cmd not in ("prep", "finish") or not os.path.isdir(repo):
        print(f"✗ użycie: prep|finish <repo> [--dir …] (jest: {argv})", file=sys.stderr)
        return 2
    return prep(repo, rel_dir) if cmd == "prep" else finish(repo, rel_dir, recon_manifest.opt(rest, "--cost-usd"))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
