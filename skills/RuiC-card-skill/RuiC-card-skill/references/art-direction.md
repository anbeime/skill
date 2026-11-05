# Layered artwork

Decide character or object, title, subtitle, action, art medium, palette, rarity and card aspect from the user. State assumptions only where they matter. Preserve reference identity when asked, and never invent text that claims official affiliation.

Everything lands on one shared portrait canvas, normally 1024×1536. Reserve roughly the top 15% and bottom 15% for typography, keep a complete readable silhouette, and keep the framing identical across layers — layers that were produced on different crops cannot be registered afterwards.

## Subject

The hero artwork: the requested subject and action with accurate anatomy and defining details, bold readable contours, and a genuinely transparent RGBA cutout. No border, no text, no background, no checkerboard, no baked full-card layout. Keep the alpha the image tool produced rather than re-mattng it by hand.

## Effects (optional)

A decorative overlay that floats on its own plane between the subject and the typography: petals, sparks, thorn work, drifting particles. It is a pre-cut RGBA asset like the subject, and it should stay sparse — this layer reads as a thin plane in front of the card, so a busy overlay looks like a second illustration fighting the hero. Set `effectsDepth` so it sits clearly in front of (or behind) the subject instead of sharing its depth. If the card has no such element, skip the layer entirely; an empty overlay just costs a plane.

## Background

Complementary atmosphere and motifs on a fully opaque canvas, with a quieter central field and quieter typography zones so the subject and the text stay legible. The foil is made by the material: restrained flecks in the painting are fine, but do not bake the rainbow sweeps, glitter or star fields into the picture — that is the material's job, and a pre-baked version leaves the parallax planes looking like sludge.

## Line art

Dark contour strokes on white, derived from the **same source** as the subject: reuse the subject's own draw calls, or run an edge and threshold pass over the finished subject. That is what keeps the contours registered; asking for a fresh line drawing from a text description produces a slightly different pose and the glow lands in the wrong place. Simplified single strokes, no hatching, no filled silhouettes. Inspect the registration before the material ever gets to amplify it.

## Text and card furniture

The exact title, subtitle, technique, tagline and edition. Prefer real fonts rendered to a transparent PNG for names and CJK text (`scripts/generate_typography.py` does this from `card-config.json`); keep high contrast and leave room for descenders and brush strokes. This layer is also where card furniture belongs — a border, a frame, corner ornaments — because the viewer samples it without parallax, so a frame drawn here stays welded to the card edge while everything else moves.

## Depth discipline

Give every layer a deliberately different depth and write those depths into `card-config.json`. Two layers sharing a depth collapse into one plane and the 3D read disappears; that is the most common reason a finished card looks flat. The border or frame layer stays at zero. When a layer must not move at all, put it in the text slot rather than trying to zero its parallax elsewhere.

## Honesty about alpha

When the image tool returns a purported cutout, check the alpha **numerically and visually**: sample the histogram, look at the edges. Some tools paint a gray/white checkerboard into RGB instead of returning alpha. `scripts/checkerboard_to_alpha.py` converts that board into a real alpha channel deterministically (and `validate_assets.py` invokes it automatically when the channel is missing, logging the result in `asset-validation.json`), but a genuine RGBA PNG from the tool is still better than a repair. Never assume a PNG has alpha because of its extension, and never let a flat opaque image into the alpha pipeline.

## References

Reference roles must be explicit — identity reference, style reference, edit target, or background — and each target stays invariant while the others change. Write the actual prompt set into the output project's provenance notes, not into this skill repository.
