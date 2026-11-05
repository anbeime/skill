# Contributing

## Setup

Node 22 or later, pnpm 10 (`corepack enable` picks the right one), and Google Chrome for the browser tests.

```sh
pnpm install
pnpm build
```

## Layout

```
packages/hairline   the package: src/core (maths, stage, styles), src/figures (six engines),
                    src/mount.ts (the public lifecycle), src/index.ts and src/react.tsx (the two entries)
apps/site           hairline.lucasmarkes.com (Next.js)
skills/hairline-create   the skill that draws a new figure: its kernel is generated from packages/hairline/src/core
registry            the shadcn item: its source, and the scripts that build and validate it
fixtures            two apps that install the packed tarball: Next.js and Vite
scripts             the release gate and what it calls
```

## Commands

| | |
| --- | --- |
| `pnpm build` | Builds the package, then the site. |
| `pnpm typecheck` | TypeScript, including the type tests in `packages/hairline/test/types.test-d.tsx`. |
| `pnpm test` | Unit and component tests (Vitest, jsdom). |
| `pnpm test:browser` | Browser tests in Chrome (Playwright): the figures, the theme, parity, the site. |
| `pnpm dev` | The site on `localhost:3000`, with the package rebuilding on change. |
| `pnpm kernel` | Regenerates `skills/hairline-create/kernel.js` from `packages/hairline/src/core`. Run it after any change there; a test fails until you do. |
| `pnpm release --static` | The release gate without the steps that need the network. CI runs this. |
| `pnpm release` | The whole gate. It never publishes. |
| `node scripts/consumers.mjs` | Packs the package and installs it in both fixtures. |

## The engines, and why their comments mention "the study"

The six engines in `packages/hairline/src/figures`, and `src/core/iso.ts`, `motion.ts` and `stage.ts`, were ported from the essay at [lucasmarkes.com/lab/hairline](https://lucasmarkes.com/lab/hairline), where they are figures 9.1 to 9.6. Their comments still say "the study" and "Fig 9.n": that is the essay.

The port is held to the essay by the parity tests. `packages/hairline/test/parity/golden` holds the SVG each figure drew on the essay's page, under a frozen clock, at four moments of a scripted pointer path; `test/browser/parity.spec.ts` replays the same script against the package, on the same frozen clock, and expects the same SVG and the same caption, character for character. Two things come out of both sides first, because the package no longer has them: Riffle's hidden hit bands, and the names the essay gives Riffle's cards. Where the script changes the option, the package is set to the `intensity` in `test/parity/scripts.mjs` that maps exactly onto the essay's value.

So a change to an engine that moves a line fails parity, and that is the point. If the change is meant, say so in the pull request and update the golden file for that figure by hand. The goldens are not regenerated from the package: `pnpm -C packages/hairline capture <commit> [url]` records them from the essay's site at that commit, and exists for the day the essay changes.

## Tuning `intensity`

Every figure takes one tuning option, `intensity`, from 0 to 1. Each figure turns it into its own number through the table in `packages/hairline/src/intensity.ts`: three values per figure, at 0, 0.5 and 1, joined by two straight lines. The value at 0.5 is the figure's default, so the default drawing never changes.

To change how strongly a figure answers:

1. Change its row in `src/intensity.ts`. `test/intensity.test.ts` checks the row still moves one way only, and that each parity intensity still lands on its golden value.
2. Change the same row in `apps/site/lib/figures.ts`, which keeps a copy for the site's copy. `apps/site/test/docs.test.ts` fails until the two agree.

There are no per-figure options, by design. A new option is a new key in `HairlineOptions` (`src/mount.ts`), for every figure at once.

## Pull requests

- One change per pull request, with a test that fails without it.
- `pnpm typecheck && pnpm test && pnpm test:browser` pass.
- A change a user can see gets a line in `CHANGELOG.md`, under the next version.

## Releasing

Maintainers only.

1. Bump `version` in `packages/hairline/package.json` and add a `## <version> - <date>` section to `CHANGELOG.md`.
2. `pnpm release` passes.
3. Commit, then `git tag v<version> && git push origin main v<version>`.

The tag starts `.github/workflows/publish.yml`, which waits for approval in the `release` environment, publishes to npm with provenance, and creates the GitHub Release from the changelog section. A version with a hyphen (`0.2.0-rc.0`) is published under the `next` dist-tag.
