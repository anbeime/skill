# -*- coding: utf-8 -*-
"""
Batch Generator for all Handdraw Style Business Application Guides (012-280).
Follows the gold-standard 5-module architecture established in 001.md.
"""
import os
import sys
import json
import time
import re
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUSINESS_DIR = os.path.join(BASE_DIR, "business")
STYLES_JSON = os.path.join(BASE_DIR, "skills", "handdraw-style-prompter", "references", "styles.json")
COLORS_JSON = os.path.join(BASE_DIR, "skills", "handdraw-style-prompter", "references", "colors.json")
LAYOUTS_JSON = os.path.join(BASE_DIR, "skills", "handdraw-style-prompter", "references", "layouts.json")

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# Load reference colors & layouts to build concrete prompt context
colors_data = json.load(open(COLORS_JSON, encoding="utf-8"))
colors_summary = "\n".join([f"- `C-{c['id'].split('-')[1]} {c['name_zh']} ({c['name_en']})`" for c in colors_data])

SYSTEM_PROMPT = f"""你是一位顶级商业插画艺术总监、品牌策略顾问与文创产品专家。
请根据提供的特定手绘风格编号、作者/参考、英文生图名、所属分组和视觉特征，为其撰写深度商业应用分析指南。

输出必须严格遵循以下 Markdown 结构与高标准要求，严禁偷工减料，严禁使用套路空话：

# {{number}}｜商业应用：{{风格中文名}} ({{generation_name}})

- **风格编号**：`{{number}}`
- **英文生图名称**：`{{generation_name}}`
- **参考作者**：`{{reference}}`
- **商业定位**：{{一句话精辟提炼品牌定位与商业人格，必须深刻、锋利，直击受众心智}}

---

## 一、 为什么适合这些生意（画风商业优势）

1. **{{洞察一标题}}**：
   {{深入剖析画风的视觉基因、心理学机制与商业穿透力，3-4句话}}
2. **{{洞察二标题}}**：
   {{深入剖析画风的媒介质感、传播属性与差异化竞争壁垒，3-4句话}}
3. **{{洞察三标题}}**：
   {{深入剖析画风如何降低认知门槛、引发受众共鸣或提供品牌溢价，3-4句话}}
4. **{{洞察四标题}}**：
   {{关于实物工艺、印刷触感、低边际成本或跨场景延展性的专业洞察，3-4句话}}

---

## 二、 优先商业应用场景与物料矩阵

| 商业场景 | 核心物料载体 | 为什么有效（如何发挥画风优势） |
| :--- | :--- | :--- |
| **{{场景1：精准垂直行业品类}}** | {{核心物料，如外带杯套、展陈海报、包装盒等}} | {{针对该场景具体痛点，阐述该画风如何发挥奇效}} |
| **{{场景2}}** | {{核心物料}} | {{为什么有效}} |
| **{{场景3}}** | {{核心物料}} | {{为什么有效}} |
| **{{场景4}}** | {{核心物料}} | {{为什么有效}} |
| **{{场景5}}** | {{核心物料}} | {{为什么有效}} |

---

## 三、 可落地的代表性商业项目策划

### 策划案：{{具体且引人入胜的品牌联名/战役/产品上市策划案标题}}

- **商业目标**：{{清晰具体的商业诉求、客群痛点与转化目标}}
- **核心视觉概念**：{{核心角色定位、主视觉母题或空间意象}}
- **产品组合（4–6 款具体单品/体验触点）**：
  1. 《{{单品1名称}}》—— {{具体物理形态、画面情节与文案隐喻}}
  2. 《{{单品2名称}}》—— {{具体物理形态、画面情节与文案隐喻}}
  3. 《{{单品3名称}}》—— {{具体物理形态、画面情节与文案隐喻}}
  4. 《{{单品4名称}}》—— {{具体物理形态、画面情节与文案隐喻}}
  5. 《{{单品5名称}}》—— {{具体物理形态、画面情节与文案隐喻}}
- **交付物清单**：
  - {{列出具体的制作规范、工程打样、宣发长图、周边生产稿等 4-5 项}}
- **后续延展复用**：{{如何沉淀为品牌常青超级资产或后续季度更新}}

---

## 四、 执行要点与适用边界

1. **{{视觉约束与线条规范}}**：{{明确线条、构图、比例、光影等不可妥协的底线}}
2. **{{客户沟通与避坑指南}}**：{{如何向客户或甲乙方解释该风格的独特美学价值，避免被误解为粗糙或幼稚}}
3. **{{特种纸材与工艺搭配}}**：{{推荐的特种纸张、印刷工艺、物理打样或数码交互规范}}
4. **不适用场景**：
   - {{明确列出 4-5 个绝不适合该画风的行业品类与商业场景，并说明理由}}

---

## 五、 推荐图型与配色搭配

- **推荐搭配图型**：
  - [`SC-XXX`（{{图型中文名}}）](../LAYOUTS.md#social-cards)
  - [`IG-XXX`（{{图型中文名}}）](../LAYOUTS.md#infographics)
  - [`SB-XXX`（{{图型中文名}}）](../LAYOUTS.md#comic-storyboards)
  - [`IP-XXX`（{{图型中文名}}）](../LAYOUTS.md#ip-characters)
  （必须精选 4-5 个适配本风格的图型编号，编号取自本库 SC-001~SC-022, IG-001~IG-035, SB-001~SB-068, IP-001~IP-017）
- **推荐主题色**：
  （必须严格从以下本库 36 色中挑选 3-4 种最契合的色彩编号与名称，绝对严禁瞎编任何颜色名称与编号）：
{colors_summary}
  - `C-XX {{中文名}} ({{英文名}})`：{{针对本画风的具体推荐理由}}
"""

