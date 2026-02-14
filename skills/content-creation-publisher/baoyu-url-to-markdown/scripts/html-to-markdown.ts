import { parseHTML } from "linkedom";
import { Readability } from "@mozilla/readability";
import TurndownService from "turndown";
import { gfm } from "turndown-plugin-gfm";

export interface PageMetadata {
  url: string;
  title: string;
  description?: string;
  author?: string;
  published?: string;
  captured_at: string;
}

export interface ConversionResult {
  metadata: PageMetadata;
  markdown: string;
}

interface ExtractionCandidate {
  title: string | null;
  byline: string | null;
  excerpt: string | null;
  published: string | null;
  html: string | null;
  textContent: string;
  method: string;
}

type AnyRecord = Record<string, unknown>;

const MIN_CONTENT_LENGTH = 120;
const GOOD_CONTENT_LENGTH = 900;

const CONTENT_SELECTORS = [
  "article",
  "main article",
  "[role='main'] article",
  "[itemprop='articleBody']",
  ".article-content",
  ".article-body",
  ".post-content",
  ".entry-content",
  ".story-body",
  "main",
  "[role='main']",
  "#content",
  ".content",
];

const REMOVE_SELECTORS = [
  "script",
  "style",
  "noscript",
  "template",
  "iframe",
  "svg",
  "path",
  "nav",
  "aside",
  "footer",
  "header",
  "form",
  ".advertisement",
  ".ads",
  ".social-share",
  ".related-articles",
  ".comments",
  ".newsletter",
  ".cookie-banner",
  ".cookie-consent",
  "[role='navigation']",
  "[aria-label*='cookie' i]",
];

const PUBLISHED_TIME_SELECTORS = [
  "meta[property='article:published_time']",
  "meta[name='pubdate']",
  "meta[name='publishdate']",
  "meta[name='date']",
  "time[datetime]",
];

const ARTICLE_TYPES = new Set([
  "Article",
  "NewsArticle",
  "BlogPosting",
  "WebPage",
  "ReportageNewsArticle",
]);

const NEXT_DATA_CONTENT_PATHS = [
  "props.pageProps.content.body",
  "props.pageProps.article.body",
  "props.pageProps.article.content",
  "props.pageProps.post.body",
  "props.pageProps.post.content",
  "props.pageProps.data.body",
  "props.pageProps.story.body.content",
];

