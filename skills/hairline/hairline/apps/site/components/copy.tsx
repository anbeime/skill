"use client";

import { useCallback, useEffect, useState, type RefObject } from "react";

/**
 * Copies text, and says so for a moment. Without clipboard permission, or on
 * a page served without a secure context where there is no clipboard at all,
 * it selects the text instead, so the keyboard can copy it. Resolves whether
 * the text reached the clipboard.
 */
export function useCopy(): [copied: boolean, copy: (text: string, fallback?: Element | null) => Promise<boolean>] {
  // counted, not flagged, so a copy made while the last one shows restarts its time
  const [copies, setCopies] = useState(0);

  useEffect(() => {
    if (!copies) return;
    const timer = setTimeout(() => setCopies(0), 1600);
    return () => clearTimeout(timer);
  }, [copies]);

  const copy = useCallback(async (text: string, fallback?: Element | null) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopies((n) => n + 1);
      return true;
    } catch {
      if (!fallback) return false;
      const range = document.createRange();
      range.selectNodeContents(fallback);
      const selection = window.getSelection();
      selection?.removeAllRanges();
      selection?.addRange(range);
      return false;
    }
  }, []);

  return [copies > 0, copy];
}

/**
 * Copy as an icon: the clipboard gives way to a check through scale, opacity
 * and blur, and back. Both icons stay in the DOM so the swap is a transition
 * either way, and interrupts cleanly on a second click.
 */
export function CopyIcon({ text, select, label = "Copy", className = "" }: { text: string | (() => string); select?: RefObject<Element | null>; label?: string; className?: string }) {
  const [copied, copy] = useCopy();
  return (
    <button type="button" className={`icopy ${className}`} data-copied={copied || undefined} aria-label={label} title={label} onClick={() => copy(typeof text === "function" ? text() : text, select?.current)}>
      <svg className="icopy-a" viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round">
        <rect x="5.25" y="5.25" width="8.5" height="8.5" rx="2" />
        <path d="M10.75 5.25V4.25a2 2 0 0 0-2-2h-4.5a2 2 0 0 0-2 2v4.5a2 2 0 0 0 2 2h1" />
      </svg>
      <svg className="icopy-b" viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3.5 8.5l3 3 6-7" />
      </svg>
      <span className="sr-only" aria-live="polite">{copied ? "Copied" : ""}</span>
    </button>
  );
}
