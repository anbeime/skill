#!/usr/bin/env python3
"""
Qwen3-ASR 语音转文字脚本

本脚本基于 Qwen3-ASR 模型，提供以下核心能力：
- 实时语音识别（语音转文字）
- 多语言支持（中文、英文等）
- 多种音频格式支持
- 时间戳输出（可选）
- 高精度识别

授权方式：ApiKey（需要用户提供 Qwen3-ASR 的 API 凭证）
凭证Key：COZE_QWEN3ASR_API_7598467069021093924
"""

import os
import sys
import argparse
import json
import time
from typing import Optional, List, Any
from coze_workload_identity import requests


class Qwen3ASRTranscriber:
    """Qwen3-ASR 语音转文字识别器"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化 ASR 识别器
        
        Args:
            api_key: Qwen3-ASR API 密钥（如果为 None，则从环境变量读取）
            base_url: Qwen3-ASR API 基础 URL（如果为 None，使用默认值）
        """
        self.skill_id = "7598467069021093924"
        self.api_key = api_key or os.getenv(f"COZE_QWEN3ASR_API_{self.skill_id}")
        
        if not self.api_key:
            raise ValueError(
                "未找到 Qwen3-ASR API 凭证。请设置环境变量或通过参数提供 API 密钥。\n"
                "凭证Key格式：COZE_QWEN3ASR_API_7598467069021093924"
            )
        
        # Qwen3-ASR API 地址
        self.base_url = base_url or os.getenv(
            "QWEN3ASR_BASE_URL",
            "https://api.qwenlm.com/v1/asr"
        )
    
    def transcribe(
        self,
        audio_file: str,
        language: str = "zh-CN",
        format: str = "wav",
        sample_rate: int = 16000,
        return_timestamps: bool = False,
        task: str = "transcribe"
    ) -> dict:
        """
        语音转文字
        
        Args:
            audio_file: 音频文件路径
            language: 语言代码（zh-CN/en-US/ja-JP/ko-KR 等）
            format: 音频格式（wav/mp3/m4a/flac）
            sample_rate: 采样率（8000/16000/48000）
            return_timestamps: 是否返回时间戳
            task: 任务类型（transcribe/translate）
        
        Returns:
            包含识别结果的字典
        """
        # 验证参数
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        if sample_rate not in [8000, 16000, 48000]:
            raise ValueError(f"不支持的采样率: {sample_rate}，必须是 8000/16000/48000")
        
        # 构建 URL
        url = f"{self.base_url}/transcribe"
        
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 构建请求体
        data = {
            "language": language,
            "format": format,
            "sample_rate": sample_rate,
            "return_timestamps": return_timestamps,
            "task": task
        }
        
        try:
            # 读取音频文件
            with open(audio_file, 'rb') as f:
                files = {'audio': (os.path.basename(audio_file), f, f'audio/{format}')}
                
                # 发起请求
                start_time = time.time()
                response = requests.post(url, headers=headers, files=files, data=data, timeout=300)
                response.raise_for_status()
                
                # 解析响应
                result = response.json()
                
                # 检查错误
                if 'error' in result or result.get('code', 0) != 0:
                    error_msg = result.get('error', result.get('message', '未知错误'))
                    raise Exception(f"ASR API 错误: {error_msg}")
                
                # 计算处理时间
                processing_time = time.time() - start_time
                
                # 返回结果
                return {
                    "success": True,
                    "text": result.get('text', ''),
                    "language": language,
                    "duration": result.get('duration', 0),
                    "processing_time": processing_time,
                    "segments": result.get('segments', []) if return_timestamps else []
                }
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"响应解析失败: {str(e)}")
        except Exception as e:
            raise Exception(f"语音转文字失败: {str(e)}")
    
    def transcribe_with_speaker_diarization(
        self,
        audio_file: str,
        language: str = "zh-CN",
        num_speakers: Optional[int] = None,
        return_timestamps: bool = True
    ) -> dict:
        """
        语音转文字（带说话人分离）
        
        Args:
            audio_file: 音频文件路径
            language: 语言代码
            num_speakers: 说话人数量（如果为 None 则自动检测）
            return_timestamps: 是否返回时间戳
        
        Returns:
            包含识别结果和说话人信息的字典
        """
        # 构建 URL
        url = f"{self.base_url}/diarize"
        
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 构建请求体
        data = {
            "language": language,
            "return_timestamps": return_timestamps
        }
        
        if num_speakers is not None:
            data["num_speakers"] = num_speakers
        
        try:
            # 读取音频文件
            with open(audio_file, 'rb') as f:
                files = {'audio': (os.path.basename(audio_file), f, 'audio/wav')}
                
                # 发起请求
                start_time = time.time()
                response = requests.post(url, headers=headers, files=files, data=data, timeout=300)
                response.raise_for_status()
                
                # 解析响应
                result = response.json()
                
                # 检查错误
                if 'error' in result or result.get('code', 0) != 0:
                    error_msg = result.get('error', result.get('message', '未知错误'))
                    raise Exception(f"ASR API 错误: {error_msg}")
                
                # 计算处理时间
                processing_time = time.time() - start_time
                
                # 返回结果
                return {
                    "success": True,
                    "text": result.get('text', ''),
                    "language": language,
                    "duration": result.get('duration', 0),
                    "processing_time": processing_time,
                    "speakers": result.get('speakers', []),
                    "segments": result.get('segments', [])
                }
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"响应解析失败: {str(e)}")
        except Exception as e:
            raise Exception(f"语音转文字失败: {str(e)}")
    
    def get_supported_languages(self) -> List[str]:
        """
        获取支持的语言列表
        
        Returns:
            支持的语言代码列表
        """
        url = f"{self.base_url}/languages"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data or data.get('code', 0) != 0:
                error_msg = data.get('error', data.get('message', '未知错误'))
                raise Exception(f"获取语言列表失败: {error_msg}")
            
            return data.get('languages', [])
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"响应解析失败: {str(e)}")
        except Exception as e:
            raise Exception(f"获取语言列表失败: {str(e)}")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="Qwen3-ASR 语音转文字工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 基础用法
  python asr_transcriber.py --audio recording.wav --output text.txt
  
  # 指定语言
  python asr_transcriber.py --audio recording.wav --language en-US --output text.txt
  
  # 返回时间戳
  python asr_transcriber.py --audio recording.wav --timestamps --output text.txt
  
  # 说话人分离
  python asr_transcriber.py --audio meeting.wav --diarize --speakers 3 --output text.txt
  
  # 导出 JSON 格式
  python asr_transcriber.py --audio recording.wav --output result.json --format json

