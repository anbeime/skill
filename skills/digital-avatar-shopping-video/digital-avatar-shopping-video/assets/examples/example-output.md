# 数字人导购视频生成示例

## 示例1：性价比手机推荐视频

### 输入需求
"我想制作一个关于性价比手机的导购视频，目标用户是学生和职场新人"

### 步骤1：内容策划方案

```json
{
  "theme": "性价比手机推荐",
  "target_audience": {
    "age_range": "18-35岁",
    "occupation": ["学生", "职场新人"],
    "core_needs": ["性价比", "性能", "续航"]
  },
  "products": [
    {
      "name": "红米Note 13",
      "price": "1299元",
      "positioning": "超高性价比",
      "key_features": ["5000mAh电池", "67W快充", "120Hz高刷屏"],
      "selling_point": "千元机中的续航怪兽"
    },
    {
      "name": "realme Q5",
      "price": "1499元",
      "positioning": "颜值与性能平衡",
      "key_features": ["轻薄设计", "6400万像素", "骁龙778G"],
      "selling_point": "轻薄好看又好拍"
    },
    {
      "name": "荣耀Play 6",
      "price": "1699元",
      "positioning": "游戏性能优先",
      "key_features": ["天玑900", "120Hz高刷", "液冷散热"],
      "selling_point": "游戏党的最佳选择"
    }
  ],
  "video_style": {
    "tone": "专业、亲切、实用",
    "visual_style": "科技感、简洁现代",
    "duration": "100-120秒"
  }
}
```

### 步骤2：分镜脚本

```json
{
  "script": [
    {
      "scene": 1,
      "time": "0:00-0:10",
      "duration": 10,
      "type": "开场",
      "dialogue": "大家好，我是小省导购员！今天给大家推荐3款性价比超高的千元手机，让你花小钱办大事！",
      "visual_notes": "导购员挥手致意，背景出现手机合集画面",
      "avatar_expression": "热情、微笑",
      "hand_gesture": "挥手致意"
    },
    {
      "scene": 2,
      "time": "0:10-0:35",
      "duration": 25,
      "type": "产品介绍",
      "dialogue": "首先是红米Note 13，千元机中的续航怪兽！5000mAh大电池加上67W快充，续航焦虑彻底说拜拜！120Hz高刷屏，看视频刷剧都超流畅。最重要的是，价格只要1299元，性价比真的无敌！",
      "visual_notes": "手机特写，突出电池和屏幕参数，配以充电动画",
      "avatar_expression": "专业、自信",
      "hand_gesture": "指向手机屏幕"
    },
    {
      "scene": 3,
      "time": "0:35-0:60",
      "duration": 25,
      "type": "产品介绍",
      "dialogue": "再来看realme Q5，轻薄好看又好拍！只有179克，手感超好。6400万像素主摄，记录生活每一个美好瞬间。骁龙778G处理器，日常使用流畅无压力！",
      "visual_notes": "手机外观展示，拍照样张对比，配以握持场景",
      "avatar_expression": "亲切、热情",
      "hand_gesture": "展示手机背面"
    },
    {
      "scene": 4,
      "time": "0:60-0:90",
      "duration": 30,
      "type": "产品介绍+对比",
      "dialogue": "最后是荣耀Play 6，游戏党的最佳选择！天玑900处理器搭配液冷散热，玩游戏发热不卡顿。120Hz高刷屏，操作跟手又流畅。\n\n三款手机各有优势：红米Note 13续航最强，适合经常外出的朋友；realme Q5轻薄好看，适合注重颜值的你；荣耀Play 6性能最强，游戏党绝对不能错过！",
      "visual_notes": "手机游戏场景展示 + 三款手机对比表格",
      "avatar_expression": "专业、认真",
      "hand_gesture": "做对比手势"
    },
    {
      "scene": 5,
      "time": "0:90-1:20",
      "duration": 30,
      "type": "结尾",
      "dialogue": "根据你的需求选择，绝对不踩坑！想了解更多？点击下方链接查看详情哦！",
      "visual_notes": "导购员微笑挥手，出现购买按钮和链接",
      "avatar_expression": "热情、期待",
      "hand_gesture": "指向下方"
    }
  ]
}
```