const cleanupAndExtractScriptBody = String.raw`
(function () {
  const baseUrl = document.baseURI || location.href;

  function toAbsolute(url) {
    if (!url) return url;
    try {
      return new URL(url, baseUrl).href;
    } catch {
      return url;
    }
  }

  function absolutizeAttr(selector, attr) {
    document.querySelectorAll(selector).forEach((el) => {
      const value = el.getAttribute(attr);
      if (!value) return;
      const abs = toAbsolute(value);
      if (abs) el.setAttribute(attr, abs);
    });
  }

  function absolutizeSrcset(selector) {
    document.querySelectorAll(selector).forEach((el) => {
      const srcset = el.getAttribute("srcset");
      if (!srcset) return;

      const normalized = srcset
        .split(",")
        .map((part) => {
          const trimmed = part.trim();
          if (!trimmed) return "";
          const pieces = trimmed.split(/\s+/);
          const url = pieces[0];
          const descriptor = pieces.slice(1).join(" ");
          const absoluteUrl = toAbsolute(url);
          return descriptor ? absoluteUrl + " " + descriptor : absoluteUrl;
        })
        .filter(Boolean)
        .join(", ");

      if (normalized) {
        el.setAttribute("srcset", normalized);
      }
    });
  }

  absolutizeAttr("a[href]", "href");
  absolutizeAttr("img[src], video[src], audio[src], source[src]", "src");
  absolutizeSrcset("img[srcset], source[srcset]");

  const removeSelectors = [
    "noscript",
    "template",
    ".cookie-banner",
    ".cookie-consent",
    ".consent-banner",
    "[aria-label*='cookie' i]",
    ".advertisement",
    ".ads"
  ];

  for (const sel of removeSelectors) {
    try {
      document.querySelectorAll(sel).forEach((el) => el.remove());
    } catch {}
  }

  function getMeta(names) {
    for (const name of names) {
      const el = document.querySelector('meta[name="' + name + '"]') || document.querySelector('meta[property="' + name + '"]');
      const content = el && el.getAttribute("content");
      if (content && content.trim()) return content.trim();
    }
    return undefined;
  }

  function flattenJsonLdItems(value) {
    if (!value || typeof value !== "object") return [];
    if (Array.isArray(value)) {
      return value.flatMap(flattenJsonLdItems);
    }

    const obj = value;
    if (Array.isArray(obj["@graph"])) {
      return obj["@graph"].flatMap(flattenJsonLdItems);
    }

    return [obj];
  }

  function extractJsonLdMeta() {
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (const script of scripts) {
      try {
        const parsed = JSON.parse(script.textContent || "");
        const items = flattenJsonLdItems(parsed);
        for (const item of items) {
          const rawType = Array.isArray(item["@type"]) ? item["@type"][0] : item["@type"];
          if (typeof rawType !== "string") continue;
          if (!["Article", "NewsArticle", "BlogPosting", "WebPage"].includes(rawType)) continue;

          const author = (() => {
            if (typeof item.author === "string") return item.author;
            if (Array.isArray(item.author) && item.author.length > 0) {
              const first = item.author[0];
              return first && typeof first === "object" ? first.name : undefined;
            }
            if (item.author && typeof item.author === "object") {
              return item.author.name;
            }
            return undefined;
          })();

          return {
            title: item.headline || item.name,
            description: item.description,
            author: typeof author === "string" ? author : undefined,
            published: item.datePublished || item.dateCreated,
          };
        }
      } catch {}
    }
    return {};
  }

  const jsonLd = extractJsonLdMeta();

  const timeEl = document.querySelector("time[datetime]");
  const title =
    getMeta(["og:title", "twitter:title"]) ||
    (typeof jsonLd.title === "string" ? jsonLd.title : undefined) ||
    document.querySelector("h1")?.textContent?.trim() ||
    document.title?.trim() ||
    "";

  const description =
    getMeta(["description", "og:description", "twitter:description"]) ||
    (typeof jsonLd.description === "string" ? jsonLd.description : undefined);

  const author =
    getMeta(["author", "article:author", "twitter:creator"]) ||
    (typeof jsonLd.author === "string" ? jsonLd.author : undefined);

  const published =
    timeEl?.getAttribute("datetime") ||
    getMeta(["article:published_time", "datePublished", "publishdate", "date"]) ||
    (typeof jsonLd.published === "string" ? jsonLd.published : undefined);

  return {
    title,
    description,
    author,
    published,
    html: document.documentElement.outerHTML,
  };
})()
`;

export const cleanupAndExtractScript = cleanupAndExtractScriptBody;

function pickString(...values: unknown[]): string | null {
  for (const value of values) {
    if (typeof value === "string") {
      const trimmed = value.trim();
      if (trimmed) return trimmed;
    }
  }
  return null;
}

function generateExcerpt(excerpt: string | null, textContent: string | null): string | null {
  if (excerpt) return excerpt;
  if (!textContent) return null;
  const trimmed = textContent.trim();
  if (!trimmed) return null;
  return trimmed.length > 200 ? `${trimmed.slice(0, 200)}...` : trimmed;
}

function extractPublishedTime(document: any): string | null {
  for (const selector of PUBLISHED_TIME_SELECTORS) {
    const el = document.querySelector(selector);
    if (!el) continue;
    const value = el.getAttribute("content") ?? el.getAttribute("datetime");
    if (value && value.trim()) return value.trim();
  }
  return null;
}

function extractTitle(document: any): string | null {
  const ogTitle = document.querySelector("meta[property='og:title']")?.getAttribute("content");
  if (ogTitle && ogTitle.trim()) return ogTitle.trim();

  const twitterTitle = document
    .querySelector("meta[name='twitter:title']")
    ?.getAttribute("content");
  if (twitterTitle && twitterTitle.trim()) return twitterTitle.trim();

  const title = document.querySelector("title")?.textContent?.trim();
  if (title) {
    const cleaned = title.split(/\s*[-|–—]\s*/)[0]?.trim();
    if (cleaned) return cleaned;
  }

  const h1 = document.querySelector("h1")?.textContent?.trim();
  return h1 || null;
}

