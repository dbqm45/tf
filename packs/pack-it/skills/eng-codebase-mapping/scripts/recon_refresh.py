#!/usr/bin/env python3
"""
Odświeżanie rekonstrukcji projektu w dwóch krokach bez modelu. Główny model tylko zleca aktualizacje kart, poprawia
miejsca z listy i zatwierdza wynik — reszta to skrypty (mniej tur, mniejszy kontekst, niższy koszt).

  python3 recon_refresh.py prep <repo> [--dir docs/project/00-reconstruction]
  python3 recon_refresh.py finish <repo> [--dir …] [--cost-usd X]
  python3 recon_refresh.py apply <repo> [--dir …]   # poprawki z raw/refresh/fixes.md (albo ze stdin), potem finish
      fixes.md:  @@ report.md:37
                 - nowa treść linii (pusty blok usuwa linię)
  python3 recon_refresh.py card <repo> <karta> [--dir …]   # kontrola jednej karty dla wykonawcy

prep: diff z manifestem (te same partie co w manifeście). Poprzednia wersja zmienionego pliku pochodzi z gita (commit
manifestu albo HEAD, gdy jej hash zgadza się z manifestem); z niej: pliki ze zmianą tylko w komentarzach i pustych
liniach nie dostają zleceń, numery linii dowodów w kartach i dokumentach są przeliczane (raz na manifest), a zlecenie
zawiera diff pliku. Kopia kart do raw/cards-prev/, zlecenie raw/refresh/<karta>.md dla każdej karty, której dotyczą
zmienione pliki (karta cytuje plik w dowodzie albo jej `batch` jest najdłuższym prefiksem ścieżki), lista plików bez
karty, plan na ekran (≤ 40 linii). Bez zleceń i plików bez karty prep od razu uruchamia finish.
finish: karty → .md, rules.md, sekcja Moduły raportu, linia „Odświeżenie przyrostowe:” w nagłówku raportu,
zmienione reguły kart (stara → nowa), miejsca do sprawdzenia z pełną treścią linii (stary znacznik z recon_cards
--prev, dowód w zmienionej linii kodu, opis podobny do zmienionej reguły) do raw/refresh/STALE.md, przesunięte dowody
(cytat jednoznacznie w innej linii pliku → nowy numer linii; poza modules/ i raw/), kontrola recon_check --final;
gdy przechodzi — nowy manifest. Podsumowanie ≤ 70 linii.
apply: zamienia wskazane linie dokumentów (poza modules/ i liniami rules.md złożonymi z kart — te poprawia się w karcie
JSON) i uruchamia finish; użyty fixes.md zmienia nazwę na fixes.applied.md. card: dowody karty z cytatem w innej, jednoznacznej linii dostają nowy numer (w JSON), karta
→ .md, kontrola dowodów; złe dowody z treścią elementu karty i linii kodu (≤ 25 linii).
Kod wyjścia: 0 — w porządku (finish/card: kontrola przeszła), 1 — kontrola nie przeszła, 2 — złe wywołanie.
"""
from __future__ import annotations

import datetime
import difflib
import hashlib
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

SLASH = {"cs", "java", "go", "js", "jsx", "ts", "tsx", "mjs", "cjs", "kt", "kts", "scala", "swift", "rs", "c", "h",
         "cc", "cpp", "hpp", "m", "dart", "php", "groovy", "gradle", "proto", "scss", "less", "sql"}
HASH = {"py", "rb", "sh", "bash", "yml", "yaml", "toml", "r", "pl", "ex", "exs", "properties"}
STAMP = "Odświeżenie przyrostowe:"


