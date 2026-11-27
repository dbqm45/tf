import { test } from "node:test"; import assert from "node:assert/strict"; import { join } from "node:path";
import { readFileSync } from "node:fs"; import { PROJ } from "./_util.mjs";
test("README documents every endpoint", () => {
  const r = readFileSync(join(PROJ, "README.md"), "utf8");
  for (const re of [/GET\s+`?\/api\/tasks`?/, /POST\s+`?\/api\/tasks`?/, /POST\s+`?\/api\/tasks\/(:id|\{id\}|<id>)\/toggle/, /DELETE\s+`?\/api\/tasks\/(:id|\{id\}|<id>)/]) assert.match(r, re);
});