### 步骤3：视觉设计方案

```json
{
  "background_design": {
    "style": "科技感、简洁现代",
    "color_palette": {
      "primary": "#0066CC",
      "secondary": "#E8F4FF",
      "accent": "#FF6B35",
      "text": "#333333"
    },
    "prompt": "现代科技风格背景，深蓝色渐变，简洁的几何线条和光效，适合科技产品展示，专业感强"
  },
  "product_visuals": [
    {
      "product_name": "红米Note 13",
      "visual_type": "产品特写",
      "key_elements": ["正面展示", "侧面薄度", "充电接口"],
      "prompt": "红米Note 13手机特写，正面大屏幕，侧面轻薄设计，充电接口特写，专业摄影，高清晰度，科技背景"
    }
  ],
  "ui_elements": [
    {
      "element_type": "价格标签",
      "content": "1299元",
      "style": "醒目、橙色背景",
      "prompt": "现代风格的价格标签UI，橙色背景，白色文字，1299元，简洁大气"
    },
    {
      "element_type": "对比表格",
      "columns": ["参数", "红米Note 13", "realme Q5", "荣耀Play 6"],
      "rows": ["价格", "续航", "拍照", "游戏"],
      "prompt": "现代简洁的对比表格UI，包含4列4行数据，蓝色主题色，清晰易读"
    }
  ]
}
```

### 步骤4：数字人方案

```json
{
  "avatar_profile": {
    "name": "小省导购员",
    "gender": "女性",
    "age": "25-28岁",
    "appearance": {
      "hairstyle": "齐肩短发，利落干练",
      "outfit": "简约职业装，浅蓝色衬衫+白色外套",
      "accessories": "无夸张饰品，简约耳环",
      "overall_vibe": "专业、亲切、值得信赖"
    },
    "prompt": "25岁左右的女性导购员，齐肩短发，穿着浅蓝色职业衬衫配白色外套，妆容精致自然，表情亲切专业，现代简约风格，高清摄影"
  },
  "expression_sequence": [
    {
      "scene": 1,
      "emotion": "热情",
      "facial_features": ["微笑", "眼神明亮", "微微点头"],
      "prompt": "年轻女性导购员，热情微笑，眼神明亮，微微点头，背景简洁专业"
    },
    {
      "scene": 2,
      "emotion": "专业自信",
      "facial_features": ["坚定", "手势有力", "语气肯定"],
      "prompt": "导购员表情专业自信，手势指向产品，语气坚定，展示产品"
    }
  ]
}
```

### 步骤5：视频合成方案

```json
{
  "video_composition": {
    "total_duration": "120秒",
    "resolution": "1920x1080",
    "frame_rate": 30
  },
  "timeline": [
    {
      "scene": 1,
      "time_range": "0:00-0:10",
      "layers": [
        {"type": "background", "content": "科技风格背景"},
        {"type": "avatar", "content": "数字人挥手致意"},
        {"type": "text", "content": "小省导购员"}
      ]
    }
  ]
}
```

---

## 示例2：夏季女装爆款对比

### 输入需求
"我想制作一个夏季女装导购视频，推荐3款不同风格的爆款连衣裙"

### 内容策划方案（简版）