def code_skeleton(text: str, path: str) -> str | None:
    """Kod bez komentarzy zajmujących całą linię i bez pustych linii; None — język nieznany albo niedomknięty blok.
    Zachowawczo: komentarz za kodem, docstring i dyrektywa (#if) zostają w szkielecie."""
    ext = path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else ""
    if ext in SLASH:
        marks, block = ("//", "--") if ext == "sql" else ("//",), True
    elif ext in HASH:
        marks, block = ("#",), False
    else:
        return None
    out, inside = [], False
    for raw in text.splitlines():
        s, cut = raw.strip(), False
        if inside:
            if "*/" not in s:
                continue
            s, inside, cut = s.split("*/", 1)[1].strip(), False, True
        while block and s.startswith("/*"):
            if "*/" in s[2:]:
                s, cut = s[2:].split("*/", 1)[1].strip(), True
            else:
                s, inside = "", True
        if s and not s.startswith(marks):
            out.append(s if cut else raw.rstrip())
    return None if inside else "\n".join(out)


def comment_only(old: str, new: str, path: str) -> bool:
    a, b = code_skeleton(old, path), code_skeleton(new, path)
    return a is not None and a == b


def old_text(repo: str, manifest: dict, rel: str) -> str | None:
    """Wersja pliku z chwili manifestu: commit manifestu albo HEAD, jeśli hash zgadza się z manifestem."""
    want = {**manifest.get("files", {}), **manifest.get("tests", {})}.get(rel)
    for rev in dict.fromkeys(r for r in (manifest.get("commit"), "HEAD") if r):
        if not want:
            break
        r = subprocess.run(["git", "-C", repo, "show", f"{rev}:{rel}"], capture_output=True)
        if r.returncode == 0 and hashlib.sha256(r.stdout).hexdigest() == want:
            return r.stdout.decode("utf-8", "replace")
    return None


def line_map(old: str, new: str) -> dict[int, int]:
    """Stary numer linii → nowy (linie zastąpione: ta sama pozycja w nowym bloku, usunięte: linia, która je zastąpiła)."""
    a, b = old.splitlines(), new.splitlines()
    m = {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        for k in range(i1, i2):
            j = j1 + (k - i1) if tag == "equal" else j1 + min(k - i1, max(0, j2 - j1 - 1))
            m[k + 1] = min(j, max(0, len(b) - 1)) + 1
    return m


def changed_lines(old: str, new: str) -> list[int]:
    """Numery linii nowej wersji, które diff zmienił albo dodał (przy usunięciu — linia, która je zastąpiła)."""
    a, b = old.splitlines(), new.splitlines()
    out = set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal":
            out |= set(range(j1 + 1, max(j2, j1 + 1) + 1))
    return sorted(out)


def review_places(d: str, changes: list[dict], code_lines: dict) -> list[tuple[str, int, str, str]]:
    """Opisy syntezy (poza kartami) z dowodem w zmienionej linii kodu albo o treści podobnej do zmienionej reguły."""
    olds = [(c["card"], recon_cards.stems(c["old"].get("rule", ""))) for c in changes if c["old"]]
    hits = []
    for dp, dn, fn in os.walk(d):
        dn[:] = sorted(x for x in dn if x not in ("raw", "modules"))
        for f in sorted(fn):
            if not f.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dp, f), d).replace(os.sep, "/")
            with open(os.path.join(dp, f), encoding="utf-8") as fh:
                lines = fh.read().split("\n")
            for n, line in enumerate(lines, 1):
                if not line.strip() or card_source(d, rel, n):
                    continue
                if any(m.group(1) in code_lines and any(abs(int(m.group(2)) - x) <= 1 for x in code_lines[m.group(1)])
                       for m in recon_check.REF.finditer(line)):
                    hits.append((rel, n, "zmieniona linia kodu", line.strip()))
                    continue
                st = recon_cards.stems(line)
                sim = next((card for card, o in olds if len(st & o) >= 3 and len(st & o) / max(1, len(st | o)) >= 0.2), None)
                if sim:
                    hits.append((rel, n, f"podobna do zmienionej reguły karty {sim}", line.strip()))
    return hits


