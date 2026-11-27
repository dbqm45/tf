import { test } from "node:test";
import assert from "node:assert/strict";
import { createApp } from "../src/server.js";

async function withServer(fn) {
  const app = createApp();
  await new Promise((r) => app.listen(0, r));
  const base = `http://127.0.0.1:${app.address().port}`;
  try { await fn(base); } finally { app.close(); }
}

test("POST then GET /api/tasks", async () => {
  await withServer(async (base) => {
    const r = await fetch(`${base}/api/tasks`, { method: "POST", body: JSON.stringify({ title: "x", priority: "high" }) });
    assert.equal(r.status, 201);
    const list = await (await fetch(`${base}/api/tasks`)).json();
    assert.equal(list.length, 1);
    assert.equal(list[0].priority, "high");
  });
});

test("serves the page", async () => {
  await withServer(async (base) => {
    const html = await (await fetch(`${base}/`)).text();
    assert.match(html, /<h1>/);
  });
});
