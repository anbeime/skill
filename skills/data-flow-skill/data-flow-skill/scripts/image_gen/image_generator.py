#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""命令行图片生成脚本。

该脚本只负责:
1. 接收已经写好的图片生成 prompt
2. 调用图像模型生成图片
3. 将图片和元数据保存到本地

不负责:
1. 根据任务内容猜测主题
2. 根据数据类型硬编码匹配场景
3. 自动编写主题插画 prompt

示例:
  python image_gen/image_generator.py generate \
    --prompt "简约动画风格，三位运动员站在领奖台上，背景留白，无文字" \
    --output output/figures/theme_illustration.png
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _load_env_key() -> str | None:
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == "DASHSCOPE_API_KEY":
                    return v.strip()
    return None


DASHSCOPE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
DEFAULT_MODEL = "qwen-image-2.0-pro"
DEFAULT_SIZE = "1328*1328"
DEFAULT_NEGATIVE_PROMPT = (
    "低分辨率，低画质，肢体畸形，手指错误，画面过饱和，文字，水印，logo，AI感过强，"
    "构图混乱，背景杂乱，模糊，重影，写实照片风，恐怖风。"
)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def parse_image_url(response_data: dict[str, Any]) -> str:
    try:
        return response_data["output"]["choices"][0]["message"]["content"][0]["image"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"未在接口响应中找到图片 URL: {response_data}") from exc


def request_image(
    prompt: str,
    api_key: str,
    *,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    prompt_extend: bool = True,
    watermark: bool = False,
    timeout: int = 300,
) -> str:
    payload = {
        "model": model,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ]
        },
        "parameters": {
            "negative_prompt": negative_prompt,
            "prompt_extend": prompt_extend,
            "watermark": watermark,
            "size": size,
        },
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        DASHSCOPE_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"图片生成请求失败: HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"图片生成请求失败: {exc.reason}") from exc
    return parse_image_url(data)


def download_image(url: str, output_path: Path, *, timeout: int = 300) -> None:
    ensure_parent(output_path)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            output_path.write_bytes(response.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(f"下载图片失败: {exc.reason}") from exc


def generate_image(
    prompt: str,
    output_path: str | Path,
    *,
    api_key=None,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    prompt_extend: bool = True,
    watermark: bool = False,
    timeout: int = 300,
) -> dict[str, Any]:
    resolved_key = api_key or os.getenv("DASHSCOPE_API_KEY") or _load_env_key()
    if not resolved_key:
        raise RuntimeError("缺少 DASHSCOPE_API_KEY，无法生成图片。")

    output = Path(output_path)
    image_url = request_image(
        prompt=prompt,
        api_key=resolved_key,
        model=model,
        size=size,
        negative_prompt=negative_prompt,
        prompt_extend=prompt_extend,
        watermark=watermark,
        timeout=timeout,
    )
    download_image(image_url, output, timeout=timeout)

    metadata = {
        "status": "success",
        "prompt": prompt,
        "model": model,
        "size": size,
        "image_url": image_url,
        "output_path": str(output.resolve()),
    }
    metadata_path = output.with_suffix(output.suffix + ".json")
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    metadata["metadata_path"] = str(metadata_path.resolve())
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="图片生成脚本")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="按给定 prompt 生成图片")
    generate_parser.add_argument("--prompt", required=True, help="图片生成 prompt")
    generate_parser.add_argument("--output", required=True, help="输出图片路径")
    generate_parser.add_argument("--size", default=DEFAULT_SIZE, help="图片尺寸，例如 1328*1328")
    generate_parser.add_argument("--model", default=DEFAULT_MODEL, help="模型名")
    generate_parser.add_argument("--api-key", default=None, help="可选，直接传入 API Key")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command != "generate":
            raise RuntimeError(f"不支持的命令: {args.command}")
        result = generate_image(
            prompt=args.prompt,
            output_path=args.output,
            api_key=args.api_key,
            model=args.model,
            size=args.size,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
