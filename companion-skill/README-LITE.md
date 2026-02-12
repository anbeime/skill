# 小跃虚拟伴侣 Skill - 简化版

## ✅ 已完成的修正

### 重要修正（避免扣费）
- ✅ `glm-4.7-flash` - 对话生成（正确模型名称）
- ✅ `glm-4.6v-flash` - 视觉理解（正确模型名称）
- ✅ 简化版不调用 AI 生图，仅使用静态图片

### 简化版特点
- ✅ 对话功能完整
- ✅ 场景识别完整
- ✅ 仅使用静态图片（免费）
- ✅ 避免产生额外费用

## 📦 手动安装步骤

由于 npm 缓存问题，请手动执行以下命令：

### 步骤1：清除缓存

```powershell
cd D:\tool\xiaoyue-companion-skill
npm cache clean --force
```

### 步骤2：删除旧文件

```powershell
# 删除 node_modules（如果存在）
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue

# 删除 package-lock.json（如果存在）
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue
```

### 步骤3：安装依赖

```powershell
npm install
```

如果失败，尝试使用淘宝镜像：

```powershell
npm install --registry=https://registry.npmmirror.com
```

### 步骤4：编译项目

```powershell
npm run build
```

### 步骤5：创建图片目录

```powershell
New-Item -ItemType Directory -Force -Path "assets\reference"
```

### 步骤6：复制参考图片

```powershell
Copy-Item "D:\tool\StepFun\resources\chat.png" "assets\reference\default.jpg"
Copy-Item "D:\tool\StepFun\resources\chat.png" "assets\reference\reference.png"
```

### 步骤7：运行测试

```powershell
npm test
```

## 💰 费用说明

**简化版每日费用：**
- 对话生成：约 ¥0.05-0.1（glm-4.7-flash）
- 图片：完全免费（静态文件）
- **总计：约 ¥0.05-0.1/天**

**不会调用的 API：**
- ❌ cogview-3-flash（图片生成）
- ❌ glm-4.6v-flash（视觉理解）

## 📁 项目结构

```
xiaoyue-companion-skill/
├── src/
│   ├── index.ts              # 主入口
│   ├── companion.ts          # 对话生成 (glm-4.7-flash)
│   ├── image-generator.ts    # 静态图片管理
│   ├── scene-detector.ts     # 场景识别
│   ├── test.ts               # 测试脚本
│   └── prompts/
│       └── personality.ts    # 人设定义
├── assets/
│   └── reference/            # 静态图片目录
├── dist/                     # 编译输出
├── .env                      # 环境变量
├── package.json              # 依赖配置
├── tsconfig.json             # TypeScript 配置
└── README-LITE.md            # 简化版说明
```

## 🔧 集成到 OpenClaw

### 1. 复制 Skill

```powershell
xcopy /E /I dist "$env:USERPROFILE\.openclaw\skills\xiaoyue-companion"
```

### 2. 配置 OpenClaw

编辑 `~/.openclaw/openclaw.json`：

```json
{
  "skills": {
    "entries": {
      "xiaoyue-companion": {
        "enabled": true,
        "env": {
          "ZHIPU_API_KEY": "da8df5ba954341829f7afd05ca23a889.RrJoTsbaAkGYA6ZU",
          "XIAOYUE_PHOTO_MODE": "static"
        }
      }
    }
  }
}
```

### 3. 更新 SOUL.md

在 `~/.openclaw/workspace/SOUL.md` 中添加小跃的人设（参考 `SKILL.md`）

### 4. 重启 OpenClaw

```powershell
openclaw restart
```

## ❓ 常见问题

### Q: npm install 失败？

**解决方案：**
1. 清除缓存：`npm cache clean --force`
2. 删除 node_modules 和 package-lock.json
3. 使用淘宝镜像：`npm install --registry=https://registry.npmmirror.com`

### Q: 模型调用失败？

**检查：**
1. API Key 是否正确
2. 网络能否访问 `https://open.bigmodel.cn`
3. 模型名称是否为 `glm-4.7-flash`（不是 glm-4-flash）

### Q: 如何添加更多图片？

将图片放入 `assets/reference/` 目录，命名规则：
- `coffee-shop-work.jpg`
- `office-coding.jpg`
- `gym-selfie.jpg`
- 等等...

## 📖 使用示例

```
用户：帮我整理一下桌面文件
小跃：好的！我这就开始整理～顺便问一下，今天工作还顺利吗？
     [后台执行任务]
用户：有点累
小跃：辛苦啦！[发送静态图片]
     要不要我帮你生成今日工作总结？
```

## 🎯 下一步

1. ✅ 完成安装和测试
2. ✅ 准备图片素材（可选）
3. ✅ 集成到 OpenClaw
4. ✅ 在飞书中测试

---

**版本**: v0.2.0-lite  
**更新日期**: 2026-02-11  
**模型**: glm-4.7-flash（对话）+ 静态图片
