import fs from 'node:fs';
import { mkdir, writeFile } from 'node:fs/promises';
import https from 'node:https';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { createHash } from 'node:crypto';

interface ImageInfo {
  placeholder: string;
  localPath: string;
  originalPath: string;
  blockIndex: number;
}

interface ParsedMarkdown {
  title: string;
  coverImage: string | null;
  contentImages: ImageInfo[];
  html: string;
  totalBlocks: number;
}

function parseFrontmatter(content: string): { frontmatter: Record<string, string>; body: string } {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  if (!match) return { frontmatter: {}, body: content };

  const frontmatter: Record<string, string> = {};
  const lines = match[1]!.split('\n');
  for (const line of lines) {
    const colonIdx = line.indexOf(':');
    if (colonIdx > 0) {
      const key = line.slice(0, colonIdx).trim();
      let value = line.slice(colonIdx + 1).trim();
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      frontmatter[key] = value;
    }
  }

  return { frontmatter, body: match[2]! };
}

function downloadFile(url: string, destPath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;
    const file = fs.createWriteStream(destPath);

    const request = protocol.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (response) => {
      if (response.statusCode === 301 || response.statusCode === 302) {
        const redirectUrl = response.headers.location;
        if (redirectUrl) {
          file.close();
          fs.unlinkSync(destPath);
          downloadFile(redirectUrl, destPath).then(resolve).catch(reject);
          return;
        }
      }

      if (response.statusCode !== 200) {
        file.close();
        fs.unlinkSync(destPath);
        reject(new Error(`Failed to download: ${response.statusCode}`));
        return;
      }

      response.pipe(file);
      file.on('finish', () => {
        file.close();
        resolve();
      });
    });

    request.on('error', (err) => {
      file.close();
      fs.unlink(destPath, () => {});
      reject(err);
    });

    request.setTimeout(30000, () => {
      request.destroy();
      reject(new Error('Download timeout'));
    });
  });
}

function getImageExtension(urlOrPath: string): string {
  const match = urlOrPath.match(/\.(jpg|jpeg|png|gif|webp)(\?|$)/i);
  return match ? match[1]!.toLowerCase() : 'png';
}

