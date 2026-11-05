#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步手绘风格库最新数据至 handraw-static (静态分发仓库)
用法:
    python scripts/sync_to_static.py           # 仅同步本地文件
    python scripts/sync_to_static.py --git     # 同步并提交推送 Git
    python scripts/sync_to_static.py --deploy  # 同步并部署至 tencent-vm 云服务器
"""

import os
import re
import sys
import json
import shutil
import time
import argparse
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_REPO_DIR = Path(os.environ.get("STATIC_REPO_DIR", str(ROOT_DIR.parent / "handraw-static")))

REF_DIR = ROOT_DIR / "skills" / "handdraw-style-prompter" / "references"
IMAGES_DIR = ROOT_DIR / "images"
CLIENT_DIR = ROOT_DIR / "client"

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def sync_data():
    print(f"=== 开始同步数据到 {STATIC_REPO_DIR} ===")
    target_data_dir = STATIC_REPO_DIR / "data"
    target_data_dir.mkdir(parents=True, exist_ok=True)

    # 1. 核心 JSON 数据文件
    files_to_copy = [
        ("styles.json", REF_DIR / "styles.json", target_data_dir / "styles.json"),
        ("layouts.json", REF_DIR / "layouts.json", target_data_dir / "layouts.json"),
        ("colors.json", REF_DIR / "colors.json", target_data_dir / "colors.json"),
        ("tones.json", REF_DIR / "tones.json", target_data_dir / "tones.json"),
        ("partners.json", CLIENT_DIR / "partners.json", target_data_dir / "partners.json"),
        ("version.json", REF_DIR / "version.json", target_data_dir / "version.json"),
        ("model_capabilities.json", REF_DIR / "model_capabilities.json", target_data_dir / "model_capabilities.json"),
        ("style_alias_map.json", REF_DIR / "style_alias_map.json", target_data_dir / "style_alias_map.json"),
    ]

    for name, src, dst in files_to_copy:
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  [OK] 同步 {name}")
        else:
            print(f"  [Skip] 源文件不存在: {src}")

    # 读取统计
    styles = load_json(target_data_dir / "styles.json")
    layouts = load_json(target_data_dir / "layouts.json")
    colors = load_json(target_data_dir / "colors.json")
    tones = load_json(target_data_dir / "tones.json")
    # The unfinished client is local-only; fresh checkouts may have no partner source.
    partner_file = target_data_dir / "partners.json"
    if not partner_file.exists():
        save_json(partner_file, [])
    partners = load_json(partner_file)

    # 2. 生成 manifest.json
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    now_ver = time.strftime("%Y.%m.%d")
    manifest = {
        "version": "1.0.0",
        "data_version": now_ver,
        "updated_at": now_iso,
        "styles_count": len(styles),
        "layouts_count": len(layouts),
        "colors_count": len(colors),
        "tones_count": len(tones),
        "partners_count": len(partners),
        "data_urls": {
            "styles": "https://static.handraw-style.com/data/styles.json",
            "layouts": "https://static.handraw-style.com/data/layouts.json",
            "colors": "https://static.handraw-style.com/data/colors.json",
            "tones": "https://static.handraw-style.com/data/tones.json",
            "partners": "https://static.handraw-style.com/data/partners.json"
        },
        "images_base_url": "https://img.handraw-style.com/images/"
    }
    save_json(STATIC_REPO_DIR / "manifest.json", manifest)
    print(f"  [OK] 已生成 manifest.json (版本: {now_ver}, 画风数: {len(styles)})")

    # 3. 增量同步图片与静态资产
    target_img_dir = STATIC_REPO_DIR / "images"
    target_img_dir.mkdir(parents=True, exist_ok=True)
    img_subdirs = ["individual", "colors", "layouts", "tones", "characters", "custom"]
    copied_img_count = 0

    # 根目录图片 (realistic.webp, 演示海报等)
    for f in IMAGES_DIR.glob("*.*"):
        if f.is_file() and f.suffix.lower() in [".webp", ".png", ".jpg", ".gif", ".svg"]:
            dst_f = target_img_dir / f.name
            if not dst_f.exists() or f.stat().st_mtime > dst_f.stat().st_mtime:
                shutil.copy2(f, dst_f)
                copied_img_count += 1

    for sub in img_subdirs:
        src_sub = IMAGES_DIR / sub
        dst_sub = target_img_dir / sub
        if not src_sub.exists():
            continue
        dst_sub.mkdir(parents=True, exist_ok=True)
        for root, _, files in os.walk(src_sub):
            rel_dir = os.path.relpath(root, src_sub)
            dest_folder = dst_sub if rel_dir == "." else dst_sub / rel_dir
            dest_folder.mkdir(parents=True, exist_ok=True)
            for f in files:
                if f.endswith((".webp", ".png", ".jpg", ".gif", ".svg", ".json", ".js")):
                    src_f = Path(root) / f
                    dst_f = dest_folder / f
                    if not dst_f.exists() or src_f.stat().st_mtime > dst_f.stat().st_mtime:
                        shutil.copy2(src_f, dst_f)
                        copied_img_count += 1

    # 4. 同步 HTML 画廊页面
    src_gallery_dir = ROOT_DIR / "skills" / "handdraw-style-prompter" / "gallery"
    target_gallery_dir = STATIC_REPO_DIR / "gallery"
    if src_gallery_dir.exists():
        target_gallery_dir.mkdir(parents=True, exist_ok=True)
        for hf in src_gallery_dir.glob("*.html"):
            content = hf.read_text(encoding="utf-8")
            adapted = re.sub(r'(\.\./)+images/', '../images/', content)
            (target_gallery_dir / hf.name).write_text(adapted, encoding="utf-8")
        print("  [OK] HTML 页面已自适应同步到 gallery/")

    print(f"  [OK] 图片同步完成 (新增/更新图片: {copied_img_count} 张)")
    return manifest

def git_push_static(manifest):
    print("\n=== 执行 Git 提交并推送 handraw-static ===")
    try:
        subprocess.run(["git", "add", "."], cwd=str(STATIC_REPO_DIR), check=True)
        msg = f"chore(data): auto sync styles {manifest['data_version']} ({manifest['styles_count']} styles)"
        res = subprocess.run(["git", "commit", "-m", msg], cwd=str(STATIC_REPO_DIR), capture_output=True, text=True)
        print(res.stdout.strip())
        subprocess.run(["git", "push", "origin", "master"], cwd=str(STATIC_REPO_DIR), check=True)
        print("  [OK] 已成功推送到 GitHub 远端仓库！")
    except Exception as e:
        print(f"  [Warn] Git 推送失败或无新变更: {e}")

def deploy_to_vm():
    import tarfile
    print("\n=== 执行部署至 tencent-vm ===")
    remote_target = "/home/yang0/projectHome/handraw-static"
    # 创建远程目录
    ssh_cmd = ["ssh", "-n", "tencent-vm", f"mkdir -p {remote_target}/data {remote_target}/images {remote_target}/gallery"]
    subprocess.run(ssh_cmd, check=True, stdin=subprocess.DEVNULL)

    # 传输 manifest 与 data
    scp_manifest = ["scp", str(STATIC_REPO_DIR / "manifest.json"), f"tencent-vm:{remote_target}/manifest.json"]
    subprocess.run(scp_manifest, check=True, stdin=subprocess.DEVNULL)

    scp_data = ["scp", "-r", f"{STATIC_REPO_DIR}/data/*", f"tencent-vm:{remote_target}/data/"]
    subprocess.run(scp_data, check=True, stdin=subprocess.DEVNULL)

    # 传输 gallery
    if (STATIC_REPO_DIR / "gallery").exists():
        scp_gallery = ["scp", "-r", f"{STATIC_REPO_DIR}/gallery/*", f"tencent-vm:{remote_target}/gallery/"]
        subprocess.run(scp_gallery, check=True, stdin=subprocess.DEVNULL)

    # 增量检测并同步远程 images
    local_img_dir = STATIC_REPO_DIR / "images"
    res = subprocess.run(["ssh", "-n", "tencent-vm", f"find {remote_target}/images -type f"], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    remote_files = set()
    prefix = f"{remote_target}/images/"
    for line in res.stdout.strip().splitlines():
        line = line.strip()
        if line.startswith(prefix):
            remote_files.add(line[len(prefix):])

    missing_images = []
    for r, _, files in os.walk(local_img_dir):
        for f in files:
            rel = Path(r, f).relative_to(local_img_dir).as_posix()
            if rel not in remote_files:
                missing_images.append(rel)

    if missing_images:
        print(f"  [Sync] 检测到 {len(missing_images)} 个远程缺失图片/资源，正在打包传输...")
        tar_path = STATIC_REPO_DIR / "temp_images_delta.tar"
        with tarfile.open(tar_path, "w") as tar:
            for rel in missing_images:
                tar.add(local_img_dir / rel, arcname=rel)

        scp_tar = ["scp", str(tar_path), f"tencent-vm:/tmp/images_delta.tar"]
        subprocess.run(scp_tar, check=True, stdin=subprocess.DEVNULL)
        tar_path.unlink(missing_ok=True)

        ssh_untar = [
            "ssh", "-n", "tencent-vm",
            f"tar -xf /tmp/images_delta.tar -C {remote_target}/images/ && rm -f /tmp/images_delta.tar"
        ]
        subprocess.run(ssh_untar, check=True, stdin=subprocess.DEVNULL)
        print(f"  [OK] 已成功传输并解压 {len(missing_images)} 个新图片/资源！")
    else:
        print("  [OK] 远程图片库已是最新，无需增量传输。")

    # 保持 discourse/public 软链接并自动重新编译公开画廊
    link_cmd = [
        "ssh", "-n", "tencent-vm",
        f"ln -sfn {remote_target}/gallery /home/yang0/projectHome/discourse/public/gallery && "
        f"ln -sfn {remote_target}/data /home/yang0/projectHome/discourse/public/data && "
        f"for f in {remote_target}/images/*; do "
        'bn=$(basename "$f"); '
        'if [ ! -e "/home/yang0/projectHome/discourse/public/images/$bn" ]; then ln -s "$f" "/home/yang0/projectHome/discourse/public/images/$bn"; fi; '
        "done; "
        'CURRENT_REL=$(cat /home/yang0/handraw-data/deployment/current 2>/dev/null || true); '
        'if [ -n "$CURRENT_REL" ] && [ -d "/home/yang0/projectHome/handraw-web/.local/releases/$CURRENT_REL/plugin" ]; then '
        '  python3 /home/yang0/projectHome/handraw-web/ops/build_public.py "/home/yang0/projectHome/handraw-web/.local/releases/$CURRENT_REL/plugin" "/home/yang0/handraw-data/public/releases/$CURRENT_REL" /home/yang0/projectHome/handraw-static; '
        'fi; true'
    ]
    subprocess.run(link_cmd, check=True, stdin=subprocess.DEVNULL)
    print("  [OK] manifest, data, gallery, images 及公开画廊 overlay 已成功部署到 tencent-vm！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync data to handraw-static")
    parser.add_argument("--git", action="store_true", help="Commit and push to Git repository")
    parser.add_argument("--deploy", action="store_true", help="Deploy to tencent-vm server")
    args = parser.parse_args()

    m = sync_data()
    if args.git:
        git_push_static(m)
    if args.deploy:
        deploy_to_vm()
    print("=== 同步完成 ===")
