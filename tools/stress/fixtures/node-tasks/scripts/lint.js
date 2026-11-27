// Minimal lint: no trailing whitespace, no `var`, no console.log in src/.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
let bad = 0;
const files = (dir) => readdirSync(dir).flatMap((f) => (statSync(join(dir, f)).isDirectory() ? files(join(dir, f)) : [join(dir, f)]));
for (const dir of ["src", "public", "test"]) {
  for (const p of files(dir)) {
    readFileSync(p, "utf8").split("\n").forEach((l, i) => {
      if (/\s+$/.test(l)) { console.error(`${p}:${i + 1} trailing whitespace`); bad++; }
      if (/\bvar\s/.test(l)) { console.error(`${p}:${i + 1} use let/const`); bad++; }
      if (dir === "src" && /console\.log/.test(l)) { console.error(`${p}:${i + 1} console.log in src`); bad++; }
    });
  }
}
process.exit(bad ? 1 : 0);
