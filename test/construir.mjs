// Compila test/run.ts con los datos dentro (como el plugin) y lo ejecuta en Node.
import esbuild from "esbuild";
import { spawnSync } from "node:child_process";
import { mkdirSync } from "node:fs";

mkdirSync(".test", { recursive: true });
await esbuild.build({
	entryPoints: ["test/run.ts"],
	bundle: true,
	platform: "node",
	format: "esm",
	target: "node20",
	loader: { ".gz": "base64" },
	alias: { obsidian: "./test/obsidian-falso.ts" },
	outfile: ".test/run.mjs",
	logLevel: "warning",
});
const r = spawnSync(process.execPath, [".test/run.mjs", ...process.argv.slice(2)], { stdio: "inherit" });
process.exit(r.status ?? 1);
