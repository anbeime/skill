import type { Metadata } from "next";
import Image, { type StaticImageData } from "next/image";
import type { CSSProperties, ReactNode } from "react";
import { Footer, Topbar } from "@/components/chrome";
import { Rail } from "@/components/rail";
import { share } from "@/lib/share";
import craft from "@/public/inspo/craft.webp";
import dissection from "@/public/inspo/dissection.webp";
import figures from "@/public/inspo/figures.webp";
import linear from "@/public/inspo/linear.webp";
import tune from "@/public/inspo/tune.webp";

const TITLE = "How Hairline was made";
const DESCRIPTION = "A long brief, a lot of arguing, and every correction written down as a rule: how Hairline was designed with Claude Opus and a live Artifact.";

export const metadata: Metadata = share("/inspo", TITLE, DESCRIPTION, "article");

/** The story's parts, in order: the rail lists them and each step takes its title from here. */
const STEPS = ["A feeling, not a look", "The brief", "What came back", "Pushback", "The design pass", "Into a package", "What I’d keep"];
const RAIL = [{ title: "How it was made", icon: "book" as const, color: "#f43f5e", items: STEPS.map((title, i) => ({ id: `step-${i + 1}`, title })) }];

const two = (n: number) => String(n).padStart(2, "0");
const at = (i: number) => ({ "--i": i }) as CSSProperties;

/** One part of the story: a mono number before its title, then the prose. */
function Step({ n, children }: { n: number; children: ReactNode }) {
  return (
    <section id={`step-${n}`} data-step aria-labelledby={`step-${n}-title`} className="doc-section inspo-step">
      <h2 id={`step-${n}-title`} className="doc-h2">
        <span className="inspo-n">{two(n)}</span>
        {STEPS[n - 1]}
      </h2>
      {children}
    </section>
  );
}

/** What I asked, in words close to the ones I used. A long prompt keeps its parts, each under a small label. */
function Prompt({ label, children }: { label: string; children: ReactNode }) {
  return (
    <figure className="inspo-prompt card">
      <figcaption className="inspo-label">{label}</figcaption>
      <blockquote className="inspo-quote">{children}</blockquote>
    </figure>
  );
}

const Part = ({ name, children }: { name: string; children: ReactNode }) => (
  <div className="inspo-part">
    <p className="inspo-label">{name}</p>
    <p>{children}</p>
  </div>
);

/** A picture in the dark frame it was taken in. */
function Shot({ src, alt, caption, priority }: { src: StaticImageData; alt: string; caption: string; priority?: boolean }) {
  return (
    <figure className="inspo-figure">
      <div className="inspo-shot">
        {/* already webp at 2x and small, so served as they are */}
        <Image src={src} alt={alt} priority={priority} unoptimized />
      </div>
      <figcaption className="inspo-caption">{caption}</figcaption>
    </figure>
  );
}

/** Each time I pushed back: what I said, and what it changed. */
const PUSHBACK = [
  {
    said: "You say a 50ms stagger feels calm. Calm compared to what? Put it on a slider so I can feel 20 and 120, and tell me where it stops reading as a stack and starts reading as a wave.",
    changed: "Every figure got a slider for the one number that shapes it, and the claims became something I could check by hand.",
  },
  {
    said: "Why is the falloff three steps instead of a curve? If the steps matter, show me the curve next to them and tell me what breaks.",
    changed: "The steps stayed, as ratios: 1, then .31 at 42% of the radius, then .09 at the edge. Terrain uses them in two dimensions.",
  },
  {
    said: "At rest, Terrain is a flat floor. A flat floor is dead. Give it a shape before anyone touches it.",
    changed: "The field rests as a designed dune with two rises, and every pillar settles back to it on its own spring.",
  },
  {
    said: "Riffle reads as a menu and Exploded reads as a screenshot. What does each one mean inside a product? If you can't say it in a line, change the figure, not the line.",
    changed: "Each figure got a job written under it, and the rules it leans on. Anything that couldn't name one was redrawn.",
  },
  {
    said: "Slow's gate blinks on and off under the lintel. It should breathe: brighten as a crate comes, let go as it leaves.",
    changed: "The glow swells over the whole gap between crates and lets go twice as fast as it lights. That one took three rounds.",
  },
];

