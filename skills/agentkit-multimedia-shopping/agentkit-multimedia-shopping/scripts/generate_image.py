#!/usr/bin/env python3
"""
图像生成脚本
基于agentkit-samples多媒体用例，生成数字人形象和场景背景
"""

import os
import requests
from typing import Optional, Dict, Any


class ImageGenerator:
    """图像生成器"""

    def __init__(self, api_key: str, api_url: str = "https://api.example.com/v1/images/generations"):
        """
        初始化图像生成器

        Args:
            api_key: API密钥
            api_url: API地址
        """
        self.api_key = api_key
        self.api_url = api_url

    def generate(
        self,
        prompt: str,
        style: str = "realistic",
        resolution: str = "1024x1024",
        num_images: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成图像

        Args:
            prompt: 图像描述
            style: 图像风格（realistic/cartoon/artistic等）
            resolution: 图像分辨率
            num_images: 生成图像数量
            **kwargs: 其他参数

        Returns:
            生成结果，包含图像URL或base64编码
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "style": style,
            "resolution": resolution,
            "num_images": num_images,
            **kwargs
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            # 检查是否有错误
            if "error" in data:
                raise Exception(f"API错误: {data['error']}")

            return data

        except requests.exceptions.RequestException as e:
            raise Exception(f"图像生成失败: {str(e)}")


def generate_avatar(
    api_key: str,
    description: str,
    style: str = "realistic",
    output_path: str = "./output/avatar.png",
    resolution: str = "1024x1024"
) -> str:
    """
    生成数字人形象

    Args:
        api_key: 图像生成API密钥
        description: 角色描述
        style: 图像风格
        output_path: 输出路径
        resolution: 图像分辨率

    Returns:
        输出文件路径
    """
    # 小省导购员固定描述
    base_description = """25岁女性数字人，鹅蛋脸、杏眼带笑、浅棕色齐肩卷发，肤色白皙，唇色淡粉，
身穿浅灰色修身西装套裙，内搭白色衬衫，脚踩米色细跟鞋，佩戴银色简约项链，
气质专业又亲和，手部姿态优雅自然。"""

    # 组合描述
    full_prompt = f"{base_description}\n{description}"

    print(f"生成数字人形象: {full_prompt[:100]}...")

    # 创建图像生成器
    generator = ImageGenerator(api_key=api_key)

    # 生成图像
    result = generator.generate(
        prompt=full_prompt,
        style=style,
        resolution=resolution
    )

    # 保存图像
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if "image_url" in result:
        # 从URL下载图像
        image_response = requests.get(result["image_url"], timeout=30)
        image_response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(image_response.content)

    elif "image_base64" in result:
        # 从base64解码图像
        import base64
        image_data = base64.b64decode(result["image_base64"])

        with open(output_path, "wb") as f:
            f.write(image_data)

    else:
        raise Exception("未找到图像数据")

    print(f"数字人形象已保存至: {output_path}")
    return output_path


def generate_background(
    api_key: str,
    description: str,
    style: str = "professional",
    output_path: str = "./output/background.png",
    resolution: str = "1920x1080"
) -> str:
    """
    生成场景背景

    Args:
        api_key: 图像生成API密钥
        description: 场景描述
        style: 图像风格
        output_path: 输出路径
        resolution: 图像分辨率

    Returns:
        输出文件路径
    """
    print(f"生成场景背景: {description[:100]}...")

    # 创建图像生成器
    generator = ImageGenerator(api_key=api_key)

    # 生成图像
    result = generator.generate(
        prompt=description,
        style=style,
        resolution=resolution
    )

    # 保存图像
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if "image_url" in result:
        # 从URL下载图像
        image_response = requests.get(result["image_url"], timeout=30)
        image_response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(image_response.content)

    elif "image_base64" in result:
        # 从base64解码图像
        import base64
        image_data = base64.b64decode(result["image_base64"])

        with open(output_path, "wb") as f:
            f.write(image_data)

    else:
        raise Exception("未找到图像数据")

    print(f"场景背景已保存至: {output_path}")
    return output_path


def main():
    """主函数（测试用）"""
    import argparse

    parser = argparse.ArgumentParser(description="图像生成脚本")
    parser.add_argument("--api-key", type=str, required=True, help="API密钥")
    parser.add_argument("--type", type=str, choices=["avatar", "background"], required=True, help="生成类型")
    parser.add_argument("--description", type=str, required=True, help="描述")
    parser.add_argument("--style", type=str, default="realistic", help="图像风格")
    parser.add_argument("--output", type=str, default="./output/image.png", help="输出路径")
    parser.add_argument("--resolution", type=str, default="1024x1024", help="图像分辨率")

    args = parser.parse_args()

    if args.type == "avatar":
        generate_avatar(
            api_key=args.api_key,
            description=args.description,
            style=args.style,
            output_path=args.output,
            resolution=args.resolution
        )
    else:
        generate_background(
            api_key=args.api_key,
            description=args.description,
            style=args.style,
            output_path=args.output,
            resolution=args.resolution
        )


if __name__ == "__main__":
    main()
