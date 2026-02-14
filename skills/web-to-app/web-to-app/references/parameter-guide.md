# Pake 参数配置指南

## 目录
- [基础参数](#基础参数)
- [窗口配置](#窗口配置)
- [外观设置](#外观设置)
- [高级选项](#高级选项)
- [平台特定选项](#平台特定选项)
- [开发调试](#开发调试)

## 概览
本文档详细说明 Pake 打包工具的所有参数，帮助你根据需求定制应用。

## 基础参数

### url
**必需参数**：要打包的网页 URL 或本地 HTML 文件路径

```bash
pake https://github.com
pake ./index.html
```

### name
**可选参数**：应用名称

- 默认：会提示输入
- 推荐：使用英文名称
- 多词命名：
  - Windows/macOS：保留空格和大小写（如 `"Google Translate"`）
  - Linux：转换为小写带连字符（如 `"google-translate"`）

```python
build_app(url="https://example.com", name="MyApp")
```

### icon
**可选参数**：自定义图标

- 支持格式：
  - 本地文件：`./my-icon.png`
  - 远程 URL：`https://example.com/icon.png`
- 自动转换：
  - macOS：`.icns` 格式
  - Windows：`.ico` 格式
  - Linux：`.png` 格式
- 不提供时：自动获取网站图标

```python
build_app(
    url="https://example.com",
    name="MyApp",
    icon="https://example.com/icon.png"
)
```

### app-version
**可选参数**：应用版本号

- 默认：`1.0.0`
- 格式：需符合语义化版本规范（如 `1.2.3`）

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"app-version": "2.0.0"}
)
```

## 窗口配置

### width / height
**可选参数**：窗口初始尺寸

- `width`：默认 1200px
- `height`：默认 780px

```python
build_app(
    url="https://example.com",
    name="MyApp",
    width=1400,
    height=900
)
```

### min-width / min-height
**可选参数**：窗口最小尺寸

- 防止窗口过小导致布局破坏
- 保持界面可用性

```python
build_app(
    url="https://example.com",
    name="MyApp",
    min_width=800,
    min_height=600
)
```

### zoom
**可选参数**：初始页面缩放级别

- 范围：50-200
- 默认：100
- 用户仍可通过快捷键调整

```python
build_app(
    url="https://example.com",
    name="MyApp",
    zoom=120  # 120%
)
```

### fullscreen
**可选参数**：全屏启动

- 默认：`false`
- 启用后应用以全屏模式启动

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"fullscreen": True}
)
```

### maximize
**可选参数**：最大化启动

- 默认：`false`
- 启用后应用以最大化窗口启动

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"maximize": True}
)
```

### always-on-top
**可选参数**：窗口置顶

- 默认：`false`
- 启用后窗口始终显示在最上层

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"always-on-top": True}
)
```

## 外观设置

### hide-title-bar
**可选参数**：隐藏标题栏（仅 macOS）

- 默认：`false`
- 启用后实现沉浸式头部

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"hide-title-bar": True}
)
```

### dark-mode
**可选参数**：强制深色模式（仅 macOS）

- 默认：`false`
- 启用后应用使用深色主题

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"dark-mode": True}
)
```

## 高级选项

### multi-instance
**可选参数**：允许多实例

- 默认：`false`
- 启用后可同时打开多个应用窗口
- 适用于聊天应用、工具类应用

```python
build_app(
    url="https://chat.example.com",
    name="ChatApp",
    options={"multi-instance": True}
)
```

### activation-shortcut
**可选参数**：激活快捷键

- 默认：空（不生效）
- 格式：`CmdOrControl+Shift+P`
- 可用修饰符：`CmdOrControl`、`Cmd`、`Ctrl`、`Shift`、`Alt`、`Option`

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"activation-shortcut": "CmdOrControl+Shift+P"}
)
```

### force-internal-navigation
**可选参数**：强制内部导航

- 默认：`false`
- 启用后所有链接在 Pake 窗口内打开
- 不会调用外部浏览器

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"force-internal-navigation": True}
)
```

### disabled-web-shortcuts
**可选参数**：禁用网页快捷键

- 默认：`false`
- 启用后禁用原网页的快捷键
- 避免与应用快捷键冲突

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"disabled-web-shortcuts": True}
)
```

### new-window
**可选参数**：允许新窗口

- 默认：`false`
- 启用后允许第三方登录授权打开新窗口

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"new-window": True}
)
```

### inject
**可选参数**：注入自定义文件

