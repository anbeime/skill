# URL 获取与时间轴

当输入是 YouTube 等在线视频链接，而不是本地视频时，读取本文件。`yt-dlp` 只负责获取用户有权处理的视频、元数据和字幕时间轴；最终图片仍由 `native_subtitle_stitch.py` 从真实视频帧生成。

不要因为第一次公开请求被 YouTube 拒绝，就告诉用户“这个 Skill 只能读取本地视频”。URL 获取本来就是此 Skill 的正式入口：先尝试无 Cookie 公开访问；若命中登录或机器人验证，再走本文的 Chrome Cookie 授权流程。

## 先区分两种“字幕”

| 内容 | 用途 | 原生字幕模式 | 脚本字幕模式 |
|---|---|---|---|
| 画面内烧录字幕 | 保留原字幕 | 必须从真实视频帧保留 | 如与后期文字重叠，应换帧或换模式 |
| YouTube 字幕轨、VTT/SRT、Whisper 文字稿 | 理解内容、选题、定位时间点 | 只做索引，不能画进成品 | 经复核后可写入 `lines[].text`，必须标记为后期台词 |

有字幕轨不等于视频画面有字幕。下载后必须实际取帧检查。若用户要求原生字幕，但画面没有烧录字幕，停止并说明；只有用户同意后，才使用本 Skill 的 `render-script` 模式，不要偷偷切换。

## 官方依据

