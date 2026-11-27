import { test } from "node:test";
import assert from "node:assert/strict";
import { Store } from "../src/store.js";

test("adds a task with default priority", () => {
  const s = new Store();
  const t = s.add({ title: "  Kupić mleko " });
  assert.equal(t.title, "Kupić mleko");
  assert.equal(t.priority, "normal");
  assert.equal(t.done, false);
});

test("rejects an empty title", () => {
  assert.throws(() => new Store().add({ title: " " }), /title is required/);
});

test("toggles and removes", () => {
  const s = new Store();
  const t = s.add({ title: "a" });
  assert.equal(s.toggle(t.id).done, true);
  assert.equal(s.remove(t.id), true);
  assert.equal(s.list().length, 0);
});
