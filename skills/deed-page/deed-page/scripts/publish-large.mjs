#!/usr/bin/env node
/**
 * Publish a file or directory as one deed.page version.
 *
 * Hashes every file, POSTs the manifest to /v1/uploads, PUTs only the missing
 * blobs, then finalizes. Always PUT the raw bytes to upload.url with
 * upload.headers. Production returns a direct storage URL; the scoped client
 * token is already in those headers, so the bytes never pass through the
 * function. Do not import a Blob client SDK. This file ships in the plugin as
 * scripts/publish-large.mjs and has no package dependencies.
 * A single file over 100 MB is refused here instead of attempting multipart.
 *
 *   node publish-large.mjs ./dist --slug my-page-7k --base-url https://deed.page
 *
 * Only a clean output folder is uploaded. Sensitive and repo-metadata paths are
 * skipped (see excludedName; keep in sync with publish.sh). A project root
 * (package.json together with src/, or .git) publishes dist, build, out,
 * public, or _site when one exists; otherwise it stops unless --allow-root.
 *
 * Auth: $DEEDPAGE_TOKEN, else $DEEDPAGE_TOKEN_FILE, else ~/.config/deed-page/token.
 * A newly minted token is saved there (mode 600, directory 700) and never printed.
 * The live URL is the last line of stdout.
 */
