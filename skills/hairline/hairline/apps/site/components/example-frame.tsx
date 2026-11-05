"use client";

import { useEffect, useRef } from "react";

/** The bench's `body` padding, 24px above and 24px below the page's one column: every page the skill writes has it. */
const PAD = 48;

/** Set inside the frame: the plate's two corner tags (the figure's name and its read-out) and the rules line under it. */
const QUIET = "hl-site-quiet";
const HIDDEN = "#name, #read, #rules { display: none !important; }";

/**
 * Hands an Escape pressed inside a frame's document on to the frame element,
 * where it bubbles to the site's document: a key pressed in the frame never
 * reaches it otherwise, so the drawer would not close. Returns its remover.
 */
export function forwardEscape(el: HTMLIFrameElement, doc: Document): () => void {
  const onKey = (event: KeyboardEvent) => {
    if (event.key === "Escape") el.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  };
  doc.addEventListener("keydown", onKey);
  return () => doc.removeEventListener("keydown", onKey);
}

/**
 * A page the skill wrote, in a frame as tall as that page: the frame never
 * scrolls inside. Its height is reserved in CSS before it loads, then fitted
 * to the page's column and kept fitted as the column's text wraps. The pages
 * are served from the site's own origin; were they not, `contentDocument`
 * would be null and the frame would keep its CSS height.
 *
 * Here an example shows only the figure, its controls and what it means: the
 * name tag, the read-out and the rules line are hidden from the site's side,
 * by one style added to the frame's document before it is measured, because
 * the page itself stays exactly as the skill wrote it. Its error line is left
 * alone, so a figure that throws still says so.
 */
export function ExampleFrame({ src, title }: { src: string; title: string }) {
  const frame = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const el = frame.current;
    if (!el) return;
    let watch: ResizeObserver | undefined;
    let unkey: (() => void) | undefined;
    const fit = () => {
      const view = el.contentWindow as (Window & typeof globalThis) | null;
      const doc = el.contentDocument;
      const main = doc?.querySelector("main");
      if (!view || !doc || !main) return;
      // once a document: the style and the Escape go in together
      if (!doc.getElementById(QUIET)) {
        const style = doc.createElement("style");
        style.id = QUIET;
        style.textContent = HIDDEN;
        doc.head.append(style);
        unkey?.();
        unkey = forwardEscape(el, doc);
      }
      const size = () => { el.style.height = `${Math.ceil(main.getBoundingClientRect().height) + PAD}px`; };
      size();
      watch?.disconnect();
      // the frame's own observer: its column is in the frame's document
      watch = new view.ResizeObserver(size);
      watch.observe(main);
    };
    fit();
    el.addEventListener("load", fit);
    return () => {
      el.removeEventListener("load", fit);
      watch?.disconnect();
      unkey?.();
    };
  }, []);

  return <iframe ref={frame} className="example-frame" src={src} title={title} loading="lazy" />;
}
