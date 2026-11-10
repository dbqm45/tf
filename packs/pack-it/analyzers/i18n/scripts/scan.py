#!/usr/bin/env python3
"""
Moduł `i18n` tf analyze, piętro 0 (bez modelu): tekst i formatowanie, które omijają umiędzynarodowienie (eng-i18n).

  python3 scan.py --root <repo> [--files a,b]     # JSON Lines na stdout (kontrakt: .tf/factory/analyze.py)

Reguły:
- `hardcoded-ui-text` — tekst w JSX/TSX, Vue, Svelte albo szablonie Angulara oraz w atrybutach `placeholder`,
  `title`, `aria-label`, `alt`, `label` poza funkcją tłumaczącą. Tylko w projekcie, który już używa biblioteki
  tłumaczeń (i18next, react-intl/FormatJS, next-intl, vue-i18n, ngx-translate, `@angular/localize`, Lingui,
  svelte-i18n) — wtedy tekst poza nią jest przeoczeniem, a nie decyzją. Elementy z atrybutem `i18n` (Angular) są
  pomijane;
- `locale-less-format` — `toLocaleDateString()`, `toLocaleTimeString()`, `toLocaleString()`,
  `new Intl.DateTimeFormat()`/`NumberFormat()` bez locale w projekcie z biblioteką tłumaczeń (język aplikacji może
  się różnić od języka przeglądarki) albo z SSR (Next.js, Nuxt, SvelteKit, Remix, Astro, Angular SSR — serwer
  i przeglądarka formatują inaczej, rozjazd hydracji); w zwykłej SPA locale przeglądarki to zwykle właściwy wybór;
- `money-without-intl` — w komponencie UI kwota z `toFixed(…)` sklejona z walutą (`zł`, `PLN`, `€`, `$`…)
  zamiast `Intl.NumberFormat` z `style: "currency"` (separator dziesiętny, pozycja symbolu, odstęp).
We Vue sprawdzany jest tylko blok `<template>`.
Znalezienie = „sprawdź”. Testy, historie (stories) i dokumentacja są pomijane. Tylko biblioteka standardowa.
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
TEST_OR_DOC = re.compile(r"(^|/)(tests?|__tests__|e2e|fixtures|spec|examples?|docs?|stories|mocks?|__mocks__)/|"
                         r"\.(test|spec|stories)\.|(^|/)test_[^/]*$|\.(md|mdx|rst|txt|adoc)$")
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts"}
TEMPLATE_EXT = {".jsx", ".tsx", ".vue", ".svelte"}
SSR = re.compile(r"""["'](?:next|nuxt|@sveltejs/kit|@remix-run/[\w-]+|astro|@angular/ssr|@nguniversal/[\w-]+|"""
                 r"""@tanstack/react-start|@builder\.io/qwik-city)["']\s*:""")
I18N_LIBS = re.compile(r"""["'](?:i18next|react-i18next|next-i18next|next-intl|react-intl|@formatjs/[\w-]+|"""
                       r"""vue-i18n|@nuxtjs/i18n|@ngx-translate/core|@angular/localize|@lingui/[\w-]+|"""
                       r"""svelte-i18n|typesafe-i18n|i18n-js|@transloco/[\w-]+|@jsverse/transloco)["']""")

ATTRS = r"(?:[^>{}\"']|\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}|\"[^\"]*\"|'[^']*')*"
TAG = re.compile(rf"<(/?)([A-Za-z][\w.:-]*)({ATTRS})>", re.S)
TEXT_ATTR = re.compile(r"(?:^|\s)(placeholder|title|aria-label|alt|label)\s*=\s*(\"[^\"]*\"|'[^']*')")
WORD = re.compile(r"[^\W\d_]{2,}")
SKIP_ELEMENTS = {"script", "style", "code", "pre", "kbd", "samp", "svg", "path", "math"}
LOCALE_LESS = re.compile(r"\.(toLocaleDateString|toLocaleTimeString|toLocaleString)\(\s*\)|"
                         r"\bnew\s+Intl\.(DateTimeFormat|NumberFormat|RelativeTimeFormat)\(\s*\)")
TOFIXED = re.compile(r"\.toFixed\(\s*\d\s*\)")
CURRENCY = re.compile(r"zł|\b(?:PLN|EUR|USD|GBP|CHF)\b|€|£|(?<![\w$])\$(?![{\w(])")


def emit(rule: str, rel: str, line: int, snippet: str, title: str, severity: str, suggestion: str,
         confidence: float = 0.6) -> None:
    print(json.dumps({"rule": rule, "title": title, "file": rel, "line": line,
                      "snippet": " ".join(snippet.split())[:160], "severity": severity, "confidence": confidence,
                      "evidence": "statyczna analiza kodu", "basis": "eng-i18n (teksty w katalogu, formatowanie Intl)",
                      "suggestion": suggestion}, ensure_ascii=False))


def blank(text: str, pattern: str, flags=re.S | re.I) -> str:
    """Zamienia dopasowania na spacje z zachowaniem nowych linii (numery linii zostają)."""
    return re.sub(pattern, lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=flags)


