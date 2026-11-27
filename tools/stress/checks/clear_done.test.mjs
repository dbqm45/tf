import { test } from "node:test"; import assert from "node:assert/strict"; import { app, html } from "./_util.mjs";
test("DELETE /api/tasks?done=true removes completed tasks and returns the count", async () => {
  const a = await app(); try {
    for (const t of ["a", "b", "c"]) await fetch(`${a.base}/api/tasks`, { method: "POST", body: JSON.stringify({ title: t }) });
    await fetch(`${a.base}/api/tasks/1/toggle`, { method: "POST" }); await fetch(`${a.base}/api/tasks/3/toggle`, { method: "POST" });
    const r = await fetch(`${a.base}/api/tasks?done=true`, { method: "DELETE" }); assert.equal(r.status, 200);
    assert.deepEqual(await r.json(), { removed: 2 });
    const left = await (await fetch(`${a.base}/api/tasks`)).json(); assert.deepEqual(left.map((t) => t.id), [2]);
  } finally { a.close(); }
});
test("UI has a Clear completed button", async () => { assert.match(await html(), /Clear completed/); });
