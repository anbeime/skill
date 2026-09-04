<div align="center">

# 🎨 Photo Abstract Editorial

**将一张照片转化为「原始摄影区域 + 抽象记忆面板 + 诗意英文标题」的竖向编辑作品**

[![Codex Skill](https://img.shields.io/badge/Codex-Skill-000000?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/ZzzLc0405/photo-abstract-editorial)
[![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey?style=for-the-badge)](./LICENSE.md)
[![Language](https://img.shields.io/badge/🌐_中文-English-blue?style=for-the-badge)](#)

</div>

---

## ⚠️ 声明

> **Free for personal, educational and non-commercial use.**
> Commercial use is not allowed.
>
> If you build something with these Skills, attribution and **@AM.** are greatly appreciated.

<details>
<summary>💬 作者的话</summary>

在这里吐槽一下，真的很无语这几天，被人抄袭，甚至有人拿这个东西去卖，我真的无语！

</details>

---

## 📖 关于本项目

这是一个 **Codex Skill**，它能将一张照片转化为「原始摄影区域 + 抽象记忆面板 + 诗意英文标题」的竖向编辑作品。

- ✅ 保留照片的**真实内容**
- ✅ 仅从照片本身提炼**空间关系、构图节奏和色彩关系**
- ❌ 不是滤镜、照片重画或风格迁移

> 📝 The skill includes the complete prompt in both **Chinese** and **English**.

---

## 🖼️ 示例作品

> 原图均为本人拍摄

<p align="center">
  <img src="./assets/examples/case-10.jpg" width="31%" align="top" alt="Case 3">
  <img src="./assets/examples/case-3.jpg" width="31%" align="top" alt="Case 1">
  <img src="./assets/examples/case-1.jpg" width="31%" align="top" alt="Case 7">
  <br><br>
  <img src="./assets/examples/case-11.jpg" width="31%" align="top" alt="Case 6">
  <img src="./assets/examples/case-9.jpg" width="31%" align="top" alt="Case 2">
  <img src="./assets/examples/case-6.jpg" width="31%" align="top" alt="Case 8">
</p>

---

## 📋 目录

- [使用方法](#-使用方法)
- [可自由调整的部分](#-可自由调整的部分)
- [核心原则](#-核心原则)
- [内容结构](#-内容结构)
- [许可证](#-许可证)

---

## 🚀 使用方法

### 方式一：作为 Codex Skill 使用

1. 将整个 `photo-abstract-editorial` 文件夹复制到你的 Codex skills 目录，例如 `~/.codex/skills/`
2. 开启新的 Codex 对话，上传一张希望处理的照片
3. 直接提出需求，例如：

   > 使用 `photo-abstract-editorial` 将这张照片制作成摄影与抽象面板组合的编辑作品。

4. Skill 会将原图保留在成品的上方或主要区域，并在下方创建由原图关系推导出的极简抽象面板。成品中只保留一个原创英文标题（可选副标题）。

### 方式二：作为提示词直接使用

也可以直接打开下列文件，并将其作为图像生成提示词使用：

| 语言 | 文件 |
| :---: | :--- |
| 🇨🇳 中文 | [references/photo-abstract-editorial-prompt.zh-CN.md](references/photo-abstract-editorial-prompt.zh-CN.md) |
| 🇬🇧 English | [references/photo-abstract-editorial-prompt.en.md](references/photo-abstract-editorial-prompt.en.md) |

---

## 🎛️ 可自由调整的部分

这套提示词应当被视为**高质量起点**，而不是不可变的版式规范。请按自己的审美和项目需求修改以下参数：

| 参数 | 说明 |
| :--- | :--- |
| **📐 照片与面板的比例** | 可调整摄影区域和抽象面板的高度占比、画布比例，以及抽象母题的大小与留白 |
| **🎨 颜色** | 可修改象牙色面板背景、照片提取色的饱和度、主色与强调色的数量和倾向 |
| **✏️ 抽象形式** | 可选择或混合色块、柔和有机质量、弧形笔触、短条、层叠色带、简化建筑质量、细线、点状标记等形式 |
| **📝 版式与文字** | 可调整母题位置、标题位置、字体气质、标题长度和是否使用副标题 |
| **🔍 抽象程度** | 可根据题材在「关系优先」和「保留少量身份特征」之间调整，例如让地标建筑或小型物件保留更多辨识线索 |

---

## 💡 核心原则

调整时建议保留两条核心原则：

1. **上传照片始终是唯一内容来源** — 照片区域不应被重画、扩展或改写
2. **抽象面板可追溯** — 每个重要元素都应能追溯到原照片中真实存在的空间、色彩或结构事实

---

## 📁 内容结构

```text
photo-abstract-editorial/
├── SKILL.md                         # Skill 工作流程与约束
├── agents/openai.yaml               # Codex 界面元数据
├── references/
│   ├── photo-abstract-editorial-prompt.zh-CN.md
│   └── photo-abstract-editorial-prompt.en.md
└── assets/examples/                 # 示例图片
```

> ⚠️ `assets/examples` 中的图片仅用于理解预期输入类型；除非用户上传该图片本身，否则不要将其中的主题、色彩或构图复用于新的作品。

---

## 📄 许可证

本项目采用 [LICENSE.md](./LICENSE.md) 中规定的许可证。

---

<div align="center">

**如果这个项目对你有帮助，欢迎 Star ⭐ 支持！**

</div>
请作者充点Token（coffee）
<p align="center">
  <img src="./pay/AliPay.jpg" width="32%">
  <img src="./pay/WechatPay.jpg" width="32%">
</p>
<!-- 
## 声明
Free for personal, educational and non-commercial use. Commercial use requires prior authorization. If you build something with these Skills, attribution and @AM. are greatly appreciated.

商业授权已不被允许，请不要私自商用，谢谢！
douyin: 12919593  xiaohongshu: Cclz_9

在这里吐槽一下，真的很无语这几天，被人抄袭，甚至有人拿这个东西去卖，我真的无语！

# Photo Abstract Editorial

将一张照片转化为“原始摄影区域 + 抽象记忆面板 + 诗意英文标题”的竖向编辑作品的 Codex Skill。它保留照片的真实内容，并仅从照片本身提炼空间关系、构图节奏和色彩关系；它不是滤镜、照片重画或风格迁移。

The skill includes the complete prompt in both Chinese and English.

## 示例图片（原图均为本人拍摄）

<table>
  <tr>
    <td><img src="./assets/examples/case-3.jpg" width="100%"></td>
    <td><img src="./assets/examples/case-1.jpg" width="100%"></td>
    <td><img src="./assets/examples/case-7.jpg" width="100%"></td>
  </tr>
  <tr>
    <td><img src="./assets/examples/case-2.jpg" width="100%"></td>
    <td><img src="./assets/examples/case-6.jpg" width="100%"></td>
    <td><img src="./assets/examples/case-8.jpg" width="100%"></td>
   
  </tr>
</table> 
<p align="center">
  <img src="./assets/examples/case-3.jpg" width="32%">
  <img src="./assets/examples/case-1.jpg" width="32%">
  <img src="./assets/examples/case-7.jpg" width="32%">
  <br>
  <img src="./assets/examples/case-6.jpg" width="32%">
  <img src="./assets/examples/case-2.jpg" width="32%">
  <img src="./assets/examples/case-8.jpg" width="32%">
</p>
## 使用方法

1. 将整个 `photo-abstract-editorial` 文件夹复制到你的 Codex skills 目录，例如 `~/.codex/skills/`。
2. 开启新的 Codex 对话，上传一张希望处理的照片。
3. 直接提出需求，例如：

   > 使用 `photo-abstract-editorial` 将这张照片制作成摄影与抽象面板组合的编辑作品。

4. Skill 会将原图保留在成品的上方或主要区域，并在下方创建由原图关系推导出的极简抽象面板。成品中只保留一个原创英文标题（可选副标题）。

也可以直接打开下列文件，并将其作为图像生成提示词使用：

- 中文版：[references/photo-abstract-editorial-prompt.zh-CN.md](references/photo-abstract-editorial-prompt.zh-CN.md)
- English version: [references/photo-abstract-editorial-prompt.en.md](references/photo-abstract-editorial-prompt.en.md)

## 可自由调整的部分

这套提示词应当被视为高质量起点，而不是不可变的版式规范。请按自己的审美和项目需求修改以下参数：

- **照片与面板的比例**：可调整摄影区域和抽象面板的高度占比、画布比例，以及抽象母题的大小与留白。
- **颜色**：可修改象牙色面板背景、照片提取色的饱和度、主色与强调色的数量和倾向。
- **抽象形式**：可选择或混合色块、柔和有机质量、弧形笔触、短条、层叠色带、简化建筑质量、细线、点状标记等形式。
- **版式与文字**：可调整母题位置、标题位置、字体气质、标题长度和是否使用副标题。
- **抽象程度**：可根据题材在“关系优先”和“保留少量身份特征”之间调整，例如让地标建筑或小型物件保留更多辨识线索。

调整时建议保留两条核心原则：

1. 上传照片始终是唯一内容来源，照片区域不应被重画、扩展或改写。
2. 抽象面板中的每个重要元素都应能追溯到原照片中真实存在的空间、色彩或结构事实。

## 内容结构

```text
photo-abstract-editorial/
├── SKILL.md                         # Skill 工作流程与约束
├── agents/openai.yaml               # Codex 界面元数据
├── references/
│   ├── photo-abstract-editorial-prompt.zh-CN.md
│   └── photo-abstract-editorial-prompt.en.md
└── assets/examples/                 # 5 张示例图片
```

`assets/examples` 中的图片仅用于理解预期输入类型；除非用户上传该图片本身，否则不要将其中的主题、色彩或构图复用于新的作品。
-->
