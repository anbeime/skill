# 视觉分析指导文档

## 目录
- [视觉模型选择](#视觉模型选择)
- [分析提示词模板](#分析提示词模板)
- [结果格式说明](#结果格式说明)
- [最佳实践](#最佳实践)

---

## 视觉模型选择

### 推荐模型

| 模型 | API Base | 优势 | 适用场景 |
|------|----------|------|----------|
| GPT-4V | https://api.openai.com/v1 | 理解能力强,描述详细 | 场景分析、人物识别 |
| Claude-3.5-Sonnet | https://api.anthropic.com/v1 | 细节捕捉准确,逻辑清晰 | 构图分析、风格识别 |
| Gemini Pro Vision | https://generativelanguage.googleapis.com/v1beta | 成本较低,速度快 | 批量处理、快速预览 |

### 配置方法

**环境变量配置:**
```bash
export VISION_API_KEY="your_api_key"
export VISION_API_BASE="https://api.openai.com/v1"
export VISION_MODEL="gpt-4-vision-preview"
```

**命令行参数:**
```bash
python scripts/visual_analyzer.py \
  --input ./output/frames \
  --output ./output/analysis.json \
  --api_key "your_api_key" \
  --api_base "https://api.openai.com/v1" \
  --model "gpt-4-vision-preview"
```

---

## 分析提示词模板

### 1. 通用场景分析
```
详细描述这张图片的场景内容,包括:
1. 场景类型(室内/室外/特定场景)
2. 人物特征(数量、外貌、表情、动作)
3. 环境元素(背景、道具、装饰)
4. 构图特点(镜头角度、景深、焦点)
5. 光影效果(光源方向、光线强度、色调)
6. 整体风格(写实/抽象/特定艺术风格)

输出格式: 结构化JSON,包含以上各维度描述。
```

### 2. AI视频创作参考
```
分析这张图片,生成AI视频创作提示词:
1. 场景描述(50字以内)
2. 人物动作描述(30字以内)
3. 构图提示词(镜头、角度、景深)
4. 光影提示词(光线、色调、氛围)
5. 风格关键词(3-5个)

输出格式: JSON格式,便于后续调用生图API。
```

### 3. 分镜提取
```
将这张图片转化为分镜描述:
1. 镜头类型(特写/中景/全景)
2. 画面主体(人物/物体/场景)
3. 关键动作(当前动作、运动趋势)
4. 时间感(瞬间/动态/静止)
5. 情绪基调(紧张/平静/温馨等)

输出格式: 标准分镜脚本格式。
```

### 4. 风格识别
```
识别这张图片的视觉风格:
1. 色彩体系(主色调、配色方案)
2. 构图风格(对称/不对称/黄金分割等)
3. 材质质感(光滑/粗糙/细腻等)
4. 艺术流派(如适用)
5. 关键风格标签(5-10个标签)

输出格式: JSON格式,包含风格特征和标签。
```

### 5. 商品细节分析
```
分析图片中的商品细节:
1. 商品类型和功能
2. 外观特征(颜色、材质、设计)
3. 显示内容(如屏幕、文字)
4. 使用状态(佩戴/摆放/操作中)
5. 细节瑕疵(如有)

输出格式: JSON格式,便于商品展示优化。
```

---

## 结果格式说明

### 分析结果JSON格式

```json
{
  "success": true,
  "total_images": 10,
  "analyzed_count": 10,
  "failed_count": 0,
  "analysis": [
    {
      "frame_file": "frame_00001.jpg",
      "frame_path": "./output/frames/frame_00001.jpg",
      "timestamp": "00:00:00",
      "time_seconds": 0.0,
      "description": "场景描述内容...",
      "analysis_status": "success"
    },
    {
      "frame_file": "frame_00002.jpg",
      "frame_path": "./output/frames/frame_00002.jpg",
      "timestamp": "00:00:03",
      "time_seconds": 3.0,
      "description": "场景描述内容...",
      "analysis_status": "success"
    }
  ],
  "errors": []
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 整体是否成功 |
| total_images | number | 总图片数 |
| analyzed_count | number | 成功分析的图片数 |
| failed_count | number | 分析失败的图片数 |
| analysis | array | 分析结果数组 |
| analysis[].frame_file | string | 文件名 |
| analysis[].frame_path | string | 完整路径 |
| analysis[].timestamp | string | 时间戳(HH:MM:SS) |
| analysis[].time_seconds | number | 时间(秒) |
| analysis[].description | string | 视觉模型分析内容 |
| analysis[].analysis_status | string | 分析状态(success/failed) |
| analysis[].error | string | 错误信息(如果失败) |
| errors | array | 错误信息数组 |

---

## 最佳实践

### 1. 抽帧策略

**根据视频类型选择抽帧间隔:**
- 快节奏视频(广告/MV): 0.5-1秒
- 正常剧情视频: 2-3秒
- 慢节奏视频(纪录片): 4-5秒

**最大抽帧数建议:**
- 短视频(<30秒): 5-10帧
- 中等视频(1-5分钟): 10-20帧
- 长视频(>5分钟): 20-30帧

### 2. 分析提示词优化

**提示词设计原则:**
- 明确输出格式(JSON/文本)
- 分维度描述(场景/人物/构图/光影)
- 控制输出长度(避免过长)
- 针对使用场景定制

**示例:**
```
# 好的提示词
描述场景、人物、构图、光影,输出JSON格式,每个维度不超过50字。

# 不好的提示词
描述这张图片。
```

### 3. 批量处理优化

**控制批量大小:**
- 默认batch_size=5,适合大多数API
- 可根据API限制调整
- 批次间添加延迟(避免速率限制)

**处理失败重试:**
```python
# 脚本已内置错误处理
# 如果部分图片分析失败,不会影响其他图片
# 失败结果会记录在errors字段中
```

### 4. 成本控制

**API调用次数:**
- 抽帧数 × 批量请求次数
- 建议先小规模测试(5-10帧)
- 确认效果后再扩大规模

**Token消耗估算:**
- GPT-4V: 每张图片约500-1000 tokens
- Claude-3.5-Sonnet: 每张图片约300-800 tokens
- 根据分析结果长度估算

### 5. 结果后处理

**智能体应用场景:**
1. **视频创作参考**: 根据分析结果生成提示词
2. **分镜设计**: 提取关键场景和构图
3. **风格迁移**: 识别风格特征
4. **内容提取**: 提取关键信息和标签

**示例 - 智能体整合:**
```
智能体读取analysis.json
→ 提取每帧的关键描述
→ 组合成连贯的故事线
→ 生成AI创作提示词
```

---

## 常见问题

### Q1: 视觉分析失败怎么办?

**A:** 检查以下几点:
1. API密钥是否正确
2. 图片格式是否支持(JPG/PNG)
3. 图片大小是否合理(<20MB)
4. API调用次数是否超限

### Q2: 分析结果不理想?

**A:** 尝试优化:
1. 调整分析提示词,明确需求
2. 切换视觉模型(不同模型特长不同)
3. 调整detail参数(low/standard/high)
4. 分阶段分析(先粗后细)

### Q3: 如何提高处理速度?

**A:** 优化策略:
1. 减少抽帧数量
2. 使用更快的模型(如Gemini Pro Vision)
3. 增大batch_size(在API限制内)
4. 使用GPU加速(本地部署)

### Q4: 分析结果如何用于AI创作?

**A:** 应用方法:
1. **生图提示词**: 直接使用description字段
2. **分镜脚本**: 根据timestamp组织内容
3. **风格参考**: 提取关键词和风格标签
4. **内容复用**: 智能体整合多帧内容生成新创意

---

## 附录: 完整示例

### 示例1: 完整反推流程

```bash
# 1. 抽帧
python scripts/video_frame_extractor.py \
  --input ./input/video.mp4 \
  --output ./output/frames \
  --interval 2 \
  --max_frames 10

# 2. 分析
python scripts/visual_analyzer.py \
  --input ./output/frames \
  --output ./output/analysis.json \
  --prompt "分析场景、人物、构图、光影,输出JSON格式,适合AI视频创作"

# 3. 智能体处理(由智能体执行)
# 读取analysis.json
# 整合描述生成创作提示词
# 输出可用的提示词列表
```

### 示例2: 自定义分析

```bash
# 分析人物表情
python scripts/visual_analyzer.py \
  --input ./output/frames \
  --output ./output/face_analysis.json \
  --prompt "分析人物表情、情绪、眼神,输出JSON格式"

# 分析构图
python scripts/visual_analyzer.py \
  --input ./output/frames \
  --output ./output/composition_analysis.json \
  --prompt "分析构图特点、镜头角度、景深,输出JSON格式"
```

### 示例3: 批量处理优化

```bash
# 小批量高频请求
python scripts/visual_analyzer.py \
  --input ./output/frames \
  --output ./output/analysis.json \
  --batch_size 3 \
  --detail low
```
