const escape = (text) => String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const ICON = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M3 1.5h4l2.5 2.5v6.5h-6.5z"/><path d="M7 1.5V4h2.5"/><path d="M6.25 5.5v3.2M4.9 7.4l1.35 1.35L7.6 7.4"/></svg>';

export const PDF_BUTTON_CSS = `.iso-plate-pdf{position:absolute;top:12px;right:13px;z-index:2;display:inline-flex;align-items:center;gap:5px;padding:4px 7px;border-radius:6px;color:var(--anatomy-muted);font-family:var(--anatomy-mono);font-size:10px;line-height:1;letter-spacing:.08em;text-decoration:none;transition:color .2s var(--anatomy-ease),background-color .2s var(--anatomy-ease)}
.iso-plate-pdf:hover,.iso-plate-pdf:focus-visible{color:var(--anatomy-strong);background:color-mix(in srgb,var(--anatomy-text) 14%,transparent);outline:none}
.iso-plate-pdf svg{width:12px;height:12px;fill:none;stroke:currentColor;stroke-width:1.3;stroke-linecap:round;stroke-linejoin:round}
.iso-plate:has(.iso-plate-pdf) .iso-plate-corner[data-corner="title"]{right:52px}`;

export function pdfButton(href, label = "Open the printable PDF") {
  return `<style>${PDF_BUTTON_CSS}</style><a class="iso-plate-pdf" href="${escape(href)}" target="_blank" rel="noopener" aria-label="${escape(label)}">${ICON}PDF</a>`;
}
