import os, zipfile, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent
skill_dir = ROOT / "skills" / "handdraw-style-prompter"
zip_path = ROOT / "dist" / "handraw-skill-workbuddy-v1.0.3.zip"

# Ensure layouts/ exists under skill_dir
layouts_src = skill_dir / "references" / "layouts"
layouts_dst = skill_dir / "layouts"
if layouts_src.exists() and not layouts_dst.exists():
    import shutil
    shutil.copytree(layouts_src, layouts_dst)
    print(f"Copied {len(list(layouts_dst.glob('*.md')))} layouts to {layouts_dst}")

# Whitelist allowed scripts
allowed_scripts = {
    'resolve_reference.py',
    'prompt_style.py',
    'layout_library.py',
    'style_asset_paths.py'
}

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for item in skill_dir.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(skill_dir)
        
        # Exclude pycache and nested subfolders
        if "__pycache__" in str(item) or item.suffix in [".pyc", ".pyo"]:
            continue

        # Allow layouts/*.md (1-level subfolder)
        if rel.parts[0] == 'layouts':
            if len(rel.parts) == 2 and rel.suffix == '.md':
                z.write(item, arcname=rel.as_posix())
            continue

        # Strictly <= 2 levels
        if len(rel.parts) > 2:
            continue
        
        # In scripts/, only include allowed scripts
        if rel.parts[0] == 'scripts' and rel.name not in allowed_scripts:
            print(f"Excluding non-runtime script: {rel}")
            continue

        z.write(item, arcname=rel.as_posix())

print(f"\nCreated: {zip_path}")
size_kb = zip_path.stat().st_size / 1024
print(f"Size: {size_kb:.2f} KB ({size_kb / 1024:.2f} MB)")

# Verify all zip entries
with zipfile.ZipFile(zip_path, "r") as z:
    names = z.namelist()
    print(f"Total files in zip: {len(names)}")
    max_depth = max(len(Path(n).parts) for n in names)
    print(f"Max directory depth in zip: {max_depth}")
    assert max_depth <= 2, f"Depth exceeded: {max_depth}"
    print("Verification PASSED: Strictly <= 2 levels!")

    # Check key files
    assert "SKILL.md" in names
    assert "layouts/SC-001.md" in names
    assert "references/layouts.json" in names
    assert "references/styles.json" in names
    assert "scripts/prompt_style.py" in names
    print("All critical files verified present in zip!")
