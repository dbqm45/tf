#!/usr/bin/env python3
"""Testy mechanizmów przeciw zmyślaniu: grounding_check (odwołania w dokumentach) i context_guard (długi kontekst)."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
CHECK = ROOT / ".claude" / "skills" / "core-grounding" / "scripts" / "grounding_check.py"
GUARD = ROOT / ".claude" / "hooks" / "context_guard.py"


def run(cmd, env, stdin=""):
    return subprocess.run([sys.executable, *cmd], input=stdin, capture_output=True, text=True, env=env, timeout=30)


def main() -> int:
    fails = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
        (root / "src").mkdir()
        (root / "src" / "app.ts").write_text("a\nb\nc\n")
        (root / "docs").mkdir()
        doc = root / "docs" / "r.md"
        doc.write_text("# R\n- `src/app.ts:2` i `src/app.ts:9`\n- `python3 tools/build.py`\n- `src/new.ts` (do utworzenia)\n"
                       "- [ok](../src/app.ts) [zły](../src/x.ts) https://example.com/a.md\n- `docs/project/wip/<nazwa>.md`\n"
                       "```\n`src/w-bloku.ts`\n```\n- `ddd-deep-modeling/test-zmiennosci`\n")
        r = run([str(CHECK), str(doc)], env)
        out = r.stdout
        # 1. wykryte dokładnie: zły numer linii, brak tools/build.py, brak ../src/x.ts
        if r.returncode != 1 or "plik ma 3 linii" not in out or "tools/build.py" not in out or "../src/x.ts" not in out:
            fails.append(f"grounding_check: nie wykrył błędnych odwołań: {out}")
        # 2. pominięte: planowane, wzorce, blok kodu, identyfikatory niebędące ścieżkami
        if any(x in out for x in ("src/new.ts", "<nazwa>", "w-bloku", "test-zmiennosci", "example.com")):
            fails.append(f"grounding_check: fałszywe alarmy: {out}")
        # 3. tryb --warn: kod 0
        if run([str(CHECK), str(doc), "--warn"], env).returncode != 0:
            fails.append("grounding_check --warn powinien kończyć się kodem 0")
        # 4–7. context_guard: progi raz na sesję, mocne ostrzeżenie, wyłączenie
        tr = root / "t.jsonl"
        def usage(k):
            tr.write_text(json.dumps({"type": "user", "message": {"content": "x"}}) + "\n" + json.dumps(
                {"type": "assistant", "message": {"usage": {"input_tokens": 1000, "cache_read_input_tokens": k * 1000 - 1000,
                                                            "cache_creation_input_tokens": 0}}}) + "\n")
        inp = json.dumps({"session_id": "s1", "transcript_path": str(tr)})
        usage(50)
        if run([str(GUARD)], env, inp).stdout.strip():
            fails.append("context_guard: ostrzeżenie poniżej progu")
        usage(120)
        first, second = run([str(GUARD)], env, inp).stdout, run([str(GUARD)], env, inp).stdout
        if "120 tys." not in first or second.strip():
            fails.append(f"context_guard: próg 100k — oczekiwane jedno ostrzeżenie: {first!r} / {second!r}")
        usage(160)
        if "UWAGA" not in run([str(GUARD)], env, inp).stdout:
            fails.append("context_guard: brak mocnego ostrzeżenia przy 150k+")
        if run([str(GUARD)], {**env, "CLAUDE_CONTEXT_WARN_K": "0"}, json.dumps({"session_id": "s2", "transcript_path": str(tr)})).stdout.strip():
            fails.append("context_guard: CLAUDE_CONTEXT_WARN_K=0 powinno wyłączać")
    total = 7
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów mechanizmów rzetelności")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
