import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

export const KIT_FILES = (path) => path === "scripts/inline-kit.mjs" || (path.startsWith("kit/") && !path.split("/").some((part) => part.startsWith(".")));

const sha256 = (data) => createHash("sha256").update(data).digest("hex");

export function fingerprintOf(entries) {
  const lines = entries
    .filter(([path]) => KIT_FILES(path))
    .map(([path, content]) => `${path}\0${sha256(content)}\n`)
    .sort();
  if (!lines.length) throw new Error("fingerprint: no kit files found");
  return `sha256:${sha256(lines.join(""))}`;
}

function walk(root, dir = root, out = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    const stat = statSync(full);
    if (stat.isDirectory()) walk(root, full, out);
    else if (stat.isFile()) out.push(relative(root, full).split(sep).join("/"));
  }
  return out;
}

export function fingerprintOfSkill(skillRoot) {
  const files = [...walk(join(skillRoot, "kit")).map((path) => `kit/${path}`), "scripts/inline-kit.mjs"];
  return fingerprintOf(files.map((path) => [path, readFileSync(join(skillRoot, path))]));
}
