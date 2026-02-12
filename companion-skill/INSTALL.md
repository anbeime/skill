# 小跃虚拟伴侣 Skill - 安装说明

## ✅ 已完成的工作

1. ✅ 创建完整的项目结构
2. ✅ 集成智谱 AI GLM-4.7-Flash 模型
3. ✅ 集成 CogView-3-Flash 图片生成
4. ✅ 实现场景识别和对话生成
5. ✅ 配置 API Key

## 📦 下一步：安装依赖

请在 PowerShell 中执行以下命令：

```powershell
# 1. 进入项目目录
cd D:\tool\xiaoyue-companion-skill

# 2. 安装依赖
npm install

# 3. 编译项目
npm run build

# 4. 运行测试
npm test
```

## 🎨 可选：生成图片库

如果你想预先生成一套完整的场景图片：

```powershell
npm run test:generate
```

⚠️ 注意：此操作会调用 9 次 CogView API，可能产生少量费用（约 ¥0.5-1）

## 🔧 集成到 OpenClaw

### 方法1：复制 dist 目录

```powershell
# 复制编译后的文件到 OpenClaw skills 目录
xcopy /E /I dist "$env:USERPROFILE\.openclaw\skills\xiaoyue-companion"
```

### 方法2：创建符号链接

```powershell
# 创建符号链接（推荐，方便开发调试）
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.openclaw\skills\xiaoyue-companion" -Target "D:\tool\xiaoyue-companion-skill\dist"
```

### 配置 OpenClaw

编辑 `~/.openclaw/openclaw.json`：

```json
{
  "skills": {
    "entries": {
      "xiaoyue-companion": {
        "enabled": true,
        "env": {
          "ZHIPU_API_KEY": "da8df5ba954341829f7afd05ca23a889.RrJoTsbaAkGYA6ZU",
          "XIAOYUE_PHOTO_MODE": "ai"
        }
      }
    }
  }
}
```

### 更新 SOUL.md

在 `~/.openclaw/workspace/SOUL.md` 中添加小跃的人设（参考 `SKILL.md`）

### 重启 OpenClaw

```powershell
openclaw restart
```

## 📖 详细文档

- **快速开始**: `QUICKSTART.md`
- **Skill 定义**: `SKILL.md`
- **完整文档**: `README.md`

## ❓ 常见问题

### Q: npm install 失败？

检查：
1. Node.js 版本是否 >= 18.0.0
2. 网络连接是否正常
3. 尝试清除缓存：`npm cache clean --force`

### Q: API 调用失败？

检查：
1. `.env` 文件中的 API Key 是否正确
2. 网络能否访问 `https://open.bigmodel.cn`
3. 查看详细错误信息：`npm test`

### Q: 如何修改小跃的外观？

编辑 `src/image-generator.ts` 中的 `characterDescription`

## 📞 需要帮助？

- 查看测试输出了解详细错误
- 检查 `.env` 配置是否正确
- 确保 API Key 有效且有余额

---

**现在就开始吧！** 🎉

```powershell
cd D:\tool\xiaoyue-companion-skill
npm install
```