- 支持注入 CSS 和 JS 文件
- 可用于广告拦截、UI 优化、功能扩展
- 支持单个文件、逗号分隔或多次指定

```python
# 单个文件
build_app(
    url="https://example.com",
    name="MyApp",
    options={"inject": "./style.css"}
)

# 多个文件（逗号分隔）
build_app(
    url="https://example.com",
    name="MyApp",
    options={"inject": "./style.css,./script.js"}
)

# 多个文件（列表格式）
build_app(
    url="https://example.com",
    name="MyApp",
    options={"inject": ["./style.css", "./script.js"]}
)
```

### proxy-url
**可选参数**：代理服务器

- 支持 HTTP、HTTPS、SOCKS5
- macOS 需 14+ 版本

```python
# HTTP 代理
build_app(
    url="https://example.com",
    name="MyApp",
    options={"proxy-url": "http://127.0.0.1:7890"}
)

# SOCKS5 代理
build_app(
    url="https://example.com",
    name="MyApp",
    options={"proxy-url": "socks5://127.0.0.1:7891"}
)
```

### use-local-file
**可选参数**：递归复制本地文件

- 默认：`false`
- 当 URL 是本地文件路径时，启用后会复制包含该文件的文件夹及所有子文件
- 用于打包静态网页应用

```python
build_app(
    url="./my-app/index.html",
    name="MyApp",
    options={"use-local-file": True}
)
```

## 平台特定选项

### multi-arch
**可选参数**：多架构支持（仅 macOS）

- 默认：`false`
- 启用后同时支持 Intel 和 M1 芯片
- 打包时间会显著增加

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"multi-arch": True}
)
```

### targets
**可选参数**：目标平台（Linux）

- 可选值：`appimage`、`deb`
- 默认：根据系统自动选择

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"targets": "appimage"}
)
```

### installer-language
**可选参数**：安装包语言（Windows）

- 默认：`en-US`
- 可选值：`zh-CN`、`ja-JP` 等（详见 [Tauri 文档](https://tauri.app/distribute/windows-installer/#internationalization)）

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"installer-language": "zh-CN"}
)
```

### show-system-tray
**可选参数**：显示系统托盘（Windows）

- 默认：`false`
- 启用后在系统托盘显示应用图标

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"show-system-tray": True}
)
```

## 开发调试

### debug
**可选参数**：调试模式

- 默认：`false`
- 启用开发者工具和详细日志
- 用于问题排查和功能测试

```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={"debug": True}
)
```

### ignore-certificate-errors
**可选参数**：忽略证书错误

- 默认：`false`
- 适用于内网应用、开发服务器、自签名证书
- 生产环境不推荐使用

```python
build_app(
    url="https://internal.example.com",
    name="MyApp",
    options={"ignore-certificate-errors": True}
)
```

## 完整示例

### 示例 1：基础配置
```python
build_app(
    url="https://github.com",
    name="GitHub"
)
```

### 示例 2：自定义窗口
```python
build_app(
    url="https://chat.openai.com",
    name="ChatGPT",
    icon="https://example.com/icon.png",
    width=1400,
    height=900
)
```

### 示例 3：高级配置
```python
build_app(
    url="https://example.com",
    name="MyApp",
    width=1200,
    height=800,
    min_width=800,
    min_height=600,
    zoom=100,
    options={
        "hide-title-bar": True,
        "always-on-top": False,
        "multi-instance": True,
        "activation-shortcut": "CmdOrControl+Shift+M",
        "debug": True
    }
)
```

### 示例 4：注入自定义脚本
```python
build_app(
    url="https://example.com",
    name="MyApp",
    options={
        "inject": ["./adblock.js", "./custom-style.css"]
    }
)
```

## 注意事项

1. **首次打包较慢**：需要下载和编译 Rust 依赖，后续打包会快很多
2. **输出位置**：默认在当前工作目录生成应用安装包
3. **平台差异**：不同平台的参数支持略有不同
4. **调试建议**：遇到问题时使用 `debug` 参数查看详细日志
5. **网络安全**：使用代理时确保代理服务器安全可靠

## 常见问题

**Q: 如何减少应用体积？**
A: Pake 生成的应用已经非常小（约 5MB），这是 Electron 的 1/20。

**Q: 支持哪些平台？**
A: 支持 macOS、Windows、Linux 三大平台。

**Q: 如何更新应用？**
A: 重新打包即可，版本号通过 `app-version` 参数控制。

**Q: 打包失败怎么办？**
A: 检查网络连接、Node.js 和 Rust 版本，使用 `debug` 参数查看详细日志。