def remap(d: str, maps: dict[str, dict[int, int]]) -> int:
    """Przelicza numery linii `plik:linia` w kartach (modules/*.json) i dokumentach .md poza raw/."""
    if not maps:
        return 0
    pat = re.compile(r"(?<![\w/.@-])(" + "|".join(re.escape(p) for p in sorted(maps, key=len, reverse=True))
                     + r"):(\d+)(?:-(\d+))?(?!\d)")
    moved = 0

    def sub(m):
        nonlocal moved
        mp, a = maps[m.group(1)], int(m.group(2))
        na = mp.get(a, a)
        nb = max(na, mp.get(int(m.group(3)), int(m.group(3)))) if m.group(3) else None
        moved += (na != a) or (nb is not None and nb != int(m.group(3)))
        return f"{m.group(1)}:{na}" + (f"-{nb}" if nb is not None else "")

    for dp, dn, fn in os.walk(d):
        dn[:] = [x for x in dn if x != "raw"]
        for f in fn:
            if f.endswith(".md") or (f.endswith(".json") and os.path.basename(dp) == "modules"):
                path = os.path.join(dp, f)
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
                new = pat.sub(sub, text)
                if new != text:
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(new)
    return moved


def diff_lines(old: str, new: str, rel: str, limit: int = 60) -> list[str]:
    out = list(difflib.unified_diff(old.splitlines(), new.splitlines(), f"a/{rel}", f"b/{rel}", n=2, lineterm=""))[2:]
    return out[:limit] + ([f"… (+{len(out) - limit} linii diffu — resztę czytasz w pliku)"] if len(out) > limit else [])


def stamp(repo: str, rel_dir: str, n_files: int) -> None:
    """Linia „Odświeżenie przyrostowe: data · commit · zmienione pliki” pod nagłówkiem raportu (jedna, nadpisywana)."""
    path = os.path.join(repo, rel_dir, "report.md")
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    if n_files == 0 and any(ln.startswith(STAMP) for ln in lines):
        return
    for i in [i for i, ln in enumerate(lines) if ln.startswith(STAMP)][::-1]:
        del lines[i - 1 if i and lines[i - 1] == "" else i:i + 1]
    dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain", "--untracked-files=no", "--", ".",
                            f":(exclude){rel_dir}"], capture_output=True, text=True).stdout.strip()
    commit = recon_manifest.commit_of(repo)[:7] or "—"
    line = (f"{STAMP} {datetime.date.today().isoformat()} · commit {commit}"
            f"{' + zmiany w katalogu roboczym' if dirty else ''} · zmienione pliki: {n_files}")
    at = next((i for i, ln in enumerate(lines[:8]) if ln.startswith("Commit")), 0)
    lines[at + 1:at + 1] = ["", line]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def card_source(d: str, rel: str, n: int) -> str | None:
    """Karta, z której finish składa daną linię (modules/<karta>.md, sekcje kart w rules.md); None — tekst syntezy."""
    rel = rel.replace(os.sep, "/")
    if rel.startswith("modules/") and rel.endswith(".md"):
        return rel[len("modules/"):-3]
    if rel != "rules.md":
        return None
    try:
        with open(os.path.join(d, rel), encoding="utf-8") as fh:
            lines = fh.read().split("\n")[:n]
    except OSError:
        return None
    head = next((ln for ln in reversed(lines) if ln.startswith("## ")), "")
    m = re.search(r"\(szczegóły: modules/([^)]+)\.md\)", head)
    return m.group(1) if m and not head.startswith("## Reguły przekrojowe") else None


def doc_line(path: str, n: int) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
        return lines[n - 1].strip()[:400] if 0 < n <= len(lines) else ""
    except OSError:
        return ""


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


