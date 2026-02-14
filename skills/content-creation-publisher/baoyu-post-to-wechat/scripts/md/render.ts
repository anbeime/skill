#!/usr/bin/env npx tsx

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import frontMatter from "front-matter";
import hljs from "highlight.js/lib/core";
import { marked, type RendererObject, type Tokens } from "marked";
import readingTime, { type ReadTimeResults } from "reading-time";

import {
  markedAlert,
  markedFootnotes,
  markedInfographic,
  markedMarkup,
  markedPlantUML,
  markedRuby,
  markedSlider,
  markedToc,
  MDKatex,
} from "./extensions/index.js";
import {
  COMMON_LANGUAGES,
  highlightAndFormatCode,
} from "./utils/languages.js";

type ThemeName = string;

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const THEME_DIR = path.resolve(SCRIPT_DIR, "themes");
const EXTERNAL_THEME_CONFIG_PATH =
  process.env.MD_THEME_CONFIG_PATH
  || "/Users/jimliu/GitHub/md/packages/shared/src/configs/theme.ts";
const EXTERNAL_THEME_DIR =
  process.env.MD_THEME_DIR
  || path.resolve(path.dirname(EXTERNAL_THEME_CONFIG_PATH), "theme-css");
const FALLBACK_THEMES: ThemeName[] = ["default", "grace", "simple"];

const DEFAULT_STYLE = {
  primaryColor: "#0F4C81",
  fontFamily:
    "-apple-system-font,BlinkMacSystemFont, Helvetica Neue, PingFang SC, Hiragino Sans GB , Microsoft YaHei UI , Microsoft YaHei ,Arial,sans-serif",
  fontSize: "16px",
  foreground: "0 0% 3.9%",
  blockquoteBackground: "#f7f7f7",
};

Object.entries(COMMON_LANGUAGES).forEach(([name, lang]) => {
  hljs.registerLanguage(name, lang);
});

export { hljs };