function extractTextFromHtml(html: string): string {
  const { document } = parseHTML(`<!doctype html><html><body>${html}</body></html>`);
  for (const selector of ["script", "style", "noscript", "template", "iframe", "svg", "path"]) {
    for (const el of document.querySelectorAll(selector)) {
      el.remove();
    }
  }
  return document.body?.textContent?.replace(/\s+/g, " ").trim() ?? "";
}

function parseDocument(html: string): any {
  const normalized = /<\s*html[\s>]/i.test(html)
    ? html
    : `<!doctype html><html><body>${html}</body></html>`;
  return parseHTML(normalized).document;
}

function sanitizeHtml(html: string): string {
  const { document } = parseHTML(`<div id="__root">${html}</div>`);
  const root = document.querySelector("#__root");
  if (!root) return html;

  for (const selector of ["script", "style", "iframe", "noscript", "template", "svg", "path"]) {
    for (const el of root.querySelectorAll(selector)) {
      el.remove();
    }
  }

  return root.innerHTML;
}

function flattenJsonLdItems(data: unknown): AnyRecord[] {
  if (!data || typeof data !== "object") return [];
  if (Array.isArray(data)) return data.flatMap(flattenJsonLdItems);

  const item = data as AnyRecord;
  if (Array.isArray(item["@graph"])) {
    return (item["@graph"] as unknown[]).flatMap(flattenJsonLdItems);
  }

  return [item];
}

function parseJsonLdScripts(document: any): AnyRecord[] {
  const results: AnyRecord[] = [];
  const scripts = document.querySelectorAll("script[type='application/ld+json']");

  for (const script of scripts) {
    try {
      const data = JSON.parse(script.textContent ?? "");
      results.push(...flattenJsonLdItems(data));
    } catch {
      // ignore malformed blocks
    }
  }

  return results;
}

function isArticleType(item: AnyRecord): boolean {
  const value = Array.isArray(item["@type"]) ? item["@type"][0] : item["@type"];
  return typeof value === "string" && ARTICLE_TYPES.has(value);
}

function extractAuthorFromJsonLd(authorData: unknown): string | null {
  if (typeof authorData === "string") return authorData;
  if (!authorData || typeof authorData !== "object") return null;

  if (Array.isArray(authorData)) {
    const names = authorData
      .map((author) => extractAuthorFromJsonLd(author))
      .filter((name): name is string => Boolean(name));
    return names.length > 0 ? names.join(", ") : null;
  }

  const author = authorData as AnyRecord;
  return typeof author.name === "string" ? author.name : null;
}

function parseJsonLdItem(item: AnyRecord): ExtractionCandidate | null {
  if (!isArticleType(item)) return null;

  const rawContent =
    (typeof item.articleBody === "string" && item.articleBody) ||
    (typeof item.text === "string" && item.text) ||
    (typeof item.description === "string" && item.description) ||
    null;

  if (!rawContent) return null;

  const content = rawContent.trim();
  const htmlLike = /<\/?[a-z][\s\S]*>/i.test(content);
  const textContent = htmlLike ? extractTextFromHtml(content) : content;

  if (textContent.length < MIN_CONTENT_LENGTH) return null;

  return {
    title: pickString(item.headline, item.name),
    byline: extractAuthorFromJsonLd(item.author),
    excerpt: pickString(item.description),
    published: pickString(item.datePublished, item.dateCreated),
    html: htmlLike ? content : null,
    textContent,
    method: "json-ld",
  };
}

function tryJsonLdExtraction(document: any): ExtractionCandidate | null {
  for (const item of parseJsonLdScripts(document)) {
    const extracted = parseJsonLdItem(item);
    if (extracted) return extracted;
  }
  return null;
}

function getByPath(value: unknown, path: string): unknown {
  let current = value;
  for (const part of path.split(".")) {
    if (!current || typeof current !== "object") return undefined;
    current = (current as AnyRecord)[part];
  }
  return current;
}

