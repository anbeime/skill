import type { CSSProperties } from "react";
import type { Metadata } from "next";
import { Exploded } from "@lucasmarkes/hairline/react";

/** The Open Graph card, as a page: scripts/og.mjs opens the figure's layers with the pointer and photographs it at 1200 × 630 into public/og.png. */
export const metadata: Metadata = { robots: { index: false } };

/* heavier, darker lines than the site's, through the figure's public theme, so they survive a feed shrinking the card */
const feed = { "--hairline-stroke": "1.35", "--hairline-mid": "#9a9aa2", "--hairline-lo": "#cfcfd5", "--hairline-edge": "#7c7c85" } as CSSProperties;

export default function Og() {
  return (
    <main className="relative h-[630px] w-[1200px] overflow-hidden">
      {/* far larger than the card, so it runs off the top and the right */}
      <div className="absolute" style={{ width: 1500, left: 280, top: -520 }}>
        <Exploded theme="light" intensity={1} style={feed} />
      </div>
      <div className="absolute bottom-14 left-16 w-[440px]">
        <p className="text-[22px] font-medium tracking-[-0.02em] text-muted">hairline</p>
        <h1 className="mt-5 text-[52px] font-medium leading-[1.02] tracking-[-0.045em]">
          Line drawings that <em className="font-serif text-[1.08em] font-normal tracking-[-0.02em]">answer</em> the pointer.
        </h1>
        <div className="mt-8 flex flex-col gap-1 font-mono text-[17px] text-muted">
          <p>npm i @lucasmarkes/hairline</p>
          <p>npx skills add lucasmarkes/hairline</p>
        </div>
      </div>
    </main>
  );
}
