import pkg from "@lucasmarkes/hairline/package.json";
import { LINKS } from "@/lib/figures";

export function GitHub() {
  return (
    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" fill="currentColor">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}

/** The bar on every page: the name home with the version beside it, then the figures, the skills, the docs, the story, GitHub. */
export function Topbar() {
  return (
    <header className="topbar">
      <div className="flex items-baseline gap-2">
        <a href="/" className="topbar-name text-[15px] font-medium tracking-[-0.02em]">hairline</a>
        <span className="topbar-version" data-version>v{pkg.version}</span>
      </div>
      <nav className="flex items-center">
        <a className="topbar-link" href="/figures">Figures</a>
        <a className="topbar-link" href="/skills">Skills</a>
        <a className="topbar-link" href="/docs">Docs</a>
        <a className="topbar-link" href="/inspo">Inspo</a>
        <a className="topbar-link" href={LINKS.github} aria-label="GitHub"><GitHub /></a>
      </nav>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="mx-auto flex max-w-[1080px] flex-wrap items-baseline gap-x-6 gap-y-6 border-t border-line px-[clamp(18px,5vw,28px)] py-8 text-[13px] text-muted">
      <p>
        MIT licensed. Built by <a className="text-ink" href={LINKS.author}>Lucas Marques</a>.
      </p>
      <nav className="flex gap-5 md:ml-auto">
        <a className="text-ink" href={LINKS.x}>X</a>
        <a className="text-ink" href={LINKS.github}>GitHub</a>
        <a className="text-ink" href={LINKS.npm}>npm</a>
        <a className="text-ink" href="/llms.txt">llms.txt</a>
      </nav>
    </footer>
  );
}
