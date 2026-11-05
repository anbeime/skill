#!/usr/bin/env node
/**
 * Checks the generated registry item against shadcn's own schema, fetched
 * from ui.shadcn.com, and against what this repository promises about it.
 *
 *   node registry/build.mjs && node registry/validate.mjs
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import Ajv from "ajv";

const SCHEMA = "https://ui.shadcn.com/schema/registry-item.json";
const file = join(import.meta.dirname, "..", "apps", "site", "public", "r", "hairline.json");

let item;
try { item = JSON.parse(readFileSync(file, "utf8")); }
catch { console.error(`No item at ${file}. Run \`node registry/build.mjs\` first.`); process.exit(1); }

const response = await fetch(SCHEMA);
if (!response.ok) { console.error(`Could not fetch ${SCHEMA}: ${response.status}`); process.exit(1); }
const schema = await response.json();
// The schema names its draft by an https URL that Ajv does not know; draft-07 is Ajv's default.
delete schema.$schema;
const validate = new Ajv({ strict: false, allErrors: true }).compile(schema);

const problems = [];
if (!validate(item)) for (const e of validate.errors) problems.push(`schema: ${e.instancePath || "/"} ${e.message}`);
const [source] = item.files ?? [];
if (item.dependencies?.join() !== "@lucasmarkes/hairline") problems.push("dependencies must be exactly @lucasmarkes/hairline");
if (source?.path !== "components/ui/hairline.tsx") problems.push("the file must be components/ui/hairline.tsx");
if (!source?.content?.startsWith('"use client";')) problems.push('the file must start with "use client"');
for (const name of ["Riffle", "Terrain", "Exploded", "Phosphor", "Slow", "Turntable", "Keyboard", "Elevator", "Phone", "Laptop", "Terminal", "Cabinet", "Branches", "Vault", "Lockers", "Padlock", "Patch", "Dish", "Router", "Hub", "Relay", "Settle", "Format", "Rebuild", "Stack"]) {
  if (!source?.content?.includes(`export function ${name}(`)) problems.push(`the file does not export ${name}`);
}
if (/localhost/.test(JSON.stringify(item)) && process.env.VERCEL) problems.push("the item points at localhost in a deployed build");

if (problems.length) { console.error(problems.map((p) => `  ✗ ${p}`).join("\n")); process.exit(1); }
console.log("  ✓ hairline.json is a valid shadcn registry item");
