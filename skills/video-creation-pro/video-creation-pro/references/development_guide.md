# 开发技能的核心落地建议

## 概览
本文档提供"影品智创"技能开发的核心落地建议，聚焦解决依赖包卡死+字幕问题，强制API合成。

## 1. 技能端添加关键词屏蔽

### 目标
在技能底层设置屏蔽词，若检测到智能体输出/执行中出现本地依赖包关键词，立即触发警告并阻断流程

### 屏蔽词列表
```
moviepy
opencv-python
mediapipe
pillow
numpy
cv2
Image
VideoFileClip
AudioFileClip
```

### 实现建议
```python
# 伪代码示例
def check_local_dependency(text):
    """
    检测文本中是否包含本地依赖包关键词
    :param text: 待检测文本
    :return: (is_blocked, keyword)
    """
    blocked_keywords = [
        "moviepy", "opencv-python", "mediapipe", "pillow", "numpy",
        "cv2", "Image", "VideoFileClip", "AudioFileClip"
    ]

    for keyword in blocked_keywords:
        if keyword.lower() in text.lower():
            return (True, keyword)

    return (False, None)

def handle_blocked_output(text, agent_name):
    """
    处理被屏蔽的输出
    """
    is_blocked, keyword = check_local_dependency(text)

    if is_blocked:
        print(f"【警告】检测到本地依赖包关键词：{keyword}")
        print(f"来源智能体：{agent_name}")
        print("已阻断流程，强制切换至纯COZE API合成流程")
        return False

    return True
```

## 2. 素材格式固化

### 目标
在技能中预设COZE API优选的素材格式，各智能体输出时直接按预设格式生成，无需自定义

### 预设格式规范

#### 图片素材
- 格式：JPG/PNG（COZE API优选格式）
- 分辨率：1080P
- 比例：横屏16:9或竖屏9:16
- 命名规范：镜头序号_场景名称（如01_熬夜泛红）

#### 音频素材
- 格式：MP3（API优选格式）
- 采样率：44100Hz或48000Hz
- 比特率：128kbps-320kbps

#### 字幕素材
- 格式：COZE API可直接解析的列表格式
- 包含：镜头序号、字幕文本、显示时长、格式参数、位置参数、同步参数

### 实现建议
```python
# 伪代码示例
class MaterialFormatValidator:
    """素材格式校验器"""

    @staticmethod
    def validate_image(image_path):
        """校验图片格式"""
        valid_formats = ['.jpg', '.png', '.jpeg']
        ext = os.path.splitext(image_path)[1].lower()

        if ext not in valid_formats:
            raise ValueError(f"图片格式不支持：{ext}，仅支持JPG/PNG格式")

        # 校验分辨率
        img = Image.open(image_path)
        width, height = img.size

        if width != 1920 or height != 1080:
            raise ValueError(f"图片分辨率不支持：{width}x{height}，仅支持1920x1080")

        return True

    @staticmethod
    def validate_audio(audio_path):
        """校验音频格式"""
        valid_formats = ['.mp3']
        ext = os.path.splitext(audio_path)[1].lower()

        if ext not in valid_formats:
            raise ValueError(f"音频格式不支持：{ext}，仅支持MP3格式")

        return True
```

## 3. API参数预设模板

### 目标
将典型视频的API合成参数保存为模板，后续同类型视频可直接调用，减少参数配置错误

### 治愈风美妆模板（玻尿酸面膜）
```json
{
  "template_name": "healing_beauty_mask",
  "description": "治愈风美妆面膜视频（玻尿酸面膜60秒）",
  "video_params": {
    "resolution": "1080P",
    "aspect_ratio": "9:16",
    "duration": 60,
    "fps": 25,
    "output_format": "MP4"
  },
  "transition_params": {
    "type": "soft_fade",
    "duration": 0.4
  },
  "audio_video_sync": {
    "enabled": true,
    "max_offset": 0.1
  },
  "quality_params": {
    "hd_noise_reduction": true,
    "color_correction": "warm_tone"
  },
  "subtitle_params": {
    "font_family": "sans_serif",
    "font_size": 28,
    "color": "off_white",
    "border_color": "light_pink",
    "border_width": 1,
    "position": {
      "x": "center",
      "y": 0.85,
      "margin_bottom": 30,
      "margin_left": 20,
      "margin_right": 20
    }
  }
}
```

### 简约科技风模板（智能手环）
```json
{
  "template_name": "minimalist_tech_watch",
  "description": "简约科技风智能手环视频（30秒）",
  "video_params": {
    "resolution": "1080P",
    "aspect_ratio": "16:9",
    "duration": 30,
    "fps": 25,
    "output_format": "MP4"
  },
  "transition_params": {
    "type": "tech_glow",
    "duration": 0.4
  },
  "audio_video_sync": {
    "enabled": true,
    "max_offset": 0.1
  },
  "quality_params": {
    "hd_noise_reduction": true,
    "color_correction": "cool_tone"
  }
}
```

### 实现建议
```python
# 伪代码示例
class TemplateManager:
    """API参数模板管理器"""

    def __init__(self):
        self.templates = {
            "healing_beauty_mask": self.healing_beauty_mask_template,
            "minimalist_tech_watch": self.minimalist_tech_watch_template
        }

    def get_template(self, template_name):
        """获取模板"""
        if template_name not in self.templates:
            raise ValueError(f"模板不存在：{template_name}")

        return self.templates[template_name]
```

## 4. 字幕参数可视化校验

