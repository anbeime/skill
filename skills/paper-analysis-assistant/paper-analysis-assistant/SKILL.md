---
name: paper-analysis-assistant
description: 根据arXiv论文网址自动下载PDF并进行多维度分析，包括文本提取、词频分析、语音播报、播客对话生成、交互式网页、PPT、总结图和引用分析
dependency:
  python:
    - requests==2.31.0
    - pdfplumber==0.10.3
    - python-pptx==0.6.23
    - pandas==2.1.4
    - pyttsx3==2.90
    - beautifulsoup4==4.12.2
    - nltk==3.8.1
---

# 论文分析助手

## 任务目标
- 本 Skill 用于:根据 arXiv 论文网址自动进行多维度分析并生成多种格式的输出
- 能力包含:PDF 下载与文本提取、词频统计、语音合成、播客对话生成、交互式网页、PPT 生成、总结图生成、引用分析
- 触发条件:用户提供 arXiv 论文网址或论文 PDF 文件

## 前置准备
- 依赖说明:所需 Python 包已在 dependency 中列出
- 停用词资源:需准备英文停用词列表，用于词频分析过滤

## 操作步骤
- 标准流程:
  1. **下载 PDF 文件**
     - 调用 `scripts/download_pdf.py` 下载 arXiv PDF
     - 参数:`--url` (arXiv 论文网址), `--output` (输出 PDF 文件路径)
  2. **提取 PDF 文本**
     - 调用 `scripts/extract_text.py` 提取纯文本
     - 参数:`--pdf` (PDF 文件路径), `--output` (输出 txt 文件路径)
  3. **词频分析**
     - 调用 `scripts/analyze_word_frequency.py` 进行词频统计
     - 参数:`--txt` (txt 文件路径), `--output` (输出 csv 文件路径)
     - 该脚本会自动过滤英文停用词（见 references/stopwords.txt）
  4. **文本转语音**
     - 调用 `scripts/text_to_speech.py` 将文本转为语音
     - 参数:`--txt` (txt 文件路径), `--output` (输出 wav 文件路径)
  5. **生成播客对话**
     - **智能体步骤**:根据论文内容生成双人对话脚本（包含两个角色的对话内容）
     - **脚本步骤**:调用 `scripts/dialogue_to_podcast.py` 将对话脚本转换为语音
     - 参数:`--dialogue` (对话脚本文件路径), `--output` (输出 wav 文件路径)
  6. **生成交互式网页**
     - 调用 `scripts/generate_html.py` 生成交互式网页
     - 参数:`--txt` (txt 文件路径), `--word_freq` (词频 csv 文件路径), `--output` (输出 html 文件路径)
  7. **生成 PPT**
     - 调用 `scripts/generate_ppt.py` 生成演示文稿
     - 参数:`--txt` (txt 文件路径), `--output` (输出 pptx 文件路径)
  8. **生成总结图**
     - **智能体步骤**:根据论文内容直接生成"一图胜千言"的总结图（PNG 格式）
  9. **分析引用链接**
     - 调用 `scripts/extract_references.py` 提取引用链接
     - 参数:`--txt` (txt 文件路径), `--output` (输出 csv 文件路径)

- 可选分支:
  - 当 用户直接提供 PDF 文件:跳过步骤 1，直接从步骤 2 开始
  - 当 用户只需要部分分析:根据需求选择性执行对应步骤

## 资源索引
- 下载脚本:见 [scripts/download_pdf.py](scripts/download_pdf.py)(用途:下载 arXiv PDF)
- 文本提取:见 [scripts/extract_text.py](scripts/extract_text.py)(用途:提取 PDF 纯文本)
- 词频分析:见 [scripts/analyze_word_frequency.py](scripts/analyze_word_frequency.py)(用途:统计词频并过滤停用词)
- 语音合成:见 [scripts/text_to_speech.py](scripts/text_to_speech.py)(用途:文本转语音)
- 播客生成:见 [scripts/dialogue_to_podcast.py](scripts/dialogue_to_podcast.py)(用途:对话脚本转语音)
- 网页生成:见 [scripts/generate_html.py](scripts/generate_html.py)(用途:生成交互式 HTML)
- PPT 生成:见 [scripts/generate_ppt.py](scripts/generate_ppt.py)(用途:生成 PPT 演示文稿)
- 引用提取:见 [scripts/extract_references.py](scripts/extract_references.py)(用途:提取引用链接)
- 停用词表:见 [references/stopwords.txt](references/stopwords.txt)(用途:词频分析时的停用词过滤)

## 注意事项
- 确保所有脚本参数路径正确，特别是输入输出文件的相对路径
- 语音合成功能需要系统支持语音引擎（pyttsx3）
- 播客对话的脚本内容由智能体生成，需确保对话格式正确
- 总结图由智能体直接生成，无需调用脚本

## 使用示例
- 示例 1:完整分析流程
  ```bash
  # 下载 PDF
  python scripts/download_pdf.py --url "https://arxiv.org/abs/2301.00001" --output ./user-data/paper.pdf
  # 提取文本
  python scripts/extract_text.py --pdf ./user-data/paper.pdf --output ./user-data/paper.txt
  # 词频分析
  python scripts/analyze_word_frequency.py --txt ./user-data/paper.txt --output ./user-data/word_freq.csv
  # 语音合成
  python scripts/text_to_speech.py --txt ./user-data/paper.txt --output ./user-data/paper.wav
  # 播客对话（智能体生成对话脚本后）
  python scripts/dialogue_to_podcast.py --dialogue ./user-data/dialogue.txt --output ./user-data/podcast.wav
  # 生成网页
  python scripts/generate_html.py --txt ./user-data/paper.txt --word_freq ./user-data/word_freq.csv --output ./user-data/analysis.html
  # 生成 PPT
  python scripts/generate_ppt.py --txt ./user-data/paper.txt --output ./user-data/presentation.pptx
  # 提取引用
  python scripts/extract_references.py --txt ./user-data/paper.txt --output ./user-data/references.csv
  ```
- 示例 2:快速分析（仅词频和引用）
  ```bash
  python scripts/analyze_word_frequency.py --txt ./user-data/paper.txt --output ./user-data/word_freq.csv
  python scripts/extract_references.py --txt ./user-data/paper.txt --output ./user-data/references.csv
  ```
