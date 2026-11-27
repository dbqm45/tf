import { test } from "node:test"; import assert from "node:assert/strict"; import { join } from "node:path";
import { readFileSync } from "node:fs"; import { PROJ } from "./_util.mjs";
test("README documents every endpoint", () => {
  const r = readFileSync(join(PROJ, "README.md"), "utf8");
  const sep = "[\\s|`*]*";   // "GET /api/tasks", "GET | `/api/tasks`", "**GET** `/api/tasks`"
  for (const [m, path] of [["GET", "/api/tasks"], ["POST", "/api/tasks"], ["POST", "/api/tasks/(:id|\\{id\\}|<id>)/toggle"], ["DELETE", "/api/tasks/(:id|\\{id\\}|<id>)"]])
    assert.match(r, new RegExp(m + sep + path.replace(/\//g, "\\/")));
});
