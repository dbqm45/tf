#!/usr/bin/env python3
"""
Szybka, deterministyczna kontrola polskiej prozy w plikach Markdown/tekstowych (zero tokenów).
Łapie błędy mechaniczne o wysokiej pewności: typografię, najczęstsze błędy pisowni, pleonazmy, kalki
i brak przecinka przed „że”/„który”. Nie zastępuje korekty (skill txt-polish-correctness) — ją odciąża.

  python3 .claude/skills/txt-polish-correctness/scripts/polish_lint.py <plik|katalog> [...] [--strict] [--json]

Pomija: frontmatter YAML, bloki kodu ```…```, `kod w linii`, adresy URL, linie z HTML-owymi komentarzami.
Pliki bez polskich znaków diakrytycznych są pomijane (tekst prawdopodobnie nie jest po polsku).
Wyjście: plik:linia [KATEGORIA|PRIORYTET] fragment → sugestia. Kod wyjścia: 0 (doradczo), z --strict 1 przy uwagach WYSOKICH.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PL_CHARS = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")

# (wzorzec, kategoria, priorytet, sugestia) — wzorce z granicami słów, bez rozróżniania wielkości liter
WORDS: list[tuple[str, str, str, str]] = [
    (r"\bnapewno\b", "SPELLING", "HIGH", "na pewno"),
    (r"\bwogóle\b", "SPELLING", "HIGH", "w ogóle"),
    (r"\bnarazie\b", "SPELLING", "HIGH", "na razie"),
    (r"\bconajmniej\b", "SPELLING", "HIGH", "co najmniej"),
    (r"\bconajwyżej\b", "SPELLING", "HIGH", "co najwyżej"),
    (r"\bpoprostu\b", "SPELLING", "HIGH", "po prostu"),
    (r"\bodrazu\b", "SPELLING", "HIGH", "od razu"),
    (r"\bprzedewszystkim\b", "SPELLING", "HIGH", "przede wszystkim"),
    (r"\bwkońcu\b", "SPELLING", "HIGH", "w końcu"),
    (r"\bz pośród\b", "SPELLING", "HIGH", "spośród"),
    (r"\bniechcę\b", "SPELLING", "HIGH", "nie chcę"),
    (r"\bniema\b", "SPELLING", "HIGH", "nie ma"),
    (r"\bwziąść\b", "GRAMMAR", "HIGH", "wziąć"),
    (r"\bposzłem\b", "GRAMMAR", "HIGH", "poszedłem"),
    (r"\b(w|wy)łanczać\b", "GRAMMAR", "HIGH", "włączać / wyłączać"),
    (r"\btą (?=[a-ząćęłńóśźż]+ę\b)", "GRAMMAR", "MEDIUM", "tę (accusative singular feminine)"),
    (r"\bw każdym bądź razie\b", "COLLOCATION", "HIGH", "w każdym razie / bądź co bądź"),
    (r"\bpełni(ć|ł|ła|ło|li|ły|ą|)? rolę\b", "COLLOCATION", "MEDIUM", "odgrywać rolę / pełnić funkcję"),
    (r"\bcofa\w* się do tyłu\b", "PLEONASM", "MEDIUM", "cofać się"),
    (r"\bwraca\w* z powrotem\b", "PLEONASM", "MEDIUM", "wracać"),
    (r"\bkontynuowa\w* dalej\b", "PLEONASM", "MEDIUM", "kontynuować"),
    (r"\bokres\w* czasu\b", "PLEONASM", "LOW", "okres"),
    (r"\bpotencjaln\w+ możliwoś\w+\b", "PLEONASM", "LOW", "możliwość"),
    (r"\bna dzień dzisiejszy\b", "STYLE", "MEDIUM", "dziś / obecnie"),
    (r"\bw dniu dzisiejszym\b", "STYLE", "LOW", "dziś"),
    (r"\bw oparciu o\b", "STYLE", "LOW", "na podstawie / opierając się na"),
    (r"\bniniejszym\b", "STYLE", "LOW", "(remove: officialese)"),
    (r"\b(za)?adres\w* (problem|kwesti|potrzeb)\w*", "CALQUE", "MEDIUM", "zająć się / rozwiązać"),
    (r"\b(zrobić|robi) (sens|różnicę)\b", "CALQUE", "MEDIUM", "mieć sens / mieć znaczenie"),
    (r"\bilość (użytkownik|osób|plików|elementów|błędów|wpisów|testów|zadań|rekordów|commitów|wierszy|żądań|zapytań|wizyt|sztuk|dni)\w*",
     "COLLOCATION", "MEDIUM", "liczba … (countable nouns)"),
]

# spójniki/zaimki wymagające przecinka przed (zdanie podrzędne)
SUB = r"(że|żeby|aby|ponieważ|gdyż|który|która|które|którego|której|któremu|którym|którzy|których|którymi|którą)"
PREP = {"w", "we", "o", "na", "do", "z", "ze", "przez", "dla", "po", "od", "przy", "za", "pod", "nad", "ku", "bez",
        "przed", "między", "u", "wśród", "według", "wg", "wewnątrz", "względem", "podstawie", "pomocą", "ramach", "trakcie", "wyniku", "przypadku", "zakresie", "obrębie", "sprawie", "stosunku", "dzięki", "mimo", "wobec", "spośród"}
COMPOUND = {"mimo", "chyba", "zwłaszcza", "tyle", "tak", "jako", "dlatego", "tylko", "zanim", "aż", "pomimo", "podczas",
            "przy", "czym", "to"}  # „to że” zostawiamy — zbyt wiele wyjątków
COORD = {"i", "oraz", "lub", "albo", "a", "ani", "czy", "bądź", "lecz", "ale"}


def strip_inline(line: str) -> str:
    # kod i adresy zastępujemy jednym słowem-zaślepką, żeby nie tworzyć sztucznych odstępów
    line = re.sub(r"`[^`]*`", "KOD", line)
    line = re.sub(r"https?://\S+", "URL", line)
    line = re.sub(r"\]\([^)]*\)", "]", line)   # cel linku Markdown
    return line


def prose_lines(text: str):
    """Linie prozy. Wyłączenia: `<!-- polish-lint: ignore-file -->`, bloki `<!-- polish-lint: off -->` … `on`."""
    if re.search(r"^\s*<!--\s*polish-lint:\s*ignore-file", text, re.M):
        return
    off = False
    in_code = False
    in_front = text.startswith("---\n")
    for no, raw in enumerate(text.splitlines(), 1):
        if in_front:
            if no > 1 and raw.strip() == "---":
                in_front = False
            continue
        if re.match(r"\s*<!--\s*polish-lint:\s*off", raw):
            off = True
        if re.match(r"\s*<!--\s*polish-lint:\s*on", raw):
            off = False
            continue
        if off:
            continue
        if raw.lstrip().startswith(("```", "~~~")):
            in_code = not in_code
            continue
        if in_code or raw.startswith("    ") or raw.lstrip().startswith("<!--"):
            continue
        yield no, strip_inline(raw)


def check_line(line: str) -> list[tuple[str, str, str, str]]:
    out = []
    for pat, cat, prio, sug in WORDS:
        for m in re.finditer(pat, line, re.I):
            out.append((cat, prio, m.group().strip(), sug))
    # typografia
    for m in re.finditer(r'(?<![\w`])"([^"\n]{1,80})"(?![\w`])', line):
        if PL_CHARS.search(m.group(1)) or re.search(r"[a-z]", m.group(1)):
            out.append(("TYPOGRAPHY", "LOW", m.group(), f"„{m.group(1)}”"))
    body = line.lstrip()
    lead = len(line) - len(body)
    for m in re.finditer(r"(?<=\w) - (?=\w)", line):
        if m.start() > lead + 1:   # nie wypunktowanie
            out.append(("TYPOGRAPHY", "LOW", line[max(0, m.start() - 12):m.end() + 12].strip(), "en dash „ – ” instead of hyphen „ - ”"))
    for m in re.finditer(r"\w \s*([,.;:!?])(?=\s|$)", line):
        if not re.search(r"\d \.\d|\.\.\.", line[m.start():m.end() + 2]):
            out.append(("TYPOGRAPHY", "MEDIUM", line[max(0, m.start() - 10):m.end()].strip(), "no space before punctuation"))
    for m in re.finditer(r"(?<=\S)  +(?=\S)", body):
        if "|" not in body:
            out.append(("TYPOGRAPHY", "LOW", body[max(0, m.start() - 10):m.end() + 10].strip(), "single space"))
    if re.search(r"\w\.\.\.(\s|$)", line):
        out.append(("TYPOGRAPHY", "LOW", "...", "ellipsis „…”"))
    # nagłówek w stylu angielskim („Title Case”) — po polsku wielka litera tylko na początku i w nazwach własnych
    h = re.match(r"\s*#{1,6}\s+(.+)$", line)
    if h:
        head = re.sub(r"\([^)]*\)|—.*$|–.*$", "", h.group(1))          # bez nawiasów i dopisków po myślniku
        english = re.search(r"\b(the|and|of|to|for|with|between|when|how|is|a|an|in|on)\b", head, re.I)
        words = [w for w in re.findall(r"[A-Za-ząćęłńóśźżĄĆĘŁŃÓŚŹŻ]+", head) if len(w) > 3]
        polish = [w for w in words if PL_CHARS.search(w) or re.search(
            r"(cja|cji|sja|sji|zja|ja|ji|ów|ych|ami|ach|ości|ość|enie|anie|ania|enia|ski|cki|owy|owa|owe)$", w.lower())]
        if not english and len(words) >= 2 and len(polish) >= 2 and all(w[0].isupper() and not w.isupper() for w in words):
            out.append(("SPELLING", "LOW", h.group(1).strip()[:60], "heading: capitalise only the first word and proper names"))
    # brak przecinka przed zdaniem podrzędnym
    for m in re.finditer(rf"(?<![\w-]){SUB}\b", line):
        before = line[:m.start()]
        words = re.findall(r"[\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ-]+|[^\s\w]", before)
        i = len(words) - 1
        while i >= 0 and words[i].lower() in PREP | COMPOUND:
            i -= 1
        if i < 0:
            continue
        prev = words[i]
        if prev.lower() in COORD or not re.match(r"[\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ]", prev):
            continue   # po spójniku współrzędnym albo po znaku (przecinek, nawias, myślnik, dwukropek…)
        if m.group(1).startswith("któr") and prev.lower() in {"kiedy", "jak", "co", "gdzie", "czy", "który", "która", "które"}:
            continue   # pytanie zależne / nagłówek „kiedy który”
        if m.group(1) == "że" and prev.lower() in {"to", "tak", "tyle", "dlatego", "tylko", "chyba", "mimo", "zwłaszcza", "aż", "nie"}:
            continue
        frag = line[max(0, m.start() - 25):m.end()].strip()
        prio = "MEDIUM" if m.group(1) in ("że", "żeby", "ponieważ", "gdyż") else "LOW"   # „który” bywa w pytaniu zależnym — tylko sygnał
        out.append(("PUNCTUATION", prio, frag, f"check for a comma before „{m.group(1)}” (or before the preposition/compound conjunction)"))
    return out


def lint_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not PL_CHARS.search(text):
        return []
    issues = []
    for no, line in prose_lines(text):
        for cat, prio, frag, sug in check_line(line):
            issues.append({"file": str(path), "line": no, "category": cat, "priority": prio, "fragment": frag, "suggestion": sug})
    return issues


def iter_files(args: list[str]):
    for a in args:
        p = Path(a)
        if p.is_dir():
            yield from sorted(x for x in p.rglob("*") if x.suffix in (".md", ".txt") and "node_modules" not in x.parts)
        elif p.is_file():
            yield p


def main(argv: list[str]) -> int:
    paths = [a for a in argv[1:] if not a.startswith("--")]
    if not paths:
        print(__doc__)
        return 2
    issues = [i for f in iter_files(paths) for i in lint_file(f)]
    if "--json" in argv:
        print(json.dumps(issues, ensure_ascii=False, indent=1))
    else:
        for i in issues:
            print(f"{i['file']}:{i['line']} [{i['category']}|{i['priority']}] {i['fragment']} → {i['suggestion']}")
        high = sum(1 for i in issues if i["priority"] == "HIGH")
        print(f"{'✓ No remarks' if not issues else f'⚠ {len(issues)} remarks (high: {high})'} — mechanical check; "
              "full proofreading: skill txt-polish-correctness")
    return 1 if "--strict" in argv and any(i["priority"] == "HIGH" for i in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