def is_valid_business_file(filepath, expected_number):
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) < 2200:
            return False
        required_elements = [
            f"# {expected_number}",
            "## 一、 为什么适合这些生意",
            "## 二、 优先商业应用场景与物料矩阵",
            "## 三、 可落地的代表性商业项目策划",
            "## 四、 执行要点与适用边界",
            "## 五、 推荐图型与配色搭配",
            "| 商业场景 | 核心物料载体 |",
            "- **风格编号**：",
            "- **商业定位**："
        ]
        for req in required_elements:
            if req not in content:
                return False
        return True
    except Exception:
        return False

def generate_one_style(style_info, max_retries=3):
    num = style_info["number"]
    target_file = os.path.join(BUSINESS_DIR, f"{num}.md")

    if is_valid_business_file(target_file, num):
        return num, True, "Already exists and valid"

    prompt = f"""请为以下手绘风格撰写深度商业应用指南：
- 风格编号：{num}
- 原参考作者/风格来源：{style_info['reference']}
- 英文生图名称：{style_info['generation_name']}
- 所属分组：{style_info.get('group', '')}
- 核心视觉特征：{style_info['traits']}

请严格按照系统要求，输出完整的 5 大模块 Markdown 文档。仅输出 Markdown 正文本身，不要包含代码块外部的寒暄。"""

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.6,
                    "max_tokens": 4000
                }).encode("utf-8")
            )
            resp = urllib.request.urlopen(req, timeout=60)
            res_json = json.loads(resp.read().decode("utf-8"))
            content = res_json["choices"][0]["message"]["content"]

            content = re.sub(r"^```markdown\s*", "", content)
            content = re.sub(r"^```\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            content = content.strip()

            # Fix Windows path slashes if needed
            content = content.replace("LAYOUTS.md#", "LAYOUTS.md#")

            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content + "\n")

            if is_valid_business_file(target_file, num):
                return num, True, f"Generated ({len(content)} chars)"
            else:
                if attempt == max_retries:
                    return num, False, "Validation failed after max retries"
                time.sleep(2)
        except Exception as e:
            if attempt == max_retries:
                return num, False, f"Exception: {str(e)}"
            time.sleep(3 * attempt)

    return num, False, "Unknown failure"

def main():
    if not os.path.exists(BUSINESS_DIR):
        os.makedirs(BUSINESS_DIR, exist_ok=True)

    styles = json.load(open(STYLES_JSON, encoding="utf-8"))
    print(f"Total styles loaded: {len(styles)}")

    # We want styles 001 to 280
    pending_styles = []
    for s in styles:
        num = s["number"]
        target = os.path.join(BUSINESS_DIR, f"{num}.md")
        if not is_valid_business_file(target, num):
            pending_styles.append(s)

    print(f"Styles requiring generation: {len(pending_styles)} / {len(styles)}")

    if not pending_styles:
        print("All styles are already completely generated!")
        return

    workers = 5
    print(f"Starting batch generation with {workers} concurrent workers...")

    completed = 0
    total = len(pending_styles)
    failures = []

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_style = {executor.submit(generate_one_style, s): s for s in pending_styles}
        for future in as_completed(future_to_style):
            s = future_to_style[future]
            num = s["number"]
            try:
                n, success, msg = future.result()
                if success:
                    completed += 1
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    remaining = (total - completed) / rate if rate > 0 else 0
                    print(f"[{completed}/{total}] Style {num} OK: {msg} (ETA: {remaining/60:.1f}m)")
                else:
                    failures.append((num, msg))
                    print(f"[FAIL] Style {num}: {msg}")
            except Exception as e:
                failures.append((num, str(e)))
                print(f"[ERR] Style {num}: {e}")

    print("\n" + "=" * 50)
    print(f"Batch run finished. Successfully generated: {completed}/{total}")
    if failures:
        print(f"Failures ({len(failures)}):")
        for num, msg in failures:
            print(f" - {num}: {msg}")
    else:
        print("ALL styles successfully generated and validated!")

if __name__ == "__main__":
    main()
