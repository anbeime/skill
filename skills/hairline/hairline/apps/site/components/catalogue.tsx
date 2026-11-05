"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { Basket, Branches, Cabinet, Dish, Drawer, Elevator, Exploded, Format, Hub, Keyboard, Laptop, Lockers, Loupe, Padlock, Patch, Phone, Phosphor, Plot, Plug, Query, Rail, Rebuild, Relay, Riffle, Router, Settle, Sieve, Slow, Stack, Terminal, Terrain, Turntable, Vault } from "@lucasmarkes/hairline/react";
import { ENTRIES, NOTICE, SHELVES, type Entry, type Shelf, type ShelfId } from "@/lib/catalogue";
import { LINKS, type FigureId } from "@/lib/figures";
import { Command } from "./command";
import { ExampleFrame } from "./example-frame";
import { MadeFrame } from "./made-frame";
import { Tabs, type Tab } from "./tabs";

const COMPONENTS: Record<FigureId, typeof Riffle> = { riffle: Riffle, terrain: Terrain, exploded: Exploded, phosphor: Phosphor, slow: Slow, turntable: Turntable, keyboard: Keyboard, elevator: Elevator, phone: Phone, laptop: Laptop, terminal: Terminal, cabinet: Cabinet, branches: Branches, vault: Vault, lockers: Lockers, padlock: Padlock, patch: Patch, dish: Dish, router: Router, loupe: Loupe, sieve: Sieve, rail: Rail, plug: Plug, query: Query, drawer: Drawer, basket: Basket, plot: Plot, hub: Hub, relay: Relay, settle: Settle, format: Format, rebuild: Rebuild, stack: Stack };

type Filter = "all" | ShelfId;

const svg = (children: ReactNode) => (
  <svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {children}
  </svg>
);

/** Each shelf's mark, drawn as the docs rail's are: a light fill under a line. */
const ICONS: Record<Filter, ReactNode> = {
  all: svg(
    <>
      <rect x="2" y="2" width="5" height="5" rx="1.5" fill="currentColor" fillOpacity=".2" />
      <rect x="9" y="2" width="5" height="5" rx="1.5" fill="currentColor" fillOpacity=".2" />
      <rect x="2" y="9" width="5" height="5" rx="1.5" fill="currentColor" fillOpacity=".2" />
      <rect x="9" y="9" width="5" height="5" rx="1.5" fill="currentColor" fillOpacity=".2" />
    </>,
  ),
  interfaces: svg(
    <>
      <rect x="1.75" y="2.75" width="12.5" height="10.5" rx="2.5" fill="currentColor" fillOpacity=".2" stroke="none" />
      <path d="M1.75 6h12.5" />
    </>,
  ),
  data: svg(
    <>
      <rect x="2" y="7" width="3" height="6" rx="1" fill="currentColor" fillOpacity=".2" />
      <rect x="6.5" y="3" width="3" height="10" rx="1" fill="currentColor" fillOpacity=".2" />
      <rect x="11" y="5" width="3" height="8" rx="1" fill="currentColor" fillOpacity=".2" />
    </>,
  ),
  machines: svg(
    <>
      <circle cx="8" cy="8" r="4.25" fill="currentColor" fillOpacity=".2" />
      <circle cx="8" cy="8" r="1.25" />
      <path d="M8 1.75v2M8 12.25v2M1.75 8h2M12.25 8h2" />
    </>,
  ),
  devices: svg(
    <>
      <rect x="4.75" y="1.75" width="6.5" height="12.5" rx="1.75" fill="currentColor" fillOpacity=".2" />
      <path d="M7 12h2" />
    </>,
  ),
  coding: svg(
    <>
      <rect x="1.75" y="2.75" width="12.5" height="10.5" rx="2.5" fill="currentColor" fillOpacity=".2" stroke="none" />
      <path d="M6 5c-1 0-1.25.5-1.25 1.25v.5C4.75 7.5 4.5 8 3.75 8c.75 0 1 .5 1 1.25v.5C4.75 10.5 5 11 6 11M10 5c1 0 1.25.5 1.25 1.25v.5c0 .75.25 1.25 1 1.25-.75 0-1 .5-1 1.25v.5c0 .75-.25 1.25-1.25 1.25" />
    </>,
  ),
  security: svg(
    <>
      <path d="M8 1.75 13 3.75v4.5c0 3-2.5 5-5 6-2.5-1-5-3-5-6v-4.5L8 1.75Z" fill="currentColor" fillOpacity=".2" />
      <path d="M6 8l1.5 1.5L10 6.5" />
    </>,
  ),
  connectivity: svg(
    <>
      <circle cx="4" cy="11.5" r="2.25" fill="currentColor" fillOpacity=".2" />
      <circle cx="12" cy="4.5" r="2.25" fill="currentColor" fillOpacity=".2" />
      <path d="m5.6 10 4.8-4.1" />
    </>,
  ),
  empty: svg(
    <>
      <rect x="2.25" y="2.25" width="11.5" height="11.5" rx="3" fill="currentColor" fillOpacity=".2" stroke="none" />
      <rect x="2.25" y="2.25" width="11.5" height="11.5" rx="3" strokeDasharray="2 2.4" />
    </>,
  ),
  marks: svg(
    <>
      <path d="M8 2.5 13.5 12h-11L8 2.5Z" fill="currentColor" fillOpacity=".2" />
      <circle cx="12.25" cy="4.25" r="1.5" />
    </>,
  ),
};

