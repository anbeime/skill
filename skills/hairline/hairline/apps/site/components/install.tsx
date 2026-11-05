"use client";

import { useEffect, useRef, useState } from "react";
import { CopyIcon } from "./copy";

/**
 * The install command in a pill. The command's first word is a button that
 * moves to the next package manager; the copy icon copies the whole line.
 * A line wider than the pill scrolls, fades at the edge while more of it is
 * hidden, and shows itself whole on hover.
 */
export function Install({ commands }: { commands: { label: string; code: string }[] }) {
  const [at, setAt] = useState(0);
  const line = useRef<HTMLElement>(null);
  const { label, code } = commands[at];
  const head = code.slice(0, code.indexOf(" "));
  const next = commands[(at + 1) % commands.length].label;
  const [more, setMore] = useState(false);

  useEffect(() => {
    const el = line.current;
    if (!el) return;
    const measure = () => setMore(el.scrollLeft + el.clientWidth < el.scrollWidth - 1);
    measure();
    el.addEventListener("scroll", measure, { passive: true });
    const resize = new ResizeObserver(measure);
    resize.observe(el);
    return () => {
      el.removeEventListener("scroll", measure);
      resize.disconnect();
    };
  }, [code]);

  return (
    <div className="pill" data-install={label}>
      <span aria-hidden="true" className="select-none text-faint">$</span>
      <code ref={line} className="pill-line" title={code} data-more={more ? "" : undefined}>
        <button type="button" className="pill-manager" onClick={() => setAt((at + 1) % commands.length)} aria-label={`${head} (${label}): switch to ${next}`} title={`Switch to ${next}`}>
          {head}
        </button>
        {code.slice(head.length)}
      </code>
      <CopyIcon text={code} select={line} label="Copy install command" />
    </div>
  );
}
