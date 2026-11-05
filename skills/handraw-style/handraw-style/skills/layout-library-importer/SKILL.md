---
name: layout-library-importer
description: Add a supplied layout image and bilingual layout prompt to the local handdraw-style layout library and gallery. Use for new SC-* social-card or IG-* infographic layouts; do not use for style-number imports.
---

# Layout Library Importer

Use this Skill when the user wants to add a new visual layout/type to the local hand-drawn layout gallery. This is a repository-local workflow: do not commit, push, publish, or install anything externally unless the user separately asks.

## Source of truth

Work from the repository root and read the live implementation before editing:

- `skills/handdraw-style-prompter/references/layouts.json` is the layout index.
- `skills/handdraw-style-prompter/references/layouts/*.md` is the authoritative bilingual prompt content.
- `images/layouts/social-cards/`, `images/layouts/infographics/`, `images/layouts/comic-storyboards/`, and `images/layouts/ip-characters/` hold the layout images; canonical assets use WebP.
- `skills/handdraw-style-prompter/scripts/build_layout_gallery.py` rebuilds the derived gallery.
- `skills/handdraw-style-prompter/scripts/validate_library.py` is the full validation command.

Preserve unrelated dirty work. Inspect `git status --short` before editing and do not reset, clean, or overwrite files outside the requested layout import.

## Import workflow

### Batch input mode

Unless the user explicitly asks to rebuild, treat consecutive layout imports as batch input. For each supplied image, convert it to WebP when needed, add its index entry, and create its bilingual prompt file, but do not rebuild `gallery/layouts.html` or run the full validator after each item.

When the user says `重建索引`, rebuild the layout gallery once from the accumulated canonical index and run the full validation and whitespace check. The canonical index is `references/layouts.json`; this request means regenerate and validate its derived gallery, not recreate the index entries already recorded.

1. Determine the next ID from the live index. Use the next number within the requested category: `SC-###` for `social-card`, `IG-###` for `infographic`, `SB-###` for `comic-storyboard`, `IP-###` for `ip-character`. Never reuse an existing ID or infer a number from a filename alone.
2. Treat the user-supplied image as the canonical visual source. The repository asset must always use the `.webp` extension. If the supplied image is already WebP, copy it to the category directory with the new ID. If it is another format, convert it to WebP losslessly using Python:

   ```powershell
   python -c "from PIL import Image; img = Image.open(r'<input>'); img.save(r'<target>.webp', format='WEBP', lossless=True)"
   ```

   Do not delete the source attachment. Do not generate, crop, recolor, or otherwise alter the image content. If the attachment is unavailable as a readable local file, stop before changing the index and ask the user to reattach it.
3. Add one index object to `references/layouts.json` with the ID, exact category, concise Chinese display name, repository-relative WebP image path (`../../../images/layouts/...webp`), prompt path (`layouts/{ID}.md`), and concrete internal keywords. Keep the JSON array ordered by category and numeric ID.
4. Create `references/layouts/{ID}.md` with exactly two non-empty marker blocks:

   ```text
   <!-- zh -->
   Chinese layout prompt

   <!-- en -->
   English layout prompt
   ```

   The prompt must describe composition, text hierarchy, placement, whitespace, and other layout constraints supplied by the user. Do not invent subject matter or illustration style. The Chinese and English blocks must express the same constraints. The layout prompt is the single source of truth used by prompt combination.
5. When the user requests a rebuild, rebuild the derived gallery and sync documentation counts:

   ```powershell
   python skills/handdraw-style-prompter/scripts/build_layout_gallery.py
   ```

   The build script automatically regenerates `gallery/layouts.html`, updates `LAYOUTS.md` / `LAYOUTS_en.md`, and synchronizes layout totals and category counts across `README.md`, `README_en.md`, and all `SKILL.md` files. Do not manually edit the generated `gallery/layouts.html`. The gallery must remain browse-only: thumbnail, ID/name information, enlarged preview, and copy-prompt behavior; no input form.

6. Synchronize client caches & mirrors:
   Always ensure local desktop caches and mirror environments reflect the new layout entry:
   - Copy `references/layouts.json` to `client/cache/layouts.json`.
   - If `.agents/` mirror exists, ensure its `references/` and `gallery/layouts.html` are synchronized.
   - When deploying to static site, verify that `https://handraw-style.com/gallery/layouts.html` returns HTTP 200 and includes the newly added layout ID.

## Validation

Run this section after an explicit rebuild request. During batch input mode, only confirm that the current image, index entry, and prompt file exist and agree. For every newly added layout, also confirm that the indexed image path ends in `.webp` and that the WebP file exists. Existing legacy PNG assets are outside this migration step.

Run the full validator and whitespace check:

```powershell
python skills/handdraw-style-prompter/scripts/validate_library.py
git diff --check
```

Also verify directly that the new image, index entry, prompt file, generated card, and category count agree. For a social-card import with no infographic entries, the generated page must not show an infographic filter. When an `IG-*` entry is added later, the existing generator should expose that category automatically.

If browser automation is available, reload the existing local `layouts.html` preview and check the new card, full-image display, category filter, enlarged preview, and copy action. If the local `file://` page is blocked by browser policy, report that visual QA was not completed; do not present string or file checks as a substitute for visual confirmation.

## Response contract

Report the assigned ID, display name, canonical image path, prompt path, validation result, and whether visual browser QA completed. Mention any browser restriction explicitly. Do not claim that a layout was generated when the user supplied the image.
