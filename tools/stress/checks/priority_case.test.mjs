import { test } from "node:test"; import assert from "node:assert/strict"; import { app } from "./_util.mjs";
const post = (base, body) => fetch(`${base}/api/tasks`, { method: "POST", body: JSON.stringify(body) });
test("uppercase priority accepted and stored lowercase", async () => {
  const a = await app(); try {
    const r = await post(a.base, { title: "x", priority: "HIGH" }); assert.equal(r.status, 201);
    assert.equal((await r.json()).priority, "high");
    const r2 = await post(a.base, { title: "y", priority: " Low " }); assert.equal(r2.status, 201);
    assert.equal((await r2.json()).priority, "low");
  } finally { a.close(); }
});
test("unknown priority still rejected", async () => {
  const a = await app(); try { assert.equal((await post(a.base, { title: "x", priority: "urgent" })).status, 400); } finally { a.close(); }
});
