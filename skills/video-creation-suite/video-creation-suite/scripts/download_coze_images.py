#!/usr/bin/env python3
"""
下载Coze图片脚本（简化版）
Coze图片URL直接返回二进制数据，无需解析HTML
"""

import os
import requests
from pathlib import Path


def download_coze_image(coze_url: str, output_path: str) -> bool:
    """
    下载Coze图片

    参数:
        coze_url: Coze图片URL
        output_path: 输出路径

    返回:
        是否成功
    """
    try:
        # 发送请求获取图片
        response = requests.get(coze_url, timeout=30)
        response.raise_for_status()

        # 检查是否是图片数据
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type.lower():
            print(f"✗ 非图片内容: {coze_url}, Content-Type: {content_type}")
            return False

        # 保存图片
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"✓ 已下载: {output_path}")
        return True

    except Exception as e:
        print(f"✗ 下载失败: {coze_url}, 错误: {str(e)}")
        return False


def batch_download_images(image_list: list, output_dir: str):
    """
    批量下载图片

    参数:
        image_list: 图片列表，格式为 [(name, url), ...]
        output_dir: 输出目录

    返回:
        成功下载的数量
    """
    success_count = 0

    for idx, (name, url) in enumerate(image_list, 1):
        # 格式化文件名，确保以序号开头
        filename = f"{idx:02d}_{name}.jpg"
        output_path = os.path.join(output_dir, filename)

        if download_coze_image(url, output_path):
            success_count += 1

    print(f"\n总计: {success_count}/{len(image_list)} 张图片下载成功")
    return success_count


if __name__ == "__main__":
    # 图片列表
    images = [
        ("时序文明", "https://s.coze.cn/image/w8FwHY3qC50/"),
        ("双剑对决", "https://s.coze.cn/image/A_pncZWL5W4/"),
        ("钟楼齿轮人影", "https://s.coze.cn/image/cNZcD9Pk69c/"),
        ("云海舰队", "https://s.coze.cn/image/VImevvJISkM/"),
        ("钟楼碎裂", "https://s.coze.cn/image/9jKDreLox1g/"),
        ("三圣持剑", "https://s.coze.cn/image/GQD8Lc3UojQ/"),
        ("云端冰堡", "https://s.coze.cn/image/biqNmwgBOac/"),
        ("翼立沙漏", "https://s.coze.cn/image/GEiOnFGdCYs/"),
        ("黑翼银发战士", "https://s.coze.cn/image/ajtLSGycTXE/"),
        ("黑翼银发者", "https://s.coze.cn/image/YHlDdSKJWEE/"),
        ("古殿沙漏", "https://s.coze.cn/image/tm_biQxVzwA/"),
        ("迷雾中的帆船", "https://s.coze.cn/image/XGy7JT-K-fw/"),
        ("飞艇破城门", "https://s.coze.cn/image/CRUXVAUoe5A/"),
        ("古墙灯照卷轴", "https://s.coze.cn/image/bzeewv_sbMg/"),
        ("仰望流光", "https://s.coze.cn/image/1mLhS2-Focc/"),
        ("时空沙漏", "https://s.coze.cn/image/8AkR5UkE2IQ/"),
        ("星际飞船", "https://s.coze.cn/image/D69C0dBazKQ/"),
        ("飞艇燃城", "https://s.coze.cn/image/rFBSjzAkliA/"),
        ("巨沙漏与钟楼", "https://s.coze.cn/image/HNXC78tWch4/"),
        ("星际战甲", "https://s.coze.cn/image/sO5dIEG3ObY/"),
        ("时光圣坛", "https://s.coze.cn/image/wYzfukGvg6M/"),
        ("破时机甲", "https://s.coze.cn/image/y-tBZlIMuZ4/"),
        ("蝶舞沙漏", "https://s.coze.cn/image/HPv8sqL_BRs/"),
        ("蒸汽机械工坊", "https://s.coze.cn/image/EWpMz0cOdns/"),
        ("星际战甲_1", "https://s.coze.cn/image/UqrSI_H1yv0/"),
        ("白袍议会", "https://s.coze.cn/image/vLMZBBDvdjI/"),
        ("双剑交错", "https://s.coze.cn/image/buPeTGpzOD4/"),
        ("时序文明_1", "https://s.coze.cn/image/x1g3QJN0oFc/"),
        ("破序文明", "https://s.coze.cn/image/MY5iZgf8i1o/"),
        ("星际飞船_1", "https://s.coze.cn/image/1ogK5TMP9SU/")
    ]

    # 输出目录
    output_dir = "./output/images"

    # 批量下载
    batch_download_images(images, output_dir)