```json
{
  "theme": "夏季女装爆款",
  "target_audience": {
    "age_range": "18-30岁",
    "gender": "女性",
    "core_needs": ["款式", "搭配", "性价比"]
  },
  "products": [
    {
      "name": "法式碎花连衣裙",
      "price": "299元",
      "positioning": "甜美浪漫",
      "key_features": ["法式收腰", "碎花图案", "A字版型"]
    },
    {
      "name": "简约衬衫连衣裙",
      "price": "359元",
      "positioning": "简约知性",
      "key_features": ["利落剪裁", "高级面料", "百搭设计"]
    },
    {
      "name": "度假风长裙",
      "price": "399元",
      "positioning": "度假休闲",
      "key_features": ["飘逸材质", "民族风图案", "超长裙摆"]
    }
  ],
  "video_style": {
    "tone": "时尚、温馨",
    "visual_style": "清新明亮",
    "duration": "90-100秒"
  }
}
```

### 分镜脚本片段

```json
{
  "script": [
    {
      "scene": 1,
      "time": "0:00-0:08",
      "dialogue": "大家好，我是小省导购员！夏天到了，今天给大家推荐3款超美连衣裙，让你在这个夏天美美哒！",
      "visual_notes": "导购员微笑致意，背景夏季清新风格",
      "avatar_expression": "亲切、甜美"
    },
    {
      "scene": 2,
      "time": "0:08-0:30",
      "dialogue": "首先是法式碎花连衣裙，甜美浪漫！法式收腰设计，显瘦又优雅。碎花图案清新可爱，A字版型包容性超好，各种身材都能驾驭！",
      "visual_notes": "连衣裙特写，展示收腰效果和碎花图案",
      "avatar_expression": "甜美、欣赏"
    }
  ]
}
```

---

## 示例3：618大促家电推荐

### 输入需求
"我想制作一个618促销的家电推荐视频，限时特价"

### 促销风格脚本

```json
{
  "script": [
    {
      "scene": 1,
      "time": "0:00-0:08",
      "type": "促销开场",
      "dialogue": "618大促来啦！我是小省导购员，今天给大家带来超值家电，错过再等一年！",
      "visual_notes": "618主题背景，导购员热情洋溢",
      "avatar_expression": "兴奋、热情",
      "ui_elements": ["618横幅", "倒计时"]
    },
    {
      "scene": 2,
      "time": "0:08-0:28",
      "dialogue": "首先是小米智能扫地机器人，原价1999元，现在1299元，直降700元！LDS激光导航，清扫无死角，让你解放双手！",
      "visual_notes": "产品展示，价格对比动画，直降700元醒目标签",
      "avatar_expression": "激动",
      "ui_elements": ["原价/现价对比", "直降700元标签"]
    }
  ]
}
```

---

## 输出格式说明

### MVP版本输出
在技术集成前，Skill输出以下内容：

1. **内容策划方案** (JSON)
   - 产品列表
   - 目标用户
   - 视频风格

2. **分镜脚本** (JSON)
   - 完整对话台词
   - 场景描述
   - 时间安排

3. **视觉设计方案** (JSON)
   - 背景设计提示词
   - 产品展示提示词
   - UI元素设计

4. **数字人方案** (JSON)
   - 形象描述
   - 表情序列
   - 动作规划

5. **视频合成方案** (JSON)
   - 时间线规划
   - 图层管理
   - 音频配置

### 完整版本输出
集成技术API后，Skill输出：

1. **生成的视觉图像** (PNG/JPG)
   - 背景图
   - 产品展示图
   - UI元素图

2. **数字人关键帧** (PNG/JPG)
   - 不同场景的表情
   - 关键动作帧

3. **合成视频** (MP4)
   - 最终导购视频文件
   - 分辨率：1920x1080
   - 时长：60-120秒

---

## 使用建议

### 快速上手
1. 先使用MVP版本验证内容和流程
2. 使用智能体图像生成能力生成视觉元素
3. 人工使用视频编辑工具完成最终合成

### 批量生产
1. 集成数字人API（如HeyGen）
2. 集成视频合成工具（如FFmpeg）
3. 实现端到端自动化生成

### 质量优化
1. 收集用户反馈
2. 优化脚本和视觉设计
3. 调整数字人形象和表现
4. 持续迭代改进