支持语言:
  zh-CN（中文）、en-US（英语）、ja-JP（日语）、ko-KR（韩语）
  以及更多语言，使用 --list-languages 查看
        """
    )
    
    # 必需参数
    parser.add_argument("--audio", "-a", required=True, help="音频文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出文件路径")
    
    # 识别参数
    parser.add_argument("--language", "-l", default="zh-CN", help="语言代码（默认 zh-CN）")
    parser.add_argument("--sample-rate", type=int, default=16000, choices=[8000, 16000, 48000], help="采样率（默认 16000）")
    parser.add_argument("--timestamps", action="store_true", help="返回时间戳")
    
    # 说话人分离
    parser.add_argument("--diarize", action="store_true", help="启用说话人分离")
    parser.add_argument("--speakers", type=int, help="说话人数量（不指定则自动检测）")
    
    # 输出格式
    parser.add_argument("--format", "-f", default="txt", choices=["txt", "json"], help="输出格式（txt/json，默认 txt）")
    
    # API 配置
    parser.add_argument("--api-key", help="Qwen3-ASR API 密钥（不提供则从环境变量读取）")
    parser.add_argument("--base-url", help="Qwen3-ASR API 基础 URL（不提供则使用默认值）")
    
    # 查询
    parser.add_argument("--list-languages", action="store_true", help="列出支持的语言")
    
    args = parser.parse_args()
    
    # 初始化 ASR 识别器
    try:
        transcriber = Qwen3ASRTranscriber(
            api_key=args.api_key,
            base_url=args.base_url
        )
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 列出支持的语言
    if args.list_languages:
        try:
            languages = transcriber.get_supported_languages()
            print("支持的语言列表:")
            for lang in languages:
                print(f"  - {lang}")
        except Exception as e:
            print(f"获取语言列表失败: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    
    # 验证音频文件
    if not os.path.exists(args.audio):
        print(f"错误：音频文件不存在: {args.audio}", file=sys.stderr)
        sys.exit(1)
    
    # 语音转文字
    try:
        if args.diarize:
            # 带说话人分离
            result = transcriber.transcribe_with_speaker_diarization(
                audio_file=args.audio,
                language=args.language,
                num_speakers=args.speakers,
                return_timestamps=args.timestamps
            )
        else:
            # 普通识别
            result = transcriber.transcribe(
                audio_file=args.audio,
                language=args.language,
                sample_rate=args.sample_rate,
                return_timestamps=args.timestamps
            )
        
        # 输出结果
        if args.format == "json":
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        else:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result["text"])
                
                if args.timestamps and result.get("segments"):
                    f.write("\n\n时间戳:\n")
                    for seg in result["segments"]:
                        f.write(f"[{seg['start']:.2f} - {seg['end']:.2f}] {seg['text']}\n")
                
                if args.diarize and result.get("speakers"):
                    f.write(f"\n说话人: {', '.join(result['speakers'])}\n")
        
        print(f"识别成功！")
        print(f"音频时长: {result['duration']:.2f} 秒")
        print(f"处理时间: {result['processing_time']:.2f} 秒")
        print(f"输出文件: {args.output}")
        print(f"文字长度: {len(result['text'])} 字符")
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
