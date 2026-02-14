# OOXML Notes for Comment-Only Reviews

This reference documents the minimal OOXML pieces needed by this skill. It is intentionally lightweight and focused on **comment insertion** only.

## Scope

- **Supported**: Adding Word comments to an existing .docx without changing document text.
- **Not supported**: Tracked changes, rich styling, or full schema validation.
- **Validation**: Only file presence + XML well-formedness.

## Required Files

The comment workflow touches only these parts inside a .docx package:

- `word/document.xml` (the main body)
- `word/comments.xml` (comment bodies)
- `word/_rels/document.xml.rels` (relationship to `comments.xml`)
- `[Content_Types].xml` (content type override for `comments.xml`)

## Namespaces

Use the WordprocessingML namespace for comment elements:

- `w` = `http://schemas.openxmlformats.org/wordprocessingml/2006/main`

## Comment Injection Model

To add a comment:

1. Insert a `w:commentRangeStart` element before the target paragraph content.
2. Insert a `w:commentRangeEnd` element at the end of the paragraph.
3. Insert a `w:commentReference` run right after the range end.
4. Append a `w:comment` entry in `word/comments.xml`.
5. Ensure `document.xml.rels` and `[Content_Types].xml` include the comments part.

### Range Markup Example

```xml
<w:commentRangeStart w:id="12"/>
<!-- paragraph content -->
<w:commentRangeEnd w:id="12"/>
<w:r><w:commentReference w:id="12"/></w:r>
```

### Comment Body Example

```xml
<w:comment w:id="12" w:author="Reviewer" w:initials="RV" w:date="2025-01-10T12:00:00Z">
  <w:p><w:r><w:t>Comment text line 1</w:t></w:r></w:p>
  <w:p><w:r><w:t>Comment text line 2</w:t></w:r></w:p>
</w:comment>
```

If a `w:t` node begins or ends with whitespace, add `xml:space="preserve"` so Word preserves spacing.

## Relationships

`word/_rels/document.xml.rels` must reference the comments part:

```xml
<Relationship Id="rIdX"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
  Target="comments.xml"/>
```

## Content Types

`[Content_Types].xml` must include:

```xml
<Override PartName="/word/comments.xml"
  ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
```

## Common Failure Modes

- **Comments do not show up**: missing relationship or content type override.
- **Comments show but are empty**: `comments.xml` malformed or `w:t` missing text node.
- **Spaces missing**: add `xml:space="preserve"` on the `w:t` nodes.

## When to Extend

If you need tracked changes, comment replies, or advanced metadata (e.g., commentsExtended), add separate modules and document them here. Keep this file short and only include what this skill actually uses.
