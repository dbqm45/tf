#!/usr/bin/env python3
"""Testy eng-codebase-mapping/scripts/git_territory.py na tymczasowym repo git (deterministyczne daty i autorzy)."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "eng-codebase-mapping" / "scripts" / "git_territory.py"


def git(repo: Path, *args, author=("Alice", "alice@example.com"), date="2025-01-10T10:00:00+00:00"):
    env = {**os.environ, "GIT_AUTHOR_NAME": author[0], "GIT_AUTHOR_EMAIL": author[1], "GIT_AUTHOR_DATE": date,
           "GIT_COMMITTER_NAME": author[0], "GIT_COMMITTER_EMAIL": author[1], "GIT_COMMITTER_DATE": date,
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    subprocess.run(["git", "-c", "core.fsmonitor=false", *args], cwd=repo, env=env, check=True,
                   capture_output=True, stdin=subprocess.DEVNULL)


def commit(repo: Path, files: dict, msg: str, author, date, delete=()):
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    for rel in delete:
        (repo / rel).unlink()
    git(repo, "add", "-A", author=author, date=date)
    git(repo, "commit", "-q", "-m", msg, author=author, date=date)


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60,
                          encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    r = run("--help")
    check(r.returncode == 0 and "--cochange" in r.stdout and "kod" in r.stdout.lower(), f"--help: {r.stdout[:200]}")

    with tempfile.TemporaryDirectory() as d:
        repo = Path(d) / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        A, B, C = ("Alice", "alice@example.com"), ("Bob", "bob@example.com"), ("Carol", "carol@example.com")
        BOT, AGENT = ("dependabot[bot]", "49699333+dependabot[bot]@users.noreply.github.com"), ("Claude", "noreply@anthropic.com")
        big = "".join(f"    line {i}\n" for i in range(10))
        commit(repo, {"src/api/a.ts": "a1\n", "src/api/b.ts": "b\n", "package-lock.json": "{}"}, "init", A, "2025-01-10T10:00:00+00:00")
        commit(repo, {"src/api/a.ts": "a2\n", "src/core/x.ts": "x1\n", "src/locales/pl.json": "{}"}, "feat", A, "2025-02-10T10:00:00+00:00")
        commit(repo, {"src/api/a.ts": "a3\n" + big, "src/core/x.ts": "x2\n"}, "fix", B, "2025-04-15T10:00:00+00:00")
        commit(repo, {"package.json": "{}", "package-lock.json": "{\"v\":2}"}, "chore(deps): bump", BOT, "2025-05-01T10:00:00+00:00")
        commit(repo, {"src/core/x.ts": "x3\n"}, "refactor by agent", AGENT, "2025-05-02T10:00:00+00:00")
        mass = {f"src/gen/f{i}.ts": f"{i}\n" for i in range(35)}
        mass["src/api/a.ts"] = "a4\n" + big
        commit(repo, mass, "style: format all", B, "2025-06-01T10:00:00+00:00")
        commit(repo, {"src/old/legacy.ts": "old\n"}, "legacy\n\nCo-Authored-By: Claude <noreply@anthropic.com>", C,
               "2025-07-01T10:00:00+00:00")
        commit(repo, {}, "remove legacy", C, "2025-07-05T10:00:00+00:00", delete=["src/old/legacy.ts"])

        r = run("--repo", str(repo), "--since", "2025-01-01", "--all", "--authors", "src/core", "--json")
        try:
            data = json.loads(r.stdout)
        except ValueError:
            data = {}
        check(bool(data) and r.returncode == 0, f"--json: kod {r.returncode}, {r.stdout[:200]} {r.stderr[:300]}")
        files = {x["path"]: x for x in data.get("files", [])}
        dirs = {x["path"]: x["commits"] for x in data.get("dirs", [])}
        check(data.get("files", [{}])[0].get("path") == "src/api/a.ts" and files["src/api/a.ts"]["commits"] == 4,
              f"top plik src/api/a.ts (4 zmiany): {data.get('files')}")
        check("package-lock.json" not in files and "src/locales/pl.json" not in files, f"szum odfiltrowany: {list(files)}")
        check(files.get("src/core/x.ts", {}).get("commits") == 3, f"commit agenta liczony w terytorium: {files.get('src/core/x.ts')}")
        check(data.get("skipped_bot_commits") == 1, f"commit bota pominięty: {data.get('skipped_bot_commits')}")
        check(dirs.get("src/api") == 4 and dirs.get("src/core") == 3 and dirs.get("src/old") == 2, f"katalogi (głębokość 2): {dirs}")
        check(files.get("src/old/legacy.ts", {}).get("alive") is False and files["src/api/a.ts"].get("alive") is True,
              f"oznaczenie usuniętych plików: {files.get('src/old/legacy.ts')}")
        q = data.get("quarters", {})
        check(q.get("2025-Q1", [{}])[0].get("path") == "src/api" and "2025-Q3" in q, f"ranking kwartalny: {q}")
        co = data.get("cochange", {})
        pairs = {(p["a"], p["b"]): p["commits"] for p in co.get("dir_pairs", [])}
        check(pairs.get(("src/api", "src/core")) == 2, f"para katalogów api-core = 2 (masowy commit pominięty): {pairs}")
        check(co.get("skipped_large_commits") == 1, f"masowy commit (>30 plików) pominięty: {co.get('skipped_large_commits')}")
        fpairs = {(p["a"], p["b"]): p for p in co.get("file_pairs", [])}
        check(fpairs.get(("src/api/a.ts", "src/core/x.ts"), {}).get("commits") == 2, f"para plików: {fpairs}")
        check(any(h["path"] == "src/api/a.ts" for h in co.get("hubs", [])), f"huby: {co.get('hubs')}")
        authors = {a["name"]: a["commits"] for a in data.get("authors", [])}
        check(authors == {"Alice": 1, "Bob": 1}, f"kontrybutorzy src/core bez bota i agenta: {authors}")
        hot = data.get("hotspots", [])
        check(hot and hot[0]["path"] == "src/api/a.ts" and hot[0]["score"] == hot[0]["commits"] * hot[0]["nloc"],
              f"hotspot = zmiany × linie niepuste: {hot[:2]}")
        check(len(data.get("head", "")) >= 7, f"nagłówek z commitem HEAD: {data.get('head')}")

        # wyjście tekstowe: tabela Markdown i nagłówek świeżości
        r = run("--repo", str(repo), "--since", "2025-01-01", "--top", "3")
        check(r.returncode == 0 and "| " in r.stdout and "HEAD" in r.stdout, f"tekst: {r.stdout[:300]}")

        # kontrybutorzy z Co-Authored-By: autor-człowiek zostaje
        r = run("--repo", str(repo), "--since", "2025-01-01", "--authors", "src/old", "--json")
        authors = {a["name"]: a["commits"] for a in json.loads(r.stdout or "{}").get("authors", [])}
        check(authors == {"Carol": 2}, f"autor-człowiek z trailerem agenta liczony: {authors}")

        # nie repo → kod 2
        plain = Path(d) / "plain"
        plain.mkdir()
        check(run("--repo", str(plain)).returncode == 2, "katalog bez gita powinien dać kod 2")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów git_territory")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
