#!/usr/bin/env python3
"""
package_skill.py - Build and verify distribution packages for Skill Marketplace.

Generates:
1. dist/handdraw-style-prompter-v{version}.zip
   - Standard flat skill package (SKILL.md at zip root).
   - Contains gallery/, images/, references/, scripts/, docs.
   - All gallery image paths adapted to ../images/ and verified offline.
2. dist/handdraw-style-prompter-folder-v{version}.zip
   - Enclosed folder package (handdraw-style-prompter/ at zip root).
3. dist/handraw-style-ecosystem-v{version}.zip
   - Complete static-image Skill ecosystem package (image design skills + assets).

Validations:
- Executes validate_library.py and audit_release.py
- Sandboxed image path verification (extracts to isolated temp folder, checks every img src)
- Computes SHA256 checksums and file size metrics
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "handdraw-style-prompter"
DIST_DIR = ROOT / "dist"
VERSION_FILE = ROOT / "version.json"
VIDEO_SKILLS = {"handraw-video-producer", "handraw-browser-producer", "handraw-jianying-producer", "handraw-volc-tts", "knowledge-video-director"}


def verify_image_only(source_dir: Path) -> None:
    """Fail if retired video implementation or UI is accidentally reintroduced."""
    for item in source_dir.rglob("*"):
        rel = item.relative_to(source_dir)
        if any(part in VIDEO_SKILLS for part in rel.parts) or item.name in {"video-shots.html", "video-shot-previews", "build_video_shot_gallery.py"}:
            raise RuntimeError(f"Video artifact in image package: {rel}")
        if item.is_file() and item.suffix == ".html":
            text = item.read_text(encoding="utf-8")
            if 'data-mode="video"' in text or 'href="video-shots.html"' in text:
                raise RuntimeError(f"Retired video UI in image package: {rel}")

IMAGE_FALLBACK_SCRIPT = """<script>
(function() {
  function fixImg(img) {
    if (!img || img.__fixed) return;
    var src = img.getAttribute('src') || '';
    var idx = src.indexOf('images/');
    if (idx === -1) return;
    var sub = src.substring(idx);
    var step = parseInt(img.dataset.retry || '0', 10);
    var candidates = [
      '../../../../' + sub,
      '../../../' + sub,
      '../../' + sub,
      '../' + sub,
      './' + sub,
      '/' + sub,
      'https://img.handraw-style.com/' + sub,
      'https://raw.githubusercontent.com/yang0/handraw-style/master/' + sub
    ];
    while (step < candidates.length) {
      var nextSrc = candidates[step];
      step++;
      if (nextSrc !== src) {
        img.dataset.retry = step.toString();
        img.src = nextSrc;
        return;
      }
    }
    img.__fixed = true;
  }
  window.addEventListener('error', function(e) {
    if (e.target && e.target.tagName === 'IMG') {
      fixImg(e.target);
    }
  }, true);
  window.addEventListener('load', function(e) {
    if (e.target && e.target.tagName === 'IMG') {
      var card = e.target.closest('.style-card, .layout-card, .color-card, .asset-card');
      if (card && e.target.src) {
        card.dataset.image = e.target.src;
      }
    }
  }, true);
})();
</script>"""


def get_version() -> str:
    if VERSION_FILE.exists():
        try:
            data = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
            return str(data.get("version", "1.9.1"))
        except Exception:
            pass
    return "1.9.1"


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_tracked_files() -> list[str]:
    res = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [p for p in res.stdout.decode("utf-8").split("\0") if p]


def adapt_html_for_standalone(html_content: str) -> str:
    """Adapt relative paths and inject fallback script for standalone skill."""
    # Convert ../../../images/ to ../images/
    adapted = re.sub(r'(\.\./)+images/', '../images/', html_content)

    # Ensure fallback script is present in head
    if "fixImg" not in adapted:
        if "<head>" in adapted:
            adapted = adapted.replace("<head>", f"<head>\n{IMAGE_FALLBACK_SCRIPT}", 1)
        elif "<style>" in adapted:
            adapted = adapted.replace("<style>", f"{IMAGE_FALLBACK_SCRIPT}\n<style>", 1)

    # In openPreview, prefer cardImg.src if available
    adapted = re.sub(
        r'preview\.src\s*=\s*card\.dataset\.image;',
        r'var cardImg = card.querySelector("img"); preview.src = (cardImg && cardImg.src) ? cardImg.src : card.dataset.image;',
        adapted,
    )
    return adapted


def build_standalone_staging(staging_dir: Path) -> None:
    """Prepare clean standalone skill files in staging_dir."""
    staging_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy SKILL.md
    shutil.copy2(SKILL_DIR / "SKILL.md", staging_dir / "SKILL.md")

    # 2. Copy gallery/
    gallery_dst = staging_dir / "gallery"
    gallery_dst.mkdir(parents=True, exist_ok=True)
    for item in (SKILL_DIR / "gallery").iterdir():
        if item.is_dir():
            shutil.copytree(item, gallery_dst / item.name, dirs_exist_ok=True)
        elif item.suffix.lower() == ".html":
            content = item.read_text(encoding="utf-8")
            adapted_content = adapt_html_for_standalone(content)
            (gallery_dst / item.name).write_text(adapted_content, encoding="utf-8")
        else:
            shutil.copy2(item, gallery_dst / item.name)

    # 3. Copy references/
    ref_dst = staging_dir / "references"
    if (SKILL_DIR / "references").exists():
        shutil.copytree(SKILL_DIR / "references", ref_dst, dirs_exist_ok=True)

    # 4. Copy scripts/
    scripts_dst = staging_dir / "scripts"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    for script_file in (SKILL_DIR / "scripts").glob("*.py"):
        shutil.copy2(script_file, scripts_dst / script_file.name)

    # 5. Copy tracked images/
    images_dst = staging_dir / "images"
    images_dst.mkdir(parents=True, exist_ok=True)
    tracked = get_tracked_files()
    tracked_images = [f for f in tracked if f.startswith("images/") and (ROOT / f).is_file()]

    for rel_path in tracked_images:
        src_path = ROOT / rel_path
        # rel_path is like "images/individual/FA/FA-001.webp"
        sub_rel = Path(rel_path).relative_to("images")
        target_path = images_dst / sub_rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, target_path)

    # 6. Copy root docs & metadata
    for doc in ["README.md", "README_en.md", "LICENSE", "version.json"]:
        if (ROOT / doc).exists():
            shutil.copy2(ROOT / doc, staging_dir / doc)


def create_zip_archive(source_dir: Path, zip_path: Path, prefix: str = "") -> None:
    verify_image_only(source_dir)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root_dir, dirs, files in os.walk(source_dir):
            for file in sorted(files):
                full_path = Path(root_dir) / file
                rel_to_source = full_path.relative_to(source_dir)
                archive_name = str(Path(prefix) / rel_to_source).replace("\\", "/")
                zf.write(full_path, archive_name)


def verify_sandbox_gallery(extract_dir: Path, is_standalone: bool) -> dict[str, int]:
    """Inspect all HTML files in unzipped package and verify that 100% of local images exist."""
    gallery_dir = extract_dir / "gallery"
    if not gallery_dir.exists():
        # Check if inside enclosing folder
        subdirs = [d for d in extract_dir.iterdir() if d.is_dir()]
        if subdirs and (subdirs[0] / "gallery").exists():
            gallery_dir = subdirs[0] / "gallery"

    assert gallery_dir.exists(), f"gallery folder not found in {extract_dir}"

    html_files = list(gallery_dir.glob("*.html"))
    verified_images = 0
    missing_images = []

    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8")
        # Match src="..." and data-image="..."
        matches = re.findall(r'(?:src|data-image)=["\']([^"\']+)["\']', content)
        for rel_url in matches:
            if not rel_url or "${" in rel_url or "{" in rel_url:
                continue
            if rel_url.endswith(".js"):
                continue
            if rel_url.startswith(("http://", "https://", "data:", "#")):
                continue
            # Strip query params or hash if any
            clean_url = rel_url.split("?")[0].split("#")[0]
            # Ensure it's an image file
            if not clean_url.lower().endswith((".webp", ".png", ".jpg", ".jpeg", ".svg", ".gif")):
                continue
            target_path = (html_file.parent / clean_url).resolve()
            if target_path.exists():
                verified_images += 1
            else:
                missing_images.append({
                    "html": html_file.name,
                    "url": rel_url,
                    "resolved": str(target_path),
                })

    if missing_images:
        print(f"❌ Verification FAILED for {extract_dir}: {len(missing_images)} missing image references!")
        for m in missing_images[:10]:
            print(f"   [{m['html']}] {m['url']} -> {m['resolved']}")
        raise RuntimeError(f"Missing images in package verification: {len(missing_images)} total")

    return {
        "html_count": len(html_files),
        "verified_images": verified_images,
        "missing_images": len(missing_images),
    }


def build_ecosystem_staging(staging_dir: Path) -> None:
    """Prepare clean ecosystem package files in staging_dir."""
    staging_dir.mkdir(parents=True, exist_ok=True)
    tracked = get_tracked_files()

    # Exclude development-only or temporary patterns
    excluded_prefixes = (
        "output/",
        "videos/",
        "downloads/",
        "temp/",
        "tmp/",
        "business/",
        "dist/",
        ".obsidian/",
        ".pytest_cache/",
        ".workbuddy/",
        "images/individual_backup/",
        "images/custom/",
    )

    for rel_path in tracked:
        if any(rel_path.startswith(ex) for ex in excluded_prefixes):
            continue
        src = ROOT / rel_path
        if not src.is_file():
            continue
        dst = staging_dir / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def main() -> int:
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    version = get_version()
    print(f"📦 Starting packaging for handdraw-style-prompter v{version}...")

    # 1. Validation checks
    print("\n🔍 Step 1: Running validations (validate_library.py & audit_release.py)...")
    res_val = subprocess.run(
        [sys.executable, "-X", "utf8", str(SKILL_DIR / "scripts" / "validate_library.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if res_val.returncode != 0:
        print("❌ validate_library.py failed:\n", res_val.stderr or res_val.stdout)
        return 1
    print("   ✅ validate_library.py passed.")

    res_audit = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit_release.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if res_audit.returncode != 0:
        print("❌ audit_release.py failed:\n", res_audit.stderr or res_audit.stdout)
        return 1
    print("   ✅ audit_release.py passed (0 secret/path leaks).")

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    (ROOT / "tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        # Step 2: Build Standalone Packages
        print("\n🔨 Step 2: Preparing standalone skill package...")
        standalone_stage = tmp_dir / "standalone_stage"
        build_standalone_staging(standalone_stage)

        # 2A: Flat zip (SKILL.md at zip root - Standard Antigravity/Claude format)
        flat_zip = DIST_DIR / f"handdraw-style-prompter-v{version}.zip"
        print(f"   Creating {flat_zip.name}...")
        create_zip_archive(standalone_stage, flat_zip, prefix="")

        # 2B: Enclosed folder zip (handdraw-style-prompter/SKILL.md)
        folder_zip = DIST_DIR / f"handdraw-style-prompter-folder-v{version}.zip"
        print(f"   Creating {folder_zip.name}...")
        create_zip_archive(standalone_stage, folder_zip, prefix="handdraw-style-prompter")

        # Step 3: Build Full Ecosystem Package
        print("\n🔨 Step 3: Preparing full ecosystem repository package...")
        eco_stage = tmp_dir / "eco_stage"
        build_ecosystem_staging(eco_stage)
        eco_zip = DIST_DIR / f"handraw-style-ecosystem-v{version}.zip"
        print(f"   Creating {eco_zip.name}...")
        create_zip_archive(eco_stage, eco_zip, prefix="")

        # Step 4: Verify Sandboxed Extraction & Image Validity
        print("\n🧪 Step 4: Verifying gallery image validity in sandboxed extractions...")

        # Verify Flat Zip
        verify_flat_dir = tmp_dir / "test_flat"
        with zipfile.ZipFile(flat_zip, "r") as zf:
            zf.extractall(verify_flat_dir)
        stats_flat = verify_sandbox_gallery(verify_flat_dir, is_standalone=True)
        print(f"   ✅ {flat_zip.name}: Verified {stats_flat['html_count']} HTML files, {stats_flat['verified_images']} images (0 broken).")

        # Verify Folder Zip
        verify_folder_dir = tmp_dir / "test_folder"
        with zipfile.ZipFile(folder_zip, "r") as zf:
            zf.extractall(verify_folder_dir)
        stats_folder = verify_sandbox_gallery(verify_folder_dir, is_standalone=True)
        print(f"   ✅ {folder_zip.name}: Verified {stats_folder['html_count']} HTML files, {stats_folder['verified_images']} images (0 broken).")

        # Verify Ecosystem Zip
        verify_eco_dir = tmp_dir / "test_eco"
        with zipfile.ZipFile(eco_zip, "r") as zf:
            zf.extractall(verify_eco_dir)
        eco_gallery_dir = verify_eco_dir / "skills" / "handdraw-style-prompter"
        stats_eco = verify_sandbox_gallery(eco_gallery_dir, is_standalone=False)
        print(f"   ✅ {eco_zip.name}: Verified {stats_eco['html_count']} HTML files, {stats_eco['verified_images']} images (0 broken).")

    # Step 5: Summary Report
    print("\n🎉 Packaging & Verification Complete! Output packages:\n")
    packages = [flat_zip, folder_zip, eco_zip]
    for pkg in packages:
        size_mb = pkg.stat().st_size / (1024 * 1024)
        checksum = sha256_file(pkg)
        print(f"• File:   {pkg.name}")
        print(f"  Path:   {pkg.resolve()}")
        print(f"  Size:   {size_mb:.2f} MB")
        print(f"  SHA256: {checksum}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
