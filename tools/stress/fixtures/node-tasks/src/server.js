// Entry point.
import { createServer } from "node:http";
import { Store } from "./store.js";
import { makeHandler } from "./routes.js";

export function createApp(store = new Store()) {
  return createServer(makeHandler(store));
}

if (process.argv[1] && process.argv[1].endsWith("server.js")) {
  const port = Number(process.env.PORT || 3000);
  createApp().listen(port);
}
