"use client";

import { useEffect, useRef, useState } from "react";
import { CopyIcon } from "./copy";

/**
 * One line to type, in a pill with a copy icon. `kind` says which line it is,
 * for the tests (`prompt` is an example's, `follow-up` the change asked for
 * after it, `usage` the bare command); a shell command takes the `$` in front
 * of it. A prompt is read, so it wraps when it must. The install command is a
 * shell line, so it stays one line: wider than the pill, it scrolls and fades
 * at the edge while more of it is hidden, as the home's install does.
 */
export function Command({ code, kind, label }: { code: string; kind: "install" | "prompt" | "follow-up" | "usage"; label: string }) {
  const line = useRef<HTMLElement>(null);
  const [more, setMore] = useState(false);
  const one = kind === "install";

  useEffect(() => {
    const el = line.current;
    if (!one || !el) return;
    const measure = () => setMore(el.scrollLeft + el.clientWidth < el.scrollWidth - 1);
    measure();
    el.addEventListener("scroll", measure, { passive: true });
    const resize = new ResizeObserver(measure);
    resize.observe(el);
    return () => {
      el.removeEventListener("scroll", measure);
      resize.disconnect();
    };
  }, [one, code]);

  return (
    <div className="pill" data-command={kind}>
      {one && <span aria-hidden="true" className="select-none text-faint">$</span>}
      <code ref={line} className="pill-line" title={code} data-more={more ? "" : undefined}>{code}</code>
      <CopyIcon text={code} select={line} label={label} />
    </div>
  );
}