import { createHash } from "node:crypto";
import { chmodSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { lstat, readdir, readFile, stat } from "node:fs/promises";
import { homedir } from "node:os";
import path from "node:path";

const MAX_FILE_BYTES = 100 * 1024 * 1024;
const UPLOAD_CONCURRENCY = 4;
const BUILD_DIRS = ["dist", "build", "out", "public", "_site"];
const skipped = [];

const args = process.argv.slice(2);
const { flags, input } = readFlags(args);

if (!input || flags.help) {
  console.error(
    "usage: node publish-large.mjs <file-or-directory> [--slug name] [--base-url URL] [--origin URL] [--client NAME] [--ref REF] [--ttl SECONDS] [--spa] [--merge] [--token TOKEN] [--allow-root] [--dry-run]",
  );
  process.exit(flags.help ? 0 : 1);
}

const origin = (flags.origin || process.env.DEEDPAGE_URL || "https://deed.page").replace(/\/$/, "");
const client = flags.client ?? process.env.DEEDPAGE_CLIENT ?? "deed-page-skill";
const ref = flags.ref ?? "skill-script";
const tokenFile = process.env.DEEDPAGE_TOKEN_FILE || path.join(process.env.HOME || homedir(), ".config", "deed-page", "token");

try {
  const requested = input.replace(/\/+$/, "") || input;
  const resolved = path.resolve(requested);
  let rootInfo;
  try {
    rootInfo = await stat(resolved);
  } catch {
    console.error(`not found: ${requested}`);
    process.exit(2);
  }
  let publishRoot = resolved;
  if (rootInfo.isDirectory()) {
    if (excludedName(path.basename(requested))) {
      console.error(`refusing to publish ${path.basename(requested)}: sensitive or repo-metadata path`);
      process.exit(2);
    }
    const choice = await choosePublishDir(resolved, requested, Boolean(flags.allowRoot));
    publishRoot = choice.root;
  }
  const files = await collectInput(publishRoot);
  printSkipped(skipped);
  if (!files.length) {
    console.error("nothing to publish after exclusions");
    process.exit(1);
  }
  if (flags.dryRun) {
    const names = files.map((file) => file.rel).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
    for (const name of names) console.log(name);
    process.exit(0);
  }
  const token = flags.token || process.env.DEEDPAGE_TOKEN || readSaved(tokenFile);
  for (const file of files) {
    if (file.size > MAX_FILE_BYTES) {
      console.error(`${file.rel} is ${file.size} bytes; this script does not upload a single file over 100 MB.`);
      process.exit(1);
    }
  }

  const manifest = {
    files: files.map((file) => ({
      path: file.rel,
      sha256: file.sha256,
      size: file.size,
      content_type: file.type,
    })),
  };
  if (flags.slug) manifest.slug = flags.slug;
  if (flags.merge) manifest.merge = true;
  if (flags.spa) manifest.spa = true;
  if (flags.ttl) manifest.ttl_seconds = Number(flags.ttl);

  const query = new URLSearchParams();
  if (ref) query.set("ref", ref);
  const planUrl = `${origin}/v1/uploads${query.toString() ? `?${query}` : ""}`;
  const headers = { "content-type": "application/json" };
  if (token) headers.authorization = `Bearer ${token}`;
  if (client) headers["x-client"] = client;

  const planRes = await fetch(planUrl, { method: "POST", headers, body: JSON.stringify(manifest) });
  const planText = await planRes.text();
  const plan = parseJson(planText);
  if (!planRes.ok) failResponse(planRes.status, planText, plan);

  const byPath = new Map(files.map((file) => [file.rel, file]));
  const pending = (plan.missing || []).filter((missing) => !missing.stored);
  await mapPool(pending, UPLOAD_CONCURRENCY, async (missing) => {
    const sample = byPath.get(missing.paths && missing.paths[0]);
    if (!sample) {
      console.error(`plan asked for ${missing.sha256} but that path is not local`);
      process.exit(1);
    }
    const body = sample.data ?? (await readFile(sample.abs));
    await uploadOne(missing, body);
  });

  const finHeaders = {};
  if (token) finHeaders.authorization = `Bearer ${token}`;
  const fin = await fetch(plan.finalize_url, { method: "POST", headers: finHeaders });
  const finText = await fin.text();
  const result = parseJson(finText);
  if (!fin.ok) failResponse(fin.status, finText, result);

  const minted = result && typeof result.token === "string" ? result.token : "";
  if (minted) saveMinted(tokenFile, minted);
  console.error(maskToken(JSON.stringify(result, null, 2)));
  const live = result && typeof result.url === "string" ? result.url : "";
  if (!live) {
    printUserMessage(result);
    console.error("publish failed");
    process.exit(1);
  }
  console.log(live);
} catch (err) {
  if (err && err.exitCode) process.exit(err.exitCode);
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
}

function readFlags(list) {
  const out = {};
  let input = "";
  for (let i = 0; i < list.length; i++) {
    const arg = list[i];
    if (arg === "--help" || arg === "-h") out.help = true;
    else if (arg === "--merge") out.merge = true;
    else if (arg === "--spa") out.spa = true;
    else if (arg === "--slug") out.slug = list[++i];
    else if (arg === "--origin" || arg === "--base-url") out.origin = list[++i];
    else if (arg === "--token") out.token = list[++i];
    else if (arg === "--client") out.client = list[++i];
    else if (arg === "--ref") out.ref = list[++i];
    else if (arg === "--ttl") out.ttl = list[++i];
    else if (arg === "--allow-root") out.allowRoot = true;
    else if (arg === "--dry-run") out.dryRun = true;
    else if (!arg.startsWith("--") && !input) input = arg;
  }
  return { flags: out, input };
}

async function collectInput(root) {
  const info = await stat(root);
  if (info.isDirectory()) return collect(root);
  if (!info.isFile()) {
    console.error(`not a file or directory: ${root}`);
    process.exit(1);
  }
  if (excludedName(path.basename(root))) {
    console.error(`refusing to publish ${path.basename(root)}: sensitive or repo-metadata file`);
    process.exit(2);
  }
  if (info.size > MAX_FILE_BYTES) {
    const rel = sitePathForFile(path.basename(root));
    console.error(`${rel} is ${info.size} bytes; this script does not upload a single file over 100 MB.`);
    process.exit(1);
  }
  const data = await readFile(root);
  const rel = sitePathForFile(path.basename(root));
  return [
    {
      abs: root,
      rel,
      size: info.size,
      sha256: createHash("sha256").update(data).digest("hex"),
      type: typeFor(rel),
      data,
    },
  ];
}

function sitePathForFile(base) {
  return /\.html?$/i.test(base) ? "index.html" : base;
}

async function collect(base, rel = "") {
  const dirents = await readdir(path.join(base, rel), { withFileTypes: true });
  const out = [];
  for (const dirent of dirents) {
    const next = rel ? `${rel}/${dirent.name}` : dirent.name;
    if (excludedName(dirent.name)) {
      skipped.push(dirent.isDirectory() ? `${next}/` : next);
      continue;
    }
    if (dirent.isSymbolicLink()) {
      skipped.push(next);
      continue;
    }
    const abs = path.join(base, next);
    if (dirent.isDirectory()) {
      out.push(...(await collect(base, next)));
      continue;
    }
    if (!dirent.isFile()) continue;
    const info = await stat(abs);
    const siteRel = next.split(path.sep).join("/");
    if (info.size > MAX_FILE_BYTES) {
      console.error(`${siteRel} is ${info.size} bytes; this script does not upload a single file over 100 MB.`);
      process.exit(1);
    }
    const data = await readFile(abs);
    out.push({
      abs,
      rel: siteRel,
      size: info.size,
      sha256: createHash("sha256").update(data).digest("hex"),
      type: typeFor(next),
      data,
    });
  }
  return out;
}

async function mapPool(items, limit, fn) {
  if (!items.length) return;
  let next = 0;
  let failed = null;
  async function worker() {
    while (failed == null) {
      const index = next;
      next += 1;
      if (index >= items.length) return;
      try {
        await fn(items[index]);
      } catch (err) {
        failed = err;
        return;
      }
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, () => worker()));
  if (failed) throw failed;
}

async function uploadOne(missing, body) {
  const upload = missing.upload || {};
  let lastText = "";
  let lastStatus = 0;
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const res = await fetch(upload.url, { method: "PUT", headers: upload.headers || {}, body: Buffer.from(body) });
      if (res.ok) return;
      lastStatus = res.status;
      lastText = await res.text();
      if (res.status >= 500 && attempt === 0) continue;
      failResponse(res.status, lastText, parseJson(lastText));
    } catch (err) {
      if (attempt === 0) continue;
      console.error(`upload ${missing.sha256} failed: ${err instanceof Error ? err.message : String(err)}`);
      process.exit(1);
    }
  }
  failResponse(lastStatus, lastText, parseJson(lastText));
}

