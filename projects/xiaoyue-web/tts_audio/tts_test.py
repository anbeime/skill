#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任嘉伦AI伴侣 - GPT-SoVITS TTS 测试脚本
自动测试多个音频素材的音色克隆效果
"""

import requests
import json
import os
import time
from pathlib import Path

# 配置
BASE_URL = "http://localhost:9874"
OUTPUT_DIR = Path("D:/tool/skill/projects/xiaoyue-web/tts_audio")

# 测试音频文件列表
AUDIO_FILES = [
    {
        "name": "红人面对面采访",
        "path": "D:/tool/skill/projects/xiaoyue-web/tts_audio/02_红人面对面_采访.wav",
        "ref_text": "大家好，我是任嘉伦",
        "priority": 1
    },
    {
        "name": "娱匠采访",
        "path": "D:/tool/skill/projects/xiaoyue-web/tts_audio/03_娱匠_采访.wav",
        "ref_text": "大家好，我是任嘉伦",
        "priority": 2
    },
    {
        "name": "芭莎星榜样采访",
        "path": "D:/tool/skill/projects/xiaoyue-web/tts_audio/04_芭莎星榜样_采访.wav",
        "ref_text": "大家好，我是任嘉伦",
        "priority": 3
    },
    {
        "name": "红人面对面花絮",
        "path": "D:/tool/skill/projects/xiaoyue-web/tts_audio/05_红人面对面_花絮.wav",
        "ref_text": "大家好，我是任嘉伦",
        "priority": 4
    },
    {
        "name": "采访合集MP3",
        "path": "D:/tool/skill/projects/xiaoyue-web/tts_audio/01_任嘉伦采访合集.mp3",
        "ref_text": "大家好，我是任嘉伦",
        "priority": 5
    }
]

# 测试文本列表
TEST_TEXTS = [
    "你好，我是任嘉伦，很高兴认识你。",
    "今天天气真不错，适合出去走走。",
    "作为演员，我觉得最重要的是真诚对待每一个角色。",
    "从6岁开始练乒乓球，到16岁因伤退役，这段经历让我学会了坚持。",
    "无论是演戏还是解说NBA，我觉得专业精神都是相通的。"
]

def test_tts_api(audio_file, test_text, output_name):
    """测试 TTS API"""
    try:
        # 构建请求
        url = f"{BASE_URL}/tts"
        
        # 准备文件和数据
        with open(audio_file["path"], 'rb') as f:
            files = {
                'refer_wav_path': (os.path.basename(audio_file["path"]), f, 'audio/wav')
            }
            data = {
                'prompt_text': audio_file["ref_text"],
                'prompt_language': 'zh',
                'text': test_text,
                'text_language': 'zh',
                'top_k': 15,
                'top_p': 0.7,
                'temperature': 0.7
            }
            
            print(f"  正在合成: {output_name}...")
            response = requests.post(url, files=files, data=data, timeout=120)
            
            if response.status_code == 200:
                # 保存音频
                output_path = OUTPUT_DIR / output_name
                with open(output_path, 'wb') as out_f:
                    out_f.write(response.content)
                print(f"  ✅ 成功: {output_path}")
                return True
            else:
                print(f"  ❌ 失败: HTTP {response.status_code}")
                print(f"  错误信息: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"  ❌ 错误: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("任嘉伦AI伴侣 - GPT-SoVITS 音色克隆测试")
    print("=" * 60)
    print()
    
    # 检查服务状态
    print("1. 检查 GPT-SoVITS 服务状态...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ GPT-SoVITS 服务运行正常")
        else:
            print(f"   ⚠️ 服务返回状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 无法连接到 GPT-SoVITS 服务: {e}")
        print(f"   请确保服务已启动: http://localhost:9874/")
        return
    
    print()
    
    # 测试每个音频文件
    results = []
    for audio_file in sorted(AUDIO_FILES, key=lambda x: x["priority"]):
        print(f"2. 测试音频素材: {audio_file['name']}")
        print(f"   文件路径: {audio_file['path']}")
        
        # 检查文件是否存在
        if not os.path.exists(audio_file['path']):
            print(f"   ❌ 文件不存在，跳过")
            continue
        
        # 测试第一条文本
        test_text = TEST_TEXTS[0]
        output_name = f"test_{audio_file['name']}_sample.wav"
        
        success = test_tts_api(audio_file, test_text, output_name)
        results.append({
            'name': audio_file['name'],
            'success': success,
            'output': output_name if success else None
        })
        
        print()
        time.sleep(2)  # 避免请求过快
    
    # 输出测试结果汇总
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for result in results:
        status = "✅ 成功" if result['success'] else "❌ 失败"
        print(f"{status} - {result['name']}")
        if result['output']:
            print(f"       输出文件: {result['output']}")
    
    print()
    print("测试完成！请试听生成的音频文件，选择效果最好的素材。")
    print(f"输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
