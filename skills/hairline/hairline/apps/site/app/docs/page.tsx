import type { Metadata } from "next";
import type { CSSProperties } from "react";
import { Footer, Topbar } from "@/components/chrome";
import { Rail, type RailGroup } from "@/components/rail";
import { SECTIONS, type Group } from "@/lib/docs";
import { COUNT, LINKS } from "@/lib/figures";
import { highlight } from "@/lib/highlight";
import { share } from "@/lib/share";
import { tiny } from "@/lib/size";
import { CDN, CSS, EMPTY, QUICKSTART, REACT, REACT_SIGNATURE, VANILLA, VANILLA_SIGNATURE, install } from "@/lib/snippets";
import { cap } from "@/lib/words";
import { Api, GettingStarted, Reference } from "./sections";

const SITE = process.env.NEXT_PUBLIC_SITE_URL!;

/** A block's place in the header's entrance. */
const at = (i: number) => ({ "--i": i }) as CSSProperties;

export const metadata: Metadata = share("/docs", "Docs");

/** Each group of the rail under its own mark and colour. */
const MARK: Record<Group, Pick<RailGroup, "icon" | "color">> = {
  "Getting started": { icon: "bolt", color: "#3b82f6" },
  API: { icon: "braces", color: "#8b5cf6" },
  Reference: { icon: "stack", color: "#f59e0b" },
};
const RAIL: RailGroup[] = (Object.keys(MARK) as Group[]).map((group) => ({ title: group, ...MARK[group], items: SECTIONS.filter((s) => s.group === group) }));

/**
 * The docs: one page of sections. A Server Component, so every snippet is
 * highlighted at build and each figure goes through server rendering and
 * hydration on every deploy, as on the home.
 */
export default async function Docs() {
  const [quickstart, empty, reactSignature, react, vanillaSignature, vanilla, cdn, css] = await Promise.all([
    Promise.all(QUICKSTART.map(async (q) => ({ label: q.label, file: q.file, html: await highlight(q.code, q.lang) }))),
    highlight(EMPTY, "tsx"),
    highlight(REACT_SIGNATURE, "tsx"),
    highlight(REACT, "tsx"),
    highlight(VANILLA_SIGNATURE, "ts"),
    highlight(VANILLA, "ts"),
    highlight(CDN, "html"),
    highlight(CSS, "css"),
  ]);

  return (
    <>
      <Topbar />
      <Rail label="Docs" groups={RAIL} />
      <main className="col">
        <header className="hero-rise">
          <h1 className="col-h1" style={at(0)}>{cap(COUNT)} figures, one set of options.</h1>
          <p className="col-lede" style={at(1)}>
            Every figure takes the same five options and draws itself in SVG, with no dependencies. Install the package, paste a figure, and turn <code className="doc-code">intensity</code> up or down.
          </p>
        </header>
        <GettingStarted commands={install(SITE)} size={tiny()} quickstart={quickstart} empty={empty} />
        <Api code={{ reactSignature, react, vanillaSignature, vanilla, cdn }} />
        <Reference css={css} />
        <p className="col-end">
          Anything missing? <a className="doc-more" href={`${LINKS.github}/issues`}>Open an issue on GitHub</a>.
        </p>
      </main>
      <Footer />
    </>
  );
}
