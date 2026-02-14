#!/usr/bin/env python3
"""
音频生成脚本
基于agentkit-samples多媒体用例，生成导购员语音和背景音乐
"""

import os
import requests
from typing import Optional, Dict, Any


class AudioGenerator:
    """音频生成器"""

    def __init__(self, api_key: str, api_url: str = "https://api.example.com/v1/audio/generations"):
        """
        初始化音频生成器

        Args:
            api_key: API密钥
            api_url: API地址
        """
        self.api_key = api_key
        self.api_url = api_url

    def generate_speech(
        self,
        text: str,
        voice: str = "xiaosheng_female",
        speed: float = 1.0,
        tone: str = "enthusiastic",
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成语音

        Args:
            text: 文本内容
            voice: 语音类型
            speed: 语速
            tone: 语气（enthusiastic/professional/calm等）
            **kwargs: 其他参数

        Returns:
            生成结果，包含音频URL或base64编码
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "text": text,
            "voice": voice,
            "speed": speed,
            "tone": tone,
            **kwargs
        }

        try:
            response = requests.post(
                f"{self.api_url}/speech",
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
            raise Exception(f"语音生成失败: {str(e)}")

    def generate_music(
        self,
        style: str = "upbeat_commercial",
        duration: int = 15,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成背景音乐

        Args:
            style: 音乐风格
            duration: 时长（秒）
            **kwargs: 其他参数

        Returns:
            生成结果，包含音频URL或base64编码
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "style": style,
            "duration": duration,
            **kwargs
        }

        try:
            response = requests.post(
                f"{self.api_url}/music",
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
            raise Exception(f"音乐生成失败: {str(e)}")


def generate_speech(
    api_key: str,
    text: str,
    voice: str = "xiaosheng_female",
    speed: float = 1.0,
    tone: str = "enthusiastic",
    output_path: str = "./output/speech.wav"
) -> str:
    """
    生成导购员语音

    Args:
        api_key: TTS API密钥
        text: 文本内容
        voice: 语音类型
        speed: 语速
        tone: 语气
        output_path: 输出路径

    Returns:
        输出文件路径
    """
    print(f"生成语音: {text[:50]}...")

    # 创建音频生成器
    generator = AudioGenerator(api_key=api_key)

    # 生成语音
    result = generator.generate_speech(
        text=text,
        voice=voice,
        speed=speed,
        tone=tone
    )

    # 保存音频
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if "audio_url" in result:
        # 从URL下载音频
        audio_response = requests.get(result["audio_url"], timeout=30)
        audio_response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(audio_response.content)

    elif "audio_base64" in result:
        # 从base64解码音频
        import base64
        audio_data = base64.b64decode(result["audio_base64"])

        with open(output_path, "wb") as f:
            f.write(audio_data)

    else:
        raise Exception("未找到音频数据")

    print(f"语音已保存至: {output_path}")
    return output_path


def generate_music(
    api_key: str,
    style: str = "upbeat_commercial",
    duration: int = 15,
    output_path: str = "./output/music.wav"
) -> str:
    """
    生成背景音乐

    Args:
        api_key: 音乐生成API密钥
        style: 音乐风格
        duration: 时长（秒）
        output_path: 输出路径

    Returns:
        输出文件路径
    """
    print(f"生成背景音乐: {style}, 时长{duration}秒")

    # 创建音频生成器
    generator = AudioGenerator(api_key=api_key)

    # 生成音乐
    result = generator.generate_music(
        style=style,
        duration=duration
    )

    # 保存音频
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if "audio_url" in result:
        # 从URL下载音频
        audio_response = requests.get(result["audio_url"], timeout=30)
        audio_response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(audio_response.content)

    elif "audio_base64" in result:
        # 从base64解码音频
        import base64
        audio_data = base64.b64decode(result["audio_base64"])

        with open(output_path, "wb") as f:
            f.write(audio_data)

    else:
        raise Exception("未找到音频数据")

    print(f"背景音乐已保存至: {output_path}")
    return output_path


def mix_audio(
    speech_path: str,
    music_path: str,
    speech_volume: float = 0.8,
    music_volume: float = 0.2,
    output_path: str = "./output/audio.wav"
) -> str:
    """
    合成音频（语音+背景音乐）

    Args:
        speech_path: 语音文件路径
        music_path: 背景音乐文件路径
        speech_volume: 语音音量
        music_volume: 背景音乐音量
        output_path: 输出路径

    Returns:
        输出文件路径

    注意：此函数需要安装pydub库
    pip install pydub
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        raise Exception("需要安装pydub库: pip install pydub")

    print(f"合成音频: {speech_path} + {music_path}")

    # 加载音频
    speech = AudioSegment.from_file(speech_path)
    music = AudioSegment.from_file(music_path)

    # 调整音量
    speech = speech + (speech_volume - 1.0) * 20  # 转换为dB
    music = music + (music_volume - 1.0) * 20

    # 延伸背景音乐以匹配语音长度
    if len(music) < len(speech):
        # 循环背景音乐
        music = music * (len(speech) // len(music) + 1)
    music = music[:len(speech)]

    # 混合音频
    mixed = speech.overlay(music)

    # 保存音频
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    mixed.export(output_path, format="wav")

    print(f"合成音频已保存至: {output_path}")
    return output_path


def main():
    """主函数（测试用）"""
    import argparse

    parser = argparse.ArgumentParser(description="音频生成脚本")
    parser.add_argument("--api-key", type=str, required=True, help="API密钥")
    parser.add_argument("--type", type=str, choices=["speech", "music", "mix"], required=True, help="生成类型")
    parser.add_argument("--text", type=str, help="文本内容（仅speech类型需要）")
    parser.add_argument("--voice", type=str, default="xiaosheng_female", help="语音类型")
    parser.add_argument("--speed", type=float, default=1.0, help="语速")
    parser.add_argument("--tone", type=str, default="enthusiastic", help="语气")
    parser.add_argument("--style", type=str, default="upbeat_commercial", help="音乐风格")
    parser.add_argument("--duration", type=int, default=15, help="时长（仅music类型需要）")
    parser.add_argument("--speech-path", type=str, help="语音文件路径（仅mix类型需要）")
    parser.add_argument("--music-path", type=str, help="音乐文件路径（仅mix类型需要）")
    parser.add_argument("--speech-volume", type=float, default=0.8, help="语音音量（仅mix类型需要）")
    parser.add_argument("--music-volume", type=float, default=0.2, help="音乐音量（仅mix类型需要）")
    parser.add_argument("--output", type=str, default="./output/audio.wav", help="输出路径")

    args = parser.parse_args()

    if args.type == "speech":
        generate_speech(
            api_key=args.api_key,
            text=args.text,
            voice=args.voice,
            speed=args.speed,
            tone=args.tone,
            output_path=args.output
        )
    elif args.type == "music":
        generate_music(
            api_key=args.api_key,
            style=args.style,
            duration=args.duration,
            output_path=args.output
        )
    else:
        mix_audio(
            speech_path=args.speech_path,
            music_path=args.music_path,
            speech_volume=args.speech_volume,
            music_volume=args.music_volume,
            output_path=args.output
        )


if __name__ == "__main__":
    main()
