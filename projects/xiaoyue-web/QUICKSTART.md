# 🚀 小易伴侣快速启动指南

## 方法 1：使用启动脚本（推荐）

直接双击 `start.bat` 文件即可！

脚本会自动：
- ✅ 检查 .env 配置
- ✅ 验证 API Key
- ✅ 启动服务器

## 方法 2：手动启动

```bash
# 进入项目目录
cd D:\tool\skill\projects\xiaoyue-web

# 启动服务器
C:\Users\ASUS\.stepfun\runtimes\node\install_1770628825604_th45cs96cig\node-v22.18.0-win-x64\node.exe server.js
```

## 📝 首次使用配置

1. **配置 API Key**（只需一次）
   ```bash
   copy .env.example .env
   notepad .env
   ```
   
2. **获取 API Key**
   - 访问：https://open.bigmodel.cn/
   - 注册并登录
   - 创建 API Key
   - 复制并粘贴到 .env 文件

3. **启动服务器**
   - 双击 `start.bat`
   - 或运行上面的手动启动命令

4. **打开浏览器**
   - 访问：http://localhost:3000
   - 开始和小易对话！

## 💬 使用示例

试试这些对话：
- "你好小易！"
- "发张你在咖啡馆的照片"
- "你在做什么？"
- "今天心情怎么样？"

## ❓ 常见问题

### Q: 提示"需要配置 API Key"
A: 编辑 .env 文件，填入真实的 API Key

### Q: 端口被占用
A: 修改 .env 中的 PORT=3000 为其他端口

### Q: 无法生成图片
A: 检查 API Key 余额，新用户有免费额度

## 🔗 相关链接

- 智谱 AI 平台：https://open.bigmodel.cn/
- GitHub 仓库：https://github.com/anbeime/skill
- 问题反馈：https://github.com/anbeime/skill/issues

---

**祝你和小易相处愉快！** 🎉
