import { cp, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";


const srcDir = path.resolve("public"); // public source directory
const outDir = path.resolve("dist", "assets"); // dist (js) output directory

// copy assets from srcDir to outDir
async function main() {
  if (!existsSync(srcDir)) return;
  await mkdir(outDir, { recursive: true });
  await cp(srcDir, outDir, { recursive: true });
}

// execute the script and handle errors
main().catch((err) => {
  console.error(err);
  process.exit(1);
});