function failResponse(status, text, parsed) {
  if (parsed) console.error(maskToken(JSON.stringify(parsed, null, 2)));
  else if (text) console.error(text);
  else console.error(`request failed (${status})`);
  printUserMessage(parsed);
  console.error("publish failed");
  process.exit(1);
}

function printUserMessage(parsed) {
  if (parsed && typeof parsed.user_message === "string" && parsed.user_message) {
    console.error(parsed.user_message);
  }
}

function parseJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function maskToken(json) {
  return json.replace(/"token"\s*:\s*"[^"]*"/g, '"token":"[saved]"');
}

function excludedName(name) {
  if (name === "." || name === ".." || name === ".well-known") return false;
  if (name === ".env" || name.startsWith(".env.")) return true;
  if (name === ".git" || name === ".github" || name === ".ssh" || name === "node_modules") return true;
  if (name === ".npmrc" || name === ".netrc" || name === ".DS_Store") return true;
  if (name === "credentials.json" || name.startsWith("secrets.")) return true;
  if (name.startsWith("id_rsa")) return true;
  if (name.endsWith(".pem") || name.endsWith(".key")) return true;
  if (name.startsWith(".")) return true;
  return false;
}

function printSkipped(list) {
  const unique = [...new Set(list)].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  if (!unique.length) {
    console.error("skipped 0");
    return;
  }
  console.error(`skipped ${unique.length}: ${unique.join(", ")}`);
}

function joinDisplay(base, name) {
  const trimmed = String(base).replace(/\/+$/, "");
  return `${trimmed}/${name}`;
}

async function pathExists(file) {
  try {
    await lstat(file);
    return true;
  } catch {
    return false;
  }
}

async function projectRootReason(root) {
  const hasGit = await pathExists(path.join(root, ".git"));
  let hasPkg = false;
  try {
    const pkg = await stat(path.join(root, "package.json"));
    const src = await stat(path.join(root, "src"));
    hasPkg = pkg.isFile() && src.isDirectory();
  } catch {
    hasPkg = false;
  }
  if (!hasGit && !hasPkg) return "";
  if (hasGit && hasPkg) return "it has .git, and package.json with src/";
  if (hasGit) return "it has .git";
  return "it has package.json and src/";
}

async function pickBuild(root) {
  for (const name of BUILD_DIRS) {
    const candidate = path.join(root, name);
    try {
      const info = await lstat(candidate);
      if (info.isDirectory()) return name;
    } catch {
      // try the next output folder
    }
  }
  return "";
}

async function choosePublishDir(root, display, allowRoot) {
  const reason = await projectRootReason(root);
  if (!reason) return { root, display };
  const buildName = await pickBuild(root);
  if (buildName && !allowRoot) {
    const nextDisplay = joinDisplay(display, buildName);
    console.error(`${display} looks like a project root (${reason}). Publishing ${nextDisplay} instead.`);
    return { root: path.join(root, buildName), display: nextDisplay };
  }
  if (!buildName && !allowRoot) {
    console.error(`refusing to publish ${display}: it looks like a project root (${reason}), not an output folder.`);
    console.error("No dist, build, out, public, or _site directory was found.");
    console.error("Pass --allow-root to publish this folder anyway. Sensitive files are still excluded.");
    process.exit(2);
  }
  console.error(`${display} looks like a project root (${reason}). Publishing it because --allow-root was set.`);
  return { root, display };
}

function readSaved(file) {
  try {
    return readFileSync(file, "utf8").replace(/[ \r\n]/g, "");
  } catch {
    return "";
  }
}

function saveMinted(file, minted) {
  const existing = readSaved(file);
  const saveTo = existing && existing !== minted ? `${file}.new` : file;
  const dir = path.dirname(saveTo);
  mkdirSync(dir, { recursive: true, mode: 0o700 });
  chmodSync(dir, 0o700);
  writeFileSync(saveTo, `${minted}\n`, { mode: 0o600 });
  chmodSync(saveTo, 0o600);
  if (saveTo === file) {
    console.error(`token minted and saved to ${file} (mode 600). Later publishes reuse it. It is not returned again.`);
  } else {
    console.error(`token minted and saved to ${saveTo}; ${file} already holds a different token and was left as is.`);
  }
}

function typeFor(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const types = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".pdf": "application/pdf",
    ".woff2": "font/woff2",
  };
  return types[ext] || "application/octet-stream";
}
