"use client";

import { useEffect, useId, useLayoutEffect, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import { CopyIcon } from "./copy";

export type Tab = { label: string; file: string; html: string };

/** Where the reader's tab is kept between visits. */
const KEY = "hairline:docs-tab";

/**
 * Code under tabs, in the same frame as CodeBlock: the tabs on the left, the
 * shown tab's file name and the copy icon on the right. The server renders
 * the first tab; the stored one is read after mount, and storage that throws
 * (private mode, blocked) leaves the first tab on.
 *
 * The selected tab's plate slides to a tab picked with a pointer. It spans the row and a clip-path cuts it down to the tab, so it never
 * animates its size. It is turned on after the first paint, and a tab picked
 * with the arrow keys lands at once.
 */
export function Tabs({ tabs, label }: { tabs: Tab[]; label: string }) {
  const [at, setAt] = useState(0);
  const panel = useRef<HTMLDivElement>(null);
  const list = useRef<HTMLDivElement>(null);
  const id = useId();
  const [box, setBox] = useState<{ x: number; y: number; w: number; h: number; rowW: number; rowH: number } | null>(null);
  const [ready, setReady] = useState(false);
  const [keyed, setKeyed] = useState(false);

  useEffect(() => {
    try {
      const stored = tabs.findIndex((tab) => tab.label === localStorage.getItem(KEY));
      if (stored > 0) setAt(stored);
    } catch {}
  }, [tabs]);

  useLayoutEffect(() => {
    const root = list.current;
    if (!root) return;
    const measure = () => {
      const el = root.querySelector<HTMLElement>('[aria-selected="true"]');
      const last = root.querySelector<HTMLElement>("[role=tab]:last-of-type");
      if (el && last) setBox({ x: el.offsetLeft, y: el.offsetTop, w: el.offsetWidth, h: el.offsetHeight, rowW: last.offsetLeft + last.offsetWidth, rowH: last.offsetTop + last.offsetHeight });
    };
    measure();
    const resize = new ResizeObserver(measure);
    resize.observe(root);
    return () => resize.disconnect();
  }, [at]);

  useEffect(() => {
    let inner = 0;
    const outer = requestAnimationFrame(() => (inner = requestAnimationFrame(() => setReady(true))));
    return () => {
      cancelAnimationFrame(outer);
      cancelAnimationFrame(inner);
    };
  }, []);

  const pick = (i: number) => {
    setAt(i);
    try {
      localStorage.setItem(KEY, tabs[i].label);
    } catch {}
  };

  const onKeyDown = (event: KeyboardEvent) => {
    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    event.preventDefault();
    setKeyed(true);
    const next = (at + step + tabs.length) % tabs.length;
    pick(next);
    list.current?.querySelectorAll<HTMLButtonElement>("[role=tab]")[next]?.focus();
  };

  return (
    <div className="code" data-code>
      <div className="code-bar">
        <div ref={list} role="tablist" aria-label={label} onKeyDown={onKeyDown} onPointerDown={() => setKeyed(false)} className="code-tabs slide" data-hl={box ? "" : undefined} data-ready={ready || undefined} data-keyed={keyed || undefined}>
          {/* a pixel larger than the row on every side, for the ring around the plate */}
          {box ? <span className="slide-hl" aria-hidden="true" style={{ width: box.rowW + 2, height: box.rowH + 2, "--t": `${box.y}px`, "--r": `${box.rowW - box.x - box.w}px`, "--b": `${box.rowH - box.y - box.h}px`, "--l": `${box.x}px` } as CSSProperties} /> : null}
          {tabs.map((tab, i) => (
            <button key={tab.label} type="button" role="tab" id={`${id}-tab-${i}`} aria-selected={i === at} aria-controls={`${id}-panel`} tabIndex={i === at ? 0 : -1} onClick={() => pick(i)} className="code-tab">
              {tab.label}
            </button>
          ))}
        </div>
        <span className="code-title" title={tabs[at].file}>{tabs[at].file}</span>
        <CopyIcon text={() => panel.current?.textContent ?? ""} select={panel} label="Copy code" />
      </div>
      <div ref={panel} role="tabpanel" id={`${id}-panel`} aria-labelledby={`${id}-tab-${at}`} tabIndex={0} className="code-body" dangerouslySetInnerHTML={{ __html: tabs[at].html }} />
    </div>
  );
}
