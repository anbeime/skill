---
name: web-to-app
description: 将任意网页转换为桌面应用，支持 macOS/Windows/Linux 三大平台。使用 Rust + Tauri 技术栈，生成的应用体积小（约 5MB）、性能高。支持自定义图标、窗口大小、快捷键等丰富配置。
dependency:
  python:
    - requests>=2.28.0
  system:
    - npm install -g pake-cli
---

# Web to App

## 任务目标
- 本 Skill 用于：将任意网页 URL 打包成原生桌面应用
- 能力包含：
  1. 自动检测并安装 pake-cli 工具
  2. 支持自定义应用名称、图标、窗口尺寸等配置
  3. 生成 macOS/Windows/Linux 平台的应用安装包
  4. 支持高级配置（隐藏标题栏、多实例、代理等）
- 触发条件：用户提出"将网页打包成应用"、"制作桌面应用"等需求

## 前置准备

### 环境要求
- **Node.js**：版本 ≥ 18.0.0（推荐 22.0+）
- **Rust**：≥ 1.85.0（首次使用会自动安装）
- **系统工具**：
  - macOS/Linux：需要 `curl`、`wget`、`file`、`tar`
  - Windows：自动处理依赖

### 安装依赖
首次使用前，需要安装 pake-cli 工具：
```bash
npm install -g pake-cli
# 或使用 pnpm（推荐）
pnpm install -g pake-cli
```

## 操作步骤

### 标准流程

1. **收集需求**
   - 确认网页 URL（必需）
   - 应用名称（建议英文）
   - 目标平台（自动检测当前系统）
   - 自定义需求（图标、窗口大小等）

2. **环境准备**
   - 调用 `scripts/install_pake.py` 检查并安装 pake-cli
   - 验证 Node.js 和 Rust 环境

3. **执行打包**
   - 根据用户需求生成配置参数
   - 调用 `scripts/build_app.py` 执行打包
   - 监控执行进度和错误信息

4. **输出验证**
   - 确认生成的应用安装包
   - 提供安装和使用说明

### 可选分支

- **当需要自定义图标**：
  - 提供图标文件路径（支持本地或远程 URL）
  - 自动转换为平台特定格式（.icns/.ico/.png）

- **当需要高级配置**：
  - 参考 [references/parameter-guide.md](references/parameter-guide.md)
  - 添加对应参数（如 `--hide-title-bar`、`--multi-instance`）

- **当打包失败**：
  - 检查网络连接（需要下载依赖）
  - 验证 Node.js 和 Rust 版本
  - 使用 `--debug` 参数查看详细日志

## 资源索引

### 必要脚本
- **[scripts/install_pake.py](scripts/install_pake.py)**
  - 用途：检查并安装 pake-cli 工具
  - 参数：无
  - 返回：安装状态和版本信息

- **[scripts/build_app.py](scripts/build_app.py)**
  - 用途：执行网页打包命令
  - 参数：
    - `url`：网页 URL（必需）
    - `name`：应用名称
    - `icon`：图标路径
    - `width`：窗口宽度
    - `height`：窗口高度
    - `options`：其他可选参数（字典格式）
  - 返回：生成的应用文件路径

### 领域参考
- **[references/parameter-guide.md](references/parameter-guide.md)**
  - 何时读取：需要配置高级选项时
  - 内容：完整的参数说明和使用示例

## 注意事项

- ⏰ **首次打包较慢**：需要下载和编译 Rust 依赖，后续打包会快很多
- 📦 **输出位置**：默认在当前工作目录（`./`）生成应用安装包
- 🖥️ **平台适配**：
  - macOS：生成 `.dmg` 安装包（设置 `PAKE_CREATE_APP=1` 可生成 `.app`）
  - Windows：生成 `.msi` 安装包
  - Linux：生成 `.deb` 或 `.AppImage` 包
- 🚀 **调试模式**：遇到问题时添加 `--debug` 参数查看详细日志
- 🔐 **证书问题**：如果是内网或自签名证书，使用 `--ignore-certificate-errors`

## 使用示例

### 示例 1：基础打包
**功能说明**：将 GitHub 网页打包成应用
**执行方式**：脚本调用

```python
from scripts.build_app import build_app

result = build_app(
    url="https://github.com",
    name="GitHub"
)
# 输出：GitHub.dmg / GitHub_x64.msi / GitHub_x86_64.deb
```

### 示例 2：自定义配置
**功能说明**：自定义窗口大小和图标
**执行方式**：脚本调用

```python
result = build_app(
    url="https://chat.openai.com",
    name="ChatGPT",
    icon="https://example.com/icon.png",
    width=1400,
    height=900,
    options={
        "hide-title-bar": True,
        "always-on-top": False
    }
)
```

### 示例 3：多实例应用
**功能说明**：允许同时打开多个应用窗口
**执行方式**：脚本调用

```python
result = build_app(
    url="https://example.com",
    name="MyApp",
    options={
        "multi-instance": True,
        "activation-shortcut": "CmdOrControl+Shift+P"
    }
)
```

## 快捷键说明

生成的应用内置以下快捷键：

| 操作 | macOS | Windows/Linux |
|------|-------|---------------|
| 刷新页面 | ⌘ + R | Ctrl + R |
| 隐藏窗口 | ⌘ + W | Ctrl + W |
| 放大/缩小 | ⌘ + +/- | Ctrl + +/- |
| 重置缩放 | ⌘ + 0 | Ctrl + 0 |
| 复制 URL | ⌘ + L | Ctrl + L |
| 返回首页 | ⌘ + Shift + H | Ctrl + Shift + H |
| 开发者工具 | ⌘ + Option + I | Ctrl + Shift + I（仅调试模式） |
| 清除缓存重启 | ⌘ + Shift + Delete | Ctrl + Shift + Delete |