def template_part(rel: str, text: str) -> str:
    ext = Path(rel).suffix.lower()
    if ext == ".vue":       # tylko blok <template>; <script>, <style> i bloki własne (<route>, <i18n>) to nie UI
        start, end = re.search(r"<template\b[^>]*>", text), text.rfind("</template>")
        if not start or end < start.end():
            return re.sub(r"[^\n]", " ", text)
        return (re.sub(r"[^\n]", " ", text[:start.end()]) + text[start.end():end]
                + re.sub(r"[^\n]", " ", text[end:]))
    if ext == ".svelte":
        return blank(text, r"<(script|style)\b[^>]*>.*?</\1\s*>")
    return text


def scan_text_nodes(rel: str, text: str) -> None:
    src = template_part(rel, text)
    src = blank(src, r"<!--.*?-->|\{/\*.*?\*/\}")
    stack: list[tuple[str, bool]] = []          # (element, i18n) — otwarte elementy, do pomijania treści
    for m in TAG.finditer(src):
        closing, name, attrs = m.group(1), m.group(2), m.group(3) or ""
        selfclose = attrs.rstrip().endswith("/")
        if closing:
            while stack and stack[-1][0] != name:
                stack.pop()
            if stack:
                stack.pop()
        elif not selfclose and name.lower() not in ("img", "input", "br", "hr", "meta", "link"):
            stack.append((name.lower(), bool(re.search(r"(?:^|\s)i18n(?:[\s=]|$)", attrs))))
        if not closing:
            for a in TEXT_ATTR.finditer(attrs):
                if re.search(rf"(?:^|\s)i18n-{a.group(1)}\b", attrs) or not WORD.search(a.group(2)):
                    continue
                ln = src.count("\n", 0, m.start()) + 1
                emit("hardcoded-ui-text", rel, ln, m.group(0), f"tekst atrybutu `{a.group(1)}` poza tłumaczeniem",
                     "niska", "przenieś tekst do katalogu tłumaczeń i użyj funkcji `t(…)`/`$t(…)`/potoku `translate`")
        nxt = src.find("<", m.end())
        if nxt < 0:
            continue
        run = src[m.end():nxt]
        if any(e in SKIP_ELEMENTS or i18n for e, i18n in stack):
            continue
        if src[m.end():m.end() + 1] == "(":           # generyk w TS: useState<string>(…)
            continue
        literal = re.sub(r"\{\{.*?\}\}|\{(?:[^{}]|\{[^{}]*\})*\}", " ", run, flags=re.S)
        if re.search(r"[;=(){}]|=>|&&|\|\|", literal):  # to kod, nie tekst elementu
            continue
        if WORD.search(literal):
            ln = src.count("\n", 0, m.end() + len(run) - len(run.lstrip())) + 1
            emit("hardcoded-ui-text", rel, ln, literal.strip(), "tekst interfejsu poza tłumaczeniem", "niska",
                 "przenieś tekst do katalogu tłumaczeń i użyj funkcji `t(…)`/`$t(…)`/potoku `translate` "
                 "albo atrybutu `i18n`")


def scan_formats(rel: str, text: str, locale_matters: bool, ui: bool) -> None:
    for i, line in enumerate(text.splitlines()):
        m = LOCALE_LESS.search(line) if locale_matters else None
        if m:
            emit("locale-less-format", rel, i + 1, line, f"formatowanie bez locale: {m.group(0).lstrip('.')}",
                 "średnia", "podaj locale użytkownika jawnie, np. `toLocaleDateString(locale)` albo "
                 "`new Intl.DateTimeFormat(locale, …)`", confidence=0.8)
        if ui and TOFIXED.search(line) and CURRENCY.search(TOFIXED.sub(" ", line)):
            emit("money-without-intl", rel, i + 1, line, "kwota z toFixed sklejona z walutą", "średnia",
                 "użyj `new Intl.NumberFormat(locale, { style: \"currency\", currency })`; kwoty licz w groszach "
                 "lub typem dziesiętnym", confidence=0.7)


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


def manifests(root: Path, files: list[str]) -> str:
    out = []
    for rel in files:
        if Path(rel).name == "package.json" and not set(Path(rel).parts) & SKIP_DIRS:
            try:
                out.append((root / rel).read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                continue
    return "\n".join(out)


def scan(root: Path, files: list[str]) -> None:
    files = [f.replace(os.sep, "/") for f in files]
    deps = manifests(root, files)
    i18n = bool(I18N_LIBS.search(deps))
    locale_matters = i18n or bool(SSR.search(deps))   # w samej SPA locale przeglądarki to zwykle właściwy wybór
    for rel in files:
        p = root / rel
        ext = p.suffix.lower()
        is_ng_template = rel.endswith(".component.html")
        if TEST_OR_DOC.search(rel) or not (ext in JS_EXT | TEMPLATE_EXT or is_ng_template) or not p.is_file() \
                or p.stat().st_size > 1_000_000 or rel.endswith((".min.js", ".d.ts")):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        jsx_in_js = ext in (".js", ".mjs") and bool(re.search(r"""from\s+["']react["']|require\(["']react["']\)""", text)) \
            and bool(re.search(r"</[A-Za-z][\w.]*>", text))
        if i18n and (ext in TEMPLATE_EXT or is_ng_template or jsx_in_js):
            scan_text_nodes(rel, text)
        if ext in JS_EXT or ext in (".vue", ".svelte"):
            scan_formats(rel, text, locale_matters, ext in TEMPLATE_EXT)


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
