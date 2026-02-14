# 历史名人现代访谈短视频创作系统

## 项目说明

这是一个基于多智能体协作的历史名人现代访谈短视频创作系统，支持从文案到视频的端到端自动化生成。

## 系统架构

### 双模式设计

- **基础模式**：4智能体文案创作
  - 历史学家智能体（Historian）
  - 热梗分析师智能体（Meme Analyst）
  - 文案师智能体（Scriptwriter）
  - 质量审查员智能体（QC）

- **完整模式**：9智能体端到端创作
  - 基础模式的4个智能体
  - 视觉设计师智能体（Visual Designer）
  - 分镜策划师智能体（Storyboard）
  - 音频匹配师智能体（Audio Matcher）
  - 素材生成器（Image Generator）
  - 视频剪辑师（Video Editor）

## 目录结构

```
scripts/
├── config/
│   └── settings.py           # 配置管理
├── memory/
│   └── shared_memory.py      # 共享记忆库
├── agents/
│   ├── __init__.py
│   ├── base_agent.py         # 智能体基类
│   ├── historian_agent.py    # 历史学家智能体
│   ├── meme_analyst_agent.py # 热梗分析师智能体
│   ├── scriptwriter_agent.py # 文案师智能体
│   ├── qc_optimizer_agent.py # 质量审查员智能体
│   ├── visual_design_agent.py # 视觉设计师智能体
│   ├── storyboard_agent.py   # 分镜策划师智能体
│   └── audio_matcher_agent.py # 音频匹配师智能体
├── tools/
│   └── external_tools.py     # 外部工具封装
├── basic_pipeline.py         # 基础模式（4智能体）
├── full_pipeline.py          # 完整模式（9智能体）
└── full_pipeline_executor.py # 全流程执行器
```

## 快速开始

### 环境要求

- Python 3.8+
- 依赖包（见 requirements.txt）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

1. 复制配置模板：

```bash
cp config/settings.py config/settings_local.py
```

2. 编辑配置文件，填入你的API密钥：

```python
# config/settings_local.py

# LLM配置
LLM_CONFIG = {
    'provider': 'openai',  # 可选：openai, anthropic, zhipu
    'api_key': 'your-api-key',
    'model': 'gpt-4',
    'base_url': None  # 如果使用代理，填写代理地址
}

# 图片生成配置
IMAGE_GENERATOR = {
    'provider': 'dalle',  # 可选：dalle, midjourney, stable_diffusion
    'api_key': 'your-api-key',
    'style': 'cartoon'
}

# 音频生成配置
AUDIO_GENERATOR = {
    'provider': 'azure',  # 可选：azure, google, aws
    'api_key': 'your-api-key',
    'region': 'eastus'
}

# 质量标准配置
QC_STANDARDS = {
    'pass_score': 85.0,
    'dimensions': {
        'historical_accuracy': {'weight': 0.3, 'description': '历史准确性'},
        'meme_naturalness': {'weight': 0.3, 'description': '梗点自然度'},
        'internet_sense': {'weight': 0.2, 'description': '网感'},
        'visual_appeal': {'weight': 0.1, 'description': '视觉吸引力'},
        'platform_fit': {'weight': 0.1, 'description': '平台适配度'}
    }
}
```

### 使用示例

#### 基础模式（4智能体文案创作）

```bash
python scripts/basic_pipeline.py
```

#### 完整模式（9智能体端到端创作）

```bash
python scripts/full_pipeline_executor.py
```

### 自定义配置

在代码中导入配置并创建执行器：

```python
from config.settings import Config
from scripts.basic_pipeline import BasicPipeline
from scripts.full_pipeline_executor import FullPipeline

# 加载配置
config = Config()

# 基础模式
basic_pipeline = BasicPipeline(config)
result = basic_pipeline.execute({
    'characters': ['qin_shihuang', 'li_bai'],
    'theme': '现代职场',
    'platform': 'douyin'
})

# 完整模式
full_pipeline = FullPipeline(config)
result = full_pipeline.execute({
    'characters': ['qin_shihuang', 'li_bai'],
    'theme': '现代职场',
    'platform': 'douyin',
    'style': 'cartoon',
    'duration': 60
})
```

## 核心功能说明

### 1. 智能体基类（BaseAgent）

所有智能体继承自 `BaseAgent`，提供基础能力：
- 日志记录
- 内存读写
- LLM调用
- 上下文管理

### 2. 共享记忆库（SharedMemory）

实现智能体间的数据共享和版本控制：
- 层级化存储（characters, memes, scripts, qc_standards）
- 版本管理
- 数据同步

### 3. 外部工具封装

- **图片生成**：支持OpenAI DALL-E、Midjourney、Stable Diffusion
- **音频生成**：支持Azure TTS、Google TTS、AWS Polly
- **视频剪辑**：支持FFmpeg、MoviePy

## 扩展开发

### 添加新的智能体

1. 继承 `BaseAgent`：

```python
from agents.base_agent import BaseAgent

class NewAgent(BaseAgent):
    def __init__(self, name, llm_client, memory_manager):
        super().__init__(name, llm_client, memory_manager)
    
    def execute(self, *args, **kwargs):
        # 实现具体逻辑
        pass
```

2. 在全流程中注册智能体：

```python
from agents.new_agent import NewAgent

class FullPipeline:
    def __init__(self, config):
        # ...
        self.agents = {
            # ...
            'new_agent': NewAgent('new_agent', self.llm_client, self.memory)
        }
```

### 添加新的外部工具

在 `tools/external_tools.py` 中添加新方法：

```python
class ExternalToolsManager(BaseAgent):
    def new_tool(self, param):
        # 实现工具逻辑
        pass
```

## 注意事项

1. **API密钥安全**：请勿将包含API密钥的配置文件提交到版本控制系统
2. **输出目录**：系统会在 `./output` 目录下生成输出文件
3. **资源消耗**：完整模式需要调用多个外部API，请注意成本控制
4. **错误处理**：所有工具调用都包含错误处理，但请确保网络连接正常

## 常见问题

### Q: 如何更换LLM提供商？

A: 修改配置文件中的 `LLM_CONFIG.provider` 和相关配置。

### Q: 如何调整质量标准？

A: 修改配置文件中的 `QC_STANDARDS` 参数。

### Q: 如何添加新的历史人物？

A: 在 `references/historical-characters.md` 中添加人物档案。

### Q: 如何自定义视觉风格？

A: 修改 `execute` 调用时的 `style` 参数，或在配置文件中设置默认风格。

## 许可证

MIT License
