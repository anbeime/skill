import type { Metadata } from "next";
import type { CSSProperties, ReactNode } from "react";
import { Anchor } from "@/components/anchor";
import { Footer, Topbar } from "@/components/chrome";
import { Command } from "@/components/command";
import { ExampleFrame } from "@/components/example-frame";
import { Rail } from "@/components/rail";
import { NOTICE } from "@/lib/catalogue";
import { COUNT, LINKS } from "@/lib/figures";
import { share } from "@/lib/share";
import { ADOPT, ADOPTED, ADOPT_STEPS, ADOPT_USE, COMMAND, FOLDER, INSTALL, STEPS, SUMMARY, USE, examples, type Shown } from "@/lib/skill";

/** The file the skill writes, set as code where a line names it. USE stays plain text for llms.txt. */
const FILE = "hairline-<name>.html";
const named = (line: string) => {
  const i = line.indexOf(FILE);
  if (i < 0) return line;
  return <>{line.slice(0, i)}<code className="doc-code">{FILE}</code>{line.slice(i + FILE.length)}</>;
};

/** A block's place in the header's entrance. */
const at = (i: number) => ({ "--i": i }) as CSSProperties;

export const metadata: Metadata = share("/skills", "Make your own figure", SUMMARY);

const RAIL = [
  {
    title: "hairline-create",
    icon: "sparkle" as const,
    color: "#8b5cf6",
    items: [
      { id: "install", title: "Install" },
      { id: "use", title: "How to use it" },
      { id: "how", title: "How it works" },
      { id: "examples", title: "What it draws" },
    ],
  },
  {
    title: "hairline-adopt",
    icon: "path" as const,
    color: "#10b981",
    items: [
      { id: "adopt-use", title: "Start from an SVG" },
      { id: "adopt-how", title: "How it reads a drawing" },
      { id: "adopt-examples", title: "What it made" },
    ],
  },
];

/** A section in the column: its title beside a button that copies its link. */
function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="doc-section">
      <div className="doc-head">
        <h2 id={`${id}-title`} className="doc-h2">{title}</h2>
        <Anchor id={id} title={title} />
      </div>
      {children}
    </section>
  );
}

/** One example: the line that asked for it, what its figure means, and the page the skill wrote, in a frame. */
function Example({ e }: { e: Shown }) {
  return (
    <article className="card ex" data-example={e.name} aria-label={e.prompt}>
      <div className="ex-h">
        <Command code={e.prompt} kind="prompt" label={`Copy prompt: ${e.idea}`} />
      </div>
      <div className="ex-b">
        <p className="ex-name">{e.name}</p>
        <p className="ex-means">{e.means}</p>
        {e.followUp && (
          <div className="ex-fu">
            <p className="ex-then">Then asked</p>
            <Command code={e.followUp} kind="follow-up" label={`Copy follow-up: ${e.idea}`} />
          </div>
        )}
      </div>
      <div className="ex-f example-figure">
        <ExampleFrame src={`${e.href}?theme=light`} title={e.means} />
      </div>
    </article>
  );
}

/** The steps a skill takes, as a numbered list. */
function Steps({ steps }: { steps: { title: string; text: string }[] }) {
  return (
    <ol className="howto" data-steps>
      {steps.map((s) => (
        <li key={s.title}><span><b>{s.title}.</b> {s.text}</span></li>
      ))}
    </ol>
  );
}

/**
 * The skills' page, as a catalogue: how to get them and use each, then what each has drawn, on a card with the line
 * that asked for it and the page it wrote, in a frame. A Server Component: it reads each example's name and meaning
 * from that page.
 */
export default function Skills() {
  const drawn = examples();
  const adopted = examples(ADOPTED, ADOPT);
  return (
    <>
      <Topbar />
      <Rail label="Skills" groups={RAIL} />
      <main className="col skill">
        {/* the home's hero sends people here, and the header arrives as the hero does */}
        <header className="hero-rise">
          <p className="col-label" style={at(0)}>Skills</p>
          <h1 className="col-h1" style={at(1)}>Make your own figure</h1>
          <p className="col-lede" style={at(2)}>{SUMMARY}</p>
        </header>

        <Section id="install" title="Install">
          <Command code={INSTALL} kind="install" label="Copy install command" />
          <p className="doc-p">{FOLDER}</p>
        </Section>

        <Section id="use" title="How to use it">
          <Command code={`${COMMAND} <idea>`} kind="usage" label="Copy command" />
          <ul role="list" className="doc-list">
            {USE.map((line) => <li key={line}>{named(line)}</li>)}
          </ul>
        </Section>

        <Section id="how" title="How it works">
          <Steps steps={STEPS} />
        </Section>

        <Section id="examples" title="What it draws">
          <p className="doc-p">Four ideas, four files. Each one opens from disk with no dependencies. Move the pointer over one.</p>
          {drawn.map((e) => <Example key={e.file} e={e} />)}
        </Section>

        <Section id="adopt-use" title="Start from an SVG">
          <Command code={`${ADOPT} <file.svg>`} kind="usage" label="Copy adopt command" />
          <ul role="list" className="doc-list">
            {ADOPT_USE.map((line) => <li key={line}>{named(line)}</li>)}
          </ul>
        </Section>

        <Section id="adopt-how" title="How it reads a drawing">
          <Steps steps={ADOPT_STEPS} />
        </Section>

        <Section id="adopt-examples" title="What it made">
          <p className="doc-p">Five SVGs, five files. The rocket was drawn for the demo; the other four are companies&rsquo; marks. Each page took a few rounds of changes after the first line. Move the pointer over one.</p>
          {adopted.map((e) => <Example key={e.file} e={e} />)}
          <p className="doc-p">{NOTICE}</p>
        </Section>

        <p className="col-end">
          The {COUNT} figures and their options are in <a className="doc-more" href="/docs">the docs</a>. The skills&rsquo; files are on GitHub, in <a className="doc-more" href={`${LINKS.github}/tree/main/skills/hairline-create`}>hairline-create</a> and <a className="doc-more" href={`${LINKS.github}/tree/main/skills/hairline-adopt`}>hairline-adopt</a>.
        </p>
      </main>
      <Footer />
    </>
  );
}