function isContentBlockArray(value: unknown): value is AnyRecord[] {
  if (!Array.isArray(value) || value.length === 0) return false;
  return value.slice(0, 5).some((item) => {
    if (!item || typeof item !== "object") return false;
    const obj = item as AnyRecord;
    return "type" in obj || "text" in obj || "textHtml" in obj || "content" in obj;
  });
}

function extractTextFromContentBlocks(blocks: AnyRecord[]): string {
  const parts: string[] = [];

  function pushParagraph(text: string): void {
    const trimmed = text.trim();
    if (!trimmed) return;
    parts.push(trimmed, "\n\n");
  }

  function walk(node: unknown): void {
    if (!node || typeof node !== "object") return;
    const block = node as AnyRecord;

    if (typeof block.text === "string") {
      pushParagraph(block.text);
      return;
    }

    if (typeof block.textHtml === "string") {
      pushParagraph(extractTextFromHtml(block.textHtml));
      return;
    }

    if (Array.isArray(block.items)) {
      for (const item of block.items) {
        if (item && typeof item === "object") {
          const text = pickString((item as AnyRecord).text);
          if (text) parts.push(`- ${text}\n`);
        }
      }
      parts.push("\n");
    }

    if (Array.isArray(block.components)) {
      for (const component of block.components) {
        walk(component);
      }
    }

    if (Array.isArray(block.content)) {
      for (const child of block.content) {
        walk(child);
      }
    }
  }

  for (const block of blocks) {
    walk(block);
  }

  return parts.join("").replace(/\n{3,}/g, "\n\n").trim();
}

function tryStringBodyExtraction(
  content: string,
  meta: AnyRecord,
  document: any,
  method: string
): ExtractionCandidate | null {
  if (!content || content.length < MIN_CONTENT_LENGTH) return null;

  const isHtml = /<\/?[a-z][\s\S]*>/i.test(content);
  const html = isHtml ? sanitizeHtml(content) : null;
  const textContent = isHtml ? extractTextFromHtml(html) : content.trim();

  if (textContent.length < MIN_CONTENT_LENGTH) return null;

  return {
    title: pickString(meta.headline, meta.title, extractTitle(document)),
    byline: pickString(meta.byline, meta.author),
    excerpt: pickString(meta.description, meta.excerpt, generateExcerpt(null, textContent)),
    published: pickString(meta.datePublished, meta.publishedAt, extractPublishedTime(document)),
    html,
    textContent,
    method,
  };
}

function tryNextDataExtraction(document: any): ExtractionCandidate | null {
  try {
    const script = document.querySelector("script#__NEXT_DATA__");
    if (!script?.textContent) return null;

    const data = JSON.parse(script.textContent) as AnyRecord;
    const pageProps = (getByPath(data, "props.pageProps") ?? {}) as AnyRecord;

    for (const path of NEXT_DATA_CONTENT_PATHS) {
      const value = getByPath(data, path);

      if (typeof value === "string") {
        const parentPath = path.split(".").slice(0, -1).join(".");
        const parent = (getByPath(data, parentPath) ?? {}) as AnyRecord;
        const meta = {
          ...pageProps,
          ...parent,
          title: parent.title ?? (pageProps.title as string | undefined),
        };

        const candidate = tryStringBodyExtraction(value, meta, document, "next-data");
        if (candidate) return candidate;
      }

      if (isContentBlockArray(value)) {
        const textContent = extractTextFromContentBlocks(value);
        if (textContent.length < MIN_CONTENT_LENGTH) continue;

        return {
          title: pickString(
            getByPath(data, "props.pageProps.content.headline"),
            getByPath(data, "props.pageProps.article.headline"),
            getByPath(data, "props.pageProps.article.title"),
            getByPath(data, "props.pageProps.post.title"),
            pageProps.title,
            extractTitle(document)
          ),
          byline: pickString(
            getByPath(data, "props.pageProps.author.name"),
            getByPath(data, "props.pageProps.article.author.name")
          ),
          excerpt: pickString(
            getByPath(data, "props.pageProps.content.description"),
            getByPath(data, "props.pageProps.article.description"),
            pageProps.description,
            generateExcerpt(null, textContent)
          ),
          published: pickString(
            getByPath(data, "props.pageProps.content.datePublished"),
            getByPath(data, "props.pageProps.article.datePublished"),
            getByPath(data, "props.pageProps.publishedAt"),
            extractPublishedTime(document)
          ),
          html: null,
          textContent,
          method: "next-data",
        };
      }
    }
  } catch {
    return null;
  }

  return null;
}

