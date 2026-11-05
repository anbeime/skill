---
name: ancient-rap-battle
description: 古人说唱 Battle：把两个历史上的死对头（诸葛亮 vs 司马懿、岳飞 vs 秦桧……）做成一条 AI 说唱对决短视频，从选题写词（每句配史料注释）、Suno 做歌、Midjourney 定妆、即梦 Seedance 2.5 网页版分段生成（提示词按半句精确到 0.01 秒写歌词，口型一次对好），到自动逐镜头对齐、拼接、字幕包装、封面和发布文案一条龙。用户说"做一期 A vs B"、"古人说唱 battle"、"历史人物说唱"、"rap battle 视频"，或者要改已有一期的歌词、镜头、字幕、封面时使用。Make an AI rap-battle short between two historical rivals, end to end, with Seedance 2.5 (or MiniMax H3).
---

# 古人说唱 Battle

两个古人在擂台上当面 diss。成片约 90 秒、16:9、2K，前奏 2.5 秒就开唱，两边各 16 句，每句底下一行史料出处。

## 0. 先说清楚的三件事

- **用户要有**：Suno 账号、Midjourney 账号、即梦会员（Seedance 2.5 网页版，按积分）。可选：MiniMax API Key 走 H3 路线
- **红线**：不用近现代政治人物、不用在世真人；脸不能像任何真实的人或演员。请求涉及这些时礼貌拒绝，建议换成古人
- **不碰别人的作品**：不帮去别人视频的水印、不搬运；拆解学习可以

全程用中文和用户说话。API Key 只通过环境变量传入，绝不写进文件或记忆。

## 工作区

每期一个文件夹（下面叫 `EP`），先 `python S/setup_check.py`（`S/` = 本 Skill 的 `scripts/`，Windows 用 `python`）。

```
EP/
  episode.json      ← 本期设定（从 examples/zhugeliang-vs-simayi/episode.json 复制改）
  01_歌词.md         ← 给用户看的歌词 + 注释 + 本期改动
  song.mp3  refs/*.png  音乐_最终.wav  字幕.srt
  seedance/NN_.../  ← 每段的素材包，用户把生成的视频下载回各自文件夹
  work/  preview/  final/  cover/
```

## 流程

### 第 1 步：选题与歌词（Claude 写，用户确认）

按 `references/lyrics-guide.md`：赢家后唱；**两边各 16 句、严格四句一换韵**；一句一个典故，句中用空格分前后半句；后唱的接住前面 3–4 句原话；**每句一个照字面演的动作**；**每句一条史料注释**（正史引原文，演义标明）。**写之前读往期歌词查重，同一人物不复用旧梗旧句式。**

先给用户纯歌词，再给注释，再给「本期改动」。用户挑出像旧梗的句子就换。定稿写进 `episode.json`（lyrics、notes、shots、look_cn、listen_cn、venue_cn）。

### 第 2 步：音乐（用户在 Suno 做）

按 `references/suno.md`：Advanced、Variety 拉到 0；**A 一段生成、挑好后 Extend 接 B 一段**（Extend from 设在 A 最后一句唱完处），Get Whole Song 下载 MP3 存成 `EP/song.mp3`。

### 第 3 步：歌曲分析与剪短

```
python S/analyze_song.py EP
```
看 line check（32 句都唱到）。然后**用 whisper 词时间查间奏**：Suno 常在口号后自己连唱一段 B 的第一句。剪间奏用 `retrim.py`，手法见 pitfalls.md「间奏拼接」——用户不接受任何停顿或卡顿：
```
python S/retrim.py EP --keep 7.36-53.64,63.63-109.8 [--mute ...] [--set b1=62.25]
```
把 `音乐_最终.wav` 发给用户听（接口、两人声音分不分得开；不开就 `pitch` 各 ±1 半音后重跑）。

### 第 4 步：定妆图（用户在 Midjourney 做）

按 `references/midjourney.md` 给 9 条提示词：两人各三视图 / 表情四宫格 / 半身（A 朝右、B 朝左），DJ、观众、场景（正面对称）。不做气氛组。逐张看图，复制改名进 `EP/refs/`。

### 第 5 步：素材包

```
python S/clean_vocal.py EP        # 更干净的人声，只给对口型用
python S/seedance_packs.py EP     # 生成 seedance/00_开场 … 10_片尾
```
每个唱歌的包：人声（从第一个字到下一句开口前，前补 0.3 秒静音）、半身 / 场景 / DJ / 表情图、提示词。**提示词里每个镜头写清「X.XX–X.XX 秒唱「半句」」**——这是口型一次对好的关键（用户确认，以后每期都这样）。检查每个包的音频首尾字完整。

### 第 6 步：用户在即梦生成（按 `references/seedance.md`）

先 480p / 720p，按编号上传图片和音频、粘贴提示词、时长选文件里写的秒数。下载回对应文件夹。满意后用「超清」放大**同一条**成 2K，存成 `2k.mp4`。

### 第 7 步：对齐（每段生成完就跑）

```
python S/seedance_align.py EP 03        # 逐镜头对齐，出 preview/03_..._配音乐.mp4
python S/seedance_align.py EP 04 --whole # 用户说「这段没事，按 11 秒对」时
```
把配音乐的小样发给用户看。**用户的眼睛是标准**：嘴不对 → 重做那段，或换成对方的反应镜头；画面和歌词对不上 → 先问是不是贴错了提示词。

### 第 8 步：拼接与包装

```
python S/seedance_assemble.py EP --2k            # preview/成片_拼接.mp4（2K 60 帧）
python S/package.py EP --test 0:12                # 先出一小段看字幕
python S/package.py EP                            # final/<标题>_成片.mp4
```
包装：开场标题叠在推镜头上、金色字幕（最后两字放大垫红笔刷）、底部史料注释（特粗纯白）、名字卡（A 左 B 右）、片尾提问、水印、调色 B（去胶质感）、开场 / 间奏 / 片尾的现场声。字幕颜色大小、注释、调色都只改 `package.py` 重新导出，不用重新生成。

### 第 9 步：封面与文案

```
python S/cover.py EP --frame <一帧两人对峙的截图>
```
竖版 3:4 + 横版 16:9。文案：IG（中英双语）、YouTube Shorts（标题中英名字）、抖音 / 小红书（金句开头）+ 话题 + 结尾提问 + 置顶评论投票下期。海外平台（IG / YouTube）优先。

### 发布前提醒（每期都说）

- 平台勾选「AI 生成内容」，片头的「AI生成 仅供娱乐」不要去掉
- Suno 免费版的歌不能商用
- 注释出处定稿前核一遍原文

## H3 API 路线（可选）

用户有 MiniMax 余额、想批量自动提交时：`make_clips.py` → `h3run.py --estimate`（先报价，同意了才提交）→ `qa.py` / `lipcheck.py` → `assemble.py` → `package.py`。模板见 `references/shot-template.md` 下半部分。

## 参考

- `references/lyrics-guide.md`：选题清单、查重、歌词结构、注释、episode.json 字段
- `references/suno.md`：设置、两段 Extend、风格模板
- `references/midjourney.md`：9 张定妆图
- `references/seedance.md`：即梦网页版生成、口型、清晰度
- `references/shot-template.md`：整片节奏；H3 的 35 条模板
- `references/pitfalls.md`：踩过的坑
- `examples/zhugeliang-vs-simayi/episode.json`：Seedance 路线完整示例；`examples/zhouyu-vs-zhugeliang/`：H3 路线示例
