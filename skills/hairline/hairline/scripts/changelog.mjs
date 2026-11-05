#!/usr/bin/env node
/**
 * Prints one version's section of CHANGELOG.md, without its heading: the body
 * of the GitHub Release.
 *
 *   node scripts/changelog.mjs 0.1.0
 *
 * A pre-release (0.1.0-rc.0) with no section of its own gets the section of
 * the version it leads to (0.1.0). No section at all is an error.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

export function section(changelog, version) {
  const lines = changelog.split("\n");
  const heading = (v) => lines.findIndex((l) => l.startsWith("## ") && l.slice(3).trim().replace(/^\[|\].*$| .*$/g, "") === v);
  let start = heading(version);
  if (start < 0 && version.includes("-")) start = heading(version.split("-")[0]);
  if (start < 0) return null;
  let end = lines.findIndex((l, i) => i > start && l.startsWith("## "));
  if (end < 0) end = lines.length;
  return lines.slice(start + 1, end).join("\n").trim();
}

if (import.meta.filename === process.argv[1]) {
  const version = process.argv[2];
  if (!version) { console.error("Usage: node scripts/changelog.mjs <version>"); process.exit(2); }
  const notes = section(readFileSync(join(import.meta.dirname, "..", "CHANGELOG.md"), "utf8"), version);
  if (!notes) { console.error(`CHANGELOG.md has no "## ${version}" section.`); process.exit(1); }
  console.log(notes);
}
