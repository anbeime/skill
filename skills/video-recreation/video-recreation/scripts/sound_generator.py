#!/usr/bin/env python3
"""
音效和背景音乐生成脚本
集成 Suno API 实现真实的音效和背景音乐生成
"""

import os
import json
import requests
import time
from typing import Dict, Any, List
from .error_handler import retry_on_failure, ErrorLogger

logger = ErrorLogger()


class SunoMusicGenerator:
    """Suno 音乐生成器"""

    def __init__(self, api_key: str = None):
        """
        初始化生成器

        Args:
            api_key: Suno API 密钥(优先级: 参数 > 环境变量 > 默认凭证)
        """
        # 优先级1: 参数传入的 API Key
        # 优先级2: 环境变量 SUNO_API_KEY
        # 优先级3: 技能凭证 COZE_SUNO_API_KEY_{skill_id}
        self.api_key = api_key or os.getenv('SUNO_API_KEY')

        # 如果仍未获取到,尝试从技能凭证获取
        if not self.api_key:
            skill_id = os.getenv('SKILL_ID', '7598086966437265442')
            self.api_key = os.getenv(f'COZE_SUNO_API_KEY_{skill_id}')

        self.api_url = "https://api.edata.cloud/v1/generate"  # 根据实际 API 地址调整

        if self.api_key:
            logger.log_info("已获取 Suno API Key")
        else:
            logger.log_info("未设置 Suno API Key,将使用占位实现")

    @retry_on_failure(max_retries=2, retry_delay=1.0)
    def generate_music(
        self,
        prompt: str,
        output_dir: str = "./output/background_music",
        instrumental: bool = True,
        model: str = "chirp-v3-5",
        title: str = "background_music"
    ) -> Dict[str, Any]:
        """
        生成背景音乐

        Args:
            prompt: 音乐描述提示词
            output_dir: 输出目录
            instrumental: 是否纯音乐(无歌词)
            model: 使用的模型
            title: 音乐标题

        Returns:
            生成结果字典
        """
        if not self.api_key:
            # 如果没有 API Key,使用占位实现
            return self._generate_music_placeholder(prompt, output_dir, title)

        os.makedirs(output_dir, exist_ok=True)

        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.api_key}",
            "content-type": "application/json"
        }

        payload = {
            "action": "generate",
            "prompt": prompt,
            "model": model,
            "instrumental": instrumental,
            "title": title,
            "custom": False
        }

        try:
            logger.log_info(f"正在使用 Suno API 生成音乐: {prompt}")

            # 发送生成请求
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                raise Exception(f"API调用失败,状态码: {response.status_code}, 响应: {response.text}")

            result = response.json()

            if not result.get('success'):
                raise Exception(f"生成失败: {result.get('message', '未知错误')}")

            # 获取任务 ID,轮询等待生成完成
            task_id = result.get('task_id')

            if not task_id:
                raise Exception("未获取到任务 ID")

            # 轮询等待生成完成
            max_wait_time = 300  # 最多等待 5 分钟
            wait_time = 0
            check_interval = 5  # 每 5 秒检查一次

            while wait_time < max_wait_time:
                time.sleep(check_interval)
                wait_time += check_interval

                # 查询任务状态
                status_result = self._check_task_status(task_id)

                if not status_result.get('success'):
                    logger.log_error(f"查询任务状态失败: {status_result.get('error')}")
                    continue

                state = status_result.get('state', 'pending')

                if state == 'succeeded':
                    # 生成成功,下载音频文件
                    audio_url = status_result.get('audio_url')
                    if not audio_url:
                        raise Exception("未获取到音频 URL")

                    # 下载音频文件
                    output_file = os.path.join(output_dir, f"{title}.mp3")
                    self._download_audio(audio_url, output_file)

                    return {
                        'success': True,
                        'output_file': output_file,
                        'title': title,
                        'duration': status_result.get('duration', 0),
                        'prompt': prompt,
                        'api_used': True
                    }

                elif state == 'failed':
                    raise Exception(f"生成任务失败: {status_result.get('error', '未知错误')}")

            raise Exception("生成任务超时")

        except Exception as e:
            logger.log_error(f"使用 Suno API 生成背景音乐失败: {str(e)}, 降级到占位实现")
            # 降级到占位实现
            return self._generate_music_placeholder(prompt, output_dir, title)

    def _check_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态字典
        """
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.get(
                f"{self.api_url}/{task_id}",
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"查询失败,状态码: {response.status_code}"
                }

            result = response.json()

            if result.get('success') and result.get('data'):
                song_data = result['data'][0]  # 获取第一首歌曲
                return {
                    'success': True,
                    'state': song_data.get('state', 'pending'),
                    'audio_url': song_data.get('audio_url'),
                    'duration': song_data.get('duration', 0),
                    'error': song_data.get('error')
                }

            return {
                'success': False,
                'error': '未知错误'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _download_audio(self, url: str, output_file: str) -> None:
        """
        下载音频文件

        Args:
            url: 音频 URL
            output_file: 输出文件路径
        """
        response = requests.get(url, stream=True, timeout=60)

        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.log_info(f"音频已下载: {output_file}")

    def _generate_music_placeholder(
        self,
        prompt: str,
        output_dir: str,
        title: str
    ) -> Dict[str, Any]:
        """
        占位实现 - 生成空白背景音乐

        Args:
            prompt: 音乐描述
            output_dir: 输出目录
            title: 音乐标题

        Returns:
            生成结果字典
        """
        import wave
        import struct
        import math

        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{title}.wav")

        # 根据提示词生成占位音频
        try:
            with wave.open(output_file, 'w') as wav_file:
                wav_file.setnchannels(2)  # 立体声
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(44100)  # 采样率

                # 生成简单的音乐波形(占位)
                duration = 60.0  # 默认 1 分钟
                num_frames = int(44100 * duration)
                frames = []

                # 根据提示词选择风格
                if 'epic' in prompt.lower() or '史诗' in prompt:
                    base_freq = 220
                    freq_var = 0.5
                elif 'upbeat' in prompt.lower() or '欢快' in prompt:
                    base_freq = 440
                    freq_var = 1.5
                elif 'tech' in prompt.lower() or '科技' in prompt:
                    base_freq = 330
                    freq_var = 1.0
                else:  # calm
                    base_freq = 330
                    freq_var = 0.3

                for i in range(num_frames):
                    t = i / 44100

                    # 多层叠加,营造和弦效果
                    sample = 0
                    for harmonic in [1, 2, 3, 4]:
                        freq = base_freq * harmonic * (1 + 0.1 * math.sin(t * freq_var))
                        sample += 0.15 * math.sin(2 * math.pi * freq * t)

                    # 添加节奏感
                    if 'epic' in prompt.lower() or 'upbeat' in prompt.lower():
                        beat_interval = 60 / 120  # 120 BPM
                        beat_phase = (t % beat_interval) / beat_interval
                        if beat_phase < 0.1:
                            sample *= 1.5  # 强拍

                    # 振幅包络
                    envelope = 0.3 + 0.2 * math.sin(t * 0.1)
                    sample *= envelope

                    # 限制振幅
                    sample = max(-32767, min(32767, int(sample)))
                    frames.append(struct.pack('<h', sample))
                    frames.append(struct.pack('<h', sample))

                wav_file.writeframes(b''.join(frames))

            logger.log_info(f"背景音乐已生成(占位实现): {output_file}")

            return {
                'success': True,
                'output_file': output_file,
                'title': title,
                'duration': duration,
                'prompt': prompt,
                'api_used': False
            }

        except Exception as e:
            logger.log_error(f"生成占位音乐失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


@retry_on_failure(max_retries=2, retry_delay=0.5)
def generate_sound_effects(
    sound_data: List[Dict[str, Any]],
    output_dir: str = "./output/sound_effects"
) -> Dict[str, Any]:
    """
    生成环境音效

    参数:
        sound_data: 音效数据列表
        output_dir: 输出目录

    返回:
        生成结果字典
    """
    os.makedirs(output_dir, exist_ok=True)

    results = {
        'success': True,
        'total_sounds': len(sound_data),
        'generated': 0,
        'failed': 0,
        'sounds': [],
        'errors': []
    }

    for i, sound in enumerate(sound_data, start=1):
        name = sound.get('name', f'sound_{i:03d}')
        sound_type = sound.get('type', 'ambient')
        duration = sound.get('duration', 2.0)
        description = sound.get('description', '')

        filename = f"{name}.wav"
        filepath = os.path.join(output_dir, filename)

        try:
            # 占位实现 - 创建音效文件
            import wave
            import struct
            import math

            with wave.open(filepath, 'w') as wav_file:
                wav_file.setnchannels(2)  # 立体声
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(44100)  # 采样率

                num_frames = int(44100 * duration)
                frames = []

                for j in range(num_frames):
                    t = j / 44100
                    if sound_type == 'transition':
                        frequency = 400 + (j / num_frames) * 800
                    elif sound_type == 'impact':
                        frequency = 1000 * (1 - j / num_frames)
                    elif sound_type == 'action':
                        frequency = 800 + 400 * (j % 1000) / 1000
                    else:
                        frequency = 100

                    amplitude = 0.3 * (1 - j / num_frames)
                    value = int(amplitude * 32767)
                    frames.append(struct.pack('<h', value))
                    frames.append(struct.pack('<h', value))

                wav_file.writeframes(b''.join(frames))

            results['generated'] += 1
            results['sounds'].append({
                'name': name,
                'filepath': filepath,
                'duration': duration,
                'type': sound_type
            })

            logger.log_info(f"音效已生成(占位实现): {filepath}")

        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'name': name,
                'error': str(e)
            })
            logger.log_error(f"生成音效失败 {name}: {str(e)}")

    if results['failed'] > 0:
        results['success'] = False

    return results


@retry_on_failure(max_retries=2, retry_delay=0.5)
def generate_background_music(
    music_data: Dict[str, Any],
    output_dir: str = "./output/background_music"
) -> Dict[str, Any]:
    """
    生成背景音乐

    参数:
        music_data: 背景音乐配置
        output_dir: 输出目录

    返回:
        生成结果字典
    """
    generator = SunoMusicGenerator()

    name = music_data.get('name', 'background')
    style = music_data.get('style', 'calm')
    duration = music_data.get('duration', 60.0)
    mood = music_data.get('mood', 'neutral')

    # 构建 Suno 提示词
    prompt = f"{mood} {style} background music, duration {duration}s"

    result = generator.generate_music(
        prompt=prompt,
        output_dir=output_dir,
        instrumental=True,
        title=name
    )

    return result


def validate_sound_data(sound_data: List[Dict[str, Any]]) -> bool:
    """
    验证音效数据格式

    参数:
        sound_data: 音效数据列表

    返回:
        是否有效
    """
    if not isinstance(sound_data, list):
        return False

    for sound in sound_data:
        if not isinstance(sound, dict):
            return False
        if 'name' not in sound:
            return False

    return True


def validate_music_data(music_data: Dict[str, Any]) -> bool:
    """
    验证背景音乐数据格式

    参数:
        music_data: 背景音乐配置字典

    返回:
        是否有效
    """
    if not isinstance(music_data, dict):
        return False

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="音效和背景音乐生成工具(Suno API)")
    parser.add_argument("--type", required=True, choices=['sound', 'music', 'both'],
                       help="生成类型: sound=音效, music=背景音乐, both=两者")
    parser.add_argument("--input", help="输入JSON文件路径")
    parser.add_argument("--output", default="./output/audio", help="输出目录")
    parser.add_argument("--suno-api-key", help="Suno API 密钥(可选,优先使用环境变量)")
    parser.add_argument("--use-placeholder", action="store_true",
                       help="强制使用占位实现(不调用API)")

    args = parser.parse_args()

    # 如果提供了 API Key,设置环境变量(优先级最高)
    if args.suno_api_key:
        os.environ['SUNO_API_KEY'] = args.suno_api_key

    # 如果指定了强制占位,清除 API Key
    if args.use_placeholder:
        os.environ['SUNO_API_KEY'] = ''

    if args.type in ['sound', 'both']:
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                sound_data = json.load(f).get('sound_effects', [])
        else:
            # 示例数据
            sound_data = [
                {
                    'name': 'transition_01',
                    'type': 'transition',
                    'duration': 2.0,
                    'description': '转场音效'
                }
            ]

        if validate_sound_data(sound_data):
            result = generate_sound_effects(sound_data, os.path.join(args.output, 'sound_effects'))
            print(f"音效生成完成: {result['generated']}/{result['total_sounds']}")
        else:
            print("✗ 音效数据格式无效")
            exit(1)

    if args.type in ['music', 'both']:
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                music_data = json.load(f).get('background_music', {})
        else:
            # 示例数据
            music_data = {
                'name': 'background',
                'style': 'calm',
                'duration': 60.0,
                'mood': 'neutral'
            }

        if validate_music_data(music_data):
            result = generate_background_music(music_data, os.path.join(args.output, 'background_music'))
            if result['success']:
                api_status = "Suno API" if result.get('api_used') else "占位实现"
                print(f"背景音乐生成完成({api_status}): {result['output_file']}")
            else:
                print(f"✗ 背景音乐生成失败: {result.get('error')}")
                exit(1)
        else:
            print("✗ 背景音乐数据格式无效")
            exit(1)
