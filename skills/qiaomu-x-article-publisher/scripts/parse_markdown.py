#!/usr/bin/env python3
"""
Parse Markdown for X Articles publishing.

Extracts:
- Title (from first H1/H2 or first line)
- Cover image (first image)
- Content images with block index for precise positioning
- HTML content (images stripped)

Usage:
    python parse_markdown.py <markdown_file> [--output json|html]

Output (JSON):
{
    "title": "Article Title",
    "cover_image": "/path/to/cover.jpg",
    "content_images": [
        {"path": "/path/to/img.jpg", "block_index": 3, "after_text": "context..."},
        ...
    ],
    "html": "<p>Content...</p><h2>Section</h2>...",
    "total_blocks": 25
}

The block_index indicates which block element (0-indexed) the image should follow.
This allows precise positioning without relying on text matching.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def split_into_blocks(markdown: str) -> list[str]:
    """Split markdown into logical blocks (paragraphs, headers, quotes, code blocks, etc.)."""
    blocks = []
    current_block = []
    in_code_block = False
    code_block_lines = []

    lines = markdown.split('\n')

    for line in lines:
        stripped = line.strip()

        # Handle code block boundaries
        if stripped.startswith('```'):
            if in_code_block:
                # End of code block
                in_code_block = False
                if code_block_lines:
                    # Mark as code block with special prefix for later processing
                    # Use ___CODE_BLOCK_START___ and ___CODE_BLOCK_END___ to preserve content
                    blocks.append('___CODE_BLOCK_START___' + '\n'.join(code_block_lines) + '___CODE_BLOCK_END___')
                code_block_lines = []
            else:
                # Start of code block
                if current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = []
                in_code_block = True
            continue

        # If inside code block, collect ALL lines (including empty lines)
        if in_code_block:
            code_block_lines.append(line)
            continue

        # Empty line signals end of block
        if not stripped:
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            continue

        # Headers, blockquotes are their own blocks
        if stripped.startswith(('#', '>')):
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            blocks.append(stripped)
            continue

        # Image on its own line is its own block
        # Support both standard Markdown ![alt](path) and Obsidian ![[filename]] syntax
        if re.match(r'^!\[.*\]\(.*\)$', stripped) or re.match(r'^!\[\[.+\]\]$', stripped):
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            blocks.append(stripped)
            continue

        current_block.append(line)

    if current_block:
        blocks.append('\n'.join(current_block))

    # Handle unclosed code block
    if code_block_lines:
        blocks.append('___CODE_BLOCK_START___' + '\n'.join(code_block_lines) + '___CODE_BLOCK_END___')

    return blocks


def resolve_image_path(img_path: str, base_path: Path) -> str:
    """Resolve image path to absolute path.

    Supports:
    - Absolute paths
    - Relative paths from markdown file
    - Obsidian-style filename-only references (searches in .assets folder)
    """
    if os.path.isabs(img_path):
        return img_path

    # Try multiple resolution strategies
    full_path = None

    # Get just the filename for searching
    img_filename = Path(img_path).name

    # Strategy 1: Relative to markdown file directory
    candidate1 = base_path / img_path
    if candidate1.exists():
        full_path = str(candidate1)

    # Strategy 2: Check .assets folder (Obsidian convention: {filename}.assets/)
    # This handles the case where images are referenced by filename only
    if not full_path:
        # Find all .assets directories in base_path
        for assets_dir in base_path.glob("*.assets"):
            candidate = assets_dir / img_filename
            if candidate.exists():
                full_path = str(candidate)
                break

    # Strategy 3: Check if img_path itself is just a filename, search in base_path
    if not full_path and '/' not in img_path and '\\' not in img_path:
        # It's just a filename, search in base_path directly
        candidate = base_path / img_filename
        if candidate.exists():
            full_path = str(candidate)

    # Strategy 4: Path might be relative to a parent directory
    # (e.g., Obsidian paths like "01.inbox/papers/.../image.png")
    if not full_path:
        # Walk up the directory tree to find the root
        current = base_path
        for _ in range(10):  # Max 10 levels up
            parent = current.parent
            candidate = parent / img_path
            if candidate.exists():
                full_path = str(candidate)
                break
            # Also check .assets folders at each level
            for assets_dir in parent.glob("*.assets"):
                candidate = assets_dir / img_filename
                if candidate.exists():
                    full_path = str(candidate)
                    break
            if full_path:
                break
            if parent == current:  # Reached root
                break
            current = parent

    # Strategy 5: Check common knowledge base roots
    if not full_path:
        common_roots = [
            Path.home() / "乔木新知识库",
            Path.home() / "Documents",
            Path.home() / "Obsidian",
        ]
        for root in common_roots:
            candidate = root / img_path
            if candidate.exists():
                full_path = str(candidate)
                break

    # Fallback: Use original resolution (might not exist)
    if not full_path:
        full_path = str(base_path / img_path)

    return full_path


def extract_images_with_placeholders(markdown: str, base_path: Path) -> tuple[list[dict], str, int]:
    """Extract images and replace them with placeholders in markdown.

    Returns:
        (image_list, markdown_with_placeholders, total_blocks)

    The placeholder format is: ___IMG_PLACEHOLDER_{index}___
    This will be converted to HTML comment: <!-- IMG_PLACEHOLDER_{index} -->
    """
    blocks = split_into_blocks(markdown)
    images = []
    result_blocks = []

    # Standard Markdown: ![alt](path)
    img_pattern = re.compile(r'^!\[([^\]]*)\]\(([^)]+)\)$')
    # Obsidian format: ![[filename]] or ![[filename|alt]]
    obsidian_pattern = re.compile(r'^!\[\[([^\]|]+)(?:\|([^\]]*))?\]\]$')
    image_index = 0

    for i, block in enumerate(blocks):
        stripped = block.strip()
        match = img_pattern.match(stripped)
        obsidian_match = obsidian_pattern.match(stripped)

        if match:
            alt_text = match.group(1)
            img_path = match.group(2)
            full_path = resolve_image_path(img_path, base_path)

            # Create placeholder
            placeholder_id = f"IMG_PLACEHOLDER_{image_index}"

            images.append({
                "path": full_path,
                "alt": alt_text,
                "placeholder_id": placeholder_id,
                "index": image_index
            })

            # Insert placeholder block (will be converted to HTML comment)
            result_blocks.append(f"___{placeholder_id}___")
            image_index += 1
        elif obsidian_match:
            # Obsidian format: ![[filename]] or ![[filename|alt]]
            filename = obsidian_match.group(1).strip()
            alt_text = obsidian_match.group(2) or filename if obsidian_match.lastindex >= 2 else filename

            # Try to find the file in common locations
            full_path = None
            candidates = [
                base_path / filename,                    # Same directory
                base_path / "assets" / filename,         # assets subdirectory
                base_path / ".." / filename,             # Parent directory
                base_path / ".." / "assets" / filename,  # Parent's assets
            ]

            for candidate in candidates:
                if candidate.exists():
                    full_path = str(candidate.resolve())
                    break

            if not full_path:
                # Fallback: use assets directory path even if not verified
                full_path = str(base_path / "assets" / filename)

            # Create placeholder
            placeholder_id = f"IMG_PLACEHOLDER_{image_index}"

            images.append({
                "path": full_path,
                "alt": alt_text,
                "placeholder_id": placeholder_id,
                "index": image_index
            })

            # Insert placeholder block
            result_blocks.append(f"___{placeholder_id}___")
            image_index += 1
        else:
            result_blocks.append(block)

    result_markdown = '\n\n'.join(result_blocks)
    return images, result_markdown, len(result_blocks)


def extract_images_with_block_index(markdown: str, base_path: Path) -> tuple[list[dict], str, int]:
    """Extract images with their block index position (legacy method).

    Returns:
        (image_list, markdown_without_images, total_blocks)
    """
    blocks = split_into_blocks(markdown)
    images = []
    clean_blocks = []

    img_pattern = re.compile(r'^!\[([^\]]*)\]\(([^)]+)\)$')

    for i, block in enumerate(blocks):
        match = img_pattern.match(block.strip())
        if match:
            alt_text = match.group(1)
            img_path = match.group(2)
            full_path = resolve_image_path(img_path, base_path)

            # block_index is the index in clean_blocks (without images)
            # i.e., this image should be inserted after clean_blocks[block_index-1]
            block_index = len(clean_blocks)

            # Get context from previous block for reference
            after_text = ""
            is_after_h2 = False
            if clean_blocks:
                prev_block = clean_blocks[-1].strip()
                # Check if previous block is an H2
                is_after_h2 = prev_block.startswith('## ')
                # Get last line of previous block
                lines = [l for l in prev_block.split('\n') if l.strip()]
                after_text = lines[-1][:80] if lines else ""

            images.append({
                "path": full_path,
                "alt": alt_text,
                "block_index": block_index,
                "after_text": after_text,  # Keep for reference/debugging
                "is_after_h2": is_after_h2  # Flag to indicate if this image is right after H2
            })
        else:
            clean_blocks.append(block)

    clean_markdown = '\n\n'.join(clean_blocks)
    return images, clean_markdown, len(clean_blocks)


def extract_title(markdown: str) -> tuple[str, str, str]:
    """Extract title from first H1, H2, or first non-empty line.

    Returns:
        (title, markdown_without_title, title_source):
        - title: Title string
        - markdown: Markdown with H1 title removed
        - title_source: "h1", "h2", "first_line", or "none"

    If title is from H1, it's removed from markdown to avoid duplication.
    """
    lines = markdown.strip().split('\n')
    title = "Untitled"
    title_line_idx = None
    title_source = "none"

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # H1 - use as title and mark for removal
        if stripped.startswith('# '):
            title = stripped[2:].strip()
            title_line_idx = idx
            title_source = "h1"
            break
        # H2 - use as title but don't remove (it's a section header)
        if stripped.startswith('## '):
            title = stripped[3:].strip()
            title_source = "h2"
            break
        # First non-empty, non-image line
        if not stripped.startswith('!['):
            title = stripped[:100]
            title_source = "first_line"
            break

    # Remove H1 title line from markdown to avoid duplication
    if title_line_idx is not None:
        lines.pop(title_line_idx)
        markdown = '\n'.join(lines)

    return title, markdown, title_source


def convert_markdown_table(table_text: str) -> str:
    """Convert markdown table to HTML table."""
    lines = [line.strip() for line in table_text.strip().split('\n') if line.strip()]

    if len(lines) < 2:
        return table_text

    # Parse table structure
    rows = []
    for line in lines:
        # Split by | and clean up
        cells = [cell.strip() for cell in line.split('|')]
        # Remove empty first/last cells (from leading/trailing |)
        if cells and not cells[0]:
            cells = cells[1:]
        if cells and not cells[-1]:
            cells = cells[:-1]
        rows.append(cells)

    if len(rows) < 2:
        return table_text

    # Second row is separator (|-----|-----|)
    header_row = rows[0]
    data_rows = rows[2:] if len(rows) > 2 else []

    # Build HTML table
    html_parts = ['<table>']

    # Header
    html_parts.append('<thead><tr>')
    for cell in header_row:
        html_parts.append(f'<th>{cell}</th>')
    html_parts.append('</tr></thead>')

    # Body
    if data_rows:
        html_parts.append('<tbody>')
        for row in data_rows:
            html_parts.append('<tr>')
            for cell in row:
                html_parts.append(f'<td>{cell}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')

    html_parts.append('</table>')
    return ''.join(html_parts)


def markdown_to_html(markdown: str) -> str:
    """Convert markdown to HTML for X Articles rich text paste."""
    html = markdown

    # Process code blocks first (marked with ___CODE_BLOCK_START___ and ___CODE_BLOCK_END___)
    # Convert to blockquote format since X Articles doesn't support <pre><code>
    def convert_code_block(match):
        code_content = match.group(1)
        lines = code_content.strip().split('\n')
        # Join non-empty lines with <br> for display
        formatted = '<br>'.join(line for line in lines if line.strip())
        return f'<blockquote>{formatted}</blockquote>'

    html = re.sub(r'___CODE_BLOCK_START___(.*?)___CODE_BLOCK_END___', convert_code_block, html, flags=re.DOTALL)

    # Convert image placeholders to a visible marker that will appear in the editor
    # Using a distinctive text marker that's easy to find and less likely to be transformed
    def convert_img_placeholder(match):
        index = match.group(1)
        # Return a visible marker wrapped in a paragraph
        # Using @@@ prefix/suffix to make it distinctive and searchable
        return f'<p>@@@IMG_{index}@@@</p>'

    html = re.sub(r'___IMG_PLACEHOLDER_(\d+)___', convert_img_placeholder, html)

    # Convert markdown tables to HTML tables
    # Match table blocks (lines starting with |)
    def process_table(match):
        return convert_markdown_table(match.group(0))

    # Match consecutive lines starting with |
    html = re.sub(r'(?:^\|.+$\n?)+', process_table, html, flags=re.MULTILINE)

    # Horizontal rules - must be processed before headers to avoid conflicts
    html = re.sub(r'^(?:---+|\*\*\*+|___+)\s*$', r'<hr>', html, flags=re.MULTILINE)

    # Headers (H2-H6, H1 is title)
    html = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
    html = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)

    # Inline code (must be before bold/italic to avoid conflicts)
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

    # Strikethrough
    html = re.sub(r'~~(.+?)~~', r'<del>\1</del>', html)

    # === ROBUST BOLD/ITALIC PROCESSING ===
    # Process line by line to avoid cross-line matching issues with unclosed markers

    def process_inline_formatting(line: str) -> str:
        """Process bold and italic within a single line, handling unclosed markers gracefully."""
        # Skip placeholder lines only
        if line.startswith('@@@'):
            return line

        # For HTML block elements, process the inner content
        # Match pattern like <h2>content</h2> and process the content part
        block_match = re.match(r'^(<(?:h[2-6]|blockquote|p)>)(.*)(</(?:h[2-6]|blockquote|p)>)$', line)
        if block_match:
            prefix, content, suffix = block_match.groups()
            # Process bold in the inner content
            content = re.sub(r'\*\*([^*\n]+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', content)
            return prefix + content + suffix

        # First, handle bold (**text**) - only match properly closed pairs
        # Use word boundary and non-greedy matching within the same line
        line = re.sub(r'\*\*([^*\n]+?)\*\*', r'<strong>\1</strong>', line)

        # Handle line-start italic for image captions: *图1：...*
        # This pattern: starts with *, ends with * at line end, no * in between
        line = re.sub(r'^\*([^*\n]+)\*$', r'<em>\1</em>', line)

        # Handle inline italic (*text*) - must have proper closure within the same segment
        # Only match if there's a closing * and content doesn't contain * or newlines
        line = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', line)

        return line

    # Process formatting line by line
    lines = html.split('\n')
    processed_lines = [process_inline_formatting(line) for line in lines]
    html = '\n'.join(processed_lines)

    # Clean up any remaining unpaired * or ** markers that could cause display issues
    # Remove orphaned ** at line start (unclosed bold)
    html = re.sub(r'^\*\*(?![^*]*\*\*)', '', html, flags=re.MULTILINE)
    # Remove orphaned * at line start that's not part of a list and not followed by space (unclosed italic)
    html = re.sub(r'^\*(?![* \n])', '', html, flags=re.MULTILINE)

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    # Blockquotes (regular markdown blockquotes, not code blocks)
    html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)

    # Unordered lists
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Ordered lists
    html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Wrap consecutive <li> in <ul>
    html = re.sub(r'((?:<li>.*?</li>\n?)+)', r'<ul>\1</ul>', html)

    # Paragraphs - split by double newlines
    parts = html.split('\n\n')
    processed_parts = []

    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Skip if already a block element
        if part.startswith(('<h2>', '<h3>', '<h4>', '<h5>', '<h6>', '<blockquote>', '<ul>', '<ol>', '<table>', '<hr>')):
            processed_parts.append(part)
        else:
            # Wrap in paragraph, convert single newlines to <br>
            part = part.replace('\n', '<br>')
            processed_parts.append(f'<p>{part}</p>')

    return ''.join(processed_parts)


def parse_markdown_file(filepath: str, use_placeholders: bool = True) -> dict:
    """Parse a markdown file and return structured data.

    Args:
        filepath: Path to the markdown file
        use_placeholders: If True, use placeholder-based image positioning (recommended).
                         If False, use legacy block_index method.
    """
    path = Path(filepath)
    base_path = path.parent

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Use filename as title (remove .md extension)
    title = path.stem  # e.g., "AI时代的软件开发，为什么大公司只提升了10%效率？"

    # Still extract and remove H1 from content to avoid duplication
    _, content, title_source = extract_title(content)

    if use_placeholders:
        # New method: Extract images and insert placeholders
        images, markdown_with_placeholders, total_blocks = extract_images_with_placeholders(content, base_path)
        # Convert to HTML (placeholders will become visible markers)
        html = markdown_to_html(markdown_with_placeholders)
    else:
        # Legacy method: Extract images with block indices
        images, clean_markdown, total_blocks = extract_images_with_block_index(content, base_path)
        html = markdown_to_html(clean_markdown)

    # Title comes from filename, so no generation needed
    needs_title_generation = False

    return {
        "title": title,
        "title_source": "filename",  # Always use filename
        "needs_title_generation": needs_title_generation,
        "cover_image": None,  # No automatic cover image
        "needs_cover_generation": False,  # User handles cover manually
        "content_images": images,
        "html": html,
        "total_blocks": total_blocks,
        "source_file": str(path.absolute()),
        "use_placeholders": use_placeholders  # Flag to indicate which method was used
    }


def main():
    parser = argparse.ArgumentParser(description='Parse Markdown for X Articles')
    parser.add_argument('file', help='Markdown file to parse')
    parser.add_argument('--output', choices=['json', 'html'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--html-only', action='store_true',
                       help='Output only HTML content')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    result = parse_markdown_file(args.file)

    if args.html_only:
        print(result['html'])
    elif args.output == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result['html'])


if __name__ == '__main__':
    main()
