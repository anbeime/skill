"use client";

import { useRef } from "react";
import { CopyIcon } from "./copy";

/**
 * A code sample in its frame: a bar with its title and a copy icon, then the
 * code, which is the block's one tab stop so the keyboard can scroll it.
 * Line numbers are drawn in CSS, so they are never selected or copied;
 * `plain` leaves them off.
 */
export function CodeBlock({ title, html, plain = false }: { title: string; html: string; plain?: boolean }) {
  const body = useRef<HTMLDivElement>(null);
  return (
    <div className="code" data-code>
      <div className="code-bar">
        <span className="code-title">{title}</span>
        <CopyIcon text={() => body.current?.textContent ?? ""} select={body} label="Copy code" />
      </div>
      <div ref={body} tabIndex={0} className="code-body" data-plain={plain || undefined} dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}