### 目标
在技能中添加简单的字幕参数预览功能，质检智能体可直接预览字幕位置/格式，避免因参数错误导致的合成后字幕遮挡

### 实现建议
```python
# 伪代码示例
def preview_subtitle(subtitle_params, image_size=(1080, 1920)):
    """
    预览字幕参数
    :param subtitle_params: 字幕参数
    :param image_size: 画面尺寸
    :return: 字幕位置和尺寸信息
    """
    # 解析字幕参数
    text = subtitle_params['text']
    font_size = subtitle_params['font_size']
    position = subtitle_params['position']

    # 计算字幕位置
    if position['x'] == 'center':
        x = image_size[0] // 2
    else:
        x = int(image_size[0] * position['x'])

    if 'y' in position:
        y = int(image_size[1] * position['y'])
    elif 'margin_bottom' in position:
        y = image_size[1] - position['margin_bottom']

    # 估算字幕尺寸
    text_width = len(text) * font_size * 0.6  # 估算
    text_height = font_size * 1.2

    # 校验是否遮挡核心元素
    # 这里需要结合实际核心元素位置信息

    return {
        'text': text,
        'position': (x, y),
        'size': (text_width, text_height),
        'is_safe': True  # 是否安全（不遮挡核心元素）
    }
```

## 5. 合成异常兜底

### 目标
为COZE API调用添加"合成失败备用方案"，若3次重试仍失败，直接将"合格图片+字幕参数+音效素材"打包输出，支持人工在COZE平台手动上传合成

### 实现建议
```python
# 伪代码示例
def api_video_synthesis_with_fallback(images, subtitle_params, audio_params, output_path):
    """
    API视频合成（带异常兜底）
    :param images: 图片列表
    :param subtitle_params: 字幕参数包
    :param audio_params: 音效素材包
    :param output_path: 输出路径
    :return: (success, output_path_or_fallback_package)
    """
    max_retries = 3
    timeout = 10  # 秒

    for attempt in range(max_retries):
        try:
            # 调用COZE API合成
            result = call_coze_api(images, subtitle_params, audio_params, timeout=timeout)

            if result['success']:
                # 合成成功
                save_video(result['video_url'], output_path)
                return (True, output_path)

        except Exception as e:
            print(f"API合成失败（尝试{attempt + 1}/{max_retries}）：{e}")

            if attempt < max_retries - 1:
                # 重试
                time.sleep(2)
                continue
            else:
                # 达到最大重试次数，触发兜底方案
                print("已达到最大重试次数，触发兜底方案")

                fallback_package_path = output_path.replace('.mp4', '_fallback_package.zip')
                create_fallback_package(images, subtitle_params, audio_params, fallback_package_path)

                print(f"已生成兜底包：{fallback_package_path}")
                print("请手动在COZE平台上传素材进行合成")

                return (False, fallback_package_path)

def create_fallback_package(images, subtitle_params, audio_params, output_path):
    """
    创建兜底包
    """
    import zipfile

    with zipfile.ZipFile(output_path, 'w') as zipf:
        # 添加图片
        for i, image in enumerate(images):
            zipf.write(image, f"images/{os.path.basename(image)}")

        # 添加字幕参数
        subtitle_json_path = "subtitle_params.json"
        with open(subtitle_json_path, 'w', encoding='utf-8') as f:
            json.dump(subtitle_params, f, ensure_ascii=False, indent=2)
        zipf.write(subtitle_json_path, "subtitle_params.json")

        # 添加音效素材
        for i, audio in enumerate(audio_params['sound_effects']):
            zipf.write(audio['file_path'], f"audio/{os.path.basename(audio['file_path'])}")

        # 添加背景音乐
        if 'background_music' in audio_params:
            zipf.write(audio_params['background_music']['file_path'], f"audio/{os.path.basename(audio_params['background_music']['file_path'])}")

        # 添加README
        readme_content = """
        # 兜底包使用说明

        本包包含视频合成所需的全部素材，请手动在COZE平台上传进行合成。

        ## 文件清单
        - images/：分镜图片（按镜头序号排序）
        - audio/：音效素材（背景音乐+场景音效）
        - subtitle_params.json：字幕参数包（COZE API格式）

        ## 使用步骤
        1. 登录COZE平台
        2. 新建视频合成任务
        3. 上传分镜图片（按镜头序号排序）
        4. 上传音效素材
        5. 复制字幕参数包内容到字幕参数配置
        6. 配置API参数（1080P、9:16、60秒、25fps、柔焦渐变转场、音画同步、高清降噪）
        7. 启动合成

        注意事项：
        - 确保素材格式正确（图片：JPG/PNG，音频：MP3）
        - 确保字幕参数包格式正确（COZE API格式）
        - 确保API参数配置正确
        """

        with open("README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        zipf.write("README.md", "README.md")
```

## 总结

### 核心落地建议
1. **技能端添加关键词屏蔽**：检测到本地依赖包关键词立即阻断流程
2. **素材格式固化**：预设COZE API优选的素材格式
3. **API参数预设模板**：将典型视频的API合成参数保存为模板
4. **字幕参数可视化校验**：添加字幕参数预览功能
5. **合成异常兜底**：API调用失败后生成兜底包，支持人工手动合成

### 核心原则
- **API合成强制**：唯一调用COZE平台视频大模型API完成视频合成
- **流程阻断规则**：若出现本地依赖包调用行为，立即终止并切换至纯COZE API合成流程
- **API适配优先**：所有输出物均按COZE视频大模型API要求定义格式
