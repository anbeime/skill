---
name: jack-scroll-3d-sites
description: >
  Build or review scroll-driven 3D/video/frame-sequence websites where a product,
  object, or visual transforms as the user scrolls. Use for 3D scroll websites,
  scroll-linked canvas, video-on-scroll, frame extraction with FFmpeg, GSAP
  ScrollTrigger, Framer Motion useScroll, Three.js accents, Apple-style
  scrollytelling, or Jack Roberts inspired scroll-stop site builds.
---

# Jack Scroll 3D Sites

Use this skill to implement premium scroll-driven websites that scrub a video or image sequence as the user scrolls.

Source attribution: public-safe synthesis inspired by Jack Roberts' public teaching on 3D scroll-based websites. Credit Jack Roberts and link https://www.youtube.com/watch?v=TZUTe7s11-I when referencing the method publicly.

## Choose The Build Mode

- Existing project: match its framework, routing, styling, and deployment conventions.
- Portable demo: use single-page HTML/CSS/JS with a local server.
- Next.js/React: use Framer Motion or GSAP when the app already uses React or needs componentized pages.
- 3D accent: use Three.js only when there is a real 3D requirement; keep the primary 3D/canvas scene full-bleed or clearly integrated.

Use Context7 for current docs when using Next.js, GSAP, Framer Motion, Three.js, Vercel, or browser APIs.

## Asset Intake

Ask for or discover:

- video file or frame sequence
- brand name, logo, colors, fonts, CTA, and copy source
- intended pages and primary conversion
- whether this is a demo, production site, or client pitch

If the user has only prompts, route to `jack-scroll-asset-prompts` first.

## Frame Sequence Pattern

Use FFmpeg when a video must be scrubbed by scroll:

```bash
ffprobe -v quiet -print_format json -show_streams -show_format video.mp4
ffmpeg -i video.mp4 -vf "fps=12,scale=1920:-2" -q:v 2 public/sequence/frame_%04d.jpg
```

Tune frame count to the experience:

- 40 to 80 frames for lightweight demos.
- 80 to 150 frames for premium hero sections.
- Prefer compressed JPG/WebP over huge PNG sequences.
- Preload frames and show loading progress before revealing the section.

## Scroll Implementation Rules

- Map scroll progress to frame index and draw with `requestAnimationFrame`.
- Only redraw when the frame index changes.
- Use `devicePixelRatio` aware canvas sizing for crisp rendering.
- Use cover fit on desktop when the subject remains visible; use contain or slightly zoomed contain on mobile when cropping would hide the asset.
- Avoid `scroll-behavior: smooth` on frame-accurate scrub sections.
- Keep scroll duration adjustable, commonly 250vh to 500vh.
- Use sticky canvas sections for the scrubbed visual and normal document flow around it.

## Motion And UX

- Add text beats sparingly. The asset is the hero; overlays should not block important object details.
- Use `emil-animation-polish` for overlay fades, buttons, nav transitions, and hover/press states.
- Use `fluid-animations` for snap points, scroll stops, gesture-controlled panels, or momentum-sensitive interactions.
- Respect `prefers-reduced-motion`: provide a still image, shorter fade, or non-scrubbed fallback.
- Keep mobile cards compact so text never overlaps the object or viewport controls.

## Production Checks

- Test desktop and mobile viewport screenshots.
- Verify no blank canvas, missing frames, flicker, text overlap, or huge layout shift.
- Confirm assets load from a local server, not `file://`, when browser security requires it.
- Check Lighthouse/performance basics and image sizes.
- Add meaningful alt text or adjacent accessible copy for visual content.
- Do not deploy or publish without explicit user approval.

## Routing

- Pair with `design-taste-frontend` for visual direction.
- Pair with `modern-web-guidance` for platform correctness and accessibility.
- Pair with `playwright-cli` for real-browser proof.
- Pair with `jack-seo-launch-audit` when pages are ready for SEO and launch review.
