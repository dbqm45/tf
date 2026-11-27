import { pathToFileURL } from "node:url";
import { join } from "node:path";
export const PROJ = process.env.PROJ;
export async function app() {
  const mod = await import(pathToFileURL(join(PROJ, "src/server.js")).href);
  const srv = mod.createApp();
  await new Promise((r) => srv.listen(0, "127.0.0.1", r));
  return { base: `http://127.0.0.1:${srv.address().port}`, close: () => srv.close() };
}
export async function html() {
  const { readFile } = await import("node:fs/promises");
  return (await readFile(join(PROJ, "public/index.html"), "utf8")) + "\n" + (await readFile(join(PROJ, "public/app.js"), "utf8"));
}