async function resolveImagePath(imagePath: string, baseDir: string, tempDir: string): Promise<string> {
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    const hash = createHash('md5').update(imagePath).digest('hex').slice(0, 8);
    const ext = getImageExtension(imagePath);
    const localPath = path.join(tempDir, `remote_${hash}.${ext}`);

    if (!fs.existsSync(localPath)) {
      console.error(`[md-to-html] Downloading: ${imagePath}`);
      await downloadFile(imagePath, localPath);
    }
    return localPath;
  }

  if (path.isAbsolute(imagePath)) {
    return imagePath;
  }

  return path.resolve(baseDir, imagePath);
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function convertMarkdownToHtml(markdown: string, imageCallback: (src: string, alt: string) => string): { html: string; totalBlocks: number } {
  const lines = markdown.split('\n');
  const blocks: string[] = [];
  let inCodeBlock = false;
  let codeBlockContent: string[] = [];
  let inList = false;
  let listItems: string[] = [];
  let listType: 'ul' | 'ol' = 'ul';

  const flushList = () => {
    if (listItems.length > 0) {
      const tag = listType === 'ol' ? 'ol' : 'ul';
      blocks.push(`<${tag}>${listItems.map((item) => `<li>${item}</li>`).join('')}</${tag}>`);
      listItems = [];
      inList = false;
    }
  };

  const processInline = (text: string): string => {
    // Bold
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/__(.+?)__/g, '<strong>$1</strong>');

    // Italic
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
    text = text.replace(/_(.+?)_/g, '<em>$1</em>');

    // Links
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

    return text;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]!;

    // Code block
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        // X doesn't support <pre><code>, convert to blockquote
        const codeContent = codeBlockContent.map((l) => escapeHtml(l)).join('<br>');
        blocks.push(`<blockquote>${codeContent}</blockquote>`);
        codeBlockContent = [];
        inCodeBlock = false;
      } else {
        flushList();
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockContent.push(line);
      continue;
    }

    // Empty line
    if (line.trim() === '') {
      flushList();
      continue;
    }

    // Image
    const imgMatch = line.match(/^!\[([^\]]*)\]\(([^)]+)\)\s*$/);
    if (imgMatch) {
      flushList();
      const placeholder = imageCallback(imgMatch[2]!, imgMatch[1]!);
      blocks.push(`<p>${placeholder}</p>`);
      continue;
    }

    // Heading (H1 is title, skip it; H2-H6 become H2)
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      flushList();
      const level = headingMatch[1]!.length;
      if (level === 1) continue; // Skip H1, it's the title
      blocks.push(`<h2>${processInline(headingMatch[2]!)}</h2>`);
      continue;
    }

    // Blockquote
    if (line.startsWith('> ')) {
      flushList();
      blocks.push(`<blockquote>${processInline(line.slice(2))}</blockquote>`);
      continue;
    }

    // Unordered list
    const ulMatch = line.match(/^[-*]\s+(.+)$/);
    if (ulMatch) {
      if (!inList || listType !== 'ul') {
        flushList();
        inList = true;
        listType = 'ul';
      }
      listItems.push(processInline(ulMatch[1]!));
      continue;
    }

    // Ordered list
    const olMatch = line.match(/^\d+\.\s+(.+)$/);
    if (olMatch) {
      if (!inList || listType !== 'ol') {
        flushList();
        inList = true;
        listType = 'ol';
      }
      listItems.push(processInline(olMatch[1]!));
      continue;
    }

    // Horizontal rule
    if (/^[-*_]{3,}\s*$/.test(line)) {
      flushList();
      blocks.push('<hr>');
      continue;
    }

    // Regular paragraph
    flushList();
    blocks.push(`<p>${processInline(line)}</p>`);
  }

  flushList();

  return {
    html: blocks.join('\n'),
    totalBlocks: blocks.length,
  };
}

