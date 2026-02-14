"""
Edge-TTS 语音生成器
真正的本地 TTS 引擎，无需 API_KEY
"""

import asyncio
import edge_tts
from typing import Dict, Any, Optional


class LocalTTSGenerator:
    """本地 TTS 生成器（Edge-TTS）"""
    
    def __init__(self):
        """初始化生成器"""
        pass
    
    def generate_speech(
        self,
        text: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        output_file: str = "output.mp3",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> Dict[str, Any]:
        """
        生成语音（同步接口）
        
        Args:
            text: 要转换的文本
            voice: 音色名称（参考 voice-guide.md）
            output_file: 输出文件路径
            rate: 语速（-50% 到 +100%）
            pitch: 音调（-10Hz 到 +10Hz）
            volume: 音量（-100% 到 +100%）
        
        Returns:
            生成结果字典
        """
        
        # 验证输入
        if not text or not text.strip():
            return {
                "success": False,
                "error": "文本不能为空"
            }
        
        # 异步生成语音
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self._generate_speech_async(
                    text=text,
                    voice=voice,
                    output_file=output_file,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )
            )
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"生成失败: {str(e)}"
            }
        finally:
            loop.close()
    
    async def _generate_speech_async(
        self,
        text: str,
        voice: str,
        output_file: str,
        rate: str,
        pitch: str,
        volume: str
    ) -> Dict[str, Any]:
        """
        异步生成语音
        
        Args:
            text: 要转换的文本
            voice: 音色名称
            output_file: 输出文件路径
            rate: 语速
            pitch: 音调
            volume: 音量
        
        Returns:
            生成结果字典
        """
        
        try:
            # 创建 Communicate 对象
            communicate = edge_tts.Communicate(
                text,
                voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )
            
            # 保存音频文件
            await communicate.save(output_file)
            
            # 获取音频信息
            audio_info = self._get_audio_info(output_file)
            
            return {
                "success": True,
                "output_file": output_file,
                "voice": voice,
                "duration": audio_info.get("duration", 0),
                "format": audio_info.get("format", "mp3")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"生成失败: {str(e)}"
            }
    
    def _get_audio_info(self, audio_file: str) -> Dict[str, Any]:
        """获取音频文件信息"""
        try:
            import soundfile as sf
            info = sf.info(audio_file)
            return {
                "duration": info.duration,
                "sample_rate": info.samplerate,
                "format": info.format
            }
        except:
            return {"duration": 0, "format": "mp3"}
    
    def list_voices(self) -> Dict[str, Any]:
        """
        列出所有可用的音色
        
        Returns:
            音色列表字典
        """
        
        try:
            voices = edge_tts.list_voices()
            
            # 按语言分组
            grouped = {}
            for voice in voices:
                lang = voice["Locale"]
                if lang not in grouped:
                    grouped[lang] = []
                grouped[lang].append({
                    "name": voice["Name"],
                    "gender": voice["Gender"],
                    "age": voice.get("Age", "Adult")
                })
            
            return {
                "success": True,
                "voices": grouped
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取音色列表失败: {str(e)}"
            }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="本地 TTS 语音生成器（Edge-TTS）")
    parser.add_argument("text", help="要转换的文本")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="音色名称")
    parser.add_argument("--output", default="output.mp3", help="输出文件")
    parser.add_argument("--rate", default="+0%", help="语速（-50% 到 +100%）")
    parser.add_argument("--pitch", default="+0Hz", help="音调（-10Hz 到 +10Hz）")
    parser.add_argument("--volume", default="+0%", help="音量（-100% 到 +100%）")
    parser.add_argument("--list-voices", action="store_true", help="列出所有音色")
    
    args = parser.parse_args()
    
    generator = LocalTTSGenerator()
    
    if args.list_voices:
        result = generator.list_voices()
        if result["success"]:
            print("可用音色：")
            for lang, voices in result["voices"].items():
                print(f"\n  {lang}:")
                for voice in voices:
                    print(f"    - {voice['name']} ({voice['gender']})")
        else:
            print(f"❌ 获取失败: {result['error']}")
    else:
        result = generator.generate_speech(
            text=args.text,
            voice=args.voice,
            output_file=args.output,
            rate=args.rate,
            pitch=args.pitch,
            volume=args.volume
        )
        
        if result["success"]:
            print(f"✅ 语音生成成功: {result['output_file']}")
            print(f"   时长: {result['duration']:.2f} 秒")
        else:
            print(f"❌ 生成失败: {result['error']}")


if __name__ == "__main__":
    main()
