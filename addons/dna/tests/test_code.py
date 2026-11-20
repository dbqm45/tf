#!/usr/bin/env python3
"""Tests of the UI catalog (lib/code.py) and its output (rules/ui.md, catalog/ui.md).
python3 addons/dna/tests/test_code.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

import dna  # noqa: E402
from lib import code, detect, emit, verify  # noqa: E402
from test_dna import evidence_ok, repo  # noqa: E402

FILES = {
    "package.json": '{"name": "shop", "workspaces": ["packages/*", "apps/*"]}',
    "package-lock.json": json.dumps({"packages": {"node_modules/@mui/material": {"version": "5.15.20"},
                                                  "node_modules/react": {"version": "18.3.1"}}}),
    "packages/ui/package.json": '{"name": "@acme/ui"}',
    "packages/ui/src/index.ts": "export { PriceTag } from './PriceTag';\n",
    "apps/web/package.json": '{"name": "web", "dependencies": {"@mui/material": "^5.15.0", "react": "^18.2.0",'
                             ' "@acme/ui": "*"}}',
    "apps/web/src/components/Card.tsx": "export function Card() { return null; }\n",
    "apps/web/src/components/OldModal.tsx": "/**\n * @deprecated use Dialog from @mui/material\n */\n"
                                            "export function OldModal() { return null; }\n",
    "apps/web/src/styles/tokens.css": ":root {\n  --color-primary: #0a66c2;\n  --space-4: 16px;\n}\n"
                                      ".x { color: var(--color-primary); }\n",
    "apps/web/src/theme.ts": "import { createTheme } from '@mui/material';\nexport const theme = createTheme({});\n",
    "tokens/color.tokens.json": '{"color": {"brand": {"$value": "#0a66c2", "$type": "color"}}}',
    "apps/web/src/pages/Orders.tsx": "import { Button, Stack, type ButtonProps } from '@mui/material';\n"
                                     "import type { Theme } from '@mui/material';\n"
                                     "import { Card } from '../components/Card';\n"
                                     "import styles from './Orders.module.css';\n"
                                     "export const Orders = () => <Stack sx={{ p: 2 }}><Button /><Card /></Stack>;\n",
    "apps/web/src/pages/Invoices.tsx": "import { Button, Stack as S } from '@mui/material';\n"
                                       "import { Card } from '../components/Card';\n"
                                       "import { OldModal } from '../components/OldModal';\n"
                                       "import { PriceTag } from '@acme/ui';\n"
                                       "import styles from './Invoices.module.css';\n"
                                       "export const Invoices = () => <S><Button /><Card /><OldModal /><PriceTag /></S>;\n",
    "apps/web/src/pages/Legacy.jsx": "import Button from '@mui/material/Button';\n"
                                     "import { OldModal } from '../components/OldModal';\n"
                                     "export const Legacy = () => <div style={{ margin: 4 }}><Button /><OldModal /></div>;\n",
}


def catalog():
    root = repo(FILES)
    items = detect.detect(root, ADDON / "registry")["items"]
    blocks, cov = code.ui(root, items, {})
    return root, items, blocks, cov


def test_design_system_components_by_usage():
    root, _, blocks, _ = catalog()
    ds = [b for b in blocks if b["data"].get("origin") == "design-system"]
    names = [(b["data"]["package"], b["data"]["name"]) for b in ds]
    assert names[0] == ("@mui/material", "Button") and ds[0]["data"]["files"] == 3   # also the subpath default import
    assert ("@mui/material", "Stack") in names                                        # `Stack as S` counts as Stack
    assert not any(n.endswith("Props") for _, n in names)
    assert ("@acme/ui", "PriceTag") in names                                          # workspace UI package
    assert next(b for b in ds if b["data"]["name"] == "PriceTag")["data"]["package_origin"] == "workspace"
    for b in blocks:
        evidence_ok(root, b)


def test_own_components_and_deprecation():
    _, _, blocks, _ = catalog()
    own = {b["data"]["name"]: b for b in blocks if b["data"].get("origin") == "own"}
    assert own["Card"]["data"]["files"] == 2 and own["Card"]["status"] == "auto-accepted"
    assert own["OldModal"]["data"]["deprecated"] and own["OldModal"]["status"] == "abandoned"
    assert own["OldModal"]["evidence"][0].endswith("OldModal.tsx:4")


def test_tokens_theme_and_styling():
    _, _, blocks, _ = catalog()
    tokens = {b["data"]["name"]: b["data"] for b in blocks if b["data"].get("topic") == "token"}
    assert tokens["--color-primary"]["value"] == "#0a66c2" and tokens["--color-primary"]["uses"] == 1
    assert tokens["--space-4"]["value"] == "16px"
    assert tokens["color.brand"]["syntax"] == "dtcg"
    assert any(b["data"].get("topic") == "theme" and b["data"]["path"].endswith("theme.ts") for b in blocks)
    styling = {b["data"]["method"]: b["data"] for b in blocks if b["data"].get("topic") == "styling"}
    assert styling["css-modules"]["files"] == 2 and styling["css-modules"]["of"] == 3
    assert styling["inline-style"]["files"] == 1 and styling["sx-prop"]["files"] == 1


def test_output_rules_and_catalog():
    root = repo(FILES)
    out = root / "out"
    assert dna.cmd_learn(root, out, online=False, cache=root / "cache") == 0
    assert verify.check_out(out, root) == []
    rules = (out / "rules" / "ui.md").read_text(encoding="utf-8")
    assert rules.startswith("---\npaths:\n") and '"**/*.tsx"' in rules
    assert "`Button`" in rules and "`@mui/material`" in rules and "css-modules in 67%" in rules
    assert "Deprecated, do not use in new code: `OldModal`" in rules
    assert "e.g. `import { Button } from '@mui/material'`" in rules          # 2 named imports beat 1 subpath
    assert len(rules.splitlines()) <= emit.RULES_MAX_LINES
    cat = (out / "catalog" / "ui.md").read_text(encoding="utf-8")
    assert "| Button | `import { Button } from '@mui/material'` | 3 |" in cat and "`--space-4`" in cat
    assert "UI: use the project's components" in (out / "INDEX.md").read_text(encoding="utf-8")


def test_repo_without_ui_has_no_ui_files():
    root = repo({"go.mod": "module x\n\ngo 1.22\n"})
    out = root / "out"
    assert dna.cmd_learn(root, out, online=False, cache=root / "cache") == 0
    assert not (out / "rules").exists() and not (out / "catalog").exists()


def main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"✗ {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - fails}/{len(tests)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
