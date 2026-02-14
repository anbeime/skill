# 技术集成指南

## 目录
- [1. 技术方案概览](#1-技术方案概览)
- [2. 数字人API集成](#2-数字人api集成)
- [3. 视频合成工具集成](#3-视频合成工具集成)
- [4. 语音合成API集成](#4-语音合成api集成)
- [5. 端到端实现方案](#5-端到端实现方案)
- [6. 成本与性能考虑](#6-成本与性能考虑)

---

## 1. 技术方案概览

### MVP方案（最小可用版本）

**实现方式**：
- 使用智能体的图像生成能力生成关键帧
- 输出详细的视频合成方案和脚本
- 人工或使用基础视频编辑工具完成视频制作

**优点**：
- 无需额外API调用，成本最低
- 快速验证内容和流程
- 灵活性高，易于调整

**适用场景**：
- 内容策划和脚本验证
- 概念演示和原型制作
- 预算有限的项目

### 完整方案（技术集成版本）

**实现方式**：
- 集成数字人生成API（HeyGen、D-ID等）
- 集成视频合成工具（ffmpeg、剪映API等）
- 集成语音合成API（Azure TTS、百度TTS等）
- 实现端到端的自动化视频生成

**优点**：
- 完全自动化，批量生成效率高
- 视频质量稳定可控
- 可扩展性强

**适用场景**：
- 商业化运营
- 大批量视频生成
- 需要高效率的生产环境

---

## 2. 数字人API集成

### 2.1 HeyGen API

**API概述**：
HeyGen提供高质量的AI数字人视频生成服务，支持文本转视频、自定义数字人形象等功能。

**核心功能**：
- 文本转视频：输入文本，生成数字人讲解视频
- 自定义数字人：上传照片或视频，训练专属数字人
- 多语言支持：支持中英文等多种语言
- 实时生成：快速生成视频内容

**集成步骤**：

#### 步骤1：注册和获取API Key

1. 访问HeyGen官网注册账号
2. 进入开发者中心创建应用
3. 获取API Key
4. 在Skill中使用`skill_credentials`配置凭证

#### 步骤2：调用API生成数字人视频

```python
import os
from coze_workload_identity import requests

def generate_avatar_video(text: str, avatar_id: str, voice_id: str):
    """
    使用HeyGen API生成数字人视频
    
    参数：
        text: 数字人台词
        avatar_id: 数字人形象ID
        voice_id: 语音ID
    
    返回：
        视频URL和下载链接
    """
    
    # 获取凭证
    skill_id = "7598200361526132770"
    api_key = os.getenv("COZE_HEYGEN_API_KEY_" + skill_id)
    
    if not api_key:
        raise ValueError("缺少HeyGen API凭证")
    
    # API端点
    url = "https://api.heygen.com/v1/video.new"
    
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key
    }
    
    # 请求体
    payload = {
        "test": False,  # 测试模式
        "caption": False,  # 是否显示字幕
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": text,
                    "voice_id": voice_id
                }
            }
        ]
    }
    
    # 发起请求
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # 提取video_id
        video_id = data.get("data", {}).get("video_id")
        if not video_id:
            raise Exception("未获取到video_id")
        
        # 查询视频状态
        status_url = f"https://api.heygen.com/v1/video.status?video_id={video_id}"
        
        max_retries = 10
        for i in range(max_retries):
            status_response = requests.get(status_url, headers=headers, timeout=30)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            status = status_data.get("data", {}).get("status")
            if status == "completed":
                video_url = status_data.get("data", {}).get("video_url")
                return {
                    "video_id": video_id,
                    "video_url": video_url,
                    "status": "completed"
                }
            elif status == "failed":
                raise Exception("视频生成失败")
            
            # 等待后重试
            import time
            time.sleep(5)
        
        raise Exception("视频生成超时")
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"HeyGen API调用失败: {str(e)}")


# 使用示例
if __name__ == "__main__":
    # 生成单个场景的数字人视频
    result = generate_avatar_video(
        text="大家好，我是小省导购员！今天给大家推荐3款性价比超高的千元手机！",
        avatar_id="your_avatar_id",  # 从HeyGen获取
        voice_id="your_voice_id"    # 从HeyGen获取
    )
    
    print(f"视频生成成功: {result['video_url']}")
```

**脚本位置**：`scripts/heygen_avatar_generator.py`

#### 步骤3：配置凭证

调用`skill_credentials`工具配置HeyGen API密钥：

```python
skill_credentials(
    credential_name="heygen_api",
    auth_type=1,
    allowed_domain="api.heygen.com",
    env_variable_list=[
        {
            "variable_name": "API_KEY",
            "api_key_location": 2,  # Header
            "api_key_param_name": "X-Api-Key",
            "api_key_prefix": ""
        }
    ]
)
```

### 2.2 D-ID API

**API概述**：
D-ID提供实时数字人生成服务，支持高质量的视频和动画。

**集成步骤**：

#### 步骤1：注册和获取API Key

1. 访问D-ID官网注册账号
2. 获取API Key
3. 在Skill中配置凭证

#### 步骤2：调用API生成数字人

```python
import os
from coze_workload_identity import requests

def generate_did_avatar(text: str, image_url: str):
    """
    使用D-ID API生成数字人视频
    
    参数：
        text: 数字人台词
        image_url: 数字人形象图片URL
    
    返回：
        视频URL
    """
    
    skill_id = "7598200361526132770"
    api_key = os.getenv("COZE_DID_API_KEY_" + skill_id)
    
    if not api_key:
        raise ValueError("缺少D-ID API凭证")
    
    url = "https://api.d-id.com/talks"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {api_key}"
    }
    
    payload = {
        "script": {
            "type": "text",
            "input": text
        },
        "source_url": image_url,
        "config": {
            "fluent": True,
            "pad_audio": 0.0
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        talk_id = data.get("id")
        if not talk_id:
            raise Exception("未获取到talk_id")
        
        # 查询视频状态
        status_url = f"https://api.d-id.com/talks/{talk_id}"
        
        max_retries = 10
        for i in range(max_retries):
            status_response = requests.get(status_url, headers=headers, timeout=30)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            status = status_data.get("status")
            if status == "done":
                result_url = status_data.get("result_url")
                return {
                    "talk_id": talk_id,
                    "video_url": result_url,
                    "status": "done"
                }
            
            import time
            time.sleep(5)
        
        raise Exception("视频生成超时")
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"D-ID API调用失败: {str(e)}")
```

**脚本位置**：`scripts/did_avatar_generator.py`

---

## 3. 视频合成工具集成

### 3.1 FFmpeg视频合成

**工具概述**：
FFmpeg是一个强大的音视频处理工具，可以用于视频剪辑、合并、添加水印等操作。

**集成方式**：

#### 使用Python调用FFmpeg

```python
import subprocess
import os

def composite_video(
    avatar_video: str,
    background_image: str,
    product_images: list,
    ui_elements: list,
    output_path: str
):
    """
    使用FFmpeg合成视频
    
    参数：
        avatar_video: 数字人视频文件路径
        background_image: 背景图片文件路径
        product_images: 产品图片列表
        ui_elements: UI元素图片列表
        output_path: 输出视频路径
    """
    
    # FFmpeg命令模板
    cmd = [
        "ffmpeg",
        "-i", avatar_video,  # 数字人视频
        "-i", background_image,  # 背景图
        # 添加产品图片和UI元素...
        "-filter_complex", "[1:v]scale=1920:1080[bg];[0:v]scale=960:1080[avatar];[bg][avatar]overlay=(W-w)/2:0",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"视频合成成功: {output_path}")
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg执行失败: {e.stderr.decode()}")

# 使用示例
if __name__ == "__main__":
    composite_video(
        avatar_video="./avatar_scene1.mp4",
        background_image="./background_scene1.png",
        product_images=["./product1.png"],
        ui_elements=["./ui_label1.png"],
        output_path="./output_scene1.mp4"
    )
```

**脚本位置**：`scripts/video_compositor_ffmpeg.py`

**依赖配置**（添加到SKILL.md）：

```yaml
dependency:
  system:
    - apt-get update && apt-get install -y ffmpeg
```

### 3.2 剪映API集成

**API概述**：
剪映提供专业的视频编辑API，支持更高级的视频合成功能。

**集成步骤**：

```python
import os
from coze_workload_identity import requests

def create_jianying_project(materials: list):
    """
    使用剪映API创建视频项目
    
    参数：
        materials: 素材列表（视频、图片、音频等）
    """
    
    skill_id = "7598200361526132770"
    api_key = os.getenv("COZE_JIANYING_API_KEY_" + skill_id)
    
    if not api_key:
        raise ValueError("缺少剪映API凭证")
    
    url = "https://api.jianying.com/v1/projects"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "name": "数字人导购视频",
        "materials": materials,
        "timeline": {
            "tracks": [
                {
                    "type": "video",
                    "clips": [
                        {
                            "material_id": "avatar_video_id",
                            "start": 0,
                            "duration": 10
                        }
                    ]
                },
                {
                    "type": "image",
                    "clips": [
                        {
                            "material_id": "background_id",
                            "start": 0,
                            "duration": 120
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        project_id = data.get("project_id")
        
        # 导出视频
        export_url = f"https://api.jianying.com/v1/projects/{project_id}/export"
        export_response = requests.post(export_url, headers=headers, timeout=30)
        export_response.raise_for_status()
        
        return export_response.json()
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"剪映API调用失败: {str(e)}")
```

**脚本位置**：`scripts/jianying_compositor.py`

---

## 4. 语音合成API集成

### 4.1 Azure TTS

**API概述**：
Azure Text-to-Speech提供高质量的自然语音合成服务。

**集成步骤**：

```python
import os
from coze_workload_identity import requests

def text_to_speech(text: str, voice: str, output_path: str):
    """
    使用Azure TTS生成语音
    
    参数：
        text: 待合成文本
        voice: 语音类型（如zh-CN-XiaoxiaoNeural）
        output_path: 输出音频文件路径
    """
    
    skill_id = "7598200361526132770"
    api_key = os.getenv("COZE_AZURE_TTS_KEY_" + skill_id)
    
    if not api_key:
        raise ValueError("缺少Azure TTS凭证")
    
    url = f"https://eastus.tts.speech.microsoft.com/cognitiveservices/v1"
    
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
    }
    
    ssml = f"""
    <speak version='1.0' xml:lang='zh-CN'>
        <voice xml:lang='zh-CN' name='{voice}'>
            {text}
        </voice>
    </speak>
    """
    
    try:
        response = requests.post(url, headers=headers, data=ssml.encode('utf-8'), timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"语音合成成功: {output_path}")
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Azure TTS调用失败: {str(e)}")

# 使用示例
if __name__ == "__main__":
    text_to_speech(
        text="大家好，我是小省导购员！今天给大家推荐3款性价比超高的千元手机！",
        voice="zh-CN-XiaoxiaoNeural",
        output_path="./audio_scene1.mp3"
    )
```

**脚本位置**：`scripts/azure_tts.py`

### 4.2 百度TTS

```python
import os
from coze_workload_identity import requests

def baidu_text_to_speech(text: str, output_path: str):
    """
    使用百度TTS生成语音
    """
    
    skill_id = "7598200361526132770"
    api_key = os.getenv("COZE_BAIDU_TTS_KEY_" + skill_id)
    secret_key = os.getenv("COZE_BAIDU_TTS_SECRET_" + skill_id)
    
    # 获取access_token
    token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
    token_response = requests.get(token_url, timeout=30)
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    
    # 调用TTS
    tts_url = f"https://tsn.baidu.com/text2audio?tok={access_token}&tex={text}&cuid=user&ctp=1&lan=zh"
    
    response = requests.get(tts_url, timeout=30)
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    
    print(f"语音合成成功: {output_path}")
```

**脚本位置**：`scripts/baidu_tts.py`

---

## 5. 端到端实现方案

### 5.1 完整流程实现

```python
import os
from typing import List, Dict

class AvatarVideoGenerator:
    """数字人导购视频生成器（完整版）"""
    
    def __init__(self, skill_id: str):
        self.skill_id = skill_id
        
    def generate_video(
        self,
        script_data: Dict,
        visual_data: Dict,
        avatar_data: Dict,
        output_dir: str
    ) -> str:
        """
        端到端生成数字人导购视频
        
        参数：
            script_data: 脚本数据
            visual_data: 视觉设计数据
            avatar_data: 数字人数据
            output_dir: 输出目录
        
        返回：
            视频文件路径
        """
        
        # 步骤1：生成数字人视频片段
        avatar_videos = []
        for scene in script_data["script_scenes"]:
            avatar_video = self._generate_avatar_scene(
                text=scene["dialogue"],
                emotion=scene["avatar_expression"]
            )
            avatar_videos.append(avatar_video)
        
        # 步骤2：合成背景和UI元素
        background_video = self._composite_background(visual_data)
        
        # 步骤3：合并所有元素
        final_video = self._composite_all_elements(
            avatar_videos=avatar_videos,
            background_video=background_video,
            output_path=os.path.join(output_dir, "final_video.mp4")
        )
        
        return final_video
    
    def _generate_avatar_scene(self, text: str, emotion: str) -> str:
        """生成单个场景的数字人视频"""
        # 调用数字人API
        pass
    
    def _composite_background(self, visual_data: Dict) -> str:
        """合成背景视频"""
        # 使用FFmpeg或其他工具
        pass
    
    def _composite_all_elements(
        self,
        avatar_videos: List[str],
        background_video: str,
        output_path: str
    ) -> str:
        """合成所有元素"""
        # 使用FFmpeg或其他工具
        pass


# 使用示例
if __name__ == "__main__":
    generator = AvatarVideoGenerator(skill_id="7598200361526132770")
    
    # 读取脚本和设计数据
    script_data = {...}
    visual_data = {...}
    avatar_data = {...}
    
    # 生成视频
    video_path = generator.generate_video(
        script_data=script_data,
        visual_data=visual_data,
        avatar_data=avatar_data,
        output_dir="./output"
    )
    
    print(f"视频生成完成: {video_path}")
```

**脚本位置**：`scripts/avatar_video_generator.py`

### 5.2 批量生成

```python
from avatar_video_generator import AvatarVideoGenerator

def batch_generate_videos(
    product_lists: List[Dict],
    output_dir: str
):
    """
    批量生成导购视频
    
    参数：
        product_lists: 产品列表
        output_dir: 输出目录
    """
    
    generator = AvatarVideoGenerator(skill_id="7598200361526132770")
    
    for i, products in enumerate(product_lists):
        print(f"正在生成第{i+1}个视频...")
        
        # 步骤1：内容策划
        # 步骤2：脚本创作
        # 步骤3：视觉设计
        # 步骤4：数字人驱动
        # 步骤5：视频合成
        
        video_path = generator.generate_video(
            script_data=script_data,
            visual_data=visual_data,
            avatar_data=avatar_data,
            output_dir=os.path.join(output_dir, f"video_{i+1}")
        )
        
        print(f"视频{i+1}生成完成: {video_path}")

# 使用示例
if __name__ == "__main__":
    product_lists = [
        {"category": "手机", "products": [...]},
        {"category": "服装", "products": [...]},
        {"category": "家电", "products": [...]}
    ]
    
    batch_generate_videos(product_lists, "./batch_output")
```

**脚本位置**：`scripts/batch_generator.py`

---

## 6. 成本与性能考虑

### 6.1 API成本分析

| 服务 | 免费额度 | 付费价格 | 适用场景 |
|-----|---------|---------|---------|
| HeyGen | 1个免费视频 | $29/月起 | 高质量数字人 |
| D-ID | 5个免费视频 | $29/月起 | 实时数字人 |
| Azure TTS | 500万字符/月 | $15/月起 | 高质量语音 |
| 百度TTS | 200万字符/天 | 按量付费 | 国内语音服务 |

**成本优化建议**：
- 优先使用免费额度
- 批量生成时选择合适的API套餐
- 考虑使用本地TTS降低成本

### 6.2 性能优化

**视频生成时间**：
- 数字人视频生成：每个场景30-60秒
- 视频合成：10-20秒/分钟视频
- 总计：100-120秒视频约需5-8分钟

**优化策略**：
- 并行生成多个数字人视频
- 使用缓存避免重复生成
- 预加载常用数字人形象

### 6.3 质量控制

**质量检查点**：
- 数字人表情是否自然
- 音画是否同步
- 视频质量是否达标
- 文件大小是否合理

**失败处理**：
- 重试机制：最多3次
- 降级方案：使用备用API
- 错误日志：记录失败原因

---

## 附录：推荐技术栈

### 入门级方案
- 数字人：D-ID（成本较低）
- 语音合成：百度TTS（国内，稳定）
- 视频合成：FFmpeg（开源免费）
- **总成本**：约$29/月

### 专业级方案
- 数字人：HeyGen（质量高）
- 语音合成：Azure TTS（自然度高）
- 视频合成：剪映API（功能强大）
- **总成本**：约$100/月

### 企业级方案
- 数字人：定制训练
- 语音合成：定制声音模型
- 视频合成：自建渲染服务
- **总成本**：根据需求定制

---

## 注意事项

1. **API凭证管理**：妥善保管API密钥，不要硬编码在脚本中
2. **配额限制**：注意API调用频率限制，避免超限
3. **版权问题**：确保使用的图片、音乐等素材有版权
4. **合规要求**：遵守各平台的API使用规范
5. **备份策略**：重要数据及时备份
6. **错误监控**：建立完善的错误监控和日志系统
