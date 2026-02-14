#!/usr/bin/env python3
"""
多平台发布脚本
支持微信公众号、知乎、微博、掘金、CSDN、简书、头条号、B站专栏、雪球、大鱼号、小红书、X、WordPress等平台的内容发布

使用方法：
python publish.py --platform zhihu --title "标题" --content "内容" --cover-image "封面图URL" --tags "标签1,标签2"

注意：需要服务器为每个平台配置独立的发布接口
"""

import argparse
import json
import sys
import os


def publish_to_api(platform, title, content, cover_image=None, tags=None):
    """
    通过独立接口发布内容

    Args:
        platform: 平台标识（wechat/zhihu/weibo/juejin/csdn/jianshu/toutiao/bilibili/xueqiu/dayu/xiaohongshu/x/wordpress）
        title: 文章标题
        content: 文章内容
        cover_image: 封面图片URL
        tags: 标签列表

    Returns:
        dict: 发布结果
    """
    # 服务器基础URL
    base_url = "http://39.108.254.228:8002"

    # 各平台的独立接口路径
    platform_endpoints = {
        "wechat": "/publish-wechat",
        "zhihu": "/publish-zhihu",
        "weibo": "/publish-weibo",
        "juejin": "/publish-juejin",
        "csdn": "/publish-csdn",
        "jianshu": "/publish-jianshu",
        "toutiao": "/publish-toutiao",
        "bilibili": "/publish-bilibili",
        "xueqiu": "/publish-xueqiu",
        "dayu": "/publish-dayu",
        "xiaohongshu": "/publish-xiaohongshu",
        "x": "/publish-x",
        "wordpress": "/publish-wordpress"
    }

    # 微信使用特殊接口
    if platform == "wechat":
        endpoint = "/publish-draft"
    else:
        endpoint = platform_endpoints.get(platform)
        if not endpoint:
            return {
                "success": False,
                "message": f"不支持的平台: {platform}",
                "platform": platform
            }

    # 完整的API URL
    api_url = f"{base_url}{endpoint}"

    # 构建请求数据
    data = {
        "title": title,
        "content": content,
    }

    # 可选参数
    if cover_image:
        data["cover"] = cover_image
    if tags:
        data["digest"] = " ".join(tags)  # 使用digest字段传递摘要/标签

    # 使用curl命令（避免依赖问题）
    import subprocess

    try:
        # 构建curl命令
        curl_cmd = [
            "curl", "-X", "POST",
            api_url,
            "-H", "Content-Type: application/json",
            "-d", json.dumps(data),
            "--connect-timeout", "30",
            "--silent"
        ]

        # 执行命令
        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        # 检查返回
        if result.returncode == 0:
            response = json.loads(result.stdout)
            # 检查接口返回的success字段
            if response.get("success", False):
                return {
                    "success": True,
                    "message": "发布成功",
                    "platform": platform,
                    "data": response.get("data", {})
                }
            else:
                error = response.get("error", {})
                errmsg = error.get("errmsg", "未知错误")
                return {
                    "success": False,
                    "message": f"发布失败: {errmsg}",
                    "platform": platform,
                    "error": error
                }
        else:
            return {
                "success": False,
                "message": f"发布失败: {result.stderr}",
                "platform": platform
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "请求超时，请检查网络连接",
            "platform": platform
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "message": f"返回数据格式错误: {result.stdout}",
            "platform": platform
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"发布异常: {str(e)}",
            "platform": platform
        }


def publish(platform, title, content, cover_image=None, tags=None):
    """
    通用发布函数，支持多平台

    Args:
        platform: 平台名称（wechat/zhihu/weibo/juejin/csdn/jianshu/toutiao/bilibili/xueqiu/dayu/xiaohongshu/x/wordpress）
        title: 文章标题
        content: 文章内容
        cover_image: 封面图片URL
        tags: 标签列表

    Returns:
        dict: 发布结果
    """
    # 平台列表
    supported_platforms = [
        "wechat",      # 微信公众号
        "zhihu",       # 知乎
        "weibo",       # 微博
        "juejin",      # 掘金
        "csdn",        # CSDN
        "jianshu",     # 简书
        "toutiao",     # 头条号
        "bilibili",    # B站专栏
        "xueqiu",      # 雪球
        "dayu",        # 大鱼号
        "xiaohongshu", # 小红书
        "x",           # X (Twitter)
        "wordpress"    # WordPress
    ]

    # 检查平台是否支持
    if platform not in supported_platforms:
        return {
            "success": False,
            "message": f"不支持的平台: {platform}，支持的平台: {', '.join(supported_platforms)}"
        }

    # 调用独立接口
    return publish_to_api(platform, title, content, cover_image, tags)


def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="多平台发布脚本")
    parser.add_argument("--platform", required=True,
                        choices=["wechat", "zhihu", "weibo", "juejin", "csdn", "jianshu", "toutiao", "bilibili", "xueqiu", "dayu", "xiaohongshu", "x", "wordpress"],
                        help="发布平台")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--content", required=True, help="文章内容")
    parser.add_argument("--cover-image", help="封面图片URL")
    parser.add_argument("--tags", help="标签列表，用逗号分隔")

    args = parser.parse_args()

    # 解析标签
    tags = None
    if args.tags:
        tags = [tag.strip() for tag in args.tags.split(",")]

    # 发布内容
    result = publish(
        platform=args.platform,
        title=args.title,
        content=args.content,
        cover_image=args.cover_image,
        tags=tags
    )

    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 返回退出码
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
