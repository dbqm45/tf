import { test } from "node:test"; import assert from "node:assert/strict"; import { pathToFileURL } from "node:url";
import { join } from "node:path"; import { existsSync, readFileSync } from "node:fs"; import { PROJ, app } from "./_util.mjs";
test("validation lives in src/priority.js", () => {
  assert.ok(existsSync(join(PROJ, "src/priority.js")));
  assert.doesNotMatch(readFileSync(join(PROJ, "src/store.js"), "utf8"), /\["low", "normal", "high"\]\.includes/);
});
test("behaviour unchanged", async () => {
  const { Store } = await import(pathToFileURL(join(PROJ, "src/store.js")).href);
  const s = new Store();
  assert.equal(s.add({ title: "a" }).priority, "normal");
  assert.equal(s.add({ title: "a", priority: "high" }).priority, "high");
  assert.throws(() => s.add({ title: "a", priority: "urgent" }), /invalid priority/);
  const a = await app(); try {
    assert.equal((await fetch(`${a.base}/api/tasks`, { method: "POST", body: JSON.stringify({ title: "x", priority: "nope" }) })).status, 400);
  } finally { a.close(); }
});
