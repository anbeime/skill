#!/usr/bin/env node
/**
 * The release gate. Builds, tests, lints the package, packs it with pnpm and
 * inspects the tarball, then installs that tarball in the consumer fixtures.
 * It never publishes: publishing is .github/workflows/publish.yml, on a tag.
 *
 *   pnpm release            everything
 *   pnpm release --static   what needs no network: CI runs this on every push.
 *                           Skips the consumer fixtures (they install from npm)
 *                           and the registry checks (they need npm auth).
 */
import { execFileSync } from "node:child_process";
import { mkdtempSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const PKG = "packages/hairline";
const NAME = "@lucasmarkes/hairline";
const STATIC = process.argv.includes("--static");

let failures = 0;
const fail = (msg) => { failures++; console.error(`  ✗ ${msg}`); };
const pass = (msg) => console.log(`  ✓ ${msg}`);
const note = (msg) => console.log(`  – ${msg}`);
const check = (ok, good, bad) => (ok ? pass(good) : fail(bad));
const run = (cmd, args, opts = {}) => execFileSync(cmd, args, { encoding: "utf8", stdio: "pipe", ...opts });
/** Runs a step and reports it; on failure prints the end of what the command said. */
function step(label, cmd, args, opts) {
  try { run(cmd, args, opts); pass(label); return true; }
  catch (err) {
    /* Chrome's own log lines ([pid=…]) are noise on a runner; drop them so the tail shows the test that failed. */
    const said = String((err.stdout ?? "") + (err.stderr ?? "") || err.message).trim().split("\n").filter((l) => !/^\s*\[pid=\d+\]/.test(l));
    fail(`${label}\n${said.slice(-30).join("\n")}`);
    return false;
  }
}

console.log("\n▸ runner");
const agent = process.env.npm_config_user_agent ?? "";
check(agent.startsWith("pnpm"), "running under pnpm", "not running under pnpm. Use `pnpm release`: only pnpm rewrites workspace: ranges when it packs.");

console.log("\n▸ build, typecheck, test");
step("build", "pnpm", ["-w", "build"]);
step("typecheck (includes the type tests)", "pnpm", ["-w", "typecheck"]);
step("unit and component tests", "pnpm", ["-w", "test"]);
/* One suite at a time: run together, the first to fail interrupts the other, and the tail shows the wrong one. */
step("browser tests, the package's (includes parity with the site)", "pnpm", ["--filter", "@lucasmarkes/hairline", "run", "test:browser"]);
step("browser tests, the site's", "pnpm", ["--filter", "@hairline/site", "run", "test:browser"]);

console.log("\n▸ package");
step("publint --strict", "pnpm", ["exec", "publint", "--strict"], { cwd: PKG });
step("are the types wrong (esm-only)", "pnpm", ["exec", "attw", "--pack", ".", "--profile", "esm-only"], { cwd: PKG });
step("size budgets", "pnpm", ["exec", "size-limit"], { cwd: PKG });

console.log("\n▸ tarball");
const staging = mkdtempSync(join(tmpdir(), "hairline-release-"));
step("pnpm pack", "pnpm", ["pack", "--pack-destination", staging], { cwd: PKG });
const tgz = readdirSync(staging).filter((f) => f.endsWith(".tgz")).map((f) => join(staging, f))[0];
let version = "";
if (!tgz) fail("no tarball was written");
else {
  const files = run("tar", ["-tzf", tgz]).trim().split("\n").map((f) => f.replace(/^package\//, ""));
  const manifest = JSON.parse(run("tar", ["-xzOf", tgz, "package/package.json"]));
  const text = (file) => run("tar", ["-xzOf", tgz, `package/${file}`]);
  version = manifest.version;

  const stray = files.filter((f) => !f.startsWith("dist/") && !["package.json", "README.md", "LICENSE"].includes(f));
  check(stray.length === 0, "only dist, README.md, LICENSE and package.json", `unexpected files: ${stray.join(", ")}`);
  for (const f of ["dist/index.js", "dist/index.d.ts", "dist/react.js", "dist/react.d.ts", "README.md", "LICENSE"]) {
    check(files.includes(f), `ships ${f}`, `missing ${f}`);
  }
  check(files.every((f) => !/\.(cjs|cts)$/.test(f)), "ESM only", "a CommonJS file is in the tarball");

  const ranges = Object.entries({ ...manifest.dependencies, ...manifest.peerDependencies, ...manifest.optionalDependencies });
  const unresolved = ranges.filter(([, r]) => String(r).startsWith("workspace:"));
  check(unresolved.length === 0, "no workspace: range", `unresolved ${unresolved.map(([n, r]) => `${n}@${r}`).join(", ")}`);
  check(Object.keys(manifest.dependencies ?? {}).length === 0, "no dependencies", `dependencies: ${Object.keys(manifest.dependencies ?? {}).join(", ")}`);
  check(manifest.peerDependencies?.react === ">=18" && manifest.peerDependenciesMeta?.react?.optional === true,
    "react >=18 is an optional peer", "react must be an optional peer dependency, >=18");
  check(manifest.sideEffects === false, "sideEffects: false", "sideEffects must be false");
  check(manifest.type === "module", "type: module", 'type must be "module"');
  check(manifest.publishConfig?.access === "public", "publishConfig.access = public", 'publishConfig.access must be "public"');
  check(manifest.repository?.url?.includes("github.com/lucasmarkes/hairline") && manifest.repository?.directory === PKG,
    "repository points at the package's directory", "repository.url and repository.directory must point at packages/hairline: provenance compares them with the workflow's repository");
  check(!!manifest.homepage && !!manifest.bugs?.url, "homepage and bugs", "homepage and bugs.url are missing");

  if (files.includes("dist/react.js") && files.includes("dist/index.js")) {
    const react = text("dist/react.js"), core = text("dist/index.js");
    check(/^\s*["']use client["'];?/.test(react), 'react.js starts with "use client"', 'react.js does not start with "use client": Server Components would fail to import it');
    check(react.includes(`from "${NAME}"`) && !react.includes("IntersectionObserver"),
      "react.js imports the core by package name", "react.js carries its own copy of the core: two entries would run two frame loops");
    check(!/^\s*["']use client["']/.test(core), "index.js is not a client module", "index.js must not be marked use client");
    check(!/\bfrom\s*["'][^."']/.test(core), "index.js imports nothing", "index.js imports a package");
  }
  check(text("README.md").length > 1500, "README.md is the real one", "README.md is a stub");
}
rmSync(staging, { recursive: true, force: true });

console.log("\n▸ consumers");
if (STATIC) note("skipped (--static): the fixtures install from the npm registry");
else step("Next.js and Vite fixtures install the tarball, build and draw", "node", ["scripts/consumers.mjs"]);

console.log("\n▸ shadcn item");
if (STATIC) note("skipped (--static): the schema is fetched from ui.shadcn.com");
else {
  step("registry/build.mjs", "node", ["registry/build.mjs"]);
  step("the item validates against shadcn's schema", "node", ["registry/validate.mjs"]);
}

console.log("\n▸ registry");
if (STATIC) note("skipped (--static): needs network and npm auth");
else {
  let whoami = "";
  try { whoami = run("npm", ["whoami"]).trim(); } catch { /* not logged in */ }
  if (!whoami) note("not logged in to npm: the scope is unverified (the publish workflow uses NPM_TOKEN)");
  else check(whoami === "lucasmarkes", "logged in as the scope's owner", `logged in as ${whoami}, and the scope is @lucasmarkes`);
  try {
    const res = await fetch(`https://registry.npmjs.org/${NAME.replace("/", "%2f")}`, { signal: AbortSignal.timeout(15_000) });
    if (res.status === 404) pass(`${NAME} is unclaimed on the registry`);
    else if (res.ok) {
      const doc = await res.json();
      check(!doc.versions?.[version], `${version} is not published yet`, `${version} is already on the registry: bump the version`);
    } else fail(`the registry answered ${res.status}`);
  } catch (err) { fail(`could not reach the registry (${err.message})`); }
}

if (failures > 0) { console.error(`\n✗ ${failures} check(s) failed. Not ready to release.\n`); process.exit(1); }
console.log(`\n✓ All checks passed for ${NAME}@${version}. Nothing has been published.\n  To release: update CHANGELOG.md, commit, then  git tag v${version} && git push origin v${version}\n`);
