"use client";

import { useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";

export type RailIcon = "bolt" | "braces" | "stack" | "book" | "sparkle" | "path";
export type RailGroup = { title: string; icon: RailIcon; color: string; items: { id: string; title: string }[] };

const svg = (children: ReactNode) => (
  <svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {children}
  </svg>
);

/** A group's mark, drawn in the group's colour: a light fill under a line, as the page's other icons are drawn. */
const ICONS: Record<RailIcon, ReactNode> = {
  bolt: svg(<path d="M9 1.75 3.5 9h4L7 14.25 12.5 7h-4L9 1.75Z" fill="currentColor" fillOpacity=".2" />),
  braces: svg(
    <>
      <rect x="1.75" y="2.75" width="12.5" height="10.5" rx="2.5" fill="currentColor" fillOpacity=".2" stroke="none" />
      <path d="M6 5c-1 0-1.25.5-1.25 1.25v.5C4.75 7.5 4.5 8 3.75 8c.75 0 1 .5 1 1.25v.5C4.75 10.5 5 11 6 11M10 5c1 0 1.25.5 1.25 1.25v.5c0 .75.25 1.25 1 1.25-.75 0-1 .5-1 1.25v.5c0 .75-.25 1.25-1.25 1.25" />
    </>,
  ),
  stack: svg(
    <>
      <path d="m8 2 6 3-6 3-6-3 6-3Z" fill="currentColor" fillOpacity=".2" />
      <path d="m2 8 6 3 6-3M2 11l6 3 6-3" />
    </>,
  ),
  book: svg(
    <>
      <path d="M2.5 3.25A1.5 1.5 0 0 1 4 1.75h9.5v10H4a1.5 1.5 0 0 0-1.5 1.5v-10Z" fill="currentColor" fillOpacity=".16" />
      <path d="M2.5 13.25a1.5 1.5 0 0 0 1.5 1.5h9.5v-3" />
    </>,
  ),
  sparkle: svg(
    <>
      <path d="M8 1.75c.4 3.1 1.9 4.6 5 5-3.1.4-4.6 1.9-5 5-.4-3.1-1.9-4.6-5-5 3.1-.4 4.6-1.9 5-5Z" fill="currentColor" fillOpacity=".2" />
      <path d="M12.75 11.25v2.5M11.5 12.5H14" />
    </>,
  ),
  path: svg(
    <>
      <path d="M3 13c.5-5 3.5-9.5 10-10" />
      <rect x="1.75" y="11.75" width="2.5" height="2.5" rx=".6" fill="currentColor" fillOpacity=".2" />
      <rect x="11.75" y="1.75" width="2.5" height="2.5" rx=".6" fill="currentColor" fillOpacity=".2" />
    </>,
  ),
};

/**
 * The section in view: the first one, in page order, inside a band from under the sticky chrome (a section's
 * scroll-margin-top, read each time, as it differs on a phone) to 30% down the viewport. Null in a gap between two
 * sections, where the mark stays put.
 */
function inView(sections: HTMLElement[]): string | null {
  const first = sections[0].id;
  const last = sections[sections.length - 1].id;
  const top = parseFloat(getComputedStyle(sections[0]).scrollMarginTop) || 0;
  const bottom = window.innerHeight * 0.3;
  if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) {
    // the last section is too short to reach the band, so the end of the page marks it; unless the reader asked for
    // a section the page could only bring into view, on a screen taller than what is left below it
    const asked = sections.find((s) => `#${s.id}` === window.location.hash);
    const at = asked?.getBoundingClientRect();
    return asked && at && at.top >= 0 && at.top < window.innerHeight ? asked.id : last;
  }
  const hit = sections.find((s) => {
    const at = s.getBoundingClientRect();
    // a pixel of slack: the section scrolled to sits flush under the chrome, and the one before can end a fraction below
    return at.bottom > top + 1 && at.top < bottom;
  });
  if (hit) return hit.id;
  // above the first section nothing is in the band, so the first is marked, as at the top
  return sections[0].getBoundingClientRect().top >= bottom ? first : null;
}

/**
 * Puts the strip's dot by the marked link's text, on its centre line. The first time, the dot appears in place; after
 * that it flies there.
 */
function place(list: HTMLElement | null, active: string) {
  const dot = list?.querySelector<HTMLElement>(".doc-dot");
  const link = list?.querySelector<HTMLElement>(`a[href="#${active}"]`);
  if (!list || !dot || !link || !list.clientWidth) return;
  const box = list.getBoundingClientRect();
  const at = link.getBoundingClientRect();
  const x = at.left - box.left + list.scrollLeft + parseFloat(getComputedStyle(link).paddingLeft);
  const y = at.top - box.top + list.scrollTop + (at.height - dot.offsetHeight) / 2;
  dot.style.translate = `${x}px ${y}px`;
  live(list);
}

/**
 * Draws the rail's line to the marked link: each group's trunk reaches down to where the marked row's arm starts to
 * bend (6px over its centre) and a pixel into it, so the two meet with no seam, or back up to nothing in the other
 * groups. The row's arm and tip take it from there, in CSS. Measured in fractions of a pixel, as the arm is placed.
 */
function reach(nav: HTMLElement | null, active: string) {
  if (!nav?.clientWidth) return;
  for (const list of nav.querySelectorAll<HTMLElement>("ul")) {
    const row = list.querySelector(`a[href="#${active}"]`)?.parentElement;
    let f = 0;
    if (row) {
      const box = list.getBoundingClientRect();
      const at = row.getBoundingClientRect();
      // the trunk runs from 2px over the list to its foot
      f = (at.top - box.top + at.height / 2 - 6 + 1 + 2) / (box.height + 2);
    }
    list.style.setProperty("--reach", String(f));
  }
  live(nav);
}

