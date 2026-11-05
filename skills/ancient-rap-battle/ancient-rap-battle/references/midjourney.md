# Midjourney 定妆图

一期 9 张，**每期都做新的**（同一个人物再出场也换年龄段 / 时期 / 服装细节，和上期区分开），存进 `<期数文件夹>/refs/`，文件名照下表。用户可以先存成中文名放在 `定妆图/`，Claude 复制改名。

| 文件名 | 内容 | 比例 | 用在 |
| --- | --- | --- | --- |
| a_sheet.png | A 三视图（全身，正 / 侧 / 背） | 16:9 | 开场、间奏的全景 |
| a_face.png | A 表情四宫格 | 1:1 | 每段的表情参考、片尾 |
| a_bust.png | A 半身，**侧身朝右** | 16:9 | 所有近景、对口型 |
| b_sheet.png | B 三视图 | 16:9 | |
| b_face.png | B 表情四宫格 | 1:1 | |
| b_bust.png | B 半身，**侧身朝左** | 16:9 | |
| dj.png | DJ | 16:9 | 每段都传，DJ 台上必须有人 |
| crowd.png | 观众 | 16:9 | 开场前景、间奏、片尾 |
| venue.png | 场景，**正面、对称、平视** | 16:9 | 每段 |

**不做气氛组**：固定三个群演反复出镜会抢戏，台上的反应交给听的那个人。

**顺序**：先做两张三视图定人物 → 用三视图当 `--oref` 做表情四宫格和半身图 → 场景 → 群众（场景当 `--sref`，色调一致；群众别用 `--oref`，会变成一堆同一张脸）。

## 挑图标准

- 脸原创，不像任何真实人物或演过这个角色的演员，像就重抽
- 两人一黑一白之类，配色和轮廓一眼分得开
- 道具（羽扇等）三张图里长得一样；形状不标准没关系，一致更重要
- 场景：舞台前沿是水平线、DJ 台在正中、A 的旗在左 B 的旗在右；斜的不能用（开场要正对着推）

## 提示词

### 三视图
```
cinematic photoreal character turnaround sheet, front view, side view and back view of the same man standing full body side by side, plain grey studio background, soft even studio light. {拼音名}, {朝代、身份、年龄、体型}. {脸型、眉眼、胡须、发型、头饰}. {表情气质}. {服装：材质、颜色、配件}. Holding a silver corded microphone in his right hand{和道具}. Original face, not resembling any real actor. realistic skin texture, ultra detailed, 35mm film still --ar 16:9 --style raw
```

### 表情四宫格（`--oref` 三视图）
```
2x2 grid of close-up portraits of the same man, cinematic photoreal, plain grey background: top left shouting a rap line into a silver microphone, top right smug confident smirk, bottom left mocking side-eye, bottom right {一个和本期梗有关的表情，例：turning his head all the way back over his shoulder with a creepy calm smile}. {名字、脸、发型、服装简述} --ar 1:1 --style raw
```

### 半身（`--oref` 三视图；A 朝右、B 朝左，就是固定站位里两人面对面的方向）
```
cinematic photoreal waist-up portrait of the same man as the reference, facing three-quarters to the {right|left}, plain grey studio background, soft even studio light. {名字、脸、胡子、帽子}. {服装}. Holding a silver corded microphone near his mouth in his right hand{和道具}. {表情}. realistic skin texture, ultra detailed, 35mm film still --ar 16:9 --style raw
```

### DJ（贴合本期场景的混搭，例：小兵套现代飞行夹克）
```
cinematic photoreal portrait, front and side half-body views of the same young Asian man, plain grey background. {发型}, big black over-ear headphones, {一件现代单品} worn over {本期时代的衣服}, thick silver chain, {一个本期梗的小道具}, cool focused expression --ar 16:9 --style raw
```

### 场景（开头写死机位，结尾 --no 排除斜角）
```
cinematic photoreal wide shot, symmetrical straight-on front view, camera at eye level facing the stage head-on from behind the audience, centered one-point perspective, the front edge of the stage perfectly horizontal and parallel to the frame, level horizon, no main characters. {场景：例 a night battlefield turned into a rap battle arena, a raised square wooden stage, rows of A's banners on the left and B's banners on the right, all banners plain without text, braziers at the four corners, a DJ booth at the back built on {本期的东西} with modern turntables, a mixer and two vertical blue-white LED tubes, a single cold white spotlight beam from above cutting through smoke onto the empty center of the stage, packed audience raising torches}. Low-key lighting, warm firelight against cool blue-white, shallow depth of field, 35mm film grain --ar 16:9 --style raw --no dutch angle, tilted camera, diagonal composition, aerial view, side angle
```

### 群众（`--sref` 场景图）
```
cinematic photoreal medium shot of a packed crowd of {本期观众：例 Three Kingdoms soldiers, the left half in A's colours, the right half in B's colours}, about twenty people aged 18 to 50 with varied faces, raising fists and torches and cheering wildly toward the stage, firelight, smoke and haze, shallow depth of field, 35mm film grain --ar 16:9 --style raw
```

场景不要每期都一样：木楼地下说唱、两军阵前擂台、宫廷宴会、江边战船……跟着人物走。
