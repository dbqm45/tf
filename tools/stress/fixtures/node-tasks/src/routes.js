// HTTP routing for the task API and static files.
import { readFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const PUBLIC = join(dirname(fileURLToPath(import.meta.url)), "..", "public");

function send(res, status, body, type = "application/json") {
  res.writeHead(status, { "Content-Type": type });
  res.end(type === "application/json" ? JSON.stringify(body) : body);
}

async function readBody(req) {
  let data = "";
  for await (const chunk of req) data += chunk;
  return data ? JSON.parse(data) : {};
}

export function makeHandler(store) {
  return async (req, res) => {
    const url = new URL(req.url, "http://localhost");
    try {
      if (url.pathname === "/api/tasks" && req.method === "GET") {
        return send(res, 200, store.list());
      }
      if (url.pathname === "/api/tasks" && req.method === "POST") {
        const body = await readBody(req);
        return send(res, 201, store.add(body));
      }
      const m = url.pathname.match(/^\/api\/tasks\/(\d+)(\/toggle)?$/);
      if (m && req.method === "POST" && m[2]) {
        const t = store.toggle(Number(m[1]));
        return t ? send(res, 200, t) : send(res, 404, { error: "not found" });
      }
      if (m && req.method === "DELETE" && !m[2]) {
        return store.remove(Number(m[1])) ? send(res, 204, "") : send(res, 404, { error: "not found" });
      }
      if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
        return send(res, 200, await readFile(join(PUBLIC, "index.html"), "utf8"), "text/html; charset=utf-8");
      }
      if (req.method === "GET" && url.pathname === "/app.js") {
        return send(res, 200, await readFile(join(PUBLIC, "app.js"), "utf8"), "text/javascript");
      }
      return send(res, 404, { error: "not found" });
    } catch (e) {
      return send(res, 400, { error: e.message });
    }
  };
}