/** Transitions start once the first mark has been drawn, so the page opens with it in place. */
function live(el: HTMLElement) {
  if (!el.hasAttribute("data-live")) requestAnimationFrame(() => requestAnimationFrame(() => el.setAttribute("data-live", "")));
}

/**
 * A page's anchors, in the craft of a rail: fixed at the column's left edge from 1100px, each group's links hung off
 * its mark on a hairline; one sideways strip under the top bar below it. All are plain links, so they work without
 * JavaScript. The script marks the section in view, and nothing is marked until it runs: in the rail the line to it
 * is drawn in its group's colour and only its group stays lit; in the strip a dot flies to it.
 * A link picked by hand marks its section at once, and the mark holds while the page glides there.
 */
export function Rail({ label, groups }: { label: string; groups: RailGroup[] }) {
  const [active, setActive] = useState<string | null>(null);
  const [edges, setEdges] = useState({ start: false, end: false });
  const column = useRef<HTMLElement>(null);
  const strip = useRef<HTMLDivElement>(null);
  const held = useRef(0);
  const items = groups.flatMap((g) => g.items);
  const ids = items.map((s) => s.id).join(" ");

  useEffect(() => {
    const sections = ids.split(" ").map((id) => document.getElementById(id)).filter((el): el is HTMLElement => el !== null);
    if (!sections.length) return;
    let timer = 0;
    const pick = () => {
      if (performance.now() < held.current) return;
      const id = inView(sections);
      if (id) setActive(id);
    };
    const release = () => {
      held.current = 0;
      pick();
    };
    // a long glide outlasts the first second: while the page still moves, the mark stays held
    const scrolled = () => {
      if (held.current) {
        held.current = Math.max(held.current, performance.now() + 200);
        clearTimeout(timer);
        timer = window.setTimeout(release, held.current - performance.now());
        return;
      }
      pick();
    };
    const hold = (event: MouseEvent) => {
      const a = (event.target as Element | null)?.closest<HTMLAnchorElement>("a[href^='#']");
      const id = a?.hash.slice(1);
      if (!id || !sections.some((s) => s.id === id)) return;
      setActive(id);
      held.current = performance.now() + 1000;
      clearTimeout(timer);
      timer = window.setTimeout(release, 1000);
    };
    pick();
    window.addEventListener("scroll", scrolled, { passive: true });
    window.addEventListener("scrollend", release);
    window.addEventListener("resize", pick);
    document.addEventListener("click", hold);
    // the browser has already scrolled to a deep link's section, at once; the reader's own clicks from here on glide
    document.documentElement.dataset.smooth = "";
    return () => {
      clearTimeout(timer);
      window.removeEventListener("scroll", scrolled);
      window.removeEventListener("scrollend", release);
      window.removeEventListener("resize", pick);
      document.removeEventListener("click", hold);
      delete document.documentElement.dataset.smooth;
    };
  }, [ids]);

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

  // before paint, so the mark is never drawn by a link that is no longer marked
  useLayoutEffect(() => {
    if (!active) return;
    reach(column.current, active);
    place(strip.current, active);
    // a list that was hidden shows, or the window changes width: the line and the dot keep to their link
    const resize = new ResizeObserver(() => {
      reach(column.current, active);
      place(strip.current, active);
    });
    for (const el of [column.current, strip.current]) if (el) resize.observe(el);
    return () => resize.disconnect();
  }, [active]);

  // Brings the marked item into the strip by scrolling the strip alone. scrollIntoView would also scroll the
  // page, and would cut short the smooth scroll a click on the strip has just started.
  useEffect(() => {
    const el = strip.current;
    const item = el?.querySelector<HTMLElement>(`a[href="#${active}"]`);
    if (!el || !item || !el.clientWidth) return;
    const pad = 24;
    const box = el.getBoundingClientRect();
    const at = item.getBoundingClientRect();
    if (at.left - pad < box.left) el.scrollTo({ left: el.scrollLeft + at.left - pad - box.left });
    else if (at.right + pad > box.right) el.scrollTo({ left: el.scrollLeft + at.right + pad - box.right });
  }, [active]);

  const link = (id: string, title: string) => (
    <li key={id}>
      <a href={`#${id}`} className="doc-link" aria-current={id === active ? "location" : undefined}>
        <span>{title}</span>
      </a>
    </li>
  );
  const dot = active && <span className="doc-dot" aria-hidden />;
  const tint = (color: string) => ({ "--gc": color }) as CSSProperties;

  return (
    <>
      <aside className="rail fade-mask-y">
        <nav ref={column} aria-label={label} className="doc-sidebar">
          {groups.map((group) => (
            <div key={group.title} className="rail-group" style={tint(group.color)}>
              <p className="rail-title">{ICONS[group.icon]}{group.title}</p>
              <ul>{group.items.map((s) => link(s.id, s.title))}</ul>
            </div>
          ))}
        </nav>
      </aside>
      <nav aria-label={label} className="doc-strip">
        <div ref={strip} className="doc-strip-scroll" data-start={edges.start || undefined} data-end={edges.end || undefined}>
          <ul>{items.map((s) => link(s.id, s.title))}</ul>
          {dot}
        </div>
      </nav>
    </>
  );
}