function stripOutputScope(cssContent: string): string {
  let css = cssContent;
  css = css.replace(/#output\s*\{/g, "body {");
  css = css.replace(/#output\s+/g, "");
  css = css.replace(/^#output\s*/gm, "");
  return css;
}

function discoverThemesFromDir(dir: string): string[] {
  if (!fs.existsSync(dir)) {
    return [];
  }
  return fs
    .readdirSync(dir)
    .filter((name) => name.endsWith(".css"))
    .map((name) => name.replace(/\.css$/i, ""))
    .filter((name) => name.toLowerCase() !== "base");
}

function readThemeNamesFromConfig(configPath: string): string[] {
  if (!fs.existsSync(configPath)) {
    return [];
  }
  const content = fs.readFileSync(configPath, "utf-8");
  const match = content.match(/themeOptionsMap\s*=\s*\{([\s\S]*?)\n\}/);
  if (!match) {
    return [];
  }
  return Array.from(match[1].matchAll(/^\s*([a-zA-Z0-9_-]+)\s*:/gm)).map(
    (item) => item[1]!
  );
}

function resolveThemeNames(): ThemeName[] {
  const localThemes = discoverThemesFromDir(THEME_DIR);
  const externalThemes = discoverThemesFromDir(EXTERNAL_THEME_DIR);
  const configThemes = readThemeNamesFromConfig(EXTERNAL_THEME_CONFIG_PATH);
  const combined = new Set<ThemeName>([
    ...localThemes,
    ...externalThemes,
    ...configThemes,
  ]);
  const resolved = Array.from(combined).filter((name) =>
    fs.existsSync(path.join(THEME_DIR, `${name}.css`))
    || fs.existsSync(path.join(EXTERNAL_THEME_DIR, `${name}.css`))
  );
  return resolved.length ? resolved : FALLBACK_THEMES;
}

const THEME_NAMES: ThemeName[] = resolveThemeNames();

marked.setOptions({
  breaks: true,
});
marked.use(markedSlider());

interface IOpts {
  legend?: string;
  citeStatus?: boolean;
  countStatus?: boolean;
  isMacCodeBlock?: boolean;
  isShowLineNumber?: boolean;
  themeMode?: "light" | "dark";
}

interface RendererAPI {
  reset: (newOpts: Partial<IOpts>) => void;
  setOptions: (newOpts: Partial<IOpts>) => void;
  getOpts: () => IOpts;
  parseFrontMatterAndContent: (markdown: string) => {
    yamlData: Record<string, any>;
    markdownContent: string;
    readingTime: ReadTimeResults;
  };
  buildReadingTime: (reading: ReadTimeResults) => string;
  buildFootnotes: () => string;
  buildAddition: () => string;
  createContainer: (html: string) => string;
}

interface ParseResult {
  yamlData: Record<string, any>;
  markdownContent: string;
  readingTime: ReadTimeResults;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/`/g, "&#96;");
}

function buildAddition(): string {
  return `
    <style>
      .preview-wrapper pre::before {
        position: absolute;
        top: 0;
        right: 0;
        color: #ccc;
        text-align: center;
        font-size: 0.8em;
        padding: 5px 10px 0;
        line-height: 15px;
        height: 15px;
        font-weight: 600;
      }
    </style>
  `;
}

function buildFootnoteArray(footnotes: [number, string, string][]): string {
  return footnotes
    .map(([index, title, link]) =>
      link === title
        ? `<code style="font-size: 90%; opacity: 0.6;">[${index}]</code>: <i style="word-break: break-all">${title}</i><br/>`
        : `<code style="font-size: 90%; opacity: 0.6;">[${index}]</code> ${title}: <i style="word-break: break-all">${link}</i><br/>`
    )
    .join("\n");
}

function transform(legend: string, text: string | null, title: string | null): string {
  const options = legend.split("-");
  for (const option of options) {
    if (option === "alt" && text) {
      return text;
    }
    if (option === "title" && title) {
      return title;
    }
  }
  return "";
}

const macCodeSvg = `
  <svg xmlns="http://www.w3.org/2000/svg" version="1.1" x="0px" y="0px" width="45px" height="13px" viewBox="0 0 450 130">
    <ellipse cx="50" cy="65" rx="50" ry="52" stroke="rgb(220,60,54)" stroke-width="2" fill="rgb(237,108,96)" />
    <ellipse cx="225" cy="65" rx="50" ry="52" stroke="rgb(218,151,33)" stroke-width="2" fill="rgb(247,193,81)" />
    <ellipse cx="400" cy="65" rx="50" ry="52" stroke="rgb(27,161,37)" stroke-width="2" fill="rgb(100,200,86)" />
  </svg>
`.trim();

function parseFrontMatterAndContent(markdownText: string): ParseResult {
  try {
    const parsed = frontMatter(markdownText);
    const yamlData = parsed.attributes;
    const markdownContent = parsed.body;

    const readingTimeResult = readingTime(markdownContent);

    return {
      yamlData: yamlData as Record<string, any>,
      markdownContent,
      readingTime: readingTimeResult,
    };
  } catch (error) {
    console.error("Error parsing front-matter:", error);
    return {
      yamlData: {},
      markdownContent: markdownText,
      readingTime: readingTime(markdownText),
    };
  }
}

export function initRenderer(opts: IOpts = {}): RendererAPI {
  const footnotes: [number, string, string][] = [];
  let footnoteIndex = 0;
  let codeIndex = 0;
  const listOrderedStack: boolean[] = [];
  const listCounters: number[] = [];
  const isBrowser = typeof window !== "undefined";

  function getOpts(): IOpts {
    return opts;
  }

  function styledContent(styleLabel: string, content: string, tagName?: string): string {
    const tag = tagName ?? styleLabel;
    const className = `${styleLabel.replace(/_/g, "-")}`;
    const headingAttr = /^h\d$/.test(tag) ? " data-heading=\"true\"" : "";
    return `<${tag} class="${className}"${headingAttr}>${content}</${tag}>`;
  }

  function addFootnote(title: string, link: string): number {
    const existingFootnote = footnotes.find(([, , existingLink]) => existingLink === link);
    if (existingFootnote) {
      return existingFootnote[0];
    }

    footnotes.push([++footnoteIndex, title, link]);
    return footnoteIndex;
  }

  function reset(newOpts: Partial<IOpts>): void {
    footnotes.length = 0;
    footnoteIndex = 0;
    setOptions(newOpts);
  }

  function setOptions(newOpts: Partial<IOpts>): void {
    opts = { ...opts, ...newOpts };
    marked.use(markedAlert());
    if (isBrowser) {
      marked.use(MDKatex({ nonStandard: true }, true));
    }
    marked.use(markedMarkup());
    marked.use(markedInfographic({ themeMode: opts.themeMode }));
  }

  function buildReadingTime(readingTimeResult: ReadTimeResults): string {
    if (!opts.countStatus) {
      return "";
    }
    if (!readingTimeResult.words) {
      return "";
    }
    return `
      <blockquote class="md-blockquote">
        <p class="md-blockquote-p">字数 ${readingTimeResult?.words}，阅读大约需 ${Math.ceil(readingTimeResult?.minutes)} 分钟</p>
      </blockquote>
    `;
  }

  const buildFootnotes = () => {
    if (!footnotes.length) {
      return "";
    }

    return (
      styledContent("h4", "引用链接")
      + styledContent("footnotes", buildFootnoteArray(footnotes), "p")
    );
  };

  const renderer: RendererObject = {
    heading({ tokens, depth }: Tokens.Heading) {
      const text = this.parser.parseInline(tokens);
      const tag = `h${depth}`;
      return styledContent(tag, text);
    },

    paragraph({ tokens }: Tokens.Paragraph): string {
      const text = this.parser.parseInline(tokens);
      const isFigureImage = text.includes("<figure") && text.includes("<img");
      const isEmpty = text.trim() === "";
      if (isFigureImage || isEmpty) {
        return text;
      }
      return styledContent("p", text);
    },

    blockquote({ tokens }: Tokens.Blockquote): string {
      const text = this.parser.parse(tokens);
      return styledContent("blockquote", text);
    },

    code({ text, lang = "" }: Tokens.Code): string {
      if (lang.startsWith("mermaid")) {
        if (isBrowser) {
          clearTimeout(codeIndex as any);
          codeIndex = setTimeout(async () => {
            const windowRef = typeof window !== "undefined" ? (window as any) : undefined;
            if (windowRef && windowRef.mermaid) {
              const mermaid = windowRef.mermaid;
              await mermaid.run();
            } else {
              const mermaid = await import("mermaid");
              await mermaid.default.run();
            }
          }, 0) as any as number;
        }
        return `<pre class="mermaid">${text}</pre>`;
      }
      const langText = lang.split(" ")[0];
      const isLanguageRegistered = hljs.getLanguage(langText);
      const language = isLanguageRegistered ? langText : "plaintext";

      const highlighted = highlightAndFormatCode(
        text,
        language,
        hljs,
        !!opts.isShowLineNumber
      );

      const span = `<span class="mac-sign" style="padding: 10px 14px 0;">${macCodeSvg}</span>`;
      let pendingAttr = "";
      if (!isLanguageRegistered && langText !== "plaintext") {
        const escapedText = text.replace(/"/g, "&quot;");
        pendingAttr = ` data-language-pending="${langText}" data-raw-code="${escapedText}" data-show-line-number="${opts.isShowLineNumber}"`;
      }
      const code = `<code class="language-${lang}"${pendingAttr}>${highlighted}</code>`;

      return `<pre class="hljs code__pre">${span}${code}</pre>`;
    },

    codespan({ text }: Tokens.Codespan): string {
      const escapedText = escapeHtml(text);
      return styledContent("codespan", escapedText, "code");
    },

    list({ ordered, items, start = 1 }: Tokens.List) {
      listOrderedStack.push(ordered);
      listCounters.push(Number(start));

      const html = items.map((item) => this.listitem(item)).join("");

      listOrderedStack.pop();
      listCounters.pop();

      return styledContent(ordered ? "ol" : "ul", html);
    },

    listitem(token: Tokens.ListItem) {
      const ordered = listOrderedStack[listOrderedStack.length - 1];
      const idx = listCounters[listCounters.length - 1]!;

      listCounters[listCounters.length - 1] = idx + 1;

      const prefix = ordered ? "" : "• ";

      let content: string;
      try {
        content = this.parser.parseInline(token.tokens);
      } catch {
        content = this.parser
          .parse(token.tokens)
          .replace(/^<p(?:\s[^>]*)?>([\s\S]*?)<\/p>/, "$1");
      }

      return styledContent("listitem", `${prefix}${content}`, "li");
    },

    image({ href, title, text }: Tokens.Image): string {
      const newText = opts.legend ? transform(opts.legend, text, title) : "";
      const subText = newText ? styledContent("figcaption", newText) : "";
      const titleAttr = title ? ` title="${title}"` : "";
      return `<figure><img src="${href}"${titleAttr} alt="${text}"/>${subText}</figure>`;
    },

    link({ href, title, text, tokens }: Tokens.Link): string {
      const parsedText = this.parser.parseInline(tokens);
      if (/^https?:\/\/mp\.weixin\.qq\.com/.test(href)) {
        return `<a href="${href}" title="${title || text}">${parsedText}</a>`;
      }
      if (href === text) {
        return parsedText;
      }
      if (opts.citeStatus) {
        const ref = addFootnote(title || text, href);
        return `<a href="${href}" title="${title || text}">${parsedText}<sup>[${ref}]</sup></a>`;
      }
      return `<a href="${href}" title="${title || text}">${parsedText}</a>`;
    },

    strong({ tokens }: Tokens.Strong): string {
      return styledContent("strong", this.parser.parseInline(tokens));
    },

    em({ tokens }: Tokens.Em): string {
      return styledContent("em", this.parser.parseInline(tokens));
    },

    table({ header, rows }: Tokens.Table): string {
      const headerRow = header
        .map((cell) => {
          const text = this.parser.parseInline(cell.tokens);
          return styledContent("th", text);
        })
        .join("");
      const body = rows
        .map((row) => {
          const rowContent = row.map((cell) => this.tablecell(cell)).join("");
          return styledContent("tr", rowContent);
        })
        .join("");
      return `
        <section style="max-width: 100%; overflow: auto">
          <table class="preview-table">
            <thead>${headerRow}</thead>
            <tbody>${body}</tbody>
          </table>
        </section>
      `;
    },

    tablecell(token: Tokens.TableCell): string {
      const text = this.parser.parseInline(token.tokens);
      return styledContent("td", text);
    },

    hr(_: Tokens.Hr): string {
      return styledContent("hr", "");
    },
  };

  marked.use({ renderer });
  marked.use(markedMarkup());
  marked.use(markedToc());
  marked.use(markedSlider());
  marked.use(markedAlert({}));
  if (isBrowser) {
    marked.use(MDKatex({ nonStandard: true }, true));
  }
  marked.use(markedFootnotes());
  marked.use(
    markedPlantUML({
      inlineSvg: isBrowser,
    })
  );
  marked.use(markedInfographic());
  marked.use(markedRuby());

  return {
    buildAddition,
    buildFootnotes,
    setOptions,
    reset,
    parseFrontMatterAndContent,
    buildReadingTime,
    createContainer(content: string) {
      return styledContent("container", content, "section");
    },
    getOpts,
  };
}

function printUsage(): void {
  console.error(
    [
      "Usage:",
      "  npx tsx src/md/render.ts <markdown_file> [--theme <name>]",
      "",
      "Options:",
      `  --theme   Theme name (${THEME_NAMES.join(", ")})`,
    ].join("\n")
  );
}

function parseArgs(argv: string[]): CliOptions | null {
  let inputPath = "";
  let theme: ThemeName = "default";

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--") && !inputPath) {
      inputPath = arg;
      continue;
    }

    if (arg === "--theme") {
      theme = (argv[i + 1] || "") as ThemeName;
      i += 1;
      continue;
    }

    if (arg.startsWith("--theme=")) {
      theme = arg.slice("--theme=".length) as ThemeName;
      continue;
    }

    if (arg === "--help" || arg === "-h") {
      return null;
    }

    console.error(`Unknown argument: ${arg}`);
    return null;
  }

  if (!inputPath) {
    return null;
  }

  if (!THEME_NAMES.includes(theme)) {
    console.error(`Unknown theme: ${theme}`);
    return null;
  }

  return {
    inputPath,
    theme,
  };
}

interface CliOptions {
  inputPath: string;
  theme: ThemeName;
}

function renderMarkdown(raw: string, renderer: RendererAPI): {
  html: string;
  readingTime: ReadTimeResults;
} {
  const { markdownContent, readingTime: readingTimeResult } =
    renderer.parseFrontMatterAndContent(raw);

  const html = marked.parse(markdownContent) as string;

  return { html, readingTime: readingTimeResult };
}

function postProcessHtml(
  baseHtml: string,
  reading: ReadTimeResults,
  renderer: RendererAPI
): string {
  let html = baseHtml;
  html = renderer.buildReadingTime(reading) + html;
  html += renderer.buildFootnotes();
  html += renderer.buildAddition();
  html += `
    <style>
      .hljs.code__pre > .mac-sign {
        display: ${renderer.getOpts().isMacCodeBlock ? "flex" : "none"};
      }
    </style>
  `;
  html += `
    <style>
      h2 strong {
        color: inherit !important;
      }
    </style>
  `;
  return renderer.createContainer(html);
}

function formatTimestamp(date = new Date()): string {
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(
    date.getDate()
  )}${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}`;
}

function ensureMarkdownPath(inputPath: string): void {
  if (!inputPath.toLowerCase().endsWith(".md")) {
    throw new Error("Input file must end with .md");
  }
}

function loadThemeCss(theme: ThemeName): {
  baseCss: string;
  themeCss: string;
} {
  const basePathCandidates = [
    path.join(THEME_DIR, "base.css"),
    path.join(EXTERNAL_THEME_DIR, "base.css"),
  ];
  const themePathCandidates = [
    path.join(THEME_DIR, `${theme}.css`),
    path.join(EXTERNAL_THEME_DIR, `${theme}.css`),
  ];
  const basePath = basePathCandidates.find((candidate) =>
    fs.existsSync(candidate)
  );
  const themePath = themePathCandidates.find((candidate) =>
    fs.existsSync(candidate)
  );

  if (!basePath) {
    throw new Error(
      `Missing base CSS. Checked: ${basePathCandidates.join(", ")}`
    );
  }

  if (!themePath) {
    throw new Error(
      `Missing theme CSS for "${theme}". Checked: ${themePathCandidates.join(", ")}`
    );
  }

  return {
    baseCss: fs.readFileSync(basePath, "utf-8"),
    themeCss: fs.readFileSync(themePath, "utf-8"),
  };
}

function buildCss(baseCss: string, themeCss: string): string {
  const variables = `
:root {
  --md-primary-color: ${DEFAULT_STYLE.primaryColor};
  --md-font-family: ${DEFAULT_STYLE.fontFamily};
  --md-font-size: ${DEFAULT_STYLE.fontSize};
  --foreground: ${DEFAULT_STYLE.foreground};
  --blockquote-background: ${DEFAULT_STYLE.blockquoteBackground};
}

body {
  margin: 0;
  padding: 24px;
  background: #ffffff;
}

#output {
  max-width: 860px;
  margin: 0 auto;
}
`.trim();

  return [variables, baseCss, themeCss].join("\n\n");
}

function normalizeThemeCss(css: string): string {
  return stripOutputScope(css);
}

function buildHtmlDocument(title: string, css: string, html: string): string {
  return [
    "<!doctype html>",
    "<html>",
    "<head>",
    '  <meta charset="utf-8" />',
    '  <meta name="viewport" content="width=device-width, initial-scale=1" />',
    `  <title>${title}</title>`,
    `  <style>${css}</style>`,
    "</head>",
    "<body>",
    '  <div id="output">',
    html,
    "  </div>",
    "</body>",
    "</html>",
  ].join("\n");
}

async function inlineCss(html: string): Promise<string> {
  try {
    const { default: juice } = await import("juice");
    return juice(html, {
      inlinePseudoElements: true,
      preserveImportant: true,
      resolveCSSVariables: false,
    });
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(
      `Missing dependency "juice" for CSS inlining. Install it first (e.g. "bun add juice" or "npm add juice"). Original error: ${detail}`
    );
  }
}

function normalizeCssText(cssText: string): string {
  return cssText
    .replace(/var\(--md-primary-color\)/g, DEFAULT_STYLE.primaryColor)
    .replace(/var\(--md-font-family\)/g, DEFAULT_STYLE.fontFamily)
    .replace(/var\(--md-font-size\)/g, DEFAULT_STYLE.fontSize)
    .replace(/var\(--blockquote-background\)/g, DEFAULT_STYLE.blockquoteBackground)
    .replace(/hsl\(var\(--foreground\)\)/g, "#3f3f3f")
    .replace(/--md-primary-color:\s*[^;"']+;?/g, "")
    .replace(/--md-font-family:\s*[^;"']+;?/g, "")
    .replace(/--md-font-size:\s*[^;"']+;?/g, "")
    .replace(/--blockquote-background:\s*[^;"']+;?/g, "")
    .replace(/--foreground:\s*[^;"']+;?/g, "");
}

function normalizeInlineCss(html: string): string {
  let output = html;
  output = output.replace(
    /<style([^>]*)>([\s\S]*?)<\/style>/gi,
    (_match, attrs: string, cssText: string) =>
      `<style${attrs}>${normalizeCssText(cssText)}</style>`
  );
  output = output.replace(
    /style="([^"]*)"/gi,
    (_match, cssText: string) => `style="${normalizeCssText(cssText)}"`
  );
  output = output.replace(
    /style='([^']*)'/gi,
    (_match, cssText: string) => `style='${normalizeCssText(cssText)}'`
  );
  return output;
}

function modifyHtmlStructure(htmlString: string): string {
  let output = htmlString;
  const pattern =
    /<li([^>]*)>([\s\S]*?)(<ul[\s\S]*?<\/ul>|<ol[\s\S]*?<\/ol>)<\/li>/i;
  while (pattern.test(output)) {
    output = output.replace(pattern, "<li$1>$2</li>$3");
  }
  return output;
}

async function main(): Promise<void> {
  const options = parseArgs(process.argv.slice(2));
  if (!options) {
    printUsage();
    process.exit(1);
  }

  const inputPath = path.resolve(process.cwd(), options.inputPath);
  ensureMarkdownPath(inputPath);

  if (!fs.existsSync(inputPath)) {
    console.error(`File not found: ${inputPath}`);
    process.exit(1);
  }

  const outputPath = path.resolve(
    process.cwd(),
    options.inputPath.replace(/\.md$/i, ".html")
  );

  const { baseCss, themeCss } = loadThemeCss(options.theme);
  const css = normalizeThemeCss(buildCss(baseCss, themeCss));
  const markdown = fs.readFileSync(inputPath, "utf-8");

  const renderer = initRenderer({});
  const { html: baseHtml, readingTime: readingTimeResult } = renderMarkdown(
    markdown,
    renderer
  );
  const content = postProcessHtml(baseHtml, readingTimeResult, renderer);

  const title = path.basename(outputPath, ".html");
  const html = buildHtmlDocument(title, css, content);
  const inlinedHtml = normalizeInlineCss(await inlineCss(html));
  const finalHtml = modifyHtmlStructure(inlinedHtml);

  let backupPath = "";
  if (fs.existsSync(outputPath)) {
    backupPath = `${outputPath}.bak-${formatTimestamp()}`;
    fs.renameSync(outputPath, backupPath);
  }

  fs.writeFileSync(outputPath, finalHtml, "utf-8");

  if (backupPath) {
    console.log(`Backup created: ${backupPath}`);
  }
  console.log(`HTML written: ${outputPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
