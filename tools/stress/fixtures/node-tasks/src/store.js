// In-memory task store.
export class Store {
  constructor() {
    this.tasks = [];
    this.nextId = 1;
  }

  add({ title, priority = "normal" }) {
    if (!title || typeof title !== "string" || !title.trim()) {
      throw new Error("title is required");
    }
    if (!["low", "normal", "high"].includes(priority)) {
      throw new Error("invalid priority");
    }
    const task = { id: this.nextId++, title: title.trim(), priority, done: false, createdAt: new Date().toISOString() };
    this.tasks.push(task);
    return task;
  }

  list() {
    return [...this.tasks];
  }

  toggle(id) {
    const t = this.tasks.find((x) => x.id === id);
    if (!t) return null;
    t.done = !t.done;
    return t;
  }

  remove(id) {
    const i = this.tasks.findIndex((x) => x.id === id);
    if (i < 0) return false;
    this.tasks.splice(i, 1);
    return true;
  }
}
