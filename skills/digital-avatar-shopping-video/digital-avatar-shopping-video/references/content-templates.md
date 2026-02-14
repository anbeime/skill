# 内容模板

## 目录
- [1. 脚本模板](#1-脚本模板)
- [2. 产品介绍模板](#2-产品介绍模板)
- [3. 对比分析模板](#3-对比分析模板)
- [4. 场景模板](#4-场景模板)
- [5. UI元素模板](#5-ui元素模板)

---

## 1. 脚本模板

### 1.1 标准导购视频脚本模板

```json
{
  "script_metadata": {
    "video_title": "【小省导购】XXX产品推荐",
    "total_duration": "100-120秒",
    "target_audience": "目标用户群体",
    "product_count": 3
  },
  "script_scenes": [
    {
      "scene": 1,
      "time_range": "0:00-0:10",
      "duration": 10,
      "type": "开场",
      "dialogue": "大家好，我是小省导购员！今天给大家推荐[X]款[产品类型]，[核心卖点]！",
      "visual_notes": "导购员挥手致意，背景出现[产品合集画面]",
      "avatar_expression": "热情、微笑",
      "hand_gesture": "挥手致意",
      "ui_elements": ["标题：小省导购员", "副标题：XXX推荐"]
    },
    {
      "scene": 2,
      "time_range": "0:10-0:35",
      "duration": 25,
      "type": "产品介绍",
      "dialogue": "首先是[产品A名称]，[定位/特点]！[核心卖点1]，[具体描述]；[核心卖点2]，[使用场景]；最重要的是，[核心卖点3]，[优势总结]！",
      "visual_notes": "[产品A特写]，突出[核心参数]，配以[动画效果]",
      "avatar_expression": "专业、自信",
      "hand_gesture": "指向产品",
      "ui_elements": ["产品名称", "价格标签", "核心卖点标签"]
    },
    {
      "scene": 3,
      "time_range": "0:35-0:60",
      "duration": 25,
      "type": "产品介绍",
      "dialogue": "再来看[产品B名称]，[定位/特点]！[核心卖点1]，[具体描述]；[核心卖点2]，[使用场景]；最重要的是，[核心卖点3]，[优势总结]！",
      "visual_notes": "[产品B特写]，突出[核心参数]，配以[动画效果]",
      "avatar_expression": "亲切、热情",
      "hand_gesture": "展示产品",
      "ui_elements": ["产品名称", "价格标签", "核心卖点标签"]
    },
    {
      "scene": 4,
      "time_range": "0:60-0:90",
      "duration": 30,
      "type": "产品介绍+对比",
      "dialogue": "最后是[产品C名称]，[定位/特点]！[核心卖点1]，[具体描述]；[核心卖点2]，[使用场景]。\n\n三款产品各有优势：[产品A名称][特点]，适合[人群A]；[产品B名称][特点]，适合[人群B]；[产品C名称][特点]，适合[人群C]！",
      "visual_notes": "[产品C特写] + [对比表格]",
      "avatar_expression": "客观、认真",
      "hand_gesture": "做对比手势",
      "ui_elements": ["产品名称", "价格标签", "对比表格"]
    },
    {
      "scene": 5,
      "time_range": "0:90-1:20",
      "duration": 30,
      "type": "结尾",
      "dialogue": "根据你的需求选择，绝对不踩坑！想了解更多？点击下方链接查看详情哦！",
      "visual_notes": "导购员微笑挥手，出现[购买按钮]和[链接]",
      "avatar_expression": "热情、期待",
      "hand_gesture": "指向下方",
      "ui_elements": ["行动按钮：立即购买", "链接：查看详情"]
    }
  ]
}
```

### 1.2 促销活动脚本模板

```json
{
  "script_metadata": {
    "video_title": "【小省导购】[节日/活动名称]大促推荐",
    "total_duration": "80-100秒",
    "target_audience": "目标用户群体",
    "product_count": 3,
    "promotion_type": "限时折扣/满减/优惠券"
  },
  "script_scenes": [
    {
      "scene": 1,
      "time_range": "0:00-0:08",
      "duration": 8,
      "type": "开场",
      "dialogue": "[节日/活动]来啦！我是小省导购员，今天给大家带来超值好物，错过再等一年！",
      "visual_notes": "节日主题背景，导购员热情洋溢",
      "avatar_expression": "兴奋、热情",
      "hand_gesture": "双手张开",
      "ui_elements": ["活动横幅", "倒计时"]
    },
    {
      "scene": 2,
      "time_range": "0:08-0:28",
      "duration": 20,
      "type": "产品介绍",
      "dialogue": "首先是[产品A名称]，原价[原价]，现在[活动价]，直降[降价金额]！[核心卖点]，[使用场景]！",
      "visual_notes": "产品展示，价格对比动画",
      "avatar_expression": "激动",
      "hand_gesture": "指向价格标签",
      "ui_elements": ["原价/现价对比", "折扣标签"]
    },
    {
      "scene": 3,
      "time_range": "0:28-0:48",
      "duration": 20,
      "type": "产品介绍",
      "dialogue": "再来看[产品B名称]，满[满减金额]减[减免金额]，还能叠加[优惠券]！[核心卖点]，[使用场景]！",
      "visual_notes": "产品展示，优惠券动画",
      "avatar_expression": "期待",
      "hand_gesture": "展示优惠券",
      "ui_elements": ["满减标签", "优惠券图标"]
    },
    {
      "scene": 4,
      "time_range": "0:48-0:80",
      "duration": 32,
      "type": "产品介绍+总结",
      "dialogue": "最后[产品C名称]，[限时秒杀]，仅剩[库存数量]件！[核心卖点]！\n\n三款好物各有特色，赶紧选一款带回家吧！",
      "visual_notes": "产品展示，库存倒计时",
      "avatar_expression": "急切",
      "hand_gesture": "催促手势",
      "ui_elements": ["秒杀标签", "库存倒计时", "购买按钮"]
    }
  ]
}
```

### 1.3 单品深度推荐脚本模板

```json
{
  "script_metadata": {
    "video_title": "【小省导购】[产品名称]深度测评",
    "total_duration": "150-180秒",
    "target_audience": "目标用户群体",
    "product_count": 1,
    "review_type": "深度测评"
  },
  "script_scenes": [
    {
      "scene": 1,
      "time_range": "0:00-0:10",
      "duration": 10,
      "type": "开场",
      "dialogue": "大家好，我是小省导购员！今天给大家深度测评[产品名称]，看看它值不值得买！",
      "visual_notes": "导购员认真表情，产品全景",
      "avatar_expression": "认真、专业",
      "hand_gesture": "手持产品"
    },
    {
      "scene": 2,
      "time_range": "0:10-0:35",
      "duration": 25,
      "type": "外观展示",
      "dialogue": "先看外观，[产品名称]采用[设计风格]，[材质/工艺]，整体[整体评价]。手感[手感描述]，颜值[颜值评价]！",
      "visual_notes": "产品360度旋转展示，细节特写",
      "avatar_expression": "欣赏",
      "hand_gesture": "展示产品细节"
    },
    {
      "scene": 3,
      "time_range": "0:35-1:00",
      "duration": 25,
      "type": "功能演示",
      "dialogue": "功能方面，[核心功能1]，[具体表现]；[核心功能2]，[具体表现]；[核心功能3]，[具体表现]！",
      "visual_notes": "功能操作演示动画",
      "avatar_expression": "专业",
      "hand_gesture": "演示功能"
    },
    {
      "scene": 4,
      "time_range": "1:00-1:30",
      "duration": 30,
      "type": "使用场景",
      "dialogue": "在实际使用中，[场景1]表现[表现评价]；[场景2]表现[表现评价]；[场景3]表现[表现评价]！",
      "visual_notes": "使用场景演示",
      "avatar_expression": "满意",
      "hand_gesture": "做对比手势"
    },
    {
      "scene": 5,
      "time_range": "1:30-1:50",
      "duration": 20,
      "type": "总结建议",
      "dialogue": "总结一下：[优点总结]。适合[推荐人群]。价格[价格评价]，性价比[性价比评价]！",
      "visual_notes": "优点列表，适合人群标签",
      "avatar_expression": "肯定",
      "hand_gesture": "竖大拇指"
    },
    {
      "scene": 6,
      "time_range": "1:50-2:00",
      "duration": 10,
      "type": "结尾",
      "dialogue": "如果你[购买条件]，强烈推荐入手！想了解更多？点击下方链接哦！",
      "visual_notes": "导购员微笑，购买按钮",
      "avatar_expression": "热情",
      "hand_gesture": "指向下方"
    }
  ]
}
```

---

## 2. 产品介绍模板

### 2.1 手机产品介绍模板

```json
{
  "product_template": {
    "category": "智能手机",
    "structure": [
      {
        "section": "开场定位",
        "duration": "5秒",
        "template": "首先是[产品名称]，[定位/特点]！"
      },
      {
        "section": "核心卖点1",
        "duration": "8秒",
        "template": "[屏幕/处理器/电池]配置超强，[具体参数]，[优势描述]！"
      },
      {
        "section": "核心卖点2",
        "duration": "8秒",
        "template": "[拍照/系统/设计]也很出色，[具体特点]，[使用场景]！"
      },
      {
        "section": "核心卖点3",
        "duration": "7秒",
        "template": "最重要的是，价格只要[价格]，性价比无敌！"
      }
    ],
    "feature_library": {
      "处理器": {
        "高端": "骁龙8 Gen 2 / 天玑9200",
        "中端": "骁龙7+ / 天玑8200",
        "入门": "骁龙6系 / 天玑700"
      },
      "屏幕": {
        "描述": "120Hz高刷屏，看视频刷剧都超流畅",
        "优势": "色彩鲜艳，触控灵敏"
      },
      "电池": {
        "描述": "5000mAh大电池，续航一整天",
        "优势": "告别续航焦虑"
      },
      "拍照": {
        "描述": "6400万像素主摄，拍照清晰",
        "优势": "记录生活每一个美好瞬间"
      }
    }
  }
}
```

### 2.2 服装产品介绍模板

```json
{
  "product_template": {
    "category": "服装",
    "structure": [
      {
        "section": "开场定位",
        "duration": "5秒",
        "template": "首先是[产品名称]，[风格/特点]！"
      },
      {
        "section": "设计亮点",
        "duration": "8秒",
        "template": "[材质/剪裁/图案]很用心，[具体特点]，[穿着感受]！"
      },
      {
        "section": "搭配建议",
        "duration": "8秒",
        "template": "搭配[搭配建议1]或者[搭配建议2]，[适用场景]都超合适！"
      },
      {
        "section": "性价比",
        "duration": "7秒",
        "template": "价格只要[价格]，设计感十足，性价比超高！"
      }
    ],
    "feature_library": {
      "材质": {
        "棉质": "柔软亲肤，透气舒适",
        "丝绸": "丝滑质感，高级感十足",
        "雪纺": "轻盈飘逸，仙气满满"
      },
      "风格": {
        "简约": "经典不过时，百搭显瘦",
        "复古": "复古潮流，个性十足",
        "甜美": "可爱甜美，减龄显嫩"
      },
      "适用场景": {
        "日常": "上班通勤、周末出游",
        "约会": "浪漫约会、聚餐派对",
        "运动": "健身运动、户外活动"
      }
    }
  }
}
```

### 2.3 家电产品介绍模板

```json
{
  "product_template": {
    "category": "家电",
    "structure": [
      {
        "section": "开场定位",
        "duration": "5秒",
        "template": "首先是[产品名称]，[定位/特点]！"
      },
      {
        "section": "核心功能",
        "duration": "8秒",
        "template": "[核心功能1]，[具体表现]，[使用效果]！"
      },
      {
        "section": "智能体验",
        "duration": "8秒",
        "template": "[智能功能]，[操作便捷性]，[省心省力]！"
      },
      {
        "section": "性价比",
        "duration": "7秒",
        "template": "价格[价格]，功能齐全，绝对物超所值！"
      }
    ],
    "feature_library": {
      "核心功能": {
        "洗衣机": "大容量设计，轻松搞定全家衣物",
        "冰箱": "多分区保鲜，食材不串味",
        "空调": "快速制冷热，舒适不等待"
      },
      "智能功能": {
        "智能控制": "手机APP远程操控",
        "语音控制": "语音指令，解放双手",
        "自动调节": "智能感知，自动调节"
      },
      "省心省力": {
        "省电": "一级能效，省电又省钱",
        "省时": "高效运行，节省时间",
        "省心": "智能提醒，使用无忧"
      }
    }
  }
}
```

---

## 3. 对比分析模板

### 3.1 三款产品对比模板

```json
{
  "comparison_template": {
    "product_count": 3,
    "comparison_points": [
      "价格",
      "性能/配置",
      "设计/外观",
      "适用人群"
    ],
    "comparison_structure": {
      "intro": "三款产品各有优势：",
      "product_A": "[产品A名称] [核心优势]，适合[人群A]！",
      "product_B": "[产品B名称] [核心优势]，适合[人群B]！",
      "product_C": "[产品C名称] [核心优势]，适合[人群C]！",
      "conclusion": "都是[产品类型]中的佼佼者！"
    },
    "comparison_library": {
      "价格": {
        "最低": "价格最亲民，性价比超高",
        "中等": "价格适中，配置均衡",
        "最高": "配置最强，物有所值"
      },
      "性能": {
        "入门级": "日常使用足够",
        "中端": "性能强劲，体验流畅",
        "高端": "旗舰配置，极致体验"
      },
      "设计": {
        "简约": "简约实用，不过时",
        "时尚": "时尚潮流，个性十足",
        "高端": "高端大气，品质感强"
      },
      "适用人群": {
        "学生": "适合学生党，预算有限",
        "职场": "适合职场人士，稳重专业",
        "家庭": "适合家庭使用，全家人都喜欢"
      }
    }
  }
}
```

### 3.2 对比表格模板

```json
{
  "comparison_table_template": {
    "columns": ["参数", "产品A", "产品B", "产品C"],
    "rows": {
      "价格": ["1299元", "1499元", "1699元"],
      "屏幕": ["6.67英寸 120Hz", "6.67英寸 120Hz", "6.74英寸 120Hz"],
      "处理器": ["骁龙695", "骁龙778G", "天玑900"],
      "电池": ["5000mAh", "5000mAh", "4300mAh"],
      "拍照": ["4800万像素", "6400万像素", "6400万像素"]
    },
    "highlight_style": {
      "best_price": "绿色高亮",
      "best_performance": "橙色高亮",
      "best_design": "蓝色高亮"
    },
    "prompt_template": "现代简洁的对比表格UI，包含4列[参数数量]行数据，蓝色主题色，清晰易读，最佳参数用绿色高亮"
  }
}
```

---

## 4. 场景模板

### 4.1 电商促销场景

```json
{
  "scenario_template": {
    "scenario_type": "电商促销",
    "themes": {
      "618大促": {
        "background": "618主题背景，橙红色调，促销氛围浓厚",
        "ui_elements": ["618横幅", "满减标签", "优惠券图标", "倒计时"],
        "music": "欢快、急促",
        "tone": "热情、急切"
      },
      "双11大促": {
        "background": "双11主题背景，紫红色调，狂欢氛围",
        "ui_elements": ["双11横幅", "红包雨", "折扣标签", "秒杀倒计时"],
        "music": "热烈、兴奋",
        "tone": "激动、期待"
      },
      "年货节": {
        "background": "春节主题背景，红色金色，喜庆氛围",
        "ui_elements": ["年货节横幅", "福字装饰", "满减标签", "年货清单"],
        "music": "喜庆、欢快",
        "tone": "喜庆、热闹"
      }
    }
  }
}
```

### 4.2 产品类型场景

```json
{
  "scenario_template": {
    "scenario_type": "产品类型",
    "product_categories": {
      "3C数码": {
        "background": "科技感背景，深蓝色渐变，几何线条，光效",
        "avatar_outfit": "简约职业装",
        "tone": "专业、科技",
        "ui_style": "现代、简洁"
      },
      "服装时尚": {
        "background": "时尚背景，柔和粉色或紫色，模特展示",
        "avatar_outfit": "时尚休闲装",
        "tone": "时尚、亲切",
        "ui_style": "时尚、精致"
      },
      "家电家居": {
        "background": "温馨居家背景，暖色调，生活化场景",
        "avatar_outfit": "休闲居家装",
        "tone": "温馨、实用",
        "ui_style": "简洁、生活化"
      },
      "美妆护肤": {
        "background": "精致美妆背景，粉色或米色，产品特写",
        "avatar_outfit": "精致时尚装",
        "tone": "精致、专业",
        "ui_style": "精致、高级"
      }
    }
  }
}
```

---

## 5. UI元素模板

### 5.1 价格标签模板

```json
{
  "ui_element_template": {
    "element_type": "价格标签",
    "styles": [
      {
        "name": "标准价格标签",
        "design": {
          "background": "橙色背景",
          "text_color": "白色",
          "font_size": "24px",
          "padding": "8px 16px",
          "border_radius": "4px"
        },
        "content": "¥1299",
        "prompt": "现代风格的价格标签UI，橙色背景，白色文字，1299元，简洁大气"
      },
      {
        "name": "折扣价格标签",
        "design": {
          "background": "红色背景",
          "text_color": "白色",
          "font_size": "24px",
          "padding": "8px 16px",
          "border_radius": "4px"
        },
        "content": "原价¥1799 现价¥1299",
        "prompt": "折扣价格标签UI，红色背景，白色文字，原价1799现价1299，划线原价效果"
      },
      {
        "name": "促销标签",
        "design": {
          "background": "渐变橙红",
          "text_color": "白色",
          "font_size": "20px",
          "padding": "6px 12px",
          "border_radius": "20px"
        },
        "content": "限时特惠",
        "prompt": "促销标签UI，橙红渐变背景，白色文字，限时特惠，圆角设计"
      }
    ]
  }
}
```

### 5.2 行动按钮模板

```json
{
  "ui_element_template": {
    "element_type": "行动按钮",
    "styles": [
      {
        "name": "立即购买按钮",
        "design": {
          "background": "渐变橙色",
          "text_color": "白色",
          "font_size": "20px",
          "padding": "12px 32px",
          "border_radius": "25px",
          "shadow": true
        },
        "content": "立即购买",
        "prompt": "购买按钮UI，橙色渐变背景，白色文字，立即购买，圆角设计，带阴影效果"
      },
      {
        "name": "查看详情按钮",
        "design": {
          "background": "透明",
          "border_color": "橙色",
          "text_color": "橙色",
          "font_size": "18px",
          "padding": "10px 28px",
          "border_radius": "22px",
          "border_width": "2px"
        },
        "content": "查看详情",
        "prompt": "查看详情按钮UI，透明背景，橙色边框，橙色文字，查看详情，圆角设计"
      },
      {
        "name": "领券按钮",
        "design": {
          "background": "红色",
          "text_color": "白色",
          "font_size": "18px",
          "padding": "10px 24px",
          "border_radius": "4px",
          "icon": "优惠券图标"
        },
        "content": "领取优惠券",
        "prompt": "领券按钮UI，红色背景，白色文字，优惠券图标，领取优惠券"
      }
    ]
  }
}
```

### 5.3 参数标签模板

```json
{
  "ui_element_template": {
    "element_type": "参数标签",
    "styles": [
      {
        "name": "核心卖点标签",
        "design": {
          "background": "蓝色背景",
          "text_color": "白色",
          "font_size": "16px",
          "padding": "6px 14px",
          "border_radius": "4px"
        },
        "content": "5000mAh大电池",
        "prompt": "产品参数标签UI，蓝色背景，白色文字，5000mAh大电池，简洁清晰"
      },
      {
        "name": "特性标签",
        "design": {
          "background": "渐变蓝",
          "text_color": "白色",
          "font_size": "14px",
          "padding": "4px 12px",
          "border_radius": "12px"
        },
        "content": "120Hz高刷",
        "prompt": "产品特性标签UI，蓝色渐变背景，白色文字，120Hz高刷，胶囊形状"
      },
      {
        "name": "适合人群标签",
        "design": {
          "background": "浅橙色背景",
          "text_color": "深橙色",
          "font_size": "14px",
          "padding": "4px 12px",
          "border_radius": "12px"
        },
        "content": "适合学生党",
        "prompt": "适合人群标签UI，浅橙色背景，深橙色文字，适合学生党，胶囊形状"
      }
    ]
  }
}
```

---

## 附录：使用说明

### 如何使用这些模板

1. **选择合适的模板**：根据产品类型和场景选择对应的模板
2. **替换占位符**：将模板中的占位符（如[产品名称]、[价格]）替换为实际内容
3. **调整内容**：根据实际情况调整时长、台词长度
4. **保持一致性**：确保同一视频中的所有元素风格一致

### 模板自定义规则

- **时长调整**：可根据实际需要调整每个部分的时长，但总时长控制在60-180秒
- **台词优化**：根据产品特点优化台词，保持口语化和亲和力
- **视觉元素**：根据品牌和产品特性调整视觉风格
- **UI元素**：确保UI元素与整体风格协调

### 注意事项

- 所有模板都应符合"小省导购员"的人设
- 避免使用绝对化词语（最好、第一等）
- 保持客观公正，提供真实的购买建议
- 确保台词自然流畅，符合口语习惯
