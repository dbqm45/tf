// Minimal lint: no trailing whitespace, no `var`, no console.log in src/.
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
let bad = 0;
for (const dir of ["src", "public", "test"]) {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    readFileSync(p, "utf8").split("\n").forEach((l, i) => {
      if (/\s+$/.test(l)) { console.error(`${p}:${i + 1} trailing whitespace`); bad++; }
      if (/\bvar\s/.test(l)) { console.error(`${p}:${i + 1} use let/const`); bad++; }
      if (dir === "src" && /console\.log/.test(l)) { console.error(`${p}:${i + 1} console.log in src`); bad++; }
    });
  }
}
process.exit(bad ? 1 : 0);