- [yt-dlp 官方 README](https://github.com/yt-dlp/yt-dlp#readme)
- [安装说明](https://github.com/yt-dlp/yt-dlp/wiki/Installation)
- [External JavaScript 指南](https://github.com/yt-dlp/yt-dlp/wiki/EJS)

yt-dlp 当前支持 CPython 3.10+ 和 PyPy 3.11+。完整 YouTube 支持强烈建议 FFmpeg、`yt-dlp-ejs` 和 JavaScript runtime。官方优先推荐 Deno，并默认启用它；Node.js 或 QuickJS 需要通过 `--js-runtimes` 显式启用。Bun 目前仍可用，但官方已将其支持标记为弃用，不应作为新环境首选。

## 环境检查

先运行 Skill 自带的只读诊断：

```bash
python3 "<SKILL_DIR>/scripts/check_environment.py" --url-mode
```

如果要绘制中日韩台词，同时检查 CJK 字体：

```bash
python3 "<SKILL_DIR>/scripts/check_environment.py" --url-mode --script-mode
```

它不会安装软件，只报告：

- Python、Pillow、FFmpeg provider 是否可用；
- `yt-dlp` 版本；
- Deno 或其他 JavaScript runtime；
- 脚本模式所需的 CJK 字体（使用 `--script-mode` 时）；
- 可选的 Whisper/语音识别能力。

缺少组件时先向用户说明，再取得安装授权。不要擅自修改系统 Python、包管理器或 shell 配置。

### 安装与更新原则

- 核心渲染依赖：`python3 -m pip install -r "<SKILL_DIR>/requirements.txt"`。
- yt-dlp 可使用官方独立可执行文件，或安装 PyPI 的 `yt-dlp[default]`；`default` extra 会带上官方推荐的 Python 依赖。
- 官方文档当前建议普通用户使用 nightly；若稳定版遇到站点解析问题，先按官方说明更新 nightly，再判断是不是命令或权限问题。
- Deno 使用官方安装方式，当前最低支持 2.3.0；若环境已有 Node.js 22+，可保留 Node，并在每条 yt-dlp 命令中加入 `--js-runtimes node`。

示例（使用 pip 的环境）：

```bash
python3 -m pip install -U "yt-dlp[default]"
```

稳定版出现站点解析错误、且用户同意更新时：

```bash
python3 -m pip install -U --pre "yt-dlp[default]"
```

不要把“安装成功”和“能解析当前链接”混为一谈；安装后至少运行：

```bash
yt-dlp --version
yt-dlp --no-playlist --skip-download --print "%(id)s | %(title)s | %(duration_string)s" "URL"
```

## 获取顺序

### 1. 只读检查元数据

```bash
yt-dlp --no-playlist --skip-download \
  --print "%(id)s | %(title)s | %(channel)s | %(duration_string)s" \
  "URL"
```

使用 Node.js 时：

```bash
yt-dlp --js-runtimes node --no-playlist --skip-download \
  --print "%(id)s | %(title)s | %(channel)s | %(duration_string)s" \
  "URL"
```

先确认链接指向单个目标视频。默认添加 `--no-playlist`，避免一个播放列表被意外整批下载。

### 2. 列出字幕轨

```bash
yt-dlp --no-playlist --list-subs "URL"
```

记录可用语言标签，不要假设一定叫 `zh`、`en` 或 `en-orig`。

### 3. 只下载文字时间轴

优先人工字幕，同时允许自动字幕作为备选：

```bash
yt-dlp --no-playlist --skip-download \
  --write-subs --write-auto-subs \
  --sub-langs "zh.*,en.*" --sub-format vtt \
  -o "source/%(id)s/%(id)s.%(ext)s" \
  "URL"
```

字幕和视频始终分两条命令下载：字幕命令带 `--skip-download`，视频命令不带任何 `--write-*subs` 参数。这样字幕请求失败（例如 429）不会中止视频下载，视频格式出错也不会白白重复请求字幕。

`zh.*` 这类正则会同时匹配 YouTube 的自动翻译轨（标签形如 `zh-Hans-en`），这类轨道最容易触发 HTTP 429。先看 `--list-subs` 的真实标签，只请求需要的一两个，例如人工字幕 `zh-Hans` 和原声自动字幕 `en-orig`；请求多个语言时加 `--sleep-subtitles 5`。

字幕轨先用来建立“内容—时间点”索引。原生模式不把 VTT 画回图片，也不因为文字稿里有一句话，就假设该时刻画面内烧录字幕完全相同。脚本模式可以使用已复核的 VTT/SRT/Whisper 文字，但必须标明为后期绘制，并将人名、数字、专有名词和翻译含义单独核对。

#### 自动字幕的滚动重复

YouTube 自动字幕（含 `en-orig` 等原声轨）是滚动显示的：VTT 里相邻条目常重复上一行文字，同一句话会出现在两三个条目里，条目开始时间也早于该句在画面上完整显示的时刻。直接拿条目开始时间取帧，容易截到上一句或对方的话，看起来像顺序错乱。使用前先：

1. 去重：合并文字相同或前缀包含关系的相邻条目，每句只保留一条，开始时间取该句首次出现的时间，结束时间取最后一次出现的时间；
2. 用去重后条目的中段而不是开始时间作为候选时间点，再用 `sample -t ... --around 0.8` 回看确认；
3. 自动字幕不分说话人，多人对话素材还要按 [end-to-end-workflow.md](end-to-end-workflow.md#多人对话与访谈先标说话人) 补标说话人。

人工字幕一般没有滚动重复，但同样不带说话人。

### 4. 下载视频

通常不需要 4K。1080p 足以做 1440×1920 的社交图；输出尺寸可能放大，但不应宣称提升了真实清晰度。

```bash
yt-dlp --no-playlist \
  -f "bv*[height<=1080]+ba/b[height<=1080]" \
  -o "source/%(id)s/%(id)s.%(ext)s" \
  "URL"
```

`/` 只在格式**不存在**时生效；某个格式存在但下载时返回 HTTP 403，yt-dlp 不会自动改用下一项。遇到 403 时先更新 yt-dlp 并重试一次，仍失败就按下表逐级换一条 `-f` 重新下载，每级只试一次：

| 级别 | `-f` 参数 | 说明 |
| --- | --- | --- |
| 1 | `bv*[height<=1080][vcodec^=av01]+ba` | 1080p AV1，优先 |
| 2 | `bv*[height<=1080][vcodec^=vp09]+ba` | 1080p VP9 |
| 3 | `bv*[height<=1080][vcodec^=avc1]+ba[ext=m4a]` | 1080p H.264 + AAC，兼容性最好 |
| 4 | `bv*[height<=1080]+ba` | 1080p 任意编码 |
| 5 | `bv*[height<=720]+ba` | 降到 720p 的分离流 |
| 6 | `b[height<=1080]` | 已合并的单文件；YouTube 上通常只剩 360p |
| 7 | `b` | 任意可用的单文件，最后手段 |

下载前先运行 `yt-dlp --no-playlist -F "URL"` 枚举变体，按 AV1 → VP9 → H.264 的顺序择优，并确认列表里有不低于 720p 的视频流。第 5~7 级实际分辨率可能低于 720p：**必须先向用户说明实际分辨率并取得确认，不得静默接受**；用户不接受就停止并报告。

每次下载后立刻自检，通过后才能抽帧、渲染：

```bash
python3 "<SKILL_DIR>/scripts/native_subtitle_stitch.py" check-source VIDEO --min-height 720
```

`check-source` 读取分辨率，并用 FFmpeg 解码前 N 秒（`--seconds`，默认 10），出现任何解码错误（例如 h264 mmco 报错）或低于 `--min-height` 就以非零状态退出。不传 `--min-height` 时，低于 720p 只警告。自检失败的文件删除后，换下一级变体重试，每级只试一次。

每次尝试（含 403、自检失败）都追加一行到工作目录的 `download-attempts.log`，记录级别、`-f` 参数、结果（成功 / HTTP 403 / 自检失败 / 用户拒绝低清）和错误摘要。所有级别用尽就停止，把日志内容报告给用户，不要继续尝试 extractor 参数。

分离的视频和音频需要 FFmpeg 合并。原生字幕取帧不依赖音频，但保留带音频的完整源文件方便复核内容。重复执行时复用已有文件，不要无理由重新下载。

## 没有可用字幕轨

按以下顺序处理：

1. 检查视频描述、章节和人工字幕轨；
2. 检查自动字幕轨；
3. 如果画面本身有烧录字幕，可先用候选帧总览人工选句；
4. 用户确实需要长视频的语义选段时，再询问是否允许使用本地 Whisper 或环境中已有的语音转写 Skill。

Whisper 是可选上游，用来生成带时间戳文字稿。它的识别文本不能替代画面内原生字幕；脚本模式需要使用它时，也必须先校对文本，并回到视频帧验证时间点。

## 登录、Cookies 与访问限制

- 只处理用户有权访问、下载和再利用的内容。
- 先执行一次不带 Cookie 的元数据检查。不要把 Cookie 作为所有公开视频的默认参数。
- 遇到 `Sign in to confirm you’re not a bot`、登录、年龄验证或用户自己的非公开视频时，不要退回“只能处理本地视频”；先说明原因并取得授权，再使用 `--cookies-from-browser chrome`。
- 不要求用户粘贴账号密码，不导出或提交 Cookie 文件，不把浏览器配置、访问令牌或绝对路径写入仓库。
- 不绕过 DRM、付费墙、地区限制或其他访问控制。
- Cookie 命令只用于当前来源获取，不得显示 Cookie 内容，也不得把 Cookie 写入日志、来源记录或交付物。
- Cookies 失败时停止并报告，不要遍历或反复尝试多个浏览器账户。

### Chrome Cookie 授权流程

只在无 Cookie 请求明确被访问验证拦截后执行：

1. 向用户复述真实错误，例如 YouTube 要求“登录以确认不是机器人”。
2. 询问：`是否允许我让 yt-dlp 临时读取 Chrome 中已登录的 YouTube Cookie？它只用于获取这个链接的视频和字幕，不会导出、保存或上传 Cookie。`
3. 用户明确同意后，把 `--cookies-from-browser chrome` 加到这个 URL 后续所有 yt-dlp 命令，而不是只加在第一次探测命令上。
4. 默认只读 Chrome 当前默认配置。若机器上有多个 Chrome 配置且默认配置无效，停止并询问用户要使用哪个配置；不要自行扫描所有配置。
5. 若用户拒绝，提供两种清晰选择：让用户自行下载视频后按本地模式继续，或结束 URL 任务。不要把这种受限后的备选说成 Skill 的固有限制。

授权后的元数据检查：

```bash
yt-dlp --cookies-from-browser chrome --js-runtimes node \
  --no-playlist --skip-download \
  --print "%(id)s | %(title)s | %(channel)s | %(duration_string)s" \
  "URL"
```

授权后的字幕轨检查与下载：

```bash
yt-dlp --cookies-from-browser chrome --js-runtimes node \
  --no-playlist --list-subs "URL"

yt-dlp --cookies-from-browser chrome --js-runtimes node \
  --no-playlist --skip-download \
  --write-subs --write-auto-subs \
  --sub-langs "zh.*,en.*" --sub-format vtt \
  -o "source/%(id)s/%(id)s.%(ext)s" \
  "URL"
```

授权后的视频下载：

```bash
yt-dlp --cookies-from-browser chrome --js-runtimes node \
  --no-playlist \
  -f "bv*[height<=1080]+ba/b[height<=1080]" \
  -o "source/%(id)s/%(id)s.%(ext)s" \
  "URL"
```

如果环境使用 Deno，删除 `--js-runtimes node` 即可，Cookie 规则不变。若默认 Chrome 配置不含有效 YouTube 会话，可在用户明确指定配置后使用 yt-dlp 支持的 `chrome:PROFILE` 形式；不要猜测配置名。读取失败、系统钥匙串拒绝访问或站点仍拒绝请求时，只重试一次经过用户确认的同一配置，然后停止并报告具体错误。

## 常见故障

### `yt-dlp` 有版本但 YouTube 格式不完整

先看诊断里是否存在 JavaScript runtime。Deno 默认启用；Node.js 环境必须显式添加：

```bash
yt-dlp --js-runtimes node ...
```

随后更新 yt-dlp。不要先改一串实验性 extractor 参数，因为这会让工作流难以复现。

### YouTube 要求登录以确认不是机器人

这是来源访问验证，不代表 Skill 只能处理本地视频。按“Chrome Cookie 授权流程”先取得用户授权，再让同一 URL 的元数据、字幕和视频命令都带上 `--cookies-from-browser chrome`。用户没有授权时才停止联网获取，并给出本地文件备选。

### 字幕语言下载不到

先运行 `--list-subs`，按真实语言标签修改 `--sub-langs`。不要把自动翻译字幕当成人工原字幕。

### 视频下载报 HTTP 403

403 通常只针对某个具体格式，或说明 yt-dlp 版本已落后于站点改动。先更新 yt-dlp 并确认 JavaScript runtime 生效，再按“下载视频”一节的格式回退表逐级重试。若所有格式都返回 403，且无 Cookie 的元数据请求也被拒，转到“登录、Cookies 与访问限制”处理，不要循环重试。

### 字幕下载报 HTTP 429

429 表示请求过于频繁，多见于自动翻译字幕轨。处理顺序：

1. 确认字幕命令与视频命令是分开的，视频下载不受影响。
2. 改用 `--list-subs` 中的具体标签，去掉自动翻译轨，只请求一两个语言。
3. 加 `--sleep-requests 1 --sleep-subtitles 5`，等待几分钟后重试一次。
4. 仍失败时，用已拿到的其他语言字幕定位时间点，或在用户同意后用 Whisper 转写；不要反复请求同一字幕轨。

### 视频下载成功，但图片里没有字幕

这不是取帧失败，而是原生字幕条件不成立。说明该视频只有独立字幕轨；若用户同意后期绘制，转用 `render-script`，否则停止。

### 下载很慢或中断

保留工作目录和分片，重试同一条命令以复用缓存。连续失败后报告网络或站点限制，不要无限重试。
