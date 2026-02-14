#!/usr/bin/env python3
"""
COZE视频大模型API封装脚本
功能：素材上传、视频合成、状态轮询、成品下载
授权方式：ApiKey
凭证Key：COZE_COZE_VIDEO_API_7598017404148613135
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

# 使用coze-workload_identity的requests，禁止使用标准库requests
from coze_workload_identity import requests

# 配置常量
SKILL_ID = "7598017404148613135"
API_BASE_URL = "https://api.coze.cn/v1"
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2


class CozeVideoAPIError(Exception):
    """COZE视频API异常"""
    pass


class CozeVideoAPI:
    """COZE视频大模型API客户端"""

    def __init__(self):
        """初始化API客户端"""
        self.api_key = os.getenv(f"COZE_COZE_VIDEO_API_{SKILL_ID}")
        if not self.api_key:
            raise CozeVideoAPIError(
                f"缺少COZE视频API凭证，请检查环境变量 COZE_COZE_VIDEO_API_{SKILL_ID}"
            )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        retries: int = MAX_RETRIES
    ) -> Dict:
        """
        发起HTTP请求

        Args:
            method: HTTP方法 (GET/POST)
            endpoint: API端点
            data: 请求体数据
            files: 上传文件
            retries: 重试次数

        Returns:
            响应JSON数据
        """
        url = f"{API_BASE_URL}{endpoint}"

        for attempt in range(retries):
            try:
                if method.upper() == "GET":
                    response = requests.get(url, headers=self.headers, params=data, timeout=TIMEOUT)
                elif method.upper() == "POST":
                    if files:
                        # 文件上传，不使用Content-Type: application/json
                        headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                        response = requests.post(url, headers=headers, data=data, files=files, timeout=TIMEOUT)
                    else:
                        response = requests.post(url, headers=self.headers, json=data, timeout=TIMEOUT)
                else:
                    raise CozeVideoAPIError(f"不支持的HTTP方法: {method}")

                response.raise_for_status()
                result = response.json()

                # 错误处理
                if result.get("code") != 0:
                    error_msg = result.get("message", "未知错误")
                    raise CozeVideoAPIError(f"API错误[{result.get('code')}]: {error_msg}")

                return result.get("data", {})

            except requests.exceptions.Timeout:
                if attempt < retries - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                raise CozeVideoAPIError(f"请求超时（已重试{retries}次）")

            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                raise CozeVideoAPIError(f"API调用失败: {str(e)}")

        raise CozeVideoAPIError(f"请求失败（已重试{retries}次）")

    def upload_image(self, image_path: str) -> str:
        """
        上传图片素材

        Args:
            image_path: 图片文件路径（JPG/PNG格式）

        Returns:
            素材ID

        Raises:
            CozeVideoAPIError: 上传失败
        """
        # 验证文件存在
        if not os.path.exists(image_path):
            raise CozeVideoAPIError(f"图片文件不存在: {image_path}")

        # 验证文件格式
        valid_formats = ['.jpg', '.jpeg', '.png']
        if not any(image_path.lower().endswith(fmt) for fmt in valid_formats):
            raise CozeVideoAPIError(f"图片格式不支持，仅支持JPG/PNG: {image_path}")

        # 准备文件上传
        filename = os.path.basename(image_path)
        with open(image_path, 'rb') as f:
            files = {"file": (filename, f, "image/jpeg")}
            result = self._request("POST", "/material/upload", files=files)

        material_id = result.get("material_id")
        if not material_id:
            raise CozeVideoAPIError("上传成功但未返回素材ID")

        print(f"✓ 图片上传成功: {filename} -> {material_id}")
        return material_id

    def upload_audio(self, audio_path: str) -> str:
        """
        上传音频素材

        Args:
            audio_path: 音频文件路径（MP3格式）

        Returns:
            素材ID

        Raises:
            CozeVideoAPIError: 上传失败
        """
        # 验证文件存在
        if not os.path.exists(audio_path):
            raise CozeVideoAPIError(f"音频文件不存在: {audio_path}")

        # 验证文件格式
        if not audio_path.lower().endswith('.mp3'):
            raise CozeVideoAPIError(f"音频格式不支持，仅支持MP3: {audio_path}")

        # 准备文件上传
        filename = os.path.basename(audio_path)
        with open(audio_path, 'rb') as f:
            files = {"file": (filename, f, "audio/mpeg")}
            result = self._request("POST", "/material/upload", files=files)

        material_id = result.get("material_id")
        if not material_id:
            raise CozeVideoAPIError("上传成功但未返回素材ID")

        print(f"✓ 音频上传成功: {filename} -> {material_id}")
        return material_id

    def create_video_task(
        self,
        image_ids: List[str],
        audio_ids: List[str],
        subtitle_config: Dict,
        duration: int = 15,
        resolution: str = "1080P",
        aspect_ratio: str = "9:16",
        transition: str = "fade"
    ) -> str:
        """
        创建视频合成任务

        Args:
            image_ids: 图片素材ID列表（按镜头顺序）
            audio_ids: 音频素材ID列表
            subtitle_config: 字幕配置（符合COZE API字幕参数包格式）
            duration: 视频总时长（秒）
            resolution: 分辨率（1080P/720P）
            aspect_ratio: 画面比例（9:16/16:9）
            transition: 转场类型（fade/none）

        Returns:
            任务ID

        Raises:
            CozeVideoAPIError: 任务创建失败
        """
        # 构建请求参数
        payload = {
            "duration": duration,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "transition": {
                "type": transition,
                "duration": 0.2 if transition == "fade" else 0
            },
            "materials": {
                "images": [{"material_id": img_id} for img_id in image_ids],
                "audios": [{"material_id": audio_id} for audio_id in audio_ids]
            },
            "subtitles": subtitle_config,
            "sync_mode": "precise",  # 音画精准同步
            "quality": {
                "denoise": True,  # 高清降噪
                "sharpen": "low"  # 轻微锐化
            }
        }

        result = self._request("POST", "/video/create", data=payload)

        task_id = result.get("task_id")
        if not task_id:
            raise CozeVideoAPIError("任务创建成功但未返回任务ID")

        print(f"✓ 视频合成任务创建成功: {task_id}")
        return task_id

    def poll_task_status(self, task_id: str, timeout: int = 180) -> Dict:
        """
        轮询任务状态

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            任务结果（包含视频下载链接）

        Raises:
            CozeVideoAPIError: 任务超时或失败
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self._request("GET", f"/video/status", data={"task_id": task_id})

            status = result.get("status")
            print(f"  任务状态: {status}")

            if status == "completed":
                print(f"✓ 视频合成完成")
                return result

            elif status == "failed":
                error_msg = result.get("error", "未知错误")
                raise CozeVideoAPIError(f"视频合成失败: {error_msg}")

            elif status == "processing":
                # 继续轮询
                time.sleep(2)

            else:
                raise CozeVideoAPIError(f"未知任务状态: {status}")

        raise CozeVideoAPIError(f"任务超时（{timeout}秒）")

    def download_video(self, download_url: str, output_path: str) -> str:
        """
        下载成品视频

        Args:
            download_url: 视频下载链接
            output_path: 输出文件路径（MP4格式）

        Returns:
            本地文件路径

        Raises:
            CozeVideoAPIError: 下载失败
        """
        try:
            response = requests.get(download_url, stream=True, timeout=TIMEOUT)
            response.raise_for_status()

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"✓ 视频下载成功: {output_path}")
            return output_path

        except Exception as e:
            raise CozeVideoAPIError(f"视频下载失败: {str(e)}")

    def batch_create_video(
        self,
        image_paths: List[str],
        audio_paths: List[str],
        subtitle_config: Dict,
        output_path: str,
        **kwargs
    ) -> str:
        """
        批量上传素材并创建视频（一站式接口）

        Args:
            image_paths: 图片文件路径列表
            audio_paths: 音频文件路径列表
            subtitle_config: 字幕配置
            output_path: 成品视频输出路径
            **kwargs: 其他视频参数（duration, resolution, aspect_ratio等）

        Returns:
            成品视频本地路径

        Raises:
            CozeVideoAPIError: 任何环节失败
        """
        print("=== COZE视频API批量合成流程 ===")

        # 1. 批量上传图片
        print(f"\n1. 上传图片素材（共{len(image_paths)}张）")
        image_ids = []
        for img_path in image_paths:
            material_id = self.upload_image(img_path)
            image_ids.append(material_id)

        # 2. 批量上传音频
        print(f"\n2. 上传音频素材（共{len(audio_paths)}个）")
        audio_ids = []
        for audio_path in audio_paths:
            material_id = self.upload_audio(audio_path)
            audio_ids.append(material_id)

        # 3. 创建视频合成任务
        print(f"\n3. 创建视频合成任务")
        task_id = self.create_video_task(
            image_ids=image_ids,
            audio_ids=audio_ids,
            subtitle_config=subtitle_config,
            **kwargs
        )

        # 4. 轮询任务状态
        print(f"\n4. 轮询任务状态")
        task_result = self.poll_task_status(task_id)

        # 5. 下载成品视频
        print(f"\n5. 下载成品视频")
        download_url = task_result.get("download_url")
        if not download_url:
            raise CozeVideoAPIError("任务完成但未提供下载链接")

        local_path = self.download_video(download_url, output_path)

        print(f"\n=== 合成完成: {local_path} ===")
        return local_path


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="COZE视频API工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # 上传素材命令
    upload_parser = subparsers.add_parser("upload", help="上传素材")
    upload_parser.add_argument("--type", required=True, choices=["image", "audio"], help="素材类型")
    upload_parser.add_argument("--path", required=True, help="文件路径")

    # 创建视频命令
    video_parser = subparsers.add_parser("create", help="创建视频")
    video_parser.add_argument("--images", required=True, nargs="+", help="图片路径列表")
    video_parser.add_argument("--audios", required=True, nargs="+", help="音频路径列表")
    video_parser.add_argument("--subtitles", required=True, help="字幕配置JSON文件路径")
    video_parser.add_argument("--output", required=True, help="输出视频路径")
    video_parser.add_argument("--duration", type=int, default=15, help="视频时长（秒）")
    video_parser.add_argument("--resolution", default="1080P", help="分辨率")
    video_parser.add_argument("--ratio", default="9:16", help="画面比例")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        api = CozeVideoAPI()

        if args.command == "upload":
            if args.type == "image":
                api.upload_image(args.path)
            else:
                api.upload_audio(args.path)

        elif args.command == "create":
            # 读取字幕配置
            with open(args.subtitles, 'r', encoding='utf-8') as f:
                subtitle_config = json.load(f)

            api.batch_create_video(
                image_paths=args.images,
                audio_paths=args.audios,
                subtitle_config=subtitle_config,
                output_path=args.output,
                duration=args.duration,
                resolution=args.resolution,
                aspect_ratio=args.ratio
            )

    except CozeVideoAPIError as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