/** The rows of the filter: All, then each shelf, each in its colour with how many figures it holds. */
const ROWS: { id: Filter; title: string; color: string; n: number }[] = [
  { id: "all", title: "All", color: "#0a0a0a", n: ENTRIES.length },
  ...SHELVES.map((s) => ({ id: s.id, title: s.title, color: s.color, n: s.figures.length })),
];

const SHELF_OF = new Map(SHELVES.flatMap((s) => s.figures.map((f) => [f.id, s] as const)));

const tint = (color: string) => ({ "--gc": color }) as CSSProperties;

/** The filter a hash names, a bare #shelf, or All. */
const fromHash = (hash: string): Filter => {
  const id = hash.slice(1);
  return SHELVES.some((s) => s.id === id) ? (id as ShelfId) : "all";
};

/** What stands in a planned figure's place: its plinth in outline, a figure not drawn yet. */
function Ghost() {
  return (
    <svg className="fig-ghost" viewBox="0 0 400 320" aria-hidden="true">
      <path className="fig-ghost-dash" d="M200 92 342 163 200 234 58 163Z" />
      <path className="fig-ghost-plate" d="M200 128 258 157 200 186 142 157Z" />
      <path d="M142 157v22l58 29v-22M258 157v22l-58 29" />
      <path className="fig-ghost-dash" d="M200 92v-22M342 163h22M58 163H36" />
    </svg>
  );
}

/**
 * The figures on their shelves. The shelves are a filter: All, the default, shows every shelf, and a shelf shows only
 * itself. The choice is kept in the address as a bare #shelf, which names no element, so a link opens on it without
 * the browser scrolling. From 1100px the filter is a list by the column's left edge, its marks on the line the name in
 * the top bar starts on, and a plate slides to the pressed row; below that it is a strip under the top bar.
 *
 * A tile shows its figure live. Picking one opens a drawer with the figure large, an intensity slider, what the figure
 * reads, and its code three ways, highlighted on the server. A planned figure has its outline instead, and a link to
 * ask for it. A figure the skill made shows its page's stage, and its drawer the page with its own controls and the
 * prompt that drew it. The header and the closing note come from the server, around the shelves.
 */
