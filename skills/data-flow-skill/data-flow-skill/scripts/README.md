# Scripts

本目录包含从原 dataflow 项目迁移来的可复用 Python 脚本。

## 目录结构

```text
scripts/
  analysis/                    # 数据检测、画像、预处理、统计分析、发现生成
  visualization/matplotlib/     # Matplotlib 静态图模板
  mermaid/                      # Mermaid 流程图生成与渲染辅助
  image_gen/                    # 主题示意图生成 CLI
```

## 安装依赖

在 `data-flow-skill` 目录下运行：

```bash
pip install -r requirements.txt
```

可选依赖：

- Node.js 与 `@mermaid-js/mermaid-cli`：用于 Mermaid 本地渲染。
- LaTeX：用于启用 `text.usetex` 的 Matplotlib 模板或 PDF 编译。
- `DASHSCOPE_API_KEY`：用于 `image_gen/image_generator.py` 调用图片生成服务。

## 使用约束

- 不要用一个脚本完成读取、清洗、分析、绘图和报告的完整链路。
- 每个脚本应服务一个明确子任务。
- 运行脚本前确认输入路径和输出路径。
- 输出建议写入 `output/` 下的对应子目录。
