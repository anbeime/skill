---
name: style-library-importer
description: Add a named or text-defined visual style to the numbered hand-drawn style library, generating a square representative image without number badges when none is supplied. Do not use for image-only Tweet imports.
---

# Text-Defined Style Library Importer

Use this Skill when the user wants to add a visual style to the local hand-drawn style library with a style name, visual traits, or both. It is separate from `tweet-style-importer`: an image-only request belongs to the Tweet workflow and must not receive a new number here.

## 核心铁律：严禁从示意图提取具体画面内容到特征描述 (Prohibition on Content Extraction)

> [!CAUTION]
> **绝对禁止“图意解析污染”**：
> 当用户提供示意图/参考图（或 AI 解析图片）录入风格时，**绝对严禁**将图中的具体主体内容提取写入 `--traits` 特征描述中！
> - **严禁提取的画面内容（Content/Subject）**：
>   - 任何人物主体（如“年轻女性”、“女孩”、“男人”、“老人”、“幼童”等）；
>   - 人物外貌与穿着（如“短发”、“长发”、“白色棉麻长裙”、“风衣”、“T恤”等）；
>   - 人物动作与姿态（如“侧身回眸”、“奔跑”、“坐在长椅上”、“微笑”等）；
>   - 具体道具与物品（如“咖啡杯”、“雨伞”、“自行车”、“书本”等）；
>   - 具体场景与地貌（如“黄色花田”、“海湾远山”、“街道”、“樱花树”等）。
> - **允许且仅允许提取的纯艺术视觉语言（Aesthetic & Medium Traits Only）**：
>   - 笔触线条（如细钢笔线、松散手绘线条、粗粝炭笔线条、色块轮廓）；
>   - 材质媒介（如水彩晕染、胶片颗粒、赛璐珞、油画厚涂、复古丝网印）；
>   - 光影色彩（如高饱和通透、日系青蓝调、低饱和灰调、柔和侧逆光、高动态自然光）；
>   - 空间虚实（如中长焦浅景深背景虚化、前景光斑、大面积留白、平铺无透视）。
> 风格特征必须对任何新主题保持绝对中立。画面中的一切主体、服饰与环境必须 100% 交由未来用户的具体主题（Theme）决定。

## Interpret the input

- **Name only:** keep the supplied name as the style label, do not invent or store visual traits, and register `name_activation=strong`, `traits_activation=none` for `gpt-image-2`.
- **Name plus traits:** preserve the name, retain only positive concrete visual traits, remove negative clauses such as `避免`、`不要`、`不准`、`禁止` or `无写实纹理`, and register `name_activation=weak`, `traits_activation=strong`.
- **Traits only:** invent a readable Chinese style label and a concise English generation name, retain only positive concrete visual traits, and register `name_activation=weak`, `traits_activation=strong`.
- **Image only:** do not change the library. Explain that image-only imports are handled by `tweet-style-importer`.

For every text-defined style, `gpt-image-2` must use its configured text activation and must not receive a reference image. Unknown models retain the library's existing image fallback behavior.

## Representative image

If the user provides an image alongside textual input, use it directly as the representative source image; do not generate another one.

If no image is provided, generate exactly one original 1:1 representative image with `gpt-image-2`. Select a simple neutral subject and setting that make the declared style legible. Use the supplied name and, when present, the filtered positive traits; do not reuse subjects, actions, scenes, compositions, or stories from existing library entries. Generate one clean image without any number badge or overlay.

## Import

After a representative image is available, run the deterministic importer from the repository root:

```powershell
python scripts/import_manual_style.py --source-name "中文风格名" --generation-name "English Generation Style Name" --traits "正向可见特征" --image "/path/to/representative.png"
```

- Omit `--traits` for name-only input.
- For traits-only input, pass the names you created with `--source-name` and `--generation-name`.
- Use `--dry-run` before importing when checking the selected activation policy would be useful.
- The importer assigns the next number, creates a 512px clean single tile (strictly without any number badge, overlay, or burned text), and continues the active H contact sheet. A single supplied or generated representative image does not create a reference grid; the clean single image is used if a reference is required. A 1024px 2×2 reference grid is created only when two to four source images are supplied. The importer then updates the source table and capability metadata, rebuilds the gallery, and runs full validation.

Strictly do NOT burn, overlay, or stamp any number badge onto the image. Keep the representative tile 100% clean and unblemished. Report the number, activation path, whether an image was generated or supplied, the active H sheet, and the validation result.
