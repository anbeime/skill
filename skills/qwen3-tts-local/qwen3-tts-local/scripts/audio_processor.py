"""
音频处理器
支持音频格式转换、质量优化、音频拼接
"""

import os
import soundfile as sf
from typing import Dict, Any, List


class AudioProcessor:
    """音频处理器"""
    
    def __init__(self):
        """初始化处理器"""
        pass
    
    def convert_format(
        self,
        input_file: str,
        output_file: str,
        format: str = "wav",
        sample_rate: int = 24000
    ) -> Dict[str, Any]:
        """
        转换音频格式
        
        Args:
            input_file: 输入文件
            output_file: 输出文件
            format: 目标格式
            sample_rate: 采样率
        
        Returns:
            转换结果字典
        """
        
        try:
            # 读取音频
            data, sr = sf.read(input_file)
            
            # 重采样
            if sr != sample_rate:
                import librosa
                data = librosa.resample(data, orig_sr=sr, target_sr=sample_rate)
                sr = sample_rate
            
            # 写入新文件
            sf.write(output_file, data, sr, format=format)
            
            return {
                "success": True,
                "output_file": output_file,
                "sample_rate": sample_rate,
                "duration": len(data) / sr
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "需要安装 librosa: pip install librosa"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"转换失败: {str(e)}"
            }
    
    def optimize_quality(
        self,
        input_file: str,
        output_file: str,
        normalize: bool = True,
        remove_silence: bool = False
    ) -> Dict[str, Any]:
        """
        优化音频质量
        
        Args:
            input_file: 输入文件
            output_file: 输出文件
            normalize: 是否标准化音量
            remove_silence: 是否移除静音
        
        Returns:
            优化结果字典
        """
        
        try:
            import numpy as np
            # 读取音频
            data, sr = sf.read(input_file)
            
            # 标准化音量
            if normalize:
                max_val = np.max(np.abs(data))
                if max_val > 0:
                    data = data / max_val * 0.95
            
            # 移除静音
            if remove_silence:
                import librosa
                intervals = librosa.effects.split(data, top_db=20)
                non_silent = np.concatenate([data[start:end] for start, end in intervals])
                data = non_silent
            
            # 写入文件
            sf.write(output_file, data, sr)
            
            return {
                "success": True,
                "output_file": output_file,
                "original_duration": len(data) / sr
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"优化失败: {str(e)}"
            }
    
    def get_audio_info(self, audio_file: str) -> Dict[str, Any]:
        """
        获取音频信息
        
        Args:
            audio_file: 音频文件路径
        
        Returns:
            音频信息字典
        """
        
        try:
            info = sf.info(audio_file)
            
            return {
                "success": True,
                "duration": info.duration,
                "sample_rate": info.samplerate,
                "channels": info.channels,
                "format": info.format,
                "subtype": info.subtype
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取信息失败: {str(e)}"
            }
    
    def concatenate_audio(
        self,
        audio_files: List[str],
        output_file: str
    ) -> Dict[str, Any]:
        """
        拼接音频
        
        Args:
            audio_files: 音频文件列表
            output_file: 输出文件
        
        Returns:
            拼接结果字典
        """
        
        try:
            import numpy as np
            all_audio = []
            target_sr = None
            
            # 读取所有音频
            for audio_file in audio_files:
                data, sr = sf.read(audio_file)
                
                if target_sr is None:
                    target_sr = sr
                elif sr != target_sr:
                    import librosa
                    data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)
                
                all_audio.append(data)
            
            # 拼接音频
            result = np.concatenate(all_audio)
            sf.write(output_file, result, target_sr)
            
            return {
                "success": True,
                "output_file": output_file,
                "segment_count": len(audio_files),
                "duration": len(result) / target_sr
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"拼接失败: {str(e)}"
            }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="音频处理器")
    parser.add_argument("action", choices=["convert", "optimize", "info", "concat"], help="操作类型")
    parser.add_argument("--input", help="输入文件")
    parser.add_argument("--output", help="输出文件")
    parser.add_argument("--format", default="wav", help="格式")
    parser.add_argument("--sample-rate", type=int, default=24000, help="采样率")
    parser.add_argument("--normalize", action="store_true", help="标准化音量")
    parser.add_argument("--remove-silence", action="store_true", help="移除静音")
    
    args = parser.parse_args()
    
    processor = AudioProcessor()
    
    if args.action == "convert":
        result = processor.convert_format(
            input_file=args.input,
            output_file=args.output,
            format=args.format,
            sample_rate=args.sample_rate
        )
    elif args.action == "optimize":
        result = processor.optimize_quality(
            input_file=args.input,
            output_file=args.output,
            normalize=args.normalize,
            remove_silence=args.remove_silence
        )
    elif args.action == "info":
        result = processor.get_audio_info(args.input)
    elif args.action == "concat":
        result = processor.concatenate_audio(
            audio_files=[args.input],
            output_file=args.output
        )
    
    if result["success"]:
        print("✅ 操作成功")
        for key, value in result.items():
            if key != "success":
                print(f"   {key}: {value}")
    else:
        print(f"❌ 操作失败: {result['error']}")


if __name__ == "__main__":
    main()