function buildReadabilityCandidate(
  article: ReturnType<Readability["parse"]>,
  document: any,
  method: string
): ExtractionCandidate | null {
  const textContent = article?.textContent?.trim() ?? "";
  if (textContent.length < MIN_CONTENT_LENGTH) return null;

  return {
    title: pickString(article?.title, extractTitle(document)),
    byline: pickString(article?.byline),
    excerpt: pickString(article?.excerpt, generateExcerpt(null, textContent)),
    published: pickString(article?.publishedTime, extractPublishedTime(document)),
    html: article?.content ? sanitizeHtml(article.content) : null,
    textContent,
    method,
  };
}

function tryReadability(document: any): ExtractionCandidate | null {
  try {
    const strictClone = document.cloneNode(true) as Document;
    const strictResult = buildReadabilityCandidate(
      new Readability(strictClone).parse(),
      document,
      "readability"
    );
    if (strictResult) return strictResult;

    const relaxedClone = document.cloneNode(true) as Document;
    return buildReadabilityCandidate(
      new Readability(relaxedClone, { charThreshold: 120 }).parse(),
      document,
      "readability-relaxed"
    );
  } catch {
    return null;
  }
}

function trySelectorExtraction(document: any): ExtractionCandidate | null {
  for (const selector of CONTENT_SELECTORS) {
    const element = document.querySelector(selector);
    if (!element) continue;

    const clone = element.cloneNode(true) as Element;
    for (const removeSelector of REMOVE_SELECTORS) {
      for (const node of clone.querySelectorAll(removeSelector)) {
        node.remove();
      }
    }

    const html = sanitizeHtml(clone.innerHTML);
    const textContent = extractTextFromHtml(html);
    if (textContent.length < MIN_CONTENT_LENGTH) continue;

    return {
      title: extractTitle(document),
      byline: null,
      excerpt: generateExcerpt(null, textContent),
      published: extractPublishedTime(document),
      html,
      textContent,
      method: `selector:${selector}`,
    };
  }

  return null;
}

function tryBodyExtraction(document: any): ExtractionCandidate | null {
  const body = document.body;
  if (!body) return null;

  const clone = body.cloneNode(true) as Element;
  for (const removeSelector of REMOVE_SELECTORS) {
    for (const node of clone.querySelectorAll(removeSelector)) {
      node.remove();
    }
  }

  const html = sanitizeHtml(clone.innerHTML);
  const textContent = extractTextFromHtml(html);
  if (!textContent) return null;

  return {
    title: extractTitle(document),
    byline: null,
    excerpt: generateExcerpt(null, textContent),
    published: extractPublishedTime(document),
    html,
    textContent,
    method: "body-fallback",
  };
}

function pickBestCandidate(candidates: ExtractionCandidate[]): ExtractionCandidate | null {
  if (candidates.length === 0) return null;

  const methodOrder = [
    "readability",
    "readability-relaxed",
    "next-data",
    "json-ld",
    "selector:",
    "body-fallback",
  ];

  function methodRank(method: string): number {
    const idx = methodOrder.findIndex((entry) =>
      entry.endsWith(":") ? method.startsWith(entry) : method === entry
    );
    return idx === -1 ? methodOrder.length : idx;
  }

  const ranked = [...candidates].sort((a, b) => {
    const rankA = methodRank(a.method);
    const rankB = methodRank(b.method);
    if (rankA !== rankB) return rankA - rankB;
    return (b.textContent.length ?? 0) - (a.textContent.length ?? 0);
  });

  for (const candidate of ranked) {
    if (candidate.textContent.length >= GOOD_CONTENT_LENGTH) {
      return candidate;
    }
  }

  for (const candidate of ranked) {
    if (candidate.textContent.length >= MIN_CONTENT_LENGTH) {
      return candidate;
    }
  }

  return ranked[0];
}

