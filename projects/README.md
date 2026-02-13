# 小易对话助手项目集

这个目录包含三个小易助手相关的项目，作为技能商店的扩展项目。

## 📦 项目列表

### 1. companion-skill
**小易伴侣技能版（TypeScript）**

基于 TypeScript 的小易伴侣技能版本，提供完整的技能系统框架。

**主要功能：**
- 🎯 场景检测能力
- 🖼️ 图像生成集成
- 💬 个性化对话提示
- 🔧 完整的技能系统架构

**技术栈：** TypeScript, Node.js

**快速开始：**
```bash
cd companion-skill
npm install
npm start
```

详细文档：[companion-skill/README.md](./companion-skill/README.md)

---

### 2. companion-simple
**小易伴侣简化版（Python）**

基于 Python 的小易伴侣简化版本，专注于技能数据管理和 Web 展示。

**主要功能：**
- 🕷️ 技能数据爬取与管理
- 🌐 Web 界面展示
- 🔌 API 服务集成
- ⏰ 定时任务调度

**技术栈：** Python, Flask/FastAPI

**快速开始：**
```bash
cd companion-simple
pip install -r requirements.txt
python main.py
```

详细文档：[companion-simple/README.md](./companion-simple/README.md)

---

### 3. assistant
**小易助手核心系统（TypeScript）**

小易助手的核心系统，提供完整的智能代理框架。

**主要功能：**
- 🤖 智能代理框架
- 🧠 记忆管理系统
- 📁 文件管理技能
- 🔄 多平台支持

**技术栈：** TypeScript, Node.js

**快速开始：**
```bash
cd assistant
npm install
npm run dev
```

详细文档：[assistant/README.md](./assistant/README.md)

---

## 🔗 与技能商店的关系

这些项目是技能商店的配套工具和框架：

- **companion-skill**: 提供技能开发框架
- **companion-simple**: 提供技能数据管理
- **assistant**: 提供技能运行环境

## 📖 使用场景

1. **技能开发者**: 使用 companion-skill 开发新技能
2. **技能管理员**: 使用 companion-simple 管理技能数据
3. **应用开发者**: 使用 assistant 构建完整应用

## 🤝 贡献

欢迎为这些项目贡献代码和建议！

## 📝 许可证

各项目遵循各自的许可证，详见各项目目录。

---

**最后更新**: 2026-02-12  
**维护者**: anbeime
