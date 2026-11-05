#!/usr/bin/env node
/**
 * Puts a figure on the bench: `node build.mjs <figure.js> [out.html]` writes
 * one self-contained page, bench.html with kernel.js and the figure in its two
 * slots and nothing else changed, and prints where it is. Without a path the
 * page is hairline-<name>.html in the working directory.
 */
import { readFileSync, realpathSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = (p) => fileURLToPath(new URL(p, import.meta.url));

/** The page for a figure's source. The replacements are functions so `$&` in the kernel or the figure is pasted as it is. */
export function assemble(figure) {
  const kernel = readFileSync(here("./kernel.js"), "utf8").replace(/\r\n/g, "\n").trimEnd();
  return readFileSync(here("./bench.html"), "utf8").replace(/\r\n/g, "\n")
    .replace("/*KERNEL*/", () => `\n${kernel}\n`)
    .replace("/*FIGURE*/", () => `\n${figure.replace(/\r\n/g, "\n").trim()}\n`);
}

/** The figure's name, read from its declaration: the last hairline({ … }) call, as validate.mjs reads it, so a `name:` earlier in the figure is not taken for it. */
export function nameOf(figure) {
  const call = [...figure.matchAll(/\bhairline\s*\(\s*\{/g)].at(-1);
  return call ? /\bname:\s*["'`]([a-z][a-z0-9-]*)["'`]/.exec(figure.slice(call.index))?.[1] ?? null : null;
}

/** Whether two resolved paths are one file. Windows paths ignore case, and the drive letter's case can differ between the two. */
export const same = (a, b, platform = process.platform) => platform === "win32" ? a.toLowerCase() === b.toLowerCase() : a === b;

/* The skill is often installed as a symlink, so the path Node was given is resolved before it is compared. */
if (process.argv[1] && same(realpathSync(process.argv[1]), realpathSync(here("./build.mjs")))) {
  const [src, out] = process.argv.slice(2);
  if (!src) {
    console.error("usage: node build.mjs <figure.js> [out.html]");
    process.exit(2);
  }
  const figure = readFileSync(src, "utf8");
  const file = resolve(out ?? `hairline-${nameOf(figure) ?? "figure"}.html`);
  writeFileSync(file, assemble(figure));
  console.log(file);
}