def task_text(stem: str, card: dict, files: list[str], kinds: dict, rel_dir: str, rel_scripts: str,
              diffs: dict | None = None) -> str:
    diffs = diffs or {}
    lines = [f"# Aktualizacja karty modułu {card.get('module') or stem} (odświeżanie przyrostowe)",
             f"Karta: {rel_dir}/modules/{stem}.json · poprzednia wersja: {rel_dir}/raw/cards-prev/{stem}.json", "",
             "Zmienione pliki (czytasz tylko je; z usuniętego pliku reguły usuwasz; numery linii w karcie są już",
             "przeliczone po zmianie):"]
    lines += [f"- {f} ({kinds.get(f, 'zmieniony')})" for f in files]
    for f in files:
        if diffs.get(f):
            lines += ["", f"Diff {f} (względem wersji z manifestu):", "```diff", *diffs[f], "```"]
    lines += ["", "Zadanie:",
              "1. Przeczytaj kartę i zmiany (diff powyżej; cały plik otwierasz tylko, gdy diffu nie ma albo brakuje",
              "   kontekstu). Zaktualizuj tylko elementy karty dotyczące tych plików: popraw",
              "   zmienione reguły, wejścia, dane i pojęcia, dodaj nowe, usuń te, których w kodzie już nie ma. Pozostałe",
              "   elementy zostaw bez zmian (te same słowa i cytaty).",
              "2. Opis modułu (pole purpose), niewiadome i odstępstwa, które wspominają zmieniony albo usunięty fakt,",
              "   popraw tak, by opisywały stan obecny (opis modułu trafia też do raportu).",
              "3. Wszystkie zmiany w karcie (sam JSON) robisz w jednej wiadomości, potem sprawdzasz ją jednym poleceniem:",
              f"   python3 {rel_scripts}/recon_refresh.py card . {stem}",
              "   Przesunięte numery linii poprawia ono samo; złe dowody wypisuje z treścią linii kodu — poprawiasz je",
              "   w karcie, aż kontrola da ✓.",
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
    snap = recon_manifest.snapshot(repo, int(old.get("budget_tokens") or 60000))
    diff = recon_manifest.diff(old, snap)
    changed = sorted(set(diff["changed_files"]) | set(diff["tests_changed"]))
    if not changed:
        print("Nic do odświeżenia (manifest zgodny z kodem).")
        return 0
    gone = set(diff["added_files"]) | set(diff["removed_files"])
    olds = {f: old_text(repo, old, f) for f in changed if f not in gone}
    news = {}
    for f, t in olds.items():
        if t is not None:
            with open(os.path.join(repo, f), encoding="utf-8", errors="replace") as fh:
                news[f] = fh.read()
    comments = sorted(f for f in news if comment_only(olds[f], news[f], f))
    with open(man, "rb") as fh:
        mark = {"manifest": hashlib.sha256(fh.read()).hexdigest(),
                "files": {f: {**snap["files"], **snap["tests"]}.get(f, "") for f in changed}}
    mark_path = os.path.join(d, "raw", "remap.json")
    try:
        with open(mark_path, encoding="utf-8") as fh:
            done = json.load(fh)
    except (OSError, ValueError):
        done = {}
    moved = 0
    if done.get("manifest") != mark["manifest"]:
        moved = remap(d, {f: line_map(olds[f], news[f]) for f in news})
        os.makedirs(os.path.dirname(mark_path), exist_ok=True)
        with open(mark_path, "w", encoding="utf-8") as fh:
            json.dump(mark, fh)
    diffs = {f: diff_lines(olds[f], news[f], f) for f in news if f not in comments}
    code_lines = {f: changed_lines(olds[f], news[f]) for f in news if f not in comments}
    changed = [f for f in changed if f not in comments]
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
    with open(os.path.join(work, "changed-lines.json"), "w", encoding="utf-8") as fh:
        json.dump(code_lines, fh)
    rel_scripts = os.path.relpath(HERE, repo).replace(os.sep, "/")
    for stem, files in sorted(by_card.items()):
        with open(os.path.join(work, stem + ".md"), "w", encoding="utf-8") as fh:
            fh.write(task_text(stem, cards[stem], files, kinds, rel_dir, rel_scripts, diffs))
    L = [f"Odświeżanie względem manifestu (commit {old.get('commit') or '—'}): zmienione pliki "
         f"{len(diff['changed_files'])} ({diff['share']}%), testy {len(diff['tests_changed'])}"]
    if diff["share"] > 50:
        L.append("⚠ zmieniło się ponad połowę plików — rozważ pełny przebieg zamiast odświeżania")
    if comments:
        L.append(f"Tylko komentarze i puste linie ({len(comments)}, bez zleceń): {', '.join(comments[:6])}"
                 f"{' …' if len(comments) > 6 else ''}")
    L.append(f"Numery linii przeliczone w kartach i dokumentach: {moved} dowodów"
             + ("" if len(news) == len(olds) else f" (bez poprzedniej wersji w gicie: {len(olds) - len(news)} plików)"))
    if done.get("manifest") == mark["manifest"] and done.get("files") != mark["files"]:
        L.append("⚠ kod zmienił się po poprzednim prep — przesunięte dowody sprawdzi finish")
    L.append(f"Karty do aktualizacji ({len(by_card)}):")
    L += [f"  {stem} ← {', '.join(files[:4])}{' …' if len(files) > 4 else ''}" for stem, files in sorted(by_card.items())[:25]]
    if orphans:
        L.append(f"Pliki bez karty ({len(orphans)}): {', '.join(orphans[:8])}{' …' if len(orphans) > 8 else ''} "
                 "— dopisz je do najbliższej karty albo zleć nową kartę")
    L += [f"Zlecenia: {rel_dir}/raw/refresh/<karta>.md — wykonawcy (Haiku) w jednej wiadomości, na pierwszym planie;",
          "  każdy dostaje jedno zdanie: „Wykonaj zlecenie z <ścieżka zlecenia>”.",
          f"Stare karty: {rel_dir}/raw/cards-prev/ · potem: python3 {rel_scripts}/recon_refresh.py finish {repo}"]
    if not by_card and not orphans:
        print("\n".join(L[:3] + ["Brak zleceń dla wykonawców — finish od razu:"]))
        return finish(repo, rel_dir, None)
    print("\n".join(L[:40]))
    return 0


def finish(repo: str, rel_dir: str, cost: str | None) -> int:
    d = os.path.join(repo, rel_dir)
    mods, prev, work = os.path.join(d, "modules"), os.path.join(d, "raw", "cards-prev"), os.path.join(d, "raw", "refresh")
    man = os.path.join(d, "manifest.json")
    try:
        with open(man, encoding="utf-8") as fh:
            base = json.load(fh)
        dd = recon_manifest.diff(base, recon_manifest.snapshot(repo, int(base.get("budget_tokens") or 60000)))
        stamp(repo, rel_dir, len(set(dd["changed_files"]) | set(dd["tests_changed"])))
    except (OSError, ValueError):
        pass
    args = [sys.executable, os.path.join(HERE, "recon_cards.py"), mods, "--repo", repo, "--rules",
            "--into", os.path.join(d, "report.md")]
    cards_out = subprocess.run(args, capture_output=True, text=True).stdout.splitlines()
    ch = recon_cards.rule_changes(prev, mods) if os.path.isdir(prev) else []
    try:
        with open(os.path.join(work, "changed-lines.json"), encoding="utf-8") as fh:
            code_lines = json.load(fh)
    except (OSError, ValueError):
        code_lines = {}
    stale, seen = [], set()
    places = (recon_cards.stale_candidates(prev, mods, d) if os.path.isdir(prev) else []) + review_places(d, ch, code_lines)
    for path, n, tok, line in places:
        src = card_source(d, path, n)
        key = (src, line) if src else (path, n)
        if key in seen:
            continue
        seen.add(key)
        stale.append(f"  {path}:{n} [{tok}]" + (f" (z karty → modules/{src}.json)" if src else "") + f" {line[:400]}")
    os.makedirs(work, exist_ok=True)
    with open(os.path.join(work, "STALE.md"), "w", encoding="utf-8") as fh:
        fh.write("# Miejsca, które mogą opisywać stan sprzed zmiany\n"
                 "Każde poprawiasz albo zostawiasz, gdy celowo mówi o starej wartości.\n\n"
                 + "\n".join(f"- {ln.strip()}" for ln in stale) + "\n")
    L = [f"Karty: {next((ln for ln in cards_out if ln.startswith(('✓', '✗'))), '—')}"]
    if os.path.isdir(prev):
        L.append(f"Zmienione reguły kart ({len(ch)}):")
        for c in ch[:15]:
            if c["kind"] == "zmieniona":
                L.append(f"  [{c['card']}] {short(c['old'])} → {short(c['new'])}")
            else:
                L.append(f"  [{c['card']}] {c['kind']}: {short(c['old'] or c['new'])}")
    L.append(f"Do sprawdzenia: {len(stale)} miejsc ({rel_dir}/raw/refresh/STALE.md) — stary znacznik, dowód"
             " w zmienionej linii kodu albo treść podobna do zmienionej reguły; poprawiasz albo zostawiasz")
    L += stale[:25]
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
        for b in (res.get("bad") or [])[:8]:
            at = os.path.relpath(b["at"], d).replace(os.sep, "/")
            f, _, n = at.rpartition(":")
            src = card_source(d, f, int(n)) if n.isdigit() else None
            L.append(f"  ✗ {at}: `{b['ref']}` — {b['problem']}" + (f" (z karty → modules/{src}.json)" if src else ""))
            L.append(f"      {doc_line(os.path.join(d, f), int(n)) if n.isdigit() else ''}")
        for u in (res.get("unsupported") or [])[:5]:
            L.append(f"  ✗ {os.path.relpath(u['at'], d)}: bez dowodu — {u['text'][:90]}")
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
    print("\n".join(L[:70]))
    return 0 if ok else 1


def apply(repo: str, rel_dir: str, text: str) -> int:
    d = os.path.join(repo, rel_dir)
    edits, cur, errs = {}, None, []
    for raw in text.split("\n"):
        if raw.startswith("@@ "):
            f, _, n = raw[3:].strip().rpartition(":")
            f = f[len(rel_dir) + 1:] if f.startswith(rel_dir + "/") else f
            if not n.isdigit() or not os.path.isfile(os.path.join(d, f)):
                errs.append(f"✗ {raw[3:].strip()}: podaj plik:linia z wydruku finish (ścieżka względem {rel_dir})")
                cur = None
                continue
            src = card_source(d, f, int(n))
            if src:
                errs.append(f"✗ {f}:{n}: linię składa finish z karty — popraw modules/{src}.json")
                cur = None
                continue
            cur = edits.setdefault(f, {}).setdefault(int(n), [])
        elif cur is not None:
            cur.append(raw)
    if errs or not edits:
        print("\n".join(errs or ["✗ brak poprawek: bloki „@@ plik:linia” z nową treścią na wejściu"]))
        return 2
    count = 0
    for f, by_line in edits.items():
        path = os.path.join(d, f)
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        for n in sorted(by_line, reverse=True):
            block = by_line[n]
            while block and not block[-1].strip():
                block.pop()
            if n <= len(lines):
                lines[n - 1:n] = block
                count += 1
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
    print(f"Poprawione linie: {count}")
    return finish(repo, rel_dir, None)


def card(repo: str, rel_dir: str, stem: str) -> int:
    d = os.path.join(repo, rel_dir)
    path = os.path.join(d, "modules", stem + ".json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as e:
        print(f"✗ karta {stem}: {e}")
        return 2
    cache, moved = {}, 0

    def src_lines(rel):
        if rel not in cache:
            try:
                with open(os.path.join(repo, rel), encoding="utf-8", errors="replace") as fh:
                    cache[rel] = fh.read().splitlines()
            except OSError:
                cache[rel] = None
        return cache[rel]

    def walk(obj):
        nonlocal moved
        if isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, dict):
            m = re.fullmatch(r"`?(.+?):(\d+)(?:-(\d+))?`?", str(obj.get("evidence", "")).strip())
            q = recon_check.norm(str(obj.get("quote") or ""))
            if m and len(q) >= 3:
                src, a = src_lines(m.group(1)), int(m.group(2))
                b = int(m.group(3) or a)
                if src and q not in recon_check.norm(" ".join(src[max(0, a - 3):b + 2])):
                    hits = [i for i, ln in enumerate(src, 1) if q in recon_check.norm(ln)]
                    if len(hits) == 1:
                        obj["evidence"] = f"{m.group(1)}:{hits[0]}" + (f"-{hits[0] + b - a}" if m.group(3) else "")
                        moved += 1
            for v in obj.values():
                walk(v)

    walk(data)
    if moved:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    subprocess.run([sys.executable, os.path.join(HERE, "recon_cards.py"), os.path.join(d, "modules"), "--repo", repo],
                   capture_output=True, text=True)
    chk = subprocess.run([sys.executable, os.path.join(HERE, "recon_check.py"), os.path.join(d, "modules", stem + ".md"),
                          "--repo", repo, "--json"], capture_output=True, text=True)
    try:
        res = json.loads(chk.stdout)
    except ValueError:
        print(f"✗ karta {stem}: kontrola nie zadziałała: {chk.stderr[-200:]}")
        return 2
    bad = res.get("bad") or []
    L = [f"{'✓' if not bad else '✗'} karta {stem}: dowody {res.get('refs', '?')}, złe {len(bad)}, "
         f"poprawione numery linii {moved}",
         f"  opis modułu (purpose): {' '.join(str(data.get('purpose') or '—').split())[:300]}",
         "  — popraw go, jeśli powtarza zmienioną albo usuniętą regułę"]
    for b in bad[:6]:
        f, _, n = b["at"].rpartition(":")
        L.append(f"  ✗ `{b['ref']}` — {b['problem']}: {doc_line(f, int(n))[:220] if n.isdigit() else ''}")
        m = re.fullmatch(r"(.+?):(\d+)(?:-\d+)?", b["ref"])
        src = src_lines(m.group(1)) if m else None
        if src and int(m.group(2)) <= len(src):
            L.append(f"      kod {m.group(1)}:{m.group(2)}: {src[int(m.group(2)) - 1].strip()[:200]}")
    print("\n".join(L[:25]))
    return 0 if not bad else 1


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    repo = rest[0] if rest and not rest[0].startswith("--") else ""
    rel_dir = recon_manifest.opt(rest, "--dir", "docs/project/00-reconstruction")
    if cmd not in ("prep", "finish", "apply", "card") or not os.path.isdir(repo):
        print(f"✗ użycie: prep|finish|apply|card <repo> [--dir …] (jest: {argv})", file=sys.stderr)
        return 2
    if cmd == "apply":
        fixes = os.path.join(repo, rel_dir, "raw", "refresh", "fixes.md")
        if not os.path.isfile(fixes):
            return apply(repo, rel_dir, sys.stdin.read())
        with open(fixes, encoding="utf-8") as fh:
            text = fh.read()
        os.replace(fixes, fixes[:-3] + ".applied.md")   # ten sam plik nie zostanie użyty drugi raz
        return apply(repo, rel_dir, text)
    if cmd == "card":
        stem = rest[1] if len(rest) > 1 and not rest[1].startswith("--") else ""
        return card(repo, rel_dir, stem) if stem else 2
    return prep(repo, rel_dir) if cmd == "prep" else finish(repo, rel_dir, recon_manifest.opt(rest, "--cost-usd"))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
