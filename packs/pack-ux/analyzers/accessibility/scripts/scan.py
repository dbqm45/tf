#!/usr/bin/env python3
"""
Moduł `accessibility` tf analyze, piętro 0 (bez modelu i przeglądarki): statyczne sprawdzenie szablonów pod kątem
WCAG 2.2 (ux-accessibility). HTML, JSX/TSX, Vue, Svelte, Astro i szablony Angulara.

  python3 scan.py --root <repo> [--files a,b]     # JSON Lines na stdout (kontrakt: .tf/factory/analyze.py)

Reguły:
- `img-without-alt` — `<img>` bez `alt` (puste `alt=""` dla grafiki dekoracyjnej jest w porządku; wiązania `:alt`,
  `[alt]`, `alt={…}` się liczą), WCAG 1.1.1;
- `control-without-name` — `<button>` albo `<a href>` bez tekstu (np. sama ikona) i bez `aria-label`,
  `aria-labelledby`, `title` ani obrazu z niepustym `alt` w środku, WCAG 4.1.2;
- `input-without-label` — `input` (poza hidden/submit/button/reset/image), `select`, `textarea` bez etykiety
  (`<label for>`/`htmlFor` do jego `id`, otaczający `<label>`, `aria-label`, `aria-labelledby`, `title`);
  placeholder nie jest etykietą, WCAG 1.3.1 i 3.3.2;
- `click-without-keyboard` — `div`/`span`/`li`/`img` z obsługą kliknięcia bez kompletu `role`, `tabindex`
  i obsługi klawiatury, WCAG 2.1.1 i 4.1.2;
- `positive-tabindex` — `tabindex` większy od zera, WCAG 2.4.3;
- `html-without-lang` — `<html>` bez `lang`, WCAG 3.1.1.
Element ze spreadem atrybutów (`{...props}`, `v-bind="…"`) jest pomijany, bo atrybuty mogą przyjść z zewnątrz.
Komponenty (nazwy z wielkiej litery) nie są sprawdzane — tylko elementy HTML. Kontrast, fokus i treść dynamiczna
wymagają przeglądarki (kolejne piętro). Znalezienie = „sprawdź”. Testy i dokumentacja są pomijane. Tylko biblioteka
standardowa.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SKIP_DIRS = {"node_modules", ".git", "dist", "build", "coverage", ".venv", "venv", "__pycache__", ".tf", ".next",
             "target", "_vendor", "vendor", ".angular", ".nuxt", ".svelte-kit", "storybook-static"}
FACTORY_OWNED = (".tf/factory/", ".claude/")
TEST_OR_DOC = re.compile(r"(^|/)(tests?|__tests__|e2e|fixtures|spec|examples?|docs?|stories)/|\.(test|spec|stories)\.|"
                         r"(^|/)test_[^/]*$|\.(md|mdx|rst|txt|adoc)$")
EXT = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro", ".js", ".ts"}

# Atrybuty: napisy, wyrażenia {…} z jednym poziomem zagnieżdżenia, reszta bez `>`.
ATTRS = r"(?:[^>{}\"']|\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}|\"[^\"]*\"|'[^']*')*"
TAG = re.compile(rf"<(img|button|a|input|select|textarea|div|span|li|html|[a-z][a-z0-9]*)(?=[\s/>])({ATTRS})>", re.S)
ANY_TAG = re.compile(rf"</?[A-Za-z][\w.:-]*{ATTRS}>|<!--.*?-->|\{{/\*.*?\*/\}}", re.S)
CLICK = re.compile(r"(?:^|[\s(])(?:onClick|onclick|\(click\)|@click|v-on:click|on:click)\s*=")
KEY = re.compile(r"(?:^|[\s(])(?:onKey(?:Down|Up|Press)|onkey(?:down|up|press)|\(key(?:down|up|press)[\w.]*\)|"
                 r"@key(?:down|up|press)[\w.]*|v-on:key(?:down|up|press)[\w.]*|on:key(?:down|up|press))\s*=")
SPREAD = re.compile(r"\{\s*\.\.\.|(?:^|\s)v-bind\s*=|(?:^|\s)\{\.\.\.")
SKIP_INPUT_TYPES = {"hidden", "submit", "button", "reset", "image"}


def has_attr(attrs: str, name: str) -> bool:
    """Atrybut zwykły, wiązanie (`:x`, `[x]`, `[attr.x]`, `v-bind:x`, `x={…}`) albo atrybut logiczny."""
    return bool(re.search(rf"(?:^|[\s\[(.:]){re.escape(name)}\]?\s*(?==|[\s/>]|$)", attrs, re.I))


def attr_value(attrs: str, name: str) -> str | None:
    m = re.search(r"(?:^|\s)\[?:?" + re.escape(name) + r"\]?\s*=\s*(\"[^\"]*\"|'[^']*'|\{[^}]*\}|[^\s>]+)", attrs,
                  re.I)
    return m.group(1).strip("\"'{} ") if m else None


def emit(rule: str, rel: str, line: int, snippet: str, title: str, severity: str, basis: str,
         suggestion: str) -> None:
    print(json.dumps({"rule": rule, "title": title, "file": rel, "line": line,
                      "snippet": " ".join(snippet.split())[:160], "severity": severity, "confidence": 0.7,
                      "evidence": "statyczna analiza szablonu (bez przeglądarki)", "basis": basis,
                      "suggestion": suggestion}, ensure_ascii=False))


def inner_text(text: str, end: int, tag: str) -> str | None:
    """Zawartość elementu do najbliższego zamknięcia albo None, gdy zamknięcia nie ma."""
    close = re.compile(rf"</{tag}\s*>", re.I)
    m = close.search(text, end)
    return text[end:m.start()] if m else None


def named_by_content(inner: str) -> bool:
    if re.search(r"<(ng-content|slot)\b", inner):          # treść wstawiana przez rodzica (Angular, Vue, Svelte)
        return True
    if "{" in inner and re.search(r"\{(?!/\*)", inner):     # wyrażenie (JSX, Vue `{{ }}`, Angular) — zwykle tekst
        return True
    if re.search(r"<img\b[^>]*\balt\s*=\s*(\"[^\"]+\"|'[^']+'|\{)", inner, re.I):
        return True
    if re.search(r"\baria-label(?:ledby)?\s*=", inner):
        return True
    return bool(re.search(r"\w", ANY_TAG.sub(" ", inner)))


def wrapped_by_labelled_component(before: str) -> bool:
    """Pole wewnątrz niezamkniętego komponentu z etykietą (`<Field label="…">`, `<FormItem label={…}>`)."""
    for m in re.finditer(rf"<([A-Z][\w.]*)({ATTRS})>", before, re.S):
        if re.search(r"(?:^|\s)label\s*=", m.group(2)) and not m.group(0).endswith("/>") \
                and not re.search(rf"</{re.escape(m.group(1))}\s*>", before[m.end():]):
            return True
    return False


def scan_text(rel: str, text: str) -> None:
    def line_of(pos: int) -> int:
        return text.count("\n", 0, pos) + 1

    label_for = set(re.findall(r"(?:\bfor|htmlFor)\s*=\s*[{\"']*\s*[\"']?([\w:-]+)", text))
    any_dynamic_for = bool(re.search(r"(?:\[for\]|\[attr\.for\]|:for|htmlFor)\s*=\s*\{?(?![\"'])", text))
    for m in TAG.finditer(text):
        tag, attrs = m.group(1), m.group(2) or ""
        if tag[0].isupper() or SPREAD.search(attrs):
            continue
        pos, snippet = m.start(), m.group(0)
        if tag == "html":
            if not has_attr(attrs, "lang"):
                emit("html-without-lang", rel, line_of(pos), snippet, "dokument bez atrybutu lang", "średnia",
                     "WCAG 2.2 SC 3.1.1", "dodaj `lang` z językiem strony, np. `<html lang=\"pl\">`")
            continue
        tabindex = attr_value(attrs, "tabindex") or attr_value(attrs, "tabIndex")
        if tabindex and re.fullmatch(r"\d+", tabindex) and int(tabindex) > 0:
            emit("positive-tabindex", rel, line_of(pos), snippet, f"tabindex={tabindex} zmienia kolejność fokusu",
                 "średnia", "WCAG 2.2 SC 2.4.3", "użyj `tabindex=\"0\"` albo `-1` i ułóż elementy w kolejności DOM")
        if tag == "img":
            if not has_attr(attrs, "alt") and not has_attr(attrs, "aria-hidden") \
                    and attr_value(attrs, "role") not in ("presentation", "none"):
                emit("img-without-alt", rel, line_of(pos), snippet, "obraz bez tekstu alternatywnego", "wysoka",
                     "WCAG 2.2 SC 1.1.1", "dodaj `alt` z opisem treści albo `alt=\"\"` dla grafiki dekoracyjnej")
        if tag in ("button", "a"):
            if tag == "a" and not has_attr(attrs, "href") and not has_attr(attrs, "routerLink"):
                continue
            if any(has_attr(attrs, a) for a in ("aria-label", "aria-labelledby", "title")):
                continue
            inner = "" if m.group(0).endswith("/>") else inner_text(text, m.end(), tag)
            if inner is not None and not named_by_content(inner):
                emit("control-without-name", rel, line_of(pos), snippet,
                     f"{'przycisk' if tag == 'button' else 'link'} bez dostępnej nazwy", "wysoka",
                     "WCAG 2.2 SC 4.1.2 i 2.4.4", "dodaj widoczny tekst albo `aria-label` (np. dla przycisku z ikoną)")
        if tag in ("input", "select", "textarea"):
            itype = (attr_value(attrs, "type") or "text").lower()
            if tag == "input" and itype in SKIP_INPUT_TYPES:
                continue
            if any(has_attr(attrs, a) for a in ("aria-label", "aria-labelledby", "title")):
                continue
            ident = attr_value(attrs, "id")
            if ident and (ident in label_for or (not re.fullmatch(r"[\w:-]+", ident) and any_dynamic_for)):
                continue
            before = text[:pos]
            if wrapped_by_labelled_component(before):
                continue
            if len(re.findall(r"<label\b", before)) > len(re.findall(r"</label\s*>", before)):
                continue
            emit("input-without-label", rel, line_of(pos), snippet, f"pole `{tag}` bez etykiety", "wysoka",
                 "WCAG 2.2 SC 1.3.1 i 3.3.2",
                 "dodaj `<label for>` (w JSX `htmlFor`) albo `aria-label`; placeholder nie zastępuje etykiety")
        if tag in ("div", "span", "li", "img", "p", "td", "tr", "section", "article") and CLICK.search(attrs):
            ok = has_attr(attrs, "role") and (has_attr(attrs, "tabindex") or has_attr(attrs, "tabIndex")) \
                and bool(KEY.search(attrs))
            if not ok:
                emit("click-without-keyboard", rel, line_of(pos), snippet,
                     f"`{tag}` z obsługą kliknięcia niedostępny z klawiatury", "wysoka", "WCAG 2.2 SC 2.1.1 i 4.1.2",
                     "użyj `<button>` albo dodaj `role`, `tabindex=\"0\"` i obsługę Enter/Spacji")


def list_files(root: Path) -> list[str]:
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if top.returncode == 0 and Path(top.stdout.strip()).resolve() == root.resolve():
        r = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        return [f for f in r.stdout.splitlines() if f and not set(Path(f).parts) & SKIP_DIRS
                and not f.startswith(FACTORY_OWNED)]
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        out += [str((Path(dp) / f).relative_to(root)) for f in fns]
    return sorted(out)


def scan(root: Path, files: list[str]) -> None:
    for rel in files:
        rel = rel.replace(os.sep, "/")
        p = root / rel
        if TEST_OR_DOC.search(rel) or p.suffix.lower() not in EXT or not p.is_file() or p.stat().st_size > 1_000_000 \
                or rel.endswith((".min.js", ".d.ts")):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if p.suffix.lower() in (".js", ".ts") and not re.search(r"<(img|button|a|input|select|textarea|div|span)\b",
                                                                text):
            continue
        scan_text(rel, text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--files", default="")
    a = ap.parse_args()
    root = Path(a.root)
    files = [f for f in a.files.split(",") if f] or list_files(root)
    scan(root, files)
    return 0


if __name__ == "__main__":
    sys.exit(main())
