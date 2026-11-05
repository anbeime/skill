import type { Metadata } from "next";
import type { CSSProperties } from "react";
import { Catalogue } from "@/components/catalogue";
import { Footer, Topbar } from "@/components/chrome";
import { SHELVES, spell, tally } from "@/lib/catalogue";
import { FIGURES, LINKS, type FigureId } from "@/lib/figures";
import { highlight } from "@/lib/highlight";
import { share } from "@/lib/share";
import { paste } from "@/lib/snippets";

/** A block's place in the header's entrance. */
const at = (i: number) => ({ "--i": i }) as CSSProperties;

/** How many the skill drew from a mark: the Marks shelf's, counted apart from the package's as tally() does. */
const MARKS = spell(SHELVES.find((s) => s.id === "marks")!.figures.length);

/** The lede in three parts, so the page can link the skill's name and the metadata can keep it as text. */
const LEAD = `${tally()}, grouped by what they draw. They ship in the package, but they are here to show what a figure can be: the`;
const SKILL = "/hairline-create";
const TAIL = `skill draws your own. Pick one to see it large and copy its code. A last shelf holds ${MARKS} the skill drew from a company's mark.`;
const LEDE = `${LEAD} ${SKILL} ${TAIL}`;

export const metadata: Metadata = share("/figures", "Figures", LEDE);

/**
 * /figures: every figure on its shelf. A Server Component, so each drawn figure's code is highlighted at build, three
 * ways, and the catalogue shows it in the drawer.
 */
export default async function Figures() {
  const code = Object.fromEntries(
    await Promise.all(
      FIGURES.map(async (f) => [f.id, await Promise.all(paste(f.name, f.id).map(async (q) => ({ label: q.label, file: q.file, html: await highlight(q.code, q.lang) })))] as const),
    ),
  ) as Record<FigureId, { label: string; file: string; html: string }[]>;

  return (
    <>
      <Topbar />
      <Catalogue
        code={code}
        header={
          <header className="hero-rise">
            <h1 className="col-h1" style={at(0)}>Every figure, by what it <em>draws</em>.</h1>
            <p className="col-lede" style={at(1)}>{LEAD} <a className="doc-more" href="/skills">{SKILL}</a> {TAIL}</p>
          </header>
        }
        end={
          <p className="col-end">
            Missing a figure, a variation, or a whole shelf? <a className="doc-more" href={`${LINKS.github}/issues`}>Ask for it on GitHub</a>. The ones most asked for are drawn first.
          </p>
        }
      />
      <Footer />
    </>
  );
}