export async function parseMarkdown(
  markdownPath: string,
  options?: { coverImage?: string; title?: string; tempDir?: string },
): Promise<ParsedMarkdown> {
  const content = fs.readFileSync(markdownPath, 'utf-8');
  const baseDir = path.dirname(markdownPath);
  const tempDir = options?.tempDir ?? path.join(os.tmpdir(), 'x-article-images');

  await mkdir(tempDir, { recursive: true });

  const { frontmatter, body } = parseFrontmatter(content);

  // Extract title from frontmatter, option, or first H1
  let title = options?.title ?? frontmatter.title ?? '';
  if (!title) {
    const h1Match = body.match(/^#\s+(.+)$/m);
    if (h1Match) title = h1Match[1]!;
  }

  // Extract cover image from frontmatter or option
  let coverImagePath = options?.coverImage ?? frontmatter.cover_image ?? frontmatter.coverImage ?? frontmatter.cover ?? frontmatter.image ?? frontmatter.featureImage ?? frontmatter.feature_image ?? null;

  const images: Array<{ src: string; alt: string; blockIndex: number }> = [];
  let imageCounter = 0;

  const { html, totalBlocks } = convertMarkdownToHtml(body, (src, alt) => {
    const placeholder = `XIMGPH_${++imageCounter}`;
    const currentBlockIndex = images.length; // Will be set properly after HTML generation

    images.push({ src, alt, blockIndex: -1 }); // blockIndex set later
    return placeholder;
  });

  // Update block indices by finding placeholders in HTML
  const htmlLines = html.split('\n');
  let blockIdx = 0;
  for (const line of htmlLines) {
    for (let i = 0; i < images.length; i++) {
      const placeholder = `XIMGPH_${i + 1}`;
      if (line.includes(placeholder)) {
        images[i]!.blockIndex = blockIdx;
      }
    }
    blockIdx++;
  }

  // Resolve image paths (download remote, resolve relative)
  const contentImages: ImageInfo[] = [];
  let isFirstImage = true;
  let coverPlaceholder: string | null = null;

  for (let i = 0; i < images.length; i++) {
    const img = images[i]!;
    const localPath = await resolveImagePath(img.src, baseDir, tempDir);

    // First image becomes cover if no cover specified
    if (isFirstImage && !coverImagePath) {
      coverImagePath = localPath;
      coverPlaceholder = `XIMGPH_${i + 1}`;
      isFirstImage = false;
      // Don't add to contentImages, it's the cover
      continue;
    }

    isFirstImage = false;
    contentImages.push({
      placeholder: `XIMGPH_${i + 1}`,
      localPath,
      originalPath: img.src,
      blockIndex: img.blockIndex,
    });
  }

  // Remove cover placeholder from HTML if first image was used as cover
  let finalHtml = html;
  if (coverPlaceholder) {
    // Remove the placeholder and its containing <p> tag
    finalHtml = finalHtml.replace(new RegExp(`<p>${coverPlaceholder}</p>\\n?`, 'g'), '');
  }

  // Resolve cover image path
  let resolvedCoverImage: string | null = null;
  if (coverImagePath) {
    resolvedCoverImage = await resolveImagePath(coverImagePath, baseDir, tempDir);
  }

  return {
    title,
    coverImage: resolvedCoverImage,
    contentImages,
    html: finalHtml,
    totalBlocks,
  };
}

function printUsage(): never {
  console.log(`Convert Markdown to HTML for X Article publishing

Usage:
  npx -y bun md-to-html.ts <markdown_file> [options]

Options:
  --title <title>       Override title from frontmatter
  --cover <image>       Override cover image from frontmatter
  --output <json|html>  Output format (default: json)
  --html-only           Output only the HTML content
  --save-html <path>    Save HTML to file

Frontmatter fields:
  title: Article title (or use first H1)
  cover_image: Cover image path or URL
  cover: Alias for cover_image
  image: Alias for cover_image

Example:
  npx -y bun md-to-html.ts article.md --output json
  npx -y bun md-to-html.ts article.md --html-only > /tmp/article.html
  npx -y bun md-to-html.ts article.md --save-html /tmp/article.html
`);
  process.exit(0);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    printUsage();
  }

  let markdownPath: string | undefined;
  let title: string | undefined;
  let coverImage: string | undefined;
  let outputFormat: 'json' | 'html' = 'json';
  let htmlOnly = false;
  let saveHtmlPath: string | undefined;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i]!;
    if (arg === '--title' && args[i + 1]) {
      title = args[++i];
    } else if (arg === '--cover' && args[i + 1]) {
      coverImage = args[++i];
    } else if (arg === '--output' && args[i + 1]) {
      outputFormat = args[++i] as 'json' | 'html';
    } else if (arg === '--html-only') {
      htmlOnly = true;
    } else if (arg === '--save-html' && args[i + 1]) {
      saveHtmlPath = args[++i];
    } else if (!arg.startsWith('-')) {
      markdownPath = arg;
    }
  }

  if (!markdownPath) {
    console.error('Error: Markdown file path required');
    process.exit(1);
  }

  if (!fs.existsSync(markdownPath)) {
    console.error(`Error: File not found: ${markdownPath}`);
    process.exit(1);
  }

  const result = await parseMarkdown(markdownPath, { title, coverImage });

  if (saveHtmlPath) {
    await writeFile(saveHtmlPath, result.html, 'utf-8');
    console.error(`[md-to-html] HTML saved to: ${saveHtmlPath}`);
  }

  if (htmlOnly) {
    console.log(result.html);
  } else if (outputFormat === 'html') {
    console.log(result.html);
  } else {
    console.log(JSON.stringify(result, null, 2));
  }
}

await main().catch((err) => {
  console.error(`Error: ${err instanceof Error ? err.message : String(err)}`);
  process.exit(1);
});
