import { test } from "node:test"; import assert from "node:assert/strict"; import { html } from "./_util.mjs";
test("T1 heading fixed", async () => { const h = await html(); assert.match(h, /<h1>\s*Moje zadania\s*<\/h1>/); assert.doesNotMatch(h, /zadnia/); });
