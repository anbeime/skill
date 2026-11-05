# Canonical Identity Reference Policy — 2.24.24

## Default
The first real-person image(s) explicitly supplied by the user for a participant are the canonical identity source. They remain the identity source across turns, themes, rerolls, card draws, remixes, grids and enlargements.

## Derived images
Beauty outputs, wardrobe previews, contact sheets, shots, enlargements, rerenders and any AI-generated portrait are derived images. They never become identity references automatically.

Derived images may be used only for composition, pose, style or scene continuity while the canonical original is still supplied as the identity reference.

## Explicit promotion
Only explicit user intent to use a derived image as the future person/identity reference may promote it. Selecting, enlarging, liking or rerendering an image is not promotion.

When promoted, retain the original canonical reference and record the promotion; allow immediate revert to the original on request.

## Multi-person
Maintain a stable participant_id → canonical original reference mapping. Never infer a replacement from a newer output and never swap identities across participants.


## Face-only identity semantics
Canonical original references are **face/identity references only**, not hairstyle references. Preserve face shape, core facial features, age impression and recognizability. Do not inherit hair length, straight/curly texture, bangs/fringe, parting, crown volume, side/back silhouette or hair-color feel from the canonical image unless the user explicitly asks to preserve the original hairstyle. When a locked `hairstyle_design` exists, it has precedence over all hair visible in identity-reference images.

## Identity Lock v2
For multi-panel contact sheets, every panel independently reconstructs each visible participant's facial identity directly from that participant's active identity reference. Never derive the next panel's face from another generated panel. Preserve stable facial geometry across panels and keep visible faces identity-readable. Composition/pose reference images never become face sources without explicit user promotion.
