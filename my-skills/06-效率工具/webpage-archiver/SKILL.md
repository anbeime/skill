---
name: "webpage-archiver"
description: "封装完整网页（HTML+图片+CSS+JS）到本地归档。当用户提供URL需要保存网页离线副本、打包网页做公司背书存档、或批量归档网页内容时使用。保存到 D:\\家富三禾农林\\网页封装\\"
version: "1.0.0"
category: "效率工具"
tags: [网页归档, 离线保存, 封装]
author: "anbeime"
license: "MIT"
---

# 家富三禾农林 - 网页封装归档技能

## 功能说明

将指定网页完整下载（HTML + 图片 + CSS + JavaScript + 其他资源），重写资源引用为本地路径，生成离线可浏览的完整网页副本，并自动更新总索引。

## 保存位置

所有封装文件保存到: `D:\家富三禾农林\网页封装\`

每个网页单独一个文件夹，命名规则: `YYYY-MM-DD_标题`

## 使用方式

### 方式一：通过TRAE Agent（推荐）

直接告诉TRAE agent要封装的URL，例如：
- "帮我封装这个网页：https://example.com/page"
- "把这篇文章存档：https://example.com/article"
- "批量封装这些网址..."（提供多个URL）

### 方式二：命令行直接运行

```bash
python "D:\家富三禾农林\网页封装工具\html_packager.py" -u <URL> -n <自定义名称>
```

### 方式三：双击批处理脚本

双击 `D:\家富三禾农林\网页封装工具\封装网页工具.bat` 启动交互式菜单。

### 方式四：批量封装

准备一个文本文件（如 `D:\家富三禾农林\网页封装工具\urls_sample.txt`），每行一个URL，格式：
```
https://example.com/page1 | 自定义名称1
https://example.com/page2 | 自定义名称2
```

然后运行：
```bash
python "D:\家富三禾农林\网页封装工具\html_packager.py" -f <文件路径>
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `-u URL` | 要封装的网页URL |
| `-n 名称` | 自定义保存名称 |
| `-f 文件` | 批量文件路径 |
| `--no-images` | 不下载图片 |
| `--no-css` | 不下载CSS |
| `--no-js` | 不下载JS |
| `--list` | 列出所有已封装记录 |
| `--open-index` | 用浏览器打开总索引 |
| `-i` | 启动交互式模式 |
| `-d 目录` | 指定保存根目录 |

## 输出结构

```
D:\家富三禾农林\网页封装\
├── index.html              # 总索引页面（浏览器打开查看所有记录）
├── YYYY-MM-DD_标题1/
│   ├── index.html          # 离线网页（可直接打开浏览）
│   ├── _metadata.json      # 元信息（URL、时间、统计等）
│   └── _assets/
│       ├── images/         # 下载的图片
│       ├── css/            # 下载的样式
│       ├── js/             # 下载的脚本
│       └── other/          # 其他资源
├── YYYY-MM-DD_标题2/
│   └── ...
└── ...
```

## 注意事项

1. 首次使用前确保已安装依赖：`pip install requests beautifulsoup4 lxml`
2. 某些动态加载的网页（SPA、大量JS渲染）可能无法完整捕获
3. 受版权保护的网页请确认有存档权限
4. 建议封装后打开验证完整性
