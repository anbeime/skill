import type { ReactNode } from "react";
import { Basket, Branches, Cabinet, Dish, Drawer, Elevator, Exploded, Format, Hub, Keyboard, Laptop, Lockers, Loupe, Padlock, Patch, Phone, Phosphor, Plot, Plug, Query, Rail, Rebuild, Relay, Riffle, Router, Settle, Sieve, Slow, Stack, Terminal, Terrain, Turntable, Vault } from "@lucasmarkes/hairline/react";
import { Anchor } from "@/components/anchor";
import { CodeBlock } from "@/components/code-block";
import { Install } from "@/components/install";
import { Tabs, type Tab } from "@/components/tabs";
import { SECTIONS } from "@/lib/docs";
import { COUNT, FIGURES, INTENSITY, OPTIONS, THEME, measure } from "@/lib/figures";
import { NO_RESULTS, PACKAGE } from "@/lib/snippets";

const SMALL = { riffle: Riffle, terrain: Terrain, exploded: Exploded, phosphor: Phosphor, slow: Slow, turntable: Turntable, keyboard: Keyboard, elevator: Elevator, phone: Phone, laptop: Laptop, terminal: Terminal, cabinet: Cabinet, branches: Branches, vault: Vault, lockers: Lockers, padlock: Padlock, patch: Patch, dish: Dish, router: Router, loupe: Loupe, sieve: Sieve, rail: Rail, plug: Plug, query: Query, drawer: Drawer, basket: Basket, plot: Plot, hub: Hub, relay: Relay, settle: Settle, format: Format, rebuild: Rebuild, stack: Stack };

