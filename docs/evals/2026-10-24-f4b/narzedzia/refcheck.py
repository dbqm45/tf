"""Czy dowody plik:linia do zmienionych plików wskazują po odświeżeniu tę samą treść co przed zmianą."""
import os, re, subprocess, sys
base, new, files = sys.argv[1], sys.argv[2], open(sys.argv[3]).read().split()
D = "docs/project/00-reconstruction"
REF = re.compile(r"(?<![\w/.@-])((?:[\w.@-]+/)*[\w.@-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?")
def src(root, rel, head=False):
    if head:
        return subprocess.run(["git", "-C", root, "show", f"HEAD:{rel}"], capture_output=True, text=True).stdout.split("\n")
    return open(os.path.join(root, rel), encoding="utf-8", errors="replace").read().split("\n")
ok = bad = other = 0
for dp, dn, fn in os.walk(os.path.join(base, D)):
    dn[:] = [x for x in dn if x != "raw"]
    for f in fn:
        if not (f.endswith(".md") or f.endswith(".json") and dp.endswith("modules")):
            continue
        rel = os.path.relpath(os.path.join(dp, f), base)
        if f == "manifest.json": continue
        a = REF.findall(open(os.path.join(base, rel), encoding="utf-8").read())
        b = REF.findall(open(os.path.join(new, rel), encoding="utf-8").read())
        if len(a) != len(b):
            print("różna liczba dowodów", rel, len(a), len(b)); continue
        for (p, l, _), (q, m, _) in zip(a, b):
            if p != q: print("różna ścieżka", rel, p, q); continue
            if p not in files:
                other += l != m
                continue
            o, n = src(base, p, True), src(new, p)
            if int(l) - 1 < len(o) and int(m) - 1 < len(n) and o[int(l) - 1].strip() == n[int(m) - 1].strip():
                ok += 1
            else:
                bad += 1; print("✗", rel, f"{p}:{l}->{m}", repr(o[int(l)-1][:60] if int(l)-1 < len(o) else None), repr(n[int(m)-1][:60] if int(m)-1 < len(n) else None))
print(f"dowody do zmienionych plików: trafne {ok}, chybione {bad}; zmienione numery w innych plikach: {other}")
