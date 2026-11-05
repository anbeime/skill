# README 示例 / README examples / README 예시

每个 README 只展示字幕语言与之相同的 3 张图：[中文](../README.md#成品案例)、[English](../README_EN.md#gallery)、[한국어](../README_KO.md#완성-예시)。图片按语言放在 `gallery/zh/`、`gallery/en/`、`gallery/ko/`，台词与时间点在 `scripts/<语言>/`，结构化记录（尺寸、来源、SHA-256）见 [gallery-manifest.json](gallery-manifest.json)。

Each README shows only the three images whose subtitles match its language. Images live in `gallery/<lang>/`, line scripts in `scripts/<lang>/`, and structured records (size, source, SHA-256) in [gallery-manifest.json](gallery-manifest.json).

각 README에는 자막 언어가 같은 이미지 3장만 표시됩니다. 이미지는 `gallery/<lang>/`, 문구와 타임스탬프는 `scripts/<lang>/`, 구조화된 기록(크기, 출처, SHA-256)은 [gallery-manifest.json](gallery-manifest.json)에 있습니다.

## 中文案例

| 案例 | 字幕模式 | 来源 | 记录 |
| --- | --- | --- | --- |
| [《大巴上的女孩》：生命属于你自己](gallery/zh/girls-on-the-bus-native.jpg) | 原生字幕 · 中英双语 · 5 句 | [Bilibili 搬运视频](https://www.bilibili.com/video/BV1jT42117zW/) | [时间点与转录](scripts/zh/girls-on-the-bus-native.json) |
| [里克·鲁宾：创意像一片变化的云](gallery/zh/rick-rubin-creative-clouds.jpg) | 脚本字幕 · 中文翻译 · 5 句 | [YouTube](https://www.youtube.com/watch?v=QP8Kpf1UQwM) | [台词与时间点](scripts/zh/rick-rubin-creative-clouds.json) |
| [陈数：工作投入，生活简单](gallery/zh/chen-shu-simple-life.jpg) | 脚本字幕 · 据原字幕整理 · 5 句 | [网易谈心社 / Bilibili](https://www.bilibili.com/video/BV1Ym4y1W7CJ/) | [台词与时间点](scripts/zh/chen-shu-simple-life.json) |

- **原生字幕**：《大巴上的女孩》一图中的 5 句字幕，都是烧录在 Bilibili 搬运版画面里的非官方中英双语字幕，直接从画面像素裁切，未识别、未重绘。左上角是视频平台水印。JSON 里的文字只是人工转录，方便检索和核对，不参与渲染。
- **脚本字幕**：里克·鲁宾一图的中文是英文播客内容的整理翻译，其中两句是第三人称转述；陈数一图依据视频原有中文字幕整理压缩后重新绘制，JSON 同时保留了 `source_text` 原文记录。两者都不是视频原字幕，也不作为人物的逐字引语。
- 三张均为 1080 × 1440。《大巴上的女孩》一图由 1440 × 1920 的存档成品统一等比缩小，未裁切、未改动画面内容；另外两张直接复制。来源链接取自本地制作记录，未重新核验视频的在线状态。

## English examples

| Example | Subtitle mode | Source | Record |
| --- | --- | --- | --- |
| [Mikayla Johnson: Define the outcome first](gallery/en/mikayla-johnson-define-outcome.jpg) | Scripted · edited English · 5 lines | [YouTube](https://www.youtube.com/watch?v=5JOL8qYed-c) | [Lines and timestamps](scripts/en/mikayla-johnson-define-outcome.json) |
| [Rick Rubin: Be yourself, not a mask](gallery/en/rick-rubin-be-yourself.jpg) | Scripted · edited English · 5 lines | [YouTube](https://www.youtube.com/watch?v=butCyO_LccY) | [Lines and timestamps](scripts/en/rick-rubin-be-yourself.json) |
| [Darby Saxbe: Share the load early](gallery/en/darby-saxbe-shared-care.jpg) | Scripted · edited English · 5 lines | [YouTube](https://www.youtube.com/watch?v=Ppyt3MptX5k) | [Lines and timestamps](scripts/en/darby-saxbe-shared-care.json) |

- All three are **scripted subtitles**: condensed or paraphrased English drawn onto real frames, not the videos' original captions and not verbatim quotations. The Rick Rubin card includes a third-person summary line, and the last Darby Saxbe line comes from a later point in the same video.
- All three are 1080 × 1440 archived outputs, copied unchanged. Source links come from local production records and were not rechecked online.

## 한국어 예시

| 예시 | 자막 모드 | 출처 | 기록 |
| --- | --- | --- | --- |
| [마수드 후세인: 모든 행동 앞에는 시작의 언덕이 있다](gallery/ko/masud-husain-starting-hill.jpg) | 스크립트 자막 · 한국어 번역 · 5줄 | [YouTube](https://www.youtube.com/watch?v=58-k4F7-AoA) | [문구와 타임스탬프](scripts/ko/masud-husain-starting-hill.json) |
| [코디 산체스: 3-2-1 말하기](gallery/ko/codie-sanchez-321-speaking.jpg) | 스크립트 자막 · 한국어 번역 · 5줄 | [YouTube](https://www.youtube.com/watch?v=t260757b_vU) | [문구와 타임스탬프](scripts/ko/codie-sanchez-321-speaking.json) |
| [이나야 맥밀란: 돈의 운영체제](gallery/ko/inaya-mcmillan-money-program.jpg) | 스크립트 자막 · 한국어 번역 · 5줄 | [YouTube](https://www.youtube.com/watch?v=U81bsDC8oP0) | [문구와 타임스탬프](scripts/ko/inaya-mcmillan-money-program.json) |

- 세 이미지 모두 **스크립트 자막**입니다. 영어 영상의 내용을 한국어로 옮겨 실제 프레임에 그려 넣은 것이며, 영상의 원래 자막이나 발언을 그대로 옮긴 인용문이 아닙니다.
- 모두 1080 × 1440 보관 결과물을 그대로 복사했습니다. 출처 링크는 로컬 제작 기록에서 가져왔으며 온라인 상태는 다시 확인하지 않았습니다.

## 权利说明 / Rights / 권리 안내

示例图只用于展示输出效果。画面、人物肖像、节目标识与台词的权利归各自权利人；仓库的 MIT 许可证不授予这些素材的使用权，原视频也不随仓库分发。

The example images only demonstrate the output format. Footage, likenesses, logos, and text remain subject to their respective rights holders; the repository's MIT license does not grant rights to this material, and source videos are not included.

예시 이미지는 결과물의 형태를 보여 주기 위한 것입니다. 영상, 인물의 초상, 로고, 문구에 대한 권리는 각 권리자에게 있으며, 이 저장소의 MIT 라이선스는 해당 자료의 사용 권한을 부여하지 않습니다. 원본 영상은 포함되어 있지 않습니다.