/** A section takes its title from SECTIONS, the list the rail reads, so the two always agree. Its link copies from beside its title. */
function Section({ id, children }: { id: string; children: ReactNode }) {
  const { title } = SECTIONS.find((s) => s.id === id)!;
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

const C = ({ children }: { children: ReactNode }) => <code className="doc-code">{children}</code>;

export function GettingStarted({ commands, size, quickstart, empty }: { commands: { label: string; code: string }[]; size: string; quickstart: Tab[]; empty: string }) {
  return (
    <>
      <Section id="install">
        <p className="doc-p">Install the package, then import a figure wherever your interface runs.</p>
        <div className="max-w-[460px]"><Install commands={commands} /></div>
        <p className="doc-note">
          Click the command to switch package manager. ESM only, no dependencies, <span data-size>{size}</span> gzipped for all {COUNT}; a bundle that imports one carries one.
        </p>
      </Section>
      <Section id="quick-start">
        <p className="doc-p">Paste a figure. It fills its parent&rsquo;s width at a 5:4 aspect ratio.</p>
        <Tabs tabs={quickstart} label="Quick start" />
      </Section>
      <Section id="options">
        <p className="doc-p">Every figure takes the same five options, all optional.</p>
        <div className="tbl-card">
          <table className="props" data-options>
            <thead>
              <tr><th>Option</th><th>Type</th><th>Default</th><th>What it does</th></tr>
            </thead>
            <tbody>
              {OPTIONS.map((row) => (
                <tr key={row.name}>
                  <td><code>{row.name}</code></td><td><code>{row.type}</code></td><td><code>{row.default}</code></td><td>{row.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
      <Section id="empty-states">
        <p className="doc-p">A figure works as an empty state at 160 to 240px, above a heading and one action. Its rest pose is the picture; the pointer is a bonus.</p>
        <div className="empty-demo" data-empty>
          <Sieve style={{ width: 200 }} label={NO_RESULTS.label} />
          <h3 className="empty-demo-title">{NO_RESULTS.heading}</h3>
          <button type="button" className="btn press">{NO_RESULTS.action}</button>
        </div>
        <CodeBlock title="no-results.tsx" html={empty} />
      </Section>
    </>
  );
}

export function Api({ code }: { code: { reactSignature: string; react: string; vanillaSignature: string; vanilla: string; cdn: string } }) {
  return (
    <>
      <Section id="react">
        <CodeBlock title="Signature" html={code.reactSignature} plain />
        <p className="doc-p">
          Import any of the {COUNT} from <C>{PACKAGE}/react</C>. Each renders a <C>&lt;div&gt;</C>, takes any <C>&lt;div&gt;</C> attribute and forwards its ref. The entry is a client module, so a Server Component renders it without writing <C>&quot;use client&quot;</C>.
        </p>
        <CodeBlock title="app/page.tsx" html={code.react} />
      </Section>
      <Section id="vanilla">
        <CodeBlock title="Signature" html={code.vanillaSignature} plain />
        <p className="doc-p">
          One function per figure, named in lower case: {FIGURES.map((f, i) => <span key={f.id}>{i ? ", " : ""}<C>{f.id}</C></span>)}. In <C>update</C>, a key set to <C>undefined</C> goes back to its default and a key left out stays as it is. <C>destroy</C> removes the drawing and its listeners.
        </p>
        <CodeBlock title="main.ts" html={code.vanilla} />
      </Section>
      <Section id="cdn">
        <p className="doc-p">Without a bundler, import from esm.sh in a module script.</p>
        <CodeBlock title="index.html" html={code.cdn} />
      </Section>
    </>
  );
}

export function Reference({ css }: { css: string }) {
  return (
    <>
      <Section id="figures">
        <p className="doc-p">Every figure takes <C>intensity</C>, from 0 to 1. Here is what it turns up.</p>
        <ul className="grid gap-[10px]">
          {FIGURES.map((doc) => {
            const Small = SMALL[doc.id];
            return (
              <li key={doc.id} className="figure-row" data-row={doc.id}>
                <div>
                  <h3 className="figure-name">{doc.name}</h3>
                  <p className="figure-text"><b>Higher intensity:</b> {doc.stronger}</p>
                  <p className="figure-text">{doc.summary}</p>
                </div>
                <div className="tile"><Small /></div>
              </li>
            );
          })}
        </ul>
        <div className="table-scroll tbl-card" tabIndex={0} role="region" aria-label="What intensity sets in each figure">
          <table className="intensity" data-intensity>
            <thead>
              <tr><th>Figure</th><th>Parameter</th><th>0</th><th>0.5</th><th>1</th></tr>
            </thead>
            <tbody>
              {FIGURES.map((doc) => (
                <tr key={doc.id}>
                  <td>{doc.name}</td>
                  <td><code>{doc.parameter.name}</code></td>
                  {INTENSITY[doc.id].map((n, i) => <td key={i}><code>{measure(n, doc.parameter.unit)}</code></td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <a className="doc-more" href="/figures">Try each one on the figures page →</a>
      </Section>
      <Section id="theme">
        <p className="doc-p">
          Six custom properties, set on the figure or on any ancestor. Without them a figure is light, or dark when an ancestor has class <C>dark</C> or <C>data-theme=&quot;dark&quot;</C>, or when the page&rsquo;s <C>color-scheme</C> is dark.
        </p>
        <div className="tbl-card">
          <table className="props" data-tokens>
            <thead>
              <tr><th>Property</th><th>Light</th><th>Role</th></tr>
            </thead>
            <tbody>
              {THEME.map((t) => (
                <tr key={t.property}><td><code>{t.property}</code></td><td><code>{t.light}</code></td><td>{t.role}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock title="globals.css" html={css} />
      </Section>
      <Section id="accessibility">
        <ul className="doc-list">
          <li>Each figure is an image with a description; <C>label</C> (or <C>aria-label</C> in React) replaces it.</li>
          <li>Riffle is a focusable group: the arrow keys walk its cards and a live region reads out the card&rsquo;s number.</li>
          <li>Under <C>prefers-reduced-motion</C>, Phosphor and Slow hold still, and every figure still answers the pointer.</li>
        </ul>
      </Section>
    </>
  );
}
