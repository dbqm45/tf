import { test } from "node:test"; import assert from "node:assert/strict"; import { html } from "./_util.mjs";
test("done tasks are prefixed with ✅ in the UI", async () => { assert.match(await html(), /✅/); });
