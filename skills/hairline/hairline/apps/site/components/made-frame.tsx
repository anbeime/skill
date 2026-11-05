"use client";

import { useEffect, useRef } from "react";
import { forwardEscape } from "./example-frame";

const QUIET = "hl-site-stage";
/** Everything of the skill's page but its stage, hidden from the site's side: the page itself stays as the skill wrote it. */
const ONLY_STAGE = "#name, #read, #rules, #means, .controls { display: none !important; } html, body { background: transparent !important; } body { padding: 0 !important; min-height: 0 !important; } main { max-width: none !important; } .plate { border: 0 !important; border-radius: 0 !important; }";

/**
 * A figure the skill made, as a tile shows it: the stage of its page and
 * nothing else. The frame has the figures' own 5:4 box from CSS, so a page
 * that is slow, missing or broken leaves the tile its shape. The page's ground
 * goes clear, so the tile's ring, drawn under the frame, still shows.
 *
 * The style can only go in once the page has loaded, and the page paints
 * before that, controls and all: so the frame stays clear until its page has
 * the style (`data-quiet`), and only the stage is ever seen.
 */
export function MadeFrame({ src, title }: { src: string; title: string }) {
  const frame = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const el = frame.current;
    if (!el) return;
    let unkey: (() => void) | undefined;
    // once a document: the style and the Escape go in together
    const quiet = () => {
      const doc = el.contentDocument;
      if (!doc?.head || doc.getElementById(QUIET)) return;
      const style = doc.createElement("style");
      style.id = QUIET;
      style.textContent = ONLY_STAGE;
      doc.head.append(style);
      // the blank document a frame starts with is not the page
      if (doc.URL !== "about:blank") el.dataset.quiet = "";
      unkey?.();
      unkey = forwardEscape(el, doc);
    };
    quiet();
    el.addEventListener("load", quiet);
    return () => {
      el.removeEventListener("load", quiet);
      unkey?.();
    };
  }, []);

  return <iframe ref={frame} className="made-frame" src={src} title={title} loading="lazy" />;
}
