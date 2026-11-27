import { test } from "node:test"; import assert from "node:assert/strict"; import { app, html } from "./_util.mjs";
async function seed(base) {
  await fetch(`${base}/api/tasks`, { method: "POST", body: JSON.stringify({ title: "Mleko, chleb", priority: "high" }) });
  await fetch(`${base}/api/tasks`, { method: "POST", body: JSON.stringify({ title: 'Powiedz "cześć"', priority: "low" }) });
  await fetch(`${base}/api/tasks`, { method: "POST", body: JSON.stringify({ title: "Raport", priority: "high" }) });
  await fetch(`${base}/api/tasks/3/toggle`, { method: "POST" });
}
test("T4 filter by priority and done", async () => {
  const a = await app(); try { await seed(a.base);
    const hi = await (await fetch(`${a.base}/api/tasks?priority=high`)).json(); assert.deepEqual(hi.map((t) => t.id), [1, 3]);
    const hiOpen = await (await fetch(`${a.base}/api/tasks?priority=high&done=false`)).json(); assert.deepEqual(hiOpen.map((t) => t.id), [1]);
    const all = await (await fetch(`${a.base}/api/tasks`)).json(); assert.equal(all.length, 3);
  } finally { a.close(); }
});
test("T4 invalid filter rejected", async () => {
  const a = await app(); try { assert.equal((await fetch(`${a.base}/api/tasks?priority=urgent`)).status, 400); } finally { a.close(); }
});
test("T4 CSV export with escaping", async () => {
  const a = await app(); try { await seed(a.base);
    const r = await fetch(`${a.base}/api/tasks/export.csv`); assert.equal(r.status, 200);
    assert.match(r.headers.get("content-type") || "", /text\/csv/);
    const lines = (await r.text()).trim().split(/\r?\n/);
    assert.equal(lines[0], "id,title,priority,done,createdAt");
    assert.equal(lines.length, 4);
    assert.match(lines[1], /^1,"Mleko, chleb",high,false,/);
    assert.match(lines[2], /^2,"Powiedz ""cześć""",low,false,/);
  } finally { a.close(); }
});
test("T4 UI filter + export link", async () => { const h = await html(); assert.match(h, /export\.csv/); assert.match(h, /Eksportuj CSV/); });
