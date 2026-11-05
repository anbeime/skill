"use client";

import { useCopy } from "./copy";

/**
 * A heading's link, copied: shown when the pointer is on the heading or the key is on the button. The chain gives way
 * to a check as the copy icon's clipboard does, through scale, opacity and blur.
 */
export function Anchor({ id, title }: { id: string; title: string }) {
  const [copied, copy] = useCopy();
  return (
    <button type="button" className="icopy anchor" data-copied={copied || undefined} aria-label={`Copy link to ${title}`} title="Copy link" onClick={() => copy(`${location.origin}${location.pathname}#${id}`)}>
      <svg className="icopy-a" viewBox="0 0 16 16" width="13" height="13" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M6.75 9.25a2.75 2.75 0 0 0 3.9 0l2-2a2.75 2.75 0 0 0-3.9-3.9l-.6.6" />
        <path d="M9.25 6.75a2.75 2.75 0 0 0-3.9 0l-2 2a2.75 2.75 0 0 0 3.9 3.9l.6-.6" />
      </svg>
      <svg className="icopy-b" viewBox="0 0 16 16" width="13" height="13" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3.5 8.5l3 3 6-7" />
      </svg>
      <span className="sr-only" aria-live="polite">{copied ? "Copied" : ""}</span>
    </button>
  );
}
