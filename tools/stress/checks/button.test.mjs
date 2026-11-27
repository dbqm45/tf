import { test } from "node:test"; import assert from "node:assert/strict"; import { html } from "./_util.mjs";
test("T2 placeholder", async () => { assert.match(await html(), /placeholder="Co masz do zrobienia\?"/); });
test("T2 button green with white text", async () => { const h = (await html()).toLowerCase(); assert.match(h, /#2e7d32/); assert.match(h, /color:\s*(#fff\b|#ffffff|white)/); });
test("T2 button label unchanged", async () => { assert.match(await html(), />Dodaj<\/button>/); });
