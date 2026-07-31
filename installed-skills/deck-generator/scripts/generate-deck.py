#!/usr/bin/env python3
"""
Generate a presentation with AI-generated slide images.

Usage:
  python3 generate-deck.py --content slides.json --style whiteboard --title "My Deck"
  python3 generate-deck.py --content slides.json --style whiteboard --title "My Deck" --google-slides

Content JSON format:
[
  {"name": "01-title", "prompt": "Slide-specific content description"},
  {"name": "02-problem", "prompt": "Problem slide content description"},
  ...
]
"""
import argparse
import json
import base64
import os
import sys
import time
import urllib.request

# ── Style presets ──
STYLES = {
    "whiteboard": "Hand-drawn whiteboard illustration style presentation slide. Black ink sketch on clean white background. Orange accent color for highlights. Bold hand-lettered headers. Simple stick figures and icons. No photos, no gradients, no 3D effects. Minimalist sketch aesthetic like a whiteboard drawing. ",
    "corporate": "Clean professional corporate presentation slide. Navy blue and white color scheme with gold accents. Modern sans-serif typography. Flat design icons. Subtle geometric patterns in background. Professional data visualization style. No clip art. ",
    "minimalist": "Ultra-minimalist presentation slide. Pure white background. Single accent color (electric blue). Large bold sans-serif text. Maximum negative space. One idea per slide. No decorative elements. Apple keynote aesthetic. ",
    "dark-tech": "Dark-themed tech presentation slide. Near-black background (#0a0a0a). Neon green (#00ff88) accent color. Monospace font for headers. Terminal/code aesthetic. Subtle grid lines. Futuristic but readable. ",
    "playful": "Colorful playful presentation slide. Bright pastel color palette. Rounded shapes and soft edges. Fun hand-drawn doodle elements. Friendly sans-serif font. Energetic but not childish. Modern startup aesthetic. ",
    "editorial": "Editorial magazine-style presentation slide. Black and white with one spot color (red). Strong typographic hierarchy. Pull-quote style layouts. Thin serif headers, clean sans-serif body. High contrast. Vogue/Economist aesthetic. ",
}


def get_gemini_key():
    """Get Gemini API key from environment."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("ERROR: Set GEMINI_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)
    return key


def generate_image(api_key, prompt, output_path, aspect="16:9", model="imagen-4.0-generate-001"):
    """Generate image via Imagen API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": aspect}
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)

    predictions = data.get("predictions", [])
    if not predictions:
        raise ValueError(f"No predictions returned: {json.dumps(data)[:200]}")

    img_b64 = predictions[0].get("bytesBase64Encoded", "")
    if not img_b64:
        raise ValueError("No image data in prediction")

    img_data = base64.b64decode(img_b64)
    with open(output_path, "wb") as f:
        f.write(img_data)
    return len(img_data)


def main():
    parser = argparse.ArgumentParser(description="Generate AI-powered presentation slides")
    parser.add_argument("--content", required=True, help="Path to slides JSON file")
    parser.add_argument("--style", default="whiteboard", help="Style preset or custom prompt prefix")
    parser.add_argument("--title", default="Generated Presentation", help="Presentation title")
    parser.add_argument("--aspect", default="16:9", help="Image aspect ratio (16:9, 1:1, 4:3, etc.)")
    parser.add_argument("--model", default="imagen-4.0-generate-001", help="Imagen model")
    parser.add_argument("--output-dir", default="./output", help="Directory for generated images")
    parser.add_argument("--slides", help="Comma-separated slide numbers to regenerate (e.g., 3,7)")
    parser.add_argument("--google-slides", action="store_true", help="Create Google Slides presentation")
    parser.add_argument("--google-account", help="Google account email (for Google Slides)")
    args = parser.parse_args()

    # Load content
    with open(args.content) as f:
        slides = json.load(f)

    print(f"Generating {len(slides)} slides in '{args.style}' style...")

    # Resolve style prefix
    style_prefix = STYLES.get(args.style, args.style + " ")

    # Get API key
    api_key = get_gemini_key()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Filter to specific slides if requested
    slide_filter = None
    if args.slides:
        slide_filter = set(int(s) for s in args.slides.split(","))

    # Generate slide images
    image_paths = []
    for i, slide in enumerate(slides):
        if slide_filter and (i + 1) not in slide_filter:
            continue

        name = slide.get("name", f"slide-{i+1:02d}")
        prompt = style_prefix + slide["prompt"]
        img_path = os.path.join(args.output_dir, f"{name}.png")

        print(f"\n--- Slide {i+1}/{len(slides)}: {name} ---")
        print(f"  Generating image...")

        try:
            size = generate_image(api_key, prompt, img_path, args.aspect, args.model)
            print(f"  Done ({size:,} bytes)")
            image_paths.append(img_path)
        except Exception as e:
            print(f"  Failed: {e}")
            image_paths.append(None)

        time.sleep(1)  # Rate limit buffer

    successful = sum(1 for p in image_paths if p)
    print(f"\n{successful}/{len(slides)} slides generated in {args.output_dir}/")

    # Cost estimate
    cost = len(slides) * 0.04
    print(f"Estimated cost: ${cost:.2f}")

    # Summary JSON
    summary = {
        "title": args.title,
        "slides_generated": successful,
        "slides_total": len(slides),
        "style": args.style,
        "output_dir": args.output_dir,
        "cost_estimate": f"${cost:.2f}",
        "images": [p for p in image_paths if p],
    }
    summary_path = os.path.join(args.output_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
