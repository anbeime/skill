# Suno 做歌

用户在 suno.com 操作。Claude 把下面各栏按本期填好发给用户。

## 设置（Advanced 模式）

1. 左侧 **Create** → 顶部切到 **Advanced**（Simple 不能填歌词）
2. `+ Voice` 不选（选了两段会是同一个声音）
3. **More Options**：Vocal Gender **Male**（两个男人时）· Duration **Auto** · Max Mode **Off**（只是多花积分）· Weirdness **35%** · Style Influence **70%** · **Variety 拉到 0**（不然 Suno 会改写风格词，两人又变像）· Personalize **Off**
4. 点了推荐风格弹出 **Overwrite Styles?** → 选 **Keep Current**

## 两个声音：分两次生成 + Extend（推荐）

Suno 不能一首歌上传两个声音（Voices 只能用用户本人、要现场朗读验证；两个 Persona 一起用不稳）。最稳的是：

1. **第一段**：只填前奏 + A 的 16 句，风格写 A 的声线，生成几首挑一首（16 句唱全、咬字清楚）
2. 在这首上 **… → Remix/Edit → Extend**，**Extend from 设在 A 最后一句刚唱完**：Lyrics 栏自动带出的 A 歌词全部消失就对了（还带着 A 的后几句 = 设早了，会被重唱掉）
3. Lyrics 清空换成第二段（间奏口号 + B 的 16 句 + 结尾口号），Styles 换成 B 的声线；**模型和第一段一样**
4. 挑 B 声音分得开、接口鼓点没断的一首 → **… → Get Whole Song** → 下载完整版 **MP3**，存成 `song.mp3`

## 第一段 Lyrics

```
[Intro: 1 bar DJ scratch]

[Verse 1: {A 拼音名}]
{A 的 16 句，一句一行}
```

## 第二段 Lyrics（Extend 时填）

```
[Break: 2 bars, crowd chanting]
{口号} {口号} {口号} {口号}

[Verse 2: {B 拼音名}]
{B 的 16 句}

[Outro: crowd chanting]
{B 的名字} {B 的名字} {B 的名字}
[End]
```

间奏口号要贴主题（诸葛亮 vs 司马懿：「出战」——观众催死守不出的司马懿出战）。

## Styles（两段只有声线那几个词不同，伴奏词完全一样，续写才接得上）

```
Chinese battle rap, old school boom bap, 95 BPM, dark cinematic, hard punchy drums, vinyl scratches, guqin and guzheng samples, war drums, deep sub bass, live crowd hype, solo male rapper, {A 声线}, clear Mandarin diction, very short intro
```
```
Chinese battle rap, old school boom bap, 95 BPM, dark cinematic, hard punchy drums, vinyl scratches, guqin and guzheng samples, war drums, deep sub bass, live crowd hype, solo {B 声线}, clear Mandarin diction, short ending
```

用户试过把鼓点词提前、去掉 dark cinematic 来「加强节奏感」，结果觉得**还是原来的好**——节奏不够就多生成几次挑，不改模板。

## 声线搭配（两段反差要大）

| 人设 | 写法 |
| --- | --- |
| 年轻、高傲、武将 | proud young male rapper, sharp bright voice, fast confident flow |
| 从容、带嘲讽 | confident witty young voice, clear bright tone, fast sharp mocking flow |
| 年老、阴、慢 | old male rapper, low raspy deep voice, slow lazy drawl, sinister calm |
| 沉稳谋士 | calm cool male rapper, smooth low deep voice, slow mocking delivery |
| 粗人、猛将 | aggressive male rapper, deep powerful voice, shouting energy |
| 帝王 | cold commanding male rapper, slow heavy delivery |

声音还是太像：`episode.json` 的 `pitch` 给两人各变 ±1 半音。

## Title

`{A}vs{B}`

## 拿到歌以后

- `analyze_song.py` 会按小节剪短前奏和结尾；**间奏要听**：Suno 常在口号后面自己加一段即兴（把 B 的第一句当副歌重复唱），用 `retrim.py` 处理，手法见 pitfalls.md「间奏拼接」
- 版权：Suno **免费版生成的歌不能商用**，要开收益用付费版重新生成最终那首。每期提醒一次
