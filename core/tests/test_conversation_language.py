#!/usr/bin/env python3
"""Language without settings (as in Claude): a fixed rule "you answer in the human's language" in the instructions, the commit language
detected from `git log` (a new repository: `commit_language.new_repo`, English by default), no `tf language`,
`tf commit-language` and `--language`. python3 .claude/tests/test_conversation_language.py"""
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "packs.py").is_file())


def load(name):
    spec = importlib.util.spec_from_file_location(f"cl_{name}", ROOT / ".tf" / "factory" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git_repo(path: Path, subjects: list[str]) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.com", "PATH": __import__("os").environ.get("PATH", "")}
    subprocess.run(["git", "init", "-q"], cwd=path, check=True, env=env)
    for i, s in enumerate(subjects):
        (path / f"f{i}.txt").write_text(s, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=path, check=True, env=env)
        subprocess.run(["git", "commit", "-q", "-m", s], cwd=path, check=True, env=env)
    return path


def main() -> int:
    pm = load("packs")
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    cfg = pm.load_yaml(ROOT / ".tf" / "factory" / "config.yaml")
    check("languages" not in cfg and "default_language" not in cfg and cfg.get("language_note"),
          "CL-1: config.yaml without `languages`/`default_language`, with a single `language_note` rule")
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        en = git_repo(t / "en", ["feat: add export to CSV", "fix: handle empty input in the parser",
                                 "docs: update the install guide", "refactor: move config loading into packs"])
        pl = git_repo(t / "pl", ["feat: dodaj eksport do CSV", "fix: popraw obsługę pustego wejścia",
                                 "docs: aktualizacja przewodnika instalacji", "refactor: przenieś ładowanie konfiguracji"])
        check(pm.commit_language(en) == "en", f"CL-2: English commits → en: {pm.commit_language(en)}")
        check(pm.commit_language(pl) == "pl", f"CL-3: Polish commits → pl: {pm.commit_language(pl)}")
        check(pm.commit_language(t / "missing") is None and pm.commit_language(git_repo(t / "empty", [])) is None,
              "CL-4: without git or without commits → None (a new repository)")
        lines = pm.language_lines(cfg, t / "missing")
        text = "\n".join(lines)
        check(cfg["language_note"].strip() in text and "in English" in text,
              f"CL-5: a new repository — the conversation rule and commits in English: {text}")
        check("in Polish" in "\n".join(pm.language_lines(cfg, pl)), "CL-6: repo z polskimi commitami → linia po polsku")
        org = {**cfg, "commit_language": {**cfg["commit_language"], "new_repo": "pl"}}
        check("in Polish" in "\n".join(pm.language_lines(org, t / "missing")),
              "CL-7: `commit_language.new_repo` (e.g. from the company pack) changes the language of a new repository")
        check("commit_language" in pm.ORG_CONFIG_KEYS and "default_language" not in pm.ORG_CONFIG_KEYS,
              f"CL-8: the company pack sets `commit_language`, not `default_language`: {pm.ORG_CONFIG_KEYS}")
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        s = t / pm.SETTINGS_REL
        s.parent.mkdir(parents=True)
        s.write_text('{"language": "pl", "commit_language": "en", "targets": ["claude"]}', encoding="utf-8")
        check(pm.drop_settings(t, "language", "commit_language") and __import__("json").loads(s.read_text()) ==
              {"targets": ["claude"]} and not pm.drop_settings(t, "language"),
              f"CL-11: an update removes the old language keys from the project settings, the rest stays: {s.read_text()}")
    tf = ROOT / ".tf" / "factory" / "tf.py"
    for cmd in ("language", "commit-language"):
        r = subprocess.run([sys.executable, str(tf), cmd, "pl"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
        check(r.returncode == 2 and "no longer" in r.stdout + r.stderr,
              f"CL-9: tf {cmd} removed — a message instead of a settings change: {r.returncode} {r.stdout}{r.stderr}")
    inst = load("install")
    args, opts = inst.parse_args(["install.py", "/tmp/x", "--language", "pl", "--commit-language", "en", "--yes"])
    check(args == ["/tmp/x"] and opts.get("--yes"), f"CL-10: the old --language/--commit-language do not become a directory: {args} {opts}")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} language without settings tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