function extractFromHtml(html: string): ExtractionCandidate | null {
  const document = parseDocument(html);

  const readabilityCandidate = tryReadability(document);
  const nextDataCandidate = tryNextDataExtraction(document);
  const jsonLdCandidate = tryJsonLdExtraction(document);
  const selectorCandidate = trySelectorExtraction(document);
  const bodyCandidate = tryBodyExtraction(document);

  const candidates = [
    readabilityCandidate,
    nextDataCandidate,
    jsonLdCandidate,
    selectorCandidate,
    bodyCandidate,
  ].filter((candidate): candidate is ExtractionCandidate => Boolean(candidate));

  const winner = pickBestCandidate(candidates);
  if (!winner) return null;

  return {
    ...winner,
    title: winner.title ?? extractTitle(document),
    published: winner.published ?? extractPublishedTime(document),
    excerpt: winner.excerpt ?? generateExcerpt(null, winner.textContent),
  };
}

const turndown = new TurndownService({
  headingStyle: "atx",
  hr: "---",
  bulletListMarker: "-",
  codeBlockStyle: "fenced",
  emDelimiter: "*",
  strongDelimiter: "**",
  linkStyle: "inlined",
});

turndown.use(gfm);

turndown.remove(["script", "style", "iframe", "noscript", "template", "svg", "path"]);

turndown.addRule("collapseFigure", {
  filter: "figure",
  replacement(content) {
    return `\n\n${content.trim()}\n\n`;
  },
});

turndown.addRule("dropInvisibleAnchors", {
  filter(node) {
    return node.nodeName === "A" && !(node as Element).textContent?.trim();
  },
  replacement() {
    return "";
  },
});

function normalizeMarkdown(markdown: string): string {
  return markdown
    .replace(/\r\n/g, "\n")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function convertHtmlToMarkdown(html: string): string {
  if (!html || !html.trim()) return "";

  try {
    const sanitized = sanitizeHtml(html);
    return turndown.turndown(sanitized);
  } catch {
    return "";
  }
}

function fallbackPlainText(html: string): string {
  const document = parseDocument(html);
  for (const selector of ["script", "style", "noscript", "template", "iframe", "svg", "path"]) {
    for (const el of document.querySelectorAll(selector)) {
      el.remove();
    }
  }
  const text = document.body?.textContent ?? document.documentElement?.textContent ?? "";
  return normalizeMarkdown(text.replace(/\s+/g, " "));
}

export function htmlToMarkdown(html: string): string {
  if (!html || !html.trim()) return "";

  const extracted = extractFromHtml(html);
  if (!extracted) {
    return fallbackPlainText(html);
  }

  let markdown = extracted.html ? convertHtmlToMarkdown(extracted.html) : "";
  if (!markdown.trim()) {
    markdown = extracted.textContent;
  }

  return normalizeMarkdown(markdown);
}

function escapeYamlValue(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r?\n/g, "\\n");
}

export function formatMetadataYaml(meta: PageMetadata): string {
  const lines = ["---"];
  lines.push(`url: ${meta.url}`);
  lines.push(`title: "${escapeYamlValue(meta.title)}"`);
  if (meta.description) lines.push(`description: "${escapeYamlValue(meta.description)}"`);
  if (meta.author) lines.push(`author: "${escapeYamlValue(meta.author)}"`);
  if (meta.published) lines.push(`published: "${escapeYamlValue(meta.published)}"`);
  lines.push(`captured_at: "${escapeYamlValue(meta.captured_at)}"`);
  lines.push("---");
  return lines.join("\n");
}

export function createMarkdownDocument(result: ConversionResult): string {
  const yaml = formatMetadataYaml(result.metadata);
  const escapedTitle = result.metadata.title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const titleRegex = new RegExp(`^#\\s+${escapedTitle}\\s*(\\n|$)`, "i");
  const hasTitle = titleRegex.test(result.markdown.trimStart());
  const title = result.metadata.title && !hasTitle ? `\n\n# ${result.metadata.title}\n\n` : "\n\n";
  return yaml + title + result.markdown;
}
