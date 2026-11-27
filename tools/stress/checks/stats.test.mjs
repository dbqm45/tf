import { test } from "node:test"; import assert from "node:assert/strict"; import { app, html } from "./_util.mjs";
test("T3 stats endpoint", async () => {
  const a = await app();
  try {
    let s = await (await fetch(`${a.base}/api/tasks/stats`)).json();
    assert.deepEqual({ open: s.open, done: s.done, total: s.total }, { open: 0, done: 0, total: 0 });
    for (const t of ["a", "b", "c"]) await fetch(`${a.base}/api/tasks`, { method: "POST", body: JSON.stringify({ title: t }) });
    await fetch(`${a.base}/api/tasks/2/toggle`, { method: "POST" });
    s = await (await fetch(`${a.base}/api/tasks/stats`)).json();
    assert.deepEqual({ open: s.open, done: s.done, total: s.total }, { open: 2, done: 1, total: 3 });
  } finally { a.close(); }
});
test("T3 UI shows open counter", async () => { assert.match(await html(), /Otwarte/); });
test("T3 existing API intact", async () => { const a = await app(); try { assert.equal((await fetch(`${a.base}/api/tasks`)).status, 200); } finally { a.close(); } });