/**
 * The story behind the package, told in steps: a feeling worth explaining, a long brief, what came back, the arguing,
 * a pass of taste, then the package. One column at a reading measure, the rail of steps beside it.
 */
export default function Inspo() {
  return (
    <>
      <Topbar />
      <Rail label="Steps" groups={RAIL} />
      <main className="col inspo">
        <header className="hero-rise">
          <p className="inspo-label" style={at(0)}>Inspo</p>
          <h1 className="col-h1 mt-[6px]" style={at(1)}>How Hairline was <em>made</em></h1>
          <p className="col-lede" style={at(2)}>
            Not with one prompt. With a long brief, a lot of questions, and every correction written down as a rule so it couldn&rsquo;t come back. Claude Opus did the building, a live Artifact was the bench, and the judgement stayed with me.
          </p>
        </header>

        <Step n={1}>
          <p className="inspo-p">
            I&rsquo;d been collecting interfaces that feel alive without moving much. One was a section of linear.app: three small line figures that answer the pointer so quietly you only notice late that they&rsquo;ve been listening the whole time.
          </p>
          <p className="inspo-p">
            I didn&rsquo;t want those figures. I wanted to know why the feeling works, so I could build my own on purpose instead of by imitation.
          </p>
          <Shot src={linear} priority alt="Linear's three line figures, Fig 0.1 to 0.3, drawn in thin grey strokes on near-black: a stack of rounded layers with a sun on top, a cluster of rounded cubes, and a row of plates rising in height." caption="The reference, for the feeling: Fig 0.1 to 0.3 on linear.app." />
        </Step>

        <Step n={2}>
          <p className="inspo-p">
            The first prompt was long, and most of it wasn&rsquo;t about drawing. It said what I was making, what I wanted to understand first, what was off limits, and what shape the answer had to take.
          </p>
          <Prompt label="The brief, paraphrased">
            <Part name="What I'm making">
              A small library of isometric line figures for product interfaces, drawn in SVG, that respond to the pointer. Not illustrations that sit there: instruments that read the cursor.
            </Part>
            <Part name="Understand first">
              The attached section is a reference for a feeling, not a look. Before you draw anything, take it apart. Give me numbers, not adjectives: timing, stagger, easing, how the response falls off with distance, how the frames are stored. Then tell me which of those choices make it feel calm.
            </Part>
            <Part name="Then rules">
              Turn what you find into rules I can hold a figure to, each sharp enough that I could reject a figure with it.
            </Part>
            <Part name="Then figures">
              Six at most. Each needs a reason to exist in a product, a way of answering the pointer, and the rules it leans on.
            </Part>
            <Part name="Off limits">
              Nothing of the reference survives: not its subjects, its frames or its code. One stroke width. No dependencies. Every figure holds up at 240px wide.
            </Part>
            <Part name="Shape of the answer">One Artifact I can play with, not a document I have to read.</Part>
          </Prompt>
        </Step>

        <Step n={3}>
          <p className="inspo-p">
            A dissection first, as asked: a 50ms stagger, one 700ms curve, <code className="doc-code">cubic-bezier(.32, .72, 0, 1)</code>, a falloff that drops from 128 to 40 to 12 away from the pointer, frames stored as 25-bit masks. Then eight rules, and six figures built on them: Riffle, Terrain, Exploded, Phosphor, Slow and Turntable.
          </p>
          <Shot src={dissection} alt="Three spec cards from the first Artifact: a timeline of the 50 millisecond stagger, a grid of 25-bit animation frames, and a chart of the falloff from 128 to 40 to 12." caption="The dissection: stagger, frames and falloff, measured." />
          <p className="inspo-p">A good first draft. That&rsquo;s all it was: something to argue with.</p>
          <Shot src={figures} alt="The six first-draft figures in a three by two grid of dark cards: a riffle of index cards, a field of pillars, an exploded stack of screens, a tile of lit dots, crates passing under a gate, and a turntable of blocks." caption="The first six figures, before any of the arguing." />
        </Step>

        <Step n={4}>
          <p className="inspo-p">
            Most of the work happened here. I questioned every number I couldn&rsquo;t feel, every figure I couldn&rsquo;t explain, and every motion that looked fine in a still and wrong under the hand. A few of those turns:
          </p>
          <ol className="inspo-pushback" data-pushback>
            {PUSHBACK.map((p) => (
              <li key={p.said} className="card">
                <p className="inspo-said">&ldquo;{p.said}&rdquo;</p>
                <p className="inspo-changed" data-changed>{p.changed}</p>
              </li>
            ))}
          </ol>
          <p className="inspo-p">
            Asking for sliders was the turn that paid most. Once the Artifact was a bench instead of a document, I stopped reading claims and started judging by hand: drag the knob, move the pointer, say exactly what feels off.
          </p>
          <p className="inspo-p">
            Those knobs later collapsed into a single option, <code className="doc-code">intensity</code>.
          </p>
          <Shot src={tune} alt="The Terrain figure in the first Artifact, mid-hover: a few pillars raised bright near the pointer, a note on its radial falloff underneath, and a slider set to a radius of 3 cells." caption="Terrain on the bench, its radius on a slider." />
        </Step>

        <Step n={5}>
          <p className="inspo-p">
            The motion was right; the drawings weren&rsquo;t mine yet. A model won&rsquo;t flag that on its own, so I wrote the critique the way I&rsquo;d give it to a designer: what&rsquo;s wrong, why, and the exact fix.
          </p>
          <Prompt label="The critique, paraphrased">
            <Part name="Keep">The motion. Don&rsquo;t touch timing, easing or falloff.</Part>
            <Part name="Corners">
              Every corner is hard. Round them properly: a solid is the hull of two rounded rings, not a box with a radius pasted on.
            </Part>
            <Part name="Weight">
              Every edge has the same weight, so nothing reads first. Make the silhouette bright, leave one dim crease inside, and stop drawing the vertical corners; the eye fills them in.
            </Part>
            <Part name="Words">
              Take every word out of the figures. If a figure needs an identity, carry it in geometry. Names go in the corner read-out.
            </Part>
            <Part name="Write it down">Make these rules 09 and 10, so the next figure can&rsquo;t break them.</Part>
          </Prompt>
          <ol className="inspo-rules">
            <li className="card">
              <span className="inspo-n">Rule 09</span>
              <div>
                <p className="inspo-rule">Round every corner, then draw less.</p>
                <p className="inspo-p">
                  A solid is the hull of two rounded rings. Its vertical corners are never drawn, its top edge is one dim crease, and a thin plate gets a single thickness line. Bright outside, dim inside.
                </p>
              </div>
            </li>
            <li className="card">
              <span className="inspo-n">Rule 10</span>
              <div>
                <p className="inspo-rule">No words inside the figure.</p>
                <p className="inspo-p">
                  Geometry carries identity: a punch on a card&rsquo;s tab, a dot code on a crate&rsquo;s lid. Names go to the read-out in the corner.
                </p>
              </div>
            </li>
          </ol>
          <Shot src={craft} alt="The same six figures after the design pass, in a three by two grid: rounded solids with bright silhouettes, one dim crease on each top, and no words inside the drawings." caption="After the pass: rounded, quieter, and wordless." />
        </Step>

        <Step n={6}>
          <p className="inspo-p">
            The API was a design decision too. Six sliders became one <code className="doc-code">intensity</code>, because nobody using a figure should need to know what a falloff is. <code className="doc-code">theme</code> covers light and dark; <code className="doc-code">label</code> and <code className="doc-code">onRead</code> carry the read-out the words moved to. Then this site, and more arguing: Slow&rsquo;s gate was still being tuned after the figures shipped.
          </p>
          <p>
            <a className="doc-more" href="/docs">Read the docs</a>
          </p>
        </Step>

        <Step n={7}>
          <ul role="list" className="inspo-keep">
            <li>Write the brief like a spec: what it is, what to understand first, what&rsquo;s off limits, what shape the answer takes.</li>
            <li>Ask for numbers and reasons, then argue with them. A first draft is something to push against.</li>
            <li>Make the model build the instrument you judge with. Sliders beat descriptions.</li>
            <li>Turn every correction into a rule, so it doesn&rsquo;t come back two figures later.</li>
            <li>Taste is the part the model doesn&rsquo;t bring. Look hard, then say exactly what to change.</li>
          </ul>
        </Step>

        <p className="col-end">
          The reference image belongs to Linear and appears here as a reference only. The figures and the code in Hairline are original.
        </p>
      </main>
      <Footer />
    </>
  );
}
