import type { CSSProperties } from "react";
import { Assembly } from "@/components/assembly";
import { Footer, Topbar } from "@/components/chrome";
import { Install } from "@/components/install";
import { SkillLink } from "@/components/skill-link";
import { COUNT } from "@/lib/figures";
import { install } from "@/lib/snippets";
import { cap } from "@/lib/words";

const SITE = process.env.NEXT_PUBLIC_SITE_URL!;

/** Where a block falls in the hero's stagger. */
const at = (i: number) => ({ "--i": i }) as CSSProperties;

/**
 * The home, as one column: the pitch, the command with the way in, the way to the
 * skill, then a window drawn in hairlines, assembling itself layer by layer. The
 * figures live on /figures and /docs.
 */
export default function Page() {
  return (
    <>
      <Topbar />
      <main className="mx-auto max-w-[1080px] px-[clamp(18px,5vw,28px)] pb-24 pt-[clamp(48px,9vh,96px)]">
        <section aria-labelledby="hairline" className="hero-rise grid grid-cols-[minmax(0,1fr)] justify-items-center text-center">
          <h1 id="hairline" className="hero-title" style={at(0)}>
            Line drawings that <em>answer</em> the pointer.
          </h1>
          <p className="hero-sub" style={at(1)}>{cap(COUNT)} isometric figures for the web. SVG, no dependencies, React or plain DOM.</p>
          <div className="hero-get" style={at(2)}>
            <Install commands={install(SITE)} />
            <a className="btn btn-primary press" href="/docs">Get started</a>
          </div>
          <p className="hero-skill" style={at(3)}><SkillLink /></p>
          <div className="hero-art" style={at(4)}><Assembly /></div>
        </section>
      </main>
      <Footer />
    </>
  );
}
