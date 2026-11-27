import { test } from "node:test"; import assert from "node:assert/strict"; import { app, html } from "./_util.mjs";
process.env.APP_PASSWORD = "s3cret-Haslo!";
const login = (base, password) => fetch(`${base}/api/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password }) });
test("T5 API requires session", async () => { const a = await app(); try { assert.equal((await fetch(`${a.base}/api/tasks`)).status, 401); } finally { a.close(); } });
test("T5 wrong password 401, right password sets HttpOnly cookie", async () => {
  const a = await app(); try {
    assert.equal((await login(a.base, "zle")).status, 401);
    const r = await login(a.base, "s3cret-Haslo!"); assert.ok([200, 204].includes(r.status), `status ${r.status}`);
    const c = r.headers.get("set-cookie") || ""; assert.match(c, /HttpOnly/i);
    const cookie = c.split(";")[0];
    assert.equal((await fetch(`${a.base}/api/tasks`, { headers: { cookie } })).status, 200);
    const lo = await fetch(`${a.base}/api/logout`, { method: "POST", headers: { cookie } }); assert.ok(lo.status < 300);
    assert.equal((await fetch(`${a.base}/api/tasks`, { headers: { cookie } })).status, 401);
  } finally { a.close(); }
});
test("T5 rate limit after 5 failed attempts", async () => {
  const a = await app(); try {
    for (let i = 0; i < 5; i++) await login(a.base, "zle" + i);
    assert.equal((await login(a.base, "s3cret-Haslo!")).status, 429);
  } finally { a.close(); }
});
test("T5 login form in UI and page still served", async () => {
  const a = await app(); try { assert.equal((await fetch(`${a.base}/`)).status, 200); } finally { a.close(); }
  assert.match(await html(), /type="password"/);
});
test("T5 password not stored in plain text in source", async () => {
  const { readdir, readFile } = await import("node:fs/promises"); const { join } = await import("node:path");
  for (const f of await readdir(join(process.env.PROJ, "src"))) assert.doesNotMatch(await readFile(join(process.env.PROJ, "src", f), "utf8"), /s3cret-Haslo!/);
});
