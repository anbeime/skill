#!/usr/bin/env python3
"""
网页设计分析脚本

功能：
1. 读取用户上传的网页截图
2. 调用 OpenAI GPT-4 Vision API 分析图片
3. 提取设计系统（色彩、排版、组件风格）
4. 返回结构化 JSON 数据和 Coding Prompt

授权方式: ApiKey
凭证Key: COZE_OPENAI_VISION_API_<skill_id>
"""

import os
import sys
import json
import base64
import argparse
from pathlib import Path
from coze_workload_identity import requests
from PIL import Image


def encode_image_to_base64(image_path: str) -> str:
    """
    将图片文件编码为 base64 字符串

    Args:
        image_path: 图片文件路径

    Returns:
        base64 编码的字符串
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        raise ValueError(f"无法读取图片文件: {str(e)}")


def validate_image(image_path: str) -> None:
    """
    验证图片文件是否有效

    Args:
        image_path: 图片文件路径
    """
    try:
        with Image.open(image_path) as img:
            img.verify()
    except Exception as e:
        raise ValueError(f"图片文件无效或格式不支持: {str(e)}")


def call_openai_vision_api(
    api_key: str,
    image_base64: str,
    model: str = "gpt-4o"
) -> dict:
    """
    调用 OpenAI GPT-4 Vision API 分析图片

    Args:
        api_key: OpenAI API Key
        image_base64: base64 编码的图片
        model: 模型名称，默认 gpt-4o

    Returns:
        API 返回的响应数据
    """
    skill_id = "7597458179647111194"

    # 1. 获取凭证
    credential = os.getenv(f"COZE_OPENAI_VISION_API_{skill_id}")
    if not credential:
        raise ValueError(
            "缺少 OpenAI Vision API 凭证配置，请检查环境变量 COZE_OPENAI_VISION_API_<skill_id>"
        )

    # 2. 构建系统提示词
    system_prompt = """## Role
你是一位拥有10年经验的全球顶尖 UI/UX 设计师和前端工程师。你擅长通过视觉分析将网页设计解构为可复用的设计系统（Design System）。

## Goal
接收一张网页截图，提取其核心视觉语言，并将其转化为开发者可以直接使用的结构化数据和代码。

## Analysis Dimensions (请严格按照以下维度分析)

1.  **Vibe & Style (氛围与风格):**
    - 用3个关键词描述整体风格 (e.g., Swiss Style, Bento Grid, Neomorphism, Cyberpunk)。
    - 描述其情绪传达 (e.g., Trustworthy, Playful, Strict)。

2.  **Color Palette (色彩系统):**
    - 提取主色 (Primary)、辅助色 (Secondary)、背景色 (Background)、强调色 (Accent)。
    - **必须**提供准确的 Hex Code。
    - 建议最接近的 Tailwind CSS 颜色类名 (e.g., `slate-900`, `indigo-500`)。

3.  **Typography (排版系统):**
    - 识别字体类型 (Serif, Sans-serif, Monospace)。
    - 估算标题与正文的字重 (Font Weight) 和行高 (Line Height) 比例。

4.  **Component Styling (组件特征):**
    - 圆角 (Border Radius): 具体像素或 Tailwind 类 (e.g., `rounded-xl`).
    - 阴影/深度 (Shadow/Depth): 描述阴影层级。
    - 边框 (Border): 是否有边框，粗细及颜色。

## Output Format (输出格式)

请以 JSON 格式输出数据，随后提供一段可直接用于AI coding工具（如Cursor，Claude Code，Antigravity、TRAE）的"Prompt"。

### 1. JSON Data
{
  "style_name": "...",
  "colors": [{"role": "primary", "hex": "#...", "tailwind": "..."}],
  "typography": "...",
  "components": "..."
}

### 2. Coding Prompt (关键部分)
(请生成一段我可以直接粘贴到AI coding工具的提示词。这段提示词应指导AI coding工具使用上述提取的设计规范，生成一个类似风格的 Landing Page 组件。)

示例模板：
"Create a Hero section using Tailwind CSS. Use background color [HEX], text color [HEX]. The design style should be [STYLE NAME], featuring [COMPONENT FEATURES]. Font should feel like [FONT STYLE]..."

请确保 JSON 格式正确，并且 Coding Prompt 清晰可用。"""

    # 3. 构建请求
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {credential}"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请分析这张网页截图，提取其设计系统。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }

    # 4. 发起请求
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        # 5. 提取结果
        if "choices" not in data or len(data["choices"]) == 0:
            raise Exception("API 返回格式错误：缺少 choices 字段")

        content = data["choices"][0]["message"]["content"]
        return {
            "raw_content": content,
            "usage": data.get("usage", {})
        }

    except requests.exceptions.RequestException as e:
        raise Exception(f"API 调用失败: {str(e)}")


def parse_analysis_result(raw_content: str) -> dict:
    """
    解析 API 返回的分析结果，提取 JSON 和 Coding Prompt

    Args:
        raw_content: API 返回的原始内容

    Returns:
        包含 JSON 数据和 Coding Prompt 的字典
    """
    # 尝试提取 JSON 部分
    json_start = raw_content.find("```json")
    json_end = raw_content.find("```", json_start + 7)

    if json_start != -1 and json_end != -1:
        json_str = raw_content[json_start + 7:json_end].strip()
        try:
            design_data = json.loads(json_str)
        except json.JSONDecodeError:
            design_data = {"raw_json": json_str}
    else:
        # 尝试直接解析整个内容
        try:
            design_data = json.loads(raw_content)
        except json.JSONDecodeError:
            design_data = {"raw_content": raw_content}

    # 提取 Coding Prompt 部分
    prompt_start = raw_content.lower().find("coding prompt")
    if prompt_start != -1:
        coding_prompt = raw_content[prompt_start:].strip()
        # 移除可能的 markdown 标记
        coding_prompt = coding_prompt.replace("```", "").strip()
    else:
        coding_prompt = raw_content

    return {
        "design_data": design_data,
        "coding_prompt": coding_prompt,
        "full_content": raw_content
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="分析网页截图，提取设计系统",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="网页截图文件路径（支持 PNG、JPG、JPEG 等格式）"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="OpenAI 模型名称（默认: gpt-4o）"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径（可选，默认打印到标准输出）"
    )

    args = parser.parse_args()

    # 验证图片
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"错误：图片文件不存在: {args.image}", file=sys.stderr)
        sys.exit(1)

    validate_image(str(image_path))

    # 编码图片
    print(f"正在处理图片: {args.image}", file=sys.stderr)
    image_base64 = encode_image_to_base64(str(image_path))

    # 调用 API
    print(f"正在调用 OpenAI Vision API...", file=sys.stderr)
    api_response = call_openai_vision_api(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        image_base64=image_base64,
        model=args.model
    )

    # 解析结果
    print("正在解析分析结果...", file=sys.stderr)
    result = parse_analysis_result(api_response["raw_content"])

    # 输出结果
    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"结果已保存到: {args.output}", file=sys.stderr)
    else:
        print(output)

    # 输出 token 使用情况
    if api_response.get("usage"):
        print(f"\nToken 使用: {api_response['usage']}", file=sys.stderr)


if __name__ == "__main__":
    main()
