#!/usr/bin/env python3
"""
图片搜索脚本
使用Unsplash API搜索适配的封面图

使用方法：
python search_images.py --keyword "AI" --count 3 --size 1600x680
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request


def search_images(keyword, count=1, size="1600x680"):
    """
    搜索图片

    Args:
        keyword: 搜索关键词
        count: 返回图片数量
        size: 图片尺寸（默认1600x680，符合微信封面比例）

    Returns:
        list: 图片URL列表
    """
    # Unsplash源API
    base_url = "https://source.unsplash.com"

    image_urls = []

    try:
        for i in range(count):
            # 构建URL
            encoded_keyword = urllib.parse.quote(keyword)
            url = f"{base_url}/{size}/?{encoded_keyword}"

            # 为了避免缓存，添加随机参数
            import time
            url_with_random = f"{url}&random={int(time.time() * 1000)}"

            image_urls.append(url_with_random)

        return {
            "success": True,
            "keyword": keyword,
            "count": len(image_urls),
            "images": image_urls
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"搜索失败: {str(e)}",
            "images": []
        }


def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="图片搜索脚本")
    parser.add_argument("--keyword", required=True, help="搜索关键词")
    parser.add_argument("--count", type=int, default=1, help="返回图片数量")
    parser.add_argument("--size", default="1600x680", help="图片尺寸（宽x高）")

    args = parser.parse_args()

    # 搜索图片
    result = search_images(
        keyword=args.keyword,
        count=args.count,
        size=args.size
    )

    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 返回退出码
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