export function Catalogue({ code, header, end }: { code: Record<FigureId, Tab[]>; header: ReactNode; end: ReactNode }) {
  const [filter, setFilterState] = useState<Filter>("all");
  const [entered, setEntered] = useState(false);
  const [open, setOpen] = useState(false);
  const [entry, setEntry] = useState<Entry | null>(null);
  const [intensity, setIntensity] = useState(0.5);
  const [reads, setReads] = useState("");
  const [edges, setEdges] = useState({ start: false, end: false });
  const list = useRef<HTMLDivElement>(null);
  const plate = useRef<HTMLSpanElement>(null);
  const strip = useRef<HTMLDivElement>(null);
  const head = useRef<HTMLDivElement>(null);
  const close = useRef<HTMLButtonElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const keyed = useRef(false);

  // the hash is read after mount, so the server's All and the first render agree
  useEffect(() => {
    const read = () => setFilterState(fromHash(window.location.hash));
    read();
    window.addEventListener("hashchange", read);
    return () => window.removeEventListener("hashchange", read);
  }, []);

  // the plate moves before paint, so it is never drawn under a row no longer pressed; the first time it lands in place
  useLayoutEffect(() => {
    const el = list.current;
    const place = () => {
      const row = el?.querySelector<HTMLElement>(`[data-filter="${filter}"]`);
      if (!el || !row || !plate.current) return;
      plate.current.style.transform = `translateY(${row.offsetTop}px)`;
      el.setAttribute("data-on", "");
    };
    place();
    if (el && !el.hasAttribute("data-live")) requestAnimationFrame(() => requestAnimationFrame(() => el.setAttribute("data-live", "")));
    window.addEventListener("resize", place);
    return () => window.removeEventListener("resize", place);
  }, [filter]);

  // brings the pressed pill into the strip by scrolling the strip alone
  useEffect(() => {
    const el = strip.current;
    const pill = el?.querySelector<HTMLElement>(`[data-filter="${filter}"]`);
    if (!el || !pill || !el.clientWidth) return;
    const pad = 24;
    const box = el.getBoundingClientRect();
    const at = pill.getBoundingClientRect();
    if (at.left - pad < box.left) el.scrollTo({ left: el.scrollLeft + at.left - pad - box.left });
    else if (at.right + pad > box.right) el.scrollTo({ left: el.scrollLeft + at.right + pad - box.right });
  }, [filter]);

  useEffect(() => {
    const el = strip.current;
    if (!el) return;
    const measure = () => setEdges({ start: el.scrollLeft > 1, end: el.scrollLeft + el.clientWidth < el.scrollWidth - 1 });
    measure();
    el.addEventListener("scroll", measure, { passive: true });
    const resize = new ResizeObserver(measure);
    resize.observe(el);
    return () => {
      el.removeEventListener("scroll", measure);
      resize.disconnect();
    };
  }, []);

  const setFilter = (id: Filter) => {
    if (id === filter) return;
    setFilterState(id);
    setEntered(true);
    try {
      history.replaceState(null, "", id === "all" ? location.pathname + location.search : `#${id}`);
    } catch {}
    // a pick made far down the page brings the shelves' top into view
    if (head.current && head.current.getBoundingClientRect().bottom < 0) {
      window.scrollTo({ top: 0, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }
  };

  const pick = (f: Entry, from: HTMLElement | null, keyboard: boolean) => {
    opener.current = from;
    keyed.current = keyboard;
    if (entry?.id !== f.id) {
      setIntensity(0.5);
      setReads("");
    }
    setEntry(f);
    setOpen(true);
  };

  // focus returns to the tile's button, and its ring shows only when the keyboard closed the drawer: a script's focus
  // would otherwise draw it after a click on the ×; Escape counts as the keyboard only once it has been steering
  const shut = useCallback((keyboard: boolean) => {
    setOpen(false);
    const back = opener.current;
    if (back?.isConnected) back.focus({ preventScroll: true, focusVisible: keyboard } as FocusOptions);
  }, []);

  useEffect(() => {
    if (!open) return;
    // the × takes focus, with its ring only when the keyboard opened the drawer, as `shut` does on the way back
    close.current?.focus({ preventScroll: true, focusVisible: keyed.current } as FocusOptions);
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Tab") keyed.current = true;
      if (event.key === "Escape") shut(keyed.current);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, entry, shut]);

  const shown = filter === "all" ? SHELVES : SHELVES.filter((s) => s.id === filter);

  return (
    <>
      <nav aria-label="Shelves" className="doc-strip">
        <div ref={strip} className="doc-strip-scroll figs-strip" data-start={edges.start || undefined} data-end={edges.end || undefined}>
          <ul>
            {ROWS.map((r) => (
              <li key={r.id}>
                <button type="button" className="doc-link figs-pill" data-filter={r.id} aria-pressed={filter === r.id} style={tint(r.color)} onClick={() => setFilter(r.id)}>
                  {ICONS[r.id]}
                  {r.title}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </nav>
      <main className="figs">
        <aside className="shelves">
          <div ref={list} role="group" aria-label="Shelves" className="shelf-list">
            <span ref={plate} className="shelf-plate" aria-hidden="true" />
            {ROWS.map((r) => (
              <button key={r.id} type="button" className="shelf" data-filter={r.id} aria-pressed={filter === r.id} style={tint(r.color)} onClick={() => setFilter(r.id)}>
                {ICONS[r.id]}
                <span>{r.title}</span>
                <span className="shelf-n">{r.n}</span>
              </button>
            ))}
          </div>
        </aside>
        <div className="figs-main">
          <div ref={head}>{header}</div>
          <div key={filter} className="figs-body" data-enter={entered ? "" : undefined}>
            {shown.map((s) => (
              <ShelfSection key={s.id} shelf={s} picked={open ? entry?.id : undefined} onPick={pick} />
            ))}
          </div>
          {/* wrapped, as the header is: an element from the server among this list's siblings warns for a key in dev */}
          <div>{end}</div>
        </div>
      </main>
      <aside
        id="figure-drawer"
        className="drawer"
        aria-labelledby={entry ? "figure-drawer-name" : undefined}
        inert={!open}
        data-open={open ? "" : undefined}
        onTransitionEnd={(event) => {
          if (event.target === event.currentTarget && event.propertyName === "visibility" && !open) setEntry(null);
        }}
      >
        {entry ? <Detail key={entry.id} entry={entry} code={entry.drawn ? code[entry.id] : undefined} intensity={intensity} setIntensity={setIntensity} reads={reads} setReads={setReads} closeRef={close} onClose={shut} /> : null}
      </aside>
    </>
  );
}

function ShelfSection({ shelf, picked, onPick }: { shelf: Shelf; picked?: string; onPick: (f: Entry, from: HTMLElement | null, keyboard: boolean) => void }) {
  const drawn = shelf.figures.filter((f) => f.drawn).length;
  return (
    <section id={`shelf-${shelf.id}`} className="doc-section" style={tint(shelf.color)} aria-labelledby={`shelf-${shelf.id}-h`}>
      <div className="doc-head figs-head">
        <h2 id={`shelf-${shelf.id}-h`} className="doc-h2">{shelf.title}</h2>
        <span className="figs-count">
          {shelf.id === "marks" ? "made with the skill" : <>{drawn} of {shelf.figures.length}<span className="sr-only"> drawn</span></>}
        </span>
      </div>
      <div className="fig-grid">
        {shelf.figures.map((f) => (
          <Tile key={f.id} entry={f} picked={picked === f.id} onPick={onPick} />
        ))}
      </div>
      {shelf.id === "marks" ? <p className="doc-p figs-notice">{NOTICE}</p> : null}
    </section>
  );
}

/**
 * One figure on its shelf. The whole tile takes a click, but the button is its name: the figure in the stage answers
 * the pointer and the keyboard itself, and Riffle's cards cannot sit inside a button. A click inside a made figure's
 * frame stays in the frame, so that tile opens from its name. Every tile plays its figure until a hand arrives.
 */
function Tile({ entry, picked, onPick }: { entry: Entry; picked: boolean; onPick: (f: Entry, from: HTMLElement | null, keyboard: boolean) => void }) {
  const button = useRef<HTMLButtonElement>(null);
  const Figure = entry.drawn ? COMPONENTS[entry.id] : null;
  const made = entry.drawn ? undefined : entry.made;
  return (
    <div className="fig-tile" data-planned={entry.drawn || made ? undefined : ""} data-picked={picked ? "" : undefined} onClick={(event) => onPick(entry, button.current, event.detail === 0)}>
      <div className="fig-stage">{Figure ? <Figure play /> : made ? <MadeFrame src={`/skill/${made.file}?theme=light&play=1`} title={entry.summary} /> : <Ghost />}</div>
      <div className="fig-foot">
        <button ref={button} type="button" className="fig-name" aria-label={entry.drawn || made ? undefined : `${entry.name}, planned`} aria-expanded={picked} aria-controls="figure-drawer" onClick={(event) => {
          event.stopPropagation();
          onPick(entry, button.current, event.detail === 0);
        }}>
          {entry.name}
        </button>
      </div>
    </div>
  );
}

function Detail({
  entry, code, intensity, setIntensity, reads, setReads, closeRef, onClose,
}: {
  entry: Entry; code?: Tab[]; intensity: number; setIntensity: (n: number) => void; reads: string; setReads: (s: string) => void;
  closeRef: React.RefObject<HTMLButtonElement | null>; onClose: (keyboard: boolean) => void;
}) {
  const shelf = SHELF_OF.get(entry.id)!;
  const Figure = entry.drawn ? COMPONENTS[entry.id] : null;
  const made = entry.drawn ? undefined : entry.made;
  return (
    <div className="detail">
      <div className="detail-h">
        <div>
          <h2 id="figure-drawer-name" className="detail-name">{entry.name}</h2>
          <p className="detail-meta">
            <span className="detail-shelf" style={tint(shelf.color)}>{ICONS[shelf.id]}{shelf.title}</span>
            {entry.drawn || made ? null : <span className="detail-tag">planned</span>}
          </p>
        </div>
        <button ref={closeRef} type="button" className="detail-close" aria-label="Close" onClick={(event) => onClose(event.detail === 0)}>
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden="true">
            <path d="m4 4 8 8M12 4l-8 8" />
          </svg>
        </button>
      </div>
      {/* a made page brings its own plate and controls, so it sits outside the stage's box */}
      {made ? (
        <div className="detail-page"><ExampleFrame src={`/skill/${made.file}?theme=light`} title={entry.summary} /></div>
      ) : (
        <div className="fig-stage detail-stage">{Figure ? <Figure intensity={intensity} onRead={setReads} /> : <Ghost />}</div>
      )}
      <p className="detail-sum">
        {entry.summary} <b>Higher intensity:</b> {entry.stronger}
      </p>
      {made ? (
        <div className="detail-made">
          <Command code={made.prompt} kind="prompt" label={`Copy prompt: ${entry.name}`} />
          <p className="doc-p">Made with <a className="doc-more" href="/skills">hairline-create</a>. It is not in the package: the page is one file, and the prompt above draws it again.</p>
          <p className="doc-p figs-notice">{NOTICE}</p>
        </div>
      ) : Figure ? (
        <>
          <label className="slider">
            <span>intensity</span>
            <input type="range" min="0" max="1" step="0.01" value={intensity} onChange={(event) => setIntensity(Number(event.target.value))} />
            <span className="tabular-nums" aria-hidden="true">{intensity.toFixed(2)}</span>
          </label>
          <p className="detail-reads">
            reads <b aria-live="polite">{reads}</b>
          </p>
          {code ? <Tabs tabs={code} label={`${entry.name} code`} /> : null}
        </>
      ) : (
        <div className="detail-ask">
          <p><b>Not drawn yet.</b> This one is on the list. Ask for it, or for a variation, and it moves up.</p>
          <a className="doc-more" href={`${LINKS.github}/issues/new?title=${encodeURIComponent(`Figure: ${entry.name}`)}`}>Request on GitHub</a>
        </div>
      )}
    </div>
  );
}
